"""Main del Bot Kamikaze.

Punto de entrada principal para la estrategia Kamikaze.
"""

import argparse
import time
from pathlib import Path

from src.bots.base.base_bot_operations import BotMode
from src.bots.strategies.Kamikaze.config import get_kamikaze_config, KAMIKAZE_SETTINGS
from src.bots.strategies.Kamikaze.strategy import KamikazeStrategy
from src.core.logger import get_bot_logger, LogConfig, LogLevel

def parse_arguments():
    parser = argparse.ArgumentParser(description="Kamikaze Bot Strategy")
    parser.add_argument("--mode", type=str, choices=["demo", "live"], default="demo", help="Modo de operación")
    parser.add_argument("--interval", type=int, default=10, help="Intervalo entre ciclos técnicos (segundos)")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Configurar Logger
    bot_dir = Path(__file__).parent
    log_dir = bot_dir / "logs"
    log_config = LogConfig(level=LogLevel.INFO, log_dir=str(log_dir), log_to_console=True, log_to_file=True)
    logger = get_bot_logger("Kamikaze_Main", log_config)
    
    logger.info("Iniciando Kamikaze Bot...")
    
    mode = BotMode.LIVE if args.mode == "live" else BotMode.DEMO
    config = get_kamikaze_config(mode)
    
    bot = KamikazeStrategy(config)
    
    if not bot.initialize():
        logger.error("Fallo inicialización.")
        return
        
    logger.info(f"Bot inicializado en modo {mode.name}. Intervalo técnico: {args.interval}s")
    
    try:
        bot.run_continuous(interval_seconds=args.interval)
    except KeyboardInterrupt:
        logger.info("Bot detenido por usuario.")
    except Exception as e:
        logger.error(f"Error crítico: {e}")
    finally:
        logger.info("Finalizando bot.")

if __name__ == "__main__":
    main()
