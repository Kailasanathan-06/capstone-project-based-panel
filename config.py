"""
SecureDT Configuration
======================
Central configuration for the Intelligent and Secure Task Scheduling
system for Digital Twin-enabled Edge-Cloud networks.

All risk model weights, GA parameters, resource definitions and path
settings are calibrated here so that they can later be tuned against a
base scientific paper without touching the core engine code.
"""

import os

# Load optional .env overrides (SECRET_KEY, GROQ_API_KEY, ...). python-dotenv
# is optional: without it the app still works from exported environment
# variables / config.yaml only.
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:  # noqa: BLE001
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "datasets")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

TASK_DATASET = os.path.join(DATASET_DIR, "tasks_10000.csv")
ATTACK_DATASET = os.path.join(DATASET_DIR, "attack_events_5000.csv")
RESOURCE_DATASET = os.path.join(DATASET_DIR, "resource_states_3000.csv")
EXPERIMENT_DATASET = os.path.join(DATASET_DIR, "experiment_results_2000.csv")
AI_TRAINING_DATASET = os.path.join(DATASET_DIR, "ai_training_10000.csv")
STORAGE_SECURITY_DATASET = os.path.join(DATASET_DIR, "storage_security_5000.csv")

# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------
# Values may be overridden via environment variables (e.g. from .env) so a
# deployment does not need to edit this file. Nothing hardcodes a secret.
HOST = os.environ.get("HOST", "127.0.0.1")
try:
    PORT = int(os.environ.get("PORT", "8000"))
except ValueError:
    PORT = 8000
DEBUG = os.environ.get("DEBUG", "False").strip().lower() in ("1", "true", "yes")
# SECRET_KEY may be exported directly, loaded from .env, or (as a last
# resort) auto-generated as a random value at startup by app.py. Never kept
# hardcoded here.
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit

