import shap
import pandas as pd
import numpy as np
from src.pipeline.explainers import SHAPExplainer
from typing import Dict, Any

class MockExplanation:
    """Mock object to emulate the shap.Explanation structure for the base explainer class."""
    def __init__(self, values: np.ndarray):
        self.values = [values]

class CorrelationDiscrepancyExplainer(SHAPExplainer):
    """Subclass of SHAPExplainer that sets/clears explanation context on the model agent
    and utilizes KernelExplainer with limited nsamples for major performance optimization.
    """
    def __init__(self, background_data_limit: int = 100):
        super().__init__(background_data_limit=background_data_limit)
        self._kernel_explainer = None

    def explain(self, model_agent: Any, X: pd.DataFrame, instance_idx: int) -> Dict[str, Any]:
        if hasattr(model_agent, 'set_explain_context'):
            model_agent.set_explain_context(instance_idx, X)
            
        if self._kernel_explainer is None:
            background = X.sample(min(len(X), self.background_data_limit), random_state=42)
            self._kernel_explainer = shap.KernelExplainer(model_agent.predict_proba, background)
            
        instance = X.iloc[[instance_idx]]
        
        # Use Kernel SHAP with nsamples=50 for fast computation
        shap_vals = self._kernel_explainer.shap_values(instance, nsamples=50, l1_reg="num_features(3)", silent=True)
        if isinstance(shap_vals, list):
            values = shap_vals[0][0]
        else:
            values = shap_vals[0]
            
        # Temporarily mock the explainer attribute for the super class
        old_explainer = self.explainer
        self.explainer = lambda inst: MockExplanation(values)
        
        try:
            res = super().explain(model_agent, X, instance_idx)
        finally:
            self.explainer = old_explainer
            if hasattr(model_agent, 'clear_explain_context'):
                model_agent.clear_explain_context()
                
        return res
