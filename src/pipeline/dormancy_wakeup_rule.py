import numpy as np
import pandas as pd
from src.pipeline.protocols import RoutingRule


class DormancyWakeupRule(RoutingRule):
    """Blocks transactions from dormant accounts that suddenly transfer large amounts outside.

    Rationale (ke_hoach_dieu_tra_gian_lan.md - Step 1.2 Group C):
    Criminals purchase mule accounts, leave them dormant for extended periods to avoid
    monitoring, then suddenly reactivate them to move illicit funds. An account inactive
    for >90 days that immediately performs a large outbound transfer exhibits the
    signature pattern of mule account activation.

    EDA validation (1.4M transactions):
    - Accounts dormant >90 days: 6,914 (0.49%)
    - Dormant >90d + amount >10M + Outside_bank: 867 (0.06%)
    - False positive risk: extremely low — legitimate users rarely return after 3+ months
      of inactivity and immediately transfer >10M to external accounts.
    """

    def __init__(self, dormancy_days: float = 90.0, amount_threshold: float = 10_000_000.0):
        self.dormancy_days = dormancy_days
        self.amount_threshold = amount_threshold

    def evaluate(self, df: pd.DataFrame) -> np.ndarray:
        days_since = pd.to_numeric(df.get('DAYS_SINCE_LAST_TRANS', 0.0)).fillna(0.0).values
        amounts = pd.to_numeric(df.get('TRANS_AMOUNT', 0.0)).fillna(0.0).values
        trans_lv2 = df.get('TRANS_LV2', pd.Series('', index=df.index)).fillna('').astype(str).values

        is_dormant = days_since > self.dormancy_days
        is_high_value = amounts > self.amount_threshold
        is_outside = np.array([('Outside' in str(v)) for v in trans_lv2])

        is_block = is_dormant & is_high_value & is_outside

        result = np.full(len(df), -1, dtype=int)
        result[is_block] = 1
        return result

    def to_natural_language(self) -> str:
        return (
            f"Block if account has been dormant for more than {self.dormancy_days:.0f} days "
            f"and transaction amount exceeds {self.amount_threshold:,.0f} "
            f"and transaction is directed outside the bank."
        )
