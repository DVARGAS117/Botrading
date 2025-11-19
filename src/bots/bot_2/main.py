"""
Bot 2 - Main (Numérico Alternativo)

Punto de entrada para Bot 2 con prompts alternativos.

Uso:
    python -m src.bots.bot_2.main
    python -m src.bots.bot_2.main --single-cycle
    python -m src.bots.bot_2.main --mode live

Author: Botrading Team  
Date: 2025-11-17
"""

import sys
import argparse
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from src.bots.bot_2.config import get_bot_2_config, BOT_2_SETTINGS
from src.bots.bot_2.strategy import Bot2Strategy
from src.bots.base.base_bot_operations import BotMode
from src.core.logger import get_bot_logger


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Bot 2 - Numérico Alternativo (Prompts Concisos)'
    )
    parser.add_argument('--mode', type=str, choices=['demo', 'live'], default='demo')
    parser.add_argument('--single-cycle', action='store_true')
    parser.add_argument('--interval', type=int, default=300)
    parser.add_argument('--symbols', type=str, nargs='+', default=['EURUSD'])
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    parser.add_argument('--save-prompts', action='store_true', 
                        help='Generar prompt en .txt SIN consultar a Gemini (ahorra tokens)')
    return parser.parse_args()


def confirm_live_mode() -> bool:
    print("\n" + "="*60)
    print("⚠️  ADVERTENCIA: MODO LIVE ACTIVADO - BOT 2")
    print("="*60)
    response = input("\n¿Continuar en modo LIVE? (escribe 'SI'): ")
    return response.strip().upper() == "SI"


def main():
    args = parse_arguments()
    logger = get_bot_logger("Bot2_Main")
    
    print("\n" + "="*60)
    print("🤖 BOT 2 - NUMÉRICO ALTERNATIVO")
    print("="*60)
    print(f"Versión: {BOT_2_SETTINGS['version']}")
    print(f"Variante: Prompts Concisos (sin velas OHLCV)")
    print(f"Modo: {args.mode.upper()}")
    print("="*60 + "\n")
    
    mode = BotMode.LIVE if args.mode == 'live' else BotMode.DEMO
    
    if mode == BotMode.LIVE and not confirm_live_mode():
        logger.info("Operación cancelada")
        return
    
    try:
        config = get_bot_2_config(mode=mode)
        config.symbols = args.symbols
        config.log_level = args.log_level
        config.save_prompts = args.save_prompts
        
        bot = Bot2Strategy(config)
        
        if not bot.initialize():
            print("\n❌ Error en inicialización")
            return
        
        if args.single_cycle:
            print("\n🔄 Ejecutando ciclo único...")
            bot.run_trading_cycle()
            print("✅ Ciclo completado")
        else:
            print(f"\n🚀 Ejecutando modo continuo (intervalo: {args.interval}s)...")
            bot.run_continuous(interval_seconds=args.interval)
            
    except KeyboardInterrupt:
        print("\n⏹️  Bot 2 detenido")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
    finally:
        print("\n👋 Cerrando Bot 2...")


if __name__ == "__main__":
    main()
