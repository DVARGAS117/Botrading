import logging
import sys
from pathlib import Path

# Asegurar que 'src' esté en sys.path para ejecución directa del script
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / 'src'
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.core.config_loader import ConfigLoader
from src.core.mt5_connector import create_connector_from_credentials
from src.core.position_manager import PositionManager

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')
logger = logging.getLogger("list_positions")


def load_mt5_connector():
    creds_path = Path("config/credentials.json")
    loader = ConfigLoader()
    creds = loader.load_json_config(str(creds_path))
    mt5_creds = creds.get("mt5", creds)
    connector = create_connector_from_credentials(mt5_creds, logger=logger)
    connector.verify_connection()
    return connector


def main():
    connector = load_mt5_connector()
    pm = PositionManager(connector, logger=logger)
    positions = pm.get_all_positions()
    if not positions:
        logger.info("Sin posiciones abiertas.")
        return
    logger.info("Listado de posiciones abiertas:")
    for p in positions:
        logger.info(
            f"Ticket={p.ticket} Symbol={p.symbol} Type={p.type.name} Vol={p.volume} Open={p.price_open} Curr={p.price_current} SL={p.sl} TP={p.tp} Profit={p.profit} Magic={p.magic} OpenTime={p.time_open.isoformat()}"
        )

if __name__ == "__main__":
    main()
