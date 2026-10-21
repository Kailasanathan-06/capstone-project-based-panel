"""
Security Risk Engine
====================
Computes a normalised security risk in [0, 1] for a resource given attack
conditions, privacy sensitivity, trust, workload and attack exposure.

The model is intentionally centralised in this module so the equations can
be calibrated later against the base paper.

Conceptual model:
    SecurityRisk = base_attack_risk
                 + severity_factor
                 + privacy_factor
                 + trust_penalty
                 + workload_factor
                 + exposure_factor
    normalised to [0,1]

Risk bands:
    0.00 - 0.30 : LOW
    0.30 - 0.60 : MEDIUM
    0.60 - 0.80 : HIGH
    0.80 - 1.00 : CRITICAL
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


def risk_level(risk):
    """Map a continuous risk value in [0,1] to a named band."""
    risk = max(0.0, min(1.0, float(risk)))
    for threshold, label in config.RISK_LEVELS:
        if risk < threshold:
            return label
    return "CRITICAL"


class RiskEngine:
    """Compute, combine and classify security risk for a resource."""

    def __init__(self):
        self.model = dict(config.RISK_MODEL)

    def compute_risk(
        self,
        attack_type=None,
        severity=0.0,
        privacy=0.0,
        trust=1.0,
        workload=0.0,
        exposure=0.0,
    ):
        """
        Return the security risk for a resource state, bounded to [0, 1].

        Conceptual model:
            ambient  = workload_weight * workload
            attack   = severity * (base_attack_risk
                                   + privacy_weight * privacy
                                   + trust_weight   * (1 - trust)
                                   + exposure_weight * exposure)
            risk     = idle_risk          (no attack, idle resource)
                     = ambient + attack   (otherwise), clipped to [0,1]

        Parameters
        ----------
        attack_type : str or None
        severity     : float in [0,1]
        privacy      : float in [0,1] - privacy sensitivity of the workload
        trust        : float in [0,1] - current trust of the resource
        workload     : float in [0,1] - normalised current utilisation
        exposure     : float in [0,1] - attack exposure attribute
        """
        w = self.model

        if not attack_type:
            # no active attack: risk grows mildly with load
            raw = w["idle_risk"] + w["workload_weight"] * workload
            return round(max(0.0, min(1.0, raw)), 4)

        base = config.ATTACK_BASE_RISK.get(attack_type, 0.30)
        ambient = w["workload_weight"] * workload
        attack = severity * (
            base
            + w["privacy_weight"] * privacy
            + w["trust_weight"] * (1.0 - trust)
            + w["exposure_weight"] * exposure
        )
        risk = ambient + attack
        risk = max(0.0, min(1.0, risk))
        return round(risk, 4)

    def status_for(self, risk):
        """Return a short status string for a risk value."""
        return risk_level(risk)


def max_risk(risks):
    """Return the maximum risk across an iterable of resources."""
    if not risks:
        return 0.0
    return max(float(r) for r in risks)


if __name__ == "__main__":
    engine = RiskEngine()
    print("Risk model unit check:")
    print("  idle            :", engine.compute_risk())
    print(
        "  DDoS 0.8 highpriv:",
        engine.compute_risk(
            attack_type="DDoS",
            severity=0.8,
            privacy=0.9,
            trust=0.4,
            workload=0.9,
            exposure=0.5,
        ),
    )
    print(
        "  level           :",
        risk_level(
            engine.compute_risk(
                attack_type="DDoS",
                severity=0.8,
                privacy=0.9,
                trust=0.4,
                workload=0.9,
                exposure=0.5,
            )
        ),
    )
