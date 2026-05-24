import os
import sys

# Add workspace root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import shap
from src.pipeline.advanced_data_loader import AdvancedDataLoader
from src.pipeline.custom_preprocessor import CustomPreprocessor

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(current_dir, "..", "data", "gcontest.db"))
    output_dir = os.path.join(current_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    val_output_path = os.path.join(output_dir, "outlier_shap_values.csv")
    sum_output_path = os.path.join(output_dir, "outlier_shap_summary.csv")

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

    outlier_indices = np.where(raw_preds == -1)[0]
    print(f"Found {len(outlier_indices)} outliers at contamination={contamination}.")

    X_outliers = X.iloc[outlier_indices]

    print("Calculating SHAP values using TreeExplainer...")
    explainer = shap.TreeExplainer(iso)
    shap_values = explainer.shap_values(X_outliers)

    # In some versions of shap, explainer.shap_values returns list or 3D array for some models.
    # For IsolationForest, it should be a 2D numpy array.
    if isinstance(shap_values, list):
        # If it returned a list (e.g. for multiple outputs), select the first one
        shap_values = shap_values[0]
    elif len(shap_values.shape) == 3:
        shap_values = shap_values[:, :, 0]

    # Save detailed SHAP values
    shap_df = pd.DataFrame(shap_values, columns=X.columns)
    shap_df.insert(0, 'CUSTOMER_NUMBER', df_raw.iloc[outlier_indices]['CUSTOMER_NUMBER'].values)
    
    print(f"Saving detailed SHAP values to {val_output_path}...")
    shap_df.to_csv(val_output_path, index=False)

    # Save ranked summary
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    summary_df = pd.DataFrame({
        'feature': X.columns,
        'mean_abs_shap': mean_abs_shap
    })
    summary_df = summary_df.sort_values(by='mean_abs_shap', ascending=False).reset_index(drop=True)
    
    print(f"Saving ranked SHAP summary to {sum_output_path}...")
    summary_df.to_csv(sum_output_path, index=False)

    print("\n=== Top 10 Contributing Features (SHAP) ===")
    for idx, row in summary_df.head(10).iterrows():
        print(f"  {idx+1}. {row['feature']}: {row['mean_abs_shap']:.6f}")
    print("============================================")

if __name__ == "__main__":
    main()
