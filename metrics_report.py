import sqlite3
import datetime
import pathlib

db_path = pathlib.Path("metrics.db")
if not db_path.exists():
    print("No metrics database found. Run drift_monitor.py first.")
    exit(0)

conn = sqlite3.connect("metrics.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM metrics ORDER BY timestamp ASC")
rows = cursor.fetchall()
conn.close()

if not rows:
    print("No metrics logged yet.")
else:
    print(f"{'Timestamp':<20} | {'Dictionary':<20} | {'ID':<12} | {'Savings':<10}")
    print("-" * 70)
    for r in rows:
        ts, df, did, orig, comp, sav = r
        time_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{time_str:<20} | {df:<20} | {did:<12} | {sav}%")
