"""
PositionSizer - Cálculo de tamaño de posición basado en riesgo - T29

Este módulo calcula el tamaño óptimo de posición (lote) basándose en:
- Porcentaje de riesgo deseado del capital
- Distancia al Stop Loss
- Especificaciones del símbolo (tick value, contract size, etc.)

Normaliza el riesgo entre activos heterogéneos (Forex, Metales, Índices).

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T29 - Cálculo de lote por % riesgo y distancia al SL
"""

from dataclasses import dataclass, field
from typing import Optional
import logging
import math


# ============================================================================
# EXCEPCIONES
# ============================================================================

class PositionSizerError(Exception):
    """Excepción base para errores del PositionSizer"""
    pass


class InvalidRiskParametersError(PositionSizerError):
    """Excepción para parámetros de riesgo inválidos"""
    pass


class InvalidSymbolSpecError(PositionSizerError):
    """Excepción para especificaciones de símbolo inválidas"""
    pass


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class SymbolSpecification:
    """
    Especificaciones de un símbolo de trading.
    
    Attributes:
        symbol: Nombre del símbolo (ej: "EURUSD", "XAUUSD")
        point: Tamaño del punto (ej: 0.00001 para EURUSD)
        tick_size: Tamaño mínimo de movimiento de precio
        tick_value: Valor en dinero de un tick por lote
        volume_min: Volumen mínimo permitido
        volume_max: Volumen máximo permitido
        volume_step: Incremento de volumen (ej: 0.01)
        contract_size: Tamaño del contrato (ej: 100,000 para Forex)
    """
    symbol: str
    point: float
    tick_size: float
    tick_value: float
    volume_min: float
    volume_max: float
    volume_step: float
    contract_size: float
    
    def __post_init__(self):
        """Validar especificaciones al inicializar"""
        if self.point <= 0:
            raise InvalidSymbolSpecError(f"Point must be positive, got {self.point}")
        
        if self.tick_size <= 0:
            raise InvalidSymbolSpecError(f"Tick size must be positive, got {self.tick_size}")
        
        if self.tick_value <= 0:
            raise InvalidSymbolSpecError(f"Tick value must be positive, got {self.tick_value}")
        
        if self.volume_min <= 0:
            raise InvalidSymbolSpecError(f"Volume min must be positive, got {self.volume_min}")
        
        if self.volume_max <= 0:
            raise InvalidSymbolSpecError(f"Volume max must be positive, got {self.volume_max}")
        
        if self.volume_min > self.volume_max:
            raise InvalidSymbolSpecError(
                f"Volume min ({self.volume_min}) cannot be greater than volume max ({self.volume_max})"
            )
        
        if self.volume_step <= 0:
            raise InvalidSymbolSpecError(f"Volume step must be positive, got {self.volume_step}")
        
        if self.contract_size <= 0:
            raise InvalidSymbolSpecError(f"Contract size must be positive, got {self.contract_size}")


@dataclass
class RiskParameters:
    """
    Parámetros para el cálculo de riesgo.
    
    Attributes:
        account_balance: Balance de la cuenta en dinero
        risk_percentage: Porcentaje del balance a arriesgar (1-100)
        entry_price: Precio de entrada planeado
        stop_loss: Precio del Stop Loss
        symbol_spec: Especificaciones del símbolo
    """
    account_balance: float
    risk_percentage: float
    entry_price: float
    stop_loss: float
    symbol_spec: SymbolSpecification
    
    def __post_init__(self):
        """Validar parámetros al inicializar"""
        if self.account_balance <= 0:
            raise InvalidRiskParametersError(
                f"Account balance must be positive, got {self.account_balance}"
            )
        
        if self.risk_percentage <= 0 or self.risk_percentage > 100:
            raise InvalidRiskParametersError(
                f"Risk percentage must be between 0 and 100, got {self.risk_percentage}"
            )
        
        if self.entry_price <= 0:
            raise InvalidRiskParametersError(
                f"Entry price must be positive, got {self.entry_price}"
            )
        
        if self.stop_loss <= 0:
            raise InvalidRiskParametersError(
                f"Stop loss must be positive, got {self.stop_loss}"
            )
        
        if self.entry_price == self.stop_loss:
            raise InvalidRiskParametersError(
                "Stop loss must be different from entry price (distance cannot be zero)"
            )


@dataclass
class PositionSize:
    """
    Resultado del cálculo de tamaño de posición.
    
    Attributes:
        lot_size: Tamaño de lote calculado y ajustado
        risk_amount: Monto de riesgo en dinero
        pip_distance: Distancia al SL en pips
        pip_value: Valor de 1 pip en dinero para el lote calculado
        symbol: Símbolo para el cual se calculó
        success: Si el cálculo fue exitoso
        message: Mensaje descriptivo del resultado
    """
    lot_size: float
    risk_amount: float
    pip_distance: float
    pip_value: float
    symbol: str
    success: bool = True
    message: str = "Position size calculated successfully"
    
    def to_dict(self) -> dict:
        """Convertir a diccionario"""
        return {
            "lot_size": self.lot_size,
            "risk_amount": self.risk_amount,
            "pip_distance": self.pip_distance,
            "pip_value": self.pip_value,
            "symbol": self.symbol,
            "success": self.success,
            "message": self.message
        }


