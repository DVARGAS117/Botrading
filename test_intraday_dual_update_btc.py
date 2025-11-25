import time
import logging
from typing import Dict, Any

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy as IntradayBot3ProStrategy
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.strategy import IntradayBot1Strategy as IntradayBot25Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode

SYMBOL = "BTCUSD"

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')
logger = logging.getLogger("dual_update_test")

def build_config(bot_id: int, model: str, name: str) -> BotConfig:
    return BotConfig(
        bot_id=bot_id,
        bot_name=name,
        bot_type="numerico",
        mode=BotMode.DEMO,
        symbols=[SYMBOL],
        trading_hours=("00:00", "23:59"),
        ai_model=model,
        enable_dual_orders=False,
        log_level="INFO",
        save_prompts=False,
    )

def open_position(strategy, symbol: str, razon: str) -> Dict[str, Any]:
    tick = strategy.mt5_connection._mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"Tick no disponible para {symbol}")
    entry = tick.ask
    sl = entry - (entry * 0.002)
    tp = entry + (entry * 0.004)
    decision = {
        "accion": "COMPRAR",
        "direccion": "long",
        "stop_loss": sl,
        "take_profit": tp,
        "razonamiento": razon,
    }
    strategy._execute_open_position(symbol, decision)
    time.sleep(2)
    positions = strategy.position_manager.get_positions_by_symbol(symbol)
    if not positions:
        raise RuntimeError("No se encontró posición recién abierta")
    pos = positions[0]
    return {"ticket": pos.ticket, "sl": pos.sl, "tp": pos.tp, "price_open": pos.price_open}

def compute_update(pos_info: Dict[str, Any]) -> Dict[str, Any]:
    price_open = pos_info['price_open']
    old_sl = pos_info['sl']
    old_tp = pos_info['tp']
    # Acercar SL un 30% de la distancia al precio de entrada (trailing)
    sl_distance = price_open - old_sl
    new_sl = old_sl + sl_distance * 0.3
    # Extender TP un 30% de la distancia actual al precio de entrada
    tp_distance = old_tp - price_open
    new_tp = old_tp + tp_distance * 0.3
    return {"stop_loss": new_sl, "take_profit": new_tp}

def verify_update(strategy, symbol: str, ticket: int, expected_sl: float, expected_tp: float):
    positions = strategy.position_manager.get_positions_by_symbol(symbol)
    for p in positions:
        if p.ticket == ticket:
            logger.info(f"Verificación posición {ticket}: SL={p.sl} TP={p.tp}")
            # Mostrar diferencias
            logger.info(f"Dif SL={p.sl - expected_sl:.5f} Dif TP={p.tp - expected_tp:.5f}")
            return p.sl, p.tp
    raise RuntimeError(f"No se encontró posición ticket {ticket} para verificación")

def main():
    logger.info("Inicializando estrategias para prueba de actualización...")
    cfg3 = build_config(101, "gemini-3-pro-preview", "update_intraday_g3")
    cfg25 = build_config(102, "gemini-2.5-pro", "update_intraday_g25")
    strat3 = IntradayBot3ProStrategy(cfg3)
    strat25 = IntradayBot25Strategy(cfg25)
    if not strat3.initialize():
        raise SystemExit("Falló initialize() gemini 3 pro")
    if not strat25.initialize():
        raise SystemExit("Falló initialize() gemini 2.5 pro")

    logger.info("Apertura posición Gemini 3 Pro para actualización...")
    pos3 = open_position(strat3, SYMBOL, "Apertura update test G3")
    logger.info(f"G3 abierta Ticket={pos3['ticket']} SL={pos3['sl']} TP={pos3['tp']}")

    logger.info("Apertura posición Gemini 2.5 Pro para actualización...")
    pos25 = open_position(strat25, SYMBOL, "Apertura update test G2.5")
    logger.info(f"G2.5 abierta Ticket={pos25['ticket']} SL={pos25['sl']} TP={pos25['tp']}")

    # Preparar decisiones de actualización
    upd3 = compute_update(pos3)
    upd25 = compute_update(pos25)

    logger.info(f"Actualizando G3 -> Nuevo SL={upd3['stop_loss']:.2f} Nuevo TP={upd3['take_profit']:.2f}")
    strat3._execute_update_position(SYMBOL, upd3)
    time.sleep(2)
    logger.info(f"Actualizando G2.5 -> Nuevo SL={upd25['stop_loss']:.2f} Nuevo TP={upd25['take_profit']:.2f}")
    strat25._execute_update_position(SYMBOL, upd25)
    time.sleep(2)

    # Verificar cambios en MT5
    new_sl3, new_tp3 = verify_update(strat3, SYMBOL, pos3['ticket'], upd3['stop_loss'], upd3['take_profit'])
    new_sl25, new_tp25 = verify_update(strat25, SYMBOL, pos25['ticket'], upd25['stop_loss'], upd25['take_profit'])

    # Validaciones simples de que se movieron en dirección esperada
    assert new_sl3 > pos3['sl'], "SL G3 no se acercó al precio"
    assert new_tp3 > pos3['tp'], "TP G3 no se extendió"
    assert new_sl25 > pos25['sl'], "SL G2.5 no se acercó al precio"
    assert new_tp25 > pos25['tp'], "TP G2.5 no se extendió"

    logger.info("Actualizaciones aplicadas correctamente en ambas variantes.")

    # Cierre posiciones para limpiar
    logger.info("Cerrando posición G3...")
    strat3._execute_close_position(SYMBOL, {"ticket": pos3['ticket']})
    time.sleep(1)
    logger.info("Cerrando posición G2.5...")
    strat25._execute_close_position(SYMBOL, {"ticket": pos25['ticket']})
    time.sleep(2)

    logger.info("Fin prueba actualización dual BTCUSD.")

if __name__ == "__main__":
    main()
