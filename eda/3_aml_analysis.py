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

def is_structured_amt(amount):
    # Standard banking AML threshold levels
    thresholds = [50000000.0, 100000000.0, 200000000.0, 500000000.0]
    for t in thresholds:
        if 0.90 * t <= amount < t:
            return 1
    return 0

def compute_rolling_unique_beneficiaries(df):
    print("Calculating rolling unique beneficiaries (24h) per customer...")
    # Group by customer and compute unique beneficiaries in the last 24h using a sliding window
    unique_counts = np.zeros(len(df), dtype=int)
    
    # We will process each customer group
    grouped = df.groupby('CUSTOMER_NUMBER')
    
    for cust, group in grouped:
        times = group['ts_dt'].values
        # Ensure it is string or hashable, replace NaN
        bens = group['Beneficiary_CUSTOMER_NUMBER'].fillna('UNKNOWN').astype(str).values
        indices = group.index.values
        
        start_idx = 0
        active_bens = {}
        
        for i in range(len(group)):
            current_time = times[i]
            b = bens[i]
            
            # Skip 'UNKNOWN' or 'NaN' in counting distinct beneficiaries if desired,
            # but usually we treat them as distinct or just group them.
            # Let's count them unless they are UNKNOWN/NaN
            if b not in ['UNKNOWN', 'NaN', 'nan']:
                active_bens[b] = active_bens.get(b, 0) + 1
            
            # Remove elements older than 24 hours
            limit_time = current_time - np.timedelta64(24, 'h')
            while times[start_idx] < limit_time:
                old_b = bens[start_idx]
                if old_b not in ['UNKNOWN', 'NaN', 'nan']:
                    active_bens[old_b] -= 1
                    if active_bens[old_b] == 0:
                        del active_bens[old_b]
                start_idx += 1
                
            unique_counts[indices[i]] = len(active_bens)
            
    return unique_counts

def run_aml_analysis():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_FILE)
    
    query = """
        SELECT 
            CUSTOMER_NUMBER,
            TRANS_DATE,
            TRANS_HOUR,
            TRANS_AMOUNT,
            Beneficiary_CUSTOMER_NUMBER,
            TRANS_LV1,
            TRANS_LV2
        FROM Data_Transaction
    """
    
    print("Loading transaction logs into memory...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} transactions. Processing timestamps...")
    df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
    
    # Sort for rolling calculation
    print("Sorting transactions sequentially...")
    df = df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
    
    # 1. Structuring (Smurfing) Analysis
    print("Analyzing structuring / smurfing attempts...")
    df['IS_STRUCTURED_AMT'] = df['TRANS_AMOUNT'].apply(is_structured_amt)
    
    df_indexed = df.set_index('ts_dt')
    df['STRUCTURING_24H_COUNT'] = df_indexed.groupby('CUSTOMER_NUMBER')['IS_STRUCTURED_AMT'].rolling('24h').sum().values
    
    # Flag structuring alert: at least 2 structured transactions within 24 hours
    df['IS_STRUCTURING_ALERT'] = (df['STRUCTURING_24H_COUNT'] >= 2).astype(int)
    
    # 2. Mule Account Outflow Fan-out Analysis
    # Since all beneficiaries are external and 100% of transactions in Data_Transaction are outbound,
    # we analyze the outbound fan-out to distinct beneficiaries in 24 hours.
    df['UNIQUE_BENEFICIARIES_24H'] = compute_rolling_unique_beneficiaries(df)
    
    # Also get rolling sum of amount in 24h
    df['SUM_AMOUNT_24H'] = df_indexed.groupby('CUSTOMER_NUMBER')['TRANS_AMOUNT'].rolling('24h').sum().values
    
    # Flag Mule: Sent money to >= 3 unique beneficiaries in 24h, totaling >= 10M
    df['IS_MULE_ALERT'] = (
        (df['UNIQUE_BENEFICIARIES_24H'] >= 3) & 
        (df['SUM_AMOUNT_24H'] >= 10000000.0)
    ).astype(int)
    
    # Summary statistics
    print("Generating distribution statistics...")
    stats = {
        'structuring': {
            'total_structured_transactions': int(df['IS_STRUCTURED_AMT'].sum()),
            'structuring_alerts': int(df['IS_STRUCTURING_ALERT'].sum())
        },
        'mule_fan_out': {
            'total_mule_alerts': int(df['IS_MULE_ALERT'].sum()),
            'max_unique_beneficiaries_24h': int(df['UNIQUE_BENEFICIARIES_24H'].max()),
            'p95_unique_beneficiaries_24h': float(df['UNIQUE_BENEFICIARIES_24H'].quantile(0.95)),
            'p99_unique_beneficiaries_24h': float(df['UNIQUE_BENEFICIARIES_24H'].quantile(0.99))
        }
    }
    
    # Save statistics JSON
    stats_file = os.path.join(OUTPUTS_DIR, "aml_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved statistics to {stats_file}")
    
    # Persist full aggregated output
    output_csv = os.path.join(OUTPUTS_DIR, "customer_aml_features.csv.gz")
    print(f"Saving full compressed AML data to {output_csv}...")
    df.to_csv(output_csv, index=False, compression='gzip')
    print("Full data persisted.")
    
    # Save top anomalies
    df['risk_score'] = (df['IS_STRUCTURING_ALERT'] * 2.0) + (df['IS_MULE_ALERT'] * 2.0)
    anomalies = df[df['risk_score'] >= 2.0].sort_values('risk_score', ascending=False)
    
    anomaly_csv = os.path.join(OUTPUTS_DIR, "aml_anomalies_top1000.csv")
    print(f"Saving top {len(anomalies[:1000])} AML anomalies to {anomaly_csv}...")
    anomalies.head(1000).to_csv(anomaly_csv, index=False)
    print("Anomalies persisted.")
    
    print("\nAML analysis completed successfully!")

if __name__ == "__main__":
    run_aml_analysis()
