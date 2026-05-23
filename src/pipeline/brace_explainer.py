import pandas as pd
import numpy as np
from src.pipeline.explainers import SHAPExplainer
from typing import List, Dict, Any

class BRACEExplainer(SHAPExplainer):
    """Subclass of SHAPExplainer implementing Sequential-Causal Recourse Partitioning (BRACE).
    Ensures counterfactual recommendations:
    1. Do not recommend changes to immutable features (e.g. Age, Tenure, Historical averages).
    2. Propagate causal changes mathematically to dependent features (e.g. Z-scores and sum velocities).
    """
    def __init__(self, background_data_limit: int = 100):
        super().__init__(background_data_limit=background_data_limit)
        
        # Features that cannot be altered for a transaction after it is initiated
        self.immutable_features = {
            'CUSTOMER_AGE', 'TENURE_DAYS', 
            'HIST_AVG_CA_BALANCE', 'HIST_AVG_TRANS_AMOUNT', 
            'HIST_TRANS_COUNT', 'HIST_ACTIVITY_COUNT',
            'CLIENT_SEX', 'EB_REGISTER_CHANNEL', 'VERIFY_METHOD',
            'TRANS_LV1', 'TRANS_LV2', 'DAY_OF_WEEK', 'TRANS_HOUR', 
            'TRANS_NO', 'STAFF', 'SMS'
        }

    def _compute_counterfactuals(
        self, model_agent: Any, X: pd.DataFrame, instance_idx: int,
        top_factors: list, n_steps: int = 20
    ) -> List[Dict[str, Any]]:
        """Binary search for minimum recourse delta, blocking immutable features and propagating causal relationships."""
        threshold = getattr(model_agent, 'threshold', 0.5)
        original = X.iloc[[instance_idx]].copy()
        counterfactuals = []

        for factor in top_factors:
            feat = factor['feature']
            orig_val = float(factor['value'])
            
            # 1. Skip immutable features (Recourse Partitioning constraint)
            if feat in self.immutable_features:
                continue
                
            col_idx = X.columns.get_loc(feat)
            col_min = float(X[feat].min())

            # Skip if already at column minimum
            if abs(orig_val - col_min) < 1e-9:
                continue

            lo, hi = col_min, orig_val
            safe_val = None

            # 2. Sequential-Causal Propagation during optimization
            if feat == 'TRANS_AMOUNT':
                # Propagate transaction amount changes to dependent ratios and sums
                hist_avg_trans = float(original['HIST_AVG_TRANS_AMOUNT'].iloc[0])
                hist_avg_ca = float(original['HIST_AVG_CA_BALANCE'].iloc[0])
                orig_amount = float(original['TRANS_AMOUNT'].iloc[0])
                orig_sum_24h = float(original['SUM_AMOUNT_24H'].iloc[0])
                orig_sum_7d = float(original['SUM_AMOUNT_7D'].iloc[0])
                
                for _ in range(n_steps):
                    mid = (lo + hi) / 2.0
                    perturbed = original.copy()
                    perturbed.iloc[0, col_idx] = mid
                    
                    # Causal updates
                    perturbed['TRANS_AMOUNT_Z_SCORE'] = mid / (hist_avg_trans + 1e-5)
                    perturbed['BALANCE_COVERAGE_RATIO'] = mid / (hist_avg_ca + 1e-5)
                    
                    new_sum_24h = orig_sum_24h - orig_amount + mid
                    new_sum_7d = orig_sum_7d - orig_amount + mid
                    perturbed['SUM_AMOUNT_24H'] = new_sum_24h
                    perturbed['SUM_AMOUNT_7D'] = new_sum_7d
                    perturbed['VELOCITY_RATIO_AMOUNT_24H_VS_7D'] = new_sum_24h / (new_sum_7d + 1e-5)
                    
                    score = float(model_agent.predict_proba(perturbed)[0])
                    if score < threshold:
                        safe_val = mid
                        lo = mid  # Try higher (closer to original)
                    else:
                        hi = mid  # Need to go lower
                        
            elif feat == 'COUNT_24H':
                # Propagate 24h count changes to count velocity ratio
                count_7d = float(original['COUNT_7D'].iloc[0])
                
                for _ in range(n_steps):
                    mid = (lo + hi) / 2.0
                    perturbed = original.copy()
                    perturbed.iloc[0, col_idx] = mid
                    
                    # Causal update
                    perturbed['VELOCITY_RATIO_COUNT_24H_VS_7D'] = mid / (count_7d + 1e-5)
                    
                    score = float(model_agent.predict_proba(perturbed)[0])
                    if score < threshold:
                        safe_val = mid
                        lo = mid
                    else:
                        hi = mid
            else:
                # Standard independent binary search for other controllable features
                for _ in range(n_steps):
                    mid = (lo + hi) / 2.0
                    perturbed = original.copy()
                    perturbed.iloc[0, col_idx] = mid
                    
                    score = float(model_agent.predict_proba(perturbed)[0])
                    if score < threshold:
                        safe_val = mid
                        lo = mid
                    else:
                        hi = mid

            if safe_val is not None:
                delta = safe_val - orig_val
                if abs(delta) < 1e-2:
                    continue
                counterfactuals.append({
                    'feature': feat,
                    'original': orig_val,
                    'safe_value': safe_val,
                    'delta': delta
                })

        return counterfactuals
