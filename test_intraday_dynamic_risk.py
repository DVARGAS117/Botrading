"""Test rápido de validación de riesgo dinámico Intraday Gemini 3 Pro.

Objetivo:
  - Forzar una decisión con `riesgo_porcentaje` explícito (ej. 1.2%)
  - Calcular lote esperado según fórmula del PositionSizer
  - Comparar lote ejecutado vs esperado (tolerancia de step)
  - Mostrar en consola: balance, riesgo (% y $), distancia SL (pips), lote esperado, lote real, magic.

Requisitos:
  - Cuenta MT5 conectada (DEMO) y símbolo EURUSD habilitado.
  - Branch actual con modificaciones de riesgo dinámico.

Ejecutar:
    python test_intraday_dynamic_risk.py
"""

from __future__ import annotations
import time
from typing import Dict, Any, Optional

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.position_sizer import PositionSizer, RiskParameters

SYMBOL = "EURUSD"
RISK_PCT = 1.2  # 1.2% riesgo deseado
SL_PIPS = 150   # Distancia SL ampliada para evitar stop level mínimo (150 * 1e-5 = 0.00150)
TP_PIPS = 300   # Objetivo proporcional


def build_config() -> BotConfig:
    return BotConfig(
        bot_id=101,
        bot_name="intraday_g3_pro_test_risk",
        bot_type="numerico",
        mode=BotMode.DEMO,
        symbols=[SYMBOL],
        trading_hours=("00:00", "23:59"),
        ai_model="gemini-3-pro-preview",
        enable_dual_orders=False,
        log_level="INFO",
        save_prompts=False,
        risk_per_trade=0.8  # Config por defecto, debería ser override al usar riesgo_porcentaje
    )


def main():
    cfg = build_config()
    strat = IntradayBot1Strategy(cfg)
    if not strat.initialize():
        raise SystemExit("Falló initialize()")

    # Obtener tick y balance
    tick = strat.mt5_connection._mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        raise RuntimeError("Tick no disponible para símbolo")
    entry = tick.ask
    account = strat.mt5_connection.get_account_info()
    balance = float(getattr(account, 'balance', 0.0))

    # Obtener info símbolo para diagnosticar stop level
    symbol_info = strat.mt5_connection.get_symbol_info(SYMBOL)
    trade_stops_level = getattr(symbol_info, 'trade_stops_level', None)
    point = getattr(symbol_info, 'point', 1e-5)
    min_stop_distance = trade_stops_level * point if trade_stops_level is not None else None

    # Calcular precios SL/TP basados en entry (BUY scenario)
    sl_price = entry - SL_PIPS * point
    tp_price = entry + TP_PIPS * point

    # Decisión simulada con riesgo explícito
    decision: Dict[str, Any] = {
        "accion": "COMPRAR",
        "direccion": "long",
        "precio_entrada": entry,
        "stop_loss": sl_price,
        "take_profit": tp_price,
        "riesgo_porcentaje": RISK_PCT,
        "razonamiento": "Test sizing dinámico riesgo 1.2%",
    }

    # Calcular lote esperado usando PositionSizer directamente
    symbol_spec = strat.symbol_spec_extractor.get_symbol_specification(SYMBOL)
    ps = PositionSizer()
    rp = RiskParameters(
        account_balance=balance,
        risk_percentage=RISK_PCT,
        entry_price=entry,
        stop_loss=sl_price,
        symbol_spec=symbol_spec,
    )
    expected = ps.calculate_lot_size(rp)
    expected_lot = expected.lot_size
    risk_amount_expected = expected.risk_amount
    pip_distance = expected.pip_distance  # debería ser ~50

    print("=== PRE-CÁLCULO ESPERADO ===")
    print(f"Balance: {balance:.2f} USD")
    print(f"Riesgo % solicitado: {RISK_PCT:.2f}% -> Riesgo $ teórico: {risk_amount_expected:.2f}")
    print(f"Distancia SL (pips internos): {pip_distance:.1f}")
    print(f"Stop Level Broker (trade_stops_level): {trade_stops_level} => Distancia mínima puntos: {min_stop_distance}")
    print(f"Lote esperado (ajustado): {expected_lot:.2f}")

    # Ejecutar apertura
    print("\n[Apertura posición dinámica]...")
    strat._execute_open_position(SYMBOL, decision)
    # Capturar posible error MT5
    last_error = None
    try:
        if hasattr(strat.mt5_connection, '_mt5') and hasattr(strat.mt5_connection._mt5, 'last_error'):
            last_error = strat.mt5_connection._mt5.last_error()
    except Exception:
        pass
    time.sleep(2)

    # Recuperar posición abierta
    positions = strat.position_manager.get_positions_by_symbol(SYMBOL)
    target = None
    # Buscar cualquier posición reciente con volumen cerca de esperado
    for pos in positions:
        if abs(pos.volume - expected_lot) < symbol_spec.volume_step * 2:  # tolerancia
            target = pos
            break
    if target is None and positions:
        target = positions[-1]

    if target is None:
        print("\n❌ No se abrió posición. Diagnóstico:")
        print(f"trade_stops_level={trade_stops_level} min_stop_distance={min_stop_distance}")
        print(f"SL intentado distancia puntos={abs(entry - sl_price)} TP distancia puntos={abs(tp_price - entry)}")
        print(f"Último error MT5: {last_error}")
        return

    volume_real = target.volume
    magic = getattr(target, 'magic', 0)

    # Buscar operación en BD para confirmar riesgo persistido
    op = strat.operations_repo.get_operation_by_magic_number(int(magic)) if magic else None

    print("\n=== RESULTADOS EJECUCIÓN ===")
    print(f"Ticket: {target.ticket} Magic: {magic}")
    print(f"Precio Entrada Real: {target.price_open}")
    print(f"SL Real: {target.sl} TP Real: {target.tp}")
    print(f"Lote Real Ejecutado: {volume_real:.2f}")
    print(f"Lote Esperado: {expected_lot:.2f}")
    print(f"Diferencia Lote: {abs(volume_real - expected_lot):.4f}")
    if op:
        print(f"Riesgo Persistido %: {op.risk_percentage:.2f}% Riesgo Persistido $: {op.risk_amount:.2f}")
    else:
        print("No se encontró operación en BD por magic (verificar patch).")

    # Validaciones simples
    assert volume_real > 0.01, "Lote real no supera mínimo, sizing dinámico no aplicado?"
    assert abs(volume_real - expected_lot) < 0.05, "Lote ejecutado difiere demasiado del esperado"
    if op:
        assert abs(op.risk_percentage - RISK_PCT) < 1e-6, "Riesgo % persistido no coincide"
        assert abs(op.risk_amount - risk_amount_expected) < 0.5, "Monto de riesgo persistido alejado del esperado"

    print("\n✅ Test riesgo dinámico completado con éxito.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        raise
