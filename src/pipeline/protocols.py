from typing import Protocol, Any, Dict, List, Optional, Union, Generator
import pandas as pd
import numpy as np

class DataLoader(Protocol):
    """Protocol for loading raw transaction and customer datasets."""
    def load_training_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Load a consolidated DataFrame for model training."""
        ...

    def stream_batches(self, batch_size: int = 1000) -> Generator[pd.DataFrame, None, None]:
        """Stream data in chunks to preserve memory."""
        ...

class FeaturePreprocessor(Protocol):
    """Protocol for data preprocessing and feature engineering."""
    def fit(self, df: pd.DataFrame) -> "FeaturePreprocessor":
        """Fit preprocessor parameters on training data."""
        ...

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply transformations and return feature-engineered DataFrame."""
        ...

class ModelAgent(Protocol):
    """Protocol standardizing model interaction for classification or anomaly detection."""
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> None:
        """Train the underlying model."""
        ...

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict binary class (0/1) or anomaly indicator."""
        ...

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities (e.g. anomaly score or fraud probability)."""
        ...

    def get_raw_model(self) -> Any:
        """Return the raw underlying model (XGBoost/scikit-learn object) for SHAP/xAI."""
        ...

class xAIExplainer(Protocol):
    """Protocol for Explainable AI (xAI) implementations."""
    def explain(self, model: ModelAgent, X: pd.DataFrame, instance_idx: int) -> Dict[str, Any]:
        """Generate local feature importance and textual explanation for a single transaction."""
        ...

class PipelinePlugin(Protocol):
    """Protocol for middleware plugins to hook into pipeline lifecycle events."""
    def on_pipeline_start(self, pipeline: Any) -> None: ...
    def on_data_extracted(self, df: pd.DataFrame) -> None: ...
    def on_features_transformed(self, X: pd.DataFrame) -> None: ...
    def on_predictions_generated(self, X: pd.DataFrame, y_pred: np.ndarray, y_prob: np.ndarray) -> None: ...
    def on_explanations_generated(self, explanations: List[Dict[str, Any]]) -> None: ...
    def on_pipeline_end(self, pipeline: Any) -> None: ...

class RoutingRule(Protocol):
    """Protocol for pluggable Tier 1 routing rules."""
    def evaluate(self, df: pd.DataFrame) -> np.ndarray:
        """Evaluate data and return integer array: 0=Safe, 1=Fraud, -1=Ambiguous."""
        ...

    def to_natural_language(self) -> str:
        """Return a natural language description of the rule."""
        ...

