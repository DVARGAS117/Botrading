"""
ReevaluationScheduler - T26
Gestión de intervalos de reevaluación periódica de posiciones

Este módulo implementa el scheduler que controla cuándo deben reevaluarse
las posiciones abiertas, respetando intervalos configurables y ventanas
de trading.

Características:
- Intervalos configurables (default 10 minutos)
- Respeto de ventana de trading (06:00-13:00 Lima)
- Verificación de días laborables
- Seguimiento independiente por posición
- Soporte para modo habilitado/deshabilitado
- Estadísticas de reevaluación

Tickets relacionados: T26, T4 (verificación de operaciones)

Author: Botrading Team
Date: 2025-11-13
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, time
from typing import Dict, Optional, Callable
import asyncio
import logging
import pytz


class ReevaluationSchedulerError(Exception):
    """Excepción personalizada para errores del scheduler"""
    pass


@dataclass
class ReevaluationConfig:
    """
    Configuración del scheduler de reevaluación
    
    Atributos:
        interval_minutes: Intervalo entre reevaluaciones en minutos (default 10)
        enabled: Si el scheduler está habilitado (default True)
        timezone: Zona horaria para ventana de trading (default America/Lima)
        trading_window_start: Hora de inicio de trading HH:MM (default 06:00)
        trading_window_end: Hora de fin de trading HH:MM (default 13:00)
    """
    interval_minutes: int = 10
    enabled: bool = True
    timezone: str = "America/Lima"
    trading_window_start: str = "06:00"
    trading_window_end: str = "13:00"
    
    def __post_init__(self):
        """Valida los parámetros después de la inicialización"""
        if self.interval_minutes <= 0:
            raise ValueError("interval_minutes debe ser positivo")
        
        if self.interval_minutes > 60:
            raise ValueError("interval_minutes no puede exceder 60")
        
        # Validar formato de horas
        try:
            time.fromisoformat(self.trading_window_start)
            time.fromisoformat(self.trading_window_end)
        except ValueError:
            raise ValueError("Formato de hora inválido. Usar HH:MM")
    
    def to_dict(self) -> Dict:
        """Convierte la configuración a diccionario"""
        return asdict(self)


class ReevaluationScheduler:
    """
    Gestiona el scheduling de reevaluaciones periódicas
    
    Este scheduler controla cuándo deben reevaluarse las posiciones abiertas,
    manteniendo un registro independiente por posición y respetando las
    ventanas de trading configuradas.
    
    Uso básico:
        >>> config = ReevaluationConfig(interval_minutes=10)
        >>> scheduler = ReevaluationScheduler(config)
        >>> 
        >>> # Verificar si debe reevaluar
        >>> if scheduler.should_reevaluate("position_123"):
        >>>     # Realizar reevaluación
        >>>     scheduler.mark_reevaluated("position_123")
    """
    
    def __init__(self, config: ReevaluationConfig):
        """
        Inicializa el scheduler
        
        Args:
            config: Configuración del scheduler
        """
        self.config = config
        self.last_reevaluation: Dict[str, datetime] = {}
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # Configurar timezone
        try:
            self.tz = pytz.timezone(config.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            logging.warning(
                f"Timezone desconocido: {config.timezone}. Usando UTC."
            )
            self.tz = pytz.UTC
        
        # Parsear horas de trading
        self.trading_start = time.fromisoformat(config.trading_window_start)
        self.trading_end = time.fromisoformat(config.trading_window_end)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"ReevaluationScheduler inicializado: "
            f"intervalo={config.interval_minutes}min, "
            f"enabled={config.enabled}"
        )
    
    def should_reevaluate(self, position_id: str) -> bool:
        """
        Determina si una posición debe reevaluarse
        
        Args:
            position_id: ID de la posición
            
        Returns:
            True si debe reevaluarse, False en caso contrario
            
        Condiciones para reevaluar:
        1. Scheduler debe estar habilitado
        2. Debe estar dentro de ventana de trading
        3. Es la primera reevaluación O ha pasado el intervalo configurado
        """
        # Si está deshabilitado, nunca reevaluar
        if not self.config.enabled:
            return False
        
        # Verificar ventana de trading
        if not self.is_within_trading_window():
            return False
        
        # Si es la primera vez, siempre reevaluar
        if position_id not in self.last_reevaluation:
            return True
        
        # Verificar si ha pasado el intervalo
        elapsed = self._get_elapsed_time(position_id)
        interval = timedelta(minutes=self.config.interval_minutes)
        
        return elapsed >= interval
    
    def mark_reevaluated(self, position_id: str):
        """
        Marca una posición como reevaluada ahora
        
        Args:
            position_id: ID de la posición
        """
        self.last_reevaluation[position_id] = datetime.now()
        
        self.logger.debug(
            f"Posición {position_id} marcada como reevaluada"
        )
    
    def get_last_reevaluation(self, position_id: str) -> Optional[datetime]:
        """
        Obtiene el timestamp de la última reevaluación
        
        Args:
            position_id: ID de la posición
            
        Returns:
            Datetime de última reevaluación o None si nunca fue reevaluada
        """
        return self.last_reevaluation.get(position_id)
    
    def get_time_since_last_reevaluation(
        self,
        position_id: str
    ) -> Optional[timedelta]:
        """
        Calcula tiempo transcurrido desde última reevaluación
        
        Args:
            position_id: ID de la posición
            
        Returns:
            Timedelta desde última reevaluación o None si nunca fue reevaluada
        """
        last = self.get_last_reevaluation(position_id)
        
        if last is None:
            return None
        
        return datetime.now() - last
    
    def _get_elapsed_time(self, position_id: str) -> timedelta:
        """
        Obtiene tiempo transcurrido (privado, asume que existe)
        
        Args:
            position_id: ID de la posición
            
        Returns:
            Timedelta desde última reevaluación
        """
        last = self.last_reevaluation[position_id]
        return datetime.now() - last
    
    def is_within_trading_window(self) -> bool:
        """
        Verifica si la hora actual está dentro de la ventana de trading
        
        Returns:
            True si está dentro de ventana y es día laborable
        """
        # Obtener hora actual en timezone configurado
        now = datetime.now(self.tz)
        
        # Verificar día laborable (lunes=0, domingo=6)
        if not self._is_trading_day(now):
            return False
        
        # Verificar hora
        current_time = now.time()
        
        return self.trading_start <= current_time <= self.trading_end
    
    def _is_trading_day(self, dt: datetime) -> bool:
        """
        Verifica si es día laborable (lunes a viernes)
        
        Args:
            dt: Datetime a verificar
            
        Returns:
            True si es lunes-viernes
        """
        # weekday: 0=lunes, 6=domingo
        return dt.weekday() < 5  # 0-4 son lunes-viernes
    
    def reset_position(self, position_id: str):
        """
        Limpia el registro de una posición
        
        Args:
            position_id: ID de la posición
            
        Útil cuando se cierra una posición para limpiar su historial
        """
        if position_id in self.last_reevaluation:
            del self.last_reevaluation[position_id]
            
            self.logger.debug(
                f"Registro de posición {position_id} limpiado"
            )
    
    def reset_all(self):
        """Limpia todos los registros de reevaluación"""
        self.last_reevaluation.clear()
        self.logger.info("Todos los registros de reevaluación limpiados")
    
    async def start(self, callback: Callable):
        """
        Inicia el scheduler con callback periódico
        
        Args:
            callback: Función async a llamar en cada intervalo
            
        El scheduler ejecutará el callback cada `interval_minutes` minutos
        mientras esté dentro de la ventana de trading.
        """
        if self.is_running:
            raise ReevaluationSchedulerError(
                "Scheduler ya está en ejecución"
            )
        
        self.is_running = True
        self.logger.info("Scheduler iniciado")
        
        try:
            while self.is_running:
                # Verificar si estamos en ventana de trading
                if self.is_within_trading_window():
                    try:
                        await callback()
                    except Exception as e:
                        self.logger.error(
                            f"Error en callback de reevaluación: {e}",
                            exc_info=True
                        )
                else:
                    self.logger.debug(
                        "Fuera de ventana de trading, omitiendo reevaluación"
                    )
                
                # Esperar intervalo configurado
                await asyncio.sleep(self.config.interval_minutes * 60)
                
        except asyncio.CancelledError:
            self.logger.info("Scheduler cancelado")
            raise
        finally:
            self.is_running = False
    
    def stop(self):
        """Detiene el scheduler"""
        if self.is_running:
            self.is_running = False
            self.logger.info("Scheduler detenido")
        
        if self._task and not self._task.done():
            self._task.cancel()
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del scheduler
        
        Returns:
            Diccionario con estadísticas actuales
        """
        return {
            'enabled': self.config.enabled,
            'interval_minutes': self.config.interval_minutes,
            'total_positions': len(self.last_reevaluation),
            'is_running': self.is_running,
            'in_trading_window': self.is_within_trading_window(),
            'timezone': self.config.timezone
        }
