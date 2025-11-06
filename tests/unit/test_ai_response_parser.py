"""
Tests unitarios para ai_response_parser.py - T40
Registro de errores de parsing de respuestas IA

Metodología TDD: Red -> Green -> Refactor
"""

import pytest
import json
from datetime import datetime
from src.core.ai_response_parser import (
    AIResponseParser,
    AIParsingError,
    AIDecisionType,
    AIDirection,
    AIOrderType,
    ParsedDecision
)


class TestAIResponseParserInitialization:
    """Tests de inicialización del parser"""
    
    def test_init_with_valid_schema(self):
        """Debe inicializar correctamente con un esquema válido"""
        schema = {
            "required_fields": ["accion"],
            "valid_actions": ["OPERAR", "NO_OPERAR"]
        }
        parser = AIResponseParser(schema=schema)
        assert parser is not None
        assert parser.schema == schema
    
    def test_init_without_schema_uses_defaults(self):
        """Debe usar esquema por defecto si no se proporciona"""
        parser = AIResponseParser()
        assert parser is not None
        assert parser.schema is not None
        assert "required_fields" in parser.schema
    
    def test_init_with_logger(self):
        """Debe aceptar un logger personalizado"""
        from src.core.logger import BotLogger
        logger = BotLogger("test_parser")
        parser = AIResponseParser(logger=logger)
        assert parser.logger is not None


class TestParseEvaluationDecision:
    """Tests de parsing de decisiones de evaluación inicial"""
    
    def test_parse_valid_operar_decision(self):
        """Debe parsear correctamente una decisión OPERAR válida"""
        response = {
            "accion": "OPERAR",
            "direccion": "BUY",
            "tipo_orden": "MARKET",
            "stop_loss": 1.2300,
            "take_profit": 1.2500,
            "riesgo_porcentaje": 2.0,
            "razonamiento": "Tendencia alcista clara"
        }
        parser = AIResponseParser()
        result = parser.parse_evaluation(json.dumps(response))
        
        assert result.is_valid is True
        assert result.decision_type == AIDecisionType.OPERAR
        assert result.direction == AIDirection.BUY
        assert result.order_type == AIOrderType.MARKET
        assert result.stop_loss == 1.2300
        assert result.take_profit == 1.2500
        assert result.risk_percentage == 2.0
    
    def test_parse_valid_no_operar_decision(self):
        """Debe parsear correctamente una decisión NO_OPERAR"""
        response = {
            "accion": "NO_OPERAR",
            "razonamiento": "Mercado lateral sin señales claras"
        }
        parser = AIResponseParser()
        result = parser.parse_evaluation(json.dumps(response))
        
        assert result.is_valid is True
        assert result.decision_type == AIDecisionType.NO_OPERAR
        assert result.direction is None
        assert result.stop_loss is None
    
    def test_parse_operar_with_limit_order(self):
        """Debe parsear OPERAR con orden LIMIT y precio de entrada"""
        response = {
            "accion": "OPERAR",
            "direccion": "SELL",
            "tipo_orden": "LIMIT",
            "precio_entrada": 1.2400,
            "stop_loss": 1.2450,
            "take_profit": 1.2300,
            "riesgo_porcentaje": 1.5,
            "razonamiento": "Resistencia fuerte en 1.2400"
        }
        parser = AIResponseParser()
        result = parser.parse_evaluation(json.dumps(response))
        
        assert result.is_valid is True
        assert result.order_type == AIOrderType.LIMIT
        assert result.entry_price == 1.2400
        assert result.direction == AIDirection.SELL


class TestParseReevaluationDecision:
    """Tests de parsing de decisiones de reevaluación"""
    
    def test_parse_valid_mantener_decision(self):
        """Debe parsear correctamente una decisión MANTENER"""
        response = {
            "accion": "MANTENER",
            "razonamiento": "La operación va según lo previsto"
        }
        parser = AIResponseParser()
        result = parser.parse_reevaluation(json.dumps(response))
        
        assert result.is_valid is True
        assert result.decision_type == AIDecisionType.MANTENER
        assert result.new_stop_loss is None
        assert result.new_take_profit is None
    
    def test_parse_valid_actualizar_decision(self):
        """Debe parsear correctamente una decisión ACTUALIZAR con nuevos SL/TP"""
        response = {
            "accion": "ACTUALIZAR",
            "nuevo_stop_loss": 1.2350,
            "nuevo_take_profit": 1.2550,
            "razonamiento": "Ajustar SL a breakeven"
        }
        parser = AIResponseParser()
        result = parser.parse_reevaluation(json.dumps(response))
        
        assert result.is_valid is True
        assert result.decision_type == AIDecisionType.ACTUALIZAR
        assert result.new_stop_loss == 1.2350
        assert result.new_take_profit == 1.2550
    
    def test_parse_valid_cerrar_decision(self):
        """Debe parsear correctamente una decisión CERRAR"""
        response = {
            "accion": "CERRAR",
            "razonamiento": "Señales de reversión"
        }
        parser = AIResponseParser()
        result = parser.parse_reevaluation(json.dumps(response))
        
        assert result.is_valid is True
        assert result.decision_type == AIDecisionType.CERRAR


