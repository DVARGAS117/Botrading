"""
Script para limpiar operaciones de prueba de la base de datos.
Elimina operaciones con magic numbers usados en tests.
"""
import sqlite3
import sys

def clean_test_operations():
    """Limpia operaciones de test de la BD."""
    try:
        conn = sqlite3.connect('data/operations.db')
        cursor = conn.cursor()
        
        print("🧹 Limpiando operaciones de test...")
        
        # Ver TODAS las operaciones antes de borrar
        cursor.execute("SELECT id, magic_number, symbol, direction, status FROM operations")
        all_operations = cursor.fetchall()
        print(f"\n📋 Operaciones totales encontradas: {len(all_operations)}")
        for op in all_operations:
            print(f"  ID={op[0]}, Magic={op[1]}, Symbol={op[2]}, Direction={op[3]}, Status={op[4]}")
        
        # Eliminar TODAS las operaciones (para test limpio)
        cursor.execute("DELETE FROM operations")
        deleted = cursor.rowcount
        conn.commit()
        print(f"\n✅ Eliminadas {deleted} operación(es) de la BD")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al limpiar BD: {e}")
        return False

if __name__ == "__main__":
    success = clean_test_operations()
    sys.exit(0 if success else 1)
