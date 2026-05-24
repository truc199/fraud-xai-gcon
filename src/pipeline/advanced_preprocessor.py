import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from typing import Dict

class AdvancedPreprocessor:
    """Preprocesses columns and engineers advanced domain-specific fraud features (Z-scores, rolling velocities, Benford, Markov)."""
    def __init__(self):
        self.categorical_cols = [
            'TRANS_LV1', 'TRANS_LV2', 'DAY_OF_WEEK', 
            'CLIENT_SEX', 'EB_REGISTER_CHANNEL', 'VERIFY_METHOD',
            'Occupation_Group'
        ]
        self.numerical_cols = [
            'TRANS_HOUR', 'TRANS_NO', 'TRANS_AMOUNT', 'STAFF', 'SMS',
            'HIST_AVG_CA_BALANCE', 'HIST_AVG_TRANS_AMOUNT', 'HIST_TRANS_COUNT',
            'BENFORD_DEV', 'ACTIVITY_SEQ_RARITY',
            'SUM_AMOUNT_1H', 'COUNT_1H',
            'SUM_AMOUNT_3H', 'COUNT_3H',
            'SUM_AMOUNT_24H', 'COUNT_24H',
            'SUM_AMOUNT_48H', 'COUNT_48H',
            'SUM_AMOUNT_7D', 'COUNT_7D',
            'SUM_AMOUNT_30D', 'COUNT_30D',
            'DAYS_SINCE_LAST_TRANS', 'UNIQUE_BENEFICIARIES_24H',
            'HOURS_SINCE_SEC_EVENT', 'HIST_BIOMETRIC_RATIO', 'HIST_LOGIN_COUNT'
        ]
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.is_fitted = False

    def fit(self, df: pd.DataFrame) -> "AdvancedPreprocessor":
        """Fit LabelEncoders to categorical columns."""
        for col in self.categorical_cols:
            if col in df.columns:
                le = LabelEncoder()
                series = df[col].fillna('UNKNOWN').astype(str)
                series_list = list(series.unique())
                if 'UNKNOWN' not in series_list:
                    series_list.append('UNKNOWN')
                le.fit(series_list)
                self.label_encoders[col] = le
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply feature-engineered transformations and return the processed DataFrame."""
        if not self.is_fitted:
            raise ValueError("Preprocessor has not been fitted. Call fit() first.")
            
        processed_df = pd.DataFrame(index=df.index)
        
        # 1. Date-based Feature Engineering
        trans_dates = pd.to_datetime(df['TRANS_DATE'], errors='coerce')
        dob_dates = pd.to_datetime(df['DATE_OF_BIRTH'], errors='coerce')
        create_dates = pd.to_datetime(df['CLIENT_CREATE_DATE'], errors='coerce')
        
        # Customer age at transaction time
        processed_df['CUSTOMER_AGE'] = (trans_dates.dt.year - dob_dates.dt.year).fillna(35.0).astype(float)
        # Account age/tenure in days at transaction time
        tenure_days = (trans_dates - create_dates).dt.days.fillna(0.0).astype(float)
        processed_df['TENURE_DAYS'] = tenure_days
        
        # 2. Extract Base Numerical Columns
        for col in self.numerical_cols:
            if col in df.columns:
                processed_df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
            else:
                processed_df[col] = 0.0

        # 3. Advanced High-Signal Fraud Feature Engineering
        
        # Z-Score: Ratio of current transaction amount to customer's historical average transaction size
        processed_df['TRANS_AMOUNT_Z_SCORE'] = (
            processed_df['TRANS_AMOUNT'] / (processed_df['HIST_AVG_TRANS_AMOUNT'] + 1e-5)
        ).astype(float)
        
        # Balance Coverage: Ratio of transaction size to average monthly account balance
        processed_df['BALANCE_COVERAGE_RATIO'] = (
            processed_df['TRANS_AMOUNT'] / (processed_df['HIST_AVG_CA_BALANCE'] + 1e-5)
        ).astype(float)
        
        # 1H vs 24H Amount Velocity Ratio
        processed_df['VELOCITY_RATIO_AMOUNT_1H_VS_24H'] = (
            processed_df['SUM_AMOUNT_1H'] / (processed_df['SUM_AMOUNT_24H'] + 1e-5)
        ).astype(float)
        
        # 24H vs 7D Amount Velocity Ratio (Spike Detector)
        processed_df['VELOCITY_RATIO_AMOUNT_24H_VS_7D'] = (
            processed_df['SUM_AMOUNT_24H'] / (processed_df['SUM_AMOUNT_7D'] + 1e-5)
        ).astype(float)
        
        # 7D vs 30D Amount Velocity Ratio
        processed_df['VELOCITY_RATIO_AMOUNT_7D_VS_30D'] = (
            processed_df['SUM_AMOUNT_7D'] / (processed_df['SUM_AMOUNT_30D'] + 1e-5)
        ).astype(float)
        
        # 1H vs 24H Transaction Count Velocity Ratio
        processed_df['VELOCITY_RATIO_COUNT_1H_VS_24H'] = (
            processed_df['COUNT_1H'] / (processed_df['COUNT_24H'] + 1e-5)
        ).astype(float)
        
        # 24H vs 7D Transaction Count Velocity Ratio (Spike Detector)
        processed_df['VELOCITY_RATIO_COUNT_24H_VS_7D'] = (
            processed_df['COUNT_24H'] / (processed_df['COUNT_7D'] + 1e-5)
        ).astype(float)
        
        # 7D vs 30D Transaction Count Velocity Ratio
        processed_df['VELOCITY_RATIO_COUNT_7D_VS_30D'] = (
            processed_df['COUNT_7D'] / (processed_df['COUNT_30D'] + 1e-5)
        ).astype(float)
        
        # Transaction amount vs average 30-day transaction amount ratio
        hist_avg_30d = processed_df['SUM_AMOUNT_30D'] / (processed_df['COUNT_30D'] + 1e-5)
        processed_df['TRANS_AMOUNT_VS_30D_AVG_RATIO'] = (
            processed_df['TRANS_AMOUNT'] / (hist_avg_30d + 1e-5)
        ).astype(float)
        
        # 4. Night transaction ratio
        is_night = ((processed_df['TRANS_HOUR'] >= 0) & (processed_df['TRANS_HOUR'] <= 5)).astype(int)
        # We need customer number context to compute cumulative night ratio
        if 'CUSTOMER_NUMBER' in df.columns:
            temp_df = pd.DataFrame({
                'CUSTOMER_NUMBER': df['CUSTOMER_NUMBER'],
                'is_night': is_night
            })
            grouped = temp_df.groupby('CUSTOMER_NUMBER')
            cum_total = grouped.cumcount()
            cum_night = grouped['is_night'].cumsum() - temp_df['is_night']
            processed_df['HIST_NIGHT_RATIO'] = (cum_night / (cum_total + 1e-5)).astype(float)
        else:
            processed_df['HIST_NIGHT_RATIO'] = 0.0

        # 5. Categorical Columns
        for col in self.categorical_cols:
            if col in df.columns:
                le = self.label_encoders[col]
                classes_set = set(le.classes_)
                series = df[col].fillna('UNKNOWN').astype(str).apply(
                    lambda x: x if x in classes_set else 'UNKNOWN'
                )
                processed_df[col] = le.transform(series).astype(float)
            else:
                if col in self.label_encoders:
                    unknown_val = self.label_encoders[col].transform(['UNKNOWN'])[0]
                    processed_df[col] = float(unknown_val)
                else:
                    processed_df[col] = 0.0
                    
        return processed_df
