"""
Tests unitarios para el PositionManager.

Este módulo implementa tests siguiendo TDD para el Ticket T08: Consulta
de posiciones por símbolo y Magic Number, permitiendo filtrar posiciones
abiertas relevantes para cada bot.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T08 - Consulta de posiciones por símbolo y Magic Number
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Optional

# Importar el módulo a testear (aún no existe, pero lo crearemos)
from src.core.position_manager import (
    PositionManager,
    Position,
    PositionType,
    PositionManagerError
)


class TestPosition:
    """Tests para la clase Position (dataclass)"""
    
    def test_position_initialization(self):
        """
        Dado que se crea una Position con datos válidos
        Cuando se inicializa
        Entonces debe contener todos los atributos requeridos
        """
        position = Position(
            ticket=12345,
            symbol="EURUSD",
            type=PositionType.BUY,
            volume=0.1,
            price_open=1.1000,
            price_current=1.1050,
            sl=1.0950,
            tp=1.1150,
            profit=50.0,
            swap=-0.5,
            magic=100001,
            comment="Test position",
            time_open=datetime(2025, 11, 11, 10, 0)
        )
        
        assert position.ticket == 12345
        assert position.symbol == "EURUSD"
        assert position.type == PositionType.BUY
        assert position.volume == 0.1
        assert position.magic == 100001
    
    def test_position_type_enum_values(self):
        """
        Dado que se definen tipos de posición
        Cuando se accede a los valores del enum
        Entonces deben corresponder a los valores de MT5
        """
        assert PositionType.BUY.value == 0  # POSITION_TYPE_BUY
        assert PositionType.SELL.value == 1  # POSITION_TYPE_SELL
    
    def test_position_type_from_int(self):
        """
        Dado un entero de tipo de posición MT5
        Cuando se convierte a enum
        Entonces debe retornar el PositionType correcto
        """
        assert PositionType.from_int(0) == PositionType.BUY
        assert PositionType.from_int(1) == PositionType.SELL
    
    def test_position_type_from_int_invalid_raises_error(self):
        """
        Dado un entero inválido de tipo de posición
        Cuando se intenta convertir a enum
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="Tipo de posición inválido"):
            PositionType.from_int(99)
    
    def test_position_to_dict(self):
        """
        Dado una Position
        Cuando se convierte a diccionario
        Entonces debe incluir todos los campos
        """
        position = Position(
            ticket=12345,
            symbol="EURUSD",
            type=PositionType.BUY,
            volume=0.1,
            price_open=1.1000,
            price_current=1.1050,
            sl=1.0950,
            tp=1.1150,
            profit=50.0,
            swap=-0.5,
            magic=100001,
            comment="Test",
            time_open=datetime(2025, 11, 11, 10, 0)
        )
        
        result = position.to_dict()
        
        assert result['ticket'] == 12345
        assert result['symbol'] == "EURUSD"
        assert result['type'] == "BUY"
        assert result['magic'] == 100001


