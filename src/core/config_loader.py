"""
Módulo de carga de configuración para el sistema Botrading.

Este módulo implementa la funcionalidad del Ticket T44: Gestión de credenciales 
y parámetros en JSON, permitiendo cargar configuración desde archivos JSON y 
variables de entorno de forma segura.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T44 - Gestión de credenciales y parámetros en JSON
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional


# Configurar logging
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Excepción personalizada para errores de configuración"""
    pass


class ConfigLoader:
    """
    Clase para cargar y gestionar configuración desde múltiples fuentes.
    
    Permite cargar configuración desde:
    - Archivos JSON
    - Variables de entorno
    - Valores por defecto
    
    Attributes:
        _config (Dict[str, Any]): Configuración cargada en memoria
        _sensitive_keys (List[str]): Lista de claves consideradas sensibles
    """
    
    def __init__(self):
        """Inicializa el ConfigLoader con configuración vacía"""
        self._config: Dict[str, Any] = {}
        self._sensitive_keys = [
            "password", "api_key", "secret", "token", 
            "credentials", "key", "pass"
        ]
    
    def load_json_config(self, file_path: str) -> Dict[str, Any]:
        """
        Carga configuración desde un archivo JSON.
        
        Args:
            file_path: Ruta al archivo JSON de configuración
            
        Returns:
            Diccionario con la configuración cargada
            
        Raises:
            ConfigurationError: Si el archivo no existe o el JSON es inválido
            
        Example:
            >>> loader = ConfigLoader()
            >>> config = loader.load_json_config("config/settings.json")
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise ConfigurationError(
                    f"Configuration file not found: {file_path}"
                )
            
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Actualizar configuración interna
            self._config.update(config_data)
            
            # Log sin exponer datos sensibles
            self._log_config_loaded(file_path, config_data)
            
            return config_data
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file {file_path}: {str(e)}"
            )
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(
                f"Error loading configuration from {file_path}: {str(e)}"
            )
    
    def load_env_variables(self, required_vars: List[str]) -> Dict[str, str]:
        """
        Carga variables de entorno requeridas.
        
        Args:
            required_vars: Lista de nombres de variables de entorno requeridas
            
        Returns:
            Diccionario con las variables de entorno cargadas
            
        Raises:
            ConfigurationError: Si falta alguna variable requerida
            
        Example:
            >>> loader = ConfigLoader()
            >>> env_vars = loader.load_env_variables(["MT5_ACCOUNT_ID", "GEMINI_API_KEY"])
        """
        env_config = {}
        missing_vars = []
        
        for var_name in required_vars:
            value = os.getenv(var_name)
            if value is None:
                missing_vars.append(var_name)
            else:
                env_config[var_name] = value
        
        if missing_vars:
            raise ConfigurationError(
                f"Required environment variables not found: {', '.join(missing_vars)}"
            )
        
        # Actualizar configuración interna
        self._config.update(env_config)
        
        logger.info(f"Loaded {len(env_config)} environment variables")
        
        return env_config
    
    def get_config_value(
        self, 
        key_path: str, 
        default: Optional[Any] = None
    ) -> Any:
        """
        Obtiene un valor de configuración usando notación de punto.
        
        Args:
            key_path: Ruta a la clave (ej: "trading_window.start")
            default: Valor por defecto si la clave no existe
            
        Returns:
            El valor de configuración o el valor por defecto
            
        Raises:
            ConfigurationError: Si la clave no existe y no hay valor por defecto
            
        Example:
            >>> loader = ConfigLoader()
            >>> start_time = loader.get_config_value("trading_window.start")
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise ConfigurationError(
                f"Configuration key not found: {key_path}"
            )
    
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
            >>> loader = ConfigLoader()
            >>> loader.validate_required_keys(["timezone", "trading_window.start"])
        """
        missing_keys = []
        
        for key in required_keys:
            try:
                self.get_config_value(key)
            except ConfigurationError:
                missing_keys.append(key)
        
        if missing_keys:
            raise ConfigurationError(
                f"Required configuration keys missing: {', '.join(missing_keys)}"
            )
        
        return True
    
    def merge_configs(
        self, 
        config1: Dict[str, Any], 
        config2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fusiona dos diccionarios de configuración.
        
        Los valores de config2 tienen prioridad sobre config1.
        
        Args:
            config1: Primer diccionario de configuración
            config2: Segundo diccionario (tiene prioridad)
            
        Returns:
            Diccionario fusionado
            
        Example:
            >>> loader = ConfigLoader()
            >>> merged = loader.merge_configs(default_config, user_config)
        """
        merged = config1.copy()
        merged.update(config2)
        
        # Actualizar configuración interna
        self._config = merged
        
        return merged
    
    def _log_config_loaded(
        self, 
        file_path: str, 
        config_data: Dict[str, Any]
    ) -> None:
        """
        Registra en log la carga de configuración sin exponer datos sensibles.
        
        Args:
            file_path: Ruta del archivo cargado
            config_data: Datos de configuración
        """
        # Crear una copia segura para el log
        safe_config = self._sanitize_for_logging(config_data)
        
        logger.info(
            f"Configuration loaded from {file_path}. "
            f"Keys: {list(safe_config.keys())}"
        )
    
    def _sanitize_for_logging(self, data: Any, path: str = "") -> Any:
        """
        Sanitiza datos recursivamente para logging seguro.
        
        Reemplaza valores sensibles con '***' para evitar exposición en logs.
        
        Args:
            data: Datos a sanitizar
            path: Ruta actual en la estructura (para recursión)
            
        Returns:
            Datos sanitizados
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                # Verificar si la clave es sensible
                if any(sensitive in key.lower() for sensitive in self._sensitive_keys):
                    sanitized[key] = "***"
                else:
                    sanitized[key] = self._sanitize_for_logging(value, current_path)
            return sanitized
        
        elif isinstance(data, list):
            return [self._sanitize_for_logging(item, path) for item in data]
        
        else:
            return data
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Obtiene toda la configuración cargada.
        
        Returns:
            Diccionario completo de configuración
        """
        return self._config.copy()
    
    def clear_config(self) -> None:
        """Limpia toda la configuración cargada"""
        self._config = {}
        logger.info("Configuration cleared")
