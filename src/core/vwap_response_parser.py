"""
VWAPResponseParser - Parseo de respuestas de IA para metodología VWAP.

Este módulo parsea las respuestas estructuradas de la IA y las convierte
en formato ejecutable por el bot. Incluye validación de señales contra
reglas de la metodología VWAP.

Autor: Sistema Botrading
Fecha: 2025-11-17
Ticket: VWAP Methodology - Response Parser
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
import re


class TradingAction(Enum):
    """Acción de trading propuesta"""
    LONG = "long"
    SHORT = "short"
    NO_TRADE = "no_trade"


class Direction(Enum):
    """Dirección de la orden"""
    BUY = "buy"
    SELL = "sell"


class ValidationError(Exception):
    """Error de validación de señal"""
    pass


@dataclass
class ParsedResponse:
    """
    Respuesta de IA parseada y estructurada.
    
    Attributes:
        action: Acción propuesta (LONG, SHORT, NO_TRADE)
        direction: Dirección de orden (BUY, SELL)
        entry_price: Precio de entrada propuesto
        stop_loss: Nivel de stop loss
        take_profit: Nivel de take profit principal
        take_profit_1: Primer take profit (opcional)
        take_profit_2: Segundo take profit (opcional)
        confidence_score: Score de confianza (1-10)
        market_state: Descripción del estado del mercado
        reasoning: Razonamiento de la señal
        raw_response: Respuesta completa original
    """
    action: TradingAction
    direction: Optional[Direction] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    confidence_score: Optional[int] = None
    market_state: Optional[str] = None
    reasoning: Optional[str] = None
    raw_response: Optional[str] = None


class VWAPResponseParser:
    """
    Parser de respuestas de IA para metodología VWAP.
    
    Extrae información estructurada de las respuestas de la IA y
    valida que las señales cumplan con las reglas VWAP.
    """
    
    def __init__(self):
        """Inicializa el parser"""
        pass
    
    def parse_response(self, response: str) -> ParsedResponse:
        """
        Parsea la respuesta completa de la IA.
        
        Args:
            response: Respuesta de texto de la IA
        
        Returns:
            ParsedResponse con información extraída
        """
        # Extraer acción
        action = self._extract_action(response)
        
        # Determinar dirección
        direction = None
        if action == TradingAction.LONG:
            direction = Direction.BUY
        elif action == TradingAction.SHORT:
            direction = Direction.SELL
        
        # Extraer precios
        entry_price = self._extract_entry_price(response)
        stop_loss = self._extract_stop_loss(response)
        take_profit = self._extract_take_profit(response)
        tp1 = self._extract_take_profit_1(response)
        tp2 = self._extract_take_profit_2(response)
        
        # Usar TP principal si no hay TP1
        if take_profit and not tp1:
            tp1 = take_profit
        
        # Extraer score de confianza
        confidence_score = self._extract_confidence_score(response)
        
        # Extraer estado del mercado
        market_state = self._extract_market_state(response)
        
        # Extraer razonamiento
        reasoning = self._extract_reasoning(response)
        
        return ParsedResponse(
            action=action,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=tp1,
            take_profit_1=tp1,
            take_profit_2=tp2,
            confidence_score=confidence_score,
            market_state=market_state,
            reasoning=reasoning,
            raw_response=response
        )
    
    def _extract_action(self, response: str) -> TradingAction:
        """Extrae la acción de trading de la respuesta"""
        response_lower = response.lower()
        
        # Buscar "Acción: LONG/SHORT/NO_OPERAR"
        patterns = [
            r'acci[oó]n:\s*(long|short|no[_\s-]?operar|no[_\s-]?trade)',
            r'action:\s*(long|short|no[_\s-]?trade)',
            r'\*\*acci[oó]n:\s*(long|short|no[_\s-]?operar)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_lower)
            if match:
                action_str = match.group(1).replace(' ', '_').replace('-', '_')
                
                if 'long' in action_str:
                    return TradingAction.LONG
                elif 'short' in action_str:
                    return TradingAction.SHORT
                elif 'no' in action_str:
                    return TradingAction.NO_TRADE
        
        # Default: NO_TRADE si no se encuentra
        return TradingAction.NO_TRADE
    
    def _extract_entry_price(self, response: str) -> Optional[float]:
        """Extrae el precio de entrada"""
        patterns = [
            r'entrada\s+sugerida:?\s*(\d+\.\d+)',
            r'entrada:?\s*(\d+\.\d+)',
            r'entry:?\s*(\d+\.\d+)',
            r'precio\s+entrada:?\s*(\d+\.\d+)',
            r'entry\s+price:?\s*(\d+\.\d+)',
            r'entrada\s+en\s+(\d+\.\d+)',
        ]
        
        return self._extract_price(response, patterns)
    
    def _extract_stop_loss(self, response: str) -> Optional[float]:
        """Extrae el stop loss"""
        patterns = [
            r'stop\s+loss\s+conservador:?\s*(\d+\.\d+)',
            r'stop\s*loss:?\s*(\d+\.\d+)',
            r'sl:?\s*(\d+\.\d+)',
            r'stop:?\s*(\d+\.\d+)',
        ]
        
        return self._extract_price(response, patterns)
    
    def _extract_take_profit(self, response: str) -> Optional[float]:
        """Extrae el take profit principal"""
        patterns = [
            r'take\s*profit:?\s*(\d+\.\d+)',
            r'tp:?\s*(\d+\.\d+)',
            r'objetivo:?\s*(\d+\.\d+)',
            r'target:?\s*(\d+\.\d+)',
        ]
        
        return self._extract_price(response, patterns)
    
    def _extract_take_profit_1(self, response: str) -> Optional[float]:
        """Extrae el primer take profit"""
        patterns = [
            r'take\s*profit\s*1:?\s*(\d+\.\d+)',
            r'tp\s*1:?\s*(\d+\.\d+)',
            r'tp1:?\s*(\d+\.\d+)',
        ]
        
        return self._extract_price(response, patterns)
    
    def _extract_take_profit_2(self, response: str) -> Optional[float]:
        """Extrae el segundo take profit"""
        patterns = [
            r'take\s*profit\s*2:?\s*(\d+\.\d+)',
            r'tp\s*2:?\s*(\d+\.\d+)',
            r'tp2:?\s*(\d+\.\d+)',
        ]
        
        return self._extract_price(response, patterns)
    
    def _extract_price(self, response: str, patterns: list) -> Optional[float]:
        """
        Extrae un precio usando múltiples patrones.
        
        Args:
            response: Texto de respuesta
            patterns: Lista de regex patterns
        
        Returns:
            Precio extraído o None
        """
        response_lower = response.lower()
        
        for pattern in patterns:
            match = re.search(pattern, response_lower)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_confidence_score(self, response: str) -> Optional[int]:
        """Extrae el score de confianza (1-10)"""
        patterns = [
            r'score:?\s*(\d+)',
            r'confianza:?\s*(\d+)',
            r'confidence:?\s*(\d+)',
            r'score.*?:\s*(\d+)\s*/\s*10',
        ]
        
        response_lower = response.lower()
        
        for pattern in patterns:
            match = re.search(pattern, response_lower)
            if match:
                try:
                    score = int(match.group(1))
                    # Validar rango 1-10
                    if 1 <= score <= 10:
                        return score
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_market_state(self, response: str) -> Optional[str]:
        """Extrae la sección ESTADO_DEL_MERCADO"""
        # Buscar sección entre ESTADO_DEL_MERCADO y siguiente ##
        pattern = r'##\s*ESTADO[_\s]DEL[_\s]MERCADO\s*\n(.*?)(?=##|\Z)'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return None
    
    def _extract_reasoning(self, response: str) -> Optional[str]:
        """Extrae el razonamiento de la señal"""
        # Buscar en PLAN_DE_TRADING_ACTUAL después de "Justificación:"
        pattern = r'justificaci[oó]n:?\s*\n(.*?)(?=##|\*\*|$)'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Si no hay justificación explícita, usar PLAN_DE_TRADING completo
        pattern = r'##\s*PLAN[_\s]DE[_\s]TRADING[_\s]ACTUAL\s*\n(.*?)(?=##|\Z)'
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return None
    
    def validate_signal(self, parsed: ParsedResponse, vwap_slope: str) -> bool:
        """
        Valida que la señal cumpla con reglas VWAP.
        
        Args:
            parsed: Respuesta parseada
            vwap_slope: Pendiente del VWAP ("ascendente", "descendente", "plana")
        
        Returns:
            True si la señal es válida
        
        Raises:
            ValidationError: Si la señal viola reglas VWAP
        """
        # NO_TRADE siempre es válido
        if parsed.action == TradingAction.NO_TRADE:
            return True
        
        # Validar LONG solo con VWAP ascendente
        if parsed.action == TradingAction.LONG:
            if vwap_slope != "ascendente":
                raise ValidationError(
                    f"Señal LONG rechazada: VWAP {vwap_slope}, "
                    f"debe ser ascendente (contra tendencia prohibido)"
                )
        
        # Validar SHORT solo con VWAP descendente
        if parsed.action == TradingAction.SHORT:
            if vwap_slope != "descendente":
                raise ValidationError(
                    f"Señal SHORT rechazada: VWAP {vwap_slope}, "
                    f"debe ser descendente (contra tendencia prohibido)"
                )
        
        return True
    
    def validate_stop_loss(self, parsed: ParsedResponse) -> bool:
        """
        Valida que el stop loss esté en la dirección correcta.
        
        Args:
            parsed: Respuesta parseada
        
        Returns:
            True si el stop loss es válido
        
        Raises:
            ValidationError: Si el stop loss es inválido
        """
        if parsed.action == TradingAction.NO_TRADE:
            return True
        
        if parsed.entry_price is None or parsed.stop_loss is None:
            return True  # No se puede validar sin precios
        
        # LONG: stop loss debe estar ABAJO de entrada
        if parsed.action == TradingAction.LONG:
            if parsed.stop_loss >= parsed.entry_price:
                raise ValidationError(
                    f"Stop loss inválido para LONG: SL {parsed.stop_loss} >= "
                    f"Entry {parsed.entry_price} (debe estar abajo)"
                )
        
        # SHORT: stop loss debe estar ARRIBA de entrada
        if parsed.action == TradingAction.SHORT:
            if parsed.stop_loss <= parsed.entry_price:
                raise ValidationError(
                    f"Stop loss inválido para SHORT: SL {parsed.stop_loss} <= "
                    f"Entry {parsed.entry_price} (debe estar arriba)"
                )
        
        return True
    
    def validate_take_profit(self, parsed: ParsedResponse) -> bool:
        """
        Valida que el take profit esté en la dirección correcta.
        
        Args:
            parsed: Respuesta parseada
        
        Returns:
            True si el take profit es válido
        
        Raises:
            ValidationError: Si el take profit es inválido
        """
        if parsed.action == TradingAction.NO_TRADE:
            return True
        
        if parsed.entry_price is None or parsed.take_profit is None:
            return True
        
        # LONG: take profit debe estar ARRIBA de entrada
        if parsed.action == TradingAction.LONG:
            if parsed.take_profit <= parsed.entry_price:
                raise ValidationError(
                    f"Take profit inválido para LONG: TP {parsed.take_profit} <= "
                    f"Entry {parsed.entry_price} (debe estar arriba)"
                )
        
        # SHORT: take profit debe estar ABAJO de entrada
        if parsed.action == TradingAction.SHORT:
            if parsed.take_profit >= parsed.entry_price:
                raise ValidationError(
                    f"Take profit inválido para SHORT: TP {parsed.take_profit} >= "
                    f"Entry {parsed.entry_price} (debe estar abajo)"
                )
        
        return True
    
    def convert_to_bot_format(self, parsed: ParsedResponse) -> Dict[str, Any]:
        """
        Convierte la respuesta parseada al formato que espera el bot.
        
        Args:
            parsed: Respuesta parseada
        
        Returns:
            Diccionario en formato bot
        """
        # Determinar acción del bot
        if parsed.action == TradingAction.NO_TRADE:
            bot_action = "esperar"
        else:
            bot_action = "abrir"
        
        # Dirección
        bot_direction = None
        if parsed.direction:
            bot_direction = parsed.direction.value
        
        return {
            "accion": bot_action,
            "direccion": bot_direction,
            "precio_entrada": parsed.entry_price,
            "stop_loss": parsed.stop_loss,
            "take_profit": parsed.take_profit,
            "take_profit_1": parsed.take_profit_1,
            "take_profit_2": parsed.take_profit_2,
            "confianza": parsed.confidence_score,
            "razonamiento": parsed.reasoning or "",
            "estado_mercado": parsed.market_state or ""
        }
