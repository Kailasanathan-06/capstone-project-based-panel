import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np, os

out = os.path.join('paper','figures'); os.makedirs(out, exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9})

# 1 Architecture
fig, ax = plt.subplots(figsize=(10.5,6.2)); ax.set_xlim(0,10); ax.set_ylim(0,6.2); ax.axis('off')
def box(x,y,w,h,t,fc,ec,fs=8.5):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.08',lw=1.4,edgecolor=ec,facecolor=fc))
    ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=fs,wrap=True)
def arr(x1,y1,x2,y2): ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='->',lw=1.2,color='#4a5568'))
box(3.2,5.25,3.6,0.75,'User / Workload Interface\nDashboard, Upload, Reports, Task History','#FEFCBF','#B7791F')
box(0.3,3.75,2.8,1.15,'Policy & Validation\nPolicyEngine (LOCAL_ONLY,\nTRUSTED_EDGE, CLOUD_ALLOWED)\nZIP/schema/safety checks','#E6FFFA','#2C7A7B')
box(3.6,3.75,2.8,1.15,'Digital Twin & Scheduler\nMixed-fidelity resource state\nGA + 5 baselines\nTask dispatch & benchmarking','#EBF8FF','#2B6CB0')
box(6.9,3.75,2.8,1.15,'Security & Audit\nRisk model, virtual attacks,\nsecurity monitor, audit logs,\nSHA-256 integrity','#FED7D7','#C53030')
box(0.3,1.7,2.8,1.35,'LOCAL Tier\nWorkstation / on-prem\n50 GB, MEASURED_HARDWARE\npsutil telemetry, confidential data','#F0FFF4','#276749')
box(3.6,1.7,2.8,1.35,'MEC Tier\nEdge agent / micro-datacenter\n200 GB, MEASURED_HEARTBEAT\nPairing, auth, heartbeat, stale detect','#FFFAF0','#C05621')
box(6.9,1.7,2.8,1.35,'CLOUD Tier\nCentralized emulator\n1000 GB, SIMULATED_CLOUD\nModeled latency/capacity','#FAF5FF','#6B46C1')
box(2.3,0.15,5.4,1.0,'Persistent Outputs & Observability\nDatasetUpload/Report/Inventory, Task & Decision history, ExperimentRun, CSV export,\nSecurityAuditEvent, storage replicas, dashboard analytics','#EDF2F7','#4A5568')
for x in [1.7,5,8.3]: arr(5,5.25,x,4.9)
for x in [1.7,5,8.3]: arr(x,3.75,x,3.05)
for x in [1.7,5,8.3]: arr(x,1.7,5,1.15)
ax.set_title('SecureDT System Architecture (As-Implemented Baseline)',fontsize=12,fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(out,'architecture.png'),dpi=220,bbox_inches='tight'); plt.close(fig)

# 2 Telemetry fidelity
fig,ax=plt.subplots(figsize=(7.2,3.3))
tiers=['LOCAL Workstation','MEC Edge Nodes','CLOUD Tier']
labels=['MEASURED_HARDWARE\nLive psutil CPU/memory/capacity','MEASURED_HEARTBEAT\nAuthenticated telemetry + freshness/stale detection','SIMULATED_CLOUD\nModeled latency/capacity/emulated storage']
colors=['#38A169','#3182CE','#A0AEC0']
for i,(t,l,c) in enumerate(zip(tiers,labels,colors)):
    ax.add_patch(FancyBboxPatch((0.05,2-i*0.9),0.35,0.6,boxstyle='round,pad=0.02,rounding_size=0.05',facecolor='#EDF2F7',edgecolor='#4A5568'))
    ax.text(0.225,2-i*0.9+0.3,t,ha='center',va='center',fontsize=9,fontweight='bold')
    ax.add_patch(FancyBboxPatch((0.45,2-i*0.9),0.5,0.6,boxstyle='round,pad=0.02,rounding_size=0.05',facecolor=c,edgecolor='#2D3748'))
    ax.text(0.7,2-i*0.9+0.3,l,ha='center',va='center',fontsize=8.5,color='white' if i<2 else '#1A202C')
ax.set_xlim(0,1); ax.set_ylim(-0.2,2.8); ax.axis('off')
ax.set_title('Digital Twin Telemetry Fidelity and Provenance',fontsize=11,fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(out,'telemetry_fidelity.png'),dpi=220,bbox_inches='tight'); plt.close(fig)

# 3 Pipeline
stages=['1 Upload\nReceipt','2 Archive\nValidation','3 Dataset\nInventory','4 Feature\nExtraction','5 Resource\nStatus','6 Privacy/\nSecurity','7 Scheduling/\nAllocation','8 Allocation\nRecommend.','9 Storage\nExec/Sim','10 Report\nGeneration']
fig,ax=plt.subplots(figsize=(11.2,2.6)); ax.set_xlim(-0.2,10.2); ax.set_ylim(0,1.6); ax.axis('off')
for i,s in enumerate(stages):
    c=plt.cm.Blues(0.25+0.055*i)
    ax.add_patch(FancyBboxPatch((i,0.45),0.86,0.75,boxstyle='round,pad=0.02,rounding_size=0.08',facecolor=c,edgecolor='#2B6CB0'))
    ax.text(i+0.43,0.825,s,ha='center',va='center',fontsize=7.5)
    if i<9: ax.annotate('',xy=(i+0.98,0.825),xytext=(i+0.87,0.825),arrowprops=dict(arrowstyle='->',lw=1.1,color='#2D3748'))
