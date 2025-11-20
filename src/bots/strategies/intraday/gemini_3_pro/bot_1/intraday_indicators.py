"""
Calculador de Indicadores para Estrategia INTRADAY.

Este módulo implementa el cálculo y formateo de indicadores técnicos específicos
para la estrategia INTRADAY, generando los paquetes JSON requeridos:
- Paquete Táctico (M15): 200 velas con indicadores pre-calculados
- Paquete Estratégico (D1): 30 velas con indicadores pre-calculados

Todos los indicadores se pre-calculan correctamente, asegurando que cada vela
tenga su indicador calculado con el histórico necesario.

Autor: Sistema Botrading
Fecha: 2025-11-19
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from src.core.mt5_data_extractor import MT5DataExtractor, Timeframe, OHLCVData
from src.core.indicator_calculator import IndicatorCalculator


@dataclass
class IntradayCandle_M15:
    """Vela M15 con todos los indicadores para paquete táctico."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    ema_20: Optional[float] = None
    ema_200: Optional[float] = None
    vwap: Optional[float] = None
    rsi_14: Optional[float] = None
    atr_14: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None


@dataclass
class IntradayCandle_D1:
    """Vela D1 con todos los indicadores para paquete estratégico."""
    date: str
    close: float
    ema_200: Optional[float] = None
    atr_14: Optional[float] = None
    prev_close: Optional[float] = None
    prev_high: Optional[float] = None
    prev_low: Optional[float] = None


