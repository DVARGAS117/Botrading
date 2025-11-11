"""
MT5DataExtractor - Módulo para extracción de datos OHLCV desde MetaTrader 5.

Este módulo implementa la extracción robusta de datos de velas OHLCV desde MT5,
asegurando que solo se obtengan velas cerradas y manejando múltiples timeframes.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T07 - Extracción de velas cerradas OHLCV por timeframe
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # Para entorno de testing

from src.core.logger import get_bot_logger, LogConfig
import logging


class MT5DataError(Exception):
    """Excepción personalizada para errores de extracción de datos MT5."""
    pass


class Timeframe(Enum):
    """
    Enum para representar timeframes de MT5.
    
    Los valores corresponden a los minutos que representa cada timeframe,
    compatible con las constantes TIMEFRAME de MT5.
    """
    M1 = 1      # 1 minuto
    M5 = 5      # 5 minutos
    M15 = 15    # 15 minutos
    M30 = 30    # 30 minutos
    H1 = 60     # 1 hora
    H4 = 240    # 4 horas
    D1 = 1440   # 1 día
    
    @classmethod
    def from_string(cls, timeframe_str: str) -> 'Timeframe':
        """
        Convierte un string a Timeframe enum.
        
        Args:
            timeframe_str: String del timeframe (ej: "M5", "H1", "D1")
            
        Returns:
            Timeframe: El enum correspondiente
            
        Raises:
            ValueError: Si el string no corresponde a un timeframe válido
        """
        try:
            return cls[timeframe_str.upper()]
        except KeyError:
            raise ValueError(
                f"Timeframe inválido: {timeframe_str}. "
                f"Valores válidos: {', '.join([t.name for t in cls])}"
            )
    
    def to_mt5_timeframe(self) -> int:
        """
        Convierte el Timeframe a la constante de MT5.
        
        Returns:
            int: El valor de timeframe para MT5
        """
        # Mapeo a las constantes TIMEFRAME_* de MT5
        mt5_map = {
            self.M1: 1,      # TIMEFRAME_M1
            self.M5: 5,      # TIMEFRAME_M5
            self.M15: 15,    # TIMEFRAME_M15
            self.M30: 30,    # TIMEFRAME_M30
            self.H1: 16385,  # TIMEFRAME_H1
            self.H4: 16388,  # TIMEFRAME_H4
            self.D1: 16408,  # TIMEFRAME_D1
        }
        return mt5_map.get(self, self.value)


@dataclass
class OHLCVData:
    """
    Clase para representar datos OHLCV extraídos de MT5.
    
    Attributes:
        symbol: Símbolo del instrumento (ej: "EURUSD")
        timeframe: Timeframe de las velas
        data: DataFrame con columnas [time, open, high, low, close, volume]
        count: Número de velas en el dataset
    """
    symbol: str
    timeframe: Timeframe
    data: pd.DataFrame
    count: int
    
    def to_dict(self) -> Dict:
        """
        Convierte OHLCVData a diccionario.
        
        Returns:
            Dict con metadatos y datos
        """
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe.name,
            'count': self.count,
            'data': self.data.to_dict(orient='records')
        }


class MT5DataExtractor:
    """
    Extractor de datos OHLCV desde MetaTrader 5.
    
    Proporciona métodos para extraer velas cerradas de diferentes timeframes,
    validar símbolos y manejar múltiples timeframes simultáneamente.
    
    Example:
        >>> from src.core.mt5_connector import MT5Connector
        >>> from src.core.mt5_data_extractor import MT5DataExtractor, Timeframe
        >>> 
        >>> connector = MT5Connector(broker_config)
        >>> connector.verify_connection()
        >>> 
        >>> extractor = MT5DataExtractor(connector)
        >>> data = extractor.get_ohlcv("EURUSD", Timeframe.M5, count=100)
        >>> print(f"Extraídas {data.count} velas de {data.symbol}")
    """
    
    def __init__(
        self,
        connector,
        enable_cache: bool = False,
        candle_waiter: Optional[object] = None,
        logger: Optional[object] = None
    ):
        """
        Inicializa el MT5DataExtractor.
        
        Args:
            connector: Instancia de MT5Connector con conexión activa
            enable_cache: Si es True, habilita caché de datos (experimental)
            candle_waiter: Instancia opcional de CandleWaiter para integración
            logger: Logger personalizado (usa el default si no se proporciona)
            
        Raises:
            MT5DataError: Si el connector no está conectado
        """
        if not connector.is_connected():
            raise MT5DataError(
                "MT5 no está conectado. Asegúrese de que el connector "
                "esté conectado antes de crear el extractor."
            )
        
        self.connector = connector
        self._mt5 = connector._mt5
        self.enable_cache = enable_cache
        self.candle_waiter = candle_waiter
        
        # Configurar logger
        if logger:
            self.logger = logger
        else:
            # Usar logging básico de Python si no se proporciona logger
            self.logger = logging.getLogger(__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        
        # Caché simple (dict: key = (symbol, timeframe, count))
        self._cache: Dict = {} if enable_cache else None
        
        self.logger.debug("MT5DataExtractor inicializado correctamente")
    
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        exclude_current: bool = False,
        wait_for_close: bool = False
    ) -> OHLCVData:
        """
        Extrae datos OHLCV para un símbolo y timeframe específico.
        
        Args:
            symbol: Símbolo del instrumento (ej: "EURUSD")
            timeframe: Timeframe de las velas
            count: Número de velas a extraer
            exclude_current: Si True, excluye la vela actual (parcial)
            wait_for_close: Si True, espera al cierre de la vela actual
            
        Returns:
            OHLCVData con las velas extraídas
            
        Raises:
            ValueError: Si los parámetros son inválidos
            MT5DataError: Si no se pueden obtener datos de MT5
        """
        # Validaciones
        if not symbol or not symbol.strip():
            raise ValueError("El símbolo es requerido y no puede estar vacío")
        
        if count <= 0:
            raise ValueError("count debe ser mayor a 0")
        
        # Verificar caché
        if self.enable_cache:
            cache_key = (symbol, timeframe, count)
            if cache_key in self._cache:
                self.logger.debug(f"Retornando datos del caché para {symbol} {timeframe.name}")
                return self._cache[cache_key]
        
        # Esperar cierre de vela si se solicita
        if wait_for_close and self.candle_waiter:
            self.logger.debug(f"Esperando cierre de vela {timeframe.name} para {symbol}")
            self.candle_waiter.wait_for_candle_close(timeframe)
        
        # Extraer datos de MT5
        try:
            self.logger.info(
                f"Extrayendo {count} velas de {symbol} en timeframe {timeframe.name}"
            )
            
            # Si exclude_current, pedir una vela más y luego removerla
            request_count = count + 1 if exclude_current else count
            
            rates = self._mt5.copy_rates_from_pos(
                symbol,
                timeframe.to_mt5_timeframe(),
                0,  # Desde la posición actual
                request_count
            )
            
            if rates is None:
                error_code = self._mt5.last_error() if hasattr(self._mt5, 'last_error') else "desconocido"
                raise MT5DataError(
                    f"No se pudieron obtener datos para {symbol} {timeframe.name}. "
                    f"Error MT5: {error_code}"
                )
            
            if len(rates) == 0:
                raise MT5DataError(
                    f"No se obtuvieron datos para {symbol} {timeframe.name}. "
                    "Verifique que el símbolo sea válido y tenga datos disponibles."
                )
            
            # Convertir a DataFrame
            df = self._convert_to_dataframe(rates)
            
            # Excluir vela actual si se solicita
            if exclude_current and len(df) > count:
                df = df.iloc[:-1]  # Remover última fila (vela actual)
            
            # Crear OHLCVData
            ohlcv_data = OHLCVData(
                symbol=symbol,
                timeframe=timeframe,
                data=df.head(count),  # Asegurar que no exceda count
                count=min(len(df), count)
            )
            
            # Guardar en caché si está habilitado
            if self.enable_cache:
                cache_key = (symbol, timeframe, count)
                self._cache[cache_key] = ohlcv_data
            
            self.logger.info(
                f"Extracción exitosa: {ohlcv_data.count} velas de {symbol} {timeframe.name}"
            )
            
            return ohlcv_data
            
        except MT5DataError:
            raise
        except Exception as e:
            self.logger.error(f"Error inesperado al extraer datos OHLCV: {e}")
            raise MT5DataError(f"Error al extraer datos: {e}") from e
    
    def get_ohlcv_multi_timeframe(
        self,
        symbol: str,
        timeframes: List[Timeframe],
        count: int,
        exclude_current: bool = False
    ) -> Dict[Timeframe, OHLCVData]:
        """
        Extrae datos OHLCV para múltiples timeframes.
        
        Args:
            symbol: Símbolo del instrumento
            timeframes: Lista de timeframes a extraer
            count: Número de velas a extraer por timeframe
            exclude_current: Si True, excluye la vela actual
            
        Returns:
            Dict mapeando Timeframe a OHLCVData
            
        Raises:
            ValueError: Si los parámetros son inválidos
            MT5DataError: Si falla la extracción
        """
        if not timeframes:
            raise ValueError("La lista de timeframes no puede estar vacía")
        
        self.logger.info(
            f"Extrayendo datos de {symbol} para {len(timeframes)} timeframes"
        )
        
        result = {}
        
        for tf in timeframes:
            try:
                ohlcv_data = self.get_ohlcv(
                    symbol=symbol,
                    timeframe=tf,
                    count=count,
                    exclude_current=exclude_current
                )
                result[tf] = ohlcv_data
            except Exception as e:
                self.logger.error(f"Error al extraer {symbol} {tf.name}: {e}")
                # Continuar con los demás timeframes
                continue
        
        if not result:
            raise MT5DataError(
                f"No se pudieron extraer datos para ningún timeframe de {symbol}"
            )
        
        self.logger.info(
            f"Extracción multi-timeframe completada: "
            f"{len(result)}/{len(timeframes)} timeframes exitosos"
        )
        
        return result
    
    def get_ohlcv_range(
        self,
        symbol: str,
        timeframe: Timeframe,
        start_date: datetime,
        end_date: datetime
    ) -> OHLCVData:
        """
        Extrae datos OHLCV para un rango de fechas específico.
        
        Args:
            symbol: Símbolo del instrumento
            timeframe: Timeframe de las velas
            start_date: Fecha de inicio del rango
            end_date: Fecha de fin del rango
            
        Returns:
            OHLCVData con las velas del rango solicitado
            
        Raises:
            ValueError: Si las fechas son inválidas
            MT5DataError: Si no se pueden obtener datos
        """
        if start_date >= end_date:
            raise ValueError("start_date debe ser anterior a end_date")
        
        self.logger.info(
            f"Extrayendo {symbol} {timeframe.name} desde {start_date} hasta {end_date}"
        )
        
        try:
            rates = self._mt5.copy_rates_range(
                symbol,
                timeframe.to_mt5_timeframe(),
                start_date,
                end_date
            )
            
            if rates is None or len(rates) == 0:
                raise MT5DataError(
                    f"No se obtuvieron datos para {symbol} en el rango especificado"
                )
            
            df = self._convert_to_dataframe(rates)
            
            ohlcv_data = OHLCVData(
                symbol=symbol,
                timeframe=timeframe,
                data=df,
                count=len(df)
            )
            
            self.logger.info(
                f"Extracción por rango exitosa: {ohlcv_data.count} velas"
            )
            
            return ohlcv_data
            
        except MT5DataError:
            raise
        except Exception as e:
            self.logger.error(f"Error al extraer datos por rango: {e}")
            raise MT5DataError(f"Error en extracción por rango: {e}") from e
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Valida si un símbolo existe en MT5.
        
        Args:
            symbol: Símbolo a validar
            
        Returns:
            True si el símbolo existe, False en caso contrario
        """
        try:
            symbol_info = self._mt5.symbol_info(symbol)
            return symbol_info is not None
        except Exception as e:
            self.logger.error(f"Error al validar símbolo {symbol}: {e}")
            return False
    
    def _convert_to_dataframe(self, rates) -> pd.DataFrame:
        """
        Convierte datos de MT5 (numpy structured array) a pandas DataFrame.
        
        Args:
            rates: Datos en formato MT5
            
        Returns:
            DataFrame con columnas [time, open, high, low, close, volume]
        """
        # Convertir a DataFrame
        # Los datos de MT5 vienen como structured array con nombres de campos
        df = pd.DataFrame(rates)
        
        # Si el DataFrame tiene índices numéricos, significa que rates era una lista
        # En ese caso, asignar nombres de columnas manualmente
        if df.columns.dtype == 'int64':
            # Formato MT5: (time, open, high, low, close, tick_volume, spread, real_volume)
            df.columns = ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
        
        # Convertir timestamp a datetime
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Seleccionar solo las columnas OHLCV
        columns_to_keep = ['time', 'open', 'high', 'low', 'close', 'tick_volume']
        
        # Renombrar tick_volume a volume
        df = df[columns_to_keep].copy()
        df.rename(columns={'tick_volume': 'volume'}, inplace=True)
        
        return df
    
    def clear_cache(self):
        """Limpia el caché de datos si está habilitado."""
        if self._cache is not None:
            self._cache.clear()
            self.logger.debug("Caché de datos limpiado")
