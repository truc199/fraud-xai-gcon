"""
Deep EDA: Distribution analysis for the 3 selected credit & infrastructure features.
1. LIMIT_UTILIZATION_VELOCITY (MoM credit velocity)
2. STRUCTURING_OVERPAYMENT_FLAG (Credit card overpayment laundering)
3. IP_HOPPING_VELOCITY (IP rotation per device in 3h window)
"""
import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'gcontest.db')
conn = sqlite3.connect(DB_PATH)

# =====================================================
# 1. LIMIT_UTILIZATION_VELOCITY
# =====================================================
print("=" * 70)
print("1. LIMIT_UTILIZATION_VELOCITY — MoM Credit Utilization Velocity")
print("=" * 70)

df_card = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, MONTH, LIMIT_AMT_CREDIT, OUTSTANDING_BAL_CREDIT
    FROM Data_Card
    WHERE LIMIT_AMT_CREDIT > 0
    ORDER BY CUSTOMER_NUMBER, MONTH
""", conn)

df_card['LIMIT_AMT_CREDIT'] = pd.to_numeric(df_card['LIMIT_AMT_CREDIT'], errors='coerce').fillna(0)
df_card['OUTSTANDING_BAL_CREDIT'] = pd.to_numeric(df_card['OUTSTANDING_BAL_CREDIT'], errors='coerce').fillna(0)
df_card = df_card[df_card['LIMIT_AMT_CREDIT'] > 0].copy()

print(f"Total card records (LIMIT > 0): {len(df_card):,}")
print(f"Unique customers with credit cards: {df_card['CUSTOMER_NUMBER'].nunique():,}")

# Compute utilization ratio per month
df_card['utilization'] = df_card['OUTSTANDING_BAL_CREDIT'] / df_card['LIMIT_AMT_CREDIT']

# Compute MoM velocity (shift within each customer)
df_card['prev_util'] = df_card.groupby('CUSTOMER_NUMBER')['utilization'].shift(1)
df_card['util_velocity'] = df_card['utilization'] - df_card['prev_util']
valid = df_card.dropna(subset=['util_velocity'])

print(f"\nRecords with valid MoM velocity: {len(valid):,}")

# Per-customer max velocity
max_velocity = valid.groupby('CUSTOMER_NUMBER')['util_velocity'].max()
print(f"\n--- Max MoM Velocity per Customer ---")
print(max_velocity.describe())

# Distribution buckets
print(f"\n--- Distribution Buckets ---")
buckets = [
    ("< 0 (decreasing)", max_velocity[max_velocity < 0].count()),
    ("0 - 0.1 (stable)", max_velocity[(max_velocity >= 0) & (max_velocity < 0.1)].count()),
    ("0.1 - 0.2 (mild increase)", max_velocity[(max_velocity >= 0.1) & (max_velocity < 0.2)].count()),
    ("0.2 - 0.3 (moderate spike)", max_velocity[(max_velocity >= 0.2) & (max_velocity < 0.3)].count()),
    ("0.3 - 0.5 (high spike)", max_velocity[(max_velocity >= 0.3) & (max_velocity < 0.5)].count()),
    ("> 0.5 (extreme bust-out risk)", max_velocity[max_velocity >= 0.5].count()),
]
total_custs = len(max_velocity)
for label, count in buckets:
    print(f"  {label}: {count:,} customers ({count/total_custs*100:.2f}%)")

# Top 10 extreme cases
print(f"\n--- Top 10 Extreme Velocity Spikes ---")
top10 = max_velocity.nlargest(10)
for cust, vel in top10.items():
    cust_data = df_card[df_card['CUSTOMER_NUMBER'] == cust][['MONTH', 'utilization', 'util_velocity']].tail(6)
    print(f"\n  Customer {cust}: Max velocity = +{vel:.4f}")
    for _, row in cust_data.iterrows():
        vel_str = f"{row['util_velocity']:+.4f}" if pd.notna(row['util_velocity']) else "N/A"
        print(f"    Month {row['MONTH']}: util={row['utilization']:.4f}, change={vel_str}")

# Cross-reference with transaction data
print(f"\n--- Cross-reference: High velocity customers & their transactions ---")
extreme_custs = set(max_velocity[max_velocity >= 0.3].index)
df_trans_extreme = pd.read_sql_query(f"""
    SELECT CUSTOMER_NUMBER, COUNT(*) as tx_count, 
           SUM(TRANS_AMOUNT) as total_amount,
           AVG(TRANS_AMOUNT) as avg_amount
    FROM Data_Transaction
    WHERE CUSTOMER_NUMBER IN ({','.join(str(c) for c in list(extreme_custs)[:500])})
    GROUP BY CUSTOMER_NUMBER
