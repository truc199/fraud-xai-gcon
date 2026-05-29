"""
Deep EDA: Analyze features computed by Fraud2026DataLoader that can be converted to rules.
Focus on: AUTH_DOWNGRADE_RISK, STRUCTURING_OVERPAYMENT_FLAG, IP_HOPPING_VELOCITY,
          BUST_OUT_UTILIZATION, HOURS_SINCE_SEC_EVENT combined with channel/amount.
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
    results = {}

    # ========================================================================
    # 1. HOURS_SINCE_SEC_EVENT distribution (exact, using same logic as loader)
    # ========================================================================
    print("="*60)
    print("1. HOURS_SINCE_SEC_EVENT × TRANS_AMOUNT × TRANS_LV2")
    print("="*60)

    # Load transactions
    tx_query = """
        SELECT col_0 as TRANSACTION_ID, CUSTOMER_NUMBER, TRANS_DATE, TRANS_HOUR,
               TRANS_AMOUNT, TRANS_LV2,
               (julianday(TRANS_DATE) + (TRANS_HOUR / 24.0)) as ts
        FROM Data_Transaction
    """
    df_tx = pd.read_sql_query(tx_query, conn)
    df_tx['ts_dt'] = pd.to_datetime(df_tx['TRANS_DATE']) + pd.to_timedelta(df_tx['TRANS_HOUR'], unit='h')
    df_tx['TRANS_AMOUNT'] = pd.to_numeric(df_tx['TRANS_AMOUNT'], errors='coerce').fillna(0)
    df_tx = df_tx.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
    df_tx['tx_id'] = df_tx.index
    total = len(df_tx)

    # Load sec events (exclude onboarding: MB_SET_PIN, SET_PASSWORD)
    sec_query = """
        SELECT CUSTOMER_NUMBER, ACTIVITY_DATE, ACTIVITY_HOUR, ACTIVITY_NAME
        FROM Data_Activity
        WHERE ACTIVITY_NAME IN ('CHANGE_PASSWORD', 'MB_CHANGE_PIN', 'MB_RESET_PIN', 'ACCOUNT_ADDRESS_BOOK_UPDATE')
    """
    sec_df = pd.read_sql_query(sec_query, conn)
    sec_df['ts_dt'] = pd.to_datetime(sec_df['ACTIVITY_DATE']) + pd.to_timedelta(sec_df['ACTIVITY_HOUR'], unit='h')
    sec_df = sec_df.sort_values('ts_dt').reset_index(drop=True)
    sec_df['sec_event_ts'] = sec_df['ts_dt']

    print(f"  Sec events (excl. onboarding): {len(sec_df):,}")

    # merge_asof to find last sec event before each transaction
    tx_sorted = df_tx.sort_values('ts_dt').reset_index(drop=True)
    merged = pd.merge_asof(
        tx_sorted[['CUSTOMER_NUMBER', 'ts_dt', 'tx_id', 'TRANS_AMOUNT', 'TRANS_LV2']],
        sec_df[['CUSTOMER_NUMBER', 'ts_dt', 'sec_event_ts']],
        on='ts_dt',
        by='CUSTOMER_NUMBER',
        direction='backward'
    )
    merged['HOURS_SINCE_SEC'] = (merged['ts_dt'] - merged['sec_event_ts']).dt.total_seconds() / 3600
    merged['HOURS_SINCE_SEC'] = merged['HOURS_SINCE_SEC'].fillna(999.0)

    # Distribution of HOURS_SINCE_SEC
    has_sec = merged['HOURS_SINCE_SEC'] < 999
    n_with_sec = has_sec.sum()
    print(f"  Transactions with a prior sec event: {n_with_sec:,} ({n_with_sec/total*100:.2f}%)")

    # ATO Panic: HOURS_SINCE_SEC < 1h AND TRANS_AMOUNT > 10M AND Outside_bank
    is_outside = merged['TRANS_LV2'].str.contains('Outside', case=False, na=False)
    
    for hours_thresh in [0.5, 1.0, 2.0, 4.0]:
        for amount_thresh in [5_000_000, 10_000_000, 20_000_000, 50_000_000]:
            mask = (merged['HOURS_SINCE_SEC'] < hours_thresh) & (merged['TRANS_AMOUNT'] > amount_thresh) & is_outside
            n = mask.sum()
            print(f"  ATO: <{hours_thresh}h + >{amount_thresh/1e6:.0f}M + Outside: {n:,}")

    # The most balanced combo
    ato_key_mask = (merged['HOURS_SINCE_SEC'] < 1.0) & (merged['TRANS_AMOUNT'] > 10_000_000) & is_outside
    n_ato = ato_key_mask.sum()
    results['ato_panic_exact'] = {
        '<1h + >10M + Outside': int(n_ato),
        'pct': round(n_ato/total*100, 4)
    }

    # ========================================================================
    # 2. DAYS_SINCE_LAST_TRANS (dormancy) × Channel × Amount
    # ========================================================================
    print("\n" + "="*60)
    print("2. DORMANCY WAKE-UP (DAYS_SINCE_LAST_TRANS)")
    print("="*60)

    df_tx_sorted = df_tx.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
    df_tx_sorted['DAYS_SINCE_LAST'] = df_tx_sorted.groupby('CUSTOMER_NUMBER')['ts_dt'].diff().dt.total_seconds() / 86400

    # For first transaction, compute from CLIENT_CREATE_DATE
    client_query = "SELECT CUSTOMER_NUMBER, CLIENT_CREATE_DATE, IB_REGISTER_DATE FROM Data_Customer"
    client_df = pd.read_sql_query(client_query, conn)
    client_df['reg_dt'] = pd.to_datetime(client_df['IB_REGISTER_DATE'], errors='coerce').fillna(
        pd.to_datetime(client_df['CLIENT_CREATE_DATE'], errors='coerce')
    )
    reg_map = dict(zip(client_df['CUSTOMER_NUMBER'], client_df['reg_dt']))
    
    first_mask = df_tx_sorted['DAYS_SINCE_LAST'].isna()
    for idx in df_tx_sorted[first_mask].index:
        cust = df_tx_sorted.at[idx, 'CUSTOMER_NUMBER']
        reg = reg_map.get(cust)
        if reg is not None and pd.notna(reg):
            df_tx_sorted.at[idx, 'DAYS_SINCE_LAST'] = (df_tx_sorted.at[idx, 'ts_dt'] - reg).total_seconds() / 86400
        else:
            df_tx_sorted.at[idx, 'DAYS_SINCE_LAST'] = 999.0
    df_tx_sorted['DAYS_SINCE_LAST'] = df_tx_sorted['DAYS_SINCE_LAST'].fillna(999.0)

    is_outside_sorted = df_tx_sorted['TRANS_LV2'].str.contains('Outside', case=False, na=False)

    for dormancy_thresh in [30, 60, 90, 180]:
        for amount_thresh in [5_000_000, 10_000_000, 20_000_000]:
            mask = (df_tx_sorted['DAYS_SINCE_LAST'] > dormancy_thresh) & \
                   (df_tx_sorted['TRANS_AMOUNT'] > amount_thresh) & is_outside_sorted
            n = mask.sum()
            print(f"  Dormancy >{dormancy_thresh}d + >{amount_thresh/1e6:.0f}M + Outside: {n:,}")

    dormancy_key = (df_tx_sorted['DAYS_SINCE_LAST'] > 90) & (df_tx_sorted['TRANS_AMOUNT'] > 10_000_000) & is_outside_sorted
    results['dormancy_exact'] = {
        '>90d + >10M + Outside': int(dormancy_key.sum()),
        'pct': round(dormancy_key.sum()/total*100, 4)
    }

    # ========================================================================
    # 3. Low-Risk Channel Bypass Analysis  
    # ========================================================================
    print("\n" + "="*60)
    print("3. LOW-RISK CHANNEL BYPASS")
    print("="*60)

    low_risk_channels = ['Credit_card_repayment', 'Utilities_payment', 'Insurance_payment', 
                         'Lending_repayment', 'Cable', 'Lifestyle_payment', 'Game', 'MCPP']
    
    for channel in low_risk_channels:
        ch_mask = df_tx['TRANS_LV2'] == channel
        n_ch = ch_mask.sum()
        if n_ch == 0:
            continue
        amounts = df_tx.loc[ch_mask, 'TRANS_AMOUNT']
        print(f"\n  {channel}: {n_ch:,} transactions")
        print(f"    Mean: {amounts.mean():,.0f} | Median: {amounts.median():,.0f}")
        print(f"    P90: {amounts.quantile(0.90):,.0f} | P95: {amounts.quantile(0.95):,.0f} | Max: {amounts.max():,.0f}")
        
        for thresh in [2_000_000, 5_000_000, 10_000_000]:
            n_below = (amounts < thresh).sum()
            print(f"    < {thresh/1e6:.0f}M: {n_below:,} ({n_below/n_ch*100:.1f}%)")

    # Combined low-risk bypass
    is_low_risk = df_tx['TRANS_LV2'].isin(low_risk_channels)
    n_low_risk = is_low_risk.sum()
    
    # Also add Topup channels (Mobile, eWallet) which are mostly small
    topup_channels = ['Mobile', 'eWallet', 'QR_payment']
    is_topup = df_tx['TRANS_LV2'].isin(topup_channels)
    n_topup = is_topup.sum()
    
    for thresh in [1_000_000, 2_000_000, 5_000_000, 10_000_000]:
        n_lr = (is_low_risk & (df_tx['TRANS_AMOUNT'] < thresh)).sum()
        n_tp = (is_topup & (df_tx['TRANS_AMOUNT'] < thresh)).sum()
        n_combined = n_lr + n_tp
        print(f"\n  Low-risk channels <{thresh/1e6:.0f}M: {n_lr:,} | Topup channels <{thresh/1e6:.0f}M: {n_tp:,} | Total: {n_combined:,} ({n_combined/total*100:.2f}%)")

    results['low_risk_bypass'] = {
        'low_risk_channel_total': int(n_low_risk),
        'topup_channel_total': int(n_topup)
    }

    # ========================================================================
    # 4. AUTH_DOWNGRADE_RISK analysis (from loader feature)
    # ========================================================================
    print("\n" + "="*60)
    print("4. AUTH DOWNGRADE (Biometric -> Password on New Device)")
    print("="*60)
    
    login_query = """
        SELECT CUSTOMER_NUMBER, ACTIVITY_NAME, COUNT(*) as cnt
        FROM Data_Activity
        WHERE ACTIVITY_NAME IN ('LOGIN', 'LOGIN_FINGER', 'LOGIN_FACEID')
        GROUP BY CUSTOMER_NUMBER, ACTIVITY_NAME
    """
    login_df = pd.read_sql_query(login_query, conn)
    login_pivot = login_df.pivot_table(index='CUSTOMER_NUMBER', columns='ACTIVITY_NAME', values='cnt', fill_value=0)
    
    bio_cols = [c for c in login_pivot.columns if c in ('LOGIN_FINGER', 'LOGIN_FACEID')]
    if bio_cols:
        login_pivot['total_bio'] = login_pivot[bio_cols].sum(axis=1)
        login_pivot['total_all'] = login_pivot.sum(axis=1)
        login_pivot['bio_ratio'] = login_pivot['total_bio'] / login_pivot['total_all']
        
        n_bio_users = (login_pivot['bio_ratio'] > 0.05).sum()
        n_high_bio = (login_pivot['bio_ratio'] > 0.5).sum()
        total_customers = len(login_pivot)
        
        print(f"  Total customers with login events: {total_customers:,}")
        print(f"  Customers using biometric >5%: {n_bio_users:,} ({n_bio_users/total_customers*100:.2f}%)")
        print(f"  Customers using biometric >50%: {n_high_bio:,} ({n_high_bio/total_customers*100:.2f}%)")
        
        results['auth_downgrade'] = {
            'total_customers': int(total_customers),
            'bio_gt_5pct': int(n_bio_users),
            'bio_gt_50pct': int(n_high_bio)
        }
    else:
        print("  No biometric login data found.")
        results['auth_downgrade'] = {'note': 'No biometric login data'}

    # ========================================================================
    # 5. IP_HOPPING_VELOCITY analysis
    # ========================================================================
    print("\n" + "="*60)
    print("5. IP HOPPING VELOCITY")
    print("="*60)
    
    ip_query = """
        SELECT Device_ID_Hash, IP_Address_Proxy, COUNT(*) as cnt,
               COUNT(DISTINCT IP_Address_Proxy) as unique_ips
        FROM Data_Transaction
        WHERE Device_ID_Hash IS NOT NULL AND Device_ID_Hash != ''
        GROUP BY Device_ID_Hash
    """
    ip_df = pd.read_sql_query(ip_query, conn)
    n_devices = len(ip_df)
    multi_ip = (ip_df['unique_ips'] >= 2).sum()
    many_ip = (ip_df['unique_ips'] >= 3).sum()
    print(f"  Total unique devices: {n_devices:,}")
    print(f"  Devices with >= 2 unique IPs: {multi_ip:,} ({multi_ip/n_devices*100:.2f}%)")
    print(f"  Devices with >= 3 unique IPs: {many_ip:,} ({many_ip/n_devices*100:.2f}%)")
    
    results['ip_hopping'] = {
        'total_devices': int(n_devices),
        'devices_gte2_ips': int(multi_ip),
        'devices_gte3_ips': int(many_ip)
    }

    # ========================================================================
    # 6. STRUCTURING_OVERPAYMENT analysis
    # ========================================================================
    print("\n" + "="*60)
    print("6. STRUCTURING OVERPAYMENT (Credit Card)")
    print("="*60)
    
    cc_repay = df_tx[df_tx['TRANS_LV2'] == 'Credit_card_repayment']
    n_cc = len(cc_repay)
    print(f"  Total credit card repayment transactions: {n_cc:,}")
    
    # Check how many customers have multiple repayments
    cc_grouped = cc_repay.groupby('CUSTOMER_NUMBER').agg(
        repay_count=('TRANS_AMOUNT', 'count'),
        total_repaid=('TRANS_AMOUNT', 'sum')
    )
    multi_repay = (cc_grouped['repay_count'] >= 2).sum()
    heavy_repay = (cc_grouped['repay_count'] >= 5).sum()
    print(f"  Customers with >= 2 repayments: {multi_repay:,}")
    print(f"  Customers with >= 5 repayments: {heavy_repay:,}")
    
    # Check outstanding balance
    card_query = """
        SELECT CUSTOMER_NUMBER, MAX(OUTSTANDING_BAL_CREDIT) as max_outstanding, 
               MAX(LIMIT_AMT_CREDIT) as max_limit
        FROM Data_Card
        WHERE OUTSTANDING_BAL_CREDIT IS NOT NULL
        GROUP BY CUSTOMER_NUMBER
    """
    card_df = pd.read_sql_query(card_query, conn)
    card_df['max_outstanding'] = pd.to_numeric(card_df['max_outstanding'], errors='coerce').fillna(0)
    
    # Join to check overpayment
    cc_vs_balance = cc_grouped.merge(card_df, on='CUSTOMER_NUMBER', how='left')
    cc_vs_balance['max_outstanding'] = cc_vs_balance['max_outstanding'].fillna(0)
    overpayers = cc_vs_balance[cc_vs_balance['total_repaid'] > cc_vs_balance['max_outstanding']]
    n_overpay = len(overpayers)
    print(f"  Customers who repaid more than outstanding: {n_overpay:,}")
    
    results['structuring_overpayment'] = {
        'cc_repayment_total': int(n_cc),
        'multi_repay_customers': int(multi_repay),
        'overpaying_customers': int(n_overpay)
    }

    # ========================================================================
    # 7. BUST_OUT_UTILIZATION analysis
    # ========================================================================
    print("\n" + "="*60)
    print("7. BUST-OUT UTILIZATION (Credit Card)")
    print("="*60)
    
    bust_query = """
        SELECT CUSTOMER_NUMBER, LIMIT_AMT_CREDIT, OUTSTANDING_BAL_CREDIT
        FROM Data_Card
        WHERE LIMIT_AMT_CREDIT > 0
    """
    bust_df = pd.read_sql_query(bust_query, conn)
    bust_df['LIMIT_AMT_CREDIT'] = pd.to_numeric(bust_df['LIMIT_AMT_CREDIT'], errors='coerce').fillna(0)
    bust_df['OUTSTANDING_BAL_CREDIT'] = pd.to_numeric(bust_df['OUTSTANDING_BAL_CREDIT'], errors='coerce').fillna(0)
    bust_df = bust_df[bust_df['LIMIT_AMT_CREDIT'] > 0]
    bust_df['utilization'] = bust_df['OUTSTANDING_BAL_CREDIT'] / bust_df['LIMIT_AMT_CREDIT']
    
    max_util = bust_df.groupby('CUSTOMER_NUMBER')['utilization'].max()
    print(f"  Customers with credit card data: {len(max_util):,}")
    for thresh in [0.5, 0.8, 0.9, 0.95, 1.0]:
        n = (max_util >= thresh).sum()
        print(f"  Max utilization >= {thresh:.0%}: {n:,} ({n/len(max_util)*100:.2f}%)")
    
    results['bust_out'] = {
        'total_customers': int(len(max_util)),
        'util_gte_80': int((max_util >= 0.8).sum()),
        'util_gte_95': int((max_util >= 0.95).sum())
    }

    # ========================================================================
    # 8. Combined: existing bypass % vs proposed new rules
    # ========================================================================
    print("\n" + "="*60)
    print("8. COMBINED BYPASS RATE ESTIMATION")
    print("="*60)
    
    # Current rules
    count_1h_query = """
        SELECT CUSTOMER_NUMBER, TRANS_AMOUNT,
               COUNT(*) OVER (PARTITION BY CUSTOMER_NUMBER ORDER BY (julianday(TRANS_DATE) + (TRANS_HOUR / 24.0)) RANGE BETWEEN 1.0/24.0 PRECEDING AND CURRENT ROW) as COUNT_1H,
               COUNT(*) OVER (PARTITION BY CUSTOMER_NUMBER ORDER BY (julianday(TRANS_DATE) + (TRANS_HOUR / 24.0)) RANGE BETWEEN 1.0 PRECEDING AND CURRENT ROW) as COUNT_24H,
               TRANS_LV2
        FROM Data_Transaction
    """
    vel_df = pd.read_sql_query(count_1h_query, conn)
    vel_df['TRANS_AMOUNT'] = pd.to_numeric(vel_df['TRANS_AMOUNT'], errors='coerce').fillna(0)
    
    # Current Rule 1 upper bound (Amount < 500K)
    r1 = vel_df['TRANS_AMOUNT'] < 500000
    # Current Rule 2 (Velocity)
    r2 = r1 & (vel_df['COUNT_1H'] <= 1) & (vel_df['COUNT_24H'] <= 2)
    
    # New bypass: Low-risk channels < 10M
    low_risk_all = ['Credit_card_repayment', 'Utilities_payment', 'Insurance_payment', 
                    'Lending_repayment', 'Cable', 'Lifestyle_payment', 'Game', 'MCPP',
                    'Mobile', 'eWallet', 'QR_payment']
    r_new_bypass = vel_df['TRANS_LV2'].isin(low_risk_all) & (vel_df['TRANS_AMOUNT'] < 10_000_000)
    
    combined_bypass = r1 | r_new_bypass
    
    n_r1 = r1.sum()
    n_new = r_new_bypass.sum()
    n_new_only = (r_new_bypass & ~r1).sum()  # new additions not already caught by amount rule
    n_combined = combined_bypass.sum()
    
    print(f"  Current Rule 1 (Amount < 500K): {n_r1:,} ({n_r1/total*100:.2f}%)")
    print(f"  New Low-Risk Channel Bypass (<10M): {n_new:,} ({n_new/total*100:.2f}%)")
    print(f"  NEW additions (not already in Rule 1): {n_new_only:,} ({n_new_only/total*100:.2f}%)")
    print(f"  Combined Bypass (Rule1 + New): {n_combined:,} ({n_combined/total*100:.2f}%)")
    print(f"  Remaining for ML: {total - n_combined:,} ({(total-n_combined)/total*100:.2f}%)")

    results['combined_bypass'] = {
        'current_rule1': int(n_r1),
        'current_rule1_pct': round(n_r1/total*100, 2),
        'new_channel_bypass': int(n_new),
        'new_additions': int(n_new_only),
        'combined_total': int(n_combined),
        'combined_pct': round(n_combined/total*100, 2),
        'remaining_for_ml': int(total - n_combined),
        'remaining_pct': round((total-n_combined)/total*100, 2)
    }

    # Save
    output_path = os.path.join(OUTPUT_DIR, "rule_deep_eda_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")
    conn.close()

if __name__ == '__main__':
    main()
