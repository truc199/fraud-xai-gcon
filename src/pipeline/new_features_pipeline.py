import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from typing import Dict, Any, List, Optional
from collections import defaultdict
from src.pipeline.protocols import FeaturePreprocessor
from src.pipeline.custom_explainer import CustomBRACEExplainer
import shap

class NewFeaturesPreprocessor(FeaturePreprocessor):
    """Preprocesses columns and engineers V4 features.
    
    Upgrades:
    - Replaces TRANS_HOUR with circular smoothed transaction hour probability per customer.
    - Replaces VELOCITY_RATIO_AMOUNT and VELOCITY_RATIO_COUNT with combined SPIKE features.
    - Removes AGE_GROUP, DAYS_AMOUNT_COMBINED, IP_HOPPING_VELOCITY, and HIST_BIOMETRIC_RATIO.
    """
    def __init__(self):
        self.raw_categorical_cols = [
            'TRANS_LV1', 'TRANS_LV2', 'Occupation_Group'
        ]
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.global_hour_probs = np.ones(24) / 24.0
        self.customer_hour_probs: Dict[Any, np.ndarray] = {}
        self.is_fitted = False
        import os
        self.transform_cache_filename = os.path.abspath(os.path.join("data", f"{self.__class__.__name__}_transform_cache.pkl"))
        self.memory_transform_cache = {}

    def fit(self, df: pd.DataFrame) -> "NewFeaturesPreprocessor":
        """Fit LabelEncoders and build/smooth transaction hour distributions."""
        # 1. Fit encoders for categorical columns
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
        
        # Smooth global distribution using circular SMA (window size 3)
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
            
            # Smooth and normalize each customer's distribution
            for cust, counts in customer_counts.items():
                smoothed = np.zeros(24)
                for h in range(24):
                    smoothed[h] = (counts[(h - 1) % 24] + counts[h] + counts[(h + 1) % 24]) / 3.0
                sum_smoothed = smoothed.sum()
                if sum_smoothed > 0:
                    self.customer_hour_probs[cust] = smoothed / sum_smoothed
                else:
                    self.customer_hour_probs[cust] = self.global_hour_probs.copy()

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
            'DAYS_SINCE_LAST_TRANS', 'HOURS_SINCE_SEC_EVENT',
            'BENFORD_DEV', 'ACTIVITY_SEQ_RARITY', 'NEW_DEVICE_FLAG',
            'LIMIT_UTILIZATION_VELOCITY', 'STRUCTURING_OVERPAYMENT_FLAG',
            'TRANS_AMOUNT_Z_SCORE', 'BALANCE_COVERAGE_RATIO',
            'SPIKE_1H_VS_24H', 'SPIKE_24H_VS_7D', 'SPIKE_7D_VS_30D',
            'TRANS_AMOUNT_VS_30D_AVG_RATIO', 'SEC_AMOUNT_COMBINED'
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
            days_since = get_numeric_series('DAYS_SINCE_LAST_TRANS', 999.0)
            hours_since_sec = get_numeric_series('HOURS_SINCE_SEC_EVENT', 999.0)
            
            # Note: We do not add TRANS_HOUR_PROB to features, but we can compute it if needed by rules.
            
            processed_df['DAYS_SINCE_LAST_TRANS'] = days_since
            processed_df['HOURS_SINCE_SEC_EVENT'] = hours_since_sec
            processed_df['BENFORD_DEV'] = get_numeric_series('BENFORD_DEV', 0.0)
            processed_df['ACTIVITY_SEQ_RARITY'] = get_numeric_series('ACTIVITY_SEQ_RARITY', 0.0)
            
            new_device_flag = get_numeric_series('NEW_DEVICE_FLAG', 0.0)
            processed_df['NEW_DEVICE_FLAG'] = new_device_flag
            
            # Credit & Infrastructure
            processed_df['LIMIT_UTILIZATION_VELOCITY'] = get_numeric_series('LIMIT_UTILIZATION_VELOCITY', 0.0)
            processed_df['STRUCTURING_OVERPAYMENT_FLAG'] = get_numeric_series('STRUCTURING_OVERPAYMENT_FLAG', 0.0)
            
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
            
            # Night features removed as requested (HIST_NIGHT_RATIO and NIGHT_ANOMALY are dropped)
            
            # Combination features
            log_sec = np.log1p(np.maximum(0.0, hours_since_sec))
            log_amount = np.log1p(np.maximum(0.0, trans_amount))
            processed_df['SEC_AMOUNT_COMBINED'] = (log_sec * log_amount).astype(float)
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


