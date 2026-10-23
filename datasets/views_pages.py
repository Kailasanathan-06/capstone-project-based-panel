"""
Dedicated Views & API Endpoints for SecureDT Redesigned Pages:
- Page A: Dashboard
- Page B: Upload Dataset
- Page C: Digital Twin
- Page D: Storage Allocation
- Page E: Dataset Reports
- Page F: Report Details & CSV Export
- Page G: Task History
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone as dj_timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from datasets.models import (
    Dataset,
    StorageDestination,
    DatasetStorageReplica,
    SecurityAuditEvent,
    DatasetUpload,
    DatasetInventoryItem,
    DatasetAnalysisReport,
)
from tasks.models import Task
from mec_manager.models import MECAgent
from engine.storage_manager import (
    ensure_storage_destinations_initialized,
    calculate_file_sha256,
)
from engine.digital_twin import DigitalTwin
from engine.dataset_analysis_service import (
    process_zip_dataset_upload,
    generate_report_csv_content,
    format_bytes,
)


# =============================================================================
# Helper function to gather real dashboard metrics
# =============================================================================
def get_real_dashboard_metrics():
    destinations = ensure_storage_destinations_initialized()
    total_uploads = DatasetUpload.objects.count()
    total_datasets = Dataset.objects.count()
    analyzed_reports = DatasetAnalysisReport.objects.count()

    tasks_completed = Task.objects.filter(status__in=["COMPLETED", "SUCCEEDED"]).count()
    tasks_failed = Task.objects.filter(status__in=["FAILED", "TIMED_OUT", "BLOCKED", "REJECTED"]).count()
    tasks_pending = Task.objects.filter(status__in=["PENDING", "QUEUED", "RUNNING", "SCHEDULED"]).count()

    latest_upload = DatasetUpload.objects.order_by("-uploaded_at").first()
    latest_allocation = DatasetInventoryItem.objects.order_by("-id").first()
    recent_audits = SecurityAuditEvent.objects.order_by("-timestamp")[:6]
    recent_tasks = Task.objects.order_by("-created_at")[:8]

    # Digital Twin status check
    twin = DigitalTwin()
    snapshot = twin.snapshot()

    # MEC agent real database check
    mec_agent = MECAgent.objects.filter(is_online=True).first()
    mec_online = mec_agent is not None

    storage_nodes = []
    for dest_id, dest in destinations.items():
        free_b = max(0, dest.capacity_bytes - dest.used_bytes)
        assigned_items_count = DatasetInventoryItem.objects.filter(selected_destination=dest_id).count()
        assigned_replicas_count = DatasetStorageReplica.objects.filter(storage_destination=dest).count()

        is_online = True
        status_label = "ONLINE"
        if dest.destination_type == "MEC":
            is_online = mec_online
            status_label = "ONLINE" if mec_online else "OFFLINE"
        elif dest.destination_type == "CLOUD":
            status_label = "VERIFIED EMULATOR" if dest.is_emulator else "CONNECTED"

        storage_nodes.append({
            "destination_id": dest.destination_id,
            "name": dest.name,
            "type": dest.destination_type,
            "status": status_label,
            "is_online": is_online,
            "is_emulator": dest.is_emulator,
            "capacity_bytes": dest.capacity_bytes,
            "capacity_formatted": format_bytes(dest.capacity_bytes),
            "used_bytes": dest.used_bytes,
            "used_formatted": format_bytes(dest.used_bytes),
            "free_bytes": free_b,
            "free_formatted": format_bytes(free_b),
            "usage_percent": round((dest.used_bytes / max(1, dest.capacity_bytes)) * 100, 1),
            "assigned_items_count": assigned_items_count + assigned_replicas_count,
            "privacy_tier_allowed": dest.privacy_tier_allowed,
        })

    return {
        "total_uploads": total_uploads,
        "total_datasets": total_datasets,
        "analyzed_reports": analyzed_reports,
        "tasks_completed": tasks_completed,
        "tasks_failed": tasks_failed,
        "tasks_pending": tasks_pending,
        "storage_nodes": storage_nodes,
        "latest_upload": latest_upload,
        "latest_allocation": latest_allocation,
        "recent_audits": recent_audits,
        "recent_tasks": recent_tasks,
    }


# =============================================================================
# Page A: Dashboard
# =============================================================================
def dashboard_view(request):
    data = get_real_dashboard_metrics()
    return render(request, "dashboard.html", {
        "active_page": "dashboard",
        "page_title": "Executive Operations Dashboard",
        **data,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def dashboard_api(request):
    data = get_real_dashboard_metrics()
    return JsonResponse({
        "success": True,
        "total_uploads": data["total_uploads"],
        "total_datasets": data["total_datasets"],
        "analyzed_reports": data["analyzed_reports"],
        "tasks_completed": data["tasks_completed"],
        "tasks_failed": data["tasks_failed"],
        "tasks_pending": data["tasks_pending"],
        "storage_nodes": data["storage_nodes"],
        "latest_upload": {
            "upload_id": data["latest_upload"].upload_id,
            "file_name": data["latest_upload"].file_name,
            "status": data["latest_upload"].status,
            "uploaded_at": data["latest_upload"].uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
        } if data["latest_upload"] else None,
        "latest_allocation": {
            "file_name": data["latest_allocation"].file_name,
            "destination": data["latest_allocation"].selected_destination,
            "status": data["latest_allocation"].status,
        } if data["latest_allocation"] else None,
    })


# =============================================================================
# Page B: Upload Dataset
# =============================================================================
def upload_dataset_view(request):
    recent_uploads = DatasetUpload.objects.order_by("-uploaded_at")[:5]
    return render(request, "upload_dataset.html", {
        "active_page": "upload",
        "page_title": "Manual ZIP Dataset Upload & Analysis",
        "recent_uploads": recent_uploads,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def upload_dataset_api(request):
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"success": False, "error": "Please select a valid ZIP archive to upload."}, status=400)

    if not uploaded_file.name.lower().endswith(".zip"):
        return JsonResponse({"success": False, "error": "Invalid format. Only .zip archives are permitted for dataset ingest."}, status=400)

    mode = request.POST.get("execution_mode", "SIMULATION").strip().upper()
    if mode not in ("SIMULATION", "EXECUTION"):
        mode = "SIMULATION"

    ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
    result = process_zip_dataset_upload(
        uploaded_file=uploaded_file,
        execution_mode=mode,
        client_ip=ip,
    )
    status_code = 200 if result.get("success") else 400
    return JsonResponse(result, status=status_code)


@api_view(["POST", "GET"])
@permission_classes([AllowAny])
def upload_demo_zip_api(request):
    """Loads pre-bundled synthetic hospital workload batch ZIP for instant testing."""
    sample_path = Path(settings.BASE_DIR) / "sample_upload_datasets" / "hospital_workload_batch.zip"
    if not sample_path.exists():
        return JsonResponse({"success": False, "error": "Sample archive 'hospital_workload_batch.zip' not found on server."}, status=404)

    with open(sample_path, "rb") as f:
        content = f.read()

    mode = request.POST.get("execution_mode", "SIMULATION") if request.method == "POST" else "SIMULATION"
    mock_file = SimpleUploadedFile("hospital_workload_batch.zip", content, content_type="application/zip")
    ip = request.META.get("REMOTE_ADDR", "127.0.0.1")

    result = process_zip_dataset_upload(
        uploaded_file=mock_file,
        execution_mode=mode,
        client_ip=ip,
    )
    status_code = 200 if result.get("success") else 400
    return JsonResponse(result, status=status_code)


# =============================================================================
# Page C: Digital Twin
# =============================================================================
def digital_twin_view(request):
    destinations = ensure_storage_destinations_initialized()
    twin = DigitalTwin()
    states = twin.states()

    mec_agents = MECAgent.objects.all().order_by("-is_online", "device_id")
    mec_online_count = MECAgent.objects.filter(is_online=True).count()

    # Local Storage stats
    local_dest = destinations.get("LOCAL_STORAGE")
    local_items_count = DatasetInventoryItem.objects.filter(selected_destination="LOCAL_STORAGE").count()
    local_tasks_count = Task.objects.filter(assigned_node="LOCAL").count()

    # MEC Storage stats
    mec_dest = destinations.get("MEC_STORAGE")
    mec_items_count = DatasetInventoryItem.objects.filter(selected_destination="MEC_STORAGE").count()
    mec_tasks_count = Task.objects.filter(assigned_tier="MEC").count()

    # Cloud Storage stats
    cloud_dest = destinations.get("CLOUD_STORAGE")
    cloud_items_count = DatasetInventoryItem.objects.filter(selected_destination="CLOUD_STORAGE").count()
    cloud_tasks_count = Task.objects.filter(assigned_tier="CLOUD").count()

    context = {
        "active_page": "digital_twin",
        "page_title": "Digital Twin Infrastructure & Resource Monitor",
        "local_dest": local_dest,
        "local_items_count": local_items_count,
        "local_tasks_count": local_tasks_count,
        "mec_dest": mec_dest,
        "mec_items_count": mec_items_count,
        "mec_tasks_count": mec_tasks_count,
        "mec_agents": mec_agents,
        "mec_online_count": mec_online_count,
        "cloud_dest": cloud_dest,
        "cloud_items_count": cloud_items_count,
        "cloud_tasks_count": cloud_tasks_count,
        "states": states,
    }
    return render(request, "digital_twin.html", context)


@api_view(["GET"])
@permission_classes([AllowAny])
def digital_twin_api(request):
    destinations = ensure_storage_destinations_initialized()
    twin = DigitalTwin()
    snapshot = twin.snapshot()

    mec_agents = list(MECAgent.objects.values(
        "device_id", "system_name", "is_online", "last_heartbeat", "hostname", "operating_system"
    ))

    nodes = {}
    for k, d in destinations.items():
        free_b = max(0, d.capacity_bytes - d.used_bytes)
        assigned_cnt = DatasetInventoryItem.objects.filter(selected_destination=k).count()
        nodes[k] = {
            "name": d.name,
            "type": d.destination_type,
            "capacity_bytes": d.capacity_bytes,
            "capacity_formatted": format_bytes(d.capacity_bytes),
            "used_bytes": d.used_bytes,
            "used_formatted": format_bytes(d.used_bytes),
            "free_bytes": free_b,
            "free_formatted": format_bytes(free_b),
            "usage_percent": round((d.used_bytes / max(1, d.capacity_bytes)) * 100, 1),
            "assigned_datasets_count": assigned_cnt,
            "is_emulator": d.is_emulator,
            "privacy_tier_allowed": d.privacy_tier_allowed,
        }

    return JsonResponse({
        "success": True,
        "destinations": nodes,
        "mec_agents": mec_agents,
        "resources": snapshot.get("resources", []),
        "timestamp": dj_timezone.now().isoformat(),
    })


# =============================================================================
# Page D: Storage Allocation
# =============================================================================
def storage_allocation_view(request):
    destinations = ensure_storage_destinations_initialized()
    items = DatasetInventoryItem.objects.select_related("upload").order_by("-id")

    # Destination summary breakdown
    local_cnt = DatasetInventoryItem.objects.filter(selected_destination="LOCAL_STORAGE").count()
    mec_cnt = DatasetInventoryItem.objects.filter(selected_destination="MEC_STORAGE").count()
    cloud_cnt = DatasetInventoryItem.objects.filter(selected_destination="CLOUD_STORAGE").count()
    unassigned_cnt = DatasetInventoryItem.objects.filter(selected_destination="UNASSIGNED").count()

    local_bytes = sum(i.file_size for i in DatasetInventoryItem.objects.filter(selected_destination="LOCAL_STORAGE"))
    mec_bytes = sum(i.file_size for i in DatasetInventoryItem.objects.filter(selected_destination="MEC_STORAGE"))
    cloud_bytes = sum(i.file_size for i in DatasetInventoryItem.objects.filter(selected_destination="CLOUD_STORAGE"))

    context = {
        "active_page": "storage_allocation",
        "page_title": "AI-Based Storage Allocation & Eligibility",
        "items": items,
        "destinations": destinations,
        "summary": {
            "local_count": local_cnt,
            "local_formatted": format_bytes(local_bytes),
            "mec_count": mec_cnt,
            "mec_formatted": format_bytes(mec_bytes),
            "cloud_count": cloud_cnt,
            "cloud_formatted": format_bytes(cloud_bytes),
            "unassigned_count": unassigned_cnt,
            "total_count": items.count(),
        }
    }
    return render(request, "storage_allocation.html", context)


@api_view(["GET"])
@permission_classes([AllowAny])
def storage_allocation_api(request):
    items = DatasetInventoryItem.objects.select_related("upload").order_by("-id")
    data = []
    for i in items:
        data.append({
            "id": i.id,
            "upload_id": i.upload.upload_id,
            "file_name": i.file_name,
            "relative_path": i.relative_path,
            "file_size": i.file_size,
            "file_size_formatted": format_bytes(i.file_size),
            "format": i.format,
            "category": i.detected_category,
            "declared_source": i.declared_source,
            "privacy_policy": i.privacy_policy,
            "local_eligible": i.local_eligible,
            "mec_eligible": i.mec_eligible,
            "cloud_eligible": i.cloud_eligible,
            "selected_destination": i.selected_destination,
            "status": i.status,
            "decision_rationale": i.decision_rationale,
            "sha256": i.sha256_checksum,
        })
    return JsonResponse({"success": True, "count": len(data), "allocations": data})


# =============================================================================
# Page E: Dataset Reports
# =============================================================================
def dataset_reports_view(request):
    reports = DatasetAnalysisReport.objects.select_related("upload").order_by("-created_at")
    return render(request, "dataset_reports.html", {
        "active_page": "reports",
        "page_title": "Dataset Storage & Analysis Reports",
        "reports": reports,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def dataset_reports_api(request):
    reports = DatasetAnalysisReport.objects.select_related("upload").order_by("-created_at")
    data = []
    for r in reports:
        data.append({
            "report_id": r.report_id,
            "upload_id": r.upload.upload_id,
            "file_name": r.upload.file_name,
            "file_size_formatted": format_bytes(r.upload.file_size),
            "total_files": r.upload.total_files_count,
            "execution_mode": r.upload.execution_mode,
            "status": r.upload.status,
            "method_used": r.method_used,
            "analysis_duration_ms": r.analysis_duration_ms,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return JsonResponse({"success": True, "reports": data, "count": len(data)})


# =============================================================================
# Page F: Report Details & CSV Export
# =============================================================================
def report_detail_view(request, report_id):
    report = get_object_or_404(DatasetAnalysisReport.objects.select_related("upload"), report_id=report_id)

    summary = json.loads(report.summary_json or "{}")
    inventory = json.loads(report.inventory_json or "[]")
    ai_analysis = json.loads(report.ai_analysis_json or "{}")
    allocation = json.loads(report.allocation_json or "{}")
    security = json.loads(report.security_audit_json or "{}")
    final_result = json.loads(report.final_result_json or "{}")

    context = {
        "active_page": "reports",
        "page_title": f"Report Details: {report.report_id}",
        "report": report,
        "summary": summary,
        "inventory": inventory,
        "ai_analysis": ai_analysis,
        "allocation": allocation,
        "security": security,
        "final_result": final_result,
    }
    return render(request, "report_detail.html", context)


@api_view(["GET"])
@permission_classes([AllowAny])
def report_detail_api(request, report_id):
    report = get_object_or_404(DatasetAnalysisReport.objects.select_related("upload"), report_id=report_id)
    return JsonResponse({
        "success": True,
        "report_id": report.report_id,
        "upload_id": report.upload.upload_id,
        "title": report.title,
        "method_used": report.method_used,
        "analysis_duration_ms": report.analysis_duration_ms,
        "scheduling_duration_ms": report.scheduling_duration_ms,
        "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": json.loads(report.summary_json or "{}"),
        "inventory": json.loads(report.inventory_json or "[]"),
        "ai_analysis": json.loads(report.ai_analysis_json or "{}"),
        "allocation": json.loads(report.allocation_json or "{}"),
        "security": json.loads(report.security_audit_json or "{}"),
        "final_result": json.loads(report.final_result_json or "{}"),
    })


def report_download_csv_view(request, report_id):
    report = get_object_or_404(DatasetAnalysisReport.objects.select_related("upload"), report_id=report_id)
    csv_text = generate_report_csv_content(report)

    response = HttpResponse(csv_text, content_type="text/csv")
    filename = f"report_{report.report_id}_{report.upload.file_name.rsplit('.', 1)[0]}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# =============================================================================
# Page G: Task History
# =============================================================================
def task_history_view(request):
    tasks = Task.objects.all().order_by("-created_at")
    total_count = tasks.count()
    completed_count = Task.objects.filter(status__in=["COMPLETED", "SUCCEEDED"]).count()
    failed_count = Task.objects.filter(status__in=["FAILED", "TIMED_OUT", "BLOCKED", "REJECTED"]).count()
    running_count = Task.objects.filter(status__in=["RUNNING", "QUEUED", "PENDING"]).count()

    context = {
        "active_page": "tasks",
        "page_title": "Task Execution & Scheduling History",
        "tasks": tasks[:100],  # Display most recent 100
        "total_count": total_count,
        "completed_count": completed_count,
        "failed_count": failed_count,
        "running_count": running_count,
    }
    return render(request, "task_history.html", context)


@api_view(["GET"])
@permission_classes([AllowAny])
def task_history_api(request):
    tasks = Task.objects.all().order_by("-created_at")[:100]
    data = []
    for t in tasks:
        dur = t.execution_time
        if dur is None and t.total_latency_ms:
            dur = round(t.total_latency_ms / 1000.0, 3)

        data.append({
            "task_id": t.task_id,
            "name": t.name,
            "workload_type": t.workload_type,
            "privacy_policy": t.privacy_policy,
            "assigned_node": t.assigned_node or (t.assigned_mec.device_id if t.assigned_mec else "Unassigned"),
            "assigned_tier": t.assigned_tier,
            "status": t.status,
            "duration": dur,
            "error_message": t.error_message,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })
    return JsonResponse({"success": True, "tasks": data, "count": len(data)})
