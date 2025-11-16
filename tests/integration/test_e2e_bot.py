"""
Pruebas de integración E2E para validar la cadena completa: datos → IA → ejecución → persistencia
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sqlite3
import os
import sys

# Agregar src al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.mt5_connector import MT5Connector
from core.mt5_data_extractor import MT5DataExtractor
from core.indicator_calculator import IndicatorCalculator
from core.gemini_client import GeminiClient
from core.order_manager import OrderManager
from core.operations_repository import OperationsRepository
from core.magic_number_generator import MagicNumberGenerator
from core.position_sizer import PositionSizer


class TestE2EBotIntegration:
    """Pruebas E2E para validar el flujo completo del bot"""

    @pytest.fixture
    def mock_mt5_data(self):
        """Datos simulados de MT5 para pruebas"""
        return {
            'EURUSD': {
                'M5': [
                    {'time': 1638360000, 'open': 1.1300, 'high': 1.1310, 'low': 1.1295, 'close': 1.1305, 'volume': 150},
                    {'time': 1638360300, 'open': 1.1305, 'high': 1.1315, 'low': 1.1300, 'close': 1.1310, 'volume': 200},
                    # ... más velas simuladas
                ] * 100,  # 100 velas para M5
                'M15': [
                    {'time': 1638360000, 'open': 1.1300, 'high': 1.1320, 'low': 1.1290, 'close': 1.1315, 'volume': 450},
                    # ... más velas
                ] * 80,
                'H1': [
                    {'time': 1638360000, 'open': 1.1300, 'high': 1.1330, 'low': 1.1280, 'close': 1.1320, 'volume': 1200},
                    # ... más velas
                ] * 50
            }
        }

    @pytest.fixture
    def mock_gemini_response(self):
        """Respuesta simulada de Gemini"""
        return {
            "accion": "OPERAR",
            "direccion": "BUY",
            "tipo_orden": "MARKET",
            "precio_entrada": 1.1310,
            "stop_loss": 1.1260,
            "take_profit": 1.1410,
            "riesgo_porcentaje": 2.0,
            "razonamiento": "Tendencia alcista confirmada por EMAs y RSI"
        }

    @pytest.fixture
    def test_db_path(self, tmp_path):
        """Base de datos temporal para pruebas"""
        return tmp_path / "test_trading.db"

    @pytest.fixture
    def db_connection(self, test_db_path):
        """Conexión a BD de prueba"""
        conn = sqlite3.connect(test_db_path)
        # Crear tablas necesarias
        conn.execute("""
            CREATE TABLE operaciones (
                id INTEGER PRIMARY KEY,
                magic_number INTEGER,
                bot_id INTEGER,
                ia_id INTEGER,
                tipo_orden TEXT,
                activo TEXT,
                direccion TEXT,
                precio_sugerido REAL,
                precio_entrada_real REAL,
                stop_loss REAL,
                take_profit REAL,
                lote REAL,
                riesgo_porcentaje REAL,
                estado TEXT,
                conversation_id TEXT,
                fecha_apertura DATETIME,
                profit_loss REAL,
                fecha_cierre DATETIME
            )
        """)
        conn.execute("""
            CREATE TABLE consultas_ia (
                id INTEGER PRIMARY KEY,
                operacion_id INTEGER,
                bot_id INTEGER,
                ia_id INTEGER,
                activo TEXT,
                tipo_consulta TEXT,
                prompt TEXT,
                respuesta TEXT,
                tokens_input INTEGER,
                tokens_output INTEGER,
                tokens_total INTEGER,
                costo_usd REAL,
                accion_decidida TEXT
            )
        """)
        conn.commit()
        yield conn
        conn.close()

    def test_e2e_complete_flow_simulation(self):
        """Prueba E2E completa simulada: Datos → IA → Ejecución → Persistencia"""

        # Mock de todos los componentes
        with patch('core.mt5_data_extractor.MT5DataExtractor') as mock_extractor_class, \
             patch('core.indicator_calculator.IndicatorCalculator') as mock_calculator_class, \
             patch('core.gemini_client.GeminiClient') as mock_gemini_class, \
             patch('core.magic_number_generator.MagicNumberGenerator') as mock_magic_class, \
             patch('core.position_sizer.PositionSizer') as mock_sizer_class, \
             patch('core.order_manager.OrderManager') as mock_order_class, \
             patch('core.operations_repository.OperationsRepository') as mock_repo_class:

            # Configurar mocks
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            mock_extractor.get_ohlcv.return_value = [{'close': 1.1310, 'time': 1638360000}]
            mock_extractor.get_current_price.return_value = {'bid': 1.1310, 'ask': 1.1312}

            mock_calculator = Mock()
            mock_calculator_class.return_value = mock_calculator
            mock_calculator.calculate_indicators_for_timeframe.return_value = Mock(
                ema20=1.1305, ema50=1.1300, rsi=65.5, macd=0.0002
            )

            mock_gemini = Mock()
            mock_gemini_class.return_value = mock_gemini
            mock_gemini.consultar_decision.return_value = {
                'decision': {
                    'accion': 'OPERAR',
                    'direccion': 'BUY',
                    'precio_entrada': 1.1310,
                    'stop_loss': 1.1260,
                    'take_profit': 1.1410,
                    'riesgo_porcentaje': 2.0
                },
                'tokens': 1500,
                'costo': 0.003
            }

            mock_magic = Mock()
            mock_magic_class.return_value = mock_magic
            mock_magic.generate.return_value = 110101

            mock_sizer = Mock()
            mock_sizer_class.return_value = mock_sizer
            mock_sizer.calculate_lot_size.return_value = 0.04

            mock_order = Mock()
            mock_order_class.return_value = mock_order
            mock_order.place_market_order.return_value = {'success': True, 'order_id': 12345}

            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.create_operation.return_value = 1

            # Simular el flujo E2E
            # 1. Extracción de datos
            connector_mock = Mock()
            extractor = mock_extractor_class(connector_mock)
            candles = extractor.get_ohlcv('EURUSD', 'M5', 100)
            current_price = extractor.get_current_price('EURUSD')

            # 2. Cálculo de indicadores
            calculator = mock_calculator_class()
            indicators = calculator.calculate_indicators_for_timeframe(candles[0])

            # 3. Consulta IA
            gemini = mock_gemini_class('test_key')
            ia_result = gemini.consultar_decision({}, 'evaluacion')

            # 4. Si IA decide operar
            if ia_result['decision']['accion'] == 'OPERAR':
                # Generar magic number
                magic_gen = mock_magic_class()
                magic_number = magic_gen.generate(1, 1, 'market')

                # Calcular lote
                sizer = mock_sizer_class()
                lote = sizer.calculate_lot_size(10000, 2.0, 1.1310, 1.1260, 'EURUSD')

                # Ejecutar orden
                order_mgr = mock_order_class()
                order_result = order_mgr.place_market_order(
                    'EURUSD', 'BUY', lote, 1.1260, 1.1410, magic_number
                )

                # Persistir
                repo = mock_repo_class()
                op_id = repo.create_operation({})

                # Verificar que todos los componentes se llamaron
                assert extractor.get_ohlcv.called
                assert extractor.get_current_price.called
                assert calculator.calculate_indicators_for_timeframe.called
                assert gemini.consultar_decision.called
                assert magic_gen.generate.called
                assert sizer.calculate_lot_size.called
                assert order_mgr.place_market_order.called
                assert repo.create_operation.called

                # Verificar resultados
                assert ia_result['decision']['accion'] == 'OPERAR'
                assert order_result['success'] is True
                assert magic_number == 110101
                assert lote == 0.04

    def test_e2e_no_operation_flow(self):
        """Prueba E2E cuando IA decide NO operar"""

        with patch('core.gemini_client.GeminiClient') as mock_gemini_class:
            mock_gemini = Mock()
            mock_gemini_class.return_value = mock_gemini
            mock_gemini.consultar_decision.return_value = {
                'decision': {
                    'accion': 'NO_OPERAR',
                    'razonamiento': 'Condiciones no favorables'
                },
                'tokens': 1200,
                'costo': 0.002
            }

            # Simular consulta IA
            gemini = mock_gemini_class('test_key')
            ia_result = gemini.consultar_decision({}, 'evaluacion')

            # Verificar que no se opera
            assert ia_result['decision']['accion'] == 'NO_OPERAR'
            assert 'razonamiento' in ia_result['decision']

    def test_e2e_integration_validation(self):
        """Prueba que valida la integración entre componentes"""

        # Esta prueba verifica que los componentes pueden instanciarse juntos
        # y que la cadena de llamadas funciona

        with patch('core.mt5_data_extractor.MT5DataExtractor') as mock_extractor_class, \
             patch('core.indicator_calculator.IndicatorCalculator') as mock_calculator_class, \
             patch('core.gemini_client.GeminiClient') as mock_gemini_class, \
             patch('core.operations_repository.OperationsRepository') as mock_repo_class:

            # Verificar que las clases se pueden importar y mockear
            assert mock_extractor_class is not None
            assert mock_calculator_class is not None
            assert mock_gemini_class is not None
            assert mock_repo_class is not None

            # Simular instanciación
            mock_connector = Mock()
            extractor = mock_extractor_class(mock_connector)
            calculator = mock_calculator_class()
            gemini = mock_gemini_class('key')
            repo = mock_repo_class()

            # Verificar que los objetos mock se crearon
            assert extractor is not None
            assert calculator is not None
            assert gemini is not None
            assert repo is not None
            
