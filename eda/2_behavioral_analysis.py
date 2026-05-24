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

def run_behavioral_analysis():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_FILE)
    
    # Query transactions joined with customer profile and monthly deposit aggregates
    query = """
        WITH deposit_agg AS (
            SELECT CUSTOMER_NUMBER, AVG(AVG_CA_BALANCE) as HIST_AVG_CA_BALANCE 
            FROM Data_Deposit GROUP BY CUSTOMER_NUMBER
        )
        SELECT 
            t.CUSTOMER_NUMBER,
            t.TRANS_DATE,
            t.TRANS_HOUR,
            t.TRANS_AMOUNT,
            t.TRANS_LV1,
            t.TRANS_LV2,
            c.IB_REGISTER_DATE,
            c.CLIENT_CREATE_DATE,
            COALESCE(d.HIST_AVG_CA_BALANCE, 0.0) as HIST_AVG_CA_BALANCE
        FROM Data_Transaction t
        LEFT JOIN Data_Customer c ON t.CUSTOMER_NUMBER = c.CUSTOMER_NUMBER
        LEFT JOIN deposit_agg d ON t.CUSTOMER_NUMBER = d.CUSTOMER_NUMBER
    """
    
    print("Loading data into memory...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} transactions. Processing timestamps...")
    df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
    df['IB_REGISTER_DATE'] = pd.to_datetime(df['IB_REGISTER_DATE'], errors='coerce')
    df['CLIENT_CREATE_DATE'] = pd.to_datetime(df['CLIENT_CREATE_DATE'], errors='coerce')
    
    # Sort for sequential calculations
    print("Sorting transactions sequentially...")
    df = df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
    
    # 1. Baseline Deviation
    print("Computing balance coverage ratios...")
    df['BALANCE_COVERAGE_RATIO'] = df['TRANS_AMOUNT'] / (df['HIST_AVG_CA_BALANCE'] + 1e-5)
    
    # 2. Dormancy Wake-up
    print("Tracking time gaps since last transaction...")
    grouped = df.groupby('CUSTOMER_NUMBER')
    
    # Compute days since last transaction
    df['DAYS_SINCE_LAST_TRANS'] = grouped['ts_dt'].diff().dt.total_seconds() / (24 * 3600)
    
    # For the first transaction, use days since IB registration or CIF creation
    reg_date = df['IB_REGISTER_DATE'].fillna(df['CLIENT_CREATE_DATE'])
    df['DAYS_SINCE_REG'] = (df['ts_dt'] - reg_date).dt.total_seconds() / (24 * 3600)
    df['DAYS_SINCE_LAST_TRANS'] = df['DAYS_SINCE_LAST_TRANS'].fillna(df['DAYS_SINCE_REG']).fillna(999.0)
    
    # Flag dormancy wakeup: Gap >= 90 days, transaction count >= 1 (or 0 but registered long ago), and large amount
    df['cum_total_count'] = grouped.cumcount()
    df['IS_DORMANT_WAKEUP'] = (
        (df['DAYS_SINCE_LAST_TRANS'] >= 90.0) & 
        (df['TRANS_AMOUNT'] >= 10000000.0)
    ).astype(int)
    
    # 3. Anomalous Times
    print("Analyzing transaction hours and profile deviations...")
    # Define night hours: 12 AM - 5 AM
    df['IS_LATE_NIGHT'] = ((df['TRANS_HOUR'] >= 0) & (df['TRANS_HOUR'] <= 5)).astype(int)
    
    # Compute historical night transaction ratio prior to the current transaction
    df['cum_night_count'] = grouped['IS_LATE_NIGHT'].cumsum() - df['IS_LATE_NIGHT']
    df['cum_night_ratio'] = df['cum_night_count'] / (df['cum_total_count'] + 1e-5)
    
    # Flag anomalous time: transaction is at night, user has transacted at least 3 times before, but night ratio is < 5%
    df['IS_ANOMALOUS_TIME_ALERT'] = (
        (df['IS_LATE_NIGHT'] == 1) & 
        (df['cum_total_count'] >= 3) & 
        (df['cum_night_ratio'] < 0.05) &
        (df['TRANS_AMOUNT'] >= 5000000.0) # High-value filter to avoid micro-charge noise
    ).astype(int)
    
    # Summary calculations
    print("Generating distribution statistics...")
    stats = {
        'BALANCE_COVERAGE_RATIO': {
            'mean': float(df['BALANCE_COVERAGE_RATIO'].mean()),
            'p50': float(df['BALANCE_COVERAGE_RATIO'].quantile(0.50)),
            'p90': float(df['BALANCE_COVERAGE_RATIO'].quantile(0.90)),
            'p95': float(df['BALANCE_COVERAGE_RATIO'].quantile(0.95)),
            'p99': float(df['BALANCE_COVERAGE_RATIO'].quantile(0.99)),
            'max': float(df['BALANCE_COVERAGE_RATIO'].max())
        },
        'DAYS_SINCE_LAST_TRANS': {
            'mean': float(df['DAYS_SINCE_LAST_TRANS'].mean()),
            'p50': float(df['DAYS_SINCE_LAST_TRANS'].quantile(0.50)),
            'p90': float(df['DAYS_SINCE_LAST_TRANS'].quantile(0.90)),
            'p95': float(df['DAYS_SINCE_LAST_TRANS'].quantile(0.95)),
            'p99': float(df['DAYS_SINCE_LAST_TRANS'].quantile(0.99)),
            'max': float(df['DAYS_SINCE_LAST_TRANS'].max())
        },
        'counts': {
            'total_transactions': int(len(df)),
            'dormant_wakeups': int(df['IS_DORMANT_WAKEUP'].sum()),
            'late_night_transactions': int(df['IS_LATE_NIGHT'].sum()),
            'anomalous_time_alerts': int(df['IS_ANOMALOUS_TIME_ALERT'].sum())
        }
    }
    
    # Save statistics JSON
    stats_file = os.path.join(OUTPUTS_DIR, "behavioral_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved statistics to {stats_file}")
    
    # Persist full aggregated output
    output_csv = os.path.join(OUTPUTS_DIR, "customer_behavioral_deviations.csv.gz")
    print(f"Saving full compressed behavioral data to {output_csv}...")
    df.to_csv(output_csv, index=False, compression='gzip')
    print("Full data persisted.")
    
    # Save top anomalies (sorted by risk factors)
    df['risk_score'] = (df['IS_DORMANT_WAKEUP'] * 2.0) + (df['IS_ANOMALOUS_TIME_ALERT'] * 2.0) + (df['BALANCE_COVERAGE_RATIO'].clip(upper=10) / 10.0)
    anomalies = df[df['risk_score'] >= 1.0].sort_values('risk_score', ascending=False)
    
    anomaly_csv = os.path.join(OUTPUTS_DIR, "behavioral_anomalies_top1000.csv")
    print(f"Saving top {len(anomalies[:1000])} behavioral anomalies to {anomaly_csv}...")
    anomalies.head(1000).to_csv(anomaly_csv, index=False)
    print("Anomalies persisted.")
    
    print("\nBehavioral analysis completed successfully!")

if __name__ == "__main__":
    run_behavioral_analysis()
