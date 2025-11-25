import time
import logging
from typing import Set, Dict, Any

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy as IntradayBot3ProStrategy
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.strategy import IntradayBot1Strategy as IntradayBot25Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.enhanced_magic_number_generator import EnhancedMagicNumberGenerator
from src.core.agent_variant_codes import resolve_codes

"""Prueba dual:
1. Inicializa dos estrategias intraday (Gemini 3 Pro y Gemini 2.5 Pro) sobre BTCUSD.
2. Abre una posición LONG con cada estrategia (simulada, sin llamada a IA).
3. Verifica que cada variante tiene su propio magic (family/strategy/agent). Se esperan dos magics distintos.
4. Cierra cada posición con su estrategia, confirmando que no queda residual.

Importante: Si la cuenta no permite múltiples posiciones LONG simultáneas en el mismo símbolo, la segunda apertura puede consolidar o netear la primera y la prueba fallará.
"""

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')
logger = logging.getLogger("dual_test")

SYMBOL = "BTCUSD"


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


def collect_variant_magics(strategy, symbol: str) -> Set[int]:
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


def open_position(strategy, symbol: str, razon: str) -> Dict[str, Any]:
    baseline = collect_variant_magics(strategy, symbol)
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
    time.sleep(3)
    current = collect_variant_magics(strategy, symbol)
    new_magics = current - baseline
    if not new_magics:
        raise RuntimeError("No se detectó nuevo magic para variante")
    new_magic = sorted(new_magics)[-1]
    positions = strategy.position_manager.get_positions_by_symbol(symbol)
    target = None
    for pos in positions:
        if int(getattr(pos, "magic", 0)) == new_magic:
            target = pos
            break
    if target is None:
        raise RuntimeError("No se encontró posición por magic nuevo")
    return {"ticket": target.ticket, "magic": target.magic, "price_open": target.price_open}


def close_position(strategy, symbol: str, ticket: int):
    strategy._execute_close_position(symbol, {"ticket": ticket})
    time.sleep(3)


def main():
    logger.info("Inicializando estrategias...")
    cfg3 = build_config(101, "gemini-3-pro-preview", "dual_intraday_g3")
    cfg25 = build_config(102, "gemini-2.5-pro", "dual_intraday_g25")
    strat3 = IntradayBot3ProStrategy(cfg3)
    strat25 = IntradayBot25Strategy(cfg25)
    if not strat3.initialize():
        raise SystemExit("Falló initialize() gemini 3 pro")
    if not strat25.initialize():
        raise SystemExit("Falló initialize() gemini 2.5 pro")

    logger.info("Abriendo posición Gemini 3 Pro...")
    pos3 = open_position(strat3, SYMBOL, "Apertura test dual Gemini 3 Pro")
    logger.info(f"-> G3 Ticket={pos3['ticket']} Magic={pos3['magic']} Precio={pos3['price_open']:.2f}")

    logger.info("Abriendo posición Gemini 2.5 Pro...")
    pos25 = open_position(strat25, SYMBOL, "Apertura test dual Gemini 2.5 Pro")
    logger.info(f"-> G2.5 Ticket={pos25['ticket']} Magic={pos25['magic']} Precio={pos25['price_open']:.2f}")

    magics3 = collect_variant_magics(strat3, SYMBOL)
    magics25 = collect_variant_magics(strat25, SYMBOL)
    logger.info(f"Magics G3: {sorted(magics3)} | Magics G2.5: {sorted(magics25)}")
    interseccion = set(magics3).intersection(set(magics25))
    if interseccion:
        logger.warning(f"Intersección de magics detectada (no esperado): {interseccion}")
    else:
        logger.info("Magics diferenciados correctamente entre variantes.")

    logger.info("Cerrando posición Gemini 3 Pro...")
    close_position(strat3, SYMBOL, pos3["ticket"])
    logger.info("Cerrando posición Gemini 2.5 Pro...")
    close_position(strat25, SYMBOL, pos25["ticket"])

    rem3 = collect_variant_magics(strat3, SYMBOL)
    rem25 = collect_variant_magics(strat25, SYMBOL)
    logger.info(f"Remanente G3: {sorted(rem3)} | Remanente G2.5: {sorted(rem25)}")
    if rem3 or rem25:
        logger.warning("Persisten magics tras cierre; revisar lógica.")
    else:
        logger.info("Cierres correctos, sin posiciones residuales de ambas variantes.")

    logger.info("Fin prueba dual BTCUSD.")


if __name__ == "__main__":
    main()
