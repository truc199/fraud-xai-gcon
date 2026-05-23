import shap
import pandas as pd
import numpy as np
from typing import Dict, Any, List

class SHAPExplainer:
    """xAI Engine using SHAP to calculate and translate contribution scores into plain-language rationales."""
    def __init__(self, background_data_limit: int = 100):
        self.background_data_limit = background_data_limit
        self.explainer = None

    def explain(self, model_agent: Any, X: pd.DataFrame, instance_idx: int) -> Dict[str, Any]:
        """Generate SHAP values and format top factors, including Z-scores, velocities, Benford, and GMM-AE ensemble weights."""
        raw_model = model_agent.get_raw_model()
        instance = X.iloc[[instance_idx]]
        
        # Lazy initialization
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

        narrative_parts = []
        for factor in top_factors:
            f_name = factor['feature']
            val = factor['value']
            
            if f_name == 'ACTIVITY_SEQ_RARITY':
                narrative_parts.append(f"highly improbable sequential activity pattern (log-probability score: {val:.3f})")
            elif f_name == 'VELOCITY_RATIO_COUNT_24H_VS_7D':
                narrative_parts.append(f"sudden transaction frequency spike (24h count is {val:.1%} of 7d count)")
            elif f_name == 'VELOCITY_RATIO_AMOUNT_24H_VS_7D':
                narrative_parts.append(f"sudden transaction volume spike (24h sum is {val:.1%} of 7d sum)")
            elif f_name == 'BENFORD_DEV':
                narrative_parts.append(f"significant transaction amount digit deviation from Benford's Law (score: {val:.4f})")
            elif f_name == 'TRANS_AMOUNT_Z_SCORE':
                narrative_parts.append(f"amount is {val:.1f}x higher than customer's average transaction size")
            elif f_name == 'BALANCE_COVERAGE_RATIO':
                narrative_parts.append(f"transaction amount covers {val:.1f}x their monthly average savings balance")
            elif f_name == 'TRANS_AMOUNT':
                narrative_parts.append(f"high transaction amount of {val:,.2f}")
            elif f_name == 'TRANS_HOUR':
                narrative_parts.append(f"transaction occurred at off-hour ({int(val)}:00)")
            elif f_name == 'CUSTOMER_AGE':
                narrative_parts.append(f"unusual customer age profile ({int(val)} years old)")
            elif f_name == 'TENURE_DAYS':
                narrative_parts.append(f"new customer tenure ({int(val)} days since signup)")
            elif f_name == 'TRANS_LV2':
                narrative_parts.append(f"specific transaction type category (code: {int(val)})")
            elif f_name == 'COUNT_24H':
                narrative_parts.append(f"high 24-hour transaction count ({int(val)} transfers)")
            elif f_name == 'SUM_AMOUNT_24H':
                narrative_parts.append(f"high 24-hour transaction volume sum ({val:,.2f})")
            elif f_name == 'COUNT_7D':
                narrative_parts.append(f"high 7-day transaction count ({int(val)} transfers)")
            elif f_name == 'SUM_AMOUNT_7D':
                narrative_parts.append(f"high 7-day transaction volume sum ({val:,.2f})")
            elif f_name == 'TRANS_NO':
                narrative_parts.append(f"unusual transaction sequence position (transaction number: {int(val)})")
            elif f_name == 'HIST_AVG_TRANS_AMOUNT':
                narrative_parts.append(f"high historical average transaction size ({val:,.2f})")
            elif f_name == 'HIST_AVG_CA_BALANCE':
                narrative_parts.append(f"high average savings balance ({val:,.2f})")
            else:
                narrative_parts.append(f"unusual activity in feature '{f_name}' (value: {val})")

        if narrative_parts:
            narrative = "Flagged due to: " + ", and ".join(narrative_parts) + "."
        else:
            narrative = "No major anomaly features detected."

        # Compute SHAP interaction values for tree-based models
        interactions = []
        if "TreeExplainer" in str(type(self.explainer)):
            interaction_matrix = self.explainer.shap_interaction_values(instance)
            if isinstance(interaction_matrix, list):
                interaction_matrix = interaction_matrix[1]
            iv = interaction_matrix[0]  # shape: (F, F)
            
            # Extract off-diagonal pairs (i != j), take upper triangle to avoid duplicates
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

        # Compute counterfactuals: minimum feature deltas to drop below threshold
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
        """Binary search for minimum feature delta that drops score below threshold."""
        threshold = getattr(model_agent, 'threshold', 0.5)
        original = X.iloc[[instance_idx]].copy()
        counterfactuals = []

        for factor in top_factors:
            feat = factor['feature']
            orig_val = float(factor['value'])
            col_idx = X.columns.get_loc(feat)

            # Search range: from current value down to column minimum
            col_min = float(X[feat].min())

            # Skip if already at minimum
            if abs(orig_val - col_min) < 1e-9:
                continue

            lo, hi = col_min, orig_val
            safe_val = None

            for _ in range(n_steps):
                mid = (lo + hi) / 2.0
                perturbed = original.copy()
                perturbed.iloc[0, col_idx] = mid
                score = float(model_agent.predict_proba(perturbed)[0])
                if score < threshold:
                    safe_val = mid
                    lo = mid  # Try higher (closer to original)
                else:
                    hi = mid  # Need to go lower

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
