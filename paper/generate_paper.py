from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, FrameBreak, NextPageTemplate, CondPageBreak
from reportlab.platypus import Frame, PageTemplate, BaseDocTemplate
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import os, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(ROOT, 'figures')
OUT = os.path.join(ROOT, 'SecureDT_IEEE_Paper.pdf')

PAGE_W, PAGE_H = letter
MARGIN = 0.62*inch
GUTTER = 0.22*inch
COL_W = (PAGE_W - 2*MARGIN - GUTTER) / 2

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='PaperTitle', parent=styles['Title'], fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor('#111111'), fontName='Times-Bold'))
styles.add(ParagraphStyle(name='PaperAuthor', parent=styles['Normal'], fontSize=9.5, leading=12, alignment=TA_CENTER, spaceAfter=2, fontName='Times-Roman'))
styles.add(ParagraphStyle(name='PaperAffil', parent=styles['Normal'], fontSize=8.5, leading=10.5, alignment=TA_CENTER, spaceAfter=1, fontName='Times-Italic', textColor=colors.HexColor('#222222')))
styles.add(ParagraphStyle(name='PaperEmail', parent=styles['Normal'], fontSize=8.2, leading=10, alignment=TA_CENTER, spaceAfter=8, fontName='Courier', textColor=colors.HexColor('#1a365d')))
styles.add(ParagraphStyle(name='AbstractHead', parent=styles['Normal'], fontSize=9, leading=11, fontName='Times-BoldItalic', alignment=TA_CENTER, spaceBefore=2, spaceAfter=2))
styles.add(ParagraphStyle(name='AbstractBody', parent=styles['Normal'], fontSize=8.8, leading=10.8, fontName='Times-Italic', alignment=TA_JUSTIFY, leftIndent=10, rightIndent=10, spaceAfter=4))
styles.add(ParagraphStyle(name='Keywords', parent=styles['Normal'], fontSize=8.6, leading=10.4, fontName='Times-Italic', alignment=TA_JUSTIFY, leftIndent=10, rightIndent=10, spaceAfter=10))
styles.add(ParagraphStyle(name='Section', parent=styles['Normal'], fontSize=10, leading=12, fontName='Times-Bold', spaceBefore=7, spaceAfter=3, textColor=colors.HexColor('#111111'), keepWithNext=True))
styles.add(ParagraphStyle(name='SubSection', parent=styles['Normal'], fontSize=9.2, leading=11, fontName='Times-BoldItalic', spaceBefore=4, spaceAfter=2, keepWithNext=True))
styles.add(ParagraphStyle(name='Body', parent=styles['Normal'], fontSize=9, leading=11.2, fontName='Times-Roman', alignment=TA_JUSTIFY, spaceAfter=4, firstLineIndent=10))
styles.add(ParagraphStyle(name='BodyNoIndent', parent=styles['Normal'], fontSize=9, leading=11.2, fontName='Times-Roman', alignment=TA_JUSTIFY, spaceAfter=4))
styles.add(ParagraphStyle(name='Caption', parent=styles['Normal'], fontSize=8, leading=9.5, fontName='Times-Italic', alignment=TA_CENTER, spaceBefore=2, spaceAfter=6))
styles.add(ParagraphStyle(name='TableCaption', parent=styles['Normal'], fontSize=8, leading=9.5, fontName='Times-Bold', alignment=TA_CENTER, spaceBefore=2, spaceAfter=2))
styles.add(ParagraphStyle(name='Ref', parent=styles['Normal'], fontSize=8, leading=9.8, fontName='Times-Roman', alignment=TA_LEFT, leftIndent=12, firstLineIndent=-12, spaceAfter=2))
styles.add(ParagraphStyle(name='Cell', parent=styles['Normal'], fontSize=7.4, leading=9, fontName='Times-Roman'))
styles.add(ParagraphStyle(name='CellH', parent=styles['Normal'], fontSize=7.4, leading=9, fontName='Times-Bold', textColor=colors.white))
styles.add(ParagraphStyle(name='Small', parent=styles['Normal'], fontSize=7.8, leading=9.4, fontName='Times-Roman', alignment=TA_JUSTIFY, spaceAfter=3))


def H(txt, style='Section'):
    return Paragraph(txt, styles[style])

