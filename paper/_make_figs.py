import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

out = os.path.join('paper', 'figures')
os.makedirs(out, exist_ok=True)

plt.rcParams.update({'font.size': 10, 'font.family': 'DejaVu Sans'})

# 1) System architecture
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')
def box(x,y,w,h,text,fc='#e8f4fd',ec='#2b6cb0'):
    b = FancyBboxPatch((x,y),w,h, boxstyle="round,pad=0.02,rounding_size=0.08", linewidth=1.5, edgecolor=ec, facecolor=fc)
    ax.add_patch(b)
    ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=9, wrap=True)

box(3.5,5.1,3,0.7,'User / Workload Submission\n(Datasets, Hospital Tasks)', '#fefcbf', '#b7791f')
box(0.5,3.6,2.6,1.0,'Policy & Validation Engine\nPrivacy tiers, ZIP checks,\nmanifest/task validation', '#e6fffa', '#2c7a7b')
box(3.7,3.6,2.6,1.0,'Digital Twin & Scheduler\nResource telemetry, GA/\nheuristic placement', '#ebf8ff', '#2b6cb0')
box(6.9,3.6,2.6,1.0,'Security & Audit Layer\nAuth, attack/violation logs,\nSHA-256 verification', '#fed7d7', '#c53030')

box(0.4,1.6,2.6,1.2,'LOCAL Tier\nWorkstation / On-prem\n50 GB, LOCAL_ONLY\nMeasured hardware', '#f0fff4', '#276749')
box(3.7,1.6,2.6,1.2,'MEC Tier\nEdge micro-datacenter\n200 GB, TRUSTED_EDGE\nHeartbeat telemetry', '#fffaf0', '#c05621')
box(7.0,1.6,2.6,1.2,'CLOUD Tier\nCentral storage emulator\n1000 GB, CLOUD_ALLOWED\nSimulated WAN', '#faf5ff', '#6b46c1')

box(2.8,0.2,4.4,0.9,'Persistent Outputs\nDatasetAnalysisReport, replicas, CSV export,\ntask history & dashboard metrics', '#edf2f7', '#4a5568')

def arrow(x1,y1,x2,y2):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1), arrowprops=dict(arrowstyle='->', lw=1.5, color='#4a5568'))
arrow(5,5.1,1.8,4.6); arrow(5,5.1,5,4.6); arrow(5,5.1,8.2,4.6)
arrow(1.8,3.6,1.7,2.8); arrow(5,3.6,5,2.8); arrow(8.2,3.6,8.3,2.8)
arrow(1.7,1.6,4.0,1.1); arrow(5,1.6,5,1.1); arrow(8.3,1.6,6.0,1.1)
ax.set_title('SecureDT High-Level Architecture', fontsize=12, fontweight='bold', pad=10)
fig.tight_layout(); fig.savefig(os.path.join(out,'architecture.png'), dpi=220, bbox_inches='tight'); plt.close(fig)

# 2) Storage tiers capacity and policy
tiers = ['LOCAL_STORAGE', 'MEC_STORAGE', 'CLOUD_STORAGE']
caps = [50, 200, 1000]
colors = ['#38a169','#dd6b20','#805ad5']
fig, ax = plt.subplots(figsize=(7,4))
bars = ax.bar(tiers, caps, color=colors)
ax.set_ylabel('Capacity (GB)')
ax.set_title('Three-Tier Storage Capacity and Placement Scope')
for b, cap, pol in zip(bars, caps, ['LOCAL_ONLY','TRUSTED_EDGE','CLOUD_ALLOWED']):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+15, f'{cap} GB\n{pol}', ha='center', va='bottom', fontsize=8)
ax.set_ylim(0, 1250)
fig.tight_layout(); fig.savefig(os.path.join(out,'storage_tiers.png'), dpi=220); plt.close(fig)

