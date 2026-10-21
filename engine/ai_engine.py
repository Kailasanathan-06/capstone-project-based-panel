"""
AI Security & Scheduling Intelligence
=====================================
A lightweight, fully-offline machine-learning module that predicts the risk
level of a task / resource from its features.

It labels the risk as one of {safe, warning, high_risk}.

The model used is a Random Forest trained on the synthetic AI-training
dataset. Evaluation metrics (accuracy, precision, recall, F1) are computed
from the actual data and are never fabricated.

If no model is available the module falls back to a transparent rule-based
risk assessment and reports itself as UNAVAILABLE, so the rest of the system
keeps working.

Optional Groq Cloud LLM insight layer
-------------------------------------
When AI_PROVIDER=groq (or hybrid) and a GROQ_API_KEY is configured, the
engine can also produce a short natural-language "security insight" for a
task through the Groq Cloud API. This layer is strictly optional:

  * it only activates on explicit calls to llm_explain() (never inside the
    batch/offline prediction paths), so the Random Forest stays the fast
    numeric backbone;
  * every call is cached (bounded LRU) and wrapped in timeouts;
  * on any failure or missing key it degrades silently to "offline" and the
    rest of the system keeps working as before.
"""

import json
import os
import pickle
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

import config

warnings.filterwarnings("ignore")

# Sentinel for the bounded LRU cache (a task_id never equals this object).
_MISS = object()


