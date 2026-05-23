import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Optional, Any, Dict

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

class EWCModelAgent:
    """ModelAgent wrapping a PyTorch Autoencoder with Elastic Weight Consolidation (EWC) continuous learning capability."""
    def __init__(self, contamination: float = 0.03, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ae: Optional[PyTorchAutoencoder] = None
        self.feature_means: Optional[np.ndarray] = None
        self.feature_stds: Optional[np.ndarray] = None
        self.max_train_mse = 1.0
        self.threshold = 0.5
        self.is_trained = False
        
        # EWC State
        self.fisher_diagonal: Dict[str, torch.Tensor] = {}
        self.old_params: Dict[str, torch.Tensor] = {}

    def _normalize(self, X: pd.DataFrame) -> np.ndarray:
        """Standardize input features for Autoencoder training/inference."""
        arr = X.values.astype(np.float32)
        if self.feature_means is None or self.feature_stds is None:
            self.feature_means = np.mean(arr, axis=0)
            self.feature_stds = np.std(arr, axis=0) + 1e-5
        return (arr - self.feature_means) / self.feature_stds

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None, epochs: int = 15, batch_size: int = 256) -> None:
        """Train the base Autoencoder on clean/historical data."""
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
                
        self.ae.eval()
        with torch.no_grad():
            reconstructed = self.ae(dataset)
            mse_per_row = torch.mean((dataset - reconstructed) ** 2, dim=1).cpu().numpy()
            self.max_train_mse = float(np.percentile(mse_per_row, 100 * (1 - self.contamination))) + 1e-5
            self.threshold = self.max_train_mse
            
        self.is_trained = True

    def calculate_fisher(self, X: pd.DataFrame) -> None:
        """Calculate the diagonal of the Fisher Information Matrix (FIM) for parameters."""
        if self.ae is None:
            raise ValueError("Model is not trained yet.")
            
        X_norm = self._normalize(X)
        dataset = torch.tensor(X_norm, dtype=torch.float32).to(self.device)
        
        self.ae.eval()
        
        # Initialize Fisher diagonal elements and cache old parameters
        self.fisher_diagonal = {}
        self.old_params = {}
        for name, param in self.ae.named_parameters():
            if param.requires_grad:
                self.fisher_diagonal[name] = torch.zeros_like(param.data)
                self.old_params[name] = param.data.clone()
                
        # Calculate gradients sample-by-sample to construct Fisher diagonal
        criterion = nn.MSELoss()
        for x in dataset:
            self.ae.zero_grad()
            x_single = x.unsqueeze(0)
            output = self.ae(x_single)
            loss = criterion(output, x_single)
            loss.backward()
            
            for name, param in self.ae.named_parameters():
                if param.requires_grad and param.grad is not None:
                    self.fisher_diagonal[name] += (param.grad.data ** 2) / len(dataset)
                    
    def fit_online(self, X_new: pd.DataFrame, lambda_ewc: float = 50.0, epochs: int = 5, batch_size: int = 256) -> None:
        """Retrain the model parameters on new drifted data, regularized by the EWC penalty."""
        if self.ae is None:
            raise ValueError("Model is not trained yet.")
            
        X_norm = self._normalize(X_new)
        dataset = torch.tensor(X_norm, dtype=torch.float32).to(self.device)
        
        optimizer = optim.Adam(self.ae.parameters(), lr=0.005)
        criterion = nn.MSELoss()
        
        self.ae.train()
        for epoch in range(epochs):
            permutation = torch.randperm(dataset.size()[0])
            for i in range(0, dataset.size()[0], batch_size):
                indices = permutation[i:i+batch_size]
                batch = dataset[indices]
                
                optimizer.zero_grad()
                outputs = self.ae(batch)
                loss_mse = criterion(outputs, batch)
                
                # Compute quadratic parameter-shift penalty
                loss_ewc = 0.0
                for name, param in self.ae.named_parameters():
                    if name in self.fisher_diagonal:
                        fisher = self.fisher_diagonal[name]
                        old_val = self.old_params[name]
                        loss_ewc += torch.sum(fisher * (param - old_val) ** 2)
                        
                loss_total = loss_mse + (lambda_ewc / 2.0) * loss_ewc
                loss_total.backward()
                optimizer.step()
                
        self.ae.eval()
        with torch.no_grad():
            reconstructed = self.ae(dataset)
            mse_per_row = torch.mean((dataset - reconstructed) ** 2, dim=1).cpu().numpy()
            self.max_train_mse = float(np.percentile(mse_per_row, 100 * (1 - self.contamination))) + 1e-5
            self.threshold = self.max_train_mse

    def predict_proba(self, X: Any) -> np.ndarray:
        """Compute relative Autoencoder reconstruction anomaly score."""
        if self.ae is None:
            raise ValueError("Model is not trained yet.")
            
        if isinstance(X, pd.DataFrame):
            X_norm = self._normalize(X)
        else:
            X_norm = (np.asarray(X) - self.feature_means) / self.feature_stds
            
        dataset = torch.tensor(X_norm, dtype=torch.float32).to(self.device)
        
        self.ae.eval()
        with torch.no_grad():
            reconstructed = self.ae(dataset)
            mse_per_row = torch.mean((dataset - reconstructed) ** 2, dim=1).cpu().numpy()
            
        scores = np.clip(mse_per_row / self.max_train_mse, 0.0, 1.0)
        return scores

    def predict(self, X: Any) -> np.ndarray:
        """Predict binary anomalies based on reconstruction threshold."""
        probs = self.predict_proba(X)
        return (probs >= 1.0).astype(int)

    def get_raw_model(self) -> Any:
        """Return raw Autoencoder module."""
        return self.ae
