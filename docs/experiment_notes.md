# Project discussion notebook — learning and review prompts (not report prose)

## Explain the project in your own words

- What does a router buffer do when packets arrive faster than the outgoing link can transmit?
- What is the *difference* between a waiting packet and a packet currently being transmitted?
- Under which loads do buffer sizes change packet loss noticeably?
- Under which loads do buffer sizes change queueing delay dramatically?
- What is the cost of making K too small? What is the cost of making K too large?

## Design choices to defend in the Q&A

1. Why a single FIFO DropTail bottleneck? This isolates the effect of buffer capacity and is simpler than a full TCP/IP model.
2. Why keep transmission speed fixed? This makes offered load and K the independent variables.
3. Why compare normal Poisson traffic against alternating high/low Poisson segments? Two traffic shapes can yield different queueing behavior even with the same mean offered load.
4. Why use 10 seeds? Stochastic arrivals introduce run-to-run variability; report average and spread.
5. Why preserve the same input timestamps when changing K? Controls one source of experimental variability.
6. Why 20 s warmup and 120 s measurement? To limit initial-empty-queue effects. Discuss whether these choices are long enough, particularly near critical load.
7. Why does K count waiting packets only? The link can concurrently transmit one separate packet; this convention must be explicit.
8. What does throughput mean here? Completed packets per simulated second, not Mbps; all packets have equal size but size is not explicitly modeled in bytes.

## Suggested figures to examine (already generated)

- `poisson_delay.png` + `poisson_loss.png`: at heavy load, how does a larger buffer change the tradeoff?
- `poisson_throughput.png`: when does throughput stop improving?
- `poisson_queue_trace.png`: does the buffer remain close to full under sustained overload?
- `bursty_delay.png`, `bursty_loss.png`, `bursty_queue_trace.png`: does time-varying traffic alter the conclusions?
- `poisson_utilization.png`: can a high utilization still coexist with poor delay?

## Example values for a targeted self-check

`results/summary_results.csv`, Poisson arrivals, load 1.2, averaged across 10 seeds:

| K waiting packets | Mean queue waiting delay (ms) | Mean drop rate (%) | Mean throughput (pkt/s) |
|---|---:|---:|---:|
| 5 | 31.7 | 18.97 | 97.38 |
| 20 | 173.2 | 16.80 | 99.99 |
| 100 | 973.0 | 16.79 | 100.00 |
| 300 | 2973.0 | 16.79 | 100.00 |

These are **simulation results from this implementation**, not values sourced from papers.

## Limitations to acknowledge

- Fixed packet sizes and constant service time; real links have variable packet sizes, aggregation, scheduling, and diverse conditions.
- One bottleneck, one shared queue, no paths, no other routers, no cross-layer effects.
- No TCP ACK, congestion window, retransmission, or rate adaptation; long-run losses under overload differ from closed-loop TCP behavior.
- DropTail only: can reference AQM approaches as related work, but do not claim a head-to-head RED/CoDel/FQ-CoDel comparison.
- Delay measured as queue wait only (and separately system delay). It is not end-to-end RTT.
- The bursty input is a simple synthetic periodic rate modulation, not a calibrated real traffic trace.
- Finite time window, chosen seeds, and simulation model choices limit generalizability.

## Report preparation checklist — write it yourselves

- [ ] State problem and research question clearly.
- [ ] Identify the technical contribution precisely (reproducible controlled simulation + quantitative comparison; **not** a new anti-bufferbloat algorithm).
- [ ] Discuss the published bufferbloat literature and distinguish external findings from your simulation's results.
- [ ] Explain queue discipline, congestion assumptions, traffic generation, random seeds, buffer-size semantics, duration/warmup, metrics.
- [ ] Present only figures you can interpret and reproduce.
- [ ] Contrast normal and bursty traffic and explain surprising results.
- [ ] Cite the external sources you actually read.
- [ ] Describe limitations and next steps.
- [ ] Add the public GitHub URL and rerun steps.
- [ ] Ensure the report is <= 5,000 words and independently written.

## Oral time-budget suggestion (both students explain every aspect)

- 1 minute: the problem and research question.
- 2 minutes: routers, queuing, DropTail, prior work.
- 3 minutes: simulator, variables, metrics, reproducibility.
- 3 minutes: core figures and what they show.
- 2 minutes: interpretation, limitations, conclusion.
- 1 minute: margin for transitions (maximum 12 min total).
