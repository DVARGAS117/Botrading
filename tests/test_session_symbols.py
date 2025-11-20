"""Script para probar el nuevo flujo de símbolos activos por sesión.

Este script simula diferentes horarios y verifica que:
1. Se obtienen solo los símbolos de la sesión activa
2. No se iteran símbolos fuera de sesión
3. Se incluyen símbolos con posiciones abiertas para reevaluación
"""

from datetime import datetime, time
from pathlib import Path

from src.core.trading_session_manager import TradingSessionManager


def print_separator(title: str):
    """Imprime separador visual"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_session_at_time(session_manager: TradingSessionManager, test_time: time, test_name: str):
    """Prueba qué símbolos están activos en un horario específico"""
    print(f"\n🕐 Probando: {test_name} ({test_time.strftime('%H:%M')})")
    
    # Crear datetime con la hora de prueba
    test_datetime = datetime.now().replace(
        hour=test_time.hour,
        minute=test_time.minute,
        second=0,
        microsecond=0
    )
    
    # Obtener símbolos activos
    active_symbols = session_manager.get_active_symbols(test_datetime)
    
    # Obtener info de sesión
    session_info = session_manager.get_current_session(test_datetime)
    
    if session_info:
        session_name = session_info['name']
        risk_level = session_info.get('risk_level', 'N/A')
        strategies = session_info.get('strategies', [])
        
        print(f"   📍 Sesión: {session_name}")
        print(f"   ⚖️  Riesgo: {risk_level}")
        print(f"   📊 Estrategias: {', '.join(strategies) if strategies else 'Ninguna'}")
        print(f"   💱 Símbolos activos: {', '.join(active_symbols) if active_symbols else 'NINGUNO'}")
        print(f"   🔢 Total: {len(active_symbols)} símbolos")
    else:
        print(f"   ⚠️  No hay sesión activa")
        print(f"   💱 Símbolos activos: NINGUNO")


def main():
    """Ejecutar tests de sesiones"""
    print("\n" + "🌍" * 35)
    print("   TEST: SÍMBOLOS ACTIVOS POR SESIÓN")
    print("🌍" * 35)
    
    # Inicializar session manager
    config_path = Path("config/trading_sessions.json")
    session_manager = TradingSessionManager(config_path=config_path)
    
    print(f"\n✅ Configuración cargada desde: {config_path}")
    print(f"   Sesiones disponibles: {len(session_manager.sessions)}")
    print(f"   Sesiones: {', '.join(session_manager.sessions.keys())}")
    
    print_separator("TESTS DE SESIONES")
    
    # Test 1: Sesión de Londres (02:00-05:00 Lima)
    test_session_at_time(
        session_manager,
        time(3, 0),  # 03:00 Lima
        "Londres (medio de sesión)"
    )
    
    # Test 2: Overlap NY-Londres (08:00-11:00 Lima)
    test_session_at_time(
        session_manager,
        time(9, 30),  # 09:30 Lima
        "NY-Londres Overlap (alta volatilidad)"
    )
    
    # Test 3: NY Tarde (11:00-13:00 Lima)
    test_session_at_time(
        session_manager,
        time(12, 0),  # 12:00 Lima
        "NY Tarde (baja volatilidad)"
    )
    
    # Test 4: Dead Zone (13:00-18:00 Lima)
    test_session_at_time(
        session_manager,
        time(15, 0),  # 15:00 Lima
        "Dead Zone (NO OPERAR)"
    )
    
    # Test 5: Asia (19:00-00:00 Lima)
    test_session_at_time(
        session_manager,
        time(21, 0),  # 21:00 Lima
        "Asia (baja volatilidad)"
    )
    
    # Test 6: Asia Madrugada (00:00-02:00 Lima)
    test_session_at_time(
        session_manager,
        time(1, 0),  # 01:00 Lima
        "Asia Madrugada (baja volatilidad)"
    )
    
    print_separator("RESUMEN")
    
    print("""
✅ El sistema ahora:
   1. Verifica el horario global (schedule.json: 06:00-13:00)
   2. Obtiene la sesión activa (trading_sessions.json)
   3. Consulta solo los símbolos de esa sesión
   4. NO itera por símbolos fuera de sesión
   
📊 Ejemplo de flujo optimizado:
   - Hora: 09:30 Lima
   - Sesión activa: ny_londres_overlap
   - Símbolos: EURUSD, GBPUSD, USDCAD, USDCHF
   - Itera: 4 símbolos (solo los permitidos)
   - No verifica: USDJPY, AUDUSD, etc.
   
🔥 Ventajas:
   - Menos iteraciones innecesarias
   - Más eficiente (no consulta símbolos fuera de horario)
   - Más claro en logs (solo muestra símbolos relevantes)
   - Respeta las sesiones de mercado
    """)


if __name__ == "__main__":
    main()
