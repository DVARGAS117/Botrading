"""
Tests para PromptBuilder - T10
Construcción de prompts específicos por tipo de bot para consultas a IA

Funcionalidades a testear:
- Construcción de prompts numéricos
- Construcción de prompts visuales
- Construcción de prompts híbridos
- Prompts de evaluación inicial
- Prompts de reevaluación
- Validación de plantillas
- Configuración personalizada

Author: Botrading Team
Date: 2025-11-13
"""

import pytest
from datetime import datetime
from src.core.prompt_builder import (
    PromptBuilder,
    BotType,
    PromptType,
    PromptData,
    PromptTemplate,
    PromptBuilderError
)


class TestBotType:
    """Tests para el enum BotType"""
    
    def test_bot_type_values(self):
        """Verificar que BotType tiene los valores correctos"""
        assert BotType.NUMERICO.value == "numerico"
        assert BotType.VISUAL.value == "visual"
        assert BotType.HIBRIDO.value == "hibrido"
    
    def test_bot_type_from_string(self):
        """Verificar conversión de string a BotType"""
        assert BotType.from_string("numerico") == BotType.NUMERICO
        assert BotType.from_string("NUMERICO") == BotType.NUMERICO
        assert BotType.from_string("visual") == BotType.VISUAL
        assert BotType.from_string("hibrido") == BotType.HIBRIDO
    
    def test_bot_type_from_string_invalid(self):
        """Verificar error con tipo inválido"""
        with pytest.raises(ValueError, match="Tipo de bot inválido"):
            BotType.from_string("invalido")


class TestPromptType:
    """Tests para el enum PromptType"""
    
    def test_prompt_type_values(self):
        """Verificar que PromptType tiene los valores correctos"""
        assert PromptType.EVALUACION.value == "evaluacion"
        assert PromptType.REEVALUACION.value == "reevaluacion"
    
    def test_prompt_type_from_string(self):
        """Verificar conversión de string a PromptType"""
        assert PromptType.from_string("evaluacion") == PromptType.EVALUACION
        assert PromptType.from_string("EVALUACION") == PromptType.EVALUACION
        assert PromptType.from_string("reevaluacion") == PromptType.REEVALUACION


class TestPromptData:
    """Tests para la dataclass PromptData"""
    
    def test_prompt_data_creation_numeric(self):
        """Verificar creación de PromptData numérico"""
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={
                "ema_20": 1.2345,
                "ema_50": 1.2340,
                "rsi": 65.5,
                "macd": 0.0012
            },
            current_price=1.2350
        )
        
        assert data.symbol == "EURUSD"
        assert data.timeframe == "5M"
        assert data.indicators["ema_20"] == 1.2345
        assert data.current_price == 1.2350
        assert data.image_paths is None
    
    def test_prompt_data_creation_visual(self):
        """Verificar creación de PromptData visual"""
        data = PromptData(
            symbol="GBPUSD",
            timeframe="15M",
            image_paths=["/path/to/chart_5m.png", "/path/to/chart_15m.png"],
            current_price=1.3500
        )
        
        assert data.symbol == "GBPUSD"
        assert data.image_paths == ["/path/to/chart_5m.png", "/path/to/chart_15m.png"]
        assert data.indicators is None
    
    def test_prompt_data_creation_hybrid(self):
        """Verificar creación de PromptData híbrido"""
        data = PromptData(
            symbol="USDJPY",
            timeframe="1H",
            indicators={"rsi": 70.0, "macd": 0.005},
            image_paths=["/path/to/chart.png"],
            current_price=150.50
        )
        
        assert data.indicators is not None
        assert data.image_paths is not None
        assert len(data.image_paths) == 1
    
    def test_prompt_data_to_dict(self):
        """Verificar conversión a diccionario"""
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0},
            current_price=1.2350
        )
        
        result = data.to_dict()
        assert result["symbol"] == "EURUSD"
        assert result["indicators"]["rsi"] == 65.0


class TestPromptTemplate:
    """Tests para la clase PromptTemplate"""
    
    def test_template_creation(self):
        """Verificar creación de template"""
        template = PromptTemplate(
            name="test_template",
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            template_text="Analiza {symbol} en {timeframe}"
        )
        
        assert template.name == "test_template"
        assert template.bot_type == BotType.NUMERICO
        assert template.prompt_type == PromptType.EVALUACION
    
    def test_template_render_basic(self):
        """Verificar renderizado básico"""
        template = PromptTemplate(
            name="basic",
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            template_text="Símbolo: {symbol}, Precio: {current_price}"
        )
        
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            current_price=1.2350
        )
        
        result = template.render(data)
        assert "Símbolo: EURUSD" in result
        assert "Precio: 1.2350" in result
    
    def test_template_render_with_indicators(self):
        """Verificar renderizado con indicadores"""
        template = PromptTemplate(
            name="with_indicators",
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            template_text="RSI: {indicators[rsi]}, MACD: {indicators[macd]}"
        )
        
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.5, "macd": 0.0012},
            current_price=1.2350
        )
        
        result = template.render(data)
        assert "RSI: 65.5" in result
        assert "MACD: 0.0012" in result