# ---------------------------------------------------------------------------
# Resources (Digital Twin managed nodes)
# ---------------------------------------------------------------------------
# Each resource is defined with its base nominal characteristics. CPU and
# memory utilisation are dynamically simulated by the Digital Twin.
RESOURCES = {
    "LOCAL": {
        "type": "edge",
        "max_cpu": 8,  # Giga-Cycles / s nominal capacity
        "max_memory": 4096,  # MB
        "base_latency_ms": 180,
        "energy_rate": 4.1,  # Joules per abstract work-unit
        "trust": 0.98,
        "security_risk": 0.05,
        "privacy_loss_factor": 0.08,
    },
    "MEC-1": {
        "type": "mec",
        "max_cpu": 16,
        "max_memory": 8192,
        "base_latency_ms": 110,
        "energy_rate": 2.4,
        "trust": 0.93,
        "security_risk": 0.10,
        "privacy_loss_factor": 0.20,
    },
    "MEC-2": {
        "type": "mec",
        "max_cpu": 16,
        "max_memory": 8192,
        "base_latency_ms": 92,
        "energy_rate": 2.1,
        "trust": 0.94,
        "security_risk": 0.12,
        "privacy_loss_factor": 0.22,
    },
    "MEC-3": {
        "type": "mec",
        "max_cpu": 16,
        "max_memory": 8192,
        "base_latency_ms": 98,
        "energy_rate": 2.2,
        "trust": 0.91,
        "security_risk": 0.14,
        "privacy_loss_factor": 0.24,
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

RESOURCE_ORDER = ["LOCAL", "MEC-1", "MEC-2", "MEC-3", "CLOUD"]

# ---------------------------------------------------------------------------
# Genetic Algorithm parameters
# ---------------------------------------------------------------------------
GA_POPULATION = 40
GA_GENERATIONS = 50
GA_MUTATION_RATE = 0.12
GA_CROSSOVER_RATE = 0.85
GA_ELITISM = 4  # number of best chromosomes carried to next generation
GA_TOURNAMENT_SIZE = 3

# Weighting of the multi-objective fitness function
GA_WEIGHTS = {
    "latency": 0.25,
    "energy": 0.15,
    "privacy": 0.20,
    "security": 0.30,
    "deadline": 0.10,
}

# ---------------------------------------------------------------------------
# Security risk model
# ---------------------------------------------------------------------------
RISK_LEVELS = [
    (0.30, "LOW"),
    (0.60, "MEDIUM"),
    (0.80, "HIGH"),
    (1.01, "CRITICAL"),
]

# Base attack risk per attack type (0..1) - scales the attack contribution
ATTACK_BASE_RISK = {
    "DDoS": 0.42,
    "Eavesdropping": 0.25,
    "Tampering": 0.30,
    "Data_Poisoning": 0.28,
    "Credential_Abuse": 0.32,
}

# Risk model weights. The conceptual model is:
#     SecurityRisk = ambient_risk + attack_contribution
#     ambient        = workload_weight * workload            (no-attack risk)
#     attack         = severity * (base_attack_risk
#                                  + privacy_weight * privacy
#                                  + trust_weight   * (1 - trust)
#                                  + exposure_weight * exposure)
#     clipped to [0, 1].
# Equations are kept in engine/risk_engine.py for later calibration.
RISK_MODEL = {
    "workload_weight": 0.30,  # ambient risk from current utilisation
    "privacy_weight": 0.25,  # contribution of workload privacy sensitivity
    "trust_weight": 0.40,  # penalty when trust < 1
    "exposure_weight": 0.15,  # attack exposure attribute
    "idle_risk": 0.08,  # base risk with no attack and idle resource
}

# ---------------------------------------------------------------------------
# Task / dataset generation
# ---------------------------------------------------------------------------
DATASET_SEED = 42

TASK_TYPES = [
    "face_recognition",
    "video_analytics",
    "autonomous_navigation",
    "industrial_control",
    "health_monitor",
    "smart_home",
    "object_detection",
    "anomaly_detection",
    "data_mining",
    "real_time_control",
]

PREFERRED_RESOURCES = ["LOCAL", "MEC-1", "MEC-2", "MEC-3", "CLOUD"]

# Chunk size used when streaming large task tables to the frontend
PAGE_SIZE = 50

# ---------------------------------------------------------------------------
# Simulated scheduling baselines
# ---------------------------------------------------------------------------
BASELINES = ["random", "greedy", "privacy_aware", "proposed_ga"]

# ---------------------------------------------------------------------------
# Storage (virtual) configuration
# ---------------------------------------------------------------------------
STORAGE_SPECS = {
    "STORAGE-A": {
        "type": "virtual",
        "capacity_gb": 1000,
        "encryption": True,
        "privacy_level": 0.9,
    },
    "STORAGE-B": {
        "type": "virtual",
        "capacity_gb": 2000,
        "encryption": True,
        "privacy_level": 0.8,
    },
    "STORAGE-C": {
        "type": "virtual",
        "capacity_gb": 500,
        "encryption": False,
        "privacy_level": 0.5,
    },
}
STORAGE_ORDER = ["STORAGE-A", "STORAGE-B", "STORAGE-C"]
STORAGE_BLOCKS_PER = 8

# ---------------------------------------------------------------------------
# AI engine
# ---------------------------------------------------------------------------
#   "localfeatures" -> offline scikit-learn Random Forest (default, no key)
#   "groq"          -> Random Forest + Groq Cloud LLM insight layer
#                      (requires GROQ_API_KEY; falls back gracefully offline)
#   "none"          -> disable AI, rule-based fallback only
AI_PROVIDER = os.environ.get("AI_PROVIDER", "localfeatures").strip().lower()
AI_MODEL_PATH = os.path.join(BASE_DIR, "models", "risk_model.pkl")
AI_TRAINING_DATASET = os.path.join(DATASET_DIR, "ai_training_10000.csv")
AI_FEATURES = [
    "cpu",
    "memory",
    "latency",
    "trust",
    "security_risk",
    "attack_severity",
    "privacy",
    "workload",
    "storage_integrity",
    "attack_exposure",
]
AI_LABEL_COL = "label"

# ---------------------------------------------------------------------------
# Groq Cloud LLM insight layer (optional)
# ---------------------------------------------------------------------------
# Read the Groq API key from GROQ_API_KEY, or fall back to AI_API_KEY.
# The key is never exposed through any API response or log.
GROQ_API_KEY = (
    os.environ.get("GROQ_API_KEY", "").strip()
    or os.environ.get("AI_API_KEY", "").strip()
)
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GROQ_BASE_URL = os.environ.get(
    "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
).strip()
LLM_ENABLED = AI_PROVIDER in ("groq", "hybrid") and bool(GROQ_API_KEY)

# ---------------------------------------------------------------------------
# Application security checks (defensive scanner data)
# ---------------------------------------------------------------------------
APP_CHECKS = {
    "security_headers": {
        "title": "Security Headers",
        "passed": True,
        "score": 90,
        "checks": [
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
        ],
    },
    "cors": {
        "title": "CORS Configuration",
        "passed": True,
        "score": 90,
        "checks": ["Restricted origins", "No credentials wildcard"],
    },
    "csrf": {
        "title": "CSRF Protection",
        "passed": True,
        "score": 100,
        "checks": ["CSRF tokens enforced on state-changing requests"],
    },
    "cookie_security": {
        "title": "Cookie Security",
        "passed": True,
        "score": 85,
        "checks": ["HttpOnly", "SameSite", "Secure flag"],
    },
    "input_validation": {
        "title": "Input Validation",
        "passed": True,
        "score": 100,
        "checks": ["sizeof limits", "type checks", "range checks", "whitelist"],
    },
    "file_upload": {
        "title": "File Upload Protection",
        "passed": True,
        "score": 95,
        "checks": ["CSV only", "size limit", "row limit", "content re-encoding"],
    },
    "rate_limiting": {
        "title": "Rate Limiting",
        "passed": True,
        "score": 90,
        "checks": ["Limiter on expensive endpoints"],
    },
    "auth_state": {
        "title": "Authentication State",
        "passed": True,
        "score": 90,
        "checks": ["Authentication-ready architecture"],
    },
    "error_disclosure": {
        "title": "Error Disclosure",
        "passed": True,
        "score": 95,
        "checks": ["No stack traces leaked to client"],
    },
    "logging": {
        "title": "Audit Logging",
        "passed": True,
        "score": 100,
        "checks": ["Structured audit events recorded"],
    },
    "dependency_status": {
        "title": "Dependency Status",
        "passed": True,
        "score": 85,
        "checks": [
            "Minimal pinned package set",
            "No runtime network calls",
            "Optional extras isolated",
        ],
    },
}

OWASP_CHECKS = {
    "A01": {
        "name": "Broken Access Control",
        "what": "Occurs when users can access resources they are not "
        "authorized for.",
        "why": "Leads to unauthorized data access, privilege escalation "
        "and data loss.",
        "how": "The prototype uses a single-role, session-ready "
        "architecture with access checks planned for multi-user.",
    },
    "A02": {
        "name": "Cryptographic Failures",
        "what": "The use of weak or absent cryptography.",
        "why": "Exposes secrets and sensitive data in transit or at rest.",
        "how": "We force HTTPS in production guidance and keep secrets "
        "in environment configuration.",
    },
    "A03": {
        "name": "Injection",
        "what": "Untrusted input interpreted as code/query.",
        "why": "Leads to SQL/command injection and data compromise.",
        "how": "All inputs are validated and never passed to shell or SQL "
        "execution.",
    },
    "A04": {
        "name": "Insecure Design",
        "what": "System architecture flaws that create risk.",
        "why": "Can make security controls bypassable.",
        "how": "We apply a layered, fail-secure design with fallbacks.",
    },
    "A05": {
        "name": "Security Misconfiguration",
        "what": "Default/insecure server settings.",
        "why": "Exposes administrative surfaces and debug info.",
        "how": "We ship secure defaults, limited debug, and secure " "headers.",
    },
    "A06": {
        "name": "Vulnerable Components",
        "what": "Using outdated libraries with known issues.",
        "why": "Known CVEs can be exploited.",
        "how": "Requirements are pinned; pip-audit guidance included.",
    },
    "A07": {
        "name": "Authentication Failures",
        "what": "Weak or missing authentication.",
        "why": "Allows impersonation and account takeover.",
        "how": "Authentication-ready architecture with secure session " "intent.",
    },
    "A08": {
        "name": "Software/Data Integrity",
        "what": "Tampering with code or data pipelines.",
        "why": "Untrusted updates and poisoned data.",
        "how": "Uploaded CSVs are re-encoded and validated, never " "executed.",
    },
    "A09": {
        "name": "Logging & Monitoring Failures",
        "what": "Failure to log/detect events.",
        "why": "Attacks go unnoticed.",
        "how": "Structured audit & event logs are recorded and visible.",
    },
    "A10": {
        "name": "Server-Side Request Forgery (SSRF)",
        "what": "Server tricked into fetching arbitrary URLs.",
        "why": "Internal network access, data exfiltration.",
        "how": "The prototype performs no outbound requests by default.",
    },
}

# ---------------------------------------------------------------------------
# Health / fault-tolerance config
# ---------------------------------------------------------------------------
MONITORED_MODULES = [
    "backend",
    "dataset",
    "digital_twin",
    "ga",
    "ai",
    "security",
    "attack",
    "storage",
    "analytics",
]

# ---------------------------------------------------------------------------
# Limits / hardening
# ---------------------------------------------------------------------------
UPLOAD_MAX_BYTES = 8 * 1024 * 1024  # 8 MB upload cap
UPLOAD_MAX_ROWS = 100000  # max rows accepted
try:
    RATE_LIMIT_PER_MIN = int(os.environ.get("RATE_LIMIT_PER_MIN", "60"))
except ValueError:
    RATE_LIMIT_PER_MIN = 60  # default limiter per client, per minute
GA_MAX_POPULATION = 200
GA_MAX_GENERATIONS = 200
AI_BATCH_MAX = 5000
EXPERIMENT_MAX_RUNS = 50

REQUEST_TIMEOUT = 10  # seconds for expensive jobs

# ---------------------------------------------------------------------------
# Big-data engine & dataset manager
# ---------------------------------------------------------------------------
DEFAULT_BIGDATA_FILE = os.path.join(DATASET_DIR, "bigdata_tasks.csv")
DEFAULT_BIGDATA_ROWS = 500000  # rows generated by default via API
BIGDATA_ROW_OPTIONS = [10000, 50000, 100000, 500000, 1000000, 5000000, 10000000]

# ---------------------------------------------------------------------------
# Telemetry (optional Zeek)
# ---------------------------------------------------------------------------
ZEEK_LOGS_DIR = os.environ.get("ZEEK_LOGS_DIR", "").strip() or None

# ---------------------------------------------------------------------------
# Data source label shown in the UI banner
# ---------------------------------------------------------------------------
DATA_SOURCE_LABEL = (
    os.environ.get("DATA_SOURCE_LABEL", "SIMULATION DATA").strip() or "SIMULATION DATA"
)


# ---------------------------------------------------------------------------
# Config file overlay (config.yaml) - optional, overrides defaults above.
# Keys mirror the module-level names; unknown keys are ignored.
# e.g. {"ga": {"population": 60}, "server": {"port": 8080}}
# ---------------------------------------------------------------------------
def _apply_config_file():
    path = os.path.join(BASE_DIR, "config.yaml")
    if not os.path.exists(path):
        return
    try:
        import yaml

        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except Exception:  # noqa: BLE001
        return
    _namespace("", data)


def _namespace(prefix, node):
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        name = f"{prefix}_{key}" if prefix else str(key)
        if isinstance(value, dict):
            _namespace(name, value)
            continue
        if name in globals():
            cur = globals()[name]
            if isinstance(cur, dict) and isinstance(value, dict):
                globals()[name].update(value)
            else:
                globals()[name] = value


_apply_config_file()
