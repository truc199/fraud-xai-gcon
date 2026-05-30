import numpy as np
import pandas as pd
from src.pipeline.protocols import RoutingRule

class SequenceRarityRule(RoutingRule):
    """Bypasses transactions with typical sequence patterns and low transaction value."""
    def __init__(self, rarity_threshold: float = -1.0, amount_threshold: float = 5000000.0):
        self.rarity_threshold = rarity_threshold
        self.amount_threshold = amount_threshold

    def evaluate(self, df: pd.DataFrame) -> np.ndarray:
        rarity_scores = pd.to_numeric(df.get('ACTIVITY_SEQ_RARITY', 0.0)).fillna(0.0).values
        amounts = pd.to_numeric(df.get('TRANS_AMOUNT', 0.0)).fillna(0.0).values
        is_safe = (rarity_scores > self.rarity_threshold) & (amounts < self.amount_threshold)
        
        result = np.full(len(df), -1, dtype=int)
        result[is_safe] = 0
        return result

    def to_natural_language(self) -> str:
        return f"Bypass if transaction sequence likelihood is typical (rarity score > {self.rarity_threshold}) and transaction amount is less than {self.amount_threshold:,.2f}."

class VelocityBypassRule(RoutingRule):
    """Bypasses transactions with normal rolling velocities and low transaction value."""
    def __init__(self, amount_threshold: float = 500000.0, count_1h_threshold: float = 1.0, count_24h_threshold: float = 2.0):
        self.amount_threshold = amount_threshold
        self.count_1h_threshold = count_1h_threshold
        self.count_24h_threshold = count_24h_threshold

    def evaluate(self, df: pd.DataFrame) -> np.ndarray:
        amounts = pd.to_numeric(df.get('TRANS_AMOUNT', 0.0)).fillna(0.0).values
        count_1h = pd.to_numeric(df.get('COUNT_1H', 1.0)).fillna(1.0).values
        count_24h = pd.to_numeric(df.get('COUNT_24H', 1.0)).fillna(1.0).values
        is_safe = (amounts < self.amount_threshold) & \
                  (count_1h <= self.count_1h_threshold) & \
                  (count_24h <= self.count_24h_threshold)
                  
        result = np.full(len(df), -1, dtype=int)
        result[is_safe] = 0
        return result

    def to_natural_language(self) -> str:
        return f"Bypass if transaction amount is less than {self.amount_threshold:,.2f} and frequency is normal (1-hour count <= {self.count_1h_threshold} and 24-hour count <= {self.count_24h_threshold})."

class SmallAmountBypassRule(RoutingRule):
    """Bypasses any transaction below a small threshold (e.g. 500,000 VND)."""
    def __init__(self, amount_threshold: float = 500000.0):
        self.amount_threshold = amount_threshold

    def evaluate(self, df: pd.DataFrame) -> np.ndarray:
        amounts = pd.to_numeric(df.get('TRANS_AMOUNT', 0.0)).fillna(0.0).values
        is_safe = amounts < self.amount_threshold
        
        result = np.full(len(df), -1, dtype=int)
        result[is_safe] = 0
        return result

    def to_natural_language(self) -> str:
        return f"Bypass all transactions with amount less than {self.amount_threshold:,.2f}."
