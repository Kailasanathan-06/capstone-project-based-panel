"""
Tasks - scheduling service.

Dispatches QUEUED tasks to eligible execution tiers (LOCAL workstation,
ONLINE non-revoked MEC devices, or CLOUD tier) strictly enforcing privacy
policies (LOCAL_ONLY, TRUSTED_EDGE, CLOUD_ALLOWED) via the Genetic Algorithm.
"""

import os
import time
import hashlib
import logging

from .models import Task
from engine.policy_engine import PolicyEngine

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
        "privacy_policy": getattr(task, "privacy_policy", "TRUSTED_EDGE"),
        "operation": getattr(task, "operation", "normalize_clahe"),
        "image_path": getattr(task, "image_path", ""),
        "target_resolution": getattr(task, "target_resolution", 224),
    }


def eligible_mec_resources():
    """
    Build the GA resource list from officially ONLINE, non-revoked MEC devices.
    OFFLINE or REVOKED devices are NEVER included.
    Preserved for backward compatibility with MEC-specific queries.
    """
    from engine.digital_twin import DigitalTwin
    from mec_manager.models import MECAgent

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
    return [s for s in states if s["resource_id"].startswith("MEC-") and s["resource_id"] in online_ids]


def execute_task_locally(task):
    """
    Execute task locally on hospital workstation with high-resolution timing and verification.
    Uses MedicalImageProcessor for genuine medical image operations.
    """
    from engine.image_processor import MedicalImageProcessor

    try:
        import psutil
        cpu_start = psutil.cpu_percent(interval=None)
        ram_start = psutil.virtual_memory().percent
    except Exception:
        cpu_start = 15.0
        ram_start = 25.0

    task.status = "RUNNING"
    task.assigned_node = "LOCAL"
    task.assigned_tier = "LOCAL"
    task.save(update_fields=["status", "assigned_node", "assigned_tier", "updated_at"])
    task.record_history("ASSIGNED", "RUNNING", changed_by="local_executor")

    start_mono = time.perf_counter()
    image_path = getattr(task, "image_path", "")

    try:
        if image_path and os.path.exists(image_path):
            processor = MedicalImageProcessor()
            op = getattr(task, "operation", "normalize_clahe") or "normalize_clahe"
            res = getattr(task, "target_resolution", 224) or 224
            proc_out = processor.process(image_path=image_path, operation=op, target_resolution=res)

            task.execution_time = proc_out["processing_time_s"]
            task.image_processing_time = proc_out["processing_time_s"]
            task.total_latency_ms = round(proc_out["processing_time_s"] * 1000.0, 2)
            task.output_path = proc_out["output_path"]
            task.input_checksum = proc_out["input_checksum"]
            task.output_checksum = proc_out["output_checksum"]
            task.result_location = proc_out["output_path"]
        else:
            # Genuine cryptographic benchmark computation
            cpu_cycles = float(task.cpu_cycles_giga or 0.5)
            rounds = int(max(10000, min(500000, cpu_cycles * 150000)))
            buf = b"SecureDT_Workstation_Local_Execution" * 64
            h = hashlib.sha256()
            for _ in range(rounds):
                h.update(buf)
            exec_time = time.perf_counter() - start_mono
            task.execution_time = round(exec_time, 4)
            task.total_latency_ms = round(exec_time * 1000.0, 2)
            task.result_location = f"results/{task.task_id}_{h.hexdigest()[:10]}.bin"

        try:
            import psutil
            task.actual_cpu = round(psutil.cpu_percent(interval=None), 2)
            task.actual_ram = round(psutil.virtual_memory().percent, 2)
        except Exception:
            task.actual_cpu = cpu_start
            task.actual_ram = ram_start

        task.network_latency = 0.5
        task.estimated_energy = round((task.execution_time or 0.1) * 0.05, 4)
        task.status = "COMPLETED"
        task.is_simulated_execution = False
        task.save()
        task.record_history("RUNNING", "COMPLETED", changed_by="local_executor")
        return True, "Executed successfully on LOCAL workstation."
    except Exception as e:
        task.status = "FAILED"
        task.error_message = str(e)
        task.save(update_fields=["status", "error_message", "updated_at"])
        task.record_history("RUNNING", "FAILED", changed_by="local_executor")
        return False, str(e)


