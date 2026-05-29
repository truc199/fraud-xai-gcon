"""
Full SHAP Feature Importance Analysis
Parses the pipeline output CSV and generates a comprehensive breakdown
of all 22 features' SHAP contributions across all anomaly alerts.
"""
import os
import re
import pandas as pd
import numpy as np
from collections import Counter, defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def find_latest_csv(pattern="full_pipeline_v3_final"):
    """Find the latest matching CSV file in data/."""
    candidates = [f for f in os.listdir(DATA_DIR) if f.startswith(pattern) and f.endswith('.csv')]
    if not candidates:
        # Fallback to anomaly_alerts_with_new_device
        candidates = [f for f in os.listdir(DATA_DIR) if 'anomaly_alerts' in f and f.endswith('.csv') and 'metadata' not in f]
    if not candidates:
        raise FileNotFoundError("No pipeline output CSV found in data/")
    candidates.sort()
    return os.path.join(DATA_DIR, candidates[0])

def parse_shap_contributors(text):
    """Parse TOP_SHAP_CONTRIBUTORS column: 'FEATURE_NAME (+0.1234), ...'"""
    if not isinstance(text, str) or not text.strip():
        return []
    pattern = r"([A-Za-z0-9_]+)\s*\(([-+][0-9.]+)\)"
    return [(name, float(score)) for name, score in re.findall(pattern, text)]

def parse_interactions(text):
    """Parse TOP_INTERACTIONS column: 'FEAT_A × FEAT_B (+0.1234), ...'"""
    if not isinstance(text, str) or not text.strip():
        return []
    pattern = r"([A-Za-z0-9_]+)\s*×\s*([A-Za-z0-9_]+)\s*\(([-+][0-9.]+)\)"
    return [(a, b, float(score)) for a, b, score in re.findall(pattern, text)]

def parse_counterfactuals(text):
    """Parse COUNTERFACTUAL column: 'FEATURE: 1234.00 -> 567.00 (-667.00), ...'"""
    if not isinstance(text, str) or not text.strip():
        return []
    pattern = r"([A-Za-z0-9_]+):\s*([0-9,.-]+)\s*->\s*([0-9,.-]+)\s*\(([-+0-9,.]+)\)"
    results = []
    for name, orig, safe, delta in re.findall(pattern, text):
        try:
            results.append((name, float(orig.replace(',', '')), float(safe.replace(',', '')), float(delta.replace(',', ''))))
        except ValueError:
            pass
    return results

