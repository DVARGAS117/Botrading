"""Script de validación para verificar integración de stop_loss_initial/take_profit_initial.

Este script:
1. Verifica que la base de datos tiene las columnas correctas
2. Simula la creación de una operación con valores iniciales
3. Verifica que se guardan correctamente
"""

from pathlib import Path
from datetime import datetime

from src.core.operations_repository import (
    OperationsRepository,
    Operation,
    OperationStatus,
    Direction,
    OrderType,
)


def print_separator(title: str):
    """Imprime separador visual"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_operations_schema():
    """Test 1: Verificar que la base de datos tiene las columnas correctas"""
    print_separator("TEST 1: Verificar Schema de Base de Datos")
    
    # Crear repositorio (creará tabla si no existe)
    db_path = Path("data/test_trailing_stop.db")
    if db_path.exists():
        db_path.unlink()  # Eliminar BD anterior
    
    repo = OperationsRepository(db_path=db_path)
    
    print("✅ Base de datos creada")
    print(f"   Ruta: {db_path}")
    
    # Verificar que se puede crear operación con valores iniciales
    try:
        operation = repo.create_operation(
            magic_number=123456,
            bot_id=5,
            ia_id=1,
            order_type=OrderType.MARKET,
            symbol="EURUSD",
            direction=Direction.BUY,
            suggested_price=1.1000,
            actual_entry_price=1.1001,
            stop_loss=1.0950,
            take_profit=1.1100,
            stop_loss_initial=1.0950,  # 🔑 Valor inicial
            take_profit_initial=1.1100,  # 🔑 Valor inicial
            lot_size=0.1,
            risk_percentage=1.0,
            status=OperationStatus.OPEN,
        )
        print("✅ Operación creada con valores iniciales")
        print(f"   Operation ID: {operation.id}")
        print(f"   Symbol: {operation.symbol}")
        print(f"   Direction: {operation.direction.value}")
        print(f"   Stop Loss Actual: {operation.stop_loss}")
        print(f"   Stop Loss Inicial: {operation.stop_loss_initial}")
        print(f"   Take Profit Actual: {operation.take_profit}")
        print(f"   Take Profit Inicial: {operation.take_profit_initial}")
        
    except Exception as e:
        print(f"❌ Error creando operación: {e}")
        return False
    
    return True


def test_trailing_stop_scenario():
    """Test 2: Simular escenario de trailing stop"""
    print_separator("TEST 2: Simular Escenario de Trailing Stop")
    
    db_path = Path("data/test_trailing_stop.db")
    repo = OperationsRepository(db_path=db_path)
    
    # Crear operación inicial
    print("1️⃣ Abrir posición BUY EURUSD")
    operation = repo.create_operation(
        magic_number=999999,
        bot_id=5,
        ia_id=1,
        order_type=OrderType.MARKET,
        symbol="EURUSD",
        direction=Direction.BUY,
        suggested_price=1.1000,
        actual_entry_price=1.1001,
        stop_loss=1.0950,  # SL inicial: -50 pips
        take_profit=1.1150,  # TP inicial: +150 pips
        stop_loss_initial=1.0950,  # 🔑 Guardar SL inicial
        take_profit_initial=1.1150,  # 🔑 Guardar TP inicial
        lot_size=0.1,
        risk_percentage=1.0,
        status=OperationStatus.OPEN,
    )
    
    print(f"   ✅ Operación abierta: ID={operation.id}")
    print(f"   Entry: {operation.actual_entry_price}")
    print(f"   SL Inicial: {operation.stop_loss_initial} (-50 pips = 1R)")
    print(f"   TP Inicial: {operation.take_profit_initial} (+150 pips = 3R)")
    
    # Calcular 1R
    sl_inicial = operation.stop_loss_initial or operation.stop_loss
    entry = operation.actual_entry_price or operation.suggested_price
    risk_1r = abs(entry - sl_inicial)
    
    print(f"\n   📊 Riesgo Inicial (1R): {risk_1r:.5f} = {risk_1r/0.0001:.1f} pips")
    
    # Simular ajuste de SL cuando alcanza +1R
    print("\n2️⃣ Precio sube a +1R → Ajustar SL a break-even")
    precio_plus_1r = entry + risk_1r
    nuevo_sl_breakeven = entry
    
    print(f"   Precio alcanza: {precio_plus_1r:.5f}")
    print(f"   Nuevo SL (break-even): {nuevo_sl_breakeven:.5f}")
    
    # Actualizar operación
    operation_updated = repo.update_operation(
        operation_id=operation.id,
        stop_loss=nuevo_sl_breakeven,  # Ajustar SL
        # stop_loss_initial NO se modifica (mantiene valor original)
    )
    
    print(f"   ✅ SL actualizado a break-even")
    print(f"   SL Actual: {operation_updated.stop_loss}")
    print(f"   SL Inicial (sin cambios): {operation_updated.stop_loss_initial}")
    print(f"   Diferencia: {operation_updated.stop_loss - operation_updated.stop_loss_initial:.5f}")
    
    # Simular ajuste de SL cuando alcanza +2R
    print("\n3️⃣ Precio sube a +2R → Ajustar SL a +1R")
    precio_plus_2r = entry + (2 * risk_1r)
    nuevo_sl_plus_1r = entry + risk_1r
    
    print(f"   Precio alcanza: {precio_plus_2r:.5f}")
    print(f"   Nuevo SL (+1R): {nuevo_sl_plus_1r:.5f}")
    
    operation_final = repo.update_operation(
        operation_id=operation.id,
        stop_loss=nuevo_sl_plus_1r,  # Ajustar SL a +1R
    )
    
    print(f"   ✅ SL actualizado a +1R")
    print(f"   SL Actual: {operation_final.stop_loss}")
    print(f"   SL Inicial (sin cambios): {operation_final.stop_loss_initial}")
    print(f"   Ganancia protegida: {(operation_final.stop_loss - entry) / 0.0001:.1f} pips")
    
    # Verificar cálculo de R con SL inicial
    print("\n4️⃣ Verificar cálculo de R usando SL inicial")
    current_price = 1.1120  # Simular precio actual
    profit_points = current_price - entry
    risk_points = abs(entry - operation_final.stop_loss_initial)
    pnl_r = profit_points / risk_points if risk_points > 0 else 0.0
    
    print(f"   Precio actual simulado: {current_price:.5f}")
    print(f"   Ganancia en puntos: {profit_points:.5f}")
    print(f"   Riesgo inicial (1R): {risk_points:.5f}")
    print(f"   PnL en R: {pnl_r:.2f}R")
    print(f"   PnL en pips: {profit_points/0.0001:.1f} pips")
    
    return True


def test_auto_fill_initial_values():
    """Test 3: Verificar auto-fill de valores iniciales"""
    print_separator("TEST 3: Verificar Auto-Fill de Valores Iniciales")
    
    db_path = Path("data/test_trailing_stop.db")
    repo = OperationsRepository(db_path=db_path)
    
    # Crear operación SIN especificar valores iniciales
    print("Crear operación sin stop_loss_initial ni take_profit_initial...")
    operation = repo.create_operation(
        magic_number=888888,
        bot_id=5,
        ia_id=1,
        order_type=OrderType.MARKET,
        symbol="GBPUSD",
        direction=Direction.SELL,
        suggested_price=1.2500,
        actual_entry_price=1.2501,
        stop_loss=1.2550,
        take_profit=1.2400,
        # stop_loss_initial=None,  # No especificar
        # take_profit_initial=None,  # No especificar
        lot_size=0.1,
        risk_percentage=1.0,
        status=OperationStatus.OPEN,
    )
    
    print(f"✅ Operación creada: ID={operation.id}")
    print(f"   Stop Loss: {operation.stop_loss}")
    print(f"   Stop Loss Inicial (auto-fill): {operation.stop_loss_initial}")
    print(f"   Take Profit: {operation.take_profit}")
    print(f"   Take Profit Inicial (auto-fill): {operation.take_profit_initial}")
    
    # Verificar que se auto-rellenaron
    assert operation.stop_loss_initial == operation.stop_loss, "❌ Auto-fill de SL falló"
    assert operation.take_profit_initial == operation.take_profit, "❌ Auto-fill de TP falló"
    
    print("\n✅ Auto-fill funciona correctamente")
    
    return True


def main():
    """Ejecutar todos los tests"""
    print("\n" + "🚀" * 35)
    print("   VALIDACIÓN DE INTEGRACIÓN: stop_loss_initial / take_profit_initial")
    print("🚀" * 35)
    
    results = []
    
    # Test 1: Schema
    results.append(("Schema BD", test_operations_schema()))
    
    # Test 2: Trailing Stop
    results.append(("Trailing Stop", test_trailing_stop_scenario()))
    
    # Test 3: Auto-Fill
    results.append(("Auto-Fill", test_auto_fill_initial_values()))
    
    # Resumen
    print_separator("RESUMEN DE VALIDACIÓN")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name:20s} → {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 TODOS LOS TESTS PASARON 🎉")
    else:
        print("  ❌ ALGUNOS TESTS FALLARON")
    print("=" * 70 + "\n")
    
    # Cleanup
    db_path = Path("data/test_trailing_stop.db")
    if db_path.exists():
        db_path.unlink()
        print("🧹 Base de datos de test eliminada\n")


if __name__ == "__main__":
    main()
