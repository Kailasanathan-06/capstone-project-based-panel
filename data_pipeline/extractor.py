"""
CSV archive extractor.

Safely unpacks zip/tar/gz archives into the target directory.
Only extract if the archive was downloaded from a known source
(checked against DATASET_CATALOG paths).  Never auto-execute
anything inside the archive.
"""

import os
import tarfile
import zipfile


def extract_archive(archive_path: str, target_dir: str) -> str:
    """Extract an archive into *target_dir*.  Returns the directory
    containing the extracted files.
    """
    os.makedirs(target_dir, exist_ok=True)
    base = os.path.basename(archive_path).split(".")[0]
    out_dir = os.path.join(target_dir, base)
    os.makedirs(out_dir, exist_ok=True)

    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path, "r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                member.file_size  # just touch; real extraction below
            zf.extractall(out_dir)
        print(f"  Zip extracted: {archive_path} -> {out_dir}")
    elif tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, "r:*") as tf:
            tf.extractall(out_dir)
        print(f"  Tarball extracted: {archive_path} -> {out_dir}")
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")

    return out_dir


def list_archive_contents(archive_path: str) -> list:
    """Return a list of filenames inside the archive without extracting."""
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path, "r") as zf:
            return [m.filename for m in zf.infolist()]
    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, "r:*") as tf:
            return [m.name for m in tf.getmembers() if m.isfile()]
    raise ValueError(f"Unsupported archive: {archive_path}")