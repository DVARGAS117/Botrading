"""
CycleScheduler - T1: Ejecución de ciclo por bot a inicio de hora

Este módulo implementa el scheduler que ejecuta ciclos de trading exactamente
al inicio de cada hora dentro de la ventana de trading 06:00-13:00 Lima,
con un ligero retraso para asegurar que las velas estén cerradas.
"""

import time
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass

from src.core.time_validator import TimeValidator


@dataclass
class SchedulerStatus:
    """Estado actual del scheduler"""
    enabled: bool
    start_delay_seconds: int
    check_interval_seconds: int
    max_wait_hours: int
    is_trading_time_valid: bool
    trading_time_reason: str
    current_time: datetime
    seconds_until_next_hour: int


class CycleScheduler:
    """
    Scheduler para ejecutar ciclos de trading al inicio de cada hora.

    Responsabilidades:
    - Esperar hasta el inicio de la próxima hora (HH:00)
    - Validar condiciones de trading (horario, día hábil)
    - Aplicar retraso configurable para asegurar velas cerradas
    - Ejecutar callback del ciclo de trading
    - Manejar timeouts y errores gracefully
    """

    def __init__(self, time_validator: TimeValidator, config: Dict[str, Any]):
        """
        Inicializa el CycleScheduler.

        Args:
            time_validator: Instancia de TimeValidator para validaciones de tiempo
            config: Configuración del scheduler
        """
        self.time_validator = time_validator
        self.config = config.get('cycle_scheduler', {})

        # Configuración con valores por defecto
        self.enabled = self.config.get('enabled', True)
        self.start_delay_seconds = self.config.get('start_delay_seconds', 3)
        self.check_interval_seconds = self.config.get('check_interval_seconds', 60)
        self.max_wait_hours = self.config.get('max_wait_hours', 8)

        # Validar configuración
        self._validate_config()

    def _validate_config(self) -> None:
        """Valida la configuración del scheduler."""
        if self.start_delay_seconds < 0:
            raise ValueError("start_delay_seconds must be non-negative")

        if self.check_interval_seconds <= 0:
            raise ValueError("check_interval_seconds must be positive")

        if self.max_wait_hours <= 0 or self.max_wait_hours > 24:
            raise ValueError("max_wait_hours must be between 1 and 24")

    def should_start_cycle(self) -> bool:
        """
        Determina si se debe iniciar un ciclo en este momento.

        Returns:
            True si se debe iniciar el ciclo, False en caso contrario
        """
        if not self.enabled:
            return False

        # Verificar que sea hora de trading
        validation = self.time_validator.is_trading_time()
        if not validation.is_valid:
            return False

        # Verificar que sea exactamente el inicio de la hora (HH:00)
        current_time = datetime.now()
        return current_time.minute == 0 and current_time.second == 0

    def wait_for_cycle_start(self) -> bool:
        """
        Espera hasta que sea momento de iniciar un ciclo.

        Returns:
            True si se alcanzó el momento de inicio, False si timeout
        """
        if not self.enabled:
            return False

        start_time = time.time()
        max_wait_seconds = self.max_wait_hours * 3600

        while time.time() - start_time < max_wait_seconds:
            if self.should_start_cycle():
                # Aplicar retraso para asegurar velas cerradas
                time.sleep(self.start_delay_seconds)
                return True

            # Esperar antes de verificar nuevamente
            time.sleep(self.check_interval_seconds)

        # Timeout alcanzado
        return False

    def run_cycle(self, cycle_callback: Callable[[], None]) -> None:
        """
        Ejecuta el ciclo de trading cuando las condiciones sean apropiadas.

        Args:
            cycle_callback: Función a ejecutar cuando sea momento del ciclo
        """
        if not self.enabled:
            return

        if self.wait_for_cycle_start():
            try:
                cycle_callback()
            except Exception as e:
                # Log error pero no detener el scheduler
                print(f"Error executing cycle: {e}")
                # TODO: Integrar con logger cuando esté disponible

    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del scheduler.

        Returns:
            Diccionario con información del estado
        """
        validation = self.time_validator.is_trading_time()

        return {
            'enabled': self.enabled,
            'start_delay_seconds': self.start_delay_seconds,
            'check_interval_seconds': self.check_interval_seconds,
            'max_wait_hours': self.max_wait_hours,
            'is_trading_time_valid': validation.is_valid,
            'trading_time_reason': validation.reason if validation.reason else "",
            'current_time': datetime.now(),
            'seconds_until_next_hour': self._calculate_seconds_until_next_hour()
        }

    def _calculate_seconds_until_next_hour(self) -> int:
        """
        Calcula los segundos hasta el próximo inicio de hora.

        Returns:
            Segundos hasta HH:00
        """
        now = datetime.now()
        # Redondear al inicio de la hora actual
        current_hour_start = now.replace(minute=0, second=0, microsecond=0)
        
        if current_hour_start == now:
            # Ya estamos en hour start
            return 0
        else:
            # Calcular hasta el próximo hour start
            next_hour = current_hour_start + timedelta(hours=1)
            return int((next_hour - now).total_seconds())