# ============================================================================
# POSITION SIZER
# ============================================================================

class PositionSizer:
    """
    Calculador de tamaño de posición basado en gestión de riesgo.
    
    Calcula el tamaño óptimo de lote para una operación basándose en:
    - Porcentaje de riesgo del capital
    - Distancia al Stop Loss
    - Especificaciones del símbolo
    
    Normaliza el riesgo entre diferentes tipos de activos.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializar PositionSizer.
        
        Args:
            logger: Logger opcional para registrar operaciones
        """
        self.logger = logger or self._create_default_logger()
    
    def _create_default_logger(self) -> logging.Logger:
        """Crear logger por defecto"""
        logger = logging.getLogger("PositionSizer")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def calculate_lot_size(self, risk_params: RiskParameters) -> PositionSize:
        """
        Calcular el tamaño de lote óptimo basado en parámetros de riesgo.
        
        Formula:
        1. Calcular monto de riesgo: account_balance * (risk_percentage / 100)
        2. Calcular distancia en pips: |entry_price - stop_loss| / point
        3. Calcular valor por pip: (tick_value / tick_size) * point
        4. Calcular lote base: risk_amount / (pip_distance * pip_value)
        5. Ajustar a límites del símbolo (min, max, step)
        
        Args:
            risk_params: Parámetros de riesgo y símbolo
        
        Returns:
            PositionSize con el lote calculado y metadata
        """
        try:
            # 1. Calcular monto de riesgo en dinero
            risk_amount = self.calculate_risk_amount(
                risk_params.account_balance,
                risk_params.risk_percentage
            )
            
            # 2. Calcular distancia al SL en precio
            price_distance = abs(risk_params.entry_price - risk_params.stop_loss)
            
            # 3. Convertir distancia a pips
            pip_distance = self.price_distance_to_pips(
                price_distance,
                risk_params.symbol_spec
            )
            
            # 4. Calcular valor de 1 pip por lote
            pip_value_per_lot = self._calculate_pip_value_per_lot(
                risk_params.symbol_spec
            )
            
            # 5. Calcular lote base
            # Lote = Riesgo_$ / (Distancia_pips * Valor_por_pip)
            if pip_distance == 0 or pip_value_per_lot == 0:
                raise PositionSizerError(
                    "Cannot calculate lot size: pip distance or pip value is zero"
                )
            
            lot_size_raw = risk_amount / (pip_distance * pip_value_per_lot)
            
            # 6. Ajustar a límites del símbolo
            lot_size_adjusted = self._adjust_to_symbol_limits(
                lot_size_raw,
                risk_params.symbol_spec
            )
            
            # 7. Log del cálculo
            self.logger.info(
                f"Calculated lot size for {risk_params.symbol_spec.symbol}: "
                f"{lot_size_adjusted:.2f} (risk: ${risk_amount:.2f}, "
                f"SL distance: {pip_distance:.1f} pips)"
            )
            
            # 8. Verificar si hubo ajustes
            if lot_size_raw != lot_size_adjusted:
                if lot_size_adjusted == risk_params.symbol_spec.volume_min:
                    self.logger.warning(
                        f"Lot size adjusted to minimum: {lot_size_adjusted} "
                        f"(calculated: {lot_size_raw:.3f})"
                    )
                elif lot_size_adjusted == risk_params.symbol_spec.volume_max:
                    self.logger.warning(
                        f"Lot size adjusted to maximum: {lot_size_adjusted} "
                        f"(calculated: {lot_size_raw:.3f})"
                    )
            
            # 9. Retornar resultado
            return PositionSize(
                lot_size=lot_size_adjusted,
                risk_amount=risk_amount,
                pip_distance=pip_distance,
                pip_value=pip_value_per_lot * lot_size_adjusted,
                symbol=risk_params.symbol_spec.symbol,
                success=True,
                message=f"Lot size calculated: {lot_size_adjusted}"
            )
        
        except Exception as e:
            self.logger.error(f"Error calculating lot size: {e}")
            raise
    
    def calculate_risk_amount(
        self,
        account_balance: float,
        risk_percentage: float
    ) -> float:
        """
        Calcular el monto de riesgo en dinero.
        
        Args:
            account_balance: Balance de la cuenta
            risk_percentage: Porcentaje a arriesgar (1-100)
        
        Returns:
            Monto de riesgo en dinero
        """
        return account_balance * (risk_percentage / 100.0)
    
    def price_distance_to_pips(
        self,
        price_distance: float,
        symbol_spec: SymbolSpecification
    ) -> float:
        """
        Convertir distancia de precio a pips.
        
        Args:
            price_distance: Distancia en unidades de precio
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            Distancia en pips
        """
        return price_distance / symbol_spec.point
    
    def pips_to_price_distance(
        self,
        pips: float,
        symbol_spec: SymbolSpecification
    ) -> float:
        """
        Convertir pips a distancia de precio.
        
        Args:
            pips: Cantidad de pips
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            Distancia en unidades de precio
        """
        return pips * symbol_spec.point
    
    def _calculate_pip_value_per_lot(
        self,
        symbol_spec: SymbolSpecification
    ) -> float:
        """
        Calcular el valor de 1 pip por lote estándar.
        
        Formula:
        pip_value = (tick_value / tick_size) * point
        
        Ejemplo EURUSD:
        - tick_value = $1
        - tick_size = 0.00001
        - point = 0.00001
        - pip_value = ($1 / 0.00001) * 0.00001 = $1 * 1 = $1
        
        Pero para un lote estándar (100,000 unidades):
        - pip_value_real = $1 * (contract_size / contract_size) = $1
        - Por cada 0.0001 (10 pips) = $10
        
        Args:
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            Valor de 1 pip en dinero
        """
        # Valor por tick
        value_per_tick = symbol_spec.tick_value
        
        # Cantidad de ticks en un pip
        ticks_per_pip = symbol_spec.point / symbol_spec.tick_size
        
        # Valor de 1 pip
        pip_value = value_per_tick * ticks_per_pip
        
        return pip_value
    
    def _adjust_to_symbol_limits(
        self,
        lot_size: float,
        symbol_spec: SymbolSpecification
    ) -> float:
        """
        Ajustar lote a los límites del símbolo (min, max, step).
        
        Args:
            lot_size: Tamaño de lote calculado
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            Lote ajustado a límites
        """
        # 1. Verificar mínimo
        if lot_size < symbol_spec.volume_min:
            return symbol_spec.volume_min
        
        # 2. Verificar máximo
        if lot_size > symbol_spec.volume_max:
            return symbol_spec.volume_max
        
        # 3. Redondear al step más cercano
        # Ejemplo: lot = 0.456, step = 0.01
        # steps = 0.456 / 0.01 = 45.6
        # rounded_steps = 46
        # adjusted = 46 * 0.01 = 0.46
        steps = lot_size / symbol_spec.volume_step
        rounded_steps = round(steps)
        adjusted_lot = rounded_steps * symbol_spec.volume_step
        
        # 4. Asegurar que no excede límites después del redondeo
        if adjusted_lot < symbol_spec.volume_min:
            return symbol_spec.volume_min
        if adjusted_lot > symbol_spec.volume_max:
            # Redondear hacia abajo en lugar de hacia arriba
            rounded_steps = math.floor(steps)
            adjusted_lot = rounded_steps * symbol_spec.volume_step
        
        # 5. Redondear a 2 decimales para evitar problemas de precisión flotante
        return round(adjusted_lot, 2)
    
    def calculate_lot_for_buy(
        self,
        account_balance: float,
        risk_percentage: float,
        entry_price: float,
        stop_loss: float,
        symbol_spec: SymbolSpecification
    ) -> PositionSize:
        """
        Método de conveniencia para calcular lote para posición BUY.
        
        Args:
            account_balance: Balance de la cuenta
            risk_percentage: Porcentaje a arriesgar
            entry_price: Precio de entrada
            stop_loss: Precio de Stop Loss (debe ser < entry_price)
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            PositionSize calculado
        """
        risk_params = RiskParameters(
            account_balance=account_balance,
            risk_percentage=risk_percentage,
            entry_price=entry_price,
            stop_loss=stop_loss,
            symbol_spec=symbol_spec
        )
        return self.calculate_lot_size(risk_params)
    
    def calculate_lot_for_sell(
        self,
        account_balance: float,
        risk_percentage: float,
        entry_price: float,
        stop_loss: float,
        symbol_spec: SymbolSpecification
    ) -> PositionSize:
        """
        Método de conveniencia para calcular lote para posición SELL.
        
        Args:
            account_balance: Balance de la cuenta
            risk_percentage: Porcentaje a arriesgar
            entry_price: Precio de entrada
            stop_loss: Precio de Stop Loss (debe ser > entry_price)
            symbol_spec: Especificaciones del símbolo
        
        Returns:
            PositionSize calculado
        """
        risk_params = RiskParameters(
            account_balance=account_balance,
            risk_percentage=risk_percentage,
            entry_price=entry_price,
            stop_loss=stop_loss,
            symbol_spec=symbol_spec
        )
        return self.calculate_lot_size(risk_params)
