# Project Phase Directory Mapping

This document maps all files in the repository to their respective development and execution phases.

---

## 1. Phase Mapping Table

| Phase | Files | Description |
| :--- | :--- | :--- |
| **1. Exploratory Data Analysis (EDA)** | `explore_k.py`<br>`scratch/verify_hypotheses.py` | Analyzes dataset properties, tests structural clustering metrics ($K$ selection), and validates unsupervised anomaly outputs. |
| **2. Database & Data Ingestion** | `clean_and_build_db.py` | Normalizes types, handles date formats, and loads raw transaction files into a structured, indexed SQLite database. |
| **3. Feature Engineering** | `src/pipeline/data_loaders.py`<br>`src/pipeline/preprocessors.py` | Aggregates transactional data over rolling windows, calculates Benford/Markov scores, and computes Z-scores/velocity ratios. |
| **4. Modeling & Machine Learning** | `src/pipeline/protocols.py`<br>`src/pipeline/models.py`<br>`src/pipeline/orchestrator.py`<br>`src/pipeline/plugins.py` | Defines interfaces, implements GMM clustering, trains Isolation Forest and Autoencoder ensembles, and runs calibrated PU-Learning XGBoost. |
| **5. Explainable AI (xAI)** | `src/pipeline/explainers.py` | Generates TreeSHAP local explanations, detects toxic feature interaction pairs, and executes binary search counterfactuals. |
| **6. Inference & Execution** | `run_pipeline.py` | Executes the end-to-end training and inference demonstration, outputting alerts to the console and exporting CSV files. |
| **7. System Documentation** | `README.md`<br>`PIPELINE.md`<br>`DATA_USAGE.md`<br>`PHASE_DIRECTORY.md` | Provides deployment instructions, database column maps, mathematical formulations, and directory mappings. |

---

## 2. Detailed File Descriptions by Phase

### Phase 1: Exploratory Data Analysis (EDA)
*   [explore_k.py](explore_k.py): Loads distinct customer profiles, scales demographic and wealth features, and tests Gaussian Mixture Models (GMM) from $K=2$ to $K=8$ using BIC, AIC, and Silhouette scores to find optimal cohort sizes.
*   `scratch/verify_hypotheses.py`: Verifies GMM Isolation Forest and PyTorch Autoencoder scores on the test set, analyzing distributions and modeling performance.

### Phase 2: Database & Data Ingestion
*   [clean_and_build_db.py](clean_and_build_db.py): Prepares schemas and table definitions, standardizes inconsistent dates and booleans, streams raw data files in batches, and builds indexing on `CUSTOMER_NUMBER` for quick joins.

### Phase 3: Feature Engineering
*   [src/pipeline/data_loaders.py](src/pipeline/data_loaders.py): Contains SQL queries to perform rolling window sums/counts (24h, 7d) and joins, and computes Benford's Law deviation and Markov Chain sequential rarity mappings.
*   [src/pipeline/preprocessors.py](src/pipeline/preprocessors.py): Computes high-signal ratios like transaction size Z-score, checking account balance coverage, and rolling velocity ratios (24h vs 7d).

### Phase 4: Modeling & Machine Learning
*   [src/pipeline/protocols.py](src/pipeline/protocols.py): Strictly typed Python Protocols that standardize all pipeline components to ensure clean modularity.
*   [src/pipeline/models.py](src/pipeline/models.py): Implements GMM clustering, cohort-level Isolation Forests, PyTorch Autoencoder reconstruction loss models, entropy-weighted blending, and the calibrated Positive-Unlabeled (PU) XGBoost model.
*   [src/pipeline/orchestrator.py](src/pipeline/orchestrator.py): Coordinates the execution of pipeline steps (Load, Preprocess, Fit, Predict, Explain).
*   [src/pipeline/plugins.py](src/pipeline/plugins.py): Lifecycle hooks used to trace memory consumption, processing times, and custom metrics during pipeline execution.

### Phase 5: Explainable AI (xAI)
*   [src/pipeline/explainers.py](src/pipeline/explainers.py): Leverages TreeSHAP to extract feature attributions, translates contributions to plain-English alerts, extracts positive off-diagonal interaction pairs, and executes binary search to discover counterfactual deltas.

### Phase 6: Inference & Execution
*   [run_pipeline.py](run_pipeline.py): Orchestrates the pipeline run. It outputs sample explanation alerts to the terminal console and exports anomalies to `data/anomaly_alerts_latest.csv`.
