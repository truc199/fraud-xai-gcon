import numpy as np
import pandas as pd
from typing import Optional, Any

class CorrelationDiscrepancyModelAgent:
    """Pluggable ModelAgent implementing Option C (CONDOR).
    Measures the Frobenius norm of the discrepancy between rolling correlation matrices 
    and the baseline historical correlation matrix to detect structural relationship anomalies.
    """
    def __init__(self, contamination: float = 0.03, window_size: int = 50):
        self.contamination = contamination
        self.window_size = window_size
        self.baseline_corr: Optional[np.ndarray] = None
        self.norm_mean = 0.0
        self.norm_std = 1.0
        self.threshold = 0.5
        self.explain_idx: Optional[int] = None
        self.inference_df: Optional[pd.DataFrame] = None
        self.explain_history_values: Optional[np.ndarray] = None

    def set_explain_context(self, instance_idx: int, inference_df: pd.DataFrame) -> None:
        """Set context for local explanations of a single transaction index."""
        self.explain_idx = instance_idx
        self.inference_df = inference_df
        # Cache history values to avoid pandas slicing overhead in predict_proba
        start = max(0, instance_idx - self.window_size + 1)
        self.explain_history_values = inference_df.iloc[start:instance_idx].values

    def clear_explain_context(self) -> None:
        """Clear context after explanations are complete."""
        self.explain_idx = None
        self.inference_df = None
        self.explain_history_values = None

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> None:
        """Fit baseline correlation matrix and calibrate normal discrepancy stats."""
        # Calculate base correlation matrix
        self.baseline_corr = X.corr().fillna(0.0).values
        
        # Compute rolling window correlation norms over training data to establish normal distribution bounds
        norms = []
        stride = 5  # Stride of 5 to accelerate training calibration
        for i in range(self.window_size, len(X), stride):
            sub_X = X.iloc[i - self.window_size : i]
            corr = sub_X.corr().fillna(0.0).values
            diff = corr - self.baseline_corr
            norm = np.linalg.norm(diff, 'fro')
            norms.append(norm)
            
        self.norm_mean = float(np.mean(norms)) if norms else 0.0
        self.norm_std = float(np.std(norms)) if norms else 1.0
        if self.norm_std == 0:
            self.norm_std = 1e-5

        # Compute training probabilities to calibrate threshold
        train_probs = []
        for norm in norms:
            z = (norm - self.norm_mean) / self.norm_std
            prob = 1.0 / (1.0 + np.exp(-1.5 * (z - 2.0)))
            train_probs.append(prob)
            
        if train_probs:
            self.threshold = float(np.percentile(train_probs, 100 * (1 - self.contamination)))
        else:
            self.threshold = 0.5

    def predict_proba(self, X: Any) -> np.ndarray:
        """Compute rolling correlation discrepancy probabilities per transaction."""
        if self.baseline_corr is None:
            raise ValueError("ModelAgent has not been fitted. Call fit() first.")
            
        # Convert input to a 2D numpy array if it is not already
        if isinstance(X, pd.DataFrame):
            X_arr = X.values
        else:
            X_arr = np.asarray(X)
            
        # Check if we are in explanation mode (Mode B)
        if self.explain_idx is not None and self.explain_history_values is not None:
            probs = []
            history_values = self.explain_history_values
            
            for row in X_arr:
                # Combine history and the perturbed row
                sub_values = np.vstack([history_values, row])
                if len(sub_values) < 5:
                    probs.append(0.0)
                    continue
                # Calculate correlation matrix
                with np.errstate(divide='ignore', invalid='ignore'):
                    corr = np.corrcoef(sub_values, rowvar=False)
                    corr = np.nan_to_num(corr, nan=0.0)
                diff = corr - self.baseline_corr
                norm = np.linalg.norm(diff, 'fro')
                z = (norm - self.norm_mean) / self.norm_std
                prob = 1.0 / (1.0 + np.exp(-1.5 * (z - 2.0)))
                probs.append(prob)
            return np.array(probs)
            
        # Mode A: Chronological inference on the whole dataset
        probs = []
        n_samples = len(X_arr)
        
        for i in range(n_samples):
            # Define sliding window bound
            start = max(0, i - self.window_size + 1)
            sub_values = X_arr[start : i + 1]
            
            # If window is too small, use prior fallback
            if len(sub_values) < 5:
                probs.append(0.0)
                continue
                
            with np.errstate(divide='ignore', invalid='ignore'):
                corr = np.corrcoef(sub_values, rowvar=False)
                corr = np.nan_to_num(corr, nan=0.0)
            diff = corr - self.baseline_corr
            norm = np.linalg.norm(diff, 'fro')
            
            # Calculate Z-score and map to risk probability via sigmoid
            z = (norm - self.norm_mean) / self.norm_std
            prob = 1.0 / (1.0 + np.exp(-1.5 * (z - 2.0)))
            probs.append(prob)
            
        return np.array(probs)

    def predict(self, X: Any) -> np.ndarray:
        """Predict binary anomaly flags based on calibrated threshold."""
        probs = self.predict_proba(X)
        return (probs >= self.threshold).astype(int)

    def get_raw_model(self) -> Any:
        """Return self for model referencing, as correlation discrepancies are computed directly."""
        return self
