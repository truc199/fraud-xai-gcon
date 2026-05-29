import os
import pandas as pd
import re

csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'anomaly_alerts_latest.csv')

if not os.path.exists(csv_path):
    print(f"File not found: {csv_path}")
    exit(1)

df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} anomalies.")

feature_counts = {}
feature_shap_sums = {}

for idx, row in df.iterrows():
    shap_str = str(row.get('TOP_SHAP_CONTRIBUTORS', ''))
    if not shap_str or pd.isna(shap_str):
        continue
    
    parts = shap_str.split(', ')
    for part in parts:
        # Example format: "DAYS_AMOUNT_COMBINED (+3.3401)"
        match = re.match(r'([A-Za-z0-9_]+) \(([+-]?[\d.]+)\)', part)
        if match:
            feat = match.group(1)
            val = float(match.group(2))
            
            if feat not in feature_counts:
                feature_counts[feat] = 0
                feature_shap_sums[feat] = 0.0
                
            feature_counts[feat] += 1
            feature_shap_sums[feat] += abs(val)  # sum absolute importance

results = []
for feat in feature_counts:
    avg_shap = feature_shap_sums[feat] / feature_counts[feat] if feature_counts[feat] > 0 else 0
    results.append({
        'Feature': feat,
        'Times_in_Top_SHAP': feature_counts[feat],
        'Average_Abs_SHAP_Value': avg_shap,
        'Percentage_of_Anomalies': (feature_counts[feat] / len(df)) * 100
    })

res_df = pd.DataFrame(results).sort_values(by='Times_in_Top_SHAP', ascending=False)
print("\n--- SHAP Importance of ALL Features in Latest Run ---")
print(res_df.to_string(index=False))

out_path = os.path.join(os.path.dirname(__file__), 'outputs', 'all_features_shap_summary.csv')
res_df.to_csv(out_path, index=False)
print(f"\nResults saved to {out_path}")
