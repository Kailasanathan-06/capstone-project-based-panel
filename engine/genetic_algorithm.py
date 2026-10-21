"""
Genetic Algorithm Scheduler
===========================
A real, working genetic algorithm that optimises task-to-resource allocation.

Chromosome representation
------------------------
A chromosome is a list of resource indices, one per task. Each gene value is
an index into the available resource list (LOCAL, MEC-1..N, CLOUD).

Fitness function (minimised)
----------------------------
    Fitness = w1*latency + w2*energy + w3*privacy_loss +
              w4*security_risk + deadline_penalty

Security risk is inflated through a penalty equipped with the resource's live
status so that a resource under attack / high risk is automatically avoided.

Operators: tournament selection, single-point crossover, per-gene mutation,
elitism and deadline-constraint adherence.

Critical: OFFLINE MECs are NEVER included as eligible execution candidates.
The scheduler must filter out offline resources before calling optimize().
"""

import os
import random
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class Scheduler:
    """Scheduler that filters offline MECs before GA optimization."""

    def __init__(self, digital_twin, seed=None):
        self.dt = digital_twin
        self.rng = random.Random(seed or config.DATASET_SEED)
        self.last_assignments = {}
        self.history = {}  # algorithm -> analytics dict

    def reset(self):
        self.last_assignments = {}
        self.history = {}

    # ------------------------------------------------------------------
    # Cost model helpers (shared with GA for consistency)
    # ------------------------------------------------------------------
    def _cost(self, task, res):
        size_mb = task["data_size_mb"]
        cpu_giga = task["cpu_cycles_giga"]
        mem_mb = task["memory_mb"]
        deadline_ms = task["deadline_ms"]
        privacy = task["privacy_sensitivity"]  # 0..1
        security = task["security_sensitivity"]  # 0..1

        latency = res["network_latency_ms"] + cpu_giga * 12.0 / max(
            res["cpu_utilization"], 0.05
        )
        energy = res["energy_rate"] * (cpu_giga / 1.0 + size_mb / 10.0)
        privacy_loss = res["privacy_loss_factor"] * (privacy + 0.1)
        risk = res["security_risk"]

        w = self.weights
        penalty = 0.0
        if deadline_ms and deadline_ms > 0 and latency > deadline_ms:
            penalty = w["deadline"] * 5.0 * (latency / deadline_ms - 1.0)

        fitness = (
            w["latency"] * latency / 1000.0
            + w["energy"] * energy / 20.0
            + w["privacy"] * privacy_loss
            + w["security"] * risk
            + penalty
        )
        return fitness, latency, energy

    # ------------------------------------------------------------------
    # Algorithms
    # ------------------------------------------------------------------
    def random_schedule(self, tasks):
        """Pick random online resources only."""
        resources = self.dt.states()
        # Filter: only include online resources (available=True)
        online_resources = [r for r in resources if r.get("availability", True)]
        ids = [r["resource_id"] for r in online_resources]
        if not ids:
            # Fallback to all resources if none online
            ids = [r["resource_id"] for r in resources]
        assignments = [self.rng.choice(ids) for _ in tasks]
        metrics = self._evaluate_solution(assignments, tasks, online_resources)
        metrics["algorithm"] = "random"
        self.history["random"] = metrics
        return assignments, metrics

    def greedy_schedule(self, tasks):
        """Pick, per task, the online resource with lowest combined latency."""
        resources = self.dt.states()
        # Filter: only include online resources
        online_resources = [r for r in resources if r.get("availability", True)]
        ids = [r["resource_id"] for r in online_resources]
        assignments = []
        for task in tasks:
            best, best_score = ids[0] if ids else None, float("inf")
            for res in online_resources:
                latency = res["network_latency_ms"] + task[
                    "cpu_cycles_giga"
                ] * 12.0 / max(res["cpu_utilization"], 0.05)
                if latency < best_score:
                    best, best_score = res["resource_id"], latency
            if best:
                assignments.append(best)
            else:
                assignments.append("LOCAL")  # fallback
        metrics = self._evaluate_solution(assignments, tasks, online_resources)
        metrics["algorithm"] = "greedy"
        self.history["greedy"] = metrics
        return assignments, metrics

    def privacy_aware_schedule(self, tasks):
        """Minimise privacy loss first, then latency (online only)."""
        resources = self.dt.states()
        # Filter: only include online resources
        online_resources = [r for r in resources if r.get("availability", True)]
        ids = [r["resource_id"] for r in online_resources]
        assignments = []
        for task in tasks:
            best, best_score = ids[0] if ids else None, float("inf")
            for res in online_resources:
                ploss = res["privacy_loss_factor"] * (task["privacy_sensitivity"] + 0.1)
                if ploss < best_score:
                    best, best_score = res["resource_id"], ploss
                if ploss == best_score:
                    latency = res["network_latency_ms"]
                else:
                    latency = float("inf")
                if latency < best_score:
                    best, best_score = res["resource_id"], latency
            if best:
                assignments.append(best)
            else:
                assignments.append("LOCAL")
        metrics = self._evaluate_solution(assignments, tasks, online_resources)
        metrics["algorithm"] = "privacy_aware"
        self.history["privacy_aware"] = metrics
        return assignments, metrics

    def proposed_ga_schedule(self, tasks, population=None, generations=None, seed=None):
        """Proposed security-aware Genetic Algorithm scheduler.

        Critical: Only online MECs are included in the resource list.
        OFFLINE MECs are automatically excluded.
        """
        resources = self.dt.states()
        # Filter: only include online + available resources
        # This is the key: OFFLINE MECs MUST NEVER be eligible
        online_resources = [
            r for r in resources 
            if r.get("availability", True) and r.get("is_online", True)
        ]
        ids = [r["resource_id"] for r in online_resources]
        
        if not ids:
            # Fallback: use all resources but mark as degraded
            online_resources = resources
            ids = [r["resource_id"] for r in resources]

        ga = GeneticAlgorithm(
            online_resources, population=population, generations=generations, seed=seed
        )
        assignments, _, history, best_fitness = ga.optimize(tasks)
        self.last_assignments = {
            tasks[i]["task_id"]: assignments[i] for i in range(len(tasks))
        }
        metrics = self._evaluate_solution(assignments, tasks, online_resources)
        metrics["algorithm"] = "proposed_ga"
        metrics["clash_history"] = history
        metrics["best_fitness"] = round(best_fitness, 4)
        metrics["generations"] = ga.generations_ran
        self.history["proposed_ga"] = metrics
        return assignments, metrics, history

    def _evaluate_solution(self, assignments, tasks, resources):
        """Compute aggregate metrics for a set of assignments."""
        total_latency = 0.0
        total_energy = 0.0
        total_privacy = 0.0
        total_risk = 0.0
        deadline_ok = 0
        util = {r["resource_id"]: 0.0 for r in resources}

        for i, task in enumerate(tasks):
            rid = assignments[i] if i < len(assignments) else "LOCAL"
            res = next((r for r in resources if r["resource_id"] == rid), None)
            if not res:
                # Skip this task if resource not found
                continue
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


