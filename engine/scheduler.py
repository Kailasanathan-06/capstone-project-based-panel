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
from engine.policy_engine import PolicyEngine


def _resource_ids(resources):
    return [r["resource_id"] for r in resources]


class Scheduler:
    def __init__(self, digital_twin, seed=None):
        self.dt = digital_twin
        self.seed = seed or config.DATASET_SEED
        self.rng = random.Random(self.seed)
        self.last_assignments = {}
        self.history = {}  # algorithm -> analytics dict
        self.ga_manager = GeneticAlgorithm  # lazy setup

    def reset(self):
        self.last_assignments = {}
        self.history = {}
        self.rng = random.Random(self.seed)

    # ------------------------------------------------------------------
    # Cost model helpers (shared with GA for consistency)
    # ------------------------------------------------------------------
    def _cost(self, task, res):
        size_mb = task.get("data_size_mb", 1.0)
        cpu = task.get("cpu_cycles_giga", 0.5)
        latency = res["network_latency_ms"] + cpu * 12.0 / max(
            res["cpu_utilization"], 0.05
        )
        energy = res["energy_rate"] * (cpu / 1.0 + size_mb / 10.0)
        privacy_loss = res["privacy_loss_factor"] * (task.get("privacy_sensitivity", 0.5) + 0.1)
        risk = res["security_risk"]
        return latency, energy, privacy_loss, risk

    def _get_eligible_candidates(self, task, resources):
        """Retrieve eligible resources satisfying task privacy policy and availability."""
        eligible = PolicyEngine.get_eligible_resources(task, resources)
        if not eligible:
            local = [r for r in resources if r.get("resource_id") == "LOCAL" and r.get("availability", True)]
            return local if local else [resources[0]] if resources else []
        return eligible

    def _evaluate_solution(self, assignments, tasks, resources):
        """Compute aggregate metrics for a set of assignments."""
        total_latency = 0.0
        total_energy = 0.0
        total_privacy = 0.0
        total_risk = 0.0
        deadline_ok = 0
        policy_violations = 0
        latencies = []
        util = {r["resource_id"]: 0 for r in resources}

        for i, task in enumerate(tasks):
            rid = assignments[i]
            res = next((r for r in resources if r["resource_id"] == rid), resources[0])
            latent, energy, ploss, risk = self._cost(task, res)
            total_latency += latent
            total_energy += energy
            total_privacy += ploss
            total_risk += risk
            latencies.append(latent)
            util[rid] = util.get(rid, 0) + 1

            deadline = task.get("deadline_ms") or 500
            if latent <= deadline:
                deadline_ok += 1

            # Validate dispatch against privacy policy
            is_valid, _ = PolicyEngine.validate_dispatch(task, rid, resources)
            if not is_valid:
                policy_violations += 1

        n = max(len(tasks), 1)
        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[int(len(latencies_sorted) * 0.50)] if latencies_sorted else 0.0
        p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies_sorted else 0.0

        return {
            "avg_latency_ms": round(total_latency / n, 2),
            "median_latency_ms": round(p50, 2),
            "p95_latency_ms": round(p95, 2),
            "total_energy_j": round(total_energy, 3),
            "avg_energy_j": round(total_energy / n, 3),
            "privacy_loss": round(total_privacy / n, 4),
            "security_risk": round(total_risk / n, 4),
            "privacy_score": round(max(0.0, 1.0 - total_privacy / n), 4),
            "security_score": round(max(0.0, 1.0 - total_risk / n), 4),
            "deadline_success": round(deadline_ok / n, 4),
            "deadline_miss_rate": round(1.0 - (deadline_ok / n), 4),
            "policy_violations": policy_violations,
            "policy_compliance_rate": round((n - policy_violations) / n, 4),
            "resource_utilization": util,
        }

    # ------------------------------------------------------------------
    # Schedulers
    # ------------------------------------------------------------------
    def round_robin_schedule(self, tasks):
        """Round Robin assignment across eligible resources."""
        resources = self.dt.states()
        assignments = []
        rr_index = 0
        for task in tasks:
            candidates = self._get_eligible_candidates(task, resources)
            choice = candidates[rr_index % len(candidates)]["resource_id"]
            rr_index += 1
            assignments.append(choice)

        metrics = self._evaluate_solution(assignments, tasks, resources)
        metrics["algorithm"] = "round_robin"
        self.history["round_robin"] = metrics
        return assignments, metrics

    def first_fit_schedule(self, tasks):
        """First Fit assignment: picks the first eligible resource in the hierarchy."""
        resources = self.dt.states()
        assignments = []
        for task in tasks:
            candidates = self._get_eligible_candidates(task, resources)
            assignments.append(candidates[0]["resource_id"])

        metrics = self._evaluate_solution(assignments, tasks, resources)
        metrics["algorithm"] = "first_fit"
        self.history["first_fit"] = metrics
        return assignments, metrics

    def random_schedule(self, tasks, seed=None):
        """Random assignment among eligible resources."""
        rng = random.Random(seed) if seed is not None else self.rng
        resources = self.dt.states()
        assignments = []
        for task in tasks:
            candidates = self._get_eligible_candidates(task, resources)
            assignments.append(rng.choice(candidates)["resource_id"])

        metrics = self._evaluate_solution(assignments, tasks, resources)
        metrics["algorithm"] = "random"
        self.history["random"] = metrics
        return assignments, metrics

    def greedy_schedule(self, tasks):
        """Pick, per task, the eligible resource with lowest combined latency."""
        resources = self.dt.states()
        assignments = []
        for task in tasks:
            candidates = self._get_eligible_candidates(task, resources)
            best_id, best_score = candidates[0]["resource_id"], float("inf")
            for res in candidates:
                cpu = task.get("cpu_cycles_giga", 0.5)
                latency = res["network_latency_ms"] + cpu * 12.0 / max(res["cpu_utilization"], 0.05)
                if latency < best_score:
                    best_id, best_score = res["resource_id"], latency
            assignments.append(best_id)

        metrics = self._evaluate_solution(assignments, tasks, resources)
        metrics["algorithm"] = "greedy"
        self.history["greedy"] = metrics
        return assignments, metrics

    def privacy_aware_schedule(self, tasks):
        """Minimise privacy loss first among eligible candidates, then latency."""
        resources = self.dt.states()
        assignments = []
        for task in tasks:
            candidates = self._get_eligible_candidates(task, resources)
            best_id, best_score, best_lat = candidates[0]["resource_id"], float("inf"), float("inf")
            for res in candidates:
                ploss = res["privacy_loss_factor"] * (task.get("privacy_sensitivity", 0.5) + 0.1)
                cpu = task.get("cpu_cycles_giga", 0.5)
                latency = res["network_latency_ms"] + cpu * 12.0 / max(res["cpu_utilization"], 0.05)
                if ploss < best_score or (ploss == best_score and latency < best_lat):
                    best_id, best_score, best_lat = res["resource_id"], ploss, latency
            assignments.append(best_id)

        metrics = self._evaluate_solution(assignments, tasks, resources)
        metrics["algorithm"] = "privacy_aware"
        self.history["privacy_aware"] = metrics
        return assignments, metrics

    def proposed_ga_schedule(self, tasks, population=None, generations=None, seed=None):
        """Proposed multi-objective Genetic Algorithm scheduler with hard privacy constraints."""
        resources = self.dt.states()
        ga = GeneticAlgorithm(
            resources,
            population=population,
            generations=generations,
            seed=seed or self.seed,
        )
        assignments, _, history, best_fitness = ga.optimize(tasks)
        self.last_assignments = {
            tasks[i].get("task_id", i): assignments[i] for i in range(len(tasks))
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
        """Run all schedulers (Round Robin, First Fit, Random, Greedy, Privacy-Aware, Proposed GA) on identical workload."""
        run_seed = seed or self.seed
        out = {}
        # 1. Round Robin
        rr_assign, rr_metrics = self.round_robin_schedule(tasks)
        out["round_robin"] = {"assignments": rr_assign, "metrics": rr_metrics}

        # 2. First Fit
        ff_assign, ff_metrics = self.first_fit_schedule(tasks)
        out["first_fit"] = {"assignments": ff_assign, "metrics": ff_metrics}

        # 3. Random (reproducible seed)
        rand_assign, rand_metrics = self.random_schedule(tasks, seed=run_seed)
        out["random"] = {"assignments": rand_assign, "metrics": rand_metrics}

        # 4. Greedy
        gr_assign, gr_metrics = self.greedy_schedule(tasks)
        out["greedy"] = {"assignments": gr_assign, "metrics": gr_metrics}

        # 5. Privacy Aware
        pa_assign, pa_metrics = self.privacy_aware_schedule(tasks)
        out["privacy_aware"] = {"assignments": pa_assign, "metrics": pa_metrics}

        # 6. Proposed GA
        ga_assign, ga_metrics, ga_hist = self.proposed_ga_schedule(
            tasks, population=ga_population, generations=ga_generations, seed=run_seed
        )
        out["proposed_ga"] = {
            "assignments": ga_assign,
            "metrics": ga_metrics,
            "history": ga_hist,
        }
        return out
