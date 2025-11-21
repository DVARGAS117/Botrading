"""
DualOrderManager - Gestor de apertura simultánea de órdenes Market y Limit - T14

Este módulo implementa la funcionalidad del Ticket T14: Apertura simultánea
de órdenes Market y Limit con los mismos parámetros de SL/TP y riesgo.

Características:
- Apertura simultánea de pares Market/Limit
- Mismo tamaño de lote basado en % de riesgo
- Magic Numbers únicos para cada orden
- Mismos parámetros SL/TP
- Manejo de ejecuciones parciales
- Trazabilidad completa

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T14 - Apertura simultánea de órdenes Market y Limit
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple
import logging

from src.core.order_manager import (
    OrderManager,
    OrderRequest,
    OrderResult,
    OrderType,
    OrderExecutionError
)
from src.core.position_sizer import (
    PositionSizer,
    RiskParameters,
    SymbolSpecification,
    PositionSize
)
from src.core.magic_number_generator import MagicNumberGenerator


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class DualOrderManagerError(Exception):
    """Excepción base para errores del DualOrderManager"""
    pass


class InvalidDualOrderParametersError(DualOrderManagerError):
    """Excepción para parámetros de orden dual inválidos"""
    pass


class PartialExecutionError(DualOrderManagerError):
    """
    Excepción para cuando Market se ejecuta pero Limit falla.
    Incluye el resultado de Market para trazabilidad.
    """
    def __init__(
        self,
        message: str,
        market_order: Optional[OrderResult] = None,
        market_magic: Optional[int] = None
    ):
        super().__init__(message)
        self.market_order = market_order
        self.market_magic = market_magic


# ==================== DATA CLASSES ====================

@dataclass
class DualOrderRequest:
    """
    Solicitud para apertura dual de órdenes Market y Limit.
    
    Attributes:
        symbol: Símbolo del instrumento (ej: "EURUSD")
        direction: Dirección de la orden ("buy" o "sell")
        account_balance: Balance de la cuenta
        risk_percentage: Porcentaje del balance a arriesgar (1-100)
        entry_price: Precio de entrada de referencia para Market
        stop_loss: Precio del Stop Loss
        take_profit: Precio del Take Profit
        limit_price: Precio límite para la orden pendiente
        bot_id: ID del bot (1-5)
        ia_config_id: ID de configuración IA (0-9)
        symbol_spec: Especificaciones del símbolo
        comment: Comentario opcional para las órdenes
        deviation: Desviación máxima permitida para Market (default: 10)
    """
    symbol: str
    direction: str  # "buy" o "sell"
    account_balance: float
    risk_percentage: float
    entry_price: float
    stop_loss: float
    take_profit: float
    limit_price: float
    bot_id: int
    ia_config_id: int
    symbol_spec: SymbolSpecification
    comment: str = ""
    deviation: int = 10
    
    def validate(self) -> None:
        """
        Valida los parámetros de la solicitud dual.
        
        Raises:
            InvalidDualOrderParametersError: Si algún parámetro es inválido
        """
        # Validar símbolo
        if not self.symbol or not self.symbol.strip():
            raise InvalidDualOrderParametersError(
                "El símbolo es requerido y no puede estar vacío"
            )
        
        # Validar dirección
        direction_lower = self.direction.lower()
        if direction_lower not in ('buy', 'sell'):
            raise InvalidDualOrderParametersError(
                f"La dirección debe ser 'buy' o 'sell', recibido: '{self.direction}'"
            )
        
        # Validar balance
        if self.account_balance <= 0:
            raise InvalidDualOrderParametersError(
                f"El balance debe ser mayor a 0, recibido: {self.account_balance}"
            )
        
        # Validar porcentaje de riesgo
        if self.risk_percentage <= 0 or self.risk_percentage > 100:
            raise InvalidDualOrderParametersError(
                f"El porcentaje de riesgo debe estar entre 0 y 100, "
                f"recibido: {self.risk_percentage}"
            )
        
        # Validar precios
        if self.entry_price <= 0:
            raise InvalidDualOrderParametersError(
                f"El precio de entrada debe ser mayor a 0, recibido: {self.entry_price}"
            )
        
        if self.stop_loss <= 0:
            raise InvalidDualOrderParametersError(
                f"El Stop Loss debe ser mayor a 0, recibido: {self.stop_loss}"
            )
        
        if self.take_profit <= 0:
            raise InvalidDualOrderParametersError(
                f"El Take Profit debe ser mayor a 0, recibido: {self.take_profit}"
            )
        
        if self.limit_price <= 0:
            raise InvalidDualOrderParametersError(
                f"El precio límite debe ser mayor a 0, recibido: {self.limit_price}"
            )
        
        # Validar lógica de SL según dirección
        if direction_lower == 'buy':
            # En BUY: SL debe estar debajo del entry
            if self.stop_loss >= self.entry_price:
                raise InvalidDualOrderParametersError(
                    f"Para BUY, el Stop Loss ({self.stop_loss}) debe estar "
                    f"debajo del precio de entrada ({self.entry_price})"
                )
            
            # En BUY: TP debe estar arriba del entry
            if self.take_profit <= self.entry_price:
                raise InvalidDualOrderParametersError(
                    f"Para BUY, el Take Profit ({self.take_profit}) debe estar "
                    f"arriba del precio de entrada ({self.entry_price})"
                )
        
        else:  # sell
            # En SELL: SL debe estar arriba del entry
            if self.stop_loss <= self.entry_price:
                raise InvalidDualOrderParametersError(
                    f"Para SELL, el Stop Loss ({self.stop_loss}) debe estar "
                    f"arriba del precio de entrada ({self.entry_price})"
                )
            
            # En SELL: TP debe estar debajo del entry
            if self.take_profit >= self.entry_price:
                raise InvalidDualOrderParametersError(
                    f"Para SELL, el Take Profit ({self.take_profit}) debe estar "
                    f"debajo del precio de entrada ({self.entry_price})"
                )
        
        # Validar bot_id (aceptar 1-5 legacy o 101-106 nuevos)
        valid_ids = [1, 2, 3, 4, 5, 101, 102, 103, 104, 105, 106]
        if not isinstance(self.bot_id, int) or self.bot_id not in valid_ids:
            raise InvalidDualOrderParametersError(
                f"bot_id debe ser uno de {valid_ids}, recibido: {self.bot_id}"
            )
        
        # Validar ia_config_id
        if not isinstance(self.ia_config_id, int) or not (0 <= self.ia_config_id <= 9):
            raise InvalidDualOrderParametersError(
                f"ia_config_id debe estar entre 0 y 9, recibido: {self.ia_config_id}"
            )


@dataclass
class DualOrderResult:
    """
    Resultado de la apertura dual de órdenes.
    
    Attributes:
        success: Indica si ambas órdenes se ejecutaron exitosamente
        market_order: Resultado de la orden Market
        limit_order: Resultado de la orden Limit
        market_magic: Magic Number de la orden Market
        limit_magic: Magic Number de la orden Limit
        lot_size: Tamaño de lote utilizado
        symbol: Símbolo de las órdenes
        direction: Dirección de las órdenes
        message: Mensaje descriptivo del resultado
    """
    success: bool
    market_order: Optional[OrderResult]
    limit_order: Optional[OrderResult]
    market_magic: int
    limit_magic: int
    lot_size: float
    symbol: str
    direction: str
    message: str = "Dual orders executed successfully"
    
    def to_dict(self) -> dict:
        """
        Convierte el resultado a diccionario.
        
        Returns:
            Dict con todos los campos del resultado
        """
        return {
            'success': self.success,
            'market_order': self.market_order.to_dict() if self.market_order else None,
            'limit_order': self.limit_order.to_dict() if self.limit_order else None,
            'market_magic': self.market_magic,
            'limit_magic': self.limit_magic,
            'lot_size': self.lot_size,
            'symbol': self.symbol,
            'direction': self.direction,
            'message': self.message
        }


# ==================== DUAL ORDER MANAGER ====================

class DualOrderManager:
    """
    Gestor de apertura simultánea de órdenes Market y Limit.
    
    Coordina la apertura de pares de órdenes (Market + Limit) con:
    - Mismo tamaño de lote calculado por riesgo
    - Mismos parámetros SL/TP
    - Magic Numbers únicos para cada orden
    - Manejo robusto de errores parciales
    
    Example:
        >>> from src.core.order_manager import OrderManager
        >>> from src.core.position_sizer import PositionSizer, SymbolSpecification
        >>> from src.core.magic_number_generator import MagicNumberGenerator
        >>> from src.core.dual_order_manager import DualOrderManager, DualOrderRequest
        >>> 
        >>> # Inicializar componentes
        >>> order_manager = OrderManager(connector)
        >>> position_sizer = PositionSizer()
        >>> magic_generator = MagicNumberGenerator()
        >>> 
        >>> # Crear DualOrderManager
        >>> dual_manager = DualOrderManager(
        ...     order_manager=order_manager,
        ...     position_sizer=position_sizer,
        ...     magic_number_generator=magic_generator
        ... )
        >>> 
        >>> # Preparar solicitud
        >>> symbol_spec = SymbolSpecification(...)
        >>> request = DualOrderRequest(
        ...     symbol="EURUSD",
        ...     direction="buy",
        ...     account_balance=10000.0,
        ...     risk_percentage=1.0,
        ...     entry_price=1.1000,
        ...     stop_loss=1.0950,
        ...     take_profit=1.1100,
        ...     limit_price=1.0990,
        ...     bot_id=1,
        ...     ia_config_id=0,
        ...     symbol_spec=symbol_spec
        ... )
        >>> 
        >>> # Abrir órdenes duales
        >>> result = dual_manager.open_dual_orders(request)
        >>> print(f"Market ticket: {result.market_order.order}")
        >>> print(f"Limit ticket: {result.limit_order.order}")
    """
    
    def __init__(
        self,
        order_manager: OrderManager,
        position_sizer: PositionSizer,
        magic_number_generator: MagicNumberGenerator,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el DualOrderManager.
        
        Args:
            order_manager: Gestor de órdenes para MT5
            position_sizer: Calculador de tamaño de posición
            magic_number_generator: Generador de Magic Numbers
            logger: Logger personalizado (opcional)
        """
        self.order_manager = order_manager
        self.position_sizer = position_sizer
        self.magic_generator = magic_number_generator
        
        # Configurar logger
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        
        self.logger.debug("DualOrderManager inicializado correctamente")
    
    # ==================== MÉTODO PRINCIPAL ====================
    
    def open_dual_orders(self, request: DualOrderRequest) -> DualOrderResult:
        """
        Abre simultáneamente órdenes Market y Limit con los mismos parámetros.
        
        Flujo:
        1. Validar parámetros del request
        2. Generar Magic Numbers únicos (Market y Limit)
        3. Calcular tamaño de lote basado en riesgo
        4. Enviar orden Market
        5. Enviar orden Limit
        6. Retornar resultado consolidado
        
        Args:
            request: Solicitud de orden dual con todos los parámetros
        
        Returns:
            DualOrderResult con ambas órdenes ejecutadas
        
        Raises:
            InvalidDualOrderParametersError: Si los parámetros son inválidos
            DualOrderManagerError: Si falla la orden Market
            PartialExecutionError: Si Market se ejecuta pero Limit falla
        
        Example:
            >>> result = dual_manager.open_dual_orders(request)
            >>> print(f"Market magic: {result.market_magic}")
            >>> print(f"Limit magic: {result.limit_magic}")
            >>> print(f"Lot size: {result.lot_size}")
        """
        # 1. Validar request
        self.logger.info(
            f"Iniciando apertura dual {request.direction.upper()} - "
            f"Símbolo: {request.symbol}, Bot: {request.bot_id}"
        )
        request.validate()
        
        # 2. Generar Magic Numbers únicos
        market_magic, limit_magic = self._generate_magic_numbers(
            request.bot_id,
            request.ia_config_id
        )
        
        self.logger.debug(
            f"Magic Numbers generados - Market: {market_magic}, Limit: {limit_magic}"
        )
        
        # 3. Calcular tamaño de lote
        lot_size = self._calculate_lot_size(request)
        
        self.logger.info(
            f"Tamaño de lote calculado: {lot_size} "
            f"(Riesgo: {request.risk_percentage}% de ${request.account_balance})"
        )
        
        # 4. Enviar orden Market
        try:
            market_order = self._send_market_order(
                request=request,
                lot_size=lot_size,
                magic=market_magic
            )
            
            self.logger.info(
                f"Orden Market ejecutada - "
                f"Ticket: {market_order.order}, Precio: {market_order.price}"
            )
        
        except Exception as e:
            error_msg = f"Failed to execute Market order: {e}"
            self.logger.error(error_msg)
            raise DualOrderManagerError(error_msg) from e
        
        # 5. Enviar orden Limit
        try:
            limit_order = self._send_limit_order(
                request=request,
                lot_size=lot_size,
                magic=limit_magic
            )
            
            self.logger.info(
                f"Orden Limit colocada - "
                f"Ticket: {limit_order.order}, Precio límite: {request.limit_price}"
            )
        
        except Exception as e:
            # Si Market se ejecutó pero Limit falla, es ejecución parcial
            error_msg = (
                f"Market order succeeded but Limit order failed: {e}. "
                f"Market ticket: {market_order.order} (magic: {market_magic})"
            )
            self.logger.error(error_msg)
            
            raise PartialExecutionError(
                message=error_msg,
                market_order=market_order,
                market_magic=market_magic
            ) from e
        
        # 6. Retornar resultado consolidado
        result = DualOrderResult(
            success=True,
            market_order=market_order,
            limit_order=limit_order,
            market_magic=market_magic,
            limit_magic=limit_magic,
            lot_size=lot_size,
            symbol=request.symbol,
            direction=request.direction,
            message=(
                f"Dual {request.direction.upper()} orders opened successfully - "
                f"Market: {market_order.order}, Limit: {limit_order.order}"
            )
        )
        
        self.logger.info(
            f"Apertura dual completada exitosamente - "
            f"Symbol: {request.symbol}, Direction: {request.direction.upper()}, "
            f"Lot: {lot_size}, Market: {market_order.order}, Limit: {limit_order.order}"
        )
        
        return result
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    def _generate_magic_numbers(
        self,
        bot_id: int,
        ia_config_id: int,
        sequence: int = 0
    ) -> Tuple[int, int]:
        """
        Genera Magic Numbers únicos para Market y Limit.
        
        Args:
            bot_id: ID del bot
            ia_config_id: ID de configuración IA
            sequence: Número de secuencia (default: 0)
        
        Returns:
            Tupla (market_magic, limit_magic)
        """
        market_magic = self.magic_generator.generate(
            bot_id=bot_id,
            ia_config_id=ia_config_id,
            order_type="market",
            sequence=sequence
        )
        
        limit_magic = self.magic_generator.generate(
            bot_id=bot_id,
            ia_config_id=ia_config_id,
            order_type="limit",
            sequence=sequence
        )
        
        return market_magic, limit_magic
    
    def _calculate_lot_size(self, request: DualOrderRequest) -> float:
        """
        Calcula el tamaño de lote basado en riesgo.
        
        Args:
            request: Solicitud de orden dual
        
        Returns:
            Tamaño de lote calculado
        """
        risk_params = RiskParameters(
            account_balance=request.account_balance,
            risk_percentage=request.risk_percentage,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            symbol_spec=request.symbol_spec
        )
        
        position_size = self.position_sizer.calculate_lot_size(risk_params)
        
        return position_size.lot_size
    
    def _send_market_order(
        self,
        request: DualOrderRequest,
        lot_size: float,
        magic: int
    ) -> OrderResult:
        """
        Envía orden Market (BUY o SELL).
        
        Args:
            request: Solicitud de orden dual
            lot_size: Tamaño de lote calculado
            magic: Magic Number para la orden
        
        Returns:
            OrderResult de la orden Market
        """
        # Determinar tipo de orden según dirección
        if request.direction.lower() == 'buy':
            order_type = OrderType.BUY
        else:
            order_type = OrderType.SELL
        
        # Crear OrderRequest para Market
        order_request = OrderRequest(
            symbol=request.symbol,
            order_type=order_type,
            volume=lot_size,
            price=request.entry_price,
            sl=request.stop_loss,
            tp=request.take_profit,
            magic=magic,
            comment=request.comment or f"Dual Market {request.direction.upper()}",
            deviation=request.deviation
        )
        
        # Enviar orden
        return self.order_manager.send_market_order(order_request)
    
    def _send_limit_order(
        self,
        request: DualOrderRequest,
        lot_size: float,
        magic: int
    ) -> OrderResult:
        """
        Envía orden Limit (BUY_LIMIT o SELL_LIMIT).
        
        Args:
            request: Solicitud de orden dual
            lot_size: Tamaño de lote calculado
            magic: Magic Number para la orden
        
        Returns:
            OrderResult de la orden Limit
        """
        # Determinar tipo de orden según dirección
        if request.direction.lower() == 'buy':
            order_type = OrderType.BUY_LIMIT
        else:
            order_type = OrderType.SELL_LIMIT
        
        # Crear OrderRequest para Limit
        order_request = OrderRequest(
            symbol=request.symbol,
            order_type=order_type,
            volume=lot_size,
            price=request.limit_price,  # Usar precio límite
            sl=request.stop_loss,
            tp=request.take_profit,
            magic=magic,
            comment=request.comment or f"Dual Limit {request.direction.upper()}"
        )
        
        # Enviar orden
        return self.order_manager.send_limit_order(order_request)
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        return "<DualOrderManager>"
    
    def __str__(self) -> str:
        """Representación en string"""
        return "DualOrderManager - Gestor de apertura simultánea Market/Limit"
