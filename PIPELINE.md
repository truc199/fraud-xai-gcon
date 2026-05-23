# Modular Cohort Fraud & xAI Pipeline Documentation

A production-grade, highly modular, protocol-driven machine learning pipeline for banking fraud detection and Explainable AI (xAI). 

---

## 1. Directory Structure

```
gcontest/
├── PIPELINE.md                 # This documentation file
├── run_pipeline.py             # Pipeline demo entrypoint
├── clean_and_build_db.py       # SQLite database builder and data cleaning script
├── data/
│   ├── gcontest.db             # Consolidated SQLite Database (1.1 GB)
│   ├── anomaly_alerts_latest.csv   # Latest anomaly-only export (overwritten each run)
│   ├── exports/                # Timestamped anomaly export archive
│   ├── legend_*.csv            # Cleaned data dictionary reference files
│   └── Data_*.csv              # Raw dataset CSV files
└── src/
    └── pipeline/
        ├── protocols.py        # Strict Python interfaces
        ├── data_loaders.py     # SQLite streaming/aggregating loaders
        ├── preprocessors.py    # Math feature engineering
        ├── models.py           # CohortAnomalyModelAgent (GMM + IF + AE + PU-XGBoost)
        ├── explainers.py       # SHAP local explanation translator
        ├── orchestrator.py     # MLPipeline execution coordinator
        └── plugins.py          # Logging and metric plugins
```

---

## 2. Architecture & Components

The pipeline enforces separation of concerns via strictly typed Python Protocols (`typing.Protocol`).

### A. Protocols (`src/pipeline/protocols.py`)
Enforces interfaces for all pluggable modules:
*   `DataLoader`: Standardizes training data loading and batch streaming.
*   `FeaturePreprocessor`: Enforces `fit` and `transform` interfaces.
*   `ModelAgent`: Standardizes training, class predictions, and probabilistic risk scores.
*   `xAIExplainer`: Defines the local feature attribution explanation schema.
*   `PipelinePlugin`: Lifecycle middleware hook methods.

### B. SQLite Data Loader (`src/pipeline/data_loaders.py`)
Queries and aggregates raw transaction files with behavioral metrics using fast, index-optimized SQLite subqueries:
*   **Benford's Law Deviation (`BENFORD_DEV`)**: Calculates the Kullback-Leibler (KL) Divergence between the empirical first-digit distribution of the customer's transaction amounts and Benford's logarithmic distribution:
    $$D_{KL}(P || Q) = \sum_{d=1}^{9} P(d) \log \left( \frac{P(d)}{Q(d)} \right)$$
*   **Sequential Activity Rarity (`ACTIVITY_SEQ_RARITY`)**: Evaluates customer action paths from `Data_Activity`. Fits a global bigram Markov Chain transition matrix, then computes the average log-probability of the customer's sequential actions.
*   **Rolling Window Metrics**: Computes transaction count and amount sums over rolling 24-hour and 7-day windows using SQLite `RANGE` window functions over numeric Julian day values (`julianday(TRANS_DATE) + TRANS_HOUR/24.0`).
*   **Customer Profile Aggregates**: Fetches checking account averages from `Data_Deposit`.

### C. Feature Engineering (`src/pipeline/preprocessors.py`)
Engineers 26 features, including high-signal anomaly indicators:
*   **`BENFORD_DEV`**: Detects structured or synthetic digit distributions (often present in bot networks or manually spoofed transfers).
*   **`ACTIVITY_SEQ_RARITY`**: Identifies unusual sequential action patterns (e.g. password resets followed immediately by high-value transfers).
*   **`VELOCITY_RATIO_AMOUNT_24H_VS_7D`**: Ratio of 24h transaction volume to 7d volume. Detects sudden monetary cash-out spikes.
*   **`VELOCITY_RATIO_COUNT_24H_VS_7D`**: Ratio of 24h transaction count to 7d count. Detects high-speed transaction frequency bursts.
*   **`TRANS_AMOUNT_Z_SCORE`**: Ratio of current transaction amount to customer's historical average amount.
*   **`BALANCE_COVERAGE_RATIO`**: Ratio of transaction size to average monthly account balance.

### D. Model Agent (`src/pipeline/models.py`)
Implements `CohortAnomalyModelAgent`, a 4-stage hybrid anomaly detection model:

