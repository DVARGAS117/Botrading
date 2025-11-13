"""
Tests unitarios para OperationVerifier.

Este módulo prueba la verificación de operaciones abiertas por activo y
Magic Number, permitiendo decidir entre evaluación nueva o reevaluación.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T04 - Verificación de operación abierta por activo y Magic Number
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from src.core.operation_verifier import (
    OperationVerifier,
    OperationVerifierError,
    VerificationResult,
    OperationInfo
)
from src.core.position_manager import Position, PositionType


class TestOperationVerifierInitialization:
    """Tests de inicialización del OperationVerifier"""
    
    def test_init_success_with_valid_connector(self):
        """
        Escenario: Inicializar con connector válido conectado
        Dado que tengo un connector conectado a MT5
        Cuando creo un OperationVerifier
        Entonces se inicializa correctamente
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        mock_position_manager = Mock()
        
        # Act
        verifier = OperationVerifier(mock_connector, mock_position_manager)
        
        # Assert
        assert verifier.connector == mock_connector
        assert verifier.position_manager == mock_position_manager
        assert verifier.logger is not None
    
    def test_init_fails_with_disconnected_connector(self):
        """
        Escenario: Inicializar con connector no conectado
        Dado que el connector NO está conectado
        Cuando intento crear un OperationVerifier
        Entonces lanza OperationVerifierError
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = False
        
        # Act & Assert
        with pytest.raises(OperationVerifierError) as exc:
            OperationVerifier(mock_connector, Mock())
        
        assert "no está conectado" in str(exc.value).lower()
    
    def test_init_with_custom_logger(self):
        """
        Escenario: Inicializar con logger personalizado
        Dado que proporciono un logger personalizado
        Cuando creo el verifier
        Entonces usa mi logger
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        custom_logger = Mock()
        
        # Act
        verifier = OperationVerifier(
            mock_connector,
            Mock(),
            logger=custom_logger
        )
        
        # Assert
        assert verifier.logger == custom_logger


