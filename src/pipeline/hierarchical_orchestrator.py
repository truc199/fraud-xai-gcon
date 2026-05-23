import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from src.pipeline.orchestrator import MLPipeline
from src.pipeline.protocols import DataLoader, FeaturePreprocessor, ModelAgent, xAIExplainer, PipelinePlugin

class HierarchicalMLPipeline(MLPipeline):
    """Orchestrator implementing Tiered Fallback Routing (Phase 5 Option B).
    Routes transactions based on latency requirements:
    - Tier 1: Fast sequence/amount check (kills 95% of normal traffic).
    - Tier 2: Preprocessing + XGBoost classifier for ambiguous cases.
    - Tier 3: BRACE causal recourse explanation only for flagged anomalies.
    """
    def __init__(
        self,
        data_loader: DataLoader,
        preprocessor: FeaturePreprocessor,
        model_agent: ModelAgent,
        explainer: Optional[xAIExplainer] = None,
        plugins: Optional[List[PipelinePlugin]] = None,
        tier1_rarity_threshold: float = -1.0,
        tier1_amount_threshold: float = 500000.0
    ):
        super().__init__(data_loader, preprocessor, model_agent, explainer, plugins)
        self.tier1_rarity_threshold = tier1_rarity_threshold
        self.tier1_amount_threshold = tier1_amount_threshold
        
        # Telemetry metrics
        self.last_run_stats: Dict[str, Any] = {}

    def run_inference_pipeline(self, df_raw: pd.DataFrame, explain_limit: int = 1000) -> Dict[str, Any]:
        """Perform hierarchical routed prediction and explanation."""
        self._trigger_plugins('on_pipeline_start', self)
        self._trigger_plugins('on_data_extracted', df_raw)
        
        n_total = len(df_raw)
        start_total = time.time()
        
        # 1. Tier 1: High-Speed Vigilance
        start_t1 = time.time()
        # Safe condition: high transition likelihood (rarity score > threshold) AND small amount
        # Safe means not anomalous (y = 0, prob = 0.0)
        rarity_scores = pd.to_numeric(df_raw.get('ACTIVITY_SEQ_RARITY', 0.0)).fillna(0.0).values
        amounts = pd.to_numeric(df_raw.get('TRANS_AMOUNT', 0.0)).fillna(0.0).values
        
        is_safe = (rarity_scores > self.tier1_rarity_threshold) & (amounts < self.tier1_amount_threshold)
        
        n_safe = int(np.sum(is_safe))
        n_ambiguous = n_total - n_safe
        t1_duration = time.time() - start_t1
        
        # Allocate output arrays
        y_pred = np.zeros(n_total, dtype=int)
        y_prob = np.zeros(n_total, dtype=float)
        
        # Safe cases are pre-filled with 0/0.0
        ambiguous_indices = np.where(~is_safe)[0]
        
        explanations = []
        n_flagged = 0
        t2_duration = 0.0
        t3_duration = 0.0
        
        # 2. Tier 2: Structural Awareness
        if n_ambiguous > 0:
            start_t2 = time.time()
            df_ambiguous = df_raw.iloc[ambiguous_indices].reset_index(drop=True)
            
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
                # Find which of the ambiguous events are flagged as anomalous
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
        
        # Update metrics stats
        self.last_run_stats = {
            "total_records": n_total,
            "tier1_filtered_safe": n_safe,
            "tier1_filter_pct": (n_safe / n_total) * 100 if n_total > 0 else 0,
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
        print(f"  Tier 1 Filtered (Safe)     : {n_safe:,} ({self.last_run_stats['tier1_filter_pct']:.1f}%)")
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
