import os
import re
import json
import pandas as pd
from collections import Counter

CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "anomaly_alerts_latest.csv"))
JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "anomaly_alerts_latest_metadata.json"))
REPORT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "evaluation_report.md"))

def parse_contributors(text):
    if not isinstance(text, str) or not text.strip():
        return []
    # format: FEATURE (+1.2345), FEATURE2 (-0.3456)
    pattern = r"([A-Za-z0-9_]+)\s*\(([-+0-9.]+)\)"
    return re.findall(pattern, text)

def parse_interactions(text):
    if not isinstance(text, str) or not text.strip():
        return []
    # format: FEAT1 × FEAT2 (+0.123), FEAT3 × FEAT4 (-0.456)
    pattern = r"([A-Za-z0-9_]+\s*×\s*[A-Za-z0-9_]+)\s*\(([-+0-9.]+)\)"
    return re.findall(pattern, text)

def parse_counterfactuals(text):
    if not isinstance(text, str) or not text.strip():
        return []
    # format: FEAT: 11.00 -> 6.00 (-5.00), FEAT2: 30.00 -> 21.00 (-9.00)
    pattern = r"([A-Za-z0-9_]+):\s*([0-9.-]+)\s*->\s*([0-9.-]+)\s*\(([-+0-9.]+)\)"
    return re.findall(pattern, text)

def main():
    if not os.path.exists(CSV_PATH) or not os.path.exists(JSON_PATH):
        print(f"Error: Required files not found at data/. Run pipeline first.")
        return

    # Load metadata
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Load CSV
    df = pd.read_csv(CSV_PATH)

    total_evaluated = metadata.get("metrics", {}).get("total_records_evaluated", 0)
    anomalies_flagged = metadata.get("metrics", {}).get("anomalies_flagged", 0)
    anomaly_rate = (anomalies_flagged / total_evaluated * 100) if total_evaluated > 0 else 0.0

    # 1. Customer Alert Skewness
    cust_counts = df["CUSTOMER_NUMBER"].value_counts()
    unique_customers_flagged = len(cust_counts)
    max_alerts_single_customer = cust_counts.max() if not cust_counts.empty else 0
    top_flagged_customer = cust_counts.idxmax() if not cust_counts.empty else "N/A"

    # 2. Transaction Amount details
    avg_anomaly_amount = df["TRANS_AMOUNT"].mean() if not df.empty else 0.0
    median_anomaly_amount = df["TRANS_AMOUNT"].median() if not df.empty else 0.0

    # 3. Categorical distribution
    device_dist = df["Device_OS"].value_counts(normalize=True).to_dict() if "Device_OS" in df.columns else {}
    channel_dist = df["TRANS_LV2"].value_counts(normalize=True).to_dict() if "TRANS_LV2" in df.columns else {}

    # 4. Parse SHAP Contributors
    shap_features = []
    for val in df["TOP_SHAP_CONTRIBUTORS"]:
        parsed = parse_contributors(val)
        for feat, score in parsed:
            shap_features.append(feat)
    top_shap_counts = Counter(shap_features).most_common(10)

    # 5. Parse Feature Interactions
    interactions = []
    if "TOP_INTERACTIONS" in df.columns:
        for val in df["TOP_INTERACTIONS"]:
            parsed = parse_interactions(val)
            for pair, score in parsed:
                interactions.append(pair)
    top_inter_counts = Counter(interactions).most_common(10)

    # 6. Parse Counterfactual Recourse statistics
    cf_features = []
    cf_count = 0
    total_anomalies_evaluated = len(df)
    for val in df["COUNTERFACTUAL"]:
        parsed = parse_counterfactuals(val)
        if parsed:
            cf_count += 1
            for feat, orig, safe, delta in parsed:
                cf_features.append(feat)
    
    cf_coverage_rate = (cf_count / total_anomalies_evaluated * 100) if total_anomalies_evaluated > 0 else 0.0
    top_cf_counts = Counter(cf_features).most_common(10)

    # Write report
    report_content = f"""# Pipeline Anomaly Detection Evaluation Report

## 1. Summary Statistics
* **Evaluation Timestamp:** {metadata.get('timestamp', 'N/A')}
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
        pct = (count / total_anomalies_evaluated * 100) if total_anomalies_evaluated > 0 else 0.0
        report_content += f"* **{feat}:** {count} alerts ({pct:.2f}%)\n"

    report_content += """
### Top 10 Toxic Feature Interactions
These pairs of features created the strongest non-linear risk interaction:
"""
    if top_inter_counts:
        for pair, count in top_inter_counts:
            pct = (count / total_anomalies_evaluated * 100) if total_anomalies_evaluated > 0 else 0.0
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

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)

    print("=== Pipeline Evaluation Completed ===")
    print(f"Report written to: {REPORT_PATH}")
    print(f"Total Evaluated: {total_evaluated} | Anomalies: {anomalies_flagged} ({anomaly_rate:.2f}%)")
    print(f"Top Flagged Customer: ID {top_flagged_customer} with {max_alerts_single_customer} alerts")
    print(f"Counterfactual Coverage: {cf_coverage_rate:.2f}%")

if __name__ == "__main__":
    main()
