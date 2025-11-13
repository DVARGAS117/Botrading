"""
Módulo de instancias independientes de bots.

Este módulo implementa el Ticket T03: Instancias independientes por bot,
permitiendo que cada bot se ejecute como proceso/servicio independiente
con su propia configuración, estado y componentes aislados.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T03 - Instancias independientes por bot
"""
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Callable

from src.core.time_validator import TimeValidator
from src.core.cycle_scheduler import CycleScheduler
from src.core.mt5_connector import MT5Connector, BrokerConfig


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class BotInstanceError(Exception):
    """Excepción base para errores de BotInstance"""
    pass


class BotConfigurationError(BotInstanceError):
    """Excepción para errores de configuración de bot"""
    pass


class BotStateError(BotInstanceError):
    """Excepción para errores de estado de bot"""
    pass


# ==================== ENUMS ====================

class BotStatus(str, Enum):
    """
    Estados posibles de un bot.
    
    STOPPED: Bot detenido (estado inicial)
    STARTING: Bot en proceso de inicio
    RUNNING: Bot ejecutándose normalmente
    ERROR: Bot en estado de error
    STOPPING: Bot en proceso de detención
    """
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    ERROR = "ERROR"
    STOPPING = "STOPPING"


# ==================== DATACLASSES ====================

@dataclass
class BotConfig:
    """
    Configuración de un bot individual.
    
    Attributes:
        bot_id: ID único del bot (1-5)
        bot_name: Nombre descriptivo del bot
        enabled: Si el bot está habilitado
        schedule_config: Configuración de horarios (para TimeValidator)
        mt5_config: Configuración de MT5 (para MT5Connector)
        cycle_config: Configuración de ciclos (para CycleScheduler)
    """
    bot_id: int
    bot_name: str
    enabled: bool
    schedule_config: Dict[str, Any]
    mt5_config: Dict[str, Any]
    cycle_config: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BotConfig':
        """
        Crea un BotConfig desde un diccionario.
        
        Args:
            config_dict: Diccionario con configuración
        
        Returns:
            Instancia de BotConfig
        
        Raises:
            BotConfigurationError: Si la configuración es inválida
        """
        # Validar campos requeridos
        if "bot_id" not in config_dict:
            raise BotConfigurationError("bot_id es requerido")
        
        bot_id = config_dict["bot_id"]
        if not isinstance(bot_id, int) or bot_id < 1 or bot_id > 5:
            raise BotConfigurationError("bot_id debe estar entre 1 y 5")
        
        if "bot_name" not in config_dict:
            raise BotConfigurationError("bot_name es requerido")
        
        return cls(
            bot_id=bot_id,
            bot_name=config_dict["bot_name"],
            enabled=config_dict.get("enabled", True),
            schedule_config=config_dict.get("schedule_config", {}),
            mt5_config=config_dict.get("mt5_config", {}),
            cycle_config=config_dict.get("cycle_config", {})
        )


