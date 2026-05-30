import os
import pickle
import numpy as np
import pandas as pd
from src.pipeline.protocols import RoutingRule


class HourlyAnomalyRule(RoutingRule):
    """Blocks transactions executed at hours with extremely low historical transaction probability 
    for the customer, combined with high transaction amount.
    
    Rationale:
    Attackers often execute automated or manual transfers as soon as they gain control of an account,
    regardless of the customer's typical daily active hours (e.g., transferring at 3 AM for a customer
    who only transacts during business hours). Combining this time-based anomaly with a large 
    outbound transfer (> 10M) serves as a high-confidence signature of fraud.
    """

    def __init__(self, prob_threshold: float = 0.015, amount_threshold: float = 10_000_000.0):
        self.prob_threshold = prob_threshold
        self.amount_threshold = amount_threshold

    def evaluate(self, df: pd.DataFrame) -> np.ndarray:
        amounts = pd.to_numeric(df.get('TRANS_AMOUNT', 0.0)).fillna(0.0).values
        
        # Calculate TRANS_HOUR_PROB dynamically
        trans_hour_prob = np.zeros(len(df))
        cust_col = df['CUSTOMER_NUMBER'].values if 'CUSTOMER_NUMBER' in df.columns else [None] * len(df)
        hour_col = pd.to_numeric(df['TRANS_HOUR'], errors='coerce').fillna(0.0).round().astype(int).values % 24
        
        # Load from preprocessor fit cache if available
        fit_cache_filename = os.path.abspath(os.path.join("data", "NewFeaturesPreprocessor_fit.pkl"))
        customer_hour_probs = {}
        global_hour_probs = np.ones(24) / 24.0
        
        if os.path.exists(fit_cache_filename):
            try:
                with open(fit_cache_filename, "rb") as f:
                    fit_state = pickle.load(f)
                customer_hour_probs = fit_state.get('customer_hour_probs', {})
                global_hour_probs = fit_state.get('global_hour_probs', np.ones(24) / 24.0)
            except Exception:
                pass
                
        for i in range(len(df)):
            cust = cust_col[i]
            h = hour_col[i]
            if cust in customer_hour_probs:
                trans_hour_prob[i] = customer_hour_probs[cust][h]
            else:
                trans_hour_prob[i] = global_hour_probs[h]

        is_low_prob = trans_hour_prob < self.prob_threshold
        is_high_value = amounts > self.amount_threshold
        is_block = is_low_prob & is_high_value

        result = np.full(len(df), -1, dtype=int)
        result[is_block] = 1
        return result

    def to_natural_language(self) -> str:
        return (
            f"Block if transaction hour probability for the customer is extremely low (< {self.prob_threshold * 100:.1f}%) "
            f"and transaction amount exceeds {self.amount_threshold:,.0f}."
        )
