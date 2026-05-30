import numpy as np
import pandas as pd
from src.pipeline.protocols import RoutingRule

class CreditCardBustOutRule(RoutingRule):
    """
    Blocks card repayments/transfers indicating Credit Card Bust-out fraud.
    Triggered when MoM credit usage spikes by >=45%, transaction amount is high (>20M),
    and balance coverage ratio is extreme (>10x average account balance).
    """
    def __init__(self, velocity_threshold: float = 0.45, amount_threshold: float = 20_000_000.0, ratio_threshold: float = 10.0):
        self.velocity_threshold = velocity_threshold
        self.amount_threshold = amount_threshold
        self.ratio_threshold = ratio_threshold

    def evaluate(self, df: pd.DataFrame) -> np.ndarray:
        # Extract features
        velocities = pd.to_numeric(df.get('LIMIT_UTILIZATION_VELOCITY', 0.0)).fillna(0.0).values
        amounts = pd.to_numeric(df.get('TRANS_AMOUNT', 0.0)).fillna(0.0).values
        avg_ca_balance = pd.to_numeric(df.get('HIST_AVG_CA_BALANCE', 0.0)).fillna(0.0).values
        
        # Calculate balance coverage ratio
        balance_coverage = amounts / (avg_ca_balance + 1e-5)
        
        # Conditions
        is_spike = velocities >= self.velocity_threshold
        is_large_amount = amounts > self.amount_threshold
        is_extreme_ratio = balance_coverage > self.ratio_threshold
        
        is_fraud = is_spike & is_large_amount & is_extreme_ratio
        
        # Initialize default return as -1 (Ambiguous)
        result = np.full(len(df), -1, dtype=int)
        result[is_fraud] = 1 # Block as Fraud (1)
        
        return result

    def to_natural_language(self) -> str:
        return (f"Chặn hành vi vét hạn mức thẻ tín dụng (Tốc độ sử dụng MoM >= {self.velocity_threshold:.1%}, "
                f"Số tiền > {self.amount_threshold:,.0f} VND và gấp > {self.ratio_threshold:.0f} lần số dư tài khoản trung bình)")
