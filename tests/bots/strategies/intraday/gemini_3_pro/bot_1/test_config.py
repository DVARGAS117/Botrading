"""Tests para la configuración del Bot 1 INTRADAY."""

import pytest

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.bots.strategies.intraday.gemini_3_pro.bot_1.config import (
    get_bot_1_config,
    BOT_1_SETTINGS,
)
from src.core.mt5_data_extractor import Timeframe


class TestBot1Config:
    """Tests para la configuración del Bot 1 INTRADAY."""

    def test_get_bot_1_config_demo_mode(self):
        """Test: Configuración en modo DEMO."""
        config = get_bot_1_config(mode=BotMode.DEMO)

        assert isinstance(config, BotConfig)
        assert config.bot_id == 101
        assert config.bot_name == "INTRADAY Baseline"
        assert config.bot_type == "intraday"
        assert config.mode == BotMode.DEMO
        assert config.ai_model == "gemini-3-pro-preview"
        assert config.enable_dual_orders is False  # INTRADAY: sin dual orders

    def test_get_bot_1_config_live_mode(self):
        """Test: Configuración en modo LIVE."""
        config = get_bot_1_config(mode=BotMode.LIVE)

        assert config.mode == BotMode.LIVE
        assert config.bot_id == 101

    def test_bot_1_config_symbols(self):
        """Test: Símbolos configurados."""
        config = get_bot_1_config()

        assert "EURUSD" in config.symbols
        assert isinstance(config.symbols, list)

    def test_bot_1_config_timeframes(self):
        """Test: Timeframes configurados."""
        config = get_bot_1_config()

        assert Timeframe.M1 in config.timeframes
        assert Timeframe.M5 in config.timeframes
        assert Timeframe.M15 in config.timeframes
        assert Timeframe.H1 in config.timeframes
        assert len(config.timeframes) == 4

    def test_bot_1_config_trading_hours(self):
        """Test: Horario de trading configurado."""
        config = get_bot_1_config()

        assert config.trading_hours == ("08:00", "16:00")  # Horario INTRADAY personalizado
        assert config.timezone_local == "America/Lima"

    def test_bot_1_config_risk_parameters(self):
        """Test: Parámetros de riesgo."""
        config = get_bot_1_config()

        assert config.risk_per_trade == 1.0  # INTRADAY: 1% por operación
        assert config.max_daily_risk == 3.0  # INTRADAY: 3R máximo diario
        assert config.reevaluation_interval_minutes == 10  # INTRADAY: cada 10 min

    def test_bot_1_settings_structure(self):
        """Test: Estructura de BOT_1_SETTINGS."""
        assert BOT_1_SETTINGS["nombre_corto"] == "B1_INTRADAY"
        assert BOT_1_SETTINGS["version"] == "1.0.0"
        assert BOT_1_SETTINGS["estrategia"] == "INTRADAY"

    def test_bot_1_settings_gemini_config(self):
        """Test: Configuración de Gemini 3 Pro."""
        gemini_cfg = BOT_1_SETTINGS["gemini_config"]

        assert gemini_cfg["thinking_level"] == "HIGH"
        assert gemini_cfg["code_execution"] is True
        assert gemini_cfg["media_resolution"] == "high"
        assert gemini_cfg["temperature"] == 0.7
        assert gemini_cfg["max_output_tokens"] == 8192

    def test_bot_1_settings_prompt_config(self):
        """Test: Configuración de prompts."""
        prompt_cfg = BOT_1_SETTINGS["prompt_config"]

        assert prompt_cfg["use_intraday_strategy"] is True
        assert prompt_cfg["include_candle_data"] is True
        assert prompt_cfg["max_candles_1m"] == 100
        assert prompt_cfg["max_candles_5m"] == 50
        assert prompt_cfg["max_candles_15m"] == 30
        assert prompt_cfg["max_candles_1h"] == 24

    def test_bot_1_settings_execution_config(self):
        """Test: Configuración de ejecución."""
        exec_cfg = BOT_1_SETTINGS["execution_config"]

        assert exec_cfg["confirm_signals"] is False
        assert exec_cfg["use_market_orders"] is True
        assert exec_cfg["use_dual_orders"] is False  # INTRADAY: sin dual orders
        assert exec_cfg["max_slippage_pips"] == 5.0
        assert exec_cfg["partial_close_enabled"] is True

    def test_bot_1_settings_logging_config(self):
        """Test: Configuración de logging."""
        log_cfg = BOT_1_SETTINGS["logging_config"]

        assert log_cfg["log_all_queries"] is True
        assert log_cfg["log_ai_responses"] is True
        assert log_cfg["save_charts"] is False
        assert log_cfg["save_prompts"] is False
        assert log_cfg["log_indicators"] is True

    def test_config_default_mode_is_demo(self):
        """Test: Modo por defecto es DEMO."""
        config = get_bot_1_config()

        assert config.mode == BotMode.DEMO

    def test_config_bot_id_unique(self):
        """Test: Bot ID es único para estrategia INTRADAY."""
        config = get_bot_1_config()

        # ID 101 para distinguir de bots VWAP (1-5)
        assert config.bot_id == 101
        assert config.bot_id not in range(1, 6)  # No conflicto con bots VWAP
