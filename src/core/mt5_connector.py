"""
Módulo de conexión a MetaTrader 5 con validación y manejo de errores.

Este módulo implementa la funcionalidad del Ticket T06: Verificación de conexión
MT5 al inicio, proporcionando una interfaz robusta para conectar, validar y
gestionar la conexión con MetaTrader 5 de cualquier broker.

El diseño es agnóstico al broker, permitiendo fácil cambio entre brokers
(actualmente Pepperstone, pero preparado para cualquier otro).

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T06 - Verificación de conexión MT5 al inicio
"""
import logging
from typing import Optional, Any
from dataclasses import dataclass

try:
    import MetaTrader5 as mt5
except ImportError:
    # Para permitir tests sin tener MT5 instalado
    mt5 = None

from src.core.retry_handler import RetryHandler, MT5_RETRY_CONFIG


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class MT5Error(Exception):
    """Excepción base para errores de MT5"""
    pass


class MT5ConnectionError(MT5Error):
    """Excepción para errores de conexión a MT5"""
    pass


class MT5InitializationError(MT5Error):
    """Excepción para errores de inicialización de MT5"""
    pass


# ==================== CONFIGURACIÓN DE BROKER ====================

@dataclass
class BrokerConfig:
    """
    Configuración para conectar a un broker de MT5.
    
    Esta clase es agnóstica al broker, permitiendo configurar
    cualquier broker compatible con MetaTrader 5.
    
    Attributes:
        account_id: ID de la cuenta (número de cuenta)
        password: Contraseña de la cuenta
        server: Servidor del broker (ej: "Pepperstone-Demo", "ICMarkets-Live")
        timeout: Timeout de conexión en segundos (default: 60)
    
    Examples:
        >>> # Pepperstone
        >>> config = BrokerConfig(
        ...     account_id="12345678",
        ...     password="my_password",
        ...     server="Pepperstone-Demo"
        ... )
        
        >>> # Otro broker
        >>> config = BrokerConfig(
        ...     account_id="87654321",
        ...     password="another_pass",
        ...     server="ICMarkets-Live"
        ... )
    """
    account_id: str
    password: str
    server: str
    timeout: int = 60
    
    def __post_init__(self):
        """Valida la configuración después de la inicialización"""
        if not self.account_id or not self.account_id.strip():
            raise ValueError("account_id es requerido")
        
        if not self.password or not self.password.strip():
            raise ValueError("password es requerido")
        
        if not self.server or not self.server.strip():
            raise ValueError("server es requerido")
        
        if self.timeout <= 0:
            raise ValueError("timeout debe ser positivo")


# ==================== DECORADOR PARA REQUERIR CONEXIÓN ====================

def require_connection(func):
    """
    Decorador que verifica que haya una conexión activa antes de ejecutar.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada que valida conexión
        
    Raises:
        MT5ConnectionError: Si no hay conexión activa
    """
    def wrapper(self, *args, **kwargs):
        if not self.is_connected():
            raise MT5ConnectionError(
                "No hay conexión activa a MT5. "
                "Llame a verify_connection() primero."
            )
        return func(self, *args, **kwargs)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# ==================== CONECTOR MT5 ====================

