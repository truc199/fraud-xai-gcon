import os
import sys

# Add workspace root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from src.pipeline.advanced_data_loader import AdvancedDataLoader
from src.pipeline.custom_preprocessor import CustomPreprocessor

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(current_dir, "..", "data", "gcontest.db"))
    output_dir = os.path.join(current_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "outlier_logits.csv")

    print(f"Loading data from {db_path}...")
    loader = AdvancedDataLoader(db_path=db_path)
    df_raw = loader.load_training_data(limit=50000)
    
    print("Preprocessing features...")
    preprocessor = CustomPreprocessor()
    preprocessor.fit(df_raw)
    X = preprocessor.transform(df_raw)

    print("Fitting Isolation Forest with contamination=0.03...")
    contamination = 0.03
    iso = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    
    raw_preds = iso.fit_predict(X)
    scores = iso.score_samples(X)

    outlier_indices = np.where(raw_preds == -1)[0]
    print(f"Found {len(outlier_indices)} outliers at contamination={contamination}.")

    outliers_df = X.iloc[outlier_indices].copy()
    outliers_df.insert(0, 'CUSTOMER_NUMBER', df_raw.iloc[outlier_indices]['CUSTOMER_NUMBER'].values)
    outliers_df.insert(1, 'anomaly_score_sample', scores[outlier_indices])

    print(f"Saving outlier scores to {output_path}...")
    outliers_df.to_csv(output_path, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
