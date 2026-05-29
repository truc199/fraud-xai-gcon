"""
EDA: Analyze current Rule-Based bypass coverage and evaluate candidate new rules.
Outputs results to eda/outputs/rule_analysis_results.json
"""
import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "gcontest.db"))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    conn = sqlite3.connect(DB_PATH)
    
    # Load base transaction data with rolling windows
    print("Loading transaction data with rolling aggregates...")
    query = """
        WITH trans_time_added AS (
            SELECT 
                t.col_0 as TRANSACTION_ID,
                t.CUSTOMER_NUMBER,
                t.TRANS_LV1,
                t.TRANS_LV2,
                t.TRANS_DATE,
                t.TRANS_HOUR,
                t.TRANS_NO,
                t.TRANS_AMOUNT,
                t.Beneficiary_CUSTOMER_NUMBER,
                t.Device_ID_Hash,
                t.Device_OS,
                t.IP_Address_Proxy,
                (julianday(t.TRANS_DATE) + (t.TRANS_HOUR / 24.0)) as ts
            FROM Data_Transaction t
        ),
        rolling_metrics AS (
            SELECT *,
                COUNT(*) OVER (
                    PARTITION BY CUSTOMER_NUMBER ORDER BY ts
                    RANGE BETWEEN 1.0/24.0 PRECEDING AND CURRENT ROW
                ) as COUNT_1H,
                COUNT(*) OVER (
                    PARTITION BY CUSTOMER_NUMBER ORDER BY ts
                    RANGE BETWEEN 1.0 PRECEDING AND CURRENT ROW
                ) as COUNT_24H,
                SUM(TRANS_AMOUNT) OVER (
                    PARTITION BY CUSTOMER_NUMBER ORDER BY ts
                    RANGE BETWEEN 1.0 PRECEDING AND CURRENT ROW
                ) as SUM_AMOUNT_24H
            FROM trans_time_added
        ),
        deposit_agg AS (
            SELECT CUSTOMER_NUMBER, AVG(AVG_CA_BALANCE) as HIST_AVG_CA_BALANCE
            FROM Data_Deposit GROUP BY CUSTOMER_NUMBER
        ),
        trans_agg AS (
            SELECT CUSTOMER_NUMBER, AVG(TRANS_AMOUNT) as HIST_AVG_TRANS_AMOUNT, COUNT(*) as HIST_TRANS_COUNT
            FROM Data_Transaction GROUP BY CUSTOMER_NUMBER
        )
        SELECT 
            r.*,
            c.STAFF,
            c.CLIENT_CREATE_DATE,
            c.Occupation_Group,
            c.DATE_OF_BIRTH,
            c.IB_REGISTER_DATE,
            COALESCE(d.HIST_AVG_CA_BALANCE, 0.0) as HIST_AVG_CA_BALANCE,
            COALESCE(ta.HIST_AVG_TRANS_AMOUNT, 0.0) as HIST_AVG_TRANS_AMOUNT,
            COALESCE(ta.HIST_TRANS_COUNT, 0) as HIST_TRANS_COUNT
        FROM rolling_metrics r
        LEFT JOIN Data_Customer c ON r.CUSTOMER_NUMBER = c.CUSTOMER_NUMBER
        LEFT JOIN deposit_agg d ON r.CUSTOMER_NUMBER = d.CUSTOMER_NUMBER
        LEFT JOIN trans_agg ta ON r.CUSTOMER_NUMBER = ta.CUSTOMER_NUMBER
    """
    df = pd.read_sql_query(query, conn)
    total = len(df)
    print(f"Total transactions loaded: {total:,}")
    
    # Ensure numeric types
    for col in ['TRANS_AMOUNT', 'COUNT_1H', 'COUNT_24H', 'SUM_AMOUNT_24H', 
                'HIST_AVG_CA_BALANCE', 'HIST_AVG_TRANS_AMOUNT', 'HIST_TRANS_COUNT', 'STAFF']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    results = {"total_transactions": total}
    
    # =========================================================================
    # PART 1: CURRENT RULES ANALYSIS
    # =========================================================================
    print("\n" + "="*60)
    print("PART 1: ANALYSIS OF EXISTING RULES")
    print("="*60)
    
    # --- Rule 1: SequenceRarityRule ---
    # Note: ACTIVITY_SEQ_RARITY is not in raw SQL, it's computed in Python
    # We can't evaluate this rule precisely without running the full loader
    # But we CAN evaluate the TRANS_AMOUNT < 500K part
    
    amount_lt_500k = df['TRANS_AMOUNT'] < 500000
    n_lt_500k = amount_lt_500k.sum()
    pct_lt_500k = n_lt_500k / total * 100
    
    print(f"\n--- Amount < 500K VND analysis ---")
    print(f"  Transactions < 500K VND: {n_lt_500k:,} ({pct_lt_500k:.2f}%)")
    print(f"  Transactions >= 500K VND: {total - n_lt_500k:,} ({100-pct_lt_500k:.2f}%)")
    
    results["rule1_sequence_rarity"] = {
        "description": "Bypass if ACTIVITY_SEQ_RARITY > -1.0 AND TRANS_AMOUNT < 500K",
        "amount_lt_500k_count": int(n_lt_500k),
        "amount_lt_500k_pct": round(pct_lt_500k, 2),
        "note": "ACTIVITY_SEQ_RARITY requires full pipeline. Amount < 500K sets the upper bound."
    }
    
    # Amount distribution analysis
    amount_bins = [0, 100000, 500000, 1000000, 5000000, 10000000, 50000000, 100000000, float('inf')]
    amount_labels = ['<100K', '100K-500K', '500K-1M', '1M-5M', '5M-10M', '10M-50M', '50M-100M', '>100M']
    df['amount_bin'] = pd.cut(df['TRANS_AMOUNT'], bins=amount_bins, labels=amount_labels, right=False)
    amount_dist = df['amount_bin'].value_counts().sort_index()
    print(f"\n--- Transaction Amount Distribution ---")
    amount_dist_dict = {}
    for label, count in amount_dist.items():
        pct = count / total * 100
        print(f"  {label}: {count:,} ({pct:.2f}%)")
        amount_dist_dict[str(label)] = {"count": int(count), "pct": round(pct, 2)}
    results["amount_distribution"] = amount_dist_dict
    
    # --- Rule 2: VelocityBypassRule ---
    vel_safe = (df['TRANS_AMOUNT'] < 500000) & (df['COUNT_1H'] <= 1) & (df['COUNT_24H'] <= 2)
    n_vel_safe = vel_safe.sum()
    pct_vel = n_vel_safe / total * 100
    
    print(f"\n--- Rule 2: VelocityBypassRule ---")
    print(f"  Safe (AMOUNT < 500K AND COUNT_1H <= 1 AND COUNT_24H <= 2): {n_vel_safe:,} ({pct_vel:.2f}%)")
    
    results["rule2_velocity_bypass"] = {
        "description": "Bypass if TRANS_AMOUNT < 500K AND COUNT_1H <= 1 AND COUNT_24H <= 2",
        "safe_count": int(n_vel_safe),
        "safe_pct": round(pct_vel, 2)
    }
    
    # Combined bypass (Rule 1 amount part OR Rule 2)
    combined_bypass = amount_lt_500k | vel_safe  # Rule 1 upper bound OR Rule 2
    n_combined = combined_bypass.sum()
    pct_combined = n_combined / total * 100
    print(f"\n--- Combined Bypass (Rule1 upper bound OR Rule2) ---")
    print(f"  Total bypassed: {n_combined:,} ({pct_combined:.2f}%)")
    print(f"  Remaining for ML: {total - n_combined:,} ({100 - pct_combined:.2f}%)")
    
    # COUNT_1H and COUNT_24H distribution
    print(f"\n--- COUNT_1H Distribution ---")
    c1h_dist = df['COUNT_1H'].value_counts().sort_index().head(15)
    c1h_dict = {}
    for val, cnt in c1h_dist.items():
        pct = cnt / total * 100
        print(f"  COUNT_1H={int(val)}: {cnt:,} ({pct:.2f}%)")
        c1h_dict[str(int(val))] = {"count": int(cnt), "pct": round(pct, 2)}
    results["count_1h_distribution"] = c1h_dict
    
    print(f"\n--- COUNT_24H Distribution ---")
    c24h_dist = df['COUNT_24H'].value_counts().sort_index().head(15)
    c24h_dict = {}
    for val, cnt in c24h_dist.items():
        pct = cnt / total * 100
        print(f"  COUNT_24H={int(val)}: {cnt:,} ({pct:.2f}%)")
        c24h_dict[str(int(val))] = {"count": int(cnt), "pct": round(pct, 2)}
    results["count_24h_distribution"] = c24h_dict
    
    # =========================================================================
    # PART 2: CANDIDATE NEW RULES - COVERAGE ANALYSIS
    # =========================================================================
    print("\n" + "="*60)
    print("PART 2: CANDIDATE NEW RULES - DATA COVERAGE")
    print("="*60)
    
    # --- Candidate A: ATO Panic Rule (BLOCK) ---
    # Security event data
    print("\n--- Candidate A: ATO Panic Rule (BLOCK) ---")
    print("  Logic: HOURS_SINCE_SEC_EVENT < 1h AND TRANS_AMOUNT > 10M")
    sec_query = """
        SELECT CUSTOMER_NUMBER, ACTIVITY_DATE, ACTIVITY_HOUR, ACTIVITY_NAME
        FROM Data_Activity
        WHERE ACTIVITY_NAME IN ('CHANGE_PASSWORD','SET_PASSWORD','MB_SET_PIN','MB_CHANGE_PIN','MB_RESET_PIN','ACCOUNT_ADDRESS_BOOK_UPDATE')
    """
    sec_df = pd.read_sql_query(sec_query, conn)
    n_sec_events = len(sec_df)
    n_customers_with_sec = sec_df['CUSTOMER_NUMBER'].nunique()
    print(f"  Total security events in Data_Activity: {n_sec_events:,}")
    print(f"  Unique customers with security events: {n_customers_with_sec:,}")
    
    # Security event type breakdown
    sec_types = sec_df['ACTIVITY_NAME'].value_counts()
    sec_types_dict = {}
    for name, cnt in sec_types.items():
        print(f"    {name}: {cnt:,}")
        sec_types_dict[name] = int(cnt)
    
    # How many transactions >= 10M exist
    gt_10m = (df['TRANS_AMOUNT'] >= 10000000).sum()
    pct_gt_10m = gt_10m / total * 100
    print(f"  Transactions >= 10M VND: {gt_10m:,} ({pct_gt_10m:.2f}%)")
    
    results["candidate_a_ato_panic"] = {
        "description": "BLOCK if HOURS_SINCE_SEC_EVENT < 1h AND TRANS_AMOUNT > 10M",
        "security_events_total": int(n_sec_events),
        "customers_with_sec_events": int(n_customers_with_sec),
        "security_event_types": sec_types_dict,
        "transactions_gte_10m": int(gt_10m),
        "transactions_gte_10m_pct": round(pct_gt_10m, 2),
        "note": "Exact match requires joining sec events with transactions by time. Upper bound analysis provided."
    }
    
    # --- Candidate B: New Account Mule Rule (BLOCK) ---
    print("\n--- Candidate B: New Account Mule Rule (BLOCK) ---")
    print("  Logic: TENURE_DAYS < 30 AND TRANS_LV2 contains 'Outside' AND TRANS_AMOUNT > 10M")
    
    df['CLIENT_CREATE_DATE_dt'] = pd.to_datetime(df['CLIENT_CREATE_DATE'], errors='coerce')
    df['TRANS_DATE_dt'] = pd.to_datetime(df['TRANS_DATE'], errors='coerce')
    df['TENURE_DAYS'] = (df['TRANS_DATE_dt'] - df['CLIENT_CREATE_DATE_dt']).dt.days
    
    tenure_valid = df['TENURE_DAYS'].notna()
    tenure_lt_30 = (df['TENURE_DAYS'] < 30) & tenure_valid
    n_tenure_lt_30 = tenure_lt_30.sum()
    
    is_outside = df['TRANS_LV2'].str.contains('Outside', case=False, na=False)
    n_outside = is_outside.sum()
    pct_outside = n_outside / total * 100
    
    mule_candidate = tenure_lt_30 & is_outside & (df['TRANS_AMOUNT'] > 10000000)
    n_mule = mule_candidate.sum()
    
    print(f"  Accounts with tenure < 30 days: {n_tenure_lt_30:,}")
    print(f"  Transactions 'Outside Bank': {n_outside:,} ({pct_outside:.2f}%)")
    print(f"  Combined match (tenure<30 + outside + >10M): {n_mule:,}")
    
    # Tenure distribution
    tenure_bins = [0, 7, 30, 90, 365, 730, float('inf')]
    tenure_labels = ['<7d', '7-30d', '30-90d', '90d-1y', '1-2y', '>2y']
    df['tenure_bin'] = pd.cut(df['TENURE_DAYS'], bins=tenure_bins, labels=tenure_labels, right=False)
    tenure_dist = df['tenure_bin'].value_counts().sort_index()
    tenure_dict = {}
    print(f"\n  Tenure Distribution:")
    for label, count in tenure_dist.items():
        pct = count / total * 100
        print(f"    {label}: {count:,} ({pct:.2f}%)")
        tenure_dict[str(label)] = {"count": int(count), "pct": round(pct, 2)}
    
    results["candidate_b_new_account_mule"] = {
        "description": "BLOCK if TENURE_DAYS < 30 AND TRANS_LV2='Outside' AND TRANS_AMOUNT > 10M",
        "tenure_lt_30": int(n_tenure_lt_30),
        "outside_bank_count": int(n_outside),
        "outside_bank_pct": round(pct_outside, 2),
        "combined_match": int(n_mule),
        "tenure_distribution": tenure_dict
    }
    
    # --- Candidate C: Dormancy Wake-up Rule (BLOCK) ---
    print("\n--- Candidate C: Dormancy Wake-up Rule (BLOCK) ---")
    print("  Logic: DAYS_SINCE_LAST_TRANS > 90 AND TRANS_AMOUNT > 10M AND TRANS_LV2='Outside'")
    # We need to compute DAYS_SINCE_LAST_TRANS
    df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
    df = df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
    df['DAYS_SINCE_LAST'] = df.groupby('CUSTOMER_NUMBER')['ts_dt'].diff().dt.total_seconds() / 86400
    reg_date = pd.to_datetime(df['IB_REGISTER_DATE'], errors='coerce').fillna(df['CLIENT_CREATE_DATE_dt'])
    days_since_reg = (df['ts_dt'] - reg_date).dt.total_seconds() / 86400
    df['DAYS_SINCE_LAST'] = df['DAYS_SINCE_LAST'].fillna(days_since_reg).fillna(999.0)
    
    dormant_90 = df['DAYS_SINCE_LAST'] > 90
    n_dormant_90 = dormant_90.sum()
    dormant_wakeup = dormant_90 & (df['TRANS_AMOUNT'] > 10000000) & is_outside
    n_dormant_wakeup = dormant_wakeup.sum()
    
    print(f"  Transactions after >90 days dormancy: {n_dormant_90:,} ({n_dormant_90/total*100:.2f}%)")
    print(f"  Dormancy >90d + >10M + Outside: {n_dormant_wakeup:,}")
    
    # Dormancy distribution
    dormancy_bins = [0, 1, 7, 30, 90, 180, 365, float('inf')]
    dormancy_labels = ['<1d', '1-7d', '7-30d', '30-90d', '90-180d', '180d-1y', '>1y']
    df['dormancy_bin'] = pd.cut(df['DAYS_SINCE_LAST'], bins=dormancy_bins, labels=dormancy_labels, right=False)
    dormancy_dist = df['dormancy_bin'].value_counts().sort_index()
    dormancy_dict = {}
    print(f"\n  Dormancy Distribution:")
    for label, count in dormancy_dist.items():
        pct = count / total * 100
        print(f"    {label}: {count:,} ({pct:.2f}%)")
        dormancy_dict[str(label)] = {"count": int(count), "pct": round(pct, 2)}
    
    results["candidate_c_dormancy_wakeup"] = {
        "description": "BLOCK if DAYS_SINCE_LAST > 90 AND TRANS_AMOUNT > 10M AND TRANS_LV2='Outside'",
        "dormant_90d_count": int(n_dormant_90),
        "dormant_wakeup_match": int(n_dormant_wakeup),
        "dormancy_distribution": dormancy_dict
    }
    
    # --- Candidate D: High-Value Outside Transfer Bypass Enhancement ---
    print("\n--- Candidate D: Staff/Internal Bypass (SAFE) ---")
    print("  Logic: STAFF=1 AND TRANS_AMOUNT < 5M")
    is_staff = df['STAFF'] == 1
    n_staff = is_staff.sum()
    staff_low_value = is_staff & (df['TRANS_AMOUNT'] < 5000000)
    n_staff_lv = staff_low_value.sum()
    print(f"  Staff transactions: {n_staff:,} ({n_staff/total*100:.2f}%)")
    print(f"  Staff + < 5M: {n_staff_lv:,} ({n_staff_lv/total*100:.2f}%)")
    
    results["candidate_d_staff_bypass"] = {
        "description": "BYPASS if STAFF=1 AND TRANS_AMOUNT < 5M",
        "staff_transactions": int(n_staff),
        "staff_lt_5m": int(n_staff_lv)
    }
    
    # --- Candidate E: Utility Payment Bypass (SAFE) ---
    print("\n--- Candidate E: Utility/Bill Payment Bypass (SAFE) ---")
    print("  Logic: TRANS_LV1 = 'Payment' AND TRANS_AMOUNT < 2M")
    trans_lv1_dist = df['TRANS_LV1'].value_counts()
    print(f"  TRANS_LV1 Distribution:")
    lv1_dict = {}
    for label, count in trans_lv1_dist.items():
        pct = count / total * 100
        print(f"    {label}: {count:,} ({pct:.2f}%)")
        lv1_dict[str(label)] = {"count": int(count), "pct": round(pct, 2)}
    
    trans_lv2_dist = df['TRANS_LV2'].value_counts()
    print(f"\n  TRANS_LV2 Distribution:")
    lv2_dict = {}
    for label, count in trans_lv2_dist.items():
        pct = count / total * 100
        print(f"    {label}: {count:,} ({pct:.2f}%)")
        lv2_dict[str(label)] = {"count": int(count), "pct": round(pct, 2)}
    
    results["transaction_type_distribution"] = {"TRANS_LV1": lv1_dict, "TRANS_LV2": lv2_dict}
    
    # --- Candidate F: Balance Drawdown Rule (BLOCK) ---
    print("\n--- Candidate F: Balance Drawdown Rule (BLOCK) ---")
    print("  Logic: SUM_AMOUNT_24H / HIST_AVG_CA_BALANCE > 0.8 AND TRANS_LV2='Outside'")
    eps = 1e-5
    df['BALANCE_DRAWDOWN'] = df['SUM_AMOUNT_24H'] / (df['HIST_AVG_CA_BALANCE'] + eps)
    has_balance = df['HIST_AVG_CA_BALANCE'] > 0
    drawdown_high = (df['BALANCE_DRAWDOWN'] > 0.8) & has_balance & is_outside
    n_drawdown = drawdown_high.sum()
    print(f"  Customers with HIST_AVG_CA_BALANCE > 0: {has_balance.sum():,}")
    print(f"  Drawdown > 80% + Outside Bank: {n_drawdown:,} ({n_drawdown/total*100:.4f}%)")
    
    # Drawdown distribution (only where balance exists)
    drawdown_vals = df.loc[has_balance, 'BALANCE_DRAWDOWN']
    print(f"  Drawdown ratio stats (where balance > 0):")
    print(f"    Mean: {drawdown_vals.mean():.4f}")
    print(f"    Median: {drawdown_vals.median():.4f}")
    print(f"    P90: {drawdown_vals.quantile(0.90):.4f}")
    print(f"    P95: {drawdown_vals.quantile(0.95):.4f}")
    print(f"    P99: {drawdown_vals.quantile(0.99):.4f}")
    print(f"    Max: {drawdown_vals.max():.4f}")
    
    results["candidate_f_balance_drawdown"] = {
        "description": "BLOCK if SUM_AMOUNT_24H / HIST_AVG_CA_BALANCE > 0.8 AND TRANS_LV2='Outside'",
        "customers_with_balance": int(has_balance.sum()),
        "drawdown_gt_80_outside": int(n_drawdown),
        "drawdown_stats": {
            "mean": round(float(drawdown_vals.mean()), 4),
            "median": round(float(drawdown_vals.median()), 4),
            "p90": round(float(drawdown_vals.quantile(0.90)), 4),
            "p95": round(float(drawdown_vals.quantile(0.95)), 4),
            "p99": round(float(drawdown_vals.quantile(0.99)), 4),
            "max": round(float(drawdown_vals.max()), 4)
        }
    }
    
    # --- Candidate G: Multi-Beneficiary Scatter Rule (BLOCK) ---
    print("\n--- Candidate G: Multi-Beneficiary Scatter Rule (BLOCK) ---")
    print("  Logic: UNIQUE_BENEFICIARIES_24H >= 3 AND SUM_AMOUNT_24H > 20M")
    # Compute unique beneficiaries 24h
    bene_query = """
        SELECT CUSTOMER_NUMBER, Beneficiary_CUSTOMER_NUMBER, COUNT(*) as cnt
        FROM Data_Transaction
        WHERE Beneficiary_CUSTOMER_NUMBER IS NOT NULL
          AND Beneficiary_CUSTOMER_NUMBER != ''
        GROUP BY CUSTOMER_NUMBER
    """
    bene_df = pd.read_sql_query(bene_query, conn)
    avg_bene = bene_df['cnt'].mean()
    print(f"  Average transactions with beneficiary per customer: {avg_bene:.2f}")
    
    # Check how many customers send to 3+ distinct beneficiaries
    bene_unique_query = """
        SELECT CUSTOMER_NUMBER, COUNT(DISTINCT Beneficiary_CUSTOMER_NUMBER) as unique_bene
        FROM Data_Transaction
        WHERE Beneficiary_CUSTOMER_NUMBER IS NOT NULL
          AND Beneficiary_CUSTOMER_NUMBER != ''
        GROUP BY CUSTOMER_NUMBER
    """
    bene_unique_df = pd.read_sql_query(bene_unique_query, conn)
    bene_gte3 = (bene_unique_df['unique_bene'] >= 3).sum()
    bene_gte5 = (bene_unique_df['unique_bene'] >= 5).sum()
    print(f"  Customers with >= 3 unique beneficiaries (lifetime): {bene_gte3:,}")
    print(f"  Customers with >= 5 unique beneficiaries (lifetime): {bene_gte5:,}")
    
    results["candidate_g_multi_beneficiary"] = {
        "description": "BLOCK if UNIQUE_BENEFICIARIES_24H >= 3 AND SUM_AMOUNT_24H > 20M",
        "avg_transactions_with_beneficiary": round(avg_bene, 2),
        "customers_gte3_unique_bene_lifetime": int(bene_gte3),
        "customers_gte5_unique_bene_lifetime": int(bene_gte5)
    }
    
    # --- Candidate H: Night High-Value Outside Transfer ---
    print("\n--- Candidate H: Night High-Value Outside Transfer ---")
    print("  Logic: TRANS_HOUR in [0,5] AND TRANS_AMOUNT > 20M AND TRANS_LV2='Outside'")
    is_night = df['TRANS_HOUR'].isin([0, 1, 2, 3, 4, 5])
    night_total = is_night.sum()
    night_high_outside = is_night & (df['TRANS_AMOUNT'] > 20000000) & is_outside
    n_night_high = night_high_outside.sum()
    
    print(f"  Night transactions (0h-5h): {night_total:,} ({night_total/total*100:.2f}%)")
    print(f"  Night + >20M + Outside: {n_night_high:,}")
    
    # Hour distribution
    hour_dist = df['TRANS_HOUR'].value_counts().sort_index()
    hour_dict = {}
    for h, cnt in hour_dist.items():
        hour_dict[str(int(h))] = {"count": int(cnt), "pct": round(cnt/total*100, 2)}
    
    results["candidate_h_night_high_value"] = {
        "description": "ALERT if TRANS_HOUR in [0-5] AND TRANS_AMOUNT > 20M AND TRANS_LV2='Outside'",
        "night_transactions": int(night_total),
        "night_high_outside": int(n_night_high),
        "hour_distribution": hour_dict
    }
    
    # --- Summary: Transaction type x amount cross-tab ---
    print("\n--- Cross-tab: TRANS_LV2 x Amount Bucket ---")
    crosstab = pd.crosstab(df['TRANS_LV2'], df['amount_bin'])
    print(crosstab.to_string())
    
    # Save results
    output_path = os.path.join(OUTPUT_DIR, "rule_analysis_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")
    
    conn.close()

if __name__ == '__main__':
    main()
