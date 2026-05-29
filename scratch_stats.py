import sqlite3
import pandas as pd
conn = sqlite3.connect('data/gcontest.db')
query = """
SELECT TRANS_LV2, TRANS_AMOUNT 
FROM Data_Transaction 
WHERE TRANS_LV2 IN ('Utilities_payment', 'Credit_card_repayment', 'Lending_repayment', 'Cable', 'Game', 'Lifestyle_payment', 'MCPP')
"""
df = pd.read_sql_query(query, conn)
summary = df.groupby('TRANS_LV2')['TRANS_AMOUNT'].describe(percentiles=[0.5, 0.75, 0.9, 0.95, 0.99])
pd.set_option('display.float_format', lambda x: '%.0f' % x)
print(summary)