def P(txt, style='Body'):
    return Paragraph(txt, styles[style])

def fig(name, caption, width=COL_W, max_h=2.4*inch):
    path = os.path.join(FIG, name)
    img = ImageReader(path)
    iw, ih = img.getSize()
    scale = min(width/iw, max_h/ih)
    im = Image(path, width=iw*scale, height=ih*scale)
    im.hAlign = 'CENTER'
    return KeepTogether([im, P(caption, 'Caption')])

def tbl(caption, header, rows, colWidths):
    data = [[Paragraph(h, styles['CellH']) for h in header]]
    for r in rows:
        data.append([Paragraph(c, styles['Cell']) for c in r])
    t = Table(data, colWidths=colWidths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#2D3748')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#F7FAFC')]),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#A0AEC0')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('PADDING',(0,0),(-1,-1),2.5),
    ]))
    return KeepTogether([P(caption, 'TableCaption'), t, Spacer(1,4)])

class Doc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        self.allowSplitting = 0
        BaseDocTemplate.__init__(self, filename, **kw)
        f1 = Frame(MARGIN, MARGIN, COL_W, PAGE_H-2*MARGIN, id='col1')
        f2 = Frame(MARGIN+COL_W+GUTTER, MARGIN, COL_W, PAGE_H-2*MARGIN, id='col2')
        self.addPageTemplates([
            PageTemplate(id='first', frames=[f1,f2]),
            PageTemplate(id='later', frames=[f1,f2]),
        ])



