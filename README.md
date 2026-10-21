# SecureDT - Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge-Cloud Networks

A comprehensive research prototype implementing intelligent task scheduling with security awareness for edge-cloud computing environments.

## Architecture Overview

```
USER → WEB FRONTEND → DJANGO SERVER → MEC AGENTS → GOOGLE DRIVE
                    ↓
            ┌───────┴───────┐
            │  CORE ENGINES │
            ├───────────────┤
            │ Digital Twin  │
            │ Genetic Alg.  │
            │ Risk Engine   │
            │ Attack Sim.   │
            │ Security Mon. │
            └───────────────┘
```

## Features

### Core Capabilities
- **MEC Agent Management**: Automatic registration, heartbeat-based online/offline detection, secure token authentication
- **Intelligent Task Scheduling**: Genetic Algorithm optimization with security, privacy, latency, and energy objectives
- **Digital Twin**: Real-time virtual representation of edge-cloud infrastructure
- **Security Monitoring**: Attack simulation, risk assessment, automated mitigation
- **Cloud Integration**: Google Drive API for dataset/result storage (via Django, not direct MEC access)
- **Energy Monitoring**: Real-time CPU, RAM, network, and estimated energy tracking

### MEC Agent
- One-time registration with pairing code
- Automatic reconnection with exponential backoff
- Windows executable (`.exe`) via PyInstaller
- Auto-start with Windows support
- Network change resilience (IP agnostic)

### Frontend
- Modern responsive design (dark/light themes)
- Real-time WebSocket updates
- Three.js network topology visualization
- Chart.js analytics dashboards
- Animated data flow and task routing visualizations

## Quick Start

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- Google Cloud Project with Drive API enabled
- Node.js (for frontend development, optional)

### Backend Setup

```bash
# Clone and enter project
cd SecureDT

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Run server
python manage.py runserver
```

### Google Drive Setup

1. Create a Google Cloud Project
2. Enable Google Drive API
3. Create a Service Account
4. Download JSON credentials to `credentials/service-account.json`
5. Share a Google Drive folder with the service account email
6. Set `GOOGLE_DRIVE_FOLDER_ID` in `.env`

### MEC Agent Build

```bash
cd mec_agent
pyinstaller --clean mec_agent.spec

# Or use the build script
./build_mec_agent.bat  # Windows
```

The executable will be at `dist/MEC_Agent.exe` or `release/MEC_Agent.exe`.

### MEC Agent Registration

```bash
# On the MEC machine
MEC_Agent.exe register --server http://your-django-server:8000 --pairing-code YOUR_CODE

# Run agent
MEC_Agent.exe run
```

### Frontend Development

The frontend uses vanilla ES6+ JavaScript with Pico.css. No build step required - templates are served directly by Django.

## Project Structure

```
SecureDT/
├── securedt/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── api_urls.py
├── mec_manager/              # MEC agent management app
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── tasks/                    # Task queue and scheduling
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── cloud/                    # Google Drive integration
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── digital_twin/             # Digital Twin API
│   ├── views.py
│   └── urls.py
├── analytics/                # Analytics and metrics
│   ├── views.py
│   └── urls.py
├── engine/                   # Core algorithms
│   ├── digital_twin.py
│   ├── genetic_algorithm.py
│   ├── scheduler.py
│   ├── risk_engine.py
│   ├── attack_simulator.py
│   ├── security_monitor.py
│   └── telemetry.py
├── mec_agent/                # MEC Agent Python application
│   ├── agent.py
│   └── __init__.py
├── templates_new/            # New modern frontend templates
│   ├── base.html
│   ├── dashboard.html
│   ├── task_routing.html
│   ├── mec_infrastructure.html
│   └── ...
├── static/                   # Static assets
│   ├── css/main.css
│   └── js/main.js
├── mec_agent.spec            # PyInstaller spec
├── build_mec_agent.bat       # Windows build script
├── requirements.txt
├── .env.example
└── manage.py
```

## API Endpoints

### MEC Management
- `POST /api/mec/register/` - Register new MEC agent
- `POST /api/mec/heartbeat/` - Receive heartbeat
- `POST /api/mec/revoke/` - Revoke MEC agent
- `GET /api/mec/` - List all MEC agents

### Task Management
- `GET /api/tasks/` - List tasks (filter by status)
- `POST /api/tasks/` - Create new task
- `POST /api/tasks/{id}/assign/` - Assign to MEC
- `POST /api/tasks/{id}/complete/` - Mark complete
- `POST /api/tasks/{id}/fail/` - Mark failed

### Cloud Storage
- `POST /api/cloud/upload/` - Upload file
- `GET /api/cloud/download/{id}/` - Download file
- `GET /api/cloud/list/` - List files
- `POST /api/cloud/create-folder/` - Create folder

### Analytics
- `GET /api/analytics/overview/` - System overview
- `GET /api/analytics/mec-metrics/` - Per-MEC metrics
- `GET /api/analytics/task-metrics/` - Task execution metrics

## Security Model

- All MEC communication authenticated via bearer tokens
- Tokens rotated periodically
- Google Drive credentials only on Django server
- MEC agents never receive cloud credentials
- Rate limiting on API endpoints
- Audit logging for all security events
- CSRF protection on state-changing operations

## Task Scheduling Objectives

The Genetic Algorithm minimizes:
- **Latency** (25%): Network + processing delay
- **Energy** (15%): Estimated power consumption
- **Privacy Loss** (20%): Data exposure risk
- **Security Risk** (30%): Current threat level
- **Deadline Penalty** (10%): Missed deadlines

**Constraint**: OFFLINE MECs are NEVER eligible for task assignment.

## Research Notes

This is a research prototype. Key assumptions:
- Attack simulation is purely virtual (no real attacks)
- Energy estimation is approximate (software-based)
- Google Drive used as object storage backend
- Single Django instance (not distributed)
- WebSocket for real-time updates (can use polling fallback)

## License

MIT License - See LICENSE file for details.

## Citation

If you use this in research, please cite:
```
@software{securetdt2024,
  title={SecureDT: Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge-Cloud Networks},
  author={Your Name},
  year={2024},
  url={https://github.com/your-repo/securetdt}
}
```