class TestVerifyOperationBySymbolAndMagic:
    """
    Tests del método principal verify_operation()
    
    Cubre el criterio de aceptación:
    - Dado que el bot conoce el símbolo actual y su Magic Number
    - Cuando consulta posiciones abiertas en MT5 filtrando por símbolo y Magic Number
    - Entonces decide ruta de reevaluación si existe al menos una posición abierta
    """
    
    def test_verify_no_positions_returns_no_operation(self):
        """
        Escenario: No hay posiciones abiertas
        Dado que no existen posiciones del símbolo y magic
        Cuando verifico operación
        Entonces retorna has_operation=False y should_reevaluate=False
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        mock_position_manager = Mock()
        mock_position_manager.get_positions_by_symbol_and_magic.return_value = []
        
        verifier = OperationVerifier(mock_connector, mock_position_manager)
        
        # Act
        result = verifier.verify_operation("EURUSD", 100001)
        
        # Assert
        assert isinstance(result, VerificationResult)
        assert result.has_operation is False
        assert result.should_reevaluate is False
        assert result.operation_count == 0
        assert result.operations == []
        mock_position_manager.get_positions_by_symbol_and_magic.assert_called_once_with(
            "EURUSD", 100001
        )
    
    def test_verify_one_position_returns_reevaluate(self):
        """
        Escenario: Existe UNA posición abierta
        Dado que hay una posición del símbolo con ese magic
        Cuando verifico operación
        Entonces retorna has_operation=True y should_reevaluate=True
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        # Crear una posición mock
        mock_position = Position(
            ticket=12345,
            symbol="EURUSD",
            type=PositionType.BUY,
            volume=0.1,
            price_open=1.1000,
            price_current=1.1050,
            sl=1.0950,
            tp=1.1100,
            profit=50.0,
            swap=0.0,
            magic=100001,
            comment="Bot1",
            time_open=datetime.now()
        )
        
        mock_position_manager = Mock()
        mock_position_manager.get_positions_by_symbol_and_magic.return_value = [
            mock_position
        ]
        
        verifier = OperationVerifier(mock_connector, mock_position_manager)
        
        # Act
        result = verifier.verify_operation("EURUSD", 100001)
        
        # Assert
        assert result.has_operation is True
        assert result.should_reevaluate is True
        assert result.operation_count == 1
        assert len(result.operations) == 1
        
        op_info = result.operations[0]
        assert isinstance(op_info, OperationInfo)
        assert op_info.ticket == 12345
        assert op_info.symbol == "EURUSD"
        assert op_info.magic == 100001
    
    def test_verify_multiple_positions_returns_reevaluate_all(self):
        """
        Escenario: Existen MÚLTIPLES posiciones abiertas
        Dado que hay 2 posiciones del mismo símbolo y magic
        Cuando verifico operación
        Entonces retorna has_operation=True, should_reevaluate=True y lista todas
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        positions = [
            Position(
                ticket=111,
                symbol="EURUSD",
                type=PositionType.BUY,
                volume=0.1,
                price_open=1.1000,
                price_current=1.1050,
                sl=1.0950,
                tp=1.1100,
                profit=50.0,
                swap=0.0,
                magic=100001,
                comment="Market",
                time_open=datetime.now()
            ),
            Position(
                ticket=222,
                symbol="EURUSD",
                type=PositionType.BUY,
                volume=0.1,
                price_open=1.1010,
                price_current=1.1050,
                sl=1.0960,
                tp=1.1110,
                profit=40.0,
                swap=0.0,
                magic=100001,
                comment="Limit",
                time_open=datetime.now()
            )
        ]
        
        mock_position_manager = Mock()
        mock_position_manager.get_positions_by_symbol_and_magic.return_value = positions
        
        verifier = OperationVerifier(mock_connector, mock_position_manager)
        
        # Act
        result = verifier.verify_operation("EURUSD", 100001)
        
        # Assert
        assert result.has_operation is True
        assert result.should_reevaluate is True
        assert result.operation_count == 2
        assert len(result.operations) == 2
        assert result.operations[0].ticket == 111
        assert result.operations[1].ticket == 222


class TestVerifyOperationValidation:
    """Tests de validación de parámetros"""
    
    def test_verify_with_empty_symbol_raises_error(self):
        """
        Escenario: Símbolo vacío
        Dado que proporciono un símbolo vacío
        Cuando intento verificar
        Entonces lanza ValueError
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        verifier = OperationVerifier(mock_connector, Mock())
        
        # Act & Assert
        with pytest.raises(ValueError) as exc:
            verifier.verify_operation("", 100001)
        
        assert "símbolo" in str(exc.value).lower()
    
    def test_verify_with_none_symbol_raises_error(self):
        """
        Escenario: Símbolo None
        Dado que proporciono None como símbolo
        Cuando intento verificar
        Entonces lanza ValueError
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        verifier = OperationVerifier(mock_connector, Mock())
        
        # Act & Assert
        with pytest.raises(ValueError) as exc:
            verifier.verify_operation(None, 100001)
        
        assert "símbolo" in str(exc.value).lower()
    
    def test_verify_with_negative_magic_raises_error(self):
        """
        Escenario: Magic number negativo
        Dado que proporciono un magic negativo
        Cuando intento verificar
        Entonces lanza ValueError
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        verifier = OperationVerifier(mock_connector, Mock())
        
        # Act & Assert
        with pytest.raises(ValueError) as exc:
            verifier.verify_operation("EURUSD", -1)
        
        assert "magic" in str(exc.value).lower()
    
    def test_verify_with_magic_zero_is_valid(self):
        """
        Escenario: Magic number cero (válido)
        Dado que proporciono magic=0
        Cuando verifico operación
        Entonces no lanza error
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        mock_position_manager = Mock()
        mock_position_manager.get_positions_by_symbol_and_magic.return_value = []
        
        verifier = OperationVerifier(mock_connector, mock_position_manager)
        
        # Act
        result = verifier.verify_operation("EURUSD", 0)
        
        # Assert
        assert result.has_operation is False


class TestVerifyOperationErrorHandling:
    """Tests de manejo de errores del position_manager"""
    
    def test_verify_handles_position_manager_error(self):
        """
        Escenario: Error del PositionManager
        Dado que el position_manager lanza un error
        Cuando verifico operación
        Entonces lanza OperationVerifierError
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        mock_position_manager = Mock()
        mock_position_manager.get_positions_by_symbol_and_magic.side_effect = \
            Exception("MT5 connection lost")
        
        verifier = OperationVerifier(mock_connector, mock_position_manager)
        
        # Act & Assert
        with pytest.raises(OperationVerifierError) as exc:
            verifier.verify_operation("EURUSD", 100001)
        
        assert "error" in str(exc.value).lower()


