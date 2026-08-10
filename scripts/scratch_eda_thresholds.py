import sqlite3
import pandas as pd
import numpy as np

print("Đang truy xuất dữ liệu từ Database...")
conn = sqlite3.connect('data/gcontest.db')

# 1. Phân tích Dormancy (Ngày ngủ đông)
print("1. Đang tính toán phân bổ ngày ngủ đông (DAYS_SINCE_LAST_TRANS)...")
df_trans = pd.read_sql_query("SELECT CUSTOMER_NUMBER, TRANS_DATE FROM Data_Transaction ORDER BY CUSTOMER_NUMBER, TRANS_DATE", conn)
df_trans['ts'] = pd.to_datetime(df_trans['TRANS_DATE'])
df_trans['prev_ts'] = df_trans.groupby('CUSTOMER_NUMBER')['ts'].shift(1)
df_trans['DAYS_SINCE_LAST_TRANS'] = (df_trans['ts'] - df_trans['prev_ts']).dt.total_seconds() / 86400.0

dormancy_stats = df_trans['DAYS_SINCE_LAST_TRANS'].dropna().describe(percentiles=[0.5, 0.75, 0.9, 0.95, 0.98, 0.99, 0.995])

print("\n--- KẾT QUẢ THỐNG KÊ NGÀY NGỦ ĐÔNG ---")
pd.set_option('display.float_format', lambda x: '%.2f' % x)
print(dormancy_stats)
print(f"Số lượng giao dịch > 90 ngày: {len(df_trans[df_trans['DAYS_SINCE_LAST_TRANS'] > 90])} ({(len(df_trans[df_trans['DAYS_SINCE_LAST_TRANS'] > 90]) / len(df_trans) * 100):.2f}%)")

# 2. Phân tích ATO Panic (Thời gian từ lúc đổi pass đến lúc giao dịch)
print("\n2. Đang tính toán phân bổ khoảng thời gian đổi bảo mật (HOURS_SINCE_SEC_EVENT)...")
query_sec = """
SELECT CUSTOMER_NUMBER, ACTIVITY_DATE as SEC_DATE 
FROM Data_Activity 
WHERE ACTIVITY_NAME IN ('CHANGE_PASSWORD', 'MB_CHANGE_PIN', 'MB_RESET_PIN', 'ACCOUNT_ADDRESS_BOOK_UPDATE')
ORDER BY CUSTOMER_NUMBER, ACTIVITY_DATE
"""
df_sec = pd.read_sql_query(query_sec, conn)
df_sec['SEC_DATE'] = pd.to_datetime(df_sec['SEC_DATE'])

# Lọc chỉ những khách hàng có sự kiện bảo mật để tính toán nhanh hơn
customers_with_sec = df_sec['CUSTOMER_NUMBER'].unique()
df_trans_sub = df_trans[df_trans['CUSTOMER_NUMBER'].isin(customers_with_sec)].copy()

df_trans_sub = df_trans_sub.sort_values('ts')
df_sec = df_sec.sort_values('SEC_DATE')

merged = pd.merge_asof(
    df_trans_sub, 
    df_sec, 
    left_on='ts', 
    right_on='SEC_DATE', 
    by='CUSTOMER_NUMBER', 
    direction='backward'
)

merged['HOURS_SINCE_SEC_EVENT'] = (merged['ts'] - merged['SEC_DATE']).dt.total_seconds() / 3600.0
sec_stats = merged['HOURS_SINCE_SEC_EVENT'].dropna().describe(percentiles=[0.01, 0.05, 0.1, 0.25, 0.5])

print("\n--- KẾT QUẢ THỐNG KÊ GIỜ SAU KHI ĐỔI BẢO MẬT ---")
print(sec_stats)
print(f"Số lượng giao dịch < 1 giờ sau đổi pass: {len(merged[merged['HOURS_SINCE_SEC_EVENT'] < 1.0])}")
print(f"Số lượng giao dịch < 1 giờ VÀ Số tiền > 10M: (Cần join lượng tiền, nhưng tỷ lệ < 1h chung là {(len(merged[merged['HOURS_SINCE_SEC_EVENT'] < 1.0]) / len(df_trans) * 100):.3f}% trên tổng dataset)")

conn.close()
