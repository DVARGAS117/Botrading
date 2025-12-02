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
    # La evaluación de patrones se ejecuta cada 5 minutos (M5) alineada a :01/:06/:11/:16/....
    # Este parámetro se mantiene para compatibilidad pero ya no fuerza ciclos en segundos.
    parser.add_argument("--interval", type=int, default=300, help="Intervalo técnico (segundos). Por defecto M5 = 300s")
    parser.add_argument("--force-trading", action="store_true", help="Ignora ventanas horarias y opera 24/7 para pruebas")
    parser.add_argument("--verbose", action="store_true", help="Muestra trazas detalladas de evaluación (DEBUG)")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Configurar Logger
    bot_dir = Path(__file__).parent
    log_dir = bot_dir / "logs"
    # Nivel de log configurable por flag --verbose
    log_level = LogLevel.DEBUG if args.verbose else LogLevel.INFO
    log_config = LogConfig(level=log_level, log_dir=str(log_dir), log_to_console=True, log_to_file=True)
    logger = get_bot_logger("Kamikaze_Main", log_config)
    
    logger.info("Iniciando Kamikaze Bot...")
    
    mode = BotMode.LIVE if args.mode == "live" else BotMode.DEMO
    config = get_kamikaze_config(mode)
    
    bot = KamikazeStrategy(config)
    # Aplicar flag para forzar trading fuera de horario
    bot.force_trading = bool(getattr(args, "force_trading", False))
    # Propagar verbose al logger interno del bot y a la estrategia
    try:
        bot.logger.set_level(log_level)
    except Exception:
        pass
    # Marcar modo verbose en la estrategia
    try:
        setattr(bot, "verbose", bool(args.verbose))
    except Exception:
        pass
    
    if not bot.initialize():
        logger.error("Fallo inicialización.")
        return
        
    logger.info(f"Bot inicializado en modo {mode.name}. Intervalo técnico: {args.interval}s")
    if args.verbose:
        logger.info("Verbose activado: nivel DEBUG y trazas detalladas")
    
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
