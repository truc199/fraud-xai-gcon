from typing import Optional, Any, Dict
from src.pipeline.protocols import ModelAgent, drop_categoricals
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import IsolationForest
import xgboost as xgb
import torch
import torch.nn as nn
import torch.optim as optim

class IsolationForestModelAgent(ModelAgent):
    """Unsupervised anomaly detection agent using scikit-learn's Isolation Forest."""
    def __init__(self, contamination: float = 0.01, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination, 
            random_state=self.random_state, 
            n_jobs=-1
        )
        self.is_trained = False

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> None:
        self.model.fit(drop_categoricals(X))
        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model has not been trained yet.")
        preds = self.model.predict(drop_categoricals(X))
        return np.where(preds == -1, 1, 0)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model has not been trained yet.")
        scores = self.model.score_samples(drop_categoricals(X))
        probs = np.clip(-scores, 0.0, 1.0)
        return probs

    def get_raw_model(self) -> Any:
        return self.model

class XGBoostModelAgent(ModelAgent):
    """Supervised classification agent using XGBoost Classifier."""
    def __init__(self, n_estimators: int = 100, max_depth: int = 5, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state,
            eval_metric='logloss',
            n_jobs=-1
        )
        self.is_trained = False

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> None:
        if y is None:
            raise ValueError("Supervised XGBoost model requires target labels 'y'.")
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model has not been trained yet.")
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model has not been trained yet.")
        return self.model.predict_proba(X)[:, 1]

    def get_raw_model(self) -> Any:
        return self.model

class PyTorchAutoencoder(nn.Module):
    """PyTorch Autoencoder for calculating reconstruction loss anomalies."""
    def __init__(self, input_dim: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))

