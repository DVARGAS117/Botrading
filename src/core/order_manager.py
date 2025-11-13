"""
OrderManager - Módulo para envío y gestión de órdenes en MT5.

Este módulo implementa la funcionalidad del Ticket T09: Envío de órdenes
y gestión de SL/TP/cierre, proporcionando métodos para:
- Enviar órdenes Market (BUY/SELL)
- Enviar órdenes Limit (BUY_LIMIT/SELL_LIMIT)
- Modificar Stop Loss y Take Profit de posiciones abiertas
- Cerrar posiciones (total o parcial)
- Cerrar múltiples posiciones por filtros

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T09 - Envío de órdenes y gestión de SL/TP/cierre
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # Para entorno de testing


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class OrderManagerError(Exception):
    """Excepción base para errores del OrderManager"""
    pass


class InvalidOrderParametersError(OrderManagerError):
    """Excepción para parámetros de orden inválidos"""
    pass


class OrderExecutionError(OrderManagerError):
    """Excepción para errores en ejecución de órdenes"""
    pass


# ==================== ENUMS ====================

class OrderType(Enum):
    """
    Enum para tipos de órdenes en MT5.
    
    Tipos soportados:
    - BUY: Orden de compra inmediata (Market)
    - SELL: Orden de venta inmediata (Market)
    - BUY_LIMIT: Orden pendiente de compra a precio límite
    - SELL_LIMIT: Orden pendiente de venta a precio límite
    """
    BUY = 0           # ORDER_TYPE_BUY
    SELL = 1          # ORDER_TYPE_SELL
    BUY_LIMIT = 2     # ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = 3    # ORDER_TYPE_SELL_LIMIT
    
    def is_market(self) -> bool:
        """Verifica si es una orden de mercado (no pendiente)"""
        return self in (OrderType.BUY, OrderType.SELL)
    
    def is_limit(self) -> bool:
        """Verifica si es una orden límite (pendiente)"""
        return self in (OrderType.BUY_LIMIT, OrderType.SELL_LIMIT)
    
    def __str__(self) -> str:
        """Retorna el nombre del tipo"""
        return self.name


# ==================== DATA CLASSES ====================

@dataclass
class OrderRequest:
    """
    Solicitud de orden para envío a MT5.
    
    Attributes:
        symbol: Símbolo del instrumento (ej: "EURUSD")
        order_type: Tipo de orden (BUY, SELL, BUY_LIMIT, SELL_LIMIT)
        volume: Volumen en lotes
        price: Precio de entrada (para limit) o referencia (para market)
        sl: Stop Loss (0 = sin SL)
        tp: Take Profit (0 = sin TP)
        magic: Magic Number del bot
        comment: Comentario de la orden
        deviation: Desviación máxima de precio permitida (solo market)
        expiration: Fecha de expiración (solo para órdenes pendientes)
    """
    symbol: str
    order_type: OrderType
    volume: float
    price: float
    sl: float = 0.0
    tp: float = 0.0
    magic: int = 0
    comment: str = ""
    deviation: int = 10
    expiration: Optional[datetime] = None
    
    def validate(self) -> None:
        """
        Valida los parámetros de la orden.
        
        Raises:
            InvalidOrderParametersError: Si algún parámetro es inválido
        """
        if not self.symbol or not self.symbol.strip():
            raise InvalidOrderParametersError("El símbolo es requerido y no puede estar vacío")
        
        if self.volume <= 0:
            raise InvalidOrderParametersError("El volumen debe ser mayor a 0")
        
        if self.price <= 0:
            raise InvalidOrderParametersError("El precio debe ser mayor a 0")
        
        if self.sl < 0:
            raise InvalidOrderParametersError("El SL no puede ser negativo")
        
        if self.tp < 0:
            raise InvalidOrderParametersError("El TP no puede ser negativo")
        
        if self.magic < 0:
            raise InvalidOrderParametersError("El Magic Number no puede ser negativo")


@dataclass
class OrderResult:
    """
    Resultado de una operación de orden.
    
    Attributes:
        success: Indica si la operación fue exitosa
        retcode: Código de retorno de MT5
        order: Número de orden
        deal: Número de deal (si aplica)
        volume: Volumen ejecutado
        price: Precio de ejecución
        comment: Comentario del resultado
        request: Request original (opcional)
    """
    success: bool
    retcode: int
    order: int = 0
    deal: int = 0
    volume: float = 0.0
    price: float = 0.0
    comment: str = ""
    request: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el resultado a diccionario.
        
        Returns:
            Dict con todos los campos del resultado
        """
        return {
            'success': self.success,
            'retcode': self.retcode,
            'order': self.order,
            'deal': self.deal,
            'volume': self.volume,
            'price': self.price,
            'comment': self.comment,
            'request': self.request
        }


