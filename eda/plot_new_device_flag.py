import os
import sqlite3
import pandas as pd
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
    'highlight_red': '#E63946',
}

# Connect to database
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_path = os.path.join(project_root, "data", "gcontest.db")
print(f"Connecting to database: {db_path}")
conn = sqlite3.connect(db_path)

print("Loading data...")
df = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, TRANS_DATE, Device_ID_Hash
    FROM Data_Transaction
    ORDER BY CUSTOMER_NUMBER, TRANS_DATE
""", conn)
conn.close()

print("Calculating NEW_DEVICE_FLAG...")
df['device_seen_before'] = df.groupby(['CUSTOMER_NUMBER', 'Device_ID_Hash']).cumcount()
df['NEW_DEVICE_FLAG'] = (df['device_seen_before'] == 0).astype(int)

counts = df['NEW_DEVICE_FLAG'].value_counts().sort_index()
total = len(df)
print(f"Counts:\n{counts}")
print(f"Percentages:\n{counts / total * 100}")

# Plot bar chart
fig, ax = plt.subplots(figsize=(6, 5))

categories = ['Known Device\n(NEW_DEVICE_FLAG=0)', 'New Device\n(NEW_DEVICE_FLAG=1)']
proportions = [counts.get(0, 0) / total, counts.get(1, 0) / total]

# Draw bars with navy palette and highlight
bars = ax.bar(categories, proportions, color=[COLORS['bright_navy'], COLORS['highlight_orange']], 
              edgecolor=COLORS['dark_midnight'], width=0.5, alpha=0.9, linewidth=1)

# Style chart
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color(COLORS['dark_midnight'])
ax.spines['bottom'].set_color(COLORS['dark_midnight'])

# Hide y-axis values/numbers to respect "Không để số trên chart" (No numbers on chart)
ax.set_yticklabels([])
ax.set_yticks([])

# Set labels and title
ax.set_ylabel('Proportion', fontsize=12, color=COLORS['dark_midnight'])
ax.set_xlabel('Device Type', fontsize=12, color=COLORS['dark_midnight'], labelpad=10)
ax.set_title('Distribution of NEW_DEVICE_FLAG', fontsize=14, weight='bold', pad=15, color=COLORS['dark_midnight'])

# Add legend with 2pt spacing from the Ox axis title
# The Ox axis title is set with labelpad=10, we place the legend right below it using bbox_to_anchor.
ax.legend(bars, ['Known Device (94.9%)', 'New Device (5.1%)'], 
          loc='upper center', bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=2)

plt.tight_layout()

# Save plot
output_path = os.path.join(project_root, "eda", "outputs", "new_device_flag_distribution.png")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
plt.savefig(output_path, dpi=200, bbox_inches='tight')
print(f"Chart successfully saved to: {output_path}")