""", conn)
print(f"  Customers with velocity >= 0.3: {len(extreme_custs):,}")
if not df_trans_extreme.empty:
    print(f"  Avg transaction count: {df_trans_extreme['tx_count'].mean():.1f}")
    print(f"  Avg total amount: {df_trans_extreme['total_amount'].mean():,.0f} VND")
    print(f"  Avg per-transaction amount: {df_trans_extreme['avg_amount'].mean():,.0f} VND")

# =====================================================
# 2. STRUCTURING_OVERPAYMENT_FLAG
# =====================================================
print("\n\n" + "=" * 70)
print("2. STRUCTURING_OVERPAYMENT_FLAG — Credit Card Overpayment Pattern")
print("=" * 70)

# Get all credit card repayment transactions
df_repay = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, TRANS_DATE, TRANS_AMOUNT, TRANS_LV2
    FROM Data_Transaction
    WHERE TRANS_LV2 LIKE '%Credit_card%'
    ORDER BY CUSTOMER_NUMBER, TRANS_DATE
""", conn)
print(f"Total CC repayment transactions: {len(df_repay):,}")
print(f"Unique customers: {df_repay['CUSTOMER_NUMBER'].nunique():,}")

# Repayment frequency distribution
repay_freq = df_repay.groupby('CUSTOMER_NUMBER').agg(
    count=('TRANS_AMOUNT', 'count'),
    total=('TRANS_AMOUNT', 'sum'),
    avg=('TRANS_AMOUNT', 'mean'),
    max_single=('TRANS_AMOUNT', 'max')
)
print(f"\n--- Repayment Frequency per Customer ---")
print(repay_freq['count'].describe())

# Multi-repayment (structuring indicator)
multi = repay_freq[repay_freq['count'] >= 2]
print(f"\nCustomers with 2+ repayments (structuring potential): {len(multi):,}")

# Get outstanding balance for overpayment check
card_outstanding = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, MAX(OUTSTANDING_BAL_CREDIT) as max_outstanding
    FROM Data_Card
    WHERE OUTSTANDING_BAL_CREDIT IS NOT NULL
    GROUP BY CUSTOMER_NUMBER
""", conn)
card_outstanding['max_outstanding'] = pd.to_numeric(card_outstanding['max_outstanding'], errors='coerce').fillna(0)
outstanding_map = dict(zip(card_outstanding['CUSTOMER_NUMBER'], card_outstanding['max_outstanding']))

# Check overpayment ratio
multi = multi.copy()
multi['outstanding'] = multi.index.map(lambda c: outstanding_map.get(c, 0))
has_outstanding = multi[multi['outstanding'] > 0].copy()
has_outstanding['overpay_ratio'] = has_outstanding['total'] / has_outstanding['outstanding']

print(f"\n--- Overpayment Analysis (Customers with 2+ repayments AND outstanding > 0) ---")
print(f"Total customers: {len(has_outstanding):,}")
if not has_outstanding.empty:
    print(f"\nOverpayment Ratio (Total Repaid / Max Outstanding):")
    print(has_outstanding['overpay_ratio'].describe())
    
    overpaid = has_outstanding[has_outstanding['overpay_ratio'] > 1.0]
    print(f"\nCustomers who OVERPAID (ratio > 1.0): {len(overpaid):,} ({len(overpaid)/len(has_outstanding)*100:.1f}%)")
    
    heavy_overpaid = has_outstanding[has_outstanding['overpay_ratio'] > 2.0]
    print(f"Customers who paid 2x+ outstanding: {len(heavy_overpaid):,}")
    
    extreme_overpaid = has_outstanding[has_outstanding['overpay_ratio'] > 5.0]
    print(f"Customers who paid 5x+ outstanding: {len(extreme_overpaid):,}")
    
    # Show top overpayers
    print(f"\n--- Top 10 Overpayers ---")
    for _, row in has_outstanding.nlargest(10, 'overpay_ratio').iterrows():
        print(f"  Customer {row.name}: "
              f"Repaid {row['total']:,.0f} vs Outstanding {row['outstanding']:,.0f} "
              f"(ratio: {row['overpay_ratio']:.1f}x, {int(row['count'])} payments)")

# =====================================================
# 3. IP_HOPPING_VELOCITY (already computed in data loader, analyze raw distribution)
# =====================================================
print("\n\n" + "=" * 70)
print("3. IP_HOPPING_VELOCITY — IP Rotation Distribution")
print("=" * 70)

# Per-device IP diversity (overall, not 3h window - gives upper bound)
df_ip = pd.read_sql_query("""
    SELECT Device_ID_Hash, 
           COUNT(DISTINCT IP_Address_Proxy) as unique_ips,
           COUNT(*) as tx_count
    FROM Data_Transaction
    GROUP BY Device_ID_Hash
