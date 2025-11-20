"""Configuración del Bot 1 (VWAP Gemini 3 Pro)."""

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.mt5_data_extractor import Timeframe


def get_bot_1_config(mode: BotMode = BotMode.DEMO) -> BotConfig:
    """Obtiene la configuración para Bot 1 (Numérico Baseline)."""

    return BotConfig(
        bot_id=1,
        bot_name="Numérico Baseline",
        bot_type="numerico",
        mode=mode,
        symbols=["EURUSD"],
        timeframes=[
            Timeframe.M1,
            Timeframe.M5,
            Timeframe.H1,
        ],
        trading_hours=("09:00", "13:00"),
        timezone_local="America/Lima",
        risk_per_trade=0.5,
        max_daily_risk=2.0,
        reevaluation_interval_minutes=10,
        ai_model="gemini-3-pro-preview",
        enable_dual_orders=True,
        log_level="INFO",
    )


BOT_1_SETTINGS = {
    "nombre_corto": "B1_NumBase",
    "descripcion": "Bot numérico baseline con metodología VWAP",
    "version": "1.0.0",
    "prompt_config": {
        "use_vwap_methodology": True,
        "include_candle_data": True,
        "max_candles_5m": "session",
        "max_candles_1m": 200,
        "max_candles_1h": 30,
    },
    "execution_config": {
        "confirm_signals": False,
        "use_market_orders": True,
        "use_limit_orders": True,
        "limit_offset_pips": 2.0,
    },
    "logging_config": {
        "log_all_queries": True,
        "log_ai_responses": True,
        "save_charts": False,
    },
}
