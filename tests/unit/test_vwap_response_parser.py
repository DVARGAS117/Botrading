"""
Tests unitarios para VWAP Response Parser

Tests para parseo de respuestas de IA en metodología VWAP.
Extrae secciones estructuradas y convierte a formato ejecutable por el bot.

Autor: Sistema Botrading
Fecha: 2025-11-17
Ticket: VWAP Methodology - Response Parser
"""

import pytest
from src.core.vwap_response_parser import (
    VWAPResponseParser,
    ParsedResponse,
    TradingAction,
    Direction,
    ValidationError
)


class TestVWAPResponseParser:
    """Tests para parseo de respuestas VWAP"""
    
    @pytest.fixture
    def parser(self):
        """Fixture del parser de respuestas"""
        return VWAPResponseParser()
    
    @pytest.fixture
    def sample_long_response(self):
        """Respuesta de ejemplo para señal LONG"""
        return """
# ANÁLISIS VWAP EURUSD

## ESTADO_DEL_MERCADO

El VWAP muestra pendiente ascendente clara (+0.8 pips/período en 5M).
Precio actual: 1.1005
VWAP: 1.1003
El precio está justo por encima del VWAP, en zona de pullback saludable.

Opening Range: Breakout alcista confirmado, precio +5 pips por encima de OR high (1.1010).
Esto confirma el sesgo alcista del día.

## PLAN_DE_TRADING_ACTUAL

**Acción: LONG**

**Justificación:**
- VWAP ascendente (condición principal cumplida)
- Precio por encima de VWAP (1.1005 > 1.1003)
- Breakout alcista del OR confirmado
- Precio cerca de EMA9, no extendido en +2σ
- ATR: 15 pips - volatilidad adecuada

**Niveles propuestos:**
- Entrada: 1.1005 (precio actual)
- Stop Loss: 1.0995 (por debajo de VWAP - banda -1σ, ~10 pips = 1.5x ATR)
- Take Profit 1: 1.1020 (15 pips, 2x ATR)
- Take Profit 2: 1.1030 (25 pips, 3x ATR)

## GESTIÓN_DE_POSICIONES_ABIERTAS

Si hubiera posición long abierta:
- Mantener mientras precio > VWAP
- Mover stop a breakeven cuando precio alcance +10 pips
- Cerrar 50% en TP1, dejar correr 50% hacia TP2

Si hubiera posición short:
- Cerrar inmediatamente (contra tendencia VWAP)

## JOURNAL_Y_SCORE

**Score de confianza: 8/10**

Señal de alta calidad porque:
- Confluencia de 3 factores alcistas (VWAP, OR, EMA)
- No hay divergencias entre timeframes
- Volatilidad adecuada (ATR no extremo)

Único factor de precaución: Sesión ya lleva 1 hora, verificar que quede tiempo suficiente antes de cierre (13:00 GMT).
"""
    
    @pytest.fixture
    def sample_short_response(self):
        """Respuesta de ejemplo para señal SHORT"""
        return """
## ESTADO_DEL_MERCADO
VWAP descendente (-0.6 pips/período). Precio 1.0995, VWAP 1.1000.
OR: Breakout bajista confirmado.

## PLAN_DE_TRADING_ACTUAL
**Acción: SHORT**
Entrada: 1.0995
Stop Loss: 1.1005 (encima de VWAP)
Take Profit: 1.0980

## GESTIÓN_DE_POSICIONES_ABIERTAS
Mantener shorts, cerrar longs.

## JOURNAL_Y_SCORE
Score: 7/10
"""
    
    @pytest.fixture
    def sample_no_trade_response(self):
        """Respuesta de ejemplo para NO_OPERAR"""
        return """
## ESTADO_DEL_MERCADO
VWAP plana (slope < 0.5 pips). Sin tendencia clara.
Precio oscilando dentro del Opening Range.

## PLAN_DE_TRADING_ACTUAL
**Acción: NO_OPERAR**

No hay tendencia definida. VWAP plana indica mercado en rango.
Esperar breakout del OR o pendiente clara en VWAP.

## GESTIÓN_DE_POSICIONES_ABIERTAS
Cerrar posiciones abiertas y esperar mejor setup.

## JOURNAL_Y_SCORE
Score: N/A (sin señal)
"""
    
    def test_parse_long_signal(self, parser, sample_long_response):
        """Test parseo de señal LONG"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        
        # Assert
        assert parsed is not None
        assert parsed.action == TradingAction.LONG
        assert parsed.direction == Direction.BUY
    
    def test_parse_short_signal(self, parser, sample_short_response):
        """Test parseo de señal SHORT"""
        # Act
        parsed = parser.parse_response(sample_short_response)
        
        # Assert
        assert parsed.action == TradingAction.SHORT
        assert parsed.direction == Direction.SELL
    
    def test_parse_no_trade_signal(self, parser, sample_no_trade_response):
        """Test parseo de señal NO_OPERAR"""
        # Act
        parsed = parser.parse_response(sample_no_trade_response)
        
        # Assert
        assert parsed.action == TradingAction.NO_TRADE
        assert parsed.direction is None
    
    def test_extract_entry_price(self, parser, sample_long_response):
        """Test extracción de precio de entrada"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        
        # Assert
        assert parsed.entry_price is not None
        assert parsed.entry_price == pytest.approx(1.1005, abs=0.0001)
    
    def test_extract_stop_loss(self, parser, sample_long_response):
        """Test extracción de stop loss"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        
        # Assert
        assert parsed.stop_loss is not None
        assert parsed.stop_loss == pytest.approx(1.0995, abs=0.0001)
    
    def test_extract_take_profit(self, parser, sample_long_response):
        """Test extracción de take profit"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        
        # Assert
        assert parsed.take_profit is not None
        assert parsed.take_profit == pytest.approx(1.1020, abs=0.0001)
    
    def test_extract_confidence_score(self, parser, sample_long_response):
        """Test extracción de score de confianza"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        
        # Assert
        assert parsed.confidence_score is not None
        assert parsed.confidence_score == 8
        assert 1 <= parsed.confidence_score <= 10
    
    def test_extract_market_state(self, parser, sample_long_response):
        """Test extracción de estado del mercado"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        
        # Assert
        assert parsed.market_state is not None
        assert len(parsed.market_state) > 0
        assert "VWAP" in parsed.market_state or "ascendente" in parsed.market_state
    
    def test_extract_reasoning(self, parser, sample_long_response):
        """Test extracción de razonamiento"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        
        # Assert
        assert parsed.reasoning is not None
        assert len(parsed.reasoning) > 0
    
    def test_validate_long_against_vwap_rules(self, parser, sample_long_response):
        """Test validación de señal LONG contra reglas VWAP"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        is_valid = parser.validate_signal(parsed, vwap_slope="ascendente")
        
        # Assert
        assert is_valid is True
    
    def test_validate_short_against_vwap_rules(self, parser, sample_short_response):
        """Test validación de señal SHORT contra reglas VWAP"""
        # Act
        parsed = parser.parse_response(sample_short_response)
        is_valid = parser.validate_signal(parsed, vwap_slope="descendente")
        
        # Assert
        assert is_valid is True
    
    def test_reject_counter_trend_long(self, parser):
        """Test rechazo de LONG cuando VWAP es descendente"""
        # Arrange - Respuesta con LONG pero VWAP descendente
        response = """
## PLAN_DE_TRADING_ACTUAL
Acción: LONG
Entrada: 1.1000
"""
        
        # Act
        parsed = parser.parse_response(response)
        
        # Assert - Debe rechazar en validación
        with pytest.raises(ValidationError, match="contra.*tendencia|counter.*trend"):
            parser.validate_signal(parsed, vwap_slope="descendente")
    
    def test_reject_counter_trend_short(self, parser):
        """Test rechazo de SHORT cuando VWAP es ascendente"""
        # Arrange
        response = """
## PLAN_DE_TRADING_ACTUAL
Acción: SHORT
Entrada: 1.1000
"""
        
        # Act
        parsed = parser.parse_response(response)
        
        # Assert
        with pytest.raises(ValidationError, match="contra.*tendencia|counter.*trend"):
            parser.validate_signal(parsed, vwap_slope="ascendente")
    
    def test_extract_multiple_take_profits(self, parser, sample_long_response):
        """Test extracción de múltiples take profits"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        
        # Assert
        assert parsed.take_profit_1 is not None
        assert parsed.take_profit_2 is not None
        assert parsed.take_profit_1 < parsed.take_profit_2  # TP1 < TP2
    
    def test_parse_with_missing_sections(self, parser):
        """Test parseo con secciones faltantes"""
        # Arrange - Respuesta incompleta
        response = """
