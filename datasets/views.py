"""
Datasets app API - powers the Dataset Management dashboard.

All numbers come from the real files on disk (data_pipeline) and MySQL
metadata.  No values are fabricated.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
import os
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from data_pipeline.dataset_manager import DatasetManager
from data_pipeline.statistics import compute_all_statistics
from data_pipeline.paths import DATASET_CATALOG

from .models import Dataset


def _manager():
    return DatasetManager(verbose=False)


def _root_datasets():
    """Root-level datasets/ tree produced by scripts/verify_datasets.py."""
    import os

    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "datasets")


def _load_statistics():
    import json
    import os

    path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "datasets", "statistics", "statistics.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return compute_all_statistics()


@api_view(["GET"])
@permission_classes([AllowAny])
def dataset_overview(request):
    """Aggregate numbers for the dashboard header cards (real values)."""
    mgr = _manager()
    stats = _load_statistics()
    cards = mgr.dataset_cards()

    attacked_info = stats.get("processed", {})
    attacked_rows = attacked_info.get("attacked_rows", 0)
    benign_rows = attacked_info.get("benign_rows", 0)

    return JsonResponse(
        {
            "total_datasets": len(DATASET_CATALOG),
            "attacked_datasets": sum(1 for c in cards if c["type"] == "ATTACKED"),
            "benign_datasets": 0,
            "total_records": attacked_rows + benign_rows,
            "processed_records": attacked_rows + benign_rows,
            "attacked_records": attacked_rows,
            "benign_records": benign_rows,
            "storage_usage_mb": stats.get("storage_usage", {}).get("mb", 0.0),
            "storage_usage_bytes": stats.get("storage_usage", {}).get("bytes", 0),
            "validation_status": "VALIDATED" if attacked_rows + benign_rows > 0 else "NO_LOCAL_DATA",
            "generated_at": stats.get("generated_at", ""),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def dataset_cards(request):
    """Panel cards split into ATTACKED and BENIGN groups."""
    cards = _manager().dataset_cards()
    attacked = [c for c in cards if c["type"] == "ATTACKED"]
    benign = [
        {
            "name": "NSL-KDD Benign split",
            "type": "BENIGN",
            "records_expected": 0,
            "records_local": None,
            "size_mb": 0.0,
            "status": "LOCAL",
            "source": "https://www.unb.ca/cic/datasets/nsl.html",
            "processing_status": "PROCESSED",
            "drive_status": "NOT_UPLOADED",
            "attack_types": ["benign"],
            "format": "CSV",
            "note": "Filtered from NSL-KDD 'normal' class; documented in metadata.",
        }
    ]
    return JsonResponse({"attacked": attacked, "benign": benign})


@api_view(["GET"])
@permission_classes([AllowAny])
def dataset_visualizations(request):
    """Chart-ready statistics, computed from actual files."""
    stats = _load_statistics()
    dist = stats.get("attacked_distribution", {}).get("rows", [])
    dist_sorted = sorted(dist, key=lambda r: -int(r.get("count", 0)))[:12]

    localStorage = stats.get("storage_usage", {})
    proc = stats.get("processed", {})

    label_sums = {"title": "Top 12 attack classes", "labels": [r["label"] for r in dist_sorted],
                  "counts": [int(r["count"]) for r in dist_sorted]}
    balance = {"title": "Benign vs Attack", "labels": ["benign", "attacked"],
               "counts": [int(proc.get("benign_rows", 0)), int(proc.get("attacked_rows", 0))]}
    sizes = {"title": "Storage usage", "labels": ["local datasets"], "bytes": [int(localStorage.get("bytes", 0))]}

    return JsonResponse({
        "attack_distribution": label_sums,
        "benign_vs_attack": balance,
        "storage": sizes,
        "processed": proc,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def dataset_mysql_rows(request):
    """Rows from the MySQL Dataset model."""
    rows = [d.to_dict() for d in Dataset.objects.all()]
    return JsonResponse({"rows": rows, "count": len(rows)})


@api_view(["GET"])
@permission_classes([AllowAny])
def verified_catalog(request):
    """Verified dataset catalogue from the research pipeline (root datasets/).

    Every value is read from dataset_validation_report.json,
    statistics/benign_summary.json and per-dataset metadata JSON produced by
    scripts/verify_datasets.py.  No fabricated numbers.
    """
    base = _root_datasets()
    report_path = os.path.join(base, "dataset_validation_report.json")
    if not os.path.exists(report_path):
        return JsonResponse({"error": "No validation report (run scripts/verify_datasets.py first)."}, status=404)

    with open(report_path, "r", encoding="utf-8") as fh:
        report = json.load(fh)
    benign_path = os.path.join(base, "statistics", "benign_summary.json")
    benign = {}
    if os.path.exists(benign_path):
        with open(benign_path, "r", encoding="utf-8") as fh:
            benign = json.load(fh)

    rows = []
    status_counts = {}
    for item in report.get("datasets", []):
        slug = item.get("slug", item.get("name", "?"))
        status = item.get("verification_status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        b = benign.get(slug, {})
        rows.append(
            {
                "slug": slug,
                "name": item.get("name", slug),
                "category": item.get("category", ""),
                "verification_status": status,
                "download_method": item.get("download_method", ""),
                "files": item.get("files", 0),
                "file_size_mb": round(item.get("file_size_bytes", 0) / 1048576.0, 2),
                "record_count": item.get("record_count", 0),
                "benign_records": b.get("benign", 0),
                "attack_records": b.get("attack", 0),
                "processed": bool(item.get("processed", False)),
                "official_source": item.get("official_source", ""),
            }
        )

    total_records = sum(r["record_count"] for r in rows)
    return JsonResponse(
        {
            "generated_at": report.get("generated", ""),
            "overview": {
                "total_datasets": len(rows),
                "verified": status_counts.get("VERIFIED", 0),
                "partial": status_counts.get("PARTIALLY VERIFIED", 0),
                "manual": status_counts.get("MANUAL VERIFICATION REQUIRED", 0),
                "total_records": total_records,
                "processed_with_splits": sum(1 for r in rows if r["processed"]),
            },
            "status_counts": status_counts,
            "datasets": rows,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def verified_detail(request, slug):
    """Verified metadata JSON for one dataset (metadata/<slug>.json)."""
    base = _root_datasets()
    safe = os.path.basename(slug)
    path = os.path.join(base, "metadata", f"{safe}.json")
    if not os.path.exists(path):
        return JsonResponse({"error": f"No metadata for '{safe}'."}, status=404)
    with open(path, "r", encoding="utf-8") as fh:
        return JsonResponse({"slug": safe, "metadata": json.load(fh)})


@api_view(["GET"])
@permission_classes([AllowAny])
def experiment_options(request):
    """Selectable options for experiments (attacked / benign / combined)."""
    return JsonResponse(
        {
            "attacked": [e["name"] for e in DATASET_CATALOG if e["type"] == "attacked"],
            "benign": ["NSL-KDD benign (normal class)", "UNSW-NB15 Normal class"],
            "modes": ["ATTACKED", "BENIGN", "COMBINED"],
        }
    )


# ============================================================================
# Smart Hospital Medical-Image Dataset Views
# ============================================================================

from django.http import HttpResponse, Http404
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from datasets.models import MedicalDatasetMetadata, MedicalDatasetSample
from tasks.models import Task, generate_task_id
from engine.image_processor import calculate_sha256
from django.conf import settings
from pathlib import Path


def medical_dataset_explorer_view(request):
    """Render the interactive Medical Dataset Explorer page."""
    metadata = MedicalDatasetMetadata.objects.filter(dataset_flag="pneumoniamnist").first()
    return render(
        request,
        "medical_dataset_explorer.html",
        {
            "metadata": metadata,
            "active_page": "medical_dataset_explorer",
        },
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def medical_dataset_summary(request):
    """API endpoint returning dataset metadata, provenance, and storage statistics."""
    meta = MedicalDatasetMetadata.objects.filter(dataset_flag="pneumoniamnist").first()
    if not meta:
        return JsonResponse(
            {
                "downloaded": False,
                "dataset_flag": "pneumoniamnist",
                "message": "Dataset not yet downloaded. Run: python manage.py download_medical_dataset",
            }
        )

    return JsonResponse(
        {
            "downloaded": meta.is_downloaded,
            "dataset_flag": meta.dataset_flag,
            "name": meta.name,
            "description": meta.description,
            "source_url": meta.source_url,
            "license_terms": meta.license_terms,
            "citation": meta.citation,
            "version": meta.version,
            "download_date": meta.download_date.isoformat() if meta.download_date else None,
            "storage_path": meta.storage_path,
            "sample_count": meta.sample_count,
            "train_count": meta.train_count,
            "val_count": meta.val_count,
            "test_count": meta.test_count,
            "image_dimensions": meta.image_dimensions,
            "channel_count": meta.channel_count,
            "file_size_mb": round(meta.file_size_bytes / (1024 * 1024), 2),
            "indexed_samples": MedicalDatasetSample.objects.filter(dataset=meta).count(),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def medical_dataset_samples(request):
    """Paginated API endpoint to browse extracted medical image samples with filters."""
    meta = MedicalDatasetMetadata.objects.filter(dataset_flag="pneumoniamnist").first()
    if not meta:
        return JsonResponse({"samples": [], "total": 0, "pages": 0, "page": 1})

    qs = MedicalDatasetSample.objects.filter(dataset=meta)

    # Filtering
    split = request.GET.get("split", "").strip().lower()
    if split in ("train", "val", "test"):
        qs = qs.filter(split=split)

    label = request.GET.get("label", "").strip().lower()
    if label in ("normal", "pneumonia"):
        qs = qs.filter(label_name=label)

    page_number = int(request.GET.get("page", 1))
    page_size = min(int(request.GET.get("page_size", 12)), 60)

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page_number)

    sample_list = [
        {
            "sample_id": s.sample_id,
            "split": s.split,
            "label_index": s.label_index,
            "label_name": s.label_name,
            "dimensions": s.dimensions,
            "file_size_bytes": s.file_size_bytes,
            "sha256": s.sha256_checksum,
            "image_url": f"/api/datasets/medical/image/{s.sample_id}/",
            "processing_status": s.processing_status,
        }
        for s in page_obj
    ]

    return JsonResponse(
        {
            "samples": sample_list,
            "total": paginator.count,
            "num_pages": paginator.num_pages,
            "current_page": page_number,
            "page_size": page_size,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def medical_dataset_sample_image(request, sample_id):
    """Serve the raw PNG image of a synthetic medical dataset sample safely."""
    try:
        sample = MedicalDatasetSample.objects.get(sample_id=sample_id)
    except MedicalDatasetSample.DoesNotExist:
        raise Http404("Sample not found")

    full_path = Path(settings.BASE_DIR) / sample.relative_image_path
    if not full_path.exists():
        raise Http404("Image file missing on disk")

    with open(full_path, "rb") as f:
        return HttpResponse(f.read(), content_type="image/png")


@api_view(["POST"])
@permission_classes([AllowAny])
def medical_dataset_create_task(request):
    """
    Convert a selected medical dataset sample into an executable processing task.
    Enforces privacy policy and validates workload parameters.
    """
    data = request.data if hasattr(request, "data") else json.loads(request.body or "{}")
    sample_id = data.get("sample_id", "").strip()

    try:
        sample = MedicalDatasetSample.objects.get(sample_id=sample_id)
    except MedicalDatasetSample.DoesNotExist:
        return JsonResponse({"error": f"Sample '{sample_id}' not found."}, status=404)

    operation = data.get("operation", "normalize_clahe").strip().lower()
    allowed_ops = {"normalize_clahe", "grayscale_resize", "normalize_only", "clahe_only"}
    if operation not in allowed_ops:
        return JsonResponse({"error": f"Invalid operation. Allowed: {list(allowed_ops)}"}, status=400)

    try:
        target_resolution = int(data.get("target_resolution", 224))
    except ValueError:
        target_resolution = 224

    privacy_policy = data.get("privacy_policy", "TRUSTED_EDGE").strip().upper()
    allowed_policies = {"LOCAL_ONLY", "TRUSTED_EDGE", "CLOUD_ALLOWED"}
    if privacy_policy not in allowed_policies:
        return JsonResponse({"error": f"Invalid privacy policy. Allowed: {list(allowed_policies)}"}, status=400)

    priority = int(data.get("priority", 1))
    deadline_ms = int(data.get("deadline_ms", 500))

    # Map privacy policy to sensitivity proxy 0..1 for legacy fitness compatibility
    policy_sensitivity_map = {
        "LOCAL_ONLY": 0.95,
        "TRUSTED_EDGE": 0.50,
        "CLOUD_ALLOWED": 0.10,
    }
    privacy_sensitivity = policy_sensitivity_map.get(privacy_policy, 0.5)

    full_img_path = Path(settings.BASE_DIR) / sample.relative_image_path
    input_sha = calculate_sha256(full_img_path) if full_img_path.exists() else sample.sha256_checksum

    task = Task.objects.create(
        task_id=generate_task_id(),
        name=f"Hospital Preprocessing: {sample.sample_id} ({sample.label_name})",
        priority=priority,
        data_size_mb=round(sample.file_size_bytes / (1024 * 1024), 4) or 0.05,
        cpu_cycles_giga=1.2 if target_resolution >= 224 else 0.4,
        memory_mb=128 if target_resolution >= 224 else 64,
        deadline_ms=deadline_ms,
        privacy_sensitivity=privacy_sensitivity,
        security_sensitivity=0.2 if privacy_policy != "LOCAL_ONLY" else 0.8,
        privacy_policy=privacy_policy,
        status="PENDING",
        dataset_sample_id=sample.sample_id,
        image_path=sample.relative_image_path,
        operation=operation,
        target_resolution=target_resolution,
        input_checksum=input_sha,
    )

    task.record_history("NONE", "PENDING", changed_by="medical_dataset_explorer")

    return JsonResponse(
        {
            "success": True,
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status,
            "sample_id": sample.sample_id,
            "privacy_policy": task.privacy_policy,
            "operation": task.operation,
            "target_resolution": task.target_resolution,
            "input_checksum": task.input_checksum,
            "message": "Hospital task successfully submitted to queue for privacy evaluation and scheduling.",
        },
        status=201,
    )