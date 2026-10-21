# GA (Genetic Algorithm) Guide

## The proposed scheduler

The core scheduler is a **security-aware, privacy-aware GA** (in
`engine/scheduler.py`) that evolves task schedules across edge–MEC–cloud
nodes while minimising latency, energy and privacy/security exposure.

## Fitness function

Fitness rewards:

- **Deadline feasibility** — every task placed before its deadline
- **Low latency** — closer nodes are cheaper
- **Low energy** — idle/energy-balanced nodes preferred
- **Privacy retention** — tasks move less often and stay on trusted nodes
- **Security posture** — nodes with high attack risk carry a penalty

## Controls

The `/genetic-algorithm` page exposes population size, generations, mutation rate and
crossover rate; the summary shows the best fitness over time and the final
per-node placement. `config.yaml` (`ga:` block) overrides the defaults for
headless runs.

## Baselines

`/analytics` compares the proposed GA against three baselines over the same
workload:
- `random` — arbitrary placement
- `greedy` — best local score at each step
- `privacy_aware` — places on most-trusted best-available node

## Expected behaviour

- Best fitness should *decrease* (improve) over generations on a fixed workload.
- The GA must place every task (or the summary must report the small number of
  deadline misses).
- `tests/test_scheduler.py::test_proposed_ga_converges` asserts convergence.

## Reproducibility

The GA RNG is deterministic for seed + configuration; see `REPRODUCIBILITY.md`.