"""
Tests unitarios para el MT5DataExtractor.

Este módulo implementa tests siguiendo TDD para el Ticket T07: Extracción
de velas cerradas OHLCV por timeframe, asegurando que los datos de mercado
se extraigan correctamente sin incluir velas parciales.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T07 - Extracción de velas cerradas OHLCV por timeframe
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd

# Importar el módulo a testear (aún no existe, pero lo crearemos)
from src.core.mt5_data_extractor import (
    MT5DataExtractor,
    MT5DataError,
    OHLCVData,
    Timeframe
)


class TestTimeframe:
    """Tests para el enum Timeframe"""
    
    def test_timeframe_enum_values(self):
        """
        Dado que se definen timeframes soportados
        Cuando se accede a los valores del enum
        Entonces deben corresponder a los valores de MT5
        """
        assert Timeframe.M1.value == 1
        assert Timeframe.M5.value == 5
        assert Timeframe.M15.value == 15
        assert Timeframe.M30.value == 30
        assert Timeframe.H1.value == 60  # 1 hora = 60 minutos
        assert Timeframe.H4.value == 240  # 4 horas = 240 minutos
        assert Timeframe.D1.value == 1440  # 1 día = 1440 minutos
    
    def test_timeframe_from_string(self):
        """
        Dado un string de timeframe
        Cuando se convierte a enum
        Entonces debe retornar el Timeframe correcto
        """
        assert Timeframe.from_string("M1") == Timeframe.M1
        assert Timeframe.from_string("M5") == Timeframe.M5
        assert Timeframe.from_string("H1") == Timeframe.H1
        assert Timeframe.from_string("D1") == Timeframe.D1
    
    def test_timeframe_from_string_case_insensitive(self):
        """
        Dado un string de timeframe en minúsculas
        Cuando se convierte a enum
        Entonces debe ser case-insensitive
        """
        assert Timeframe.from_string("m1") == Timeframe.M1
        assert Timeframe.from_string("h1") == Timeframe.H1
    
    def test_timeframe_from_string_invalid_raises_error(self):
        """
        Dado un string inválido de timeframe
        Cuando se intenta convertir a enum
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="Timeframe inválido"):
            Timeframe.from_string("INVALID")


class TestOHLCVData:
    """Tests para la clase OHLCVData"""
    
    def test_ohlcv_data_initialization(self):
        """
        Dado que se crea un OHLCVData con datos válidos
        Cuando se inicializa
        Entonces debe contener todos los atributos requeridos
        """
        data = OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=pd.DataFrame({
                'time': [datetime.now()],
                'open': [1.1000],
                'high': [1.1010],
                'low': [1.0990],
                'close': [1.1005],
                'volume': [1000]
            }),
            count=1
        )
        
        assert data.symbol == "EURUSD"
        assert data.timeframe == Timeframe.M5
        assert len(data.data) == 1
        assert data.count == 1
    
    def test_ohlcv_data_to_dict(self):
        """
        Dado un OHLCVData
        Cuando se convierte a diccionario
        Entonces debe incluir metadatos y datos
        """
        df = pd.DataFrame({
            'time': [datetime(2025, 11, 11, 10, 0)],
            'open': [1.1000],
            'high': [1.1010],
            'low': [1.0990],
            'close': [1.1005],
            'volume': [1000]
        })
        
        data = OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=df,
            count=1
        )
        
        result = data.to_dict()
        
        assert result['symbol'] == "EURUSD"
        assert result['timeframe'] == "M5"
        assert result['count'] == 1
        assert 'data' in result


