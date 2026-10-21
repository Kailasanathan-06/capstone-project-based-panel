"""manage.py sync_verified_catalog - upsert verified research pipeline datasets into MySQL metadata.

Reads the root-level datasets/dataset_validation_report.json produced by
scripts/verify_datasets.py and syncs every entry into the Dataset model.
"""

from django.core.management.base import BaseCommand
from datasets.models import Dataset
from datasets.views import _root_datasets

import json
import os


class Command(BaseCommand):
    help = "Sync datasets/dataset_validation_report.json into the Dataset metadata rows"

    def handle(self, *args, **options):
        report_path = os.path.join(_root_datasets(), "dataset_validation_report.json")
        if not os.path.exists(report_path):
            self.stdout.write(self.style.ERROR("No report - run scripts/verify_datasets.py first."))
            return
        with open(report_path, "r", encoding="utf-8") as fh:
            report = json.load(fh)

        rows = report.get("datasets", [])
        created, updated = 0, 0
        for item in rows:
            slug = item.get("slug", "")
            if not slug:
                continue
            defaults = {
                "name": item.get("name", slug),
                "dataset_type": "attacked"
                if "ATTACKED" in str(item.get("category", ""))
                else "benign"
                if "BENIGN" in str(item.get("category", ""))
                else "mixed",
                "source": item.get("official_source", ""),
                "file_name": slug,
                "file_size": int(item.get("file_size_bytes", 0) or 0),
                "record_count": int(item.get("record_count", 0) or 0),
                "format": "CSV",
                "storage_location": os.path.join(_root_datasets(), "raw"),
                "validation_status": "local" if item.get("verification_status") == "VERIFIED"
                else "manual_download_required",
                "processing_status": "processed" if item.get("processed") else "raw_only",
            }
            ds, was_created = Dataset.objects.update_or_create(
                dataset_id=slug.lower().replace(" ", "_"),
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Synced {len(rows)} datasets "
                                             f"(created={created}, updated={updated})."))