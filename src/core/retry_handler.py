"""
Módulo de reintentos automáticos con backoff exponencial.

Este módulo implementa la funcionalidad del Ticket T38: Reintentos automáticos 
con backoff, permitiendo que las llamadas a MT5 o IA fallen temporalmente y se 
reintenten automáticamente con estrategia de backoff exponencial.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T38 - Reintentos automáticos con backoff
"""
import time
import random
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type, Dict, List


# Configurar logging
logger = logging.getLogger(__name__)


class RetryConfigError(Exception):
    """Excepción para errores de configuración de reintentos"""
    pass


class RetryExhaustedError(Exception):
    """
    Excepción lanzada cuando se agotan todos los intentos de reintento.
    
    Attributes:
        message: Mensaje de error
        last_exception: La última excepción que causó el fallo
        attempts: Número de intentos realizados
    """
    
    def __init__(
        self, 
        message: str, 
        last_exception: Exception, 
        attempts: int
    ):
        """
        Inicializa la excepción.
        
        Args:
            message: Mensaje descriptivo del error
            last_exception: Última excepción que causó el fallo
            attempts: Número de intentos realizados
        """
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


class RetryConfig:
    """
    Configuración para el mecanismo de reintentos.
    
    Attributes:
        max_attempts: Número máximo de intentos (incluye el intento inicial)
        initial_delay: Delay inicial en segundos antes del primer reintento
        max_delay: Delay máximo en segundos entre reintentos
        backoff_factor: Factor multiplicador para backoff exponencial
        exponential_base: Base para el cálculo exponencial
        jitter: Si se debe agregar jitter aleatorio al delay
        retry_on: Tupla de excepciones que deben causar reintento
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        exponential_base: int = 2,
        jitter: bool = True,
        retry_on: Optional[Tuple[Type[Exception], ...]] = None
    ):
        """
        Inicializa la configuración de reintentos.
        
        Args:
            max_attempts: Número máximo de intentos
            initial_delay: Delay inicial en segundos
            max_delay: Delay máximo en segundos
            backoff_factor: Factor de backoff
            exponential_base: Base exponencial
            jitter: Agregar jitter aleatorio
            retry_on: Tupla de excepciones para reintentar (None = todas)
            
        Raises:
            RetryConfigError: Si la configuración es inválida
        """
        # Validaciones
        if max_attempts < 1:
            raise RetryConfigError("max_attempts debe ser al menos 1")
        
        if initial_delay < 0:
            raise RetryConfigError("initial_delay debe ser positivo")
        
        if max_delay < 0:
            raise RetryConfigError("max_delay debe ser positivo")
        
        if backoff_factor <= 1:
            raise RetryConfigError("backoff_factor debe ser mayor que 1")
        
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retry_on = retry_on or (Exception,)


class RetryHandler:
    """
    Handler para ejecutar funciones con reintentos automáticos.
    
    Implementa backoff exponencial con jitter opcional y registro de intentos.
    
    Attributes:
        config: Configuración de reintentos
        _last_attempts: Lista de intentos del último execute
    
    Example:
        >>> config = RetryConfig(max_attempts=3, initial_delay=1.0)
        >>> handler = RetryHandler(config)
        >>> result = handler.execute(risky_function, arg1, arg2)
    """
    
    def __init__(self, config: RetryConfig):
        """
        Inicializa el handler de reintentos.
        
        Args:
            config: Configuración de reintentos
        """
        self.config = config
        self._last_attempts: List[Dict[str, Any]] = []
    
    def execute(
        self,
        func: Callable,
        *args,
        logger: Optional[Any] = None,
        **kwargs
    ) -> Any:
        """
        Ejecuta una función con reintentos automáticos.
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales para la función
            logger: Logger opcional para registrar intentos
            **kwargs: Argumentos nombrados para la función
            
        Returns:
            El resultado de la función si tiene éxito
            
        Raises:
            RetryExhaustedError: Si se agotan todos los intentos
            Exception: Si la excepción no debe causar reintento
        """
        self._last_attempts = []
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # Intentar ejecutar la función
                result = func(*args, **kwargs)
                
                # Registrar intento exitoso
                self._record_attempt(
                    attempt_number=attempt,
                    success=True,
                    exception=None
                )
                
                # Log de éxito si hubo reintentos previos
                if attempt > 1 and logger:
                    logger.info(
                        f"Operación exitosa después de {attempt} intentos",
                        extra={"attempts": attempt}
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Verificar si esta excepción debe causar reintento
                if not self._should_retry(e):
                    # No reintentar, lanzar inmediatamente
                    raise
                
                # Registrar intento fallido
                self._record_attempt(
                    attempt_number=attempt,
                    success=False,
                    exception=e
                )
                
                # Si es el último intento, lanzar RetryExhaustedError
                if attempt >= self.config.max_attempts:
                    error_msg = (
                        f"Agotados todos los intentos ({self.config.max_attempts}). "
                        f"Última excepción: {type(e).__name__}: {str(e)}"
                    )
                    
                    if logger:
                        logger.error(
                            error_msg,
                            extra={
                                "attempts": attempt,
                                "exception_type": type(e).__name__,
                                "exception_message": str(e)
                            }
                        )
                    
                    raise RetryExhaustedError(
                        error_msg,
                        last_exception=e,
                        attempts=attempt
                    )
                
                # Calcular delay antes del siguiente intento
                delay = self._calculate_delay(attempt)
                
                # Log del reintento
                if logger:
                    logger.warning(
                        f"Intento {attempt} falló, reintentando en {delay:.2f}s",
                        extra={
                            "attempt": attempt,
                            "delay_seconds": delay,
                            "exception_type": type(e).__name__,
                            "exception_message": str(e)
                        }
                    )
                
                # Esperar antes del siguiente intento
                time.sleep(delay)
    
    def _should_retry(self, exception: Exception) -> bool:
        """
        Determina si una excepción debe causar un reintento.
        
        Args:
            exception: La excepción a verificar
            
        Returns:
            True si se debe reintentar, False si no
        """
        return isinstance(exception, self.config.retry_on)
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calcula el delay antes del siguiente intento usando backoff exponencial.
        
        Args:
            attempt: Número de intento actual (1-indexed)
            
        Returns:
            Delay en segundos
        """
        # Backoff exponencial: initial_delay * (backoff_factor ^ (attempt - 1))
        delay = self.config.initial_delay * (
            self.config.backoff_factor ** (attempt - 1)
        )
        
        # Aplicar límite máximo
        delay = min(delay, self.config.max_delay)
        
        # Agregar jitter si está habilitado
        if self.config.jitter:
            # Jitter: ±25% del delay
            jitter_range = delay * 0.25
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay + jitter)
        
        return delay
    
    def _record_attempt(
        self,
        attempt_number: int,
        success: bool,
        exception: Optional[Exception]
    ) -> None:
        """
        Registra información sobre un intento.
        
        Args:
            attempt_number: Número del intento
            success: Si el intento fue exitoso
            exception: Excepción si el intento falló
        """
        attempt_info = {
            "attempt_number": attempt_number,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if not success and exception:
            attempt_info.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception)
            })
        
        self._last_attempts.append(attempt_info)
    
    def get_last_attempts(self) -> List[Dict[str, Any]]:
        """
        Obtiene información sobre los intentos del último execute.
        
        Returns:
            Lista de diccionarios con información de cada intento
        """
        return self._last_attempts.copy()
    
    def __enter__(self):
        """Permite usar el handler como context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Limpia recursos al salir del contexto"""
        self._last_attempts = []
        return False


