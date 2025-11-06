"""
Módulo de logging estructurado para el sistema Botrading.

Este módulo implementa la funcionalidad del Ticket T39: Logging por bot y nivel,
permitiendo logs estructurados con información de bot, nivel, timestamp y mensaje
para facilitar diagnósticos y trazabilidad.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T39 - Logging por bot y nivel
"""
import os
import json
import logging
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import TimedRotatingFileHandler


class LogLevel(Enum):
    """Niveles de logging soportados"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LoggerError(Exception):
    """Excepción personalizada para errores del logger"""
    pass


class LogConfig:
    """
    Configuración para el logger.
    
    Attributes:
        level: Nivel mínimo de logging
        log_dir: Directorio para archivos de log
        log_to_console: Si debe mostrar logs en consola
        log_to_file: Si debe guardar logs en archivo
        format_json: Si debe formatear logs en JSON
        max_bytes: Tamaño máximo por archivo (para rotación)
        backup_count: Número de archivos de backup a mantener
    """
    
    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        log_dir: str = "logs",
        log_to_console: bool = True,
        log_to_file: bool = True,
        format_json: bool = False,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ):
        """
        Inicializa la configuración del logger.
        
        Args:
            level: Nivel mínimo de logging
            log_dir: Directorio para archivos de log
            log_to_console: Si debe mostrar logs en consola
            log_to_file: Si debe guardar logs en archivo
            format_json: Si debe formatear logs en JSON
            max_bytes: Tamaño máximo por archivo
            backup_count: Número de archivos de backup
        """
        self.level = level
        self.log_dir = log_dir
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        self.format_json = format_json
        self.max_bytes = max_bytes
        self.backup_count = backup_count


class JSONFormatter(logging.Formatter):
    """Formateador personalizado para logs en formato JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro de log en JSON.
        
        Args:
            record: Registro de logging a formatear
            
        Returns:
            String JSON con el log formateado
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "bot": getattr(record, 'bot_name', 'unknown'),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Agregar datos extra si existen
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename',
                              'funcName', 'levelname', 'levelno', 'lineno',
                              'module', 'msecs', 'pathname', 'process',
                              'processName', 'relativeCreated', 'thread',
                              'threadName', 'exc_info', 'exc_text', 'stack_info',
                              'bot_name']:
                    log_data[key] = value
        
        # Agregar traceback si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class BotFormatter(logging.Formatter):
    """Formateador personalizado para logs de bot"""
    
    def __init__(self, bot_name: str):
        """
        Inicializa el formateador.
        
        Args:
            bot_name: Nombre del bot
        """
        super().__init__()
        self.bot_name = bot_name
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro de log con información del bot.
        
        Args:
            record: Registro de logging a formatear
            
        Returns:
            String con el log formateado
        """
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        
        log_line = (
            f"[{timestamp}] "
            f"[{self.bot_name}] "
            f"[{record.levelname}] "
            f"{record.getMessage()}"
        )
        
        # Agregar traceback si existe
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)
        
        return log_line


class BotLogger:
    """
    Logger estructurado para bots del sistema Botrading.
    
    Proporciona logging con información de bot, nivel, timestamp y mensaje,
    con soporte para consola, archivo y formato JSON.
    
    Attributes:
        bot_name: Nombre del bot
        logger: Instancia del logger de Python
        config: Configuración del logger
    
    Example:
        >>> config = LogConfig(level=LogLevel.INFO)
        >>> logger = BotLogger("bot_1", config)
        >>> logger.info("Bot iniciado")
        >>> logger.error("Error en operación", extra={"symbol": "EURUSD"})
    """
    
    def __init__(self, bot_name: str, config: Optional[LogConfig] = None):
        """
        Inicializa el logger para un bot específico.
        
        Args:
            bot_name: Nombre del bot
            config: Configuración del logger (opcional)
            
        Raises:
            LoggerError: Si hay error al configurar el logger
        """
        self.bot_name = bot_name
        self.config = config or LogConfig()
        
        # Crear logger con nombre único
        self.logger = logging.getLogger(f"botrading.{bot_name}")
        self.logger.setLevel(self.config.level.value)
        
        # Limpiar handlers existentes
        self.logger.handlers.clear()
        
        # Configurar handlers
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Configura los handlers del logger según la configuración"""
        try:
            # Handler para consola
            if self.config.log_to_console:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(self.config.level.value)
                
                if self.config.format_json:
                    console_handler.setFormatter(JSONFormatter())
                else:
                    console_handler.setFormatter(BotFormatter(self.bot_name))
                
                self.logger.addHandler(console_handler)
            
            # Handler para archivo
            if self.config.log_to_file:
                self._setup_file_handler()
                
        except Exception as e:
            raise LoggerError(f"Error al configurar handlers: {str(e)}")
    
    def _setup_file_handler(self) -> None:
        """Configura el handler para archivo con rotación por fecha"""
        try:
            # Crear directorio de logs si no existe
            log_dir = Path(self.config.log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Nombre del archivo con fecha
            today = datetime.now().strftime("%Y%m%d")
            log_file = log_dir / f"{self.bot_name}_{today}.log"
            
            # Crear handler con rotación diaria
            file_handler = logging.FileHandler(
                str(log_file),
                mode='a',
                encoding='utf-8'
            )
            file_handler.setLevel(self.config.level.value)
            
            if self.config.format_json:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(BotFormatter(self.bot_name))
            
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            raise LoggerError(f"Error al configurar file handler: {str(e)}")
    
    def _log(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """
        Método interno para registrar logs.
        
        Args:
            level: Nivel de logging
            message: Mensaje a registrar
            extra: Datos extra a incluir
            exc_info: Si debe incluir información de excepción
        """
        log_extra = {"bot_name": self.bot_name}
        if extra:
            log_extra.update(extra)
        
        self.logger.log(level, message, extra=log_extra, exc_info=exc_info)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra un mensaje DEBUG.
        
        Args:
            message: Mensaje a registrar
            extra: Datos extra a incluir
        """
        self._log(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra un mensaje INFO.
        
        Args:
            message: Mensaje a registrar
            extra: Datos extra a incluir
        """
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra un mensaje WARNING.
        
        Args:
            message: Mensaje a registrar
            extra: Datos extra a incluir
        """
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra un mensaje ERROR.
        
        Args:
            message: Mensaje a registrar
            extra: Datos extra a incluir
        """
        self._log(logging.ERROR, message, extra)
    
    def critical(
        self, 
        message: str, 
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra un mensaje CRITICAL.
        
        Args:
            message: Mensaje a registrar
            extra: Datos extra a incluir
        """
        self._log(logging.CRITICAL, message, extra)
    
    def exception(
        self, 
        message: str, 
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra un mensaje ERROR con traceback de excepción.
        
        Debe ser llamado dentro de un bloque except.
        
        Args:
            message: Mensaje a registrar
            extra: Datos extra a incluir
        """
        self._log(logging.ERROR, message, extra, exc_info=True)
    
    def set_level(self, level: LogLevel) -> None:
        """
        Cambia el nivel de logging dinámicamente.
        
        Args:
            level: Nuevo nivel de logging
        """
        self.config.level = level
        self.logger.setLevel(level.value)
        
        for handler in self.logger.handlers:
            handler.setLevel(level.value)
    
    def get_log_file_path(self) -> Optional[Path]:
        """
        Obtiene la ruta del archivo de log actual.
        
        Returns:
            Path del archivo de log o None si no hay archivo
        """
        if not self.config.log_to_file:
            return None
        
        today = datetime.now().strftime("%Y%m%d")
        return Path(self.config.log_dir) / f"{self.bot_name}_{today}.log"


def get_bot_logger(bot_name: str, config: Optional[LogConfig] = None) -> BotLogger:
    """
    Factory function para obtener un logger de bot.
    
    Args:
        bot_name: Nombre del bot
        config: Configuración del logger (opcional)
        
    Returns:
        Instancia de BotLogger configurada
        
    Example:
        >>> logger = get_bot_logger("bot_1")
        >>> logger.info("Bot iniciado")
    """
    return BotLogger(bot_name, config)
