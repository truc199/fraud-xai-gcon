import numpy as np
import pandas as pd
from src.pipeline.protocols import RoutingRule


class LowRiskChannelBypassRule(RoutingRule):
    """Bypasses low-value transactions on channels that have no viable fraud exit path.

    Rationale (ke_hoach_dieu_tra_gian_lan.md - Step 1.1, Goal #3):
    The third requirement for successful fraud is "extracting assets before detection."
    Certain digital banking channels do not provide an exit path for stolen funds:
    - Credit_card_repayment: Pays money back TO the bank (reduces card outstanding balance)
    - Utilities_payment: Pays verified utility providers (EVN, VNPT, etc.)
    - Cable, Game, MCPP, Lifestyle_payment, Lending_repayment: Small fixed payments to
      verified merchants

    Attackers never use stolen funds to pay the victim's electricity bill or credit card debt.

    EDA validation (1.4M transactions):
    - Total low-risk channel transactions: ~74,000
    - Transactions < 5M on these channels: ~43,747
    - NET new bypass (not already caught by existing Amount < 500K rule): ~14,000 (+1%)
    - Amount threshold set at 5M (not 10M) to guard against credit card overpayment
      structuring (EDA found 3,456 customers who repaid more than their outstanding balance)

    Excluded channels:
    - Insurance_payment: median 15.5M, only 12.1% < 5M — too high for safe bypass
    - Within_bank: used for layering in money laundering schemes
    - Mobile/eWallet/QR_payment: already covered by existing Amount < 500K bypass rules
    """

    LOW_RISK_CHANNELS = frozenset([
        'Credit_card_repayment',
        'Utilities_payment',
        'Lending_repayment',
        'Cable',
        'Lifestyle_payment',
        'Game',
        'MCPP',
    ])

    def __init__(self, amount_threshold: float = 5_000_000.0):
        self.amount_threshold = amount_threshold

    def evaluate(self, df: pd.DataFrame) -> np.ndarray:
        amounts = pd.to_numeric(df.get('TRANS_AMOUNT', 0.0)).fillna(0.0).values
        trans_lv2 = df.get('TRANS_LV2', pd.Series('', index=df.index)).fillna('').astype(str).values

        is_low_risk_channel = np.array([v in self.LOW_RISK_CHANNELS for v in trans_lv2])
        is_low_amount = amounts < self.amount_threshold

        is_safe = is_low_risk_channel & is_low_amount

        result = np.full(len(df), -1, dtype=int)
        result[is_safe] = 0
        return result

    def to_natural_language(self) -> str:
        channels = ', '.join(sorted(self.LOW_RISK_CHANNELS))
        return (
            f"Bypass if transaction channel is low-risk ({channels}) "
            f"and transaction amount is less than {self.amount_threshold:,.0f}."
        )