class TestHasOpenOperation:
    """Tests del método auxiliar has_open_operation()"""
    
    def test_has_open_operation_returns_true_when_positions_exist(self):
        """
        Escenario: Verificar si hay operación (existe)
        Dado que hay posiciones abiertas
        Cuando llamo has_open_operation
        Entonces retorna True
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        mock_position = Position(
            ticket=12345,
            symbol="EURUSD",
            type=PositionType.BUY,
            volume=0.1,
            price_open=1.1000,
            price_current=1.1050,
            sl=1.0950,
            tp=1.1100,
            profit=50.0,
            swap=0.0,
            magic=100001,
            comment="Test",
            time_open=datetime.now()
        )
        
        mock_position_manager = Mock()
        mock_position_manager.get_positions_by_symbol_and_magic.return_value = [
            mock_position
        ]
        
        verifier = OperationVerifier(mock_connector, mock_position_manager)
        
        # Act
        has_operation = verifier.has_open_operation("EURUSD", 100001)
        
        # Assert
        assert has_operation is True
    
    def test_has_open_operation_returns_false_when_no_positions(self):
        """
        Escenario: Verificar si hay operación (no existe)
        Dado que NO hay posiciones abiertas
        Cuando llamo has_open_operation
        Entonces retorna False
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        mock_position_manager = Mock()
        mock_position_manager.get_positions_by_symbol_and_magic.return_value = []
        
        verifier = OperationVerifier(mock_connector, mock_position_manager)
        
        # Act
        has_operation = verifier.has_open_operation("EURUSD", 100001)
        
        # Assert
        assert has_operation is False


class TestVerificationResultDataClass:
    """Tests de la dataclass VerificationResult"""
    
    def test_verification_result_creation(self):
        """
        Escenario: Crear VerificationResult
        Cuando creo un resultado de verificación
        Entonces contiene todos los campos necesarios
        """
        # Arrange
        mock_op = Mock()
        
        # Act
        result = VerificationResult(
            has_operation=True,
            should_reevaluate=True,
            operation_count=2,
            operations=[mock_op, mock_op]
        )
        
        # Assert
        assert result.has_operation is True
        assert result.should_reevaluate is True
        assert result.operation_count == 2
        assert len(result.operations) == 2
    
    def test_verification_result_to_dict(self):
        """
        Escenario: Convertir VerificationResult a dict
        Cuando convierto a diccionario
        Entonces contiene todos los campos serializados
        """
        # Arrange
        op_info = OperationInfo(
            ticket=123,
            symbol="EURUSD",
            magic=100001,
            type="BUY",
            volume=0.1,
            profit=50.0
        )
        
        result = VerificationResult(
            has_operation=True,
            should_reevaluate=True,
            operation_count=1,
            operations=[op_info]
        )
        
        # Act
        result_dict = result.to_dict()
        
        # Assert
        assert result_dict['has_operation'] is True
        assert result_dict['should_reevaluate'] is True
        assert result_dict['operation_count'] == 1
        assert len(result_dict['operations']) == 1
        assert result_dict['operations'][0]['ticket'] == 123


