"""
data_pipeline
=============

Dataset collection, validation, cleaning, preprocessing, feature
engineering, statistics and management for the SecureDT project.

Pipeline honour rules:

* RAW files under ``datasets/raw/`` are never modified.
* Only ``datasets/processed/`` may be written.
* Every record count, size and class distribution is computed from the
   actual files on disk - never from a constant.
* ``ATTACKED`` vs ``BENIGN`` separation is preserved at every stage.
* Downloads that require manual action print MANUAL DOWNLOAD REQUIRED
   and show the official source page; nothing is invented.
"""

from .dataset_manager import DatasetManager  # noqa: F401

__all__ = ["DatasetManager"]