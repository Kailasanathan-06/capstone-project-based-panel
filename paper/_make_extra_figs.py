import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

out = os.path.join('paper', 'figures')
os.makedirs(out, exist_ok=True)
plt.rcParams.update({'font.size': 10, 'font.family': 'DejaVu Sans'})

# 7) Telemetry fidelity by tier (factual)
fig, ax = plt.subplots(figsize=(7, 3.2))
tiers = ['LOCAL\nWorkstation', 'MEC\nEdge Nodes', 'CLOUD\nTier']
types = ['Measured hardware\n(psutil, live)', 'Measured heartbeat\n(freshness/staleness-aware)', 'Simulated\n(modeled, emulator)']
colors = ['#38a169', '#3182ce', '#a0aec0']
bars = ax.barh(tiers, [1, 1, 1], color=colors, edgecolor='#2d3748')
for bar, label in zip(bars, types):
    ax.text(0.5, bar.get_y() + bar.get_height()/2, label, ha='center', va='center', fontsize=9, color='white' if label.startswith('Measured') or 'heartbeat' in label else '#1a202c', fontweight='bold')
ax.set_xlim(0, 1)
ax.set_xticks([])
ax.set_xlabel('Telemetry/source basis (as implemented)')
ax.set_title('Digital Twin Telemetry Fidelity by Tier')
for spine in ['top','right','bottom']:
    ax.spines[spine].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(out,'telemetry_fidelity.png'), dpi=220, bbox_inches='tight'); plt.close(fig)

# 8) Hospital workload scenarios by category (factual)
cats = ['Success', 'Controlled\nerror', 'Defensive\nsecurity', 'Timeout /\nretry']
counts = [5, 3, 3, 3]
colors = ['#48bb78', '#ed8936', '#f56565', '#ecc94b']
fig, ax = plt.subplots(figsize=(6.5, 3.8))
bars = ax.bar(cats, counts, color=colors, edgecolor='#2d3748')
ax.set_ylabel('Number of scenarios')
ax.set_ylim(0, 6)
ax.set_title('Hospital Workload Scenarios by Category (14 total)')
for b, c in zip(bars, counts):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.1, str(c), ha='center', fontsize=10, fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(out,'hospital_workload_categories.png'), dpi=220); plt.close(fig)

# 9) GA convergence illustration (illustrative)
rng = np.random.default_rng(42)
gens = np.arange(1, 31)
best = 18.0 * np.exp(-0.09*gens) + 4.2 + rng.normal(0, 0.15, size=gens.size).cumsum()*0.02
best = np.minimum.accumulate(best)
avg = best + 3.5*np.exp(-0.05*gens) + 1.2 + rng.normal(0, 0.08, size=gens.size)
fig, ax = plt.subplots(figsize=(6.8, 3.8))
ax.plot(gens, avg, color='#a0aec0', linewidth=1.8, label='Average fitness (illustrative)')
ax.plot(gens, best, color='#2b6cb0', linewidth=2.2, label='Best fitness (illustrative)')
ax.set_xlabel('Generation')
ax.set_ylabel('Fitness value (lower is better)')
ax.set_title('Illustrative GA Convergence Behavior')
ax.grid(True, linestyle='--', alpha=0.35)
ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(out,'ga_convergence.png'), dpi=220); plt.close(fig)

print('extra figs ok')
