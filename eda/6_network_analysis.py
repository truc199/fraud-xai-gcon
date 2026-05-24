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

def run_network_analysis():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_FILE)
    
    query = """
        SELECT 
            CUSTOMER_NUMBER,
            TRANS_DATE,
            TRANS_HOUR,
            TRANS_AMOUNT,
            Device_ID_Hash,
            Beneficiary_CUSTOMER_NUMBER
        FROM Data_Transaction
    """
    
    print("Loading transaction logs into memory...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} transactions. Processing timestamps...")
    df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
    df['tx_id'] = df.index
    
    # 1. Device Sharing Analysis (Shared Hardware)
    print("Analyzing shared hardware / device hubs...")
    # Filter out missing or invalid device hashes
    valid_devices = df[df['Device_ID_Hash'].notna() & (~df['Device_ID_Hash'].isin(['NaN', 'nan', 'UNKNOWN', '', 'None']))]
    
    # Map device to unique customer count
    device_cust_counts = valid_devices.groupby('Device_ID_Hash')['CUSTOMER_NUMBER'].nunique().to_dict()
    device_tx_counts = valid_devices.groupby('Device_ID_Hash')['tx_id'].count().to_dict()
    
    df['DEVICE_TOTAL_DISTINCT_CUSTOMERS'] = df['Device_ID_Hash'].map(device_cust_counts).fillna(1).astype(int)
    df['DEVICE_TOTAL_TRANS_COUNT'] = df['Device_ID_Hash'].map(device_tx_counts).fillna(1).astype(int)
    
    # 2. Beneficiary Linkage Analysis (Common Receivers)
    print("Analyzing common beneficiaries...")
    valid_bens = df[df['Beneficiary_CUSTOMER_NUMBER'].notna() & (~df['Beneficiary_CUSTOMER_NUMBER'].isin(['NaN', 'nan', 'UNKNOWN', '', 'None']))]
    
    ben_sender_counts = valid_bens.groupby('Beneficiary_CUSTOMER_NUMBER')['CUSTOMER_NUMBER'].nunique().to_dict()
    ben_tx_counts = valid_bens.groupby('Beneficiary_CUSTOMER_NUMBER')['tx_id'].count().to_dict()
    ben_amount_sums = valid_bens.groupby('Beneficiary_CUSTOMER_NUMBER')['TRANS_AMOUNT'].sum().to_dict()
    
    df['BENEFICIARY_TOTAL_DISTINCT_SENDERS'] = df['Beneficiary_CUSTOMER_NUMBER'].map(ben_sender_counts).fillna(1).astype(int)
    df['BENEFICIARY_TOTAL_TRANS_COUNT'] = df['Beneficiary_CUSTOMER_NUMBER'].map(ben_tx_counts).fillna(1).astype(int)
    df['BENEFICIARY_TOTAL_AMOUNT'] = df['Beneficiary_CUSTOMER_NUMBER'].map(ben_amount_sums).fillna(0.0).astype(float)
    
    # Flags for network anomalies
    df['IS_SHARED_DEVICE_ALERT'] = (df['DEVICE_TOTAL_DISTINCT_CUSTOMERS'] >= 3).astype(int)
    df['IS_COMMON_RECEIVER_ALERT'] = (df['BENEFICIARY_TOTAL_DISTINCT_SENDERS'] >= 3).astype(int)
    
    # Generate statistics
    print("Generating distribution statistics...")
    stats = {
        'shared_devices': {
            'max_customers_per_device': int(df['DEVICE_TOTAL_DISTINCT_CUSTOMERS'].max()),
            'p90_customers_per_device': float(df['DEVICE_TOTAL_DISTINCT_CUSTOMERS'].quantile(0.90)),
            'p95_customers_per_device': float(df['DEVICE_TOTAL_DISTINCT_CUSTOMERS'].quantile(0.95)),
            'p99_customers_per_device': float(df['DEVICE_TOTAL_DISTINCT_CUSTOMERS'].quantile(0.99)),
            'transactions_on_shared_devices_ge3': int(df['IS_SHARED_DEVICE_ALERT'].sum())
        },
        'common_receivers': {
            'max_senders_per_beneficiary': int(df['BENEFICIARY_TOTAL_DISTINCT_SENDERS'].max()),
            'p90_senders_per_beneficiary': float(df['BENEFICIARY_TOTAL_DISTINCT_SENDERS'].quantile(0.90)),
            'p95_senders_per_beneficiary': float(df['BENEFICIARY_TOTAL_DISTINCT_SENDERS'].quantile(0.95)),
            'p99_senders_per_beneficiary': float(df['BENEFICIARY_TOTAL_DISTINCT_SENDERS'].quantile(0.99)),
            'transactions_to_common_receivers_ge3': int(df['IS_COMMON_RECEIVER_ALERT'].sum())
        }
    }
    
    # Save statistics JSON
    stats_file = os.path.join(OUTPUTS_DIR, "network_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved statistics to {stats_file}")
    
    # Persist full aggregated output
    output_csv = os.path.join(OUTPUTS_DIR, "customer_network_features.csv.gz")
    print(f"Saving full compressed network data to {output_csv}...")
    df.to_csv(output_csv, index=False, compression='gzip')
    print("Full data persisted.")
    
    # Save top anomalies (sorted by risk factors)
    df['risk_score'] = (df['IS_SHARED_DEVICE_ALERT'] * 2.0) + (df['IS_COMMON_RECEIVER_ALERT'] * 2.0)
    anomalies = df[df['risk_score'] >= 2.0].sort_values('risk_score', ascending=False)
    
    anomaly_csv = os.path.join(OUTPUTS_DIR, "network_anomalies_top1000.csv")
    print(f"Saving top {len(anomalies[:1000])} network anomalies to {anomaly_csv}...")
    anomalies.head(1000).to_csv(anomaly_csv, index=False)
    print("Anomalies persisted.")
    
    print("\nNetwork analysis completed successfully!")

if __name__ == "__main__":
    run_network_analysis()