ax.set_title('10-Stage Dataset Ingestion, Validation, Allocation, and Reporting Pipeline',fontsize=11,fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(out,'pipeline.png'),dpi=220,bbox_inches='tight'); plt.close(fig)

# 4 Storage tiers
fig,ax=plt.subplots(figsize=(7,3.8))
tiers=['LOCAL_STORAGE','MEC_STORAGE','CLOUD_STORAGE']; caps=[50,200,1000]
colors=['#38A169','#DD6B20','#805AD5']; pol=['LOCAL_ONLY','TRUSTED_EDGE','CLOUD_ALLOWED']
bars=ax.bar(tiers,caps,color=colors,edgecolor='#2D3748')
for b,c,p in zip(bars,caps,pol): ax.text(b.get_x()+b.get_width()/2,b.get_height()+20,f'{c} GB\n{p}',ha='center',fontsize=8)
ax.set_ylabel('Capacity (GB)'); ax.set_ylim(0,1250); ax.set_title('Tri-Tier Storage Capacity and Privacy Scope')
fig.tight_layout(); fig.savefig(os.path.join(out,'storage_tiers.png'),dpi=220); plt.close(fig)

# 5 Scenario distribution
fig,ax=plt.subplots(figsize=(8.5,3.6))
labels=['Hospital\nSuccess','Hospital\nError','Hospital\nSecurity','Hospital\nTimeout','ZIP\nSuccess','ZIP\nFailure','ZIP\nLoop/Timeout']
vals=[5,3,3,3,10,10,10]
colors=['#48BB78','#F6AD55','#FC8181','#ECC94B','#68D391','#F56565','#D69E2E']
bars=ax.bar(labels,vals,color=colors,edgecolor='#2D3748')
for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.1,str(v),ha='center',fontsize=8,fontweight='bold')
ax.set_ylabel('Count'); ax.set_ylim(0,12); ax.set_title('Evaluation Assets: 14 Hospital Workload Scenarios + 30 ZIP Test Cases')
fig.tight_layout(); fig.savefig(os.path.join(out,'scenario_assets.png'),dpi=220); plt.close(fig)

# 6 Scheduler comparison illustrative
methods=['GA\n(Proposed)','Round\nRobin','First\nFit','Random','Greedy','Privacy-\nAware']
makespan=[42,61,58,67,49,55]; violations=[0,6,5,8,4,1]
x=np.arange(len(methods)); w=0.36
fig,ax1=plt.subplots(figsize=(8.2,4))
ax1.bar(x-w/2,makespan,w,label='Normalized makespan (illustrative)',color='#4299E1',edgecolor='#2B6CB0')
ax2=ax1.twinx(); ax2.bar(x+w/2,violations,w,label='Policy violations (illustrative)',color='#F56565',edgecolor='#C53030')
ax1.set_ylabel('Normalized makespan',color='#2B6CB0'); ax2.set_ylabel('Policy violations',color='#C53030')
ax1.set_xticks(x); ax1.set_xticklabels(methods); ax1.set_title('Illustrative Scheduler Comparison (Design Target; not benchmark claim)')
l1,lab1=ax1.get_legend_handles_labels(); l2,lab2=ax2.get_legend_handles_labels(); ax1.legend(l1+l2,lab1+lab2,fontsize=7,loc='upper right')
fig.tight_layout(); fig.savefig(os.path.join(out,'scheduler_comparison.png'),dpi=220); plt.close(fig)

# 7 Component status
cats=['Fully\nImplemented','Partially\nImplemented','Simulated/\nModel-based','Requires\nImprovement']
vals=[11,9,6,4] # based on audit summary categories
colors=['#38A169','#4299E1','#A0AEC0','#ED8936']
fig,ax=plt.subplots(figsize=(6.8,3.8))
bars=ax.bar(cats,vals,color=colors,edgecolor='#2D3748')
for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.1,str(v),ha='center',fontweight='bold')
ax.set_ylabel('Component count (Phase 1 audit)'); ax.set_ylim(0,13)
ax.set_title('Phase 1 Implementation Status Summary')
fig.tight_layout(); fig.savefig(os.path.join(out,'audit_status.png'),dpi=220); plt.close(fig)

# 8 Roadmap
fig,ax=plt.subplots(figsize=(10.5,2.8)); ax.axis('off'); ax.set_xlim(0,10); ax.set_ylim(0,2.8)
phases=[('P1 Audit\n(Completed)','#9AE6B4'),('P2 Consistency\n& Provenance','#90CDF4'),('P3 Trust-Aware\nAdaptive Scheduling','#FBD38D'),('P4 Security &\nAnomaly Resilience','#FEB2B2'),('P5 Twin/MEC/Cloud\nFidelity','#D6BCFA'),('P6 Evaluation &\nReproducibility','#BEE3F8')]
for i,(p,c) in enumerate(phases):
    x=i*1.62+0.1
    ax.add_patch(FancyBboxPatch((x,0.9),1.45,1.0,boxstyle='round,pad=0.02,rounding_size=0.08',facecolor=c,edgecolor='#2D3748'))
    ax.text(x+0.725,1.4,p,ha='center',va='center',fontsize=8.2,fontweight='bold')
    if i<5: ax.annotate('',xy=(x+1.62,1.4),xytext=(x+1.45,1.4),arrowprops=dict(arrowstyle='->',lw=1.3,color='#2D3748'))
ax.set_title('SecureDT 2.0 Incremental Implementation Roadmap',fontsize=11,fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(out,'roadmap.png'),dpi=220,bbox_inches='tight'); plt.close(fig)

print('figs',sorted(os.listdir(out)))