class IntradayIndicatorCalculator:
    """
    Calculador especializado de indicadores para estrategia INTRADAY.
    
    Genera dos paquetes de datos:
    1. PAQUETE TÁCTICO (M15): 200 velas con indicadores
    2. PAQUETE ESTRATÉGICO (D1): 30 velas con indicadores
    
    Garantiza pre-cálculo correcto: para calcular EMA 200 en vela #1,
    se obtienen 200 velas adicionales de histórico.
    """
    
    def __init__(self, data_extractor: MT5DataExtractor):
        """
        Inicializa el calculador de indicadores INTRADAY.
        
        Args:
            data_extractor: Extractor de datos MT5 para obtener históricos
        """
        self.data_extractor = data_extractor
        self.base_calculator = IndicatorCalculator()
    
    def _calculate_bollinger_bands(
        self, 
        prices: pd.Series, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Calcula Bandas de Bollinger.
        
        Args:
            prices: Serie de precios de cierre
            period: Período para SMA (default: 20)
            std_dev: Número de desviaciones estándar (default: 2.0)
        
        Returns:
            Diccionario con 'upper', 'middle', 'lower', 'width'
        """
        # Banda media es SMA
        middle = prices.rolling(window=period).mean()
        
        # Desviación estándar
        std = prices.rolling(window=period).std()
        
        # Bandas superior e inferior
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        # Ancho de bandas
        width = upper - lower
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'width': width
        }
    
    def calculate_tactical_package(
        self, 
        symbol: str, 
        candles_to_return: int = 200
    ) -> List[IntradayCandle_M15]:
        """
        Calcula el PAQUETE TÁCTICO (M15) con pre-cálculo correcto.
        
        Para asegurar que todos los indicadores estén correctamente calculados,
        especialmente EMA 200 que requiere 200 velas de histórico, se obtienen
        más velas del necesario y luego se retornan solo las últimas N.
        
        Args:
            symbol: Símbolo a analizar (ej: "EURUSD")
            candles_to_return: Número de velas a retornar (default: 200)
        
        Returns:
            Lista de IntradayCandle_M15 con indicadores calculados
        
        Raises:
            ValueError: Si no hay suficientes datos históricos
        """
        # Calcular velas totales necesarias
        # Para tener 200 velas con EMA 200 válida, necesitamos:
        # 200 (velas a retornar) + 200 (período EMA) = 400 velas mínimo
        # Agregamos margen de seguridad
        total_candles_needed = candles_to_return + 250  # 450 velas totales
        
        # Obtener datos históricos M15
        ohlcv_data = self.data_extractor.get_ohlcv(
            symbol=symbol,
            timeframe=Timeframe.M15,
            count=total_candles_needed
        )
        
        if ohlcv_data.count < total_candles_needed:
            raise ValueError(
                f"Datos insuficientes para {symbol} M15. "
                f"Se requieren {total_candles_needed}, se obtuvieron {ohlcv_data.count}"
            )
        
        df = ohlcv_data.data
        
        # Calcular todos los indicadores sobre el dataset completo
        ema_20 = self.base_calculator._calculate_ema(df['close'], 20)
        ema_200 = self.base_calculator._calculate_ema(df['close'], 200)
        vwap = self.base_calculator._calculate_vwap(df)
        rsi_14 = self.base_calculator._calculate_rsi(df['close'], 14)
        atr_14 = self.base_calculator._calculate_atr(df, 14)
        
        # Bandas de Bollinger
        bb = self._calculate_bollinger_bands(df['close'], period=20, std_dev=2.0)
        
        # Tomar solo las últimas N velas (con indicadores ya calculados)
        result = []
        start_idx = len(df) - candles_to_return
        
        for i in range(start_idx, len(df)):
            candle = IntradayCandle_M15(
                timestamp=df.index[i].strftime('%Y-%m-%d %H:%M:%S'),
                open=float(df['open'].iloc[i]),
                high=float(df['high'].iloc[i]),
                low=float(df['low'].iloc[i]),
                close=float(df['close'].iloc[i]),
                volume=float(df['volume'].iloc[i]),
                ema_20=float(ema_20.iloc[i]) if not pd.isna(ema_20.iloc[i]) else None,
                ema_200=float(ema_200.iloc[i]) if not pd.isna(ema_200.iloc[i]) else None,
                vwap=float(vwap.iloc[i]) if not pd.isna(vwap.iloc[i]) else None,
                rsi_14=float(rsi_14.iloc[i]) if not pd.isna(rsi_14.iloc[i]) else None,
                atr_14=float(atr_14.iloc[i]) if not pd.isna(atr_14.iloc[i]) else None,
                bb_upper=float(bb['upper'].iloc[i]) if not pd.isna(bb['upper'].iloc[i]) else None,
                bb_lower=float(bb['lower'].iloc[i]) if not pd.isna(bb['lower'].iloc[i]) else None,
                bb_width=float(bb['width'].iloc[i]) if not pd.isna(bb['width'].iloc[i]) else None,
            )
            result.append(candle)
        
        return result
    
    def calculate_strategic_package(
        self, 
        symbol: str, 
        candles_to_return: int = 30
    ) -> List[IntradayCandle_D1]:
        """
        Calcula el PAQUETE ESTRATÉGICO (D1) con pre-cálculo correcto.
        
        Para asegurar que EMA 200 esté correctamente calculada en todas las velas,
        se obtienen velas adicionales de histórico.
        
        Args:
            symbol: Símbolo a analizar (ej: "EURUSD")
            candles_to_return: Número de velas a retornar (default: 30)
        
        Returns:
            Lista de IntradayCandle_D1 con indicadores calculados
        
        Raises:
            ValueError: Si no hay suficientes datos históricos
        """
        # Para 30 velas con EMA 200 válida, necesitamos:
        # 30 (velas a retornar) + 200 (período EMA) = 230 velas mínimo
        # Agregamos margen de seguridad
        total_candles_needed = candles_to_return + 210  # 240 velas totales
        
        # Obtener datos históricos D1
        ohlcv_data = self.data_extractor.get_ohlcv(
            symbol=symbol,
            timeframe=Timeframe.D1,
            count=total_candles_needed
        )
        
        if ohlcv_data.count < total_candles_needed:
            raise ValueError(
                f"Datos insuficientes para {symbol} D1. "
                f"Se requieren {total_candles_needed}, se obtuvieron {ohlcv_data.count}"
            )
        
        df = ohlcv_data.data
        
        # Calcular indicadores sobre el dataset completo
        ema_200 = self.base_calculator._calculate_ema(df['close'], 200)
        atr_14 = self.base_calculator._calculate_atr(df, 14)
        
        # Calcular prev_close, prev_high, prev_low
        prev_close = df['close'].shift(1)
        prev_high = df['high'].shift(1)
        prev_low = df['low'].shift(1)
        
        # Tomar solo las últimas N velas
        result = []
        start_idx = len(df) - candles_to_return
        
        for i in range(start_idx, len(df)):
            candle = IntradayCandle_D1(
                date=df.index[i].strftime('%Y-%m-%d'),
                close=float(df['close'].iloc[i]),
                ema_200=float(ema_200.iloc[i]) if not pd.isna(ema_200.iloc[i]) else None,
                atr_14=float(atr_14.iloc[i]) if not pd.isna(atr_14.iloc[i]) else None,
                prev_close=float(prev_close.iloc[i]) if not pd.isna(prev_close.iloc[i]) else None,
                prev_high=float(prev_high.iloc[i]) if not pd.isna(prev_high.iloc[i]) else None,
                prev_low=float(prev_low.iloc[i]) if not pd.isna(prev_low.iloc[i]) else None,
            )
            result.append(candle)
        
        return result
    
    def get_full_intraday_packages(
        self, 
        symbol: str,
        tactical_candles: int = 200,
        strategic_candles: int = 30
    ) -> Dict[str, List]:
        """
        Obtiene ambos paquetes INTRADAY completos en formato JSON-ready.
        
        Args:
            symbol: Símbolo a analizar
            tactical_candles: Número de velas M15 (default: 200)
            strategic_candles: Número de velas D1 (default: 30)
        
        Returns:
            Diccionario con dos claves:
            - 'tactical_m15': Lista de diccionarios con datos M15
            - 'strategic_d1': Lista de diccionarios con datos D1
        """
        # Calcular paquete táctico
        tactical = self.calculate_tactical_package(symbol, tactical_candles)
        
        # Calcular paquete estratégico
        strategic = self.calculate_strategic_package(symbol, strategic_candles)
        
        # Convertir a diccionarios (JSON-ready)
        return {
            'tactical_m15': [asdict(candle) for candle in tactical],
            'strategic_d1': [asdict(candle) for candle in strategic]
        }
