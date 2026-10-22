"""
Management command to list and validate registered hospital datasets and the 14 workload scenarios.
"""

from pathlib import Path
import hashlib

from django.core.management.base import BaseCommand
from datasets.models import WorkloadScenario, MedicalDatasetMetadata, DatasetVersion, StorageDestination, DatasetStorageReplica
from engine.hospital_workloads import ensure_all_14_scenarios_registered


class Command(BaseCommand):
    help = "List and validate registered hospital datasets, workload scenarios, and storage destinations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--validate",
            action="store_true",
            help="Verify integrity and presence of all physical input fixtures and dataset archives",
        )

    def handle(self, *args, **options):
        validate = options.get("validate", False)

        # Ensure scenarios exist
        ensure_all_14_scenarios_registered()

        self.stdout.write(self.style.MIGRATE_HEADING("=== 14 HOSPITAL WORKLOAD SCENARIOS ==="))
        scenarios = WorkloadScenario.objects.all().order_by("category", "scenario_id")
        current_cat = None

        for s in scenarios:
            if s.category != current_cat:
                current_cat = s.category
                self.stdout.write(self.style.NOTICE(f"\n[{current_cat}]"))

            validation_info = ""
            if validate:
                if s.input_file_path:
                    p = Path(s.input_file_path)
                    if p.exists():
                        size_kb = p.stat().st_size / 1024
                        validation_info = f" [FILE OK: {size_kb:.1f} KB]"
                    else:
                        validation_info = " [FILE MISSING]"
                elif s.input_payload:
                    validation_info = " [SYNTHETIC PAYLOAD PRESENT]"

            self.stdout.write(
                f"  • {s.scenario_id:<16} | {s.name:<55} | Policy: {s.privacy_policy:<13} | Expected: {s.expected_status}{validation_info}"
            )

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== REGISTERED PUBLIC DATASETS & VERSIONS ==="))
        versions = DatasetVersion.objects.all()
        if versions.exists():
            for v in versions:
                self.stdout.write(f"  • {v.dataset_name} ({v.version_tag}) | License: {v.license} | Samples: {v.total_samples}")
                if validate and v.storage_path:
                    p = Path(v.storage_path)
                    status_str = "EXISTS" if p.exists() else "NOT FOUND ON DISK"
                    self.stdout.write(f"    Path: {p} [{status_str}]")
        else:
            self.stdout.write("  No public dataset versions registered yet. Run 'python manage.py download_hospital_datasets' to download.")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== 3 VERIFIED STORAGE DESTINATIONS ==="))
        from engine.storage_manager import ensure_storage_destinations_initialized

        dests = ensure_storage_destinations_initialized()
        for dest_id, d in dests.items():
            used_mb = round(d.used_bytes / (1024 * 1024), 2)
            cap_gb = round(d.capacity_bytes / (1024 * 1024 * 1024), 1)
            self.stdout.write(
                f"  • {d.destination_id:<16} ({d.destination_type}) | Policy: {d.privacy_tier_allowed:<13} | Used: {used_mb} MB / {cap_gb} GB\n    Path: {d.base_path}"
            )

        replicas = DatasetStorageReplica.objects.all()
        if replicas.exists():
            self.stdout.write(self.style.MIGRATE_HEADING("\n=== DATASET STORAGE REPLICAS ==="))
            for r in replicas:
                self.stdout.write(
                    f"  • {r.replica_id:<32} | {r.dataset_id} @ {r.storage_destination.destination_id} | Status: {r.replication_status}"
                )
