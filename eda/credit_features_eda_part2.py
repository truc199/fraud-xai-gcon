"""
EDA Part 2: Auth Downgrade, IP Hopping, Graph features
(Continued from credit_features_eda.py - fixing column name)
"""
import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'gcontest.db')
conn = sqlite3.connect(DB_PATH)

# =====================================================
# 3. AUTH_DOWNGRADE_RISK analysis
# =====================================================
print("=" * 70)
print("3. AUTH_DOWNGRADE_RISK — Biometric Downgrade on New Device")
print("=" * 70)

df_activity = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, ACTIVITY_NAME, ACTIVITY_DATE
    FROM Data_Activity
    WHERE ACTIVITY_NAME IN ('LOGIN', 'LOGIN_FINGER', 'LOGIN_FACEID')
    ORDER BY CUSTOMER_NUMBER, ACTIVITY_DATE
""", conn)

print(f"Total login activity records: {len(df_activity):,}")

bio_logins = df_activity[df_activity['ACTIVITY_NAME'].isin(['LOGIN_FINGER', 'LOGIN_FACEID'])]
pwd_logins = df_activity[df_activity['ACTIVITY_NAME'] == 'LOGIN']

print(f"Biometric logins (FaceID/Finger): {len(bio_logins):,}")
print(f"Password logins: {len(pwd_logins):,}")

# Per-customer biometric ratio
login_counts = df_activity.groupby('CUSTOMER_NUMBER').agg(
    total=('ACTIVITY_NAME', 'count'),
    bio=('ACTIVITY_NAME', lambda x: (x.isin(['LOGIN_FINGER', 'LOGIN_FACEID'])).sum())
)
login_counts['bio_ratio'] = login_counts['bio'] / login_counts['total']

print(f"\nBiometric usage ratio per customer:")
print(login_counts['bio_ratio'].describe())

# Users with high bio ratio who ALSO have password logins
high_bio = login_counts[login_counts['bio_ratio'] > 0.5]
print(f"\nCustomers with >50% biometric usage: {len(high_bio):,}")

# Check how many of those high-bio users also did password logins
high_bio_custs = set(high_bio.index)
pwd_on_high_bio = pwd_logins[pwd_logins['CUSTOMER_NUMBER'].isin(high_bio_custs)]
unique_downgraders = pwd_on_high_bio['CUSTOMER_NUMBER'].nunique()
print(f"Of those, customers who ALSO used password login (potential downgrade): {unique_downgraders:,}")

# =====================================================
# 4. IP_HOPPING_VELOCITY analysis
# =====================================================
print("\n" + "=" * 70)
print("4. IP_HOPPING_VELOCITY — Unique IPs per Device in 3h Window")
print("=" * 70)

df_ip = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, Device_ID_Hash, IP_Address_Proxy, TRANS_DATE, TRANS_HOUR
    FROM Data_Transaction
    ORDER BY CUSTOMER_NUMBER, TRANS_DATE, TRANS_HOUR
""", conn)

print(f"Total transactions with IP data: {len(df_ip):,}")
print(f"Unique IP/Proxy values: {df_ip['IP_Address_Proxy'].nunique():,}")
print(f"Unique Device_ID_Hash values: {df_ip['Device_ID_Hash'].nunique():,}")

# Per-device unique IP count
ip_per_device = df_ip.groupby('Device_ID_Hash')['IP_Address_Proxy'].nunique()
print(f"\nUnique IPs per device:")
print(ip_per_device.describe())

multi_ip_devices = ip_per_device[ip_per_device > 3]
print(f"\nDevices using 3+ unique IPs: {len(multi_ip_devices):,}")

extreme_ip = ip_per_device[ip_per_device > 10]
print(f"Devices using 10+ unique IPs (suspicious): {len(extreme_ip):,}")

# =====================================================
# 5. Graph Features (Beneficiary Network)
# =====================================================
print("\n" + "=" * 70)
print("5. GRAPH FEATURES — Beneficiary Network Analysis")
print("=" * 70)

df_graph = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, Beneficiary_CUSTOMER_NUMBER
    FROM Data_Transaction
    WHERE Beneficiary_CUSTOMER_NUMBER IS NOT NULL 
      AND Beneficiary_CUSTOMER_NUMBER != ''
      AND Beneficiary_CUSTOMER_NUMBER != CUSTOMER_NUMBER
""", conn)

print(f"Transfer edges (sender->receiver): {len(df_graph):,}")
print(f"Unique senders: {df_graph['CUSTOMER_NUMBER'].nunique():,}")
print(f"Unique receivers: {df_graph['Beneficiary_CUSTOMER_NUMBER'].nunique():,}")

# In-degree distribution (who receives from many people)
in_degree = df_graph.groupby('Beneficiary_CUSTOMER_NUMBER')['CUSTOMER_NUMBER'].nunique()
print(f"\nIn-degree (unique senders per receiver):")
print(in_degree.describe())

high_indegree = in_degree[in_degree > 10]
print(f"\nReceivers from 10+ unique senders (potential mules): {len(high_indegree):,}")

conn.close()
print("\nDone.")
