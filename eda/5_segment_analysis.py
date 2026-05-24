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

def run_segment_analysis():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_FILE)
    
    query = """
        SELECT 
            t.CUSTOMER_NUMBER,
            t.TRANS_DATE,
            t.TRANS_HOUR,
            t.TRANS_AMOUNT,
            t.TRANS_LV1,
            t.TRANS_LV2,
            c.CLIENT_CREATE_DATE,
            c.DATE_OF_BIRTH,
            c.Occupation_Group
        FROM Data_Transaction t
        LEFT JOIN Data_Customer c ON t.CUSTOMER_NUMBER = c.CUSTOMER_NUMBER
    """
    
    print("Loading transaction logs joined with customer profiles...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} transactions. Processing timestamps...")
    df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
    df['CLIENT_CREATE_DATE'] = pd.to_datetime(df['CLIENT_CREATE_DATE'], errors='coerce')
    df['DATE_OF_BIRTH'] = pd.to_datetime(df['DATE_OF_BIRTH'], errors='coerce')
    
    # 1. New Account Activity Gap
    print("Calculating account tenure...")
    df['TENURE_DAYS'] = (df['ts_dt'] - df['CLIENT_CREATE_DATE']).dt.total_seconds() / (24 * 3600)
    df['TENURE_DAYS'] = df['TENURE_DAYS'].fillna(999.0)
    
    df['IS_NEW_ACCOUNT'] = (df['TENURE_DAYS'] <= 7.0).astype(int)
    # Alert if transaction is in the first 7 days and amount is high (>= 50M)
    df['IS_EARLY_ABUSE_ALERT'] = (
        (df['IS_NEW_ACCOUNT'] == 1) & 
        (df['TRANS_AMOUNT'] >= 50000000.0)
    ).astype(int)
    
    # 2. Demographic Risk Factors
    print("Calculating customer age...")
    df['CUSTOMER_AGE'] = (df['ts_dt'] - df['DATE_OF_BIRTH']).dt.total_seconds() / (365.25 * 24 * 3600)
    df['CUSTOMER_AGE'] = df['CUSTOMER_AGE'].fillna(35.0) # median age fallback
    
    # Flag age extremes with high amount transfers (>= 38M, p95 global threshold)
    df['IS_AGE_EXTREME'] = (
        ((df['CUSTOMER_AGE'] < 18.0) | (df['CUSTOMER_AGE'] > 70.0)) & 
        (df['TRANS_AMOUNT'] >= 38000000.0)
    ).astype(int)
    
    # Profile by Occupation Group
    print("Profiling transactions across occupation groups...")
    df['Occupation_Group'] = df['Occupation_Group'].fillna('UNKNOWN').astype(str).str.strip().str.upper()
    
    # Determine the 99th percentile amount for each occupation group to find standard profiles
    occupation_p99 = df.groupby('Occupation_Group')['TRANS_AMOUNT'].quantile(0.99).to_dict()
    
    # Flag if the transaction size is an extreme outlier for the customer's specific occupation
    df['OCCUPATION_P99_THRESHOLD'] = df['Occupation_Group'].map(occupation_p99)
    df['IS_OCCUPATION_OUTLIER'] = (df['TRANS_AMOUNT'] >= df['OCCUPATION_P99_THRESHOLD']).astype(int)
    
    # Specific flag: Low-income segment (Student / Unemployed / Retired) executing large transfers (>= 38M)
    low_income_groups = ['STUDENT', 'UNEMPLOYED', 'RETIRED']
    df['IS_LOW_INCOME_HIGH_VALUE_ALERT'] = (
        df['Occupation_Group'].isin(low_income_groups) & 
        (df['TRANS_AMOUNT'] >= 38000000.0)
    ).astype(int)
    
    # Generate statistics
    print("Generating distribution statistics...")
    stats = {
        'early_lifecycle': {
            'total_new_account_transactions': int(df['IS_NEW_ACCOUNT'].sum()),
            'early_abuse_alerts': int(df['IS_EARLY_ABUSE_ALERT'].sum())
        },
        'demographics': {
            'age_extreme_alerts': int(df['IS_AGE_EXTREME'].sum()),
            'low_income_high_value_alerts': int(df['IS_LOW_INCOME_HIGH_VALUE_ALERT'].sum()),
            'occupation_p99_thresholds': {k: float(v) for k, v in occupation_p99.items()}
        }
    }
    
    # Save statistics JSON
    stats_file = os.path.join(OUTPUTS_DIR, "segment_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved statistics to {stats_file}")
    
    # Persist full aggregated output
    output_csv = os.path.join(OUTPUTS_DIR, "customer_segment_features.csv.gz")
    print(f"Saving full compressed segment data to {output_csv}...")
    df.to_csv(output_csv, index=False, compression='gzip')
    print("Full data persisted.")
    
    # Save top anomalies
    df['risk_score'] = (df['IS_EARLY_ABUSE_ALERT'] * 2.0) + (df['IS_AGE_EXTREME'] * 2.0) + (df['IS_LOW_INCOME_HIGH_VALUE_ALERT'] * 2.0) + (df['IS_OCCUPATION_OUTLIER'] * 1.0)
    anomalies = df[df['risk_score'] >= 1.0].sort_values('risk_score', ascending=False)
    
    anomaly_csv = os.path.join(OUTPUTS_DIR, "segment_anomalies_top1000.csv")
    print(f"Saving top {len(anomalies[:1000])} segment anomalies to {anomaly_csv}...")
    anomalies.head(1000).to_csv(anomaly_csv, index=False)
    print("Anomalies persisted.")
    
    print("\nSegment analysis completed successfully!")

if __name__ == "__main__":
    run_segment_analysis()
