import os
import sys
import json

# Add workspace root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
import shap
from src.pipeline.new_features_data_loader import NewFeaturesDataLoader
from src.pipeline.new_features_preprocessor import NewFeaturesPreprocessor
from src.pipeline.nnpu_c_classifier import NNPUCModelAgent


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(current_dir, "..", "data", "gcontest.db"))
    output_dir = os.path.join(current_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    val_output_path = os.path.join(output_dir, "outlier_shap_values.csv")
    sum_output_path = os.path.join(output_dir, "outlier_shap_summary.csv")

    print(f"Loading data from {db_path}...")
    loader = NewFeaturesDataLoader(db_path=db_path)
    df_raw = loader.load_training_data(limit=900000)
    
    print("Preprocessing features...")
    preprocessor = NewFeaturesPreprocessor()
    preprocessor.fit(df_raw)
    X = preprocessor.transform(df_raw)

    print("Fitting NNPUCModelAgent on training data...")
    contamination = 0.005
    
    # Load confirmed frauds if file exists
    confirmed_transactions = set()
    fraud_file = os.path.abspath(os.path.join(current_dir, "..", "data", "confirmed_frauds.json"))
    if os.path.exists(fraud_file):
        try:
            with open(fraud_file, "r") as f:
                data = json.load(f)
                confirmed_transactions = set(str(c).strip() for c in data.get("confirmed_transactions", []))
        except Exception as e:
            print(f"Warning: Failed to load confirmed frauds: {e}")

    y = pd.Series(0, index=df_raw.index)
    if confirmed_transactions:
        y.loc[y.index.isin(confirmed_transactions)] = 1
        print(f"Loaded {len(confirmed_transactions)} confirmed frauds.")

    model_agent = NNPUCModelAgent(contamination=contamination)
    model_agent.fit(X, y)

    print("Predicting anomalies...")
    raw_preds = model_agent.predict(X)

    outlier_indices = np.where(raw_preds == 1)[0]
    print(f"Found {len(outlier_indices)} outliers at contamination={contamination}.")

    if len(outlier_indices) == 0:
        print("No outliers found! Exiting.")
        return

    X_outliers = X.iloc[outlier_indices]

    print("Calculating SHAP values using TreeExplainer...")
    raw_model = model_agent.get_raw_model()
    explainer = shap.TreeExplainer(raw_model)
    shap_values = explainer.shap_values(X_outliers)

    # In some versions of shap, explainer.shap_values returns list or 3D array for some models.
    if isinstance(shap_values, list):
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

    print("\n=== All Contributing Features (SHAP) ===")
    for idx, row in summary_df.iterrows():
        print(f"  {idx+1}. {row['feature']}: {row['mean_abs_shap']:.6f}")
    print("============================================")

if __name__ == "__main__":
    main()
