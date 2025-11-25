"""Tests para verificación de reevaluación fuera de horario con Magic Numbers estructurados.

Este test garantiza que el bot incluya símbolos con posiciones abiertas
aunque el magic number sea de 6 dígitos (nuevo esquema) y no coincida
directamente con bot_id legacy.

Escenario:
 - Bot ID = 3
 - Posición abierta con magic = 300000 (market order estructurada)
 - Sesión actual sin símbolos activos (simulada) -> solo debe incluir símbolo por reevaluación.

El test falla en la implementación anterior porque filtraba pos.magic == bot_id.
"""

from datetime import datetime
from typing import List

from src.bots.base.base_bot_operations import BaseBotOperations, BotConfig, BotMode
from src.core.trading_session_manager import TradingSessionManager


class DummyPosition:
    def __init__(self, symbol: str, magic: int, ticket: int = 1):
        self.symbol = symbol
        self.magic = magic
        self.ticket = ticket


class DummyMT5Connection:
    def __init__(self, positions: List[DummyPosition]):
        self._positions = positions

    def get_positions(self, symbol: str | None = None):  # Simplified interface
        if symbol:
            return [p for p in self._positions if p.symbol == symbol]
        return list(self._positions)


class DummyBot(BaseBotOperations):
    def prepare_data_for_ai(self, symbol, indicators, or_data, market_context, ohlcv_data=None):
        return ("SYSTEM", f"USER {symbol}")

    def parse_ai_response(self, response_text: str):
        return {"accion": "NO_OPERAR"}


def test_active_symbols_includes_structured_magic_position():
    # Configurar bot con ID 3 y horario amplio para evitar bloqueo por horas.
    config = BotConfig(
        bot_id=3,
        bot_name="INTRADAY Baseline",
        bot_type="numerico",
        mode=BotMode.DEMO,
        symbols=["EURUSD"],
        trading_hours=("00:00", "23:59"),
        enable_dual_orders=False
    )

    bot = DummyBot(config)
    # Marcar inicializado manualmente (evitamos initialize completo)
    bot.is_initialized = True

    # Simular session_manager con lista vacía para obligar reevaluación a depender de posiciones abiertas
    bot.session_manager = TradingSessionManager()
    bot.session_manager.sessions = {"dead_zone": {"start": "13:00", "end": "18:59", "symbols": []}}
    bot.session_manager.global_rules["allow_reevaluation_outside_hours"] = True

    # Inyectar conexión MT5 dummy con posición abierta usando magic estructurado: 300000
    bot.mt5_connection = DummyMT5Connection([
        DummyPosition(symbol="EURUSD", magic=300000)
    ])

    active = bot._get_active_symbols_for_trading()

    assert "EURUSD" in active, (
        f"El símbolo EURUSD debe estar presente para reevaluación. Activos: {active}"
    )
    assert len(active) == 1, f"Solo debe incluir EURUSD. Activos: {active}"

    # Nota: No ejecutamos run_trading_cycle() para evitar dependencias de MT5 y extractores
    # Aquí solo validamos que la fuente de símbolos activos incluya la reevaluación por posiciones abiertas.


if __name__ == "__main__":  # Permite ejecución directa
    test_active_symbols_includes_structured_magic_position()
    print("✅ test_active_symbols_includes_structured_magic_position PASÓ")
