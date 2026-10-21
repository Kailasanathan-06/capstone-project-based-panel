"""manage.py validate_datasets - validate all local dataset files."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Validate datasets and write datasets/statistics/validation_report*"

    def handle(self, *args, **options):
        from data_pipeline.validator import run_validator

        payload = run_validator()
        self.stdout.write("\nVALIDATION SUMMARY")
        for key in ("files_validated", "files_ok", "attacked_files", "benign_files", "raw_real_files_ok"):
            self.stdout.write(f"  {key}: {payload.get(key, '-')}")
        self.stdout.write(self.style.SUCCESS("Reports -> datasets/statistics/"))