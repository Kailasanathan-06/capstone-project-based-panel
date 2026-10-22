"""
Management command to run the multi-algorithm comparative scheduler benchmark on hospital workloads.
"""

from django.core.management.base import BaseCommand
from engine.benchmark_runner import run_hospital_benchmark, export_benchmark_csv


class Command(BaseCommand):
    help = "Run comparative scheduling benchmark across hospital workloads and export results to CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tasks-count",
            type=int,
            default=14,
            help="Number of hospital workload tasks to evaluate (default: 14)",
        )
        parser.add_argument(
            "--population",
            type=int,
            default=30,
            help="Genetic Algorithm population size (default: 30)",
        )
        parser.add_argument(
            "--generations",
            type=int,
            default=20,
            help="Genetic Algorithm generation count (default: 20)",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for reproducibility (default: 42)",
        )
        parser.add_argument(
            "--export-csv",
            type=str,
            default="",
            help="Custom output path for exported CSV benchmark results",
        )

    def handle(self, *args, **options):
        tasks_count = options.get("tasks_count", 14)
        population = options.get("population", 30)
        generations = options.get("generations", 20)
        seed = options.get("seed", 42)
        csv_out = options.get("export_csv", "")

        self.stdout.write(self.style.MIGRATE_HEADING("=== RUNNING HOSPITAL SCHEDULER COMPARATIVE BENCHMARK ==="))
        self.stdout.write(f"Evaluating {tasks_count} tasks | GA Pop: {population}, Gen: {generations} | Seed: {seed}\n")

        result = run_hospital_benchmark(
            tasks_count=tasks_count,
            population=population,
            generations=generations,
            seed=seed,
            record_decisions=True,
        )

        csv_path = export_benchmark_csv(result, output_path=csv_out or None)

        self.stdout.write(self.style.MIGRATE_HEADING("=== SCHEDULER COMPARISON SUMMARY ==="))
        headers = f"{'Algorithm':<16} | {'Avg Latency':<12} | {'Avg Energy':<12} | {'Miss Rate':<10} | {'Policy Violations':<18} | {'Blocked'}"
        self.stdout.write(headers)
        self.stdout.write("-" * len(headers))

        for algo, m in result["summary"].items():
            lat = f"{m.get('avg_latency_ms', 0):.2f} ms"
            eng = f"{m.get('avg_energy_j', 0):.3f} J"
            miss = f"{m.get('deadline_miss_rate', 0) * 100:.1f} %"
            viols = str(m.get('policy_violations', 0))
            blkd = str(m.get('blocked_tasks', 0))
            self.stdout.write(f"{algo:<16} | {lat:<12} | {eng:<12} | {miss:<10} | {viols:<18} | {blkd}")

        self.stdout.write(self.style.SUCCESS(f"\n[OK] Benchmark Experiment ID: {result['experiment_id']}"))
        self.stdout.write(self.style.SUCCESS(f"[OK] CSV Export generated at: {csv_path}\n"))
