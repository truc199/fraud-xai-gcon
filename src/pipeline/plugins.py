from typing import Any, List, Dict
import pandas as pd
import numpy as np

class ConsoleLoggerPlugin:
    """Plugin to print logs at each step of the pipeline lifecycle."""
    def on_pipeline_start(self, pipeline: Any) -> None:
        print("[Pipeline] Execution initialized.")

    def on_data_extracted(self, df: pd.DataFrame) -> None:
        print(f"[Pipeline] Extract Step: Loaded {df.shape[0]:,} raw records.")

    def on_features_transformed(self, X: pd.DataFrame) -> None:
        print(f"[Pipeline] Transform Step: Engineered {X.shape[1]} features.")

    def on_predictions_generated(self, X: pd.DataFrame, y_pred: np.ndarray, y_prob: np.ndarray) -> None:
        flagged = int(np.sum(y_pred))
        pct = (flagged / len(y_pred)) * 100 if len(y_pred) > 0 else 0
        print(f"[Pipeline] Predict Step: Flagged {flagged:,} records as anomalies ({pct:.2f}%).")

    def on_explanations_generated(self, explanations: List[Dict[str, Any]]) -> None:
        print(f"[Pipeline] Explain Step: Generated {len(explanations)} xAI explanation narratives.")

    def on_pipeline_end(self, pipeline: Any) -> None:
        print("[Pipeline] Execution completed successfully.")

class MetricsTrackerPlugin:
    """Plugin to collect and display runtime statistics."""
    def __init__(self):
        self.metrics: Dict[str, Any] = {}

    def on_pipeline_start(self, pipeline: Any) -> None:
        self.metrics = {}

    def on_data_extracted(self, df: pd.DataFrame) -> None:
        self.metrics['raw_records'] = int(df.shape[0])

    def on_features_transformed(self, X: pd.DataFrame) -> None:
        self.metrics['feature_dimensions'] = int(X.shape[1])

    def on_predictions_generated(self, X: pd.DataFrame, y_pred: np.ndarray, y_prob: np.ndarray) -> None:
        self.metrics['anomalies_flagged'] = int(np.sum(y_pred))
        self.metrics['mean_anomaly_prob'] = float(np.mean(y_prob)) if len(y_prob) > 0 else 0.0
        self.metrics['max_anomaly_prob'] = float(np.max(y_prob)) if len(y_prob) > 0 else 0.0

    def on_explanations_generated(self, explanations: List[Dict[str, Any]]) -> None:
        pass

    def on_pipeline_end(self, pipeline: Any) -> None:
        print("\n=== Pipeline Execution Metrics ===")
        for key, value in self.metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value:,}")
        print("==================================\n")
