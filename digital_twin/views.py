import csv
import io
from datetime import datetime, timezone
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from engine.digital_twin import DigitalTwin
from engine.scheduler import Scheduler
from engine.storage_simulator import StorageSimulator
from engine.security_monitor import SecurityMonitor
from mec_manager.services import refresh_mec_status
from tasks.services import run_ga_dispatch, build_task_dict
from datasets.models import MedicalDatasetSample
from tasks.models import Task


class DigitalTwinViewSet(viewsets.ViewSet):
    """Digital Twin state and interaction endpoints."""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [AllowAny]

    def list(self, request):
        refresh_mec_status()
        twin = DigitalTwin()
        snapshot = twin.snapshot()
        snapshot["online_mecs"] = sum(
            1 for r in snapshot["resources"] if r["resource_id"].startswith("MEC-") and r["availability"]
        )
        snapshot["offline_mecs"] = len(
            [r for r in snapshot["resources"] if r["resource_id"].startswith("MEC-") and not r["availability"]]
        )
        return Response(snapshot)

    def resources(self, request):
        refresh_mec_status()
        return Response(DigitalTwin().states())

    def attack(self, request):
        """Simulate an attack on a virtual resource (never affects real hosts)."""
        resource_id = request.data.get("resource_id")
        attack_type = request.data.get("attack_type", "DDoS")
        severity = float(request.data.get("severity", 0.5))
        twin = DigitalTwin()
        result = twin.apply_attack(resource_id, attack_type, severity)
        if not result.get("applied"):
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)

    def mitigate(self, request):
        """Quarantine a virtual resource (simulated)."""
        resource_id = request.data.get("resource_id")
        twin = DigitalTwin()
        result = twin.quarantine(resource_id)
        if not result:
            return Response({"error": "Resource not found"}, status=404)
        return Response(result)

    def unquarantine(self, request):
        resource_id = request.data.get("resource_id")
        twin = DigitalTwin()
        result = twin.unquarantine(resource_id)
        if not result:
            return Response({"error": "Resource not found"}, status=404)
        return Response(result)

    def schedule(self, request):
        """Run the GA scheduler against queued tasks (DB-backed)."""
        result = run_ga_dispatch(
            population=int(request.data.get("population", 40)),
            generations=int(request.data.get("generations", 30)),
        )
        return Response(result)

    def storage_status(self, request):
        """Virtual storage lab status (simulation)."""
        sim = StorageSimulator()
        return Response(sim.status())

    def storage_attack(self, request):
        """Simulate an attack on virtual storage (never touches real disks)."""
        sim = StorageSimulator()
        storage_id = str(request.data.get("storage_id", "STORAGE-A")).upper()
        severity = min(1.0, max(0.0, float(request.data.get("severity", 0.5))))
        result = sim.attack(storage_id, severity)
        return Response(result)

    def storage_recover(self, request):
        sim = StorageSimulator()
        storage_id = str(request.data.get("storage_id", "STORAGE-A")).upper()
        stor = sim.storages.get(storage_id)
        if not stor:
            return Response({"ok": False, "message": "Unknown storage target"}, status=400)
        result = stor.recover()
        result["ok"] = True
        return Response(result)

    def security(self, request):
        """Live security posture built from the real digital twin + DB."""
        refresh_mec_status()
        twin = DigitalTwin()
        from engine.attack_simulator import AttackSimulator

        monitor = SecurityMonitor()
        overview = monitor.overview(twin, AttackSimulator(twin))
        states = twin.states()
        risk = max((s.get("security_risk", 0) for s in states), default=0.0)
        enriched = []
        for s in states:
            s = dict(s)
            s["risk_label"] = (
                "CRITICAL" if risk >= 0.8 else "HIGH" if risk >= 0.6 else "MEDIUM" if risk >= 0.3 else "LOW"
            )
            enriched.append(s)

        alerts = list(monitor.get_alerts(limit=50))
        try:
            from datasets.models import SecurityAuditEvent
            for ev in SecurityAuditEvent.objects.order_by("-timestamp")[:50]:
                alerts.append({
                    "timestamp": ev.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "kind": ev.event_type,
                    "severity": ev.severity.lower(),
                    "resource": ev.task_id or ev.source_ip or "STORAGE",
                    "message": f"[{ev.event_type}] {ev.description} (Blocked: {ev.blocked})",
                })
            alerts.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
        except Exception:
            pass

        return Response(
            {
                "overview": overview,
                "threat_level": monitor.threat_level(twin),
                "max_risk": round(risk, 3),
                "alerts": alerts,
                "resources": enriched,
            }
        )

    def _generate_benchmark_tasks(self, count=12, seed=42):
        """Generate deterministic medical-image benchmark workload using MedMNIST PneumoniaMNIST samples."""
        import random
        rng = random.Random(seed)
        samples = list(MedicalDatasetSample.objects.all()[:count])

        policies = ["LOCAL_ONLY", "TRUSTED_EDGE", "CLOUD_ALLOWED"]
        tasks = []
        for i in range(count):
            sample = samples[i % len(samples)] if samples else None
            policy = policies[i % 3]

            if policy == "LOCAL_ONLY":
                privacy_sens = 0.90
                sec_sens = 0.70
                data_size = 1.2
                cpu_giga = 0.8
                deadline = 350
                op = "normalize_clahe"
            elif policy == "TRUSTED_EDGE":
                privacy_sens = 0.50
                sec_sens = 0.40
                data_size = 0.8
                cpu_giga = 0.5
                deadline = 280
                op = "normalize_clahe"
            else:  # CLOUD_ALLOWED
                privacy_sens = 0.15
                sec_sens = 0.20
                data_size = 0.5
                cpu_giga = 0.3
                deadline = 420
                op = "grayscale_resize"

            task_id = f"EXP-{1001 + i}"
            sample_id = sample.sample_id if sample else f"SYN-MED-{1000 + i}"
            image_path = sample.image_file_path if sample else ""

            tasks.append({
                "task_id": task_id,
                "name": f"PneumoniaMNIST-{policy}-{i+1}",
                "dataset_sample_id": sample_id,
                "image_path": image_path,
                "operation": op,
                "target_resolution": 224,
                "data_size_mb": data_size,
                "cpu_cycles_giga": cpu_giga,
                "memory_mb": 256,
                "deadline_ms": deadline,
                "privacy_policy": policy,
                "privacy_sensitivity": privacy_sens,
                "security_sensitivity": sec_sens,
            })
        return tasks

    def compare(self, request):
        """
        Compare Proposed Genetic Algorithm vs Baselines (Round Robin, First Fit, Random, Greedy, Privacy Aware).
        Evaluates on identical workload respecting privacy policies and online resource constraints.
        """
        refresh_mec_status()
        twin = DigitalTwin()

        # Handle parameters from query params or POST json body
        data = request.data if request.method == "POST" else request.query_params
        try:
            tasks_count = max(3, min(100, int(data.get("tasks_count", 12))))
        except (ValueError, TypeError):
            tasks_count = 12

        try:
            population = max(10, min(200, int(data.get("population", 40))))
        except (ValueError, TypeError):
            population = 40

        try:
            generations = max(5, min(150, int(data.get("generations", 30))))
        except (ValueError, TypeError):
            generations = 30

        try:
            seed = int(data.get("seed", 42))
        except (ValueError, TypeError):
            seed = 42

        use_queued = str(data.get("use_queued", "false")).lower() in ("true", "1")

        if use_queued:
            queued_tasks = list(Task.objects.filter(status__in=["PENDING", "QUEUED"]).order_by("priority", "created_at"))
            if queued_tasks:
                tasks = [build_task_dict(t) for t in queued_tasks[:tasks_count]]
            else:
                tasks = self._generate_benchmark_tasks(count=tasks_count, seed=seed)
        else:
            tasks = self._generate_benchmark_tasks(count=tasks_count, seed=seed)

        scheduler = Scheduler(twin, seed=seed)
        all_results = scheduler.run_all_baselines(
            tasks,
            ga_population=population,
            ga_generations=generations,
            seed=seed,
        )

        # Build clean summary
        summary = {
            "metadata": {
                "tasks_count": len(tasks),
                "population": population,
                "generations": generations,
                "seed": seed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "available_resources": [r["resource_id"] for r in twin.states() if r.get("availability", True)],
            },
            "algorithms": all_results,
            "tasks": tasks,
        }
        return Response(summary)

    def export_experiments_csv(self, request):
        """Export comprehensive scheduler comparison metrics as downloadable CSV."""
        refresh_mec_status()
        twin = DigitalTwin()

        data = request.data if request.method == "POST" else request.query_params
        try:
            tasks_count = max(3, min(100, int(data.get("tasks_count", 12))))
        except (ValueError, TypeError):
            tasks_count = 12
        try:
            population = max(10, min(200, int(data.get("population", 40))))
        except (ValueError, TypeError):
            population = 40
        try:
            generations = max(5, min(150, int(data.get("generations", 30))))
        except (ValueError, TypeError):
            generations = 30
        try:
            seed = int(data.get("seed", 42))
        except (ValueError, TypeError):
            seed = 42

        tasks = self._generate_benchmark_tasks(count=tasks_count, seed=seed)
        scheduler = Scheduler(twin, seed=seed)
        all_results = scheduler.run_all_baselines(
            tasks,
            ga_population=population,
            ga_generations=generations,
            seed=seed,
        )

        output = io.StringIO()
        writer = csv.writer(output)

        # Header for algorithm-level benchmark comparison
        writer.writerow([
            "Algorithm",
            "Avg_Latency_ms",
            "Median_Latency_ms",
            "P95_Latency_ms",
            "Deadline_Success_Rate",
            "Deadline_Miss_Rate",
            "Total_Energy_J",
            "Avg_Energy_J",
            "Privacy_Score",
            "Security_Score",
            "Policy_Violations",
            "Policy_Compliance_Rate",
            "Tasks_Count",
            "Random_Seed",
            "Timestamp"
        ])

        now_ts = datetime.now(timezone.utc).isoformat()
        for algo_name, data_item in all_results.items():
            m = data_item["metrics"]
            writer.writerow([
                algo_name,
                m.get("avg_latency_ms", 0.0),
                m.get("median_latency_ms", 0.0),
                m.get("p95_latency_ms", 0.0),
                m.get("deadline_success", 0.0),
                m.get("deadline_miss_rate", 0.0),
                m.get("total_energy_j", 0.0),
                m.get("avg_energy_j", 0.0),
                m.get("privacy_score", 0.0),
                m.get("security_score", 0.0),
                m.get("policy_violations", 0),
                m.get("policy_compliance_rate", 1.0),
                len(tasks),
                seed,
                now_ts
            ])

        # Blank line and second table: per-task assignment breakdown
        writer.writerow([])
        writer.writerow(["Task_ID", "Privacy_Policy", "Algorithm", "Assigned_Resource", "Operation"])
        for i, t in enumerate(tasks):
            tid = t.get("task_id", f"T-{i}")
            pol = t.get("privacy_policy", "TRUSTED_EDGE")
            op = t.get("operation", "normalize_clahe")
            for algo_name, data_item in all_results.items():
                assigned_rid = data_item["assignments"][i] if i < len(data_item["assignments"]) else "N/A"
                writer.writerow([tid, pol, algo_name, assigned_rid, op])

        response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="secure_dt_scheduling_benchmarks_seed_{seed}.csv"'
        return response