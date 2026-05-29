import sqlite3
import pandas as pd
import numpy as np

db_path = 'data/gcontest.db'
conn = sqlite3.connect(db_path)

print("=== 1. FINDING IP HOPPING ===")
# Tìm các giao dịch có nhiều IP Proxy khác nhau trên cùng 1 Device trong cùng 1 ngày
query_ip = """
SELECT Device_ID_Hash, TRANS_DATE, COUNT(DISTINCT IP_Address_Proxy) as Unique_IPs
FROM Data_Transaction
WHERE Device_ID_Hash != 'UNKNOWN' AND IP_Address_Proxy != 'UNKNOWN'
GROUP BY Device_ID_Hash, TRANS_DATE
HAVING Unique_IPs > 2
ORDER BY Unique_IPs DESC
LIMIT 5;
"""
df_ip = pd.read_sql(query_ip, conn)
print(df_ip)
if not df_ip.empty:
    sample_dev = df_ip.iloc[0]['Device_ID_Hash']
    sample_date = df_ip.iloc[0]['TRANS_DATE']
    print(f"\nTransaction details for device {sample_dev} on {sample_date}:")
    df_ip_detail = pd.read_sql(f"""
    SELECT TRANS_HOUR, IP_Address_Proxy, CUSTOMER_NUMBER
    FROM Data_Transaction 
    WHERE Device_ID_Hash = '{sample_dev}' AND TRANS_DATE = '{sample_date}'
    ORDER BY TRANS_HOUR
    """, conn)
    print(df_ip_detail)

print("\n=== 2. FINDING MONEY MULE (GNN HUB) ===")
# Tìm Beneficiary_CUSTOMER_NUMBER nhận tiền từ nhiều người gửi nhất
query_hub = """
SELECT Beneficiary_CUSTOMER_NUMBER, COUNT(DISTINCT CUSTOMER_NUMBER) as Unique_Senders
FROM Data_Transaction
WHERE Beneficiary_CUSTOMER_NUMBER NOT IN ('UNKNOWN', 'NaN', 'nan', '')
GROUP BY Beneficiary_CUSTOMER_NUMBER
ORDER BY Unique_Senders DESC
LIMIT 5;
"""
df_hub = pd.read_sql(query_hub, conn)
print(df_hub)

print("\n=== 3. FINDING BUST-OUT (LIMIT UTILIZATION > 95%) ===")
query_bust = """
SELECT CUSTOMER_NUMBER, MONTH, LIMIT_AMT_CREDIT, OUTSTANDING_BAL_CREDIT,
       (OUTSTANDING_BAL_CREDIT / LIMIT_AMT_CREDIT) as Utilization
FROM Data_Card
WHERE LIMIT_AMT_CREDIT > 0 AND (OUTSTANDING_BAL_CREDIT / LIMIT_AMT_CREDIT) > 0.95
ORDER BY Utilization DESC
LIMIT 5;
"""
df_bust = pd.read_sql(query_bust, conn)
print(df_bust)

print("\n=== 4. FINDING AUTHENTICATION DOWNGRADE ===")
# Tìm User có dùng LOGIN_FACEID/FINGER, và sau đó dùng LOGIN thường
query_auth = """
WITH user_auth AS (
    SELECT CUSTOMER_NUMBER, ACTIVITY_NAME, COUNT(*) as cnt
    FROM Data_Activity
    WHERE ACTIVITY_NAME IN ('LOGIN', 'LOGIN_FACEID', 'LOGIN_FINGER')
    GROUP BY CUSTOMER_NUMBER, ACTIVITY_NAME
)
SELECT u1.CUSTOMER_NUMBER, u1.cnt as Biometric_Logins, u2.cnt as Password_Logins
FROM user_auth u1
JOIN user_auth u2 ON u1.CUSTOMER_NUMBER = u2.CUSTOMER_NUMBER
WHERE u1.ACTIVITY_NAME IN ('LOGIN_FACEID', 'LOGIN_FINGER') 
  AND u2.ACTIVITY_NAME = 'LOGIN'
  AND u1.cnt > 10 AND u2.cnt > 0
ORDER BY u2.cnt ASC
LIMIT 5;
"""
df_auth = pd.read_sql(query_auth, conn)
print(df_auth)

conn.close()
