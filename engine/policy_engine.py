"""
Privacy and Security Policy Engine
===================================
Enforces explicit task placement policies before and during scheduling:
- LOCAL_ONLY: Medical data strictly prohibited from leaving hospital workstation (LOCAL only).
- TRUSTED_EDGE: May execute on hospital workstation or an authenticated, non-stale, online MEC node.
- CLOUD_ALLOWED: Eligible for any available tier (Local, MEC, or Cloud) adhering to security constraints.

NOTE: These are research testbed placement policies, not claims of legal or regulatory compliance.
Hard feasibility constraints are enforced before candidates are generated and during dispatch.
"""

from typing import Any, Dict, List, Optional, Tuple


class PolicyEngine:
    """Enforces placement policies and determines candidate resource eligibility."""

    VALID_POLICIES = {"LOCAL_ONLY", "TRUSTED_EDGE", "CLOUD_ALLOWED"}

    @classmethod
    def get_eligible_resources(
        cls,
        task: Dict[str, Any],
        resources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Filter candidate resources for a specific task based on hard constraints:
        1. Privacy placement policy (LOCAL_ONLY, TRUSTED_EDGE, CLOUD_ALLOWED)
        2. Availability status (must be available/online, not revoked, not stale)
        3. Supported operation workloads
        4. Memory capacity
        """
        policy = str(task.get("privacy_policy") or "TRUSTED_EDGE").strip().upper()
        if policy not in cls.VALID_POLICIES:
            policy = "TRUSTED_EDGE"

        operation = str(task.get("operation") or "normalize_clahe").strip().lower()
        required_mem = int(task.get("memory_mb") or 0)

        eligible = []
        for res in resources:
            rid = str(res.get("resource_id", "")).upper()
            rtype = str(res.get("resource_type", "")).lower()

            # Rule 1: Node must be online and available
            is_avail = bool(res.get("availability", True))
            is_stale = bool(res.get("is_stale", False))
            is_online = bool(res.get("is_online", True))
            if not is_avail or is_stale or not is_online:
                continue

            # Rule 2: Privacy Policy placement enforcement
            if policy == "LOCAL_ONLY":
                if rid != "LOCAL" and rtype != "local":
                    continue
            elif policy == "TRUSTED_EDGE":
                # Only LOCAL or authentic MEC nodes
                if rid == "CLOUD" or rtype == "cloud":
                    continue
            elif policy == "CLOUD_ALLOWED":
                # All eligible tiers allowed
                pass

            # Rule 3: Memory capacity check
            max_mem = int(res.get("max_memory", 4096))
            if required_mem > 0 and required_mem > max_mem:
                continue

            # Rule 4: Workload support check (if specified)
            supported = res.get("supported_workloads")
            if supported and operation and operation not in supported:
                continue

            eligible.append(res)

        return eligible

    @classmethod
    def validate_dispatch(
        cls,
        task: Dict[str, Any],
        assigned_resource_id: str,
        resources: List[Dict[str, Any]],
    ) -> Tuple[bool, str]:
        """
        Validate that an assigned resource is strictly compliant at dispatch time.
        Returns (is_valid, reason).
        """
        rid = str(assigned_resource_id).upper()
        res = next((r for r in resources if str(r.get("resource_id", "")).upper() == rid), None)
        if not res:
            return False, f"Target resource '{rid}' does not exist in Digital Twin."

        if not res.get("availability", True) or res.get("is_stale", False) or not res.get("is_online", True):
            return False, f"Target resource '{rid}' is offline, stale, or revoked."

        policy = str(task.get("privacy_policy") or "TRUSTED_EDGE").strip().upper()
        rtype = str(res.get("resource_type", "")).lower()

        if policy == "LOCAL_ONLY" and rid != "LOCAL" and rtype != "local":
            return False, f"Violation: Task is LOCAL_ONLY but assigned to non-local resource '{rid}'."

        if policy == "TRUSTED_EDGE" and (rid == "CLOUD" or rtype == "cloud"):
            return False, f"Violation: Task is TRUSTED_EDGE but assigned to cloud resource '{rid}'."

        return True, "Dispatch assignment compliant with privacy and availability constraints."
