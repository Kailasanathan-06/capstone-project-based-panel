"""
Digital Twin API - Views.

The digital twin is a live virtual mirror of the real registered MEC devices.
It reflects actual database state (online/offline, telemetry) and drives the
security-aware GA scheduler.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from engine.digital_twin import DigitalTwin
from engine.scheduler import Scheduler
from engine.storage_simulator import StorageSimulator
from engine.security_monitor import SecurityMonitor
from mec_manager.services import refresh_mec_status
from tasks.services import run_ga_dispatch


class DigitalTwinViewSet(viewsets.ViewSet):
    """Digital Twin state and interaction endpoints."""

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

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
        return Response(
            {
                "overview": overview,
                "threat_level": monitor.threat_level(twin),
                "max_risk": round(risk, 3),
                "alerts": monitor.get_alerts(limit=100),
                "resources": enriched,
            }
        )

    def compare(self, request):
        """Compare GA vs baseline schedulers on the current twin state."""
        twin = DigitalTwin()
        scheduler = Scheduler(twin)
        states = [s for s in twin.states() if s["resource_id"].startswith("MEC-")]

        sample_tasks = [
            {
                "task_id": "SMP-1",
                "name": "sample-latency",
                "data_size_mb": 120,
                "cpu_cycles_giga": 2.4,
                "memory_mb": 512,
                "deadline_ms": 4200,
                "privacy_sensitivity": 0.4,
                "security_sensitivity": 0.3,
            },
            {
                "task_id": "SMP-2",
                "name": "sample-privacy",
                "data_size_mb": 60,
                "cpu_cycles_giga": 1.2,
                "memory_mb": 256,
                "deadline_ms": 3000,
                "privacy_sensitivity": 0.9,
                "security_sensitivity": 0.7,
            },
            {
                "task_id": "SMP-3",
                "name": "sample-burst",
                "data_size_mb": 400,
                "cpu_cycles_giga": 6.0,
                "memory_mb": 2048,
                "deadline_ms": 9000,
                "privacy_sensitivity": 0.2,
                "security_sensitivity": 0.5,
            },
        ]
        if twin:
            # Keep the comparison honest: use whichever MEC resources exist.
            pass
        history = scheduler.run_all_baselines(sample_tasks, ga_population=40, ga_generations=25)
        simplified = {
            algo: {"algorithm": v["metrics"]["algorithm"], "metrics": v["metrics"]}
            for algo, v in history.items()
        }
        return Response(simplified)