""", conn)
print(f"Total unique devices: {len(df_ip):,}")

print(f"\n--- Unique IPs per Device (Overall) ---")
print(df_ip['unique_ips'].describe())

# Distribution buckets
print(f"\n--- Distribution Buckets ---")
ip_buckets = [
    ("1 IP (single connection)", df_ip[df_ip['unique_ips'] == 1].shape[0]),
    ("2 IPs (normal, home+office)", df_ip[df_ip['unique_ips'] == 2].shape[0]),
    ("3-5 IPs (mobile user)", df_ip[(df_ip['unique_ips'] >= 3) & (df_ip['unique_ips'] <= 5)].shape[0]),
    ("6-10 IPs (frequent traveler)", df_ip[(df_ip['unique_ips'] >= 6) & (df_ip['unique_ips'] <= 10)].shape[0]),
    ("11-50 IPs (suspicious)", df_ip[(df_ip['unique_ips'] >= 11) & (df_ip['unique_ips'] <= 50)].shape[0]),
    ("51-100 IPs (highly suspicious)", df_ip[(df_ip['unique_ips'] >= 51) & (df_ip['unique_ips'] <= 100)].shape[0]),
    ("> 100 IPs (bot/proxy rotation)", df_ip[df_ip['unique_ips'] > 100].shape[0]),
]
for label, count in ip_buckets:
    print(f"  {label}: {count:,} devices ({count/len(df_ip)*100:.2f}%)")

# The actual 3h window calculation - sample analysis
print(f"\n--- 3-Hour Window Analysis (Sample: 50K transactions) ---")
df_sample = pd.read_sql_query("""
    SELECT Device_ID_Hash, IP_Address_Proxy, TRANS_DATE, TRANS_HOUR
    FROM Data_Transaction
    ORDER BY TRANS_DATE, TRANS_HOUR
    LIMIT 50000
""", conn)
df_sample['ts'] = pd.to_datetime(df_sample['TRANS_DATE']) + pd.to_timedelta(df_sample['TRANS_HOUR'], unit='h')

# Rolling 3h unique IP count per device
results_3h = []
for device, group in df_sample.groupby('Device_ID_Hash'):
    if len(group) < 2:
        continue
    group = group.sort_values('ts')
    for i in range(len(group)):
        current_time = group.iloc[i]['ts']
        window_start = current_time - pd.Timedelta(hours=3)
        window = group[(group['ts'] >= window_start) & (group['ts'] <= current_time)]
        unique_ips_3h = window['IP_Address_Proxy'].nunique()
        if unique_ips_3h > 1:
            results_3h.append({
                'device': device,
                'unique_ips_3h': unique_ips_3h,
                'tx_in_window': len(window)
            })

if results_3h:
    df_3h = pd.DataFrame(results_3h)
    print(f"Transactions with 2+ unique IPs in 3h window: {len(df_3h):,}")
    print(f"Unique devices with IP hopping: {df_3h['device'].nunique():,}")
    print(f"\nUnique IPs in 3h window distribution:")
    print(df_3h['unique_ips_3h'].describe())
else:
    print("No IP hopping detected in 3h window within sample.")

conn.close()

# Save outputs
output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(output_dir, exist_ok=True)
max_velocity.to_csv(os.path.join(output_dir, 'limit_utilization_velocity.csv'))
print(f"\nOutputs saved to {output_dir}/")
print("Done.")
