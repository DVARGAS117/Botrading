"""Configuración para la estrategia Kamikaze."""

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.mt5_data_extractor import Timeframe

KAMIKAZE_SETTINGS = {
    "bot_id": 106,
    "bot_name": "Kamikaze Bot",
    "version": "1.0.0",
    "descripcion": "Estrategia de ruptura de volatilidad M5 alineada con tendencia H1 (Gemini)",
    "estrategia": "Kamikaze",
    "gemini_config": {
        "model": "gemini-2.5-pro",
        "temperature": 0.1, # Baja temperatura para respuestas deterministas (BULLISH/BEARISH)
        "max_output_tokens": 100,
        "top_p": 0.8,
        "top_k": 40,
    },
    "trading_config": {
        "symbols": ["XAUUSD", "US100"], # Default symbols
        "timeframe_analysis": "H1",
        "timeframe_execution": "M5",
        "gemini_interval": 1800, # 30 minutos
        "lot_size": 0.01,
        "sl_points": 500, # Default, ajustar por simbolo
        "tp_points": 1000, # Default, ajustar por simbolo
        "deviation": 20,
    }
}

def get_kamikaze_config(mode: BotMode = BotMode.DEMO) -> BotConfig:
    """Genera la configuración del bot Kamikaze."""
    return BotConfig(
        bot_id=KAMIKAZE_SETTINGS["bot_id"],
        bot_name=KAMIKAZE_SETTINGS["bot_name"],
        bot_type="numerico",
        mode=mode,
        symbols=KAMIKAZE_SETTINGS["trading_config"]["symbols"],
        timeframes=[Timeframe.M5, Timeframe.H1],
        risk_per_trade=1.0, # No usado directamente, usamos lotes fijos por ahora según estrategia.md
        max_daily_risk=5.0,
        ai_model=KAMIKAZE_SETTINGS["gemini_config"]["model"],
        log_level="INFO",
        save_prompts=False
    )
