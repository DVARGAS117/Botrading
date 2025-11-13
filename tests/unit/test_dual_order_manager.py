"""
Tests unitarios para DualOrderManager - T14

Este módulo contiene tests para la funcionalidad de apertura simultánea
de órdenes Market y Limit con los mismos parámetros de riesgo y SL/TP.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T14 - Apertura simultánea de órdenes Market y Limit
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from src.core.dual_order_manager import (
    DualOrderManager,
    DualOrderRequest,
    DualOrderResult,
    DualOrderManagerError,
    InvalidDualOrderParametersError,
    PartialExecutionError
)
from src.core.order_manager import OrderType, OrderResult
from src.core.position_sizer import SymbolSpecification, PositionSize
from src.core.magic_number_generator import MagicNumberGenerator


# ==================== FIXTURES ====================

@pytest.fixture
def mock_connector():
    """Mock de MT5Connector"""
    connector = Mock()
    connector.is_connected.return_value = True
    connector._mt5 = Mock()
    return connector


@pytest.fixture
def mock_order_manager():
    """Mock de OrderManager"""
    manager = Mock()
    manager.send_market_order = Mock()
    manager.send_limit_order = Mock()
    return manager


@pytest.fixture
def mock_position_sizer():
    """Mock de PositionSizer"""
    sizer = Mock()
    return sizer


@pytest.fixture
def mock_magic_number_generator():
    """Mock de MagicNumberGenerator"""
    generator = Mock(spec=MagicNumberGenerator)
    generator.generate = Mock()
    return generator


@pytest.fixture
def symbol_spec():
    """Especificación de símbolo de prueba (EURUSD)"""
    return SymbolSpecification(
        symbol="EURUSD",
        point=0.00001,
        tick_size=0.00001,
        tick_value=1.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        contract_size=100000.0
    )


@pytest.fixture
def dual_order_request(symbol_spec):
    """Request de prueba para orden dual"""
    return DualOrderRequest(
        symbol="EURUSD",
        direction="buy",
        account_balance=10000.0,
        risk_percentage=1.0,
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        limit_price=1.0990,
        bot_id=1,
        ia_config_id=0,
        symbol_spec=symbol_spec,
        comment="Test dual order"
    )


@pytest.fixture
def dual_manager(mock_order_manager, mock_position_sizer, mock_magic_number_generator):
    """Instancia de DualOrderManager con mocks"""
    return DualOrderManager(
        order_manager=mock_order_manager,
        position_sizer=mock_position_sizer,
        magic_number_generator=mock_magic_number_generator
    )


# ==================== TESTS DE INICIALIZACIÓN ====================

def test_dual_order_manager_initialization(dual_manager):
    """Test: Inicialización correcta del DualOrderManager"""
    assert dual_manager is not None
    assert dual_manager.order_manager is not None
    assert dual_manager.position_sizer is not None
    assert dual_manager.magic_generator is not None


def test_dual_order_manager_initialization_without_dependencies():
    """Test: Error al inicializar sin dependencias requeridas"""
    with pytest.raises(TypeError):
        DualOrderManager()


# ==================== TESTS DE VALIDACIÓN DE PARÁMETROS ====================

def test_dual_order_request_validation_success(dual_order_request):
    """Test: Validación exitosa de parámetros de DualOrderRequest"""
    # No debe lanzar excepción
    dual_order_request.validate()


def test_dual_order_request_invalid_symbol():
    """Test: Error con símbolo inválido"""
    with pytest.raises(InvalidDualOrderParametersError):
        request = DualOrderRequest(
            symbol="",  # Vacío
            direction="buy",
            account_balance=10000.0,
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=Mock()
        )
        request.validate()


def test_dual_order_request_invalid_direction():
    """Test: Error con dirección inválida"""
    with pytest.raises(InvalidDualOrderParametersError):
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="invalid",  # Debe ser 'buy' o 'sell'
            account_balance=10000.0,
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=Mock()
        )
        request.validate()


def test_dual_order_request_invalid_balance():
    """Test: Error con balance inválido"""
    with pytest.raises(InvalidDualOrderParametersError):
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="buy",
            account_balance=-1000.0,  # Negativo
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=Mock()
        )
        request.validate()


def test_dual_order_request_invalid_risk_percentage():
    """Test: Error con porcentaje de riesgo inválido"""
    with pytest.raises(InvalidDualOrderParametersError):
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="buy",
            account_balance=10000.0,
            risk_percentage=150.0,  # Más de 100%
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=Mock()
        )
        request.validate()


def test_dual_order_request_invalid_prices():
    """Test: Error con precios inválidos"""
    with pytest.raises(InvalidDualOrderParametersError):
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="buy",
            account_balance=10000.0,
            risk_percentage=1.0,
            entry_price=0.0,  # Precio cero
            stop_loss=1.0950,
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=Mock()
        )
        request.validate()


def test_dual_order_request_buy_invalid_sl():
    """Test: Error en orden BUY con SL por encima del entry"""
    with pytest.raises(InvalidDualOrderParametersError):
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="buy",
            account_balance=10000.0,
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.1050,  # SL debe estar debajo del entry en BUY
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=Mock()
        )
        request.validate()


def test_dual_order_request_sell_invalid_sl():
    """Test: Error en orden SELL con SL por debajo del entry"""
    with pytest.raises(InvalidDualOrderParametersError):
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="sell",
            account_balance=10000.0,
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.0950,  # SL debe estar arriba del entry en SELL
            take_profit=1.0900,
            limit_price=1.1010,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=Mock()
        )
        request.validate()


# ==================== TESTS DE GENERACIÓN DE MAGIC NUMBERS ====================

def test_generate_unique_magic_numbers_for_dual_orders(dual_manager, dual_order_request):
    """Test: Generación de Magic Numbers únicos para Market y Limit"""
    # Configurar mocks
    dual_manager.magic_generator.generate.side_effect = [100000, 100001]
    
    # Generar magic numbers
    market_magic, limit_magic = dual_manager._generate_magic_numbers(
        dual_order_request.bot_id,
        dual_order_request.ia_config_id
    )
    
    # Verificar que sean diferentes
    assert market_magic != limit_magic
    
    # Verificar que se llamó al generador con los parámetros correctos
    assert dual_manager.magic_generator.generate.call_count == 2
    calls = dual_manager.magic_generator.generate.call_args_list
    
    # Primera llamada: Market
    assert calls[0] == call(
        bot_id=1,
        ia_config_id=0,
        order_type="market",
        sequence=0
    )
    
    # Segunda llamada: Limit
    assert calls[1] == call(
        bot_id=1,
        ia_config_id=0,
        order_type="limit",
        sequence=0
    )


# ==================== TESTS DE CÁLCULO DE LOTE ====================

def test_calculate_lot_size_for_dual_orders(dual_manager, dual_order_request):
    """Test: Cálculo de lote con PositionSizer"""
    # Configurar mock de PositionSizer
    expected_lot = 0.20
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=expected_lot,
        risk_amount=100.0,
        pip_distance=50.0,
        pip_value=2.0,
        symbol="EURUSD",
        success=True
    )
    
    # Calcular lote
    lot_size = dual_manager._calculate_lot_size(dual_order_request)
    
    # Verificar resultado
    assert lot_size == expected_lot
    
    # Verificar que se llamó al sizer con los parámetros correctos
    dual_manager.position_sizer.calculate_lot_size.assert_called_once()


# ==================== TESTS DE APERTURA DUAL EXITOSA ====================

def test_open_dual_orders_buy_success(dual_manager, dual_order_request):
    """Test: Apertura exitosa de órdenes Market y Limit para BUY"""
    # Configurar mocks
    dual_manager.magic_generator.generate.side_effect = [100000, 100001]
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=0.10,
        risk_amount=100.0,
        pip_distance=50.0,
        pip_value=1.0,
        symbol="EURUSD",
        success=True
    )
    
    # Mock de resultados de órdenes
    market_result = OrderResult(
        success=True,
        retcode=10009,
        order=12345,
        deal=67890,
        volume=0.10,
        price=1.1000,
        comment="Market order executed"
    )
    
    limit_result = OrderResult(
        success=True,
        retcode=10009,
        order=12346,
        deal=0,  # Limit no tiene deal hasta que se active
        volume=0.10,
        price=1.0990,
        comment="Limit order placed"
    )
    
    dual_manager.order_manager.send_market_order.return_value = market_result
    dual_manager.order_manager.send_limit_order.return_value = limit_result
    
    # Ejecutar
    result = dual_manager.open_dual_orders(dual_order_request)
    
    # Verificar resultado
    assert result.success is True
    assert result.market_order is not None
    assert result.limit_order is not None
    assert result.market_order.order == 12345
    assert result.limit_order.order == 12346
    assert result.market_magic == 100000
    assert result.limit_magic == 100001


def test_open_dual_orders_sell_success(dual_manager):
    """Test: Apertura exitosa de órdenes Market y Limit para SELL"""
    # Crear request para SELL
    symbol_spec = SymbolSpecification(
        symbol="EURUSD",
        point=0.00001,
        tick_size=0.00001,
        tick_value=1.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        contract_size=100000.0
    )
    
    request = DualOrderRequest(
        symbol="EURUSD",
        direction="sell",
        account_balance=10000.0,
        risk_percentage=1.0,
        entry_price=1.1000,
        stop_loss=1.1050,  # SL arriba del entry en SELL
        take_profit=1.0900,  # TP abajo del entry en SELL
        limit_price=1.1010,  # Limit arriba del entry en SELL
        bot_id=1,
        ia_config_id=0,
        symbol_spec=symbol_spec
    )
    
    # Configurar mocks
    dual_manager.magic_generator.generate.side_effect = [100000, 100001]
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=0.10,
        risk_amount=100.0,
        pip_distance=50.0,
        pip_value=1.0,
        symbol="EURUSD",
        success=True
    )
    
    market_result = OrderResult(
        success=True,
        retcode=10009,
        order=12345,
        deal=67890,
        volume=0.10,
        price=1.1000
    )
    
    limit_result = OrderResult(
        success=True,
        retcode=10009,
        order=12346,
        deal=0,
        volume=0.10,
        price=1.1010
    )
    
    dual_manager.order_manager.send_market_order.return_value = market_result
    dual_manager.order_manager.send_limit_order.return_value = limit_result
    
    # Ejecutar
    result = dual_manager.open_dual_orders(request)
    
    # Verificar
    assert result.success is True
    assert result.market_order.order == 12345
    assert result.limit_order.order == 12346


# ==================== TESTS DE MANEJO DE ERRORES PARCIALES ====================

def test_open_dual_orders_market_fails(dual_manager, dual_order_request):
    """Test: Fallo en orden Market, debe lanzar excepción sin crear Limit"""
    # Configurar mocks
    dual_manager.magic_generator.generate.side_effect = [100000, 100001]
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=0.10,
        risk_amount=100.0,
        pip_distance=50.0,
        pip_value=1.0,
        symbol="EURUSD",
        success=True
    )
    
    # Market falla
    from src.core.order_manager import OrderExecutionError
    dual_manager.order_manager.send_market_order.side_effect = OrderExecutionError(
        "Market order failed"
    )
    
    # Ejecutar y verificar excepción
    with pytest.raises(DualOrderManagerError, match="Failed to execute Market order"):
        dual_manager.open_dual_orders(dual_order_request)
    
    # Verificar que NO se intentó enviar Limit
    dual_manager.order_manager.send_limit_order.assert_not_called()


def test_open_dual_orders_limit_fails_after_market_success(dual_manager, dual_order_request):
    """Test: Market exitoso pero Limit falla, debe lanzar PartialExecutionError"""
    # Configurar mocks
    dual_manager.magic_generator.generate.side_effect = [100000, 100001]
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=0.10,
        risk_amount=100.0,
        pip_distance=50.0,
        pip_value=1.0,
        symbol="EURUSD",
        success=True
    )
    
    # Market exitoso
    market_result = OrderResult(
        success=True,
        retcode=10009,
        order=12345,
        deal=67890,
        volume=0.10,
        price=1.1000
    )
    dual_manager.order_manager.send_market_order.return_value = market_result
    
    # Limit falla
    from src.core.order_manager import OrderExecutionError
    dual_manager.order_manager.send_limit_order.side_effect = OrderExecutionError(
        "Limit order failed"
    )
    
    # Ejecutar y verificar excepción
    with pytest.raises(PartialExecutionError) as exc_info:
        dual_manager.open_dual_orders(dual_order_request)
    
    # Verificar que la excepción contiene el resultado parcial
    assert exc_info.value.market_order is not None
    assert exc_info.value.market_order.order == 12345
    assert exc_info.value.market_magic == 100000


# ==================== TESTS DE DUAL ORDER RESULT ====================

def test_dual_order_result_to_dict():
    """Test: Conversión de DualOrderResult a diccionario"""
    market_result = OrderResult(
        success=True,
        retcode=10009,
        order=12345,
        deal=67890,
        volume=0.10,
        price=1.1000
    )
    
    limit_result = OrderResult(
        success=True,
        retcode=10009,
        order=12346,
        deal=0,
        volume=0.10,
        price=1.0990
    )
    
    dual_result = DualOrderResult(
        success=True,
        market_order=market_result,
        limit_order=limit_result,
        market_magic=100000,
        limit_magic=100001,
        lot_size=0.10,
        symbol="EURUSD",
        direction="buy"
    )
    
    # Convertir a dict
    result_dict = dual_result.to_dict()
    
    # Verificar estructura
    assert result_dict['success'] is True
    assert result_dict['symbol'] == "EURUSD"
    assert result_dict['direction'] == "buy"
    assert result_dict['lot_size'] == 0.10
    assert result_dict['market_magic'] == 100000
    assert result_dict['limit_magic'] == 100001
    assert 'market_order' in result_dict
    assert 'limit_order' in result_dict


# ==================== TESTS DE INTEGRACIÓN ====================

def test_full_workflow_buy_dual_orders(dual_manager, dual_order_request):
    """Test de integración: Workflow completo de apertura dual BUY"""
    # Configurar todos los mocks
    dual_manager.magic_generator.generate.side_effect = [100000, 100001]
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=0.15,
        risk_amount=100.0,
        pip_distance=50.0,
        pip_value=1.5,
        symbol="EURUSD",
        success=True
    )
    
    market_result = OrderResult(
        success=True,
        retcode=10009,
        order=12345,
        deal=67890,
        volume=0.15,
        price=1.1000,
        comment="Market BUY executed"
    )
    
    limit_result = OrderResult(
        success=True,
        retcode=10009,
        order=12346,
        deal=0,
        volume=0.15,
        price=1.0990,
        comment="Limit BUY placed"
    )
    
    dual_manager.order_manager.send_market_order.return_value = market_result
    dual_manager.order_manager.send_limit_order.return_value = limit_result
    
    # Ejecutar workflow completo
    result = dual_manager.open_dual_orders(dual_order_request)
    
    # Verificaciones completas
    assert result.success is True
    assert result.symbol == "EURUSD"
    assert result.direction == "buy"
    assert result.lot_size == 0.15
    
    # Verificar Market
    assert result.market_order.order == 12345
    assert result.market_order.price == 1.1000
    assert result.market_magic == 100000
    
    # Verificar Limit
    assert result.limit_order.order == 12346
    assert result.limit_order.price == 1.0990
    assert result.limit_magic == 100001
    
    # Verificar que se llamaron todos los componentes
    dual_manager.magic_generator.generate.assert_called()
    dual_manager.position_sizer.calculate_lot_size.assert_called_once()
    dual_manager.order_manager.send_market_order.assert_called_once()
    dual_manager.order_manager.send_limit_order.assert_called_once()


def test_full_workflow_sell_dual_orders(dual_manager):
    """Test de integración: Workflow completo de apertura dual SELL"""
    # Crear request SELL
    symbol_spec = SymbolSpecification(
        symbol="GBPUSD",
        point=0.00001,
        tick_size=0.00001,
        tick_value=1.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        contract_size=100000.0
    )
    
    request = DualOrderRequest(
        symbol="GBPUSD",
        direction="sell",
        account_balance=10000.0,
        risk_percentage=2.0,
        entry_price=1.2500,
        stop_loss=1.2550,
        take_profit=1.2400,
        limit_price=1.2510,
        bot_id=2,
        ia_config_id=1,
        symbol_spec=symbol_spec
    )
    
    # Configurar mocks
    dual_manager.magic_generator.generate.side_effect = [210000, 210001]
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=0.20,
        risk_amount=200.0,
        pip_distance=50.0,
        pip_value=2.0,
        symbol="GBPUSD",
        success=True
    )
    
    market_result = OrderResult(
        success=True,
        retcode=10009,
        order=22345,
        deal=77890,
        volume=0.20,
        price=1.2500,
        comment="Market SELL executed"
    )
    
    limit_result = OrderResult(
        success=True,
        retcode=10009,
        order=22346,
        deal=0,
        volume=0.20,
        price=1.2510,
        comment="Limit SELL placed"
    )
    
    dual_manager.order_manager.send_market_order.return_value = market_result
    dual_manager.order_manager.send_limit_order.return_value = limit_result
    
    # Ejecutar
    result = dual_manager.open_dual_orders(request)
    
    # Verificar
    assert result.success is True
    assert result.symbol == "GBPUSD"
    assert result.direction == "sell"
    assert result.lot_size == 0.20
    assert result.market_order.order == 22345
    assert result.limit_order.order == 22346
    assert result.market_magic == 210000
    assert result.limit_magic == 210001


# ==================== TESTS DE CASOS EDGE ====================

def test_dual_orders_with_zero_sequence(dual_manager, dual_order_request):
    """Test: Órdenes duales con sequence=0 (primera operación)"""
    dual_manager.magic_generator.generate.side_effect = [100000, 100001]
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=0.10,
        risk_amount=100.0,
        pip_distance=50.0,
        pip_value=1.0,
        symbol="EURUSD",
        success=True
    )
    
    market_result = OrderResult(success=True, retcode=10009, order=1, deal=1, volume=0.10, price=1.1000)
    limit_result = OrderResult(success=True, retcode=10009, order=2, deal=0, volume=0.10, price=1.0990)
    
    dual_manager.order_manager.send_market_order.return_value = market_result
    dual_manager.order_manager.send_limit_order.return_value = limit_result
    
    result = dual_manager.open_dual_orders(dual_order_request)
    
    # Verificar que los magic numbers se generaron con sequence=0
    calls = dual_manager.magic_generator.generate.call_args_list
    assert calls[0][1]['sequence'] == 0
    assert calls[1][1]['sequence'] == 0


def test_dual_orders_with_minimum_lot_size(dual_manager, dual_order_request):
    """Test: Órdenes duales con lote mínimo"""
    dual_manager.magic_generator.generate.side_effect = [100000, 100001]
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=0.01,  # Lote mínimo
        risk_amount=10.0,
        pip_distance=50.0,
        pip_value=0.1,
        symbol="EURUSD",
        success=True
    )
    
    market_result = OrderResult(success=True, retcode=10009, order=1, deal=1, volume=0.01, price=1.1000)
    limit_result = OrderResult(success=True, retcode=10009, order=2, deal=0, volume=0.01, price=1.0990)
    
    dual_manager.order_manager.send_market_order.return_value = market_result
    dual_manager.order_manager.send_limit_order.return_value = limit_result
    
    result = dual_manager.open_dual_orders(dual_order_request)
    
    assert result.success is True
    assert result.lot_size == 0.01


def test_dual_orders_with_high_risk_percentage(dual_manager):
    """Test: Órdenes duales con alto porcentaje de riesgo"""
    symbol_spec = SymbolSpecification(
        symbol="EURUSD",
        point=0.00001,
        tick_size=0.00001,
        tick_value=1.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        contract_size=100000.0
    )
    
    request = DualOrderRequest(
        symbol="EURUSD",
        direction="buy",
        account_balance=10000.0,
        risk_percentage=5.0,  # 5% de riesgo
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        limit_price=1.0990,
        bot_id=1,
        ia_config_id=0,
        symbol_spec=symbol_spec
    )
    
    dual_manager.magic_generator.generate.side_effect = [100000, 100001]
    dual_manager.position_sizer.calculate_lot_size.return_value = PositionSize(
        lot_size=1.00,  # Lote más grande por mayor riesgo
        risk_amount=500.0,
        pip_distance=50.0,
        pip_value=10.0,
        symbol="EURUSD",
        success=True
    )
    
    market_result = OrderResult(success=True, retcode=10009, order=1, deal=1, volume=1.00, price=1.1000)
    limit_result = OrderResult(success=True, retcode=10009, order=2, deal=0, volume=1.00, price=1.0990)
    
    dual_manager.order_manager.send_market_order.return_value = market_result
    dual_manager.order_manager.send_limit_order.return_value = limit_result
    
    result = dual_manager.open_dual_orders(request)
    
    assert result.success is True
    assert result.lot_size == 1.00
