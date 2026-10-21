#!/usr/bin/env python3
"""
Documentation Generator for SecureDT
Generates all required PDF documentation files.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    print("Warning: fpdf2 not available. Install with: pip install fpdf2")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available. Install with: pip install reportlab")


class SecureDTDocGenerator:
    """Generates all documentation PDFs for SecureDT."""
    
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "docs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_all(self):
        """Generate all documentation PDFs."""
        docs = [
            ("COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf", self.generate_installation_guide),
            ("MEC_AGENT_INSTALLATION_AND_CONNECTION_GUIDE.pdf", self.generate_mec_agent_guide),
            ("GOOGLE_DRIVE_CLOUD_SETUP_GUIDE.pdf", self.generate_google_drive_guide),
            ("DATASET_UPLOAD_AND_PROCESSING_GUIDE.pdf", self.generate_dataset_guide),
            ("AI_MODEL_INSTALLATION_AND_USAGE.pdf", self.generate_ai_model_guide),
            ("GENETIC_ALGORITHM_GUIDE.pdf", self.generate_ga_guide),
            ("DIGITAL_TWIN_ARCHITECTURE.pdf", self.generate_digital_twin_guide),
            ("SECURITY_ARCHITECTURE.pdf", self.generate_security_guide),
            ("DATA_FLOW_AND_COMMUNICATION.pdf", self.generate_data_flow_guide),
            ("REVIEW_0_DOCUMENTATION.pdf", self.generate_review_guide),
        ]
        
        for filename, generator in docs:
            try:
                filepath = self.output_dir / filename
                generator(filepath)
                print(f"[OK] Generated: {filename}")
            except Exception as e:
                print(f"[FAIL] Failed to generate {filename}: {e}")
    
    def _create_pdf(self, filepath, title, sections):
        """Create a PDF document with the given sections."""
        if REPORTLAB_AVAILABLE:
            return self._create_reportlab_pdf(filepath, title, sections)
        elif FPDF_AVAILABLE:
            return self._create_fpdf_pdf(filepath, title, sections)
        else:
            # Create a simple text file as fallback
            with open(filepath.with_suffix('.txt'), 'w') as f:
                f.write(f"{title}\n{'='*len(title)}\n\n")
                f.write(f"Generated: {self.timestamp}\n\n")
                for section_title, content in sections:
                    f.write(f"{section_title}\n{'-'*len(section_title)}\n\n")
                    f.write(f"{content}\n\n")
            print(f"  (Created text fallback for {filepath.name})")
    
    def _create_reportlab_pdf(self, filepath, title, sections):
        """Create PDF using reportlab."""
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            'CustomTitle', parent=styles['Title'],
            fontSize=24, spaceAfter=30, alignment=TA_CENTER
        ))
        styles.add(ParagraphStyle(
            'SectionHeader', parent=styles['Heading1'],
            fontSize=16, spaceAfter=12, spaceBefore=20
        ))
        styles.add(ParagraphStyle(
            'SubSectionHeader', parent=styles['Heading2'],
            fontSize=14, spaceAfter=8, spaceBefore=12
        ))
        styles.add(ParagraphStyle(
            'BodyText2', parent=styles['Normal'],
            fontSize=11, leading=14, alignment=TA_JUSTIFY, spaceAfter=8
        ))
        styles.add(ParagraphStyle(
            'CodeBlock', parent=styles['Normal'],
            fontName='Courier', fontSize=9, leading=12,
            backColor=colors.HexColor('#f5f5f5'),
            borderWidth=1, borderColor=colors.HexColor('#ddd'),
            borderPadding=8, spaceAfter=12
        ))
        
        story = []
        story.append(Paragraph(title, styles['CustomTitle']))
        story.append(Paragraph(f"Generated: {self.timestamp}", styles['Normal']))
        story.append(Paragraph("SecureDT - Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge-Cloud Networks", styles['Normal']))
        story.append(Spacer(1, 20))
        
        for section_title, content in sections:
            story.append(Paragraph(section_title, styles['SectionHeader']))
            # Split content by lines and create paragraphs
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    if paragraph.startswith('    ') or paragraph.startswith('\t'):
                        story.append(Paragraph(paragraph.strip(), styles['CodeBlock']))
                    else:
                        story.append(Paragraph(paragraph.strip(), styles['BodyText2']))
        
        doc.build(story)
    
    def _create_fpdf_pdf(self, filepath, title, sections):
        """Create PDF using fpdf2."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        
        # Title
        pdf.set_font('Helvetica', 'B', 24)
        pdf.cell(0, 15, title, 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f"Generated: {self.timestamp}", 0, 1, 'C')
        pdf.cell(0, 6, "SecureDT - Intelligent and Secure Task Scheduling", 0, 1, 'C')
        pdf.ln(10)
        
        for section_title, content in sections:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, section_title, 0, 1)
            pdf.ln(3)
            
            pdf.set_font('Helvetica', '', 10)
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    pdf.multi_cell(0, 5, paragraph.strip())
                    pdf.ln(3)
            
            pdf.ln(5)
        
        pdf.output(str(filepath))
    
    # =========================================================================
    # Individual Document Generators
    # =========================================================================
    
    def generate_installation_guide(self, filepath):
        sections = [
            ("1. System Requirements", """
                Minimum requirements for running SecureDT:
                
                Server (Django Backend):
                - Python 3.11 or higher
                - MySQL 8.0+ or MariaDB 10.5+
                - 4 GB RAM minimum (8 GB recommended)
                - 10 GB disk space
                - Network access for MEC agents and Google Drive API
                
                MEC Agent Nodes:
                - Windows 10/11, Linux (Ubuntu 20.04+), or macOS 12+
                - Python 3.11+ (if running from source)
                - 2 GB RAM minimum
                - Network connectivity to Django server
                
                Client Browser:
                - Modern browser with ES6+ support (Chrome 90+, Firefox 88+, Edge 90+, Safari 14+)
                - WebSocket support for real-time updates
            """),
            ("2. Backend Installation", """
                1. Clone the repository:
                   git clone <repository-url>
                   cd SecureDT
                
                2. Create and activate virtual environment:
                   python -m venv venv
                   source venv/bin/activate  # Linux/macOS
                   venv\\Scripts\\activate     # Windows
                
                3. Install Python dependencies:
                   pip install -r requirements.txt
                
                4. Configure environment:
                   cp .env.example .env
                   # Edit .env with your settings:
                   # - DJANGO_SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(50))")
                   # - MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT
                   # - GOOGLE_SERVICE_ACCOUNT_FILE (path to Google service account JSON)
                   # - GOOGLE_DRIVE_FOLDER_ID (Google Drive folder ID for storage)
                
                5. Set up MySQL database:
                   CREATE DATABASE securetdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
                   CREATE USER 'securetdb_user'@'%' IDENTIFIED BY 'your_password';
                   GRANT ALL PRIVILEGES ON securetdb.* TO 'securetdb_user'@'%';
                   FLUSH PRIVILEGES;
                
                6. Run migrations:
                   python manage.py migrate
                
                7. Create superuser:
                   python manage.py createsuperuser
                
                8. Collect static files:
                   python manage.py collectstatic
                
                9. Start development server:
                   python manage.py runserver 0.0.0.0:8000
            """),
            ("3. Google Drive API Setup", """
                1. Go to Google Cloud Console (https://console.cloud.google.com/)
                2. Create a new project or select existing
                3. Enable Google Drive API
                4. Create Service Account:
                   - IAM & Admin > Service Accounts > Create Service Account
                   - Name: "securetd-drive"
                   - Grant: "Editor" role (or custom with Drive permissions)
                5. Create and download JSON key:
                   - Service Account > Keys > Add Key > Create New Key > JSON
                6. Save as credentials/service-account.json in project root
                7. Create a folder in Google Drive for SecureDT
                8. Share folder with service account email (from JSON: client_email)
                9. Copy folder ID from URL (https://drive.google.com/drive/folders/FOLDER_ID)
                10. Set GOOGLE_DRIVE_FOLDER_ID in .env
            """),
            ("4. MEC Agent Deployment", """
                Option A: Run from Source (Development)
                ---------------------------------------
                1. Copy mec_agent/ folder to target machine
                2. Install dependencies: pip install psutil requests
                3. Register agent:
                   python -m mec_agent.agent register --server http://YOUR_SERVER:8000 --pairing-code YOUR_CODE
                4. Run agent:
                   python -m mec_agent.agent run
                
                Option B: Windows Executable (Production)
                -----------------------------------------
                1. On Windows build machine:
                   cd mec_agent
                   build_mec_agent.bat
                2. Copy release/MEC_Agent.exe to target machine
                3. Register:
                   MEC_Agent.exe register --server http://YOUR_SERVER:8000 --pairing-code YOUR_CODE
                4. Run:
                   MEC_Agent.exe run
                
                Option C: Auto-start on Windows
                ---------------------------------
                1. After registration, the agent saves config to %USERPROFILE%\\.mec_agent\\
                2. Create shortcut to MEC_Agent.exe run in shell:startup
                3. Or use Task Scheduler: "At startup" > "Run MEC_Agent.exe run"
            """),
            ("5. Verification", """
                1. Access web UI: http://localhost:8000
                2. Login with superuser credentials
                3. Go to MEC Infrastructure page
                3. Register a MEC agent (use pairing code from admin or generate one)
                4. Start MEC agent on another machine
                5. Verify it shows ONLINE in dashboard
                6. Create a test task in Task Routing
                6. Verify task is assigned and completed
                7. Check Google Drive for results
            """),
            ("6. Production Deployment", """
                For production deployment:
                
                1. Use a proper WSGI server (Gunicorn):
                   pip install gunicorn
                   gunicorn securedt.wsgi:application --bind 0.0.0.0:8000 --workers 4
                
                2. Set up reverse proxy (Nginx):
                   server {
                       listen 80;
                       server_name your-domain.com;
                       
                       location / {
                           proxy_pass http://127.0.0.1:8000;
                           proxy_set_header Host $host;
                           proxy_set_header X-Real-IP $remote_addr;
                           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                           proxy_set_header X-Forwarded-Proto $scheme;
                       }
                       
                       location /ws/ {
                           proxy_pass http://127.0.0.1:8000;
                           proxy_http_version 1.1;
                           proxy_set_header Upgrade $http_upgrade;
                           proxy_set_header Connection "upgrade";
                       }
                   }
                
                3. Enable HTTPS with Let's Encrypt:
                   certbot --nginx -d your-domain.com
                
                4. Set DEBUG=False in .env
                5. Configure ALLOWED_HOSTS in .env
                6. Set up systemd service for Django and MEC agents
                7. Configure log rotation
                8. Set up monitoring (Prometheus/Grafana or similar)
            """),
        ]
        self._create_pdf(filepath, "Complete Installation and Usage Guide", sections)
    
    def generate_mec_agent_guide(self, filepath):
        sections = [
            ("1. Overview", """
                The MEC Agent is a lightweight Python application that runs on edge computing nodes
                (Multi-access Edge Computing - MEC). It provides:
                
                - Secure registration with Django server using pairing codes
                - Automatic heartbeat-based online/offline detection
                - Encrypted communication with token-based authentication
                - Task execution and result reporting
                - System telemetry collection (CPU, RAM, disk, network, energy)
                - Automatic reconnection with exponential backoff
                - Network change resilience (IP address agnostic)
                - Windows auto-start capability
            """),
            ("2. Architecture", """
                The MEC Agent follows a client-initiated architecture:
                
                1. Agent starts and loads saved configuration from ~/.mec_agent/config.json
                2. If not registered, user runs registration command with server URL and pairing code
                3. Server validates pairing code and returns device_id + auth_token
                4. Agent saves credentials and begins heartbeat loop
                5. Every 10 seconds (configurable), agent sends heartbeat with telemetry
                6. Server updates MEC status to ONLINE
                7. If server assigns task, agent executes and reports result
                8. On network interruption, agent retries with exponential backoff
                9. On startup, agent automatically reconnects using saved credentials
                
                Security Model:
                - All communication over HTTPS (in production)
                - Bearer token authentication
                - Tokens rotated periodically
                - No credentials in executable
                - Pairing codes single-use
            """),
            ("3. Installation", """
                Prerequisites:
                - Python 3.11+ (for source) or Windows 10+ (for .exe)
                - Network access to Django server
                - Pairing code from administrator
                
                From Source:
                1. Copy mec_agent/ directory to target machine
                2. Install dependencies: pip install psutil requests
                3. Run: python -m mec_agent.agent register --server URL --pairing-code CODE
                
                Windows Executable:
                1. Copy MEC_Agent.exe to target machine (e.g., C:\\MEC_Agent\\)
                2. Open PowerShell as Administrator
                3. Run: .\\MEC_Agent.exe register --server http://SERVER:8000 --pairing-code CODE
                3. Run: .\\MEC_Agent.exe run
            """),
            ("4. Registration Process", """
                Registration is a one-time process per MEC node:
                
                1. Administrator generates pairing code in Django admin or via API
                2. User runs registration command on MEC machine:
                   MEC_Agent.exe register --server http://django:8000 --pairing-code ABC123 --name "EDGE-PC-01"
                
                3. Server validates pairing code and creates:
                   - Unique device_id (e.g., MEC-001, MEC-002, etc.)
                   - Secure auth_token (32-byte URL-safe random string)
                   - Django user account for the MEC
                
                4. Agent receives and stores:
                   - device_id
                   - auth_token
                   - server_url
                   - system_name
                
                5. Configuration saved to ~/.mec_agent/config.json (encrypted on Windows)
                
                6. Future starts automatically load config and connect
            """),
            ("5. Heartbeat & Online/Offline Detection", """
                Heartbeat Protocol:
                - Interval: 10 seconds (configurable via HEARTBEAT_INTERVAL)
                - Payload: device_id, CPU%, RAM%, disk%, current_task, hostname, OS, etc.
                - Authentication: Bearer token in Authorization header
                
                Online Detection:
                - Server updates last_seen on each valid heartbeat
                - MEC marked ONLINE if heartbeat received within timeout
                
                Offline Detection:
                - Timeout: 30 seconds (configurable via HEARTBEAT_TIMEOUT)
                - If no heartbeat for timeout period: MEC marked OFFLINE
                - Dashboard shows RED dot for OFFLINE, GREEN for ONLINE
                - NO tasks dispatched to OFFLINE MECs
                
                Reconnection:
                - Agent retries with exponential backoff (5s, 10s, 20s, 40s... max 5min)
                - On reconnection, sends immediate heartbeat
                - Status updates to ONLINE automatically
            """),
            ("6. Task Execution Flow", """
                1. Server assigns task via API (task status -> ASSIGNED)
                2. Agent polls for tasks every 5 seconds
                3. Agent downloads input data from Google Drive via Django API
                4. Agent executes task (simulated workload based on parameters)
                5. Agent measures: execution_time, CPU%, RAM%, estimated energy
                6. Agent uploads results to Google Drive via Django API
                7. Agent reports completion: task status -> COMPLETED
                8. Server updates Digital Twin and analytics
                
                Task Types Supported:
                - CPU-intensive (video analytics, ML inference)
                - Memory-intensive (data processing, caching)
                - Network-intensive (data transfer, synchronization)
                - Mixed workloads
            """),
            ("7. Configuration", """
                Configuration file: ~/.mec_agent/config.json
                
                {
                    "server_url": "http://django:8000",
                    "device_id": "MEC-001",
                    "auth_token": "secure-random-token",
                    "system_name": "EDGE-PC-01",
                    "heartbeat_interval": 10,
                    "heartbeat_timeout": 30,
                    "auto_start": true,
                    "max_retries": 10,
                    "base_retry_delay": 5,
                    "max_retry_delay": 300,
                    "verify_ssl": true
                }
                
                Environment variables (override config):
                - MEC_SERVER_URL
                - MEC_DEVICE_ID
                - MEC_AUTH_TOKEN
            """),
            ("8. Troubleshooting", """
                Agent won't start:
                - Check Python version (3.11+)
                - Verify dependencies: pip install psutil requests
                - Check config file permissions
                
                Registration fails:
                - Verify server URL accessible (curl http://server:8000/api/state/)
                - Check pairing code is valid and not used
                - Ensure server has MECAgent app installed
                
                Agent shows OFFLINE:
                - Check network connectivity to server
                - Verify server is running
                - Check firewall allows outbound HTTPS
                - Verify auth_token not expired
                
                Tasks not executing:
                - Check agent is ONLINE in dashboard
                - Verify task assigned to this MEC's device_id
                - Check agent logs for errors
                - Verify Google Drive credentials on server
                
                Logs:
                - Log file: ~/.mec_agent/agent.log
                - Console output when running in foreground
            """),
        ]
        self._create_pdf(filepath, "MEC Agent Installation and Connection Guide", sections)
    
    def generate_google_drive_guide(self, filepath):
        sections = [
            ("1. Overview", """
                SecureDT uses Google Drive as the cloud storage backend for:
                - Dataset storage (uploaded by users)
                - Task input data (downloaded by MEC agents)
                - Task results (uploaded by MEC agents)
                - ML models and experiment artifacts
                
                Security Model:
                - MEC agents NEVER have direct Google Drive credentials
                - All Drive operations go through Django API
                - Django uses service account with limited scope
                - Files organized in structured folder hierarchy
            """),
            ("2. Google Cloud Setup", """
                Step-by-step:
                
                1. Create Google Cloud Project:
                   - Go to https://console.cloud.google.com/
                   - Create project: "SecureDT-Project"
                   - Note project ID
                
                2. Enable APIs:
                   - APIs & Services > Library
                   - Search "Google Drive API"
                   - Click Enable
                
                3. Create Service Account:
                   - IAM & Admin > Service Accounts
                   - Create Service Account: "securetd-drive-service"
                   - Description: "SecureDT Google Drive Access"
                   - Grant roles: "Editor" (or custom: roles/drive.file)
                
                4. Create and Download Key:
                   - Open service account details
                   - Keys > Add Key > Create New Key
                   - Type: JSON
                   - Save as credentials/service-account.json
                
                5. Configure Drive Folder:
                   - Open Google Drive
                   - Create folder: "Intelligent_Secure_Scheduling"
                   - Right-click > Share
                   - Add service account email (from JSON: client_email)
                   - Give "Editor" access
                   - Copy folder ID from URL
            """),
            ("3. Django Configuration", """
                Environment variables (.env):
                
                GOOGLE_SERVICE_ACCOUNT_FILE=./credentials/service-account.json
                GOOGLE_DRIVE_FOLDER_ID=your-folder-id-from-step-5
                
                The Django cloud app automatically:
                - Creates subfolders on first run:
                  Intelligent_Secure_Scheduling/
                    datasets/     # Uploaded datasets
                    pcap/         # PCAP/network flow files
                    processed/    # Processed datasets
                    results/      # Task execution results
                    models/       # ML models
                    experiments/  # Experiment outputs
                - Uses service account for all operations
                - Handles authentication automatically
            """),
            ("4. Folder Structure", """
                Google Drive folder hierarchy:
                
                Intelligent_Secure_Scheduling/ (root folder, GOOGLE_DRIVE_FOLDER_ID)
                ├── datasets/
                │   ├── dataset_001.csv
                │   └── dataset_002.pcap
                ├── pcap/
                │   └── capture_2024.pcap
                ├── processed/
                │   └── processed_dataset_001.csv
                ├── results/
                │   ├── TASK-1001_result.json
                │   └── TASK-1002_output.csv
                ├── models/
                │   └── risk_model_v1.pkl
                └── experiments/
                    └── exp_20240115_results.csv
            """),
            ("5. API Usage", """
                Upload file:
                POST /api/cloud/upload/
                Content-Type: multipart/form-data
                Fields: file (file), file_name, folder_id (optional), result_type
                
                Download file:
                GET /api/cloud/download/{file_id}/
                
                List files:
                GET /api/cloud/list/?folder_id={folder_id}
                
                Create folder:
                POST /api/cloud/create-folder/
                Content-Type: application/json
                Body: {"folder_name": "new_folder", "parent_id": "optional"}
            """),
            ("6. Security Considerations", """
                - Service account has access ONLY to shared folder
                - No user credentials stored
                - All file operations logged in CloudUploadRecord model
                - File metadata stored in Django DB (not file contents)
                - Large files streamed (not loaded into memory)
                - MEC agents never see service account credentials
            """),
        ]
        self._create_pdf(filepath, "Google Drive Cloud Setup Guide", sections)
    
    def generate_dataset_guide(self, filepath):
        sections = [
            ("1. Supported Formats", """
                SecureDT supports CSV datasets with the following conventions:
                
                Required columns (auto-detected):
                - task_id, data_size_mb, cpu_cycles_giga, memory_mb
                - deadline_ms, privacy_sensitivity, security_sensitivity
                
                PCAP files:
                - Uploaded as .pcap or .pcapng
                - Processed via Zeek (optional) for network flow extraction
                - Stored in /pcap/ folder
                
                Generic CSV:
                - Any CSV with headers
                - Metadata extracted automatically
            """),
            ("2. Upload Process", """
                Via Web UI:
                1. Go to Datasets page
                2. Click "Upload Dataset"
                3. Select CSV file
                4. Enter name, type, description
                5. Click "Upload to Google Drive"
                
                Via API:
                POST /api/cloud/upload/
                - file: CSV file
                - file_name: "my_dataset.csv"
                - result_type: "dataset"
                
                Processing:
                - File validated (size, format, row count)
                - Metadata extracted (rows, columns, types)
                - Stored in Google Drive
                - Metadata saved in GoogleDriveFile model
                - Status: pending -> processing -> completed
            """),
            ("3. Dataset Types", """
                Task Definitions:
                - Columns: task_id, name, priority, data_size_mb, cpu_cycles_giga, 
                  memory_mb, deadline_ms, privacy_sensitivity, security_sensitivity
                - Used for scheduling benchmarks
                
                Network Flows (PCAP):
                - Raw PCAP files
                - Processed to extract: src, dst, protocol, bytes, duration
                - Used for attack simulation training
                
                Edge Telemetry:
                - Columns: timestamp, cpu, memory, latency, trust, risk, etc.
                - Used for Digital Twin calibration
                
                Attack Events:
                - Columns: timestamp, attack_type, target, severity, etc.
                - Used for risk engine training
                
                Resource States:
                - Historical resource utilization
                - Used for GA fitness evaluation
            """),
            ("4. Large Dataset Handling", """
                For large datasets (>100MB):
                - Streaming upload (chunked)
                - Background processing (async)
                - Progress tracking via UI
                - Row limit: 10M rows default (configurable)
                - Chunked reading for metadata extraction
                
                Big Data Engine:
                - Generates synthetic datasets up to 10M rows
                - Streaming CSV writer (memory efficient)
                - Used for scalability testing
            """),
        ]
        self._create_pdf(filepath, "Dataset Upload and Processing Guide", sections)
    
    def generate_ai_model_guide(self, filepath):
        sections = [
            ("1. AI Architecture", """
                SecureDT uses a two-tier AI approach:
                
                Tier 1: Local ML (Always Available)
                - Random Forest classifier (scikit-learn)
                - Trained on historical telemetry + attack data
                - Features: CPU, memory, latency, trust, risk, attack_severity, 
                  privacy, workload, storage_integrity, attack_exposure
                - Labels: attack_type, risk_level
                - Runs entirely offline, no external dependencies
                
                Tier 2: Groq LLM Enhancement (Optional)
                - Requires GROQ_API_KEY in .env
                - Provides natural language explanations
                - Summarizes security events
                - Explains GA scheduling decisions
                - Gracefully falls back to local if unavailable
            """),
            ("2. Model Training", """
                Training Data:
                - Default: ai_training_10000.csv (10K samples)
                - Large: lakhs_ai_training_200_000.csv (200K samples)
                - Generated from synthetic telemetry + attack simulations
                
                Training Process:
                1. Go to AI Intelligence page
                2. Select dataset
                3. Configure test split (default 0.2)
                4. Enable cross-validation (5-fold)
                5. Click "Train Model"
                6. Model saved to models/risk_model.pkl
                
                Features:
                - cpu: CPU utilization (0-100)
                - memory: RAM utilization (0-100)
                - latency: Network latency (ms)
                - trust: Resource trust score (0-1)
                - security_risk: Current risk level (0-1)
                - attack_severity: Attack severity (0-1)
                - privacy: Privacy sensitivity (0-1)
                - workload: Current workload (0-1)
                - storage_integrity: Storage health (0-1)
                - attack_exposure: Exposure level (0-1)
                
                Labels:
                - risk_level: LOW, MEDIUM, HIGH, CRITICAL
                - attack_type: DDoS, Eavesdropping, Tampering, etc.
            """),
            ("3. Inference", """
                Real-time inference:
                - Triggered on each heartbeat
                - Input: current resource telemetry
                - Output: risk_score, anomaly_flag, recommended_action
                - Latency: ~2ms on CPU
                
                Integration:
                - Risk Engine uses AI predictions for risk calculation
                - GA Scheduler considers AI risk scores
                - Security Monitor displays AI alerts
                - All predictions logged for audit
            """),
            ("4. Groq LLM Integration", """
                Optional enhancement:
                1. Get API key from https://console.groq.com
                2. Add to .env: GROQ_API_KEY=your_key
                3. Set AI_PROVIDER=groq
                4. Model: llama-3.3-70b-versatile (default)
                
                Capabilities:
                - Explain security events in plain English
                - Summarize GA scheduling rationale
                - Generate incident reports
                - Answer operational questions
                
                Safety:
                - Never executes code or commands
                - No access to credentials or database
                - Read-only inference
                - Graceful fallback if API unavailable
            """),
        ]
        self._create_pdf(filepath, "AI Model Installation and Usage Guide", sections)
    
    def generate_ga_guide(self, filepath):
        sections = [
            ("1. Genetic Algorithm Overview", """
                The Genetic Algorithm (GA) is the core scheduler for SecureDT.
                It optimizes task-to-resource assignment with multiple objectives.
                
                Chromosome Representation:
                - One gene per task
                - Gene value = resource index (0 to N-1)
                - Resources: LOCAL, MEC-1..N, CLOUD
                - Population: 40 chromosomes (default)
                
                Fitness Function (minimize):
                Fitness = w1*latency + w2*energy + w3*privacy_loss + w4*security_risk + deadline_penalty
                
                Default Weights:
                - latency: 0.25
                - energy: 0.15
                - privacy: 0.20
                - security: 0.30
                - deadline: 0.10
                
                Operators:
                - Selection: Tournament (size 3)
                - Crossover: Single-point (rate 0.85)
                - Mutation: Per-gene (rate 0.12)
                - Elitism: Top 4 preserved
                - Generations: 50 (default)
            """),
            ("2. Security-Aware Scheduling", """
                Critical constraint: OFFLINE MECs are NEVER eligible for task assignment.
                
                Before GA optimization:
                1. Digital Twin provides current resource states
                2. Scheduler filters: only resources with availability=True and is_online=True
                3. GA operates on filtered resource list only
                4. If all MECs offline, falls back to LOCAL or CLOUD
                
                Security Risk Integration:
                - Each resource has security_risk (0-1) from Digital Twin
                - Risk directly impacts fitness (weight 0.30)
                - High-risk resources automatically avoided
                - Attack simulation increases risk -> GA re-optimizes
            """),
            ("3. Multi-Objective Optimization", """
                Objectives (all minimized):
                1. Latency: network + processing delay
                2. Energy: estimated power consumption
                3. Privacy Loss: data exposure based on resource privacy_factor
                4. Security Risk: current threat level of resource
                5. Deadline Penalty: quadratic penalty for missed deadlines
                
                Pareto Optimization:
                - GA finds Pareto-optimal solutions
                - Best fitness tracks convergence
                - History recorded for analysis
            """),
            ("4. Baseline Comparisons", """
                GA compared against:
                - Random: Random resource assignment
                - Greedy: Minimum latency per task
                - Privacy-Aware: Minimum privacy loss per task
                - Proposed GA: Multi-objective with security
                
                Metrics:
                - Average latency (ms)
                - Energy consumption (J)
                - Privacy loss (normalized)
                - Security risk (normalized)
                - Deadline success rate (%)
            """),
        ]
        self._create_pdf(filepath, "Genetic Algorithm Guide", sections)
    
    def generate_digital_twin_guide(self, filepath):
        sections = [
            ("1. Digital Twin Concept", """
                The Digital Twin is a real-time virtual replica of the physical edge-cloud infrastructure.
                
                Components Tracked:
                - LOCAL: Edge device (user's local compute)
                - MEC-1..N: Registered edge nodes
                - CLOUD: Central cloud resource
                
                State Variables (per resource):
                - cpu_utilization: Current CPU % (dynamic)
                - memory_utilization: Current RAM % (dynamic)
                - network_latency_ms: Current RTT to resource
                - energy_rate: Joules per work unit (static)
                - trust_score: 0-1 trustworthiness
                - security_risk: 0-1 current threat level
                - privacy_loss_factor: Data exposure coefficient
                - availability: True/False (online status)
                - active_tasks: Count of running tasks
                - status: SAFE, WARNING, HIGH RISK, CRITICAL, QUARANTINED
            """),
            ("2. Dynamic Updates", """
                Update Sources:
                1. Heartbeats from MEC agents (every 10s)
                2. Attack simulator events
                3. Task assignment/completion
                4. Natural drift simulation (tick())
                
                Update Flow:
                MEC Agent -> Heartbeat API -> Django -> Digital Twin -> WebSocket -> Dashboard
                
                Tick Simulation:
                - Called periodically (or on demand)
                - Adds small random variations to CPU/RAM
                - Adjusts latency based on utilization
                - Slow trust recovery when risk < 0.3
            """),
            ("3. Attack Response", """
                When attack detected:
                1. Attack Simulator calls digital_twin.apply_attack()
                2. Resource state updated:
                   - CPU/RAM increased by stress factor
                   - Latency increased
                   - Trust decreased
                   - Security risk computed by RiskEngine
                3. Status updated to WARNING/HIGH/CRITICAL
                4. Scheduler notified -> GA re-optimization
                5. Tasks rerouted away from attacked resource
                
                Mitigation:
                - Quarantine: availability=False, risk>=0.8
                - Unquarantine: availability=True, risk<=0.25
            """),
            ("4. Dashboard Integration", """
                Real-time visualization:
                - Resource cards show live metrics
                - Network topology (Three.js) shows connections
                - Animated packets represent data/task/result flow
                - Color coding: Green=safe, Yellow=warning, Red=critical
                - WebSocket pushes updates every heartbeat
            """),
        ]
        self._create_pdf(filepath, "Digital Twin Architecture Guide", sections)
    
    def generate_security_guide(self, filepath):
        sections = [
            ("1. Security Architecture", """
                SecureDT implements defense-in-depth:
                
                Network Security:
                - All API communication over HTTPS (production)
                - WebSocket for real-time with token auth
                - CORS restricted to configured origins
                - Rate limiting on all endpoints
                
                Authentication:
                - Django session auth for web UI
                - Token auth for API (DRF TokenAuthentication)
                - MEC agents: Bearer token (rotated periodically)
                - Pairing codes: Single-use registration
                
                Authorization:
                - Role-based access (admin/user)
                - MEC agents: scoped to own device_id
                - Resource-level permissions
            """),
            ("2. MEC Communication Security", """
                Registration:
                - Pairing code validates authorization
                - Server generates unique device_id + auth_token
                - Token stored securely on agent (file permissions)
                
                Heartbeat:
                - Every request includes Authorization: Bearer <token>
                - Server validates token against device_id
                - Token rotation: periodic re-issue (configurable)
                
                Task Execution:
                - Task assignment via API (authenticated)
                - Data download via Django proxy (no direct Drive access)
                - Results uploaded via Django proxy
                - All traffic logged for audit
            """),
            ("3. Attack Simulation Safety", """
                All attacks are SIMULATED ONLY:
                
                What IS simulated:
                - Virtual resource state changes (CPU, RAM, latency, risk)
                - Kill chain progression (RECON -> OBJECTIVES)
                - Visual attack packets on topology
                - Security alerts and logs
                - GA re-optimization triggers
                
                What is NOT done:
                - No real network attacks
                - No malware execution
                - No credential theft
                - No data exfiltration
                - No system modification
                - No Google Drive modification during simulation
            """),
            ("4. Data Protection", """
                At Rest:
                - Database: MySQL with encryption at rest (if configured)
                - Google Drive: AES-256 (Google managed)
                - MEC agent config: File permissions (600 on Linux)
                
                In Transit:
                - TLS 1.2+ for all HTTP/WS
                - Service account JWT for Google API
                
                Secrets Management:
                - .env file (never committed)
                - Service account JSON (file permissions)
                - MEC tokens: not logged, not in frontend
            """),
        ]
        self._create_pdf(filepath, "Security Architecture Guide", sections)
    
    def generate_data_flow_guide(self, filepath):
        sections = [
            ("1. End-to-End Data Flow", """
                Complete data lifecycle in SecureDT:
                
                1. USER UPLOAD
                   User -> Web UI -> Django API -> Google Drive (datasets/)
                   
                2. DATA VALIDATION
                   Django validates CSV format, size, structure
                   Metadata extracted and stored
                   
                3. SECURITY CHECK
                   Privacy/sensitivity tags applied
                   Access controls verified
                   
                4. SCHEDULER (GA)
                   Task submitted -> GA optimization -> Resource selected
                   Only ONLINE resources considered
                   
                5. DATA TRANSFER TO MEC
                   MEC Agent -> Django API -> Google Drive download
                   Encrypted in transit
                   
                6. MEC PROCESSING
                   Agent executes workload
                   Measures: time, CPU, RAM, energy
                   
                7. RESULT RETURN
                   Agent -> Django API -> Google Drive (results/)
                   
                8. DIGITAL TWIN UPDATE
                   Resource states updated
                   Dashboard refreshed via WebSocket
            """),
            ("2. Animated Visualization", """
                Data Flow Page shows:
                - 10-stage pipeline with real-time status
                - Network topology with Three.js
                - Animated packets: DATA (cyan), ATTACK (red), RESULT (green)
                - Live metrics: bandwidth, latency, duration, success rate
                
                Packet Types:
                - DATA: User upload, dataset transfer to MEC
                - TASK: Task assignment from scheduler to MEC
                - RESULT: Completed task output from MEC to Drive
                - TELEMETRY: Heartbeat data from MEC to server
                - ATTACK: Simulated attack traffic (red)
            """),
            ("3. Measured Metrics", """
                All metrics are REAL measurements:
                
                Upload/Download:
                - Transfer speed (MB/s)
                - Duration (ms)
                - File size (bytes)
                - Source/Destination
                
                MEC Execution:
                - Execution time (seconds)
                - CPU utilization (%)
                - RAM utilization (%)
                - Estimated energy (Wh) - labeled as ESTIMATED
                - Network latency (ms)
                
                Note: Energy is estimated from CPU usage (software-based).
                Hardware power meters required for accurate measurement.
            """),
        ]
        self._create_pdf(filepath, "Data Flow and Communication Guide", sections)
    
    def generate_review_guide(self, filepath):
        sections = [
            ("1. Project Summary", """
                SecureDT is a research prototype demonstrating intelligent and secure
                task scheduling for digital twin-enabled edge-cloud networks.
                
                Key Innovations:
                1. MEC Agent with automatic registration and heartbeat-based lifecycle
                2. Security-aware Genetic Algorithm scheduler
                3. Real-time Digital Twin with attack response
                4. Google Drive integration via secure Django proxy
                5. Comprehensive visualization (topology, pipeline, analytics)
            """),
            ("2. Technical Stack", """
                Backend:
                - Django 5.2 + Django REST Framework
                - MySQL 8.0
                - Channels (WebSocket)
                - scikit-learn (Random Forest)
                - Google Drive API (service account)
                
                MEC Agent:
                - Python 3.11+
                - psutil (system telemetry)
                - requests (HTTP client)
                - PyInstaller (Windows .exe)
                
                Frontend:
                - Vanilla ES6+ JavaScript
                - Pico.css (lightweight CSS framework)
                - Chart.js v4 (analytics)
                - Three.js r158 (3D topology)
            """),
            ("3. Evaluation Methodology", """
                Baseline Algorithms:
                - Random: Random resource assignment
                - Greedy: Minimum latency per task
                - Privacy-Aware: Minimum privacy loss
                - Proposed GA: Multi-objective with security
                
                Metrics Collected:
                - Latency (ms): End-to-end task completion
                - Energy (J): Estimated consumption
                - Privacy Loss: Normalized exposure metric
                - Security Risk: Resource threat level
                - Deadline Success: % tasks meeting deadline
                
                Test Scenarios:
                - 1, 3, 10, 50 MEC nodes
                - 100, 1000, 10000 tasks
                - With/without attacks
                - Varying privacy/security requirements
            """),
            ("4. Reproducibility", """
                All experiments reproducible:
                - Fixed random seeds (DATASET_SEED=42)
                - Synthetic dataset generators
                - Configuration via .env and config.yaml
                - Docker support planned
                
                Run Experiments:
                python manage.py shell -c "
                from engine.scheduler import Scheduler
                from engine.digital_twin import DigitalTwin
                dt = DigitalTwin()
                sched = Scheduler(dt)
                # ... run experiments
                "
            """),
        ]
        self._create_pdf(filepath, "Review 0 Documentation", sections)


def main():
    """Main entry point."""
    generator = SecureDTDocGenerator()
    generator.generate_all()
    print(f"\nAll documentation generated in: {generator.output_dir}")


if __name__ == "__main__":
    main()