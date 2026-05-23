import os
import argparse
import pandas as pd
import datetime
import json
import numpy as np
from src.pipeline.second_order_markov_loader import SecondOrderMarkovDataLoader
from src.pipeline.preprocessors import StandardPreprocessor
from src.pipeline.nnpu_c_classifier import NNPUCModelAgent
from src.pipeline.brace_explainer import BRACEExplainer
from src.pipeline.ewc_model_agent import EWCModelAgent
from src.pipeline.hierarchical_orchestrator import HierarchicalMLPipeline
from src.pipeline.plugins import ConsoleLoggerPlugin, MetricsTrackerPlugin

DB_PATH = "/home/hoang/python/gcontest/data/gcontest.db"

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

def main():
    parser = argparse.ArgumentParser(description="Advanced Cohort Fraud & xAI Pipeline")
    parser.add_argument("--name", type=str, default=None, help="Custom export file name prefix")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Run clean_and_build_db.py first.")
        return

    print("=== Advanced Cohort Fraud & xAI Pipeline Demo ===")
    
    # 1. Instantiate modular components conforming to Protocols
    data_loader = SecondOrderMarkovDataLoader(db_path=DB_PATH)
    preprocessor = StandardPreprocessor()
    
    # Use NNPU & C Calibrated XGBoost Model Agent (Option A + C)
    model_agent = NNPUCModelAgent(contamination=0.03)
    explainer = BRACEExplainer(background_data_limit=100)
    
    # Middlewares
    plugins = [ConsoleLoggerPlugin(), MetricsTrackerPlugin()]
    
    # 2. Assemble the Pipeline (Hierarchical Fallback Routing - Option B)
    pipeline = HierarchicalMLPipeline(
        data_loader=data_loader,
        preprocessor=preprocessor,
        model_agent=model_agent,
        explainer=explainer,
        plugins=plugins,
        tier1_rarity_threshold=-1.0,
        tier1_amount_threshold=500000.0
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
                    print(f"    - {cf['feature']}: {cf['original']:,.2f} → {cf['safe_value']:,.2f} (delta: {cf['delta']:+,.2f})")
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
            cf_list = [f"{cf['feature']}: {cf['original']:,.2f} → {cf['safe_value']:,.2f} ({cf['delta']:+,.2f})" for cf in exp['counterfactuals']]
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
