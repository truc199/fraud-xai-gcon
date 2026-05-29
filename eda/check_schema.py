import sqlite3, os
conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'data', 'gcontest.db'))
cur = conn.cursor()
cur.execute('PRAGMA table_info(Data_Transaction)')
print('Data_Transaction columns:', [r[1] for r in cur.fetchall()])
conn.close()