def build():
    doc = Doc(OUT, pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN)
    story = []

    # Title/authors
    story.append(Paragraph('Intelligent and Secure Task Scheduling for Digital Twin-Enabled Edge&#8211;Cloud Networks', styles['PaperTitle']))
    story.append(Paragraph('<b>Dr. R. G. Suresh Kumar</b><super>1</super>, <b>DEVANAND P</b><super>2</super>, <b>HARISH T</b><super>2</super>, <b>KAILASANATHAN M</b><super>2</super>', styles['PaperAuthor']))
    story.append(Paragraph('<super>1</super>Professor and Head of the Department, Department of Computer Science and Engineering, Rajiv Gandhi College of Engineering and Technology, Puducherry &#8211; 607 403, India', styles['PaperAffil']))
    story.append(Paragraph('<super>2</super>Department of Computer Science and Engineering, Rajiv Gandhi College of Engineering and Technology, Puducherry &#8211; 607 403, India', styles['PaperAffil']))
    story.append(Paragraph('sureshkumar_rg@rgcet.edu.in | devanand.slp@gmail.com | harishthirunavukkarasu24@gmail.com | m.kailasam.06@gmail.com', styles['PaperEmail']))
    story.append(HRFlowable(width='100%', thickness=0.7, color=colors.HexColor('#444444'), spaceBefore=0, spaceAfter=6))

    story.append(P('<i><b>Abstract&#8212;</b>Digital Twin-enabled edge&#8211;cloud systems require scheduling decisions that simultaneously satisfy latency, energy, privacy, security, and resource constraints. This paper presents a rebuilt research baseline for SecureDT, an as-implemented Django-based platform for intelligent and secure task scheduling across Local, Mobile Edge Computing (MEC), and Cloud tiers. The system combines a policy engine enforcing LOCAL_ONLY, TRUSTED_EDGE, and CLOUD_ALLOWED constraints; a mixed-fidelity Digital Twin with measured local hardware telemetry, measured MEC heartbeat telemetry, and simulated cloud state; a multi-objective Genetic Algorithm (GA) and five baseline schedulers for task dispatch; a 10-stage dataset ingestion/analysis pipeline; tri-tier storage with SHA-256 integrity and privacy-boundary enforcement; and virtualized security/risk monitoring. A Phase 1 code audit of the repository identifies implemented strengths, partial components, and critical research gaps. Key findings include a real GA in the task scheduling path, a methodological inconsistency where dataset upload allocation uses deterministic heuristic scoring while reports label GA/policy engine behavior, and reliance on model-based/simulated cloud and security components. The paper distinguishes measured, simulated, and model-based evidence and defines a SecureDT 2.0 roadmap toward adaptive, trust-aware, and reproducible edge&#8211;cloud scheduling.</i>', 'AbstractBody'))
    story.append(P('<i><b>Keywords&#8212;</b>Digital Twin, edge&#8211;cloud computing, task scheduling, genetic algorithm, privacy policy, MEC, security monitoring, tri-tier storage, SecureDT</i>', 'Keywords'))

    # I. Intro
    story.append(H('I. Introduction'))
    story.append(P('Edge&#8211;cloud infrastructures support latency-sensitive and privacy-sensitive workloads by distributing computation across local workstations, edge nodes, and centralized cloud resources. Digital Twins (DTs) improve observability by maintaining virtual representations of physical resources, but scheduling decisions remain challenging when workloads have heterogeneous deadlines, privacy policies, security exposure, and resource demands. A practical scheduler must not only optimize latency and energy but also enforce hard privacy constraints and account for trust and security risk.'))
    story.append(P('SecureDT is an implemented research platform that explores this problem in a hospital-oriented edge&#8211;cloud testbed scenario. This paper remakes the SecureDT report from the current repository state rather than from prior narrative claims. It is grounded in a Phase 1 audit of the codebase and explicitly separates fully implemented, partially implemented, simulated, model-based, and unverified behaviors. The objective is to provide an honest, reproducible baseline for evolving the system into SecureDT 2.0: an AI-driven adaptive and trust-aware task scheduling framework for secure Digital Twin-enabled edge&#8211;cloud networks.'))
    story.append(P('<b>Contributions.</b> (1) A repository-grounded architecture and workflow description of SecureDT; (2) a code-audit-based component inventory with implementation status; (3) identification of methodological and fidelity gaps, including GA labeling inconsistency in the dataset upload path; (4) a research gap analysis and incremental roadmap for SecureDT 2.0.'))

    # II. Related/Context
    story.append(H('II. Background and System Context'))
    story.append(P('SecureDT combines concepts from edge&#8211;cloud offloading, Digital Twins, multi-objective optimization, and security-aware computing. Traditional schedulers such as Round Robin, First Fit, Random, Greedy, and privacy-aware heuristics provide useful baselines but do not jointly optimize multiple constraints with policy-aware feasibility. Genetic Algorithms (GAs) are suitable for multi-objective task-to-resource assignment because they can encode assignments as chromosomes and optimize weighted fitness under constraints.'))
    story.append(P('The current SecureDT implementation is a Django/Python platform with Django REST Framework, optional MySQL/SQLite persistence, psutil-based local telemetry, and modular engines for scheduling, policy enforcement, Digital Twin state, dataset analysis, storage, risk, attack simulation, and benchmarking. The repository also contains 14 hospital workload scenarios and 30 ZIP evaluation assets used as a realistic clinical demonstration scenario. Runtime validation of these assets is not claimed as executed in this Phase 1 paper.'))
    story.append(fig('architecture.png', 'Fig. 1. SecureDT as-implemented architecture showing policy, Digital Twin, scheduling, security, tri-tier execution/storage, and persistent observability.', width=COL_W, max_h=2.3*inch))

    # III. Architecture
    story.append(H('III. SecureDT Architecture and Implementation'))
    story.append(P('Fig. 1 summarizes the implemented architecture. The Django application layer exposes dashboard, upload, Digital Twin, storage allocation, reports, task history, and REST APIs. The engine layer contains the scheduling, policy, twin, dataset analysis, storage, risk, attack, and benchmark logic. Persistence stores tasks, datasets, MEC agents, heartbeats, decisions, experiment runs, reports, audit events, and storage replicas.'))
    story.append(tbl('Table I. Core Django Applications and Responsibilities', ['App', 'Responsibility', 'Key Evidence'], [
        ['datasets', 'Dataset upload, 10-stage analysis, reports, storage allocation, dashboard/history pages.', 'datasets/models.py, views_pages.py'],
        ['tasks', 'Task lifecycle, dispatch, queue/history, benchmark APIs.', 'tasks/models.py, services.py, views.py'],
        ['mec_manager', 'MEC pairing, token auth, heartbeat telemetry, online/offline, revoke/requeue.', 'mec_manager/models.py, services.py, views.py'],
        ['digital_twin', 'Twin state APIs, virtual attack/mitigation/quarantine, compare/export.', 'digital_twin/views.py, engine/digital_twin.py'],
        ['analytics', 'Aggregated MEC/task/energy/security/cloud metrics and data flow.', 'analytics/views.py'],
        ['cloud', 'Cloud/Drive metadata, upload/download/status/folders; simulated/fallback capable.', 'cloud/models.py, views.py'],
    ], [0.95*inch, 2.15*inch, 2.0*inch]))

    story.append(H('A. Mixed-Fidelity Digital Twin'))
    story.append(P('The Digital Twin maintains resource states for Local, MEC, and Cloud tiers. Local resources are measured from workstation hardware using psutil and labeled <i>MEASURED_HARDWARE</i>. MEC resources are derived from authenticated heartbeats and labeled <i>MEASURED_HEARTBEAT</i>; stale heartbeats trigger offline/unavailable treatment. Cloud is explicitly labeled <i>SIMULATED_CLOUD</i> with modeled latency/capacity behavior. This mixed-fidelity design is useful for experimentation, but it requires careful provenance labeling in reports and research claims.'))
    story.append(fig('telemetry_fidelity.png', 'Fig. 2. Digital Twin telemetry fidelity: measured local, measured heartbeat MEC, and simulated cloud.', width=COL_W, max_h=1.7*inch))

    story.append(H('B. Policy Engine and Scheduling'))
    story.append(P('The PolicyEngine enforces hard placement constraints: <i>LOCAL_ONLY</i> restricts execution to local resources; <i>TRUSTED_EDGE</i> permits local or authenticated, online, non-stale MEC resources; <i>CLOUD_ALLOWED</i> permits local, eligible MEC, or cloud. The engine also checks availability, staleness, memory capacity, and supported workload types before dispatch.'))
    story.append(P('The task scheduling path uses a real GA implementation in <font name="Courier" size="7.5">engine/genetic_algorithm.py</font>. Each chromosome encodes per-task resource assignments. The GA applies tournament selection, single-point crossover, per-gene mutation, elitism, and policy-aware candidate filtering. The fitness function combines latency, energy, privacy loss, security risk, and deadline penalty; unassignable tasks are represented as blocked assignments. The scheduler also implements Round Robin, First Fit, Random, Greedy, and Privacy-Aware baselines through a common evaluation model.'))
    story.append(fig('scheduler_comparison.png', 'Fig. 3. Illustrative scheduler comparison showing the design target of GA under multi-objective constraints. Values are illustrative only, not measured benchmark results.', width=COL_W, max_h=2.0*inch))

    # IV. Dataset pipeline and storage
    story.append(H('IV. Dataset Pipeline and Tri-Tier Storage'))
    story.append(P('SecureDT includes a 10-stage dataset ZIP ingestion and analysis pipeline. The implemented stages cover upload receipt, archive validation, inventory extraction, feature extraction, resource status collection, privacy/security assessment, scheduling/allocation, allocation recommendation, storage execution/simulation, and report generation. The pipeline includes ZIP safety checks for path traversal, executable content, and decompression/size limits, along with SHA-256 checksums and report persistence.'))
    story.append(fig('pipeline.png', 'Fig. 4. Ten-stage dataset ingestion, validation, allocation, and reporting pipeline.', width=COL_W*2+GUTTER, max_h=1.25*inch))
    story.append(NextPageTemplate('later'))
    story.append(FrameBreak())

    story.append(P('The storage manager provides three destinations outside the webroot: LOCAL_STORAGE (50 GB), MEC_STORAGE (200 GB), and CLOUD_STORAGE (1000 GB, emulator-flagged). It supports SHA-256 verification, privacy-boundary enforcement, idempotent replication, and audit logging for violations. This design supports confidentiality-aware data placement but requires clear labeling where cloud behavior is emulated rather than backed by a verified public cloud.'))
    story.append(fig('storage_tiers.png', 'Fig. 5. Tri-tier storage capacities and privacy scope.', width=COL_W, max_h=1.9*inch))

    story.append(tbl('Table II. Data Provenance and Execution Fidelity', ['Component', 'Fidelity/Status', 'Evidence'], [
        ['Local telemetry', 'Measured hardware (psutil).', 'engine/digital_twin.py'],
        ['MEC telemetry', 'Measured heartbeat with stale detection.', 'engine/digital_twin.py, mec_manager/services.py'],
        ['Cloud tier', 'Simulated/emulated cloud state and execution path.', 'engine/digital_twin.py, tasks/services.py'],
        ['Task GA scheduler', 'Implemented algorithmic GA in task path.', 'engine/genetic_algorithm.py, scheduler.py'],
        ['Dataset upload allocation', 'Deterministic heuristic scoring; GA/policy label inconsistency in reports.', 'engine/dataset_analysis_service.py'],
        ['Security/attacks', 'Model-based risk and virtual in-process attack simulation.', 'engine/risk_engine.py, attack_simulator.py'],
    ], [1.35*inch, 2.25*inch, 1.5*inch]))

    # V. Security, MEC, evaluation assets
    story.append(H('V. Security, MEC Lifecycle, and Evaluation Assets'))
    story.append(P('MEC management includes one-time pairing, device/token authentication, heartbeat processing, timeout-based online/offline state, revocation, and task reassignment hooks. These mechanisms provide a practical edge-agent lifecycle for the testbed. The security layer computes normalized risk from attack, severity, privacy, trust, workload, and exposure factors; simulates virtual attacks over Digital Twin state; and aggregates events through a security monitor. An AI risk module uses an offline RandomForest classifier with rule-based fallback and optional cached Groq explanation. These components are useful for controlled experiments but should be described as model-based or simulated unless validated against real adversarial telemetry.'))
    story.append(P('The repository includes 14 hospital workload scenarios across success, error, security, and timeout categories, plus 30 ZIP test-case assets. The scenarios cover realistic clinical operations such as image preprocessing, EHR scoring, lab panels, document metadata extraction, appointment scheduling, malformed input handling, policy violations, and timeout/retry behavior. This paper does not claim runtime pass/fail results for all assets because Phase 1 did not execute end-to-end validation.'))
    story.append(fig('scenario_assets.png', 'Fig. 6. Evaluation assets included in the repository: 14 hospital workload scenarios and 30 ZIP test cases.', width=COL_W, max_h=1.9*inch))

    # VI. Audit findings
    story.append(H('VI. Phase 1 Audit Findings'))
    story.append(P('The Phase 1 audit reviewed configuration, models, engines, APIs, UI routes, storage, tests, and documentation. The system is a substantial research prototype with real implementations in key scheduling and lifecycle components, but several claims require tighter provenance and validation.'))
    story.append(fig('audit_status.png', 'Fig. 7. Phase 1 audit status summary by component category.', width=COL_W, max_h=1.8*inch))
    story.append(tbl('Table III. Key Audit Findings', ['Finding', 'Impact', 'Status'], [
        ['Task path uses real GA and baselines with policy-aware evaluation.', 'Supports multi-objective scheduling research baseline.', 'Implemented'],
        ['Dataset upload allocation uses deterministic heuristic scoring but reports GA/policy engine.', 'Methodological traceability gap; can overstate GA use.', 'Critical gap'],
        ['Digital Twin mixes measured local/MEC and simulated cloud.', 'Valid for prototype; requires explicit provenance in claims.', 'Partial/mixed'],
        ['Cloud execution/storage includes simulation/emulation.', 'Not evidence of real public-cloud performance.', 'Simulated'],
        ['Security/risk/attack modules are model-based or virtual.', 'Useful for controlled testing, not real adversarial hardening.', 'Model-based'],
        ['Tests and 30-case runtime outcomes not executed in Phase 1.', 'No runtime pass/fail or benchmark claim made.', 'Unverified'],
    ], [2.25*inch, 1.95*inch, 0.9*inch]))

    # VII. Gaps and roadmap
    story.append(H('VII. Research Gaps and SecureDT 2.0 Roadmap'))
    story.append(P('The main gap between the current system and the SecureDT 2.0 objective is the absence of continuously adaptive, trust-aware intelligence grounded in observed behavior. Scheduling weights are largely static, trust is coarse/model-driven, and security evidence is primarily virtual. The dataset allocation path must be made methodologically consistent with the task scheduler or clearly labeled as a separate heuristic. Digital Twin fidelity must improve through calibration, uncertainty/provenance metadata, and stronger MEC/cloud synchronization.'))
    story.append(P('The roadmap preserves reusable foundations: PolicyEngine, GA/baselines, MEC lifecycle, Digital Twin abstraction, storage integrity mechanisms, and report/benchmark persistence. Future phases should add decision provenance, trust scoring from longitudinal evidence, anomaly/fault detection, stronger measured evaluation, and calibrated twin synchronization before major architectural redesign.'))
    story.append(fig('roadmap.png', 'Fig. 8. Incremental SecureDT 2.0 roadmap from audit baseline to adaptive, trust-aware evaluation.', width=COL_W*2+GUTTER, max_h=1.1*inch))

    # VIII. Conclusion
    story.append(H('VIII. Conclusion'))
    story.append(P('This paper reconstructed the SecureDT report from the current repository implementation and Phase 1 audit. SecureDT already provides a meaningful baseline: a Django-based edge&#8211;cloud testbed with policy-constrained multi-objective GA scheduling, mixed-fidelity Digital Twin telemetry, MEC lifecycle management, tri-tier storage with integrity controls, dataset analysis/reporting, and simulated security tooling. At the same time, the audit identifies critical gaps that must be addressed before stronger research claims: methodological consistency between scheduling paths, explicit measured/simulated/model-based labeling, runtime validation of evaluation assets, and evolution toward adaptive trust-aware decision-making. The resulting baseline is suitable for incremental SecureDT 2.0 development without premature architectural rewrite.'))

    story.append(H('Acknowledgment'))
    story.append(P('The authors acknowledge the Department of Computer Science and Engineering, Rajiv Gandhi College of Engineering and Technology, Puducherry, for academic guidance and project support.', 'BodyNoIndent'))

    story.append(H('References'))
    refs = [
        '[1] W. Shi, J. Cao, Q. Zhang, Y. Li, and L. Xu, "Edge Computing: Vision and Challenges," <i>IEEE Internet of Things Journal</i>, vol. 3, no. 5, pp. 637&#8211;646, 2016.',
        '[2] M. Grieves and J. Vickers, "Digital Twin: Mitigating Unpredictable, Undesirable Emergent Behavior in Complex Systems," in <i>Transdisciplinary Perspectives on Complex Systems</i>, Springer, 2017.',
        '[3] D. E. Goldberg, <i>Genetic Algorithms in Search, Optimization, and Machine Learning</i>. Addison-Wesley, 1989.',
        '[4] K. Deb, A. Pratap, S. Agarwal, and T. Meyarivan, "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II," <i>IEEE Transactions on Evolutionary Computation</i>, vol. 6, no. 2, pp. 182&#8211;197, 2002.',
        '[5] Y. Mao, C. You, J. Zhang, K. Huang, and K. B. Letaief, "A Survey on Mobile Edge Computing: The Communication Perspective," <i>IEEE Communications Surveys &amp; Tutorials</i>, vol. 19, no. 4, pp. 2322&#8211;2358, 2017.',
        '[6] T. Taleb, K. Samdanis, B. Mada, H. Flinck, S. Dutta, and D. Sabella, "On Multi-Access Edge Computing: A Survey of the Emerging 5G Network Edge Cloud Architecture and Orchestration," <i>IEEE Communications Surveys &amp; Tutorials</i>, vol. 19, no. 3, pp. 1657&#8211;1681, 2017.',
        '[7] A. M. Rahmani et al., "Exploiting Smart e-Health Gateways at the Edge of Healthcare Internet-of-Things: A Fog Computing Approach," <i>Future Generation Computer Systems</i>, vol. 78, pp. 641&#8211;658, 2018.',
        '[8] R. Buyya et al., "A Manifesto for Future Generation Cloud Computing: Research Directions for the Next Decade," <i>ACM Computing Surveys</i>, vol. 51, no. 5, 2018.',
        '[9] NIST, "Zero Trust Architecture," NIST Special Publication 800-207, 2020.',
        '[10] SecureDT Project Repository, "Phase 1 Audit and Existing Implementation Baseline," internal audit docs: <font name="Courier" size="7">docs/SECUREDT_EXISTING_ARCHITECTURE.md</font>, <font name="Courier" size="7">docs/SECUREDT_CODE_AUDIT.md</font>, <font name="Courier" size="7">docs/RESEARCH_GAP_ANALYSIS.md</font>, 2026.'
    ]
    for r in refs:
        story.append(P(r, 'Ref'))

    doc.build(story)
    print('WROTE', OUT)

if __name__ == '__main__':
    build()
