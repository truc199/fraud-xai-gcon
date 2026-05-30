import os
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from mplfonts import use_font

# Font setup
use_font('Noto Serif')

# Navy color palette
COLORS = {
    'dark_midnight': '#003366',
    'usafa': '#004C99',
    'bright_navy': '#0066CC',
    'azure': '#007FFF',
    'dodger': '#3399FF',
    'french_sky': '#66B2FF',
    'baby_blue': '#99CCFF',
    'highlight_orange': '#FF6B35',
    'highlight_red': '#E63946',
}

# Load global preprocessor cache
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
cache_path = os.path.join(project_root, "data", "global_preprocessor_cache.pkl")
print(f"Loading cache from: {cache_path}")

with open(cache_path, "rb") as f:
    cache_data = pickle.load(f)

print(f"Cache type: {type(cache_data)}")

# The cache is a dict keyed by hash -> DataFrame
# Find the largest DataFrame (the full 546k ambiguous set)
if isinstance(cache_data, dict):
    print(f"Cache keys: {list(cache_data.keys())[:5]}")
    # Find the entry with most rows
    best_key = None
    best_len = 0
    for k, v in cache_data.items():
        if hasattr(v, '__len__'):
            if len(v) > best_len:
                best_len = len(v)
                best_key = k
    print(f"Best key: {best_key}, rows: {best_len}")
    df = cache_data[best_key]
else:
    df = cache_data

print(f"DataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

if 'TRANS_HOUR_PROB' not in df.columns:
    print("ERROR: TRANS_HOUR_PROB not found in cache!")
    exit(1)

values = df['TRANS_HOUR_PROB'].dropna().values
print(f"\nTRANS_HOUR_PROB stats:")
print(f"  Count: {len(values):,}")
print(f"  Min: {values.min():.6f}")
print(f"  Max: {values.max():.6f}")
print(f"  Mean: {values.mean():.6f}")
print(f"  Median: {np.median(values):.6f}")
print(f"  Std: {values.std():.6f}")

# Percentiles
for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    print(f"  P{p}: {np.percentile(values, p):.6f}")

# Plot distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: Histogram
ax1 = axes[0]
n, bins, patches = ax1.hist(values, bins=50, color=COLORS['bright_navy'], 
                             edgecolor=COLORS['dark_midnight'], alpha=0.85, linewidth=0.5)

# Color gradient for bars
for i, patch in enumerate(patches):
    ratio = i / len(patches)
    if ratio < 0.2:
        patch.set_facecolor(COLORS['dark_midnight'])
    elif ratio < 0.4:
        patch.set_facecolor(COLORS['usafa'])
    elif ratio < 0.6:
        patch.set_facecolor(COLORS['bright_navy'])
    elif ratio < 0.8:
        patch.set_facecolor(COLORS['azure'])
    else:
        patch.set_facecolor(COLORS['dodger'])

ax1.axvline(np.mean(values), color=COLORS['highlight_orange'], linestyle='--', linewidth=1.5, label=f'Mean ({np.mean(values):.4f})')
ax1.axvline(np.median(values), color=COLORS['highlight_red'], linestyle='-.', linewidth=1.5, label=f'Median ({np.median(values):.4f})')

ax1.set_xlabel('TRANS_HOUR_PROB')
ax1.set_ylabel('Frequency')
ax1.set_title('Distribution of TRANS_HOUR_PROB')
ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Remove numbers from y-axis
ax1.set_yticklabels([])

# Right: Box + Violin
ax2 = axes[1]
vp = ax2.violinplot(values, positions=[0], showmeans=True, showmedians=True, showextrema=False)
vp['bodies'][0].set_facecolor(COLORS['french_sky'])
vp['bodies'][0].set_alpha(0.6)
vp['bodies'][0].set_edgecolor(COLORS['dark_midnight'])
vp['cmeans'].set_color(COLORS['highlight_orange'])
vp['cmeans'].set_linewidth(2)
vp['cmedians'].set_color(COLORS['highlight_red'])
vp['cmedians'].set_linewidth(2)

bp = ax2.boxplot(values, positions=[0], widths=0.15, patch_artist=True,
                  boxprops=dict(facecolor=COLORS['baby_blue'], edgecolor=COLORS['dark_midnight'], alpha=0.8),
                  whiskerprops=dict(color=COLORS['dark_midnight']),
                  capprops=dict(color=COLORS['dark_midnight']),
                  medianprops=dict(color=COLORS['highlight_red'], linewidth=2),
                  flierprops=dict(marker='o', markerfacecolor=COLORS['highlight_orange'], markersize=3, alpha=0.3))

ax2.set_title('Box + Violin Plot')
ax2.set_ylabel('TRANS_HOUR_PROB')
ax2.set_xticks([])
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

plt.tight_layout()

output_path = os.path.join(os.path.dirname(__file__), "outputs", "trans_hour_prob_distribution.png")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
plt.savefig(output_path, dpi=200, bbox_inches='tight')
print(f"\nChart saved to: {output_path}")
