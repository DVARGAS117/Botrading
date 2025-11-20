"""Ver esquema de operations.db"""
import sqlite3

conn = sqlite3.connect('data/operations.db')
cursor = conn.cursor()

# Ver columnas
cursor.execute('PRAGMA table_info(operations)')
columns = cursor.fetchall()
print('\nColumnas de operations:')
for c in columns:
    not_null = "NOT NULL" if c[3] else ""
    unique = "UNIQUE" if "magic_number" in str(c[1]).lower() else ""
    print(f'  {c[1]:25} {c[2]:10} {not_null:10} {unique}')

# Ver índices
cursor.execute('PRAGMA index_list(operations)')
indexes = cursor.fetchall()
print(f'\nÍndices: {len(indexes)}')
for idx in indexes:
    print(f'  {idx[1]}')
    cursor.execute(f'PRAGMA index_info({idx[1]})')
    index_cols = cursor.fetchall()
    for col in index_cols:
        print(f'    - {col[2]}')

conn.close()