def with_retry(
    config: Optional[RetryConfig] = None
) -> Callable:
    """
    Decorador para aplicar reintentos automáticos a una función.
    
    Args:
        config: Configuración de reintentos (opcional)
        
    Returns:
        Función decorada con capacidad de reintentos
        
    Example:
        >>> @with_retry(RetryConfig(max_attempts=3))
        ... def connect_to_mt5():
        ...     # código que puede fallar
        ...     pass
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = RetryHandler(config)
            return handler.execute(func, *args, **kwargs)
        
        return wrapper
    
    return decorator


# Configuraciones predefinidas para casos comunes

MT5_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    backoff_factor=2.0,
    retry_on=(ConnectionError, TimeoutError, OSError)
)
"""Configuración recomendada para operaciones con MT5"""

IA_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=2.0,
    max_delay=30.0,
    backoff_factor=2.0,
    retry_on=(ConnectionError, TimeoutError)
)
"""Configuración recomendada para consultas a IA (Gemini)"""

NETWORK_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    initial_delay=1.0,
    max_delay=60.0,
    backoff_factor=2.0,
    jitter=True,
    retry_on=(ConnectionError, TimeoutError)
)
"""Configuración recomendada para operaciones de red en general"""


# Funciones helper para casos comunes

def retry_mt5_operation(func: Callable, *args, **kwargs) -> Any:
    """
    Ejecuta una operación MT5 con reintentos automáticos.
    
    Args:
        func: Función MT5 a ejecutar
        *args: Argumentos posicionales
        **kwargs: Argumentos nombrados
        
    Returns:
        Resultado de la función
        
    Example:
        >>> result = retry_mt5_operation(mt5.connect, server="broker")
    """
    handler = RetryHandler(MT5_RETRY_CONFIG)
    return handler.execute(func, *args, **kwargs)


def retry_ia_query(func: Callable, *args, **kwargs) -> Any:
    """
    Ejecuta una consulta a IA con reintentos automáticos.
    
    Args:
        func: Función de consulta a IA
        *args: Argumentos posicionales
        **kwargs: Argumentos nombrados
        
    Returns:
        Resultado de la función
        
    Example:
        >>> result = retry_ia_query(gemini.query, prompt="Analyze EURUSD")
    """
    handler = RetryHandler(IA_RETRY_CONFIG)
    return handler.execute(func, *args, **kwargs)
