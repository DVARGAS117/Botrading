"""
Ejemplo de uso de OperationsRepository - T32

Este archivo demuestra cómo utilizar el OperationsRepository para
persistir y gestionar operaciones de trading en SQLite.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T32 - Persistencia de operaciones con parámetros y estados
"""

from pathlib import Path
from datetime import datetime
from src.core.operations_repository import (
    OperationsRepository,
    Operation,
    OrderType,
    Direction,
    OperationStatus
)


def print_separator(title: str = ""):
    """Imprime un separador visual"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"{'-'*60}\n")


def ejemplo_1_crear_operacion():
    """Ejemplo 1: Crear una operación básica"""
    print_separator("EJEMPLO 1: Crear una operación básica")
    
    # Crear repositorio
    repo = OperationsRepository(db_path=Path("data/examples/operations_example.db"))
    
    # Crear una operación Market
    operation = repo.create_operation(
        magic_number=123456,
        bot_id=1,
        ia_id=1,
        order_type=OrderType.MARKET,
        symbol="EURUSD",
        direction=Direction.BUY,
        suggested_price=1.0850,
        actual_entry_price=1.0851,  # Precio real ligeramente diferente
        stop_loss=1.0800,
        take_profit=1.0950,
        lot_size=0.10,
        risk_percentage=1.0,
        status=OperationStatus.OPEN,
        conversation_id="conv_123_abc"
    )
    
    print(f"✅ Operación creada exitosamente!")
    print(f"   ID: {operation.id}")
    print(f"   Magic Number: {operation.magic_number}")
    print(f"   Símbolo: {operation.symbol}")
    print(f"   Dirección: {operation.direction.value}")
    print(f"   Precio entrada: {operation.actual_entry_price}")
    print(f"   Stop Loss: {operation.stop_loss}")
    print(f"   Take Profit: {operation.take_profit}")
    print(f"   Estado: {operation.status.value}")
    
    return repo, operation


def ejemplo_2_consultar_operaciones(repo: OperationsRepository):
    """Ejemplo 2: Consultar operaciones"""
    print_separator("EJEMPLO 2: Consultar operaciones")
    
    # Buscar por ID
    operation = repo.get_operation_by_id(1)
    if operation:
        print(f"✅ Operación encontrada por ID 1:")
        print(f"   Símbolo: {operation.symbol}")
        print(f"   Estado: {operation.status.value}")
    
    # Buscar por Magic Number
    operation = repo.get_operation_by_magic_number(123456)
    if operation:
        print(f"\n✅ Operación encontrada por Magic Number 123456:")
        print(f"   ID: {operation.id}")
        print(f"   Tipo: {operation.order_type.value}")
    
    # Listar todas las operaciones abiertas
    open_ops = repo.list_operations(status=OperationStatus.OPEN)
    print(f"\n✅ Total de operaciones abiertas: {len(open_ops)}")
    for op in open_ops:
        print(f"   - {op.symbol} | Magic: {op.magic_number} | {op.direction.value}")


def ejemplo_3_actualizar_operacion(repo: OperationsRepository):
    """Ejemplo 3: Actualizar una operación"""
    print_separator("EJEMPLO 3: Actualizar una operación")
    
    # Actualizar SL a breakeven
    operation = repo.update_operation(
        1,
        stop_loss=1.0851,  # Mover SL a precio de entrada (breakeven)
        actual_entry_price=1.0851
    )
    
    if operation:
        print(f"✅ Operación actualizada a breakeven:")
        print(f"   Stop Loss nuevo: {operation.stop_loss}")
        print(f"   Precio entrada: {operation.actual_entry_price}")


def ejemplo_4_cerrar_operacion(repo: OperationsRepository):
    """Ejemplo 4: Cerrar una operación"""
    print_separator("EJEMPLO 4: Cerrar una operación")
    
    # Cerrar operación con ganancia
    operation = repo.close_operation(
        operation_id=1,
        profit_loss=95.50  # Ganancia en USD
    )
    
    if operation:
        print(f"✅ Operación cerrada exitosamente:")
        print(f"   Profit/Loss: ${operation.profit_loss}")
        print(f"   Estado: {operation.status.value}")
        print(f"   Cerrada en: {operation.close_time}")


def ejemplo_5_pares_dual_market_limit():
    """Ejemplo 5: Crear par de operaciones Market y Limit"""
    print_separator("EJEMPLO 5: Par dual Market/Limit")
    
    repo = OperationsRepository(db_path=Path("data/examples/operations_example.db"))
    
    # Parámetros comunes (sin status, lo estableceremos individualmente)
    base_params = {
        'bot_id': 1,
        'ia_id': 1,
        'symbol': 'GBPUSD',
        'direction': Direction.SELL,
        'suggested_price': 1.2500,
        'stop_loss': 1.2550,
        'take_profit': 1.2400,
        'lot_size': 0.05,
        'risk_percentage': 0.5,
        'conversation_id': 'conv_456_xyz'
    }
    
    # Crear orden MARKET
    market_op = repo.create_operation(
        magic_number=200001,
        order_type=OrderType.MARKET,
        actual_entry_price=1.2501,  # Slippage
        status=OperationStatus.OPEN,
        **base_params
    )
    
    # Crear orden LIMIT
    limit_op = repo.create_operation(
        magic_number=200002,
        order_type=OrderType.LIMIT,
        status=OperationStatus.PENDING,  # Pendiente de activación
        **base_params
    )
    
    print(f"✅ Par dual creado:")
    print(f"   MARKET - ID: {market_op.id} | Magic: {market_op.magic_number} | Estado: {market_op.status.value}")
    print(f"   LIMIT  - ID: {limit_op.id} | Magic: {limit_op.magic_number} | Estado: {limit_op.status.value}")
    
    return repo, market_op, limit_op


def ejemplo_6_multi_activo():
    """Ejemplo 6: Operaciones en múltiples activos"""
    print_separator("EJEMPLO 6: Multi-activo")
    
    repo = OperationsRepository(db_path=Path("data/examples/operations_example.db"))
    
    # EURUSD
    eurusd_op = repo.create_operation(
        magic_number=300001,
        bot_id=1,
        ia_id=1,
        order_type=OrderType.MARKET,
        symbol="EURUSD",
        direction=Direction.BUY,
        suggested_price=1.0850,
        actual_entry_price=1.0851,
        stop_loss=1.0800,
        take_profit=1.0950,
        lot_size=0.10,
        risk_percentage=1.0,
        status=OperationStatus.OPEN
    )
    
    # XAUUSD (Oro)
    xauusd_op = repo.create_operation(
        magic_number=300002,
        bot_id=1,
        ia_id=1,
        order_type=OrderType.MARKET,
        symbol="XAUUSD",
        direction=Direction.SELL,
        suggested_price=1950.00,
        actual_entry_price=1950.50,
        stop_loss=1970.00,
        take_profit=1900.00,
        lot_size=0.02,
        risk_percentage=2.0,
        status=OperationStatus.OPEN
    )
    
    # GBPJPY
    gbpjpy_op = repo.create_operation(
        magic_number=300003,
        bot_id=1,
        ia_id=1,
        order_type=OrderType.MARKET,
        symbol="GBPJPY",
        direction=Direction.BUY,
        suggested_price=185.50,
        actual_entry_price=185.52,
        stop_loss=184.50,
        take_profit=187.50,
        lot_size=0.05,
        risk_percentage=1.5,
        status=OperationStatus.OPEN
    )
    
    print(f"✅ Operaciones creadas en múltiples activos:")
    
    # Listar por símbolo
    for symbol in ["EURUSD", "XAUUSD", "GBPJPY"]:
        ops = repo.list_operations(symbol=symbol)
        print(f"   {symbol}: {len(ops)} operación(es)")


def ejemplo_7_estadisticas():
    """Ejemplo 7: Estadísticas y métricas"""
    print_separator("EJEMPLO 7: Estadísticas")
    
    repo = OperationsRepository(db_path=Path("data/examples/operations_example.db"))
    
    # Contar operaciones por estado
    total = repo.count_operations()
    abiertas = repo.count_operations(status=OperationStatus.OPEN)
    cerradas = repo.count_operations(status=OperationStatus.CLOSED)
    pendientes = repo.count_operations(status=OperationStatus.PENDING)
    
    print(f"📊 Estadísticas de operaciones:")
    print(f"   Total: {total}")
    print(f"   Abiertas: {abiertas}")
    print(f"   Cerradas: {cerradas}")
    print(f"   Pendientes: {pendientes}")
    
    # Listar operaciones cerradas con ganancia
    operaciones_cerradas = repo.list_operations(status=OperationStatus.CLOSED)
    if operaciones_cerradas:
        print(f"\n💰 Operaciones cerradas:")
        for op in operaciones_cerradas:
            resultado = "✅ WIN" if op.profit_loss and op.profit_loss > 0 else "❌ LOSS"
            print(f"   {op.symbol} | ${op.profit_loss:.2f} | {resultado}")


def ejemplo_8_flujo_completo():
    """Ejemplo 8: Flujo completo de vida de una operación"""
    print_separator("EJEMPLO 8: Flujo completo de operación")
    
    repo = OperationsRepository(db_path=Path("data/examples/operations_example.db"))
    
    print("1️⃣ Verificar si existe operación abierta...")
    existing = repo.get_open_operation_for_symbol_and_magic(
        symbol="USDJPY",
        magic_number=400001
    )
    
    if existing:
        print(f"   ⚠️ Ya existe operación abierta: ID {existing.id}")
    else:
        print(f"   ✅ No hay operación abierta, podemos crear nueva")
        
        print("\n2️⃣ Crear nueva operación...")
        operation = repo.create_operation(
            magic_number=400001,
            bot_id=1,
            ia_id=1,
            order_type=OrderType.MARKET,
            symbol="USDJPY",
            direction=Direction.BUY,
            suggested_price=148.50,
            actual_entry_price=148.52,
            stop_loss=147.50,
            take_profit=150.50,
            lot_size=0.10,
            risk_percentage=1.0,
            status=OperationStatus.OPEN,
            conversation_id="conv_789_usdjpy"
        )
        print(f"   ✅ Operación creada: ID {operation.id}")
        
        print("\n3️⃣ Simular reevaluación - mover SL a breakeven...")
        if operation.id:
            updated_operation = repo.update_operation(
                operation.id,
                stop_loss=148.52  # Breakeven
            )
            if updated_operation:
                print(f"   ✅ SL actualizado a breakeven: {updated_operation.stop_loss}")
        
        print("\n4️⃣ Simular cierre con ganancia...")
        if operation.id:
            closed_operation = repo.close_operation(
                operation_id=operation.id,
                profit_loss=180.00
            )
            if closed_operation:
                print(f"   ✅ Operación cerrada con ganancia: ${closed_operation.profit_loss}")
                print(f"   📅 Abierta en: {closed_operation.open_time}")
                print(f"   📅 Cerrada en: {closed_operation.close_time}")


def main():
    """Función principal que ejecuta todos los ejemplos"""
    print("\n" + "="*60)
    print(" EJEMPLOS DE USO: OperationsRepository (T32)")
    print("="*60)
    
    # Ejemplo 1: Crear operación básica
    repo, operation = ejemplo_1_crear_operacion()
    
    # Ejemplo 2: Consultar operaciones
    ejemplo_2_consultar_operaciones(repo)
    
    # Ejemplo 3: Actualizar operación
    ejemplo_3_actualizar_operacion(repo)
    
    # Ejemplo 4: Cerrar operación
    ejemplo_4_cerrar_operacion(repo)
    
    # Ejemplo 5: Pares dual Market/Limit
    repo, market_op, limit_op = ejemplo_5_pares_dual_market_limit()
    
    # Ejemplo 6: Multi-activo
    ejemplo_6_multi_activo()
    
    # Ejemplo 7: Estadísticas
    ejemplo_7_estadisticas()
    
    # Ejemplo 8: Flujo completo
    ejemplo_8_flujo_completo()
    
    print_separator("EJEMPLOS COMPLETADOS")
    print("✅ Todos los ejemplos se ejecutaron correctamente")
    print(f"📁 Base de datos: data/examples/operations_example.db")
    print(f"💡 Revisa el código en examples/operations_repository_example.py")
    print(f"📚 Documentación: context/DOCUMENTACION/T32_persistencia_operaciones.md\n")


if __name__ == "__main__":
    main()
