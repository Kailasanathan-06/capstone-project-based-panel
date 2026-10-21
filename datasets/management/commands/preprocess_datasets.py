"""manage.py preprocess_datasets - clean, preprocess and feature-engineer."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clean, preprocess and feature-engineer datasets into datasets/processed/"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Re-run cleaning even if outputs exist")

    def handle(self, *args, **options):
        from data_pipeline.cleaner import run_cleaner
        from data_pipeline.preprocessor import run_preprocessor
        from data_pipeline.feature_engineering import run_feature_engineering

        self.stdout.write("Cleaning...")
        clean = run_cleaner(force=options["force"])
        for name, s in clean.items():
            self.stdout.write(f"  {name}: {s.get('status')} attack={s.get('attack_rows')} benign={s.get('benign_rows')}")
        self.stdout.write("Preprocessing...")
        prep = run_preprocessor(force=options["force"])
        for name, s in prep.items():
            self.stdout.write(f"  {name}: {s.get('status')} rows={s.get('total_rows')} train={s.get('train_rows')} test={s.get('test_rows')}")
        self.stdout.write("Feature engineering...")
        fe = run_feature_engineering()
        self.stdout.write(f"  derived risk_score/flow_rate on {len(fe)} file(s)")
        self.stdout.write(self.style.SUCCESS("Processed datasets written to datasets/processed/"))