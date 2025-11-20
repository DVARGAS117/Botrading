"""Main del Bot 1 (VWAP Gemini 3 Pro).

Basado en `src.bots.bot_1.main`, reubicado bajo strategies.
"""

import argparse

from src.bots.base.base_bot_operations import BotMode
from src.bots.strategies.vwap.gemini_3_pro.bot_1.config import (
    get_bot_1_config,
    BOT_1_SETTINGS,
)
from src.bots.strategies.vwap.gemini_3_pro.bot_1.strategy import Bot1Strategy
from src.core.logger import get_bot_logger


def parse_arguments():
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Bot 1 - Numérico Baseline con VWAP Methodology",
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["demo", "live"],
        default="demo",
        help="Modo de operación (default: demo)",
    )

    parser.add_argument(
        "--single-cycle",
        action="store_true",
        help="Ejecutar un solo ciclo de trading y salir",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Intervalo entre ciclos en segundos (default: 300 = 5min)",
    )

    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        default=["EURUSD"],
        help="Símbolos a operar (default: EURUSD)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nivel de logging (default: INFO)",
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-confirma ejecución LIVE (salta prompt interactivo)",
    )

    parser.add_argument(
        "--save-prompts",
        action="store_true",
        help="Generar prompt en .txt SIN consultar a Gemini (solo validación)",
    )

    return parser.parse_args()


def confirm_live_mode() -> bool:
    """Solicita confirmación para operar en modo LIVE."""

    print("\n" + "=" * 60)
    print("⚠️  ADVERTENCIA: MODO LIVE ACTIVADO")
    print("=" * 60)
    print("Estás a punto de ejecutar el bot en modo LIVE.")
    print("Esto significa que se ejecutarán operaciones REALES con dinero REAL.")
    print("=" * 60)

    response = input("\n¿Estás seguro de continuar en modo LIVE? (escribe 'SI' para confirmar): ")

    return response.strip().upper() == "SI"


def main() -> None:
    """Punto de entrada del Bot 1 VWAP Gemini 3 Pro."""

    args = parse_arguments()
    logger = get_bot_logger("Bot1_Main")

    print("\n" + "=" * 60)
    print("🤖 BOT 1 - NUMÉRICO BASELINE")
    print("=" * 60)
    print(f"Versión: {BOT_1_SETTINGS['version']}")
    print(f"Descripción: {BOT_1_SETTINGS['descripcion']}")
    print(f"Modo: {args.mode.upper()}")
    print(f"Símbolos: {', '.join(args.symbols)}")
    print(f"Intervalo: {args.interval}s")
    print("=" * 60 + "\n")

    mode = BotMode.LIVE if args.mode == "live" else BotMode.DEMO

    if mode == BotMode.LIVE and not args.yes:
        if not confirm_live_mode():
            logger.info("Operación cancelada por el usuario")
            print("\n❌ Operación cancelada. No se ejecutará en modo LIVE.")
            return

    try:
        config = get_bot_1_config(mode=mode)
        config.symbols = args.symbols
        config.log_level = args.log_level
        config.save_prompts = args.save_prompts

        logger.info("Creando instancia de Bot 1...")
        bot = Bot1Strategy(config)

        logger.info("Inicializando componentes...")
        if not bot.initialize():
            logger.error("❌ Error en inicialización. Abortando.")
            print("\n❌ Error en inicialización. Revisa los logs para más detalles.")
            return

        logger.info("✅ Bot inicializado correctamente")

        if args.single_cycle:
            logger.info("Ejecutando un solo ciclo de trading...")
            print("\n🔄 Ejecutando ciclo de trading...")
            bot.run_trading_cycle()
            print("✅ Ciclo completado")

            metrics = bot.get_performance_metrics()
            print("\n📊 Métricas:")
            print(f"  - PnL del día: {metrics['current_pnl_r']:.2f}R")
            print(f"  - Trades hoy: {metrics['trades_today']}")
            print(f"  - Contexto: {metrics['market_context']}")

        else:
            logger.info(
                f"Iniciando ejecución continua (intervalo: {args.interval}s)...",
            )
            print("\n🚀 Bot ejecutándose en modo continuo...")
            print(f"⏱️  Intervalo: {args.interval}s ({args.interval/60:.1f} minutos)")
            print("Press Ctrl+C to stop\n")

            bot.run_continuous(interval_seconds=args.interval)

    except KeyboardInterrupt:
        logger.info("\n⏹️  Bot detenido por usuario")
        print("\n⏹️  Bot detenido")

    except Exception as e:  # pragma: no cover - ruta crítica
        logger.error(f"❌ Error crítico: {str(e)}")
        print(f"\n❌ Error crítico: {str(e)}")
        print("Revisa los logs para más detalles")

    finally:
        print("\n👋 Cerrando Bot 1...")
        logger.info("Bot 1 finalizado")


if __name__ == "__main__":
    main()
