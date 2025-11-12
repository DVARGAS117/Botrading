"""
Tests unitarios para LotAdjuster - T30

Este archivo contiene tests exhaustivos para el módulo LotAdjuster,
que ajusta el tamaño de lote a las restricciones del símbolo (min, max, step).

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T30 - Ajuste de lote a step y límites del símbolo
"""

import pytest
import logging
from src.core.lot_adjuster import (
    LotAdjuster,
    SymbolSpecification,
    AdjustedLot,
    LotAdjusterError,
    InvalidLotSizeError,
    InvalidSymbolSpecError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def eurusd_spec():
    """Especificaciones de EURUSD"""
    return SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )


@pytest.fixture
def xauusd_spec():
    """Especificaciones de XAUUSD (Oro)"""
    return SymbolSpecification(
        symbol="XAUUSD",
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01
    )


@pytest.fixture
def us30_spec():
    """Especificaciones de US30 (Índice)"""
    return SymbolSpecification(
        symbol="US30",
        volume_min=0.1,
        volume_max=10.0,
        volume_step=0.1
    )


@pytest.fixture
def exotic_spec():
    """Especificaciones de símbolo con step irregular"""
    return SymbolSpecification(
        symbol="EXOTIC",
        volume_min=0.05,
        volume_max=5.0,
        volume_step=0.05
    )


@pytest.fixture
def adjuster():
    """LotAdjuster sin logger"""
    return LotAdjuster()


@pytest.fixture
def adjuster_with_logger(caplog):
    """LotAdjuster con logger configurado"""
    logger = logging.getLogger("test_lot_adjuster")
    logger.setLevel(logging.DEBUG)
    return LotAdjuster(logger=logger)


# ============================================================================
# TESTS: INICIALIZACIÓN
# ============================================================================

def test_lot_adjuster_init_without_logger(adjuster):
    """Test: Inicialización sin logger crea logger por defecto"""
    assert adjuster is not None
    assert adjuster.logger is not None
    assert adjuster.logger.name == "LotAdjuster"


def test_lot_adjuster_init_with_logger(adjuster_with_logger):
    """Test: Inicialización con logger personalizado"""
    assert adjuster_with_logger is not None
    assert adjuster_with_logger.logger.name == "test_lot_adjuster"


# ============================================================================
# TESTS: VALIDACIÓN DE SYMBOL SPECIFICATION
# ============================================================================

def test_symbol_spec_valid():
    """Test: SymbolSpecification válida se crea correctamente"""
    spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    assert spec.symbol == "EURUSD"
    assert spec.volume_min == 0.01
    assert spec.volume_max == 100.0
    assert spec.volume_step == 0.01


def test_symbol_spec_invalid_volume_min_negative():
    """Test: volume_min negativo lanza excepción"""
    with pytest.raises(InvalidSymbolSpecError, match="volume_min must be positive"):
        SymbolSpecification(
            symbol="EURUSD",
            volume_min=-0.01,
            volume_max=100.0,
            volume_step=0.01
        )


def test_symbol_spec_invalid_volume_min_zero():
    """Test: volume_min cero lanza excepción"""
    with pytest.raises(InvalidSymbolSpecError, match="volume_min must be positive"):
        SymbolSpecification(
            symbol="EURUSD",
            volume_min=0.0,
            volume_max=100.0,
            volume_step=0.01
        )


def test_symbol_spec_invalid_volume_max_negative():
    """Test: volume_max negativo lanza excepción"""
    with pytest.raises(InvalidSymbolSpecError, match="volume_max must be positive"):
        SymbolSpecification(
            symbol="EURUSD",
            volume_min=0.01,
            volume_max=-100.0,
            volume_step=0.01
        )


