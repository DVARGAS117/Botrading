"""
Pruebas unitarias para IndicatorCalculator - Cálculo de indicadores técnicos por timeframe.

Este módulo contiene las pruebas TDD para el cálculo de indicadores EMA, RSI, MACD
y volumen por múltiples timeframes, siguiendo los criterios de aceptación del issue T23.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T23 - Cálculo y formato de indicadores por timeframe
"""
import pytest
import pandas as pd
import numpy as np

from src.core.indicator_calculator import IndicatorCalculator, IndicatorData, TimeframeIndicators
from src.core.mt5_data_extractor import OHLCVData, Timeframe


class TestIndicatorCalculator:
    """Pruebas para la clase IndicatorCalculator."""

    @pytest.fixture
    def sample_ohlcv_data(self):
        """Fixture que proporciona datos OHLCV de ejemplo."""
        # Crear datos de prueba con 100 velas
        np.random.seed(42)  # Para reproducibilidad
        n = 100

        # Generar precios con tendencia
        base_price = 1.1000
        trend = np.linspace(0, 0.01, n)
        noise = np.random.normal(0, 0.001, n)
        close_prices = base_price + trend + noise

        # Generar OHLC basado en close
        high = close_prices + np.abs(np.random.normal(0, 0.0005, n))
        low = close_prices - np.abs(np.random.normal(0, 0.0005, n))
        open_prices = close_prices + np.random.normal(0, 0.0002, n)

        # Volumen
        volume = np.random.randint(1000, 10000, n)

        # Crear DataFrame
        data = {
            'time': pd.date_range('2023-01-01', periods=n, freq='5min'),
            'open': open_prices,
            'high': high,
            'low': low,
            'close': close_prices,
            'volume': volume
        }

        df = pd.DataFrame(data)

        return OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=df,
            count=n
        )

    @pytest.fixture
    def indicator_calculator(self):
        """Fixture que proporciona una instancia de IndicatorCalculator."""
        return IndicatorCalculator()

    def test_calculate_ema20(self, indicator_calculator, sample_ohlcv_data):
        """Prueba el cálculo de EMA 20."""
        ema20 = indicator_calculator._calculate_ema(sample_ohlcv_data.data['close'], 20)

        # Verificar que se calcula correctamente
        assert len(ema20) == len(sample_ohlcv_data.data)
        assert not ema20.isna().all()  # No debe ser todo NaN

        # EMA se calcula desde el primer valor, pero los primeros son menos confiables
        assert not ema20.isna().any()  # No debe haber NaN en EMA

        # Verificar que es una serie pandas
        assert isinstance(ema20, pd.Series)

    def test_calculate_rsi(self, indicator_calculator, sample_ohlcv_data):
        """Prueba el cálculo de RSI."""
        rsi = indicator_calculator._calculate_rsi(sample_ohlcv_data.data['close'], 14)

        assert len(rsi) == len(sample_ohlcv_data.data)
        # RSI puede tener algunos NaN al inicio debido al cálculo
        valid_rsi = rsi.dropna()
        assert len(valid_rsi) > 0

        # RSI debe estar entre 0 y 100 cuando es válido
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()

    def test_calculate_macd(self, indicator_calculator, sample_ohlcv_data):
        """Prueba el cálculo de MACD."""
        macd_data = indicator_calculator._calculate_macd(sample_ohlcv_data.data['close'])

        assert 'macd' in macd_data
        assert 'signal' in macd_data
        assert 'histogram' in macd_data

        # Verificar longitudes
        assert len(macd_data['macd']) == len(sample_ohlcv_data.data)
        assert len(macd_data['signal']) == len(sample_ohlcv_data.data)
        assert len(macd_data['histogram']) == len(sample_ohlcv_data.data)

        # Verificar que histogram = macd - signal
        histogram_calc = macd_data['macd'] - macd_data['signal']
        pd.testing.assert_series_equal(
            macd_data['histogram'],
            histogram_calc,
            check_names=False
        )

    def test_calculate_indicators_multi_timeframe(self, indicator_calculator):
        """Prueba el cálculo de indicadores para múltiples timeframes."""
        # Crear datos mock para diferentes timeframes
        timeframes_data = {}

        for tf in [Timeframe.M5, Timeframe.M15, Timeframe.H1]:
            # Crear datos similares pero con diferentes longitudes
            n = 60 if tf == Timeframe.M5 else 60 if tf == Timeframe.M15 else 60

            data = {
                'time': pd.date_range('2023-01-01', periods=n, freq='5min'),
                'open': np.random.uniform(1.09, 1.11, n),
                'high': np.random.uniform(1.10, 1.12, n),
                'low': np.random.uniform(1.08, 1.10, n),
                'close': np.random.uniform(1.09, 1.11, n),
                'volume': np.random.randint(1000, 10000, n)
            }

            timeframes_data[tf] = OHLCVData(
                symbol="EURUSD",
                timeframe=tf,
                data=pd.DataFrame(data),
                count=n
            )

        result = indicator_calculator.calculate_indicators_multi_timeframe(
            "EURUSD", timeframes_data
        )

        assert isinstance(result, TimeframeIndicators)
        assert result.symbol == "EURUSD"

        # Verificar que tiene los tres timeframes
        assert Timeframe.M5 in result.indicators
        assert Timeframe.M15 in result.indicators
        assert Timeframe.H1 in result.indicators

        # Verificar que cada timeframe tiene indicadores
        for tf in [Timeframe.M5, Timeframe.M15, Timeframe.H1]:
            assert isinstance(result.indicators[tf], IndicatorData)

    def test_format_indicators_json(self, indicator_calculator):
        """Prueba el formateo de indicadores a JSON."""
        # Crear datos de prueba
        indicators = TimeframeIndicators(
            symbol="EURUSD",
            indicators={
                Timeframe.M5: IndicatorData(
                    symbol="EURUSD",
                    timeframe=Timeframe.M5,
                    ema20=1.1050,
                    ema50=1.1020,
                    rsi=65.5,
                    macd=0.0012,
                    signal=0.0008,
                    histogram=0.0004,
                    volume_avg=5000.0
                ),
                Timeframe.M15: IndicatorData(
                    symbol="EURUSD",
                    timeframe=Timeframe.M15,
                    ema20=1.1045,
                    ema50=1.1015,
                    rsi=62.0,
                    macd=0.0010,
                    signal=0.0007,
                    histogram=0.0003,
                    volume_avg=4800.0
                ),
                Timeframe.H1: IndicatorData(
                    symbol="EURUSD",
                    timeframe=Timeframe.H1,
                    ema20=1.1040,
                    ema50=1.1010,
                    rsi=58.5,
                    macd=0.0008,
                    signal=0.0006,
                    histogram=0.0002,
                    volume_avg=4500.0
                )
            }
        )

        json_data = indicator_calculator.format_indicators_json(indicators)

        # Verificar estructura del JSON
        assert "symbol" in json_data
        assert "timestamp" in json_data
        assert "timeframes" in json_data

        assert json_data["symbol"] == "EURUSD"
        assert isinstance(json_data["timestamp"], str)

        timeframes = json_data["timeframes"]
        assert "M5" in timeframes
        assert "M15" in timeframes
        assert "H1" in timeframes

        # Verificar estructura de cada timeframe
        for tf_name in ["M5", "M15", "H1"]:
            tf_data = timeframes[tf_name]
            assert "indicators" in tf_data

            indicators_tf = tf_data["indicators"]
            required_keys = ["ema20", "ema50", "rsi", "macd", "signal", "histogram", "volume_avg"]
            for key in required_keys:
                assert key in indicators_tf
                assert isinstance(indicators_tf[key], (float, int))