"""Tests unitarios para cierre de posición sin ticket usando caché de magic.

Objetivo: validar que `_execute_close_position` cierra correctamente una posición
cuando la decisión de la IA no incluye `ticket` pero existe `magic` en
`_active_magic_by_symbol` y sólo hay una posición coincidente.

Escenarios cubiertos:
1. Cierre determinista con caché (una posición) -> debe invocar close_position.
2. Cierre abortado por múltiples posiciones sin caché -> no debe invocar close_position.

Nota: Se mockean los componentes MT5 y OrderManager para no depender de conexión real.
"""

from __future__ import annotations

from typing import Any, Dict, List

import types

from src.bots.base.base_bot_operations import BaseBotOperations, BotConfig, BotMode


class DummyPosition:
    def __init__(self, symbol: str, ticket: int, magic: int):
        self.symbol = symbol
        self.ticket = ticket
        self.magic = magic


class DummyMT5Connection:
    def __init__(self, positions: List[DummyPosition]):
        self._positions = positions

    def get_positions(self, symbol: str | None = None) -> List[DummyPosition]:  # interface compatible
        if symbol is None:
            return list(self._positions)
        return [p for p in self._positions if p.symbol == symbol]


class DummyOrderManager:
    def __init__(self):
        self.closed_tickets: List[int] = []

    def close_position(self, ticket: int) -> None:
        self.closed_tickets.append(ticket)


class DummyBot(BaseBotOperations):
    """Implementación mínima concreta para pruebas unitarias."""

    def prepare_data_for_ai(
        self,
        symbol: str,
        indicators: Dict,
        or_data: Any,
        market_context: Any,
        ohlcv_data: Dict | None = None,
    ) -> tuple[str, str]:  # pragma: no cover - no se usa en estos tests
        return ("", "")

    def parse_ai_response(self, response_text: str) -> Dict[str, Any]:  # pragma: no cover
        return {}


def _build_config() -> BotConfig:
    return BotConfig(
        bot_id=999,  # ID aislado para test
        bot_name="test_bot",
        bot_type="numerico",
        mode=BotMode.DEMO,
        symbols=["EURUSD"],
        ai_model="gemini-2.5-pro",
        enable_dual_orders=False,
        log_level="ERROR",  # Reducir ruido en tests
    )


def test_close_without_ticket_uses_magic_cache():
    """Debe cerrar la posición usando caché de magic cuando no hay ticket en decisión."""
    symbol = "EURUSD"
    position = DummyPosition(symbol=symbol, ticket=123456, magic=111001)
    bot = DummyBot(_build_config())
    # Inyectar dependencias mock
    bot.mt5_connection = DummyMT5Connection([position])
    bot.order_manager = DummyOrderManager()
    # Registrar magic en caché como lo haría la apertura
    bot._active_magic_by_symbol[symbol] = position.magic

    decision = {"accion": "CERRAR"}  # Sin 'ticket'
    bot._execute_close_position(symbol, decision)

    assert bot.order_manager.closed_tickets == [position.ticket], (
        "Debe haberse cerrado el ticket usando caché determinista de magic"
    )


def test_close_without_ticket_abort_multiple_positions_without_cache():
    """Si hay múltiples posiciones y no existe caché de magic, debe abortar cierre."""
    symbol = "EURUSD"
    p1 = DummyPosition(symbol=symbol, ticket=111, magic=111001)
    p2 = DummyPosition(symbol=symbol, ticket=222, magic=111002)
    bot = DummyBot(_build_config())
    bot.mt5_connection = DummyMT5Connection([p1, p2])
    bot.order_manager = DummyOrderManager()
    # No se registra caché: escenario ambiguo

    decision = {"accion": "CERRAR"}
    bot._execute_close_position(symbol, decision)

    assert bot.order_manager.closed_tickets == [], (
        "No debe cerrar ninguna posición si existen múltiples y falta caché/ticket"
    )


# Ejecutar pruebas manualmente (fallback) si se llama directamente
if __name__ == "__main__":  # pragma: no cover
    test_close_without_ticket_uses_magic_cache()
    test_close_without_ticket_abort_multiple_positions_without_cache()
    print("Tests ejecutados manualmente OK")