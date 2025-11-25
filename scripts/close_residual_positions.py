import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / 'src'
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.core.config_loader import ConfigLoader
from src.core.mt5_connector import create_connector_from_credentials
from src.core.position_manager import PositionManager
from src.core.order_manager import OrderManager

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')
logger = logging.getLogger("close_residual")

# Magic prefixes intraday usados (familia 1 estrategia 10 tipo 0 agente variantes 4,5,6,7,9 etc.)
INTRADAY_MAGIC_PREFIXES = {110104, 110105, 110106, 110107, 110108, 110109, 110426, 110427, 110430, 110431, 110432}


def load_connector():
    creds_path = Path("config/credentials.json")
    loader = ConfigLoader()
    creds = loader.load_json_config(str(creds_path))
    mt5_creds = creds.get("mt5", creds)
    connector = create_connector_from_credentials(mt5_creds, logger=logger)
    connector.verify_connection()
    return connector


def main(symbol_filter: str = None):
    connector = load_connector()
    pm = PositionManager(connector, logger=logger)
    om = OrderManager(connector, logger=logger)

    positions = pm.get_all_positions()
    if not positions:
        logger.info("No hay posiciones abiertas.")
        return

    to_close = []
    for p in positions:
        if symbol_filter and p.symbol != symbol_filter:
            continue
        if p.magic in INTRADAY_MAGIC_PREFIXES:
            to_close.append(p)

    if not to_close:
        logger.info("No se encontraron posiciones intraday residuales para cerrar.")
        return

    logger.info(f"Cerrando {len(to_close)} posiciones intraday residuales...")
    for pos in to_close:
        try:
            logger.info(f"Cerrando Ticket={pos.ticket} Symbol={pos.symbol} Magic={pos.magic} Vol={pos.volume}")
            om.close_position(ticket=pos.ticket)
        except Exception as e:
            logger.error(f"Error cerrando ticket {pos.ticket}: {e}")

    # Verificar
    remaining = pm.get_all_positions()
    remaining_ids = [r.ticket for r in remaining if (not symbol_filter or r.symbol == symbol_filter) and r.magic in INTRADAY_MAGIC_PREFIXES]
    if remaining_ids:
        logger.warning(f"Persisten tickets tras intento de cierre: {remaining_ids}")
    else:
        logger.info("Cierre residual completado sin posiciones pendientes.")

if __name__ == "__main__":
    # Cerrar solo BTCUSD si se desea, pasar argumento desde CLI posteriormente.
    main(symbol_filter="BTCUSD")