## PLAN_DE_TRADING_ACTUAL
Acción: LONG
"""
        
        # Act
        parsed = parser.parse_response(response)
        
        # Assert - Debe parsear lo que puede
        assert parsed.action == TradingAction.LONG
        # Otros campos pueden ser None
        assert parsed.entry_price is None or parsed.entry_price > 0
    
    def test_parse_various_price_formats(self, parser):
        """Test parseo de diferentes formatos de precio"""
        # Arrange - Diferentes formas de escribir precio
        responses = [
            "Entrada: 1.1005",
            "Entrada en 1.1005",
            "Entry: 1.1005",
            "Entry Price: 1.1005",
            "Precio entrada: 1.1005",
            "- Entrada: 1.1005 (precio actual)",
        ]
        
        # Act & Assert
        for response in responses:
            full_response = f"## PLAN_DE_TRADING_ACTUAL\nAcción: LONG\n{response}"
            parsed = parser.parse_response(full_response)
            assert parsed.entry_price == pytest.approx(1.1005, abs=0.0001)
    
    def test_convert_to_bot_format(self, parser, sample_long_response):
        """Test conversión a formato bot"""
        # Act
        parsed = parser.parse_response(sample_long_response)
        bot_format = parser.convert_to_bot_format(parsed)
        
        # Assert
        assert isinstance(bot_format, dict)
        assert "accion" in bot_format
        assert "direccion" in bot_format
        assert "precio_entrada" in bot_format
        assert "stop_loss" in bot_format
        assert "take_profit" in bot_format
        assert "razonamiento" in bot_format
        
        # Valores correctos
        assert bot_format["accion"] == "abrir"
        assert bot_format["direccion"] == "buy"
    
    def test_bot_format_no_trade(self, parser, sample_no_trade_response):
        """Test formato bot para NO_OPERAR"""
        # Act
        parsed = parser.parse_response(sample_no_trade_response)
        bot_format = parser.convert_to_bot_format(parsed)
        
        # Assert
        assert bot_format["accion"] == "esperar"
        assert bot_format["direccion"] is None


class TestVWAPResponseParserEdgeCases:
    """Tests de casos edge para Response Parser"""
    
    @pytest.fixture
    def parser(self):
        return VWAPResponseParser()
    
    def test_parse_malformed_response(self, parser):
        """Test parseo de respuesta malformada"""
        # Arrange
        response = "Esto no es una respuesta estructurada válida"
        
        # Act
        parsed = parser.parse_response(response)
        
        # Assert - Debe manejar gracefully
        assert parsed is not None
        # Puede tener valores por defecto o None
    
    def test_parse_empty_response(self, parser):
        """Test parseo de respuesta vacía"""
        # Arrange
        response = ""
        
        # Act
        parsed = parser.parse_response(response)
        
        # Assert
        assert parsed is not None
        assert parsed.action == TradingAction.NO_TRADE  # Default seguro
    
    def test_parse_mixed_case_action(self, parser):
        """Test parseo con diferentes mayúsculas/minúsculas"""
        # Arrange
        responses = [
            "Acción: LONG",
            "Acción: long",
            "Acción: Long",
            "accion: LONG",
            "Action: LONG"
        ]
        
        # Act & Assert
        for resp in responses:
            full_response = f"## PLAN_DE_TRADING_ACTUAL\n{resp}"
            parsed = parser.parse_response(full_response)
            assert parsed.action == TradingAction.LONG
    
    def test_extract_price_with_noise(self, parser):
        """Test extracción de precio con texto adicional"""
        # Arrange
        response = """