class NewFeaturesExplainer(CustomBRACEExplainer):
    """xAI explainer supporting the upgraded features and recourse logic."""
    def __init__(self, background_data_limit: int = 100):
        super().__init__(background_data_limit=background_data_limit)
        
        # Update immutable features to match V4 feature set
        self.immutable_features = {
            'TRANS_HOUR_PROB', 'DAYS_SINCE_LAST_TRANS', 'HOURS_SINCE_SEC_EVENT',
            'BENFORD_DEV', 'ACTIVITY_SEQ_RARITY', 'NEW_DEVICE_FLAG',
            'LIMIT_UTILIZATION_VELOCITY', 'STRUCTURING_OVERPAYMENT_FLAG'
        }

    def explain(self, model_agent: Any, X: pd.DataFrame, instance_idx: int) -> Dict[str, Any]:
        """Generate SHAP values and narratives tailored to V4 features."""
        raw_model = model_agent.get_raw_model()
        instance = X.iloc[[instance_idx]]
        
        # Lazy initialization of SHAP explainer
        if self.explainer is None:
            if "XGBClassifier" in str(type(raw_model)):
                self.explainer = shap.TreeExplainer(raw_model)
            else:
                background = X.sample(min(len(X), self.background_data_limit), random_state=42)
                self.explainer = shap.Explainer(model_agent.predict_proba, background)

        # Compute SHAP values
        if "TreeExplainer" in str(type(self.explainer)):
            shap_values_obj = self.explainer(instance)
            values = shap_values_obj.values[0]
            if len(values.shape) == 2:
                values = values[:, 1]
        else:
            shap_values_obj = self.explainer(instance)
            values = shap_values_obj.values[0]

        feature_names = X.columns.tolist()
        raw_values = instance.values[0]

        contributions = []
        for name, raw_val, contrib in zip(feature_names, raw_values, values):
            contributions.append({
                'feature': name,
                'value': raw_val,
                'contribution': float(contrib)
            })

        contributions.sort(key=lambda x: x['contribution'], reverse=True)
        top_factors = [c for c in contributions if c['contribution'] > 0.0][:3]

        # Generate narratives customized for V4 features
        narrative_parts = []
        for factor in top_factors:
            f_name = factor['feature']
            val = factor['value']
            
            if f_name == 'SEC_AMOUNT_COMBINED':
                narrative_parts.append(f"unusual combination of high transaction amount shortly after a security credential update (combined score: {val:.2f})")
            elif f_name == 'TRANS_AMOUNT_Z_SCORE':
                narrative_parts.append(f"transaction amount is {val:.1f} standard deviations away from historical average")
            elif f_name == 'BALANCE_COVERAGE_RATIO':
                narrative_parts.append(f"transaction amount covers {val:.1f}x monthly average balance")
            elif f_name == 'SPIKE_1H_VS_24H':
                narrative_parts.append(f"sudden 1h spending volume/frequency spike relative to 24 hours (spike factor: {val:.2f})")
            elif f_name == 'SPIKE_24H_VS_7D':
                narrative_parts.append(f"sudden 24h spending volume/frequency spike relative to 7 days (spike factor: {val:.2f})")
            elif f_name == 'SPIKE_7D_VS_30D':
                narrative_parts.append(f"sudden 7d spending volume/frequency spike relative to 30 days (spike factor: {val:.2f})")
            elif f_name == 'TRANS_AMOUNT_VS_30D_AVG_RATIO':
                narrative_parts.append(f"transaction amount is {val:.1f}x higher than 30-day average transaction size")
            elif f_name == 'ACTIVITY_SEQ_RARITY':
                narrative_parts.append(f"improbable sequential activity transition pattern (score: {val:.3f})")
            elif f_name == 'BENFORD_DEV':
                narrative_parts.append(f"transaction amount leading digits deviation from Benford's Law (score: {val:.4f})")
            elif f_name == 'DAYS_SINCE_LAST_TRANS':
                narrative_parts.append(f"long inactivity period ({val:.1f} days since last transaction)")
            elif f_name == 'HOURS_SINCE_SEC_EVENT':
                narrative_parts.append(f"recent security credential modification ({val:.1f} hours ago)")
            elif f_name == 'TRANS_HOUR_PROB':
                narrative_parts.append(f"low historical transaction probability for this hour (probability: {val:.4f})")
            else:
                narrative_parts.append(f"unusual behavior in feature '{f_name}' (value: {val:.2f})")

        if narrative_parts:
            narrative = "Flagged due to: " + ", and ".join(narrative_parts) + "."
        else:
            narrative = "No major anomaly features detected."

        # Compute SHAP interaction values
        interactions = []
        if "TreeExplainer" in str(type(self.explainer)):
            interaction_matrix = self.explainer.shap_interaction_values(instance)
            if isinstance(interaction_matrix, list):
                interaction_matrix = interaction_matrix[1]
            iv = interaction_matrix[0]
            n_feats = len(feature_names)
            pairs = []
            for i in range(n_feats):
                for j in range(i + 1, n_feats):
                    pair_val = float(iv[i, j] + iv[j, i])
                    if abs(pair_val) > 0.01:
                        pairs.append({
                            'feature_a': feature_names[i],
                            'feature_b': feature_names[j],
                            'interaction': pair_val
                        })
            pairs.sort(key=lambda x: abs(x['interaction']), reverse=True)
            interactions = pairs[:3]

        # Compute counterfactuals
        counterfactuals = self._compute_counterfactuals(
            model_agent, X, instance_idx, top_factors
        )

        return {
            'instance_index': instance_idx,
            'prediction_score': float(model_agent.predict_proba(instance)[0]),
            'narrative': narrative,
            'contributions': contributions[:5],
            'interactions': interactions,
            'counterfactuals': counterfactuals
        }

    def _compute_counterfactuals(
        self, model_agent: Any, X: pd.DataFrame, instance_idx: int,
        top_factors: list, n_steps: int = 20
    ) -> List[Dict[str, Any]]:
        """Recourse search on virtual TRANS_AMOUNT propagating to V4-specific dependent features."""
        controllable_factors = [
            f for f in top_factors 
            if f['feature'] not in self.immutable_features
        ]
        
        if not controllable_factors:
            return []

        if self.raw_df_ambiguous is None or len(self.raw_df_ambiguous) <= instance_idx:
            # Fallback
            return super(BRACEExplainer, self)._compute_counterfactuals(
                model_agent, X, instance_idx, top_factors, n_steps
            )
            
        raw_row = self.raw_df_ambiguous.iloc[instance_idx]
        orig_amount = float(raw_row.get('TRANS_AMOUNT', 0.0))
        if orig_amount <= 0.0:
            return []
            
        threshold = getattr(model_agent, 'threshold', 0.5)
        original = X.iloc[[instance_idx]].copy()
        
        # Search over the virtual TRANS_AMOUNT
        lo, hi = 0.0, orig_amount
        safe_amount = None
        
        # Extract pre-calculated constant values for causal updates
        hist_avg_trans = float(raw_row.get('HIST_AVG_TRANS_AMOUNT', 0.0))
        hist_std_trans = float(raw_row.get('HIST_STD_TRANS_AMOUNT', 0.0))
        hist_avg_ca = float(raw_row.get('HIST_AVG_CA_BALANCE', 0.0))
        
        orig_sum_1h = float(raw_row.get('SUM_AMOUNT_1H', 0.0))
        orig_sum_24h = float(raw_row.get('SUM_AMOUNT_24H', 0.0))
        orig_sum_7d = float(raw_row.get('SUM_AMOUNT_7D', 0.0))
        orig_sum_30d = float(raw_row.get('SUM_AMOUNT_30D', 0.0))
        
        count_1h = float(raw_row.get('COUNT_1H', 0.0))
        count_24h = float(raw_row.get('COUNT_24H', 0.0))
        count_7d = float(raw_row.get('COUNT_7D', 0.0))
        count_30d = float(raw_row.get('COUNT_30D', 0.0))
        
        v_cnt_1h_24h = np.clip(count_1h / (count_24h + 1e-5), 0.0, 1.0)
        v_cnt_24h_7d = np.clip(count_24h / (count_7d + 1e-5), 0.0, 1.0)
        v_cnt_7d_30d = np.clip(count_7d / (count_30d + 1e-5), 0.0, 1.0)
        
        hours_since_sec = float(raw_row.get('HOURS_SINCE_SEC_EVENT', 999.0))
        log_sec = np.log1p(max(0.0, hours_since_sec))
        
        for _ in range(n_steps):
            mid = (lo + hi) / 2.0
            perturbed = original.copy()
            
            # 1. Update relative features
            if hist_std_trans > 1e-5:
                perturbed['TRANS_AMOUNT_Z_SCORE'] = (mid - hist_avg_trans) / hist_std_trans
            else:
                perturbed['TRANS_AMOUNT_Z_SCORE'] = 0.0
            perturbed['BALANCE_COVERAGE_RATIO'] = mid / (hist_avg_ca + 1e-5)
            
            new_sum_1h = max(0.0, orig_sum_1h - orig_amount + mid)
            new_sum_24h = max(0.0, orig_sum_24h - orig_amount + mid)
            new_sum_7d = max(0.0, orig_sum_7d - orig_amount + mid)
            new_sum_30d = max(0.0, orig_sum_30d - orig_amount + mid)
            
            # Compute new amount velocity ratios
            v_amt_1h_24h = np.clip(new_sum_1h / (new_sum_24h + 1e-5), 0.0, 1.0)
            v_amt_24h_7d = np.clip(new_sum_24h / (new_sum_7d + 1e-5), 0.0, 1.0)
            v_amt_7d_30d = np.clip(new_sum_7d / (new_sum_30d + 1e-5), 0.0, 1.0)
            
            # Compute new combined SPIKE values (Option A)
            perturbed['SPIKE_1H_VS_24H'] = (1.0 - v_amt_1h_24h) * (1.0 - v_cnt_1h_24h)
            perturbed['SPIKE_24H_VS_7D'] = (1.0 - v_amt_24h_7d) * (1.0 - v_cnt_24h_7d)
            perturbed['SPIKE_7D_VS_30D'] = (1.0 - v_amt_7d_30d) * (1.0 - v_cnt_7d_30d)
            
            hist_avg_30d = new_sum_30d / (count_30d + 1e-5)
            perturbed['TRANS_AMOUNT_VS_30D_AVG_RATIO'] = mid / (hist_avg_30d + 1e-5)
            
            # 2. Update log-multiplicative features
            log_mid = np.log1p(max(0.0, mid))
            perturbed['SEC_AMOUNT_COMBINED'] = log_sec * log_mid
            
            # Predict probability with the perturbed features
            score = float(model_agent.predict_proba(perturbed)[0])
            if score < threshold:
                safe_amount = mid
                lo = mid
            else:
                hi = mid
                
        if safe_amount is not None:
            delta = safe_amount - orig_amount
            if abs(delta) > 1e-2:
                return [{
                    'feature': 'TRANS_AMOUNT',
                    'original': orig_amount,
                    'safe_value': safe_amount,
                    'delta': delta
                }]
                
        return []
