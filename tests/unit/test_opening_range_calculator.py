"""
Tests unitarios para Opening Range Calculator

Tests para cálculo de Opening Range (OR) de sesión europea.
El OR se define en los primeros 15-30 minutos de la sesión (08:00-08:30 GMT).

Autor: Sistema Botrading
Fecha: 2025-11-17
Ticket: VWAP Methodology - Opening Range Calculator
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, time
from src.core.opening_range_calculator import (
    OpeningRangeCalculator,
    OpeningRangeData,
    BreakoutStatus
)


class TestOpeningRangeCalculator:
    """Tests para cálculo de Opening Range"""
    
    @pytest.fixture
    def calculator(self):
        """Fixture del calculador de Opening Range"""
        return OpeningRangeCalculator(
            session_start_hour=8,
            session_start_minute=0,
            or_duration_minutes=30
        )
    
    @pytest.fixture
    def european_session_data(self):
        """
        Datos de sesión europea con Opening Range definido.
        08:00 GMT - apertura
        08:30 GMT - fin de OR
        """
        dates = pd.date_range(
            start='2025-11-17 08:00:00',
            periods=120,  # 2 horas de datos en timeframe 1M
            freq='1min'
        )
        
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000] * 30 + [1.1005] * 30 + [1.1010] * 30 + [1.1015] * 30,
            'high': [1.1010] * 30 + [1.1015] * 30 + [1.1020] * 30 + [1.1025] * 30,
            'low': [1.0995] * 30 + [1.1000] * 30 + [1.1005] * 30 + [1.1010] * 30,
            'close': [1.1005] * 30 + [1.1010] * 30 + [1.1015] * 30 + [1.1020] * 30,
            'volume': [1000] * 120
        })
        
        return data
    
    def test_calculate_opening_range_basic(self, calculator, european_session_data):
        """Test básico de cálculo de Opening Range"""
        # Act
        or_data = calculator.calculate_opening_range(european_session_data)
        
        # Assert
        assert or_data is not None
        assert or_data.or_high > 0
        assert or_data.or_low > 0
        assert or_data.or_high > or_data.or_low
    
    def test_opening_range_boundaries(self, calculator):
        """Test que OR se calcula solo en ventana 08:00-08:30 GMT"""
        # Arrange - Datos con diferentes horas
        dates_before = pd.date_range('2025-11-17 07:30:00', periods=30, freq='1min')
        dates_or = pd.date_range('2025-11-17 08:00:00', periods=30, freq='1min')
        dates_after = pd.date_range('2025-11-17 08:30:00', periods=30, freq='1min')
        
        all_dates = dates_before.tolist() + dates_or.tolist() + dates_after.tolist()
        
        data = pd.DataFrame({
            'time': all_dates,
            'open': [1.0990] * 30 + [1.1000] * 30 + [1.1020] * 30,
            'high': [1.1000] * 30 + [1.1015] * 30 + [1.1030] * 30,
            'low': [1.0985] * 30 + [1.0995] * 30 + [1.1015] * 30,
            'close': [1.0995] * 30 + [1.1010] * 30 + [1.1025] * 30,
            'volume': [1000] * 90
        })
        
        # Act
        or_data = calculator.calculate_opening_range(data)
        
        # Assert - OR debe estar basado solo en datos 08:00-08:30
        assert or_data.or_high == 1.1015  # Max high en OR window
        assert or_data.or_low == 1.0995   # Min low en OR window
    
    def test_breakout_status_above(self, calculator):
        """Test detección de breakout alcista"""
        # Arrange - Precio rompe por encima de OR
        dates = pd.date_range('2025-11-17 08:00:00', periods=60, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000] * 30 + [1.1020] * 30,  # Rompe arriba después de OR
            'high': [1.1010] * 30 + [1.1030] * 30,
            'low': [1.0995] * 30 + [1.1015] * 30,
            'close': [1.1005] * 30 + [1.1025] * 30,
            'volume': [1000] * 60
        })
        
        # Act
        or_data = calculator.calculate_opening_range(data)
        
        # Assert
        assert or_data.breakout_status == BreakoutStatus.ABOVE
        assert or_data.current_price > or_data.or_high
    
    def test_breakout_status_below(self, calculator):
        """Test detección de breakout bajista"""
        # Arrange - Precio rompe por debajo de OR
        dates = pd.date_range('2025-11-17 08:00:00', periods=60, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000] * 30 + [1.0980] * 30,  # Rompe abajo después de OR
            'high': [1.1010] * 30 + [1.0990] * 30,
            'low': [1.0995] * 30 + [1.0975] * 30,
            'close': [1.1005] * 30 + [1.0985] * 30,
            'volume': [1000] * 60
        })
        
        # Act
        or_data = calculator.calculate_opening_range(data)
        
        # Assert
        assert or_data.breakout_status == BreakoutStatus.BELOW
        assert or_data.current_price < or_data.or_low
    
    def test_breakout_status_inside(self, calculator):
        """Test detección de precio dentro de OR"""
        # Arrange - Precio permanece dentro de OR
        dates = pd.date_range('2025-11-17 08:00:00', periods=60, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000] * 60,
            'high': [1.1008] * 60,
            'low': [1.0998] * 60,
            'close': [1.1003] * 60,
            'volume': [1000] * 60
        })
        
        # Act
        or_data = calculator.calculate_opening_range(data)
        
        # Assert
        assert or_data.breakout_status == BreakoutStatus.INSIDE
        assert or_data.or_low <= or_data.current_price <= or_data.or_high
    
    def test_or_range_size(self, calculator, european_session_data):
        """Test cálculo de tamaño de rango de OR"""
        # Act
        or_data = calculator.calculate_opening_range(european_session_data)
        
        # Assert
        expected_range = or_data.or_high - or_data.or_low
        assert or_data.or_range == pytest.approx(expected_range, abs=1e-6)
        assert or_data.or_range > 0
    
    def test_or_midpoint(self, calculator, european_session_data):
        """Test cálculo de punto medio de OR"""
        # Act
        or_data = calculator.calculate_opening_range(european_session_data)
        
        # Assert
        expected_midpoint = (or_data.or_high + or_data.or_low) / 2
        assert or_data.or_midpoint == pytest.approx(expected_midpoint, abs=1e-6)
        assert or_data.or_low < or_data.or_midpoint < or_data.or_high
    
    def test_different_or_duration(self):
        """Test con diferentes duraciones de OR (15 min vs 30 min)"""
        # Arrange
        calculator_15 = OpeningRangeCalculator(
            session_start_hour=8,
            session_start_minute=0,
            or_duration_minutes=15
        )
        
        calculator_30 = OpeningRangeCalculator(
            session_start_hour=8,
            session_start_minute=0,
            or_duration_minutes=30
        )
        
        dates = pd.date_range('2025-11-17 08:00:00', periods=60, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': np.linspace(1.1000, 1.1030, 60),
            'high': np.linspace(1.1010, 1.1040, 60),
            'low': np.linspace(1.0995, 1.1025, 60),
            'close': np.linspace(1.1005, 1.1035, 60),
            'volume': [1000] * 60
        })
        
        # Act
        or_15 = calculator_15.calculate_opening_range(data)
        or_30 = calculator_30.calculate_opening_range(data)
        
        # Assert - OR de 30 min debería tener rango mayor o igual
        assert or_30.or_range >= or_15.or_range
    
    def test_or_with_no_session_data(self, calculator):
        """Test cuando no hay datos de sesión europea"""
        # Arrange - Datos fuera de horario de sesión
        dates = pd.date_range('2025-11-17 15:00:00', periods=30, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000] * 30,
            'high': [1.1010] * 30,
            'low': [1.0995] * 30,
            'close': [1.1005] * 30,
            'volume': [1000] * 30
        })
        
        # Act & Assert
        with pytest.raises(ValueError, match="No se encontraron datos.*Opening Range"):
            calculator.calculate_opening_range(data)
    
    def test_distance_from_or_high(self, calculator):
        """Test cálculo de distancia desde OR high"""
        # Arrange
        dates = pd.date_range('2025-11-17 08:00:00', periods=60, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000] * 30 + [1.1020] * 30,
            'high': [1.1010] * 30 + [1.1030] * 30,
            'low': [1.0995] * 30 + [1.1015] * 30,
            'close': [1.1005] * 30 + [1.1025] * 30,
            'volume': [1000] * 60
        })
        
        # Act
        or_data = calculator.calculate_opening_range(data)
        
        # Assert
        expected_distance = or_data.current_price - or_data.or_high
        assert or_data.distance_from_or_high == pytest.approx(expected_distance, abs=1e-6)
    
    def test_distance_from_or_low(self, calculator):
        """Test cálculo de distancia desde OR low"""
        # Arrange
        dates = pd.date_range('2025-11-17 08:00:00', periods=60, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000] * 30 + [1.0980] * 30,
            'high': [1.1010] * 30 + [1.0990] * 30,
            'low': [1.0995] * 30 + [1.0975] * 30,
            'close': [1.1005] * 30 + [1.0985] * 30,
            'volume': [1000] * 60
        })
        
        # Act
        or_data = calculator.calculate_opening_range(data)
        
        # Assert
        expected_distance = or_data.current_price - or_data.or_low
        assert or_data.distance_from_or_low == pytest.approx(expected_distance, abs=1e-6)


class TestOpeningRangeEdgeCases:
    """Tests de casos edge para Opening Range"""
    
    @pytest.fixture
    def calculator(self):
        return OpeningRangeCalculator(
            session_start_hour=8,
            session_start_minute=0,
            or_duration_minutes=30
        )
    
    def test_or_with_single_candle(self, calculator):
        """Test OR con una sola vela en ventana"""
        # Arrange
        dates = pd.date_range('2025-11-17 08:00:00', periods=1, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000],
            'high': [1.1010],
            'low': [1.0995],
            'close': [1.1005],
            'volume': [1000]
        })
        
        # Act
        or_data = calculator.calculate_opening_range(data)
        
        # Assert
        assert or_data.or_high == 1.1010
        assert or_data.or_low == 1.0995
    
    def test_or_with_flat_price(self, calculator):
        """Test OR con precio plano (sin rango)"""
        # Arrange
        dates = pd.date_range('2025-11-17 08:00:00', periods=30, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000] * 30,
            'high': [1.1000] * 30,
            'low': [1.1000] * 30,
            'close': [1.1000] * 30,
            'volume': [1000] * 30
        })
        
        # Act
        or_data = calculator.calculate_opening_range(data)
        
        # Assert
        assert or_data.or_range == 0.0
        assert or_data.or_high == or_data.or_low == 1.1000
    
    def test_or_crosses_midnight(self):
        """Test OR que cruza la medianoche (caso especial)"""
        # Arrange - Sesión que comienza a las 23:45
        calculator = OpeningRangeCalculator(
            session_start_hour=23,
            session_start_minute=45,
            or_duration_minutes=30  # Hasta 00:15
        )
        
        dates = pd.date_range('2025-11-17 23:45:00', periods=30, freq='1min')
        data = pd.DataFrame({
            'time': dates,
            'open': [1.1000] * 30,
            'high': [1.1010] * 30,
            'low': [1.0995] * 30,
            'close': [1.1005] * 30,
            'volume': [1000] * 30
        })
        
        # Act
        or_data = calculator.calculate_opening_range(data)
        
        # Assert
        assert or_data is not None
        assert or_data.or_high > or_data.or_low
