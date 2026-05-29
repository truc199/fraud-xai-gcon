import sqlite3
import pandas as pd

db_path = 'data/gcontest.db'
conn = sqlite3.connect(db_path)

print("=== TABLES IN DB ===")
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
print(tables)

for table in tables['name']:
    print(f"\n--- Columns for {table} ---")
    cols = pd.read_sql(f"PRAGMA table_info({table});", conn)
    print(cols['name'].tolist())

# specifically looking for:
# Device_OS (does it contain Root/Jailbreak info?)
if 'Data_Transaction' in tables['name'].values:
    print("\n--- Device_OS unique values ---")
    os_vals = pd.read_sql("SELECT Device_OS, COUNT(*) FROM Data_Transaction GROUP BY Device_OS;", conn)
    print(os_vals)
    
    print("\n--- IP_Address_Proxy sample ---")
    ip_vals = pd.read_sql("SELECT IP_Address_Proxy, COUNT(*) FROM Data_Transaction GROUP BY IP_Address_Proxy ORDER BY COUNT(*) DESC LIMIT 5;", conn)
    print(ip_vals)

# VERIFY_METHOD
if 'Data_Customer' in tables['name'].values:
    print("\n--- VERIFY_METHOD unique values ---")
    verify_vals = pd.read_sql("SELECT VERIFY_METHOD, COUNT(*) FROM Data_Customer GROUP BY VERIFY_METHOD;", conn)
    print(verify_vals)

conn.close()
