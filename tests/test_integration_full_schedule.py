"""Test de integración completo del sistema de horarios.

Verifica todos los horarios del día y confirma que los símbolos correctos
están activos en cada momento según la documentación.
"""

from datetime import datetime, timedelta
from src.core.trading_session_manager import TradingSessionManager


def test_all_day_schedule():
    """Verifica cada hora del día contra la configuración esperada."""
    
    manager = TradingSessionManager()
    
    # Configuración esperada por hora
    expected_config = {
        0: {"session": "asia_madrugada", "symbols": ["USDJPY", "AUDUSD", "NZDUSD"]},
        1: {"session": "asia_madrugada", "symbols": ["USDJPY", "AUDUSD", "NZDUSD"]},
        2: {"session": "londres", "symbols": ["EURUSD", "GBPUSD", "EURGBP"]},
        3: {"session": "londres", "symbols": ["EURUSD", "GBPUSD", "EURGBP"]},
        4: {"session": "londres", "symbols": ["EURUSD", "GBPUSD", "EURGBP"]},
        5: {"session": None, "symbols": []},  # Gap intencional
        6: {"session": None, "symbols": []},
        7: {"session": None, "symbols": []},
        8: {"session": "ny_londres_overlap", "symbols": ["EURUSD", "GBPUSD", "USDCAD", "USDCHF", "XAUUSD"]},
        9: {"session": "ny_londres_overlap", "symbols": ["EURUSD", "GBPUSD", "USDCAD", "USDCHF", "XAUUSD"]},
        10: {"session": "ny_londres_overlap", "symbols": ["EURUSD", "GBPUSD", "USDCAD", "USDCHF", "XAUUSD"]},
        11: {"session": "ny_tarde", "symbols": ["EURUSD", "USDCAD"]},
        12: {"session": "ny_tarde", "symbols": ["EURUSD", "USDCAD"]},
        13: {"session": "dead_zone", "symbols": []},  # ⛔ NO OPERAR
        14: {"session": "dead_zone", "symbols": []},
        15: {"session": "dead_zone", "symbols": []},
        16: {"session": "dead_zone", "symbols": []},
        17: {"session": "dead_zone", "symbols": []},
        18: {"session": "dead_zone", "symbols": []},
        19: {"session": "asia", "symbols": ["USDJPY", "AUDUSD", "NZDUSD", "AUDJPY"]},
        20: {"session": "asia", "symbols": ["USDJPY", "AUDUSD", "NZDUSD", "AUDJPY"]},
        21: {"session": "asia", "symbols": ["USDJPY", "AUDUSD", "NZDUSD", "AUDJPY"]},
        22: {"session": "asia", "symbols": ["USDJPY", "AUDUSD", "NZDUSD", "AUDJPY"]},
        23: {"session": "asia", "symbols": ["USDJPY", "AUDUSD", "NZDUSD", "AUDJPY"]},
    }
    
    print("\n" + "=" * 80)
    print("TEST INTEGRACIÓN: Verificación de Horarios Completos (24 horas)")
    print("=" * 80)
    
    base_date = datetime(2025, 11, 20, 0, 0, 0)
    all_passed = True
    failed_hours = []
    
    for hour in range(24):
        test_time = base_date.replace(hour=hour)
        expected = expected_config[hour]
        
        # Obtener símbolos activos
        active_symbols = set(manager.get_active_symbols(test_time))
        expected_symbols = set(expected["symbols"])
        
        # Comparar
        if active_symbols == expected_symbols:
            status = "✅"
            session_name = expected["session"] or "---"
            symbol_count = len(active_symbols)
            symbol_str = f"{symbol_count} símbolos" if symbol_count > 0 else "NINGUNO"
        else:
            status = "❌"
            session_name = expected["session"] or "---"
            symbol_str = f"Esperado: {len(expected_symbols)}, Actual: {len(active_symbols)}"
            all_passed = False
            failed_hours.append(hour)
        
        print(f"{status} {hour:02d}:00 | {session_name:<20} | {symbol_str}")
    
    print("=" * 80)
    
    if all_passed:
        print("✅ TODOS LOS HORARIOS SON CORRECTOS")
        print("\nSesiones validadas:")
        print("  • 00:00-02:00: Asia Madrugada ✅")
        print("  • 02:00-05:00: Londres ✅")
        print("  • 05:00-08:00: Sin sesión (gap intencional) ✅")
        print("  • 08:00-11:00: NY + Londres Overlap (ZONA ORO) 🔥")
        print("  • 11:00-13:00: NY Tarde ✅")
        print("  • 13:00-19:00: Dead Zone (NO OPERAR) ⛔")
        print("  • 19:00-00:00: Asia ✅")
    else:
        print(f"❌ HAY {len(failed_hours)} HORAS CON PROBLEMAS")
        print(f"   Horas fallidas: {', '.join(f'{h:02d}:00' for h in failed_hours)}")
    
    print("=" * 80 + "\n")
    
    return all_passed


