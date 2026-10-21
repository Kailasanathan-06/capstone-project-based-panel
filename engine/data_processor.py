"""
Data Processor
==============
Validates, cleans and analyses task data as it flows through the pipeline.
Reused by the frontend processing animation and the live processing API.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class DataProcessor:
    """Pipeline validation/cleaning/preparation for task records."""

    STAGES = [
        "raw",
        "validation",
        "cleaning",
        "feature_extraction",
        "privacy",
        "security",
        "ai_risk",
        "digital_twin",
        "genetic_algorithm",
        "resource",
        "execution",
    ]

    def validate_row(self, row):
        """Return (ok, list_of_issues) for a dict-like task row."""
        issues = []
        if row.get("data_size_mb") is None or not isinstance(
            row.get("data_size_mb"), (int, float)
        ):
            issues.append("invalid data_size_mb")
        if row.get("cpu_cycles_giga") is None or not isinstance(
            row.get("cpu_cycles_giga"), (int, float)
        ):
            issues.append("invalid cpu_cycles")
        if row.get("memory_mb") is None or not isinstance(
            row.get("memory_mb"), (int, float)
        ):
            issues.append("invalid memory")
        if row.get("deadline_ms") is None or not isinstance(
            row.get("deadline_ms"), (int, float)
        ):
            issues.append("invalid deadline")
        if not 0.0 <= float(row.get("privacy_sensitivity", 0.0)) <= 1.0:
            issues.append("privacy out of range")
        if not 0.0 <= float(row.get("security_sensitivity", 0.0)) <= 1.0:
            issues.append("security out of range")
        if not isinstance(row.get("task_id"), str):
            issues.append("missing task_id")
        return (len(issues) == 0, issues)

    def clean_row(self, row):
        """Return a cleaned copy with NaN handled and numeric coercions."""
        cleaned = dict(row)
        numeric = [
            "data_size_mb",
            "cpu_cycles_giga",
            "memory_mb",
            "deadline_ms",
            "privacy_sensitivity",
            "security_sensitivity",
            "arrival_rate",
            "expected_latency_ms",
            "expected_energy_j",
            "attack_exposure",
        ]
        for key in numeric:
            try:
                cleaned[key] = float(cleaned.get(key, 0.0) or 0.0)
            except (TypeError, ValueError):
                cleaned[key] = 0.0
        return cleaned

    def feature_columns(self, task):
        """Return the numeric feature set used by AI / GA."""
        return {
            "data_size_mb": float(task.get("data_size_mb", 0.0)),
            "cpu_cycles_giga": float(task.get("cpu_cycles_giga", 0.0)),
            "memory_mb": float(task.get("memory_mb", 0.0)),
            "deadline_ms": float(task.get("deadline_ms", 0.0)),
            "privacy_sensitivity": float(task.get("privacy_sensitivity", 0.0)),
            "security_sensitivity": float(task.get("security_sensitivity", 0.0)),
            "arrival_rate": float(task.get("arrival_rate", 0.0)),
            "expected_latency_ms": float(task.get("expected_latency_ms", 0.0)),
            "expected_energy_j": float(task.get("expected_energy_j", 0.0)),
            "attack_exposure": float(task.get("attack_exposure", 0.0)),
        }

    def privacy_level(self, task):
        v = float(task.get("privacy_sensitivity", 0.0))
        return "HIGH" if v >= 0.65 else ("MEDIUM" if v >= 0.35 else "LOW")

    def security_level(self, task):
        v = float(task.get("security_sensitivity", 0.0))
        return "HIGH" if v >= 0.65 else ("MEDIUM" if v >= 0.35 else "LOW")

    def process_task(self, task):
        """Run the full single-task pipeline and return a result dict."""
        ok, issues = self.validate_row(task)
        if not ok:
            return {
                "processed": False,
                "task_id": task.get("task_id"),
                "issues": issues,
            }
        cleaned = self.clean_row(task)
        return {
            "processed": True,
            "task_id": cleaned.get("task_id"),
            "privacy_level": self.privacy_level(cleaned),
            "security_level": self.security_level(cleaned),
            "deadline_ok": cleaned.get("deadline_ms", 0) >= 150,
            "features": self.feature_columns(cleaned),
        }


if __name__ == "__main__":
    dp = DataProcessor()
    t = {
        "task_id": "T1",
        "data_size_mb": 8.4,
        "cpu_cycles_giga": 3.2,
        "memory_mb": 512,
        "deadline_ms": 650,
        "privacy_sensitivity": 0.8,
        "security_sensitivity": 0.6,
        "attack_exposure": 0.5,
    }
    print(dp.process_task(t))
