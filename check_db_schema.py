"""Script para verificar el schema de la BD operations.db"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "operations.db"

if not db_path.exists():
    print(f"❌ La base de datos NO existe: {db_path}")
    print("\n✅ Se creará automáticamente al ejecutar el bot por primera vez")
else:
    print(f"✅ Base de datos encontrada: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener columnas de la tabla operations
    cursor.execute("PRAGMA table_info(operations)")
    columns = cursor.fetchall()
    
    print("\n📋 Columnas en tabla 'operations':")
    print("-" * 60)
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        nullable = "NOT NULL" if not_null else "NULL"
        print(f"  {name:<25} {col_type:<10} {nullable}")
    
    # Verificar si existen las nuevas columnas
    column_names = [col[1] for col in columns]
    
    print("\n🔍 Verificación de columnas nuevas:")
    print("-" * 60)
    
    if 'stop_loss_initial' in column_names:
        print("  ✅ stop_loss_initial - EXISTE")
    else:
        print("  ❌ stop_loss_initial - NO EXISTE (necesita migración)")
    
    if 'take_profit_initial' in column_names:
        print("  ✅ take_profit_initial - EXISTE")
    else:
        print("  ❌ take_profit_initial - NO EXISTE (necesita migración)")
    
    conn.close()