class TestParsingErrors:
    """Tests de manejo de errores de parsing"""
    
    def test_parse_invalid_json_raises_error(self):
        """Debe lanzar AIParsingError si el JSON es inválido"""
        parser = AIResponseParser()
        invalid_json = "{ accion: OPERAR, invalid }"
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(invalid_json)
        
        assert "JSON inválido" in str(exc_info.value)
        assert exc_info.value.error_type == "json_decode_error"
    
    def test_parse_missing_required_field_raises_error(self):
        """Debe lanzar AIParsingError si falta campo requerido 'accion'"""
        parser = AIResponseParser()
        response = {
            "direccion": "BUY",
            "stop_loss": 1.2300
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert "campo requerido" in str(exc_info.value).lower()
        assert exc_info.value.error_type == "missing_required_field"
        assert exc_info.value.field_name == "accion"
    
    def test_parse_invalid_action_raises_error(self):
        """Debe lanzar AIParsingError si la acción no es válida"""
        parser = AIResponseParser()
        response = {
            "accion": "COMPRAR_AHORA",  # Inválido
            "razonamiento": "..."
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert "acción inválida" in str(exc_info.value).lower()
        assert exc_info.value.error_type == "invalid_field_value"
        assert exc_info.value.field_name == "accion"
    
    def test_parse_operar_without_required_fields_raises_error(self):
        """Debe lanzar error si OPERAR sin direccion/SL/TP"""
        parser = AIResponseParser()
        response = {
            "accion": "OPERAR",
            "razonamiento": "Señal de compra"
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert exc_info.value.error_type == "missing_conditional_field"
    
    def test_parse_invalid_direction_raises_error(self):
        """Debe lanzar error si la dirección no es BUY o SELL"""
        parser = AIResponseParser()
        response = {
            "accion": "OPERAR",
            "direccion": "LONG",  # Inválido
            "stop_loss": 1.2300,
            "take_profit": 1.2500,
            "riesgo_porcentaje": 2.0
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert exc_info.value.field_name == "direccion"
    
    def test_parse_invalid_risk_percentage_raises_error(self):
        """Debe lanzar error si el riesgo está fuera de rango (1-5%)"""
        parser = AIResponseParser()
        response = {
            "accion": "OPERAR",
            "direccion": "BUY",
            "stop_loss": 1.2300,
            "take_profit": 1.2500,
            "riesgo_porcentaje": 10.0  # Fuera de rango
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert exc_info.value.error_type == "invalid_field_value"
        assert "riesgo_porcentaje" in str(exc_info.value)


class TestFieldTypeValidation:
    """Tests de validación de tipos de campos"""
    
    def test_parse_stop_loss_as_string_raises_error(self):
        """Debe lanzar error si stop_loss no es numérico"""
        parser = AIResponseParser()
        response = {
            "accion": "OPERAR",
            "direccion": "BUY",
            "stop_loss": "1.2300",  # String en lugar de float
            "take_profit": 1.2500,
            "riesgo_porcentaje": 2.0
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert exc_info.value.error_type == "invalid_field_type"
        assert exc_info.value.field_name == "stop_loss"
    
    def test_parse_actualizar_with_string_values_raises_error(self):
        """Debe lanzar error si nuevo_stop_loss no es numérico"""
        parser = AIResponseParser()
        response = {
            "accion": "ACTUALIZAR",
            "nuevo_stop_loss": "1.2350",  # String
            "nuevo_take_profit": 1.2550
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_reevaluation(json.dumps(response))
        
        assert exc_info.value.error_type == "invalid_field_type"


class TestErrorLogging:
    """Tests de registro de errores"""
    
    def test_parsing_error_is_logged(self):
        """Debe registrar error cuando el parsing falla"""
        parser = AIResponseParser()
        invalid_response = "{ invalid json }"
        
        try:
            parser.parse_evaluation(invalid_response)
        except AIParsingError:
            pass
        
        # Verificar que el error fue registrado
        errors = parser.get_error_history()
        assert len(errors) > 0
        assert errors[-1]["error_type"] == "json_decode_error"
        assert "raw_response" in errors[-1]
    
    def test_error_history_includes_timestamp(self):
        """Debe incluir timestamp en el historial de errores"""
        parser = AIResponseParser()
        
        try:
            parser.parse_evaluation("{}")
        except AIParsingError:
            pass
        
        errors = parser.get_error_history()
        assert "timestamp" in errors[-1]
        assert isinstance(errors[-1]["timestamp"], str)
    
    def test_get_error_statistics(self):
        """Debe proporcionar estadísticas de errores"""
        parser = AIResponseParser()
        
        # Generar varios errores
        for _ in range(3):
            try:
                parser.parse_evaluation("{ invalid }")
            except AIParsingError:
                pass
        
        try:
            parser.parse_evaluation("{}")
        except AIParsingError:
            pass
        
        stats = parser.get_error_statistics()
        assert stats["total_errors"] == 4
        assert "json_decode_error" in stats["by_type"]
        assert stats["by_type"]["json_decode_error"] >= 3


class TestParsedDecision:
    """Tests de la clase ParsedDecision"""
    
    def test_parsed_decision_initialization(self):
        """Debe inicializar correctamente un ParsedDecision"""
        decision = ParsedDecision(
            is_valid=True,
            decision_type=AIDecisionType.OPERAR,
            direction=AIDirection.BUY,
            stop_loss=1.2300,
            take_profit=1.2500,
            risk_percentage=2.0
        )
        
        assert decision.is_valid is True
        assert decision.decision_type == AIDecisionType.OPERAR
        assert decision.direction == AIDirection.BUY
    
    def test_parsed_decision_to_dict(self):
        """Debe convertir ParsedDecision a diccionario"""
        decision = ParsedDecision(
            is_valid=True,
            decision_type=AIDecisionType.NO_OPERAR,
            reasoning="Mercado lateral"
        )
        
        result = decision.to_dict()
        assert result["is_valid"] is True
        assert result["decision_type"] == "NO_OPERAR"
        assert result["reasoning"] == "Mercado lateral"
    
    def test_invalid_parsed_decision(self):
        """Debe poder crear ParsedDecision inválido con error"""
        decision = ParsedDecision(
            is_valid=False,
            error_type="json_decode_error",
            error_message="JSON malformado"
        )
        
        assert decision.is_valid is False
        assert decision.error_type == "json_decode_error"
        assert decision.decision_type is None


class TestAIDecisionType:
    """Tests del enum AIDecisionType"""
    
    def test_ai_decision_type_enum_values(self):
        """Debe tener todos los valores esperados"""
        assert AIDecisionType.OPERAR.value == "OPERAR"
        assert AIDecisionType.NO_OPERAR.value == "NO_OPERAR"
        assert AIDecisionType.MANTENER.value == "MANTENER"
        assert AIDecisionType.ACTUALIZAR.value == "ACTUALIZAR"
        assert AIDecisionType.CERRAR.value == "CERRAR"
    
    def test_from_string_conversion(self):
        """Debe convertir string a enum"""
        assert AIDecisionType.from_string("OPERAR") == AIDecisionType.OPERAR
        assert AIDecisionType.from_string("MANTENER") == AIDecisionType.MANTENER
    
    def test_from_string_case_insensitive(self):
        """Debe convertir string a enum sin importar mayúsculas"""
        assert AIDecisionType.from_string("operar") == AIDecisionType.OPERAR
        assert AIDecisionType.from_string("Cerrar") == AIDecisionType.CERRAR
    
    def test_from_string_invalid_raises_error(self):
        """Debe lanzar error si el string no es válido"""
        with pytest.raises(ValueError):
            AIDecisionType.from_string("COMPRAR")


class TestAIDirection:
    """Tests del enum AIDirection"""
    
    def test_ai_direction_enum_values(self):
        """Debe tener BUY y SELL"""
        assert AIDirection.BUY.value == "BUY"
        assert AIDirection.SELL.value == "SELL"
    
    def test_from_string_conversion(self):
        """Debe convertir string a enum"""
        assert AIDirection.from_string("BUY") == AIDirection.BUY
        assert AIDirection.from_string("sell") == AIDirection.SELL


class TestAIOrderType:
    """Tests del enum AIOrderType"""
    
    def test_ai_order_type_enum_values(self):
        """Debe tener MARKET y LIMIT"""
        assert AIOrderType.MARKET.value == "MARKET"
        assert AIOrderType.LIMIT.value == "LIMIT"
    
    def test_from_string_conversion(self):
        """Debe convertir string a enum"""
        assert AIOrderType.from_string("MARKET") == AIOrderType.MARKET
        assert AIOrderType.from_string("limit") == AIOrderType.LIMIT


class TestSafeParsing:
    """Tests de parsing seguro sin excepciones"""
    
    def test_safe_parse_returns_invalid_decision_on_error(self):
        """Debe retornar ParsedDecision inválido sin lanzar excepción"""
        parser = AIResponseParser()
        result = parser.safe_parse_evaluation("{ invalid json }")
        
        assert result.is_valid is False
        assert result.error_type is not None
        assert result.error_message is not None
    
    def test_safe_parse_valid_response_returns_valid_decision(self):
        """Debe retornar ParsedDecision válido en caso exitoso"""
        parser = AIResponseParser()
        response = {
            "accion": "NO_OPERAR",
            "razonamiento": "Sin señales"
        }
        result = parser.safe_parse_evaluation(json.dumps(response))
        
        assert result.is_valid is True
        assert result.decision_type == AIDecisionType.NO_OPERAR


class TestBusinessLogicValidation:
    """Tests de validación de lógica de negocio"""
    
    def test_sl_must_be_below_entry_for_buy(self):
        """Para BUY, el SL debe estar por debajo del precio de entrada"""
        parser = AIResponseParser()
        response = {
            "accion": "OPERAR",
            "direccion": "BUY",
            "tipo_orden": "LIMIT",
            "precio_entrada": 1.2400,
            "stop_loss": 1.2450,  # SL por encima de entrada (inválido)
            "take_profit": 1.2500,
            "riesgo_porcentaje": 2.0
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert exc_info.value.error_type == "invalid_business_logic"
        assert "stop_loss" in str(exc_info.value).lower()
    
    def test_sl_must_be_above_entry_for_sell(self):
        """Para SELL, el SL debe estar por encima del precio de entrada"""
        parser = AIResponseParser()
        response = {
            "accion": "OPERAR",
            "direccion": "SELL",
            "tipo_orden": "LIMIT",
            "precio_entrada": 1.2400,
            "stop_loss": 1.2350,  # SL por debajo de entrada (inválido)
            "take_profit": 1.2300,
            "riesgo_porcentaje": 2.0
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert exc_info.value.error_type == "invalid_business_logic"
    
    def test_tp_must_be_above_entry_for_buy(self):
        """Para BUY, el TP debe estar por encima del precio de entrada"""
        parser = AIResponseParser()
        response = {
            "accion": "OPERAR",
            "direccion": "BUY",
            "tipo_orden": "LIMIT",
            "precio_entrada": 1.2400,
            "stop_loss": 1.2350,
            "take_profit": 1.2390,  # TP por debajo de entrada (inválido)
            "riesgo_porcentaje": 2.0
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert exc_info.value.error_type == "invalid_business_logic"
        assert "take_profit" in str(exc_info.value).lower()


class TestEdgeCases:
    """Tests de casos extremos"""
    
    def test_parse_empty_string_raises_error(self):
        """Debe lanzar error con string vacío"""
        parser = AIResponseParser()
        
        with pytest.raises(AIParsingError):
            parser.parse_evaluation("")
    
    def test_parse_empty_json_object_raises_error(self):
        """Debe lanzar error con JSON vacío"""
        parser = AIResponseParser()
        
        with pytest.raises(AIParsingError):
            parser.parse_evaluation("{}")
    
    def test_parse_with_extra_fields_is_accepted(self):
        """Debe aceptar respuesta con campos adicionales no esperados"""
        parser = AIResponseParser()
        response = {
            "accion": "NO_OPERAR",
            "razonamiento": "Sin señales",
            "confianza": 0.85,  # Campo extra
            "timestamp": "2025-01-01T10:00:00"  # Campo extra
        }
        result = parser.parse_evaluation(json.dumps(response))
        
        assert result.is_valid is True
    
    def test_parse_limit_order_without_entry_price_raises_error(self):
        """Debe lanzar error si orden LIMIT sin precio_entrada"""
        parser = AIResponseParser()
        response = {
            "accion": "OPERAR",
            "direccion": "BUY",
            "tipo_orden": "LIMIT",
            # precio_entrada faltante
            "stop_loss": 1.2300,
            "take_profit": 1.2500,
            "riesgo_porcentaje": 2.0
        }
        
        with pytest.raises(AIParsingError) as exc_info:
            parser.parse_evaluation(json.dumps(response))
        
        assert exc_info.value.error_type == "missing_conditional_field"
        assert "precio_entrada" in str(exc_info.value)


class TestClearErrorHistory:
    """Tests de limpieza de historial"""
    
    def test_clear_error_history(self):
        """Debe limpiar el historial de errores"""
        parser = AIResponseParser()
        
        # Generar errores
        for _ in range(3):
            try:
                parser.parse_evaluation("{}")
            except AIParsingError:
                pass
        
        assert len(parser.get_error_history()) == 3
        
        parser.clear_error_history()
        assert len(parser.get_error_history()) == 0
    
    def test_statistics_reset_after_clear(self):
        """Debe resetear estadísticas después de limpiar"""
        parser = AIResponseParser()
        
        try:
            parser.parse_evaluation("{}")
        except AIParsingError:
            pass
        
        parser.clear_error_history()
        stats = parser.get_error_statistics()
        assert stats["total_errors"] == 0
