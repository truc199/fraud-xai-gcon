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

def run_spatial_analysis():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_FILE)
    
    query = """
        SELECT 
            CUSTOMER_NUMBER,
            TRANS_DATE,
            TRANS_HOUR,
            TRANS_AMOUNT,
            IP_Address_Proxy,
            Device_ID_Hash
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
    
    # 1. Impossible Travel Detection
    print("Analyzing consecutive transactions for location changes...")
    grouped = df.groupby('CUSTOMER_NUMBER')
    
    df['prev_ip'] = grouped['IP_Address_Proxy'].shift(1)
    df['prev_ts'] = grouped['ts_dt'].shift(1)
    
    # Clean string column to ensure comparison is robust
    df['IP_Address_Proxy'] = df['IP_Address_Proxy'].fillna('UNKNOWN').astype(str).str.strip().str.upper()
    df['prev_ip'] = df['prev_ip'].fillna('UNKNOWN').astype(str).str.strip().str.upper()
    
    df['is_ip_changed'] = (
        (df['IP_Address_Proxy'] != df['prev_ip']) & 
        (df['IP_Address_Proxy'] != 'UNKNOWN') & 
        (df['prev_ip'] != 'UNKNOWN')
    ).astype(int)
    
    df['time_diff_hours'] = (df['ts_dt'] - df['prev_ts']).dt.total_seconds() / 3600
    
    # Flag impossible travel: location changes and time gap < 1 hour
    df['IS_IMPOSSIBLE_TRAVEL'] = (
        (df['is_ip_changed'] == 1) & 
        (df['time_diff_hours'] < 1.0)
    ).astype(int)
    
    # 2. First-Time Location Outliers
    print("Analyzing first-time location usage per customer...")
    # Cumulative count of each specific IP per customer
    df['ip_cum_count'] = df.groupby(['CUSTOMER_NUMBER', 'IP_Address_Proxy']).cumcount()
    # Total historical transactions of this customer
    df['cum_tx_count'] = grouped.cumcount()
    
    # Flag new location: first time using this IP, and it is not their first ever transaction
    df['IS_NEW_LOCATION'] = (
        (df['ip_cum_count'] == 0) & 
        (df['cum_tx_count'] > 0) & 
        (df['IP_Address_Proxy'] != 'UNKNOWN')
    ).astype(int)
    
    # High-value new location alert (new location + transfer >= 38M)
    df['IS_NEW_LOCATION_HIGH_VALUE'] = (
        (df['IS_NEW_LOCATION'] == 1) & 
        (df['TRANS_AMOUNT'] >= 38000000.0)
    ).astype(int)
    
    # Generate statistics
    print("Generating distribution statistics...")
    stats = {
        'spatial_metrics': {
            'total_impossible_travel_alerts': int(df['IS_IMPOSSIBLE_TRAVEL'].sum()),
            'total_new_location_uses': int(df['IS_NEW_LOCATION'].sum()),
            'total_new_location_high_value_alerts': int(df['IS_NEW_LOCATION_HIGH_VALUE'].sum())
        }
    }
    
    # Save statistics JSON
    stats_file = os.path.join(OUTPUTS_DIR, "spatial_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved statistics to {stats_file}")
    
    # Persist full aggregated output
    output_csv = os.path.join(OUTPUTS_DIR, "customer_spatial_features.csv.gz")
    print(f"Saving full compressed spatial data to {output_csv}...")
    df.to_csv(output_csv, index=False, compression='gzip')
    print("Full data persisted.")
    
    # Save top anomalies
    df['risk_score'] = (df['IS_IMPOSSIBLE_TRAVEL'] * 2.0) + (df['IS_NEW_LOCATION_HIGH_VALUE'] * 2.0)
    anomalies = df[df['risk_score'] >= 2.0].sort_values('risk_score', ascending=False)
    
    anomaly_csv = os.path.join(OUTPUTS_DIR, "spatial_anomalies_top1000.csv")
    print(f"Saving top {len(anomalies[:1000])} spatial anomalies to {anomaly_csv}...")
    anomalies.head(1000).to_csv(anomaly_csv, index=False)
    print("Anomalies persisted.")
    
    print("\nSpatial analysis completed successfully!")

if __name__ == "__main__":
    run_spatial_analysis()
