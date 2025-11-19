"""
Bot 2 - Configuración (Numérico Alternativo)

Bot de trading numérico que utiliza una VARIANTE de prompts vs Bot 1.
Mantiene la metodología VWAP pero experimenta con diferentes formas
de presentar la información a la IA.

Objetivo: Comparar efectividad de diferentes estilos de prompt.

Author: Botrading Team
Date: 2025-11-17
"""

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.mt5_data_extractor import Timeframe


def get_bot_2_config(mode: BotMode = BotMode.DEMO) -> BotConfig:
    """
    Obtiene la configuración para Bot 2 (Numérico Alternativo).
    
    Args:
        mode: Modo de operación (DEMO o LIVE)
    
    Returns:
        BotConfig configurado para Bot 2
    """
    return BotConfig(
        bot_id=2,
        bot_name="Numérico Alternativo",
        bot_type="numerico",
        mode=mode,
        
        # Configuración idéntica a Bot 1
        symbols=["EURUSD"],
        timeframes=[
            Timeframe.M1,
            Timeframe.M5,
            Timeframe.H1
        ],
        trading_hours=("06:00", "13:00"),
        timezone_local="America/Lima",
        risk_per_trade=0.5,
        max_daily_risk=2.0,
        reevaluation_interval_minutes=10,
        ai_model="gemini-2.5-pro",
        enable_dual_orders=True,
        log_level="INFO"
    )


# Configuración adicional específica de Bot 2
BOT_2_SETTINGS = {
    "nombre_corto": "B2_NumAlt",
    "descripcion": "Bot numérico con prompts alternativos (variante experimental)",
    "version": "1.0.0",
    
    # Configuración de prompts (DIFERENTE a Bot 1)
    "prompt_config": {
        "use_vwap_methodology": True,
        "prompt_style": "concise",  # Estilo más conciso vs Bot 1
        "include_candle_data": False,  # NO incluir velas (solo indicadores)
        "emphasize_discipline": True,  # Énfasis en disciplina
        "include_counter_examples": True  # Incluir ejemplos de qué NO hacer
    },
    
    # Ejecución idéntica a Bot 1
    "execution_config": {
        "confirm_signals": False,
        "use_market_orders": True,
        "use_limit_orders": True,
        "limit_offset_pips": 2.0
    },
    
    "logging_config": {
        "log_all_queries": True,
        "log_ai_responses": True,
        "save_charts": False
    }
}
