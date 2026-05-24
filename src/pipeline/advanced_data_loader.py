import os
import sqlite3
import pandas as pd
import numpy as np
import math
from collections import defaultdict
from typing import Optional, Generator, Dict
from src.pipeline.second_order_markov_loader import calculate_second_order_markov_mapping, calculate_benford_mapping

def compute_rolling_unique_beneficiaries(df):
    unique_counts = np.zeros(len(df), dtype=int)
    grouped = df.groupby('CUSTOMER_NUMBER')
    
    for cust, group in grouped:
        times = group['ts_dt'].values
        bens = group['Beneficiary_CUSTOMER_NUMBER'].fillna('UNKNOWN').astype(str).values
        indices = group.index.values
        
        start_idx = 0
        active_bens = {}
        
        for i in range(len(group)):
            current_time = times[i]
            b = bens[i]
            
            if b not in ['UNKNOWN', 'NaN', 'nan']:
                active_bens[b] = active_bens.get(b, 0) + 1
            
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

class AdvancedDataLoader:
    """DataLoader that extracts transactional data aggregated with multi-window rollings,
    activity changes, and login channel drift statistics.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.benford_mapping: Optional[Dict[int, float]] = None
        self.seq_mapping: Optional[Dict[int, float]] = None
        self.cached_df: Optional[pd.DataFrame] = None

    def _get_sql_query(self, limit: Optional[int] = None) -> str:
        query = """
            WITH trans_time_added AS (
                SELECT 
                    t.CUSTOMER_NUMBER,
                    t.TRANS_LV1,
                    t.TRANS_LV2,
                    t.TRANS_DATE,
                    t.DAY_OF_WEEK,
                    t.TRANS_HOUR,
                    t.TRANS_NO,
                    t.TRANS_AMOUNT,
                    t.Beneficiary_CUSTOMER_NUMBER,
                    t.Device_OS,
                    t.IP_Address_Proxy,
                    (julianday(t.TRANS_DATE) + (t.TRANS_HOUR / 24.0)) as ts
                FROM Data_Transaction t
            ),
            rolling_metrics AS (
                SELECT 
                    CUSTOMER_NUMBER,
                    TRANS_LV1,
                    TRANS_LV2,
                    TRANS_DATE,
                    DAY_OF_WEEK,
                    TRANS_HOUR,
                    TRANS_NO,
                    TRANS_AMOUNT,
                    Beneficiary_CUSTOMER_NUMBER,
                    Device_OS,
                    IP_Address_Proxy,
                    ts,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 1.0/24.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_1H,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 1.0/24.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_1H,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 3.0/24.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_3H,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 3.0/24.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_3H,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 1.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_24H,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 1.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_24H,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 2.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_48H,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 2.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_48H,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 7.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_7D,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 7.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_7D,
                    SUM(TRANS_AMOUNT) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 30.0 PRECEDING AND CURRENT ROW
                    ) as SUM_AMOUNT_30D,
                    COUNT(*) OVER (
                        PARTITION BY CUSTOMER_NUMBER 
                        ORDER BY ts
                        RANGE BETWEEN 30.0 PRECEDING AND CURRENT ROW
                    ) as COUNT_30D
                FROM trans_time_added
            ),
            deposit_agg AS (
                SELECT CUSTOMER_NUMBER, AVG(AVG_CA_BALANCE) as HIST_AVG_CA_BALANCE 
                FROM Data_Deposit GROUP BY CUSTOMER_NUMBER
            ),
            trans_agg AS (
                SELECT CUSTOMER_NUMBER, AVG(TRANS_AMOUNT) as HIST_AVG_TRANS_AMOUNT, COUNT(*) as HIST_TRANS_COUNT
                FROM Data_Transaction GROUP BY CUSTOMER_NUMBER
            )
            SELECT 
                r.CUSTOMER_NUMBER,
                r.TRANS_LV1,
                r.TRANS_LV2,
                r.TRANS_DATE,
                r.DAY_OF_WEEK,
                r.TRANS_HOUR,
                r.TRANS_NO,
                r.TRANS_AMOUNT,
                r.Beneficiary_CUSTOMER_NUMBER,
                r.Device_OS,
                r.IP_Address_Proxy,
                c.CLIENT_SEX,
                c.CLIENT_CREATE_DATE,
                c.DATE_OF_BIRTH,
                c.STAFF,
                c.IB_REGISTER_DATE,
                c.EB_REGISTER_CHANNEL,
                c.SMS,
                c.VERIFY_METHOD,
                c.Occupation_Group,
                r.SUM_AMOUNT_1H,
                r.COUNT_1H,
                r.SUM_AMOUNT_3H,
                r.COUNT_3H,
                r.SUM_AMOUNT_24H,
                r.COUNT_24H,
                r.SUM_AMOUNT_48H,
                r.COUNT_48H,
                r.SUM_AMOUNT_7D,
                r.COUNT_7D,
                r.SUM_AMOUNT_30D,
                r.COUNT_30D,
                COALESCE(d.HIST_AVG_CA_BALANCE, 0.0) as HIST_AVG_CA_BALANCE,
                COALESCE(ta.HIST_AVG_TRANS_AMOUNT, 0.0) as HIST_AVG_TRANS_AMOUNT,
                COALESCE(ta.HIST_TRANS_COUNT, 0) as HIST_TRANS_COUNT
            FROM rolling_metrics r
            LEFT JOIN Data_Customer c ON r.CUSTOMER_NUMBER = c.CUSTOMER_NUMBER
            LEFT JOIN deposit_agg d ON r.CUSTOMER_NUMBER = d.CUSTOMER_NUMBER
            LEFT JOIN trans_agg ta ON r.CUSTOMER_NUMBER = ta.CUSTOMER_NUMBER
        """
        if limit:
            query += f" LIMIT {limit}"
        return query

    def load_training_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Load fully aggregated dataset with advanced continuous features."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        print("Extracting transaction logs and rolling window aggregates...")
        conn = sqlite3.connect(self.db_path)
        query = self._get_sql_query(limit=limit)
        df = pd.read_sql_query(query, conn)
        
        # 1. Processing timestamps and sorting sequentially
        df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
        df['CLIENT_CREATE_DATE'] = pd.to_datetime(df['CLIENT_CREATE_DATE'], errors='coerce')
        df['DATE_OF_BIRTH'] = pd.to_datetime(df['DATE_OF_BIRTH'], errors='coerce')
        df['IB_REGISTER_DATE'] = pd.to_datetime(df['IB_REGISTER_DATE'], errors='coerce')
        
        df = df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
        df['tx_id'] = df.index
        
        # 2. Compute Days Since Last Transaction
        print("Computing transaction time gaps...")
        grouped = df.groupby('CUSTOMER_NUMBER')
        df['DAYS_SINCE_LAST_TRANS'] = grouped['ts_dt'].diff().dt.total_seconds() / (24 * 3600)
        reg_date = df['IB_REGISTER_DATE'].fillna(df['CLIENT_CREATE_DATE'])
        days_since_reg = (df['ts_dt'] - reg_date).dt.total_seconds() / (24 * 3600)
        df['DAYS_SINCE_LAST_TRANS'] = df['DAYS_SINCE_LAST_TRANS'].fillna(days_since_reg).fillna(999.0)
        
        # 3. Compute Outbound unique beneficiaries in 24 hours
        df['UNIQUE_BENEFICIARIES_24H'] = compute_rolling_unique_beneficiaries(df)
        
        # 4. Integrate Security Event to Transaction Gaps
        print("Loading customer activity logs for security event mapping...")
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
        act_df['ts_dt'] = pd.to_datetime(act_df['ACTIVITY_DATE']) + pd.to_timedelta(act_df['ACTIVITY_HOUR'], unit='h')
        
        security_names = [
            'CHANGE_PASSWORD', 'SET_PASSWORD', 
            'MB_SET_PIN', 'MB_CHANGE_PIN', 'MB_RESET_PIN',
            'ACCOUNT_ADDRESS_BOOK_UPDATE'
        ]
        sec_df = act_df[act_df['ACTIVITY_NAME'].isin(security_names)].copy()
        login_df = act_df[~act_df['ACTIVITY_NAME'].isin(security_names)].copy()
        
        # Sort and merge security events
        tx_df_sorted = df.sort_values('ts_dt').reset_index(drop=True)
        sec_df = sec_df.sort_values('ts_dt').reset_index(drop=True)
        sec_df['sec_event_ts'] = sec_df['ts_dt']
        
        merged_sec = pd.merge_asof(
            tx_df_sorted,
            sec_df[['CUSTOMER_NUMBER', 'ts_dt', 'sec_event_ts']],
            on='ts_dt',
            by='CUSTOMER_NUMBER',
            direction='backward'
        )
        
        # Align back to df
        merged_sec = merged_sec.sort_values('tx_id').reset_index(drop=True)
        df['LAST_SEC_EVENT_TS'] = merged_sec['sec_event_ts']
        df['HOURS_SINCE_SEC_EVENT'] = (df['ts_dt'] - df['LAST_SEC_EVENT_TS']).dt.total_seconds() / 3600
        df['HOURS_SINCE_SEC_EVENT'] = df['HOURS_SINCE_SEC_EVENT'].fillna(999.0)
        
        # 5. Integrate Login Channel Statistics
        print("Mapping login events and computing biometric usage ratio...")
        login_df = login_df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
        login_df['IS_BIOMETRIC'] = login_df['ACTIVITY_NAME'].isin(['LOGIN_FINGER', 'LOGIN_FACEID']).astype(int)
        
        grouped_logins = login_df.groupby('CUSTOMER_NUMBER')
        login_df['cum_login_count'] = grouped_logins.cumcount()
        login_df['cum_biometric_count'] = grouped_logins['IS_BIOMETRIC'].cumsum() - login_df['IS_BIOMETRIC']
        login_df['cum_biometric_ratio'] = login_df['cum_biometric_count'] / (login_df['cum_login_count'] + 1e-5)
        
        login_df['login_ts'] = login_df['ts_dt']
        login_df = login_df.sort_values('ts_dt').reset_index(drop=True)
        
        merged_login = pd.merge_asof(
            tx_df_sorted,
            login_df[['CUSTOMER_NUMBER', 'ts_dt', 'login_ts', 'ACTIVITY_NAME', 'cum_biometric_ratio', 'cum_login_count']],
            on='ts_dt',
            by='CUSTOMER_NUMBER',
            direction='backward'
        )
        
        # Align back to df
        merged_login = merged_login.sort_values('tx_id').reset_index(drop=True)
        df['LAST_LOGIN_METHOD'] = merged_login['ACTIVITY_NAME'].fillna('UNKNOWN')
        df['HIST_BIOMETRIC_RATIO'] = merged_login['cum_biometric_ratio'].fillna(0.0)
        df['HIST_LOGIN_COUNT'] = merged_login['cum_login_count'].fillna(0)
        
        # 6. Map Benford & Markov Sequence Rarity
        print("Mapping Benford and Markov sequence rarity scores...")
        if self.benford_mapping is None:
            self.benford_mapping = calculate_benford_mapping(conn)
        if self.seq_mapping is None:
            self.seq_mapping = calculate_second_order_markov_mapping(conn)
            
        df['BENFORD_DEV'] = df['CUSTOMER_NUMBER'].map(self.benford_mapping).fillna(0.0)
        df['ACTIVITY_SEQ_RARITY'] = df['CUSTOMER_NUMBER'].map(self.seq_mapping).fillna(0.0)
        
        conn.close()
        
        # Drop temporary columns
        df = df.drop(columns=['tx_id', 'LAST_SEC_EVENT_TS', 'ts_dt'], errors='ignore')
        return df

    def stream_batches(self, batch_size: int = 1000) -> Generator[pd.DataFrame, None, None]:
        """Stream data in chunks by caching the processed dataset first."""
        if self.cached_df is None:
            self.cached_df = self.load_training_data()
            
        n_rows = len(self.cached_df)
        for i in range(0, n_rows, batch_size):
            yield self.cached_df.iloc[i : i + batch_size].copy()
