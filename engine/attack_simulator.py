"""
Attack Simulator (Strengthened)
===============================
Simulates a controlled, visual-only attacker. This module NEVER interacts with
real networks, IP addresses, devices or systems. The "hacker" is purely a
software actor that perturbs the virtual Digital Twin state.

Strengthened capabilities (still 100% simulated, in-process, no real traffic):
  * more attack types (DDoS, Eavesdropping, Tampering, Data_Poisoning,
    Credential_Abuse, Brute_Force, Ransomware, APT, MITM, Supply_Chain)
  * Lockheed-Martin style kill-chain phases (RECON -> WEAPONIZE -> DELIVER ->
    EXPLOIT -> PERSIST -> C2 -> OBJECTIVES) that advance during an attack
  * persistence attempts (if the attack is not mitigated quickly the risk
    stays elevated after the main burst)
  * defense-evasion probability that lowers detection confidence
  * adaptive escalation: higher severity drives deeper phases

Everything here operates on virtual variables only
(cpu, memory, latency, trust, security_risk, availability...).
"""

import os
import random
import sys
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from engine.risk_engine import RiskEngine

ATTACK_LABELS = {
    "DDoS": "DDoS / Resource Overload",
    "Eavesdropping": "Eavesdropping",
    "Tampering": "Data Tampering",
    "Data_Poisoning": "Data Poisoning",
    "Credential_Abuse": "Credential Abuse",
    "Brute_Force": "Brute Force",
    "Ransomware": "Simulated Ransomware",
    "APT": "Advanced Persistent Threat",
    "MITM": "Man-in-the-Middle",
    "Supply_Chain": "Simulated Supply Chain Attack",
}

# More aggressive risk contribution per attack type (0..1)
ATTACK_BASE_RISK = {
    "DDoS": 0.55,
    "Eavesdropping": 0.30,
    "Tampering": 0.40,
    "Data_Poisoning": 0.35,
    "Credential_Abuse": 0.42,
    "Brute_Force": 0.60,
    "Ransomware": 0.80,
    "APT": 0.85,
    "MITM": 0.70,
    "Supply_Chain": 0.90,
}

KILL_CHAIN = [
    "RECONNAISSANCE",
    "WEAPONIZATION",
    "DELIVERY",
    "EXPLOITATION",
    "PERSISTENCE",
    "COMMAND_AND_CONTROL",
    "ACTIONS_ON_OBJECTIVES",
]

# phase index -> extra risk multiplier applied while the attack advances
PHASE_RISK_MULT = [0.0, 0.1, 0.25, 0.45, 0.60, 0.75, 1.0]


