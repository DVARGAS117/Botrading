"""
Tests unitarios para OrderManager - T09: Envío de órdenes y gestión de SL/TP/cierre.

Este módulo implementa pruebas exhaustivas para la gestión de órdenes en MT5:
- Envío de órdenes Market
- Envío de órdenes Limit (pending orders)
- Modificación de SL/TP en posiciones abiertas
- Cierre de posiciones
- Validaciones y manejo de errores

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T09
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from dataclasses import dataclass

# Importar clases a testear (se crearán después)
from src.core.order_manager import (
    OrderManager,
    OrderType,
    OrderRequest,
    OrderResult,
    OrderManagerError,
    InvalidOrderParametersError,
    OrderExecutionError
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_mt5():
    """Mock del módulo MetaTrader5"""
    with patch('src.core.order_manager.mt5') as mock:
        # Configurar constantes MT5
        mock.ORDER_TYPE_BUY = 0
        mock.ORDER_TYPE_SELL = 1
        mock.ORDER_TYPE_BUY_LIMIT = 2
        mock.ORDER_TYPE_SELL_LIMIT = 3
        mock.ORDER_TYPE_BUY_STOP = 4
        mock.ORDER_TYPE_SELL_STOP = 5
        mock.TRADE_ACTION_DEAL = 1
        mock.TRADE_ACTION_PENDING = 5
        mock.TRADE_ACTION_SLTP = 2
        mock.TRADE_ACTION_REMOVE = 3
        mock.ORDER_FILLING_IOC = 1
        mock.ORDER_FILLING_FOK = 2
        mock.ORDER_TIME_GTC = 0
        mock.ORDER_TIME_SPECIFIED = 1
        mock.TRADE_RETCODE_DONE = 10009
        
        yield mock


@pytest.fixture
def mock_connector(mock_mt5):
    """Mock del MT5Connector"""
    connector = Mock()
    connector.is_connected.return_value = True
    connector._mt5 = mock_mt5
    return connector


@pytest.fixture
def mock_logger():
    """Mock del logger"""
    return Mock()


@pytest.fixture
def order_manager(mock_connector, mock_logger, mock_mt5):
    """Fixture que crea una instancia de OrderManager"""
    return OrderManager(mock_connector, logger=mock_logger)


# ==================== TESTS DE INICIALIZACIÓN ====================

def test_order_manager_initialization_success(mock_connector, mock_logger, mock_mt5):
    """Test: OrderManager se inicializa correctamente"""
    manager = OrderManager(mock_connector, logger=mock_logger)
    
    assert manager.connector == mock_connector
    assert manager.logger == mock_logger
    mock_connector.is_connected.assert_called_once()


def test_order_manager_initialization_not_connected(mock_logger, mock_mt5):
    """Test: OrderManager lanza error si connector no está conectado"""
    connector = Mock()
    connector.is_connected.return_value = False
    
    with pytest.raises(OrderManagerError, match="no está conectado"):
        OrderManager(connector, logger=mock_logger)


def test_order_manager_initialization_creates_default_logger(mock_connector, mock_mt5):
    """Test: OrderManager crea logger por defecto si no se proporciona"""
    manager = OrderManager(mock_connector)
    
    assert manager.logger is not None


# ==================== TESTS DE ENVÍO DE ÓRDENES MARKET ====================

def test_send_market_order_buy_success(order_manager, mock_mt5):
    """Test: Enviar orden Market BUY exitosamente"""
    # Configurar mock
    mock_result = Mock()
    mock_result.retcode = 10009  # TRADE_RETCODE_DONE
    mock_result.order = 123456
    mock_result.deal = 123457
    mock_result.volume = 0.1
    mock_result.price = 1.1000
    mock_result.comment = "Request executed"
    
    mock_mt5.order_send.return_value = mock_result
    
    # Crear solicitud
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.1,
        price=1.1000,
        sl=1.0950,
        tp=1.1100,
        magic=100001,
        comment="Test BUY"
    )
    
    # Ejecutar
    result = order_manager.send_market_order(request)
    
    # Verificar
    assert result.success is True
    assert result.order == 123456
    assert result.deal == 123457
    assert result.volume == 0.1
    assert result.price == 1.1000
    assert result.retcode == 10009
    
    # Verificar que se llamó a order_send
    mock_mt5.order_send.assert_called_once()


def test_send_market_order_sell_success(order_manager, mock_mt5):
    """Test: Enviar orden Market SELL exitosamente"""
    # Configurar mock
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.order = 123458
    mock_result.deal = 123459
    mock_result.volume = 0.1
    mock_result.price = 1.0950
    mock_result.comment = "Request executed"
    
    mock_mt5.order_send.return_value = mock_result
    
    # Crear solicitud
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.SELL,
        volume=0.1,
        price=1.0950,
        sl=1.1000,
        tp=1.0850,
        magic=100001,
        comment="Test SELL"
    )
    
    # Ejecutar
    result = order_manager.send_market_order(request)
    
    # Verificar
    assert result.success is True
    assert result.order == 123458
    assert result.deal == 123459


def test_send_market_order_invalid_parameters(order_manager):
    """Test: Orden Market con parámetros inválidos lanza error"""
    # Volume negativo
    with pytest.raises(InvalidOrderParametersError, match="volumen debe ser mayor a 0"):
        request = OrderRequest(
            symbol="EURUSD",
            order_type=OrderType.BUY,
            volume=-0.1,
            price=1.1000
        )
        order_manager.send_market_order(request)
    
    # Símbolo vacío
    with pytest.raises(InvalidOrderParametersError, match="símbolo es requerido"):
        request = OrderRequest(
            symbol="",
            order_type=OrderType.BUY,
            volume=0.1,
            price=1.1000
        )
        order_manager.send_market_order(request)


def test_send_market_order_execution_failed(order_manager, mock_mt5):
    """Test: Orden Market falla en ejecución"""
    # Configurar mock para retornar error
    mock_result = Mock()
    mock_result.retcode = 10013  # TRADE_RETCODE_INVALID_PRICE
    mock_result.comment = "Invalid price"
    
    mock_mt5.order_send.return_value = mock_result
    
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.1,
        price=1.1000
    )
    
    # Debería lanzar excepción
    with pytest.raises(OrderExecutionError, match="Error al ejecutar orden"):
        order_manager.send_market_order(request)


def test_send_market_order_mt5_returns_none(order_manager, mock_mt5):
    """Test: MT5 retorna None al enviar orden"""
    mock_mt5.order_send.return_value = None
    
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.1,
        price=1.1000
    )
    
    with pytest.raises(OrderExecutionError, match="retornó None"):
        order_manager.send_market_order(request)


# ==================== TESTS DE ÓRDENES LIMIT ====================

def test_send_limit_order_buy_success(order_manager, mock_mt5):
    """Test: Enviar orden BUY LIMIT exitosamente"""
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.order = 123460
    mock_result.volume = 0.1
    mock_result.price = 1.0950
    mock_result.comment = "Request executed"
    
    mock_mt5.order_send.return_value = mock_result
    
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY_LIMIT,
        volume=0.1,
        price=1.0950,  # Precio límite
        sl=1.0900,
        tp=1.1050,
        magic=100002
    )
    
    result = order_manager.send_limit_order(request)
    
    assert result.success is True
    assert result.order == 123460


def test_send_limit_order_sell_success(order_manager, mock_mt5):
    """Test: Enviar orden SELL LIMIT exitosamente"""
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.order = 123461
    mock_result.volume = 0.1
    mock_result.price = 1.1050
    
    mock_mt5.order_send.return_value = mock_result
    
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.SELL_LIMIT,
        volume=0.1,
        price=1.1050,
        sl=1.1100,
        tp=1.0950,
        magic=100002
    )
    
    result = order_manager.send_limit_order(request)
    
    assert result.success is True
    assert result.order == 123461


# ==================== TESTS DE MODIFICACIÓN SL/TP ====================

def test_modify_position_sltp_success(order_manager, mock_mt5):
    """Test: Modificar SL/TP de una posición exitosamente"""
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.comment = "Request executed"
    
    mock_mt5.order_send.return_value = mock_result
    
    # Modificar
    result = order_manager.modify_position(
        ticket=123456,
        sl=1.0950,
        tp=1.1100
    )
    
    assert result.success is True
    assert result.retcode == 10009


def test_modify_position_only_sl(order_manager, mock_mt5):
    """Test: Modificar solo SL (sin cambiar TP)"""
    mock_result = Mock()
    mock_result.retcode = 10009
    
    mock_mt5.order_send.return_value = mock_result
    
    result = order_manager.modify_position(
        ticket=123456,
        sl=1.0950,
        tp=0.0  # No modificar TP
    )
    
    assert result.success is True


def test_modify_position_only_tp(order_manager, mock_mt5):
    """Test: Modificar solo TP (sin cambiar SL)"""
    mock_result = Mock()
    mock_result.retcode = 10009
    
    mock_mt5.order_send.return_value = mock_result
    
    result = order_manager.modify_position(
        ticket=123456,
        sl=0.0,  # No modificar SL
        tp=1.1100
    )
    
    assert result.success is True


def test_modify_position_invalid_ticket(order_manager):
    """Test: Modificar posición con ticket inválido"""
    with pytest.raises(ValueError, match="Ticket debe ser mayor a 0"):
        order_manager.modify_position(ticket=-1, sl=1.0950, tp=1.1100)
    
    with pytest.raises(ValueError, match="Ticket debe ser mayor a 0"):
        order_manager.modify_position(ticket=0, sl=1.0950, tp=1.1100)


def test_modify_position_no_changes(order_manager):
    """Test: Modificar posición sin cambios (SL=0 y TP=0)"""
    with pytest.raises(InvalidOrderParametersError, match="Debe especificar al menos SL o TP"):
        order_manager.modify_position(ticket=123456, sl=0.0, tp=0.0)


def test_modify_position_failed(order_manager, mock_mt5):
    """Test: Modificación de SL/TP falla"""
    mock_result = Mock()
    mock_result.retcode = 10015  # TRADE_RETCODE_INVALID_STOPS
    mock_result.comment = "Invalid stops"
    
    mock_mt5.order_send.return_value = mock_result
    
    with pytest.raises(OrderExecutionError, match="Error al modificar posición"):
        order_manager.modify_position(ticket=123456, sl=1.0950, tp=1.1100)


# ==================== TESTS DE CIERRE DE POSICIONES ====================

def test_close_position_success(order_manager, mock_mt5):
    """Test: Cerrar posición exitosamente"""
    # Mock de la posición actual
    mock_position = Mock()
    mock_position.ticket = 123456
    mock_position.symbol = "EURUSD"
    mock_position.volume = 0.1
    mock_position.type = 0  # BUY
    
    mock_mt5.positions_get.return_value = [mock_position]
    
    # Mock del resultado del cierre
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.deal = 123470
    mock_result.comment = "Request executed"
    
    mock_mt5.order_send.return_value = mock_result
    
    # Ejecutar cierre
    result = order_manager.close_position(ticket=123456)
    
    assert result.success is True
    assert result.deal == 123470
    mock_mt5.positions_get.assert_called_once()
    mock_mt5.order_send.assert_called_once()


def test_close_position_not_found(order_manager, mock_mt5):
    """Test: Cerrar posición que no existe"""
    mock_mt5.positions_get.return_value = None
    
    with pytest.raises(OrderExecutionError, match="Posición .* no encontrada"):
        order_manager.close_position(ticket=999999)


def test_close_position_invalid_ticket(order_manager):
    """Test: Cerrar posición con ticket inválido"""
    with pytest.raises(ValueError, match="Ticket debe ser mayor a 0"):
        order_manager.close_position(ticket=-1)


def test_close_position_failed(order_manager, mock_mt5):
    """Test: Falla al cerrar posición"""
    # Mock de la posición
    mock_position = Mock()
    mock_position.ticket = 123456
    mock_position.symbol = "EURUSD"
    mock_position.volume = 0.1
    mock_position.type = 0
    
    mock_mt5.positions_get.return_value = [mock_position]
    
    # Mock de resultado fallido
    mock_result = Mock()
    mock_result.retcode = 10018  # TRADE_RETCODE_MARKET_CLOSED
    mock_result.comment = "Market is closed"
    
    mock_mt5.order_send.return_value = mock_result
    
    with pytest.raises(OrderExecutionError, match="Error al cerrar posición"):
        order_manager.close_position(ticket=123456)


def test_close_position_partial_volume(order_manager, mock_mt5):
    """Test: Cerrar posición con volumen parcial"""
    # Mock de la posición
    mock_position = Mock()
    mock_position.ticket = 123456
    mock_position.symbol = "EURUSD"
    mock_position.volume = 1.0
    mock_position.type = 0
    
    mock_mt5.positions_get.return_value = [mock_position]
    
    # Mock del resultado
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.deal = 123471
    
    mock_mt5.order_send.return_value = mock_result
    
    # Cerrar solo 0.5 lotes
    result = order_manager.close_position(ticket=123456, volume=0.5)
    
    assert result.success is True
    
    # Verificar que se llamó con el volumen correcto
    call_args = mock_mt5.order_send.call_args
    assert call_args[0][0]['volume'] == 0.5


# ==================== TESTS DE VALIDACIONES ====================

def test_order_request_validation():
    """Test: Validación de OrderRequest"""
    # Request válido
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.1,
        price=1.1000
    )
    
    assert request.symbol == "EURUSD"
    assert request.order_type == OrderType.BUY
    assert request.volume == 0.1


def test_order_type_enum():
    """Test: OrderType enum contiene los tipos correctos"""
    assert OrderType.BUY
    assert OrderType.SELL
    assert OrderType.BUY_LIMIT
    assert OrderType.SELL_LIMIT


def test_order_result_to_dict():
    """Test: OrderResult se puede convertir a diccionario"""
    result = OrderResult(
        success=True,
        retcode=10009,
        order=123456,
        deal=123457,
        volume=0.1,
        price=1.1000,
        comment="Test"
    )
    
    result_dict = result.to_dict()
    
    assert result_dict['success'] is True
    assert result_dict['retcode'] == 10009
    assert result_dict['order'] == 123456
    assert result_dict['deal'] == 123457


# ==================== TESTS DE LOGGING ====================

def test_order_manager_logs_market_order(order_manager, mock_logger, mock_mt5):
    """Test: OrderManager registra logs al enviar orden market"""
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.order = 123456
    mock_result.deal = 123457
    
    mock_mt5.order_send.return_value = mock_result
    
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.1,
        price=1.1000
    )
    
    order_manager.send_market_order(request)
    
    # Verificar que se hicieron llamadas de log
    assert mock_logger.info.called


def test_order_manager_logs_position_close(order_manager, mock_logger, mock_mt5):
    """Test: OrderManager registra logs al cerrar posición"""
    mock_position = Mock()
    mock_position.ticket = 123456
    mock_position.symbol = "EURUSD"
    mock_position.volume = 0.1
    mock_position.type = 0
    
    mock_mt5.positions_get.return_value = [mock_position]
    
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.deal = 123470
    
    mock_mt5.order_send.return_value = mock_result
    
    order_manager.close_position(ticket=123456)
    
    assert mock_logger.info.called


# ==================== TESTS DE EDGE CASES ====================

def test_send_market_order_with_deviation(order_manager, mock_mt5):
    """Test: Enviar orden market con desviación de precio"""
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.order = 123456
    
    mock_mt5.order_send.return_value = mock_result
    
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.1,
        price=1.1000,
        deviation=10  # 10 puntos de desviación
    )
    
    result = order_manager.send_market_order(request)
    
    assert result.success is True
    
    # Verificar que se pasó la desviación
    call_args = mock_mt5.order_send.call_args
    assert call_args[0][0]['deviation'] == 10


def test_send_order_with_expiration(order_manager, mock_mt5):
    """Test: Enviar orden limit con tiempo de expiración"""
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.order = 123456
    
    mock_mt5.order_send.return_value = mock_result
    
    expiration = datetime(2025, 12, 31, 23, 59, 59)
    
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY_LIMIT,
        volume=0.1,
        price=1.0950,
        expiration=expiration
    )
    
    result = order_manager.send_limit_order(request)
    
    assert result.success is True


def test_close_all_positions_by_symbol(order_manager, mock_mt5):
    """Test: Cerrar todas las posiciones de un símbolo"""
    # Mock de múltiples posiciones
    positions = [
        Mock(ticket=123456, symbol="EURUSD", volume=0.1, type=0),
        Mock(ticket=123457, symbol="EURUSD", volume=0.2, type=1),
        Mock(ticket=123458, symbol="EURUSD", volume=0.15, type=0)
    ]
    
    mock_mt5.positions_get.return_value = positions
    
    # Mock de resultado exitoso
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.deal = 123470
    
    mock_mt5.order_send.return_value = mock_result
    
    # Cerrar todas las posiciones
    results = order_manager.close_all_positions(symbol="EURUSD")
    
    assert len(results) == 3
    assert all(r.success for r in results)


def test_close_all_positions_by_magic(order_manager, mock_mt5):
    """Test: Cerrar todas las posiciones de un magic number"""
    # Mock de múltiples posiciones
    positions = [
        Mock(ticket=123456, symbol="EURUSD", volume=0.1, type=0, magic=100001),
        Mock(ticket=123457, symbol="GBPUSD", volume=0.2, type=1, magic=100001),
        Mock(ticket=123458, symbol="USDJPY", volume=0.15, type=0, magic=100002)
    ]
    
    mock_mt5.positions_get.return_value = positions
    
    mock_result = Mock()
    mock_result.retcode = 10009
    mock_result.deal = 123470
    
    mock_mt5.order_send.return_value = mock_result
    
    # Cerrar solo las posiciones con magic 100001
    results = order_manager.close_all_positions(magic=100001)
    
    assert len(results) == 2  # Solo 2 posiciones tienen magic 100001


# ==================== TESTS DE INTEGRACIÓN ====================

def test_full_lifecycle_market_order(order_manager, mock_mt5):
    """Test: Ciclo completo - Abrir Market, Modificar SL/TP, Cerrar"""
    # 1. Abrir orden Market
    mock_result_open = Mock()
    mock_result_open.retcode = 10009
    mock_result_open.order = 123456
    mock_result_open.deal = 123457
    mock_result_open.volume = 0.1
    mock_result_open.price = 1.1000
    
    mock_mt5.order_send.return_value = mock_result_open
    
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.1,
        price=1.1000,
        sl=1.0950,
        tp=1.1100,
        magic=100001
    )
    
    result_open = order_manager.send_market_order(request)
    assert result_open.success is True
    
    # 2. Modificar SL/TP
    mock_result_modify = Mock()
    mock_result_modify.retcode = 10009
    mock_mt5.order_send.return_value = mock_result_modify
    
    result_modify = order_manager.modify_position(
        ticket=123456,
        sl=1.0960,  # Nuevo SL
        tp=1.1120   # Nuevo TP
    )
    assert result_modify.success is True
    
    # 3. Cerrar posición
    mock_position = Mock()
    mock_position.ticket = 123456
    mock_position.symbol = "EURUSD"
    mock_position.volume = 0.1
    mock_position.type = 0
    
    mock_mt5.positions_get.return_value = [mock_position]
    
    mock_result_close = Mock()
    mock_result_close.retcode = 10009
    mock_result_close.deal = 123470
    mock_mt5.order_send.return_value = mock_result_close
    
    result_close = order_manager.close_position(ticket=123456)
    assert result_close.success is True


def test_full_lifecycle_limit_order(order_manager, mock_mt5):
    """Test: Ciclo completo - Abrir Limit, esperar activación, Modificar, Cerrar"""
    # 1. Abrir orden Limit
    mock_result_open = Mock()
    mock_result_open.retcode = 10009
    mock_result_open.order = 123460
    
    mock_mt5.order_send.return_value = mock_result_open
    
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY_LIMIT,
        volume=0.1,
        price=1.0950,
        sl=1.0900,
        tp=1.1050,
        magic=100002
    )
    
    result_open = order_manager.send_limit_order(request)
    assert result_open.success is True
    assert result_open.order == 123460
