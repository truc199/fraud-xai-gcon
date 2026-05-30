import os
import argparse
import pandas as pd
import datetime
import json
import re
import numpy as np
from collections import Counter
from src.pipeline.new_features_data_loader import NewFeaturesDataLoader
from src.pipeline.new_features_preprocessor import NewFeaturesPreprocessor
from src.pipeline.new_features_explainer import NewFeaturesExplainer
from src.pipeline.custom_orchestrator import CustomHierarchicalMLPipeline
from src.pipeline.nnpu_c_classifier import NNPUCModelAgent
from src.pipeline.plugins import ConsoleLoggerPlugin, MetricsTrackerPlugin
from src.pipeline.rules import SequenceRarityRule, VelocityBypassRule, SmallAmountBypassRule
from src.pipeline.dormancy_wakeup_rule import DormancyWakeupRule
from src.pipeline.ato_panic_rule import ATOPanicRule
from src.pipeline.low_risk_channel_rule import LowRiskChannelBypassRule
from src.pipeline.hourly_anomaly_rule import HourlyAnomalyRule
from src.pipeline.credit_card_bustout_rule import CreditCardBustOutRule


DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "gcontest.db"))


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
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Run clean_and_build_db.py first.")
        return

    print("=== Advanced Cohort Fraud & xAI Experimental Pipeline ===")
    print("=== (No counterfactual recourse — fast full-population SHAP) ===")
    
    # 1. Instantiate modular components conforming to Protocols
    data_loader = NewFeaturesDataLoader(db_path=DB_PATH)
    preprocessor = NewFeaturesPreprocessor()
    
    # Use NNPU & C Calibrated XGBoost Model Agent (Option A + C)
    model_agent = NNPUCModelAgent(contamination=0.005)
    explainer = NewFeaturesExplainer(background_data_limit=100, compute_recourse=False)
    
    # Middlewares
    plugins = [ConsoleLoggerPlugin(), MetricsTrackerPlugin()]
    
    # 2. Assemble the Pipeline (Hierarchical Fallback Routing - Option B)
    rules = [
        # Existing BYPASS rules
        SequenceRarityRule(rarity_threshold=-1.0, amount_threshold=5000000.0),
        VelocityBypassRule(amount_threshold=500000.0, count_1h_threshold=1.0, count_24h_threshold=2.0),
        # New BYPASS rule
        LowRiskChannelBypassRule(amount_threshold=5_000_000),
        # New BLOCK rules (Fraud=1 overrides Safe=0 per orchestrator logic)
        DormancyWakeupRule(dormancy_days=90, amount_threshold=10_000_000),
        ATOPanicRule(hours_threshold=1.0, amount_threshold=10_000_000, min_hist_count=10),
        HourlyAnomalyRule(prob_threshold=0.015, amount_threshold=10_000_000),
        CreditCardBustOutRule(velocity_threshold=0.45, amount_threshold=20_000_000, ratio_threshold=10.0),
        SmallAmountBypassRule(amount_threshold=500000.0),
    ]
    pipeline = CustomHierarchicalMLPipeline(
        data_loader=data_loader,
        preprocessor=preprocessor,
        model_agent=model_agent,
        explainer=explainer,
        plugins=plugins,
        rules=rules
    )
    
    # 3. Train on the training set
    print("\n--- Phase 1: Training ---")
    confirmed_transactions = set()
    fraud_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "confirmed_frauds.json"))
    if os.path.exists(fraud_file):
        try:
            with open(fraud_file, "r") as f:
                data = json.load(f)
                confirmed_transactions = set(str(c).strip() for c in data.get("confirmed_transactions", []))
        except Exception as e:
            print(f"Warning: Failed to load confirmed frauds: {e}")
            
    df_train = data_loader.load_training_data(limit=900000)
    
    # Print active features
    preprocessor.fit(df_train)
    sample_features = preprocessor.transform(df_train.head(1))
    print("\n" + "="*60)
    print(f"ACTIVE PIPELINE FEATURES ({len(sample_features.columns)} total):")
    for idx, col in enumerate(sorted(sample_features.columns)):
        print(f"  {idx+1}. {col}")
    print("="*60 + "\n")

    y = pd.Series(0, index=df_train.index)
    if confirmed_transactions:
        y.loc[y.index.isin(confirmed_transactions)] = 1
        print(f"Loaded {len(confirmed_transactions)} confirmed fraud transactions. Flagged {y.sum()} transactions in training set.")
    else:
        print("No confirmed fraud transactions loaded for training.")
        
    pipeline.run_training_pipeline(limit=900000, y=y)
    
    # 4. Fetch test batch for inference and explanation
    print("\n--- Phase 2: Inference & xAI Generation (No Recourse) ---")
    df_test = data_loader.load_training_data(limit=900000)
    
    # Run prediction and generate explanations for ALL anomalies
    results = pipeline.run_inference_pipeline(df_test, explain_limit=100000)
    
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
            print("-" * 50)

    # 6. Export full results to experimental_result.csv
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
    
    # Map counterfactuals (will be empty since compute_recourse=False)
    cf_map = {}
    for exp in explanations:
        if exp.get('counterfactuals'):
            cf_list = [f"{cf['feature']}: {cf['original']:,.2f} -> {cf['safe_value']:,.2f} ({cf['delta']:+,.2f})" for cf in exp['counterfactuals']]
            cf_map[exp['instance_index']] = ", ".join(cf_list)
    df_export['COUNTERFACTUAL'] = [cf_map.get(i, "") for i in range(len(df_export))]
    
    # Reorder columns for visibility and filter to anomalies only
    key_cols = ['TRANSACTION_ID', 'CUSTOMER_NUMBER', 'ANOMALY_PRED', 'ANOMALY_SCORE', 'EXPLANATION', 'TOP_SHAP_CONTRIBUTORS', 'TOP_INTERACTIONS', 'COUNTERFACTUAL']
    other_cols = [c for c in df_export.columns if c not in key_cols]
    df_export = df_export[key_cols + other_cols]
    df_export = df_export[df_export['ANOMALY_PRED'] == 1].reset_index(drop=True)
    
    # Fill rule-based explanations for forced-fraud rows (Tier 1 BLOCK rules)
    # These rows have ANOMALY_SCORE == 1.0 and empty EXPLANATION because they
    # bypassed the model/explainer via deterministic routing rules.
    forced_mask = (df_export['ANOMALY_SCORE'] == 1.0) & (df_export['EXPLANATION'] == "")
    n_forced = forced_mask.sum()
    if n_forced > 0:
        # Load customer hour probabilities for HourlyAnomalyRule explanation
        import pickle
        fit_cache_filename = os.path.abspath(os.path.join("data", "NewFeaturesPreprocessor_fit.pkl"))
        customer_hour_probs = {}
        global_hour_probs = np.ones(24) / 24.0
        if os.path.exists(fit_cache_filename):
            try:
                with open(fit_cache_filename, "rb") as f:
                    fit_state = pickle.load(f)
                customer_hour_probs = fit_state.get('customer_hour_probs', {})
                global_hour_probs = fit_state.get('global_hour_probs', np.ones(24) / 24.0)
            except Exception:
                pass

        print(f"[Pipeline] Filling rule-based explanations for {n_forced:,} forced-fraud rows...")
        for idx in df_export[forced_mask].index:
            row = df_export.loc[idx]
            reasons = []
            
            # Check DormancyWakeupRule conditions
            days_since = float(row.get('DAYS_SINCE_LAST_TRANS', 0))
            amount = float(row.get('TRANS_AMOUNT', 0))
            trans_lv2 = str(row.get('TRANS_LV2', ''))
            hours_since_sec = float(row.get('HOURS_SINCE_SEC_EVENT', 999))
            hist_count = float(row.get('HIST_TRANS_COUNT', 0))
            
            if days_since > 90 and amount > 10_000_000 and 'Outside' in trans_lv2:
                reasons.append(
                    f"dormant account reactivation ({days_since:.0f} days inactive, "
                    f"large outbound transfer of {amount:,.0f})"
                )
            
            # Check ATOPanicRule conditions (new logic)
            reg_date = pd.to_datetime(row.get('IB_REGISTER_DATE'))
            if pd.isna(reg_date):
                reg_date = pd.to_datetime(row.get('CLIENT_CREATE_DATE'))
            
            if not pd.isna(reg_date):
                ts_dt = pd.to_datetime(row.get('TRANS_DATE')) + pd.to_timedelta(row.get('TRANS_HOUR', 0), unit='h')
                tenure_days = (ts_dt - reg_date).total_seconds() / (24 * 3600.0)
            else:
                tenure_days = 0.0

            if hours_since_sec <= 1.0 and amount > 10_000_000 and 'Outside_bank' in trans_lv2 and tenure_days >= 1.0:
                reasons.append(
                    f"potential account takeover (security credential changed {hours_since_sec:.1f}h ago, "
                    f"immediate large outbound transfer of {amount:,.0f} with tenure {tenure_days:.1f} days)"
                )

            # Check HourlyAnomalyRule conditions
            cust = row.get('CUSTOMER_NUMBER')
            h = int(round(float(row.get('TRANS_HOUR', 0)))) % 24
            prob = customer_hour_probs[cust][h] if cust in customer_hour_probs else global_hour_probs[h]
            if prob < 0.015 and amount > 10_000_000:
                reasons.append(
                    f"highly unusual transaction hour for customer (probability {prob * 100:.2f}%, "
                    f"large outbound transfer of {amount:,.0f})"
                )
            
            if reasons:
                narrative = "Blocked by deterministic rule: " + "; and ".join(reasons) + "."
            else:
                narrative = "Blocked by deterministic routing rule (high-confidence fraud pattern)."
            
            df_export.at[idx, 'EXPLANATION'] = narrative
            df_export.at[idx, 'TOP_SHAP_CONTRIBUTORS'] = "RULE_BLOCKED (no SHAP — deterministic)"
    
    os.makedirs("data", exist_ok=True)
    df_export.to_csv("data/experimental_result.csv", index=False)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export companion metadata JSON
    metadata = {
        "timestamp": timestamp,
        "components": {
            "orchestrator": pipeline.__class__.__name__,
            "data_loader": data_loader.__class__.__name__,
            "preprocessor": preprocessor.__class__.__name__,
            "model_agent": model_agent.__class__.__name__,
            "explainer": explainer.__class__.__name__,
            "compute_recourse": False,
            "plugins": [p.__class__.__name__ for p in plugins]
        },
        "metrics": {
            "anomalies_flagged": len(df_export),
            "total_records_evaluated": len(df_test),
            "explanations_generated": len(explanations)
        }
    }
    
    if hasattr(pipeline, "get_rules_descriptions"):
        metadata["rules"] = pipeline.get_rules_descriptions()
    
    with open("data/experimental_result_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    
    print(f"\n[Export] Full prediction and explanation results saved to:")
    print(f"  - data/experimental_result.csv ({len(df_export):,} anomaly rows)")
    print(f"  - data/experimental_result_metadata.json")
    print(f"  - Explanations generated: {len(explanations):,}")

if __name__ == "__main__":
    main()