def test_symbol_spec_invalid_min_greater_than_max():
    """Test: volume_min > volume_max lanza excepción"""
    with pytest.raises(InvalidSymbolSpecError, match="volume_min .* cannot be greater than volume_max"):
        SymbolSpecification(
            symbol="EURUSD",
            volume_min=100.0,
            volume_max=10.0,
            volume_step=0.01
        )


def test_symbol_spec_invalid_volume_step_zero():
    """Test: volume_step cero lanza excepción"""
    with pytest.raises(InvalidSymbolSpecError, match="volume_step must be positive"):
        SymbolSpecification(
            symbol="EURUSD",
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.0
        )


def test_symbol_spec_invalid_volume_step_negative():
    """Test: volume_step negativo lanza excepción"""
    with pytest.raises(InvalidSymbolSpecError, match="volume_step must be positive"):
        SymbolSpecification(
            symbol="EURUSD",
            volume_min=0.01,
            volume_max=100.0,
            volume_step=-0.01
        )


# ============================================================================
# TESTS: AJUSTE A LÍMITES (BÁSICO)
# ============================================================================

def test_adjust_lot_within_limits(adjuster, eurusd_spec):
    """Test: Lote dentro de límites no se modifica (solo redondea al step)"""
    result = adjuster.adjust_lot(0.50, eurusd_spec)
    
    assert result.adjusted_lot == 0.50
    assert result.original_lot == 0.50
    assert result.was_adjusted is False
    assert result.reason == "Lot within limits"
    assert result.symbol == "EURUSD"


def test_adjust_lot_below_minimum(adjuster, eurusd_spec):
    """Test: Lote por debajo del mínimo se ajusta al mínimo"""
    result = adjuster.adjust_lot(0.005, eurusd_spec)
    
    assert result.adjusted_lot == 0.01
    assert result.original_lot == 0.005
    assert result.was_adjusted is True
    assert "minimum" in result.reason
    assert result.symbol == "EURUSD"


def test_adjust_lot_above_maximum(adjuster, eurusd_spec):
    """Test: Lote por encima del máximo se ajusta al máximo"""
    result = adjuster.adjust_lot(150.0, eurusd_spec)
    
    assert result.adjusted_lot == 100.0
    assert result.original_lot == 150.0
    assert result.was_adjusted is True
    assert "maximum" in result.reason
    assert result.symbol == "EURUSD"


def test_adjust_lot_exact_minimum(adjuster, eurusd_spec):
    """Test: Lote exactamente en el mínimo no se ajusta"""
    result = adjuster.adjust_lot(0.01, eurusd_spec)
    
    assert result.adjusted_lot == 0.01
    assert result.was_adjusted is False


def test_adjust_lot_exact_maximum(adjuster, eurusd_spec):
    """Test: Lote exactamente en el máximo no se ajusta"""
    result = adjuster.adjust_lot(100.0, eurusd_spec)
    
    assert result.adjusted_lot == 100.0
    assert result.was_adjusted is False


# ============================================================================
# TESTS: AJUSTE AL STEP
# ============================================================================

def test_adjust_lot_to_step_round_down(adjuster, eurusd_spec):
    """Test: Lote se redondea hacia abajo al step más cercano"""
    # 0.456 -> 0.46 con step 0.01
    result = adjuster.adjust_lot(0.454, eurusd_spec)
    
    assert result.adjusted_lot == 0.45
    assert result.was_adjusted is True
    assert "rounded to step" in result.reason


def test_adjust_lot_to_step_round_up(adjuster, eurusd_spec):
    """Test: Lote se redondea hacia arriba al step más cercano"""
    # 0.456 -> 0.46 con step 0.01
    result = adjuster.adjust_lot(0.456, eurusd_spec)
    
    assert result.adjusted_lot == 0.46
    assert result.was_adjusted is True
    assert "rounded to step" in result.reason


def test_adjust_lot_to_step_exact(adjuster, eurusd_spec):
    """Test: Lote exacto al step no se ajusta"""
    result = adjuster.adjust_lot(0.50, eurusd_spec)
    
    assert result.adjusted_lot == 0.50
    assert result.was_adjusted is False


