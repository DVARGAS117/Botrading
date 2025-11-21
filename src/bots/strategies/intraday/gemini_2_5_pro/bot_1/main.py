"""Main del Bot 1 (INTRADAY Gemini 2.5 Pro).

Punto de entrada principal para la estrategia INTRADAY usando Gemini 2.5 Pro.
Maneja argumentos de línea de comandos, inicialización del bot y ciclos de trading.
"""

import argparse
import time
from datetime import datetime, timedelta

from src.bots.base.base_bot_operations import BotMode
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.config import (
    get_bot_1_config,
    BOT_1_SETTINGS,
)
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.strategy import IntradayBot1Strategy
from src.core.logger import get_bot_logger


def parse_arguments():
    """Parsea argumentos de línea de comandos.
    
    Returns:
        Argumentos parseados con configuración CLI
    """
    parser = argparse.ArgumentParser(
        description="Bot 1 - INTRADAY Strategy con Gemini 2.5 Pro",
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
        default=900,
        help="Intervalo entre ciclos en segundos (default: 900 = 15min)",
    )

    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        default=None,  # No default, usar configuración del bot
        help="Símbolos a operar (default: usar configuración del bot)",
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
    """Solicita confirmación para operar en modo LIVE.
    
    Returns:
        True si el usuario confirma, False en caso contrario
    """
    print("\n" + "=" * 60)
    print("⚠️  ADVERTENCIA: MODO LIVE ACTIVADO")
    print("=" * 60)
    print("Estás a punto de ejecutar el bot INTRADAY en modo LIVE.")
    print("Esto significa que se ejecutarán operaciones REALES con dinero REAL.")
    print("=" * 60)

    response = input(
        "\n¿Estás seguro de continuar en modo LIVE? (escribe 'SI' para confirmar): "
    )

    return response.strip().upper() == "SI"


def ask_evaluation_mode() -> str:
    """Pregunta al usuario si desea evaluar al instante o esperar el ciclo.
    
    Esta función se ejecuta siempre al iniciar el bot, independientemente
    del modo de operación (single-cycle o continuo).
    
    Returns:
        'instant' para evaluación inmediata, 'wait' para esperar ciclo
    """
    print("\n" + "=" * 60)
    print("⏰ MODO DE EVALUACIÓN")
    print("=" * 60)
    print("El bot puede:")
    print("• INSTANT: Evaluar inmediatamente con datos disponibles")
    print("• WAIT: Esperar el próximo ciclo de vela cerrada (1 min después)")
    print("=" * 60)
    print("IMPORTANTE: El bot siempre usa velas CERRADAS, nunca velas en formación.")
    print("Si ejecutas a las 8:16, usará datos hasta la vela cerrada a las 8:15.")
    print("=" * 60)

    while True:
        response = input(
            "\n¿Deseas evaluar al INSTANTE o ESPERAR el ciclo? (instant/wait): "
        ).strip().lower()

        if response in ['instant', 'wait']:
            return response
        else:
            print("❌ Respuesta inválida. Escribe 'instant' o 'wait'.")


def wait_for_next_cycle() -> None:
    """Espera hasta el próximo ciclo de vela (1 minuto después de vela cerrada).
    
    El sistema de velas M15 se cierra cada 15 minutos.
    Si estamos en minuto X, esperamos hasta X+1 para asegurar vela cerrada.
    """
    now = datetime.now()
    current_minute = now.minute
    current_second = now.second

    # Calcular minutos hasta el próximo minuto + 1
    # Ejemplo: si son las 8:16:30, esperamos hasta 8:17:00
    wait_seconds = 60 - current_second  # Esperar hasta el próximo minuto

    print(f"\n⏳ Esperando próximo ciclo de vela...")
    print(f"⏰ Hora actual: {now.strftime('%H:%M:%S')}")
    print(f"⏱️  Esperando {wait_seconds} segundos hasta el próximo minuto...")

    time.sleep(wait_seconds)

    final_time = datetime.now()
    print(f"✅ Ciclo completado. Continuando a las {final_time.strftime('%H:%M:%S')}")


def display_bot_banner() -> None:
    """Muestra banner de información del bot."""
    print("\n" + "=" * 60)
    print("🤖 BOT 1 - ESTRATEGIA INTRADAY")
    print("=" * 60)
    print(f"Versión: {BOT_1_SETTINGS['version']}")
    print(f"Descripción: {BOT_1_SETTINGS['descripcion']}")
    print(f"Estrategia: {BOT_1_SETTINGS['estrategia']}")
    print("=" * 60)


def display_gemini_config() -> None:
    """Muestra configuración de Gemini 2.5 Pro."""
    gemini_cfg = BOT_1_SETTINGS['gemini_config']
    print("\n📡 Configuración Gemini 2.5 Pro:")
    print(f"  - Thinking Level: {gemini_cfg['thinking_level']}")
    print(f"  - Code Execution: {'Habilitado' if gemini_cfg['code_execution'] else 'Deshabilitado'}")
    print(f"  - Media Resolution: {gemini_cfg['media_resolution']}")
    print(f"  - Temperature: {gemini_cfg['temperature']}")
    print(f"  - Max Output Tokens: {gemini_cfg['max_output_tokens']}")


