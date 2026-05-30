import os
import hashlib
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from typing import Dict, Any, Optional
from collections import defaultdict
from src.pipeline.protocols import FeaturePreprocessor

def hash_df_index(df: pd.DataFrame) -> str:
    """Generate a fast, collision-resistant hash of a DataFrame's index and shape."""
    if df.empty:
        return "empty"
    idx_values = df.index.values
    first_few = str(idx_values[:10])
    last_few = str(idx_values[-10:])
    shape_str = str(df.shape)
    full_str = f"{first_few}_{last_few}_{shape_str}"
    return hashlib.sha256(full_str.encode('utf-8')).hexdigest()

class NewFeaturesPreprocessor(FeaturePreprocessor):
    """Preprocessor for V4 features, with class-name-specific memory and disk caching."""
    def __init__(self):
        self.raw_categorical_cols = [
            'TRANS_LV1', 'TRANS_LV2', 'Occupation_Group'
        ]
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.global_hour_probs = np.ones(24) / 24.0
        self.customer_hour_probs: Dict[Any, np.ndarray] = {}
        self.is_fitted = False
        
        # Cache paths named after the class name
        self.fit_cache_filename = os.path.abspath(os.path.join("data", f"{self.__class__.__name__}_fit.pkl"))
        self.transform_cache_filename = os.path.abspath(os.path.join("data", f"{self.__class__.__name__}_transform_cache.pkl"))
        
        # Memory caches
        self.memory_transform_cache: Dict[str, pd.DataFrame] = {}
        self.disk_transform_cache: Dict[str, pd.DataFrame] = {}
        
        # Load transform cache from disk if it exists
        if os.path.exists(self.transform_cache_filename):
            try:
                with open(self.transform_cache_filename, "rb") as f:
                    self.disk_transform_cache = pickle.load(f)
                # Stale cache invalidation check (must have exactly 15 features)
                for k, v in list(self.disk_transform_cache.items()):
                    if len(v.columns) != 15:
                        print(f"[Preprocessor Cache] Invalidating stale transform cache with {len(v.columns)} columns (expected 15).")
                        self.disk_transform_cache.clear()
                        try:
                            os.remove(self.transform_cache_filename)
                        except OSError:
                            pass
                        break
            except Exception as e:
                print(f"[Preprocessor Cache] Warning: Failed to load transform cache: {e}")

    def fit(self, df: pd.DataFrame) -> "NewFeaturesPreprocessor":
        """Fit LabelEncoders and build customer hour distributions, with caching."""
        # Check disk cache for fit state
        if os.path.exists(self.fit_cache_filename):
            print(f"[Preprocessor Cache] Loading fitted state from {self.fit_cache_filename}...")
            try:
                with open(self.fit_cache_filename, "rb") as f:
                    fit_state = pickle.load(f)
                self.label_encoders = fit_state['label_encoders']
                self.global_hour_probs = fit_state['global_hour_probs']
                self.customer_hour_probs = fit_state['customer_hour_probs']
                self.is_fitted = True
                return self
            except Exception as e:
                print(f"[Preprocessor Cache] Fit cache load failed: {e}. Re-fitting...")

        print("[Preprocessor Cache] Fit cache miss. Fitting preprocessor on dataset...")
        # 1. Fit encoders
        for col in self.raw_categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                series = df[col].fillna('UNKNOWN').astype(str)
                series_list = list(series.unique())
                if 'UNKNOWN' not in series_list:
                    series_list.append('UNKNOWN')
                le.fit(series_list)
                self.label_encoders[col] = le

        # 2. Build global transaction hour distribution
        global_counts = np.zeros(24)
        if 'TRANS_HOUR' in df.columns:
            hours = pd.to_numeric(df['TRANS_HOUR'], errors='coerce').fillna(0.0).round().astype(int) % 24
            for h in hours:
                global_counts[h] += 1
        
        global_smoothed = np.zeros(24)
        for h in range(24):
            global_smoothed[h] = (global_counts[(h - 1) % 24] + global_counts[h] + global_counts[(h + 1) % 24]) / 3.0
        
        sum_global = global_smoothed.sum()
        self.global_hour_probs = global_smoothed / sum_global if sum_global > 0 else np.ones(24) / 24.0

        # 3. Build per-customer transaction hour distributions
        self.customer_hour_probs = {}
        if 'CUSTOMER_NUMBER' in df.columns and 'TRANS_HOUR' in df.columns:
            grouped = df.groupby(['CUSTOMER_NUMBER', 'TRANS_HOUR']).size().reset_index(name='count')
            customer_counts = defaultdict(lambda: np.zeros(24))
            for _, row in grouped.iterrows():
                cust = row['CUSTOMER_NUMBER']
                h = int(round(float(row['TRANS_HOUR']))) % 24
                cnt = row['count']
                customer_counts[cust][h] += cnt
            
            for cust, counts in customer_counts.items():
                smoothed = np.zeros(24)
                for h in range(24):
                    smoothed[h] = (counts[(h - 1) % 24] + counts[h] + counts[(h + 1) % 24]) / 3.0
                sum_smoothed = smoothed.sum()
                if sum_smoothed > 0:
                    self.customer_hour_probs[cust] = smoothed / sum_smoothed
                else:
                    self.customer_hour_probs[cust] = self.global_hour_probs.copy()

        # Save fit state to disk cache
        try:
            os.makedirs(os.path.dirname(self.fit_cache_filename), exist_ok=True)
            with open(self.fit_cache_filename, "wb") as f:
                pickle.dump({
                    'label_encoders': self.label_encoders,
                    'global_hour_probs': self.global_hour_probs,
                    'customer_hour_probs': self.customer_hour_probs
                }, f)
        except Exception as e:
            print(f"[Preprocessor Cache] Warning: Failed to save fit cache to disk: {e}")

        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform dataframe with memory, local class disk cache, and global disk cache."""
        if not self.is_fitted:
            raise ValueError("Preprocessor has not been fitted. Call fit() first.")
            
        df_hash = hash_df_index(df)
        
        # Check memory cache
        if df_hash in self.memory_transform_cache:
            return self.memory_transform_cache[df_hash]

        from src.pipeline.cache_helpers import transform_preprocessor_cache
        global_cache_filename = os.path.abspath(os.path.join("data", "global_preprocessor_cache.pkl"))
        
        required_cols = [
            'BENFORD_DEV', 'ACTIVITY_SEQ_RARITY',
            'TRANS_AMOUNT_Z_SCORE', 'BALANCE_COVERAGE_RATIO',
            'SPIKE_1H_VS_24H', 'SPIKE_24H_VS_7D', 'SPIKE_7D_VS_30D',
            'TRANS_AMOUNT_VS_30D_AVG_RATIO'
        ]

        def _do_transform():
            print(f"[Preprocessor Cache] Cache miss. Transforming {df.shape[0]:,} records...")
            processed_df = pd.DataFrame(index=df.index)
            
            # Helper to extract numerical series
            def get_numeric_series(col_name, default_val=0.0):
                if col_name in df.columns:
                    return pd.to_numeric(df[col_name], errors='coerce').fillna(default_val).astype(float)
                else:
                    return pd.Series(default_val, index=df.index, dtype=float)
    
            trans_amount = get_numeric_series('TRANS_AMOUNT', 0.0)
            
            # Note: We do not add TRANS_HOUR_PROB to features, but we can compute it if needed by rules.
            
            processed_df['BENFORD_DEV'] = get_numeric_series('BENFORD_DEV', 0.0)
            processed_df['ACTIVITY_SEQ_RARITY'] = get_numeric_series('ACTIVITY_SEQ_RARITY', 0.0)
            
            # Relative features
            hist_avg_trans = get_numeric_series('HIST_AVG_TRANS_AMOUNT', 0.0)
            hist_std_trans = get_numeric_series('HIST_STD_TRANS_AMOUNT', 0.0)
            processed_df['TRANS_AMOUNT_Z_SCORE'] = np.where(
                hist_std_trans > 1e-5,
                (trans_amount - hist_avg_trans) / hist_std_trans,
                0.0
            ).astype(float)
            
            hist_avg_ca = get_numeric_series('HIST_AVG_CA_BALANCE', 0.0)
            processed_df['BALANCE_COVERAGE_RATIO'] = (trans_amount / (hist_avg_ca + 1e-5)).astype(float)
            
            sum_amount_1h = get_numeric_series('SUM_AMOUNT_1H', 0.0)
            sum_amount_24h = get_numeric_series('SUM_AMOUNT_24H', 0.0)
            sum_amount_7d = get_numeric_series('SUM_AMOUNT_7D', 0.0)
            sum_amount_30d = get_numeric_series('SUM_AMOUNT_30D', 0.0)
            
            count_1h = get_numeric_series('COUNT_1H', 0.0)
            count_24h = get_numeric_series('COUNT_24H', 0.0)
            count_7d = get_numeric_series('COUNT_7D', 0.0)
            count_30d = get_numeric_series('COUNT_30D', 0.0)
            
            # Compute velocity ratios (clipped)
            v_amt_1h_24h = np.clip(sum_amount_1h / (sum_amount_24h + 1e-5), 0.0, 1.0)
            v_cnt_1h_24h = np.clip(count_1h / (count_24h + 1e-5), 0.0, 1.0)
            
            v_amt_24h_7d = np.clip(sum_amount_24h / (sum_amount_7d + 1e-5), 0.0, 1.0)
            v_cnt_24h_7d = np.clip(count_24h / (count_7d + 1e-5), 0.0, 1.0)
            
            v_amt_7d_30d = np.clip(sum_amount_7d / (sum_amount_30d + 1e-5), 0.0, 1.0)
            v_cnt_7d_30d = np.clip(count_7d / (count_30d + 1e-5), 0.0, 1.0)
            
            # Combine to SPIKE features (Option A)
            processed_df['SPIKE_1H_VS_24H'] = (1.0 - v_amt_1h_24h) * (1.0 - v_cnt_1h_24h)
            processed_df['SPIKE_24H_VS_7D'] = (1.0 - v_amt_24h_7d) * (1.0 - v_cnt_24h_7d)
            processed_df['SPIKE_7D_VS_30D'] = (1.0 - v_amt_7d_30d) * (1.0 - v_cnt_7d_30d)
            
            hist_avg_30d = sum_amount_30d / (count_30d + 1e-5)
            processed_df['TRANS_AMOUNT_VS_30D_AVG_RATIO'] = (trans_amount / (hist_avg_30d + 1e-5)).astype(float)
            
            return processed_df

        res = transform_preprocessor_cache(
            own_cache_filename=self.transform_cache_filename,
            global_cache_filename=global_cache_filename,
            df_hash=df_hash,
            required_columns=required_cols,
            transform_fn=_do_transform
        )

        self.memory_transform_cache[df_hash] = res
        return res