class CohortAnomalyModelAgent(ModelAgent):
    """Advanced hybrid anomaly agent blending GMM soft-cohort Isolation Forests and PyTorch Autoencoder MSE loss,
    and training a Positive-Unlabeled (PU) XGBoost classifier on top ensemble anomaly predictions."""
    def __init__(self, n_cohorts: int = 3, contamination: float = 0.01, random_state: int = 42):
        self.n_cohorts = n_cohorts
        self.contamination = contamination
        self.random_state = random_state
        
        self.gmm = GaussianMixture(
            n_components=self.n_cohorts, 
            random_state=self.random_state, 
            n_init=1
        )
        self.cohort_models: Dict[int, IsolationForest] = {}
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ae: Optional[PyTorchAutoencoder] = None
        self.feature_means: Optional[np.ndarray] = None
        self.feature_stds: Optional[np.ndarray] = None
        self.max_train_mse = 1.0
        
        self.pu_model: Optional[xgb.XGBClassifier] = None
        self.pu_c: float = 1.0
        
        self.threshold = 0.5
        self.is_trained = False
        
        self.cohort_features = [
            'CUSTOMER_AGE', 'TENURE_DAYS', 
            'HIST_AVG_CA_BALANCE', 'HIST_AVG_TRANS_AMOUNT', 
            'HIST_TRANS_COUNT', 'HIST_ACTIVITY_COUNT'
        ]

    def _get_clustering_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Select clustering features and fill missing values."""
        feats = [col for col in self.cohort_features if col in X.columns]
        return X[feats].fillna(0.0)

    def _normalize(self, X: pd.DataFrame) -> np.ndarray:
        """Standardize input features for Autoencoder training/inference."""
        arr = X.values.astype(np.float32)
        if self.feature_means is None or self.feature_stds is None:
            self.feature_means = np.mean(arr, axis=0)
            self.feature_stds = np.std(arr, axis=0) + 1e-5
        return (arr - self.feature_means) / self.feature_stds

    def _train_autoencoder(self, X: pd.DataFrame, epochs: int = 15, batch_size: int = 256) -> None:
        """Train PyTorch Autoencoder on scaled features using MSE Loss."""
        X_norm = self._normalize(X)
        input_dim = X_norm.shape[1]
        
        self.ae = PyTorchAutoencoder(input_dim).to(self.device)
        optimizer = optim.Adam(self.ae.parameters(), lr=0.01)
        criterion = nn.MSELoss()
        
        dataset = torch.tensor(X_norm, dtype=torch.float32).to(self.device)
        
        self.ae.train()
        for epoch in range(epochs):
            permutation = torch.randperm(dataset.size()[0])
            for i in range(0, dataset.size()[0], batch_size):
                indices = permutation[i:i+batch_size]
                batch = dataset[indices]
                
                optimizer.zero_grad()
                outputs = self.ae(batch)
                loss = criterion(outputs, batch)
                loss.backward()
                optimizer.step()
                
        # Calculate training set maximum MSE to use as scaling factor during inference
        self.ae.eval()
        with torch.no_grad():
            reconstructed = self.ae(dataset)
            mse_per_row = torch.mean((dataset - reconstructed) ** 2, dim=1).cpu().numpy()
            self.max_train_mse = float(np.percentile(mse_per_row, 99.0)) + 1e-5

    def _get_autoencoder_losses(self, X: pd.DataFrame) -> np.ndarray:
        """Compute scaled Autoencoder reconstruction losses."""
        X_norm = self._normalize(X)
        dataset = torch.tensor(X_norm, dtype=torch.float32).to(self.device)
        
        self.ae.eval()
        with torch.no_grad():
            reconstructed = self.ae(dataset)
            mse_per_row = torch.mean((dataset - reconstructed) ** 2, dim=1).cpu().numpy()
            
        scaled_losses = np.clip(mse_per_row / self.max_train_mse, 0.0, 1.0)
        return scaled_losses

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> None:
        """Train GMM cohorts, Isolation Forests, the PyTorch Autoencoder, and calibration PU-XGBoost."""
        # 1. Fit GMM Cohorts
        X_clust = self._get_clustering_features(X)
        self.gmm.fit(X_clust)
        cohort_labels = self.gmm.predict(X_clust)
        
        X_w_cohort = X.copy()
        X_w_cohort['cohort'] = cohort_labels
        
        # 2. Fit Isolation Forests
        self.cohort_models = {}
        for c_idx in range(self.n_cohorts):
            X_cohort = X_w_cohort[X_w_cohort['cohort'] == c_idx].drop(columns=['cohort'])
            model = IsolationForest(
                contamination=self.contamination, 
                random_state=self.random_state, 
                n_jobs=-1
            )
            if len(X_cohort) > 10:
                model.fit(drop_categoricals(X_cohort))
            self.cohort_models[c_idx] = model
            
        # 3. Train Autoencoder
        self._train_autoencoder(X)
        
        # Mark as trained for internal ensemble predictions during fit
        self.is_trained = True
        
        # 4. Generate unsupervised proxy scores and labels
        ensemble_probs = self._predict_proba_ensemble(X)
        percentile = (1.0 - self.contamination) * 100
        threshold_ensemble = np.percentile(ensemble_probs, percentile)
        s = np.where(ensemble_probs >= threshold_ensemble, 1, 0)
        
        # 5. Train PU XGBoost Classifier
        self.pu_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.05,
            random_state=self.random_state,
            eval_metric='logloss',
            n_jobs=-1
        )
        self.pu_model.fit(X, s)
        
        # 6. Calibrate labeling constant c using positive predictions (Elkan-Noto)
        pos_indices = np.where(s == 1)[0]
        if len(pos_indices) > 0:
            pos_probs = self.pu_model.predict_proba(X.iloc[pos_indices])[:, 1]
            self.pu_c = float(np.mean(pos_probs))
            if self.pu_c < 1e-5:
                self.pu_c = 1e-5
        else:
            self.pu_c = 1.0
            
        # 7. Calibrate final decision threshold on PU probabilities
        pu_probs = self.predict_proba(X)
        self.threshold = float(np.percentile(pu_probs, percentile))

    def _predict_proba_ensemble(self, X: pd.DataFrame) -> np.ndarray:
        """Internal helper to calculate ensembled GMM-IF + Autoencoder scores."""
        X_clust = self._get_clustering_features(X)
        
        # GMM soft probabilities
        gmm_probs = self.gmm.predict_proba(X_clust)
        
        # Calculate Shannon entropy: H = -sum(P * log2(P))
        eps = 1e-9
        entropy = -np.sum(gmm_probs * np.log2(gmm_probs + eps), axis=1)
        max_entropy = np.log2(self.n_cohorts)
        
        # Scale normalized entropy between 0.0 and 1.0
        norm_entropy = np.clip(entropy / max_entropy, 0.0, 1.0)
        
        # Map dynamic weights: high entropy -> higher Autoencoder weight (range: 0.2 to 0.8)
        w_ae = 0.2 + 0.6 * norm_entropy
        w_if = 1.0 - w_ae
        
        # Isolation Forest cohort scores
        n_samples = len(X)
        cohort_scores = np.zeros((n_samples, self.n_cohorts))
        for c_idx, model in self.cohort_models.items():
            if hasattr(model, 'estimators_'):
                scores = model.score_samples(drop_categoricals(X))
                cohort_scores[:, c_idx] = np.clip(-scores, 0.0, 1.0)
            else:
                cohort_scores[:, c_idx] = 0.5
                
        # Blended IF score
        blended_if = np.sum(gmm_probs * cohort_scores, axis=1)
        
        # Autoencoder reconstruction loss
        ae_losses = self._get_autoencoder_losses(X)
        
        # Dynamic weighted sum
        final_scores = w_if * blended_if + w_ae * ae_losses
        return final_scores

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Calculate ensembled anomaly score calibrated via PU-learning and Elkan-Noto correction."""
        if not self.is_trained or self.pu_model is None:
            raise ValueError("Model has not been trained yet.")
        
        # Predict s=1 probability from XGBoost
        g_x = self.pu_model.predict_proba(X)[:, 1]
        
        # Calibrate using Elkan-Noto formula: P(y=1|x) = g(x) / c
        calibrated_probs = np.clip(g_x / self.pu_c, 0.0, 1.0)
        return calibrated_probs

    def predict(self, X: pd.DataFrame, contamination: Optional[float] = None) -> np.ndarray:
        """Predict binary anomalies. Calibrate threshold on the fly if contamination is specified."""
        probs = self.predict_proba(X)
        if contamination is not None:
            # Calibrate threshold on the current prediction batch
            percentile = (1.0 - contamination) * 100
            threshold = float(np.percentile(probs, percentile))
        else:
            threshold = self.threshold
        return np.where(probs >= threshold, 1, 0).astype(int)

    def get_raw_model(self) -> Any:
        """Return the trained XGBoost model for TreeSHAP explainability."""
        return self.pu_model
