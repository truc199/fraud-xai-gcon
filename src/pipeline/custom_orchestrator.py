import time
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from src.pipeline.orchestrator import MLPipeline
from src.pipeline.protocols import DataLoader, FeaturePreprocessor, ModelAgent, xAIExplainer, PipelinePlugin, RoutingRule

class CustomHierarchicalMLPipeline(MLPipeline):
    """Custom hierarchical orchestrator that integrates CustomBRACEExplainer by passing
    the intermediate ambiguous transaction records for causal recourse tracking.
    """
    def __init__(
        self,
        data_loader: DataLoader,
        preprocessor: FeaturePreprocessor,
        model_agent: ModelAgent,
        explainer: Optional[xAIExplainer] = None,
        plugins: Optional[List[PipelinePlugin]] = None,
        rules: Optional[List[RoutingRule]] = None
    ):
        super().__init__(
            data_loader=data_loader,
            preprocessor=preprocessor,
            model_agent=model_agent,
            explainer=explainer,
            plugins=plugins
        )
        self.rules = rules or []

    def run_inference_pipeline(self, df_raw: pd.DataFrame, explain_limit: int = 1000) -> Dict[str, Any]:
        """Perform hierarchical routed prediction and explanation with custom explainer data mapping."""
        self._trigger_plugins('on_pipeline_start', self)
        self._trigger_plugins('on_data_extracted', df_raw)
        
        n_total = len(df_raw)
        start_total = time.time()
        
        # 1. Tier 1: Pluggable Rules Bypass (Safe & Fraud)
        start_t1 = time.time()
        
        decisions = np.full(n_total, -1, dtype=int)
        for rule in self.rules:
            rule_decisions = rule.evaluate(df_raw)
            # Safe (0) overrides ambiguous (-1)
            decisions = np.where((decisions == -1) & (rule_decisions == 0), 0, decisions)
            # Fraud (1) overrides all
            decisions = np.where(rule_decisions == 1, 1, decisions)
            
        n_safe = int(np.sum(decisions == 0))
        n_forced_fraud = int(np.sum(decisions == 1))
        n_ambiguous = n_total - n_safe - n_forced_fraud
        t1_duration = time.time() - start_t1
        
        y_pred = np.zeros(n_total, dtype=int)
        y_prob = np.zeros(n_total, dtype=float)
        
        # Pre-fill bypass decisions
        y_pred[decisions == 1] = 1
        y_prob[decisions == 1] = 1.0
        
        ambiguous_indices = np.where(decisions == -1)[0]
        
        explanations = []
        n_flagged = 0
        t2_duration = 0.0
        t3_duration = 0.0
        
        # 2. Tier 2: Structural Awareness
        if n_ambiguous > 0:
            start_t2 = time.time()
            df_ambiguous = df_raw.iloc[ambiguous_indices].reset_index(drop=True)
            
            # Feed raw ambiguous data to explainer for causal tracing before transformation
            if self.explainer and hasattr(self.explainer, 'set_raw_df_ambiguous'):
                self.explainer.set_raw_df_ambiguous(df_ambiguous)
            
            # Run full preprocessing and prediction for ambiguous events
            X_features = self.preprocessor.transform(df_ambiguous)
            self._trigger_plugins('on_features_transformed', X_features)
            
            ambiguous_preds = self.model_agent.predict(X_features)
            ambiguous_probs = self.model_agent.predict_proba(X_features)
            
            # Map back to main indices
            for i, local_idx in enumerate(ambiguous_indices):
                y_pred[local_idx] = ambiguous_preds[i]
                y_prob[local_idx] = ambiguous_probs[i]
                
            self._trigger_plugins('on_predictions_generated', X_features, ambiguous_preds, ambiguous_probs)
            t2_duration = time.time() - start_t2
            
            # 3. Tier 3: Causal Explanation
            start_t3 = time.time()
            if self.explainer:
                flagged_ambiguous_local_indices = np.where(ambiguous_preds == 1)[0]
                n_flagged = len(flagged_ambiguous_local_indices)
                
                for local_idx in flagged_ambiguous_local_indices[:explain_limit]:
                    global_idx = ambiguous_indices[local_idx]
                    explanation = self.explainer.explain(self.model_agent, X_features, int(local_idx))
                    explanation['instance_index'] = int(global_idx)  # Map back to global index
                    explanation['raw_record'] = df_raw.iloc[global_idx].to_dict()
                    explanations.append(explanation)
                    
                self._trigger_plugins('on_explanations_generated', explanations)
            t3_duration = time.time() - start_t3
            
        total_duration = time.time() - start_total
        
        self.last_run_stats = {
            "total_records": n_total,
            "tier1_filtered_safe": n_safe,
            "tier1_forced_fraud": n_forced_fraud,
            "tier1_filter_pct": ((n_safe + n_forced_fraud) / n_total) * 100 if n_total > 0 else 0,
            "tier2_evaluated": n_ambiguous,
            "tier3_flagged_anomalies": n_flagged,
            "tier1_time_sec": t1_duration,
            "tier2_time_sec": t2_duration,
            "tier3_time_sec": t3_duration,
            "total_time_sec": total_duration
        }
        
        # Console output for routing audit
        print("\n=== Hierarchical Routing Execution Stats ===")
        print(f"  Total Telemetry Evaluated : {n_total:,}")
        print(f"  Tier 1 Filtered (Safe)     : {n_safe:,}")
        print(f"  Tier 1 Forced (Fraud)      : {n_forced_fraud:,}")
        print(f"  Tier 2 Processed (Ambiguous): {n_ambiguous:,}")
        print(f"  Tier 3 Explanations (Alerts): {n_flagged:,}")
        print(f"  Execution Time breakdown:")
        print(f"    - Tier 1: {t1_duration * 1000:.2f} ms")
        print(f"    - Tier 2: {t2_duration * 1000:.2f} ms")
        print(f"    - Tier 3: {t3_duration * 1000:.2f} ms")
        print(f"    - Total : {total_duration * 1000:.2f} ms")
        print("============================================")
        
        self._trigger_plugins('on_pipeline_end', self)
        
        return {
            'predictions': y_pred,
            'probabilities': y_prob,
            'explanations': explanations
        }

    def get_rules_descriptions(self) -> List[str]:
        """Return a list of rule descriptions in natural language."""
        return [rule.to_natural_language() for rule in self.rules]
