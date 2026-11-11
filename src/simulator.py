"""Single-bottleneck, FIFO DropTail discrete-event simulation.

Queue capacity counts WAITING packets, excluding one packet in service.
Traffic is exogenous: arrivals do not react to loss (no TCP feedback).
All packets have the same size, and service time is deterministic.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import math
import random
from typing import Iterable


@dataclass(frozen=True)
class Config:
    capacity: int = 20
    arrival_rate: float = 100.0
    service_rate: float = 100.0
    warmup: float = 20.0
    duration: float = 120.0
    seed: int = 1
    traffic: str = "poisson"
    burst_period: float = 4.0
    burst_factor: float = 1.8
    sample_interval: float = 0.5

    def validate(self) -> None:
        if self.capacity < 0 or not isinstance(self.capacity, int):
            raise ValueError("capacity must be a nonnegative integer")
        if self.arrival_rate <= 0 or self.service_rate <= 0:
            raise ValueError("rates must be positive")
        if self.duration <= 0 or self.warmup < 0 or self.sample_interval <= 0:
            raise ValueError("duration and sample_interval must be positive; warmup >= 0")
        if self.traffic not in ("poisson", "bursty"):
            raise ValueError("traffic must be poisson or bursty")
        if self.burst_period <= 0 or not (1 <= self.burst_factor < 2):
            raise ValueError("burst_period > 0 and 1 <= burst_factor < 2 required")


@dataclass
class Result:
    traffic: str
    capacity: int
    arrival_rate: float
    service_rate: float
    seed: int
    warmup_s: float
    duration_s: float
    arrivals: int
    drops: int
    departures: int
    loss_pct: float
    throughput_pps: float
    utilization_pct: float
    mean_queue_wait_ms: float
    p95_queue_wait_ms: float
    mean_system_delay_ms: float
    mean_queue_packets: float
    max_queue_packets: int
    remaining_packets_at_end: int

    def as_dict(self) -> dict:
        return asdict(self)


def arrivals_for(config: Config) -> list[float]:
    """Generate Poisson arrivals or alternating high/low-rate Poisson bursts.

    For bursty traffic, high and low segments occupy equal time. Rates are
    mean_rate*burst_factor and mean_rate*(2-burst_factor), respectively.
    This preserves mean offered load when complete cycles are used.
    """
    config.validate()
    rng = random.Random(config.seed)
    end = config.warmup + config.duration
    if config.traffic == "poisson":
        t = 0.0
        out = []
        while True:
            t += rng.expovariate(config.arrival_rate)
            if t >= end:
                break
            out.append(t)
        return out
    t0 = 0.0
    out = []
    segment_index = 0
    half_period = config.burst_period / 2
    while t0 < end:
        limit = min(end, t0 + half_period)
        rate = config.arrival_rate * (config.burst_factor if segment_index % 2 == 0 else (2 - config.burst_factor))
        t = t0
        while True:
            t += rng.expovariate(rate)
            if t >= limit:
                break
            out.append(t)
        t0 = limit
        segment_index += 1
    return out


def _percentile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    ordered = sorted(xs)
    p = (len(ordered) - 1) * q
    lo = math.floor(p)
    hi = math.ceil(p)
    return ordered[lo] * (hi - p) + ordered[hi] * (p - lo) if hi != lo else ordered[lo]


def simulate(config: Config, arrivals: Iterable[float] | None = None, trace: bool = False) -> tuple[Result, list[dict]]:
    """Run simulation. At equal timestamps, departure is processed first.

    Measurements are taken in [warmup, warmup+duration). Departures and
    their queue/system delays are measured at completion time; drops and
    offered arrivals are measured at arrival time. Hence these counts are
    not a closed packet cohort at measurement boundaries.
    """
    config.validate()
    end = config.warmup + config.duration
    timestamps = arrivals_for(config) if arrivals is None else list(arrivals)
    if any(not math.isfinite(t) or t < 0 or t >= end for t in timestamps):
        raise ValueError("arrival timestamps must be finite and in [0, simulation_end)")
    if any(b < a for a, b in zip(timestamps, timestamps[1:])):
        raise ValueError("arrivals must be sorted")

    wait: deque[float] = deque()
    busy = False
    service_start = 0.0
    in_service_arrival = 0.0
    finish = math.inf
    next_arrival_index = 0
    next_arrival = timestamps[0] if timestamps else math.inf
    next_sample = config.warmup
    queue_area = 0.0
    busy_area = 0.0
    last = 0.0
    arrivals_count = drops = departures = max_queue = 0
    queue_delays: list[float] = []
    system_delays: list[float] = []
    points: list[dict] = []
    service_time = 1 / config.service_rate

    def advance(t: float) -> None:
        nonlocal last, queue_area, busy_area
        lo = max(last, config.warmup)
        hi = min(t, end)
        if hi > lo:
            queue_area += len(wait) * (hi - lo)
            busy_area += int(busy) * (hi - lo)
        last = t

    while True:
        event_time = min(next_arrival, finish, next_sample if trace else math.inf, end)
        advance(event_time)
        # At the end of the measurement window, stop without processing events.
        if event_time >= end:
            break
        # Departures are processed before simultaneous arrivals and sampling.
        if finish <= next_arrival and finish <= (next_sample if trace else math.inf):
            if finish >= config.warmup:
                departures += 1
                queue_delays.append(service_start - in_service_arrival)
                system_delays.append(finish - in_service_arrival)
            if wait:
                in_service_arrival = wait.popleft()
                service_start = finish
                finish += service_time
            else:
                busy = False
                finish = math.inf
        elif next_arrival <= (next_sample if trace else math.inf):
            t = next_arrival
            if t >= config.warmup:
                arrivals_count += 1
            if not busy:
                busy = True
                service_start = t
                in_service_arrival = t
                finish = t + service_time
            elif len(wait) < config.capacity:
                wait.append(t)
                max_queue = max(max_queue, len(wait))
            else:
                if t >= config.warmup:
                    drops += 1
            next_arrival_index += 1
            next_arrival = timestamps[next_arrival_index] if next_arrival_index < len(timestamps) else math.inf
        else:
            points.append({"time_s": round(next_sample - config.warmup, 9), "queue_packets": len(wait), "busy": int(busy)})
            next_sample += config.sample_interval

    result = Result(
        traffic=config.traffic, capacity=config.capacity, arrival_rate=config.arrival_rate,
        service_rate=config.service_rate, seed=config.seed,
        warmup_s=config.warmup, duration_s=config.duration, arrivals=arrivals_count,
        drops=drops, departures=departures,
        loss_pct=100 * drops / arrivals_count if arrivals_count else 0.0,
        throughput_pps=departures / config.duration,
        utilization_pct=100 * busy_area / config.duration,
        mean_queue_wait_ms=1000 * sum(queue_delays) / len(queue_delays) if queue_delays else float("nan"),
        p95_queue_wait_ms=1000 * _percentile(queue_delays, 0.95),
        mean_system_delay_ms=1000 * sum(system_delays) / len(system_delays) if system_delays else float("nan"),
        mean_queue_packets=queue_area / config.duration,
        max_queue_packets=max_queue,
        remaining_packets_at_end=len(wait) + int(busy),
    )
    return result, points