class TestPromptBuilder:
    """Tests para la clase PromptBuilder principal"""
    
    @pytest.fixture
    def builder(self):
        """Fixture que retorna un PromptBuilder configurado"""
        config = {
            "prompt_templates": {
                "numerico_evaluacion": {
                    "bot_type": "numerico",
                    "prompt_type": "evaluacion",
                    "template": "Analiza {symbol} con RSI: {indicators[rsi]}"
                },
                "visual_evaluacion": {
                    "bot_type": "visual",
                    "prompt_type": "evaluacion",
                    "template": "Analiza las imágenes de {symbol}"
                }
            }
        }
        return PromptBuilder(config=config)
    
    def test_builder_initialization(self, builder):
        """Verificar inicialización correcta"""
        assert builder is not None
        assert len(builder.templates) >= 2
    
    def test_builder_get_template(self, builder):
        """Verificar obtención de template"""
        template = builder.get_template(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION
        )
        assert template is not None
        assert template.bot_type == BotType.NUMERICO
    
    def test_builder_build_numeric_evaluation_prompt(self, builder):
        """Verificar construcción de prompt numérico de evaluación"""
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={
                "rsi": 65.5,
                "ema_20": 1.2345,
                "ema_50": 1.2340,
                "macd": 0.0012,
                "volume": 15000
            },
            current_price=1.2350
        )
        
        prompt = builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        
        assert "EURUSD" in prompt
        assert "65.5" in prompt or "rsi" in prompt.lower()
        assert len(prompt) > 50  # Debe ser un prompt sustancial
    
    def test_builder_build_visual_evaluation_prompt(self, builder):
        """Verificar construcción de prompt visual de evaluación"""
        data = PromptData(
            symbol="GBPUSD",
            timeframe="15M",
            image_paths=["/path/chart_5m.png", "/path/chart_15m.png"],
            current_price=1.3500
        )
        
        prompt = builder.build_prompt(
            bot_type=BotType.VISUAL,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        
        assert "GBPUSD" in prompt
        assert len(prompt) > 30
    
    def test_builder_build_hybrid_evaluation_prompt(self, builder):
        """Verificar construcción de prompt híbrido de evaluación"""
        data = PromptData(
            symbol="USDJPY",
            timeframe="1H",
            indicators={"rsi": 70.0, "macd": 0.005},
            image_paths=["/path/chart.png"],
            current_price=150.50
        )
        
        # Para híbrido, necesitamos configurar el template
        builder.add_template(
            name="hibrido_evaluacion",
            bot_type=BotType.HIBRIDO,
            prompt_type=PromptType.EVALUACION,
            template_text="Analiza {symbol} con datos e imágenes"
        )
        
        prompt = builder.build_prompt(
            bot_type=BotType.HIBRIDO,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        
        assert "USDJPY" in prompt
    
    def test_builder_build_reevaluation_prompt(self, builder):
        """Verificar construcción de prompt de reevaluación"""
        builder.add_template(
            name="numerico_reevaluacion",
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.REEVALUACION,
            template_text="Reevalúa la posición en {symbol}"
        )
        
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 50.0},
            current_price=1.2360,
            position_data={
                "entry_price": 1.2350,
                "stop_loss": 1.2300,
                "take_profit": 1.2500,
                "current_pnl": 10.0
            }
        )
        
        prompt = builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.REEVALUACION,
            data=data
        )
        
        assert "EURUSD" in prompt
    
    def test_builder_add_template(self, builder):
        """Verificar adición de nuevo template"""
        initial_count = len(builder.templates)
        
        builder.add_template(
            name="custom_template",
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            template_text="Custom: {symbol}"
        )
        
        assert len(builder.templates) == initial_count + 1
        template = builder.get_template(BotType.NUMERICO, PromptType.EVALUACION)
        assert template.name == "custom_template"
    
    def test_builder_missing_template(self, builder):
        """Verificar error cuando no existe template"""
        with pytest.raises(PromptBuilderError, match="No se encontró template"):
            builder.build_prompt(
                bot_type=BotType.HIBRIDO,
                prompt_type=PromptType.REEVALUACION,
                data=PromptData(symbol="TEST", timeframe="5M", current_price=1.0)
            )
    
    def test_builder_validate_data_numeric(self, builder):
        """Verificar validación de datos numéricos"""
        # Datos válidos
        valid_data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0},
            current_price=1.2350
        )
        assert builder.validate_data(BotType.NUMERICO, valid_data) is True
        
        # Datos inválidos (sin indicadores)
        invalid_data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            current_price=1.2350
        )
        assert builder.validate_data(BotType.NUMERICO, invalid_data) is False
    
    def test_builder_validate_data_visual(self, builder):
        """Verificar validación de datos visuales"""
        # Datos válidos
        valid_data = PromptData(
            symbol="GBPUSD",
            timeframe="15M",
            image_paths=["/path/chart.png"],
            current_price=1.3500
        )
        assert builder.validate_data(BotType.VISUAL, valid_data) is True
        
        # Datos inválidos (sin imágenes)
        invalid_data = PromptData(
            symbol="GBPUSD",
            timeframe="15M",
            current_price=1.3500
        )
        assert builder.validate_data(BotType.VISUAL, invalid_data) is False
    
    def test_builder_validate_data_hybrid(self, builder):
        """Verificar validación de datos híbridos"""
        # Datos válidos
        valid_data = PromptData(
            symbol="USDJPY",
            timeframe="1H",
            indicators={"rsi": 70.0},
            image_paths=["/path/chart.png"],
            current_price=150.50
        )
        assert builder.validate_data(BotType.HIBRIDO, valid_data) is True
        
        # Datos inválidos (falta alguno de los dos)
        invalid_data = PromptData(
            symbol="USDJPY",
            timeframe="1H",
            indicators={"rsi": 70.0},
            current_price=150.50
        )
        assert builder.validate_data(BotType.HIBRIDO, invalid_data) is False
    
    def test_builder_format_json_instructions(self, builder):
        """Verificar inclusión de instrucciones de formato JSON"""
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0},
            current_price=1.2350
        )
        
        prompt = builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data,
            include_json_instructions=True
        )
        
        # Debe incluir instrucciones sobre formato JSON
        assert "JSON" in prompt.upper()
        assert "OPERAR" in prompt or "NO_OPERAR" in prompt
    
    def test_builder_multiple_timeframes(self, builder):
        """Verificar construcción de prompt con múltiples timeframes"""
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
        
        prompt = builder.build_multi_timeframe_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            timeframe_data=[data_5m, data_15m, data_1h]
        )
        
        assert "5M" in prompt
        assert "15M" in prompt
        assert "1H" in prompt
        assert "EURUSD" in prompt
    
    def test_builder_custom_variables(self, builder):
        """Verificar sustitución de variables personalizadas"""
        builder.add_template(
            name="custom_vars",
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            template_text="Bot: {bot_name}, Hora: {timestamp}"
        )
        
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0},
            current_price=1.2350
        )
        
        prompt = builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data,
            custom_vars={
                "bot_name": "Bot_1",
                "timestamp": "2025-11-13 10:00:00"
            }
        )
        
        assert "Bot_1" in prompt
        assert "2025-11-13 10:00:00" in prompt


