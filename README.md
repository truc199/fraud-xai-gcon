# Banking Fraud & xAI Pipeline

An advanced, production-ready machine learning framework for banking fraud detection and Explainable AI (xAI). It combines unsupervised ensemble methods with Positive-Unlabeled (PU) XGBoost classifiers, exact SHAP explanations, joint feature interaction matrices, and decision boundary counterfactual alerts.

For a detailed breakdown of the mathematical formulations, preprocessing steps, and architectural choices, see [PIPELINE.md](file:///home/hoang/python/gcontest/PIPELINE.md).

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
uv sync
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
* Overwrites `data/anomaly_alerts_latest.csv` and saves a timestamped CSV archive under `data/exports/` listing anomalies only.
