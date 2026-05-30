import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Optional, Generator
from src.pipeline.fraud_2026_data_loader import Fraud2026DataLoader, compute_rolling_unique_beneficiaries, calculate_benford_mapping_strict
from src.pipeline.second_order_markov_loader import calculate_second_order_markov_mapping

class NewFeaturesDataLoader(Fraud2026DataLoader):
    """DataLoader implementing permanent disk and memory caching,
    with IP Hopping and PageRank calculations completely removed for performance.
    """
    def __init__(self, db_path: str):
        super().__init__(db_path=db_path)
        self.cached_df: Optional[pd.DataFrame] = None
        self.cache_filename = os.path.abspath(os.path.join("data", f"{self.__class__.__name__}_cache.pkl"))

    def _get_sql_query(self, limit: Optional[int] = None) -> str:
        query = """
            WITH trans_time_added AS (
                SELECT 
                    t.col_0 as TRANSACTION_ID,
                    t.CUSTOMER_NUMBER,
                    t.TRANS_LV1,
                    t.TRANS_LV2,
                    t.TRANS_DATE,
                    t.DAY_OF_WEEK,
                    t.TRANS_HOUR,
                    t.TRANS_NO,
                    t.TRANS_AMOUNT,
                    t.Beneficiary_CUSTOMER_NUMBER,
                    t.Device_ID_Hash,
                    t.Device_OS,
                    t.IP_Address_Proxy,
                    (julianday(t.TRANS_DATE) + (t.TRANS_HOUR / 24.0)) as ts
                FROM Data_Transaction t
            ),
            rolling_metrics AS (
                SELECT 
                    TRANSACTION_ID,
                    CUSTOMER_NUMBER,
                    TRANS_LV1,
                    TRANS_LV2,
                    TRANS_DATE,
                    DAY_OF_WEEK,
                    TRANS_HOUR,
                    TRANS_NO,
                    TRANS_AMOUNT,
                    Beneficiary_CUSTOMER_NUMBER,
                    Device_ID_Hash,
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
                SELECT 
                    CUSTOMER_NUMBER, 
                    AVG(TRANS_AMOUNT) as HIST_AVG_TRANS_AMOUNT, 
                    COUNT(*) as HIST_TRANS_COUNT,
                    SQRT(MAX(AVG(TRANS_AMOUNT * TRANS_AMOUNT) - AVG(TRANS_AMOUNT) * AVG(TRANS_AMOUNT), 0)) as HIST_STD_TRANS_AMOUNT
                FROM Data_Transaction 
                GROUP BY CUSTOMER_NUMBER
            )
            SELECT 
                r.TRANSACTION_ID,
                r.CUSTOMER_NUMBER,
                r.TRANS_LV1,
                r.TRANS_LV2,
                r.TRANS_DATE,
                r.DAY_OF_WEEK,
                r.TRANS_HOUR,
                r.TRANS_NO,
                r.TRANS_AMOUNT,
                r.Beneficiary_CUSTOMER_NUMBER,
                r.Device_ID_Hash,
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
                COALESCE(ta.HIST_STD_TRANS_AMOUNT, 0.0) as HIST_STD_TRANS_AMOUNT,
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
        """Load training data, prioritizing memory, local class disk cache, and global disk cache."""
        # 1. Check in-memory cache
        if self.cached_df is not None:
            if limit is not None:
                return self.cached_df.head(limit)
            return self.cached_df

        from src.pipeline.cache_helpers import load_dataloader_cache
        global_cache_filename = os.path.abspath(os.path.join("data", "global_dataloader_cache.pkl"))
        
        required_cols = [
            'CUSTOMER_NUMBER', 'TRANS_HOUR', 'TRANS_AMOUNT', 
            'DAYS_SINCE_LAST_TRANS', 'HOURS_SINCE_SEC_EVENT', 
            'BENFORD_DEV', 'ACTIVITY_SEQ_RARITY',
            'LIMIT_UTILIZATION_VELOCITY',
            'HIST_AVG_TRANS_AMOUNT', 'HIST_STD_TRANS_AMOUNT', 'HIST_AVG_CA_BALANCE',
            'SUM_AMOUNT_1H', 'SUM_AMOUNT_24H', 'SUM_AMOUNT_7D', 'SUM_AMOUNT_30D',
            'COUNT_1H', 'COUNT_24H', 'COUNT_7D', 'COUNT_30D'
        ]

        def _calculate():
            print(f"[DataLoader Cache] Cache miss. Computing features from scratch...")
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database not found at {self.db_path}")
                
            conn = sqlite3.connect(self.db_path)
            # Load the full dataset (no limit) to build a complete permanent cache
            query = self._get_sql_query(limit=None)
            df = pd.read_sql_query(query, conn)
            
            # --- Base Features Calculation ---
            df['ts_dt'] = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
            df['CLIENT_CREATE_DATE'] = pd.to_datetime(df['CLIENT_CREATE_DATE'], errors='coerce')
            df['DATE_OF_BIRTH'] = pd.to_datetime(df['DATE_OF_BIRTH'], errors='coerce')
            df['IB_REGISTER_DATE'] = pd.to_datetime(df['IB_REGISTER_DATE'], errors='coerce')
            
            df = df.sort_values(['CUSTOMER_NUMBER', 'ts_dt']).reset_index(drop=True)
            df['tx_id'] = df.index
            
            # Days Since Last Transaction
            grouped = df.groupby('CUSTOMER_NUMBER')
            df['DAYS_SINCE_LAST_TRANS'] = grouped['ts_dt'].diff().dt.total_seconds() / (24 * 3600)
            reg_date = df['IB_REGISTER_DATE'].fillna(df['CLIENT_CREATE_DATE'])
            days_since_reg = (df['ts_dt'] - reg_date).dt.total_seconds() / (24 * 3600)
            df['DAYS_SINCE_LAST_TRANS'] = df['DAYS_SINCE_LAST_TRANS'].fillna(days_since_reg).fillna(999.0)
            
            # Unique Beneficiaries 24h
            df['UNIQUE_BENEFICIARIES_24H'] = compute_rolling_unique_beneficiaries(df)
            
            # Activity logs mapping for security events
            act_query = """
                SELECT CUSTOMER_NUMBER, ACTIVITY_DATE, ACTIVITY_HOUR, ACTIVITY_NAME
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
            
            merged_sec = merged_sec.sort_values('tx_id').reset_index(drop=True)
            df['LAST_SEC_EVENT_TS'] = merged_sec['sec_event_ts']
            df['HOURS_SINCE_SEC_EVENT'] = (df['ts_dt'] - df['LAST_SEC_EVENT_TS']).dt.total_seconds() / 3600
            df['HOURS_SINCE_SEC_EVENT'] = df['HOURS_SINCE_SEC_EVENT'].fillna(999.0)
            
            # Benford and Markov sequence rarity
            if self.benford_mapping is None:
                self.benford_mapping = calculate_benford_mapping_strict(conn)
            if self.seq_mapping is None:
                self.seq_mapping = calculate_second_order_markov_mapping(conn)
                
            df['BENFORD_DEV'] = df['CUSTOMER_NUMBER'].map(self.benford_mapping).fillna(0.0)
            df['ACTIVITY_SEQ_RARITY'] = df['CUSTOMER_NUMBER'].map(self.seq_mapping).fillna(0.0)
    
            df['IP_HOPPING_VELOCITY'] = 0.0
            df['PAGERANK_SCORE'] = 0.0
            df['IN_DEGREE_CENTRALITY'] = 0.0
    
            # Limit Utilization Velocity
            if self.limit_util_velocity_mapping is None:
                self.limit_util_velocity_mapping = super(NewFeaturesDataLoader, self).compute_limit_utilization_velocity_mapping() if hasattr(super(NewFeaturesDataLoader, self), 'compute_limit_utilization_velocity_mapping') else None
                if self.limit_util_velocity_mapping is None:
                    from src.pipeline.fraud_2026_data_loader import compute_limit_utilization_velocity
                    self.limit_util_velocity_mapping = compute_limit_utilization_velocity(conn)
                    
            df['LIMIT_UTILIZATION_VELOCITY'] = df['CUSTOMER_NUMBER'].map(self.limit_util_velocity_mapping).fillna(0.0)
            df['AUTH_DOWNGRADE_RISK'] = 0.0
    
            conn.close()
            
            # Clean up temporary columns
            df = df.drop(columns=['tx_id', 'LAST_SEC_EVENT_TS', 'ts_dt'], errors='ignore')
            if 'TRANSACTION_ID' in df.columns:
                df['TRANSACTION_ID'] = df['TRANSACTION_ID'].astype(str)
                df = df.set_index('TRANSACTION_ID', drop=False)
            return df

        self.cached_df = load_dataloader_cache(
            own_cache_filename=self.cache_filename,
            global_cache_filename=global_cache_filename,
            required_columns=required_cols,
            calculate_fn=_calculate,
            limit=None
        )

        if limit is not None:
            return self.cached_df.head(limit)
        return self.cached_df

    def stream_batches(self, batch_size: int = 1000) -> Generator[pd.DataFrame, None, None]:
        """Stream data in chunks using cached dataset."""
        if self.cached_df is None:
            self.load_training_data()
            
        n_rows = len(self.cached_df)
        for i in range(0, n_rows, batch_size):
            yield self.cached_df.iloc[i : i + batch_size].copy()
