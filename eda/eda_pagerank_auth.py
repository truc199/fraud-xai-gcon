import sqlite3
import pandas as pd
import numpy as np
import networkx as nx
import os
import json

# Ensure eda/outputs directory exists
os.makedirs("eda/outputs", exist_ok=True)

db_path = "data/gcontest.db"
conn = sqlite3.connect(db_path)

print("--- EDA: PAGERANK_SCORE ---")
query = """
SELECT CUSTOMER_NUMBER, Beneficiary_CUSTOMER_NUMBER
FROM Data_Transaction
WHERE Beneficiary_CUSTOMER_NUMBER IS NOT NULL
  AND Beneficiary_CUSTOMER_NUMBER != 'UNKNOWN'
  AND Beneficiary_CUSTOMER_NUMBER != ''
"""
df_edges = pd.read_sql_query(query, conn)
print(f"Total edges loaded: {len(df_edges)}")

G = nx.DiGraph()
for _, row in df_edges.iterrows():
    sender = str(row['CUSTOMER_NUMBER'])
    receiver = str(row['Beneficiary_CUSTOMER_NUMBER'])
    if G.has_edge(sender, receiver):
        G[sender][receiver]['weight'] += 1
    else:
        G.add_edge(sender, receiver, weight=1)

print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
pagerank = nx.pagerank(G, weight='weight', max_iter=100)
pr_values = list(pagerank.values())
print(f"PageRank Mean: {np.mean(pr_values):.10f}")
print(f"PageRank Max:  {np.max(pr_values):.10f}")
print(f"PageRank Min:  {np.min(pr_values):.10f}")

# Propose scaling: multiply by N or take log1p(score * N) or MinMax
scaled_pr = [pr * G.number_of_nodes() for pr in pr_values]
print(f"Scaled (xN) Mean: {np.mean(scaled_pr):.4f}")
print(f"Scaled (xN) Max:  {np.max(scaled_pr):.4f}")

# Save EDA output
with open("eda/outputs/pagerank_eda.json", "w") as f:
    json.dump({
        "mean_raw": np.mean(pr_values),
        "max_raw": np.max(pr_values),
        "mean_scaled": np.mean(scaled_pr),
        "max_scaled": np.max(scaled_pr)
    }, f, indent=4)

print("\n--- EDA: AUTH_DOWNGRADE_RISK ---")
# Let's analyze Data_Activity for Biometric ratios and Data_Transaction for Device_ID_Hash
# See how many customers have bio_ratio >= 0.6
act_query = """
SELECT CUSTOMER_NUMBER, ACTIVITY_NAME
FROM Data_Activity
WHERE ACTIVITY_NAME IN ('LOGIN', 'LOGIN_FINGER', 'LOGIN_FACEID')
"""
act_df = pd.read_sql_query(act_query, conn)
act_df['IS_BIOMETRIC'] = act_df['ACTIVITY_NAME'].isin(['LOGIN_FINGER', 'LOGIN_FACEID']).astype(int)

cust_bio = act_df.groupby('CUSTOMER_NUMBER').agg(
    total_logins=('IS_BIOMETRIC', 'count'),
    bio_logins=('IS_BIOMETRIC', 'sum')
).reset_index()
cust_bio['bio_ratio'] = cust_bio['bio_logins'] / cust_bio['total_logins']

high_bio_custs = cust_bio[cust_bio['bio_ratio'] >= 0.6]
print(f"Total customers with logins: {len(cust_bio)}")
print(f"Customers with bio_ratio >= 0.6: {len(high_bio_custs)}")

# Check Device_ID_Hash in Data_Transaction for these customers
high_bio_list = tuple(high_bio_custs['CUSTOMER_NUMBER'].tolist())
# Limit query size for speed if necessary, but we can do it via SQL
tx_device_query = f"""
SELECT CUSTOMER_NUMBER, Device_ID_Hash, COUNT(*) as tx_count
FROM Data_Transaction
WHERE CUSTOMER_NUMBER IN {high_bio_list[:1000]} -- Sample 1000 customers for speed
  AND Device_ID_Hash IS NOT NULL AND Device_ID_Hash != 'UNKNOWN'
GROUP BY CUSTOMER_NUMBER, Device_ID_Hash
"""
tx_device = pd.read_sql_query(tx_device_query, conn)
device_counts = tx_device.groupby('CUSTOMER_NUMBER')['Device_ID_Hash'].nunique()
print(f"Avg devices per high-bio customer (in sample): {device_counts.mean():.2f}")
print(f"Customers with > 1 device: {(device_counts > 1).sum()}")

conn.close()