def test_adjust_lot_to_step_irregular(adjuster, exotic_spec):
    """Test: Ajuste con step irregular (0.05)"""
    # 0.23 -> 0.25 con step 0.05
    result = adjuster.adjust_lot(0.23, exotic_spec)
    
    assert result.adjusted_lot == 0.25
    assert result.was_adjusted is True


def test_adjust_lot_to_step_us30(adjuster, us30_spec):
    """Test: Ajuste con step 0.1 (índice)"""
    # 2.45 -> 2.4 con step 0.1 (redondeo al más cercano)
    result = adjuster.adjust_lot(2.45, us30_spec)
    
    assert result.adjusted_lot == 2.4  # round(2.45/0.1) * 0.1 = 24 * 0.1 = 2.4
    assert result.was_adjusted is True


# ============================================================================
# TESTS: DIFERENTES SÍMBOLOS
# ============================================================================

def test_adjust_lot_eurusd(adjuster, eurusd_spec):
    """Test: Ajuste para EURUSD"""
    result = adjuster.adjust_lot(0.75, eurusd_spec)
    
    assert result.adjusted_lot == 0.75
    assert result.symbol == "EURUSD"


def test_adjust_lot_xauusd(adjuster, xauusd_spec):
    """Test: Ajuste para XAUUSD con máximo diferente"""
    result = adjuster.adjust_lot(60.0, xauusd_spec)
    
    assert result.adjusted_lot == 50.0  # Máximo de oro
    assert result.was_adjusted is True
    assert result.symbol == "XAUUSD"


def test_adjust_lot_us30(adjuster, us30_spec):
    """Test: Ajuste para US30 con mínimo diferente"""
    result = adjuster.adjust_lot(0.05, us30_spec)
    
    assert result.adjusted_lot == 0.1  # Mínimo de US30
    assert result.was_adjusted is True
    assert result.symbol == "US30"


# ============================================================================
# TESTS: VALIDACIÓN DE ENTRADA
# ============================================================================

def test_adjust_lot_negative_lot(adjuster, eurusd_spec):
    """Test: Lote negativo lanza excepción"""
    with pytest.raises(InvalidLotSizeError, match="Lot size must be positive"):
        adjuster.adjust_lot(-0.50, eurusd_spec)


def test_adjust_lot_zero_lot(adjuster, eurusd_spec):
    """Test: Lote cero lanza excepción"""
    with pytest.raises(InvalidLotSizeError, match="Lot size must be positive"):
        adjuster.adjust_lot(0.0, eurusd_spec)


def test_adjust_lot_none_lot(adjuster, eurusd_spec):
    """Test: Lote None lanza excepción"""
    with pytest.raises(InvalidLotSizeError):
        adjuster.adjust_lot(None, eurusd_spec)


def test_adjust_lot_none_spec(adjuster):
    """Test: SymbolSpecification None lanza excepción"""
    with pytest.raises(InvalidSymbolSpecError):
        adjuster.adjust_lot(0.50, None)


# ============================================================================
# TESTS: CASOS EDGE
# ============================================================================

def test_adjust_lot_very_small_lot(adjuster, eurusd_spec):
    """Test: Lote extremadamente pequeño se ajusta al mínimo"""
    result = adjuster.adjust_lot(0.0001, eurusd_spec)
    
    assert result.adjusted_lot == 0.01
    assert result.was_adjusted is True


def test_adjust_lot_very_large_lot(adjuster, eurusd_spec):
    """Test: Lote extremadamente grande se ajusta al máximo"""
    result = adjuster.adjust_lot(999999.99, eurusd_spec)
    
    assert result.adjusted_lot == 100.0
    assert result.was_adjusted is True


