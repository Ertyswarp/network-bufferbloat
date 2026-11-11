# Bufferbloat: router buffer-size experiment (ESILV Network — Topic 6)

Python discrete-event simulation studying how FIFO DropTail router buffer capacity affects delay, packet loss, throughput, and utilization under different offered loads.

**Research question:** Does increasing the buffer capacity always improve network performance, or can it increase delay without meaningful throughput benefit?

## Setup

Python 3.10+ recommended. From the repository root:

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/experiments.py
```

If activation is blocked, use `.\.venv\Scripts\python.exe` instead of `python` in the last three commands.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/experiments.py
```

For a smaller smoke test: `python src/experiments.py --quick --output quick_results`.

The full run creates/overwrites CSVs and plots in `results/` and can be rerun. Only `matplotlib` is required beyond Python's standard library.

## Code layout

- `src/simulator.py`: timestamped packet arrivals, FIFO waiting queue, deterministic transmission, tail drop, measurement counters, and traffic generators.
- `src/experiments.py`: full factorial experiment grid, CSV export, mean and sample standard deviation, figure generation.
- `tests/test_simulator.py`: deterministic test cases for queueing semantics, losses, timing, metrics, and reproducibility.
- `results/raw_results.csv`: one record for each simulation run.
- `results/summary_results.csv`: mean and standard deviation for each condition.
- `results/queue_traces.csv`: sample queue lengths versus time.
- `results/figures/`: plots of all primary metrics and example queue traces.
- `docs/experiment_notes.md`: methodology, interpretation prompts, limitations, checks.
- `docs/references.md`: primary background references to consult and cite independently.

## Network model and assumptions

```
independent packet arrivals  -->  [ FIFO DropTail queue, K waiting packets ]
                                       |
                             [single deterministic server]
                                       |
                                  departures
```

1. **One bottleneck link.** The server processes fixed-size packets at `mu = 100 packets/second`; each service time is `1/mu = 10 ms`.
2. **K is the maximum number of WAITING packets**, in addition to one possibly in transmission. If the server is busy and K waiting slots are occupied, an arriving packet is dropped (DropTail).
3. **No feedback control:** traffic sources continue sending at an exogenous rate even if packets are dropped. This is a **queueing experiment, not a TCP/IP implementation**. End-to-end TCP flow control, packet retransmissions, ACKs, application-layer delay, variable packet sizes, and multiple competing flows are not simulated.
4. Two generated traffic profiles:
   - `poisson`: exponential interarrival times with mean rate `lambda`.
   - `bursty`: independent Poisson arrivals within alternating high/low segments of 2 s each, high rate = `1.8*lambda`, low rate = `0.2*lambda`. Average offered load over complete cycles is `lambda`.
5. Warmup lasts **20 s** and measurement lasts **120 s**. All results are obtained by discrete events at their timestamps, not by counting a fixed number of packets per clock tick.
6. When arrival and service completion timestamps are equal, the departure is processed first. Events exactly at the measurement end are excluded.

## Experimental design

| Parameter | Values |
|---|---|
| Waiting buffer capacity K (packets) | 4, 20, 80, 150, 300 |
| Offered rate lambda (packets/s) | 40, 60, 80, 100, 120, 150 |
| Service rate mu (packets/s) | 100 (fixed) |
| Offered load rho = lambda/mu | 0.5, 0.8, 1.0, 1.2, 1.5 |
| Arrival profiles | poisson, bursty |
| Seeds per condition | 1 through 10 |
| Measurements after warmup | 120 seconds |
| Total independent runs | 5 × 6 × 2 × 10 = **600** |

For fairness, each profile/load/seed combination uses exactly the **same generated timestamps** when comparing buffer capacities, so observed variation across capacities is not caused by different input traffic sequences. Error bars in plots are **sample standard deviation across seeds**, not confidence intervals.

## Metrics and their definitions

- **Drop rate (%)** = 100 × dropped arrivals during measurement / all arrivals during measurement.
- **Throughput (packets/s)** = departures completed during measurement / measurement seconds.
- **Utilization (%)** = 100 × time link is occupied during measurement / measurement seconds.
- **Mean queue waiting delay (ms)** = average of (start-of-service − arrival) over packets completed during measurement × 1000.
- **P95 queue waiting delay (ms)** = 95th percentile of waiting delays of packets completed during measurement × 1000.
- **Mean queue length (packets)** = time integral of waiting packets in buffer / measurement seconds.
- **Mean system delay (ms)** = average of (completion − arrival) for packets completed during measurement × 1000.
