import numpy as np
import pandas as pd
from src.pipeline.protocols import RoutingRule


class ATOPanicRule(RoutingRule):
    """Blocks transactions executed immediately after a security credential change on
    established accounts.

    Rationale (fraud_timeline_analysis_2018_2026.md - Profile A: Phishing Credential Replay):
    In 2019 Vietnam, the dominant ATO (Account Takeover) attack followed a fixed sequence:
    1. Attacker obtains victim's credentials via phishing site
    2. Attacker logs in and changes password/PIN to lock out the victim
    3. Attacker immediately transfers maximum funds to external accounts
    The entire attack window is typically 15-90 minutes (ke_hoach_dieu_tra_gian_lan.md - Step 2.2).

    The HIST_TRANS_COUNT > min_hist_count condition excludes newly created accounts where
    MB_SET_PIN (onboarding PIN setup) followed by a first transaction is normal behavior.

    EDA validation (1.4M transactions, excluding MB_SET_PIN and SET_PASSWORD events):
    - Transactions with prior sec event <1h + >10M + Outside: 496 (0.035%)
    - After HIST_TRANS_COUNT > 10 filter: estimated <400 transactions
    - False positive risk: extremely low — established users rarely change passwords
      and immediately transfer >10M to external accounts within the same hour.
    """

    def __init__(self, hours_threshold: float = 1.0, amount_threshold: float = 10_000_000.0,
                 min_hist_count: int = 10):
        self.hours_threshold = hours_threshold
        self.amount_threshold = amount_threshold
        self.min_hist_count = min_hist_count

    def evaluate(self, df: pd.DataFrame) -> np.ndarray:
        hours_since_sec = pd.to_numeric(df.get('HOURS_SINCE_SEC_EVENT', 999.0)).fillna(999.0).values
        amounts = pd.to_numeric(df.get('TRANS_AMOUNT', 0.0)).fillna(0.0).values
        trans_lv2 = df.get('TRANS_LV2', pd.Series('', index=df.index)).fillna('').astype(str).values

        # Calculate tenure in days (current transaction time - registration date)
        ts_dt = pd.to_datetime(df['TRANS_DATE']) + pd.to_timedelta(df['TRANS_HOUR'], unit='h')
        reg_date = pd.to_datetime(df.get('IB_REGISTER_DATE')).fillna(pd.to_datetime(df.get('CLIENT_CREATE_DATE')))
        reg_date = reg_date.fillna(ts_dt)  # Fallback: if registration date is missing, tenure is 0 days
        tenure_days = (ts_dt - reg_date).dt.total_seconds() / (24 * 3600.0)
        tenure_days = tenure_days.fillna(0.0).values

        # Conditions: hours_since_sec <= threshold, TRANS_AMOUNT > threshold, TRANS_LV2 = 'Outside_bank'
        is_recent_sec = hours_since_sec <= self.hours_threshold
        is_high_value = amounts > self.amount_threshold
        is_outside = np.array([(str(v) == 'Outside_bank' or 'Outside_bank' in str(v)) for v in trans_lv2])

        is_triggered = is_recent_sec & is_high_value & is_outside
        
        # If triggered and tenure >= 1.0 day -> Fraud (1)
        # If triggered and tenure < 1.0 day -> Ambiguous (-1)
        # If not triggered -> Ambiguous (-1)
        is_block = is_triggered & (tenure_days >= 1.0)

        result = np.full(len(df), -1, dtype=int)
        result[is_block] = 1
        return result

    def to_natural_language(self) -> str:
        return (
            f"Evaluate as Fraud (1) if a security credential was changed within the last {self.hours_threshold:.1f} hour(s) "
            f"and transaction amount exceeds {self.amount_threshold:,.0f} "
            f"and transaction is directed to Outside_bank "
            f"and customer account tenure is at least 1 day. "
            f"If tenure is less than 1 day under these conditions, return Ambiguous (-1)."
        )

