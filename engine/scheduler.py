"""
Scheduler
=========
Contains the baseline schedulers (random, greedy, privacy-aware) and the
proposed security-aware GA scheduler. Each scheduler returns a per-task
resource assignment plus latency/energy/risk figures used for analytics.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from engine.genetic_algorithm import GeneticAlgorithm


def _resource_ids(resources):
    return [r["resource_id"] for r in resources]


class Scheduler:
    def __init__(self, digital_twin, seed=None):
        self.dt = digital_twin
        self.rng = random.Random(seed or config.DATASET_SEED)
        self.last_assignments = {}
        self.history = {}  # algorithm -> analytics dict
        self.ga_manager = GeneticAlgorithm  # lazy setup

    def reset(self):
        self.last_assignments = {}
        self.history = {}

    # ------------------------------------------------------------------
    # Cost model helpers (shared with GA for consistency)
    # ------------------------------------------------------------------
    def _cost(self, task, res):
        size_mb = task["data_size_mb"]
        cpu = task["cpu_cycles_giga"]
        latency = res["network_latency_ms"] + cpu * 12.0 / max(
            res["cpu_utilization"], 0.05
        )
        energy = res["energy_rate"] * (cpu / 1.0 + size_mb / 10.0)
        privacy_loss = res["privacy_loss_factor"] * (task["privacy_sensitivity"] + 0.1)
        risk = res["security_risk"]
        return latency, energy, privacy_loss, risk

    def _evaluate_solution(self, assignments, tasks, resources):
        """Compute aggregate metrics for a set of assignments."""
        total_latency = 0.0
        total_energy = 0.0
        total_privacy = 0.0
        total_risk = 0.0
        deadline_ok = 0
        util = {r["resource_id"]: 0.0 for r in resources}

        for i, task in enumerate(tasks):
            rid = assignments[i]
            res = next(r for r in resources if r["resource_id"] == rid)
            latent, energy, ploss, risk = self._cost(task, res)
            total_latency += latent
            total_energy += energy
            total_privacy += ploss
            total_risk += risk
            util[rid] += 1
            if latent <= task["deadline_ms"]:
                deadline_ok += 1

        n = max(len(tasks), 1)
        return {
            "avg_latency_ms": round(total_latency / n, 2),
            "energy_j": round(total_energy / n, 3),
            "privacy_loss": round(total_privacy / n, 4),
            "security_risk": round(total_risk / n, 4),
            "privacy_score": round(1.0 - total_privacy / n, 4),
            "security_score": round(1.0 - total_risk / n, 4),
            "deadline_success": round(deadline_ok / n, 4),
            "resource_utilization": util,
        }

    # ------------------------------------------------------------------
    # Algorithms
    # ------------------------------------------------------------------
    def random_schedule(self, tasks):
        resources = self.dt.states()
        ids = _resource_ids(resources)
        assignments = [self.rng.choice(ids) for _ in tasks]
        metrics = self._evaluate_solution(assignments, tasks, resources)
        metrics["algorithm"] = "random"
        self.history["random"] = metrics
        return assignments, metrics

    def greedy_schedule(self, tasks):
        """Pick, per task, the resource with lowest combined latency."""
        resources = self.dt.states()
        ids = _resource_ids(resources)
        assignments = []
        for task in tasks:
            best, best_score = ids[0], float("inf")
            for res in resources:
                latency = res["network_latency_ms"] + task[
                    "cpu_cycles_giga"
                ] * 12.0 / max(res["cpu_utilization"], 0.05)
                if latency < best_score:
                    best, best_score = res["resource_id"], latency
            assignments.append(best)
        metrics = self._evaluate_solution(assignments, tasks, resources)
        metrics["algorithm"] = "greedy"
        self.history["greedy"] = metrics
        return assignments, metrics

    def privacy_aware_schedule(self, tasks):
        """Minimise privacy loss first, then latency."""
        resources = self.dt.states()
        ids = _resource_ids(resources)
        assignments = []
        for task in tasks:
            best, best_score = ids[0], float("inf")
            for res in resources:
                ploss = res["privacy_loss_factor"] * (task["privacy_sensitivity"] + 0.1)
                if ploss < best_score:
                    best, best_score = res["resource_id"], ploss
                    continue
                if ploss == best_score:
                    latency = res["network_latency_ms"]
                else:
                    latency = float("inf")
                if latency < best_score:
                    best, best_score = res["resource_id"], latency
            assignments.append(best)
        metrics = self._evaluate_solution(assignments, tasks, resources)
        metrics["algorithm"] = "privacy_aware"
        self.history["privacy_aware"] = metrics
        return assignments, metrics

    def proposed_ga_schedule(self, tasks, population=None, generations=None, seed=None):
        """Proposed security-aware Genetic Algorithm scheduler."""
        resources = self.dt.states()
        ga = GeneticAlgorithm(
            resources, population=population, generations=generations, seed=seed
        )
        assignments, _, history, best_fitness = ga.optimize(tasks)
        self.last_assignments = {
            tasks[i]["task_id"]: assignments[i] for i in range(len(tasks))
        }
        metrics = self._evaluate_solution(assignments, tasks, resources)
        metrics["algorithm"] = "proposed_ga"
        metrics["clash_history"] = history
        metrics["best_fitness"] = round(best_fitness, 4)
        metrics["generations"] = ga.generations_ran
        self.history["proposed_ga"] = metrics
        return assignments, metrics, history

    def run_all_baselines(
        self, tasks, ga_population=None, ga_generations=None, seed=None
    ):
        """Run random, greedy, privacy-aware and the proposed GA."""
        out = {}
        assignments, metrics = self.random_schedule(tasks)
        out["random"] = {"assignments": assignments, "metrics": metrics}
        assignments, metrics = self.greedy_schedule(tasks)
        out["greedy"] = {"assignments": assignments, "metrics": metrics}
        assignments, metrics = self.privacy_aware_schedule(tasks)
        out["privacy_aware"] = {"assignments": assignments, "metrics": metrics}
        assignments, metrics, history = self.proposed_ga_schedule(
            tasks, population=ga_population, generations=ga_generations, seed=seed
        )
        out["proposed_ga"] = {
            "assignments": assignments,
            "metrics": metrics,
            "history": history,
        }
        return out
