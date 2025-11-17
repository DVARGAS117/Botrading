"""
IndicatorCalculator - Cálculo de indicadores técnicos por timeframe.

Este módulo implementa el cálculo de indicadores técnicos (EMA, RSI, MACD, volumen)
para múltiples timeframes y el formateo consistente para envío a IA.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T23 - Cálculo y formato de indicadores por timeframe
"""
from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from src.core.mt5_data_extractor import OHLCVData, Timeframe


@dataclass
class IndicatorData:
    """
    Clase para representar indicadores calculados para un timeframe específico.

    Attributes:
        symbol: Símbolo del instrumento
        timeframe: Timeframe de los indicadores
        ema9: EMA de 9 períodos (timing micro)
        ema20: EMA de 20 períodos
        ema50: EMA de 50 períodos
        rsi: RSI de 14 períodos
        macd: Línea MACD
        signal: Línea de señal MACD
        histogram: Histograma MACD
        volume_avg: Promedio de volumen de 20 períodos
        
        # Indicadores VWAP (Metodología VWAP Intradía)
        vwap: VWAP de sesión
        vwap_slope: Pendiente de VWAP (derivada)
        vwap_slope_description: Descripción de pendiente (ascendente/descendente/plana)
        vwap_upper_1: Banda superior +1σ
        vwap_lower_1: Banda inferior -1σ
        vwap_upper_2: Banda superior +2σ
        vwap_lower_2: Banda inferior -2σ
    """
    symbol: str
    timeframe: Timeframe
    ema9: Optional[float] = None
    ema20: Optional[float] = None
    ema50: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None
    volume_avg: Optional[float] = None
    
    # VWAP Indicators
    vwap: Optional[float] = None
    vwap_slope: Optional[float] = None
    vwap_slope_description: Optional[str] = None
    vwap_upper_1: Optional[float] = None
    vwap_lower_1: Optional[float] = None
    vwap_upper_2: Optional[float] = None
    vwap_lower_2: Optional[float] = None


@dataclass
class TimeframeIndicators:
    """
    Clase para representar indicadores calculados para múltiples timeframes.

    Attributes:
        symbol: Símbolo del instrumento
        indicators: Diccionario mapeando Timeframe a IndicatorData
    """
    symbol: str
    indicators: Dict[Timeframe, IndicatorData]


