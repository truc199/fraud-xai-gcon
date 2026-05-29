import os
import pandas as pd
import json

# Ensure output directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), 'outputs'), exist_ok=True)

csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'anomaly_alerts_latest.csv')

if not os.path.exists(csv_path):
    print(f"File not found: {csv_path}")
    exit(1)

df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} anomalies.")

new_features = [
    'BENFORD_DEV',
    'IP_HOPPING_VELOCITY',
    'PAGERANK_SCORE',
    'IN_DEGREE_CENTRALITY',
    'BUST_OUT_UTILIZATION',
    'STRUCTURING_OVERPAYMENT_FLAG',
    'AUTH_DOWNGRADE_RISK'
]

# TOP_SHAP_CONTRIBUTORS looks like: 
# "['DAYS_AMOUNT_COMBINED (+3.34)', 'SEC_AMOUNT_COMBINED (+0.92)', ...]"
# But wait, looking at the previous log, it's:
# "{'DAYS_AMOUNT_COMBINED': 3.3401, 'SEC_AMOUNT_COMBINED': 0.9197, ...}" 
# Let's check how it's formatted in the CSV.

feature_counts = {f: 0 for f in new_features}
feature_shap_sums = {f: 0.0 for f in new_features}

for idx, row in df.iterrows():
    shap_str = str(row.get('TOP_SHAP_CONTRIBUTORS', ''))
    if not shap_str or pd.isna(shap_str):
        continue
    
    parts = shap_str.split(', ')
    for part in parts:
        for feat in new_features:
            if part.startswith(feat):
                feature_counts[feat] += 1
                # Extract value in parentheses like "(+3.3401)"
                import re
                match = re.search(r'\(([+-]?[\d.]+)\)', part)
                if match:
                    feature_shap_sums[feat] += float(match.group(1))

results = []
for feat in new_features:
    avg_shap = feature_shap_sums[feat] / feature_counts[feat] if feature_counts[feat] > 0 else 0
    results.append({
        'Feature': feat,
        'Times_in_Top_SHAP': feature_counts[feat],
        'Average_SHAP_Value': avg_shap,
        'Percentage_of_Anomalies': (feature_counts[feat] / len(df)) * 100
    })

res_df = pd.DataFrame(results).sort_values(by='Times_in_Top_SHAP', ascending=False)
print("\n--- SHAP Importance of New 2026 Features ---")
print(res_df.to_string(index=False))

out_path = os.path.join(os.path.dirname(__file__), 'outputs', 'new_features_shap_summary.csv')
res_df.to_csv(out_path, index=False)
print(f"\nResults saved to {out_path}")
