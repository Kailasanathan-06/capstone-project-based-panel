"""
Live Telemetry Adapter (optional - Zeek)
========================================
Optional integration with Zeek structured logs. The application works
perfectly without Zeek: when Zeek (or a log directory) is not available the
adapter reports `available: False` and the UI shows:

    "Live telemetry unavailable. Simulation mode is active."

Supported log types (parsed defensively, never executed):

    conn / dns / http / files / ssl / ssh / notice / weird

Flow (only when the user supplies a Zeek log dir):

    PCAP -> Zeek -> structured logs -> normalization -> security pipeline

This module performs no outbound network activity.
"""

import glob
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

import config  # noqa: E402

LOG_TYPES = ["conn", "dns", "http", "files", "ssl", "ssh", "notice", "weird"]

# A small set of fields normalised from Zeek conn.log out of the box
ZEEK_CONN_FIELDS = {
    "timestamp": ["ts"],
    "src": ["id.orig_h"],
    "dst": ["id.resp_h"],
    "bytes": ["orig_bytes"],
    "protocol": ["proto"],
    "duration": ["duration"],
    "label": [],
}


def zeek_binary():
    """Return the path to a detected zeek binary, or None."""
    for name in ("zeek", "zeek.exe", "bro", "bro.exe"):
        import shutil

        p = shutil.which(name)
        if p:
            return p
    return None


def _parse_zeek_log(path):
    """Parse a Zeek ASCII log using its #fields header (memory-friendly)."""
    fields = []
    sep = "\t"
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = []
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("#separator"):
                sep = line.split()[-1].replace("\\x09", "\t")
                continue
            if line.startswith("#fields"):
                fields = line[len("#fields") + 1 :].split(sep)
                continue
            if line.startswith("#"):
                continue
            if not line.strip():
                continue
            lines.append(line.split(sep))
    if not fields:
        return pd.DataFrame(), []
    df = pd.DataFrame(lines, columns=[f.strip() for f in fields])
    return df, fields


class TelemetryAdapter:
    BINARY_TTL = 15.0  # seconds before re-scanning PATH for zeek
    LOGS_TTL = 5.0  # seconds between directory rescans

    def __init__(self, log_dir=None):
        self.log_dir = log_dir
        self.events = []
        self.last_timestamp = None
        self._zeek_binary = None
        self._zeek_found_at = 0.0
        self._logs = []
        self._logs_dir = None
        self._logs_at = 0.0

    def _find_zeek(self):
        """Cache the (expensive) PATH scan for the zeek binary."""
        now = time.monotonic()
        if self._zeek_found_at and now - self._zeek_found_at < self.BINARY_TTL:
            return self._zeek_binary
        p = zeek_binary()
        self._zeek_binary = p
        self._zeek_found_at = now
        return p

    # ------------------------------------------------------------------
    def detect(self, log_dir=None):
        """True if a Zeek binary or a Zeek log directory is available."""
        if log_dir:
            self.log_dir = log_dir
            return len(self.available_logs(log_dir)) > 0
        if self.log_dir and len(self.available_logs(self.log_dir)) > 0:
            return True
        return bool(self._find_zeek())

    def available_logs(self, log_dir=None):
        """List *.log files that look like Zeek output (cached, short TTL)."""
        log_dir = log_dir or self.log_dir
        if not log_dir or not os.path.isdir(log_dir):
            return []
        now = time.monotonic()
        if (
            self._logs_dir == log_dir
            and self._logs_at
            and now - self._logs_at < self.LOGS_TTL
        ):
            return self._logs
        found = []
        for pattern in ["*.log", "*_*.log"]:
            for p in glob.glob(os.path.join(log_dir, pattern)):
                base = os.path.basename(p)
                for t in LOG_TYPES:
                    if base.startswith(t) or base.startswith(t + "."):
                        found.append(p)
                        break
        self._logs, self._logs_dir, self._logs_at = found, log_dir, now
        return found

    def status_payload(self):
        logs = self.available_logs() if self.log_dir else []
        detected = bool(self.log_dir or self._find_zeek())
        available = detected or bool(logs)
        return {
            "ok": True,
            "available": available,
            "mode": "LIVE TELEMETRY" if available else "SIMULATION DATA",
            "message": (
                "Live telemetry unavailable. Simulation mode is active."
                if not available
                else f"Live telemetry available ({len(logs)} Zeek logs)"
            ),
            "binary": self._find_zeek(),
            "log_dir": self.log_dir,
            "logs": [os.path.basename(p) for p in logs[:12]],
            "log_types": LOG_TYPES,
        }

    def parse_log(self, path):
        """Parse one Zeek log into pandas rows."""
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        return _parse_zeek_log(path)

    def ingest(self, log_dir=None, max_rows=5000):
        """Ingest available Zeek logs into normalized event dicts."""
        self.log_dir = log_dir or self.log_dir
        if not self.log_dir:
            raise ValueError("no log directory configured")
        logs = self.available_logs(self.log_dir)
        if not logs:
            raise ValueError("no Zeek logs found")
        out = []
        for p, t in ((p, os.path.basename(p).split(".")[0]) for p in logs):
            try:
                df, fields = _parse_zeek_log(p)
            except Exception:  # noqa: BLE001
                continue
            if df.empty:
                continue
            for i in range(min(len(df), max_rows)):
                row = df.iloc[i]
                ev = {
                    "event_id": f"zeek-{t}-{i}",
                    "source_type": f"zeek_{t}",
                    "timestamp": _cell(row, "ts"),
                    "src": _cell(row, "id.orig_h"),
                    "dst": _cell(row, "id.resp_h"),
                    "protocol": _cell(row, "proto"),
                    "bytes": _num(_cell(row, "orig_bytes")),
                    "duration": _num(_cell(row, "duration")),
                    "label": "normal",
                    "metadata": {"zeek_log": os.path.basename(p)},
                }
                out.append(ev)
                if len(out) >= max_rows:
                    self.events = out
                    return out
        self.events = out
        return out

    def active_events(self, limit=200):
        return self.events[-limit:]


def _cell(row, field):
    if isinstance(row, dict):
        return row.get(field)
    try:
        return row[field] if field in row.index else None
    except (KeyError, TypeError):
        return None


def _num(v):
    if v is None:
        return 0.0
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return 0.0


if __name__ == "__main__":
    t = TelemetryAdapter()
    print(t.status_payload()["message"])
    print("zeek binary:", zeek_binary())
