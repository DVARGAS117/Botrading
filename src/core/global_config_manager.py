"""
Módulo de gestión global de configuración para el sistema Botrading.

Este módulo implementa la funcionalidad del Ticket T05: Parámetros globales
centralizados, proporcionando acceso unificado a todas las configuraciones
del sistema (settings, schedule, credentials, etc.).

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T05 - Parámetros globales centralizados
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.core.config_loader import ConfigLoader, ConfigurationError


# Configurar logging
logger = logging.getLogger(__name__)


class GlobalConfigManager:
    """
    Gestor global de configuración que centraliza acceso a todos los parámetros.
    
    Carga y gestiona múltiples archivos de configuración:
    - settings.json: Configuración general del sistema
    - schedule.json: Horarios y calendario de trading
    - credentials.json: Credenciales de MT5 y Gemini
    - filters.json: Filtros de trading
    - ia_config.json: Configuración de IA
    
    Cumple con T05: Permite modificar parámetros en archivos JSON sin tocar código.
    
    Attributes:
        config_dir (Path): Directorio de archivos de configuración
        _loader (ConfigLoader): Loader interno para manejo de archivos
        _merged_config (Dict): Configuración fusionada de todos los archivos
    
    Example:
        >>> manager = GlobalConfigManager("config")
        >>> timezone = manager.get_value("timezone")
        >>> bot_config = manager.get_bot_config("bot_1")
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Inicializa el GlobalConfigManager cargando todos los archivos de configuración.
        
        Args:
            config_dir: Directorio donde se encuentran los archivos de configuración
            
        Raises:
            ConfigurationError: Si algún archivo requerido no existe o es inválido
        """
        self.config_dir = Path(config_dir)
        self._loader = ConfigLoader()
        self._merged_config: Dict[str, Any] = {}
        
        # Cargar todas las configuraciones
        self._load_all_configs()
        
        logger.info(f"GlobalConfigManager initialized with {len(self._merged_config)} configuration keys")
    
    def _load_all_configs(self) -> None:
        """
        Carga todos los archivos de configuración del directorio.
        
        Archivos principales:
        - settings.json: Obligatorio
        - schedule.json: Obligatorio
        - credentials.json: Obligatorio
        - filters.json: Opcional
        - ia_config.json: Opcional
        
        Raises:
            ConfigurationError: Si algún archivo obligatorio falta o es inválido
        """
        # Archivos obligatorios
        required_files = ["settings.json", "schedule.json", "credentials.json"]
        
        for filename in required_files:
            file_path = self.config_dir / filename
            if not file_path.exists():
                raise ConfigurationError(
                    f"Required configuration file not found: {file_path}"
                )
            
            config_data = self._loader.load_json_config(str(file_path))
            self._merged_config.update(config_data)
        
        # Archivos opcionales
        optional_files = ["filters.json", "ia_config.json", "quota_validation.json"]
        
        for filename in optional_files:
            file_path = self.config_dir / filename
            if file_path.exists():
                try:
                    config_data = self._loader.load_json_config(str(file_path))
                    self._merged_config.update(config_data)
                    logger.info(f"Loaded optional config: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to load optional config {filename}: {e}")
    
    def get_value(self, key_path: str, default: Optional[Any] = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de punto.
        
        Permite acceso a valores anidados de forma sencilla.
        
        Args:
            key_path: Ruta a la clave usando notación de punto (ej: "bots.bot_1.enabled")
            default: Valor por defecto si la clave no existe
            
        Returns:
            El valor de configuración o el valor por defecto
            
        Raises:
            ConfigurationError: Si la clave no existe y no hay default
            
        Example:
            >>> manager.get_value("timezone")
            'America/Lima'
            >>> manager.get_value("trading_window.start")
            '06:00'
            >>> manager.get_value("missing.key", default="N/A")
            'N/A'
        """
        return self._loader.get_config_value(key_path, default)
    
    def get_bot_config(self, bot_name: str) -> Dict[str, Any]:
        """
        Obtiene la configuración completa de un bot específico.
        
        Args:
            bot_name: Nombre del bot (ej: "bot_1", "bot_2")
            
        Returns:
            Diccionario con la configuración del bot
            
        Raises:
            ConfigurationError: Si el bot no existe en la configuración
            
        Example:
            >>> bot_config = manager.get_bot_config("bot_1")
            >>> print(bot_config["instruments"])
            ['EURUSD', 'GBPUSD']
        """
        try:
            bot_config = self.get_value(f"bots.{bot_name}")
            return bot_config
        except ConfigurationError:
            raise ConfigurationError(
                f"Bot '{bot_name}' not found in configuration"
            )
    
    def list_enabled_bots(self) -> List[str]:
        """
        Lista todos los bots que están habilitados en la configuración.
        
        Returns:
            Lista de nombres de bots habilitados
            
        Example:
            >>> manager.list_enabled_bots()
            ['bot_1', 'bot_3']
        """
        bots_config = self.get_value("bots", default={})
        
        enabled_bots = [
            bot_name 
            for bot_name, config in bots_config.items()
            if config.get("enabled", False)
        ]
        
        return enabled_bots
    
    def get_all_instruments(self) -> List[str]:
        """
        Obtiene lista única de todos los instrumentos de bots habilitados.
        
        Returns:
            Lista de instrumentos sin duplicados
            
        Example:
            >>> manager.get_all_instruments()
            ['EURUSD', 'GBPUSD', 'USDJPY']
        """
        enabled_bots = self.list_enabled_bots()
        instruments = set()
        
        for bot_name in enabled_bots:
            bot_config = self.get_bot_config(bot_name)
            bot_instruments = bot_config.get("instruments", [])
            instruments.update(bot_instruments)
        
        return sorted(list(instruments))
    
    def get_trading_window(self) -> Dict[str, Any]:
        """
        Obtiene la configuración de la ventana de trading.
        
        Returns:
            Diccionario con start, end, y opcionalmente days
            
        Example:
            >>> window = manager.get_trading_window()
            >>> print(f"{window['start']} - {window['end']}")
            '06:00 - 13:00'
        """
        return self.get_value("trading_window")
    
    def validate_required_keys(self, required_keys: List[str]) -> bool:
        """
        Valida que todas las claves requeridas existan en la configuración.
        
        Args:
            required_keys: Lista de claves requeridas (notación de punto soportada)
            
        Returns:
            True si todas las claves existen
            
        Raises:
            ConfigurationError: Si falta alguna clave requerida
            
        Example:
            >>> manager.validate_required_keys([
            ...     "timezone",
            ...     "trading_window.start",
            ...     "mt5.account_id"
            ... ])
            True
        """
        return self._loader.validate_required_keys(required_keys)
    
    def reload_config(self) -> None:
        """
        Recarga todos los archivos de configuración.
        
        Permite aplicar cambios en archivos de configuración sin reiniciar
        el sistema (cumple criterio de T05: modificar sin tocar código).
        
        Example:
            >>> # Usuario modifica config/settings.json
            >>> manager.reload_config()  # Aplica los cambios
        """
        # Limpiar configuraciones actuales
        self._loader.clear_config()
        self._merged_config = {}
        
        # Recargar todas las configuraciones
        self._load_all_configs()
        
        logger.info("Configuration reloaded successfully")
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Obtiene toda la configuración fusionada.
        
        Returns:
            Diccionario completo con toda la configuración
        """
        return self._loader.get_all_config()
