# Banking Fraud & xAI Pipeline

An advanced, production-ready machine learning framework for banking fraud detection and Explainable AI (xAI). It combines unsupervised ensemble methods with Positive-Unlabeled (PU) XGBoost classifiers, exact SHAP explanations, joint feature interaction matrices, and decision boundary counterfactual alerts.

For a detailed breakdown of the mathematical formulations, preprocessing steps, and architectural choices, see [PIPELINE.md](PIPELINE.md).

---

## 1. Setup & Data Requirements

The raw datasets are large and excluded from version control. You must manually acquire and place the raw datasets inside the `data/` directory before running the pipeline.

### Required Directory Structure
Ensure your `data/` folder is structured as follows:
```
gcontest/
└── data/
    ├── 0.Data Guidline.xlsx       # Metadata guidelines sheet
    ├── Data_Customer.csv          # Customer profile demographics
    ├── Data_Transaction.csv       # Financial transaction logs
    ├── Data_Activity.csv          # Digital activity audit trails
    ├── Data_Deposit.csv           # checking/saving balances
    ├── Data_Lending.csv           # Lending and liability accounts
    └── Data_Card.csv              # Credit/debit card profiles
```

---

## 2. Step-by-Step Execution Guide

### Step 1: Install Dependencies
This project uses `uv` for ultra-fast, reproducible dependency management. Install the required libraries into the local virtual environment:
```bash
uv add scikit-learn shap openpyxl pandas xgboost torch
```

### Step 2: Clean Data & Build SQLite Database
Run the preprocessor builder to clean the raw files and ingest them into a fast, indexed SQLite database:
```bash
uv run clean_and_build_db.py
```
**What this does**:
* Extracts database definitions and standardizes column name mismatches.
* Normalizes dates to `YYYY-MM-DD` and string flags to binary `1`/`0` booleans.
* Loads CSVs in streaming batches to limit RAM footprint.
* Builds high-performance indexes on `CUSTOMER_NUMBER` for immediate database queries.

### Step 3: Run the End-to-End Pipeline
Run the demonstration script to train the hybrid models, run inference, generate explanations, and output flagged alerts:
```bash
uv run run_pipeline.py
```
**What this does**:
* Evaluates cohort structures using Gaussian Mixture Model (GMM).
* Computes unsupervised anomalies blending Isolation Forests and PyTorch Autoencoders.
* Refines thresholds using a sample-weighted PU-Learning XGBoost classifier.
* Calculates TreeSHAP attributions, off-diagonal interaction pairs (toxic combinations), and decision boundary counterfactual target values.
* Exports anomaly alerts and component configuration files to the `data/` folder.

---

## 3. Pipeline Output Files

Running `run_pipeline.py` creates the following files in the `data/` directory:

*   `data/anomaly_alerts_latest.csv`: Latest anomaly-only transaction alerts (filtered by prediction flag). Features reordered to display critical xAI outputs (`CUSTOMER_NUMBER`, `ANOMALY_SCORE`, `EXPLANATION`, `TOP_SHAP_CONTRIBUTORS`, `TOP_INTERACTIONS`, `COUNTERFACTUAL`) first.
*   `data/anomaly_alerts_latest_metadata.json`: A companion metadata JSON mapping the **exact classes and components** (e.g. data loader, preprocessor, model agent, explainer, plugins) used in that specific pipeline run.
*   `data/exports/anomaly_alerts_YYYYMMDD_HHMMSS.csv`: Timestamped CSV archive of the anomaly alerts.
*   `data/exports/anomaly_alerts_YYYYMMDD_HHMMSS_metadata.json`: Timestamped companion JSON metadata configuration archive.

---

## 4. Component Extensions Policy (No Code Deletion)

The pipeline enforces separation of concerns via strictly typed Python Protocols (`src/pipeline/protocols.py`). When testing new pipeline modules:

1.  **NEVER delete or overwrite existing component code** in the codebase (e.g., in `src/pipeline/data_loaders.py`).
2.  **Create a new file** in the appropriate directory (e.g. `src/pipeline/second_order_markov_loader.py`).
3.  **Implement your new class** (e.g., `SecondOrderMarkovDataLoader`) conforming to the target Protocol.
4.  **Plug the new component** into `run_pipeline.py` by importing it and swapping instances in the initialization block:
    ```python
    data_loader = SecondOrderMarkovDataLoader(db_path=DB_PATH)
    ```
