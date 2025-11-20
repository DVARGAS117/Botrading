"""Ver contenido de operations.db"""
import sqlite3

conn = sqlite3.connect('data/operations.db')
cursor = conn.cursor()

cursor.execute('SELECT id, magic_number, symbol, direction, status, open_time FROM operations')
rows = cursor.fetchall()

print(f'\nTotal operaciones: {len(rows)}\n')
print(f"{'ID':<5} {'Magic':<12} {'Symbol':<8} {'Dir':<6} {'Status':<10} {'Open Time':<20}")
print("-" * 70)
for r in rows:
    print(f"{r[0]:<5} {r[1]:<12} {r[2]:<8} {r[3]:<6} {r[4]:<10} {r[5]:<20}")

conn.close()
