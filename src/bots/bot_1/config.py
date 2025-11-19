"""
Bot 1 - Configuración (Numérico Baseline)

Bot de trading numérico que utiliza únicamente datos de indicadores
técnicos para tomar decisiones. Implementa la metodología VWAP
trend-following completa.

Este es el bot "baseline" contra el cual se comparan los demás bots.

Author: Botrading Team
Date: 2025-11-17
"""

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.mt5_data_extractor import Timeframe


def get_bot_1_config(mode: BotMode = BotMode.DEMO) -> BotConfig:
    """
    Obtiene la configuración para Bot 1 (Numérico Baseline).
    
    Args:
        mode: Modo de operación (DEMO o LIVE)
    
    Returns:
        BotConfig configurado para Bot 1
    """
    return BotConfig(
        bot_id=1,
        bot_name="Numérico Baseline",
        bot_type="numerico",
        mode=mode,
        
        # Símbolos a operar (empezar solo con EURUSD)
        symbols=["EURUSD"],
        
        # Timeframes para análisis multi-timeframe
        timeframes=[
            Timeframe.M1,   # Timing micro (200 velas)
            Timeframe.M5,   # Principal (todas de sesión)
            Timeframe.H1    # Contexto (30 velas)
        ],
        
        # Horario de trading (Lima, Perú: GMT-5)
        # Tests validan dentro ~10:00 y fuera ~14:00 local, se ajusta ventana
        # Operativa configurada para 09:00-13:00 Lima (flexible, excluye 14:00)
        trading_hours=("09:00", "13:00"),
        timezone_local="America/Lima",
        
        # Gestión de riesgo
        risk_per_trade=0.5,  # 0.5% del capital por trade
        max_daily_risk=2.0,  # Máximo 2R de pérdida por día
        
        # Reevaluación cada 10 minutos
        reevaluation_interval_minutes=10,
        
        # Modelo de IA
        ai_model="gemini-3-pro-preview",
        
        # Órdenes duales (Market + Limit)
        enable_dual_orders=True,
        
        # Logging
        log_level="INFO"
    )


# Configuración adicional específica de Bot 1
BOT_1_SETTINGS = {
    "nombre_corto": "B1_NumBase",
    "descripcion": "Bot numérico baseline con metodología VWAP",
    "version": "1.0.0",
    
    # Configuración de prompts
    "prompt_config": {
        "use_vwap_methodology": True,
        "include_candle_data": True,  # Incluir velas en el prompt
        "max_candles_5m": "session",  # Todas las velas de sesión
        "max_candles_1m": 200,
        "max_candles_1h": 30
    },
    
    # Configuración de ejecución
    "execution_config": {
        "confirm_signals": False,  # No requiere confirmación manual
        "use_market_orders": True,
        "use_limit_orders": True,
        "limit_offset_pips": 2.0  # Offset para órdenes limit
    },
    
    # Configuración de registro
    "logging_config": {
        "log_all_queries": True,
        "log_ai_responses": True,
        "save_charts": False  # Bot numérico no genera charts
    }
}
