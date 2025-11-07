"""
Tests unitarios para el MT5Connector.

Este módulo implementa tests siguiendo TDD para el Ticket T06: Verificación
de conexión MT5 al inicio, asegurando que la conexión a MetaTrader 5 se
valide correctamente antes de operar.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T06 - Verificación de conexión MT5 al inicio
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Importar el módulo a testear (aún no existe, pero lo crearemos)
from src.core.mt5_connector import (
    MT5Connector,
    MT5ConnectionError,
    MT5InitializationError,
    BrokerConfig
)


class TestBrokerConfig:
    """Tests para la configuración de broker"""
    
    def test_broker_config_initialization(self):
        """
        Dado que se proporciona configuración válida de broker
        Cuando se crea un BrokerConfig
        Entonces se inicializa correctamente con todos los parámetros
        """
        config = BrokerConfig(
            account_id="12345678",
            password="test_password",
            server="Pepperstone-Demo",
            timeout=60
        )
        
        assert config.account_id == "12345678"
        assert config.password == "test_password"
        assert config.server == "Pepperstone-Demo"
        assert config.timeout == 60
    
    def test_broker_config_default_timeout(self):
        """
        Dado que se crea un BrokerConfig sin especificar timeout
        Cuando se accede al timeout
        Entonces debe tener un valor por defecto de 60 segundos
        """
        config = BrokerConfig(
            account_id="12345678",
            password="test_password",
            server="Pepperstone-Demo"
        )
        
        assert config.timeout == 60
    
    def test_broker_config_validation_missing_account(self):
        """
        Dado que se intenta crear BrokerConfig sin account_id
        Cuando se valida la configuración
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="account_id es requerido"):
            BrokerConfig(
                account_id="",
                password="test_password",
                server="Pepperstone-Demo"
            )
    
    def test_broker_config_validation_missing_password(self):
        """
        Dado que se intenta crear BrokerConfig sin password
        Cuando se valida la configuración
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="password es requerido"):
            BrokerConfig(
                account_id="12345678",
                password="",
                server="Pepperstone-Demo"
            )
    
    def test_broker_config_validation_missing_server(self):
        """
        Dado que se intenta crear BrokerConfig sin server
        Cuando se valida la configuración
        Entonces debe lanzar ValueError
        """
        with pytest.raises(ValueError, match="server es requerido"):
            BrokerConfig(
                account_id="12345678",
                password="test_password",
                server=""
            )


class TestMT5Connector:
    """Tests para el MT5Connector"""
    
    @pytest.fixture
    def broker_config(self):
        """Fixture con configuración de broker válida"""
        return BrokerConfig(
            account_id="12345678",
            password="test_password",
            server="Pepperstone-Demo",
            timeout=60
        )
    
    @pytest.fixture
    def mock_mt5(self):
        """Fixture con mock del módulo MetaTrader5"""
        with patch('src.core.mt5_connector.mt5') as mock:
            yield mock
    
    @pytest.fixture
    def mock_retry_handler(self):
        """Fixture con mock del RetryHandler"""
        with patch('src.core.mt5_connector.RetryHandler') as mock:
            yield mock
    
    @pytest.fixture
    def connector(self, broker_config, mock_mt5, mock_retry_handler):
        """Fixture con MT5Connector configurado"""
        return MT5Connector(broker_config)
    
    # ==================== TESTS DE INICIALIZACIÓN ====================
    
    def test_connector_initialization(self, broker_config, mock_mt5, mock_retry_handler):
        """
        Dado que se proporciona una configuración válida
        Cuando se crea un MT5Connector
        Entonces se inicializa correctamente sin conectar aún
        """
        connector = MT5Connector(broker_config)
        
        assert connector.config == broker_config
        assert connector.is_connected() is False
        assert connector._mt5 is not None
    
    def test_connector_initialization_with_logger(self, broker_config, mock_mt5, mock_retry_handler):
        """
        Dado que se proporciona un logger personalizado
        Cuando se crea un MT5Connector
        Entonces debe usar ese logger
        """
        custom_logger = Mock()
        connector = MT5Connector(broker_config, logger=custom_logger)
        
        assert connector.logger == custom_logger
    
    # ==================== TESTS DE CONEXIÓN EXITOSA ====================
    
    def test_verify_connection_success(self, connector, mock_mt5):
        """
        Dado que MT5 está disponible y las credenciales son correctas
        Cuando se llama a verify_connection
        Entonces debe conectarse exitosamente y retornar True
        """
        # Configurar mocks para conexión exitosa
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = Mock(
            connected=True,
            trade_allowed=True
        )
        
        result = connector.verify_connection()
        
        assert result is True
        assert connector.is_connected() is True
        mock_mt5.initialize.assert_called_once()
        mock_mt5.login.assert_called_once_with(
            login=int(connector.config.account_id),
            password=connector.config.password,
            server=connector.config.server,
            timeout=connector.config.timeout
        )
    
    def test_verify_connection_with_retry_handler(self, connector, mock_mt5, mock_retry_handler):
        """
        Dado que se configura el connector con retry handler
        Cuando se verifica la conexión
        Entonces debe usar el retry handler para manejar fallos temporales
        """
        # Configurar mock de retry handler
        mock_handler_instance = Mock()
        mock_retry_handler.return_value = mock_handler_instance
        mock_handler_instance.execute.return_value = True
        
        # Recrear connector para que use el mock
        connector = MT5Connector(connector.config)
        
        # Verificar que se puede ejecutar con retry
        result = connector.verify_connection()
        
        assert result is True
    
    # ==================== TESTS DE FALLOS DE INICIALIZACIÓN ====================
    
    def test_verify_connection_initialization_fails(self, connector, mock_mt5):
        """
        Dado que MT5.initialize() falla
        Cuando se intenta verificar la conexión
        Entonces debe lanzar MT5InitializationError
        """
        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (1, "Initialization failed")
        
        with pytest.raises(MT5InitializationError, match="No se pudo inicializar MT5"):
            connector.verify_connection()
        
        assert connector.is_connected() is False
    
    def test_verify_connection_login_fails(self, connector, mock_mt5):
        """
        Dado que MT5.initialize() tiene éxito pero login() falla
        Cuando se intenta verificar la conexión
        Entonces debe lanzar MT5ConnectionError
        """
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = False
        mock_mt5.last_error.return_value = (2, "Invalid credentials")
        
        with pytest.raises(MT5ConnectionError, match="No se pudo autenticar"):
            connector.verify_connection()
        
        assert connector.is_connected() is False
    
    def test_verify_connection_terminal_not_connected(self, connector, mock_mt5):
        """
        Dado que login tiene éxito pero el terminal no está conectado
        Cuando se verifica el estado del terminal
        Entonces debe lanzar MT5ConnectionError
        """
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = Mock(
            connected=False,
            trade_allowed=False
        )
        
        with pytest.raises(MT5ConnectionError, match="Terminal no conectado"):
            connector.verify_connection()
    
    # ==================== TESTS DE REINTENTOS ====================
    
    def test_verify_connection_with_retries_success_on_second_attempt(
        self, connector, mock_mt5
    ):
        """
        Dado que el primer intento falla pero el segundo tiene éxito
        Cuando se verifica la conexión con reintentos
        Entonces debe conectarse exitosamente después del reintento
        """
        # Simular fallo en primer intento, éxito en segundo
        mock_mt5.initialize.side_effect = [False, True]
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = Mock(
            connected=True,
            trade_allowed=True
        )
        mock_mt5.last_error.return_value = (1, "Temporary error")
        
        # La lógica de retry debería estar en el RetryHandler
        # Este test verifica que la segunda llamada funcione
        with pytest.raises(MT5InitializationError):
            connector.verify_connection()
        
        # Segundo intento
        mock_mt5.initialize.side_effect = None
        mock_mt5.initialize.return_value = True
        result = connector.verify_connection()
        
        assert result is True
    
    # ==================== TESTS DE DESCONEXIÓN ====================
    
    def test_disconnect_when_connected(self, connector, mock_mt5):
        """
        Dado que el connector está conectado
        Cuando se llama a disconnect
        Entonces debe cerrar la conexión y actualizar el estado
        """
        # Simular conexión exitosa primero
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = Mock(
            connected=True,
            trade_allowed=True
        )
        connector.verify_connection()
        
        # Ahora desconectar
        connector.disconnect()
        
        mock_mt5.shutdown.assert_called_once()
        assert connector.is_connected() is False
    
    def test_disconnect_when_not_connected(self, connector, mock_mt5):
        """
        Dado que el connector no está conectado
        Cuando se llama a disconnect
        Entonces no debe hacer nada y no lanzar error
        """
        connector.disconnect()
        
        mock_mt5.shutdown.assert_not_called()
        assert connector.is_connected() is False
    
    # ==================== TESTS DE INFORMACIÓN DEL TERMINAL ====================
    
    def test_get_terminal_info_when_connected(self, connector, mock_mt5):
        """
        Dado que el connector está conectado
        Cuando se solicita información del terminal
        Entonces debe retornar información válida
        """
        # Conectar primero
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        terminal_info_mock = Mock(
            connected=True,
            trade_allowed=True,
            company="Pepperstone",
            name="MetaTrader 5"
        )
        mock_mt5.terminal_info.return_value = terminal_info_mock
        
        connector.verify_connection()
        
        # Obtener info
        info = connector.get_terminal_info()
        
        assert info is not None
        assert info.connected is True
        assert info.trade_allowed is True
        assert info.company == "Pepperstone"
    
    def test_get_terminal_info_when_not_connected(self, connector):
        """
        Dado que el connector no está conectado
        Cuando se solicita información del terminal
        Entonces debe lanzar MT5ConnectionError
        """
        with pytest.raises(MT5ConnectionError, match="No hay conexión activa"):
            connector.get_terminal_info()
    
    # ==================== TESTS DE INFORMACIÓN DE CUENTA ====================
    
    def test_get_account_info_when_connected(self, connector, mock_mt5):
        """
        Dado que el connector está conectado
        Cuando se solicita información de la cuenta
        Entonces debe retornar información válida
        """
        # Conectar primero
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = Mock(
            connected=True,
            trade_allowed=True
        )
        account_info_mock = Mock(
            login=12345678,
            balance=10000.00,
            equity=10000.00,
            margin=0.00,
            margin_free=10000.00,
            server="Pepperstone-Demo"
        )
        mock_mt5.account_info.return_value = account_info_mock
        
        connector.verify_connection()
        
        # Obtener info
        info = connector.get_account_info()
        
        assert info is not None
        assert info.login == 12345678
        assert info.balance == 10000.00
        assert info.server == "Pepperstone-Demo"
    
    def test_get_account_info_when_not_connected(self, connector):
        """
        Dado que el connector no está conectado
        Cuando se solicita información de la cuenta
        Entonces debe lanzar MT5ConnectionError
        """
        with pytest.raises(MT5ConnectionError, match="No hay conexión activa"):
            connector.get_account_info()
    
    # ==================== TESTS DE CONTEXT MANAGER ====================
    
    def test_connector_as_context_manager(self, broker_config, mock_mt5):
        """
        Dado que se usa MT5Connector como context manager
        Cuando se entra y sale del contexto
        Entonces debe conectar al entrar y desconectar al salir
        """
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = Mock(
            connected=True,
            trade_allowed=True
        )
        
        with MT5Connector(broker_config) as connector:
            assert connector.is_connected() is True
        
        mock_mt5.shutdown.assert_called_once()
    
    def test_connector_context_manager_with_exception(self, broker_config, mock_mt5):
        """
        Dado que ocurre una excepción dentro del context manager
        Cuando se sale del contexto
        Entonces debe desconectar correctamente
        """
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = Mock(
            connected=True,
            trade_allowed=True
        )
        
        try:
            with MT5Connector(broker_config) as connector:
                assert connector.is_connected() is True
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        mock_mt5.shutdown.assert_called_once()
    
    # ==================== TESTS DE VALIDACIÓN DE ESTADO ====================
    
    def test_require_connection_decorator_when_connected(self, connector, mock_mt5):
        """
        Dado que el connector está conectado
        Cuando se llama a un método que requiere conexión
        Entonces debe ejecutarse normalmente
        """
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = Mock(
            connected=True,
            trade_allowed=True
        )
        
        connector.verify_connection()
        
        # get_terminal_info requiere conexión
        info = connector.get_terminal_info()
        assert info is not None
    
    def test_require_connection_decorator_when_not_connected(self, connector):
        """
        Dado que el connector NO está conectado
        Cuando se llama a un método que requiere conexión
        Entonces debe lanzar MT5ConnectionError
        """
        with pytest.raises(MT5ConnectionError, match="No hay conexión activa"):
            connector.get_terminal_info()
    
    # ==================== TESTS DE COMPATIBILIDAD DE BROKER ====================
    
    def test_pepperstone_broker_configuration(self, mock_mt5):
        """
        Dado que se configura Pepperstone como broker
        Cuando se crea el connector
        Entonces debe aceptar la configuración de Pepperstone
        """
        config = BrokerConfig(
            account_id="12345678",
            password="test_password",
            server="Pepperstone-Demo"
        )
        connector = MT5Connector(config)
        
        assert connector.config.server == "Pepperstone-Demo"
    
    def test_generic_broker_configuration(self, mock_mt5):
        """
        Dado que se configura un broker genérico
        Cuando se crea el connector
        Entonces debe aceptar cualquier configuración válida de broker
        """
        config = BrokerConfig(
            account_id="87654321",
            password="another_password",
            server="AnotherBroker-Live"
        )
        connector = MT5Connector(config)
        
        assert connector.config.server == "AnotherBroker-Live"
        assert connector.config.account_id == "87654321"
    
    # ==================== TESTS DE LOGGING ====================
    
    def test_connection_logs_on_success(self, connector, mock_mt5):
        """
        Dado que la conexión es exitosa
        Cuando se verifica la conexión
        Entonces debe registrar logs informativos
        """
        mock_logger = Mock()
        connector.logger = mock_logger
        
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = Mock(
            connected=True,
            trade_allowed=True
        )
        
        connector.verify_connection()
        
        # Verificar que se registraron logs
        assert mock_logger.info.called
    
    def test_connection_logs_on_failure(self, connector, mock_mt5):
        """
        Dado que la conexión falla
        Cuando se intenta verificar la conexión
        Entonces debe registrar logs de error
        """
        mock_logger = Mock()
        connector.logger = mock_logger
        
        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (1, "Connection failed")
        
        with pytest.raises(MT5InitializationError):
            connector.verify_connection()
        
        # Verificar que se registraron errores
        assert mock_logger.error.called
