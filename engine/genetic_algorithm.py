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


from engine.policy_engine import PolicyEngine


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
        self.seed = seed or config.DATASET_SEED
        self.rng = random.Random(self.seed)

        self.best_chromosome = None
        self.best_fitness = float("inf")
        self.history = []  # [(generation, best_fitness, avg_fitness)]
        self.generations_ran = 0

    def _get_task_eligible_indices(self, task):
        """Determine resource indices that strictly satisfy task privacy policy and availability."""
        eligible_res = PolicyEngine.get_eligible_resources(task, self.resources)
        eligible_ids = {r["resource_id"] for r in eligible_res}
        indices = [i for i, r in enumerate(self.resources) if r["resource_id"] in eligible_ids]
        # Return strict eligible indices only without fallback to avoid policy violations
        return indices

    # -- core cost model ------------------------------------------------
    def _resource_cost(self, task, resource_index):
        if resource_index == -1 or resource_index >= len(self.resources):
            # Task cannot be scheduled on any eligible resource; severe blocked penalty
            return 50000.0, 99999.0, 99999.0

        res = self.resources[resource_index]
        rid = res["resource_id"]

        # Hard constraint feasibility check via PolicyEngine
        is_valid, _ = PolicyEngine.validate_dispatch(task, rid, self.resources)
        if not is_valid:
            # Severe penalty for hard constraint violation
            return 10000.0, 9999.0, 9999.0

        size_mb = task.get("data_size_mb", 1.0)
        cpu_giga = task.get("cpu_cycles_giga", 0.5)
        deadline_ms = task.get("deadline_ms", 500)
        privacy = task.get("privacy_sensitivity", 0.5)
        security = task.get("security_sensitivity", 0.1)

        latency = res["network_latency_ms"] + cpu_giga * 12.0 / max(
            res["cpu_utilization"], 0.05
        )
        energy = res["energy_rate"] * (cpu_giga / 1.0 + size_mb / 10.0)
        privacy_loss = res["privacy_loss_factor"] * (privacy + 0.1)
        risk = res["security_risk"]

        w = self.weights
        penalty = 0.0
        if deadline_ms and deadline_ms > 0 and latency > deadline_ms:
            penalty = w.get("deadline", 5.0) * 5.0 * (latency / deadline_ms - 1.0)

        fitness = (
            w.get("latency", 0.35) * latency / 1000.0
            + w.get("energy", 0.25) * energy / 20.0
            + w.get("privacy", 0.20) * privacy_loss
            + w.get("security", 0.20) * risk
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
    def _init_population(self, tasks):
        population = []
        n_tasks = len(tasks)
        task_candidates = [self._get_task_eligible_indices(t) for t in tasks]

        for _ in range(self.pop_size):
            chromo = []
            for i in range(n_tasks):
                candidates = task_candidates[i]
                if candidates:
                    chromo.append(self.rng.choice(candidates))
                else:
                    chromo.append(-1)
            population.append(chromo)
        return population, task_candidates

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

    def _mutate(self, chromo, task_candidates):
        out = chromo[:]
        for i in range(len(out)):
            if self.rng.random() < self.mutation_rate:
                candidates = task_candidates[i]
                if candidates:
                    out[i] = self.rng.choice(candidates)
                else:
                    out[i] = -1
        return out

    # -- main loop ---------------------------------------------------------
    def optimize(self, tasks):
        n_tasks = len(tasks)
        if n_tasks == 0:
            return [], [], self.history, self.best_fitness

        population, task_candidates = self._init_population(tasks)
        self.history = []
        self.best_chromosome = None
        self.best_fitness = float("inf")
        self.generations_ran = 0

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
                new_pop.append(self._mutate(c1, task_candidates))
                if len(new_pop) < self.pop_size:
                    new_pop.append(self._mutate(c2, task_candidates))

            population = new_pop

        assignments = []
        for i, gene in enumerate(self.best_chromosome):
            if gene == -1 or gene >= len(self.resource_ids):
                assignments.append("BLOCKED")
            else:
                assignments.append(self.resource_ids[gene])
        return assignments, self.best_chromosome, self.history, self.best_fitness

    def resource_assignment_map(self, tasks):
        """Return a dict {task_id: resource_id} using the best chromosome."""
        if self.best_chromosome is None:
            return {}
        return {
            tasks[i].get("task_id", i): (
                self.resource_ids[g] if 0 <= g < len(self.resource_ids) else "BLOCKED"
            )
            for i, g in enumerate(self.best_chromosome)
        }



if __name__ == "__main__":
    # quick self test with a handful of tasks
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "securedt.settings")
    django.setup()

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
    from engine.scheduler import Scheduler
    sched = Scheduler(twin)
    assignments, metrics, history = sched.proposed_ga_schedule(sample_tasks)
    print("best fitness:", metrics.get("best_fitness"))
    print("history (last 5):", history[-5:])
    print("assignments:", assignments)