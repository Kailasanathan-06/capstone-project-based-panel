"""
Management command to download and index official MedMNIST datasets (default: PneumoniaMNIST).
Stores raw data and extracted sample images OUTSIDE the public web root.
Provides synthetic task references for smart hospital privacy-aware scheduling experiments.
"""

import os
import hashlib
from pathlib import Path
from PIL import Image
import numpy as np

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone

import medmnist
from medmnist import INFO
from datasets.models import MedicalDatasetMetadata, MedicalDatasetSample


class Command(BaseCommand):
    help = "Download and index official MedMNIST medical image dataset (PneumoniaMNIST)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            type=str,
            default="pneumoniamnist",
            help="MedMNIST dataset flag (default: pneumoniamnist)",
        )
        parser.add_argument(
            "--max-samples",
            type=int,
            default=120,
            help="Maximum sample images to extract for UI browsing (default: 120, 0 for all)",
        )
        parser.add_argument(
            "--target-dir",
            type=str,
            default="",
            help="Directory to store datasets outside public webroot (default: settings.MEDICAL_DATASET_DIR)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-download and re-indexing even if already present",
        )

    def handle(self, *args, **options):
        dataset_flag = options["dataset"].lower().strip()
        max_samples = options["max_samples"]
        force = options["force"]

        if dataset_flag not in INFO:
            raise CommandError(
                f"Unsupported dataset flag '{dataset_flag}'. Available in MedMNIST v{medmnist.__version__}: {list(INFO.keys())}"
            )

        info = INFO[dataset_flag]
        dataset_name = f"{info['python_class']} (MedMNIST v{medmnist.__version__})"
        source_url = info.get("url", "https://zenodo.org/records/10519652/files/pneumoniamnist.npz?download=1")
        license_terms = info.get("license", "CC BY 4.0")
        citation = "Yang et al., MedMNIST v2 - A large-scale lightweight benchmark for 2D and 3D biomedical image classification, Scientific Data, 2023."
        channels = info.get("n_channels", 1)
        expected_samples = info.get("n_samples", {})

        target_base = Path(options["target_dir"]) if options["target_dir"] else getattr(
            settings, "MEDICAL_DATASET_DIR", settings.BASE_DIR / "data_storage" / "medical_datasets"
        )
        dataset_dir = target_base / dataset_flag
        samples_dir = dataset_dir / "samples"
        samples_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(self.style.NOTICE(f"Checking dataset: {dataset_name} in {dataset_dir}"))

        # Check existing metadata
        metadata, _ = MedicalDatasetMetadata.objects.get_or_create(
            dataset_flag=dataset_flag,
            defaults={
                "name": dataset_name,
                "description": info.get("description", ""),
                "source_url": source_url,
                "license_terms": license_terms,
                "citation": citation,
                "version": medmnist.__version__,
                "storage_path": str(dataset_dir),
                "image_dimensions": f"{channels}x28x28",
                "channel_count": channels,
            },
        )

        npz_filename = f"{dataset_flag}.npz"
        npz_path = dataset_dir / npz_filename

        # Download using official MedMNIST package
        if not npz_path.exists() or force:
            self.stdout.write(f"Downloading {dataset_flag} from official source...")
            try:
                # Instantiate dataset class with download=True
                dataset_class = getattr(medmnist, info["python_class"])
                # Download train split (downloads entire npz)
                _ = dataset_class(split="train", download=True, root=str(dataset_dir))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"Download failed: {exc}"))
                raise CommandError(
                    f"Unable to download {dataset_flag} from official MedMNIST source ({source_url}). "
                    f"Error: {exc}. Please verify network connectivity."
                )

        if not npz_path.exists():
            raise CommandError(f"Dataset archive not found at expected location: {npz_path}")

        file_size = npz_path.stat().st_size
        self.stdout.write(f"Validating dataset file: {npz_path} ({file_size / (1024*1024):.2f} MB)...")

        # Compute SHA-256
        sha256 = hashlib.sha256()
        with open(npz_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        npz_checksum = sha256.hexdigest()

        # Load and validate npz contents
        try:
            data = np.load(npz_path)
            train_imgs = data["train_images"]
            train_labels = data["train_labels"]
            val_imgs = data["val_images"]
            val_labels = data["val_labels"]
            test_imgs = data["test_images"]
            test_labels = data["test_labels"]
        except Exception as exc:
            raise CommandError(f"Failed to load dataset archive: {exc}")

        total_samples = len(train_imgs) + len(val_imgs) + len(test_imgs)
        self.stdout.write(
            f"Verified splits: train={len(train_imgs)}, val={len(val_imgs)}, test={len(test_imgs)} (total: {total_samples})"
        )

        # Update metadata record
        metadata.name = dataset_name
        metadata.description = info.get("description", "")
        metadata.source_url = source_url
        metadata.license_terms = license_terms
        metadata.citation = citation
        metadata.version = medmnist.__version__
        metadata.is_downloaded = True
        metadata.download_date = timezone.now()
        metadata.storage_path = str(dataset_dir)
        metadata.sample_count = total_samples
        metadata.train_count = len(train_imgs)
        metadata.val_count = len(val_imgs)
        metadata.test_count = len(test_imgs)
        metadata.image_dimensions = f"{channels}x{train_imgs.shape[1]}x{train_imgs.shape[2]}"
        metadata.channel_count = channels
        metadata.file_size_bytes = file_size
        metadata.save()

        # Extract sample PNG images for browsing
        label_map = {0: "normal", 1: "pneumonia"}
        label_dict = info.get("label", label_map)
        # Handle string or int keys
        normalized_label_dict = {}
        for k, v in label_dict.items():
            try:
                normalized_label_dict[int(k)] = str(v)
            except (ValueError, TypeError):
                normalized_label_dict[k] = str(v)

        splits_to_extract = [
            ("train", train_imgs, train_labels),
            ("val", val_imgs, val_labels),
            ("test", test_imgs, test_labels),
        ]

        if max_samples > 0:
            per_split_limit = max(1, max_samples // 3)
        else:
            per_split_limit = None

        if force:
            MedicalDatasetSample.objects.filter(dataset=metadata).delete()

        existing_sample_ids = set(
            MedicalDatasetSample.objects.filter(dataset=metadata).values_list("sample_id", flat=True)
        )

        extracted_count = 0
        new_samples = []

        for split_name, imgs, labels in splits_to_extract:
            split_limit = per_split_limit if per_split_limit is not None else len(imgs)
            indices = range(min(split_limit, len(imgs)))

            for idx in indices:
                # Synthetic medical task reference e.g. MED-PN-TRAIN-0001
                sample_id = f"MED-PN-{split_name.upper()}-{idx+1:04d}"
                if sample_id in existing_sample_ids:
                    continue

                img_arr = imgs[idx]
                lbl_val = int(labels[idx][0]) if labels[idx].ndim > 0 else int(labels[idx])
                lbl_name = normalized_label_dict.get(lbl_val, f"class_{lbl_val}")

                # Save sample as PNG
                img_filename = f"{split_name}_{idx+1:04d}_{lbl_name}.png"
                img_path = samples_dir / img_filename

                if not img_path.exists() or force:
                    pil_img = Image.fromarray(img_arr)
                    pil_img.save(img_path, format="PNG")

                sample_size = img_path.stat().st_size
                with open(img_path, "rb") as sf:
                    sample_hash = hashlib.sha256(sf.read()).hexdigest()

                rel_path = f"data_storage/medical_datasets/{dataset_flag}/samples/{img_filename}"

                new_samples.append(
                    MedicalDatasetSample(
                        sample_id=sample_id,
                        dataset=metadata,
                        split=split_name,
                        label_index=lbl_val,
                        label_name=lbl_name,
                        relative_image_path=rel_path,
                        file_size_bytes=sample_size,
                        image_format="PNG",
                        dimensions=f"{img_arr.shape[0]}x{img_arr.shape[1]}",
                        sha256_checksum=sample_hash,
                        processing_status="UNPROCESSED",
                    )
                )
                extracted_count += 1

        if new_samples:
            MedicalDatasetSample.objects.bulk_create(new_samples)
            self.stdout.write(self.style.SUCCESS(f"Indexed {len(new_samples)} new medical image samples."))

        total_indexed = MedicalDatasetSample.objects.filter(dataset=metadata).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully set up {dataset_name}!"
                f"\nArchive: {npz_path} ({file_size / (1024*1024):.2f} MB)"
                f"\nSHA-256: {npz_checksum[:16]}..."
                f"\nSamples Indexed for Browser: {total_indexed}"
                f"\nProvenance: {citation} [{license_terms}]"
            )
        )