class TestMT5DataExtractor:
    """Tests para el MT5DataExtractor"""
    
    @pytest.fixture
    def mock_connector(self):
        """Fixture con mock del MT5Connector"""
        connector = Mock()
        connector.is_connected.return_value = True
        connector._mt5 = Mock()
        return connector
    
    @pytest.fixture
    def extractor(self, mock_connector):
        """Fixture con MT5DataExtractor configurado"""
        return MT5DataExtractor(mock_connector)
    
    # ==================== TESTS DE INICIALIZACIÓN ====================
    
    def test_extractor_initialization(self, mock_connector):
        """
        Dado un MT5Connector válido
        Cuando se crea un MT5DataExtractor
        Entonces se inicializa correctamente
        """
        extractor = MT5DataExtractor(mock_connector)
        
        assert extractor.connector == mock_connector
        assert extractor._mt5 is not None
    
    def test_extractor_initialization_requires_connection(self):
        """
        Dado un connector sin conexión activa
        Cuando se intenta crear un extractor
        Entonces debe lanzar MT5DataError
        """
        connector = Mock()
        connector.is_connected.return_value = False
        
        with pytest.raises(MT5DataError, match="MT5 no está conectado"):
            MT5DataExtractor(connector)
    
    # ==================== TESTS DE EXTRACCIÓN BÁSICA ====================
    
    def test_get_ohlcv_returns_data(self, extractor, mock_connector):
        """
        Dado que MT5 tiene datos disponibles
        Cuando se solicita OHLCV para un símbolo y timeframe
        Entonces debe retornar OHLCVData con velas cerradas
        """
        # Mock de datos de MT5
        mock_rates = [
            (datetime(2025, 11, 11, 10, 0).timestamp(), 1.1000, 1.1010, 1.0990, 1.1005, 0, 1000, 0),
            (datetime(2025, 11, 11, 10, 5).timestamp(), 1.1005, 1.1015, 1.0995, 1.1010, 0, 1100, 0),
        ]
        
        mock_connector._mt5.copy_rates_from_pos.return_value = mock_rates
        
        result = extractor.get_ohlcv(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            count=2
        )
        
        assert isinstance(result, OHLCVData)
        assert result.symbol == "EURUSD"
        assert result.timeframe == Timeframe.M5
        assert result.count == 2
        assert len(result.data) == 2
    
    def test_get_ohlcv_validates_symbol(self, extractor):
        """
        Dado un símbolo vacío
        Cuando se solicita OHLCV
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="El símbolo es requerido"):
            extractor.get_ohlcv(
                symbol="",
                timeframe=Timeframe.M5,
                count=10
            )
    
    def test_get_ohlcv_validates_count(self, extractor):
        """
        Dado un count inválido (menor a 1)
        Cuando se solicita OHLCV
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="count debe ser mayor a 0"):
            extractor.get_ohlcv(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                count=0
            )
    
    def test_get_ohlcv_no_data_raises_error(self, extractor, mock_connector):
        """
        Dado que MT5 no retorna datos (None)
        Cuando se solicita OHLCV
        Entonces debe lanzar MT5DataError
        """
        mock_connector._mt5.copy_rates_from_pos.return_value = None
        
        with pytest.raises(MT5DataError, match="No se pudieron obtener datos"):
            extractor.get_ohlcv(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                count=10
            )
    
    def test_get_ohlcv_empty_data_raises_error(self, extractor, mock_connector):
        """
        Dado que MT5 retorna array vacío
        Cuando se solicita OHLCV
        Entonces debe lanzar MT5DataError
        """
        mock_connector._mt5.copy_rates_from_pos.return_value = []
        
        with pytest.raises(MT5DataError, match="No se obtuvieron datos"):
            extractor.get_ohlcv(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                count=10
            )
    
    # ==================== TESTS DE VELAS CERRADAS ====================
    
    def test_get_ohlcv_only_closed_candles(self, extractor, mock_connector):
        """
        Dado que se solicitan velas cerradas
        Cuando se extraen datos
        Entonces debe excluir la vela actual (parcial)
        """
        # Simular datos con vela actual
        now = datetime.now()
        mock_rates = [
            ((now - timedelta(minutes=10)).timestamp(), 1.1000, 1.1010, 1.0990, 1.1005, 0, 1000, 0),
            ((now - timedelta(minutes=5)).timestamp(), 1.1005, 1.1015, 1.0995, 1.1010, 0, 1100, 0),
            (now.timestamp(), 1.1010, 1.1020, 1.1000, 1.1015, 0, 1200, 0),  # Vela parcial
        ]
        
        mock_connector._mt5.copy_rates_from_pos.return_value = mock_rates
        
        result = extractor.get_ohlcv(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            count=2,
            exclude_current=True
        )
        
        # Debe retornar solo 2 velas cerradas, sin la actual
        assert result.count == 2
    
    # ==================== TESTS DE TIMEFRAMES MÚLTIPLES ====================
    
    def test_get_ohlcv_multiple_timeframes(self, extractor, mock_connector):
        """
        Dado que se solicitan datos de múltiples timeframes
        Cuando se usa get_ohlcv_multi_timeframe
        Entonces debe retornar datos para cada timeframe
        """
        mock_rates_m5 = [
            (datetime(2025, 11, 11, 10, 0).timestamp(), 1.1000, 1.1010, 1.0990, 1.1005, 0, 1000, 0),
        ]
        mock_rates_m15 = [
            (datetime(2025, 11, 11, 10, 0).timestamp(), 1.1000, 1.1015, 1.0985, 1.1010, 0, 3000, 0),
        ]
        mock_rates_h1 = [
            (datetime(2025, 11, 11, 10, 0).timestamp(), 1.1000, 1.1025, 1.0975, 1.1020, 0, 12000, 0),
        ]
        
        def side_effect(symbol, timeframe, position, count):
            # timeframe viene como el valor retornado por to_mt5_timeframe()
            if timeframe == Timeframe.M5.to_mt5_timeframe():
                return mock_rates_m5
            elif timeframe == Timeframe.M15.to_mt5_timeframe():
                return mock_rates_m15
            elif timeframe == Timeframe.H1.to_mt5_timeframe():
                return mock_rates_h1
            return None
        
        mock_connector._mt5.copy_rates_from_pos.side_effect = side_effect
        
        result = extractor.get_ohlcv_multi_timeframe(
            symbol="EURUSD",
            timeframes=[Timeframe.M5, Timeframe.M15, Timeframe.H1],
            count=1
        )
        
        assert len(result) == 3
        assert Timeframe.M5 in result
        assert Timeframe.M15 in result
        assert Timeframe.H1 in result
    
    # ==================== TESTS DE CONVERSIÓN DE DATOS ====================
    
    def test_convert_mt5_data_to_dataframe(self, extractor):
        """
        Dado datos en formato MT5 (numpy structured array)
        Cuando se convierten a DataFrame
        Entonces debe tener las columnas correctas
        """
        mock_rates = [
            (datetime(2025, 11, 11, 10, 0).timestamp(), 1.1000, 1.1010, 1.0990, 1.1005, 0, 1000, 0),
        ]
        
        df = extractor._convert_to_dataframe(mock_rates)
        
        assert 'time' in df.columns
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
        assert len(df) == 1
    
    def test_dataframe_time_column_is_datetime(self, extractor):
        """
        Dado datos convertidos a DataFrame
        Cuando se verifica la columna time
        Entonces debe ser de tipo datetime
        """
        mock_rates = [
            (datetime(2025, 11, 11, 10, 0).timestamp(), 1.1000, 1.1010, 1.0990, 1.1005, 0, 1000, 0),
        ]
        
        df = extractor._convert_to_dataframe(mock_rates)
        
        assert pd.api.types.is_datetime64_any_dtype(df['time'])
    
    # ==================== TESTS DE VALIDACIÓN DE SÍMBOLO ====================
    
    def test_validate_symbol_exists(self, extractor, mock_connector):
        """
        Dado un símbolo que existe en MT5
        Cuando se valida
        Entonces debe retornar True
        """
        mock_connector._mt5.symbol_info.return_value = Mock(name="EURUSD")
        
        result = extractor.validate_symbol("EURUSD")
        
        assert result is True
    
    def test_validate_symbol_not_exists(self, extractor, mock_connector):
        """
        Dado un símbolo que no existe en MT5
        Cuando se valida
        Entonces debe retornar False
        """
        mock_connector._mt5.symbol_info.return_value = None
        
        result = extractor.validate_symbol("INVALID")
        
        assert result is False
    
    # ==================== TESTS DE EXTRACCIÓN POR RANGO DE FECHAS ====================
    
    def test_get_ohlcv_date_range(self, extractor, mock_connector):
        """
        Dado un rango de fechas específico
        Cuando se solicitan datos por rango
        Entonces debe retornar datos del rango solicitado
        """
        start_date = datetime(2025, 11, 1, 0, 0)
        end_date = datetime(2025, 11, 10, 23, 59)
        
        mock_rates = [
            (datetime(2025, 11, 5, 10, 0).timestamp(), 1.1000, 1.1010, 1.0990, 1.1005, 0, 1000, 0),
        ]
        
        mock_connector._mt5.copy_rates_range.return_value = mock_rates
        
        result = extractor.get_ohlcv_range(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            start_date=start_date,
            end_date=end_date
        )
        
        assert isinstance(result, OHLCVData)
        assert result.count == 1
        
        mock_connector._mt5.copy_rates_range.assert_called_once()
    
    # ==================== TESTS DE LOGGING ====================
    
    def test_extraction_logs_on_success(self, extractor, mock_connector):
        """
        Dado que la extracción es exitosa
        Cuando se extraen datos
        Entonces debe registrar logs informativos
        """
        mock_logger = Mock()
        extractor.logger = mock_logger
        
        mock_rates = [
            (datetime(2025, 11, 11, 10, 0).timestamp(), 1.1000, 1.1010, 1.0990, 1.1005, 0, 1000, 0),
        ]
        mock_connector._mt5.copy_rates_from_pos.return_value = mock_rates
        
        extractor.get_ohlcv(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            count=1
        )
        
        assert mock_logger.info.called or mock_logger.debug.called
    
    def test_extraction_logs_on_error(self, extractor, mock_connector):
        """
        Dado que ocurre un error inesperado (no MT5DataError)
        Cuando se intenta extraer datos
        Entonces debe registrar logs de error
        """
        mock_logger = Mock()
        mock_logger.info = Mock()
        mock_logger.error = Mock()
        extractor.logger = mock_logger
        
        # Simular un error inesperado (no MT5DataError) al acceder a los datos
        mock_connector._mt5.copy_rates_from_pos.side_effect = ValueError("Error inesperado")
        
        with pytest.raises(MT5DataError):
            extractor.get_ohlcv(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                count=1
            )
        
        # Verificar que se llamó info (al intentar extraer) y error (al fallar)
        assert mock_logger.info.called
        assert mock_logger.error.called
    
    # ==================== TESTS DE CACHÉ (OPCIONAL) ====================
    
    def test_cache_enabled_returns_cached_data(self, extractor, mock_connector):
        """
        Dado que el caché está habilitado
        Cuando se solicitan los mismos datos dos veces
        Entonces la segunda llamada debe usar caché
        """
        mock_rates = [
            (datetime(2025, 11, 11, 10, 0).timestamp(), 1.1000, 1.1010, 1.0990, 1.1005, 0, 1000, 0),
        ]
        mock_connector._mt5.copy_rates_from_pos.return_value = mock_rates
        
        extractor_with_cache = MT5DataExtractor(mock_connector, enable_cache=True)
        
        # Primera llamada
        result1 = extractor_with_cache.get_ohlcv("EURUSD", Timeframe.M5, 1)
        
        # Segunda llamada (debería usar caché)
        result2 = extractor_with_cache.get_ohlcv("EURUSD", Timeframe.M5, 1)
        
        # Verificar que solo se llamó una vez a MT5
        assert mock_connector._mt5.copy_rates_from_pos.call_count == 1
        assert result1.count == result2.count
    
    # ==================== TESTS DE INTEGRACIÓN CON CANDLEWAITER ====================
    
    def test_get_ohlcv_waits_for_candle_close(self, extractor, mock_connector):
        """
        Dado que se usa integración con CandleWaiter
        Cuando se solicitan datos con wait_for_close=True
        Entonces debe esperar al cierre de la vela actual
        """
        mock_candle_waiter = Mock()
        mock_candle_waiter.wait_for_candle_close.return_value = True
        
        extractor_with_waiter = MT5DataExtractor(
            mock_connector,
            candle_waiter=mock_candle_waiter
        )
        
        mock_rates = [
            (datetime(2025, 11, 11, 10, 0).timestamp(), 1.1000, 1.1010, 1.0990, 1.1005, 0, 1000, 0),
        ]
        mock_connector._mt5.copy_rates_from_pos.return_value = mock_rates
        
        extractor_with_waiter.get_ohlcv(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            count=1,
            wait_for_close=True
        )
        
        assert mock_candle_waiter.wait_for_candle_close.called
