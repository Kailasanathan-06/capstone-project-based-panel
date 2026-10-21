"""
Metrics and Analytics
=====================
Aggregate performance, compute charts payloads and support the comparison
of the four scheduling algorithms under normal, attack and post-mitigation
conditions.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class MetricsEngine:
    """Computes analytics payloads consumed by the results page."""

    def attack_impact(self, twin, attack_sim):
        """Before/during/after impact scene for the rerouting pages.

        Reads the most recent IMPACT log entry (pre/post risk). When no attack
        has yet run, before==after==current risk (no impact recorded).
        """
        states = twin.states()
        risks = self._risk(states)
        current_risk = round(sum(risks) / len(risks), 4) if risks else 0.0
        latest = None
        for entry in reversed(getattr(attack_sim, "attack_log", [])):
            if entry.get("kind") == "IMPACT":
                latest = entry
                break
        pre = round(latest["pre_risk"], 4) if latest else current_risk
        post = round(latest["post_risk"], 4) if latest else current_risk
        return {
            "before": pre,
            "during": round(max(pre, current_risk), 4),
            "after": post,
            "current": current_risk,
            "risk_before": pre,
            "risk_after": post,
            "elevated": bool(
                getattr(attack_sim, "active_attack", None)
                and attack_sim.active_attack.get("active")
            ),
        }

    @staticmethod
    def _risk(states):
        return [s.get("security_risk", 0.0) for s in states]

    def summarize(self, scheduler, task_manager):
        """Build overall state payload for main dashboard."""
        if task_manager.tasks is None:
            return {
                "total_tasks": 0,
                "completed": 0,
                "pending": 0,
                "avg_latency": 0,
                "energy": 0,
                "privacy_score": 0,
                "security_score": 0,
            }

        n = task_manager.tasks.shape[0]
        completed = len(task_manager.results)
        avg_latency = 0.0
        energy = 0.0
        if task_manager.results:
            lat = [r["latency"] for r in task_manager.results.values()]
            eng = [r["energy"] for r in task_manager.results.values()]
            avg_latency = round(sum(lat) / len(lat), 2)
            energy = round(sum(eng) / len(eng), 3)

        privacy = 1.0 - float(task_manager.tasks["privacy_sensitivity"].mean())
        security = 1.0 - float(task_manager.tasks["security_sensitivity"].mean())
        return {
            "total_tasks": int(n),
            "completed": completed,
            "pending": int(n - completed),
            "avg_latency": avg_latency,
            "energy": energy,
            "privacy_score": round(privacy, 4),
            "security_score": round(security, 4),
        }

    def algorithm_comparison(self, scheduler, tasks):
        """Return bar-chart data for the results page."""
        # ensure all four baselines present
        if "random" not in scheduler.history:
            scheduler.random_schedule(tasks)
        if "greedy" not in scheduler.history:
            scheduler.greedy_schedule(tasks)
        if "privacy_aware" not in scheduler.history:
            scheduler.privacy_aware_schedule(tasks)
        if "proposed_ga" not in scheduler.history:
            names = [t["task_id"] for t in tasks[:50]]
            scheduler.proposed_ga_schedule(tasks[:50])

        labels = ["Random", "Greedy", "Privacy-Aware", "Proposed GA"]
        keys = ["random", "greedy", "privacy_aware", "proposed_ga"]
        series = {
            m: []
            for m in [
                "avg_latency_ms",
                "energy_j",
                "privacy_score",
                "security_score",
                "deadline_success",
            ]
        }
        for k in keys:
            h = scheduler.history.get(k, {})
            for m in series:
                series[m].append(round(h.get(m, 0), 4))
        return {"labels": labels, "series": series}


def load_default_datasets():
    """Load the shipped CSV datasets into a TaskManager (tests/checks)."""
    import pandas as pd

    df = pd.read_csv(config.TASK_DATASET)
    return df


if __name__ == "__main__":
    print("Metrics engine import OK")