**Stage 1 — Unsupervised Ensemble (Label Generation)**:
*   **Soft Cohort Clustering**: Runs Gaussian Mixture Model (GMM) on demographic/wealth profiles (`CUSTOMER_AGE`, `TENURE_DAYS`, `HIST_AVG_CA_BALANCE`, `HIST_AVG_TRANS_AMOUNT`) to assign customers soft probabilities into $N$ cohorts.
*   **Cohort Isolation Forests**: Trains a dedicated `IsolationForest` on transaction features for each cohort, then blends their anomaly scores using GMM cohort probabilities.
*   **Deep Autoencoder**: Trains a PyTorch MLP Autoencoder on normal transactions. The MSE reconstruction loss is normalized by the training 99th percentile MSE (`max_train_mse`).
*   **Entropy-Weighted Blending**: Shannon entropy of GMM cohort probabilities dynamically balances GMM-IF and Autoencoder weights:
    *   High entropy (ambiguous cohort fit) $\rightarrow$ higher Autoencoder weight (up to 0.8), relying on global reconstruction patterns.
    *   Low entropy (clear cohort fit) $\rightarrow$ higher GMM Isolation Forest weight (up to 0.8), relying on cohort boundaries.

**Stage 2 — Positive-Unlabeled (PU) Learning (Refinement)**:
*   The top `contamination` fraction of ensemble scores are treated as positive labels ($s = 1$), the rest as unlabeled ($s = 0$).
*   An `XGBClassifier` is trained to predict $s$ from preprocessed features, learning non-linear decision boundaries.
*   **Elkan-Noto Calibration**: Computes the labeling constant $c = \text{mean}(P(s=1|x) \text{ for } s == 1)$. At inference, probabilities are calibrated: $P(y=1|x) = \min(P(s=1|x) / c, 1.0)$.
*   `get_raw_model()` returns the trained XGBoost model, enabling exact `TreeSHAP` explainability.

### E. Explainable AI Engine (`src/pipeline/explainers.py`)
Computes mathematical feature contributions and counterfactuals using **SHAP (SHapley Additive exPlanations)**:
*   **Feature Attribution**: Extracts local SHAP feature attributions on a per-prediction basis. Sorts features by positive contribution weight (risk drivers) and generates natural language narratives translating numbers to business rationale.
*   **SHAP Interaction Values (Phase 3.1)**: Computes the exact joint contribution of feature pairs using TreeSHAP interaction values ($N \times F \times F$ matrix). Surrounds off-diagonal values to isolate toxic pairs where individual features might seem benign, but their combination triggers anomalies (e.g. `HIST_AVG_TRANS_AMOUNT × SUM_AMOUNT_24H`).
*   **Decision Boundary Counterfactuals (Phase 3.2)**: For each anomaly, executes binary search on top SHAP drivers to determine the minimal change in feature values needed to drop the calibrated anomaly score below the decision threshold. Filters out zero-delta counterfactuals (where single-feature adjustment is insufficient to clear the alert).

---

## 3. Dynamic Threshold Calibration & Alert Volume

The model supports calibration of the decision boundary threshold on-the-fly using a target `contamination` rate.

Evaluation results on the test dataset (5,000 transactions) under different contamination levels:
| Contamination Rate | Training Threshold | Test Alerts Flagged | Alert Rate | Description / Trade-off |
| :--- | :--- | :--- | :--- | :--- |
| **0.01** | `0.6169` | 21 | 0.42% | Extremely high precision, high leakage risk (low recall). |
| **0.02** | `0.5721` | 64 | 1.28% | Balanced high-precision alerts. |
| **0.03** | `0.5441` | 114 | 2.28% | **Recommended baseline**. Strong recall with manageable alert volume. |
| **0.05** | `0.5046` | 226 | 4.52% | Maximum recall, high manual verification cost (higher false positives). |

---

## 4. Output & Export

Each pipeline run exports anomaly-only results to CSV for human analyst review:
*   `data/anomaly_alerts_latest.csv` — overwritten each run (latest snapshot).
*   `data/exports/anomaly_alerts_YYYYMMDD_HHMMSS.csv` — timestamped archive for audit trail.

Exported columns per anomaly row:
| Column | Description |
| :--- | :--- |
| `CUSTOMER_NUMBER` | Customer identifier. |
| `ANOMALY_PRED` | Binary flag (always `1` in export). |
| `ANOMALY_SCORE` | Calibrated PU-XGBoost risk probability (0.0–1.0). |
| `EXPLANATION` | Natural language narrative describing why flagged. |
| `TOP_SHAP_CONTRIBUTORS` | Top 3 SHAP feature drivers with log-odds contributions. |
| `TOP_INTERACTIONS` | Joint feature interaction pairs with interaction values. |
| `COUNTERFACTUAL` | Actionable target states (`original -> safe_value (delta)`) to clear the anomaly flag. |
| *(remaining columns)* | All raw transaction and profile fields for cross-reference. |

---

## 5. Run & Execution

### Installation
Run this command in the workspace root to pull all required libraries:
```bash
uv add scikit-learn shap openpyxl pandas xgboost torch
```

### Execution
Run the end-to-end training and inference demonstration:
```bash
uv run run_pipeline.py
```
*Note: Memory usage remains `< 150MB` throughout training and inference.*
