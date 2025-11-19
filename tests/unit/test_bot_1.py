"""
Tests para Bot 1 - Numérico Baseline

Valida la funcionalidad básica de Bot 1 incluyendo:
- Inicialización correcta
- Preparación de datos para IA
- Parsing de respuestas
- Gestión de horarios

Author: Botrading Team
Date: 2025-11-17
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, time

from src.bots.bot_1.config import get_bot_1_config, BOT_1_SETTINGS
from src.bots.bot_1.strategy import Bot1Strategy
from src.bots.base.base_bot_operations import BotMode
from src.core.vwap_prompt_builder import MarketContext
from src.core.mt5_data_extractor import Timeframe


class TestBot1Config:
    """Tests para configuración de Bot 1"""
    
    def test_get_bot_1_config_demo(self):
        """Test configuración en modo demo"""
        config = get_bot_1_config(mode=BotMode.DEMO)
        
        assert config.bot_id == 1
        assert config.bot_name == "Numérico Baseline"
        assert config.bot_type == "numerico"
        assert config.mode == BotMode.DEMO
        assert "EURUSD" in config.symbols
        assert config.risk_per_trade == 0.5
        assert config.enable_dual_orders is True
    
    def test_get_bot_1_config_live(self):
        """Test configuración en modo live"""
        config = get_bot_1_config(mode=BotMode.LIVE)
        
        assert config.mode == BotMode.LIVE
        # Resto de configuración debe ser igual
        assert config.bot_id == 1
        assert config.bot_type == "numerico"
    
    def test_bot_1_settings(self):
        """Test settings adicionales de Bot 1"""
        assert BOT_1_SETTINGS['nombre_corto'] == "B1_NumBase"
        assert BOT_1_SETTINGS['version'] == "1.0.0"
        assert BOT_1_SETTINGS['prompt_config']['use_vwap_methodology'] is True


class TestBot1Strategy:
    """Tests para estrategia de Bot 1"""
    
    @pytest.fixture
    def bot_config(self):
        """Fixture de configuración"""
        return get_bot_1_config(mode=BotMode.DEMO)
    
    @pytest.fixture
    def bot(self, bot_config):
        """Fixture de bot"""
        return Bot1Strategy(bot_config)
    
    def test_bot_initialization(self, bot):
        """Test inicialización básica"""
        assert bot.config.bot_id == 1
        assert bot.config.bot_name == "Numérico Baseline"
        assert bot.is_initialized is False
    
    def test_is_trading_hours_within_range(self, bot):
        """Test validación de horarios dentro del rango"""
        # Mock datetime para estar dentro de horario (10:00 Lima)
        with patch('src.bots.base.base_bot_operations.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 17, 10, 0)
            
            result = bot.is_trading_hours()
            assert result is True
    
    def test_is_trading_hours_outside_range(self, bot):
        """Test validación de horarios fuera del rango"""
        # Mock datetime para estar fuera de horario (14:00 Lima)
        with patch('src.bots.base.base_bot_operations.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 11, 17, 14, 0)
            
            result = bot.is_trading_hours()
            assert result is False
    
    def test_should_stop_trading_negative_pnl(self, bot):
        """Test detención por pérdida máxima"""
        bot.current_pnl_r = -2.5
        bot.config.max_daily_risk = 2.0
        
        result = bot.should_stop_trading_today()
        assert result is True
    
    def test_should_not_stop_trading_normal_pnl(self, bot):
        """Test continuar trading con PnL normal"""
        bot.current_pnl_r = -1.0
        bot.config.max_daily_risk = 2.0
        
        result = bot.should_stop_trading_today()
        assert result is False
    
    def test_get_market_context_pre_market(self, bot):
        """Test determinación de contexto pre-market"""
        with patch('src.bots.base.base_bot_operations.datetime') as mock_datetime:
            # 07:00 GMT (antes de sesión)
            mock_datetime.utcnow.return_value = datetime(2025, 11, 17, 7, 0)
            
            context = bot.get_market_context()
            assert context == MarketContext.PRE_MARKET
    
    def test_get_market_context_european_session(self, bot):
        """Test determinación de contexto sesión europea"""
        with patch('src.bots.base.base_bot_operations.datetime') as mock_datetime:
            # 10:00 GMT (sesión europea)
            mock_datetime.utcnow.return_value = datetime(2025, 11, 17, 10, 0)
            
            context = bot.get_market_context()
            assert context == MarketContext.EUROPEAN_SESSION
    
    @patch('src.bots.bot_1.strategy.Bot1Strategy.prompt_builder')
    def test_prepare_data_for_ai(self, mock_prompt_builder, bot):
        """Test preparación de datos para IA"""
        # Mock del prompt builder
        bot.prompt_builder = MagicMock()
        bot.prompt_builder.build_vwap_methodology_prompt.return_value = (
            "System Prompt Test",
            "User Prompt Test"
        )
        
        # Datos de prueba
        indicators = {Timeframe.M5: Mock()}
        or_data = Mock()
        market_context = MarketContext.EUROPEAN_SESSION
        
        # Ejecutar
        system_prompt, user_prompt = bot.prepare_data_for_ai(
            symbol="EURUSD",
            indicators=indicators,
            or_data=or_data,
            market_context=market_context
        )
        
        # Verificar
        assert system_prompt == "System Prompt Test"
        assert user_prompt == "User Prompt Test"
        bot.prompt_builder.build_vwap_methodology_prompt.assert_called_once()
    
    @patch('src.bots.bot_1.strategy.Bot1Strategy.response_parser')
    def test_parse_ai_response_valid(self, mock_parser, bot):
        """Test parsing de respuesta válida"""
        # Mock del parser
        bot.response_parser = MagicMock()
        bot.response_parser.parse_response.return_value = Mock()
        bot.response_parser.convert_to_bot_format.return_value = {
            'accion': 'OPERAR',
            'direccion': 'BUY',
            'precio_entrada': 1.1050
        }
        
        # Ejecutar
        result = bot.parse_ai_response("Respuesta de prueba")
        
        # Verificar
        assert result['accion'] == 'OPERAR'
        assert result['direccion'] == 'BUY'
    
    def test_get_performance_metrics(self, bot):
        """Test obtención de métricas"""
        bot.current_pnl_r = 1.5
        bot.trades_today = 3
        
        metrics = bot.get_performance_metrics()
        
        assert metrics['bot_id'] == 1
        assert metrics['bot_name'] == "Numérico Baseline"
        assert metrics['current_pnl_r'] == 1.5
        assert metrics['trades_today'] == 3
        assert 'timestamp' in metrics


class TestBot1Integration:
    """Tests de integración para Bot 1"""
    
    @pytest.fixture
    def bot_config(self):
        """Fixture de configuración"""
        return get_bot_1_config(mode=BotMode.DEMO)
    
    @pytest.fixture
    def bot(self, bot_config):
        """Fixture de bot"""
        return Bot1Strategy(bot_config)
    
    @patch('src.bots.base.base_bot_operations.create_connector_from_credentials')
    @patch('src.bots.base.base_bot_operations.MT5DataExtractor')
    @patch('src.bots.base.base_bot_operations.VertexAIClient')
    def test_full_initialization(
        self,
        mock_vertex,
        mock_extractor,
        mock_connector_factory,
        bot
    ):
        """Test inicialización completa con mocks"""
        # Mock factory de connector y verificación exitosa
        mock_connector = MagicMock()
        mock_connector.verify_connection.return_value = True
        mock_connector_factory.return_value = mock_connector
        
        # Inicializar
        result = bot.initialize()
        
        # Verificar
        assert result is True
        assert bot.is_initialized is True
        mock_connector_factory.assert_called_once()
        mock_connector.verify_connection.assert_called_once()
    
    @patch('src.bots.base.base_bot_operations.create_connector_from_credentials')
    def test_initialization_failure(self, mock_connector_factory, bot):
        """Test fallo en inicialización"""
        # Mock verificación fallida
        mock_connector = MagicMock()
        mock_connector.verify_connection.side_effect = Exception("Fallo de conexión")
        mock_connector_factory.return_value = mock_connector
        
        # Inicializar
        result = bot.initialize()
        
        # Verificar
        assert result is False
        assert bot.is_initialized is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
