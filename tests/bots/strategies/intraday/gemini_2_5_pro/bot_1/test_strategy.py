"""Tests para estrategia del Bot 1 INTRADAY Gemini 2.5 Pro.

Este módulo prueba la lógica de la estrategia siguiendo metodología TDD.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.config import get_bot_1_config
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.strategy import IntradayBot1Strategy


class TestIntradayBot1Strategy:
    """Tests para IntradayBot1Strategy con Gemini 2.5 Pro."""
    
    @pytest.fixture
    def bot_config(self):
        """Fixture: Configuración del bot para tests."""
        return get_bot_1_config(mode=BotMode.DEMO)
    
    @pytest.fixture
    def mock_mt5_connection(self):
        """Fixture: Mock de conexión MT5."""
        mock = Mock()
        mock.initialize = Mock(return_value=True)
        mock.shutdown = Mock()
        return mock
    
    def test_bot_initialization_creates_instance(self, bot_config):
        """Test: IntradayBot1Strategy se inicializa correctamente."""
        bot = IntradayBot1Strategy(bot_config)
        
        assert bot is not None
        assert isinstance(bot, IntradayBot1Strategy)
        assert bot.config.bot_id == 106
        assert bot.config.ai_model == "gemini-2.5-pro"
    
    def test_bot_has_required_attributes(self, bot_config):
        """Test: Bot tiene atributos requeridos después de inicialización."""
        bot = IntradayBot1Strategy(bot_config)
        
        assert hasattr(bot, 'ia_query_repository')
        assert hasattr(bot, 'operations_repo')
        assert hasattr(bot, 'vertex_client')
        assert hasattr(bot, '_use_intraday_calculator')
        assert bot._use_intraday_calculator is True
    
    def test_bot_logger_is_configured(self, bot_config):
        """Test: Logger del bot está correctamente configurado."""
        bot = IntradayBot1Strategy(bot_config)
        
        assert bot.logger is not None
        assert hasattr(bot.logger, 'info')
        assert hasattr(bot.logger, 'error')
        assert hasattr(bot.logger, 'warning')
    
    def test_parse_ai_response_valid_comprar(self, bot_config):
        """Test: parse_ai_response parsea correctamente acción COMPRAR."""
        bot = IntradayBot1Strategy(bot_config)
        
        response = json.dumps({
            "accion": "COMPRAR",
            "razonamiento": "Tendencia alcista confirmada",
            "direccion": "LONG",
            "stop_loss": 1.05000,
            "take_profit": 1.05500,
            "confianza": 85.0,
            "estrategia_usada": "A",
            "diagnostico_mercado": "Mercado en tendencia alcista"
        })
        
        result = bot.parse_ai_response(response)
        
        assert result["accion"] == "COMPRAR"
        assert result["razonamiento"] == "Tendencia alcista confirmada"
        assert result["direccion"] == "LONG"
        assert result["stop_loss"] == 1.05000
        assert result["take_profit"] == 1.05500
        assert result["confianza"] == 85.0
    
    def test_parse_ai_response_valid_no_operar(self, bot_config):
        """Test: parse_ai_response parsea correctamente acción NO_OPERAR."""
        bot = IntradayBot1Strategy(bot_config)
        
        response = json.dumps({
            "accion": "NO_OPERAR",
            "razonamiento": "No hay setup claro",
            "direccion": None,
            "stop_loss": None,
            "take_profit": None,
            "confianza": 30.0
        })
        
        result = bot.parse_ai_response(response)
        
        assert result["accion"] == "NO_OPERAR"
        assert result["direccion"] is None
        assert result["stop_loss"] is None
    
    def test_parse_ai_response_invalid_json(self, bot_config):
        """Test: parse_ai_response lanza error con JSON inválido."""
        bot = IntradayBot1Strategy(bot_config)
        
        invalid_response = "esto no es json válido"
        
        with pytest.raises(ValueError, match="no es JSON válido"):
            bot.parse_ai_response(invalid_response)
    
    def test_parse_ai_response_missing_required_field(self, bot_config):
        """Test: parse_ai_response lanza error si falta campo requerido."""
        bot = IntradayBot1Strategy(bot_config)
        
        # JSON sin campo 'accion'
        response = json.dumps({
            "razonamiento": "Test",
            "direccion": "LONG"
        })
        
        with pytest.raises(ValueError, match="no contiene campo 'accion'"):
            bot.parse_ai_response(response)
    
    def test_parse_ai_response_invalid_action(self, bot_config):
        """Test: parse_ai_response lanza error con acción inválida."""
        bot = IntradayBot1Strategy(bot_config)
        
        response = json.dumps({
            "accion": "ACCION_INVALIDA",
            "razonamiento": "Test"
        })
        
        with pytest.raises(ValueError, match="Acción inválida"):
            bot.parse_ai_response(response)
    
    def test_bot_config_has_correct_model(self, bot_config):
        """Test: Configuración del bot tiene modelo correcto."""
        bot = IntradayBot1Strategy(bot_config)
        
        assert bot.config.ai_model == "gemini-2.5-pro"
    
    def test_bot_prompts_directory_exists(self, bot_config):
        """Test: Directorio de prompts está correctamente configurado."""
        bot = IntradayBot1Strategy(bot_config)
        
        assert hasattr(bot, 'prompts_dir')
        assert isinstance(bot.prompts_dir, Path)
        # El directorio debe apuntar a config/prompt_templates
        assert str(bot.prompts_dir).endswith('prompt_templates')
