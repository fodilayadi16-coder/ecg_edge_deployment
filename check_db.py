import sqlite3
import os

DB = os.path.join(os.getcwd(), "ecg_results.db")
conn = sqlite3.connect(DB)
cursor = conn.cursor()

def list_tables():
	cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
	return [r[0] for r in cursor.fetchall()]

print("tables:", list_tables())

print('\n-- patients --')
try:
	cursor.execute("SELECT * FROM patient")
	for row in cursor.fetchall():
		print(row)
except Exception as e:
	print('no patient table or query failed:', e)

# Try to find ECG records table (case-insensitive match containing 'ecg')
ecg_table = None
for t in list_tables():
	if 'ecg' in t.lower():
		ecg_table = t
		break

if ecg_table:
	print(f"\n-- ECG records (from '{ecg_table}') --")
	# Inspect columns
	try:
		cursor.execute(f"PRAGMA table_info({ecg_table})")
		cols = [r[1] for r in cursor.fetchall()]
	except Exception:
		cols = []

	# attempt to order by timestamp if present
	order_clause = "ORDER BY timestamp DESC" if 'timestamp' in cols else ""
	try:
		cursor.execute(f"SELECT * FROM {ecg_table} {order_clause} LIMIT 50")
		rows = cursor.fetchall()
		for r in rows:
			print(r)
		if not rows:
			print('(no ECG records found)')
	except Exception as e:
		print('failed to query ECG table:', e)
else:
	print('\n(no ECG table found)')

conn.close()