class TestPositionManager:
    """Tests para el PositionManager"""
    
    @pytest.fixture
    def mock_connector(self):
        """Fixture con mock del MT5Connector"""
        connector = Mock()
        connector.is_connected.return_value = True
        connector._mt5 = Mock()
        return connector
    
    @pytest.fixture
    def manager(self, mock_connector):
        """Fixture con PositionManager configurado"""
        return PositionManager(mock_connector)
    
    # ==================== TESTS DE INICIALIZACIÓN ====================
    
    def test_manager_initialization(self, mock_connector):
        """
        Dado un MT5Connector válido
        Cuando se crea un PositionManager
        Entonces se inicializa correctamente
        """
        manager = PositionManager(mock_connector)
        
        assert manager.connector == mock_connector
        assert manager._mt5 is not None
    
    def test_manager_initialization_requires_connection(self):
        """
        Dado un connector sin conexión activa
        Cuando se intenta crear un manager
        Entonces debe lanzar PositionManagerError
        """
        connector = Mock()
        connector.is_connected.return_value = False
        
        with pytest.raises(PositionManagerError, match="MT5 no está conectado"):
            PositionManager(connector)
    
    # ==================== TESTS DE CONSULTA DE POSICIONES ====================
    
    def test_get_all_positions_returns_list(self, manager, mock_connector):
        """
        Dado que MT5 tiene posiciones abiertas
        Cuando se solicitan todas las posiciones
        Entonces debe retornar lista de Position
        """
        # Mock de posiciones de MT5
        mock_positions = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001),
            self._create_mock_mt5_position(12346, "GBPUSD", 1, 0.2, 100001),
        ]
        
        mock_connector._mt5.positions_get.return_value = mock_positions
        
        result = manager.get_all_positions()
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, Position) for p in result)
    
    def test_get_all_positions_empty_returns_empty_list(self, manager, mock_connector):
        """
        Dado que no hay posiciones abiertas en MT5
        Cuando se solicitan todas las posiciones
        Entonces debe retornar lista vacía
        """
        mock_connector._mt5.positions_get.return_value = []
        
        result = manager.get_all_positions()
        
        assert result == []
    
    def test_get_all_positions_none_returns_empty_list(self, manager, mock_connector):
        """
        Dado que MT5 retorna None (sin posiciones)
        Cuando se solicitan todas las posiciones
        Entonces debe retornar lista vacía
        """
        mock_connector._mt5.positions_get.return_value = None
        
        result = manager.get_all_positions()
        
        assert result == []
    
    # ==================== TESTS DE FILTRADO POR SÍMBOLO ====================
    
    def test_get_positions_by_symbol(self, manager, mock_connector):
        """
        Dado que existen posiciones de EURUSD
        Cuando se filtran por símbolo "EURUSD"
        Entonces debe retornar solo posiciones de EURUSD
        """
        mock_positions = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001),
            self._create_mock_mt5_position(12346, "EURUSD", 1, 0.2, 100002),
        ]
        
        mock_connector._mt5.positions_get.return_value = mock_positions
        
        result = manager.get_positions_by_symbol("EURUSD")
        
        assert len(result) == 2
        assert all(p.symbol == "EURUSD" for p in result)
    
    def test_get_positions_by_symbol_uses_mt5_filter(self, manager, mock_connector):
        """
        Dado que se solicitan posiciones de un símbolo
        Cuando se llama a get_positions_by_symbol
        Entonces debe usar el parámetro symbol de MT5
        """
        mock_connector._mt5.positions_get.return_value = []
        
        manager.get_positions_by_symbol("EURUSD")
        
        mock_connector._mt5.positions_get.assert_called_once_with(symbol="EURUSD")
    
    def test_get_positions_by_symbol_validates_symbol(self, manager):
        """
        Dado un símbolo vacío
        Cuando se filtran posiciones
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="El símbolo es requerido"):
            manager.get_positions_by_symbol("")
    
    # ==================== TESTS DE FILTRADO POR MAGIC NUMBER ====================
    
    def test_get_positions_by_magic(self, manager, mock_connector):
        """
        Dado que existen posiciones con diferentes magic numbers
        Cuando se filtran por magic 100001
        Entonces debe retornar solo posiciones con ese magic
        """
        mock_positions = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001),
            self._create_mock_mt5_position(12346, "GBPUSD", 1, 0.2, 100001),
            self._create_mock_mt5_position(12347, "USDJPY", 0, 0.15, 100002),
        ]
        
        mock_connector._mt5.positions_get.return_value = mock_positions
        
        result = manager.get_positions_by_magic(100001)
        
        assert len(result) == 2
        assert all(p.magic == 100001 for p in result)
    
    def test_get_positions_by_magic_validates_magic(self, manager):
        """
        Dado un magic number inválido (negativo)
        Cuando se filtran posiciones
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="Magic number debe ser mayor o igual a 0"):
            manager.get_positions_by_magic(-1)
    
    # ==================== TESTS DE FILTRADO COMBINADO ====================
    
    def test_get_positions_by_symbol_and_magic(self, manager, mock_connector):
        """
        Dado que existen posiciones variadas
        Cuando se filtran por símbolo Y magic number
        Entonces debe retornar solo las que cumplen ambas condiciones
        """
        # Mock retorna solo posiciones de EURUSD (MT5 ya filtra por símbolo)
        mock_positions_eurusd = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001),  # ✓ Match
            self._create_mock_mt5_position(12346, "EURUSD", 1, 0.2, 100002),  # ✗ Otro magic
            self._create_mock_mt5_position(12348, "EURUSD", 0, 0.3, 100001),  # ✓ Match
        ]
        
        # MT5 positions_get(symbol="EURUSD") retorna solo EURUSD
        mock_connector._mt5.positions_get.return_value = mock_positions_eurusd
        
        result = manager.get_positions_by_symbol_and_magic("EURUSD", 100001)
        
        assert len(result) == 2
        assert all(p.symbol == "EURUSD" and p.magic == 100001 for p in result)
    
    def test_get_positions_by_symbol_and_magic_uses_mt5_filter(self, manager, mock_connector):
        """
        Dado que se solicitan posiciones con filtros combinados
        Cuando se llama a get_positions_by_symbol_and_magic
        Entonces debe usar ambos parámetros en MT5
        """
        mock_connector._mt5.positions_get.return_value = []
        
        manager.get_positions_by_symbol_and_magic("EURUSD", 100001)
        
        # Verificar que se llamó con los filtros correctos
        call_kwargs = mock_connector._mt5.positions_get.call_args.kwargs
        assert call_kwargs.get('symbol') == "EURUSD"
        # Note: MT5 no soporta filtrar por magic directamente, 
        # se hace post-procesamiento en Python
    
    # ==================== TESTS DE CONSULTA POR TICKET ====================
    
    def test_get_position_by_ticket(self, manager, mock_connector):
        """
        Dado que existe una posición con ticket 12345
        Cuando se consulta por ese ticket
        Entonces debe retornar la Position correspondiente
        """
        mock_position = self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001)
        
        mock_connector._mt5.positions_get.return_value = [mock_position]
        
        result = manager.get_position_by_ticket(12345)
        
        assert result is not None
        assert result.ticket == 12345
    
    def test_get_position_by_ticket_not_found_returns_none(self, manager, mock_connector):
        """
        Dado que no existe posición con ticket 99999
        Cuando se consulta por ese ticket
        Entonces debe retornar None
        """
        mock_connector._mt5.positions_get.return_value = None
        
        result = manager.get_position_by_ticket(99999)
        
        assert result is None
    
    def test_get_position_by_ticket_validates_ticket(self, manager):
        """
        Dado un ticket inválido (negativo)
        Cuando se consulta
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="Ticket debe ser mayor a 0"):
            manager.get_position_by_ticket(-1)
    
    # ==================== TESTS DE CÁLCULOS ====================
    
    def test_get_total_positions_count(self, manager, mock_connector):
        """
        Dado que hay 3 posiciones abiertas
        Cuando se consulta el total
        Entonces debe retornar 3
        """
        mock_positions = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001),
            self._create_mock_mt5_position(12346, "GBPUSD", 1, 0.2, 100001),
            self._create_mock_mt5_position(12347, "USDJPY", 0, 0.15, 100001),
        ]
        
        mock_connector._mt5.positions_get.return_value = mock_positions
        
        result = manager.get_total_positions()
        
        assert result == 3
    
    def test_get_positions_profit_sum(self, manager, mock_connector):
        """
        Dado posiciones con diferentes profits
        Cuando se calcula el profit total
        Entonces debe sumar correctamente
        """
        mock_positions = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001, profit=50.0),
            self._create_mock_mt5_position(12346, "GBPUSD", 1, 0.2, 100001, profit=-20.0),
            self._create_mock_mt5_position(12347, "USDJPY", 0, 0.15, 100001, profit=30.0),
        ]
        
        mock_connector._mt5.positions_get.return_value = mock_positions
        
        result = manager.get_total_profit()
        
        assert result == 60.0  # 50 - 20 + 30
    
    def test_get_positions_by_type(self, manager, mock_connector):
        """
        Dado posiciones BUY y SELL
        Cuando se filtran por tipo BUY
        Entonces debe retornar solo las BUY
        """
        mock_positions = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001),  # BUY
            self._create_mock_mt5_position(12346, "GBPUSD", 1, 0.2, 100001),  # SELL
            self._create_mock_mt5_position(12347, "USDJPY", 0, 0.15, 100001), # BUY
        ]
        
        mock_connector._mt5.positions_get.return_value = mock_positions
        
        result = manager.get_positions_by_type(PositionType.BUY)
        
        assert len(result) == 2
        assert all(p.type == PositionType.BUY for p in result)
    
    # ==================== TESTS DE CONVERSIÓN ====================
    
    def test_convert_mt5_position_to_position(self, manager):
        """
        Dado una posición en formato MT5
        Cuando se convierte a Position
        Entonces debe tener todos los campos mapeados
        """
        mt5_position = self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001)
        
        result = manager._convert_to_position(mt5_position)
        
        assert isinstance(result, Position)
        assert result.ticket == 12345
        assert result.symbol == "EURUSD"
        assert result.type == PositionType.BUY
        assert result.volume == 0.1
        assert result.magic == 100001
    
    # ==================== TESTS DE LOGGING ====================
    
    def test_query_logs_on_success(self, manager, mock_connector):
        """
        Dado que la consulta es exitosa
        Cuando se consultan posiciones
        Entonces debe registrar logs informativos
        """
        mock_logger = Mock()
        manager.logger = mock_logger
        
        mock_positions = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001),
        ]
        mock_connector._mt5.positions_get.return_value = mock_positions
        
        manager.get_all_positions()
        
        # Verificar que se llamó a logger (info o debug)
        assert mock_logger.info.called or mock_logger.debug.called
    
    def test_query_logs_on_error(self, manager, mock_connector):
        """
        Dado que ocurre un error en la consulta
        Cuando se intenta consultar posiciones
        Entonces debe registrar logs de error
        """
        mock_logger = Mock()
        manager.logger = mock_logger
        
        mock_connector._mt5.positions_get.side_effect = Exception("MT5 error")
        
        with pytest.raises(PositionManagerError):
            manager.get_all_positions()
        
        assert mock_logger.error.called
    
    # ==================== TESTS DE HAS_POSITIONS ====================
    
    def test_has_positions_returns_true_when_positions_exist(self, manager, mock_connector):
        """
        Dado que existen posiciones abiertas
        Cuando se consulta has_positions
        Entonces debe retornar True
        """
        mock_positions = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001),
        ]
        mock_connector._mt5.positions_get.return_value = mock_positions
        
        result = manager.has_positions()
        
        assert result is True
    
    def test_has_positions_returns_false_when_no_positions(self, manager, mock_connector):
        """
        Dado que no hay posiciones abiertas
        Cuando se consulta has_positions
        Entonces debe retornar False
        """
        mock_connector._mt5.positions_get.return_value = []
        
        result = manager.has_positions()
        
        assert result is False
    
    def test_has_positions_by_symbol_and_magic(self, manager, mock_connector):
        """
        Dado que existen posiciones de EURUSD con magic 100001
        Cuando se consulta has_positions con esos filtros
        Entonces debe retornar True
        """
        mock_positions = [
            self._create_mock_mt5_position(12345, "EURUSD", 0, 0.1, 100001),
        ]
        mock_connector._mt5.positions_get.return_value = mock_positions
        
        result = manager.has_positions(symbol="EURUSD", magic=100001)
        
        assert result is True
    
    # ==================== HELPER METHODS ====================
    
    def _create_mock_mt5_position(
        self,
        ticket: int,
        symbol: str,
        type_int: int,
        volume: float,
        magic: int,
        profit: float = 0.0
    ):
        """Crea un mock de posición MT5"""
        position = Mock()
        position.ticket = ticket
        position.symbol = symbol
        position.type = type_int
        position.volume = volume
        position.price_open = 1.1000
        position.price_current = 1.1050
        position.sl = 0.0
        position.tp = 0.0
        position.profit = profit
        position.swap = -0.5
        position.magic = magic
        position.comment = "Test"
        position.time = int(datetime(2025, 11, 11, 10, 0).timestamp())
        return position
