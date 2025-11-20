"""Script de prueba rápida para verificar horarios de trading.

Simula la ejecución del bot a las 13:52 (hora del problema reportado)
para confirmar que ya no procesa símbolos en dead_zone.
"""

from datetime import datetime
from src.core.trading_session_manager import TradingSessionManager

def main():
    print("\n" + "=" * 70)
    print("SIMULACIÓN: Bot INTRADAY ejecutándose a las 13:52 (Dead Zone)")
    print("=" * 70)
    
    # Simular hora del problema
    test_time = datetime(2025, 11, 20, 13, 52, 0)
    
    # Símbolos configurados en el bot
    bot_symbols = ["EURUSD", "GBPUSD", "USDCAD", "USDCHF", "XAUUSD"]
    
    manager = TradingSessionManager()
    
    print(f"\n⏰ Hora actual simulada: {test_time.strftime('%H:%M:%S')}")
    print(f"📋 Símbolos configurados en bot: {', '.join(bot_symbols)}")
    print("\n" + "-" * 70)
    
    # Obtener símbolos activos según sesiones
    active_symbols = manager.get_active_symbols(test_time)
    
    print(f"\n🔍 Verificando sesiones activas...")
    
    if len(active_symbols) == 0:
        print("✅ CORRECTO: Ningún símbolo activo (dead_zone)")
        print("\n📊 Estado esperado del bot:")
        print("   ⏸️  No hay símbolos permitidos en la sesión actual (dead_zone)")
        print("   ⏭️  El bot NO procesará ningún símbolo")
        print("   ⏰ Próxima sesión: 'asia' a las 19:00")
    else:
        print(f"❌ ERROR: Símbolos activos encontrados: {', '.join(active_symbols)}")
        print("   Esto NO debería ocurrir en dead_zone")
        print("   Revisa config/trading_sessions.json")
    
    print("\n" + "-" * 70)
    print("\n📊 Verificación individual de símbolos:")
    
    for symbol in bot_symbols:
        is_tradeable, reason = manager.is_symbol_tradeable(
            symbol=symbol,
            current_time=test_time,
            has_open_position=False
        )
        
        status = "✅" if not is_tradeable else "❌"
        action = "SKIP" if not is_tradeable else "PROCESAR"
        
        print(f"{status} {symbol:<8} → {action:<10} | {reason}")
    
    print("\n" + "-" * 70)
    print("\n💡 Simulación de caso con posición abierta:")
    
    # Simular EURUSD con posición abierta
    is_tradeable, reason = manager.is_symbol_tradeable(
        symbol="EURUSD",
        current_time=test_time,
        has_open_position=True
    )
    
    if is_tradeable and "reevaluación" in reason.lower():
        print("✅ EURUSD (CON posición) → PROCESAR | " + reason)
        print("   El bot SÍ puede reevaluar para cerrar o ajustar la posición")
    else:
        print(f"❌ EURUSD (CON posición) → Estado inesperado: {reason}")
    
    print("\n" + "=" * 70)
    print("✅ Verificación completada")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