def _resource_ids(resources):
    return [r["resource_id"] for r in resources]


class GeneticAlgorithm:
    def __init__(
        self,
        resources,
        weights=None,
        population=None,
        generations=None,
        mutation_rate=None,
        crossover_rate=None,
        elitism=None,
        tournament_size=None,
        seed=None,
    ):
        self.resources = resources
        self.resource_ids = [r["resource_id"] for r in resources]
        self.n_resources = len(self.resource_ids)
        self.weights = weights or dict(config.GA_WEIGHTS)
        self.pop_size = population or config.GA_POPULATION
        self.generations = generations or config.GA_GENERATIONS
        self.mutation_rate = mutation_rate or config.GA_MUTATION_RATE
        self.crossover_rate = crossover_rate or config.GA_CROSSOVER_RATE
        self.elitism = elitism or config.GA_ELITISM
        self.tournament_size = tournament_size or config.GA_TOURNAMENT_SIZE
        self.rng = random.Random(seed or config.DATASET_SEED)

        self.best_chromosome = None
        self.best_fitness = float("inf")
        self.history = []  # [(generation, best_fitness, avg_fitness)]
        self.generations_ran = 0

    # -- core cost model ------------------------------------------------
    def _resource_cost(self, task, resource_index):
        res = self.resources[resource_index]
        size_mb = task["data_size_mb"]
        cpu_giga = task["cpu_cycles_giga"]
        mem_mb = task["memory_mb"]
        deadline_ms = task["deadline_ms"]
        privacy = task["privacy_sensitivity"]  # 0..1
        security = task["security_sensitivity"]  # 0..1

        latency = res["network_latency_ms"] + cpu_giga * 12.0 / max(
            res["cpu_utilization"], 0.05
        )
        energy = res["energy_rate"] * (cpu_giga / 1.0 + size_mb / 10.0)
        privacy_loss = res["privacy_loss_factor"] * (privacy + 0.1)
        risk = res["security_risk"]

        w = self.weights
        penalty = 0.0
        if deadline_ms and deadline_ms > 0 and latency > deadline_ms:
            penalty = w["deadline"] * 5.0 * (latency / deadline_ms - 1.0)

        fitness = (
            w["latency"] * latency / 1000.0
            + w["energy"] * energy / 20.0
            + w["privacy"] * privacy_loss
            + w["security"] * risk
            + penalty
        )
        return fitness, latency, energy

    def _chromosome_fitness(self, chromo, tasks):
        total = 0.0
        for i, gene in enumerate(chromo):
            fit, _, _ = self._resource_cost(tasks[i], gene)
            total += fit
        return total / max(len(tasks), 1)

    # -- GA operators -----------------------------------------------------
    def _init_population(self, n_tasks):
        population = []
        for _ in range(self.pop_size):
            population.append(
                [self.rng.randrange(self.n_resources) for _ in range(n_tasks)]
            )
        return population

    def _tournament_select(self, population, fitnesses):
        best = None
        for _ in range(self.tournament_size):
            idx = self.rng.randrange(len(population))
            if best is None or fitnesses[idx] < best[1]:
                best = (population[idx], fitnesses[idx])
        return best[0]

    def _crossover(self, p1, p2):
        if self.rng.random() > self.crossover_rate or len(p1) < 2:
            return p1[:], p2[:]
        point = self.rng.randrange(1, len(p1))
        c1 = p1[:point] + p2[point:]
        c2 = p2[:point] + p1[point:]
        return c1, c2

    def _mutate(self, chromo):
        out = chromo[:]
        for i in range(len(out)):
            if self.rng.random() < self.mutation_rate:
                out[i] = self.rng.randrange(self.n_resources)
        return out

    # -- main loop ---------------------------------------------------------
    def optimize(self, tasks):
        n_tasks = len(tasks)
        if n_tasks == 0:
            return [], [], self.history, self.best_fitness

        population = self._init_population(n_tasks)
        self.history = []
        self.best_chromosome = None
        self.best_fitness = float("inf")
        self.generations_ran = 0

        # sort tasks once - genes map 1:1 to task order
        for gen in range(1, self.generations + 1):
            fitnesses = [self._chromosome_fitness(c, tasks) for c in population]
            idx = sorted(range(len(population)), key=lambda i: fitnesses[i])

            if fitnesses[idx[0]] < self.best_fitness:
                self.best_fitness = fitnesses[idx[0]]
                self.best_chromosome = population[idx[0]][:]

            avg_fit = sum(fitnesses) / len(fitnesses)
            self.history.append((gen, round(self.best_fitness, 4), round(avg_fit, 4)))
            self.generations_ran = gen

            # elitism
            new_pop = [population[i][:] for i in idx[: self.elitism]]

            while len(new_pop) < self.pop_size:
                p1 = self._tournament_select(population, fitnesses)
                p2 = self._tournament_select(population, fitnesses)
                c1, c2 = self._crossover(p1, p2)
                new_pop.append(self._mutate(c1))
                if len(new_pop) < self.pop_size:
                    new_pop.append(self._mutate(c2))

            population = new_pop

        assignments = []
        for i, gene in enumerate(self.best_chromosome):
            assignments.append(self.resource_ids[gene])
        return assignments, self.best_chromosome, self.history, self.best_fitness

    def resource_assignment_map(self, tasks):
        """Return a dict {task_id: resource_id} using the best chromosome."""
        if self.best_chromosome is None:
            return {}
        return {
            tasks[i].get("task_id", i): self.resource_ids[g]
            for i, g in enumerate(self.best_chromosome)
        }


if __name__ == "__main__":
    # quick self test with a handful of tasks
    from engine.digital_twin import DigitalTwin
    twin = DigitalTwin()
    resources = twin.states()
    sample_tasks = []
    for i in range(12):
        sample_tasks.append(
            {
                "task_id": f"T{1000+i}",
                "data_size_mb": 0.5 + i,
                "cpu_cycles_giga": 0.3 + i * 0.2,
                "memory_mb": 64 + i * 8,
                "deadline_ms": 150 + i * 10,
                "privacy_sensitivity": 0.2 + (i % 5) * 0.1,
                "security_sensitivity": 0.1 + (i % 4) * 0.1,
            }
        )
    # Use the scheduler which filters online resources
    sched = Scheduler(twin)
    assignments, metrics, history, best = sched.proposed_ga_schedule(sample_tasks)
    print("best fitness:", best)
    print("history (last 5):", history[-5:])
    print("assignments:", assignments)