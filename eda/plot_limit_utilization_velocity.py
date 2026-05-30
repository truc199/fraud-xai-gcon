import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
    'highlight_teal': '#008080',
    'highlight_red': '#E63946',
}

# Connect to database
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_path = os.path.join(project_root, "data", "gcontest.db")
print(f"Connecting to database: {db_path}")
conn = sqlite3.connect(db_path)

# Compute values
from src.pipeline.fraud_2026_data_loader import compute_limit_utilization_velocity
velocity_map = compute_limit_utilization_velocity(conn)
conn.close()

if not velocity_map:
    print("No credit utilization velocity data found!")
    exit(1)

values = list(velocity_map.values())
series = pd.Series(values)

print(f"Total customers with credit velocity: {len(series):,}")
print("\nLIMIT_UTILIZATION_VELOCITY statistics:")
print(series.describe())

print("\nPercentiles:")
for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    print(f"  P{p}: {np.percentile(values, p):.4f}")

# Plot distribution
fig, ax = plt.subplots(figsize=(8, 5))

# Hist
n, bins, patches = ax.hist(values, bins=40, color=COLORS['bright_navy'], 
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

# Draw mean & median lines
mean_val = np.mean(values)
median_val = np.median(values)
mean_line = ax.axvline(mean_val, color=COLORS['highlight_orange'], linestyle='--', linewidth=1.5)
median_line = ax.axvline(median_val, color=COLORS['highlight_red'], linestyle='-.', linewidth=1.5)

# Style chart
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color(COLORS['dark_midnight'])
ax.spines['bottom'].set_color(COLORS['dark_midnight'])

# Hide y-axis values to obey "Không để số trên chart" (No data numbers on y-axis)
ax.set_yticklabels([])
ax.set_yticks([])

# Labels
ax.set_xlabel('LIMIT_UTILIZATION_VELOCITY (Month-over-Month Spike)', fontsize=12, color=COLORS['dark_midnight'], labelpad=10)
ax.set_ylabel('Density', fontsize=12, color=COLORS['dark_midnight'])
ax.set_title('Distribution of LIMIT_UTILIZATION_VELOCITY', fontsize=14, weight='bold', pad=15, color=COLORS['dark_midnight'])

# Legend with 2pt spacing from Ox title
ax.legend([mean_line, median_line], 
          [f'Mean ({mean_val:.3f})', f'Median ({median_val:.3f})'], 
          loc='upper center', bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=2)

plt.tight_layout()

# Save plot
output_path = os.path.join(project_root, "eda", "outputs", "limit_utilization_velocity_distribution.png")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
plt.savefig(output_path, dpi=200, bbox_inches='tight')
print(f"Chart successfully saved to: {output_path}")
