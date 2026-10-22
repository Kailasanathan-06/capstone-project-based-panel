"""
Real Medical-Image Preprocessing Engine
=======================================
Implements verifiable, high-integrity medical image preprocessing operations:
- File format and dimensional validation
- Malformed / corrupted image rejection
- Grayscale conversion
- Configurable target resolution resizing
- Pixel intensity normalization [0.0, 1.0]
- Contrast-Limited Adaptive Histogram Equalization (CLAHE)
- Monotonic high-resolution execution timing (time.perf_counter)
- Cryptographic SHA-256 integrity checksums for input and output

NOTE: This is a medical image preprocessing testbed, NOT a diagnostic system.
Preprocessing prepares chest X-rays for pipeline workflows and does NOT diagnose disease.
"""

import hashlib
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageOps

try:
    from skimage import exposure
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False


# Supported formats and security limits
ALLOWED_FORMATS = {"PNG", "JPEG", "JPG", "TIFF", "TIF", "BMP"}
MAX_IMAGE_FILE_SIZE = 25 * 1024 * 1024  # 25 MB max upload
MIN_DIMENSION = 8
MAX_DIMENSION = 8192


def calculate_sha256(file_path_or_bytes: Union[str, Path, bytes]) -> str:
    """Calculate the cryptographic SHA-256 checksum of a file or byte string."""
    sha256 = hashlib.sha256()
    if isinstance(file_path_or_bytes, bytes):
        sha256.update(file_path_or_bytes)
    else:
        with open(file_path_or_bytes, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
    return sha256.hexdigest()


def validate_image_file(file_path: Union[str, Path]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate that a file exists, is within safe size limits, and is a valid image.
    Returns (is_valid, error_message, metadata_dict).
    """
    path = Path(file_path)
    if not path.exists():
        return False, f"File does not exist: {path}", None

    file_size = path.stat().st_size
    if file_size == 0:
        return False, "File is empty (0 bytes)", None
    if file_size > MAX_IMAGE_FILE_SIZE:
        return False, f"File size exceeds maximum allowed ({file_size} > {MAX_IMAGE_FILE_SIZE} bytes)", None

    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as exc:
        return False, f"Corrupted or invalid image data: {exc}", None

    # Re-open to read properties (verify closes or invalidates the image pointer)
    try:
        with Image.open(path) as img:
            fmt = (img.format or "").upper()
            width, height = img.size
            mode = img.mode

        if fmt not in ALLOWED_FORMATS:
            return False, f"Unsupported format '{fmt}'. Allowed: {', '.join(sorted(ALLOWED_FORMATS))}", None

        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            return False, f"Image dimensions too small ({width}x{height} < {MIN_DIMENSION})", None
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            return False, f"Image dimensions exceed maximum safe limit ({width}x{height} > {MAX_DIMENSION})", None

        metadata = {
            "format": fmt,
            "width": width,
            "height": height,
            "mode": mode,
            "file_size_bytes": file_size,
            "sha256": calculate_sha256(path),
        }
        return True, None, metadata
    except Exception as exc:
        return False, f"Failed to read image metadata: {exc}", None


class MedicalImageProcessor:
    """Executes verifiable medical image preprocessing workloads."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            try:
                from django.conf import settings
                if settings.configured and hasattr(settings, "PROCESSED_IMAGE_DIR"):
                    self.output_dir = Path(settings.PROCESSED_IMAGE_DIR)
                elif settings.configured and hasattr(settings, "BASE_DIR"):
                    self.output_dir = Path(settings.BASE_DIR) / "data_storage" / "processed_medical_images"
                else:
                    self.output_dir = Path(__file__).resolve().parent.parent / "data_storage" / "processed_medical_images"
            except Exception:
                self.output_dir = Path(__file__).resolve().parent.parent / "data_storage" / "processed_medical_images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process(
        self,
        input_image_path: Union[str, Path] = None,
        operation: str = "normalize_clahe",
        target_resolution: int = 224,
        task_id: str = "WORKLOAD",
        clip_limit: float = 0.03,
        image_path: Union[str, Path] = None,
        raise_on_error: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute real medical image preprocessing on the given image.

        Operations supported:
        - 'normalize_clahe': Grayscale -> Resize -> Intensity Normalization -> CLAHE enhancement
        - 'grayscale_resize': Grayscale -> Resize only
        - 'normalize_only': Grayscale -> Resize -> Intensity Normalization
        - 'clahe_only': Grayscale -> CLAHE enhancement (maintains native resolution)

        Measures processing duration using high-resolution monotonic timer (time.perf_counter).
        """
        t_start = time.perf_counter()
        raw_path = input_image_path if input_image_path is not None else image_path
        if raw_path is None:
            if raise_on_error:
                raise ValueError("Must provide either input_image_path or image_path.")
            return {"success": False, "error": "No image path provided."}

        input_path = Path(raw_path)
        if not input_path.exists():
            if raise_on_error:
                raise FileNotFoundError(f"Input image file not found: {input_path}")
            return {
                "success": False,
                "error": f"Input image file not found: {input_path}",
                "input_path": str(input_path),
                "output_path": None,
                "processing_time_s": 0.0,
                "processing_time_sec": 0.0,
            }

        # 1. Validation
        is_valid, error_msg, in_meta = validate_image_file(input_path)
        if not is_valid:
            duration = time.perf_counter() - t_start
            if raise_on_error:
                raise ValueError(f"Corrupted or invalid image: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "input_path": str(input_path),
                "output_path": None,
                "processing_time_s": round(duration, 6),
                "processing_time_sec": round(duration, 6),
                "input_checksum": None,
                "output_checksum": None,
                "operation": operation,
                "task_id": task_id,
            }

        input_checksum = in_meta["sha256"]

        try:
            with Image.open(input_path) as img:
                # 2. Convert to Grayscale if not already
                if img.mode != "L":
                    gray_img = ImageOps.grayscale(img)
                else:
                    gray_img = img.copy()

                orig_w, orig_h = gray_img.size

                # 3. Resize if target_resolution specified and operation requests it
                target_res = int(target_resolution) if target_resolution else 224
                if operation in ("normalize_clahe", "grayscale_resize", "normalize_only"):
                    if (orig_w, orig_h) != (target_res, target_res):
                        # Use high-quality Lanczos resampling
                        processed_img = gray_img.resize((target_res, target_res), Image.Resampling.LANCZOS)
                    else:
                        processed_img = gray_img
                else:
                    processed_img = gray_img

                # Convert to numpy array for numerical preprocessing
                arr = np.array(processed_img, dtype=np.float32)

                # 4. Pixel Intensity Normalization to [0.0, 1.0]
                min_val = float(np.min(arr))
                max_val = float(np.max(arr))
                if max_val > min_val:
                    norm_arr = (arr - min_val) / (max_val - min_val)
                else:
                    norm_arr = np.zeros_like(arr)

                # 5. Optional CLAHE (Contrast-Limited Adaptive Histogram Equalization)
                if operation in ("normalize_clahe", "clahe_only"):
                    if SKIMAGE_AVAILABLE:
                        # CLAHE via scikit-image on normalized float array [0.0, 1.0]
                        enhanced_arr = exposure.equalize_adapthist(norm_arr, clip_limit=clip_limit)
                        # Scale back to 8-bit [0, 255] for image saving
                        final_arr = np.clip(enhanced_arr * 255.0, 0, 255).astype(np.uint8)
                    else:
                        # Fallback to standard PIL histogram equalization
                        temp_pil = Image.fromarray((norm_arr * 255.0).astype(np.uint8), mode="L")
                        temp_pil = ImageOps.equalize(temp_pil)
                        final_arr = np.array(temp_pil, dtype=np.uint8)
                elif operation in ("normalize_only",):
                    final_arr = np.clip(norm_arr * 255.0, 0, 255).astype(np.uint8)
                else:
                    # grayscale_resize only
                    final_arr = np.array(processed_img, dtype=np.uint8)

                # 6. Save processed result to output directory
                output_filename = f"{task_id}_{operation}_{target_res}x{target_res}.png"
                output_path = self.output_dir / output_filename
                out_pil = Image.fromarray(final_arr, mode="L")
                out_pil.save(output_path, format="PNG", optimize=True)

            # 7. Compute output SHA-256 checksum and finish timing
            output_checksum = calculate_sha256(output_path)
            t_end = time.perf_counter()
            duration_sec = t_end - t_start

            return {
                "success": True,
                "error": None,
                "task_id": task_id,
                "operation": operation,
                "target_resolution": target_res,
                "input_path": str(input_path),
                "output_path": str(output_path),
                "input_checksum": input_checksum,
                "output_checksum": output_checksum,
                "original_dimensions": f"{orig_w}x{orig_h}",
                "processed_dimensions": f"{final_arr.shape[1]}x{final_arr.shape[0]}",
                "input_size_bytes": in_meta["file_size_bytes"],
                "output_size_bytes": output_path.stat().st_size,
                "processing_time_s": round(duration_sec, 6),
                "processing_time_sec": round(duration_sec, 6),
                "parameters": {
                    "operation": operation,
                    "target_resolution": target_res,
                    "clip_limit": clip_limit,
                    "skimage_clahe_used": SKIMAGE_AVAILABLE and operation in ("normalize_clahe", "clahe_only"),
                },
            }
        except Exception as exc:
            duration = time.perf_counter() - t_start
            return {
                "success": False,
                "error": f"Image processing failed: {exc}",
                "task_id": task_id,
                "operation": operation,
                "input_path": str(input_path),
                "output_path": None,
                "input_checksum": input_checksum,
                "output_checksum": None,
                "processing_time_sec": round(duration, 6),
            }
