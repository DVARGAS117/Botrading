"""
LotAdjuster - Ajuste de lote a step y límites del símbolo - T30

Este módulo ajusta el tamaño de lote calculado a las restricciones del símbolo:
- Mínimo de volumen (volume_min)
- Máximo de volumen (volume_max)
- Incremento permitido (volume_step)

Garantiza que las órdenes enviadas a MT5 cumplan con las reglas del broker.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T30 - Ajuste de lote a step y límites del símbolo
"""

from dataclasses import dataclass
from typing import Optional
import logging
import math


# ============================================================================
# EXCEPCIONES
# ============================================================================

class LotAdjusterError(Exception):
    """Excepción base para errores del LotAdjuster"""
    pass


class InvalidLotSizeError(LotAdjusterError):
    """Excepción para tamaños de lote inválidos"""
    pass


class InvalidSymbolSpecError(LotAdjusterError):
    """Excepción para especificaciones de símbolo inválidas"""
    pass


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class SymbolSpecification:
    """
    Especificaciones de volumen de un símbolo de trading.
    
    Attributes:
        symbol: Nombre del símbolo (ej: "EURUSD", "XAUUSD")
        volume_min: Volumen mínimo permitido por el broker
        volume_max: Volumen máximo permitido por el broker
        volume_step: Incremento de volumen (ej: 0.01, 0.1)
    """
    symbol: str
    volume_min: float
    volume_max: float
    volume_step: float
    
    def __post_init__(self):
        """Validar especificaciones al inicializar"""
        if self.volume_min <= 0:
            raise InvalidSymbolSpecError(
                f"volume_min must be positive, got {self.volume_min}"
            )
        
        if self.volume_max <= 0:
            raise InvalidSymbolSpecError(
                f"volume_max must be positive, got {self.volume_max}"
            )
        
        if self.volume_min > self.volume_max:
            raise InvalidSymbolSpecError(
                f"volume_min ({self.volume_min}) cannot be greater than "
                f"volume_max ({self.volume_max})"
            )
        
        if self.volume_step <= 0:
            raise InvalidSymbolSpecError(
                f"volume_step must be positive, got {self.volume_step}"
            )


@dataclass
class AdjustedLot:
    """
    Resultado del ajuste de lote.
    
    Attributes:
        adjusted_lot: Tamaño de lote después del ajuste
        original_lot: Tamaño de lote original antes del ajuste
        was_adjusted: Si el lote fue modificado
        reason: Razón del ajuste o confirmación
        symbol: Símbolo para el cual se ajustó
    """
    adjusted_lot: float
    original_lot: float
    was_adjusted: bool
    reason: str
    symbol: str
    
    def to_dict(self) -> dict:
        """Convertir a diccionario"""
        return {
            "adjusted_lot": self.adjusted_lot,
            "original_lot": self.original_lot,
            "was_adjusted": self.was_adjusted,
            "reason": self.reason,
            "symbol": self.symbol
        }
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        status = "adjusted" if self.was_adjusted else "unchanged"
        return (
            f"<AdjustedLot({self.symbol}: {self.original_lot} -> "
            f"{self.adjusted_lot}, {status})>"
        )


# ============================================================================
# LOT ADJUSTER
# ============================================================================

