"""
Script para verificar cómo se manejan horarios sin símbolos configurados
"""

from datetime import datetime
from src.core.trading_session_manager import TradingSessionManager

manager = TradingSessionManager()

print('='*70)
print('Verificando horarios 00:00-02:00 AM')
print('='*70)

# Probar diferentes símbolos en la madrugada
test_times = [
    datetime(2025, 1, 15, 0, 0),
    datetime(2025, 1, 15, 0, 30),
    datetime(2025, 1, 15, 1, 0),
    datetime(2025, 1, 15, 1, 30),
]

symbols_to_test = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']

for test_time in test_times:
    print(f'\n📅 Hora: {test_time.strftime("%H:%M")}')
    print('-'*70)
    for symbol in symbols_to_test:
        is_tradeable, reason = manager.is_symbol_tradeable(symbol, test_time)
        status = '✅' if is_tradeable else '❌'
        print(f'{status} {symbol:8} | {reason}')
    
    # Mostrar símbolos activos globalmente
    active = manager.get_active_symbols(test_time)
    print(f'\n🌍 Símbolos activos globales: {active if active else "NINGUNO"}')

print('\n' + '='*70)
print('Configuración de sesiones:')
print('='*70)

# Mostrar configuración de sesiones relevantes
sessions_to_check = ['asia_madrugada', 'londres']

for session_name in sessions_to_check:
    if session_name in manager.sessions:
        session = manager.sessions[session_name]
        print(f'\n📋 {session_name}:')
        print(f'   Horario: {session["start"]} - {session["end"]}')
        print(f'   Símbolos: {session["symbols"]}')
        print(f'   Risk level: {session["risk_level"]}')

print('\n' + '='*70)
print('Prueba con horarios SIN ninguna sesión configurada (ej: 06:00-07:00)')
print('='*70)

test_time = datetime(2025, 1, 15, 6, 30)
print(f'\n📅 Hora: {test_time.strftime("%H:%M")}')
print('-'*70)
for symbol in symbols_to_test:
    is_tradeable, reason = manager.is_symbol_tradeable(symbol, test_time)
    status = '✅' if is_tradeable else '❌'
    print(f'{status} {symbol:8} | {reason}')

active = manager.get_active_symbols(test_time)
print(f'\n🌍 Símbolos activos globales: {active if active else "NINGUNO"}')
