import os
import sqlite3
import pandas as pd
import numpy as np
import json

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DATA_DIR, "gcontest.db")
EDA_DIR = os.path.join(BASE_DIR, "eda")
OUTPUTS_DIR = os.path.join(EDA_DIR, "outputs")

os.makedirs(OUTPUTS_DIR, exist_ok=True)

def run_context_analysis():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_FILE)
    
    query = """
        SELECT 
            CUSTOMER_NUMBER,
            TRANS_DATE,
            TRANS_HOUR,
            TRANS_AMOUNT,
            TRANS_LV1,
            TRANS_LV2,
            Merchant_ID_Masked
        FROM Data_Transaction
    """
    
    print("Loading transaction logs into memory...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} transactions. Processing timestamps...")
    df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
    df['tx_id'] = df.index
    
    print("Sorting transactions sequentially...")
    df = df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
    
    # Standardize strings
    df['TRANS_LV2'] = df['TRANS_LV2'].fillna('UNKNOWN').astype(str).str.strip()
    df['Merchant_ID_Masked'] = df['Merchant_ID_Masked'].fillna('UNKNOWN').astype(str).str.strip()
    
    # 1. Profile Drift in High-Risk Categories
    print("Analyzing high-risk category usage...")
    high_risk_categories = ['Outside_bank', 'eWallet', 'Game']
    df['is_high_risk_cat'] = df['TRANS_LV2'].isin(high_risk_categories).astype(int)
    
    # Cumulative count of this specific category per customer
    df['cum_cat_count'] = df.groupby(['CUSTOMER_NUMBER', 'TRANS_LV2']).cumcount()
    # Total historical transactions of this customer
    df['cum_tx_count'] = df.groupby('CUSTOMER_NUMBER').cumcount()
    
    # Flag first-time high-risk category usage
    df['IS_FIRST_TIME_HIGH_RISK_CAT'] = (
        (df['is_high_risk_cat'] == 1) & 
        (df['cum_cat_count'] == 0) & 
        (df['cum_tx_count'] > 0)
    ).astype(int)
    
    # Flag first-time high-risk category combined with high value (>= 38M)
    df['IS_FIRST_TIME_HIGH_RISK_HIGH_VAL'] = (
        (df['IS_FIRST_TIME_HIGH_RISK_CAT'] == 1) & 
        (df['TRANS_AMOUNT'] >= 38000000.0)
    ).astype(int)
    
    # 2. Merchant Concentration Profile
    print("Profiling merchant concentrations...")
    valid_merchants = df[~df['Merchant_ID_Masked'].isin(['NaN', 'nan', 'UNKNOWN', '', 'None'])]
    
    merchant_cust_counts = valid_merchants.groupby('Merchant_ID_Masked')['CUSTOMER_NUMBER'].nunique().to_dict()
    merchant_tx_counts = valid_merchants.groupby('Merchant_ID_Masked')['tx_id'].count().to_dict()
    merchant_amount_sums = valid_merchants.groupby('Merchant_ID_Masked')['TRANS_AMOUNT'].sum().to_dict()
    
    df['MERCHANT_TOTAL_DISTINCT_CUSTOMERS'] = df['Merchant_ID_Masked'].map(merchant_cust_counts).fillna(1).astype(int)
    df['MERCHANT_TOTAL_TRANS_COUNT'] = df['Merchant_ID_Masked'].map(merchant_tx_counts).fillna(1).astype(int)
    df['MERCHANT_TOTAL_AMOUNT'] = df['Merchant_ID_Masked'].map(merchant_amount_sums).fillna(0.0).astype(float)
    
    # Generate statistics
    print("Generating distribution statistics...")
    # Get top 5 merchants by unique customer counts
    sorted_merchants = sorted(merchant_cust_counts.items(), key=lambda x: x[1], reverse=True)
    top_5_merchants = {k: {
        'unique_customers': int(v),
        'total_transactions': int(merchant_tx_counts[k]),
        'total_amount': float(merchant_amount_sums[k])
    } for k, v in sorted_merchants[:5]}
    
    stats = {
        'high_risk_categories': {
            'total_first_time_high_risk_uses': int(df['IS_FIRST_TIME_HIGH_RISK_CAT'].sum()),
            'total_first_time_high_risk_high_value_alerts': int(df['IS_FIRST_TIME_HIGH_RISK_HIGH_VAL'].sum())
        },
        'merchant_concentration': {
            'total_unique_merchants': len(merchant_cust_counts),
            'top_5_merchants': top_5_merchants
        }
    }
    
    # Save statistics JSON
    stats_file = os.path.join(OUTPUTS_DIR, "context_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved statistics to {stats_file}")
    
    # Persist full aggregated output
    output_csv = os.path.join(OUTPUTS_DIR, "customer_context_features.csv.gz")
    print(f"Saving full compressed context data to {output_csv}...")
    df.to_csv(output_csv, index=False, compression='gzip')
    print("Full data persisted.")
    
    # Save top anomalies
    df['risk_score'] = (df['IS_FIRST_TIME_HIGH_RISK_HIGH_VAL'] * 2.0) + (df['IS_FIRST_TIME_HIGH_RISK_CAT'] * 0.5)
    anomalies = df[df['risk_score'] >= 2.0].sort_values('risk_score', ascending=False)
    
    anomaly_csv = os.path.join(OUTPUTS_DIR, "context_anomalies_top1000.csv")
    print(f"Saving top {len(anomalies[:1000])} context anomalies to {anomaly_csv}...")
    anomalies.head(1000).to_csv(anomaly_csv, index=False)
    print("Anomalies persisted.")
    
    print("\nContext analysis completed successfully!")

if __name__ == "__main__":
    run_context_analysis()