@dataclass
class BotState:
    """
    Estado de un bot individual.
    
    Attributes:
        bot_id: ID del bot
        status: Estado actual del bot
        started_at: Timestamp de inicio
        stopped_at: Timestamp de detención
        cycles_completed: Número de ciclos completados
        last_cycle_at: Timestamp del último ciclo
        error_count: Contador de errores
        last_error: Último mensaje de error
    """
    bot_id: int
    status: BotStatus = BotStatus.STOPPED
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    cycles_completed: int = 0
    last_cycle_at: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    
    def transition_to(self, new_status: BotStatus, error_message: Optional[str] = None) -> None:
        """
        Transiciona el bot a un nuevo estado.
        
        Args:
            new_status: Nuevo estado
            error_message: Mensaje de error (para estado ERROR)
        """
        self.status = new_status
        
        if new_status == BotStatus.RUNNING:
            self.started_at = datetime.now()
        elif new_status == BotStatus.STOPPED:
            self.stopped_at = datetime.now()
        elif new_status == BotStatus.ERROR:
            self.error_count += 1
            if error_message:
                self.last_error = error_message
    
    def increment_cycle(self) -> None:
        """Incrementa el contador de ciclos completados"""
        self.cycles_completed += 1
        self.last_cycle_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el estado a diccionario.
        
        Returns:
            Diccionario con el estado
        """
        return {
            "bot_id": self.bot_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "cycles_completed": self.cycles_completed,
            "last_cycle_at": self.last_cycle_at.isoformat() if self.last_cycle_at else None,
            "error_count": self.error_count,
            "last_error": self.last_error
        }


# ==================== CLASE PRINCIPAL ====================

class BotInstance:
    """
    Instancia independiente de un bot de trading.
    
    Cada instancia representa un bot completo con:
    - Configuración propia
    - Estado independiente
    - Componentes aislados (TimeValidator, CycleScheduler, MT5Connector)
    - Lifecycle management (start, stop, status)
    
    Funcionalidades:
    - Inicialización con configuración específica
    - Gestión de lifecycle (start/stop)
    - Ejecución de ciclos de trading
    - Monitoreo de estado
    - Aislamiento entre instancias
    
    Example:
        >>> # Configurar bot 1
        >>> config1 = BotConfig(
        ...     bot_id=1,
        ...     bot_name="ScalpingBot",
        ...     enabled=True,
        ...     schedule_config={...},
        ...     mt5_config={...},
        ...     cycle_config={...}
        ... )
        >>> 
        >>> # Crear instancia
        >>> bot1 = BotInstance(config1)
        >>> 
        >>> # Iniciar bot
        >>> bot1.start()
        >>> 
        >>> # Ejecutar ciclo
        >>> def my_trading_cycle():
        ...     # Lógica del bot
        ...     pass
        >>> 
        >>> bot1.execute_cycle(my_trading_cycle)
        >>> 
        >>> # Detener bot
        >>> bot1.stop()
    """
    
    def __init__(
        self,
        config: BotConfig,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa una instancia de bot.
        
        Args:
            config: Configuración del bot
            logger: Logger opcional (se crea uno por defecto si no se proporciona)
        """
        self.config = config
        self.bot_id = config.bot_id
        self.bot_name = config.bot_name
        
        # Estado del bot
        self.state = BotState(bot_id=self.bot_id)
        
        # Logger específico para este bot
        if logger is None:
            self.logger = logging.getLogger(f"BotInstance.{self.bot_name}")
            self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger
        
        self.logger.info(
            f"Inicializando bot {self.bot_name} (ID: {self.bot_id})"
        )
        
        # Inicializar componentes
        self._initialize_components()
        
        self.logger.info(
            f"Bot {self.bot_name} inicializado correctamente"
        )
    
    def _initialize_components(self) -> None:
        """
        Inicializa los componentes del bot.
        
        Cada bot tiene sus propios componentes aislados:
        - TimeValidator: Para validaciones de horario
        - CycleScheduler: Para programación de ciclos
        - MT5Connector: Para conexión a MetaTrader 5
        """
        # TimeValidator con configuración propia
        self.time_validator = TimeValidator(
            config=self.config.schedule_config
        )
        
        # CycleScheduler con configuración propia
        self.cycle_scheduler = CycleScheduler(
            time_validator=self.time_validator,
            config=self.config.cycle_config,
            logger=self.logger,
            bot_name=self.bot_name
        )
        
        # MT5Connector con configuración propia
        broker_config = BrokerConfig(
            account_id=self.config.mt5_config.get("account_id", ""),
            password=self.config.mt5_config.get("password", ""),
            server=self.config.mt5_config.get("server", ""),
            timeout=self.config.mt5_config.get("timeout", 60)
        )
        
        self.mt5_connector = MT5Connector(
            config=broker_config,
            logger=self.logger
        )
        
        self.logger.debug("Componentes del bot inicializados")
    
    # ==================== LIFECYCLE MANAGEMENT ====================
    
    def start(self) -> bool:
        """
        Inicia el bot.
        
        Pasos:
        1. Verifica que el bot esté habilitado
        2. Verifica que no esté ya corriendo
        3. Conecta a MT5
        4. Transiciona a estado RUNNING
        
        Returns:
            True si el inicio fue exitoso, False en caso contrario
        """
        # Verificar que esté habilitado
        if not self.config.enabled:
            self.logger.warning(
                f"Bot {self.bot_name} está deshabilitado en configuración"
            )
            return False
        
        # Verificar que no esté ya corriendo
        if self.state.status == BotStatus.RUNNING:
            self.logger.warning(
                f"Bot {self.bot_name} ya está en ejecución"
            )
            return False
        
        self.logger.info(f"Iniciando bot {self.bot_name}...")
        self.state.transition_to(BotStatus.STARTING)
        
        try:
            # Conectar a MT5
            if not self.mt5_connector.verify_connection():
                error_msg = "No se pudo establecer conexión con MT5"
                self.logger.error(error_msg)
                self.state.transition_to(BotStatus.ERROR, error_message=error_msg)
                return False
            
            # Transicionar a RUNNING
            self.state.transition_to(BotStatus.RUNNING)
            
            self.logger.info(
                f"Bot {self.bot_name} iniciado exitosamente"
            )
            
            return True
        
        except Exception as e:
            error_msg = f"Error al iniciar bot: {e}"
            self.logger.error(error_msg)
            self.state.transition_to(BotStatus.ERROR, error_message=error_msg)
            return False
    
    def stop(self) -> bool:
        """
        Detiene el bot.
        
        Pasos:
        1. Verifica que esté corriendo
        2. Desconecta de MT5
        3. Transiciona a estado STOPPED
        
        Returns:
            True si la detención fue exitosa, False en caso contrario
        """
        if self.state.status != BotStatus.RUNNING:
            self.logger.warning(
                f"Bot {self.bot_name} no está en ejecución"
            )
            return False
        
        self.logger.info(f"Deteniendo bot {self.bot_name}...")
        self.state.transition_to(BotStatus.STOPPING)
        
        try:
            # Desconectar de MT5
            self.mt5_connector.disconnect()
            
            # Transicionar a STOPPED
            self.state.transition_to(BotStatus.STOPPED)
            
            self.logger.info(
                f"Bot {self.bot_name} detenido exitosamente"
            )
            
            return True
        
        except Exception as e:
            error_msg = f"Error al detener bot: {e}"
            self.logger.error(error_msg)
            self.state.transition_to(BotStatus.ERROR, error_message=error_msg)
            return False
    
    def is_running(self) -> bool:
        """
        Verifica si el bot está en ejecución.
        
        Returns:
            True si está corriendo, False en caso contrario
        """
        return self.state.status == BotStatus.RUNNING
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado completo del bot.
        
        Returns:
            Diccionario con información del estado
        """
        status = self.state.to_dict()
        status["bot_name"] = self.bot_name
        status["enabled"] = self.config.enabled
        
        return status
    
    # ==================== EJECUCIÓN DE CICLOS ====================
    
    def execute_cycle(self, cycle_callback: Callable[[], None]) -> None:
        """
        Ejecuta un ciclo de trading.
        
        Args:
            cycle_callback: Función que implementa la lógica del ciclo
        
        Raises:
            BotStateError: Si el bot no está en estado RUNNING
            Exception: Si hay error en la ejecución del ciclo
        """
        if self.state.status != BotStatus.RUNNING:
            raise BotStateError(
                f"Bot debe estar en estado RUNNING para ejecutar ciclos. "
                f"Estado actual: {self.state.status.value}"
            )
        
        self.logger.info(
            f"Ejecutando ciclo #{self.state.cycles_completed + 1} "
            f"para bot {self.bot_name}"
        )
        
        try:
            # Ejecutar el callback del ciclo
            cycle_callback()
            
            # Incrementar contador de ciclos
            self.state.increment_cycle()
            
            self.logger.info(
                f"Ciclo #{self.state.cycles_completed} completado exitosamente"
            )
        
        except Exception as e:
            error_msg = f"Error en ciclo: {e}"
            self.logger.error(error_msg)
            self.state.transition_to(BotStatus.ERROR, error_message=error_msg)
            raise
    
    # ==================== REPRESENTACIÓN ====================
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        return (
            f"<BotInstance(id={self.bot_id}, name='{self.bot_name}', "
            f"status={self.state.status.value})>"
        )
    
    def __str__(self) -> str:
        """Representación en string"""
        return (
            f"Bot {self.bot_name} (ID: {self.bot_id})\n"
            f"  Estado: {self.state.status.value}\n"
            f"  Habilitado: {self.config.enabled}\n"
            f"  Ciclos completados: {self.state.cycles_completed}"
        )