class TestPromptBuilderEdgeCases:
    """Tests para casos borde y manejo de errores"""
    
    def test_empty_config(self):
        """Verificar comportamiento con configuración vacía"""
        builder = PromptBuilder(config={})
        # Debe usar templates por defecto
        assert len(builder.templates) > 0
    
    def test_missing_required_field_in_data(self):
        """Verificar error cuando falta campo requerido"""
        builder = PromptBuilder()
        
        # Data sin symbol (requerido)
        invalid_data = PromptData(
            symbol=None,
            timeframe="5M",
            current_price=1.2350
        )
        
        with pytest.raises(PromptBuilderError, match="Campo requerido"):
            builder.build_prompt(
                bot_type=BotType.NUMERICO,
                prompt_type=PromptType.EVALUACION,
                data=invalid_data
            )
    
    def test_template_with_missing_variable(self):
        """Verificar manejo de variable faltante en template"""
        builder = PromptBuilder()
        builder.add_template(
            name="missing_var",
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            template_text="Símbolo: {symbol}, Inexistente: {inexistente}"
        )
        
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0},
            current_price=1.2350
        )
        
        # Debe manejar variable faltante gracefully o lanzar error
        with pytest.raises((PromptBuilderError, KeyError)):
            builder.build_prompt(
                bot_type=BotType.NUMERICO,
                prompt_type=PromptType.EVALUACION,
                data=data
            )
    
    def test_extremely_long_prompt(self):
        """Verificar manejo de prompts muy largos"""
        builder = PromptBuilder()
        
        # Crear data con muchos indicadores
        indicators = {f"indicator_{i}": i * 1.5 for i in range(100)}
        
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators=indicators,
            current_price=1.2350
        )
        
        prompt = builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        
        # Debe generar prompt sin error
        assert len(prompt) > 0
        assert "EURUSD" in prompt
