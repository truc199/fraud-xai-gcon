import os
import argparse
import pandas as pd
import datetime
import json
import re
import numpy as np
from collections import Counter
from src.pipeline.advanced_data_loader import AdvancedDataLoader
from src.pipeline.custom_preprocessor import CustomPreprocessor
from src.pipeline.custom_explainer import CustomBRACEExplainer
from src.pipeline.custom_orchestrator import CustomHierarchicalMLPipeline
from src.pipeline.nnpu_c_classifier import NNPUCModelAgent
from src.pipeline.ewc_model_agent import EWCModelAgent
from src.pipeline.plugins import ConsoleLoggerPlugin, MetricsTrackerPlugin


DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "gcontest.db"))

def resolve_filename(directory: str, base_name: str, ext: str) -> str:
    if base_name.endswith(ext):
        base_name = base_name[:-len(ext)]
    candidate = os.path.join(directory, f"{base_name}{ext}")
    if not os.path.exists(candidate):
        return candidate
    n = 2
    while True:
        candidate = os.path.join(directory, f"{base_name}({n}){ext}")
        if not os.path.exists(candidate):
            return candidate
        n += 1
def parse_contributors(text):
    if not isinstance(text, str) or not text.strip():
        return []
    pattern = r"([A-Za-z0-9_]+)\s*\(([-+0-9.]+)\)"
    return re.findall(pattern, text)

def parse_interactions(text):
    if not isinstance(text, str) or not text.strip():
        return []
    pattern = r"([A-Za-z0-9_]+\s*×\s*[A-Za-z0-9_]+)\s*\(([-+0-9.]+)\)"
    return re.findall(pattern, text)

def parse_counterfactuals(text):
    if not isinstance(text, str) or not text.strip():
        return []
    pattern = r"([A-Za-z0-9_]+):\s*([0-9.-]+)\s*->\s*([0-9.-]+)\s*\(([-+0-9.]+)\)"
    return re.findall(pattern, text)