class TestOperationInfoDataClass:
    """Tests de la dataclass OperationInfo"""
    
    def test_operation_info_creation(self):
        """
        Escenario: Crear OperationInfo
        Cuando creo información de operación
        Entonces contiene todos los campos necesarios
        """
        # Act
        op_info = OperationInfo(
            ticket=12345,
            symbol="GBPUSD",
            magic=200002,
            type="SELL",
            volume=0.2,
            profit=-25.0
        )
        
        # Assert
        assert op_info.ticket == 12345
        assert op_info.symbol == "GBPUSD"
        assert op_info.magic == 200002
        assert op_info.type == "SELL"
        assert op_info.volume == 0.2
        assert op_info.profit == -25.0
    
    def test_operation_info_to_dict(self):
        """
        Escenario: Convertir OperationInfo a dict
        Cuando convierto a diccionario
        Entonces contiene todos los campos
        """
        # Arrange
        op_info = OperationInfo(
            ticket=12345,
            symbol="GBPUSD",
            magic=200002,
            type="SELL",
            volume=0.2,
            profit=-25.0
        )
        
        # Act
        op_dict = op_info.to_dict()
        
        # Assert
        assert op_dict['ticket'] == 12345
        assert op_dict['symbol'] == "GBPUSD"
        assert op_dict['magic'] == 200002
        assert op_dict['type'] == "SELL"
        assert op_dict['volume'] == 0.2
        assert op_dict['profit'] == -25.0


class TestVerifyMultipleSymbols:
    """Tests de verificación en múltiples símbolos"""
    
    def test_verify_different_symbols_independently(self):
        """
        Escenario: Verificar múltiples símbolos
        Dado que tengo posiciones en EURUSD pero no en GBPUSD
        Cuando verifico ambos
        Entonces EURUSD retorna has_operation=True y GBPUSD=False
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        mock_position = Position(
            ticket=12345,
            symbol="EURUSD",
            type=PositionType.BUY,
            volume=0.1,
            price_open=1.1000,
            price_current=1.1050,
            sl=1.0950,
            tp=1.1100,
            profit=50.0,
            swap=0.0,
            magic=100001,
            comment="Test",
            time_open=datetime.now()
        )
        
        mock_position_manager = Mock()
        
        def get_positions_side_effect(symbol, magic):
            if symbol == "EURUSD":
                return [mock_position]
            else:
                return []
        
        mock_position_manager.get_positions_by_symbol_and_magic.side_effect = \
            get_positions_side_effect
        
        verifier = OperationVerifier(mock_connector, mock_position_manager)
        
        # Act
        result_eurusd = verifier.verify_operation("EURUSD", 100001)
        result_gbpusd = verifier.verify_operation("GBPUSD", 100001)
        
        # Assert
        assert result_eurusd.has_operation is True
        assert result_gbpusd.has_operation is False


class TestLogging:
    """Tests de logging del verifier"""
    
    def test_verify_logs_verification_process(self):
        """
        Escenario: Logging de verificación
        Dado que tengo un logger
        Cuando verifico operación
        Entonces se registran los eventos
        """
        # Arrange
        mock_connector = Mock()
        mock_connector.is_connected.return_value = True
        mock_connector._mt5 = Mock()
        
        mock_position_manager = Mock()
        mock_position_manager.get_positions_by_symbol_and_magic.return_value = []
        
        mock_logger = Mock()
        
        verifier = OperationVerifier(
            mock_connector,
            mock_position_manager,
            logger=mock_logger
        )
        
        # Act
        verifier.verify_operation("EURUSD", 100001)
        
        # Assert
        assert mock_logger.info.called or mock_logger.debug.called
