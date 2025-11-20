"""Test para verificar que la dead_zone (13:00-18:00) no permite ningún símbolo.

Este test verifica que el problema reportado (bot operando a las 13:52) 
ha sido resuelto después de eliminar test_session del archivo de configuración.
"""

from datetime import datetime, time
from src.core.trading_session_manager import TradingSessionManager


def test_dead_zone_no_symbols():
    """Verifica que ningún símbolo esté activo durante la dead_zone (13:00-18:00)."""
    
    manager = TradingSessionManager()
    
    # Simular diferentes horas dentro de la dead_zone
    test_times = [
        datetime(2025, 11, 20, 13, 0, 0),   # 13:00 - Inicio de dead_zone
        datetime(2025, 11, 20, 13, 52, 0),  # 13:52 - Hora del problema reportado
        datetime(2025, 11, 20, 15, 0, 0),   # 15:00 - Mitad de dead_zone
        datetime(2025, 11, 20, 17, 59, 59), # 17:59:59 - Final de dead_zone
    ]
    
    test_symbols = [
        "EURUSD", "GBPUSD", "USDCAD", "USDCHF", 
        "XAUUSD", "USDJPY", "AUDUSD", "NZDUSD"
    ]
    
    print("\n" + "=" * 70)
    print("TEST: Verificación de Dead Zone (13:00-18:00)")
    print("=" * 70)
    
    all_passed = True
    
    for test_time in test_times:
        print(f"\n⏰ Hora: {test_time.strftime('%H:%M:%S')}")
        print("-" * 70)
        
        # Verificar que no haya símbolos activos
        active_symbols = manager.get_active_symbols(test_time)
        
        if len(active_symbols) == 0:
            print(f"✅ CORRECTO: Ningún símbolo activo (dead_zone)")
        else:
            print(f"❌ ERROR: Se encontraron símbolos activos: {', '.join(active_symbols)}")
            all_passed = False
        
        # Verificar cada símbolo individualmente
        for symbol in test_symbols:
            is_tradeable, reason = manager.is_symbol_tradeable(
                symbol=symbol,
                current_time=test_time,
                has_open_position=False
            )
            
            if is_tradeable:
                print(f"  ❌ {symbol}: INCORRECTO - Permitido en dead_zone ({reason})")
                all_passed = False
            else:
                print(f"  ✅ {symbol}: Bloqueado correctamente ({reason})")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ TEST PASADO: Dead zone funciona correctamente")
        print("   Ningún símbolo está activo entre 13:00-18:00")
    else:
        print("❌ TEST FALLIDO: Hay símbolos activos en dead_zone")
        print("   Revisar configuración de trading_sessions.json")
    print("=" * 70)
    
    return all_passed


def test_valid_sessions():
    """Verifica que los horarios válidos SÍ permitan símbolos."""
    
    manager = TradingSessionManager()
    
    test_cases = [
        # (hora, símbolo, debería_permitir, sesión_esperada)
        (datetime(2025, 11, 20, 9, 0, 0), "EURUSD", True, "ny_londres_overlap"),
        (datetime(2025, 11, 20, 3, 0, 0), "GBPUSD", True, "londres"),
        (datetime(2025, 11, 20, 20, 0, 0), "USDJPY", True, "asia"),
        (datetime(2025, 11, 20, 12, 0, 0), "USDCAD", True, "ny_tarde"),
        (datetime(2025, 11, 20, 1, 0, 0), "AUDUSD", True, "asia_madrugada"),
    ]
    
    print("\n" + "=" * 70)
    print("TEST: Verificación de Sesiones Válidas")
    print("=" * 70)
    
    all_passed = True
    
    for test_time, symbol, should_allow, expected_session in test_cases:
        is_tradeable, reason = manager.is_symbol_tradeable(
            symbol=symbol,
            current_time=test_time,
            has_open_position=False
        )
        
        if is_tradeable == should_allow:
            session_match = expected_session in reason if expected_session else True
            if session_match:
                print(f"✅ {test_time.strftime('%H:%M')} | {symbol}: {reason}")
            else:
                print(f"⚠️  {test_time.strftime('%H:%M')} | {symbol}: Permitido pero sesión incorrecta")
                print(f"   Esperado: {expected_session}, Recibido: {reason}")
                all_passed = False
        else:
            print(f"❌ {test_time.strftime('%H:%M')} | {symbol}: Estado incorrecto")
            print(f"   Esperado: {'Permitido' if should_allow else 'Bloqueado'}, Recibido: {'Permitido' if is_tradeable else 'Bloqueado'}")
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("✅ TEST PASADO: Todas las sesiones válidas funcionan correctamente")
    else:
        print("❌ TEST FALLIDO: Hay problemas con las sesiones válidas")
    print("=" * 70)
    
    return all_passed


def test_reevaluation_with_position():
    """Verifica que la reevaluación funcione fuera de horario si hay posición abierta."""
    
    manager = TradingSessionManager()
    
    # Probar en dead_zone con posición abierta
    test_time = datetime(2025, 11, 20, 14, 0, 0)  # 14:00 - plena dead_zone
    
    print("\n" + "=" * 70)
    print("TEST: Verificación de Reevaluación con Posición Abierta")
    print("=" * 70)
    print(f"⏰ Hora: {test_time.strftime('%H:%M:%S')} (Dead Zone)")
    print("-" * 70)
    
    all_passed = True
    
    # Sin posición - debe bloquear
    is_tradeable, reason = manager.is_symbol_tradeable(
        symbol="EURUSD",
        current_time=test_time,
        has_open_position=False
    )
    
    if not is_tradeable:
        print(f"✅ SIN posición: Bloqueado correctamente ({reason})")
    else:
        print(f"❌ SIN posición: INCORRECTO - No debería permitir ({reason})")
        all_passed = False
    
    # Con posición - debe permitir para reevaluación
    is_tradeable, reason = manager.is_symbol_tradeable(
        symbol="EURUSD",
        current_time=test_time,
        has_open_position=True
    )
    
    if is_tradeable and "reevaluación" in reason.lower():
        print(f"✅ CON posición: Permitido para reevaluación ({reason})")
    else:
        print(f"❌ CON posición: INCORRECTO - Debería permitir reevaluación ({reason})")
        all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("✅ TEST PASADO: Reevaluación funciona correctamente")
    else:
        print("❌ TEST FALLIDO: Problemas con reevaluación")
    print("=" * 70)
    
    return all_passed


def main():
    """Ejecuta todos los tests de verificación."""
    print("\n")
    print("█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  SUITE DE TESTS: VERIFICACIÓN DE HORARIOS DE TRADING".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    results = {
        "Dead Zone": test_dead_zone_no_symbols(),
        "Sesiones Válidas": test_valid_sessions(),
        "Reevaluación": test_reevaluation_with_position(),
    }
    
    print("\n")
    print("=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASADO" if passed else "❌ FALLIDO"
        print(f"{test_name:.<50} {status}")
    
    print("=" * 70)
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 TODOS LOS TESTS PASARON")
        print("El problema de trading en horarios incorrectos ha sido resuelto.")
        print("\nConfiguración verificada:")
        print("  ✅ Dead zone (13:00-18:00) bloquea todos los símbolos")
        print("  ✅ Sesiones válidas permiten símbolos correctos")
        print("  ✅ Reevaluación de posiciones funciona correctamente")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        print("Revisa la configuración de trading_sessions.json")
    
    print("\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
