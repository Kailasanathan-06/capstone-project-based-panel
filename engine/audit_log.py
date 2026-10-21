"""
Audit Logger
============
Thread-safe structured logging with categories:

    INFO, WARNING, SECURITY, ERROR, AUDIT

Entries are kept in a bounded in-memory ring buffer and (optionally) appended
to a CSV file. Callers must never log secrets (passwords, API keys, tokens,
sensitive payloads).

The Audit Log page reads `/api/audit` for the last entries and a category
breakdown.
"""

import csv
import os
import sys
import threading
import time
import uuid
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402

CATEGORIES = ("INFO", "WARNING", "SECURITY", "ERROR", "AUDIT")


class AuditLogger:
    def __init__(self, capacity=5000, csv_path=None):
        self.capacity = capacity
        self._lock = threading.Lock()
        self._entries = deque(maxlen=capacity)
        self.csv_path = csv_path or os.path.join(config.DATASET_DIR, "audit_log.csv")

    def record(self, category, message, detail=None, module=None):
        category = category.upper() if category.upper() in CATEGORIES else "INFO"
        entry = {
            "id": uuid.uuid4().hex[:10],
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "module": module or "app",
            "message": str(message),
            "detail": (detail or {}),
        }
        with self._lock:
            self._entries.append(entry)
            self._write_csv(entry)
        return entry

    def info(self, message, module=None):
        return self.record("INFO", message, module=module)

    def warn(self, message, module=None):
        return self.record("WARNING", message, module=module)

    def security(self, message, module=None):
        return self.record("SECURITY", message, module=module)

    def error(self, message, module=None):
        return self.record("ERROR", message, module=module)

    def audit(self, message, module=None):
        return self.record("AUDIT", message, module=module)

    def entries(self, limit=500, category=None):
        with self._lock:
            items = list(self._entries)
        if category:
            items = [e for e in items if e["category"].upper() == category.upper()]
        items = items[-limit:] if limit else items
        return items

    def counts(self):
        with self._lock:
            items = list(self._entries)
        c = {k: 0 for k in CATEGORIES}
        for e in items:
            c[e["category"]] = c.get(e["category"], 0) + 1
        c["total"] = len(items)
        return c

    def clear(self):
        with self._lock:
            self._entries.clear()

    def _write_csv(self, entry):
        try:
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
            exists = os.path.exists(self.csv_path)
            with open(self.csv_path, "a", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                if not exists:
                    writer.writerow(["id", "time", "category", "module", "message"])
                writer.writerow(
                    [
                        entry["id"],
                        entry["time"],
                        entry["category"],
                        entry["module"],
                        entry["message"],
                    ]
                )
        except Exception:  # noqa: BLE001
            pass  # logging must never crash the app


if __name__ == "__main__":
    lg = AuditLogger(csv_path=os.path.join(config.DATASET_DIR, "_audit_demo.csv"))
    lg.audit("System started", module="app")
    lg.security("CSRF token rotated", module="security")
    print(lg.counts())
    print(lg.entries(5))
