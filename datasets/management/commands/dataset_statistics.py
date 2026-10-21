"""manage.py dataset_statistics - compute statistics from real dataset files."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compute dataset statistics and write reports to datasets/statistics/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-sync-mysql",
            action="store_true",
            help="Skip syncing MySQL Dataset metadata rows",
        )

    def handle(self, *args, **options):
        from data_pipeline.statistics import compute_all_statistics

        stats = compute_all_statistics()
        self.stdout.write("\nPROCESSED ROWS")
        for k, v in stats.get("processed", {}).items():
            self.stdout.write(f"  {k}: {v}")
        self.stdout.write("\nSTORAGE USAGE")
        for k, v in stats.get("storage_usage", {}).items():
            self.stdout.write(f"  {k}: {v}")

        if not options["no_sync_mysql"]:
            try:
                from data_pipeline.dataset_manager import DatasetManager
                from datasets.models import sync_from_pipeline

                mgr = DatasetManager(verbose=False)
                sync_from_pipeline(mgr.registry_overview(), mgr.dataset_cards())
                self.stdout.write(self.style.SUCCESS("MySQL dataset metadata synced."))
            except Exception as exc:  # noqa: BLE001
                self.stdout.write(self.style.WARNING(f"MySQL sync skipped: {exc}"))

        self.stdout.write(self.style.SUCCESS("Reports -> datasets/statistics/"))