class IndicatorCalculator:
    """
    Calculador de indicadores técnicos para múltiples timeframes.

    Proporciona métodos para calcular EMA, RSI, MACD y volumen promedio,
    y formatear los resultados en JSON consistente para IA.

    Example:
        >>> from src.core.mt5_data_extractor import MT5DataExtractor, Timeframe
        >>> from src.core.indicator_calculator import IndicatorCalculator
        >>>
        >>> extractor = MT5DataExtractor(connector)
        >>> calculator = IndicatorCalculator()
        >>>
        >>> # Calcular para múltiples timeframes
        >>> timeframes_data = extractor.get_ohlcv_multi_timeframe(
        ...     "EURUSD", [Timeframe.M5, Timeframe.M15, Timeframe.H1], 100
        ... )
        >>> result = calculator.calculate_indicators_multi_timeframe("EURUSD", timeframes_data)
        >>> json_data = calculator.format_indicators_json(result)
    """

    def __init__(self):
        """Inicializa el IndicatorCalculator."""
        pass

    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calcula la EMA (Exponential Moving Average).

        Args:
            prices: Serie de precios de cierre
            period: Período para el cálculo de EMA

        Returns:
            Serie con los valores de EMA
        """
        return prices.ewm(span=period, adjust=False).mean()

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcula el RSI (Relative Strength Index).

        Args:
            prices: Serie de precios de cierre
            period: Período para el cálculo de RSI (default: 14)

        Returns:
            Serie con los valores de RSI (0-100)
        """
        delta = prices.diff()
        gain = (delta.where(delta.gt(0), 0)).rolling(window=period).mean()
        loss = (-delta.where(delta.lt(0), 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_macd(self, prices: pd.Series,
                       fast_period: int = 12,
                       slow_period: int = 26,
                       signal_period: int = 9) -> Dict[str, pd.Series]:
        """
        Calcula el MACD (Moving Average Convergence Divergence).

        Args:
            prices: Serie de precios de cierre
            fast_period: Período para EMA rápida (default: 12)
            slow_period: Período para EMA lenta (default: 26)
            signal_period: Período para línea de señal (default: 9)

        Returns:
            Diccionario con 'macd', 'signal', 'histogram'
        """
        fast_ema = self._calculate_ema(prices, fast_period)
        slow_ema = self._calculate_ema(prices, slow_period)

        macd = fast_ema - slow_ema
        signal = self._calculate_ema(macd, signal_period)
        histogram = macd - signal

        return {
            'macd': macd,
            'signal': signal,
            'histogram': histogram
        }

    def _calculate_vwap(self, data: pd.DataFrame) -> pd.Series:
        """
        Calcula VWAP (Volume Weighted Average Price) acumulativo.
        
        VWAP = Σ(Precio Típico × Volumen) / Σ(Volumen)
        Precio Típico = (High + Low + Close) / 3
        
        Args:
            data: DataFrame con columnas 'high', 'low', 'close', 'volume'
        
        Returns:
            Serie con valores de VWAP acumulativos
        """
        # Calcular precio típico
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        
        # VWAP acumulativo
        cumulative_tpv = (typical_price * data['volume']).cumsum()
        cumulative_volume = data['volume'].cumsum()
        
        # Evitar división por cero
        vwap = cumulative_tpv / cumulative_volume.replace(0, np.nan)
        
        return vwap
    
    def _calculate_vwap_slope(self, vwap_series: pd.Series, lookback: int = 10) -> tuple:
        """
        Calcula la pendiente de VWAP (derivada simple).
        
        Args:
            vwap_series: Serie de valores VWAP
            lookback: Número de períodos para calcular pendiente
        
        Returns:
            tuple: (slope: float, description: str)
                description puede ser: "ascendente", "descendente", "plana", "insuficiente"
        """
        if len(vwap_series) < lookback:
            return 0.0, "insuficiente"
        
        # Tomar últimos N valores
        recent_vwap = vwap_series.dropna().tail(lookback)
        
        if len(recent_vwap) < 2:
            return 0.0, "insuficiente"
        
        # Calcular pendiente: (último - primero) / períodos
        slope = (recent_vwap.iloc[-1] - recent_vwap.iloc[0]) / len(recent_vwap)
        
        # Umbral para EURUSD (ajustable según activo)
        # 0.00005 = 0.5 pips
        threshold = 0.00005
        
        if slope > threshold:
            return slope, "ascendente"
        elif slope < -threshold:
            return slope, "descendente"
        else:
            return slope, "plana"
    
    def _calculate_vwap_bands(self, data: pd.DataFrame, vwap: pd.Series) -> Dict[str, pd.Series]:
        """
        Calcula bandas de VWAP (±1σ, ±2σ) usando desviación estándar ponderada por volumen.
        
        Args:
            data: DataFrame con columnas 'high', 'low', 'close', 'volume'
            vwap: Serie de VWAP ya calculada
        
        Returns:
            Diccionario con 'upper_1', 'lower_1', 'upper_2', 'lower_2'
        """
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        
        # Calcular varianza ponderada acumulativa
        squared_diff = (typical_price - vwap) ** 2
        cumulative_var = (squared_diff * data['volume']).cumsum() / data['volume'].cumsum()
        
        # Desviación estándar
        std_dev = np.sqrt(cumulative_var)
        
        # Bandas
        return {
            'upper_1': vwap + std_dev,
            'lower_1': vwap - std_dev,
            'upper_2': vwap + 2 * std_dev,
            'lower_2': vwap - 2 * std_dev
        }
    
    def _calculate_volume_average(self, volume: pd.Series, period: int = 20) -> pd.Series:
        """
        Calcula el promedio móvil de volumen.

        Args:
            volume: Serie de volumen
            period: Período para el promedio (default: 20)

        Returns:
            Serie con el promedio de volumen
        """
        return volume.rolling(window=period).mean()

    def calculate_indicators_for_timeframe(self, ohlcv_data: OHLCVData) -> IndicatorData:
        """
        Calcula todos los indicadores para un timeframe específico.

        Args:
            ohlcv_data: Datos OHLCV para el timeframe

        Returns:
            IndicatorData con todos los indicadores calculados

        Raises:
            ValueError: Si los datos son insuficientes
        """
        if ohlcv_data.count < 50:  # Mínimo para EMA50
            raise ValueError(
                f"Datos insuficientes para {ohlcv_data.symbol} {ohlcv_data.timeframe.name}. "
                f"Se requieren al menos 50 velas, se tienen {ohlcv_data.count}"
            )

        # Calcular indicadores estándar
        ema9 = self._calculate_ema(ohlcv_data.data['close'], 9)
        ema20 = self._calculate_ema(ohlcv_data.data['close'], 20)
        ema50 = self._calculate_ema(ohlcv_data.data['close'], 50)
        rsi = self._calculate_rsi(ohlcv_data.data['close'], 14)
        macd_data = self._calculate_macd(ohlcv_data.data['close'])
        volume_avg = self._calculate_volume_average(ohlcv_data.data['volume'], 20)
        
        # Calcular indicadores VWAP
        vwap = self._calculate_vwap(ohlcv_data.data)
        vwap_slope, vwap_slope_desc = self._calculate_vwap_slope(vwap, lookback=10)
        vwap_bands = self._calculate_vwap_bands(ohlcv_data.data, vwap)

        # Obtener los últimos valores válidos
        latest_ema9 = ema9.dropna().iloc[-1] if not ema9.dropna().empty else None
        latest_ema20 = ema20.dropna().iloc[-1] if not ema20.dropna().empty else None
        latest_ema50 = ema50.dropna().iloc[-1] if not ema50.dropna().empty else None
        latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else None
        latest_macd = macd_data['macd'].dropna().iloc[-1] if not macd_data['macd'].dropna().empty else None
        latest_signal = macd_data['signal'].dropna().iloc[-1] if not macd_data['signal'].dropna().empty else None
        latest_histogram = macd_data['histogram'].dropna().iloc[-1] if not macd_data['histogram'].dropna().empty else None
        latest_volume_avg = volume_avg.dropna().iloc[-1] if not volume_avg.dropna().empty else None
        
        # VWAP últimos valores
        latest_vwap = vwap.dropna().iloc[-1] if not vwap.dropna().empty else None
        latest_vwap_upper_1 = vwap_bands['upper_1'].dropna().iloc[-1] if not vwap_bands['upper_1'].dropna().empty else None
        latest_vwap_lower_1 = vwap_bands['lower_1'].dropna().iloc[-1] if not vwap_bands['lower_1'].dropna().empty else None
        latest_vwap_upper_2 = vwap_bands['upper_2'].dropna().iloc[-1] if not vwap_bands['upper_2'].dropna().empty else None
        latest_vwap_lower_2 = vwap_bands['lower_2'].dropna().iloc[-1] if not vwap_bands['lower_2'].dropna().empty else None

        return IndicatorData(
            symbol=ohlcv_data.symbol,
            timeframe=ohlcv_data.timeframe,
            ema9=latest_ema9,
            ema20=latest_ema20,
            ema50=latest_ema50,
            rsi=latest_rsi,
            macd=latest_macd,
            signal=latest_signal,
            histogram=latest_histogram,
            volume_avg=latest_volume_avg,
            vwap=latest_vwap,
            vwap_slope=vwap_slope,
            vwap_slope_description=vwap_slope_desc,
            vwap_upper_1=latest_vwap_upper_1,
            vwap_lower_1=latest_vwap_lower_1,
            vwap_upper_2=latest_vwap_upper_2,
            vwap_lower_2=latest_vwap_lower_2
        )

    def calculate_indicators_multi_timeframe(self,
                                           symbol: str,
                                           timeframes_data: Dict[Timeframe, OHLCVData]) -> TimeframeIndicators:
        """
        Calcula indicadores para múltiples timeframes.

        Args:
            symbol: Símbolo del instrumento
            timeframes_data: Diccionario mapeando Timeframe a OHLCVData

        Returns:
            TimeframeIndicators con indicadores para todos los timeframes

        Raises:
            ValueError: Si no se proporcionan timeframes
        """
        if not timeframes_data:
            raise ValueError("No se proporcionaron datos de timeframes")

        indicators = {}

        for timeframe, ohlcv_data in timeframes_data.items():
            try:
                indicators[timeframe] = self.calculate_indicators_for_timeframe(ohlcv_data)
            except Exception as e:
                # Log error pero continuar con otros timeframes
                print(f"Error calculando indicadores para {timeframe.name}: {e}")
                continue

        if not indicators:
            raise ValueError(f"No se pudieron calcular indicadores para ningún timeframe de {symbol}")

        return TimeframeIndicators(
            symbol=symbol,
            indicators=indicators
        )

    def format_indicators_json(self, indicators: TimeframeIndicators) -> Dict:
        """
        Formatea los indicadores en JSON consistente para IA.

        Args:
            indicators: TimeframeIndicators a formatear

        Returns:
            Diccionario JSON con estructura consistente
        """
        timeframes_data = {}

        for timeframe, indicator_data in indicators.indicators.items():
            timeframes_data[timeframe.name] = {
                "indicators": {
                    "ema9": indicator_data.ema9,
                    "ema20": indicator_data.ema20,
                    "ema50": indicator_data.ema50,
                    "rsi": indicator_data.rsi,
                    "macd": indicator_data.macd,
                    "signal": indicator_data.signal,
                    "histogram": indicator_data.histogram,
                    "volume_avg": indicator_data.volume_avg,
                    "vwap": indicator_data.vwap,
                    "vwap_slope": indicator_data.vwap_slope,
                    "vwap_slope_description": indicator_data.vwap_slope_description,
                    "vwap_bands": {
                        "upper_1": indicator_data.vwap_upper_1,
                        "lower_1": indicator_data.vwap_lower_1,
                        "upper_2": indicator_data.vwap_upper_2,
                        "lower_2": indicator_data.vwap_lower_2
                    }
                }
            }

        return {
            "symbol": indicators.symbol,
            "timestamp": datetime.now().isoformat(),
            "timeframes": timeframes_data
        }