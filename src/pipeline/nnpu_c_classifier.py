import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import KFold
from typing import Optional, Any
from src.pipeline.protocols import ModelAgent, drop_categoricals

class NNPUCModelAgent(ModelAgent):
    """Pluggable ModelAgent combining:
    - Option A: nnPU & PAYN Spy-Determined Thresholding (designed to go with XGBoost)
    - Option C: Rademacher Complexity Regularization & CV-based Unlabeled Optimization (CVuO)
    """
    def __init__(
        self, 
        contamination: float = 0.03, 
        spy_fraction: float = 0.10, 
        cv_folds: int = 5,
        filter_fraction: float = 0.10,
        random_state: int = 42
    ):
        self.contamination = contamination
        self.spy_fraction = spy_fraction
        self.cv_folds = cv_folds
        self.filter_fraction = filter_fraction
        self.random_state = random_state
        
        # Final XGBoost model with regularized bounds to emulate Rademacher Complexity Bounding
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=3,            # Strict depth constraint (Complexity Regularization)
            reg_alpha=1.0,          # L1 regularization (Complexity Regularization)
            reg_lambda=2.0,         # L2 regularization (Complexity Regularization)
            learning_rate=0.05,
            random_state=self.random_state,
            eval_metric='logloss',
            n_jobs=-1
        )
        self.pu_c = 1.0
        self.threshold = 0.5
        self.is_trained = False

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> None:
        """Fit the model using PAYN Spy-filtering (Option A) and CVuO loss-filtering (Option C)."""
        # 1. Bootstrap positive labels using an Isolation Forest proxy, merged with y if available
        iso = IsolationForest(contamination=self.contamination, random_state=self.random_state, n_jobs=-1)
        raw_scores = iso.fit_predict(drop_categoricals(X))
        s_iso = np.where(raw_scores == -1, 1, 0)
        
        if y is not None:
            # Union of known positives and unsupervised anomalies
            s = np.where((s_iso == 1) | (np.asarray(y) == 1), 1, 0)
        else:
            s = s_iso

        P_indices = np.where(s == 1)[0]
        U_indices = np.where(s == 0)[0]

        if len(P_indices) < 10:
            # Fallback if too few positives
            self.model.fit(X, s)
            self.is_trained = True
            return

        # 2. Option A: PAYN Spy-Filtering (Implemented with XGBoost)
        # Select a random subset of positives to act as "spies"
        n_spies = int(len(P_indices) * self.spy_fraction)
        if n_spies < 1:
            n_spies = 1
        
        np.random.seed(self.random_state)
        spy_sub_indices = np.random.choice(P_indices, size=n_spies, replace=False)
        
        # Build training set for spy model:
        # - Labeled positives (P excluding spies) -> Labeled 1
        # - Unlabeled + Spies -> Labeled 0
        P_no_spies = np.setdiff1d(P_indices, spy_sub_indices)
        U_w_spies = np.concatenate([U_indices, spy_sub_indices])
        
        X_spy_train = pd.concat([X.iloc[P_no_spies], X.iloc[U_w_spies]], axis=0).reset_index(drop=True)
        y_spy_train = np.concatenate([np.ones(len(P_no_spies)), np.zeros(len(U_w_spies))])
        
        # Train spy detection XGBoost classifier
        spy_model = xgb.XGBClassifier(
            n_estimators=50,
            max_depth=3,
            reg_alpha=1.0,
            reg_lambda=1.0,
            random_state=self.random_state,
            eval_metric='logloss',
            n_jobs=-1
        )
        spy_model.fit(X_spy_train, y_spy_train)
        
        # Evaluate predictions on the spies
        X_spies = X.iloc[spy_sub_indices]
        spy_probs = spy_model.predict_proba(X_spies)[:, 1]
        
        # Find threshold below which only 5% of spies fall
        tau_spy = float(np.percentile(spy_probs, 5.0))
        
        # Re-label the unlabeled pool: any unlabeled sample below tau_spy is confirmed negative (y = 0)
        X_unlabeled = X.iloc[U_indices]
        unlabeled_probs = spy_model.predict_proba(X_unlabeled)[:, 1]
        
        confirmed_neg_mask = unlabeled_probs < tau_spy
        confirmed_neg_indices = U_indices[confirmed_neg_mask]
        remaining_unlabeled_indices = U_indices[~confirmed_neg_mask]
        
        # 3. Option C: CV-based Unlabeled Optimization (CVuO)
        # To filter out high-loss/adversarial samples from the remaining unlabeled pool:
        if len(remaining_unlabeled_indices) > 10:
            kf = KFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state)
            unlabeled_losses = np.zeros(len(remaining_unlabeled_indices))
            
            # Map indices to local list positions
            local_indices = np.arange(len(remaining_unlabeled_indices))
            
            for train_idx, val_idx in kf.split(local_indices):
                # Build temporary fold datasets
                fold_val_u_indices = remaining_unlabeled_indices[val_idx]
                
                # Training on positives and confirmed negatives
                train_p_indices = P_indices
                train_n_indices = confirmed_neg_indices
                
                # Combine training
                train_X = pd.concat([X.iloc[train_p_indices], X.iloc[train_n_indices]], axis=0).reset_index(drop=True)
                train_y = np.concatenate([np.ones(len(train_p_indices)), np.zeros(len(train_n_indices))])
                
                fold_model = xgb.XGBClassifier(
                    n_estimators=50,
                    max_depth=3,
                    random_state=self.random_state,
                    eval_metric='logloss',
                    n_jobs=-1
                )
                fold_model.fit(train_X, train_y)
                
                # Evaluate log-loss on validation unlabeled samples assuming they are negative (y = 0)
                X_val_u = X.iloc[fold_val_u_indices]
                val_u_probs = fold_model.predict_proba(X_val_u)[:, 1]
                
                # Log-loss formula: -log(1 - p)
                val_u_losses = -np.log(1.0 - val_u_probs + 1e-15)
                unlabeled_losses[val_idx] = val_u_losses
                
            # Discard top filter_fraction of unlabeled samples with highest losses
            loss_threshold = np.percentile(unlabeled_losses, 100 * (1 - self.filter_fraction))
            keep_mask = unlabeled_losses <= loss_threshold
            filtered_unlabeled_indices = remaining_unlabeled_indices[keep_mask]
        else:
            filtered_unlabeled_indices = remaining_unlabeled_indices
            
        # 4. Final Model Training
        # Train final XGBoost model on positives + confirmed negatives + filtered unlabeled
        final_pos_indices = P_indices
        final_neg_indices = np.concatenate([confirmed_neg_indices, filtered_unlabeled_indices])
        
        X_final = pd.concat([X.iloc[final_pos_indices], X.iloc[final_neg_indices]], axis=0).reset_index(drop=True)
        y_final = np.concatenate([np.ones(len(final_pos_indices)), np.zeros(len(final_neg_indices))])
        
        self.model.fit(X_final, y_final)
        
        # 5. Elkan-Noto Probability Calibration
        # Calculate calibration constant c using positive predictions
        pos_probs = self.model.predict_proba(X.iloc[P_indices])[:, 1]
        self.pu_c = float(np.mean(pos_probs))
        if self.pu_c < 1e-5:
            self.pu_c = 1e-5
            
        # Calibrate decision threshold on training set predictions
        self.is_trained = True
        final_probs = self.predict_proba(X)
        percentile = (1.0 - self.contamination) * 100
        self.threshold = float(np.percentile(final_probs, percentile))

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Compute calibrated probabilities via Elkan-Noto correction."""
        if not self.is_trained:
            raise ValueError("ModelAgent has not been trained yet.")
        g_x = self.model.predict_proba(X)[:, 1]
        calibrated_probs = np.clip(g_x / self.pu_c, 0.0, 1.0)
        return calibrated_probs

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict binary anomaly flags based on calibrated threshold."""
        probs = self.predict_proba(X)
        return (probs >= self.threshold).astype(int)

    def get_raw_model(self) -> Any:
        """Return raw model for SHAP/TreeExplainer support."""
        return self.model