class AIEngine:
    ANALYSIS_CACHE_SIZE = 512
    LLM_CACHE_SIZE = 256

    def __init__(self, dataset_path=None, model_path=None):
        self.dataset_path = dataset_path or config.AI_TRAINING_DATASET
        self.model_path = model_path or config.AI_MODEL_PATH
        self.model = None
        self.features = list(config.AI_FEATURES)
        self.metrics = None
        self.status = "UNAVAILABLE"  # "READY" / "UNAVAILABLE"
        self.classes_ = None
        self._cache_order = []  # LRU keys for analyze_task
        self._cache = {}
        # Groq LLM insight layer state (never stores the API key)
        self.llm_enabled = bool(config.LLM_ENABLED)
        self.llm_client = None
        self.llm_status = "disabled"
        if self.llm_enabled:
            self.llm_status = "ready"
        self._llm_cache = {}  # LRU keys for llm_explain
        self._llm_cache_order = []

    def _cache_get(self, key):
        if key in self._cache:
            self._cache_order.remove(key)
            self._cache_order.append(key)
            return self._cache[key]
        return _MISS

    def _cache_put(self, key, value):
        if key in self._cache:
            self._cache_order.remove(key)
        self._cache[key] = value
        self._cache_order.append(key)
        if len(self._cache_order) > self.ANALYSIS_CACHE_SIZE:
            old = self._cache_order.pop(0)
            self._cache.pop(old, None)

    def _llm_cache_get(self, key):
        if key in self._llm_cache:
            self._llm_cache_order.remove(key)
            self._llm_cache_order.append(key)
            return self._llm_cache[key]
        return _MISS

    def _llm_cache_put(self, key, value):
        if key in self._llm_cache:
            self._llm_cache_order.remove(key)
        self._llm_cache[key] = value
        self._llm_cache_order.append(key)
        if len(self._llm_cache_order) > self.LLM_CACHE_SIZE:
            old = self._llm_cache_order.pop(0)
            self._llm_cache.pop(old, None)

    # -- model load/train ----------------------------------------------
    def load_or_train(self):
        """Load a saved model or train from the dataset if available."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, "rb") as fh:
                    data = pickle.load(fh)
                self.model = data.get("model")
                self.metrics = data.get("metrics")
                self.classes_ = data.get("classes")
                self.status = "READY"
                return self.status
        except Exception:  # noqa: BLE001
            pass
        # try training from dataset
        try:
            if os.path.exists(self.dataset_path):
                self.train(self.dataset_path)
            else:
                self.status = "UNAVAILABLE"
        except Exception:  # noqa: BLE001
            self.status = "UNAVAILABLE"
        return self.status

    def _prepare(self, df):
        """Coerce and return feature matrix + labels for a dataframe."""
        df = df.copy()
        for f in self.features:
            if f not in df.columns:
                df[f] = 0.0
        X = df[self.features].astype(float)
        y = df[config.AI_LABEL_COL].astype(str)
        label_map = {
            "safe": 0,
            "normal": 0,
            "warning": 1,
            "sensitive": 1,
            "high_risk": 2,
        }
        y = y.map(lambda v: label_map.get(v, 0))
        return X, y

    def train(self, path):
        """Train a Random Forest on the AI training dataset."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import (
            accuracy_score,
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
        )
        from sklearn.model_selection import train_test_split

        df = pd.read_csv(path)
        X, y = self._prepare(df)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        clf = RandomForestClassifier(
            n_estimators=120, max_depth=12, random_state=42, n_jobs=-1
        )
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        cm = [[int(v) for v in row] for row in confusion_matrix(y_test, y_pred)]
        self.metrics = {
            "train_size": int(X_train.shape[0]),
            "test_size": int(X_test.shape[0]),
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "precision": round(
                float(
                    precision_score(y_test, y_pred, average="weighted", zero_division=0)
                ),
                4,
            ),
            "recall": round(
                float(
                    recall_score(y_test, y_pred, average="weighted", zero_division=0)
                ),
                4,
            ),
            "f1": round(
                float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4
            ),
            "confusion_matrix": cm,
        }
        self.model = clf
        self.classes_ = clf.classes_
        self.status = "READY"
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        try:
            with open(self.model_path, "wb") as fh:
                pickle.dump(
                    {
                        "model": self.model,
                        "metrics": self.metrics,
                        "classes": self.classes_,
                    },
                    fh,
                )
        except Exception:  # noqa: BLE001
            pass

    # -- prediction -------------------------------------------------------
    def predict(self, features):
        """Predict risk class for a feature dict/row."""
        if self.model is None:
            return self._rule_based(features)
        row = np.array(
            [[float(features.get(f, 0.0)) for f in self.features]], dtype=float
        )
        pred = int(self.model.predict(row)[0])
        proba = self.model.predict_proba(row)[0].tolist()
        label = {0: "safe", 1: "warning", 2: "high_risk"}.get(pred, "safe")
        return {
            "level": label,
            "confidence": round(max(proba), 4),
            "model": "rule_based" if self.model is None else "random_forest",
            "proba": proba,
        }

    def _rule_based(self, features):
        """Fallback when no trained model is available."""
        risk = float(features.get("security_risk", 0.0))
        expo = float(features.get("attack_exposure", 0.0))
        privacy = float(features.get("privacy", 0.0))
        trust = float(features.get("trust", 1.0))
        workload = float(features.get("workload", 0.0))
        score = (
            0.5 * risk
            + 0.2 * expo
            + 0.15 * privacy
            + 0.15 * (1 - trust)
            + 0.1 * workload
        )
        if score >= 0.6:
            level, conf = "high_risk", 0.8
        elif score >= 0.3:
            level, conf = "warning", 0.6
        else:
            level, conf = "safe", 0.5
        return {
            "level": level,
            "confidence": conf,
            "model": "rule_based",
            "proba": [1 - conf, 0, conf],
        }

    def analyze_task(self, task):
        """Build an explainable AI analysis for a task dict (cached)."""
        key = (
            str(task.get("task_id", "")),
            round(float(task.get("cpu_cycles_giga", 0.0)), 4),
            round(float(task.get("memory_mb", 0.0)), 2),
            round(float(task.get("security_sensitivity", 0.3)), 4),
            round(float(task.get("privacy_sensitivity", 0.3)), 4),
        )
        cached = self._cache_get(key)
        if cached is not _MISS:
            return cached
        row = {
            "cpu": task.get("cpu_cycles_giga", 0.0) / 5.0,
            "memory": task.get("memory_mb", 0.0) / 1024.0,
            "latency": task.get("expected_latency_ms", 100.0) / 300.0,
            "trust": 0.9,
            "security_risk": task.get("security_sensitivity", 0.3),
            "attack_severity": 0.0,
            "privacy": task.get("privacy_sensitivity", 0.3),
            "workload": 0.4,
            "storage_integrity": 1.0,
            "attack_exposure": task.get("attack_exposure", 0.2),
        }
        pred = self.predict(row)

        deadline_risk = "LOW"
        if task.get("deadline_ms", 0) and task.get("deadline_ms", 0) < 150:
            deadline_risk = "HIGH"
        elif task.get("deadline_ms", 0) < 300:
            deadline_risk = "MEDIUM"

        reasons = []
        if row["attack_exposure"] > 0.5:
            reasons.append("High attack exposure")
        if row["privacy"] > 0.6:
            reasons.append("Privacy-sensitive task")
        if row["security_risk"] > 0.6:
            reasons.append("High security sensitivity")
        if row["memory"] > 0.6:
            reasons.append("High memory requirement")
        if deadline_risk == "HIGH":
            reasons.append("Tight deadline")
        if not reasons:
            reasons.append("Balanced resource profile")

        priority = {"high_risk": "HIGH", "warning": "MEDIUM", "safe": "LOW"}.get(
            pred["level"], "MEDIUM"
        )

        result = {
            "privacy_risk": _label(task.get("privacy_sensitivity", 0.3)),
            "security_risk": _label(task.get("security_sensitivity", 0.3)),
            "deadline_risk": deadline_risk,
            "recommended_priority": priority,
            "predicted_level": pred["level"],
            "confidence": pred["confidence"],
            "model": pred["model"],
            "reasons": reasons,
            "features": row,
        }
        self._cache_put(key, result)
        return result

    def status_payload(self):
        return {
            "status": self.status,
            "model": "random_forest" if self.model else "rule_based",
            "metrics": self.metrics,
            "features": self.features,
            "provider": config.AI_PROVIDER,
            "llm": self.llm_status,
        }

    # -- optional Groq Cloud LLM insight layer ----------------------------
    def _get_llm_client(self):
        """Lazily build the Groq client when a key is configured. Never
        raises: on failure the engine simply reports itself as offline."""
        if not self.llm_enabled:
            self.llm_status = "disabled"
            return None
        if self.llm_client is not None:
            return self.llm_client
        try:
            from groq import Groq

            client = Groq(api_key=config.GROQ_API_KEY)
            # cheap connectivity probe via the models endpoint (2s timeout)
            client.models.list(timeout=5)
            self.llm_client = client
            self.llm_status = "connected"
        except Exception:  # noqa: BLE001
            self.llm_client = None
            self.llm_status = "offline"
        return self.llm_client

    def llm_explain(self, task, analysis=None):
        """Produce a short natural-language security insight for a task via
        Groq Cloud (cached, timeout-guarded, graceful offline fallback).

        Returns a dict, or None when the LLM layer is disabled/unavailable.
        The returned insight is model-generated and informational only - it
        never overrides the local Random Forest prediction."""
        task_id = str(task.get("task_id", ""))
        cached = self._llm_cache_get(task_id)
        if cached is not _MISS:
            return cached
        if self._get_llm_client() is None:
            self._llm_cache_put(task_id, None)
            return None
        analysis = analysis or self.analyze_task(task)
        prompt = (
            "You are a Security Operations analyst for an edge-cloud network. "
            "A task was classified by a local Random Forest model.\n\n"
            f"Task id: {task_id}\n"
            f"Type: {task.get('task_type', 'unknown')}\n"
            f"CPU (GC/s): {task.get('cpu_cycles_giga', '?')}\n"
            f"Memory (MB): {task.get('memory_mb', '?')}\n"
            f"Deadline (ms): {task.get('deadline_ms', '?')}\n"
            f"Attack exposure: {task.get('attack_exposure', '?')}\n"
            f"Privacy sensitivity: {task.get('privacy_sensitivity', '?')}\n"
            f"Security sensitivity: {task.get('security_sensitivity', '?')}\n\n"
            f"Model prediction: {analysis.get('predicted_level')}\n"
            f"Confidence: {analysis.get('confidence')}\n"
            "Predicted priorities: "
            f"{analysis.get('recommended_priority')}\n"
            f"Rules used: {', '.join(analysis.get('reasons') or [])}\n\n"
            "Reply with ONLY valid JSON of the form "
            '{"insight": "<1-3 sentence plain-language security insight>", '
            '"recommendation": "<what the operator should do next>", '
            '"severity": "LOW|MEDIUM|HIGH"}'
        )
        try:
            resp = self.llm_client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise, technical security "
                        "operations analyst. Always answer in JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=260,
                response_format={"type": "json_object"},
                timeout=config.REQUEST_TIMEOUT + 10,
            )
            content = resp.choices[0].message.content or "{}"
            try:
                parsed = json.loads(content) or {}
            except Exception:  # noqa: BLE001
                parsed = {"insight": content.strip()[:400]}
            insight = {
                "task_id": task_id,
                "insight": str(parsed.get("insight", "")).strip()[:600],
                "recommendation": str(parsed.get("recommendation", "")).strip()[:400],
                "severity": str(parsed.get("severity", "MEDIUM")).upper(),
                "model": "groq/" + config.GROQ_MODEL,
            }
        except Exception:  # noqa: BLE001
            self.llm_status = "offline"
            self.llm_client = None  # retry on next call
            self._llm_cache_put(task_id, None)
            return None
        self._llm_cache_put(task_id, insight)
        return insight

    # -- extended intelligence ------------------------------------------
    def predict_resource_risk(self, resource_state):
        """Predict the risk level of a resource from its live state."""
        rs = resource_state or {}
        row = {
            "cpu": rs.get("cpu_utilization", 0.4),
            "memory": rs.get("memory_utilization", 0.4),
            "latency": (rs.get("network_latency_ms", 100)) / 350.0,
            "trust": rs.get("trust_score", 0.9),
            "security_risk": rs.get("security_risk", 0.1),
            "attack_severity": 0.0,
            "privacy": rs.get("privacy_loss_factor", 0.2),
            "workload": rs.get("active_tasks", 0) / 40.0,
            "storage_integrity": 1.0,
            "attack_exposure": rs.get("security_risk", 0.1),
        }
        pred = self.predict(row)
        pred["resource_id"] = rs.get("resource_id", "?")
        pred["status"] = rs.get("status", "SAFE")
        return pred

    def recommend_ga_params(self, current_state=None):
        """Suggest GA population/generations/mutation from the dataset
        size and risk state (actual values, not hardcoded)."""
        tm = current_state or {}
        n_tasks = int(tm.get("task_count", 0) or 0)
        risk = float(tm.get("risk", 0.0) or 0.0)
        base = config.GA_POPULATION if isinstance(config.GA_POPULATION, int) else 40
        population = max(20, min(config.GA_MAX_POPULATION, base + int(n_tasks * 0.02)))
        generations = max(
            10, min(config.GA_MAX_GENERATIONS, config.GA_GENERATIONS + int(risk * 30))
        )
        mutation = round(min(0.30, 0.10 + risk * 0.15), 3)
        return {
            "population": population,
            "generations": generations,
            "mutation_rate": mutation,
            "basis": {"task_count": n_tasks, "risk": round(risk, 3)},
        }

    def estimate_attack_impact(self, attack_type, target_state=None, severity=0.5):
        """Estimate the impact of a simulated attack on a resource."""
        from engine.attack_simulator import ATTACK_BASE_RISK

        base = ATTACK_BASE_RISK.get(attack_type, 0.5)
        target_state = target_state or {}
        severity = max(0.0, min(1.0, severity))
        risk_delta = min(
            1.0, base * severity + (1 - float(target_state.get("trust_score", 0.9)))
        )
        latency_mult = 1.0 + 2.0 * severity
        cpu_inc = min(
            0.99,
            float(target_state.get("cpu_utilization", 0.4))
            + 0.35 * (0.3 + 0.6 * severity),
        )
        return {
            "attack_type": attack_type,
            "severity": severity,
            "expected_risk_delta": round(risk_delta, 3),
            "expected_latency_multiplier": round(latency_mult, 2),
            "expected_cpu": round(cpu_inc, 3),
            "estimated_mitigation": "quarantine + reroute",
        }

    def anomaly_score(self, resource_metrics):
        """Compute an anomaly score for a resource metric stream."""
        if not resource_metrics:
            return {"score": 0.0, "reasons": ["No metrics available"]}
        vals = [float(v) for v in resource_metrics if isinstance(v, (int, float))]
        if len(vals) < 3:
            return {"score": 0.0, "reasons": ["Insufficient samples"]}
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = var**0.5
        latest = vals[-1]
        z = abs(latest - mean) / (std + 1e-9)
        score = min(1.0, z / 3.0)
        reasons = []
        if z > 2.5:
            reasons.append("Extreme deviation from recent trend")
        elif z > 1.5:
            reasons.append("Notable deviation detected")
        if len(vals) > 1 and latest > max(vals[:-1]):
            reasons.append("New maximum observed")
        if not reasons:
            reasons.append("Within normal variability")
        return {"score": round(score, 3), "z_score": round(z, 3), "reasons": reasons}


def _label(v):
    if v >= 0.7:
        return "HIGH"
    if v >= 0.4:
        return "MEDIUM"
    return "LOW"


if __name__ == "__main__":
    ai = AIEngine()
    ai.load_or_train()
    print("AI status:", ai.status)
    print("metrics:", ai.metrics)
    sample = {
        "cpu_cycles_giga": 3.2,
        "memory_mb": 512.0,
        "expected_latency_ms": 120.0,
        "security_sensitivity": 0.6,
        "privacy_sensitivity": 0.8,
        "attack_exposure": 0.7,
        "deadline_ms": 200.0,
    }
    print("analyze:", ai.analyze_task(sample))
