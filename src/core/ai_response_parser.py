"""
AIResponseParser - T40
Parser y validador de respuestas JSON de IA con registro de errores

Funcionalidades:
- Parseo de decisiones de evaluación (OPERAR/NO_OPERAR)
- Parseo de decisiones de reevaluación (MANTENER/ACTUALIZAR/CERRAR)
- Validación de estructura, tipos y lógica de negocio
- Registro de errores de parsing con historial
- Estadísticas de errores

Author: Botrading Team
Date: 2025-11-06
"""

import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, List, Any, Union
from src.core.logger import BotLogger


class AIDecisionType(Enum):
    """Tipos de decisiones que la IA puede tomar"""
    OPERAR = "OPERAR"
    NO_OPERAR = "NO_OPERAR"
    MANTENER = "MANTENER"
    ACTUALIZAR = "ACTUALIZAR"
    CERRAR = "CERRAR"
    
    @classmethod
    def from_string(cls, value: str) -> 'AIDecisionType':
        """Convierte string a enum (case-insensitive)"""
        value_upper = value.upper()
        for member in cls:
            if member.value == value_upper:
                return member
        raise ValueError(f"Valor inválido para AIDecisionType: {value}")


class AIDirection(Enum):
    """Dirección de la operación"""
    BUY = "BUY"
    SELL = "SELL"
    
    @classmethod
    def from_string(cls, value: str) -> 'AIDirection':
        """Convierte string a enum (case-insensitive)"""
        value_upper = value.upper()
        for member in cls:
            if member.value == value_upper:
                return member
        raise ValueError(f"Valor inválido para AIDirection: {value}")


class AIOrderType(Enum):
    """Tipo de orden"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    
    @classmethod
    def from_string(cls, value: str) -> 'AIOrderType':
        """Convierte string a enum (case-insensitive)"""
        value_upper = value.upper()
        for member in cls:
            if member.value == value_upper:
                return member
        raise ValueError(f"Valor inválido para AIOrderType: {value}")


@dataclass
class ParsedDecision:
    """Resultado del parsing de una decisión de IA"""
    is_valid: bool
    decision_type: Optional[AIDecisionType] = None
    direction: Optional[AIDirection] = None
    order_type: Optional[AIOrderType] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_percentage: Optional[float] = None
    new_stop_loss: Optional[float] = None
    new_take_profit: Optional[float] = None
    reasoning: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario"""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if isinstance(value, Enum):
                    result[key] = value.value
                else:
                    result[key] = value
        return result


