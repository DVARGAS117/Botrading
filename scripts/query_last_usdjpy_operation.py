"""Script diagnóstico: Última operación USDJPY (SL inicial vs SL actual).

Uso:
    python scripts/query_last_usdjpy_operation.py

Requisitos:
    - Base de datos en ruta por defecto `data/operations.db`
    - Operaciones registradas con símbolo USDJPY

Salida:
    Imprime las 5 operaciones más recientes de USDJPY mostrando:
      ID | Magic | Estado | SL Inicial | SL Actual | TP | Fecha Apertura
    Destaca si hay discrepancia entre SL inicial y SL actual sin actualizar prompt.
"""
from pathlib import Path
from datetime import datetime

from src.core.operations_repository import OperationsRepository, OperationStatus


def main():
    repo = OperationsRepository(db_path=Path("data/operations.db"))
    ops = repo.list_operations(symbol="USDJPY", limit=50)
    if not ops:
        print("No hay operaciones USDJPY en BD.")
        return
    # Ordenar por created_at descendente (list_operations ya lo hace) y tomar primeras 5
    header = f"{'ID':>4} {'Magic':>8} {'Estado':>7} {'SL Inicial':>12} {'SL Actual':>11} {'TP':>11} {'Apertura':>20}"
    print(header)
    print('-' * len(header))
    for op in ops[:5]:
        sl_init = getattr(op, 'stop_loss_initial', None)
        sl_curr = op.stop_loss
        discrepancia = ''
        if sl_init is not None and abs(sl_curr - sl_init) > 1e-6:
            discrepancia = ' *SL AJUSTADO*'
        print(f"{op.id:>4} {op.magic_number:>8} {op.status.value:>7} "
              f"{(sl_init if sl_init is not None else 'None'):>12} {sl_curr:>11} {op.take_profit:>11} "
              f"{op.open_time.strftime('%Y-%m-%d %H:%M:%S') if op.open_time else 'N/A':>20}{discrepancia}")

    # Mostrar detalle de la primera
    op0 = ops[0]
    print("\nDetalle última operación:")
    print(f"ID={op0.id} Magic={op0.magic_number} Símbolo={op0.symbol} Estado={op0.status.value}")
    print(f"SL Inicial={op0.stop_loss_initial} SL Actual={op0.stop_loss} TP={op0.take_profit}")


if __name__ == "__main__":
    main()
