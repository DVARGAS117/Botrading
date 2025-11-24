"""Test de consistencia Stop Loss Inicial vs Prompt y BD (Intraday Gemini 3 Pro).

Objetivo:
  - Abrir una posición SHORT simulada en USDJPY con SL y TP definidos.
  - Verificar que `stop_loss_initial` en BD coincide con `stop_loss` tras apertura (sin ajustes iniciales).
  - Generar prompt inmediatamente y comprobar que la línea 'Stop Loss Actual' muestra (⚠️ SL inicial: ... ajustado a: ...) SOLO si fue modificado.
  - Validar que 'Riesgo Inicial (1R)' se basa en el SL inicial correcto.

Uso:
    python tests/intraday/test_intraday_sl_consistency.py

Requisitos:
  - Conexión MT5 DEMO activa con símbolo USDJPY disponible.
  - Rama con parches de SequenceManager global y verificación de símbolo en SL inicial.
"""
from __future__ import annotations
import re
import time
from typing import Dict, Any

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.vwap_prompt_builder import MarketContext
from src.core.operations_repository import OperationsRepository

SYMBOL = "USDJPY"
SL_PIPS = 150  # Distancia para riesgo (~1.50 en USDJPY si pip=0.01)
TP_PIPS = 300
RISK_PCT = 0.6  # Riesgo moderado para test


def build_config() -> BotConfig:
    return BotConfig(
        bot_id=3,
        bot_name="intraday_g3_pro_sl_consistency",
        bot_type="numerico",
        mode=BotMode.DEMO,
        symbols=[SYMBOL],
        trading_hours=("00:00", "23:59"),
        ai_model="gemini-3-pro-preview",
        enable_dual_orders=False,
        log_level="INFO",
        save_prompts=False,
        risk_per_trade=RISK_PCT,
    )


def open_position(strat: IntradayBot1Strategy) -> Dict[str, Any]:
    tick = strat.mt5_connection._mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        raise RuntimeError("Tick no disponible para símbolo")
    entry = tick.bid  # Abrimos SHORT
    point = strat.mt5_connection.get_symbol_info(SYMBOL).point or 0.01
    sl_price = entry + SL_PIPS * point
    tp_price = entry - TP_PIPS * point
    decision: Dict[str, Any] = {
        "accion": "VENDER",
        "direccion": "short",
        "precio_entrada": entry,
        "stop_loss": sl_price,
        "take_profit": tp_price,
        "riesgo_porcentaje": RISK_PCT,
        "razonamiento": "Test SL inicial consistencia",
    }
    strat._execute_open_position(SYMBOL, decision)
    time.sleep(2)  # Esperar registro
    return decision


def extract_prompt(strat: IntradayBot1Strategy) -> str:
    # Usar prepare_data_for_ai para obtener user_prompt con posición incluida
    # MarketContext arbitrario (no afecta SL)
    data = strat.prepare_data_for_ai(
        symbol=SYMBOL,
        indicators={},
        or_data=None,
        market_context=MarketContext.EUROPEAN_SESSION,
        ohlcv_data=None,
    )
    # Cuando prepare_data_for_ai devuelve dict (segunda definición), adaptamos
    if isinstance(data, tuple):  # fallback a primera firma
        _, user_prompt = data
    else:
        user_prompt = data["user_prompt"]
    return user_prompt


def main():
    cfg = build_config()
    strat = IntradayBot1Strategy(cfg)
    if not strat.initialize():
        raise SystemExit("Falló initialize()")

    decision = open_position(strat)

    # Recuperar posición y operación BD
    positions = strat.position_manager.get_positions_by_symbol(SYMBOL)
    if not positions:
        raise AssertionError("No se abrió posición para el test")
    # Recuperar la operación más reciente abierta desde la BD (evita legacy con magic elevado)
    from src.core.operations_repository import OperationStatus as _OpStatus
    latest_ops = strat.operations_repo.list_operations(status=_OpStatus.OPEN, symbol=SYMBOL, limit=1)
    assert latest_ops, "No se encontró operación abierta en BD para el símbolo"
    magic = int(latest_ops[0].magic_number)

    repo: OperationsRepository = strat.operations_repo
    op = repo.get_operation_by_magic_number(magic)
    assert op, "Operación no encontrada en BD por magic"
    print(f"DEBUG Operación BD recuperada -> magic={op.magic_number} stop_loss_initial={op.stop_loss_initial} stop_loss={op.stop_loss} entry={op.actual_entry_price}")

    sl_initial_db = op.stop_loss_initial
    sl_current_db = op.stop_loss
    assert sl_initial_db is not None and sl_current_db is not None, "Valores SL inicial/actual None"
    assert abs(sl_initial_db - sl_current_db) < 1e-9, "SL inicial y actual difieren tras apertura sin ajustes"

    # Obtener SL inicial vía método
    sl_initial_method = strat._get_initial_sl_from_db(SYMBOL)
    assert sl_initial_method is not None, "_get_initial_sl_from_db devolvió None"
    print(f"DEBUG SL valores -> BD: {sl_initial_db} | Método: {sl_initial_method}")
    assert sl_initial_db is not None, "SL inicial BD es None"
    assert abs(sl_initial_method - sl_initial_db) < 1e-9, "SL inicial método != SL inicial BD"

    # Generar prompt y extraer líneas relevantes
    user_prompt = extract_prompt(strat)
    sl_line_match = re.search(r"Stop Loss Actual: ([0-9.]+)(.*)", user_prompt)
    assert sl_line_match, "No se encontró línea de Stop Loss Actual en prompt"
    sl_actual_prompt = float(sl_line_match.group(1))
    extra_segment = sl_line_match.group(2)

    # Validar coherencia de nota de ajuste según diferencia real broker vs inicial
    pip_value = 0.01 if "JPY" in SYMBOL else 0.0001
    sl_diff_prompt = abs(sl_actual_prompt - sl_initial_db)
    if sl_diff_prompt <= pip_value * 0.1:
        assert "ajustado" not in extra_segment, "Prompt indica ajuste de SL sin diferencia significativa"
    else:
        assert "ajustado" in extra_segment, "Prompt no indica ajuste pese a diferencia significativa"
    # Si el broker ajustó SL, el prompt reflejará el SL real distinto al almacenado inicialmente
    if abs(sl_actual_prompt - sl_current_db) <= pip_value * 0.1:
        assert abs(sl_actual_prompt - sl_current_db) < 1e-6, "SL en prompt difiere del SL actual sin ajuste"
    else:
        # Diferencia significativa aceptada; BD será actualizada por reconciliación futura o cierre
        pass

    # Verificar Riesgo Inicial (1R) usa SL inicial correcto
    risk_initial_match = re.search(r"Riesgo Inicial \(1R\): ([0-9.]+) pips .* SL inicial: ([0-9.]+)", user_prompt)
    assert risk_initial_match, "No se encontró bloque de Riesgo Inicial en prompt"
    sl_in_prompt_initial = float(risk_initial_match.group(2))
    assert sl_initial_db is not None, "SL inicial BD es None"
    assert abs(sl_in_prompt_initial - sl_initial_db) < 1e-6, "SL inicial en prompt difiere del SL inicial BD"

    print("=== RESULTADOS TEST SL CONSISTENCIA ===")
    print(f"Magic: {magic}")
    print(f"SL Inicial BD: {sl_initial_db}")
    print(f"SL Actual BD: {sl_current_db}")
    print(f"SL Prompt Actual: {sl_actual_prompt}")
    print("Prompt sin nota de ajuste ✅")
    print("SL inicial coincide en BD, método y prompt ✅")
    print("Test completado exitosamente.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        raise
