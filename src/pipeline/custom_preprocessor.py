import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from typing import Dict

class CustomPreprocessor:
    """Preprocesses columns and engineers custom features with specific removals, mixes,
    age categorization, and stable interaction features.
    """
    def __init__(self):
        # Active categorical features after removals
        self.categorical_cols = [
            'TRANS_LV1', 'TRANS_LV2', 'Occupation_Group', 'AGE_GROUP'
        ]
        
        # We still need to fit label encoders for raw categorical columns, including the new AGE_GROUP
        self.raw_categorical_cols = [
            'TRANS_LV1', 'TRANS_LV2', 'Occupation_Group'
        ]
        
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.is_fitted = False

    def fit(self, df: pd.DataFrame) -> "CustomPreprocessor":
        """Fit LabelEncoders to categorical columns."""
        # Fit encoders for existing categorical features
        for col in self.raw_categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                series = df[col].fillna('UNKNOWN').astype(str)
                series_list = list(series.unique())
                if 'UNKNOWN' not in series_list:
                    series_list.append('UNKNOWN')
                le.fit(series_list)
                self.label_encoders[col] = le
                
        # Fit encoder for the new AGE_GROUP category
        le_age = LabelEncoder()
        le_age.fit(['young', 'middle', 'old', 'UNKNOWN'])
        self.label_encoders['AGE_GROUP'] = le_age
        
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply feature engineering, mixes, categorizations, and drop disallowed features."""
        if not self.is_fitted:
            raise ValueError("Preprocessor has not been fitted. Call fit() first.")
            
        processed_df = pd.DataFrame(index=df.index)
        
        # 1. Age Categorization (CUSTOMER_AGE -> young | middle | old)
        trans_dates = pd.to_datetime(df['TRANS_DATE'], errors='coerce')
        dob_dates = pd.to_datetime(df['DATE_OF_BIRTH'], errors='coerce')
        raw_age = (trans_dates.dt.year - dob_dates.dt.year).fillna(35.0).astype(float)
        
        age_group = []
        for age in raw_age:
            if age < 30.0:
                age_group.append('young')
            elif age < 60.0:
                age_group.append('middle')
            else:
                age_group.append('old')
        
        # Label Encode AGE_GROUP
        le_age = self.label_encoders['AGE_GROUP']
        processed_df['AGE_GROUP'] = le_age.transform(age_group).astype(float)

        # 2. Extract needed base numerical columns safely
        def get_numeric_series(col_name, default_val=0.0):
            if col_name in df.columns:
                return pd.to_numeric(df[col_name]).fillna(default_val).astype(float)
            else:
                return pd.Series(default_val, index=df.index, dtype=float)

        trans_amount = get_numeric_series('TRANS_AMOUNT', 0.0)
        days_since = get_numeric_series('DAYS_SINCE_LAST_TRANS', 999.0)
        hours_since_sec = get_numeric_series('HOURS_SINCE_SEC_EVENT', 999.0)
        trans_hour = get_numeric_series('TRANS_HOUR', 0.0)
        
        # Intermediate calculated features or direct inputs to be kept
        processed_df['TRANS_HOUR'] = trans_hour
        processed_df['DAYS_SINCE_LAST_TRANS'] = days_since
        processed_df['HOURS_SINCE_SEC_EVENT'] = hours_since_sec
        
        # Keep relative features that are not explicitly removed
        processed_df['BENFORD_DEV'] = get_numeric_series('BENFORD_DEV', 0.0)
        processed_df['ACTIVITY_SEQ_RARITY'] = get_numeric_series('ACTIVITY_SEQ_RARITY', 0.0)
        processed_df['HIST_BIOMETRIC_RATIO'] = get_numeric_series('HIST_BIOMETRIC_RATIO', 0.0)
        
        hist_night_ratio = get_numeric_series('HIST_NIGHT_RATIO', 0.0)
        processed_df['HIST_NIGHT_RATIO'] = hist_night_ratio
        
        # Keep relative features derived from amounts/counts that were not explicitly removed
        hist_avg_trans = get_numeric_series('HIST_AVG_TRANS_AMOUNT', 0.0)
        processed_df['TRANS_AMOUNT_Z_SCORE'] = (trans_amount / (hist_avg_trans + 1e-5)).astype(float)
        
        hist_avg_ca = get_numeric_series('HIST_AVG_CA_BALANCE', 0.0)
        processed_df['BALANCE_COVERAGE_RATIO'] = (trans_amount / (hist_avg_ca + 1e-5)).astype(float)
        
        sum_amount_24h = get_numeric_series('SUM_AMOUNT_24H', 0.0)
        sum_amount_7d = get_numeric_series('SUM_AMOUNT_7D', 0.0)
        sum_amount_30d = get_numeric_series('SUM_AMOUNT_30D', 0.0)
        
        processed_df['VELOCITY_RATIO_AMOUNT_24H_VS_7D'] = (sum_amount_24h / (sum_amount_7d + 1e-5)).astype(float)
        processed_df['VELOCITY_RATIO_AMOUNT_7D_VS_30D'] = (sum_amount_7d / (sum_amount_30d + 1e-5)).astype(float)
        
        count_24h = get_numeric_series('COUNT_24H', 0.0)
        count_7d = get_numeric_series('COUNT_7D', 0.0)
        count_30d = get_numeric_series('COUNT_30D', 0.0)
        
        processed_df['VELOCITY_RATIO_COUNT_24H_VS_7D'] = (count_24h / (count_7d + 1e-5)).astype(float)
        processed_df['VELOCITY_RATIO_COUNT_7D_VS_30D'] = (count_7d / (count_30d + 1e-5)).astype(float)
        
        hist_avg_30d = sum_amount_30d / (count_30d + 1e-5)
        processed_df['TRANS_AMOUNT_VS_30D_AVG_RATIO'] = (trans_amount / (hist_avg_30d + 1e-5)).astype(float)

        # 3. Night transaction anomaly mix (TRANS_HOUR:HIST_NIGHT_RATIO)
        is_night = ((trans_hour >= 0.0) & (trans_hour <= 5.0)).astype(float)
        processed_df['NIGHT_ANOMALY'] = (is_night * (1.0 - hist_night_ratio)).astype(float)

        # 4. Numerically Stable Combination Features (log-multiplicative)
        # Using ln(1+x) transformation to keep value ranges stable
        log_days = np.log1p(np.maximum(0.0, days_since))
        log_sec = np.log1p(np.maximum(0.0, hours_since_sec))
        log_amount = np.log1p(np.maximum(0.0, trans_amount))
        
        processed_df['DAYS_AMOUNT_COMBINED'] = (log_days * log_amount).astype(float)
        processed_df['SEC_AMOUNT_COMBINED'] = (log_sec * log_amount).astype(float)

        # 5. Add encoded categorical columns
        for col in self.raw_categorical_cols:
            if col in df.columns:
                le = self.label_encoders[col]
                classes_set = set(le.classes_)
                series = df[col].fillna('UNKNOWN').astype(str).apply(
                    lambda x: x if x in classes_set else 'UNKNOWN'
                )
                processed_df[col] = le.transform(series).astype(float)
            else:
                unknown_val = self.label_encoders[col].transform(['UNKNOWN'])[0]
                processed_df[col] = float(unknown_val)
                
        return processed_df
