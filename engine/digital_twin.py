"""
Digital Twin
============

Maintains the continuous virtual state of the real (simulated) resources:
LOCAL, registered MEC-1..N and CLOUD.

The Digital Twin tracks CPU, memory, network latency, energy, active tasks,
availability, trust and security risk, and exposes that state to the scheduler
and the frontend. When an attack event occurs the twin updates the affected
virtual resource so that the scheduler can react.

This version dynamically loads resources from the MEC Manager database.
Every registered MEC appears in the twin; `availability` mirrors its real
ONLINE/OFFLINE state taken from the latest heartbeat. No device is fabricated.
"""

import os
import random
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from mec_manager.models import MECAgent
from engine.risk_engine import RiskEngine


class ResourceState:
    """Virtual representation of a single real resource."""

    def __init__(self, resource_id, params):
        self.resource_id = resource_id
        self.resource_type = params["type"]
        self.max_cpu = params["max_cpu"]
        self.max_memory = params["max_memory"]
        self.base_latency_ms = params["base_latency_ms"]
        self.energy_rate = params["energy_rate"]
        self._trust = params["trust"]
        self._risk = params["security_risk"]
        self.privacy_loss_factor = params["privacy_loss_factor"]

        self.base_cpu = random.uniform(0.25, 0.45)
        self.base_mem = random.uniform(0.28, 0.48)
        self.cpu_utilization = self.base_cpu
        self.memory_utilization = self.base_mem
        self.network_latency_ms = self.base_latency_ms
        self.available = True
        self.active_tasks = 0
        self._status = "SAFE"
        self.lockdown = False
        self.owner = None
        self.kind = "core"

    # -- trust -------------------------------------------------------------
    @property
    def trust(self):
        return self._trust

    # -- security risk -----------------------------------------------------
    @property
    def security_risk(self):
        return self._risk

    @security_risk.setter
    def security_risk(self, value):
        self._risk = max(0.0, min(1.0, float(value)))
        self._refresh_status()

    @property
    def status(self):
        return self._status

    def _refresh_status(self):
        level = self.risk_level()
        if not self.available:
            self._status = "QUARANTINED"
        elif self._risk >= 0.80:
            self._status = "CRITICAL"
        elif self._risk >= 0.60:
            self._status = "HIGH RISK"
        elif self._risk >= 0.30:
            self._status = "WARNING"
        else:
            self._status = "SAFE"

    def risk_level(self):
        from engine.risk_engine import risk_level

        return risk_level(self._risk)

    # -- util operations ---------------------------------------------------
    def snap(self):
        """Return a plain dict snapshot for API / chart consumption."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "cpu_utilization": round(self.cpu_utilization, 3),
            "memory_utilization": round(self.memory_utilization, 3),
            "network_latency_ms": round(self.network_latency_ms, 1),
            "energy_rate": self.energy_rate,
            "trust_score": round(self._trust, 3),
            "security_risk": self._risk,
            "availability": self.available,
            "active_tasks": self.active_tasks,
            "status": self._status,
            "privacy_loss_factor": self.privacy_loss_factor,
            "owner": self.owner,
            "kind": self.kind,
        }

    def tick(self):
        """Light natural drift that simulates a living system."""
        if not self.available:
            return
        self.cpu_utilization = max(
            0.05, min(0.99, self.cpu_utilization + random.uniform(-0.02, 0.02))
        )
        self.memory_utilization = max(
            0.05, min(0.99, self.memory_utilization + random.uniform(-0.015, 0.015))
        )
        self.network_latency_ms = max(
            5.0, self.base_latency_ms * (1.0 + (self.cpu_utilization - 0.3) * 0.3)
        )
        # slow trust recovery
        self._trust = max(
            0.05, min(1.0, self._trust + 0.0005 if self._risk < 0.3 else self._trust)
        )


class DigitalTwin:
    """Virtual replica of the whole edge-cloud environment."""

    def __init__(self, risk_engine=None):
        self.risk_engine = risk_engine or RiskEngine()
        self.resources = {}
        self._load_mec_agents()
        self.tick_count = 0

    def _load_mec_agents(self):
        """Load every registered MEC agent from the database.

        The digital twin is a virtual mirror of the REAL devices: all registered
        agents appear, and `availability` reflects their true ONLINE/OFFLINE
        state from the latest heartbeat. No synthetic devices are fabricated.
        """
        # All registered agents (OFFLINE ones are mirrored as unavailable)
        agents = MECAgent.objects.all().select_related()

        # Always include LOCAL and CLOUD as baseline
        default_resources = {
            "LOCAL": {
                "type": "edge",
                "max_cpu": 8,
                "max_memory": 4096,
                "base_latency_ms": 180,
                "energy_rate": 4.1,
                "trust": 0.98,
                "security_risk": 0.05,
                "privacy_loss_factor": 0.08,
            },
            "CLOUD": {
                "type": "cloud",
                "max_cpu": 64,
                "max_memory": 32768,
                "base_latency_ms": 170,
                "energy_rate": 5.1,
                "trust": 0.86,
                "security_risk": 0.18,
                "privacy_loss_factor": 0.52,
            },
        }

        # Always mirror LOCAL and CLOUD even before any MEC registers
        for rid, params in default_resources.items():
            self.resources[rid] = ResourceState(rid, params)

        # Add registered MEC agents
        for agent in agents:
            resource_id = agent.device_id.upper()
            # Build resource params from agent info or defaults
            max_cpu = 16  # Default MEC capacity
            max_memory = 8192
            base_latency_ms = 100  # Typical MEC latency
            energy_rate = 2.5
            trust = 0.93
            security_risk = 0.10
            privacy_loss_factor = 0.20

            self.resources[resource_id] = ResourceState(
                resource_id,
                {
                    "type": "mec",
                    "max_cpu": max_cpu,
                    "max_memory": max_memory,
                    "base_latency_ms": base_latency_ms,
                    "energy_rate": energy_rate,
                    "trust": trust,
                    "security_risk": security_risk,
                    "privacy_loss_factor": privacy_loss_factor,
                },
            )
            # Store agent reference for tracking
            self.resources[resource_id].owner = agent.device_id
            # Mirror the real ONLINE/OFFLINE state (OFFLINE devices are unavailable)
            if not agent.is_online:
                self.resources[resource_id].available = False
                self.resources[resource_id]._status = "OFFLINE"

        # Do NOT fabricate MEC devices here - the twin mirrors only registered agents.

        # Set resource order: LOCAL, MECs (sorted by device_id), CLOUD
        all_resource_ids = list(self.resources.keys())
        # Move LOCAL and CLOUD to fixed positions
        ordered = []
        if "LOCAL" in all_resource_ids:
            ordered.append("LOCAL")
        # Add MEC resources
        mec_resources = [r for r in all_resource_ids if r.startswith("MEC-")]
        mec_resources.sort()  # Sort by MEC-1, MEC-2, MEC-3, etc.
        ordered.extend(mec_resources)
        if "CLOUD" in all_resource_ids:
            ordered.append("CLOUD")
        # Add any other resources
        for rid in all_resource_ids:
            if rid not in ordered:
                ordered.append(rid)
        config.RESOURCE_ORDER = ordered

        # Update config with actual resources
        config.RESOURCES = {}
        for rid in ordered:
            if rid in self.resources:
                config.RESOURCES[rid] = self.resources[rid].snap()

    def reset(self):
        self.__init__()

    # -- state -------------------------------------------------------------
    def states(self):
        order = config.RESOURCE_ORDER
        return [self.resources[r].snap() for r in order if r in self.resources]

    def snapshot(self):
        return {
            "tick": self.tick_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resources": self.states(),
        }

    def tick(self):
        self.tick_count += 1
        for res in self.resources.values():
            res.tick()

    # -- attacks -----------------------------------------------------------
    def apply_attack(self, resource_id, attack_type, severity, risk_bonus=0.0):
        """
        Update the virtual resource state to reflect an ongoing attack.
        Returns a dict describing what changed.

        risk_bonus: extra risk contribution (e.g. advanced kill-chain
        objectives / dangerous attack classes). Always clamped to [0,1].
        """
        res = self.resources.get(resource_id)
        before = res.snap() if res else None
        if not (res and res.available):
            return {
                "applied": False,
                "reason": "resource unavailable",
                "before": before,
                "after": before,
            }

        # Attack pressure inflates load and latency
        stress = 0.3 + 0.6 * severity
        res.cpu_utilization = min(0.99, res.cpu_utilization + 0.35 * stress)
        res.memory_utilization = min(0.99, res.memory_utilization + 0.25 * stress)
        res.network_latency_ms = res.base_latency_ms * (1.0 + 2.4 * stress)

        # Trust degrades quickly, risk climbs
        res._trust = max(0.05, res._trust * (1.0 - 0.35 * stress))

        privacy = 0.3 + 0.5 * severity
        workload = res.cpu_utilization
        risk = self.risk_engine.compute_risk(
            attack_type=attack_type,
            severity=severity,
            privacy=privacy,
            trust=res._trust,
            workload=workload,
            exposure=0.4 + 0.4 * severity,
        )
        res.security_risk = min(1.0, risk + abs(float(risk_bonus)))
        res._refresh_status()
        after = res.snap()
        return {"applied": True, "before": before, "after": after}

    def quarantine(self, resource_id):
        res = self.resources.get(resource_id)
        if res:
            res.available = False
            res._risk = max(res._risk, 0.80)
            res._refresh_status()
        return res.snap() if res else None

    def unquarantine(self, resource_id):
        res = self.resources.get(resource_id)
        if res:
            res.available = True
            res._risk = min(res._risk, 0.25)
            res._refresh_status()
        return res.snap() if res else None

    # -- user-managed resources -----------------------------------------
    def add_resource(self, resource_id, params, owner=None, kind="custom"):
        """Register a user-added resource (e.g. a cloud node or an edge
        accelerator) into the virtual twin. Params mirror config.RESOURCES."""
        rid = str(resource_id).strip().upper()
        if not rid:
            raise ValueError("Invalid resource id")
        if rid in self.resources:
            raise ValueError(f"Resource {rid} already exists")
        resource_type = params.get("type", "custom")
        self.resources[rid] = ResourceState(
            rid,
            {
                "type": resource_type,
                "max_cpu": float(params.get("max_cpu", 16)),
                "max_memory": float(params.get("max_memory", 8192)),
                "base_latency_ms": float(params.get("base_latency_ms", 120)),
                "energy_rate": float(params.get("energy_rate", 2.5)),
                "trust": float(params.get("trust", 0.9)),
                "security_risk": float(params.get("security_risk", 0.1)),
                "privacy_loss_factor": float(params.get("privacy_loss_factor", 0.2)),
            },
        )
        self.resources[rid].owner = owner
        self.resources[rid].kind = kind
        if rid not in config.RESOURCE_ORDER:
            config.RESOURCE_ORDER.append(rid)
        return self.resources[rid].snap()

    def remove_resource(self, resource_id):
        rid = str(resource_id).strip().upper()
        if rid in config.RESOURCE_ORDER:
            config.RESOURCE_ORDER.remove(rid)
        return bool(self.resources.pop(rid, None))

    def custom_resources(self):
        return [
            r.snap()
            for r in self.resources.values()
            if getattr(r, "kind", "core") not in ("core", None)
        ]

    def custom_storages(self):
        return [
            r.snap()
            for r in self.resources.values()
            if getattr(r, "resource_type", "") == "storage"
        ]


if __name__ == "__main__":
    dt = DigitalTwin()
    print("Before attack:")
    for s in dt.states():
        print("  ", s["resource_id"], "risk", s["security_risk"], s["status"])
    print("Launching DDoS on MEC-2 ...")
    result = dt.apply_attack("MEC-2", "DDoS", 0.8)
    print("  applied:", result["applied"])
    print("  before :", result["before"])
    print("  after  :", result["after"])