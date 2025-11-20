"""Tests para IntradayIndicatorCalculator.

Valida el cálculo correcto de indicadores con pre-cálculo adecuado:
- Paquete Táctico M15: 200 velas con indicadores
- Paquete Estratégico D1: 30 velas con indicadores
- Verificación de que EMA 200 se calcula con 200 velas de histórico
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from src.bots.strategies.intraday.gemini_3_pro.bot_1.intraday_indicators import (
    IntradayIndicatorCalculator,
    IntradayCandle_M15,
    IntradayCandle_D1,
)
from src.core.mt5_data_extractor import MT5DataExtractor, Timeframe, OHLCVData


@pytest.fixture
def mock_data_extractor():
    """Fixture: Mock de MT5DataExtractor."""
    extractor = Mock(spec=MT5DataExtractor)
    return extractor


@pytest.fixture
def sample_ohlcv_m15():
    """Fixture: Datos OHLCV M15 de prueba (450 velas)."""
    dates = pd.date_range(start='2023-01-01', periods=450, freq='15min')
    
    # Generar datos sintéticos realistas
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(450) * 0.1)
    
    data = pd.DataFrame({
        'open': close_prices + np.random.randn(450) * 0.05,
        'high': close_prices + abs(np.random.randn(450) * 0.1),
        'low': close_prices - abs(np.random.randn(450) * 0.1),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 450),
    }, index=dates)
    
    return OHLCVData(
        symbol="EURUSD",
        timeframe=Timeframe.M15,
        data=data,
        count=450
    )


@pytest.fixture
def sample_ohlcv_d1():
    """Fixture: Datos OHLCV D1 de prueba (240 velas)."""
    dates = pd.date_range(start='2023-01-01', periods=240, freq='D')
    
    # Generar datos sintéticos realistas
    np.random.seed(43)
    close_prices = 100 + np.cumsum(np.random.randn(240) * 0.5)
    
    data = pd.DataFrame({
        'open': close_prices + np.random.randn(240) * 0.2,
        'high': close_prices + abs(np.random.randn(240) * 0.4),
        'low': close_prices - abs(np.random.randn(240) * 0.4),
        'close': close_prices,
        'volume': np.random.randint(10000, 100000, 240),
    }, index=dates)
    
    return OHLCVData(
        symbol="EURUSD",
        timeframe=Timeframe.D1,
        data=data,
        count=240
    )


@pytest.fixture
def sample_ohlcv_m15_update():
    """Fixture: Datos OHLCV M15 para tactical update (300 velas)."""
    # Generar 300 velas para tener suficiente histórico para updates
    dates = pd.date_range(start='2025-11-19 10:00', periods=300, freq='15min')
    
    np.random.seed(44)
    close_prices = 100 + np.cumsum(np.random.randn(300) * 0.1)
    
    data = pd.DataFrame({
        'open': close_prices + np.random.randn(300) * 0.05,
        'high': close_prices + abs(np.random.randn(300) * 0.1),
        'low': close_prices - abs(np.random.randn(300) * 0.1),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 300),
    }, index=dates)
    
    return OHLCVData(
        symbol="EURUSD",
        timeframe=Timeframe.M15,
        data=data,
        count=300
    )


class TestIntradayIndicatorCalculator:
    """Tests para IntradayIndicatorCalculator."""
    
    def test_calculate_tactical_package_returns_200_candles(
        self, mock_data_extractor, sample_ohlcv_m15
    ):
        """Test: Paquete táctico retorna exactamente 200 velas."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        result = calculator.calculate_tactical_package("EURUSD", candles_to_return=200)
        
        assert len(result) == 200
        assert all(isinstance(c, IntradayCandle_M15) for c in result)
    
    def test_tactical_package_has_all_indicators(
        self, mock_data_extractor, sample_ohlcv_m15
    ):
        """Test: Todas las velas del paquete táctico tienen indicadores."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        result = calculator.calculate_tactical_package("EURUSD", candles_to_return=200)
        
        # Verificar que las últimas velas tienen todos los indicadores calculados
        last_candle = result[-1]
        
        assert last_candle.open is not None
        assert last_candle.high is not None
        assert last_candle.low is not None
        assert last_candle.close is not None
        assert last_candle.volume is not None
        assert last_candle.ema_20 is not None
        assert last_candle.ema_200 is not None  # Crítico: debe estar calculado
        assert last_candle.vwap is not None
        assert last_candle.rsi_14 is not None
        assert last_candle.atr_14 is not None
        assert last_candle.bb_upper is not None
        assert last_candle.bb_lower is not None
        assert last_candle.bb_width is not None
    
    def test_tactical_package_ema200_pre_calculated(
        self, mock_data_extractor, sample_ohlcv_m15
    ):
        """Test: EMA 200 está calculada correctamente en las primeras velas retornadas."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        result = calculator.calculate_tactical_package("EURUSD", candles_to_return=200)
        
        # La primera vela del array (índice 0) debe tener EMA 200
        # porque se calculó con 200 velas de histórico previas
        first_candle = result[0]
        assert first_candle.ema_200 is not None
        
        # Verificar que EMA 200 es un número válido
        assert isinstance(first_candle.ema_200, float)
        assert first_candle.ema_200 > 0
    
    def test_tactical_package_bollinger_bands_calculated(
        self, mock_data_extractor, sample_ohlcv_m15
    ):
        """Test: Bandas de Bollinger están calculadas correctamente."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        result = calculator.calculate_tactical_package("EURUSD", candles_to_return=200)
        
        last_candle = result[-1]
        
        # BB Upper debe ser mayor que BB Lower
        assert last_candle.bb_upper > last_candle.bb_lower
        
        # BB Width debe ser positivo y coherente
        expected_width = last_candle.bb_upper - last_candle.bb_lower
        assert abs(last_candle.bb_width - expected_width) < 0.0001
    
    def test_calculate_strategic_package_returns_30_candles(
        self, mock_data_extractor, sample_ohlcv_d1
    ):
        """Test: Paquete estratégico retorna exactamente 30 velas."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_d1
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        result = calculator.calculate_strategic_package("EURUSD", candles_to_return=30)
        
        assert len(result) == 30
        assert all(isinstance(c, IntradayCandle_D1) for c in result)
    
    def test_strategic_package_has_all_indicators(
        self, mock_data_extractor, sample_ohlcv_d1
    ):
        """Test: Todas las velas del paquete estratégico tienen indicadores."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_d1
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        result = calculator.calculate_strategic_package("EURUSD", candles_to_return=30)
        
        last_candle = result[-1]
        
        assert last_candle.close is not None
        assert last_candle.ema_200 is not None  # Crítico
        assert last_candle.atr_14 is not None
        # prev_close, prev_high, prev_low pueden ser None en la primera vela
        # pero en la última deben estar
        assert last_candle.prev_close is not None
        assert last_candle.prev_high is not None
        assert last_candle.prev_low is not None
    
    def test_strategic_package_ema200_pre_calculated(
        self, mock_data_extractor, sample_ohlcv_d1
    ):
        """Test: EMA 200 está calculada en todas las velas del paquete estratégico."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_d1
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        result = calculator.calculate_strategic_package("EURUSD", candles_to_return=30)
        
        # Todas las velas deben tener EMA 200
        for candle in result:
            assert candle.ema_200 is not None
            assert isinstance(candle.ema_200, float)
    
    def test_strategic_package_prev_values(
        self, mock_data_extractor, sample_ohlcv_d1
    ):
        """Test: Valores previos están calculados correctamente."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_d1
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        result = calculator.calculate_strategic_package("EURUSD", candles_to_return=30)
        
        # Verificar que prev_close de vela N+1 == close de vela N
        for i in range(1, len(result)):
            current = result[i]
            previous = result[i - 1]
            
            if current.prev_close is not None:
                assert abs(current.prev_close - previous.close) < 0.0001
    
    def test_get_full_intraday_packages(
        self, mock_data_extractor, sample_ohlcv_m15, sample_ohlcv_d1
    ):
        """Test: get_full_intraday_packages retorna ambos paquetes."""
        def side_effect(symbol, timeframe, count):
            if timeframe == Timeframe.M15:
                return sample_ohlcv_m15
            elif timeframe == Timeframe.D1:
                return sample_ohlcv_d1
        
        mock_data_extractor.get_ohlcv.side_effect = side_effect
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        result = calculator.get_full_intraday_packages("EURUSD")
        
        assert 'tactical_m15' in result
        assert 'strategic_d1' in result
        
        assert len(result['tactical_m15']) == 200
        assert len(result['strategic_d1']) == 30
        
        # Verificar que son diccionarios (JSON-ready)
        assert isinstance(result['tactical_m15'][0], dict)
        assert isinstance(result['strategic_d1'][0], dict)
    
    def test_tactical_package_insufficient_data(
        self, mock_data_extractor
    ):
        """Test: Error cuando no hay suficientes datos para M15."""
        # Crear OHLCV con solo 100 velas (insuficiente)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='15min')
        data = pd.DataFrame({
            'open': [100] * 100,
            'high': [101] * 100,
            'low': [99] * 100,
            'close': [100] * 100,
            'volume': [1000] * 100,
        }, index=dates)
        
        insufficient_data = OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M15,
            data=data,
            count=100
        )
        
        mock_data_extractor.get_ohlcv.return_value = insufficient_data
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        with pytest.raises(ValueError, match="Datos insuficientes"):
            calculator.calculate_tactical_package("EURUSD", candles_to_return=200)
    
    def test_strategic_package_insufficient_data(
        self, mock_data_extractor
    ):
        """Test: Error cuando no hay suficientes datos para D1."""
        # Crear OHLCV con solo 50 velas (insuficiente)
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        data = pd.DataFrame({
            'open': [100] * 50,
            'high': [101] * 50,
            'low': [99] * 50,
            'close': [100] * 50,
            'volume': [10000] * 50,
        }, index=dates)
        
        insufficient_data = OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.D1,
            data=data,
            count=50
        )
        
        mock_data_extractor.get_ohlcv.return_value = insufficient_data
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        with pytest.raises(ValueError, match="Datos insuficientes"):
            calculator.calculate_strategic_package("EURUSD", candles_to_return=30)
    
    def test_bollinger_bands_calculation(
        self, mock_data_extractor
    ):
        """Test: Cálculo de Bandas de Bollinger es correcto."""
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        # Crear serie de precios simple
        prices = pd.Series([100, 101, 102, 103, 104] * 20)  # 100 valores
        
        bb = calculator._calculate_bollinger_bands(prices, period=20, std_dev=2.0)
        
        assert 'upper' in bb
        assert 'middle' in bb
        assert 'lower' in bb
        assert 'width' in bb
        
        # Verificar que upper > middle > lower (en la mayoría de casos)
        valid_idx = ~bb['upper'].isna()
        assert (bb['upper'][valid_idx] >= bb['middle'][valid_idx]).all()
        assert (bb['middle'][valid_idx] >= bb['lower'][valid_idx]).all()


# ==================== TESTS: TACTICAL UPDATE ====================

class TestTacticalUpdate:
    """Tests para actualización táctica incremental."""
    
    def test_tactical_update_returns_new_candles_only(
        self, mock_data_extractor, sample_ohlcv_m15_update
    ):
        """Test: Retorna solo velas nuevas entre timestamps."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15_update
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        # Simular consulta hace 30 minutos (2 velas M15)
        current_time = datetime(2025, 11, 19, 14, 30, 0)
        last_time = datetime(2025, 11, 19, 14, 0, 0)
        
        update = calculator.calculate_tactical_update(
            symbol="EURUSD",
            last_timestamp=last_time,
            current_timestamp=current_time
        )
        
        # Debe retornar 2 velas (14:00 y 14:15)
        assert len(update) == 2
        
        # Verificar que son las velas correctas
        assert "14:00" in update[0].timestamp or "14:15" in update[0].timestamp
        assert "14:15" in update[1].timestamp or "14:30" in update[1].timestamp
    
    def test_tactical_update_all_indicators_present(
        self, mock_data_extractor, sample_ohlcv_m15_update
    ):
        """Test: Todas las velas tienen todos los indicadores principales."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15_update
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        current_time = datetime(2025, 11, 19, 14, 30, 0)
        last_time = datetime(2025, 11, 19, 14, 0, 0)
        
        update = calculator.calculate_tactical_update(
            symbol="EURUSD",
            last_timestamp=last_time,
            current_timestamp=current_time
        )
        
        # Verificar indicadores principales (siempre deben estar)
        for candle in update:
            assert candle.ema_20 is not None
            assert candle.ema_200 is not None
            assert candle.vwap is not None
            assert candle.rsi_14 is not None
            assert candle.atr_14 is not None
            # Bollinger Bands pueden ser None en primeras velas si no hay suficiente histórico
            # pero al menos deben estar definidos los atributos
            assert hasattr(candle, 'bb_upper')
            assert hasattr(candle, 'bb_lower')
            assert hasattr(candle, 'bb_width')
    
    def test_tactical_update_no_new_candles(
        self, mock_data_extractor
    ):
        """Test: Retorna lista vacía si no hay velas nuevas."""
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        # Misma hora (diferencia de 0 minutos)
        current_time = datetime(2025, 11, 19, 14, 0, 0)
        last_time = datetime(2025, 11, 19, 14, 0, 0)
        
        # Debe lanzar ValueError porque last >= current
        with pytest.raises(ValueError, match="debe ser anterior"):
            calculator.calculate_tactical_update(
                symbol="EURUSD",
                last_timestamp=last_time,
                current_timestamp=current_time
            )
    
    def test_tactical_update_single_candle(
        self, mock_data_extractor, sample_ohlcv_m15_update
    ):
        """Test: Retorna una sola vela si solo pasaron 15 minutos."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15_update
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        current_time = datetime(2025, 11, 19, 14, 15, 0)
        last_time = datetime(2025, 11, 19, 14, 0, 0)
        
        update = calculator.calculate_tactical_update(
            symbol="EURUSD",
            last_timestamp=last_time,
            current_timestamp=current_time
        )
        
        # Debe retornar 1 vela (14:00)
        assert len(update) == 1
        assert "14:00" in update[0].timestamp or "14:15" in update[0].timestamp
    
    def test_tactical_update_multiple_candles(
        self, mock_data_extractor, sample_ohlcv_m15_update
    ):
        """Test: Retorna múltiples velas si pasó más tiempo."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15_update
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        # 1 hora = 4 velas M15
        current_time = datetime(2025, 11, 19, 15, 0, 0)
        last_time = datetime(2025, 11, 19, 14, 0, 0)
        
        update = calculator.calculate_tactical_update(
            symbol="EURUSD",
            last_timestamp=last_time,
            current_timestamp=current_time
        )
        
        # Debe retornar 4 velas (14:00, 14:15, 14:30, 14:45)
        assert len(update) == 4
    
    def test_tactical_update_validates_timestamp_order(
        self, mock_data_extractor
    ):
        """Test: Valida que last_timestamp < current_timestamp."""
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        # Timestamps invertidos
        current_time = datetime(2025, 11, 19, 14, 0, 0)
        last_time = datetime(2025, 11, 19, 15, 0, 0)
        
        with pytest.raises(ValueError, match="debe ser anterior"):
            calculator.calculate_tactical_update(
                symbol="EURUSD",
                last_timestamp=last_time,
                current_timestamp=current_time
            )
    
    def test_tactical_update_default_current_timestamp(
        self, mock_data_extractor, sample_ohlcv_m15_update
    ):
        """Test: Usa datetime.now() si no se proporciona current_timestamp."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15_update
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        # Solo proporcionar last_timestamp
        last_time = datetime.now() - pd.Timedelta(minutes=30)
        
        # No debe lanzar error (usa datetime.now() internamente)
        update = calculator.calculate_tactical_update(
            symbol="EURUSD",
            last_timestamp=last_time
        )
        
        # Debe retornar al menos 1 vela
        assert len(update) >= 1
    
    def test_tactical_update_ema_200_calculated_correctly(
        self, mock_data_extractor, sample_ohlcv_m15_update
    ):
        """Test: EMA 200 está calculada correctamente en velas nuevas."""
        mock_data_extractor.get_ohlcv.return_value = sample_ohlcv_m15_update
        
        calculator = IntradayIndicatorCalculator(mock_data_extractor)
        
        current_time = datetime(2025, 11, 19, 14, 30, 0)
        last_time = datetime(2025, 11, 19, 14, 0, 0)
        
        update = calculator.calculate_tactical_update(
            symbol="EURUSD",
            last_timestamp=last_time,
            current_timestamp=current_time
        )
        
        # Todas las velas deben tener EMA 200 (pre-calculada con histórico)
        for candle in update:
            assert candle.ema_200 is not None
            assert candle.ema_200 > 0
