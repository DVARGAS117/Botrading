"""
MockMarketDataExtractor - Generador de datos OHLCV sintéticos para desarrollo

Permite ejecutar bots sin dependencia de MetaTrader5 generando series OHLCV
coherentes para pruebas locales y validación de integración con Vertex.

Activación: establecer variable de entorno `MOCK_MARKET_DATA=1`.
"""
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import numpy as np

from src.core.mt5_data_extractor import OHLCVData, Timeframe


class MockMarketDataExtractor:
    def __init__(self, seed: Optional[int] = 42):
        self._rng = np.random.default_rng(seed)

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        exclude_current: bool = False,
        wait_for_close: bool = False,
    ) -> OHLCVData:
        if count < 50:
            count = 50

        # Determinar delta de tiempo por timeframe
        minutes = timeframe.value
        end_time = datetime.utcnow()
        times = [end_time - timedelta(minutes=minutes * i) for i in range(count)][::-1]

        # Generar precios con random walk alrededor de 1.0900
        base = 1.0900
        steps = self._rng.normal(0, 0.0003, size=count).cumsum()
        close = base + steps
        # high/low a partir de close con pequeñas variaciones
        spread = np.abs(self._rng.normal(0.0005, 0.0002, size=count))
        high = close + spread / 2
        low = close - spread / 2
        open_prices = np.concatenate(([close[0]], close[:-1]))
        volume = np.abs(self._rng.normal(1000, 300, size=count)).astype(int)

        df = pd.DataFrame(
            {
                "time": times,
                "open": open_prices,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )

        return OHLCVData(symbol=symbol, timeframe=timeframe, data=df, count=len(df))
