"""
Tests de Integración para IA - T10
Prueba el flujo completo: PromptBuilder → GeminiClient → AIResponseParser

Este módulo prueba la integración entre los componentes principales
del sistema de IA, asegurando que trabajen correctamente juntos.

Funcionalidades a testear:
- Flujo completo de evaluación inicial
- Flujo completo de reevaluación
- Manejo de errores end-to-end
- Integración con configuración
- Tracking de tokens y costos

Author: Botrading Team
Date: 2025-11-13
"""

import pytest
from unittest.mock import Mock, patch
from src.core.prompt_builder import (
    PromptBuilder,
    PromptData,
    BotType,
    PromptType
)
from src.core.gemini_client import (
    GeminiClient,
    GeminiConfig,
    GeminiResponse
)
from src.core.ai_response_parser import (
    AIResponseParser,
    ParsedDecision,
    AIDecisionType
)


class TestIAIntegrationEvaluacion:
    """Tests de integración para flujo de evaluación inicial"""
    
    @pytest.fixture
    def prompt_builder(self):
        """Fixture que retorna un PromptBuilder"""
        return PromptBuilder()
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Fixture que retorna un GeminiClient mockeado"""
        with patch('src.core.gemini_client.genai'):
            config = GeminiConfig(model="gemini-2.5-pro")
            client = GeminiClient(api_key="test_api_key", config=config)
            return client
    
    @pytest.fixture
    def ai_parser(self):
        """Fixture que retorna un AIResponseParser"""
        return AIResponseParser()
    
    def test_full_flow_numeric_evaluation_operar(
        self,
        prompt_builder,
        mock_gemini_client,
        ai_parser
    ):
        """Prueba flujo completo: datos numéricos → prompt → IA → parseo (OPERAR)"""
        
        # 1. Preparar datos
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={
                "rsi": 65.0,
                "ema_20": 1.2345,
                "ema_50": 1.2340,
                "macd": 0.0012,
                "volume": 15000
            },
            current_price=1.2350
        )
        
        # 2. Construir prompt
        prompt = prompt_builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data,
            include_json_instructions=True
        )
        
        assert "EURUSD" in prompt
        assert "RSI: 65.0" in prompt or "rsi" in prompt.lower()
        assert "JSON" in prompt
        
        # 3. Simular respuesta de IA (OPERAR)
        mock_response_text = """{
            "accion": "OPERAR",
            "direccion": "BUY",
            "tipo_orden": "MARKET",
            "stop_loss": 1.2300,
            "take_profit": 1.2500,
            "riesgo_porcentaje": 2.0,
            "razonamiento": "RSI indica momentum alcista, cruce de EMAs confirmado"
        }"""
        
        # Mock de la respuesta del cliente
        with patch.object(mock_gemini_client, 'send_prompt') as mock_send:
            mock_send.return_value = GeminiResponse(
                success=True,
                content=mock_response_text,
                tokens_input=500,
                tokens_output=100,
                cost=0.05
            )
            
            gemini_response = mock_gemini_client.send_prompt(prompt)
        
        assert gemini_response.success is True
        assert gemini_response.content is not None
        
        # 4. Parsear respuesta
        parsed = ai_parser.parse_evaluation(gemini_response.content)
        
        assert parsed.is_valid is True
        assert parsed.decision_type == AIDecisionType.OPERAR
        assert parsed.direction.value == "BUY"
        assert parsed.stop_loss == 1.2300
        assert parsed.take_profit == 1.2500
        assert parsed.risk_percentage == 2.0
    
    def test_full_flow_numeric_evaluation_no_operar(
        self,
        prompt_builder,
        mock_gemini_client,
        ai_parser
    ):
        """Prueba flujo completo: datos numéricos → prompt → IA → parseo (NO_OPERAR)"""
        
        # 1. Preparar datos
        data = PromptData(
            symbol="GBPUSD",
            timeframe="15M",
            indicators={
                "rsi": 50.0,
                "ema_20": 1.3500,
                "ema_50": 1.3500
            },
            current_price=1.3505
        )
        
        # 2. Construir prompt
        prompt = prompt_builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        
        # 3. Simular respuesta de IA (NO_OPERAR)
        mock_response_text = """{
            "accion": "NO_OPERAR",
            "razonamiento": "Mercado lateral, RSI neutral, sin señal clara"
        }"""
        
        with patch.object(mock_gemini_client, 'send_prompt') as mock_send:
            mock_send.return_value = GeminiResponse(
                success=True,
                content=mock_response_text,
                tokens_input=450,
                tokens_output=50,
                cost=0.03
            )
            
            gemini_response = mock_gemini_client.send_prompt(prompt)
        
        # 4. Parsear respuesta
        parsed = ai_parser.parse_evaluation(gemini_response.content)
        
        assert parsed.is_valid is True
        assert parsed.decision_type == AIDecisionType.NO_OPERAR
        assert parsed.reasoning is not None
    
    def test_full_flow_visual_evaluation(
        self,
        prompt_builder,
        mock_gemini_client,
        ai_parser
    ):
        """Prueba flujo completo con datos visuales (imágenes)"""
        
        # 1. Preparar datos con imágenes
        data = PromptData(
            symbol="USDJPY",
            timeframe="1H",
            image_paths=["/path/chart_5m.png", "/path/chart_15m.png"],
            current_price=150.50
        )
        
        # 2. Construir prompt
        prompt = prompt_builder.build_prompt(
            bot_type=BotType.VISUAL,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        
        assert "USDJPY" in prompt
        
        # 3. Simular respuesta de IA
        mock_response_text = """{
            "accion": "OPERAR",
            "direccion": "SELL",
            "tipo_orden": "LIMIT",
            "precio_entrada": 150.80,
            "stop_loss": 151.20,
            "take_profit": 149.80,
            "riesgo_porcentaje": 1.5,
            "razonamiento": "Patrón de doble techo visible en gráfica, resistencia clara"
        }"""
        
        with patch.object(mock_gemini_client, 'send_prompt') as mock_send:
            mock_send.return_value = GeminiResponse(
                success=True,
                content=mock_response_text,
                tokens_input=600,
                tokens_output=120,
                cost=0.06
            )
            
            gemini_response = mock_gemini_client.send_prompt(
                prompt,
                image_paths=data.image_paths
            )
        
        # 4. Parsear respuesta
        parsed = ai_parser.parse_evaluation(gemini_response.content)
        
        assert parsed.is_valid is True
        assert parsed.decision_type == AIDecisionType.OPERAR
        assert parsed.direction.value == "SELL"
        assert parsed.order_type.value == "LIMIT"
        assert parsed.entry_price == 150.80


class TestIAIntegrationReevaluacion:
    """Tests de integración para flujo de reevaluación"""
    
    @pytest.fixture
    def prompt_builder(self):
        return PromptBuilder()
    
    @pytest.fixture
    def mock_gemini_client(self):
        with patch('src.core.gemini_client.genai'):
            config = GeminiConfig()
            return GeminiClient(api_key="test_api_key", config=config)
    
    @pytest.fixture
    def ai_parser(self):
        return AIResponseParser()
    
    def test_full_flow_reevaluation_mantener(
        self,
        prompt_builder,
        mock_gemini_client,
        ai_parser
    ):
        """Prueba flujo completo de reevaluación (MANTENER)"""
        
        # 1. Preparar datos con posición abierta
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 60.0, "macd": 0.0010},
            current_price=1.2380,
            position_data={
                "entry_price": 1.2350,
                "stop_loss": 1.2300,
                "take_profit": 1.2500,
                "current_pnl": 30.0,
                "direction": "BUY"
            }
        )
        
        # 2. Construir prompt de reevaluación
        prompt = prompt_builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.REEVALUACION,
            data=data
        )
        
        assert "reevalúa" in prompt.lower() or "posición" in prompt.lower()
        
        # 3. Simular respuesta de IA
        mock_response_text = """{
            "accion": "MANTENER",
            "razonamiento": "Operación en profit, tendencia sigue favorable, mantener posición"
        }"""
        
        with patch.object(mock_gemini_client, 'send_prompt') as mock_send:
            mock_send.return_value = GeminiResponse(
                success=True,
                content=mock_response_text,
                tokens_input=400,
                tokens_output=60,
                cost=0.04
            )
            
            gemini_response = mock_gemini_client.send_prompt(prompt)
        
        # 4. Parsear respuesta
        parsed = ai_parser.parse_reevaluation(gemini_response.content)
        
        assert parsed.is_valid is True
        assert parsed.decision_type == AIDecisionType.MANTENER
    
    def test_full_flow_reevaluation_actualizar(
        self,
        prompt_builder,
        mock_gemini_client,
        ai_parser
    ):
        """Prueba flujo completo de reevaluación (ACTUALIZAR)"""
        
        # 1. Preparar datos
        data = PromptData(
            symbol="GBPUSD",
            timeframe="15M",
            indicators={"rsi": 65.0},
            current_price=1.3550,
            position_data={
                "entry_price": 1.3500,
                "stop_loss": 1.3450,
                "take_profit": 1.3600,
                "current_pnl": 50.0
            }
        )
        
        # 2. Construir prompt
        prompt = prompt_builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.REEVALUACION,
            data=data
        )
        
        # 3. Simular respuesta de IA (ACTUALIZAR)
        mock_response_text = """{
            "accion": "ACTUALIZAR",
            "nuevo_stop_loss": 1.3520,
            "nuevo_take_profit": 1.3650,
            "razonamiento": "Mover SL a breakeven y extender TP por momentum fuerte"
        }"""
        
        with patch.object(mock_gemini_client, 'send_prompt') as mock_send:
            mock_send.return_value = GeminiResponse(
                success=True,
                content=mock_response_text,
                tokens_input=420,
                tokens_output=80,
                cost=0.045
            )
            
            gemini_response = mock_gemini_client.send_prompt(prompt)
        
        # 4. Parsear respuesta
        parsed = ai_parser.parse_reevaluation(gemini_response.content)
        
        assert parsed.is_valid is True
        assert parsed.decision_type == AIDecisionType.ACTUALIZAR
        assert parsed.new_stop_loss == 1.3520
        assert parsed.new_take_profit == 1.3650
    
    def test_full_flow_reevaluation_cerrar(
        self,
        prompt_builder,
        mock_gemini_client,
        ai_parser
    ):
        """Prueba flujo completo de reevaluación (CERRAR)"""
        
        # 1. Preparar datos
        data = PromptData(
            symbol="USDJPY",
            timeframe="1H",
            indicators={"rsi": 30.0, "macd": -0.005},
            current_price=149.80,
            position_data={
                "entry_price": 150.50,
                "stop_loss": 149.50,
                "take_profit": 151.50,
                "current_pnl": -70.0,
                "direction": "BUY"
            }
        )
        
        # 2. Construir prompt
        prompt = prompt_builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.REEVALUACION,
            data=data
        )
        
        # 3. Simular respuesta de IA (CERRAR)
        mock_response_text = """{
            "accion": "CERRAR",
            "razonamiento": "Señales de reversión confirmadas, RSI bajista, mejor cerrar ahora"
        }"""
        
        with patch.object(mock_gemini_client, 'send_prompt') as mock_send:
            mock_send.return_value = GeminiResponse(
                success=True,
                content=mock_response_text,
                tokens_input=410,
                tokens_output=65,
                cost=0.042
            )
            
            gemini_response = mock_gemini_client.send_prompt(prompt)
        
        # 4. Parsear respuesta
        parsed = ai_parser.parse_reevaluation(gemini_response.content)
        
        assert parsed.is_valid is True
        assert parsed.decision_type == AIDecisionType.CERRAR


class TestIAIntegrationErrorHandling:
    """Tests de integración para manejo de errores"""
    
    @pytest.fixture
    def prompt_builder(self):
        return PromptBuilder()
    
    @pytest.fixture
    def mock_gemini_client(self):
        with patch('src.core.gemini_client.genai'):
            return GeminiClient(api_key="test_api_key")
    
    @pytest.fixture
    def ai_parser(self):
        return AIResponseParser()
    
    def test_full_flow_with_invalid_json_response(
        self,
        prompt_builder,
        mock_gemini_client,
        ai_parser
    ):
        """Prueba manejo de respuesta JSON inválida"""
        
        # 1. Construir prompt válido
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0},
            current_price=1.2350
        )
        
        prompt = prompt_builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        
        # 2. Simular respuesta de IA con JSON inválido
        invalid_response = "Esta no es una respuesta JSON válida"
        
        with patch.object(mock_gemini_client, 'send_prompt') as mock_send:
            mock_send.return_value = GeminiResponse(
                success=True,
                content=invalid_response,
                tokens_input=500,
                tokens_output=100,
                cost=0.05
            )
            
            gemini_response = mock_gemini_client.send_prompt(prompt)
        
        # 3. Intentar parsear (debe manejar el error)
        parsed = ai_parser.safe_parse_evaluation(gemini_response.content)
        
        assert parsed.is_valid is False
        assert parsed.error_type == "json_decode_error"
    
    def test_full_flow_with_gemini_api_error(
        self,
        prompt_builder,
        mock_gemini_client,
        ai_parser
    ):
        """Prueba manejo de error de API de Gemini"""
        
        # 1. Construir prompt
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0},
            current_price=1.2350
        )
        
        prompt = prompt_builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        
        # 2. Simular error de API
        with patch.object(mock_gemini_client, 'send_prompt') as mock_send:
            mock_send.return_value = GeminiResponse(
                success=False,
                error_message="API rate limit exceeded",
                error_type="rate_limit"
            )
            
            gemini_response = mock_gemini_client.send_prompt(prompt)
        
        # 3. Verificar que se manejó el error
        assert gemini_response.success is False
        assert gemini_response.error_message is not None
        assert gemini_response.content is None
    
    def test_full_flow_with_missing_required_fields(
        self,
        prompt_builder,
        mock_gemini_client,
        ai_parser
    ):
        """Prueba manejo de respuesta con campos faltantes"""
        
        # 1. Construir prompt
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0},
            current_price=1.2350
        )
        
        prompt = prompt_builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        
        # 2. Simular respuesta incompleta (falta stop_loss)
        incomplete_response = """{
            "accion": "OPERAR",
            "direccion": "BUY",
            "take_profit": 1.2500,
            "riesgo_porcentaje": 2.0
        }"""
        
        with patch.object(mock_gemini_client, 'send_prompt') as mock_send:
            mock_send.return_value = GeminiResponse(
                success=True,
                content=incomplete_response,
                tokens_input=500,
                tokens_output=100,
                cost=0.05
            )
            
            gemini_response = mock_gemini_client.send_prompt(prompt)
        
        # 3. Intentar parsear (debe detectar campo faltante)
        parsed = ai_parser.safe_parse_evaluation(gemini_response.content)
        
        assert parsed.is_valid is False
        assert parsed.error_type == "missing_conditional_field"


class TestIAIntegrationMultiTimeframe:
    """Tests de integración con múltiples timeframes"""
    
    @pytest.fixture
    def prompt_builder(self):
        return PromptBuilder()
    
    def test_multi_timeframe_prompt_construction(self, prompt_builder):
        """Prueba construcción de prompt con múltiples timeframes"""
        
        # Preparar datos para 3 timeframes
        data_5m = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0, "ema_20": 1.2345},
            current_price=1.2350
        )
        
        data_15m = PromptData(
            symbol="EURUSD",
            timeframe="15M",
            indicators={"rsi": 60.0, "ema_20": 1.2340},
            current_price=1.2350
        )
        
        data_1h = PromptData(
            symbol="EURUSD",
            timeframe="1H",
            indicators={"rsi": 58.0, "ema_20": 1.2335},
            current_price=1.2350
        )
        
        # Construir prompt multi-timeframe
        prompt = prompt_builder.build_multi_timeframe_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            timeframe_data=[data_5m, data_15m, data_1h]
        )
        
        # Verificar que contiene información de todos los timeframes
        assert "5M" in prompt
        assert "15M" in prompt
        assert "1H" in prompt
        assert "EURUSD" in prompt
        assert "65.0" in prompt or "rsi" in prompt.lower()
