import pandas as pd
import numpy as np
import shap
from src.pipeline.brace_explainer import BRACEExplainer
from typing import List, Dict, Any

class CustomBRACEExplainer(BRACEExplainer):
    """Custom Sequential-Causal Recourse Partitioning (CustomBRACE).
    Handles the new feature set and translates log-multiplicative combinations
    and night anomaly mixes into plain-language rationales and recourse.
    """
    def __init__(self, background_data_limit: int = 100):
        super().__init__(background_data_limit=background_data_limit)
        
        # Define immutable features for the custom features
        self.immutable_features = {
            'AGE_GROUP', 'Occupation_Group', 'TRANS_LV1', 'TRANS_LV2',
            'TRANS_HOUR', 'HIST_NIGHT_RATIO', 'HIST_BIOMETRIC_RATIO',
            'ACTIVITY_SEQ_RARITY', 'BENFORD_DEV',
            'DAYS_SINCE_LAST_TRANS', 'HOURS_SINCE_SEC_EVENT',
            'NIGHT_ANOMALY', 'VELOCITY_RATIO_COUNT_24H_VS_7D',
            'VELOCITY_RATIO_COUNT_7D_VS_30D'
        }
        self.raw_df_ambiguous = None

    def set_raw_df_ambiguous(self, df_ambiguous: pd.DataFrame) -> None:
        """Store the raw ambiguous dataframe for causal tracking."""
        self.raw_df_ambiguous = df_ambiguous

    def explain(self, model_agent: Any, X: pd.DataFrame, instance_idx: int) -> Dict[str, Any]:
        """Generate SHAP values and custom narratives for the new feature set."""
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

        # Generate narratives customized for the new features
        narrative_parts = []
        for factor in top_factors:
            f_name = factor['feature']
            val = factor['value']
            
            if f_name == 'NIGHT_ANOMALY':
                narrative_parts.append(f"night transaction anomaly (rare off-hour transfer relative to customer's history, score: {val:.2f})")
            elif f_name == 'DAYS_AMOUNT_COMBINED':
                narrative_parts.append(f"unusual combination of high transaction amount and long inactivity period (combined score: {val:.2f})")
            elif f_name == 'SEC_AMOUNT_COMBINED':
                narrative_parts.append(f"unusual combination of high transaction amount shortly after a security credential update (combined score: {val:.2f})")
            elif f_name == 'TRANS_AMOUNT_Z_SCORE':
                narrative_parts.append(f"transaction amount is {val:.1f}x higher than historical average")
            elif f_name == 'BALANCE_COVERAGE_RATIO':
                narrative_parts.append(f"transaction amount covers {val:.1f}x monthly average balance")
            elif f_name == 'VELOCITY_RATIO_AMOUNT_24H_VS_7D':
                narrative_parts.append(f"sudden 24h spending volume spike relative to 7 days (ratio: {val:.1%})")
            elif f_name == 'VELOCITY_RATIO_AMOUNT_7D_VS_30D':
                narrative_parts.append(f"sudden 7d spending volume spike relative to 30 days (ratio: {val:.1%})")
            elif f_name == 'TRANS_AMOUNT_VS_30D_AVG_RATIO':
                narrative_parts.append(f"transaction amount is {val:.1f}x higher than 30-day average transaction size")
            elif f_name == 'ACTIVITY_SEQ_RARITY':
                narrative_parts.append(f"improbable sequential activity transition pattern (score: {val:.3f})")
            elif f_name == 'BENFORD_DEV':
                narrative_parts.append(f"transaction amount leading digits deviation from Benford's Law (score: {val:.4f})")
            elif f_name == 'AGE_GROUP':
                age_labels = ['young', 'middle', 'old']
                lbl = age_labels[int(val)] if int(val) < len(age_labels) else 'UNKNOWN'
                narrative_parts.append(f"customer belongs to the '{lbl}' age group category")
            elif f_name == 'DAYS_SINCE_LAST_TRANS':
                narrative_parts.append(f"long inactivity period ({val:.1f} days since last transaction)")
            elif f_name == 'HOURS_SINCE_SEC_EVENT':
                narrative_parts.append(f"recent security credential modification ({val:.1f} hours ago)")
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
        """Causal recourse on the virtual TRANS_AMOUNT variable, propagating to dependent ratios and log combinations."""
        # Find if any factor is an amount-related controllable feature
        controllable_factors = [
            f for f in top_factors 
            if f['feature'] not in self.immutable_features
        ]
        
        if not controllable_factors:
            return []

        # Check if we have the raw ambiguous dataframe attached
        if self.raw_df_ambiguous is None or len(self.raw_df_ambiguous) <= instance_idx:
            # Fallback to independent search if raw data not available
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
        hist_avg_ca = float(raw_row.get('HIST_AVG_CA_BALANCE', 0.0))
        
        orig_sum_24h = float(raw_row.get('SUM_AMOUNT_24H', 0.0))
        orig_sum_7d = float(raw_row.get('SUM_AMOUNT_7D', 0.0))
        orig_sum_30d = float(raw_row.get('SUM_AMOUNT_30D', 0.0))
        
        count_24h = float(raw_row.get('COUNT_24H', 0.0))
        count_7d = float(raw_row.get('COUNT_7D', 0.0))
        count_30d = float(raw_row.get('COUNT_30D', 0.0))
        
        days_since = float(raw_row.get('DAYS_SINCE_LAST_TRANS', 999.0))
        hours_since_sec = float(raw_row.get('HOURS_SINCE_SEC_EVENT', 999.0))
        
        log_days = np.log1p(max(0.0, days_since))
        log_sec = np.log1p(max(0.0, hours_since_sec))
        
        for _ in range(n_steps):
            mid = (lo + hi) / 2.0
            perturbed = original.copy()
            
            # 1. Update relative features
            perturbed['TRANS_AMOUNT_Z_SCORE'] = mid / (hist_avg_trans + 1e-5)
            perturbed['BALANCE_COVERAGE_RATIO'] = mid / (hist_avg_ca + 1e-5)
            
            new_sum_24h = max(0.0, orig_sum_24h - orig_amount + mid)
            new_sum_7d = max(0.0, orig_sum_7d - orig_amount + mid)
            new_sum_30d = max(0.0, orig_sum_30d - orig_amount + mid)
            
            perturbed['VELOCITY_RATIO_AMOUNT_24H_VS_7D'] = new_sum_24h / (new_sum_7d + 1e-5)
            perturbed['VELOCITY_RATIO_AMOUNT_7D_VS_30D'] = new_sum_7d / (new_sum_30d + 1e-5)
            
            hist_avg_30d = new_sum_30d / (count_30d + 1e-5)
            perturbed['TRANS_AMOUNT_VS_30D_AVG_RATIO'] = mid / (hist_avg_30d + 1e-5)
            
            # 2. Update log-multiplicative features
            log_mid = np.log1p(max(0.0, mid))
            perturbed['DAYS_AMOUNT_COMBINED'] = log_days * log_mid
            perturbed['SEC_AMOUNT_COMBINED'] = log_sec * log_mid
            
            # Predict probability with the perturbed features
            score = float(model_agent.predict_proba(perturbed)[0])
            if score < threshold:
                safe_amount = mid
                lo = mid  # Try to find a higher safe amount (closer to original)
            else:
                hi = mid  # Need to reduce amount further
                
        if safe_amount is not None:
            delta = safe_amount - orig_amount
            # If the delta is meaningful, recommend this counterfactual recourse on TRANS_AMOUNT
            if abs(delta) > 1e-2:
                return [{
                    'feature': 'TRANS_AMOUNT',
                    'original': orig_amount,
                    'safe_value': safe_amount,
                    'delta': delta
                }]
                
        return []