def display_execution_summary(args, config_symbols) -> None:
    """Muestra resumen de configuración de ejecución.
    
    Args:
        args: Argumentos parseados de CLI
        config_symbols: Símbolos de la configuración del bot
    """
    symbols_to_show = args.symbols if args.symbols else config_symbols
    print(f"\n⚙️  Configuración de Ejecución:")
    print(f"  - Modo: {args.mode.upper()}")
    print(f"  - Símbolos: {', '.join(symbols_to_show)}")
    print(f"  - Intervalo: {args.interval}s ({args.interval/60:.1f} minutos)")
    print(f"  - Log Level: {args.log_level}")
    print(f"  - Ciclo Único: {'Sí' if args.single_cycle else 'No'}")
    print(f"  - Guardar Prompts: {'Sí' if args.save_prompts else 'No'}")
    print("=" * 60 + "\n")


def main() -> None:
    """Punto de entrada del Bot 1 INTRADAY Gemini 2.5 Pro."""
    args = parse_arguments()
    
    # Configurar logging para guardar en directorio del bot
    from pathlib import Path
    from src.core.logger import LogConfig, LogLevel
    
    # Directorio del bot
    bot_dir = Path(__file__).parent
    log_dir = bot_dir / "logs"
    
    # Convertir log_level string a LogLevel enum
    try:
        level_enum = LogLevel[args.log_level.upper()]
    except KeyError:
        level_enum = LogLevel.INFO  # Default fallback
    
    # Configuración de logging con archivo
    log_config = LogConfig(
        level=level_enum,
        log_dir=str(log_dir),
        log_to_console=True,
        log_to_file=True,
        format_json=False
    )
    
    logger = get_bot_logger("IntradayBot1_Main", log_config)

    # Determinar modo de operación
    mode = BotMode.LIVE if args.mode == "live" else BotMode.DEMO

    # Mostrar información del bot
    display_bot_banner()
    display_gemini_config()
    
    # Obtener configuración del bot para mostrar símbolos
    temp_config = get_bot_1_config(mode=mode)
    display_execution_summary(args, temp_config.symbols)

    # Confirmar modo LIVE si es necesario
    if mode == BotMode.LIVE and not args.yes:
        if not confirm_live_mode():
            logger.info("Operación cancelada por el usuario")
            print("\n❌ Operación cancelada. No se ejecutará en modo LIVE.")
            return

    # Preguntar modo de evaluación (siempre, independientemente del modo)
    evaluation_mode = ask_evaluation_mode()

    if evaluation_mode == 'wait':
        wait_for_next_cycle()

    try:
        # Obtener configuración del bot
        config = get_bot_1_config(mode=mode)
        
        # Usar símbolos de CLI si se especificaron, sino usar configuración del bot
        if args.symbols:
            config.symbols = args.symbols
        
        config.log_level = args.log_level
        config.save_prompts = args.save_prompts

        logger.info("Creando instancia de Bot INTRADAY 1 (Gemini 2.5 Pro)...")
        bot = IntradayBot1Strategy(config)

        logger.info("Inicializando componentes...")
        if not bot.initialize():
            logger.error("❌ Error en inicialización. Abortando.")
            print("\n❌ Error en inicialización. Revisa los logs para más detalles.")
            return

        logger.info("✅ Bot INTRADAY inicializado correctamente")

        if args.single_cycle:
            # Ejecutar un solo ciclo
            logger.info("Ejecutando un solo ciclo de trading INTRADAY...")
            print("\n🔄 Ejecutando ciclo de trading INTRADAY...")
            bot.run_trading_cycle()
            print("✅ Ciclo completado")

            # Mostrar métricas
            metrics = bot.get_performance_metrics()
            print("\n📊 Métricas INTRADAY:")
            print(f"  - PnL del día: {metrics['current_pnl_r']:.2f}R")
            print(f"  - Trades hoy: {metrics['trades_today']}")
            print(f"  - Contexto: {metrics['market_context']}")
            print(f"  - Timestamp: {metrics['timestamp']}")

        else:
            # Ejecutar en modo continuo
            logger.info(
                f"Iniciando ejecución continua INTRADAY (intervalo: {args.interval}s)...",
            )
            print("\n🚀 Bot INTRADAY ejecutándose en modo continuo...")
            print(f"⏱️  Intervalo: {args.interval}s ({args.interval/60:.1f} minutos)")
            print("Press Ctrl+C to stop\n")

            bot.run_continuous(interval_seconds=args.interval)

    except KeyboardInterrupt:
        logger.info("\n⏹️  Bot INTRADAY detenido por usuario")
        print("\n⏹️  Bot INTRADAY detenido")

    except Exception as e:  # pragma: no cover - ruta crítica
        logger.error(f"❌ Error crítico en Bot INTRADAY: {str(e)}")
        print(f"\n❌ Error crítico: {str(e)}")
        print("Revisa los logs para más detalles")

    finally:
        print("\n👋 Cerrando Bot INTRADAY 1...")
        logger.info("Bot INTRADAY 1 finalizado")


if __name__ == "__main__":
    main()