def main():
    csv_path = find_latest_csv()
    print(f"Analyzing: {csv_path}")
    df = pd.read_csv(csv_path)
    total_alerts = len(df)
    print(f"Total anomaly alerts: {total_alerts}")
    
    # =========================================================
    # 1. SHAP Feature Importance (Frequency + Mean Magnitude)
    # =========================================================
    print("\n" + "=" * 70)
    print("1. SHAP FEATURE IMPORTANCE — FREQUENCY & MEAN MAGNITUDE")
    print("=" * 70)
    
    feature_freq = Counter()          # How many alerts each feature appears in top contributors
    feature_total_shap = defaultdict(list)  # All SHAP values per feature
    feature_rank_sum = defaultdict(list)    # Track rank position
    
    for _, row in df.iterrows():
        contribs = parse_shap_contributors(row.get('TOP_SHAP_CONTRIBUTORS', ''))
        for rank, (name, score) in enumerate(contribs):
            feature_freq[name] += 1
            feature_total_shap[name].append(abs(score))
            feature_rank_sum[name].append(rank + 1)
    
    # Build summary table
    summary_rows = []
    for feat in feature_freq:
        freq = feature_freq[feat]
        shap_vals = feature_total_shap[feat]
        ranks = feature_rank_sum[feat]
        summary_rows.append({
            'Feature': feat,
            'Appearances': freq,
            'Appearance_Rate': freq / total_alerts * 100,
            'Mean_Abs_SHAP': np.mean(shap_vals),
            'Max_Abs_SHAP': np.max(shap_vals),
            'Mean_Rank': np.mean(ranks),
        })
    
    summary_df = pd.DataFrame(summary_rows).sort_values('Appearances', ascending=False)
    
    print(f"\n{'Feature':<40} {'Freq':>6} {'Rate%':>7} {'Mean|SHAP|':>12} {'Max|SHAP|':>11} {'Avg Rank':>9}")
    print("-" * 95)
    for _, r in summary_df.iterrows():
        print(f"{r['Feature']:<40} {int(r['Appearances']):>6} {r['Appearance_Rate']:>6.1f}% {r['Mean_Abs_SHAP']:>11.4f} {r['Max_Abs_SHAP']:>10.4f} {r['Mean_Rank']:>8.1f}")
    
    # =========================================================
    # 2. SHAP Feature Interactions
    # =========================================================
    print("\n" + "=" * 70)
    print("2. TOXIC FEATURE INTERACTIONS — FREQUENCY & MEAN MAGNITUDE")
    print("=" * 70)
    
    interaction_freq = Counter()
    interaction_shap = defaultdict(list)
    
    for _, row in df.iterrows():
        interactions = parse_interactions(row.get('TOP_INTERACTIONS', ''))
        for a, b, score in interactions:
            pair = f"{a} × {b}"
            interaction_freq[pair] += 1
            interaction_shap[pair].append(abs(score))
    
    inter_rows = []
    for pair in interaction_freq:
        freq = interaction_freq[pair]
        vals = interaction_shap[pair]
        inter_rows.append({
            'Interaction': pair,
            'Appearances': freq,
            'Appearance_Rate': freq / total_alerts * 100,
            'Mean_Abs_SHAP': np.mean(vals),
            'Max_Abs_SHAP': np.max(vals),
        })
    
    inter_df = pd.DataFrame(inter_rows).sort_values('Appearances', ascending=False)
    
    print(f"\n{'Interaction Pair':<55} {'Freq':>6} {'Rate%':>7} {'Mean|SHAP|':>12} {'Max|SHAP|':>11}")
    print("-" * 95)
    for _, r in inter_df.head(15).iterrows():
        print(f"{r['Interaction']:<55} {int(r['Appearances']):>6} {r['Appearance_Rate']:>6.1f}% {r['Mean_Abs_SHAP']:>11.4f} {r['Max_Abs_SHAP']:>10.4f}")
    
    # =========================================================
    # 3. Counterfactual Analysis
    # =========================================================
    print("\n" + "=" * 70)
    print("3. COUNTERFACTUAL RECOURSE — WHICH FEATURES NEED ADJUSTMENT?")
    print("=" * 70)
    
    cf_freq = Counter()
    cf_deltas = defaultdict(list)
    
    for _, row in df.iterrows():
        cfs = parse_counterfactuals(row.get('COUNTERFACTUAL', ''))
        for name, orig, safe, delta in cfs:
            cf_freq[name] += 1
            cf_deltas[name].append(abs(delta))
    
    cf_rows = []
    for feat in cf_freq:
        freq = cf_freq[feat]
        deltas = cf_deltas[feat]
        cf_rows.append({
            'Feature': feat,
            'Appearances': freq,
            'Appearance_Rate': freq / total_alerts * 100,
            'Mean_Delta': np.mean(deltas),
            'Median_Delta': np.median(deltas),
        })
    
    cf_df = pd.DataFrame(cf_rows).sort_values('Appearances', ascending=False)
    
    print(f"\n{'Feature':<40} {'Freq':>6} {'Rate%':>7} {'Mean Delta':>14} {'Median Delta':>14}")
    print("-" * 85)
    for _, r in cf_df.iterrows():
        print(f"{r['Feature']:<40} {int(r['Appearances']):>6} {r['Appearance_Rate']:>6.1f}% {r['Mean_Delta']:>13,.0f} {r['Median_Delta']:>13,.0f}")
    
    # =========================================================
    # 4. Alert Profile Summary
    # =========================================================
    print("\n" + "=" * 70)
    print("4. ALERT PROFILE SUMMARY")
    print("=" * 70)
    
    if 'ANOMALY_SCORE' in df.columns:
        print(f"\nAnomaly Score Distribution:")
        print(f"  Mean:   {df['ANOMALY_SCORE'].mean():.4f}")
        print(f"  Median: {df['ANOMALY_SCORE'].median():.4f}")
        print(f"  Std:    {df['ANOMALY_SCORE'].std():.4f}")
        print(f"  Min:    {df['ANOMALY_SCORE'].min():.4f}")
        print(f"  Max:    {df['ANOMALY_SCORE'].max():.4f}")
    
    if 'TRANS_AMOUNT' in df.columns:
        print(f"\nFlagged Transaction Amounts:")
        print(f"  Mean:   {df['TRANS_AMOUNT'].mean():,.0f} VND")
        print(f"  Median: {df['TRANS_AMOUNT'].median():,.0f} VND")
        print(f"  Min:    {df['TRANS_AMOUNT'].min():,.0f} VND")
        print(f"  Max:    {df['TRANS_AMOUNT'].max():,.0f} VND")
    
    if 'TRANS_LV2' in df.columns:
        print(f"\nChannel Distribution:")
        for ch, cnt in df['TRANS_LV2'].value_counts().items():
            print(f"  {ch}: {cnt} ({cnt/total_alerts*100:.1f}%)")
    
    if 'NEW_DEVICE_FLAG' in df.columns:
        new_dev = (df['NEW_DEVICE_FLAG'] == 1).sum()
        print(f"\nNEW_DEVICE_FLAG=1 in alerts: {new_dev} ({new_dev/total_alerts*100:.1f}%)")
    
    # Save outputs
    output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    summary_df.to_csv(os.path.join(output_dir, 'shap_feature_importance.csv'), index=False)
    inter_df.to_csv(os.path.join(output_dir, 'shap_interactions.csv'), index=False)
    cf_df.to_csv(os.path.join(output_dir, 'counterfactual_analysis.csv'), index=False)
    print(f"\nOutputs saved to {output_dir}/")

if __name__ == "__main__":
    main()