def execute_task_cloud_simulation(task, cloud_res=None):
    """
    Execute CLOUD_ALLOWED task via explicitly labeled simulated Cloud tier.
    """
    from engine.image_processor import MedicalImageProcessor

    task.status = "RUNNING"
    task.assigned_node = "CLOUD"
    task.assigned_tier = "CLOUD"
    task.execute_in_cloud = True
    task.is_simulated_execution = True
    task.save(
        update_fields=[
            "status",
            "assigned_node",
            "assigned_tier",
            "execute_in_cloud",
            "is_simulated_execution",
            "updated_at",
        ]
    )
    task.record_history("ASSIGNED", "RUNNING", changed_by="cloud_simulator")

    start_mono = time.perf_counter()
    image_path = getattr(task, "image_path", "")

    try:
        base_cloud_latency = (cloud_res.get("network_latency_ms") if cloud_res else 170.0) or 170.0
        if image_path and os.path.exists(image_path):
            processor = MedicalImageProcessor()
            op = getattr(task, "operation", "normalize_clahe") or "normalize_clahe"
            res = getattr(task, "target_resolution", 224) or 224
            proc_out = processor.process(image_path=image_path, operation=op, target_resolution=res)

            task.execution_time = proc_out["processing_time_s"]
            task.image_processing_time = proc_out["processing_time_s"]
            task.total_latency_ms = round((proc_out["processing_time_s"] * 1000.0) + base_cloud_latency, 2)
            task.output_path = proc_out["output_path"]
            task.input_checksum = proc_out["input_checksum"]
            task.output_checksum = proc_out["output_checksum"]
            task.result_location = proc_out["output_path"]
        else:
            cpu_cycles = float(task.cpu_cycles_giga or 0.5)
            exec_time = max(0.05, cpu_cycles * 0.15)
            task.execution_time = round(exec_time, 4)
            task.total_latency_ms = round((exec_time * 1000.0) + base_cloud_latency, 2)
            task.result_location = f"cloud_results/{task.task_id}_cloud.bin"

        task.actual_cpu = 45.0
        task.actual_ram = 50.0
        task.network_latency = base_cloud_latency
        task.estimated_energy = round((task.execution_time or 0.1) * 0.18, 4)
        task.status = "COMPLETED"
        task.save()
        task.record_history("RUNNING", "COMPLETED", changed_by="cloud_simulator")
        return True, "Simulated on CLOUD tier."
    except Exception as e:
        task.status = "FAILED"
        task.error_message = str(e)
        task.save(update_fields=["status", "error_message", "updated_at"])
        task.record_history("RUNNING", "FAILED", changed_by="cloud_simulator")
        return False, str(e)


