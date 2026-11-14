"""Reproducible buffer-size and offered-load experiments."""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from pathlib import Path
from statistics import mean, stdev
import sys

from simulator import Config, arrivals_for, simulate

METRICS = ["loss_pct", "throughput_pps", "utilization_pct", "mean_queue_wait_ms", "p95_queue_wait_ms", "mean_queue_packets"]


def save_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("cannot save empty results")
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def build_results(output: Path, quick: bool = False) -> tuple[list[dict], list[dict]]:
    base = Config(service_rate=100, warmup=20 if not quick else 5,
                  duration=120 if not quick else 20, sample_interval=0.5)
    buffers = [4, 20, 80, 150, 300]
    loads = [0.4, 0.6, 0.8, 1.0, 1.2, 1.5]
    seeds = range(1, 11 if not quick else 4)
    raw: list[dict] = []
    # Run same arrival timestamps at each buffer size for a given profile/load/seed.
    for profile in ("poisson", "bursty"):
        for load in loads:
            for seed in seeds:
                cfg = replace(base, arrival_rate=100 * load, seed=seed, traffic=profile)
                arrivals = arrivals_for(cfg)
                for k in buffers:
                    result, _ = simulate(replace(cfg, capacity=k), arrivals)
                    rec = result.as_dict()
                    rec["offered_load"] = load
                    raw.append(rec)
    save_csv(output / "raw_results.csv", raw)
    summary: list[dict] = []
    for profile in ("poisson", "bursty"):
        for load in loads:
            for k in buffers:
                subset = [r for r in raw if r["traffic"] == profile and r["offered_load"] == load and r["capacity"] == k]
                record = {"traffic": profile, "offered_load": load, "capacity": k, "n_runs": len(subset)}
                for metric in METRICS:
                    values = [float(r[metric]) for r in subset]
                    record[metric + "_mean"] = mean(values)
                    record[metric + "_sd"] = stdev(values) if len(values) > 1 else 0.0
                summary.append(record)
    save_csv(output / "summary_results.csv", summary)

    trace_rows: list[dict] = []
    for profile, load in (("poisson", 1.2), ("bursty", 0.8)):
        cfg = replace(base, arrival_rate=100 * load, traffic=profile, seed=7)
        arrivals = arrivals_for(cfg)
        for k in (4, 80, 300):
            _, samples = simulate(replace(cfg, capacity=k), arrivals, trace=True)
            for sample in samples:
                trace_rows.append({"traffic": profile, "offered_load": load, "capacity": k, **sample})
    save_csv(output / "queue_traces.csv", trace_rows)
    return raw, summary


def plot_results(output: Path, summary: list[dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure_dir = output / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    for profile in ("poisson", "bursty"):
        for metric, ylabel, name in (
            ("mean_queue_wait_ms", "Average waiting time (ms)", "delay"),
            ("loss_pct", "Packet drop rate (%)", "loss"),
            ("throughput_pps", "Throughput (packets/s)", "throughput"),
            ("utilization_pct", "Link utilization (%)", "utilization"),
        ):
            fig, ax = plt.subplots(figsize=(7.5, 4.5))
            for load in (0.4, 0.6, 0.8, 1.0, 1.2, 1.5):
                rows = [r for r in summary if r["traffic"] == profile and r["offered_load"] == load]
                ax.errorbar([r["capacity"] for r in rows], [r[metric + "_mean"] for r in rows],
                            yerr=[r[metric + "_sd"] for r in rows], marker="o", capsize=3,
                            label=f"Offered load {load:.1f}x")
            ax.set(xlabel="Buffer capacity (waiting packets)", ylabel=ylabel,
                   title=f"{profile.capitalize()} arrivals: {name} vs buffer capacity")
            ax.grid(alpha=0.25)
            ax.legend(fontsize=8)
            fig.tight_layout()
            fig.savefig(figure_dir / f"{profile}_{name}.png", dpi=160)
            plt.close(fig)

    with (output / "queue_traces.csv").open(newline="", encoding="utf-8") as f:
        traces = list(csv.DictReader(f))
    for profile, load in (("poisson", 1.2), ("bursty", 0.8)):
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for k in (4, 80, 300):
            rows = [r for r in traces if r["traffic"] == profile and float(r["offered_load"]) == load and int(r["capacity"]) == k]
            ax.plot([float(r["time_s"]) for r in rows], [int(r["queue_packets"]) for r in rows], label=f"K={k}")
        ax.set(xlabel="Time after warmup (s)", ylabel="Waiting packets in buffer",
               title=f"Queue length over time ({profile}, load {load:.1f}x)")
        ax.grid(alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(figure_dir / f"{profile}_queue_trace.png", dpi=160)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="short runs for checking installation")
    parser.add_argument("--output", default="results", help="result directory")
    args = parser.parse_args()
    output = Path(args.output)
    raw, summary = build_results(output, args.quick)
    plot_results(output, summary)
    print(f"Saved {len(raw)} simulation runs, {len(summary)} summaries, and plots in {output}")


if __name__ == "__main__":
    main()
