"""Flujo real de validación Magic v2 en estrategia Intraday Gemini 3 Pro.

Pasos:
1. Inicializa la estrategia (`IntradayBot1Strategy`).
2. Abre una posición simulando decisión IA (LONG o SHORT) con SL/TP.
3. Genera prompt de reevaluación y extrae bloque de `POSICIÓN ACTIVA`.
4. Cierra la posición y verifica que ya no esté activa.

Requisitos:
- MT5 abierto y conectado en la cuenta configurada en `config/credentials.json`.
- Símbolo disponible (por defecto EURUSD).

Uso:
    python test_intraday_open_manage_close.py

Nota: No invoca Gemini (la apertura usa decisión simulada). El segundo prompt refleja datos de la posición real abierta (precio, SL, TP, PnL, duración...).
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Any, List, Set

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.vwap_prompt_builder import MarketContext
from src.core.enhanced_magic_number_generator import EnhancedMagicNumberGenerator


SYMBOL = "EURUSD"


def _build_bot_config() -> BotConfig:
    """Construye configuración mínima para prueba (sin guardar prompts)."""
    return BotConfig(
        bot_id=101,  # ID mapeado para primer dígito legacy (permite fallback)
        bot_name="intraday_g3_pro_test",
        bot_type="numerico",
        mode=BotMode.DEMO,
        symbols=[SYMBOL],
        trading_hours=("00:00", "23:59"),
        ai_model="gemini-3-pro-preview",
        enable_dual_orders=False,
        log_level="INFO",
        save_prompts=False,  # Necesitamos que parsee sin modo dummy
    )


def _collect_variant_magics(strategy: IntradayBot1Strategy, symbol: str) -> Set[int]:
    """Recoge magic numbers v2 del agente variante actual en el símbolo."""
    gen = EnhancedMagicNumberGenerator()
    family_id, strategy_id, agent_variant_id = (resolve_codes := __import__('src.core.agent_variant_codes', fromlist=['resolve_codes']).resolve_codes)(
        ai_model=strategy.config.ai_model, strategy_name="INTRADAY", data_mode="raw"
    )
    magics: Set[int] = set()
    positions = strategy.position_manager.get_positions_by_symbol(symbol)
    for pos in positions:
        try:
            comp = gen.decode(int(pos.magic))
            if comp.family_id == family_id and comp.strategy_id == strategy_id and comp.agent_id == agent_variant_id:
                magics.add(int(pos.magic))
        except Exception:
            continue
    return magics


def open_position(strategy: IntradayBot1Strategy, symbol: str) -> Dict[str, Any]:
    """Abre posición y retorna datos de la NUEVA posición (mismo variante)."""
    baseline_magics = _collect_variant_magics(strategy, symbol)

    tick = strategy.mt5_connection._mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"No se pudo obtener tick para {symbol}")
    entry_price = tick.ask
    sl = entry_price - 0.0020
    tp = entry_price + 0.0040

    decision = {
        "accion": "COMPRAR",
        "direccion": "long",
        "stop_loss": sl,
        "take_profit": tp,
        "razonamiento": "Test apertura manual.",
    }

    strategy._execute_open_position(symbol, decision)
    time.sleep(2)

    # Detectar nuevo magic
    current_magics = _collect_variant_magics(strategy, symbol)
    new_magics = current_magics - baseline_magics
    if not new_magics:
        raise RuntimeError("No se detectó nuevo magic v2 para la posición abierta")
    new_magic = sorted(new_magics)[-1]

    # Buscar posición correspondiente
    positions = strategy.position_manager.get_positions_by_symbol(symbol)
    target_pos = None
    for pos in positions:
        if int(getattr(pos, 'magic', 0)) == new_magic:
            target_pos = pos
            break
    if target_pos is None:
        raise RuntimeError("No se encontró la posición asociada al nuevo magic")

    return {
        "ticket": target_pos.ticket,
        "magic": target_pos.magic,
        "price_open": target_pos.price_open,
        "type": "LONG" if target_pos.type == 0 else "SHORT",
        "baseline_magics": baseline_magics,
    }


def generate_management_prompt(strategy: IntradayBot1Strategy, symbol: str) -> str:
    """Genera prompt con posición activa usando método interno de estrategia."""
    # Indicadores y or_data no se usan en intraday actual
    market_context = strategy.get_market_context() if hasattr(strategy, "get_market_context") else MarketContext.NEUTRAL
    intraday_dict = strategy._prepare_intraday_data_for_ai(
        symbol=symbol,
        indicators={},
        or_data=None,
        market_context=market_context,
        ohlcv_data=None,
    )
    return intraday_dict["user_prompt"]


def extract_position_block(user_prompt: str) -> str:
    """Extrae bloque de posición desde el prompt para validación visual."""
    marker = "POSICIÓN ACTIVA:"  # cuando hay posición
    if marker in user_prompt:
        start = user_prompt.index(marker)
        # Buscar doble salto de línea posterior para delimitar (heurística simple)
        end = user_prompt.find("\n\n", start)
        if end == -1:
            end = len(user_prompt)
        return user_prompt[start:end]
    # Fallback: sin posición
    marker_none = "POSICIÓN ACTUAL: NONE"
    if marker_none in user_prompt:
        start = user_prompt.index(marker_none)
        end = user_prompt.find("\n\n", start)
        if end == -1:
            end = len(user_prompt)
        return user_prompt[start:end]
    return "[Bloque posición no localizado]"


def close_position(strategy: IntradayBot1Strategy, symbol: str, ticket: int) -> None:
    decision_close = {"ticket": ticket}
    strategy._execute_close_position(symbol, decision_close)
    time.sleep(2)


def main():
    print("[1] Inicializando estrategia...")
    config = _build_bot_config()
    strategy = IntradayBot1Strategy(config)
    if not strategy.initialize():
        raise SystemExit("Falló initialize()")

    print(f"[2] Abriendo posición de prueba en {SYMBOL}...")
    pos_info = open_position(strategy, SYMBOL)
    print(f"    -> NUEVA Ticket={pos_info['ticket']} Magic={pos_info['magic']} Precio={pos_info['price_open']:.5f}")

    has_pos = strategy._has_active_position(SYMBOL)
    print(f"[3] Verificación interna _has_active_position: {has_pos}")
    if not has_pos:
        raise RuntimeError("La estrategia no detecta la posición como activa")

    print("[4] Generando prompt de gestión (reevaluación)...")
    user_prompt = generate_management_prompt(strategy, SYMBOL)
    block = extract_position_block(user_prompt)
    print("\n=== Bloque POSICIÓN ACTIVA extraído ===")
    print(block)
    print("======================================\n")

    print("[5] Cerrando posición...")
    close_position(strategy, SYMBOL, pos_info["ticket"])
    # Verificar que el magic nuevo ya no esté
    remaining_magics = _collect_variant_magics(strategy, SYMBOL)
    closed_magic_still_present = int(pos_info['magic']) in remaining_magics
    print(f"[6] Magic cerrado presente aún? {closed_magic_still_present}. Magics restantes variante: {sorted(remaining_magics)}")

    print("[7] Flujo completado.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        raise