class AIParsingError(Exception):
    """Excepción específica para errores de parsing de respuestas IA"""
    
    def __init__(
        self,
        message: str,
        error_type: str,
        field_name: Optional[str] = None,
        raw_response: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.field_name = field_name
        self.raw_response = raw_response
        self.timestamp = datetime.now().isoformat()


class AIResponseParser:
    """Parser de respuestas JSON de IA con validación y registro de errores"""
    
    DEFAULT_SCHEMA = {
        "required_fields": ["accion"],
        "valid_actions": ["OPERAR", "NO_OPERAR", "MANTENER", "ACTUALIZAR", "CERRAR"],
        "valid_directions": ["BUY", "SELL"],
        "valid_order_types": ["MARKET", "LIMIT"],
        "risk_percentage_range": [1.0, 5.0],
        "operar_required_fields": ["direccion", "stop_loss", "take_profit", "riesgo_porcentaje"],
        "actualizar_required_fields": ["nuevo_stop_loss", "nuevo_take_profit"]
    }
    
    def __init__(
        self,
        schema: Optional[Dict[str, Any]] = None,
        logger: Optional[BotLogger] = None
    ):
        """
        Inicializa el parser
        
        Args:
            schema: Esquema de validación personalizado (opcional)
            logger: Logger personalizado (opcional)
        """
        self.schema = schema if schema is not None else self.DEFAULT_SCHEMA.copy()
        self.logger = logger if logger is not None else BotLogger("ai_response_parser")
        self._error_history: List[Dict[str, Any]] = []
    
    def parse_evaluation(self, response: str) -> ParsedDecision:
        """
        Parsea una respuesta de evaluación inicial (OPERAR/NO_OPERAR)
        
        Args:
            response: String JSON con la respuesta de la IA
            
        Returns:
            ParsedDecision con los datos parseados
            
        Raises:
            AIParsingError: Si el parsing falla
        """
        # Parsear JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            error = AIParsingError(
                message=f"JSON inválido: {str(e)}",
                error_type="json_decode_error",
                raw_response=response
            )
            self._log_error(error)
            raise error
        
        # Validar campo requerido: accion
        if "accion" not in data:
            error = AIParsingError(
                message="Campo requerido 'accion' no está presente",
                error_type="missing_required_field",
                field_name="accion",
                raw_response=response
            )
            self._log_error(error)
            raise error
        
        # Validar acción
        accion_str = data["accion"]
        if accion_str not in self.schema["valid_actions"]:
            error = AIParsingError(
                message=f"Acción inválida: {accion_str}",
                error_type="invalid_field_value",
                field_name="accion",
                raw_response=response
            )
            self._log_error(error)
            raise error
        
        decision_type = AIDecisionType.from_string(accion_str)
        
        # Si es NO_OPERAR, solo necesitamos el razonamiento
        if decision_type == AIDecisionType.NO_OPERAR:
            return ParsedDecision(
                is_valid=True,
                decision_type=decision_type,
                reasoning=data.get("razonamiento"),
                raw_response=response
            )
        
        # Si es OPERAR, validar campos adicionales
        if decision_type == AIDecisionType.OPERAR:
            return self._parse_operar_decision(data, response)
        
        # Otros tipos de decisión no son válidos para evaluación
        error = AIParsingError(
            message=f"Tipo de decisión '{accion_str}' no válido para evaluación",
            error_type="invalid_field_value",
            field_name="accion",
            raw_response=response
        )
        self._log_error(error)
        raise error
    
    def parse_reevaluation(self, response: str) -> ParsedDecision:
        """
        Parsea una respuesta de reevaluación (MANTENER/ACTUALIZAR/CERRAR)
        
        Args:
            response: String JSON con la respuesta de la IA
            
        Returns:
            ParsedDecision con los datos parseados
            
        Raises:
            AIParsingError: Si el parsing falla
        """
        # Parsear JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            error = AIParsingError(
                message=f"JSON inválido: {str(e)}",
                error_type="json_decode_error",
                raw_response=response
            )
            self._log_error(error)
            raise error
        
        # Validar campo requerido: accion
        if "accion" not in data:
            error = AIParsingError(
                message="Campo requerido 'accion' no está presente",
                error_type="missing_required_field",
                field_name="accion",
                raw_response=response
            )
            self._log_error(error)
            raise error
        
        accion_str = data["accion"]
        valid_reevaluation_actions = ["MANTENER", "ACTUALIZAR", "CERRAR"]
        
        if accion_str not in valid_reevaluation_actions:
            error = AIParsingError(
                message=f"Acción '{accion_str}' no válida para reevaluación",
                error_type="invalid_field_value",
                field_name="accion",
                raw_response=response
            )
            self._log_error(error)
            raise error
        
        decision_type = AIDecisionType.from_string(accion_str)
        
        # MANTENER y CERRAR solo necesitan razonamiento
        if decision_type in [AIDecisionType.MANTENER, AIDecisionType.CERRAR]:
            return ParsedDecision(
                is_valid=True,
                decision_type=decision_type,
                reasoning=data.get("razonamiento"),
                raw_response=response
            )
        
        # ACTUALIZAR necesita nuevos valores de SL/TP
        if decision_type == AIDecisionType.ACTUALIZAR:
            return self._parse_actualizar_decision(data, response)
        
        # No debería llegar aquí, pero por si acaso
        error = AIParsingError(
            message=f"Estado inesperado en parse_reevaluation",
            error_type="unknown_error",
            raw_response=response
        )
        self._log_error(error)
        raise error
    
    def _parse_operar_decision(self, data: Dict[str, Any], raw_response: str) -> ParsedDecision:
        """Parsea una decisión OPERAR con sus campos requeridos"""
        # Validar campos requeridos
        required = self.schema["operar_required_fields"]
        for field in required:
            if field not in data:
                error = AIParsingError(
                    message=f"Campo requerido '{field}' no está presente para OPERAR",
                    error_type="missing_conditional_field",
                    field_name=field,
                    raw_response=raw_response
                )
                self._log_error(error)
                raise error
        
        # Validar dirección
        direccion_str = data["direccion"]
        if direccion_str not in self.schema["valid_directions"]:
            error = AIParsingError(
                message=f"Dirección inválida: {direccion_str}",
                error_type="invalid_field_value",
                field_name="direccion",
                raw_response=raw_response
            )
            self._log_error(error)
            raise error
        
        direction = AIDirection.from_string(direccion_str)
        
        # Validar tipo de orden (opcional, por defecto MARKET)
        order_type = AIOrderType.MARKET
        if "tipo_orden" in data:
            tipo_orden_str = data["tipo_orden"]
            if tipo_orden_str not in self.schema["valid_order_types"]:
                error = AIParsingError(
                    message=f"Tipo de orden inválido: {tipo_orden_str}",
                    error_type="invalid_field_value",
                    field_name="tipo_orden",
                    raw_response=raw_response
                )
                self._log_error(error)
                raise error
            order_type = AIOrderType.from_string(tipo_orden_str)
        
        # Si es LIMIT, validar precio_entrada
        entry_price = None
        if order_type == AIOrderType.LIMIT:
            if "precio_entrada" not in data:
                error = AIParsingError(
                    message="Campo 'precio_entrada' requerido para orden LIMIT",
                    error_type="missing_conditional_field",
                    field_name="precio_entrada",
                    raw_response=raw_response
                )
                self._log_error(error)
                raise error
            entry_price = self._validate_float_field(data, "precio_entrada", raw_response)
        
        # Validar tipos y valores numéricos
        stop_loss = self._validate_float_field(data, "stop_loss", raw_response)
        take_profit = self._validate_float_field(data, "take_profit", raw_response)
        risk_percentage = self._validate_float_field(data, "riesgo_porcentaje", raw_response)
        
        # Validar rango de riesgo
        min_risk, max_risk = self.schema["risk_percentage_range"]
        if not (min_risk <= risk_percentage <= max_risk):
            error = AIParsingError(
                message=f"riesgo_porcentaje fuera de rango [{min_risk}, {max_risk}]: {risk_percentage}",
                error_type="invalid_field_value",
                field_name="riesgo_porcentaje",
                raw_response=raw_response
            )
            self._log_error(error)
            raise error
        
        # Validar lógica de negocio
        self._validate_business_logic(
            direction=direction,
            order_type=order_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            raw_response=raw_response
        )
        
        return ParsedDecision(
            is_valid=True,
            decision_type=AIDecisionType.OPERAR,
            direction=direction,
            order_type=order_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_percentage=risk_percentage,
            reasoning=data.get("razonamiento"),
            raw_response=raw_response
        )
    
    def _parse_actualizar_decision(self, data: Dict[str, Any], raw_response: str) -> ParsedDecision:
        """Parsea una decisión ACTUALIZAR con nuevos SL/TP"""
        # Al menos uno de los dos campos debe estar presente
        has_new_sl = "nuevo_stop_loss" in data
        has_new_tp = "nuevo_take_profit" in data
        
        if not has_new_sl and not has_new_tp:
            error = AIParsingError(
                message="ACTUALIZAR requiere al menos 'nuevo_stop_loss' o 'nuevo_take_profit'",
                error_type="missing_conditional_field",
                raw_response=raw_response
            )
            self._log_error(error)
            raise error
        
        new_sl = None
        new_tp = None
        
        if has_new_sl:
            new_sl = self._validate_float_field(data, "nuevo_stop_loss", raw_response)
        
        if has_new_tp:
            new_tp = self._validate_float_field(data, "nuevo_take_profit", raw_response)
        
        return ParsedDecision(
            is_valid=True,
            decision_type=AIDecisionType.ACTUALIZAR,
            new_stop_loss=new_sl,
            new_take_profit=new_tp,
            reasoning=data.get("razonamiento"),
            raw_response=raw_response
        )
    
    def _validate_float_field(
        self,
        data: Dict[str, Any],
        field_name: str,
        raw_response: str
    ) -> float:
        """Valida que un campo sea numérico (float o int)"""
        value = data[field_name]
        
        if not isinstance(value, (int, float)):
            error = AIParsingError(
                message=f"Campo '{field_name}' debe ser numérico, recibido: {type(value).__name__}",
                error_type="invalid_field_type",
                field_name=field_name,
                raw_response=raw_response
            )
            self._log_error(error)
            raise error
        
        return float(value)
    
    def _validate_business_logic(
        self,
        direction: AIDirection,
        order_type: AIOrderType,
        entry_price: Optional[float],
        stop_loss: float,
        take_profit: float,
        raw_response: str
    ):
        """Valida la lógica de negocio (SL/TP vs dirección)"""
        # Para MARKET, usamos precios relativos (asumimos que el entry es el precio actual)
        # Para LIMIT, validamos contra el precio de entrada especificado
        
        if order_type == AIOrderType.LIMIT and entry_price is not None:
            # BUY: SL < Entry < TP
            if direction == AIDirection.BUY:
                if stop_loss >= entry_price:
                    error = AIParsingError(
                        message=f"Para BUY, stop_loss ({stop_loss}) debe ser menor que precio_entrada ({entry_price})",
                        error_type="invalid_business_logic",
                        field_name="stop_loss",
                        raw_response=raw_response
                    )
                    self._log_error(error)
                    raise error
                
                if take_profit <= entry_price:
                    error = AIParsingError(
                        message=f"Para BUY, take_profit ({take_profit}) debe ser mayor que precio_entrada ({entry_price})",
                        error_type="invalid_business_logic",
                        field_name="take_profit",
                        raw_response=raw_response
                    )
                    self._log_error(error)
                    raise error
            
            # SELL: SL > Entry > TP
            if direction == AIDirection.SELL:
                if stop_loss <= entry_price:
                    error = AIParsingError(
                        message=f"Para SELL, stop_loss ({stop_loss}) debe ser mayor que precio_entrada ({entry_price})",
                        error_type="invalid_business_logic",
                        field_name="stop_loss",
                        raw_response=raw_response
                    )
                    self._log_error(error)
                    raise error
                
                if take_profit >= entry_price:
                    error = AIParsingError(
                        message=f"Para SELL, take_profit ({take_profit}) debe ser menor que precio_entrada ({entry_price})",
                        error_type="invalid_business_logic",
                        field_name="take_profit",
                        raw_response=raw_response
                    )
                    self._log_error(error)
                    raise error
    
    def safe_parse_evaluation(self, response: str) -> ParsedDecision:
        """
        Parsea una evaluación sin lanzar excepciones
        
        Returns:
            ParsedDecision válido si el parsing es exitoso, inválido si falla
        """
        try:
            return self.parse_evaluation(response)
        except AIParsingError as e:
            return ParsedDecision(
                is_valid=False,
                error_type=e.error_type,
                error_message=e.message,
                raw_response=response
            )
    
    def safe_parse_reevaluation(self, response: str) -> ParsedDecision:
        """
        Parsea una reevaluación sin lanzar excepciones
        
        Returns:
            ParsedDecision válido si el parsing es exitoso, inválido si falla
        """
        try:
            return self.parse_reevaluation(response)
        except AIParsingError as e:
            return ParsedDecision(
                is_valid=False,
                error_type=e.error_type,
                error_message=e.message,
                raw_response=response
            )
    
    def _log_error(self, error: AIParsingError):
        """Registra un error en el historial y en el logger"""
        error_record = {
            "timestamp": error.timestamp,
            "error_type": error.error_type,
            "error_message": error.message,
            "field_name": error.field_name,
            "raw_response": error.raw_response[:200] if error.raw_response else None  # Truncar
        }
        
        self._error_history.append(error_record)
        
        self.logger.error(
            f"Error de parsing: {error.error_type} - {error.message}",
            extra={
                "error_type": error.error_type,
                "field_name": error.field_name
            }
        )
    
    def get_error_history(self) -> List[Dict[str, Any]]:
        """Retorna el historial completo de errores"""
        return self._error_history.copy()
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas de errores"""
        total = len(self._error_history)
        
        # Contar por tipo
        by_type = {}
        for error in self._error_history:
            error_type = error["error_type"]
            by_type[error_type] = by_type.get(error_type, 0) + 1
        
        return {
            "total_errors": total,
            "by_type": by_type
        }
    
    def clear_error_history(self):
        """Limpia el historial de errores"""
        self._error_history.clear()
