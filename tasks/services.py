"""
Tasks - scheduling service.

Dispatches QUEUED tasks to ONLINE, non-revoked MEC devices using the
security-aware Genetic Algorithm. Offline devices are never candidates.
"""

import logging

from .models import Task

logger = logging.getLogger(__name__)


def build_task_dict(task):
    return {
        "task_id": task.task_id,
        "name": task.name,
        "priority": task.priority,
        "data_size_mb": task.data_size_mb,
        "cpu_cycles_giga": task.cpu_cycles_giga,
        "memory_mb": task.memory_mb,
        "deadline_ms": task.deadline_ms,
        "privacy_sensitivity": task.privacy_sensitivity,
        "security_sensitivity": task.security_sensitivity,
    }


def eligible_mec_resources():
    """
    Build the GA resource list from officially ONLINE, non-revoked MEC devices.
    OFFLINE or REVOKED devices are NEVER included.
    """
    from engine.digital_twin import DigitalTwin
    from mec_manager.models import MECAgent

    # Wrap task requeue for any device that dropped offline before processing.
    online_ids = set(
        MECAgent.objects.filter(is_online=True, is_revoked=False).values_list(
            "device_id", flat=True
        )
    )
    for task in Task.objects.filter(status__in=["ASSIGNED"], assigned_mec__isnull=False):
        if task.assigned_mec and not task.assigned_mec.is_eligible:
            previous = task.status
            task.status = "QUEUED"
            task.assigned_mec = None
            task.save(update_fields=["status", "assigned_mec", "updated_at"])
            task.record_history(previous, "QUEUED", changed_by="auto_offline")

    twin = DigitalTwin()
    states = twin.states()
    # Keep ONLY genuine MEC-XXX resources that correspond to online devices.
    return [s for s in states if s["resource_id"].startswith("MEC-") and s["resource_id"] in online_ids]


def run_ga_dispatch(population=40, generations=30):
    """
    Dispatch all QUEUED and PENDING tasks to eligible online MECs.

    Returns a summary dict with assignments and GA metrics, or an error dict.
    """
    from engine.scheduler import Scheduler
    from engine.digital_twin import DigitalTwin

    tasks = list(Task.objects.filter(status__in=["PENDING", "QUEUED"]).order_by("priority", "created_at"))
    if not tasks:
        return {"dispatched": 0, "message": "no queued tasks", "assignments": [], "metrics": None}

    resources = eligible_mec_resources()
    if not resources:
        # No ONLINE eligible MEC -> tasks must stay queued (never sent offline).
        return {
            "dispatched": 0,
            "message": "no online MEC is available; tasks kept in queue",
            "assignments": [],
            "metrics": None,
        }

    from engine.scheduler import Scheduler
    from engine.digital_twin import DigitalTwin
    from engine.genetic_algorithm import GeneticAlgorithm

    task_dicts = [build_task_dict(t) for t in tasks]
    ga = GeneticAlgorithm(
        resources,
        population=population,
        generations=generations,
    )
    assignments, _, history, best_fitness = ga.optimize(task_dicts)

    twin = DigitalTwin()
    scheduler = Scheduler(twin)
    metrics = scheduler._evaluate_solution(assignments, task_dicts, resources)
    metrics["algorithm"] = "proposed_ga"
    metrics["best_fitness"] = round(best_fitness, 4)
    metrics["resource_utilization"] = None  # sanitized for the API

    results = []
    for task, resource_id in zip(tasks, assignments):
        from mec_manager.models import MECAgent

        try:
            mec = MECAgent.objects.get(device_id=resource_id)
        except MECAgent.DoesNotExist:
            continue
        if not mec.is_eligible:
            continue
        task.assigned_mec = mec
        task.status = "ASSIGNED"
        task.save(update_fields=["assigned_mec", "status", "updated_at"])
        task.record_history("QUEUED", "ASSIGNED", changed_by="ga_scheduler")
        results.append({"task_id": task.task_id, "mec_id": mec.device_id})

    metrics["dispatched"] = len(results)
    return {"dispatched": len(results), "message": "tasks dispatched", "assignments": results, "metrics": metrics}


def requeue_tasks_with_offline_agents():
    """Central helper used by heartbeat processing and API calls."""
    requeued = 0
    for task in Task.objects.filter(status__in=["ASSIGNED", "RUNNING"], assigned_mec__isnull=False):
        if task.requeue_if_offline():
            requeued += 1
    return requeued