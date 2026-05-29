import sqlite3
import pandas as pd
import numpy as np
import os

conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'data', 'gcontest.db'))

# =====================================================
# EDA 1: NEW_DEVICE_FLAG - How many transactions use a device never seen before?
# =====================================================
print("=" * 60)
print("EDA 1: NEW_DEVICE_FLAG analysis")
print("=" * 60)

df = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, TRANS_DATE, Device_ID_Hash, TRANS_AMOUNT, TRANS_LV2
    FROM Data_Transaction
    ORDER BY CUSTOMER_NUMBER, TRANS_DATE
""", conn)

total = len(df)
print(f"Total transactions: {total:,}")

# Count how many devices each customer has used historically (cumulative)
df['device_seen_before'] = df.groupby(['CUSTOMER_NUMBER', 'Device_ID_Hash']).cumcount()
df['NEW_DEVICE_FLAG'] = (df['device_seen_before'] == 0).astype(int)

new_device_count = df['NEW_DEVICE_FLAG'].sum()
print(f"\nTransactions on a NEW device (first time for that customer): {new_device_count:,} ({new_device_count/total*100:.2f}%)")
print(f"Transactions on a KNOWN device: {total - new_device_count:,} ({(total - new_device_count)/total*100:.2f}%)")

# Cross-tab: New device + high amount + outside bank
new_dev_high = df[(df['NEW_DEVICE_FLAG'] == 1) & (df['TRANS_AMOUNT'] > 10_000_000)]
new_dev_high_outside = new_dev_high[new_dev_high['TRANS_LV2'].str.contains('Outside', na=False)]
print(f"\nNew device + Amount > 10M: {len(new_dev_high):,} ({len(new_dev_high)/total*100:.2f}%)")
print(f"New device + Amount > 10M + Outside bank: {len(new_dev_high_outside):,} ({len(new_dev_high_outside)/total*100:.2f}%)")

# Average transaction amount: new vs known device
avg_new = df[df['NEW_DEVICE_FLAG'] == 1]['TRANS_AMOUNT'].mean()
avg_known = df[df['NEW_DEVICE_FLAG'] == 0]['TRANS_AMOUNT'].mean()
print(f"\nAvg amount on NEW device: {avg_new:,.0f} VND")
print(f"Avg amount on KNOWN device: {avg_known:,.0f} VND")
print(f"Ratio (new/known): {avg_new/avg_known:.2f}x")

# Unique device count per customer
device_stats = df.groupby('CUSTOMER_NUMBER')['Device_ID_Hash'].nunique().describe()
print(f"\nUnique devices per customer:\n{device_stats}")

# =====================================================
# EDA 2: BENEFICIARY_IS_NEW - First-time beneficiary analysis
# =====================================================
print("\n" + "=" * 60)
print("EDA 2: BENEFICIARY_IS_NEW analysis")
print("=" * 60)

df_ben = pd.read_sql_query("""
    SELECT CUSTOMER_NUMBER, TRANS_DATE, Beneficiary_CUSTOMER_NUMBER, TRANS_AMOUNT, TRANS_LV2
    FROM Data_Transaction
    WHERE Beneficiary_CUSTOMER_NUMBER IS NOT NULL 
      AND Beneficiary_CUSTOMER_NUMBER != ''
    ORDER BY CUSTOMER_NUMBER, TRANS_DATE
""", conn)

total_with_ben = len(df_ben)
print(f"Transactions with a beneficiary: {total_with_ben:,}")

# Mark first-time beneficiary for each customer
df_ben['ben_seen_before'] = df_ben.groupby(['CUSTOMER_NUMBER', 'Beneficiary_CUSTOMER_NUMBER']).cumcount()
df_ben['BENEFICIARY_IS_NEW'] = (df_ben['ben_seen_before'] == 0).astype(int)

new_ben_count = df_ben['BENEFICIARY_IS_NEW'].sum()
print(f"Transactions to a NEW beneficiary (first time): {new_ben_count:,} ({new_ben_count/total_with_ben*100:.2f}%)")
print(f"Transactions to a KNOWN beneficiary: {total_with_ben - new_ben_count:,} ({(total_with_ben - new_ben_count)/total_with_ben*100:.2f}%)")

# Cross-tab: New beneficiary + high amount + outside
new_ben_high = df_ben[(df_ben['BENEFICIARY_IS_NEW'] == 1) & (df_ben['TRANS_AMOUNT'] > 10_000_000)]
new_ben_high_outside = new_ben_high[new_ben_high['TRANS_LV2'].str.contains('Outside', na=False)]
print(f"\nNew beneficiary + Amount > 10M: {len(new_ben_high):,} ({len(new_ben_high)/total_with_ben*100:.2f}%)")
print(f"New beneficiary + Amount > 10M + Outside bank: {len(new_ben_high_outside):,} ({len(new_ben_high_outside)/total_with_ben*100:.2f}%)")

# Average transaction amount: new vs known beneficiary
avg_new_ben = df_ben[df_ben['BENEFICIARY_IS_NEW'] == 1]['TRANS_AMOUNT'].mean()
avg_known_ben = df_ben[df_ben['BENEFICIARY_IS_NEW'] == 0]['TRANS_AMOUNT'].mean()
print(f"\nAvg amount to NEW beneficiary: {avg_new_ben:,.0f} VND")
print(f"Avg amount to KNOWN beneficiary: {avg_known_ben:,.0f} VND")
print(f"Ratio (new/known): {avg_new_ben/avg_known_ben:.2f}x")

# Unique beneficiaries per customer
ben_stats = df_ben.groupby('CUSTOMER_NUMBER')['Beneficiary_CUSTOMER_NUMBER'].nunique().describe()
print(f"\nUnique beneficiaries per customer:\n{ben_stats}")

conn.close()
print("\nDone.")