class LotAdjuster:
    """
    Ajustador de tamaño de lote a las restricciones del símbolo.
    
    Este módulo garantiza que el tamaño de lote cumpla con:
    - Volumen mínimo del broker
    - Volumen máximo del broker
    - Incremento permitido (step)
    
    Es utilizado por PositionSizer y OrderManager para validar lotes
    antes de enviar órdenes a MT5.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializar LotAdjuster.
        
        Args:
            logger: Logger opcional para registrar operaciones
        """
        self.logger = logger or self._create_default_logger()
    
    def _create_default_logger(self) -> logging.Logger:
        """Crear logger por defecto"""
        logger = logging.getLogger("LotAdjuster")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def adjust_lot(
        self,
        lot_size: float,
        symbol_spec: SymbolSpecification
    ) -> AdjustedLot:
        """
        Ajustar tamaño de lote a las restricciones del símbolo.
        
        Proceso de ajuste:
        1. Validar entrada
        2. Verificar mínimo
        3. Verificar máximo
        4. Redondear al step más cercano
        5. Re-verificar límites después del redondeo
        
        Args:
            lot_size: Tamaño de lote a ajustar
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            AdjustedLot con el lote ajustado y metadata
        
        Raises:
            InvalidLotSizeError: Si lot_size es inválido
            InvalidSymbolSpecError: Si symbol_spec es inválido
        
        Example:
            >>> adjuster = LotAdjuster()
            >>> spec = SymbolSpecification("EURUSD", 0.01, 100.0, 0.01)
            >>> result = adjuster.adjust_lot(0.456, spec)
            >>> print(result.adjusted_lot)  # 0.46
        """
        # Validar entrada
        self._validate_inputs(lot_size, symbol_spec)
        
        original_lot = lot_size
        adjusted = False
        reason = "Lot within limits"
        
        # 1. Verificar mínimo
        if lot_size < symbol_spec.volume_min:
            lot_size = symbol_spec.volume_min
            adjusted = True
            reason = f"Adjusted from {original_lot} to minimum {lot_size}"
            self.logger.warning(
                f"{symbol_spec.symbol}: Lot {original_lot} below minimum "
                f"{symbol_spec.volume_min}, adjusted to {lot_size}"
            )
        
        # 2. Verificar máximo
        elif lot_size > symbol_spec.volume_max:
            lot_size = symbol_spec.volume_max
            adjusted = True
            reason = f"Adjusted from {original_lot} to maximum {lot_size}"
            self.logger.warning(
                f"{symbol_spec.symbol}: Lot {original_lot} above maximum "
                f"{symbol_spec.volume_max}, adjusted to {lot_size}"
            )
        
        # 3. Redondear al step más cercano
        else:
            # Calcular cuántos steps hay en el lote
            steps = lot_size / symbol_spec.volume_step
            rounded_steps = round(steps)
            new_lot_size = rounded_steps * symbol_spec.volume_step
            
            # Redondear a 2 decimales para evitar problemas de punto flotante
            new_lot_size = round(new_lot_size, 2)
            
            # Verificar si hubo cambio significativo
            if abs(new_lot_size - lot_size) > 0.0001:
                adjusted = True
                reason = f"Lot rounded to step {symbol_spec.volume_step}"
                self.logger.info(
                    f"{symbol_spec.symbol}: Lot {lot_size} rounded to "
                    f"{new_lot_size} (step: {symbol_spec.volume_step})"
                )
            
            lot_size = new_lot_size
            
            # 4. Re-verificar límites después del redondeo
            if lot_size < symbol_spec.volume_min:
                lot_size = symbol_spec.volume_min
                adjusted = True
                reason = f"After rounding, adjusted to minimum {lot_size}"
            elif lot_size > symbol_spec.volume_max:
                # Redondear hacia abajo en lugar de hacia arriba
                rounded_steps = math.floor(steps)
                lot_size = round(rounded_steps * symbol_spec.volume_step, 2)
                adjusted = True
                reason = f"After rounding, adjusted to maximum {lot_size}"
        
        # Log del resultado
        if adjusted:
            self.logger.debug(
                f"Adjusted lot for {symbol_spec.symbol}: "
                f"{original_lot} -> {lot_size}"
            )
        else:
            self.logger.debug(
                f"Lot for {symbol_spec.symbol} unchanged: {lot_size}"
            )
        
        return AdjustedLot(
            adjusted_lot=lot_size,
            original_lot=original_lot,
            was_adjusted=adjusted,
            reason=reason,
            symbol=symbol_spec.symbol
        )
    
    def _validate_inputs(
        self,
        lot_size: float,
        symbol_spec: SymbolSpecification
    ) -> None:
        """
        Validar entradas antes de ajustar.
        
        Args:
            lot_size: Tamaño de lote
            symbol_spec: Especificaciones del símbolo
        
        Raises:
            InvalidLotSizeError: Si lot_size es inválido
            InvalidSymbolSpecError: Si symbol_spec es inválido
        """
        if lot_size is None:
            raise InvalidLotSizeError("Lot size cannot be None")
        
        if not isinstance(lot_size, (int, float)):
            raise InvalidLotSizeError(
                f"Lot size must be a number, got {type(lot_size)}"
            )
        
        if lot_size <= 0:
            raise InvalidLotSizeError(
                f"Lot size must be positive, got {lot_size}"
            )
        
        if symbol_spec is None:
            raise InvalidSymbolSpecError("SymbolSpecification cannot be None")
        
        if not isinstance(symbol_spec, SymbolSpecification):
            raise InvalidSymbolSpecError(
                f"symbol_spec must be SymbolSpecification, "
                f"got {type(symbol_spec)}"
            )
    
    def is_valid_lot(
        self,
        lot_size: float,
        symbol_spec: SymbolSpecification
    ) -> bool:
        """
        Verificar si un lote es válido sin ajustarlo.
        
        Args:
            lot_size: Tamaño de lote a verificar
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            True si el lote es válido, False en caso contrario
        
        Example:
            >>> adjuster.is_valid_lot(0.50, eurusd_spec)
            True
            >>> adjuster.is_valid_lot(0.005, eurusd_spec)
            False
        """
        try:
            self._validate_inputs(lot_size, symbol_spec)
        except (InvalidLotSizeError, InvalidSymbolSpecError):
            return False
        
        # Verificar límites
        if lot_size < symbol_spec.volume_min:
            return False
        
        if lot_size > symbol_spec.volume_max:
            return False
        
        # Verificar que respete el step
        steps = lot_size / symbol_spec.volume_step
        rounded_steps = round(steps)
        expected_lot = round(rounded_steps * symbol_spec.volume_step, 2)
        
        # Permitir pequeña diferencia por punto flotante
        if abs(lot_size - expected_lot) > 0.0001:
            return False
        
        return True
    
    def adjust_lot_for_buy(
        self,
        lot_size: float,
        symbol_spec: SymbolSpecification
    ) -> AdjustedLot:
        """
        Método de conveniencia para ajustar lote de posición BUY.
        
        Args:
            lot_size: Tamaño de lote
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            AdjustedLot
        """
        return self.adjust_lot(lot_size, symbol_spec)
    
    def adjust_lot_for_sell(
        self,
        lot_size: float,
        symbol_spec: SymbolSpecification
    ) -> AdjustedLot:
        """
        Método de conveniencia para ajustar lote de posición SELL.
        
        Args:
            lot_size: Tamaño de lote
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            AdjustedLot
        """
        return self.adjust_lot(lot_size, symbol_spec)
