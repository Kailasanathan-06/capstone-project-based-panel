# Digital Twin Guide

## Concept

The digital twin (`engine/digital_twin.py`) maintains a live, per-node mirror
of the edge–cloud network: CPU, memory, trust, availability, security risk,
state, and an `attack_active` flag. Everything the scheduler, security and
attack labs read comes from this single source of truth.

## Node tiers

| Tier | Local risk weight | Availability |
|---|---|---|
| Edge | 0.30 | low |
| MEC | 0.55 | high |
| Cloud | 0.85 | very high |

## Security model

- Every node exposes a **security risk** (base 0.12) and a **trust** score.
- An attack raises risk via `apply_attack(node, type, severity)`; when risk
  crosses 0.8 the node status flips to `CRITICAL`, and `quarantine()` forces
  availability to 0 and flips state.
- `stop_attack()` decays risk back toward baseline with `dt` recovery so the
  twin heals realistically over time.

## How the twin is kept in sync

The `/api/digital-twin/state` endpoint returns the exact same data structure
the UI renders, so the dashboard auto-refresh always matches the engine.

## Pages that exercise the twin

- `/digital-twin` — live node map and resource cards
- `/attack-simulation` — launch + mitigate simulated attacks against the twin
- `/storage-attack` — virtual storage integrity/risk lab
- `/task-routing` — reschedule the active workload after mitigation

## Guarantees

- No real network, Docker or edge devices are touched.
- All node data is synthetic and respawned on reset.
- States cover resource exhaustion (`OVERLOADED`/`CRITICAL`) as well as normal
  operation (`idle`, `normal`, `busy`).