# ==================== ORDER MANAGER ====================

class OrderManager:
    """
    Gestor de órdenes para MetaTrader 5.
    
    Proporciona métodos de alto nivel para:
    - Enviar órdenes Market y Limit
    - Modificar SL/TP de posiciones abiertas
    - Cerrar posiciones (individuales o múltiples)
    - Validar parámetros de órdenes
    - Logging detallado de operaciones
    
    Example:
        >>> from src.core.mt5_connector import MT5Connector, BrokerConfig
        >>> from src.core.order_manager import OrderManager, OrderRequest, OrderType
        >>> 
        >>> # Conectar a MT5
        >>> config = BrokerConfig(...)
        >>> connector = MT5Connector(config)
        >>> connector.verify_connection()
        >>> 
        >>> # Crear manager
        >>> manager = OrderManager(connector)
        >>> 
        >>> # Enviar orden Market
        >>> request = OrderRequest(
        ...     symbol="EURUSD",
        ...     order_type=OrderType.BUY,
        ...     volume=0.1,
        ...     price=1.1000,
        ...     sl=1.0950,
        ...     tp=1.1100,
        ...     magic=100001
        ... )
        >>> result = manager.send_market_order(request)
        >>> 
        >>> # Modificar SL/TP
        >>> manager.modify_position(ticket=result.order, sl=1.0960, tp=1.1120)
        >>> 
        >>> # Cerrar posición
        >>> manager.close_position(ticket=result.order)
    """
    
    def __init__(
        self,
        connector,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el OrderManager.
        
        Args:
            connector: Instancia de MT5Connector con conexión activa
            logger: Logger personalizado (usa default si no se proporciona)
        
        Raises:
            OrderManagerError: Si el connector no está conectado
        """
        if not connector.is_connected():
            raise OrderManagerError(
                "MT5 no está conectado. Asegúrese de que el connector "
                "esté conectado antes de crear el manager."
            )
        
        self.connector = connector
        self._mt5 = connector._mt5
        
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
        
        self.logger.debug("OrderManager inicializado correctamente")
    
    # ==================== ENVÍO DE ÓRDENES MARKET ====================
    
    def send_market_order(self, request: OrderRequest) -> OrderResult:
        """
        Envía una orden Market (BUY o SELL) a MT5.
        
        Las órdenes Market se ejecutan inmediatamente al mejor precio disponible.
        
        Args:
            request: Solicitud de orden con todos los parámetros
        
        Returns:
            OrderResult con el resultado de la ejecución
        
        Raises:
            InvalidOrderParametersError: Si los parámetros son inválidos
            OrderExecutionError: Si falla la ejecución
        
        Example:
            >>> request = OrderRequest(
            ...     symbol="EURUSD",
            ...     order_type=OrderType.BUY,
            ...     volume=0.1,
            ...     price=1.1000,
            ...     sl=1.0950,
            ...     tp=1.1100,
            ...     magic=100001
            ... )
            >>> result = manager.send_market_order(request)
            >>> print(f"Orden ejecutada: {result.order}")
        """
        # Validar parámetros
        request.validate()
        
        # Verificar que sea orden Market
        if not request.order_type.is_market():
            raise InvalidOrderParametersError(
                f"send_market_order solo acepta BUY o SELL, "
                f"recibido: {request.order_type}"
            )
        
        self.logger.info(
            f"Enviando orden Market {request.order_type} - "
            f"Símbolo: {request.symbol}, Volumen: {request.volume}, "
            f"SL: {request.sl}, TP: {request.tp}, Magic: {request.magic}"
        )
        
        # Construir request para MT5
        mt5_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": request.symbol,
            "volume": request.volume,
            "type": request.order_type.value,
            "price": request.price,
            "sl": request.sl,
            "tp": request.tp,
            "deviation": request.deviation,
            "magic": request.magic,
            "comment": request.comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Enviar orden
        result = self._mt5.order_send(mt5_request)
        
        # Validar resultado
        if result is None:
            error_msg = "MT5 order_send retornó None"
            self.logger.error(error_msg)
            raise OrderExecutionError(error_msg)
        
        # Verificar código de retorno
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = (
                f"Error al ejecutar orden Market: "
                f"[{result.retcode}] {result.comment}"
            )
            self.logger.error(error_msg)
            raise OrderExecutionError(error_msg)
        
        # Éxito
        self.logger.info(
            f"Orden Market ejecutada exitosamente - "
            f"Ticket: {result.order}, Deal: {result.deal}, "
            f"Precio: {result.price}"
        )
        
        return OrderResult(
            success=True,
            retcode=result.retcode,
            order=result.order,
            deal=result.deal,
            volume=result.volume,
            price=result.price,
            comment=result.comment,
            request=mt5_request
        )
    
    # ==================== ENVÍO DE ÓRDENES LIMIT ====================
    
    def send_limit_order(self, request: OrderRequest) -> OrderResult:
        """
        Envía una orden Limit (BUY_LIMIT o SELL_LIMIT) a MT5.
        
        Las órdenes Limit son pendientes y se activan cuando el precio
        alcanza el nivel especificado.
        
        Args:
            request: Solicitud de orden con precio límite
        
        Returns:
            OrderResult con el resultado del envío
        
        Raises:
            InvalidOrderParametersError: Si los parámetros son inválidos
            OrderExecutionError: Si falla el envío
        
        Example:
            >>> request = OrderRequest(
            ...     symbol="EURUSD",
            ...     order_type=OrderType.BUY_LIMIT,
            ...     volume=0.1,
            ...     price=1.0950,  # Precio límite
            ...     sl=1.0900,
            ...     tp=1.1050,
            ...     magic=100002
            ... )
            >>> result = manager.send_limit_order(request)
        """
        # Validar parámetros
        request.validate()
        
        # Verificar que sea orden Limit
        if not request.order_type.is_limit():
            raise InvalidOrderParametersError(
                f"send_limit_order solo acepta BUY_LIMIT o SELL_LIMIT, "
                f"recibido: {request.order_type}"
            )
        
        self.logger.info(
            f"Enviando orden Limit {request.order_type} - "
            f"Símbolo: {request.symbol}, Volumen: {request.volume}, "
            f"Precio límite: {request.price}, SL: {request.sl}, TP: {request.tp}"
        )
        
        # Construir request para MT5
        mt5_request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": request.symbol,
            "volume": request.volume,
            "type": request.order_type.value,
            "price": request.price,
            "sl": request.sl,
            "tp": request.tp,
            "magic": request.magic,
            "comment": request.comment,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        
        # Agregar expiración si se especificó
        if request.expiration:
            mt5_request["type_time"] = mt5.ORDER_TIME_SPECIFIED
            mt5_request["expiration"] = int(request.expiration.timestamp())
        
        # Enviar orden
        result = self._mt5.order_send(mt5_request)
        
        # Validar resultado
        if result is None:
            error_msg = "MT5 order_send retornó None"
            self.logger.error(error_msg)
            raise OrderExecutionError(error_msg)
        
        # Verificar código de retorno
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = (
                f"Error al enviar orden Limit: "
                f"[{result.retcode}] {result.comment}"
            )
            self.logger.error(error_msg)
            raise OrderExecutionError(error_msg)
        
        # Éxito
        self.logger.info(
            f"Orden Limit enviada exitosamente - "
            f"Orden: {result.order}, Precio límite: {request.price}"
        )
        
        return OrderResult(
            success=True,
            retcode=result.retcode,
            order=result.order,
            volume=result.volume,
            price=request.price,  # Precio límite, no de ejecución
            comment=result.comment,
            request=mt5_request
        )
    
    # ==================== MODIFICACIÓN DE SL/TP ====================
    
    def modify_position(
        self,
        ticket: int,
        sl: float = 0.0,
        tp: float = 0.0
    ) -> OrderResult:
        """
        Modifica el Stop Loss y/o Take Profit de una posición abierta.
        
        Args:
            ticket: Número de ticket de la posición
            sl: Nuevo Stop Loss (0 para mantener actual o eliminar)
            tp: Nuevo Take Profit (0 para mantener actual o eliminar)
        
        Returns:
            OrderResult con el resultado de la modificación
        
        Raises:
            ValueError: Si el ticket es inválido
            InvalidOrderParametersError: Si no se especifica SL ni TP
            OrderExecutionError: Si falla la modificación
        
        Example:
            >>> # Modificar solo SL
            >>> manager.modify_position(ticket=123456, sl=1.0960, tp=0.0)
            >>> 
            >>> # Modificar solo TP
            >>> manager.modify_position(ticket=123456, sl=0.0, tp=1.1120)
            >>> 
            >>> # Modificar ambos
            >>> manager.modify_position(ticket=123456, sl=1.0960, tp=1.1120)
        """
        # Validar ticket
        if ticket <= 0:
            raise ValueError("Ticket debe ser mayor a 0")
        
        # Validar que al menos uno se esté modificando
        if sl == 0.0 and tp == 0.0:
            raise InvalidOrderParametersError(
                "Debe especificar al menos SL o TP para modificar"
            )
        
        self.logger.info(
            f"Modificando posición {ticket} - "
            f"Nuevo SL: {sl}, Nuevo TP: {tp}"
        )
        
        # Construir request para MT5
        mt5_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": sl,
            "tp": tp,
        }
        
        # Enviar modificación
        result = self._mt5.order_send(mt5_request)
        
        # Validar resultado
        if result is None:
            error_msg = f"MT5 order_send retornó None al modificar posición {ticket}"
            self.logger.error(error_msg)
            raise OrderExecutionError(error_msg)
        
        # Verificar código de retorno
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = (
                f"Error al modificar posición {ticket}: "
                f"[{result.retcode}] {result.comment}"
            )
            self.logger.error(error_msg)
            raise OrderExecutionError(error_msg)
        
        # Éxito
        self.logger.info(
            f"Posición {ticket} modificada exitosamente - "
            f"SL: {sl}, TP: {tp}"
        )
        
        return OrderResult(
            success=True,
            retcode=result.retcode,
            order=ticket,
            comment=result.comment,
            request=mt5_request
        )
    
    # ==================== CIERRE DE POSICIONES ====================
    
    def close_position(
        self,
        ticket: int,
        volume: Optional[float] = None,
        deviation: int = 10
    ) -> OrderResult:
        """
        Cierra una posición abierta (total o parcialmente).
        
        Args:
            ticket: Número de ticket de la posición a cerrar
            volume: Volumen a cerrar (None = cerrar toda la posición)
            deviation: Desviación máxima de precio permitida
        
        Returns:
            OrderResult con el resultado del cierre
        
        Raises:
            ValueError: Si el ticket es inválido
            OrderExecutionError: Si la posición no existe o falla el cierre
        
        Example:
            >>> # Cerrar posición completa
            >>> manager.close_position(ticket=123456)
            >>> 
            >>> # Cerrar parcialmente (0.5 lotes)
            >>> manager.close_position(ticket=123456, volume=0.5)
        """
        # Validar ticket
        if ticket <= 0:
            raise ValueError("Ticket debe ser mayor a 0")
        
        self.logger.info(
            f"Cerrando posición {ticket}" +
            (f" - Volumen parcial: {volume}" if volume else " - Cierre total")
        )
        
        # Obtener información de la posición
        positions = self._mt5.positions_get(ticket=ticket)
        
        if positions is None or len(positions) == 0:
            error_msg = f"Posición {ticket} no encontrada"
            self.logger.error(error_msg)
            raise OrderExecutionError(error_msg)
        
        position = positions[0]
        
        # Determinar volumen a cerrar
        close_volume = volume if volume is not None else position.volume
        
        # Determinar tipo de orden opuesta
        if position.type == 0:  # BUY position
            close_type = mt5.ORDER_TYPE_SELL
            close_price = self._mt5.symbol_info_tick(position.symbol).bid
        else:  # SELL position
            close_type = mt5.ORDER_TYPE_BUY
            close_price = self._mt5.symbol_info_tick(position.symbol).ask
        
        # Construir request de cierre
        mt5_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": close_volume,
            "type": close_type,
            "position": ticket,
            "price": close_price,
            "deviation": deviation,
            "magic": position.magic,
            "comment": f"Close position {ticket}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Enviar orden de cierre
        result = self._mt5.order_send(mt5_request)
        
        # Validar resultado
        if result is None:
            error_msg = f"MT5 order_send retornó None al cerrar posición {ticket}"
            self.logger.error(error_msg)
            raise OrderExecutionError(error_msg)
        
        # Verificar código de retorno
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_msg = (
                f"Error al cerrar posición {ticket}: "
                f"[{result.retcode}] {result.comment}"
            )
            self.logger.error(error_msg)
            raise OrderExecutionError(error_msg)
        
        # Éxito
        self.logger.info(
            f"Posición {ticket} cerrada exitosamente - "
            f"Deal: {result.deal}, Volumen: {close_volume}, "
            f"Precio: {close_price}"
        )
        
        return OrderResult(
            success=True,
            retcode=result.retcode,
            order=ticket,
            deal=result.deal,
            volume=close_volume,
            price=close_price,
            comment=result.comment,
            request=mt5_request
        )
    
    # ==================== CIERRE MÚLTIPLE ====================
    
    def close_all_positions(
        self,
        symbol: Optional[str] = None,
        magic: Optional[int] = None
    ) -> List[OrderResult]:
        """
        Cierra múltiples posiciones según filtros.
        
        Args:
            symbol: Símbolo para filtrar (None = todos)
            magic: Magic Number para filtrar (None = todos)
        
        Returns:
            Lista de OrderResult para cada posición cerrada
        
        Example:
            >>> # Cerrar todas las posiciones de EURUSD
            >>> results = manager.close_all_positions(symbol="EURUSD")
            >>> 
            >>> # Cerrar todas las posiciones con magic 100001
            >>> results = manager.close_all_positions(magic=100001)
            >>> 
            >>> # Cerrar todas las posiciones de EURUSD con magic 100001
            >>> results = manager.close_all_positions(symbol="EURUSD", magic=100001)
        """
        self.logger.info(
            f"Cerrando posiciones - "
            f"Símbolo: {symbol or 'Todos'}, Magic: {magic if magic is not None else 'Todos'}"
        )
        
        # Obtener posiciones
        if symbol:
            positions = self._mt5.positions_get(symbol=symbol)
        else:
            positions = self._mt5.positions_get()
        
        if positions is None or len(positions) == 0:
            self.logger.info("No hay posiciones para cerrar")
            return []
        
        # Filtrar por magic si se especificó
        if magic is not None:
            positions = [p for p in positions if p.magic == magic]
        
        # Cerrar cada posición
        results = []
        for position in positions:
            try:
                result = self.close_position(ticket=position.ticket)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"Error al cerrar posición {position.ticket}: {e}"
                )
                # Continuar con las demás posiciones
                results.append(OrderResult(
                    success=False,
                    retcode=-1,
                    order=position.ticket,
                    comment=str(e)
                ))
        
        self.logger.info(
            f"Cerradas {len([r for r in results if r.success])}/{len(results)} posiciones"
        )
        
        return results