def test_adjust_lot_fractional_step(adjuster, exotic_spec):
    """Test: Ajuste con múltiples pasos fraccionarios"""
    # 1.234 con step 0.05 -> debería ajustarse a 1.25 o 1.20
    result = adjuster.adjust_lot(1.234, exotic_spec)
    
    # Verificar que se ajustó correctamente al step
    steps = result.adjusted_lot / exotic_spec.volume_step
    assert abs(steps - round(steps)) < 0.01  # Es múltiplo del step


def test_adjust_lot_precision_edge_case(adjuster, eurusd_spec):
    """Test: Caso edge con precisión de punto flotante"""
    # 0.3333333... debería ajustarse correctamente
    result = adjuster.adjust_lot(1.0 / 3.0, eurusd_spec)
    
    # Debe ser múltiplo de 0.01
    assert result.adjusted_lot in [0.33, 0.34]


# ============================================================================
# TESTS: LOGGING
# ============================================================================

def test_adjust_lot_logs_adjustment(adjuster_with_logger, eurusd_spec, caplog):
    """Test: Ajuste de lote genera log apropiado"""
    caplog.set_level(logging.INFO)
    
    result = adjuster_with_logger.adjust_lot(0.005, eurusd_spec)
    
    # Verificar que se generó un log de warning para ajuste
    assert any("adjusted" in record.message.lower() for record in caplog.records)


def test_adjust_lot_logs_success(adjuster_with_logger, eurusd_spec, caplog):
    """Test: Lote válido genera log de info"""
    caplog.set_level(logging.DEBUG)
    
    result = adjuster_with_logger.adjust_lot(0.50, eurusd_spec)
    
    # Debe haber al menos un log
    assert len(caplog.records) > 0


# ============================================================================
# TESTS: ADJUSTED LOT DATACLASS
# ============================================================================

def test_adjusted_lot_to_dict(adjuster, eurusd_spec):
    """Test: AdjustedLot se convierte correctamente a diccionario"""
    result = adjuster.adjust_lot(0.50, eurusd_spec)
    
    data = result.to_dict()
    
    assert isinstance(data, dict)
    assert data["adjusted_lot"] == 0.50
    assert data["original_lot"] == 0.50
    assert data["was_adjusted"] is False
    assert "reason" in data
    assert data["symbol"] == "EURUSD"


def test_adjusted_lot_repr(adjuster, eurusd_spec):
    """Test: AdjustedLot tiene representación legible"""
    result = adjuster.adjust_lot(0.50, eurusd_spec)
    
    repr_str = repr(result)
    
    assert "AdjustedLot" in repr_str
    assert "0.5" in repr_str or "0.50" in repr_str


# ============================================================================
# TESTS: BATCH ADJUSTMENT
# ============================================================================

def test_adjust_multiple_lots(adjuster, eurusd_spec):
    """Test: Ajustar múltiples lotes de una vez"""
    lot_sizes = [0.005, 0.50, 150.0, 0.75]
    
    results = [adjuster.adjust_lot(lot, eurusd_spec) for lot in lot_sizes]
    
    assert len(results) == 4
    assert results[0].adjusted_lot == 0.01  # Ajustado al mínimo
    assert results[1].adjusted_lot == 0.50  # Sin cambio
    assert results[2].adjusted_lot == 100.0  # Ajustado al máximo
    assert results[3].adjusted_lot == 0.75  # Sin cambio


# ============================================================================
# TESTS: INTEGRACIÓN CON POSITION SIZER
# ============================================================================

def test_adjust_lot_from_position_sizer_output(adjuster, eurusd_spec):
    """Test: Ajustar lote calculado por PositionSizer"""
    # Simular salida de PositionSizer
    calculated_lot = 0.4567  # Valor típico calculado
    
    result = adjuster.adjust_lot(calculated_lot, eurusd_spec)
    
    # Debería ajustarse a 0.46
    assert result.adjusted_lot == 0.46
    assert result.was_adjusted is True