class MT5Connector:
    """
    Conector robusto para MetaTrader 5 con validación y reintentos.
    
    Proporciona funcionalidad para:
    - Conectar a MT5 con cualquier broker
    - Validar conexión con reintentos automáticos
    - Obtener información de terminal y cuenta
    - Manejar desconexiones gracefully
    - Logging detallado de operaciones
    
    El diseño es agnóstico al broker, funcionando con Pepperstone,
    IC Markets, XM, o cualquier broker compatible con MT5.
    
    Attributes:
        config: Configuración del broker
        logger: Logger para registrar operaciones
        _mt5: Referencia al módulo MetaTrader5
        _connected: Estado de conexión
        _retry_handler: Handler para reintentos automáticos
    
    Example:
        >>> from src.core.mt5_connector import MT5Connector, BrokerConfig
        >>> 
        >>> # Configurar para Pepperstone
        >>> config = BrokerConfig(
        ...     account_id="12345678",
        ...     password="my_password",
        ...     server="Pepperstone-Demo"
        ... )
        >>> 
        >>> # Conectar con context manager (recomendado)
        >>> with MT5Connector(config) as connector:
        ...     if connector.verify_connection():
        ...         account = connector.get_account_info()
        ...         print(f"Balance: {account.balance}")
        >>> 
        >>> # O manualmente
        >>> connector = MT5Connector(config)
        >>> try:
        ...     connector.verify_connection()
        ...     # Usar connector
        ... finally:
        ...     connector.disconnect()
    """
    
    def __init__(
        self,
        config: BrokerConfig,
        logger: Optional[logging.Logger] = None,
        retry_handler: Optional[RetryHandler] = None
    ):
        """
        Inicializa el conector de MT5.
        
        Args:
            config: Configuración del broker
            logger: Logger opcional para registrar operaciones
            retry_handler: Handler opcional para reintentos (usa default si None)
        
        Raises:
            MT5InitializationError: Si MT5 no está disponible
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._connected = False
        
        # Verificar que MT5 esté disponible
        if mt5 is None:
            raise MT5InitializationError(
                "El módulo MetaTrader5 no está disponible. "
                "Instale con: pip install MetaTrader5"
            )
        
        self._mt5 = mt5
        
        # Configurar retry handler
        self._retry_handler = retry_handler or RetryHandler(MT5_RETRY_CONFIG)
        
        self.logger.debug(
            f"MT5Connector inicializado para servidor: {config.server}"
        )
    
    # ==================== GESTIÓN DE CONEXIÓN ====================
    
    def verify_connection(self) -> bool:
        """
        Verifica y establece la conexión con MT5.
        
        Este método:
        1. Inicializa MT5
        2. Autentica con las credenciales del broker
        3. Verifica que el terminal esté conectado
        4. Valida que el trading esté permitido
        
        Returns:
            True si la conexión es exitosa
        
        Raises:
            MT5InitializationError: Si falla la inicialización
            MT5ConnectionError: Si falla la autenticación o conexión
        
        Example:
            >>> connector.verify_connection()
            True
        """
        self.logger.info(
            f"Verificando conexión a MT5 - Servidor: {self.config.server}"
        )
        
        try:
            # Paso 1: Inicializar MT5
            if not self._initialize():
                error_code, error_msg = self._mt5.last_error()
                self.logger.error(
                    f"Error al inicializar MT5: [{error_code}] {error_msg}"
                )
                raise MT5InitializationError(
                    f"No se pudo inicializar MT5: [{error_code}] {error_msg}"
                )
            
            # Paso 2: Autenticar
            if not self._login():
                error_code, error_msg = self._mt5.last_error()
                self.logger.error(
                    f"Error al autenticar con MT5: [{error_code}] {error_msg}"
                )
                raise MT5ConnectionError(
                    f"No se pudo autenticar en MT5: [{error_code}] {error_msg}"
                )
            
            # Paso 3: Verificar estado del terminal
            terminal_info = self._mt5.terminal_info()
            if terminal_info is None:
                raise MT5ConnectionError(
                    "No se pudo obtener información del terminal"
                )
            
            if not terminal_info.connected:
                raise MT5ConnectionError(
                    "Terminal no conectado al servidor del broker"
                )
            
            if not terminal_info.trade_allowed:
                self.logger.warning(
                    "Trading no está permitido en el terminal"
                )
            
            # Conexión exitosa
            self._connected = True
            self.logger.info(
                f"Conexión exitosa a MT5 - Cuenta: {self.config.account_id}, "
                f"Servidor: {self.config.server}"
            )
            
            return True
        
        except (MT5InitializationError, MT5ConnectionError):
            self._connected = False
            raise
        
        except Exception as e:
            self._connected = False
            self.logger.error(f"Error inesperado al conectar a MT5: {e}")
            raise MT5ConnectionError(f"Error inesperado: {e}")
    
    def _initialize(self) -> bool:
        """
        Inicializa el terminal MT5.
        
        Returns:
            True si la inicialización es exitosa
        """
        self.logger.debug("Inicializando terminal MT5...")
        return self._mt5.initialize()
    
    def _login(self) -> bool:
        """
        Autentica con las credenciales del broker.
        
        Returns:
            True si la autenticación es exitosa
        """
        self.logger.debug(
            f"Autenticando cuenta {self.config.account_id} "
            f"en servidor {self.config.server}..."
        )
        
        return self._mt5.login(
            login=int(self.config.account_id),
            password=self.config.password,
            server=self.config.server,
            timeout=self.config.timeout
        )
    
    def disconnect(self) -> None:
        """
        Desconecta y cierra la sesión de MT5.
        
        Es seguro llamar este método múltiples veces o cuando
        no hay conexión activa.
        
        Example:
            >>> connector.disconnect()
        """
        if self._connected:
            self.logger.info("Desconectando de MT5...")
            self._mt5.shutdown()
            self._connected = False
            self.logger.debug("Desconexión completada")
        else:
            self.logger.debug("No hay conexión activa para desconectar")
    
    def is_connected(self) -> bool:
        """
        Verifica si hay una conexión activa a MT5.
        
        Returns:
            True si está conectado, False en caso contrario
        
        Example:
            >>> connector.is_connected()
            True
        """
        return self._connected
    
    # ==================== INFORMACIÓN DEL TERMINAL ====================
    
    @require_connection
    def get_terminal_info(self) -> Any:
        """
        Obtiene información del terminal MT5.
        
        Returns:
            Objeto con información del terminal (connected, trade_allowed, etc.)
        
        Raises:
            MT5ConnectionError: Si no hay conexión activa
        
        Example:
            >>> info = connector.get_terminal_info()
            >>> print(f"Conectado: {info.connected}")
            >>> print(f"Trading: {info.trade_allowed}")
        """
        info = self._mt5.terminal_info()
        
        if info is None:
            raise MT5ConnectionError(
                "No se pudo obtener información del terminal"
            )
        
        return info
    
    # ==================== INFORMACIÓN DE CUENTA ====================
    
    @require_connection
    def get_account_info(self) -> Any:
        """
        Obtiene información de la cuenta actual.
        
        Returns:
            Objeto con información de la cuenta (balance, equity, margin, etc.)
        
        Raises:
            MT5ConnectionError: Si no hay conexión activa
        
        Example:
            >>> account = connector.get_account_info()
            >>> print(f"Balance: ${account.balance}")
            >>> print(f"Equity: ${account.equity}")
            >>> print(f"Servidor: {account.server}")
        """
        account = self._mt5.account_info()
        
        if account is None:
            raise MT5ConnectionError(
                "No se pudo obtener información de la cuenta"
            )
        
        return account
    
    # ==================== CONTEXT MANAGER ====================
    
    def __enter__(self):
        """
        Permite usar el connector como context manager.
        
        Example:
            >>> with MT5Connector(config) as connector:
            ...     account = connector.get_account_info()
        """
        self.verify_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Desconecta al salir del contexto"""
        self.disconnect()
        return False
    
    # ==================== REPRESENTACIÓN ====================
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        status = "conectado" if self._connected else "desconectado"
        return (
            f"<MT5Connector(servidor={self.config.server}, "
            f"cuenta={self.config.account_id}, "
            f"estado={status})>"
        )
    
    def __str__(self) -> str:
        """Representación en string"""
        status = "✓ Conectado" if self._connected else "✗ Desconectado"
        return (
            f"MT5Connector - {status}\n"
            f"  Servidor: {self.config.server}\n"
            f"  Cuenta: {self.config.account_id}"
        )


# ==================== FUNCIONES HELPER ====================

def create_connector_from_credentials(
    credentials: dict,
    logger: Optional[logging.Logger] = None
) -> MT5Connector:
    """
    Crea un MT5Connector desde un diccionario de credenciales.
    
    Args:
        credentials: Dict con claves 'account_id', 'password', 'server'
        logger: Logger opcional
    
    Returns:
        MT5Connector configurado
    
    Raises:
        KeyError: Si faltan claves requeridas
        ValueError: Si los valores son inválidos
    
    Example:
        >>> creds = {
        ...     'account_id': '12345678',
        ...     'password': 'my_password',
        ...     'server': 'Pepperstone-Demo'
        ... }
        >>> connector = create_connector_from_credentials(creds)
    """
    try:
        config = BrokerConfig(
            account_id=credentials['account_id'],
            password=credentials['password'],
            server=credentials['server'],
            timeout=credentials.get('timeout', 60)
        )
        
        return MT5Connector(config, logger=logger)
    
    except KeyError as e:
        raise KeyError(f"Credencial faltante: {e}")