def run_ga_dispatch(population=40, generations=30, algorithm="proposed_ga", seed=None):
    """
    Dispatch all QUEUED and PENDING tasks across eligible tiers (LOCAL, MEC, CLOUD)
    using the security-aware Genetic Algorithm while strictly enforcing privacy policies.
    """
    from engine.scheduler import Scheduler
    from engine.digital_twin import DigitalTwin
    from mec_manager.models import MECAgent

    tasks = list(Task.objects.filter(status__in=["PENDING", "QUEUED"]).order_by("priority", "created_at"))
    if not tasks:
        return {"dispatched": 0, "message": "no queued tasks", "assignments": [], "metrics": None}

    twin = DigitalTwin()
    all_states = twin.states()

    # Verify at least one resource is available
    available_states = [s for s in all_states if s.get("availability", True) and not s.get("is_stale", False)]
    if not available_states:
        return {
            "dispatched": 0,
            "message": "no online or active resources available in Digital Twin",
            "assignments": [],
            "metrics": None,
        }

    task_dicts = [build_task_dict(t) for t in tasks]
    scheduler = Scheduler(twin, seed=seed)

    if algorithm == "round_robin":
        assignments, metrics = scheduler.round_robin_schedule(task_dicts)
        history = []
        best_fitness = 0.0
    elif algorithm == "first_fit":
        assignments, metrics = scheduler.first_fit_schedule(task_dicts)
        history = []
        best_fitness = 0.0
    elif algorithm == "random":
        assignments, metrics = scheduler.random_schedule(task_dicts, seed=seed)
        history = []
        best_fitness = 0.0
    elif algorithm == "greedy":
        assignments, metrics = scheduler.greedy_schedule(task_dicts)
        history = []
        best_fitness = 0.0
    elif algorithm == "privacy_aware":
        assignments, metrics = scheduler.privacy_aware_schedule(task_dicts)
        history = []
        best_fitness = 0.0
    else:
        # Default: proposed_ga
        assignments, metrics, history = scheduler.proposed_ga_schedule(
            task_dicts, population=population, generations=generations, seed=seed
        )
        best_fitness = metrics.get("best_fitness", 0.0)

    cloud_state = next((s for s in all_states if s["resource_id"] == "CLOUD"), None)
    results = []

    for task, task_dict, target_rid in zip(tasks, task_dicts, assignments):
        if target_rid == "BLOCKED" or not target_rid:
            task.status = "BLOCKED"
            task.error_message = "No eligible resource satisfies privacy or capacity policy."
            task.save(update_fields=["status", "error_message", "updated_at"])
            task.record_history("QUEUED", "BLOCKED", changed_by=f"{algorithm}_scheduler")
            results.append({"task_id": task.task_id, "node_id": "NONE", "tier": "NONE", "status": "BLOCKED"})
            continue

        # Enforce hard dispatch constraint validation
        is_valid, reason = PolicyEngine.validate_dispatch(task_dict, target_rid, all_states)
        if not is_valid:
            logger.warning(f"Task {task.task_id} rejected dispatch to {target_rid}: {reason}")
            task.status = "REJECTED"
            task.error_message = reason
            task.save(update_fields=["status", "error_message", "updated_at"])
            task.record_history("QUEUED", "REJECTED", changed_by=f"{algorithm}_scheduler")
            results.append({"task_id": task.task_id, "node_id": target_rid, "tier": "NONE", "status": "REJECTED"})
            continue

        rid_upper = target_rid.upper()

        if rid_upper == "LOCAL":
            task.assigned_node = "LOCAL"
            task.assigned_tier = "LOCAL"
            task.assigned_mec = None
            task.scheduler_algorithm = algorithm
            task.save(update_fields=["assigned_node", "assigned_tier", "assigned_mec", "scheduler_algorithm", "updated_at"])
            task.record_history("QUEUED", "ASSIGNED", changed_by=f"{algorithm}_scheduler")
            execute_task_locally(task)
            results.append({"task_id": task.task_id, "node_id": "LOCAL", "tier": "LOCAL", "status": task.status})

        elif rid_upper.startswith("MEC-"):
            try:
                mec = MECAgent.objects.get(device_id=rid_upper)
            except MECAgent.DoesNotExist:
                continue
            if not mec.is_eligible:
                continue

            task.assigned_mec = mec
            task.assigned_node = mec.device_id
            task.assigned_tier = "MEC"
            task.status = "ASSIGNED"
            task.scheduler_algorithm = algorithm
            task.save(update_fields=["assigned_mec", "assigned_node", "assigned_tier", "status", "scheduler_algorithm", "updated_at"])
            task.record_history("QUEUED", "ASSIGNED", changed_by=f"{algorithm}_scheduler")
            results.append({"task_id": task.task_id, "node_id": mec.device_id, "tier": "MEC", "status": "ASSIGNED"})

        elif rid_upper == "CLOUD":
            task.assigned_node = "CLOUD"
            task.assigned_tier = "CLOUD"
            task.assigned_mec = None
            task.scheduler_algorithm = algorithm
            task.save(update_fields=["assigned_node", "assigned_tier", "assigned_mec", "scheduler_algorithm", "updated_at"])
            task.record_history("QUEUED", "ASSIGNED", changed_by=f"{algorithm}_scheduler")
            execute_task_cloud_simulation(task, cloud_state)
            results.append({"task_id": task.task_id, "node_id": "CLOUD", "tier": "CLOUD", "status": task.status})

    metrics["dispatched"] = len(results)
    return {
        "dispatched": len(results),
        "message": f"Tasks dispatched using {algorithm}",
        "assignments": results,
        "metrics": metrics,
    }


def requeue_tasks_with_offline_agents():
    """Central helper used by heartbeat processing and API calls."""
    requeued = 0
    for task in Task.objects.filter(status__in=["ASSIGNED", "RUNNING"], assigned_mec__isnull=False):
        if task.requeue_if_offline():
            requeued += 1
    return requeued