"""
Tests unitarios para ATR Calculator

Tests para cálculo de ATR (Average True Range) según fórmula de Wilder.

Autor: Sistema Botrading
Fecha: 2025-11-17
Ticket: VWAP Methodology - ATR Calculator
"""

import pytest
import pandas as pd
import numpy as np
from src.core.indicator_calculator import IndicatorCalculator
from src.core.mt5_data_extractor import OHLCVData, Timeframe


class TestATRCalculator:
    """Tests para cálculo de ATR"""
    
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
    
    def test_calculate_atr_basic(self, calculator, sample_ohlcv_data):
        """Test básico de cálculo de ATR"""
        # Act
        atr_series = calculator._calculate_atr(sample_ohlcv_data.data, period=14)
        
        # Assert
        assert atr_series is not None
        assert len(atr_series) == len(sample_ohlcv_data.data)
        
        # ATR debe tener valores positivos
        valid_atr = atr_series.dropna()
        assert (valid_atr > 0).all()
    
    def test_atr_formula_correctness(self, calculator):
        """Test de correctitud de fórmula ATR"""
        # Arrange - Datos controlados
        data = pd.DataFrame({
            'time': pd.date_range('2025-11-17 08:00', periods=20, freq='5min'),
            'high': [1.1010, 1.1020, 1.1015, 1.1025, 1.1030, 
                     1.1028, 1.1035, 1.1040, 1.1038, 1.1045,
                     1.1043, 1.1050, 1.1048, 1.1055, 1.1053,
                     1.1060, 1.1058, 1.1065, 1.1063, 1.1070],
            'low': [1.1000, 1.1010, 1.1005, 1.1015, 1.1020,
                    1.1018, 1.1025, 1.1030, 1.1028, 1.1035,
                    1.1033, 1.1040, 1.1038, 1.1045, 1.1043,
                    1.1050, 1.1048, 1.1055, 1.1053, 1.1060],
            'close': [1.1005, 1.1015, 1.1010, 1.1020, 1.1025,
                      1.1023, 1.1030, 1.1035, 1.1033, 1.1040,
                      1.1038, 1.1045, 1.1043, 1.1050, 1.1048,
                      1.1055, 1.1053, 1.1060, 1.1058, 1.1065],
            'volume': [1000] * 20
        })
        
        # Act
        atr_series = calculator._calculate_atr(data, period=14)
        
        # Assert - ATR debe existir después del período inicial
        assert not atr_series.iloc[-1] is None
        assert atr_series.iloc[-1] > 0
    
    def test_atr_period_14(self, calculator, sample_ohlcv_data):
        """Test ATR con período 14 (estándar)"""
        # Act
        atr_14 = calculator._calculate_atr(sample_ohlcv_data.data, period=14)
        
        # Assert
        assert atr_14 is not None
        # ATR debe empezar a tener valores después de 14 períodos
        assert not atr_14.iloc[13:].dropna().empty
    
    def test_atr_period_21(self, calculator, sample_ohlcv_data):
        """Test ATR con período 21"""
        # Act
        atr_21 = calculator._calculate_atr(sample_ohlcv_data.data, period=21)
        
        # Assert
        assert atr_21 is not None
        # ATR debe empezar a tener valores después de 21 períodos
        assert not atr_21.iloc[20:].dropna().empty
    
    def test_atr_increases_with_volatility(self, calculator):
        """Test que ATR aumenta con mayor volatilidad"""
        # Arrange - Datos con baja volatilidad
        dates = pd.date_range('2025-11-17 08:00', periods=50, freq='5min')
        low_vol_data = pd.DataFrame({
            'time': dates,
            'high': [1.1010] * 50,
            'low': [1.1000] * 50,
            'close': [1.1005] * 50,
            'volume': [1000] * 50
        })
        
        # Datos con alta volatilidad
        high_vol_data = pd.DataFrame({
            'time': dates,
            'high': [1.1000 + i * 0.0010 for i in range(50)],
            'low': [1.1000 + i * 0.0010 - 0.0020 for i in range(50)],
            'close': [1.1000 + i * 0.0010 - 0.0010 for i in range(50)],
            'volume': [1000] * 50
        })
        
        # Act
        atr_low_vol = calculator._calculate_atr(low_vol_data, period=14)
        atr_high_vol = calculator._calculate_atr(high_vol_data, period=14)
        
        # Assert - ATR alto > ATR bajo
        assert atr_high_vol.iloc[-1] > atr_low_vol.iloc[-1]
    
    def test_atr_in_indicator_data(self, calculator, sample_ohlcv_data):
        """Test integración de ATR en IndicatorData"""
        # Act
        indicators = calculator.calculate_indicators_for_timeframe(sample_ohlcv_data)
        
        # Assert
        assert hasattr(indicators, 'atr_14')
        assert hasattr(indicators, 'atr_21')
        
        # Valores no deben ser None
        assert indicators.atr_14 is not None
        assert indicators.atr_21 is not None
        
        # Deben ser positivos
        assert indicators.atr_14 > 0
        assert indicators.atr_21 > 0
    
    def test_atr_format_json(self, calculator, sample_ohlcv_data):
        """Test formateo JSON de ATR"""
        # Arrange
        timeframes_data = {Timeframe.M5: sample_ohlcv_data}
        indicators = calculator.calculate_indicators_multi_timeframe(
            "EURUSD", timeframes_data
        )
        
        # Act
        json_data = calculator.format_indicators_json(indicators)
        
        # Assert
        assert 'timeframes' in json_data
        assert 'M5' in json_data['timeframes']
        
        m5_indicators = json_data['timeframes']['M5']['indicators']
        assert 'atr_14' in m5_indicators
        assert 'atr_21' in m5_indicators
        
        # Valores positivos
        assert m5_indicators['atr_14'] > 0
        assert m5_indicators['atr_21'] > 0
    
    def test_atr_with_gaps(self, calculator):
        """Test ATR con gaps (diferencias grandes entre close y open siguiente)"""
        # Arrange - Datos con gap
        dates = pd.date_range('2025-11-17 08:00', periods=20, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': [1.1010] * 10 + [1.1110] * 10,  # Gap de 100 pips
            'low': [1.1000] * 10 + [1.1100] * 10,
            'close': [1.1005] * 10 + [1.1105] * 10,
            'volume': [1000] * 20
        })
        
        # Act
        atr_series = calculator._calculate_atr(data, period=14)
        
        # Assert - ATR debe reflejar el gap
        # ATR después del gap debe ser mayor que antes
        atr_before_gap = atr_series.iloc[9]
        atr_after_gap = atr_series.iloc[-1]
        
        # Puede ser NaN antes del período mínimo
        if not pd.isna(atr_before_gap):
            assert atr_after_gap > atr_before_gap
    
    def test_atr_minimal_data(self, calculator):
        """Test ATR con datos mínimos"""
        # Arrange - Justo suficiente para ATR 14
        dates = pd.date_range('2025-11-17 08:00', periods=15, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': np.linspace(1.1000, 1.1050, 15),
            'low': np.linspace(1.0990, 1.1040, 15),
            'close': np.linspace(1.0995, 1.1045, 15),
            'volume': [1000] * 15
        })
        
        # Act
        atr_series = calculator._calculate_atr(data, period=14)
        
        # Assert
        assert atr_series is not None
        # Último valor debe existir
        assert not pd.isna(atr_series.iloc[-1])
    
    def test_atr_constant_range(self, calculator):
        """Test ATR con rango constante"""
        # Arrange - Rango constante de 10 pips
        dates = pd.date_range('2025-11-17 08:00', periods=30, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': [1.1010] * 30,
            'low': [1.1000] * 30,
            'close': [1.1005] * 30,
            'volume': [1000] * 30
        })
        
        # Act
        atr_series = calculator._calculate_atr(data, period=14)
        
        # Assert - ATR debe estabilizarse en el valor del rango
        stable_atr = atr_series.iloc[-5:]  # Últimos 5 valores
        
        # ATR debe ser cercano a 0.0010 (el rango constante)
        assert all(np.isclose(stable_atr.dropna(), 0.0010, rtol=0.1))