## PLAN_DE_TRADING_ACTUAL
Acción: LONG
Entrada sugerida: 1.1005 (esperando confirmación en vela actual)
Stop Loss conservador: 1.0995 pips (por debajo de soporte clave)
"""
        
        # Act
        parsed = parser.parse_response(response)
        
        # Assert
        assert parsed.entry_price == pytest.approx(1.1005, abs=0.0001)
        assert parsed.stop_loss == pytest.approx(1.0995, abs=0.0001)
    
    def test_validate_stop_loss_direction_long(self, parser):
        """Test validación de dirección de stop loss en LONG"""
        # Arrange
        response = """
## PLAN_DE_TRADING_ACTUAL
Acción: LONG
Entrada: 1.1000
Stop Loss: 1.1010
"""
        
        # Act
        parsed = parser.parse_response(response)
        
        # Assert - Stop loss ARRIBA de entrada en LONG es inválido
        with pytest.raises(ValidationError, match="[Ss]top [Ll]oss inv[aá]lido"):
            parser.validate_stop_loss(parsed)
    
    def test_validate_stop_loss_direction_short(self, parser):
        """Test validación de dirección de stop loss en SHORT"""
        # Arrange
        response = """
## PLAN_DE_TRADING_ACTUAL
Acción: SHORT
Entrada: 1.1000
Stop Loss: 1.0990
"""
        
        # Act
        parsed = parser.parse_response(response)
        
        # Assert - Stop loss ABAJO de entrada en SHORT es inválido
        with pytest.raises(ValidationError, match="[Ss]top [Ll]oss inv[aá]lido"):
            parser.validate_stop_loss(parsed)
    
    def test_validate_take_profit_direction(self, parser):
        """Test validación de dirección de take profit"""
        # Arrange - TP en dirección incorrecta
        response = """
## PLAN_DE_TRADING_ACTUAL
Acción: LONG
Entrada: 1.1000
Take Profit: 1.0990
"""
        
        # Act
        parsed = parser.parse_response(response)
        
        # Assert
        with pytest.raises(ValidationError, match="[Tt]ake [Pp]rofit inv[aá]lido"):
            parser.validate_take_profit(parsed)
    
    def test_extract_score_variations(self, parser):
        """Test extracción de score en diferentes formatos"""
        # Arrange
        score_formats = [
            "Score: 8/10",
            "Score de confianza: 8/10",
            "Confidence: 8/10",
            "Confianza: 8 de 10",
            "Score: 8",
        ]
        
        # Act & Assert
        for score_text in score_formats:
            response = f"## JOURNAL_Y_SCORE\n{score_text}"
            parsed = parser.parse_response(response)
            assert parsed.confidence_score == 8
