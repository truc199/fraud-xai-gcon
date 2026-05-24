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

def run_device_analysis():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_FILE)
    
    query = """
        SELECT 
            CUSTOMER_NUMBER,
            TRANS_DATE,
            TRANS_HOUR,
            TRANS_AMOUNT,
            Device_OS
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
    
    # Standardize OS labels
    df['Device_OS'] = df['Device_OS'].fillna('UNKNOWN').astype(str).str.strip().str.upper()
    
    # 1. Device OS Drift Detection
    print("Analyzing consecutive transactions for OS shifts...")
    grouped = df.groupby('CUSTOMER_NUMBER')
    
    df['prev_os'] = grouped['Device_OS'].shift(1)
    df['prev_ts'] = grouped['ts_dt'].shift(1)
    df['prev_os'] = df['prev_os'].fillna('UNKNOWN').astype(str).str.strip().str.upper()
    
    df['is_os_changed'] = (
        (df['Device_OS'] != df['prev_os']) & 
        (df['Device_OS'] != 'UNKNOWN') & 
        (df['prev_os'] != 'UNKNOWN')
    ).astype(int)
    
    df['time_diff_hours'] = (df['ts_dt'] - df['prev_ts']).dt.total_seconds() / 3600
    
    # Flag OS Drift: OS changes and time gap < 24 hours
    df['IS_OS_DRIFT'] = (
        (df['is_os_changed'] == 1) & 
        (df['time_diff_hours'] < 24.0)
    ).astype(int)
    
    # 2. Rare OS Profiling
    print("Profiling global OS frequency...")
    os_counts = df['Device_OS'].value_counts()
    os_freq = df['Device_OS'].value_counts(normalize=True).to_dict()
    
    # Flag rare OS: relative frequency < 0.1% (excluding UNKNOWN)
    rare_os_list = [k for k, v in os_freq.items() if v < 0.001 and k != 'UNKNOWN']
    df['IS_RARE_OS'] = df['Device_OS'].isin(rare_os_list).astype(int)
    
    # Generate statistics
    print("Generating distribution statistics...")
    stats = {
        'device_metrics': {
            'total_os_drift_alerts': int(df['IS_OS_DRIFT'].sum()),
            'total_rare_os_transactions': int(df['IS_RARE_OS'].sum()),
            'global_os_distribution': {k: float(v) for k, v in os_freq.items()},
            'rare_os_detected': rare_os_list
        }
    }
    
    # Save statistics JSON
    stats_file = os.path.join(OUTPUTS_DIR, "device_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved statistics to {stats_file}")
    
    # Persist full aggregated output
    output_csv = os.path.join(OUTPUTS_DIR, "customer_device_features.csv.gz")
    print(f"Saving full compressed device data to {output_csv}...")
    df.to_csv(output_csv, index=False, compression='gzip')
    print("Full data persisted.")
    
    # Save top anomalies
    df['risk_score'] = (df['IS_OS_DRIFT'] * 2.0) + (df['IS_RARE_OS'] * 2.0)
    anomalies = df[df['risk_score'] >= 2.0].sort_values('risk_score', ascending=False)
    
    anomaly_csv = os.path.join(OUTPUTS_DIR, "device_anomalies_top1000.csv")
    print(f"Saving top {len(anomalies[:1000])} device anomalies to {anomaly_csv}...")
    anomalies.head(1000).to_csv(anomaly_csv, index=False)
    print("Anomalies persisted.")
    
    print("\nDevice analysis completed successfully!")

if __name__ == "__main__":
    run_device_analysis()