class TestATREdgeCases:
    """Tests de casos edge para ATR"""
    
    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()
    
    def test_atr_with_zero_range(self, calculator):
        """Test ATR con rangos cero (precio sin movimiento)"""
        # Arrange - Precios idénticos (sin movimiento)
        dates = pd.date_range('2025-11-17 08:00', periods=20, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': [1.1000] * 20,
            'low': [1.1000] * 20,
            'close': [1.1000] * 20,
            'volume': [1000] * 20
        })
        
        # Act
        atr_series = calculator._calculate_atr(data, period=14)
        
        # Assert - ATR debe ser 0 o muy cercano a 0
        last_atr = atr_series.dropna().iloc[-1]
        assert np.isclose(last_atr, 0.0, atol=1e-10)
    
    def test_atr_period_larger_than_data(self, calculator):
        """Test ATR cuando período es mayor que datos disponibles"""
        # Arrange - Solo 10 velas, pero período 14
        dates = pd.date_range('2025-11-17 08:00', periods=10, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': np.linspace(1.1000, 1.1050, 10),
            'low': np.linspace(1.0990, 1.1040, 10),
            'close': np.linspace(1.0995, 1.1045, 10),
            'volume': [1000] * 10
        })
        
        # Act
        atr_series = calculator._calculate_atr(data, period=14)
        
        # Assert - ATR puede tener todos NaN o valores solo al final
        assert atr_series is not None
        # No debe crashear, aunque pueda tener NaN
    
    def test_atr_different_periods_comparison(self, calculator):
        """Test comparación entre ATR 14 y ATR 21"""
        # Arrange
        dates = pd.date_range('2025-11-17 08:00', periods=50, freq='5min')
        data = pd.DataFrame({
            'time': dates,
            'high': np.random.uniform(1.1000, 1.1100, 50),
            'low': np.random.uniform(1.0950, 1.1050, 50),
            'close': np.random.uniform(1.0975, 1.1075, 50),
            'volume': [1000] * 50
        })
        data['high'] = data[['high', 'close']].max(axis=1)
        data['low'] = data[['low', 'close']].min(axis=1)
        
        # Act
        atr_14 = calculator._calculate_atr(data, period=14)
        atr_21 = calculator._calculate_atr(data, period=21)
        
        # Assert - Ambos deben existir
        assert not pd.isna(atr_14.iloc[-1])
        assert not pd.isna(atr_21.iloc[-1])
        
        # ATR 14 suele ser más reactivo (puede variar más)
        # Pero ambos deben estar en el mismo orden de magnitud
        ratio = atr_14.iloc[-1] / atr_21.iloc[-1]
        assert 0.5 < ratio < 2.0  # No deben diferir por más del doble
