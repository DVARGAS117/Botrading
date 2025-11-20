"""Configuración del Bot 1 (INTRADAY Gemini 3 Pro).

Este archivo define la configuración base para el bot de estrategia INTRADAY
utilizando el modelo Gemini 3 Pro con los parámetros óptimos recomendados:
- thinking_level: HIGH (para razonamiento profundo)
- code_execution: Habilitado (cálculos matemáticos precisos)
- media_resolution: high (análisis de alta calidad)
"""

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.mt5_data_extractor import Timeframe


def get_bot_1_config(mode: BotMode = BotMode.DEMO) -> BotConfig:
    """Obtiene la configuración para Bot 1 (INTRADAY Baseline).
    
    Args:
        mode: Modo de operación (DEMO o LIVE)
        
    Returns:
        BotConfig: Configuración del bot con parámetros optimizados para Gemini 3 Pro
    """
    return BotConfig(
        bot_id=101,  # ID único para estrategia INTRADAY
        bot_name="INTRADAY Baseline",
        bot_type="intraday",
        mode=mode,
        symbols=["EURUSD"],
        timeframes=[
            Timeframe.M1,   # Para señales precisas de entrada
            Timeframe.M5,   # Para contexto táctico
            Timeframe.M15,  # Para contexto intermedio
            Timeframe.H1,   # Para tendencia general
        ],
        trading_hours=("08:00", "16:00"),  # Horario personalizado INTRADAY
        timezone_local="America/Lima",
        risk_per_trade=1.0,  # 1% de riesgo por operación (configuración INTRADAY)
        max_daily_risk=3.0,  # Máximo 3R de pérdida diaria
        reevaluation_interval_minutes=10,  # Reevaluación cada 10 minutos
        ai_model="gemini-3-pro-preview",  # Modelo Gemini 3 Pro
        enable_dual_orders=False,  # INTRADAY: Solo una orden por señal
        log_level="INFO",
    )


BOT_1_SETTINGS = {
    "nombre_corto": "B1_INTRADAY",
    "descripcion": "Bot baseline para estrategia INTRADAY con Gemini 3 Pro",
    "version": "1.0.0",
    "estrategia": "INTRADAY",
    
    # Configuración de prompts y análisis
    "prompt_config": {
        "use_intraday_strategy": True,
        "include_candle_data": True,
        "max_candles_1m": 100,   # Últimas 100 velas M1
        "max_candles_5m": 50,    # Últimas 50 velas M5
        "max_candles_15m": 30,   # Últimas 30 velas M15
        "max_candles_1h": 24,    # Últimas 24 velas H1
    },
    
    # Parámetros específicos de Gemini 3 Pro
    "gemini_config": {
        "thinking_level": "HIGH",  # Razonamiento profundo
        "code_execution": True,    # Habilitar ejecución de código Python
        "media_resolution": "high",  # Resolución alta para análisis
        "temperature": 0.7,  # Balance entre creatividad y consistencia
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    },
    
    # Configuración de ejecución
    "execution_config": {
        "confirm_signals": False,  # Auto-ejecución sin confirmación
        "use_market_orders": True,  # Solo órdenes de mercado (sin dual orders)
        "use_dual_orders": False,   # INTRADAY: Una orden por señal
        "max_slippage_pips": 5.0,   # Slippage máximo aceptable
        "partial_close_enabled": True,  # Permitir cierres parciales
        "trailing_stop_enabled": False,  # Trailing stop (a implementar)
    },
    
    # Configuración de logging y debugging
    "logging_config": {
        "log_all_queries": True,      # Registrar todas las consultas a IA
        "log_ai_responses": True,     # Registrar respuestas de IA
        "save_charts": False,         # No guardar gráficos por defecto
        "save_prompts": False,        # No guardar prompts por defecto
        "log_indicators": True,       # Registrar valores de indicadores
    },
    
    # Indicadores a utilizar (placeholder - se definirán posteriormente)
    "indicators": {
        # TODO: Definir indicadores específicos de la estrategia INTRADAY
        # Ejemplos: EMA, RSI, MACD, Bandas de Bollinger, etc.
    },
}
