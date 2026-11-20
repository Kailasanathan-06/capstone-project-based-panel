import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Image, FrameBreak, Table, TableStyle, NextPageTemplate)
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, 'figures')
OUT = os.path.join(BASE, 'SecureDT_IEEE_Paper.pdf')

# Page layout (IEEE-like, letter)
page_w, page_h = letter
margin_top = 0.75 * inch
margin_bottom = 1.0 * inch
margin_side = 0.625 * inch
gutter = 0.2 * inch
col_w = (page_w - 2*margin_side - gutter) / 2.0

title_h = 3.15 * inch
# Frames
full_frame = Frame(margin_side, page_h - margin_top - title_h, page_w - 2*margin_side, title_h,
                   id='full', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=4)
f_left = Frame(margin_side, margin_bottom, col_w, page_h - margin_top - margin_bottom - title_h - 0.05*inch,
               id='fleft', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
f_right = Frame(margin_side + col_w + gutter, margin_bottom, col_w, page_h - margin_top - margin_bottom - title_h - 0.05*inch,
                id='fright', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
left = Frame(margin_side, margin_bottom, col_w, page_h - margin_top - margin_bottom,
             id='left', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
right = Frame(margin_side + col_w + gutter, margin_bottom, col_w, page_h - margin_top - margin_bottom,
              id='right', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman', 10)
    canvas.drawCentredString(page_w/2.0, 0.55*inch, str(doc.page))
    canvas.restoreState()

doc = BaseDocTemplate(OUT, pagesize=letter,
                      leftMargin=margin_side, rightMargin=margin_side,
                      topMargin=margin_top, bottomMargin=margin_bottom)
doc.addPageTemplates([
    PageTemplate(id='first', frames=[full_frame, f_left, f_right], onPage=on_page),
    PageTemplate(id='later', frames=[left, right], onPage=on_page),
])

# Styles
paper_title = ParagraphStyle('PaperTitle', fontName='Times-Bold', fontSize=24, leading=28,
                             alignment=TA_CENTER, spaceAfter=10)
author_s = ParagraphStyle('Author', fontName='Times-Roman', fontSize=11, leading=14,
                          alignment=TA_CENTER, spaceAfter=2)
affil_s = ParagraphStyle('Affil', fontName='Times-Roman', fontSize=10, leading=12,
                         alignment=TA_CENTER, spaceAfter=4)
abstract_s = ParagraphStyle('Abstract', fontName='Times-Bold', fontSize=9, leading=11,
                            alignment=TA_JUSTIFY, leftIndent=18, rightIndent=18, spaceAfter=4)
keywords_s = ParagraphStyle('Keywords', fontName='Times-Italic', fontSize=9, leading=11,
                            alignment=TA_JUSTIFY, leftIndent=18, rightIndent=18, spaceAfter=4)
h1 = ParagraphStyle('H1', fontName='Times-Roman', fontSize=10, leading=12,
                    alignment=TA_CENTER, spaceBefore=10, spaceAfter=4)
h2 = ParagraphStyle('H2', fontName='Times-Italic', fontSize=10, leading=12,
                    alignment=TA_LEFT, spaceBefore=6, spaceAfter=2)
body = ParagraphStyle('Body', fontName='Times-Roman', fontSize=10, leading=12,
                      alignment=TA_JUSTIFY, spaceAfter=3, firstLineIndent=14)
body0 = ParagraphStyle('Body0', fontName='Times-Roman', fontSize=10, leading=12,
                       alignment=TA_JUSTIFY, spaceAfter=3, firstLineIndent=0)
bullet = ParagraphStyle('Bullet', fontName='Times-Roman', fontSize=10, leading=12,
                        alignment=TA_JUSTIFY, spaceAfter=2, leftIndent=10, firstLineIndent=0)
cap = ParagraphStyle('Cap', fontName='Times-Roman', fontSize=8, leading=9.5,
                     alignment=TA_CENTER, spaceBefore=2, spaceAfter=6)
ref = ParagraphStyle('Ref', fontName='Times-Roman', fontSize=8, leading=9.5,
                     alignment=TA_JUSTIFY, spaceAfter=2, leftIndent=12, firstLineIndent=-12)
small = ParagraphStyle('Small', fontName='Times-Roman', fontSize=8, leading=9.5,
                       alignment=TA_JUSTIFY, spaceAfter=2)
cell = ParagraphStyle('Cell', fontName='Times-Roman', fontSize=8, leading=9.5, alignment=TA_LEFT)
cell_c = ParagraphStyle('CellC', fontName='Times-Roman', fontSize=8, leading=9.5, alignment=TA_CENTER)
cell_h = ParagraphStyle('CellH', fontName='Times-Bold', fontSize=8, leading=9.5, alignment=TA_CENTER)

story = []

def add_fig(filename, width, caption_text, max_h=2.25*inch):
    path = os.path.join(FIG, filename)
    elems = []
    if os.path.exists(path):
        im = Image(path)
        iw, ih = im.imageWidth, im.imageHeight
        aspect = ih / float(iw)
        h = width * aspect
        if h > max_h:
            h = max_h
            width = h / aspect
        elems.append(Image(path, width=width, height=h))
    elems.append(Paragraph(caption_text, cap))
    return elems

def make_table(data, col_widths, caption_text):
    t = Table(data, colWidths=col_widths, repeatRows=1, hAlign='CENTER')
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Times-Roman'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.Color(0.93,0.93,0.93)),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    return [t, Paragraph(caption_text, cap)]

# ---------- TITLE BLOCK ----------
story.append(Paragraph('Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge&ndash;Cloud Networks', paper_title))
story.append(Paragraph('Dr. R. G. Suresh Kumar', author_s))
story.append(Paragraph('Professor and Head of the Department<br/>Department of Computer Science and Engineering<br/>Rajiv Gandhi College of Engineering and Technology<br/>Puducherry &ndash; 607 403, India<br/>Email: sureshkumar_rg@rgcet.edu.in', affil_s))
story.append(Spacer(1, 4))
story.append(Paragraph('DEVANAND P, HARISH T, KAILASANATHAN M', author_s))
story.append(Paragraph('Department of Computer Science and Engineering<br/>Rajiv Gandhi College of Engineering and Technology<br/>Puducherry &ndash; 607 403, India<br/>Email: devanand.slp@gmail.com, harishthirunavukkarasu24@gmail.com, m.kailasam.06@gmail.com', affil_s))
story.append(Paragraph('<i><b>Abstract</b></i>&mdash;Latency-sensitive and privacy-critical applications increasingly rely on coordinated use of local devices, edge servers, and cloud platforms. Distributing workloads across these tiers, however, raises difficult questions about where tasks should execute, where data should be stored, and how a system should respond to node failures, stale telemetry, or unsafe inputs. This paper presents SecureDT, an implemented digital twin&ndash;enabled framework for secure task scheduling, dataset analysis, and policy-driven storage allocation in edge&ndash;cloud environments. SecureDT integrates measured local workstation telemetry, heartbeat-based Multi-access Edge Computing (MEC) monitoring, and an explicitly modeled cloud tier within a unified resource view. A multi-objective genetic algorithm (GA) optimizes task placement by considering latency, energy, privacy loss, and security risk, while hard feasibility rules enforce placement policies before and during assignment. The platform also provides a 10-stage ZIP dataset ingestion pipeline with integrity verification, schema validation, dependency-cycle detection, timeout handling, and persistent reporting, applying policy-aware allocation logic to dataset and storage placement decisions. To demonstrate domain relevance and robustness, SecureDT includes 14 hospital workload processing scenarios and a 30-case structured test suite covering success, failure, and loop/timeout conditions. We describe the architecture, algorithms, implementation, and a Phase&nbsp;1 evidence-based qualitative assessment of the framework, and discuss its strengths, current limitations, and a roadmap toward adaptive, trust-aware edge&ndash;cloud orchestration.', abstract_s))
story.append(Paragraph('<i><b>Index Terms</b></i>&mdash;Digital twin, edge computing, MEC, cloud storage, task scheduling, genetic algorithm, privacy-aware placement, trust-aware systems, secure data management, workload analysis.', keywords_s))
story.append(FrameBreak())
story.append(NextPageTemplate('later'))

# ---------- I. INTRODUCTION ----------
story.append(Paragraph('I. INTRODUCTION', h1))
story.append(Paragraph('Modern computing systems increasingly operate at the intersection of centralized clouds and resource-constrained endpoints. Applications in healthcare, smart infrastructure, transportation, and industrial monitoring generate continuous streams of data that must often be processed within tight time bounds while preserving confidentiality and integrity. Cloud platforms provide elasticity and large-scale storage, but exclusive dependence on remote data centers can introduce network delay, bandwidth pressure, and unnecessary exposure for sensitive records. Local processing reduces communication overhead and improves control over data, yet individual devices may lack sufficient compute, memory, or storage capacity to handle sustained or bursty workloads [1], [6], [7].', body0))
story.append(Paragraph('Edge computing and Multi-access Edge Computing (MEC) address this tension by placing computational resources closer to data sources [2], [5]. In principle, this enables lower latency, reduced backhaul traffic, and more flexible placement decisions. In practice, however, edge&ndash;cloud collaboration creates a complex orchestration problem. A platform must determine not only where a task can run efficiently, but also whether a destination is currently available, trustworthy, and permitted under privacy or organizational policies. Storage decisions add further constraints: some data must remain on-premises, some may be shared with trusted edge nodes, and only selected workloads may be eligible for cloud placement.', body))
story.append(Paragraph('Digital twin technology offers a promising abstraction for managing such complexity [3], [10]. By maintaining a software representation of physical and logical resources, a system can observe current state, reason about constraints, and support informed decisions. SecureDT applies this concept in an implemented research testbed for privacy-aware task scheduling and tri-tier storage management. The platform integrates a Django-based web interface and REST APIs with modular engines for digital twin state, policy enforcement, scheduling, dataset analysis, and storage operations. It is designed to make the interactions among performance, policy, and security explicit and traceable.', body))
story.append(Paragraph('The key contributions of this work are:', body0))
story.append(Paragraph('1) <b>Privacy-aware tri-tier architecture:</b> A unified model spanning local, MEC, and cloud tiers with explicit placement scopes (LOCAL_ONLY, TRUSTED_EDGE, CLOUD_ALLOWED) and integrity-verified storage handling.', bullet))
story.append(Paragraph('2) <b>Digital twin resource model:</b> A consistent view of heterogeneous resources combining measured local hardware telemetry, heartbeat-based MEC status with stale detection, and an explicitly simulated cloud tier.', bullet))
story.append(Paragraph('3) <b>Multi-objective scheduling:</b> A genetic algorithm for task-to-resource mapping that considers latency, energy, privacy loss, and security risk, together with hard feasibility checks and support for baseline comparison; policy-aware allocation is applied within the dataset analysis workflow.', bullet))
story.append(Paragraph('4) <b>Defensive analysis pipeline:</b> A 10-stage ZIP ingestion workflow with archive validation, schema checks, dependency-cycle detection, timeout handling, SHA-256 verification, and persistent reporting.', bullet))
story.append(Paragraph('5) <b>Scenario-based evaluation assets:</b> Fourteen hospital workload scenarios and a 30-case structured ZIP test suite covering success, failure, security, and loop/timeout conditions.', bullet))
story.append(Paragraph('The remainder of this paper is organized as follows. Section II reviews background and motivation. Section III describes the system architecture. Section IV presents the methodology, including the analysis pipeline, policy model, and scheduling approach. Section V details implementation and the evaluation setup. Section VI presents a Phase&nbsp;1 qualitative assessment, limitations, and future directions, and Section VII concludes the paper.', body))

# ---------- II. BACKGROUND ----------
story.append(Paragraph('II. BACKGROUND AND MOTIVATION', h1))
story.append(Paragraph('<i>A. Edge&ndash;Cloud Task Offloading</i>', h2))
story.append(Paragraph('Task offloading aims to decide whether computation should execute locally, on an edge/MEC server, or in the cloud. The decision is influenced by factors such as input size, processing demand, network conditions, queueing delay, and energy consumption [1], [6], [12]. Because these factors vary across nodes and over time, offloading is commonly formulated as a multi-objective optimization problem. Heuristic and metaheuristic methods, including genetic algorithms, are widely used to explore large assignment spaces and balance competing objectives without requiring simple convex formulations [4], [11].', body0))
story.append(Paragraph('<i>B. Digital Twins for Distributed Systems</i>', h2))
story.append(Paragraph('A digital twin is a virtual counterpart that reflects the state of a corresponding entity or system [3]. In distributed computing, digital twins can aggregate telemetry, represent capacity and health, and provide a basis for monitoring and decision support [10]. For orchestration, a twin is valuable not only because it stores current values, but because it presents heterogeneous sources&mdash;such as measured hardware metrics, remote heartbeats, and modeled resources&mdash;through a common interface. SecureDT uses this abstraction to expose availability, utilization, latency, trust, and risk attributes to both users and scheduling logic.', body0))
story.append(Paragraph('<i>C. Privacy, Security, and Safe Failure Handling</i>', h2))
story.append(Paragraph('In privacy-sensitive domains, placement policies must be treated as constraints rather than soft preferences. Data may include confidential attributes that restrict movement across administrative or network boundaries. Systems must also cope with faulty or adversarial conditions: malformed archives, schema violations, unauthorized actions, stalled workers, and dependency errors can all disrupt processing. Effective platforms therefore require validation, integrity checks, bounded failure handling, and auditable outcomes. SecureDT incorporates these concerns into its ingestion, storage, and scheduling workflows to support traceable and defensive operation.', body0))
story.append(Paragraph('<i>D. Need for an Integrated Platform</i>', h2))
story.append(Paragraph('Although scheduling, storage management, and security are often studied separately, real deployments require them to work together. A placement that minimizes latency may violate privacy policy; a node that becomes stale affects both feasibility and reliability; and a storage action without integrity verification undermines trust in results. SecureDT is motivated by the need for an integrated testbed in which these interactions are explicit, observable, and reproducible through structured scenarios and reports.', body))

# ---------- III. ARCHITECTURE ----------
story.append(Paragraph('III. SYSTEM ARCHITECTURE', h1))
story.append(Paragraph('Fig. 1 shows the high-level architecture of SecureDT. The platform is organized into four cooperating layers: (i) a web and API interface, (ii) policy, digital twin, and scheduling engines, (iii) security and audit mechanisms, and (iv) a tri-tier execution and storage substrate. This separation allows user interaction, decision logic, and data handling to evolve independently while sharing a common resource and reporting model.', body0))
story.extend(add_fig('architecture.png', col_w, 'Fig. 1. High-level architecture of the SecureDT platform.', max_h=2.2*inch))

story.append(Paragraph('<i>A. Application and API Layer</i>', h2))
story.append(Paragraph('The user-facing layer is implemented with Django views and templates. Core pages include the dashboard, dataset upload, digital twin, edge system, storage allocation, dataset reports, report details, and task history. These pages are backed by application APIs that provide dashboard statistics, upload and demo-upload processing, digital twin status, edge system checks and registration, storage allocation records, report retrieval and export, and task history. Modular endpoints also support authentication, MEC management, cloud operations, analytics, and dataset services, enabling the platform to function as an integrated environment rather than a collection of isolated tools.', body0))

story.append(Paragraph('<i>B. Tri-Tier Storage and Execution Substrate</i>', h2))
story.append(Paragraph('SecureDT defines three storage tiers outside the public web root, summarized in Table I and Fig. 2. LOCAL_STORAGE provides 50 GB of on-premises capacity for data that must remain local. MEC_STORAGE provides 200 GB of edge micro-datacenter capacity for trusted low-latency workloads. CLOUD_STORAGE provides a 1 TB centralized emulator for data eligible for broader placement. The storage manager initializes directories, tracks usage metadata, computes SHA-256 checksums for stored artifacts, and supports idempotent handling when a verified copy already exists. These mechanisms provide a basis for traceable and policy-aware storage operations.', body0))

t1_data = [
    [Paragraph('<b>Tier</b>', cell_h), Paragraph('<b>Type</b>', cell_h), Paragraph('<b>Capacity</b>', cell_h), Paragraph('<b>Policy Scope</b>', cell_h)],
    [Paragraph('LOCAL_STORAGE', cell), Paragraph('On-prem local', cell_c), Paragraph('50 GB', cell_c), Paragraph('LOCAL_ONLY', cell_c)],
    [Paragraph('MEC_STORAGE', cell), Paragraph('Edge micro-datacenter', cell_c), Paragraph('200 GB', cell_c), Paragraph('TRUSTED_EDGE', cell_c)],
    [Paragraph('CLOUD_STORAGE', cell), Paragraph('Cloud emulator', cell_c), Paragraph('1000 GB', cell_c), Paragraph('CLOUD_ALLOWED', cell_c)],
]
story.extend(make_table(t1_data, [1.0*inch, 1.05*inch, 0.55*inch, 0.85*inch], 'TABLE I<br/>TRI-TIER STORAGE CONFIGURATION'))
story.extend(add_fig('storage_tiers.png', col_w, 'Fig. 2. Storage tier capacities and privacy placement scopes.', max_h=1.95*inch))

story.append(Paragraph('<i>C. Digital Twin Resource Model</i>', h2))
story.append(Paragraph('The digital twin maintains virtual representations of local, MEC, and cloud resources with mixed-fidelity telemetry. The local workstation is modeled using measured hardware indicators (e.g., CPU and memory utilization via system monitoring), providing a measured view of on-prem capacity. MEC nodes are tracked through heartbeat updates and associated freshness information; stale or unavailable nodes can be excluded from eligible placement. The cloud tier is explicitly represented as a simulated environment with modeled latency and capacity characteristics. Each resource state exposes attributes such as availability, utilization, latency, trust, and security risk, enabling consistent use by monitoring views and decision logic; trust and risk values are currently model-derived or scenario-influenced rather than continuously learned from longitudinal evidence.', body0))

story.append(Paragraph('<i>D. Security and Traceability Mechanisms</i>', h2))
story.append(Paragraph('SecureDT incorporates defensive measures across the workflow. Archive ingestion validates structure and content, rejects path traversal entries, blocks disallowed executable types, and enforces decompression limits. Policy checks prevent privacy-incompatible placement, while storage actions use SHA-256 checksums to verify artifact integrity. Security monitoring and attack-handling components in the current testbed operate primarily through model-based risk computation and virtual (in-process) simulation to demonstrate defensive behavior. Analysis results, scheduler outputs, and storage actions are recorded in persistent reports and task histories. These features support auditability and safe failure handling within the research testbed, without implying formal regulatory certification or real adversarial hardening.', body))

# ---------- IV. METHODOLOGY ----------
story.append(Paragraph('IV. METHODOLOGY', h1))
story.append(Paragraph('<i>A. Dataset Ingestion and 10-Stage Analysis Pipeline</i>', h2))
story.append(Paragraph('A central component of SecureDT is its ZIP-based dataset analysis workflow. As shown in Fig. 3, each submission is processed through ten stages: (1) upload receipt, (2) archive validation, (3) dataset inventory, (4) feature extraction, (5) resource status check, (6) privacy and security validation, (7) scheduling/allocation decision, (8) allocation recommendation, (9) storage execution or simulation, and (10) persistent report generation.', body0))
story.extend(add_fig('workflow_pipeline.png', col_w, 'Fig. 3. Ten-stage dataset upload and analysis pipeline.', max_h=1.45*inch))
story.append(Paragraph('Archive validation confirms that the input is a readable ZIP file, computes an archive checksum, and applies safety checks. The pipeline rejects path traversal entries, blocks disallowed executable extensions, and enforces decompression size limits. Manifest validation requires key fields such as a scenario identifier and a resource list with at least three tiers. Task metadata is examined for dependency cycles using graph traversal; when a cycle is detected, the submission is rejected safely rather than allowed to enter an unbounded execution state. Timeout conditions are identified when simulated latency exceeds configured bounds, and bounded retry behavior is recorded where applicable.', body))
story.append(Paragraph('The workflow supports two operating modes. In simulation mode, placement decisions are computed and reported without physically writing tier artifacts. In execution mode, selected files are written to the corresponding storage directories, checksums are verified, storage usage is updated, and replica records are created. In both modes, the system produces a structured, persistent report that can be inspected through the web interface or exported as CSV for further analysis.', body))

story.append(Paragraph('<i>B. Privacy Placement Policies and Eligibility</i>', h2))
story.append(Paragraph('SecureDT enforces privacy placement as a hard eligibility constraint. Each workload or dataset component is associated with a policy scope that determines allowable destinations, as summarized in Table II. LOCAL_ONLY data must remain on the local workstation. TRUSTED_EDGE data may be placed on the local tier or on authenticated, non-stale MEC nodes. CLOUD_ALLOWED data may use any eligible tier, subject to availability and operational checks. Filtering candidates before optimization reduces the likelihood that performance-oriented scoring selects a non-compliant assignment.', body0))
t2_data = [
    [Paragraph('<b>Policy</b>', cell_h), Paragraph('<b>Eligible Destinations</b>', cell_h), Paragraph('<b>Placement Intent</b>', cell_h)],
    [Paragraph('LOCAL_ONLY', cell_c), Paragraph('Local workstation only', cell), Paragraph('Strict on-prem confinement', cell)],
    [Paragraph('TRUSTED_EDGE', cell_c), Paragraph('Local and authenticated MEC', cell), Paragraph('Trusted low-latency edge use', cell)],
    [Paragraph('CLOUD_ALLOWED', cell_c), Paragraph('Local, MEC, and Cloud', cell), Paragraph('Flexible placement when permitted', cell)],
]
story.extend(make_table(t2_data, [0.9*inch, 1.3*inch, 1.25*inch], 'TABLE II<br/>PRIVACY PLACEMENT POLICIES'))

story.append(Paragraph('At dispatch time, policy validation can be applied again to confirm that the selected resource remains compliant. This two-stage view&mdash;eligibility filtering followed by dispatch validation&mdash;helps maintain consistency when resource availability or freshness changes between planning and execution.', body))

story.append(Paragraph('<i>C. Multi-Objective Genetic Algorithm Scheduling</i>', h2))
story.append(Paragraph('Task scheduling in heterogeneous edge&ndash;cloud environments involves trade-offs among multiple objectives. SecureDT includes a genetic algorithm (GA) scheduler for task-to-resource assignment and dispatch. In this formulation, a chromosome encodes the resource index selected for each task. The population evolves through tournament selection, single-point crossover, per-gene mutation, and elitism over a configured number of generations. Resources that are offline, stale, or policy-ineligible are excluded from candidate generation, and tasks without feasible placements can be marked as blocked. In the current implementation, the GA and baseline schedulers are applied in the task scheduling/benchmarking path, while the dataset-upload pipeline performs deterministic, policy-aware multi-objective allocation scoring for storage placement recommendations; aligning these decision mechanisms and their reporting is an identified improvement target.', body0))
story.append(Paragraph('The fitness function combines latency, energy, privacy loss, and security risk, with additional penalties for deadline violations and infeasible assignments (Fig. 4). Conceptually, the objective can be expressed as:', body0))
story.append(Paragraph('Fitness = w<sub>1</sub>&middot;Latency + w<sub>2</sub>&middot;Energy + w<sub>3</sub>&middot;PrivacyLoss + w<sub>4</sub>&middot;SecurityRisk + P', 
                        ParagraphStyle('Eq', parent=body0, leftIndent=16, firstLineIndent=0, spaceBefore=2, spaceAfter=2, fontName='Times-Italic')))
story.append(Paragraph('where <i>w<sub>1</sub></i>&ndash;<i>w<sub>4</sub></i> are weighting coefficients and <i>P</i> represents penalty terms for constraint violations or missed deadlines. The GA implementation in the engine is designed to explore diverse assignments while preserving feasible, policy-compliant solutions. For comparative evaluation, the platform also supports baseline strategies such as round-robin, first-fit, random, greedy, and privacy-aware scheduling in its broader benchmarking design. Current objective weights and decision logic are largely static, and AI-based risk analysis (where used) is offline or rule-based rather than continuously adaptive.', body))
story.extend(add_fig('ga_fitness.png', col_w, 'Fig. 4. Multi-objective fitness components used in GA-based scheduling.', max_h=1.95*inch))

story.append(Paragraph('<i>D. Hospital Workload and Scenario Model</i>', h2))
story.append(Paragraph('To demonstrate applicability to privacy-sensitive domains, SecureDT defines 14 hospital workload scenarios grouped into four categories (Table III). These scenarios exercise both normal processing and controlled fault conditions. Success cases include medical image preprocessing, clinical record risk scoring, laboratory panel analysis, medical document metadata extraction, and appointment scheduling. Controlled error cases validate malformed input handling, missing mandatory fields, and unsupported formats. Defensive security cases address unauthorized submission, invalid MEC credentials, and blocked unauthorized cloud replication. Timeout and retry cases assess execution time limits, unresponsive workers, and bounded retry exhaustion.', body0))
t3_data = [
    [Paragraph('<b>Category</b>', cell_h), Paragraph('<b>Count</b>', cell_h), Paragraph('<b>Examples / Focus</b>', cell_h)],
    [Paragraph('Success', cell_c), Paragraph('5', cell_c), Paragraph('Image preprocessing, EHR scoring, lab analysis, metadata extraction, scheduling', cell)],
    [Paragraph('Controlled error', cell_c), Paragraph('3', cell_c), Paragraph('Malformed image, missing fields, unsupported format rejection', cell)],
    [Paragraph('Defensive security', cell_c), Paragraph('3', cell_c), Paragraph('Unauthorized submission, invalid MEC auth, blocked replication', cell)],
    [Paragraph('Timeout / retry', cell_c), Paragraph('3', cell_c), Paragraph('Execution timeout, unresponsive worker, retry exhaustion', cell)],
]
story.extend(make_table(t3_data, [1.0*inch, 0.4*inch, 2.05*inch], 'TABLE III<br/>HOSPITAL WORKLOAD SCENARIO CATEGORIES'))
story.append(Paragraph('Together, these scenarios provide a structured way to evaluate correctness, safety, and resilience. They complement the archive-based test suite by focusing on domain-oriented processing behaviors and policy enforcement outcomes.', body))

# ---------- V. IMPLEMENTATION ----------
story.append(Paragraph('V. IMPLEMENTATION AND EVALUATION SETUP', h1))
story.append(Paragraph('<i>A. Software Implementation</i>', h2))
story.append(Paragraph('SecureDT is implemented primarily in Python. The backend uses Django and Django REST Framework for web views and APIs, with SQLite as the default database and optional MySQL support. The engine layer includes modules for digital twin state management, genetic algorithm and baseline scheduling, policy enforcement, dataset analysis, storage management, hospital workload processing, risk/security monitoring, and related support functions. Data processing and analysis components use libraries such as NumPy, pandas, scikit-learn, SciPy, Pillow, and scikit-image. Local telemetry is collected through system monitoring utilities (e.g., psutil), and reporting/export features support structured inspection of results. A Random Forest&ndash;based risk classifier with rule-based fallback is included for offline/model-based risk analysis. The platform also includes components for MEC agent pairing, authentication, heartbeat-based status tracking, and interaction within the broader edge workflow.', body0))

story.append(Paragraph('<i>B. Structured ZIP Test Suite</i>', h2))
story.append(Paragraph('To validate ingestion and analysis behavior, SecureDT provides 30 standardized ZIP archives: 10 success, 10 failure, and 10 loop/timeout scenarios (Fig. 5). Success cases exercise valid multi-tier allocation, mixed file formats, capacity-aware and privacy-aware decisions, and multi-task scheduling. Failure cases include corrupt archives, invalid or malformed manifests, missing or mistyped fields, insufficient resource tiers, disallowed executable content, path traversal entries, and decompression-limit violations. Loop/timeout cases cover large bounded queues, dependency cycles (including self, mutual, and multi-node cycles), watchdog timeouts, retry storms, retry exhaustion, and mixed cycle-timeout conditions.', body0))
story.extend(add_fig('scenario_distribution.png', col_w, 'Fig. 5. Distribution of the 30-case ZIP scenario test suite.', max_h=1.85*inch))
story.append(Paragraph('Each valid archive follows a consistent internal structure containing <i>manifest.json</i>, per-tier <i>resource.json</i> descriptors and dataset files under local/MEC/cloud directories, <i>tasks/task_metadata.json</i>, and <i>expected_results/expected_result.json</i>. This consistency enables repeatable functional testing and comparison between expected and observed outcomes across the analysis pipeline.', body))

story.append(Paragraph('<i>C. Reporting, Metrics, and Observability</i>', h2))
story.append(Paragraph('For every analyzed submission, SecureDT generates a persistent structured report that records validation outcomes, scheduler/allocation decisions, allocation recommendations, storage actions, and timing information. Reports can be reviewed through the web interface and exported for offline analysis. Reporting fields include processing duration, scheduler duration, and a simulated energy estimate, which is explicitly treated as model-based rather than hardware-measured. The dashboard aggregates operational indicators such as upload counts, report status, task queue states, storage usage, recent audit events, and digital twin summaries. Consistent provenance labeling of measured, simulated, and model-based values across all outputs remains an important refinement goal.', body0))

# ---------- VI. DISCUSSION ----------
story.append(Paragraph('VI. PHASE 1 ASSESSMENT AND DISCUSSION', h1))
story.append(Paragraph('<i>A. Baseline Qualitative Assessment</i>', h2))
story.append(Paragraph('A Phase&nbsp;1 code and architecture audit of the repository indicates that scheduling, storage management, and defensive checks are coordinated within a single digital twin&ndash;enabled workflow. The 10-stage ingestion pipeline provides structured handling of archive inputs, from validation and inventory to allocation and reporting. Policy-aware eligibility checks help ensure that placement decisions respect defined privacy scopes, while SHA-256 verification and persistent reports improve traceability of storage and analysis actions. The scenario suites and test assets provide a basis for structured validation of successful operations and controlled failure conditions; comprehensive runtime verification of all cases remains part of ongoing evaluation.', body0))

story.append(Paragraph('<i>B. Scheduler Comparison Perspective</i>', h2))
story.append(Paragraph('Fig. 6 provides an illustrative comparison between a GA-oriented scheduling approach and several baseline strategies in terms of normalized makespan and policy violation count. The figure reflects an important design principle of SecureDT: performance gains should not come at the expense of feasibility or policy compliance. In sensitive environments, a placement that is fast but violates locality or trust constraints is unacceptable. Accordingly, the platform emphasizes constraint-aware decision-making alongside optimization objectives.', body0))
story.extend(add_fig('scheduler_comparison.png', col_w, 'Fig. 6. Illustrative comparison of scheduling strategies by normalized makespan and policy violations.', max_h=2.0*inch))

story.append(Paragraph('<i>C. Alignment and Practical Implications</i>', h2))
story.append(Paragraph('By combining digital twin state, policy enforcement, and structured reporting, SecureDT supports a workflow in which decisions can be inspected and justified. This is particularly relevant for domains where operators need to understand not only the final placement, but also why a destination was eligible, what validations were performed, and how failures were handled. The modular architecture also allows individual components&mdash;such as telemetry sources, schedulers, or storage backends&mdash;to be refined without redesigning the entire system.', body0))

story.append(Paragraph('<i>D. Limitations and Future Work</i>', h2))
story.append(Paragraph('Several limitations of the current implementation should be acknowledged. First, the cloud tier is represented as a simulated/emulated environment, so cloud-side results do not constitute measurements from a production deployment. Second, while a genetic algorithm scheduler is implemented for task scheduling, some dataset-upload allocation paths currently use deterministic heuristic scoring with GA-style reporting metadata; unifying optimization behavior and method labeling across all workflows is an important area for improvement. Third, energy, risk, and some performance values are simulation/model-based estimates rather than direct hardware measurements, and provenance labeling should be made fully consistent across reports and interfaces. Fourth, trust representation and AI-based risk analysis are presently coarse, offline, or rule-based rather than continuously adaptive and evidence-driven, limiting alignment with trust-aware SecureDT&nbsp;2.0 objectives. Fifth, security evaluation is primarily virtual/simulated within the testbed and requires broader validation under realistic conditions.', body))
story.append(Paragraph('Future work will focus on tighter integration and consistent reporting of optimization methods across all scheduling and allocation paths; hardware-backed telemetry and calibrated energy/latency measurement; and expanded deployment on physical MEC nodes. Advancing toward SecureDT&nbsp;2.0 will require adaptive, evidence-based trust modeling integrated into scheduling objectives, feedback-driven optimization, and anomaly-informed security responses. Additional empirical studies using the 14 scenarios and 30-case suite with reproducible protocols and clear measured/simulated/model-based provenance will further strengthen validity. Enhancing security evaluation with broader adversarial scenarios and formal verification of selected policy properties would also be valuable extensions.', body))

# ---------- VII. CONCLUSION ----------
story.append(Paragraph('VII. CONCLUSION', h1))
story.append(Paragraph('This paper presented SecureDT, an implemented digital twin&ndash;enabled framework for secure task scheduling and tri-tier storage management in edge&ndash;cloud environments, together with a Phase&nbsp;1 evidence-based assessment of its current capabilities. The platform integrates heterogeneous (measured and simulated) resource telemetry, privacy-aware placement policies, multi-objective scheduling, and a defensive dataset analysis pipeline within a unified system. Through its tri-tier storage model, 10-stage ingestion workflow, hospital workload scenarios, and 30-case structured test suite, SecureDT provides a practical baseline for policy-compliant, traceable edge&ndash;cloud orchestration. While some components remain simulated, model-based, or methodologically inconsistent across workflows, the framework and audit findings establish a solid foundation for incremental evolution toward adaptive, trust-aware, and rigorously validated SecureDT&nbsp;2.0 capabilities.', body0))

# ---------- ACKNOWLEDGMENT ----------
story.append(Paragraph('ACKNOWLEDGMENT', h1))
story.append(Paragraph('The authors thank the Department of Computer Science and Engineering, Rajiv Gandhi College of Engineering and Technology, Puducherry, for the guidance and support provided during this capstone project.', body0))

# ---------- REFERENCES ----------
story.append(Paragraph('REFERENCES', h1))
refs = [
    '[1] W. Shi, J. Cao, Q. Zhang, Y. Li, and L. Xu, &ldquo;Edge computing: Vision and challenges,&rdquo; <i>IEEE Internet of Things Journal</i>, vol. 3, no. 5, pp. 637&ndash;646, Oct. 2016.',
    '[2] P. Mach and Z. Becvar, &ldquo;Mobile edge computing: A survey on architecture and computation offloading,&rdquo; <i>IEEE Communications Surveys &amp; Tutorials</i>, vol. 19, no. 3, pp. 1628&ndash;1656, 2017.',
    '[3] M. Grieves and J. Vickers, &ldquo;Digital twin: Mitigating unpredictable, undesirable emergent behavior in complex systems,&rdquo; in <i>Transdisciplinary Perspectives on Complex Systems</i>. Cham, Switzerland: Springer, 2017, pp. 85&ndash;113.',
    '[4] D. E. Goldberg, <i>Genetic Algorithms in Search, Optimization, and Machine Learning</i>. Reading, MA, USA: Addison-Wesley, 1989.',
    '[5] T. Taleb, K. Samdanis, B. Mada, H. Flinck, S. Dutta, and D. Sabella, &ldquo;On multi-access edge computing: A survey of the emerging 5G network edge cloud architecture and orchestration,&rdquo; <i>IEEE Communications Surveys &amp; Tutorials</i>, vol. 19, no. 3, pp. 1657&ndash;1681, 2017.',
    '[6] Y. Mao, C. You, J. Zhang, K. Huang, and K. B. Letaief, &ldquo;A survey on mobile edge computing: The communication perspective,&rdquo; <i>IEEE Communications Surveys &amp; Tutorials</i>, vol. 19, no. 4, pp. 2322&ndash;2358, 2017.',
    '[7] R. Buyya <i>et al.</i>, &ldquo;A manifesto for future generation cloud computing: Research directions for the next decade,&rdquo; <i>ACM Computing Surveys</i>, vol. 51, no. 5, pp. 1&ndash;38, Nov. 2018.',
    '[8] J. Gubbi, R. Buyya, S. Marusic, and M. Palaniswami, &ldquo;Internet of Things (IoT): A vision, architectural elements, and future directions,&rdquo; <i>Future Generation Computer Systems</i>, vol. 29, no. 7, pp. 1645&ndash;1660, Sep. 2013.',
    '[9] N. Abbas, Y. Zhang, A. Taherkordi, and T. Skeie, &ldquo;Mobile edge computing: A survey,&rdquo; <i>IEEE Internet of Things Journal</i>, vol. 5, no. 1, pp. 450&ndash;465, Feb. 2018.',
    '[10] F. Tao, H. Zhang, A. Liu, and A. Y. C. Nee, &ldquo;Digital twin in industry: State-of-the-art,&rdquo; <i>IEEE Transactions on Industrial Informatics</i>, vol. 15, no. 4, pp. 2405&ndash;2415, Apr. 2019.',
    '[11] Z. Zhou, X. Chen, E. Li, L. Zeng, K. Luo, and J. Zhang, &ldquo;Edge intelligence: Paving the last mile of artificial intelligence with edge computing,&rdquo; <i>Proceedings of the IEEE</i>, vol. 107, no. 8, pp. 1738&ndash;1762, Aug. 2019.',
    '[12] S. Wang, X. Zhang, Y. Zhang, L. Wang, J. Yang, and W. Wang, &ldquo;A survey on mobile edge networks: Convergence of computing, caching and communications,&rdquo; <i>IEEE Access</i>, vol. 5, pp. 6757&ndash;6779, 2017.',
]
for r in refs:
    story.append(Paragraph(r, ref))

story.append(Spacer(1, 4))
story.append(Paragraph('<i>Note:</i> This paper reflects a Phase&nbsp;1 repository audit of the current implementation. Energy, cloud-tier behavior, and several risk/performance values are simulation/model-based unless explicitly identified as measured. Dataset-upload allocation in the current pipeline may use deterministic heuristic scoring distinct from GA-based task scheduling, and reporting consistency is a target for refinement. Privacy policy labels denote placement controls within this research testbed and do not constitute formal regulatory compliance claims.', small))

doc.build(story)
print('PDF_CREATED', OUT)
