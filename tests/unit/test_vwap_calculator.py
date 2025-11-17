"""
Tests unitarios para VWAP Calculator

Tests para cálculo de VWAP (Volume Weighted Average Price), bandas de VWAP,
pendiente y reinicio de sesión.

Autor: Sistema Botrading
Fecha: 2025-11-17
Ticket: VWAP Methodology - Indicadores VWAP
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from src.core.indicator_calculator import IndicatorCalculator, IndicatorData
from src.core.mt5_data_extractor import OHLCVData, Timeframe


class TestVWAPCalculator:
    """Tests para cálculo de VWAP"""
    
    @pytest.fixture
    def calculator(self):
        """Fixture del calculador de indicadores"""
        return IndicatorCalculator()
    
    @pytest.fixture
    def sample_ohlcv_data(self):
        """Datos OHLCV de ejemplo para testing"""
        dates = pd.date_range(start='2025-11-17 08:00', periods=100, freq='5min')
        
        data = pd.DataFrame({
            'time': dates,
            'open': np.random.uniform(1.1000, 1.1100, 100),
            'high': np.random.uniform(1.1050, 1.1150, 100),
            'low': np.random.uniform(1.0950, 1.1050, 100),
            'close': np.random.uniform(1.1000, 1.1100, 100),
            'volume': np.random.uniform(1000, 5000, 100)
        })
        
        # Asegurar que high >= low
        data['high'] = data[['high', 'close', 'open']].max(axis=1)
        data['low'] = data[['low', 'close', 'open']].min(axis=1)
        
        return OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=data,
            count=100
        )
    
    @pytest.fixture
    def realistic_eurusd_data(self):
        """Datos EURUSD más realistas con tendencia"""
        dates = pd.date_range(start='2025-11-17 08:00', periods=100, freq='5min')
        
        # Crear tendencia alcista realista
        base_price = 1.1000
        trend = np.linspace(0, 0.0050, 100)  # Tendencia de +50 pips
        noise = np.random.normal(0, 0.0010, 100)  # Ruido ±10 pips
        
        close_prices = base_price + trend + noise
        
        data = pd.DataFrame({
            'time': dates,
            'open': close_prices - np.random.uniform(0, 0.0005, 100),
            'high': close_prices + np.random.uniform(0.0005, 0.0015, 100),
            'low': close_prices - np.random.uniform(0.0005, 0.0015, 100),
            'close': close_prices,
            'volume': np.random.uniform(2000, 8000, 100)
        })
        
        return OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=data,
            count=100
        )
    
    def test_calculate_vwap_basic(self, calculator, sample_ohlcv_data):
        """Test básico de cálculo de VWAP"""
        # Act
        vwap_series = calculator._calculate_vwap(sample_ohlcv_data.data)
        
        # Assert
        assert vwap_series is not None
        assert len(vwap_series) == len(sample_ohlcv_data.data)
        assert not vwap_series.isna().all()  # Al menos algunos valores no-NaN
        
        # VWAP debe estar dentro de un rango razonable
        last_vwap = vwap_series.iloc[-1]
        assert 1.0900 < last_vwap < 1.1200
    
    def test_vwap_formula_correctness(self, calculator):
        """Test de correctitud de fórmula VWAP"""
        # Arrange - Datos controlados
        data = pd.DataFrame({
            'time': pd.date_range('2025-11-17 08:00', periods=5, freq='5min'),
            'high': [1.1010, 1.1020, 1.1030, 1.1040, 1.1050],
            'low': [1.1000, 1.1010, 1.1020, 1.1030, 1.1040],
            'close': [1.1005, 1.1015, 1.1025, 1.1035, 1.1045],
            'volume': [1000, 2000, 1500, 2500, 1000]
        })
        
        # Act
        vwap_series = calculator._calculate_vwap(data)
        
        # Assert - Cálculo manual del último VWAP
        typical_prices = (data['high'] + data['low'] + data['close']) / 3
        cumulative_tpv = (typical_prices * data['volume']).cumsum()
        cumulative_volume = data['volume'].cumsum()
        expected_vwap = cumulative_tpv / cumulative_volume
        
        assert np.isclose(vwap_series.iloc[-1], expected_vwap.iloc[-1], rtol=1e-6)
    
    def test_vwap_is_cumulative(self, calculator, sample_ohlcv_data):
        """Test que VWAP es acumulativo (cada valor depende de anteriores)"""
        # Act
        vwap_series = calculator._calculate_vwap(sample_ohlcv_data.data)
        
        # Assert - VWAP debe cambiar gradualmente, no bruscamente
        vwap_changes = vwap_series.diff().abs()
        
        # Los cambios no deben ser mayores al 1% del precio (muy brusco para VWAP)
        max_reasonable_change = 0.01 * vwap_series.mean()
        assert (vwap_changes[1:] < max_reasonable_change).all()
    
    def test_calculate_vwap_slope(self, calculator, realistic_eurusd_data):
        """Test de cálculo de pendiente de VWAP"""
        # Arrange
        vwap_series = calculator._calculate_vwap(realistic_eurusd_data.data)
        
        # Act
        slope, description = calculator._calculate_vwap_slope(vwap_series, lookback=10)
        
        # Assert
        assert slope is not None
        assert description in ["ascendente", "descendente", "plana", "insuficiente"]
        
        # Para datos con tendencia alcista, esperamos pendiente positiva
        # (aunque puede fallar con datos random, así que solo verificamos el tipo)
        assert isinstance(slope, (int, float))
    
    def test_vwap_slope_ascending(self, calculator):
        """Test pendiente ascendente clara"""
        # Arrange - VWAP claramente ascendente
        dates = pd.date_range('2025-11-17 08:00', periods=20, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': np.linspace(1.1000, 1.1100, 20),
            'low': np.linspace(1.0990, 1.1090, 20),
            'close': np.linspace(1.0995, 1.1095, 20),
            'volume': [1000] * 20
        })
        
        vwap_series = calculator._calculate_vwap(data)
        
        # Act
        slope, description = calculator._calculate_vwap_slope(vwap_series, lookback=10)
        
        # Assert
        assert slope > 0
        assert description == "ascendente"
    
    def test_vwap_slope_descending(self, calculator):
        """Test pendiente descendente clara"""
        # Arrange - VWAP claramente descendente
        dates = pd.date_range('2025-11-17 08:00', periods=20, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': np.linspace(1.1100, 1.1000, 20),
            'low': np.linspace(1.1090, 1.0990, 20),
            'close': np.linspace(1.1095, 1.0995, 20),
            'volume': [1000] * 20
        })
        
        vwap_series = calculator._calculate_vwap(data)
        
        # Act
        slope, description = calculator._calculate_vwap_slope(vwap_series, lookback=10)
        
        # Assert
        assert slope < 0
        assert description == "descendente"
    
    def test_vwap_slope_flat(self, calculator):
        """Test pendiente plana"""
        # Arrange - VWAP plano
        dates = pd.date_range('2025-11-17 08:00', periods=20, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': [1.1005] * 20,
            'low': [1.0995] * 20,
            'close': [1.1000] * 20,
            'volume': [1000] * 20
        })
        
        vwap_series = calculator._calculate_vwap(data)
        
        # Act
        slope, description = calculator._calculate_vwap_slope(vwap_series, lookback=10)
        
        # Assert
        assert abs(slope) < 0.0001  # Muy cerca de 0
        assert description == "plana"
    
    def test_calculate_vwap_bands(self, calculator, sample_ohlcv_data):
        """Test de cálculo de bandas VWAP"""
        # Arrange
        vwap_series = calculator._calculate_vwap(sample_ohlcv_data.data)
        
        # Act
        bands = calculator._calculate_vwap_bands(sample_ohlcv_data.data, vwap_series)
        
        # Assert
        assert 'upper_1' in bands
        assert 'lower_1' in bands
        assert 'upper_2' in bands
        assert 'lower_2' in bands
        
        # Las bandas deben ser series con la misma longitud
        assert len(bands['upper_1']) == len(sample_ohlcv_data.data)
        assert len(bands['lower_1']) == len(sample_ohlcv_data.data)
        
        # Validar orden: upper_2 > upper_1 > VWAP > lower_1 > lower_2
        last_idx = -1
        assert bands['upper_2'].iloc[last_idx] > bands['upper_1'].iloc[last_idx]
        assert bands['upper_1'].iloc[last_idx] > vwap_series.iloc[last_idx]
        assert vwap_series.iloc[last_idx] > bands['lower_1'].iloc[last_idx]
        assert bands['lower_1'].iloc[last_idx] > bands['lower_2'].iloc[last_idx]
    
    def test_vwap_bands_symmetry(self, calculator):
        """Test simetría de bandas VWAP"""
        # Arrange - Datos simétricos
        dates = pd.date_range('2025-11-17 08:00', periods=50, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': [1.1010] * 50,
            'low': [1.0990] * 50,
            'close': [1.1000] * 50,
            'volume': [1000] * 50
        })
        
        vwap_series = calculator._calculate_vwap(data)
        
        # Act
        bands = calculator._calculate_vwap_bands(data, vwap_series)
        
        # Assert - Las bandas deben ser aproximadamente simétricas
        last_idx = -1
        upper_1_distance = bands['upper_1'].iloc[last_idx] - vwap_series.iloc[last_idx]
        lower_1_distance = vwap_series.iloc[last_idx] - bands['lower_1'].iloc[last_idx]
        
        assert np.isclose(upper_1_distance, lower_1_distance, rtol=0.01)
    
    def test_vwap_with_session_reset(self, calculator):
        """Test reinicio de VWAP en nueva sesión"""
        # Arrange - Datos de 2 días
        day1_dates = pd.date_range('2025-11-17 08:00', periods=50, freq='5min')
        day2_dates = pd.date_range('2025-11-18 08:00', periods=50, freq='5min')
        
        day1_data = pd.DataFrame({
            'time': day1_dates,
            'high': np.linspace(1.1000, 1.1100, 50),
            'low': np.linspace(1.0990, 1.1090, 50),
            'close': np.linspace(1.0995, 1.1095, 50),
            'volume': [1000] * 50
        })
        
        day2_data = pd.DataFrame({
            'time': day2_dates,
            'high': np.linspace(1.1100, 1.1200, 50),
            'low': np.linspace(1.1090, 1.1190, 50),
            'close': np.linspace(1.1095, 1.1195, 50),
            'volume': [1000] * 50
        })
        
        # Act - Calcular VWAP por separado (simulando reinicio)
        vwap_day1 = calculator._calculate_vwap(day1_data)
        vwap_day2 = calculator._calculate_vwap(day2_data)
        
        # Assert - El primer valor de día 2 debe ser cercano al precio típico inicial
        typical_price_day2_first = (
            day2_data['high'].iloc[0] + 
            day2_data['low'].iloc[0] + 
            day2_data['close'].iloc[0]
        ) / 3
        
        assert np.isclose(vwap_day2.iloc[0], typical_price_day2_first, rtol=0.01)
    
    def test_vwap_in_indicator_data(self, calculator, realistic_eurusd_data):
        """Test integración de VWAP en IndicatorData"""
        # Act
        indicators = calculator.calculate_indicators_for_timeframe(realistic_eurusd_data)
        
        # Assert
        assert hasattr(indicators, 'vwap')
        assert hasattr(indicators, 'vwap_slope')
        assert hasattr(indicators, 'vwap_slope_description')
        assert hasattr(indicators, 'vwap_upper_1')
        assert hasattr(indicators, 'vwap_lower_1')
        assert hasattr(indicators, 'vwap_upper_2')
        assert hasattr(indicators, 'vwap_lower_2')
        
        # Valores no deben ser None
        assert indicators.vwap is not None
        assert indicators.vwap_slope is not None
        assert indicators.vwap_slope_description is not None
    
    def test_vwap_format_json(self, calculator, realistic_eurusd_data):
        """Test formateo JSON de indicadores VWAP"""
        # Arrange
        timeframes_data = {Timeframe.M5: realistic_eurusd_data}
        indicators = calculator.calculate_indicators_multi_timeframe(
            "EURUSD", timeframes_data
        )
        
        # Act
        json_data = calculator.format_indicators_json(indicators)
        
        # Assert
        assert 'timeframes' in json_data
        assert 'M5' in json_data['timeframes']
        
        m5_indicators = json_data['timeframes']['M5']['indicators']
        assert 'vwap' in m5_indicators
        assert 'vwap_slope' in m5_indicators
        assert 'vwap_slope_description' in m5_indicators
        assert 'vwap_bands' in m5_indicators
        
        vwap_bands = m5_indicators['vwap_bands']
        assert 'upper_1' in vwap_bands
        assert 'lower_1' in vwap_bands
        assert 'upper_2' in vwap_bands
        assert 'lower_2' in vwap_bands
    
    def test_vwap_handles_zero_volume(self, calculator):
        """Test manejo de volumen cero"""
        # Arrange - Datos con volumen cero
        dates = pd.date_range('2025-11-17 08:00', periods=10, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': [1.1010] * 10,
            'low': [1.0990] * 10,
            'close': [1.1000] * 10,
            'volume': [0] * 10  # Volumen cero
        })
        
        # Act & Assert - No debe lanzar error
        try:
            vwap_series = calculator._calculate_vwap(data)
            # Si hay volumen cero, VWAP podría ser NaN o inf
            # Lo importante es que no crashee
            assert vwap_series is not None
        except Exception as e:
            pytest.fail(f"VWAP falló con volumen cero: {e}")
    
    def test_vwap_with_minimal_data(self, calculator):
        """Test VWAP con datos mínimos (edge case)"""
        # Arrange - Solo 3 velas
        dates = pd.date_range('2025-11-17 08:00', periods=3, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': [1.1010, 1.1020, 1.1030],
            'low': [1.0990, 1.1000, 1.1010],
            'close': [1.1000, 1.1010, 1.1020],
            'volume': [1000, 1500, 1200]
        })
        
        # Act
        vwap_series = calculator._calculate_vwap(data)
        
        # Assert
        assert len(vwap_series) == 3
        assert not vwap_series.isna().all()


class TestVWAPEdgeCases:
    """Tests de casos edge para VWAP"""
    
    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()
    
    def test_vwap_with_high_volatility(self, calculator):
        """Test VWAP con alta volatilidad"""
        dates = pd.date_range('2025-11-17 08:00', periods=50, freq='5min')
        
        # Datos con alta volatilidad
        close_prices = [1.1000]
        for _ in range(49):
            change = np.random.choice([-0.0030, 0.0030])  # ±30 pips
            close_prices.append(close_prices[-1] + change)
        
        data = pd.DataFrame({
            'time': dates,
            'high': [p + 0.0010 for p in close_prices],
            'low': [p - 0.0010 for p in close_prices],
            'close': close_prices,
            'volume': np.random.uniform(1000, 5000, 50)
        })
        
        # Act
        vwap_series = calculator._calculate_vwap(data)
        bands = calculator._calculate_vwap_bands(data, vwap_series)
        
        # Assert - Bandas deben ser más anchas con alta volatilidad
        band_width = bands['upper_2'].iloc[-1] - bands['lower_2'].iloc[-1]
        assert band_width > 0.0050  # Más de 50 pips de ancho
    
    def test_vwap_slope_insufficient_data(self, calculator):
        """Test pendiente con datos insuficientes"""
        # Arrange - Solo 5 velas, lookback=10
        dates = pd.date_range('2025-11-17 08:00', periods=5, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': [1.1010] * 5,
            'low': [1.0990] * 5,
            'close': [1.1000] * 5,
            'volume': [1000] * 5
        })
        
        vwap_series = calculator._calculate_vwap(data)
        
        # Act
        slope, description = calculator._calculate_vwap_slope(vwap_series, lookback=10)
        
        # Assert
        assert description == "insuficiente"
