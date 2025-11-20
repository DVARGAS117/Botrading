"""Tests para configuración del Bot 1 INTRADAY Gemini 2.5 Pro.

Este módulo prueba la configuración del bot siguiendo metodología TDD.
"""

import pytest
from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.config import (
    get_bot_1_config,
    BOT_1_SETTINGS,
)
from src.core.mt5_data_extractor import Timeframe


class TestBot1Config:
    """Tests para la configuración del Bot 1 INTRADAY Gemini 2.5 Pro."""
    
    def test_get_bot_1_config_default(self):
        """Test: get_bot_1_config retorna BotConfig con valores correctos por defecto."""
        config = get_bot_1_config()
        
        assert isinstance(config, BotConfig)
        assert config.bot_id == 6
        assert config.bot_name == "INTRADAY Gemini 2.5 Pro"
        assert config.bot_type == "numerico"
        assert config.mode == BotMode.DEMO
        assert config.ai_model == "gemini-2.5-pro"
        assert config.risk_per_trade == 1.0
        assert config.max_daily_risk == 3.0
        assert config.enable_dual_orders is False
    
    def test_get_bot_1_config_live_mode(self):
        """Test: get_bot_1_config acepta modo LIVE."""
        config = get_bot_1_config(mode=BotMode.LIVE)
        
        assert config.mode == BotMode.LIVE
        assert config.bot_id == 6
        assert config.ai_model == "gemini-2.5-pro"
    
    def test_bot_1_config_symbols(self):
        """Test: Configuración incluye símbolos correctos."""
        config = get_bot_1_config()
        
        assert len(config.symbols) == 5
        assert "EURUSD" in config.symbols
        assert "GBPUSD" in config.symbols
        assert "USDCAD" in config.symbols
        assert "USDCHF" in config.symbols
        assert "XAUUSD" in config.symbols
    
    def test_bot_1_config_timeframes(self):
        """Test: Configuración incluye timeframes correctos para INTRADAY."""
        config = get_bot_1_config()
        
        assert len(config.timeframes) == 4
        assert Timeframe.M1 in config.timeframes
        assert Timeframe.M5 in config.timeframes
        assert Timeframe.M15 in config.timeframes
        assert Timeframe.H1 in config.timeframes
    
    def test_bot_1_settings_structure(self):
        """Test: BOT_1_SETTINGS tiene estructura correcta."""
        assert "nombre_corto" in BOT_1_SETTINGS
        assert "descripcion" in BOT_1_SETTINGS
        assert "version" in BOT_1_SETTINGS
        assert "estrategia" in BOT_1_SETTINGS
        
        assert BOT_1_SETTINGS["nombre_corto"] == "B1_INTRADAY_2.5"
        assert BOT_1_SETTINGS["estrategia"] == "INTRADAY"
        assert BOT_1_SETTINGS["version"] == "1.0.0"
    
    def test_bot_1_settings_gemini_config(self):
        """Test: BOT_1_SETTINGS contiene configuración de Gemini 2.5 Pro."""
        gemini_cfg = BOT_1_SETTINGS["gemini_config"]
        
        assert gemini_cfg["thinking_level"] == "HIGH"
        assert gemini_cfg["code_execution"] is True
        assert gemini_cfg["media_resolution"] == "high"
        assert gemini_cfg["temperature"] == 0.7
        assert gemini_cfg["max_output_tokens"] == 24576
    
    def test_bot_1_settings_execution_config(self):
        """Test: BOT_1_SETTINGS contiene configuración de ejecución correcta."""
        exec_cfg = BOT_1_SETTINGS["execution_config"]
        
        assert exec_cfg["confirm_signals"] is False
        assert exec_cfg["use_market_orders"] is True
        assert exec_cfg["use_dual_orders"] is False
        assert exec_cfg["max_slippage_pips"] == 5.0
    
    def test_bot_1_settings_indicators(self):
        """Test: BOT_1_SETTINGS define indicadores tácticos y estratégicos."""
        indicators = BOT_1_SETTINGS["indicators"]
        
        assert "tactical" in indicators
        assert "strategic" in indicators
        
        # Validar paquete táctico (M15)
        tactical = indicators["tactical"]
        assert tactical["timeframe"] == "M15"
        assert tactical["candles"] == 200
        assert len(tactical["indicators"]) > 0
        
        # Validar paquete estratégico (D1)
        strategic = indicators["strategic"]
        assert strategic["timeframe"] == "D1"
        assert strategic["candles"] == 30
        assert strategic["exclude_current_day"] is True
    
    def test_bot_1_config_trading_hours(self):
        """Test: Configuración tiene horarios de trading correctos."""
        config = get_bot_1_config()
        
        assert config.trading_hours == ("00:00", "23:59")
        assert config.timezone_local == "America/Lima"
    
    def test_bot_1_config_reevaluation_interval(self):
        """Test: Configuración tiene intervalo de reevaluación correcto."""
        config = get_bot_1_config()
        
        assert config.reevaluation_interval_minutes == 10
