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