class AttackSimulator:
    def __init__(
        self, digital_twin, risk_engine=None, seed=None, security_monitor=None
    ):
        self.dt = digital_twin
        self.risk_engine = risk_engine or RiskEngine()
        self.rng = random.Random(seed or config.DATASET_SEED)
        self.active_attack = None
        self.attack_log = []  # list of dicts (timeline events)
        self.event_count = 0
        self.total_attacks = 0
        self.mitigations = 0
        self.detected = 0
        self.security_monitor = security_monitor
        self._lock = threading.Lock()
        self._persist_job = None
        self._running = False

    def reset(self):
        with self._lock:
            self.active_attack = None
            self.attack_log = []
            self.event_count = 0
            self.total_attacks = 0
            self.mitigations = 0
            self.detected = 0
            self._running = False

    def _log(self, kind, message, resource=None, **extra):
        with self._lock:
            return self._log_inner(kind, message, resource=resource, **extra)

    def _log_inner(self, kind, message, resource=None, **extra):
        """Append a log entry. CALLER MUST HOLD self._lock."""
        self.event_count += 1
        entry = {
            "event_id": self.event_count,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "kind": kind,
            "message": message,
            "resource": resource,
        }
        entry.update(extra)
        self.attack_log.append(entry)
        if self.security_monitor:
            sev = (
                "critical"
                if kind in ("IMPACT", "PERSIST")
                else ("warning" if kind in ("START", "DETECT", "PHASE") else "info")
            )
            sm_extra = {k: v for k, v in extra.items() if k != "severity"}
            self.security_monitor.record_event(
                kind, message, resource=resource, severity=sev, **sm_extra
            )
        return entry

    def start_attack(self, attack_type, target, severity):
        """Launch a simulated attack on a virtual resource.

        Returns a dict with before/after state and the active attack record.
        """
        with self._lock:
            target = target.upper()
            if target not in self.dt.resources:
                return {"ok": False, "message": f"Unknown target {target}"}

            if self.active_attack and self.active_attack.get("active"):
                return {"ok": False, "message": "An attack is already active"}

            severity = max(0.0, min(1.0, float(severity)))
            self.total_attacks += 1

            phase_count = max(1, int(round(3 + 4 * severity)))
            self._log_inner(
                "START",
                f"{ATTACK_LABELS.get(attack_type, attack_type)} "
                f"simulated against {target}",
                resource=target,
                severity=severity,
            )
            self._log_inner("ANIM", "Hacker spawning attack packets", resource=target)

            # defense evasion: harder to detect with higher severity
            evaded = self.rng.random() < 0.15 + 0.25 * severity
            detected_conf = self.rng.uniform(0.6, 0.99)
            detect = not evaded

            self._log_inner(
                "DETECT",
                (
                    "Suspicious activity detected " "(simulated anomaly)"
                    if detect
                    else "Activity evading detection (simulated stealth)"
                ),
                resource=target,
                detection_score=round(detected_conf, 3),
            )

            base = ATTACK_BASE_RISK.get(attack_type, 0.5)
            result = self.dt.apply_attack(
                target,
                attack_type,
                severity,
                risk_bonus=base * PHASE_RISK_MULT[phase_count - 1] * severity,
            )

            if detect:
                self.detected += 1

            phases = KILL_CHAIN[:phase_count]
            self._log_inner(
                "PHASE",
                f"Kill-chain advanced to "
                f"{phases[-1]} ({phase_count}/{len(KILL_CHAIN)})",
                resource=target,
                phase=phases[-1],
                phase_no=phase_count,
            )

            after_risk = result["after"]["security_risk"]
            self._log_inner(
                "IMPACT",
                f"{target} risk rose to {after_risk:0.2f}",
                resource=target,
                pre_risk=result["before"]["security_risk"],
                post_risk=after_risk,
                detected=detect,
                detection_score=round(detected_conf, 3),
            )
            self._log_inner(
                "TWIN", "Digital Twin updated virtual state", resource=target
            )
            self._log_inner(
                "NOTIFY", "Scheduler notified of risk change", resource=target
            )

            self.active_attack = {
                "active": True,
                "attack_type": attack_type,
                "target": target,
                "severity": severity,
                "pre_risk": result["before"]["security_risk"],
                "post_risk": result["after"]["security_risk"],
                "phases": phases,
                "phase_no": phase_count,
                "detected": detect,
                "detection_score": round(detected_conf, 3),
                "started": datetime.now().isoformat(),
                "state": "ATTACKING",
            }

            # scheduled persistence: risk stays elevated if not mitigated
            if (
                attack_type in ("APT", "Ransomware", "Supply_Chain", "Credential_Abuse")
                and severity >= 0.5
            ):
                self._schedule_persistence(target, severity)

        return {
            "ok": True,
            "before": result["before"],
            "after": result["after"],
            "attack": self.active_attack,
        }

    def _schedule_persistence(self, target, severity):
        """After the main attack burst, keep risk elevated for a while."""
        delay = 1.2
        boost = 0.08 + 0.2 * severity
        try:
            if self._persist_job and self._persist_job.is_alive():
                return
            self._running = True

            def work():
                time.sleep(delay)
                with self._lock:
                    if not self._running:
                        return
                    res = self.dt.resources.get(target)
                    if res and res.available:
                        res.security_risk = max(
                            0.0, min(1.0, res.security_risk + boost)
                        )
                        self._log_inner(
                            "PERSIST",
                            f"Persistent presence on {target} keeps risk elevated",
                            resource=target,
                            post_risk=round(res.security_risk, 3),
                        )
                        self._running = False

            import threading as _th

            self._persist_job = _th.Thread(target=work, daemon=True)
            self._persist_job.start()
        except Exception:  # noqa: BLE001
            self._running = False

    def mitigate(self):
        """Respond to an active attack: quarantine the target and log it."""
        with self._lock:
            if not (self.active_attack and self.active_attack.get("active")):
                return {"ok": False, "message": "No active attack to mitigate"}

            target = self.active_attack["target"]
            self.mitigations += 1
            self._running = False
            self._log_inner(
                "MITIGATE", "Quarantining high-risk resource", resource=target
            )

            quarantined = self.dt.quarantine(target)
            self._log_inner(
                "TWIN", "Digital Twin set resource to QUARANTINED", resource=target
            )
            self._log_inner("SCHED", "GA re-optimisation started", resource=target)
            self._log_inner(
                "REROUTE", f"Tasks rerouted away from {target}", resource=target
            )
            self._log_inner("SECURE", "Secure re-execution continuing", resource=target)

            self.active_attack["active"] = False
            self.active_attack["mitigated"] = True
            self.active_attack["state"] = "MITIGATED"
            return {
                "ok": True,
                "quarantined": quarantined,
                "attack": self.active_attack,
            }

    def stop_active(self):
        """Stop any active attack and restore resources to SAFE without a
        full quarantine record. Returns True if an attack was stopped."""
        if not (self.active_attack and self.active_attack.get("active")):
            return False
        with self._lock:
            self._running = False
            self.active_attack["active"] = False
            self.active_attack["stopped"] = True
            self.active_attack["state"] = "STOPPED"
            state = self.dt.states()
            for res in state:
                if res["status"] in ("ATTACKED", "QUARANTINED", "COMPROMISED"):
                    self.dt.unquarantine(res["resource_id"])
            self._log_inner("STOP", "Active attack stopped; resources released")
        return True

    def status(self):
        targets = self.dt.states()
        return {
            "total_attacks": self.total_attacks,
            "detected": self.detected,
            "mitigations": self.mitigations,
            "active_attack": self.active_attack,
            "attack_labels": ATTACK_LABELS,
            "kill_chain": KILL_CHAIN,
            "resources": targets,
            "log": self.attack_log[-80:],
        }


if __name__ == "__main__":
    from engine.digital_twin import DigitalTwin

    dt = DigitalTwin()
    sim = AttackSimulator(dt)
    print("Attack types:", list(ATTACK_LABELS))
    print("Kill-chain:", KILL_CHAIN)
    r = sim.start_attack("DDoS", "MEC-2", 0.8)
    print("start ok:", r["ok"], "risk:", round(r["after"]["security_risk"], 3))
    print("phases:", sim.active_attack["phases"])
    sim.mitigate()
    print("mitigations:", sim.mitigations)
