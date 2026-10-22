# Smart Hospital Medical-Image Processing using Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge–Cloud Networks

An advanced academic research prototype and edge-computing testbed that integrates **real medical-image preprocessing**, a **live multi-tier Digital Twin**, and a **security-aware multi-objective Genetic Algorithm (GA)** scheduler for smart hospital edge–cloud networks.

---

## 1. System Architecture & End-to-End Workflow

```
+---------------------------------------------------------------------------------------------------------+
|                                    SMART HOSPITAL NETWORK ARCHITECTURE                                  |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                                 [Medical Image Ingestion]
                     MedMNIST PneumoniaMNIST Testbed (PNG / NPZ / Uploads)
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                           POLICY ENGINE: PRIVACY & FEASIBILITY PLACEMENT                                |
|  - LOCAL_ONLY     : Strictly restricted to Hospital Workstation (Zero offloading permitted)            |
|  - TRUSTED_EDGE   : Eligible for Workstation or Authenticated, Non-Stale, Online MEC Nodes              |
|  - CLOUD_ALLOWED  : Eligible for Workstation, MEC Nodes, or Simulated Cloud Infrastructure               |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                             DIGITAL TWIN: REAL-TIME VIRTUAL MIRROR                                      |
|  - LOCAL Workstation: Live hardware CPU & RAM metrics via `psutil` (MEASURED_HARDWARE)                  |
|  - MEC Edge Nodes   : Live telemetry via periodic heartbeats with 35s stale-timeout (MEASURED_HEARTBEAT) |
|  - CLOUD Tier       : High-capacity simulated execution tier with WAN latency model (SIMULATED_CLOUD)   |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                     MULTI-OBJECTIVE GENETIC ALGORITHM (GA) & BASELINE SCHEDULERS                        |
|  Minimise: Fitness = w1*Latency + w2*Energy + w3*Privacy_Loss + w4*Security_Risk + Hard_Penalty        |
|  Baselines: Round Robin | First Fit | Random | Greedy (Latency-First) | Privacy-Aware                   |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                    ┌────────────────────────────────┼────────────────────────────────┐
                    │                                │                                │
                    ▼                                ▼                                ▼
         [LOCAL WORKSTATION]                  [MEC EDGE AGENT]               [SIMULATED CLOUD]
         - Direct Execution                  - Autonomous Poll               - WAN Transfer (170ms)
         - Hospital Workstation              - Authenticated Task Run        - De-identified Scans
                    │                                │                                │
                    └────────────────────────────────┼────────────────────────────────┘
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                         GENUINE MEDICAL-IMAGE PREPROCESSING PIPELINE                                    |
|  1. Format & Dimensional Validation (Rejects corrupt/non-image inputs with descriptive diagnostics)     |
|  2. Grayscale Conversion (Standardized 8-bit single channel)                                            |
|  3. Lanczos Target Resizing (e.g., 224x224 standard deep learning input)                                |
|  4. Pixel Intensity Normalization ([0.0, 1.0] range)                                                    |
|  5. CLAHE Contrast Enhancement (scikit-image exposure adaptive histogram equalization)                  |
|  6. Cryptographic SHA-256 Checksums (Input and Output verification for auditability)                    |
|  7. Monotonic High-Resolution Timing (`time.perf_counter` execution logging)                            |
+---------------------------------------------------------------------------------------------------------+
                                                     │
                                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                         EXPERIMENT BENCHMARKING & CSV EXPORT SUITE                                      |
|  - Live Comparison Tables: Latency (Avg, Median, P95), Deadline Miss %, Energy (J), Compliance Rate     |
|  - Interactive Visualizations: Chart.js Bar & Line Convergence Charts                                   |
|  - RFC-Compliant CSV Streaming: Downloadable benchmark data for research analysis                      |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Dataset Integration & Provenance

The system integrates the official **MedMNIST v3** PneumoniaMNIST dataset:

- **Dataset Name:** PneumoniaMNIST (MedMNIST v3.0.2)
- **Source:** Yang et al., *"MedMNIST v2: A Large-Scale Lightweight Benchmark for 2D and 3D Biomedical Image Classification"*, Nature Scientific Data (2023).
- **Primary Source:** Kermany et al., *"Identifying Medical Diagnoses and Treatable Diseases by Image-Based Deep Learning"*, Cell 172.5 (2018): 1122-1131.
- **Storage Location:** `data_storage/medical_datasets/pneumoniamnist/` (strictly outside the public webroot).
- **Split Breakdown:** 4,708 training, 524 validation, and 624 test images (5,856 total 28x28 grayscale pediatric chest X-rays).
- **Synthetic Patient IDs:** Indexed with mock hospital references (`MED-PN-TEST-0001`, etc.) to demonstrate realistic hospital workflow handling without exposing real PHI.

---

## 3. Explicit Privacy Placement Policies

Tasks are tagged with explicit placement policies enforced before candidate chromosome sampling and validated at dispatch:

| Policy | Allowed Execution Tiers | Description / Hospital Use Case |
| :--- | :--- | :--- |
| **`LOCAL_ONLY`** | `LOCAL` Workstation only | Confidential or high-privacy scans prohibited from leaving hospital premises. Rejects MEC and Cloud placement with a hard penalty (`+10,000.0`). |
| **`TRUSTED_EDGE`** | `LOCAL` Workstation or authenticated, non-stale `MEC` | General hospital ward tasks offloadable to verified edge nodes. Cloud placement is strictly forbidden. |
| **`CLOUD_ALLOWED`** | `LOCAL`, `MEC`, or `CLOUD` | De-identified research scans eligible for burst offloading to cloud tiers with simulated latency models. |

---

## 4. Digital Twin Telemetry Engine

The Digital Twin (`engine/digital_twin.py`) provides an accurate virtual replica of execution tiers:

1. **`LOCAL` Workstation:**
   - Telemetry mode: `MEASURED_HARDWARE`
   - Real-time CPU and RAM utilization measured directly from the host system via `psutil`.
2. **`MEC` Edge Nodes:**
   - Telemetry mode: `MEASURED_HEARTBEAT`
   - Reflects registered `MECAgent` database models. Automatically transitions to `STALE_OFFLINE` if no heartbeat is received within 35 seconds.
3. **`CLOUD` Infrastructure:**
   - Telemetry mode: `SIMULATED_CLOUD`
   - Explicitly labeled as a simulation tier with configurable network WAN latency (default ~170ms) and energy rates.

---

## 5. Multi-Objective Scheduling & Baseline Comparison

The system implements a multi-objective Genetic Algorithm alongside 5 baseline schedulers evaluated on identical workloads:

- **Genetic Algorithm (GA):** Tournament selection, single-point crossover, per-gene mutation respecting candidate eligibility, elitism, and penalty functions for offline or privacy violations.
- **Round Robin:** Cycles through eligible resources for each task.
- **First Fit:** Selects the first eligible node in the hierarchy.
- **Random:** Reproducible pseudo-random choice among eligible resources.
- **Greedy:** Latency-minimizing assignment among eligible resources.
- **Privacy-Aware:** Privacy-loss minimizing assignment with latency tie-breaking.

### Downloadable CSV Benchmarks
Evaluated results can be exported as RFC-compliant CSV files from the web UI or via:
```http
GET /api/digital-twin/experiments/export-csv/?tasks_count=12&seed=42
```

---

## 6. Getting Started (Windows Execution)

### Prerequisites
- Python 3.11, 3.12, or 3.13 on Windows 10/11
- Virtual environment (`venv`)

### Step 1: Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Database Setup
The application is pre-configured with a dual database engine that defaults to SQLite (`db.sqlite3`) and switches to MySQL when `USE_MYSQL=1` is set in the environment:
```powershell
python manage.py migrate
```

### Step 3: Download & Extract Medical Dataset
Download the verified MedMNIST PneumoniaMNIST dataset and extract benchmark samples outside the webroot:
```powershell
python manage.py download_medical_dataset
```

### Step 4: Run the Development Server
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` to access the SecureDT dashboard.
- **Medical Images Explorer:** `http://127.0.0.1:8000/medical-dataset/`
- **Scheduler & GA Benchmarks:** `http://127.0.0.1:8000/genetic-algorithm/`
- **Task Routing:** `http://127.0.0.1:8000/task-routing/`
- **MEC Infrastructure:** `http://127.0.0.1:8000/mec-infrastructure/`

### Step 5: Run Autonomous MEC Edge Agent (Optional Edge Node)
In a separate terminal:
```powershell
python mec_agent/agent.py run
```
The agent connects to the Django server, sends live telemetry heartbeats, pulls assigned medical image tasks, executes genuine preprocessing or CPU workloads, and reports verifiable results back to the server.

---

## 7. Automated Test Suite

Run the complete regression and verification test suite:
```powershell
python manage.py test tests -v 2
```
All 26 tests (including smoke, authentication, Google Drive integration, image preprocessing, policy engine, digital twin, GA optimizer, baselines, and CSV streaming) should complete with `OK`.

---

## 8. Research Limitations & Medical Disclaimer

> [!WARNING]
> **Academic Research Prototype Notice:**
> This software is an engineering and computing research testbed for evaluating task scheduling, edge computing, Digital Twins, and privacy placement policies.
> It is **NOT** a medical diagnostic device and has **NOT** been certified or approved by the FDA, CE, or any health authority for clinical decision-making or diagnosis.
> Preprocessing operations prepare medical images for pipeline analysis and must never be interpreted as clinical diagnoses.