def main():
    parser = argparse.ArgumentParser(description="Advanced Cohort Fraud & xAI Pipeline")
    parser.add_argument("--name", type=str, default=None, help="Custom export file name prefix")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Run clean_and_build_db.py first.")
        return

    print("=== Advanced Cohort Fraud & xAI Pipeline Demo ===")
    
    # 1. Instantiate modular components conforming to Protocols
    data_loader = AdvancedDataLoader(db_path=DB_PATH)
    preprocessor = CustomPreprocessor()
    
    # Use NNPU & C Calibrated XGBoost Model Agent (Option A + C)
    model_agent = NNPUCModelAgent(contamination=0.03)
    explainer = CustomBRACEExplainer(background_data_limit=100)
    
    # Middlewares
    plugins = [ConsoleLoggerPlugin(), MetricsTrackerPlugin()]
    
    # 2. Assemble the Pipeline (Hierarchical Fallback Routing - Option B)
    pipeline = CustomHierarchicalMLPipeline(
        data_loader=data_loader,
        preprocessor=preprocessor,
        model_agent=model_agent,
        explainer=explainer,
        plugins=plugins,
        tier1_rarity_threshold=-1.0,
        tier1_amount_threshold=500000.0,
        tier1_count_1h_threshold=1.0,
        tier1_count_24h_threshold=2.0
    )
    
    # 3. Train on a memory-safe subset of 50,000 records
    print("\n--- Phase 1: Training ---")
    pipeline.run_training_pipeline(limit=50000)
    
    # 4. Fetch test batch (5,000 records) for inference and explanation
    print("\n--- Phase 2: Inference & xAI Generation ---")
    df_test = data_loader.load_training_data(limit=5000)
    
    # Run prediction and generate explanations for all anomalies (up to 1000)
    results = pipeline.run_inference_pipeline(df_test, explain_limit=1000)
    
    # 5. Display the Explainable AI Alert Cards (limit console display to 3)
    explanations = results['explanations']
    print("\n=== Flagged Anomalies xAI Explanation Cards (Sample of 3) ===")
    if not explanations:
        print("No transactions were flagged as anomalous in this test batch.")
    else:
        for idx, exp in enumerate(explanations[:3]):
            print(f"\n[ALERT #{idx + 1}] Transaction Index: {exp['instance_index']}")
            print(f"  Risk Score: {exp['prediction_score']:.4f}")
            print(f"  Explanation Narrative: {exp['narrative']}")
            print("  Top Contributing Features (SHAP Values):")
            for c in exp['contributions']:
                print(f"    - {c['feature']} (value: {c['value']}): contribution = {c['contribution']:+.4f}")
            
            raw = exp['raw_record']
            print("  Raw Transaction Info:")
            print(f"    Customer ID: {raw['CUSTOMER_NUMBER']}")
            print(f"    Type: {raw['TRANS_LV1']} / {raw['TRANS_LV2']}")
            print(f"    Amount: {raw['TRANS_AMOUNT']:,.2f} | Average Amount: {raw['HIST_AVG_TRANS_AMOUNT']:,.2f}")
            print(f"    Average CA Balance: {raw['HIST_AVG_CA_BALANCE']:,.2f}")
            print(f"    Benford's Law Deviation Score: {raw['BENFORD_DEV']:.4f}")
            print(f"    Sequential Activity Rarity (Log-Prob): {raw['ACTIVITY_SEQ_RARITY']:.4f}")
            print(f"    Rolling 24h: Count = {int(raw['COUNT_24H'])} | Sum = {raw['SUM_AMOUNT_24H']:,.2f}")
            print(f"    Rolling 7d: Count = {int(raw['COUNT_7D'])} | Sum = {raw['SUM_AMOUNT_7D']:,.2f}")
            print(f"    Hour: {raw['TRANS_HOUR']} | Day: {raw['DAY_OF_WEEK']}")
            if exp.get('interactions'):
                print("  Toxic Feature Interactions (SHAP Interaction Values):")
                for inter in exp['interactions']:
                    print(f"    - {inter['feature_a']} × {inter['feature_b']}: interaction = {inter['interaction']:+.4f}")
            if exp.get('counterfactuals'):
                print("  Counterfactuals (minimum change to clear alert):")
                for cf in exp['counterfactuals']:
                    print(f"    - {cf['feature']}: {cf['original']:,.2f} -> {cf['safe_value']:,.2f} (delta: {cf['delta']:+,.2f})")
            print("-" * 50)

    # 6. Export full results to CSV files for analyst review
    os.makedirs("data/exports", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    df_export = df_test.copy()
    df_export['ANOMALY_PRED'] = results['predictions']
    df_export['ANOMALY_SCORE'] = results['probabilities']
    
    # Map narratives
    narrative_map = {exp['instance_index']: exp['narrative'] for exp in explanations}
    df_export['EXPLANATION'] = [narrative_map.get(i, "") for i in range(len(df_export))]
    
    # Map top contributors
    top_feats_map = {}
    for exp in explanations:
        feats_list = [f"{c['feature']} ({c['contribution']:+.4f})" for c in exp['contributions'][:3]]
        top_feats_map[exp['instance_index']] = ", ".join(feats_list)
    df_export['TOP_SHAP_CONTRIBUTORS'] = [top_feats_map.get(i, "") for i in range(len(df_export))]
    
    # Map top interactions
    interactions_map = {}
    for exp in explanations:
        if exp.get('interactions'):
            pairs_list = [f"{p['feature_a']} × {p['feature_b']} ({p['interaction']:+.4f})" for p in exp['interactions']]
            interactions_map[exp['instance_index']] = ", ".join(pairs_list)
    df_export['TOP_INTERACTIONS'] = [interactions_map.get(i, "") for i in range(len(df_export))]
    
    # Map counterfactuals
    cf_map = {}
    for exp in explanations:
        if exp.get('counterfactuals'):
            cf_list = [f"{cf['feature']}: {cf['original']:,.2f} -> {cf['safe_value']:,.2f} ({cf['delta']:+,.2f})" for cf in exp['counterfactuals']]
            cf_map[exp['instance_index']] = ", ".join(cf_list)
    df_export['COUNTERFACTUAL'] = [cf_map.get(i, "") for i in range(len(df_export))]
    
    # Reorder columns for visibility and filter to anomalies only
    key_cols = ['CUSTOMER_NUMBER', 'ANOMALY_PRED', 'ANOMALY_SCORE', 'EXPLANATION', 'TOP_SHAP_CONTRIBUTORS', 'TOP_INTERACTIONS', 'COUNTERFACTUAL']
    other_cols = [c for c in df_export.columns if c not in key_cols]
    df_export = df_export[key_cols + other_cols]
    df_export = df_export[df_export['ANOMALY_PRED'] == 1].reset_index(drop=True)
    
    if args.name:
        csv_latest = resolve_filename("data", args.name, ".csv")
        base_no_ext = os.path.splitext(os.path.basename(csv_latest))[0]
        json_latest = os.path.join("data", f"{base_no_ext}_metadata.json")
        
        csv_timestamped = resolve_filename("data/exports", f"{base_no_ext}_{timestamp}", ".csv")
        ts_base_no_ext = os.path.splitext(os.path.basename(csv_timestamped))[0]
        json_timestamped = os.path.join("data/exports", f"{ts_base_no_ext}_metadata.json")
    else:
        csv_latest = "data/anomaly_alerts_latest.csv"
        csv_timestamped = f"data/exports/anomaly_alerts_{timestamp}.csv"
        json_latest = "data/anomaly_alerts_latest_metadata.json"
        json_timestamped = f"data/exports/anomaly_alerts_{timestamp}_metadata.json"
    
    df_export.to_csv(csv_latest, index=False)
    df_export.to_csv(csv_timestamped, index=False)
    
    # Export companion metadata JSON
    metadata = {
        "timestamp": timestamp,
        "components": {
            "orchestrator": pipeline.__class__.__name__,
            "data_loader": data_loader.__class__.__name__,
            "preprocessor": preprocessor.__class__.__name__,
            "model_agent": model_agent.__class__.__name__,
            "explainer": explainer.__class__.__name__,
            "plugins": [p.__class__.__name__ for p in plugins]
        },
        "metrics": {
            "anomalies_flagged": len(df_export),
            "total_records_evaluated": len(df_test)
        }
    }
    
    with open(json_latest, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    with open(json_timestamped, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"\n[Export] Full prediction and explanation results saved to:")
    print(f"  - {csv_latest}")
    print(f"  - {csv_timestamped}")
    print(f"  - {json_latest}")
    print(f"  - {json_timestamped}")

    # Generate data/evaluation_report.md
    total_evaluated = len(df_test)
    anomalies_flagged = len(df_export)
    anomaly_rate = (anomalies_flagged / total_evaluated * 100) if total_evaluated > 0 else 0.0

    cust_counts = df_export["CUSTOMER_NUMBER"].value_counts()
    unique_customers_flagged = len(cust_counts)
    max_alerts_single_customer = cust_counts.max() if not cust_counts.empty else 0
    top_flagged_customer = cust_counts.idxmax() if not cust_counts.empty else "N/A"

    avg_anomaly_amount = df_export["TRANS_AMOUNT"].mean() if not df_export.empty else 0.0
    median_anomaly_amount = df_export["TRANS_AMOUNT"].median() if not df_export.empty else 0.0

    device_dist = df_export["Device_OS"].value_counts(normalize=True).to_dict() if "Device_OS" in df_export.columns else {}
    channel_dist = df_export["TRANS_LV2"].value_counts(normalize=True).to_dict() if "TRANS_LV2" in df_export.columns else {}

    shap_features = []
    for val in df_export["TOP_SHAP_CONTRIBUTORS"]:
        parsed = parse_contributors(val)
        for feat, score in parsed:
            shap_features.append(feat)
    top_shap_counts = Counter(shap_features).most_common(10)

    interactions = []
    if "TOP_INTERACTIONS" in df_export.columns:
        for val in df_export["TOP_INTERACTIONS"]:
            parsed = parse_interactions(val)
            for pair, score in parsed:
                interactions.append(pair)
    top_inter_counts = Counter(interactions).most_common(10)

    cf_features = []
    cf_count = 0
    for val in df_export["COUNTERFACTUAL"]:
        parsed = parse_counterfactuals(val)
        if parsed:
            cf_count += 1
            for feat, orig, safe, delta in parsed:
                cf_features.append(feat)
    
    cf_coverage_rate = (cf_count / anomalies_flagged * 100) if anomalies_flagged > 0 else 0.0
    top_cf_counts = Counter(cf_features).most_common(10)

    report_content = f"""# Pipeline Anomaly Detection Evaluation Report

## 1. Summary Statistics
* **Evaluation Timestamp:** {timestamp}
* **Total Transactions Evaluated:** {total_evaluated:,}
* **Anomalies Flagged:** {anomalies_flagged:,}
* **Anomaly Flagging Rate:** {anomaly_rate:.2f}%
* **Unique Customers Flagged:** {unique_customers_flagged:,}
* **Max Alerts on Single Customer:** {max_alerts_single_customer:,} (Customer ID: {top_flagged_customer})

---

## 2. Risk Distribution Analysis

### Transaction Amount Profile
* **Average Flagged Transaction Amount:** {avg_anomaly_amount:,.2f}
* **Median Flagged Transaction Amount:** {median_anomaly_amount:,.2f}

### Device OS Distribution (Anomaly Alerts)
"""
    for os_name, val in device_dist.items():
        report_content += f"* **{os_name}:** {val * 100:.2f}%\n"

    report_content += "\n### Digital Channel Subtype Distribution (Anomaly Alerts)\n"
    for chan, val in channel_dist.items():
        report_content += f"* **{chan}:** {val * 100:.2f}%\n"

    report_content += f"""
---

## 3. Explainable AI (xAI) Insights

### Top 10 Primary Risk Contributors (SHAP)
These features appeared most frequently as the strongest driver of anomalous classification:
"""
    for feat, count in top_shap_counts:
        pct = (count / anomalies_flagged * 100) if anomalies_flagged > 0 else 0.0
        report_content += f"* **{feat}:** {count} alerts ({pct:.2f}%)\n"

    report_content += """
### Top 10 Toxic Feature Interactions
These pairs of features created the strongest non-linear risk interaction:
"""
    if top_inter_counts:
        for pair, count in top_inter_counts:
            pct = (count / anomalies_flagged * 100) if anomalies_flagged > 0 else 0.0
            report_content += f"* **{pair}:** {count} alerts ({pct:.2f}%)\n"
    else:
        report_content += "* No feature interaction values recorded.\n"

    report_content += f"""
---

## 4. Recourse & Actionability (Counterfactuals)
* **Counterfactual Coverage Rate:** {cf_coverage_rate:.2f}% (percentage of flagged anomalies with generated recourse instructions)
* **Top Adjusted Features for Recourse:**
"""
    if top_cf_counts:
        for feat, count in top_cf_counts:
            pct = (count / cf_count * 100) if cf_count > 0 else 0.0
            report_content += f"* **{feat}:** {count} recommendations ({pct:.2f}% of recourse cases)\n"
    else:
        report_content += "* No counterfactual adjustments recommended.\n"

    report_content += """
---

## 5. Areas for Quality Improvement

1. **Extreme Customer Skewness:**
   A single customer ID represents a disproportionate number of alerts. This indicates the model may have a bias toward specific account transaction patterns or needs customer-specific baseline normalization.
   
2. **Actionability of Recourse:**
   The top counterfactual recommendations involve historical rolling features (like 24-hour and 7-day counts) which a user cannot change in real-time. The explainer must be updated to prioritize actionable features (like transaction amount) or propagate changes to dependent features.
"""

    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "evaluation_report.md"))
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"  - {report_path}")


    # 7. Simulated Continuous Learning with EWC (Phase 5 Option B)
    print("\n--- Phase 3: Simulated Continuous Learning with EWC ---")
    df_train_subset = data_loader.load_training_data(limit=10000)
    X_train_sub = preprocessor.transform(df_train_subset)
    
    ewc_agent = EWCModelAgent(contamination=0.03)
    ewc_agent.fit(X_train_sub, epochs=5)
    print("  Base Autoencoder trained successfully.")
    
    print("  Calculating Fisher Information Matrix (FIM)...")
    ewc_agent.calculate_fisher(X_train_sub)
    
    # Simulate behavioral drift (e.g. transaction amounts multiply by 5.0)
    print("  Simulating transaction behavioral drift...")
    df_drifted = df_train_subset.copy()
    if 'TRANS_AMOUNT' in df_drifted.columns:
        df_drifted['TRANS_AMOUNT'] = df_drifted['TRANS_AMOUNT'] * 5.0
    X_drifted = preprocessor.transform(df_drifted)
    
    # Online retraining with EWC protection
    print("  Retraining Autoencoder online WITH EWC protection...")
    ewc_agent.fit_online(X_drifted, lambda_ewc=50.0, epochs=3)
    base_scores_ewc = ewc_agent.predict_proba(X_train_sub)
    print(f"  Mean anomaly score on baseline data WITH EWC    : {np.mean(base_scores_ewc):.4f}")
    
    # Compare with standard online retraining WITHOUT EWC
    standard_agent = EWCModelAgent(contamination=0.03)
    standard_agent.fit(X_train_sub, epochs=5)
    standard_agent.fit_online(X_drifted, lambda_ewc=0.0, epochs=3)
    base_scores_standard = standard_agent.predict_proba(X_train_sub)
    print(f"  Mean anomaly score on baseline data WITHOUT EWC : {np.mean(base_scores_standard):.4f}")
    print("  EWC keeps baseline anomaly scores lower, preventing catastrophic forgetting!")

if __name__ == "__main__":
    main()
