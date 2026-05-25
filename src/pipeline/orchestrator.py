from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from src.pipeline.protocols import DataLoader, FeaturePreprocessor, ModelAgent, xAIExplainer, PipelinePlugin

class MLPipeline:
    """The central orchestrator wiring loaders, preprocessors, models, explainers, and plugins."""
    def __init__(
        self,
        data_loader: DataLoader,
        preprocessor: FeaturePreprocessor,
        model_agent: ModelAgent,
        explainer: Optional[xAIExplainer] = None,
        plugins: Optional[List[PipelinePlugin]] = None
    ):
        self.data_loader = data_loader
        self.preprocessor = preprocessor
        self.model_agent = model_agent
        self.explainer = explainer
        self.plugins = plugins or []

    def _trigger_plugins(self, hook_name: str, *args, **kwargs) -> None:
        """Helper to invoke lifecycle hooks on all registered plugins."""
        for plugin in self.plugins:
            hook = getattr(plugin, hook_name, None)
            if hook and callable(hook):
                hook(*args, **kwargs)

    def run_training_pipeline(self, limit: Optional[int] = None, y: Optional[pd.Series] = None) -> None:
        """Run standard extraction, preprocessor fitting, and model training workflow."""
        self._trigger_plugins('on_pipeline_start', self)

        # 1. Extraction
        df_raw = self.data_loader.load_training_data(limit=limit)
        self._trigger_plugins('on_data_extracted', df_raw)

        # 2. Preprocessing & Feature Engineering
        self.preprocessor.fit(df_raw)
        X_features = self.preprocessor.transform(df_raw)
        self._trigger_plugins('on_features_transformed', X_features)

        # 3. Model Training
        self.model_agent.fit(X_features, y)

        self._trigger_plugins('on_pipeline_end', self)

    def run_inference_pipeline(self, df_raw: pd.DataFrame, explain_limit: int = 5) -> Dict[str, Any]:
        """Perform predictions and generate explanations for flagged anomalies."""
        self._trigger_plugins('on_pipeline_start', self)
        self._trigger_plugins('on_data_extracted', df_raw)

        # 1. Feature Preprocessing
        X_features = self.preprocessor.transform(df_raw)
        self._trigger_plugins('on_features_transformed', X_features)

        # 2. Prediction
        y_pred = self.model_agent.predict(X_features)
        y_prob = self.model_agent.predict_proba(X_features)
        self._trigger_plugins('on_predictions_generated', X_features, y_pred, y_prob)

        # 3. Explanation Generation (explain only anomalies)
        explanations = []
        if self.explainer and len(y_pred) > 0:
            anomaly_indices = np.where(y_pred == 1)[0]
            for idx in anomaly_indices[:explain_limit]:
                explanation = self.explainer.explain(self.model_agent, X_features, int(idx))
                # Add context metadata
                explanation['raw_record'] = df_raw.iloc[idx].to_dict()
                explanations.append(explanation)
            self._trigger_plugins('on_explanations_generated', explanations)

        self._trigger_plugins('on_pipeline_end', self)

        return {
            'predictions': y_pred,
            'probabilities': y_prob,
            'explanations': explanations
        }