def test_critical_hours():
    """Verifica las horas críticas mencionadas en el problema."""
    
    manager = TradingSessionManager()
    
    print("\n" + "=" * 80)
    print("TEST CRÍTICO: Horas Específicas del Problema")
    print("=" * 80)
    
    critical_tests = [
        {
            "time": datetime(2025, 11, 20, 13, 52, 0),
            "expected_symbols": [],
            "description": "Hora del problema reportado (13:52)"
        },
        {
            "time": datetime(2025, 11, 20, 9, 0, 0),
            "expected_symbols": ["EURUSD", "GBPUSD", "USDCAD", "USDCHF", "XAUUSD"],
            "description": "Zona de oro - Máxima liquidez (09:00)"
        },
        {
            "time": datetime(2025, 11, 20, 15, 30, 0),
            "expected_symbols": [],
            "description": "Plena dead zone (15:30)"
        },
        {
            "time": datetime(2025, 11, 20, 20, 0, 0),
            "expected_symbols": ["USDJPY", "AUDUSD", "NZDUSD", "AUDJPY"],
            "description": "Sesión asiática (20:00)"
        },
    ]
    
    all_passed = True
    
    for test in critical_tests:
        test_time = test["time"]
        expected = set(test["expected_symbols"])
        actual = set(manager.get_active_symbols(test_time))
        
        passed = (expected == actual)
        status = "✅" if passed else "❌"
        
        print(f"\n{status} {test['description']}")
        print(f"   Hora: {test_time.strftime('%H:%M:%S')}")
        
        if passed:
            if len(expected) > 0:
                print(f"   ✓ Símbolos activos correctos: {', '.join(sorted(expected))}")
            else:
                print(f"   ✓ Correctamente bloqueado (dead zone)")
        else:
            print(f"   ✗ Esperado: {sorted(expected) if expected else 'NINGUNO'}")
            print(f"   ✗ Actual: {sorted(actual) if actual else 'NINGUNO'}")
            all_passed = False
    
    print("\n" + "=" * 80)
    
    if all_passed:
        print("✅ TODOS LOS TESTS CRÍTICOS PASARON")
    else:
        print("❌ ALGUNOS TESTS CRÍTICOS FALLARON")
    
    print("=" * 80 + "\n")
    
    return all_passed


def main():
    """Ejecuta todos los tests de integración."""
    
    print("\n")
    print("█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  TEST DE INTEGRACIÓN COMPLETO - SISTEMA DE HORARIOS".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    results = {
        "Horarios Completos (24h)": test_all_day_schedule(),
        "Horas Críticas": test_critical_hours(),
    }
    
    print("\n" + "=" * 80)
    print("RESUMEN FINAL DE INTEGRACIÓN")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASADO" if passed else "❌ FALLIDO"
        print(f"{test_name:.<60} {status}")
    
    print("=" * 80)
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 INTEGRACIÓN COMPLETA EXITOSA")
        print("\nEl sistema de horarios funciona correctamente:")
        print("  ✅ Las 24 horas del día están correctamente configuradas")
        print("  ✅ Dead zone bloquea correctamente las operaciones")
        print("  ✅ Zonas de alta liquidez están bien definidas")
        print("  ✅ El bot NO operará en horarios incorrectos")
        print("\n✨ El problema reportado (operación a las 13:52) está RESUELTO")
    else:
        print("\n❌ INTEGRACIÓN CON PROBLEMAS")
        print("Revisa los detalles arriba para identificar los fallos")
    
    print("\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
