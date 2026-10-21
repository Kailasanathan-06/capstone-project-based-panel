"""manage.py download_datasets - fetch or document official dataset downloads."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Download datasets (or document MANUAL DOWNLOAD REQUIRED sources)."

    def handle(self, *args, **options):
        from data_pipeline.downloader import run_downloader

        results = run_downloader()
        self.stdout.write("\nSUMMARY")
        for name, status in results.items():
            self.stdout.write(f"  {name:20s} -> {status.get('status', '?')}")
        self.stdout.write(self.style.NOTICE(
            "NSL-KDD is present locally in datasets/real/. "
            "UNSW-NB15 and other UNSW/UNB datasets require manual download "
            "(see docs/DATASET_SELECTION_REPORT.md)."
        ))
        # Sync MySQL metadata
        try:
            from data_pipeline.dataset_manager import DatasetManager
            from .models import sync_from_pipeline

            mgr = DatasetManager(verbose=False)
            sync_from_pipeline(mgr.registry_overview(), mgr.dataset_cards())
            self.stdout.write(self.style.SUCCESS("MySQL dataset metadata synced."))
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(self.style.WARNING(f"MySQL sync skipped: {exc}"))