"""
Storage Simulator
=================
Models virtual storage for the STORAGE ATTACK LAB. Tracks capacity, used
space, integrity, risk, access attempts, encryption state and per-block
integrity. All "attacks" only alter these virtual variables.

Never touches real storage, files or systems.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402


class StorageBlock:
    def __init__(self, block_id):
        self.block_id = block_id
        self.integrity = 1.0
        self.encrypted = random.random() > 0.2


class VirtualStorage:
    def __init__(self, storage_id, params, seed=None):
        self.storage_id = storage_id
        self.rng = random.Random(seed)
        self.params = params
        self.capacity_gb = params["capacity_gb"]
        self.used_space = self.capacity_gb * random.uniform(0.45, 0.7)
        self.integrity = random.uniform(0.9, 1.0)
        self.security_risk = 0.04 + random.uniform(0, 0.1)
        self.trust = random.uniform(0.88, 0.98)
        self.privacy_level = params["privacy_level"]
        self.availability = True
        self.blocks = []
        for i in range(config.STORAGE_BLOCKS_PER):
            self.blocks.append(StorageBlock(f"{storage_id}-D{i+1:03d}"))
        self.access_attempts = random.randint(1, 8)
        self.suspicious_access = random.randint(0, 1)

    def snap(self):
        return {
            "storage_id": self.storage_id,
            "storage_type": self.params["type"],
            "capacity_gb": int(self.capacity_gb),
            "used_space": round(self.used_space, 1),
            "integrity": round(self.integrity, 3),
            "security_risk": round(self.security_risk, 3),
            "trust": round(self.trust, 3),
            "access_attempts": self.access_attempts,
            "suspicious_access": self.suspicious_access,
            "encryption": self.params["encryption"],
            "privacy_level": round(self.privacy_level, 3),
            "availability": self.availability,
            "blocks": [
                {
                    "id": b.block_id,
                    "integrity": round(b.integrity, 3),
                    "encrypted": b.encrypted,
                }
                for b in self.blocks
            ],
        }

    def apply_attack(self, severity):
        """Decrease integrity, increase risk; return before/after snapshots."""
        before = self.snap()
        stress = 0.3 + 0.6 * severity
        self.integrity = max(0.0, self.integrity - 0.25 * stress)
        self.security_risk = min(
            1.0, self.security_risk + 0.7 * stress * (1 - self.trust)
        )
        self.trust = max(0.2, self.trust - 0.25 * stress)
        self.access_attempts += int(20 * severity)
        self.suspicious_access += int(12 * severity)
        # corrupt some data blocks
        corrupt = int(len(self.blocks) * 0.55 * severity)
        for b in self.rng.sample(self.blocks, corrupt):
            b.integrity = max(0.0, b.integrity - self.rng.uniform(0.3, 0.8))
        after = self.snap()
        return {"before": before, "after": after}

    def recover(self):
        before = self.snap()
        self.integrity = min(0.98, self.integrity + 0.35)
        self.security_risk = max(0.08, self.security_risk - 0.4)
        self.trust = min(0.95, self.trust + 0.2)
        return {"before": before, "after": self.snap()}


class StorageSimulator:
    def __init__(self, seed=None):
        self.rng = random.Random(seed or 7)
        self.storages = {}
        for sid, params in config.STORAGE_SPECS.items():
            self.storages[sid] = VirtualStorage(sid, params, self.rng.random())
        self.logs = []
        self.owner = {}  # storage_id -> owner username (user-added)

    def states(self):
        return [self.storages[s].snap() for s in config.STORAGE_ORDER]

    def add_storage(self, storage_id, params, owner=None):
        """Register a user-added virtual storage device."""
        sid = str(storage_id).strip().upper()
        if not sid:
            raise ValueError("Invalid storage id")
        if sid in self.storages:
            raise ValueError(f"Storage {sid} already exists")
        if sid not in config.STORAGE_ORDER:
            config.STORAGE_ORDER.append(sid)
        spec = {
            "type": params.get("type", "virtual"),
            "capacity_gb": float(params.get("capacity_gb", 1000)),
            "encryption": bool(params.get("encryption", True)),
            "privacy_level": float(params.get("privacy_level", 0.8)),
        }
        self.storages[sid] = VirtualStorage(sid, spec, self.rng.random())
        if owner:
            self.owner[sid] = owner
        return self.storages[sid].snap()

    def remove_storage(self, storage_id):
        sid = str(storage_id).strip().upper()
        if sid in config.STORAGE_ORDER:
            config.STORAGE_ORDER.remove(sid)
        self.owner.pop(sid, None)
        return bool(self.storages.pop(sid, None))

    def custom_storages(self):
        return [self.storages[s].snap() for s in self.storages if s in self.owner]

    def attack(self, storage_id, severity):
        stor = self.storages.get(storage_id)
        if not stor:
            return {"ok": False, "message": "Unknown storage target"}
        severity = max(0.0, min(1.0, severity))
        res = stor.apply_attack(severity)
        self.logs.append("storage_attack:" + storage_id)
        return {"ok": True, **res}

    def status(self):
        return {"storages": self.states(), "total_logs": len(self.logs)}


if __name__ == "__main__":
    ss = StorageSimulator()
    print("before:", ss.storages["STORAGE-A"].snap()["integrity"])
    res = ss.attack("STORAGE-A", 0.8)
    print(
        "after integrity:",
        res["after"]["integrity"],
        "risk:",
        res["after"]["security_risk"],
    )
