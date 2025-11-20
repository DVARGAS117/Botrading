"""Tests para la estrategia del Bot 1 INTRADAY."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.core.vwap_prompt_builder import MarketContext
from src.core.mt5_data_extractor import Timeframe


@pytest.fixture
def bot_config():
    """Fixture: Configuración base del bot."""
    return BotConfig(
        bot_id=101,
        bot_name="INTRADAY Baseline",
        bot_type="intraday",
        mode=BotMode.DEMO,
        symbols=["EURUSD"],
        timeframes=[Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.H1],
        trading_hours=("08:00", "16:00"),
        risk_per_trade=1.0,
        max_daily_risk=3.0,
        ai_model="gemini-3-pro-preview",
        enable_dual_orders=False,  # INTRADAY: sin dual orders
    )


class TestIntradayBot1Strategy:
    """Tests para IntradayBot1Strategy."""

    @patch("src.bots.base.base_bot_operations.get_bot_logger")
    def test_init_strategy(self, mock_logger, bot_config):
        """Test: Inicialización de la estrategia."""
        strategy = IntradayBot1Strategy(bot_config)

        assert strategy.config.bot_id == 101
        assert strategy.config.bot_name == "INTRADAY Baseline"
        assert strategy.config.bot_type == "intraday"

    @patch("src.bots.base.base_bot_operations.get_bot_logger")
    def test_prepare_data_for_ai_success(self, mock_logger, bot_config):
        """Test: Preparación de datos para IA exitosa (placeholder)."""
        strategy = IntradayBot1Strategy(bot_config)

        indicators = {"ema_20": 1.1000, "rsi": 55.0}
        market_context = MarketContext.EUROPEAN_SESSION

        system_prompt, user_prompt = strategy.prepare_data_for_ai(
            symbol="EURUSD",
            indicators=indicators,
            or_data=None,
            market_context=market_context,
            ohlcv_data=None,
        )

        # Verificar que retorna prompts (placeholder)
        assert isinstance(system_prompt, str)
        assert isinstance(user_prompt, str)
        assert len(system_prompt) > 0
        assert len(user_prompt) > 0
        assert "EURUSD" in system_prompt or "EURUSD" in user_prompt

    @patch("src.bots.base.base_bot_operations.get_bot_logger")
    def test_parse_ai_response_placeholder(self, mock_logger, bot_config):
        """Test: Parseo de respuesta IA (placeholder)."""
        strategy = IntradayBot1Strategy(bot_config)

        response_text = "Test AI response"
        result = strategy.parse_ai_response(response_text)

        # Por ahora debe retornar NO_OPERAR (placeholder)
        assert result["accion"] == "NO_OPERAR"
        assert "placeholder" in result["razonamiento"].lower() or "pendiente" in result["razonamiento"].lower()

    @patch("src.bots.base.base_bot_operations.get_bot_logger")
    @patch("src.bots.base.base_bot_operations.datetime")
    def test_get_performance_metrics(self, mock_datetime, mock_logger, bot_config):
        """Test: Obtención de métricas de rendimiento."""
        # Mock datetime
        mock_now = datetime(2025, 11, 19, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        strategy = IntradayBot1Strategy(bot_config)
        strategy.current_pnl_r = 1.5
        strategy.trades_today = 3

        # Mock métodos de BaseBotOperations
        strategy.is_trading_hours = Mock(return_value=True)
        strategy.should_stop_trading_today = Mock(return_value=False)
        strategy.get_market_context = Mock(return_value=MarketContext.EUROPEAN_SESSION)

        metrics = strategy.get_performance_metrics()

        assert metrics["bot_id"] == 101
        assert metrics["bot_name"] == "INTRADAY Baseline"
        assert metrics["strategy"] == "INTRADAY"
        assert metrics["current_pnl_r"] == 1.5
        assert metrics["trades_today"] == 3
        assert metrics["is_trading_hours"] is True
        assert metrics["should_stop"] is False
        assert metrics["market_context"] == "european_session"

    @patch("src.bots.base.base_bot_operations.get_bot_logger")
    def test_analyze_intraday_levels_placeholder(self, mock_logger, bot_config):
        """Test: Análisis de niveles intraday (placeholder)."""
        strategy = IntradayBot1Strategy(bot_config)

        ohlcv_data = {"M5": [], "H1": []}
        levels = strategy.analyze_intraday_levels(ohlcv_data)

        # Por ahora es placeholder, debe retornar estructura vacía
        assert "support_levels" in levels
        assert "resistance_levels" in levels
        assert "pivot_points" in levels
        assert isinstance(levels["support_levels"], list)
        assert isinstance(levels["resistance_levels"], list)

    @patch("src.bots.base.base_bot_operations.get_bot_logger")
    def test_calculate_intraday_volatility_placeholder(self, mock_logger, bot_config):
        """Test: Cálculo de volatilidad intraday (placeholder)."""
        strategy = IntradayBot1Strategy(bot_config)

        ohlcv_data = {"M5": [], "H1": []}
        volatility = strategy.calculate_intraday_volatility(ohlcv_data)

        # Por ahora es placeholder, debe retornar 0.0
        assert volatility == 0.0
        assert isinstance(volatility, float)

    @patch("src.bots.base.base_bot_operations.get_bot_logger")
    def test_strategy_inherits_from_base(self, mock_logger, bot_config):
        """Test: La estrategia hereda correctamente de BaseBotOperations."""
        from src.bots.base.base_bot_operations import BaseBotOperations

        strategy = IntradayBot1Strategy(bot_config)

        assert isinstance(strategy, BaseBotOperations)
        assert hasattr(strategy, "initialize")
        assert hasattr(strategy, "run_trading_cycle")
        assert hasattr(strategy, "run_continuous")
