import sqlite3
import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import os

DB_PATH = "data/gcontest.db"

def explore_k():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # Query cohort features for distinct customers
    query = """
        WITH deposit_agg AS (
            SELECT CUSTOMER_NUMBER, AVG(AVG_CA_BALANCE) as HIST_AVG_CA_BALANCE 
            FROM Data_Deposit GROUP BY CUSTOMER_NUMBER
        ),
        trans_agg AS (
            SELECT CUSTOMER_NUMBER, AVG(TRANS_AMOUNT) as HIST_AVG_TRANS_AMOUNT, COUNT(*) as HIST_TRANS_COUNT
            FROM Data_Transaction GROUP BY CUSTOMER_NUMBER
        )
        SELECT 
            c.CUSTOMER_NUMBER,
            (strftime('%Y', 'now') - strftime('%Y', c.DATE_OF_BIRTH)) as CUSTOMER_AGE,
            (julianday('now') - julianday(c.CLIENT_CREATE_DATE)) as TENURE_DAYS,
            COALESCE(d.HIST_AVG_CA_BALANCE, 0.0) as HIST_AVG_CA_BALANCE,
            COALESCE(ta.HIST_AVG_TRANS_AMOUNT, 0.0) as HIST_AVG_TRANS_AMOUNT,
            COALESCE(ta.HIST_TRANS_COUNT, 0) as HIST_TRANS_COUNT
        FROM Data_Customer c
        LEFT JOIN deposit_agg d ON c.CUSTOMER_NUMBER = d.CUSTOMER_NUMBER
        LEFT JOIN trans_agg ta ON c.CUSTOMER_NUMBER = ta.CUSTOMER_NUMBER
    """
    
    print("Loading customer data from database...")
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Data preprocessing
    features = ['CUSTOMER_AGE', 'TENURE_DAYS', 'HIST_AVG_CA_BALANCE', 'HIST_AVG_TRANS_AMOUNT', 'HIST_TRANS_COUNT']
    X = df[features].fillna(0.0)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Use 20,000 samples for GMM and 3,000 for Silhouette (due to O(N^2) memory/time)
    np.random.seed(42)
    sample_indices = np.random.choice(len(X_scaled), min(len(X_scaled), 20000), replace=False)
    X_sample = X_scaled[sample_indices]
    
    silhouette_indices = np.random.choice(len(X_scaled), min(len(X_scaled), 3000), replace=False)
    X_sil_sample = X_scaled[silhouette_indices]

    print("\n--- GMM Clustering Evaluation ---")
    print(f"Evaluating K from 2 to 8 (using {len(X_sample)} customer samples)...")
    print(f"{'K':<5} | {'BIC':<15} | {'AIC':<15} | {'Silhouette':<12}")
    print("-" * 55)

    best_k_bic = None
    min_bic = float('inf')
    
    for k in range(2, 9):
        gmm = GaussianMixture(n_components=k, random_state=42, n_init=1)
        gmm.fit(X_sample)
        
        bic = gmm.bic(X_sample)
        aic = gmm.aic(X_sample)
        
        # Silhouette Score calculation
        labels = gmm.predict(X_sil_sample)
        # Avoid error if all samples assigned to 1 cluster
        if len(np.unique(labels)) > 1:
            sil = silhouette_score(X_sil_sample, labels)
        else:
            sil = -1.0
            
        print(f"{k:<5} | {bic:<15,.2f} | {aic:<15,.2f} | {sil:<12.4f}")
        
        if bic < min_bic:
            min_bic = bic
            best_k_bic = k
            
    print("-" * 55)
    print(f"Optimal K based on minimum BIC: {best_k_bic}")

if __name__ == "__main__":
    explore_k()
