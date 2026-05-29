import os
import pandas as pd
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.pipeline.fraud_2026_data_loader import Fraud2026DataLoader

db_path = 'data/gcontest.db'
if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    sys.exit(1)

print("Loading data using Fraud2026DataLoader...")
loader = Fraud2026DataLoader(db_path=db_path)
# Just load a sample of 5000 exactly like the pipeline did for the evaluation
df = loader.load_training_data(limit=5000)

new_features = [
    'BENFORD_DEV',
    'IP_HOPPING_VELOCITY',
    'PAGERANK_SCORE',
    'IN_DEGREE_CENTRALITY',
    'BUST_OUT_UTILIZATION',
    'STRUCTURING_OVERPAYMENT_FLAG',
    'AUTH_DOWNGRADE_RISK'
]

print("\n--- Descriptive Statistics for New 2026 Features (Sample N=5000) ---")
print(df[new_features].describe().T)

print("\n--- Non-zero counts ---")
for feat in new_features:
    non_zeros = (df[feat] > 0).sum()
    print(f"{feat}: {non_zeros} / {len(df)} ({(non_zeros/len(df))*100:.2f}%)")
