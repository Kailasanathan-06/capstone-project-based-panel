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

    def scene(self, request):
        """Read-only topology snapshot assembled from existing SecureDT records."""
        import hashlib
        import json
        import posixpath

        from django.conf import settings
        from django.db.models import Count
        from django.utils import timezone

        from datasets.models import (
            DatasetAnalysisReport,
            DatasetInventoryItem,
            DatasetStorageReplica,
            DatasetUpload,
            SecurityAuditEvent,
            StorageDestination,
        )
        from engine.policy_engine import PolicyEngine
        from mec_manager.models import MECAgent
        from tasks.models import SchedulingDecision, Task

        refresh_mec_status()
        twin = DigitalTwin()
        states = twin.states()
        state_by_id = {r["resource_id"]: r for r in states}
        timeout = getattr(settings, "HEARTBEAT_TIMEOUT_SECONDS", 30)

        resources = []
        for r in states:
            resources.append(
                {
                    "resource_id": r["resource_id"],
                    "resource_type": r["resource_type"],
                    "status": r["status"],
                    "is_online": bool(r["is_online"]),
                    "availability": bool(r["availability"]),
                    "is_stale": bool(r["is_stale"]),
                    "is_simulated": bool(r["is_simulated"]),
                    "telemetry_mode": r["telemetry_mode"],
                    "freshness_seconds": round(r["freshness_seconds"], 1),
                    "cpu_utilization": round(r["cpu_utilization"], 3),
                    "memory_utilization": round(r["memory_utilization"], 3),
                    "network_latency_ms": round(r["network_latency_ms"], 1),
                    "security_risk": round(r["security_risk"], 3),
                    "active_tasks": r["active_tasks"],
                }
            )

        active_counts = {}
        for row in Task.objects.filter(status__in=["ASSIGNED", "RUNNING"]).values_list(
            "assigned_node", flat=True
        ):
            if row:
                active_counts[row] = active_counts.get(row, 0) + 1

        mecs = []
        for agent in MECAgent.objects.all().order_by("device_id"):
            rid = agent.device_id.upper()
            res = state_by_id.get(rid)
            if res:
                freshness = res["freshness_seconds"]
                stale = res["is_stale"]
            else:
                freshness = (
                    (timezone.now() - agent.last_seen).total_seconds()
                    if agent.last_seen
                    else None
                )
                stale = freshness is None or freshness > timeout

            if agent.is_revoked or not agent.is_online or stale:
                connection = "OFFLINE"
            elif not agent.is_approved:
                connection = "CONNECTING"
            else:
                connection = "CONNECTED"

            mecs.append(
                {
                    "device_id": agent.device_id,
                    "connection_state": connection,
                    "eligible": connection == "CONNECTED" and bool(agent.is_approved),
                    "heartbeat_freshness_seconds": round(freshness, 1)
                    if freshness is not None
                    else None,
                    "telemetry_mode": res["telemetry_mode"] if res else "UNKNOWN",
                    "cpu_utilization": res["cpu_utilization"] if res else None,
                    "memory_utilization": res["memory_utilization"] if res else None,
                    "active_tasks": active_counts.get(rid, 0),
                }
            )

        destination_rows = {
            d.destination_id: d for d in StorageDestination.objects.all()
        }
        replica_counts = {
            row["storage_destination__destination_id"]: row["count"]
            for row in DatasetStorageReplica.objects.values(
                "storage_destination__destination_id"
            ).annotate(count=Count("id"))
        }
        inventory_counts = {
            row["selected_destination"]: row["count"]
            for row in DatasetInventoryItem.objects.exclude(
                selected_destination="UNASSIGNED"
            )
            .values("selected_destination")
            .annotate(count=Count("id"))
        }
        tier_task_counts = {
            row["assigned_tier"]: row["count"]
            for row in Task.objects.filter(status__in=["ASSIGNED", "RUNNING"])
            .exclude(assigned_tier="")
            .values("assigned_tier")
            .annotate(count=Count("id"))
        }
        tiers = []
        for key, dest in destination_rows.items():
            tiers.append(
                {
                    "destination_id": key,
                    "destination_type": dest.destination_type,
                    "name": dest.name,
                    "is_emulator": bool(dest.is_emulator),
                    "privacy_tier_allowed": dest.privacy_tier_allowed,
                    "capacity_bytes": dest.capacity_bytes,
                    "used_bytes": dest.used_bytes,
                }
            )

        item_by_name = {}
        for item in DatasetInventoryItem.objects.all().only(
            "relative_path", "privacy_policy", "declared_source"
        ):
            item_by_name[posixpath.basename(item.relative_path)] = item

        known_sources = {r["resource_id"] for r in states} | set(destination_rows)
        transfer_states = {
            "PENDING": "WAITING",
            "COPYING": "TRANSFERRING",
            "VERIFIED": "COMPLETED",
            "FAILED": "FAILED",
            "BLOCKED_BY_POLICY": "BLOCKED",
            "UNAVAILABLE": "FAILED",
        }
        transfers = []
        replicas = DatasetStorageReplica.objects.select_related(
            "storage_destination"
        ).order_by("-created_at")[:12]
        for replica in replicas:
            item = item_by_name.get(posixpath.basename(replica.relative_key))
            policy = item.privacy_policy if item else "UNKNOWN"
            declared = (item.declared_source or "").upper() if item else ""
            source_known = declared in known_sources
            suffix = ""
            if item and getattr(item, "format", ""):
                candidate = "".join(
                    c for c in item.format.lower() if c.isalnum()
                )[:5]
                suffix = f".{candidate}" if candidate else ""
            digest = hashlib.sha256(replica.replica_id.encode("utf-8")).hexdigest()[
                :8
            ].upper()
            transfers.append(
                {
                    "transfer_id": f"DATA-{digest}",
                    "label": f"DATA-{digest}{suffix}",
                    "source": declared if source_known else "SOURCE NOT RECORDED",
                    "source_known": source_known,
                    "destination": replica.storage_destination.destination_id,
                    "state": transfer_states.get(
                        replica.replication_status, "WAITING"
                    ),
                    "privacy_policy": policy,
                    "recorded_at": replica.created_at.isoformat(),
                }
            )

        tasks = []
        for task in Task.objects.order_by("-created_at")[:20]:
            tasks.append(
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "privacy_policy": task.privacy_policy,
                    "assigned_node": task.assigned_node
                    or (task.assigned_mec.device_id if task.assigned_mec else ""),
                    "assigned_tier": task.assigned_tier,
                    "recorded_at": task.created_at.isoformat(),
                }
            )

        decisions = []
        for decision in SchedulingDecision.objects.order_by("-timestamp")[:6]:
            objective = {}
            try:
                parsed = json.loads(decision.objective_scores or "{}")
                if isinstance(parsed, dict):
                    objective = {
                        k: round(float(v), 4)
                        for k, v in parsed.items()
                        if isinstance(v, (int, float)) and not isinstance(v, bool)
                    }
            except (ValueError, TypeError):
                objective = {}
            try:
                rejected = json.loads(decision.rejected_candidates or "[]")
            except (ValueError, TypeError):
                rejected = []
            decisions.append(
                {
                    "task_id": decision.task.task_id,
                    "algorithm": decision.algorithm,
                    "selected_resource": decision.selected_resource,
                    "selected_tier": decision.selected_tier,
                    "objective_scores": objective,
                    "rejected_count": len(rejected) if hasattr(rejected, "__len__") else 0,
                    "recorded_at": decision.timestamp.isoformat(),
                }
            )

        policies = {}
        for policy in ["LOCAL_ONLY", "TRUSTED_EDGE", "CLOUD_ALLOWED"]:
            probe = {
                "privacy_policy": policy,
                "operation": "normalize_clahe",
                "memory_mb": 256,
            }
            eligible = PolicyEngine.get_eligible_resources(probe, states)
            policies[policy] = {
                "allowed_tiers": sorted(
                    {r["resource_type"].upper() for r in eligible}
                ),
                "eligible_resources": [r["resource_id"] for r in eligible],
            }

        events = []
        for event in SecurityAuditEvent.objects.order_by("-timestamp")[:12]:
            events.append(
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "blocked": bool(event.blocked),
                    "verdict": "BLOCKED" if event.blocked else "RECORDED",
                    "task_id": event.task_id,
                    "device_id": event.device_id,
                    "recorded_at": event.timestamp.isoformat(),
                }
            )

        latest_upload_row = DatasetUpload.objects.order_by("-uploaded_at").first()
        latest_report_row = DatasetAnalysisReport.objects.order_by("-created_at").first()
        latest_upload = None
        if latest_upload_row:
            latest_upload = {
                "upload_id": latest_upload_row.upload_id,
                "status": latest_upload_row.status,
                "execution_mode": latest_upload_row.execution_mode,
                "total_files_count": latest_upload_row.total_files_count,
                "total_uncompressed_bytes": latest_upload_row.total_uncompressed_bytes,
                "uploaded_at": latest_upload_row.uploaded_at.isoformat()
                if latest_upload_row.uploaded_at
                else None,
            }
        latest_analysis = None
        if latest_report_row:
            latest_analysis = {
                "report_id": latest_report_row.report_id,
                "created_at": latest_report_row.created_at.isoformat()
                if latest_report_row.created_at
                else None,
                "analysis_duration_ms": round(latest_report_row.analysis_duration_ms, 1),
                "scheduling_duration_ms": round(latest_report_row.scheduling_duration_ms, 1),
                "has_inventory": bool(latest_report_row.inventory_json),
                "has_allocation": bool(latest_report_row.allocation_json),
            }

        has_validation_failure = any(
            e["event_type"] == "ZIP_VALIDATION_ERROR" for e in events
        )
        has_policy_violation = any(
            e["event_type"] == "PRIVACY_POLICY_VIOLATION" for e in events
        )
        completed_tasks = sum(1 for t in tasks if t["status"] in ("COMPLETED", "SUCCEEDED"))
        connected_mecs = sum(
            1 for m in mecs if m["connection_state"] == "CONNECTED"
        )
        server = {
            "id": "CENTRAL",
            "label": "SecureDT Central Server",
            "status": "ONLINE",
            "registered_mecs": len(mecs),
            "connected_mecs": connected_mecs,
            "active_tasks": len(active_counts),
            "active_transfers": sum(
                1
                for t in transfers
                if t["state"] in ("TRANSFERRING", "WAITING")
            ),
        }
        capabilities = {
            "encryption_confirmed": False,
            "policy_enforcement": True,
            "ga_scheduler": True,
            "heartbeat_timeout_seconds": timeout,
            "transfer_progress_available": False,
        }

        def stage(step, stage_id, title, source, destination, status, detail, data_source):
            return {
                "step": step,
                "id": stage_id,
                "title": title,
                "source": source,
                "destination": destination,
                "status": status,
                "detail": detail,
                "data_source": data_source,
            }

        workflow_stages = [
            stage(1, "infrastructure", "Infrastructure Overview", "CENTRAL", "CENTRAL",
                  "AVAILABLE", f"{connected_mecs} connected of {len(mecs)} registered MEC agents.", "BACKEND"),
            stage(2, "dataset_source", "Dataset Source Selection", "CLIENT", "CENTRAL",
                  "AVAILABLE" if latest_upload else "PENDING",
                  f"Latest sanitized upload record: {latest_upload['upload_id']}" if latest_upload
                  else "No dataset upload record yet.", "BACKEND"),
            stage(3, "zip_upload", "ZIP Upload", "CLIENT", "CENTRAL",
                  "AVAILABLE" if latest_upload else "PENDING",
                  f"Latest upload status: {latest_upload['status']} ({latest_upload['execution_mode']})"
                  if latest_upload else "No upload status is recorded yet.", "BACKEND"),
            stage(4, "zip_validation", "Archive Validation", "CENTRAL", "CENTRAL",
                  "BLOCKED" if has_validation_failure else "AVAILABLE" if latest_upload else "PENDING",
                  "A recorded ZIP validation error exists." if has_validation_failure
                  else "Validation is enforced; no recorded failure in recent events."
                  if latest_upload else "No validation result is recorded yet.", "BACKEND"),
            stage(5, "dataset_analysis", "Dataset Analysis", "CENTRAL", "CENTRAL",
                  "AVAILABLE" if latest_analysis else "PENDING",
                  f"Latest report {latest_analysis['report_id']} is available."
                  if latest_analysis else "No analysis report is recorded yet.", "BACKEND"),
            stage(6, "privacy_policy", "Privacy Policy Check", "CENTRAL", "CENTRAL",
                  "AVAILABLE",
                  f"{len(policies)} policies available; "
                  f"{'a policy violation is recorded' if has_policy_violation else 'no recent policy violation recorded'}.",
                  "BACKEND"),
            stage(7, "resource_monitoring", "Digital Twin Resource State", "CENTRAL", "LOCAL",
                  "AVAILABLE", f"{len(resources)} resources report digital-twin state.", "BACKEND"),
            stage(8, "ga_scheduling", "Genetic Algorithm Scheduling", "CENTRAL", "CENTRAL",
                  "AVAILABLE" if decisions else "BACKEND_CAPABILITY",
                  f"{len(decisions)} recorded benchmark decision(s)." if decisions
                  else "GA service is available; normal dispatch decisions are not persisted.", "BACKEND"),
            stage(9, "resource_selection", "Resource Selection", "CENTRAL",
                  decisions[0]["selected_resource"] if decisions else "CENTRAL",
                  "AVAILABLE" if decisions else "PENDING",
                  f"Latest recorded selection: {decisions[0]['selected_resource']}" if decisions
                  else "No recorded selection is available.", "BACKEND"),
            stage(10, "file_transfer", "Data Transfer", "LOCAL", "MEC_STORAGE",
                   "AVAILABLE" if transfers else "PENDING",
                   f"{len(transfers)} recorded transfer state(s)." if transfers
                   else "No replica transfer record is available.", "BACKEND"),
            stage(11, "task_processing", "Task Processing", "CENTRAL", "LOCAL",
                   "AVAILABLE" if tasks else "PENDING",
                   f"{len(tasks)} task record(s); {completed_tasks} complete.", "BACKEND"),
            stage(12, "result_delivery", "Result Delivery", "LOCAL", "CENTRAL",
                   "AVAILABLE" if completed_tasks else "PENDING",
                   f"{completed_tasks} completed task record(s)." if completed_tasks
                   else "No completed task is recorded yet.", "BACKEND"),
            stage(13, "storage_allocation", "Storage Allocation", "CENTRAL", "MEC_STORAGE",
                   "AVAILABLE", f"{len(tiers)} storage tier(s) are configured.", "BACKEND"),
            stage(14, "task_completion", "Task Completion", "CENTRAL", "LOCAL",
                   "AVAILABLE" if completed_tasks else "PENDING",
                   f"{completed_tasks} task(s) reached a completed state." if completed_tasks
                   else "No confirmed task completion is recorded.", "BACKEND"),
            stage(15, "security_audit", "Security Audit Summary", "ATTACKER", "CENTRAL",
                   "AVAILABLE" if events else "PENDING",
                   f"{len(events)} recent audit event(s)." if events
                   else "No recent audit event is recorded.", "BACKEND"),
        ]
        workflow = {
            "live_mode_available": bool(latest_upload or tasks or events),
            "latest_upload": latest_upload,
            "latest_analysis": latest_analysis,
            "stages": workflow_stages,
        }
        security_layers = [
            {
                "id": "upload_validation",
                "label": "Upload Validation",
                "status": "ENFORCED",
                "evidence": "ZIP readability, corruption, path-traversal, executable-extension and archive-size checks.",
            },
            {
                "id": "authentication_authorization",
                "label": "Authentication & Authorization",
                "status": "PARTIAL",
                "evidence": "MEC task and result endpoints require agent authentication; several dashboard APIs are AllowAny.",
            },
            {
                "id": "privacy_aware_scheduling",
                "label": "Privacy-Aware Scheduling",
                "status": "ENFORCED",
                "evidence": "Policy engine screens eligible resources and replication blocks policy violations.",
            },
            {
                "id": "resource_trust_availability",
                "label": "Resource Trust & Availability",
                "status": "ENFORCED",
                "evidence": "MEC approval, revocation and heartbeat staleness determine eligibility.",
            },
            {
                "id": "security_audit",
                "label": "Security Audit",
                "status": "ENFORCED",
                "evidence": "Persistent audit records exist for validation, policy, authentication and task events.",
            },
            {
                "id": "data_protection",
                "label": "Data Protection",
                "status": "POLICY_ONLY",
                "evidence": "Transport encryption is not confirmed; the shield is a policy visualization only.",
            },
        ]
        simulation_catalog = [
            {
                "id": "UNAUTHORIZED_TASK_SUBMISSION",
                "label": "Unauthorized Task Submission",
                "target": "CENTRAL",
                "backend_evidence": "UNAUTHORIZED_TASK_SUBMISSION audit event type exists.",
            },
            {
                "id": "INVALID_MEC_AUTH",
                "label": "Invalid MEC Credentials",
                "target": "MEC",
                "backend_evidence": "INVALID_MEC_AUTH audit event type exists.",
            },
            {
                "id": "ZIP_VALIDATION_ERROR",
                "label": "Invalid ZIP Archive",
                "target": "CENTRAL",
                "backend_evidence": "Archive validation errors are recorded in audit events.",
            },
            {
                "id": "PRIVACY_POLICY_VIOLATION",
                "label": "Privacy Policy Violation",
                "target": "CLOUD",
                "backend_evidence": "Policy engine blocks ineligible destinations.",
            },
            {
                "id": "OFFLINE_MEC_RESOURCE",
                "label": "Offline MEC Resource",
                "target": "MEC",
                "backend_evidence": "Heartbeat staleness and approval state mark MEC resources offline.",
            },
            {
                "id": "TASK_QUEUE_ACCESS",
                "label": "Unauthorized Queue Access",
                "target": "CENTRAL",
                "backend_evidence": "Task queue access control is not confirmed.",
            },
            {
                "id": "REPEATED_SUSPICIOUS_REQUESTS",
                "label": "Repeated Suspicious Requests",
                "target": "CENTRAL",
                "backend_evidence": "Bounded visualization only; no real requests are generated.",
            },
            {
                "id": "TRANSFER_INTERRUPTION",
                "label": "Transfer Interruption",
                "target": "MEC_STORAGE",
                "backend_evidence": "Replica states record FAILED and UNAVAILABLE outcomes.",
            },
        ]
        client_devices = [
            {
                "client_id": "CLIENT-LOCAL",
                "label": "Dataset Submission Client",
                "client_type": "WEB_UPLOAD_CLIENT",
                "is_simulated": False,
                "note": "Logical client represented by the existing web upload interface.",
            }
        ]

        def clean_number(value, default=None):
            try:
                number = float(value)
            except (TypeError, ValueError):
                return default
            if number != number or number in (float("inf"), float("-inf")):
                return default
            return number

        def non_negative_int(value):
            number = clean_number(value)
            if number is None:
                return None
            return max(0, int(number))

        def safe_percent(used, capacity):
            if used is None or capacity is None or capacity <= 0:
                return None
            return round(min(100.0, used * 100.0 / capacity), 1)

        def telemetry_for(resource_id, fallback):
            res = state_by_id.get(resource_id)
            if not res:
                return {
                    "status": "UNKNOWN",
                    "telemetry_mode": fallback,
                    "is_simulated": False,
                    "is_stale": False,
                    "freshness_seconds": None,
                    "cpu_utilization": None,
                    "memory_utilization": None,
                    "network_latency_ms": None,
                    "active_tasks": 0,
                }
            return {
                "status": res["status"],
                "telemetry_mode": res["telemetry_mode"],
                "is_simulated": bool(res["is_simulated"]),
                "is_stale": bool(res["is_stale"]),
                "freshness_seconds": round(res["freshness_seconds"], 1),
                "cpu_utilization": round(res["cpu_utilization"], 3),
                "memory_utilization": round(res["memory_utilization"], 3),
                "network_latency_ms": round(res["network_latency_ms"], 1),
                "active_tasks": res["active_tasks"],
            }

        def storage_detail(node_id, destination_id, label, node_kind, status, resource_id=None):
            dest = destination_rows.get(destination_id)
            used = non_negative_int(dest.used_bytes) if dest else None
            capacity = non_negative_int(dest.capacity_bytes) if dest else None
            free = (
                max(0, capacity - used)
                if used is not None and capacity is not None
                else None
            )
            telemetry = telemetry_for(
                resource_id,
                "SIMULATED_CLOUD" if dest and dest.is_emulator else "CONFIGURED_STORAGE",
            )
            simulated = bool(dest and dest.is_emulator) or bool(telemetry["is_simulated"])
            note = (
                "CLOUD is an emulator; storage figures are SIMULATED STORAGE DATA."
                if simulated
                else "Storage figures are read from configured backend records."
            )
            return {
                "device_id": node_id,
                "label": label,
                "device_type": "STORAGE_TIER",
                "node_kind": node_kind,
                "status": status,
                "telemetry_mode": telemetry["telemetry_mode"],
                "is_simulated": simulated,
                "is_emulator": bool(dest.is_emulator) if dest else False,
                "is_stale": telemetry["is_stale"],
                "freshness_seconds": telemetry["freshness_seconds"],
                "cpu_utilization": telemetry["cpu_utilization"],
                "memory_utilization": telemetry["memory_utilization"],
                "network_latency_ms": telemetry["network_latency_ms"],
                "privacy_tier_allowed": dest.privacy_tier_allowed if dest else "Not available",
                "capacity_bytes": capacity,
                "used_bytes": used,
                "free_bytes": free,
                "utilization_percent": safe_percent(used, capacity),
                "replica_count": replica_counts.get(destination_id, 0),
                "inventory_item_count": inventory_counts.get(destination_id, 0),
                "assigned_task_count": tier_task_counts.get(destination_id, 0),
                "details_note": note,
            }

        device_details = {
            "CENTRAL": {
                "device_id": "CENTRAL",
                "label": server["label"],
                "device_type": "CONTROL_PLANE",
                "node_kind": "central",
                "status": server["status"],
                "telemetry_mode": "BACKEND_SNAPSHOT",
                "is_simulated": False,
                "registered_mecs": server["registered_mecs"],
                "connected_mecs": server["connected_mecs"],
                "active_tasks": server["active_tasks"],
                "active_transfers": server["active_transfers"],
                "policy_enforcement": capabilities["policy_enforcement"],
                "encryption_confirmed": capabilities["encryption_confirmed"],
                "details_note": "Protection policy visualization only; no transport encryption is confirmed by the application.",
            },
            "LOCAL": storage_detail(
                "LOCAL", "LOCAL_STORAGE", "Local Workstation", "local", "ONLINE", "LOCAL"
            ),
            "CLOUD": storage_detail(
                "CLOUD",
                "CLOUD_STORAGE",
                "Cloud Storage Tier",
                "cloud",
                "ONLINE",
                "CLOUD",
            ),
            "MEC_STORAGE": storage_detail(
                "MEC_STORAGE", "MEC_STORAGE", "MEC Storage Tier", "edge-store", "ONLINE"
            ),
        }
        for mec in mecs:
            rid = mec["device_id"]
            res = state_by_id.get(rid.upper())
            device_details[rid] = {
                "device_id": rid,
                "label": rid,
                "device_type": "EDGE_AGENT",
                "node_kind": "mec",
                "status": mec["connection_state"],
                "telemetry_mode": mec["telemetry_mode"],
                "is_simulated": False,
                "is_stale": bool(res and res["is_stale"]),
                "freshness_seconds": mec["heartbeat_freshness_seconds"],
                "cpu_utilization": mec["cpu_utilization"],
                "memory_utilization": mec["memory_utilization"],
                "network_latency_ms": res["network_latency_ms"] if res else None,
                "active_tasks": mec["active_tasks"],
                "shared_storage_tier_id": "MEC_STORAGE",
                "storage_is_shared": True,
                "details_note": "Storage is reported at the shared MEC_STORAGE tier, not for this individual agent.",
            }
        device_details["ATTACKER"] = {
            "device_id": "ATTACKER",
            "label": "Simulated Attacker",
            "device_type": "SIMULATION",
            "node_kind": "attacker",
            "status": "SIMULATED",
            "telemetry_mode": "LOCAL_SIMULATION",
            "is_simulated": True,
            "details_note": "This node exists only for labeled defensive attack simulations; no real host is represented.",
        }

        return Response(
            {
                "mode": "live",
                "generated_at": timezone.now().isoformat(),
                "server": server,
                "resources": resources,
                "mec_devices": mecs,
                "tiers": tiers,
                "transfers": transfers,
                "tasks": tasks,
                "scheduling": {
                    "decisions": decisions,
                    "decision_source": "recorded SchedulingDecision records",
                },
                "security_events": events,
                "policies": policies,
                "capabilities": capabilities,
                "device_details": device_details,
                "workflow": workflow,
                "security_layers": security_layers,
                "simulation_catalog": simulation_catalog,
                "client_devices": client_devices,
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