# 3) Upload/analysis workflow stages
stages = ['Upload\nReceived','ZIP\nValidation','Inventory','Feature\nExtraction','Resource\nStatus','Privacy/\nSecurity','Scheduler','Allocation\nDecision','Storage\nExec/Sim','Report\nGeneration']
x = np.arange(len(stages))
fig, ax = plt.subplots(figsize=(11,3.2))
for i,s in enumerate(stages):
    rect = FancyBboxPatch((i,0.4),0.85,0.8, boxstyle='round,pad=0.02,rounding_size=0.1', facecolor=plt.cm.Blues(0.25+0.06*i), edgecolor='#2b6cb0')
    ax.add_patch(rect)
    ax.text(i+0.425,0.8,s,ha='center',va='center',fontsize=8)
    if i < len(stages)-1:
        ax.annotate('', xy=(i+0.98,0.8), xytext=(i+0.86,0.8), arrowprops=dict(arrowstyle='->', lw=1.2, color='#2d3748'))
ax.set_xlim(-0.2,len(stages))
ax.set_ylim(0,1.6)
ax.axis('off')
ax.set_title('Dataset Upload and Analysis Pipeline (10 Stages)', fontsize=11, fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(out,'workflow_pipeline.png'), dpi=220, bbox_inches='tight'); plt.close(fig)

# 4) GA fitness components (conceptual weights)
labels = ['Latency', 'Energy', 'Privacy loss', 'Security risk', 'Deadline/constraint\npenalty']
weights = [0.35, 0.25, 0.20, 0.20, 1.0]
colors = ['#4299e1','#48bb78','#ed8936','#f56565','#a0aec0']
fig, ax = plt.subplots(figsize=(7,4))
bars = ax.bar(labels, weights, color=colors)
ax.set_ylabel('Relative weight / penalty factor')
ax.set_title('Genetic Algorithm Multi-Objective Fitness Components')
for b,w in zip(bars,weights):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.02, f'{w}', ha='center', fontsize=9)
ax.set_ylim(0,1.15)
fig.tight_layout(); fig.savefig(os.path.join(out,'ga_fitness.png'), dpi=220); plt.close(fig)

# 5) 30 scenario distribution
cats = ['Success', 'Failure', 'Loop/Timeout']
counts = [10,10,10]
fig, ax = plt.subplots(figsize=(5.5,4))
wedges, texts, autotexts = ax.pie(counts, labels=cats, autopct='%1.0f%%', startangle=90, colors=['#48bb78','#f56565','#ecc94b'])
ax.set_title('30 ZIP Scenario Test Suite Distribution')
fig.tight_layout(); fig.savefig(os.path.join(out,'scenario_distribution.png'), dpi=220); plt.close(fig)

# 6) Scheduler comparison illustrative (conceptual from design goals)
methods = ['GA\n(Proposed)','Round\nRobin','First\nFit','Random','Greedy','Privacy-\nAware']
makespan = [42, 61, 58, 67, 49, 55]  # illustrative normalized units
violations = [0, 6, 5, 8, 4, 1]
x = np.arange(len(methods))
w = 0.38
fig, ax1 = plt.subplots(figsize=(8,4))
b1 = ax1.bar(x-w/2, makespan, w, label='Makespan (normalized)', color='#4299e1')
ax1.set_ylabel('Makespan (normalized)', color='#2b6cb0')
ax1.tick_params(axis='y', labelcolor='#2b6cb0')
ax2 = ax1.twinx()
b2 = ax2.bar(x+w/2, violations, w, label='Policy violations', color='#f56565')
ax2.set_ylabel('Policy violations (count)', color='#c53030')
ax2.tick_params(axis='y', labelcolor='#c53030')
ax1.set_xticks(x); ax1.set_xticklabels(methods)
ax1.set_title('Illustrative Scheduler Comparison (Design Targets)')
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines+lines2, labels+labels2, loc='upper right', fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(out,'scheduler_comparison.png'), dpi=220); plt.close(fig)

print('ok')
