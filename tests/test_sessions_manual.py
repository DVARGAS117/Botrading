"""
Script de prueba manual para TradingSessionManager

Ejecuta diferentes escenarios para verificar la lógica de sesiones.
"""

from datetime import datetime, time
from pathlib import Path
import sys

# Asegurar que el path incluya src
sys.path.insert(0, str(Path(__file__).parent))

from src.core.trading_session_manager import TradingSessionManager


def test_basic_functionality():
    """Tests básicos de funcionalidad."""
    print("="*70)
    print("TEST 1: Inicialización y carga de configuración")
    print("="*70)
    
    manager = TradingSessionManager()
    print(f"✅ Sesiones cargadas: {len(manager.sessions)}")
    print(f"✅ Global rules: {manager.global_rules}")
    print()
    
    print("="*70)
    print("TEST 2: EURUSD en horario NY+Londres overlap (09:00)")
    print("="*70)
    
    test_time = datetime(2025, 1, 15, 9, 0)
    is_tradeable, reason = manager.is_symbol_tradeable("EURUSD", test_time)
    
    print(f"Hora: {test_time.strftime('%H:%M')}")
    print(f"Símbolo: EURUSD")
    print(f"¿Puede operar?: {is_tradeable}")
    print(f"Razón: {reason}")
    print()
    
    print("="*70)
    print("TEST 3: EURUSD en dead_zone (14:00) SIN posición")
    print("="*70)
    
    test_time = datetime(2025, 1, 15, 14, 0)
    is_tradeable, reason = manager.is_symbol_tradeable(
        "EURUSD", 
        test_time,
        has_open_position=False
    )
    
    print(f"Hora: {test_time.strftime('%H:%M')}")
    print(f"Símbolo: EURUSD")
    print(f"Posición abierta: No")
    print(f"¿Puede operar?: {is_tradeable}")
    print(f"Razón: {reason}")
    print()
    
    print("="*70)
    print("TEST 4: EURUSD en dead_zone (14:00) CON posición")
    print("="*70)
    
    is_tradeable, reason = manager.is_symbol_tradeable(
        "EURUSD", 
        test_time,
        has_open_position=True
    )
    
    print(f"Hora: {test_time.strftime('%H:%M')}")
    print(f"Símbolo: EURUSD")
    print(f"Posición abierta: Sí")
    print(f"¿Puede operar?: {is_tradeable}")
    print(f"Razón: {reason}")
    print()
    
    print("="*70)
    print("TEST 5: USDJPY en sesión Asia (20:00)")
    print("="*70)
    
    test_time = datetime(2025, 1, 15, 20, 0)
    is_tradeable, reason = manager.is_symbol_tradeable("USDJPY", test_time)
    
    print(f"Hora: {test_time.strftime('%H:%M')}")
    print(f"Símbolo: USDJPY")
    print(f"¿Puede operar?: {is_tradeable}")
    print(f"Razón: {reason}")
    print()
    
    print("="*70)
    print("TEST 6: Símbolos activos en diferentes horarios")
    print("="*70)
    
    test_times = [
        datetime(2025, 1, 15, 3, 0),   # Londres
        datetime(2025, 1, 15, 9, 0),   # NY+Londres overlap
        datetime(2025, 1, 15, 15, 0),  # Dead zone
        datetime(2025, 1, 15, 20, 0),  # Asia
    ]
    
    for test_time in test_times:
        active = manager.get_active_symbols(test_time)
        print(f"{test_time.strftime('%H:%M')}: {', '.join(active) if active else 'NINGUNO'}")
    
    print()
    
    print("="*70)
    print("TEST 7: Información completa de sesión")
    print("="*70)
    
    test_time = datetime(2025, 1, 15, 9, 0)
    info = manager.get_current_session_info("EURUSD", test_time)
    
    print(f"Hora: {test_time.strftime('%H:%M')}")
    print(f"Símbolo: EURUSD")
    print(f"¿Puede operar?: {info['is_tradeable']}")
    print(f"Sesión activa: {info['session_name']}")
    print(f"Razón: {info['reason']}")
    
    if info['session_data']:
        print(f"Estrategias permitidas: {', '.join(info['session_data']['strategies'])}")
        print(f"Nivel de riesgo: {info['session_data']['risk_level']}")
    
    print()
    
    print("="*70)
    print("TEST 8: Sesión que cruza medianoche")
    print("="*70)
    
    # Asia va de 19:00 a 23:59
    test_time = datetime(2025, 1, 15, 23, 30)
    is_tradeable, reason = manager.is_symbol_tradeable("USDJPY", test_time)
    print(f"23:30 - USDJPY: {is_tradeable} ({reason})")
    
    # Asia madrugada va de 00:00 a 02:00
    test_time = datetime(2025, 1, 15, 1, 0)
    is_tradeable, reason = manager.is_symbol_tradeable("USDJPY", test_time)
    print(f"01:00 - USDJPY: {is_tradeable} ({reason})")
    
    print()
    
    print("="*70)
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print("="*70)


if __name__ == "__main__":
    test_basic_functionality()