# ============================================================================
# TESTS: MÉTODO DE CONVENIENCIA
# ============================================================================

def test_is_valid_lot_true(adjuster, eurusd_spec):
    """Test: is_valid_lot retorna True para lote válido"""
    assert adjuster.is_valid_lot(0.50, eurusd_spec) is True


def test_is_valid_lot_false_below_min(adjuster, eurusd_spec):
    """Test: is_valid_lot retorna False para lote debajo del mínimo"""
    assert adjuster.is_valid_lot(0.005, eurusd_spec) is False


def test_is_valid_lot_false_above_max(adjuster, eurusd_spec):
    """Test: is_valid_lot retorna False para lote sobre el máximo"""
    assert adjuster.is_valid_lot(150.0, eurusd_spec) is False


def test_is_valid_lot_false_wrong_step(adjuster, eurusd_spec):
    """Test: is_valid_lot retorna False para lote que no respeta step"""
    assert adjuster.is_valid_lot(0.456, eurusd_spec) is False


def test_is_valid_lot_true_exact_boundaries(adjuster, eurusd_spec):
    """Test: is_valid_lot retorna True en límites exactos"""
    assert adjuster.is_valid_lot(0.01, eurusd_spec) is True  # Min
    assert adjuster.is_valid_lot(100.0, eurusd_spec) is True  # Max


# ============================================================================
# TESTS: MÉTODO CALCULATE_adjustment_amount
# ============================================================================

def test_calculate_adjustment_amount_no_adjustment(adjuster, eurusd_spec):
    """Test: Sin ajuste, el monto es 0"""
    result = adjuster.adjust_lot(0.50, eurusd_spec)
    adjustment = result.adjusted_lot - result.original_lot
    
    assert abs(adjustment) < 0.0001


def test_calculate_adjustment_amount_positive(adjuster, eurusd_spec):
    """Test: Ajuste positivo cuando se aumenta al mínimo"""
    result = adjuster.adjust_lot(0.005, eurusd_spec)
    adjustment = result.adjusted_lot - result.original_lot
    
    assert adjustment > 0
    assert abs(adjustment - 0.005) < 0.0001


def test_calculate_adjustment_amount_negative(adjuster, eurusd_spec):
    """Test: Ajuste negativo cuando se reduce al máximo"""
    result = adjuster.adjust_lot(150.0, eurusd_spec)
    adjustment = result.adjusted_lot - result.original_lot
    
    assert adjustment < 0
    assert abs(adjustment - (-50.0)) < 0.0001


# ============================================================================
# TESTS: CASOS ESPECÍFICOS DE SÍMBOLOS REALES
# ============================================================================

def test_adjust_lot_eurusd_typical_trade():
    """Test: Caso típico de trading en EURUSD"""
    adjuster = LotAdjuster()
    spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    
    # PositionSizer calculó 0.4032
    result = adjuster.adjust_lot(0.4032, spec)
    
    assert result.adjusted_lot == 0.40
    assert result.was_adjusted is True


def test_adjust_lot_xauusd_typical_trade():
    """Test: Caso típico de trading en XAUUSD"""
    adjuster = LotAdjuster()
    spec = SymbolSpecification(
        symbol="XAUUSD",
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01
    )
    
    # PositionSizer calculó 0.1567
    result = adjuster.adjust_lot(0.1567, spec)
    
    assert result.adjusted_lot == 0.16
    assert result.was_adjusted is True


def test_adjust_lot_us30_typical_trade():
    """Test: Caso típico de trading en US30"""
    adjuster = LotAdjuster()
    spec = SymbolSpecification(
        symbol="US30",
        volume_min=0.1,
        volume_max=10.0,
        volume_step=0.1
    )
    
    # PositionSizer calculó 2.34
    result = adjuster.adjust_lot(2.34, spec)
    
    assert result.adjusted_lot == 2.3
    assert result.was_adjusted is True
