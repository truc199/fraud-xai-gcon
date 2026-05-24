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

def run_velocity_analysis():
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
            IP_Address_Proxy,
            Device_ID_Hash
        FROM Data_Transaction
    """
    print("Loading transactions into memory...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} transactions. Processing timestamps...")
    # Convert date and hour to datetime
    df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
    
    # Sort by customer and timestamp to ensure correct rolling calculation
    print("Sorting data by Customer and Timestamp...")
    df = df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
    
    # Set index to datetime for rolling time window calculations
    df_indexed = df.set_index('ts_dt')
    grouped = df_indexed.groupby('CUSTOMER_NUMBER')
    
    windows = ['1h', '3h', '24h', '48h', '7d', '30d']
    print("Calculating rolling window metrics...")
    for window in windows:
        w_upper = window.upper()
        print(f"  Calculating {w_upper} window...")
        
        # Use .values to directly assign, since sorting matches groupby output order
        df[f'SUM_{w_upper}'] = grouped['TRANS_AMOUNT'].rolling(window).sum().values
        df[f'COUNT_{w_upper}'] = grouped['TRANS_AMOUNT'].rolling(window).count().values

    print("Calculating velocity ratios...")
    # Amount ratios
    df['VELOCITY_RATIO_AMOUNT_1H_VS_24H'] = df['SUM_1H'] / (df['SUM_24H'] + 1e-5)
    df['VELOCITY_RATIO_AMOUNT_24H_VS_7D'] = df['SUM_24H'] / (df['SUM_7D'] + 1e-5)
    df['VELOCITY_RATIO_AMOUNT_7D_VS_30D'] = df['SUM_7D'] / (df['SUM_30D'] + 1e-5)
    
    # Count ratios
    df['VELOCITY_RATIO_COUNT_1H_VS_24H'] = df['COUNT_1H'] / (df['COUNT_24H'] + 1e-5)
    df['VELOCITY_RATIO_COUNT_24H_VS_7D'] = df['COUNT_24H'] / (df['COUNT_7D'] + 1e-5)
    df['VELOCITY_RATIO_COUNT_7D_VS_30D'] = df['COUNT_7D'] / (df['COUNT_30D'] + 1e-5)
    
    # Z-scores against monthly baseline
    # If the user transacts, how does this amount compare to their average 30D transaction size?
    # To avoid dividing by zero or single transaction bias:
    df['HIST_AVG_30D_TRANS_AMOUNT'] = df['SUM_30D'] / (df['COUNT_30D'] + 1e-5)
    df['TRANS_AMOUNT_VS_30D_AVG_RATIO'] = df['TRANS_AMOUNT'] / (df['HIST_AVG_30D_TRANS_AMOUNT'] + 1e-5)

    # 1. Profile statistics
    print("Generating distribution statistics...")
    stats = {}
    cols_to_profile = [
        'TRANS_AMOUNT',
        'SUM_1H', 'COUNT_1H',
        'SUM_3H', 'COUNT_3H',
        'SUM_24H', 'COUNT_24H',
        'SUM_48H', 'COUNT_48H',
        'SUM_7D', 'COUNT_7D',
        'SUM_30D', 'COUNT_30D',
        'VELOCITY_RATIO_AMOUNT_1H_VS_24H',
        'VELOCITY_RATIO_AMOUNT_24H_VS_7D',
        'VELOCITY_RATIO_AMOUNT_7D_VS_30D',
        'VELOCITY_RATIO_COUNT_1H_VS_24H',
        'VELOCITY_RATIO_COUNT_24H_VS_7D',
        'VELOCITY_RATIO_COUNT_7D_VS_30D',
        'TRANS_AMOUNT_VS_30D_AVG_RATIO'
    ]
    
    for col in cols_to_profile:
        col_series = df[col]
        stats[col] = {
            'mean': float(col_series.mean()),
            'std': float(col_series.std()),
            'min': float(col_series.min()),
            'p50': float(col_series.percentile(50) if hasattr(col_series, 'percentile') else col_series.quantile(0.50)),
            'p90': float(col_series.quantile(0.90)),
            'p95': float(col_series.quantile(0.95)),
            'p99': float(col_series.quantile(0.99)),
            'p99.9': float(col_series.quantile(0.999)),
            'max': float(col_series.max())
        }

    # Save statistics JSON
    stats_file = os.path.join(OUTPUTS_DIR, "velocity_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved statistics to {stats_file}")

    # 2. Persist full aggregated output using compression (saves space)
    output_csv = os.path.join(OUTPUTS_DIR, "customer_velocity.csv.gz")
    print(f"Saving full compressed velocity data to {output_csv}...")
    df.to_csv(output_csv, index=False, compression='gzip')
    print("Full data persisted.")

    # 3. Filter high-velocity anomalies for review (e.g. 1H amount velocity ratio > 0.9 and SUM_1H > p95)
    p95_sum_1h = stats['SUM_1H']['p95']
    anomalies = df[
        (df['VELOCITY_RATIO_AMOUNT_1H_VS_24H'] >= 0.8) & 
        (df['SUM_1H'] > p95_sum_1h) & 
        (df['COUNT_1H'] > 1)
    ].sort_values('SUM_1H', ascending=False)
    
    anomaly_csv = os.path.join(OUTPUTS_DIR, "velocity_anomalies_top1000.csv")
    print(f"Saving top {len(anomalies[:1000])} velocity anomalies to {anomaly_csv}...")
    anomalies.head(1000).to_csv(anomaly_csv, index=False)
    print("Anomalies persisted.")
    
    print("\nVelocity analysis complete successfully!")

if __name__ == "__main__":
    run_velocity_analysis()
