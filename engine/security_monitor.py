"""
Security Monitor
================
Aggregates security events, tracks threat levels, and provides the
security overview dashboard data. Works with the AttackSimulator and
DigitalTwin to give a unified security posture view.

All values are computed from virtual simulation state. No real systems
are monitored.
"""

import os
import sys
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class SecurityMonitor:
    """Centralized security event aggregation and threat tracking."""

    def __init__(self):
        self.alerts = []
        self.alert_count = 0
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self.alerts = []
            self.alert_count = 0

    def record_event(self, kind, message, resource=None, severity="info", **extra):
        """Record a security event into the immutable-style log."""
        with self._lock:
            self.alert_count += 1
            entry = {
                "event_id": self.alert_count,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "kind": kind,
                "message": message,
                "resource": resource,
                "severity": severity,
            }
            entry.update(extra)
            self.alerts.append(entry)
            return entry

    def threat_level(self, digital_twin):
        """Derive the current threat level from Digital Twin resource states."""
        states = digital_twin.states()
        risks = [r.get("security_risk", 0.0) for r in states]
        if not risks:
            return "LOW"
        max_risk = max(risks)
        avg_risk = sum(risks) / len(risks)
        if max_risk >= 0.80 or avg_risk >= 0.50:
            return "CRITICAL"
        if max_risk >= 0.60 or avg_risk >= 0.35:
            return "HIGH"
        if max_risk >= 0.30 or avg_risk >= 0.15:
            return "MEDIUM"
        return "LOW"

    def overview(self, digital_twin, attack_simulator):
        """Build the security overview payload for the monitor dashboard."""
        states = digital_twin.states()
        risks = [r.get("security_risk", 0.0) for r in states]
        max_risk = max(risks) if risks else 0.0
        avg_risk = sum(risks) / len(risks) if risks else 0.0
        threat = self.threat_level(digital_twin)

        affected = [
            r["resource_id"] for r in states if r.get("status") not in ("SAFE",)
        ]
        quarantined = [
            r["resource_id"] for r in states if r.get("status") == "QUARANTINED"
        ]

        total_attacks = getattr(attack_simulator, "total_attacks", 0)
        detected = getattr(attack_simulator, "detected", 0)
        mitigations = getattr(attack_simulator, "mitigations", 0)
        detection_score = round(detected / max(total_attacks, 1), 3)

        return {
            "threat_level": threat,
            "max_risk": round(max_risk, 4),
            "avg_risk": round(avg_risk, 4),
            "total_attacks": total_attacks,
            "detected": detected,
            "detection_score": detection_score,
            "mitigations": mitigations,
            "affected_resources": affected,
            "quarantined_resources": quarantined,
            "active_attack": getattr(attack_simulator, "active_attack", None),
            "resource_count": len(states),
            "healthy_count": sum(1 for r in states if r.get("status") == "SAFE"),
        }

    def get_alerts(self, limit=100):
        """Return the most recent security alerts."""
        with self._lock:
            return list(reversed(self.alerts[-limit:]))

    def filter_alerts(self, kind=None, resource=None, limit=50):
        """Return alerts filtered by kind and/or resource."""
        with self._lock:
            filtered = self.alerts
            if kind:
                filtered = [
                    a for a in filtered if a.get("kind", "").upper() == kind.upper()
                ]
            if resource:
                filtered = [a for a in filtered if a.get("resource", "") == resource]
            return list(reversed(filtered[-limit:]))


if __name__ == "__main__":
    sm = SecurityMonitor()
    sm.record_event("TEST", "Security monitor initialized")
    sm.record_event("SCAN", "Port scan detected", resource="MEC-2", severity="warning")
    print("Alerts:", sm.get_alerts())
