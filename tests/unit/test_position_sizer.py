"""
Tests unitarios para PositionSizer - T29

Este módulo de tests cubre todas las funcionalidades del PositionSizer:
- Cálculo de lote por % de riesgo
- Conversión de pips a precio
- Validación de parámetros
- Manejo de diferentes tipos de símbolos (Forex, Metales, Índices)
- Casos edge y validaciones

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T29 - Cálculo de lote por % riesgo y distancia al SL
"""

import pytest
from unittest.mock import Mock, MagicMock
from decimal import Decimal

from src.core.position_sizer import (
    PositionSizer,
    RiskParameters,
    SymbolSpecification,
    PositionSize,
    PositionSizerError,
    InvalidRiskParametersError,
    InvalidSymbolSpecError
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_logger():
    """Mock del logger"""
    return Mock()


@pytest.fixture
def eurusd_spec():
    """Especificaciones de EURUSD"""
    return SymbolSpecification(
        symbol="EURUSD",
        point=0.0001,  # 1 pip estándar (4 decimales)
        tick_size=0.00001,  # 1 pipette (5 decimales)
        tick_value=1.0,  # $1 por tick por lote estándar
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        contract_size=100000  # 1 lote = 100,000 unidades
    )


@pytest.fixture
def xauusd_spec():
    """Especificaciones de XAUUSD (Oro)"""
    return SymbolSpecification(
        symbol="XAUUSD",
        point=0.01,  # 1 pip = 1 centavo
        tick_size=0.01,
        tick_value=1.0,  # $1 por tick por lote
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        contract_size=100  # 1 lote = 100 onzas
    )


@pytest.fixture
def us30_spec():
    """Especificaciones de US30 (Dow Jones)"""
    return SymbolSpecification(
        symbol="US30",
        point=1.0,  # 1 punto
        tick_size=1.0,
        tick_value=1.0,  # $1 por punto
        volume_min=0.1,
        volume_max=10.0,
        volume_step=0.1,
        contract_size=1  # Índice
    )


# ============================================================================
# TEST: INICIALIZACIÓN
# ============================================================================

class TestPositionSizerInitialization:
    """Tests de inicialización del PositionSizer"""
    
    def test_init_success(self, mock_logger):
        """Test: Inicialización exitosa"""
        sizer = PositionSizer(logger=mock_logger)
        assert sizer is not None
        assert sizer.logger == mock_logger
    
    def test_init_without_logger(self):
        """Test: Inicialización sin logger crea uno por defecto"""
        sizer = PositionSizer()
        assert sizer is not None
        assert sizer.logger is not None


# ============================================================================
# TEST: CÁLCULO DE LOTE POR RIESGO (FOREX)
# ============================================================================

class TestCalculateLotSizeForex:
    """Tests de cálculo de lote para pares de Forex"""
    
    def test_calculate_lot_eurusd_basic(self, eurusd_spec):
        """Test: Cálculo básico de lote para EURUSD"""
        sizer = PositionSizer()
        
        # Cuenta de $10,000, riesgo 2%, distancia SL 50 pips
        risk_params = RiskParameters(
            account_balance=10000.0,
            risk_percentage=2.0,  # 2%
            entry_price=1.1000,
            stop_loss=1.0950,  # 50 pips de distancia
            symbol_spec=eurusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Riesgo: $200 (2% de $10,000)
        # Distancia SL: 50 pips = 0.0050
        # Valor por pip por lote: $10 (para EURUSD)
        # Lote esperado: $200 / (50 pips * $10) = 0.4 lotes
        assert result.lot_size == pytest.approx(0.40, rel=0.01)
        assert result.risk_amount == 200.0
        assert result.pip_distance == pytest.approx(50.0, rel=0.01)
        assert result.success is True
    
    def test_calculate_lot_eurusd_high_risk(self, eurusd_spec):
        """Test: Cálculo con mayor riesgo"""
        sizer = PositionSizer()
        
        risk_params = RiskParameters(
            account_balance=50000.0,
            risk_percentage=5.0,  # 5% (alto riesgo)
            entry_price=1.1000,
            stop_loss=1.0900,  # 100 pips
            symbol_spec=eurusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Riesgo: $2,500 (5% de $50,000)
        # Distancia SL: 100 pips
        # Lote esperado: $2,500 / (100 pips * $10) = 2.5 lotes
        assert result.lot_size == pytest.approx(2.50, rel=0.01)
        assert result.risk_amount == 2500.0
        assert result.pip_distance == pytest.approx(100.0, rel=0.01)
    
    def test_calculate_lot_eurusd_small_account(self, eurusd_spec):
        """Test: Cuenta pequeña resulta en lote mínimo"""
        sizer = PositionSizer()
        
        risk_params = RiskParameters(
            account_balance=100.0,  # Cuenta pequeña
            risk_percentage=2.0,
            entry_price=1.1000,
            stop_loss=1.0950,  # 50 pips
            symbol_spec=eurusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Riesgo: $2 (2% de $100)
        # Lote calculado sería muy pequeño, se limita al mínimo
        assert result.lot_size == eurusd_spec.volume_min
        assert result.lot_size == 0.01
    
    def test_calculate_lot_eurusd_sell_position(self, eurusd_spec):
        """Test: Posición SELL (SL arriba de entrada)"""
        sizer = PositionSizer()
        
        risk_params = RiskParameters(
            account_balance=10000.0,
            risk_percentage=2.0,
            entry_price=1.1000,
            stop_loss=1.1050,  # SL arriba (SELL)
            symbol_spec=eurusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Distancia debe ser absoluta (50 pips)
        assert result.pip_distance == pytest.approx(50.0, rel=0.01)
        assert result.lot_size == pytest.approx(0.40, rel=0.01)


# ============================================================================
# TEST: CÁLCULO DE LOTE (OTROS ACTIVOS)
# ============================================================================

class TestCalculateLotSizeOtherAssets:
    """Tests de cálculo de lote para metales e índices"""
    
    def test_calculate_lot_xauusd(self, xauusd_spec):
        """Test: Cálculo de lote para Oro (XAUUSD)"""
        sizer = PositionSizer()
        
        # Oro a $2,000, SL en $1,980 = $20 de distancia
        risk_params = RiskParameters(
            account_balance=10000.0,
            risk_percentage=2.0,
            entry_price=2000.0,
            stop_loss=1980.0,
            symbol_spec=xauusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Riesgo: $200
        # Distancia: $20 = 2000 pips (cada pip = $0.01)
        # Valor por pip por lote: $1
        # Lote: $200 / (2000 pips * $1) = 0.1 lotes
        assert result.lot_size == pytest.approx(0.10, rel=0.01)
        assert result.risk_amount == 200.0
    
    def test_calculate_lot_us30(self, us30_spec):
        """Test: Cálculo de lote para índice US30"""
        sizer = PositionSizer()
        
        risk_params = RiskParameters(
            account_balance=20000.0,
            risk_percentage=1.5,
            entry_price=35000.0,
            stop_loss=34900.0,  # 100 puntos
            symbol_spec=us30_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Riesgo: $300 (1.5% de $20,000)
        # Distancia: 100 puntos
        # Valor por punto: $1
        # Lote: $300 / (100 * $1) = 3.0 lotes
        assert result.lot_size == pytest.approx(3.0, rel=0.1)
        assert result.risk_amount == 300.0


# ============================================================================
# TEST: VALIDACIONES
# ============================================================================

class TestRiskParametersValidation:
    """Tests de validación de parámetros de riesgo"""
    
    def test_invalid_account_balance_negative(self, eurusd_spec):
        """Test: Balance negativo es inválido"""
        with pytest.raises(InvalidRiskParametersError, match="Account balance must be positive"):
            RiskParameters(
                account_balance=-100.0,  # ❌ Negativo
                risk_percentage=2.0,
                entry_price=1.1000,
                stop_loss=1.0950,
                symbol_spec=eurusd_spec
            )
    
    def test_invalid_account_balance_zero(self, eurusd_spec):
        """Test: Balance cero es inválido"""
        with pytest.raises(InvalidRiskParametersError, match="Account balance must be positive"):
            RiskParameters(
                account_balance=0.0,  # ❌ Cero
                risk_percentage=2.0,
                entry_price=1.1000,
                stop_loss=1.0950,
                symbol_spec=eurusd_spec
            )
    
    def test_invalid_risk_percentage_negative(self, eurusd_spec):
        """Test: Porcentaje de riesgo negativo es inválido"""
        with pytest.raises(InvalidRiskParametersError, match="Risk percentage must be between"):
            RiskParameters(
                account_balance=10000.0,
                risk_percentage=-1.0,  # ❌ Negativo
                entry_price=1.1000,
                stop_loss=1.0950,
                symbol_spec=eurusd_spec
            )
    
    def test_invalid_risk_percentage_zero(self, eurusd_spec):
        """Test: Porcentaje de riesgo cero es inválido"""
        with pytest.raises(InvalidRiskParametersError, match="Risk percentage must be between"):
            RiskParameters(
                account_balance=10000.0,
                risk_percentage=0.0,  # ❌ Cero
                entry_price=1.1000,
                stop_loss=1.0950,
                symbol_spec=eurusd_spec
            )
    
    def test_invalid_risk_percentage_too_high(self, eurusd_spec):
        """Test: Porcentaje de riesgo > 100% es inválido"""
        with pytest.raises(InvalidRiskParametersError, match="Risk percentage must be between"):
            RiskParameters(
                account_balance=10000.0,
                risk_percentage=150.0,  # ❌ > 100%
                entry_price=1.1000,
                stop_loss=1.0950,
                symbol_spec=eurusd_spec
            )
    
    def test_invalid_entry_price_negative(self, eurusd_spec):
        """Test: Precio de entrada negativo es inválido"""
        with pytest.raises(InvalidRiskParametersError, match="Entry price must be positive"):
            RiskParameters(
                account_balance=10000.0,
                risk_percentage=2.0,
                entry_price=-1.1000,  # ❌ Negativo
                stop_loss=1.0950,
                symbol_spec=eurusd_spec
            )
    
    def test_invalid_stop_loss_negative(self, eurusd_spec):
        """Test: Stop Loss negativo es inválido"""
        with pytest.raises(InvalidRiskParametersError, match="Stop loss must be positive"):
            RiskParameters(
                account_balance=10000.0,
                risk_percentage=2.0,
                entry_price=1.1000,
                stop_loss=-1.0950,  # ❌ Negativo
                symbol_spec=eurusd_spec
            )
    
    def test_invalid_entry_equals_stop_loss(self, eurusd_spec):
        """Test: Entrada = SL es inválido (distancia cero)"""
        with pytest.raises(InvalidRiskParametersError, match="Stop loss must be different from entry price"):
            RiskParameters(
                account_balance=10000.0,
                risk_percentage=2.0,
                entry_price=1.1000,
                stop_loss=1.1000,  # ❌ Igual a entrada
                symbol_spec=eurusd_spec
            )


# ============================================================================
# TEST: VALIDACIONES DE SYMBOL SPEC
# ============================================================================

class TestSymbolSpecificationValidation:
    """Tests de validación de especificaciones de símbolos"""
    
    def test_invalid_point_zero(self):
        """Test: Point = 0 es inválido"""
        with pytest.raises(InvalidSymbolSpecError, match="Point must be positive"):
            SymbolSpecification(
                symbol="EURUSD",
                point=0.0,  # ❌ Cero
                tick_size=0.00001,
                tick_value=1.0,
                volume_min=0.01,
                volume_max=100.0,
                volume_step=0.01,
                contract_size=100000
            )
    
    def test_invalid_tick_value_negative(self):
        """Test: Tick value negativo es inválido"""
        with pytest.raises(InvalidSymbolSpecError, match="Tick value must be positive"):
            SymbolSpecification(
                symbol="EURUSD",
                point=0.00001,
                tick_size=0.00001,
                tick_value=-1.0,  # ❌ Negativo
                volume_min=0.01,
                volume_max=100.0,
                volume_step=0.01,
                contract_size=100000
            )
    
    def test_invalid_volume_min_greater_than_max(self):
        """Test: Volume min > max es inválido"""
        with pytest.raises(InvalidSymbolSpecError, match="cannot be greater than"):
            SymbolSpecification(
                symbol="EURUSD",
                point=0.00001,
                tick_size=0.00001,
                tick_value=1.0,
                volume_min=10.0,  # ❌ Mayor que max
                volume_max=1.0,
                volume_step=0.01,
                contract_size=100000
            )
    
    def test_invalid_contract_size_zero(self):
        """Test: Contract size = 0 es inválido"""
        with pytest.raises(InvalidSymbolSpecError, match="Contract size must be positive"):
            SymbolSpecification(
                symbol="EURUSD",
                point=0.00001,
                tick_size=0.00001,
                tick_value=1.0,
                volume_min=0.01,
                volume_max=100.0,
                volume_step=0.01,
                contract_size=0  # ❌ Cero
            )


# ============================================================================
# TEST: CONVERSIÓN DE PIPS
# ============================================================================

class TestPipConversion:
    """Tests de conversión entre precio y pips"""
    
    def test_price_distance_to_pips_eurusd(self, eurusd_spec):
        """Test: Convertir distancia de precio a pips (EURUSD)"""
        sizer = PositionSizer()
        
        # Distancia: 0.0050 = 50 pips para EURUSD
        pips = sizer.price_distance_to_pips(0.0050, eurusd_spec)
        assert pips == 50.0
    
    def test_price_distance_to_pips_xauusd(self, xauusd_spec):
        """Test: Convertir distancia de precio a pips (XAUUSD)"""
        sizer = PositionSizer()
        
        # Distancia: $20.0 = 2000 pips para XAUUSD (punto = 0.01)
        pips = sizer.price_distance_to_pips(20.0, xauusd_spec)
        assert pips == 2000.0
    
    def test_pips_to_price_distance_eurusd(self, eurusd_spec):
        """Test: Convertir pips a distancia de precio (EURUSD)"""
        sizer = PositionSizer()
        
        # 100 pips = 0.0100 para EURUSD
        price_dist = sizer.pips_to_price_distance(100.0, eurusd_spec)
        assert price_dist == pytest.approx(0.0100, rel=0.0001)
    
    def test_pips_to_price_distance_us30(self, us30_spec):
        """Test: Convertir pips a distancia de precio (US30)"""
        sizer = PositionSizer()
        
        # 50 puntos = 50.0 para US30
        price_dist = sizer.pips_to_price_distance(50.0, us30_spec)
        assert price_dist == 50.0


# ============================================================================
# TEST: AJUSTE DE LOTE A LÍMITES
# ============================================================================

class TestLotSizeAdjustment:
    """Tests de ajuste de lote a límites del símbolo"""
    
    def test_adjust_lot_below_minimum(self, eurusd_spec):
        """Test: Lote calculado < mínimo se ajusta al mínimo"""
        sizer = PositionSizer()
        
        # Simular lote muy pequeño
        adjusted = sizer._adjust_to_symbol_limits(0.005, eurusd_spec)
        assert adjusted == eurusd_spec.volume_min  # 0.01
    
    def test_adjust_lot_above_maximum(self, eurusd_spec):
        """Test: Lote calculado > máximo se ajusta al máximo"""
        sizer = PositionSizer()
        
        # Simular lote muy grande
        adjusted = sizer._adjust_to_symbol_limits(200.0, eurusd_spec)
        assert adjusted == eurusd_spec.volume_max  # 100.0
    
    def test_adjust_lot_to_step(self, eurusd_spec):
        """Test: Lote se redondea al step más cercano"""
        sizer = PositionSizer()
        
        # 0.456 debe redondearse a 0.46 (step = 0.01)
        adjusted = sizer._adjust_to_symbol_limits(0.456, eurusd_spec)
        assert adjusted == 0.46
        
        # 1.234 debe redondearse a 1.23
        adjusted = sizer._adjust_to_symbol_limits(1.234, eurusd_spec)
        assert adjusted == 1.23
    
    def test_adjust_lot_us30_step(self, us30_spec):
        """Test: Ajuste con step diferente (US30 = 0.1)"""
        sizer = PositionSizer()
        
        # 2.37 debe redondearse a 2.4 (step = 0.1)
        adjusted = sizer._adjust_to_symbol_limits(2.37, us30_spec)
        assert adjusted == pytest.approx(2.4, rel=0.01)


# ============================================================================
# TEST: CÁLCULO DE RIESGO EN DINERO
# ============================================================================

class TestRiskAmountCalculation:
    """Tests de cálculo del monto de riesgo en dinero"""
    
    def test_calculate_risk_amount_basic(self):
        """Test: Cálculo básico de riesgo en dinero"""
        sizer = PositionSizer()
        
        risk_amount = sizer.calculate_risk_amount(10000.0, 2.0)
        assert risk_amount == 200.0
    
    def test_calculate_risk_amount_high_percentage(self):
        """Test: Cálculo con alto porcentaje"""
        sizer = PositionSizer()
        
        risk_amount = sizer.calculate_risk_amount(50000.0, 10.0)
        assert risk_amount == 5000.0
    
    def test_calculate_risk_amount_decimal_percentage(self):
        """Test: Cálculo con porcentaje decimal"""
        sizer = PositionSizer()
        
        risk_amount = sizer.calculate_risk_amount(20000.0, 1.5)
        assert risk_amount == 300.0


# ============================================================================
# TEST: POSITIONSIZE DATACLASS
# ============================================================================

class TestPositionSizeDataclass:
    """Tests del dataclass PositionSize"""
    
    def test_position_size_initialization(self, eurusd_spec):
        """Test: Inicialización de PositionSize"""
        pos_size = PositionSize(
            lot_size=0.5,
            risk_amount=100.0,
            pip_distance=50.0,
            pip_value=10.0,
            symbol=eurusd_spec.symbol,
            success=True,
            message="Calculated successfully"
        )
        
        assert pos_size.lot_size == 0.5
        assert pos_size.risk_amount == 100.0
        assert pos_size.pip_distance == 50.0
        assert pos_size.pip_value == 10.0
        assert pos_size.symbol == "EURUSD"
        assert pos_size.success is True
        assert "successfully" in pos_size.message
    
    def test_position_size_to_dict(self, eurusd_spec):
        """Test: Conversión a diccionario"""
        pos_size = PositionSize(
            lot_size=1.0,
            risk_amount=200.0,
            pip_distance=100.0,
            pip_value=10.0,
            symbol=eurusd_spec.symbol,
            success=True
        )
        
        result = pos_size.to_dict()
        
        assert result["lot_size"] == 1.0
        assert result["risk_amount"] == 200.0
        assert result["pip_distance"] == 100.0
        assert result["symbol"] == "EURUSD"
        assert result["success"] is True


# ============================================================================
# TEST: CASOS EDGE
# ============================================================================

class TestEdgeCases:
    """Tests de casos edge y situaciones especiales"""
    
    def test_very_small_account_very_wide_stop(self, eurusd_spec):
        """Test: Cuenta muy pequeña con SL muy amplio"""
        sizer = PositionSizer()
        
        risk_params = RiskParameters(
            account_balance=50.0,  # Muy pequeña
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.0500,  # 500 pips (muy amplio)
            symbol_spec=eurusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Debe retornar el lote mínimo
        assert result.lot_size == eurusd_spec.volume_min
        assert result.success is True
    
    def test_very_large_account_tight_stop(self, eurusd_spec):
        """Test: Cuenta muy grande con SL muy estrecho"""
        sizer = PositionSizer()
        
        risk_params = RiskParameters(
            account_balance=1000000.0,  # $1M
            risk_percentage=5.0,
            entry_price=1.1000,
            stop_loss=1.0999,  # Solo 1 pip
            symbol_spec=eurusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Riesgo: $50,000
        # Distancia: 1 pip
        # Valor por pip: $10
        # Lote calculado: $50,000 / $10 = 5,000 lotes
        # Debe limitarse al máximo permitido
        assert result.lot_size == eurusd_spec.volume_max
    
    def test_fractional_pip_distance(self, eurusd_spec):
        """Test: Distancia con fracciones de pip"""
        sizer = PositionSizer()
        
        risk_params = RiskParameters(
            account_balance=10000.0,
            risk_percentage=2.0,
            entry_price=1.10000,
            stop_loss=1.09975,  # 2.5 pips
            symbol_spec=eurusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Debe manejar fracciones correctamente
        assert result.pip_distance == pytest.approx(2.5, rel=0.1)
        assert result.lot_size > 0


# ============================================================================
# TEST: LOGGING
# ============================================================================

class TestLogging:
    """Tests de logging del PositionSizer"""
    
    def test_logs_calculation_success(self, eurusd_spec, mock_logger):
        """Test: Log cuando el cálculo es exitoso"""
        sizer = PositionSizer(logger=mock_logger)
        
        risk_params = RiskParameters(
            account_balance=10000.0,
            risk_percentage=2.0,
            entry_price=1.1000,
            stop_loss=1.0950,
            symbol_spec=eurusd_spec
        )
        
        sizer.calculate_lot_size(risk_params)
        
        # Verificar que se registró el cálculo
        mock_logger.info.assert_called()
    
    def test_logs_adjustment_to_limits(self, eurusd_spec, mock_logger):
        """Test: Log cuando se ajusta a límites"""
        sizer = PositionSizer(logger=mock_logger)
        
        # Forzar cuenta muy pequeña para trigger ajuste
        risk_params = RiskParameters(
            account_balance=10.0,
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.0000,  # Muy amplio
            symbol_spec=eurusd_spec
        )
        
        sizer.calculate_lot_size(risk_params)
        
        # Debe loggear el ajuste al mínimo
        mock_logger.warning.assert_called()


# ============================================================================
# TEST: INTEGRACIÓN CON ORDER MANAGER
# ============================================================================

class TestIntegrationWithOrderManager:
    """Tests de integración con OrderManager"""
    
    def test_calculate_lot_for_market_order(self, eurusd_spec):
        """Test: Calcular lote antes de enviar orden Market"""
        sizer = PositionSizer()
        
        # Simular escenario real antes de enviar orden
        account_balance = 10000.0
        risk_pct = 2.0
        entry = 1.1000
        sl = 1.0950
        
        risk_params = RiskParameters(
            account_balance=account_balance,
            risk_percentage=risk_pct,
            entry_price=entry,
            stop_loss=sl,
            symbol_spec=eurusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # El lote resultante se usaría en OrderRequest
        assert result.success is True
        assert result.lot_size > 0
        assert result.lot_size >= eurusd_spec.volume_min
        assert result.lot_size <= eurusd_spec.volume_max
    
    def test_calculate_lot_respects_symbol_limits(self, us30_spec):
        """Test: Lote calculado respeta límites del símbolo"""
        sizer = PositionSizer()
        
        risk_params = RiskParameters(
            account_balance=100000.0,
            risk_percentage=3.0,
            entry_price=35000.0,
            stop_loss=34950.0,
            symbol_spec=us30_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        # Verificar que está dentro de límites de US30
        assert result.lot_size >= us30_spec.volume_min
        assert result.lot_size <= us30_spec.volume_max
        # Verificar que respeta el step
        step_multiple = result.lot_size / us30_spec.volume_step
        assert step_multiple == pytest.approx(round(step_multiple), rel=0.01)
