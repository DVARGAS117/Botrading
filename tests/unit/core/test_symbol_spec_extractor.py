"""
Tests unitarios para SymbolSpecificationExtractor - T31

Valida la obtención de especificaciones de símbolos desde MT5.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T31 - Obtención de especificaciones del símbolo desde MT5
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

from src.core.symbol_spec_extractor import (
    SymbolSpecificationExtractor,
    SymbolSpecificationError,
    SymbolNotFoundError
)
from src.core.position_sizer import SymbolSpecification as PositionSizerSpec
from src.core.lot_adjuster import SymbolSpecification as LotAdjusterSpec


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_mt5_connector():
    """Fixture que provee un MT5Connector mockeado"""
    connector = Mock()
    connector.is_connected.return_value = True
    return connector


@pytest.fixture
def mock_eurusd_symbol_info():
    """Fixture con información de símbolo EURUSD"""
    info = MagicMock()
    info.name = "EURUSD"
    info.point = 0.00001
    info.tick_size = 0.00001
    info.tick_value = 1.0
    info.volume_min = 0.01
    info.volume_max = 100.0
    info.volume_step = 0.01
    info.contract_size = 100000.0
    info.digits = 5
    return info


@pytest.fixture
def mock_xauusd_symbol_info():
    """Fixture con información de símbolo XAUUSD (Gold)"""
    info = MagicMock()
    info.name = "XAUUSD"
    info.point = 0.01
    info.tick_size = 0.01
    info.tick_value = 1.0
    info.volume_min = 0.01
    info.volume_max = 50.0
    info.volume_step = 0.01
    info.contract_size = 100.0
    info.digits = 2
    return info


@pytest.fixture
def extractor(mock_mt5_connector):
    """Fixture que provee un SymbolSpecificationExtractor"""
    return SymbolSpecificationExtractor(mock_mt5_connector)


# ============================================================================
# TESTS DE INICIALIZACIÓN
# ============================================================================

def test_extractor_initialization():
    """Test: El extractor se inicializa correctamente con MT5Connector"""
    connector = Mock()
    extractor = SymbolSpecificationExtractor(connector)
    
    assert extractor.connector == connector
    assert extractor.logger is not None


def test_extractor_initialization_without_connector():
    """Test: El extractor requiere un MT5Connector"""
    with pytest.raises(ValueError, match="MT5Connector is required"):
        SymbolSpecificationExtractor(None)


# ============================================================================
# TESTS DE EXTRACCIÓN DE ESPECIFICACIONES
# ============================================================================

def test_extract_symbol_specification_eurusd(
    extractor,
    mock_mt5_connector,
    mock_eurusd_symbol_info
):
    """
    Test: Extraer especificaciones de EURUSD desde MT5
    
    Dado que el bot va a calcular el lote para EURUSD
    Cuando se consultan las especificaciones desde MT5
    Entonces se obtiene un SymbolSpecification con datos reales del símbolo
    """
    # Arrange
    mock_mt5_connector.get_symbol_info.return_value = mock_eurusd_symbol_info
    
    # Act
    spec = extractor.get_symbol_specification("EURUSD")
    
    # Assert
    assert isinstance(spec, PositionSizerSpec)
    assert spec.symbol == "EURUSD"
    assert spec.point == 0.00001
    assert spec.tick_size == 0.00001
    assert spec.tick_value == 1.0
    assert spec.volume_min == 0.01
    assert spec.volume_max == 100.0
    assert spec.volume_step == 0.01
    assert spec.contract_size == 100000.0
    
    # Verificar que se llamó get_symbol_info
    mock_mt5_connector.get_symbol_info.assert_called_once_with("EURUSD")


def test_extract_symbol_specification_xauusd(
    extractor,
    mock_mt5_connector,
    mock_xauusd_symbol_info
):
    """Test: Extraer especificaciones de XAUUSD (Gold) desde MT5"""
    # Arrange
    mock_mt5_connector.get_symbol_info.return_value = mock_xauusd_symbol_info
    
    # Act
    spec = extractor.get_symbol_specification("XAUUSD")
    
    # Assert
    assert spec.symbol == "XAUUSD"
    assert spec.point == 0.01
    assert spec.contract_size == 100.0
    assert spec.volume_max == 50.0


def test_extract_symbol_not_found(extractor, mock_mt5_connector):
    """Test: Error cuando el símbolo no existe en MT5"""
    # Arrange
    mock_mt5_connector.get_symbol_info.side_effect = ValueError(
        "Symbol 'INVALID' not found"
    )
    
    # Act & Assert
    with pytest.raises(SymbolNotFoundError, match="Symbol 'INVALID' not found"):
        extractor.get_symbol_specification("INVALID")


def test_extract_symbol_empty_name(extractor):
    """Test: Error cuando el nombre del símbolo está vacío"""
    with pytest.raises(ValueError, match="Symbol name cannot be empty"):
        extractor.get_symbol_specification("")


def test_extract_symbol_none_name(extractor):
    """Test: Error cuando el nombre del símbolo es None"""
    with pytest.raises(ValueError, match="Symbol name cannot be empty"):
        extractor.get_symbol_specification(None)


# ============================================================================
# TESTS DE CONVERSIÓN A LotAdjuster SymbolSpecification
# ============================================================================

def test_get_lot_adjuster_specification(
    extractor,
    mock_mt5_connector,
    mock_eurusd_symbol_info
):
    """
    Test: Obtener especificación en formato LotAdjuster
    
    Dado que LotAdjuster necesita solo volume_min, volume_max, volume_step
    Cuando se solicita la especificación para LotAdjuster
    Entonces se retorna un objeto LotAdjusterSpec con los campos necesarios
    """
    # Arrange
    mock_mt5_connector.get_symbol_info.return_value = mock_eurusd_symbol_info
    
    # Act
    spec = extractor.get_lot_adjuster_specification("EURUSD")
    
    # Assert
    assert isinstance(spec, LotAdjusterSpec)
    assert spec.symbol == "EURUSD"
    assert spec.volume_min == 0.01
    assert spec.volume_max == 100.0
    assert spec.volume_step == 0.01


# ============================================================================
# TESTS DE CACHÉ DE ESPECIFICACIONES
# ============================================================================

def test_cache_symbol_specification(
    extractor,
    mock_mt5_connector,
    mock_eurusd_symbol_info
):
    """
    Test: Las especificaciones se cachean para evitar múltiples llamadas a MT5
    
    Dado que ya se obtuvo la especificación de un símbolo
    Cuando se solicita nuevamente la misma especificación
    Entonces se retorna desde caché sin llamar a MT5 nuevamente
    """
    # Arrange
    mock_mt5_connector.get_symbol_info.return_value = mock_eurusd_symbol_info
    
    # Act
    spec1 = extractor.get_symbol_specification("EURUSD")
    spec2 = extractor.get_symbol_specification("EURUSD")
    
    # Assert
    assert spec1 == spec2
    # Debe haberse llamado solo una vez a MT5
    assert mock_mt5_connector.get_symbol_info.call_count == 1


def test_clear_cache(
    extractor,
    mock_mt5_connector,
    mock_eurusd_symbol_info
):
    """Test: El caché se puede limpiar"""
    # Arrange
    mock_mt5_connector.get_symbol_info.return_value = mock_eurusd_symbol_info
    
    # Act
    spec1 = extractor.get_symbol_specification("EURUSD")
    extractor.clear_cache()
    spec2 = extractor.get_symbol_specification("EURUSD")
    
    # Assert
    # Debe haberse llamado dos veces a MT5 (una antes y otra después del clear)
    assert mock_mt5_connector.get_symbol_info.call_count == 2


def test_cache_different_symbols(
    extractor,
    mock_mt5_connector,
    mock_eurusd_symbol_info,
    mock_xauusd_symbol_info
):
    """Test: Diferentes símbolos se cachean independientemente"""
    # Arrange
    def get_symbol_side_effect(symbol):
        if symbol == "EURUSD":
            return mock_eurusd_symbol_info
        elif symbol == "XAUUSD":
            return mock_xauusd_symbol_info
        else:
            raise ValueError(f"Symbol '{symbol}' not found")
    
    mock_mt5_connector.get_symbol_info.side_effect = get_symbol_side_effect
    
    # Act
    eurusd_spec = extractor.get_symbol_specification("EURUSD")
    xauusd_spec = extractor.get_symbol_specification("XAUUSD")
    eurusd_spec2 = extractor.get_symbol_specification("EURUSD")
    
    # Assert
    assert eurusd_spec.symbol == "EURUSD"
    assert xauusd_spec.symbol == "XAUUSD"
    assert eurusd_spec == eurusd_spec2
    # Debe haberse llamado 2 veces (EURUSD primera vez y XAUUSD)
    assert mock_mt5_connector.get_symbol_info.call_count == 2


# ============================================================================
# TESTS DE VALIDACIÓN DE DATOS
# ============================================================================

def test_validate_symbol_info_invalid_point(extractor, mock_mt5_connector):
    """Test: Error si point es inválido"""
    # Arrange
    invalid_info = MagicMock()
    invalid_info.point = 0.0  # Inválido
    mock_mt5_connector.get_symbol_info.return_value = invalid_info
    
    # Act & Assert
    with pytest.raises(SymbolSpecificationError, match="Invalid point"):
        extractor.get_symbol_specification("INVALID")


def test_validate_symbol_info_invalid_volume_min(extractor, mock_mt5_connector):
    """Test: Error si volume_min es inválido"""
    # Arrange
    invalid_info = MagicMock()
    invalid_info.point = 0.00001
    invalid_info.tick_size = 0.00001
    invalid_info.tick_value = 1.0
    invalid_info.volume_min = 0.0  # Inválido
    invalid_info.volume_max = 100.0
    invalid_info.volume_step = 0.01
    invalid_info.contract_size = 100000.0
    mock_mt5_connector.get_symbol_info.return_value = invalid_info
    
    # Act & Assert
    with pytest.raises(SymbolSpecificationError, match="Invalid volume_min"):
        extractor.get_symbol_specification("INVALID")


# ============================================================================
# TESTS DE ACTUALIZACIÓN DE ESPECIFICACIONES
# ============================================================================

def test_refresh_symbol_specification(
    extractor,
    mock_mt5_connector,
    mock_eurusd_symbol_info
):
    """
    Test: Forzar actualización de especificación desde MT5
    
    Dado que las especificaciones pueden cambiar en MT5
    Cuando se fuerza un refresh de la especificación
    Entonces se obtienen datos actualizados desde MT5
    """
    # Arrange
    mock_mt5_connector.get_symbol_info.return_value = mock_eurusd_symbol_info
    
    # Act
    spec1 = extractor.get_symbol_specification("EURUSD")
    
    # Modificar los datos en MT5 (simular cambio)
    mock_eurusd_symbol_info.volume_max = 200.0
    
    # Refresh sin caché
    spec2 = extractor.get_symbol_specification("EURUSD", use_cache=False)
    
    # Assert
    assert spec1.volume_max == 100.0  # Valor original en caché
    assert spec2.volume_max == 200.0  # Valor actualizado


# ============================================================================
# TESTS DE INTEGRACIÓN CON PositionSizer
# ============================================================================

def test_integration_with_position_sizer(
    extractor,
    mock_mt5_connector,
    mock_eurusd_symbol_info
):
    """
    Test: Integración con PositionSizer
    
    Dado que PositionSizer necesita SymbolSpecification
    Cuando se obtiene desde SymbolSpecificationExtractor
    Entonces PositionSizer puede usarlo directamente
    """
    # Arrange
    from src.core.position_sizer import PositionSizer, RiskParameters
    
    mock_mt5_connector.get_symbol_info.return_value = mock_eurusd_symbol_info
    
    # Act
    spec = extractor.get_symbol_specification("EURUSD")
    
    risk_params = RiskParameters(
        account_balance=10000.0,
        risk_percentage=1.0,
        entry_price=1.10000,
        stop_loss=1.09900,
        symbol_spec=spec
    )
    
    sizer = PositionSizer()
    result = sizer.calculate_lot_size(risk_params)
    
    # Assert
    assert result.success is True
    assert result.lot_size > 0


# ============================================================================
# TESTS DE MANEJO DE ERRORES DE MT5
# ============================================================================

def test_mt5_connection_error(extractor, mock_mt5_connector):
    """Test: Error cuando MT5 no está conectado"""
    # Arrange
    mock_mt5_connector.get_symbol_info.side_effect = Exception(
        "MT5 not connected"
    )
    
    # Act & Assert
    with pytest.raises(SymbolSpecificationError, match="Error getting symbol"):
        extractor.get_symbol_specification("EURUSD")


def test_mt5_returns_none(extractor, mock_mt5_connector):
    """Test: Error cuando MT5 retorna None para un símbolo"""
    # Arrange
    mock_mt5_connector.get_symbol_info.return_value = None
    
    # Act & Assert
    with pytest.raises(SymbolSpecificationError, match="No symbol info"):
        extractor.get_symbol_specification("EURUSD")
