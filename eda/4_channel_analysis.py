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

def run_channel_analysis():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_FILE)
    
    # 1. Load transactions
    print("Loading transaction logs...")
    tx_query = """
        SELECT 
            CUSTOMER_NUMBER,
            TRANS_DATE,
            TRANS_HOUR,
            TRANS_AMOUNT,
            TRANS_LV1,
            TRANS_LV2
        FROM Data_Transaction
    """
    tx_df = pd.read_sql_query(tx_query, conn)
    tx_df['ts_dt'] = pd.to_datetime(tx_df['TRANS_DATE']) + pd.to_timedelta(tx_df['TRANS_HOUR'], unit='h')
    tx_df['tx_id'] = tx_df.index
    
    # 2. Load relevant activities (security events and logins)
    print("Loading relevant customer activities (logins and security events)...")
    act_query = """
        SELECT 
            CUSTOMER_NUMBER,
            ACTIVITY_DATE,
            ACTIVITY_HOUR,
            ACTIVITY_NAME
        FROM Data_Activity
        WHERE ACTIVITY_NAME IN (
            'LOGIN', 'LOGIN_FINGER', 'LOGIN_FACEID',
            'CHANGE_PASSWORD', 'SET_PASSWORD', 
            'MB_SET_PIN', 'MB_CHANGE_PIN', 'MB_RESET_PIN',
            'ACCOUNT_ADDRESS_BOOK_UPDATE'
        )
    """
    act_df = pd.read_sql_query(act_query, conn)
    conn.close()
    
    print(f"Loaded {len(act_df):,} activity records. Processing timestamps...")
    act_df['ts_dt'] = pd.to_datetime(act_df['ACTIVITY_DATE']) + pd.to_timedelta(act_df['ACTIVITY_HOUR'], unit='h')
    
    # Split activities into logins and security events
    security_names = [
        'CHANGE_PASSWORD', 'SET_PASSWORD', 
        'MB_SET_PIN', 'MB_CHANGE_PIN', 'MB_RESET_PIN',
        'ACCOUNT_ADDRESS_BOOK_UPDATE'
    ]
    
    sec_df = act_df[act_df['ACTIVITY_NAME'].isin(security_names)].copy()
    login_df = act_df[~act_df['ACTIVITY_NAME'].isin(security_names)].copy()
    
    # Sort for merge_asof requirements
    tx_df = tx_df.sort_values('ts_dt').reset_index(drop=True)
    sec_df = sec_df.sort_values('ts_dt').reset_index(drop=True)
    login_df = login_df.sort_values('ts_dt').reset_index(drop=True)
    
    # Calculate Security Gap
    print("Mapping security events to transactions using merge_asof...")
    sec_df['sec_event_ts'] = sec_df['ts_dt']
    
    merged_sec = pd.merge_asof(
        tx_df,
        sec_df[['CUSTOMER_NUMBER', 'ts_dt', 'sec_event_ts', 'ACTIVITY_NAME']],
        on='ts_dt',
        by='CUSTOMER_NUMBER',
        direction='backward'
    )
    
    tx_df['LAST_SEC_EVENT_TS'] = merged_sec['sec_event_ts']
    tx_df['LAST_SEC_EVENT_NAME'] = merged_sec['ACTIVITY_NAME']
    tx_df['HOURS_SINCE_SEC_EVENT'] = (tx_df['ts_dt'] - tx_df['LAST_SEC_EVENT_TS']).dt.total_seconds() / 3600
    
    # Flag ATO Alert: transaction within 24h of a security change
    tx_df['IS_ATO_ALERT'] = (
        (tx_df['HOURS_SINCE_SEC_EVENT'] <= 24.0) & 
        (tx_df['TRANS_AMOUNT'] >= 1000000.0) # avoid micro-charge noise
    ).astype(int)
    
    # Calculate Login Channel Drift
    print("Calculating login cumulative statistics...")
    login_df = login_df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
    login_df['IS_BIOMETRIC'] = login_df['ACTIVITY_NAME'].isin(['LOGIN_FINGER', 'LOGIN_FACEID']).astype(int)
    
    # Calculate cumulative biometric ratios per customer prior to each login event
    grouped_logins = login_df.groupby('CUSTOMER_NUMBER')
    login_df['cum_login_count'] = grouped_logins.cumcount()
    login_df['cum_biometric_count'] = grouped_logins['IS_BIOMETRIC'].cumsum() - login_df['IS_BIOMETRIC']
    login_df['cum_biometric_ratio'] = login_df['cum_biometric_count'] / (login_df['cum_login_count'] + 1e-5)
    
    print("Mapping login events to transactions using merge_asof...")
    login_df['login_ts'] = login_df['ts_dt']
    login_df = login_df.sort_values('ts_dt').reset_index(drop=True)
    
    merged_login = pd.merge_asof(
        tx_df,
        login_df[['CUSTOMER_NUMBER', 'ts_dt', 'login_ts', 'ACTIVITY_NAME', 'cum_biometric_ratio', 'cum_login_count']],
        on='ts_dt',
        by='CUSTOMER_NUMBER',
        direction='backward'
    )
    
    tx_df['LAST_LOGIN_TS'] = merged_login['login_ts']
    tx_df['LAST_LOGIN_METHOD'] = merged_login['ACTIVITY_NAME']
    tx_df['HIST_BIOMETRIC_RATIO'] = merged_login['cum_biometric_ratio']
    tx_df['HIST_LOGIN_COUNT'] = merged_login['cum_login_count']
    
    # Flag Login Channel Drift: User typically logs in with bio (>= 50% bio ratio over >= 3 logins),
    # but the last login right before this transaction was standard password web login ('LOGIN').
    tx_df['IS_LOGIN_DRIFT_ALERT'] = (
        (tx_df['LAST_LOGIN_METHOD'] == 'LOGIN') &
        (tx_df['HIST_LOGIN_COUNT'] >= 3) &
        (tx_df['HIST_BIOMETRIC_RATIO'] >= 0.5) &
        (tx_df['TRANS_AMOUNT'] >= 1000000.0)
    ).astype(int)
    
    # Generate statistics
    print("Generating distribution statistics...")
    stats = {
        'security_events': {
            'total_security_events_found': int(len(sec_df)),
            'total_ato_alerts': int(tx_df['IS_ATO_ALERT'].sum())
        },
        'login_channel_drift': {
            'total_logins_found': int(len(login_df)),
            'total_login_drift_alerts': int(tx_df['IS_LOGIN_DRIFT_ALERT'].sum())
        }
    }
    
    # Save statistics JSON
    stats_file = os.path.join(OUTPUTS_DIR, "channel_statistics.json")
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=4)
    print(f"Saved statistics to {stats_file}")
    
    # Persist full aggregated output
    output_csv = os.path.join(OUTPUTS_DIR, "customer_channel_features.csv.gz")
    print(f"Saving full compressed channel data to {output_csv}...")
    tx_df = tx_df.sort_values('tx_id').reset_index(drop=True)
    tx_df.to_csv(output_csv, index=False, compression='gzip')
    print("Full data persisted.")
    
    # Save top anomalies
    tx_df['risk_score'] = (tx_df['IS_ATO_ALERT'] * 2.0) + (tx_df['IS_LOGIN_DRIFT_ALERT'] * 2.0)
    anomalies = tx_df[tx_df['risk_score'] >= 2.0].sort_values('risk_score', ascending=False)
    
    anomaly_csv = os.path.join(OUTPUTS_DIR, "channel_anomalies_top1000.csv")
    print(f"Saving top {len(anomalies[:1000])} channel anomalies to {anomaly_csv}...")
    anomalies.head(1000).to_csv(anomaly_csv, index=False)
    print("Anomalies persisted.")
    
    print("\nDigital channel analysis completed successfully!")

if __name__ == "__main__":
    run_channel_analysis()
