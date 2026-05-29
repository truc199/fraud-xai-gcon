"""
EDA: Validate credit & advanced features from Data_Card and Data_Transaction.
Check the discriminative power of:
  1. BUST_OUT_UTILIZATION (LIMIT_UTILIZATION_VELOCITY)
  2. STRUCTURING_OVERPAYMENT_FLAG
  3. AUTH_DOWNGRADE_RISK
  4. IP_HOPPING_VELOCITY
  5. PAGERANK_SCORE / IN_DEGREE_CENTRALITY
"""
import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'gcontest.db')
conn = sqlite3.connect(DB_PATH)

# =====================================================
# 1. Data_Card: Credit utilization analysis
# =====================================================
print("=" * 70)
print("1. BUST_OUT_UTILIZATION — Credit Card Utilization from Data_Card")
print("=" * 70)

df_card = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, MONTH, LIMIT_AMT_CREDIT, OUTSTANDING_BAL_CREDIT
    FROM Data_Card
""", conn)

print(f"Total Data_Card records: {len(df_card):,}")
print(f"Unique customers in Data_Card: {df_card['CUSTOMER_NUMBER'].nunique():,}")

# Check how many have credit limits > 0
df_card['LIMIT_AMT_CREDIT'] = pd.to_numeric(df_card['LIMIT_AMT_CREDIT'], errors='coerce').fillna(0)
df_card['OUTSTANDING_BAL_CREDIT'] = pd.to_numeric(df_card['OUTSTANDING_BAL_CREDIT'], errors='coerce').fillna(0)

has_credit = df_card[df_card['LIMIT_AMT_CREDIT'] > 0]
print(f"Records with credit limit > 0: {len(has_credit):,}")
print(f"Customers with active credit cards: {has_credit['CUSTOMER_NUMBER'].nunique():,}")

if not has_credit.empty:
    has_credit = has_credit.copy()
    has_credit['utilization'] = has_credit['OUTSTANDING_BAL_CREDIT'] / has_credit['LIMIT_AMT_CREDIT']
    
    print(f"\nCredit Utilization Distribution:")
    print(has_credit['utilization'].describe())
    
    # High utilization (bust-out risk)
    high_util = has_credit[has_credit['utilization'] > 0.8]
    print(f"\nHigh utilization (>80%): {high_util['CUSTOMER_NUMBER'].nunique():,} customers")
    
    extreme_util = has_credit[has_credit['utilization'] > 0.95]
    print(f"Extreme utilization (>95%): {extreme_util['CUSTOMER_NUMBER'].nunique():,} customers")
    
    # Month-over-month velocity
    has_credit_sorted = has_credit.sort_values(['CUSTOMER_NUMBER', 'MONTH'])
    has_credit_sorted['prev_util'] = has_credit_sorted.groupby('CUSTOMER_NUMBER')['utilization'].shift(1)
    has_credit_sorted['util_change'] = has_credit_sorted['utilization'] - has_credit_sorted['prev_util']
    
    valid_changes = has_credit_sorted.dropna(subset=['util_change'])
    if not valid_changes.empty:
        print(f"\nMonth-over-Month Utilization Change:")
        print(valid_changes['util_change'].describe())
        
        spike = valid_changes[valid_changes['util_change'] > 0.3]
        print(f"\nUtilization spike > 30% in one month: {spike['CUSTOMER_NUMBER'].nunique():,} customers ({len(spike):,} records)")
else:
    print("No credit card data found.")

# =====================================================
# 2. STRUCTURING_OVERPAYMENT_FLAG
# =====================================================
print("\n" + "=" * 70)
print("2. STRUCTURING_OVERPAYMENT_FLAG — Credit Card Repayment Pattern")
print("=" * 70)

df_repay = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, TRANS_DATE, TRANS_AMOUNT, TRANS_LV2
    FROM Data_Transaction
    WHERE TRANS_LV2 LIKE '%Credit_card%' OR TRANS_LV2 LIKE '%credit%'
    ORDER BY CUSTOMER_NUMBER, TRANS_DATE
""", conn)

print(f"Total credit card repayment transactions: {len(df_repay):,}")
print(f"Unique customers making CC repayments: {df_repay['CUSTOMER_NUMBER'].nunique():,}")

if not df_repay.empty:
    # Frequency of repayments per customer
    repay_freq = df_repay.groupby('CUSTOMER_NUMBER').size()
    print(f"\nRepayment frequency per customer:")
    print(repay_freq.describe())
    
    multi_repay = repay_freq[repay_freq >= 2]
    print(f"\nCustomers with 2+ repayments: {len(multi_repay):,}")
    
    # Check overpayment potential
    if not has_credit.empty:
        # Get max outstanding per customer
        max_outstanding = has_credit.groupby('CUSTOMER_NUMBER')['OUTSTANDING_BAL_CREDIT'].max()
        total_repay = df_repay.groupby('CUSTOMER_NUMBER')['TRANS_AMOUNT'].sum()
        
        merged = pd.DataFrame({
            'total_repaid': total_repay,
            'max_outstanding': max_outstanding
        }).dropna()
        
        overpaid = merged[merged['total_repaid'] > merged['max_outstanding']]
        print(f"\nCustomers whose total repayments EXCEED max outstanding: {len(overpaid):,}")
        if not overpaid.empty:
            overpaid['excess_ratio'] = overpaid['total_repaid'] / overpaid['max_outstanding']
            print(f"Average excess ratio: {overpaid['excess_ratio'].mean():.2f}x")
else:
    print("No credit card repayment transactions found.")

# =====================================================
# 3. AUTH_DOWNGRADE_RISK analysis
# =====================================================
print("\n" + "=" * 70)
print("3. AUTH_DOWNGRADE_RISK — Biometric Downgrade on New Device")
print("=" * 70)

df_activity = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, ACTIVITY, ACTIVITY_DATE
    FROM Data_Activity
    WHERE ACTIVITY IN ('LOGIN', 'LOGIN_FINGER', 'LOGIN_FACEID')
    ORDER BY CUSTOMER_NUMBER, ACTIVITY_DATE
""", conn)

print(f"Total login activity records: {len(df_activity):,}")

if not df_activity.empty:
    bio_logins = df_activity[df_activity['ACTIVITY'].isin(['LOGIN_FINGER', 'LOGIN_FACEID'])]
    pwd_logins = df_activity[df_activity['ACTIVITY'] == 'LOGIN']
    
    print(f"Biometric logins (FaceID/Finger): {len(bio_logins):,}")
    print(f"Password logins: {len(pwd_logins):,}")
    
    # Per-customer biometric ratio
    login_counts = df_activity.groupby('CUSTOMER_NUMBER').agg(
        total=('ACTIVITY', 'count'),
        bio=('ACTIVITY', lambda x: (x.isin(['LOGIN_FINGER', 'LOGIN_FACEID'])).sum())
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
# 5. Graph Features (already computed, check distribution)
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

# Save summary
output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(output_dir, exist_ok=True)
print(f"\nEDA complete. Results above.")
