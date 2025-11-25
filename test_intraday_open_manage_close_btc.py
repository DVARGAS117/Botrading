"""Flujo real de apertura, reevaluación y cierre para BTCUSD (Gemini 3 Pro).

Pasos:
1. Inicializa estrategia Intraday Gemini 3 Pro.
2. Abre posición LONG simulada en BTCUSD con SL/TP relativos.
3. Genera prompt de gestión (reevaluación) y muestra bloque POSICIÓN ACTIVA.
4. Cierra posición y verifica ausencia del magic recién creado.

Uso:
    python test_intraday_open_manage_close_btc.py

Requisitos:
- MT5 conectado y símbolo BTCUSD disponible.
- Credenciales en config/credentials.json.

Nota: No llama a Gemini; la decisión de apertura es simulada.
"""

from __future__ import annotations

import time
from typing import Dict, Any, Set

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.vwap_prompt_builder import MarketContext
from src.core.enhanced_magic_number_generator import EnhancedMagicNumberGenerator
from src.core.agent_variant_codes import resolve_codes

SYMBOL = "BTCUSD"


def build_config() -> BotConfig:
    return BotConfig(
        bot_id=101,  # ID usado para gemini 3 pro tests
        bot_name="intraday_g3_pro_test_btc",
        bot_type="numerico",
        mode=BotMode.DEMO,
        symbols=[SYMBOL],
        trading_hours=("00:00", "23:59"),
        ai_model="gemini-3-pro-preview",
        enable_dual_orders=False,
        log_level="INFO",
        save_prompts=False,
    )


def collect_variant_magics(strategy: IntradayBot1Strategy, symbol: str) -> Set[int]:
    gen = EnhancedMagicNumberGenerator()
    family_id, strategy_id, agent_variant_id = resolve_codes(
        ai_model=strategy.config.ai_model, strategy_name="INTRADAY", data_mode="raw"
    )
    magics: Set[int] = set()
    positions = strategy.position_manager.get_positions_by_symbol(symbol)
    for pos in positions:
        try:
            comp = gen.decode(int(pos.magic))
            if (
                comp.family_id == family_id
                and comp.strategy_id == strategy_id
                and comp.agent_id == agent_variant_id
            ):
                magics.add(int(pos.magic))
        except Exception:
            continue
    return magics


def open_position(strategy: IntradayBot1Strategy, symbol: str) -> Dict[str, Any]:
    baseline = collect_variant_magics(strategy, symbol)
    tick = strategy.mt5_connection._mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"Tick no disponible para {symbol}")
    entry = tick.ask
    # Para cripto usar rangos relativos más amplios si el broker maneja puntos distintos
    sl = entry - (entry * 0.002)  # 0.2% debajo
    tp = entry + (entry * 0.004)  # 0.4% arriba
    decision = {
        "accion": "COMPRAR",
        "direccion": "long",
        "stop_loss": sl,
        "take_profit": tp,
        "razonamiento": "Apertura test BTCUSD Gemini 3 Pro",
    }
    strategy._execute_open_position(symbol, decision)
    time.sleep(3)
    current = collect_variant_magics(strategy, symbol)
    new_magics = current - baseline
    if not new_magics:
        raise RuntimeError("No se detectó nuevo magic variante BTCUSD")
    new_magic = sorted(new_magics)[-1]
    positions = strategy.position_manager.get_positions_by_symbol(symbol)
    target = None
    for pos in positions:
        if int(getattr(pos, "magic", 0)) == new_magic:
            target = pos
            break
    if target is None:
        raise RuntimeError("No se encontró posición por magic nuevo BTCUSD")
    return {"ticket": target.ticket, "magic": target.magic, "price_open": target.price_open}


def generate_prompt(strategy: IntradayBot1Strategy, symbol: str) -> str:
    market_context = (
        strategy.get_market_context()
        if hasattr(strategy, "get_market_context")
        else MarketContext.NEUTRAL
    )
    data = strategy._prepare_intraday_data_for_ai(
        symbol=symbol,
        indicators={},
        or_data=None,
        market_context=market_context,
        ohlcv_data=None,
    )
    return data["user_prompt"]


def extract_block(user_prompt: str) -> str:
    marker = "POSICIÓN ACTIVA:"; none_marker = "POSICIÓN ACTUAL: NONE"
    if marker in user_prompt:
        start = user_prompt.index(marker)
        end = user_prompt.find("\n\n", start)
        if end == -1:
            end = len(user_prompt)
        return user_prompt[start:end]
    if none_marker in user_prompt:
        start = user_prompt.index(none_marker)
        end = user_prompt.find("\n\n", start)
        if end == -1:
            end = len(user_prompt)
        return user_prompt[start:end]
    return "[Bloque no encontrado]"


def close_position(strategy: IntradayBot1Strategy, symbol: str, ticket: int) -> None:
    strategy._execute_close_position(symbol, {"ticket": ticket})
    time.sleep(3)


def main():
    print("[1] Inicializando estrategia Gemini 3 Pro BTCUSD...")
    cfg = build_config()
    strat = IntradayBot1Strategy(cfg)
    if not strat.initialize():
        raise SystemExit("Falló initialize()")
    print("[2] Apertura posición prueba BTCUSD...")
    pos_info = open_position(strat, SYMBOL)
    print(
        f"    -> Ticket={pos_info['ticket']} Magic={pos_info['magic']} Precio={pos_info['price_open']:.2f}"
    )
    print("[3] Prompt gestión...")
    user_prompt = generate_prompt(strat, SYMBOL)
    block = extract_block(user_prompt)
    print("\n=== Bloque POSICIÓN ACTIVA (BTCUSD Gemini 3 Pro) ===")
    print(block)
    print("===============================================\n")
    print("[4] Cierre posición...")
    close_position(strat, SYMBOL, pos_info["ticket"])
    remaining = collect_variant_magics(strat, SYMBOL)
    print(
        f"[5] Magic cerrado sigue presente? {int(pos_info['magic']) in remaining}. Restantes: {sorted(remaining)}"
    )
    print("[6] Flujo BTCUSD 3 Pro completado.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        raise
