import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "db", "upao_new.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()

print("--- SQLITE TABLES AND SCHEMAS ---")
for name, sql in tables:
    print(f"\nTABLE: {name}")
    print(sql)
    cur.execute(f"SELECT COUNT(*) FROM `{name}`")
    count = cur.fetchone()[0]
    print(f"COUNT: {count} rows")

conn.close()
