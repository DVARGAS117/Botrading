"""
Módulo de monitoreo de salud para bots del sistema Botrading.

Este módulo implementa el Ticket T43: Monitoreo de estado y logs de cada bot,
permitiendo monitorear logs y detectar anomalías operativas en tiempo real.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T43 - Monitoreo de estado y logs de cada bot
"""
import re
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class BotHealthStatus:
    """
    Estado de salud de un bot individual.

    Attributes:
        bot_name: Nombre del bot
        is_active: Si el bot está activo (logs recientes)
        last_log_time: Timestamp del último log
        error_count: Número de errores recientes
        recent_errors: Lista de mensajes de error recientes
    """
    bot_name: str
    is_active: bool
    last_log_time: Optional[datetime]
    error_count: int
    recent_errors: List[str]


@dataclass
class HealthAnomaly:
    """
    Anomalía detectada en la salud de un bot.

    Attributes:
        bot_name: Nombre del bot
        anomaly_type: Tipo de anomalía ('inactive', 'errors', etc.)
        message: Descripción de la anomalía
        timestamp: Cuando se detectó
    """
    bot_name: str
    anomaly_type: str
    message: str
    timestamp: datetime


class HealthMonitor:
    """
    Monitor de salud para bots del sistema Botrading.

    Monitorea logs de bots para detectar:
    - Bots inactivos (sin logs recientes)
    - Errores y anomalías en logs
    - Estado general de salud

    Attributes:
        logs_dir: Directorio donde se almacenan los logs
        max_age_hours: Horas máximas para considerar logs como recientes
    """

    # Patrón regex para parsear líneas de log
    LOG_PATTERN = re.compile(
        r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[([^\]]+)\] \[([^\]]+)\] (.+)$'
    )

    def __init__(self, logs_dir: Path, max_age_hours: int = 2):
        """
        Inicializa el monitor de salud.

        Args:
            logs_dir: Directorio de logs
            max_age_hours: Horas para considerar logs recientes
        """
        self.logs_dir = logs_dir
        self.max_age_hours = max_age_hours

    def get_bot_status(self, bot_name: str) -> BotHealthStatus:
        """
        Obtiene el estado de salud de un bot específico.

        Args:
            bot_name: Nombre del bot

        Returns:
            Estado de salud del bot
        """
        log_files = self._get_bot_log_files(bot_name)
        all_logs = self._parse_all_logs(log_files)
        recent_logs = [log for log in all_logs if self._is_recent_log(log['timestamp'])]

        if not all_logs:
            return BotHealthStatus(
                bot_name=bot_name,
                is_active=False,
                last_log_time=None,
                error_count=0,
                recent_errors=[]
            )

        last_log_time = max(log['timestamp'] for log in all_logs)
        errors = [log for log in recent_logs if log['level'] in ['ERROR', 'CRITICAL']]
        recent_errors = [error['message'] for error in errors]

        return BotHealthStatus(
            bot_name=bot_name,
            is_active=len(recent_logs) > 0,
            last_log_time=last_log_time,
            error_count=len(errors),
            recent_errors=recent_errors
        )

    def get_all_bots_status(self) -> Dict[str, BotHealthStatus]:
        """
        Obtiene el estado de salud de todos los bots.

        Returns:
            Diccionario con estados de todos los bots encontrados
        """
        bot_names = self._discover_bot_names()
        return {bot: self.get_bot_status(bot) for bot in bot_names}

    def check_anomalies(self) -> List[HealthAnomaly]:
        """
        Verifica anomalías en todos los bots.

        Returns:
            Lista de anomalías detectadas
        """
        anomalies = []
        all_status = self.get_all_bots_status()

        for bot_name, status in all_status.items():
            # Verificar bots inactivos
            if not status.is_active:
                anomalies.append(HealthAnomaly(
                    bot_name=bot_name,
                    anomaly_type='inactive',
                    message=f'Bot inactivo - último log: {status.last_log_time}',
                    timestamp=datetime.now()
                ))

            # Verificar errores recientes
            if status.error_count > 0:
                anomalies.append(HealthAnomaly(
                    bot_name=bot_name,
                    anomaly_type='errors',
                    message=f'{status.error_count} errores recientes: {"; ".join(status.recent_errors[:3])}',
                    timestamp=datetime.now()
                ))

        return anomalies

    def _get_bot_log_files(self, bot_name: str) -> List[Path]:
        """
        Obtiene archivos de log para un bot.

        Args:
            bot_name: Nombre del bot

        Returns:
            Lista de archivos de log
        """
        if not self.logs_dir.exists():
            return []

        pattern = f"{bot_name}_*.log"
        return list(self.logs_dir.glob(pattern))

    def _parse_all_logs(self, log_files: List[Path]) -> List[Dict[str, Any]]:
        """
        Parsea todos los logs de archivos.

        Args:
            log_files: Lista de archivos de log

        Returns:
            Lista de logs parseados
        """
        all_logs = []

        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parsed = self._parse_log_line(line.strip())
                        if parsed:
                            all_logs.append(parsed)
            except Exception:
                # Ignorar errores de lectura
                continue

        return all_logs

    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parsea una línea de log.

        Args:
            line: Línea de log

        Returns:
            Diccionario con datos parseados o None si inválida
        """
        match = self.LOG_PATTERN.match(line)
        if not match:
            return None

        timestamp_str, bot_name, level, message = match.groups()

        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

        return {
            'timestamp': timestamp,
            'bot_name': bot_name,
            'level': level,
            'message': message
        }

    def _is_recent_log(self, timestamp: datetime) -> bool:
        """
        Verifica si un timestamp es reciente.

        Args:
            timestamp: Timestamp a verificar

        Returns:
            True si es reciente
        """
        max_age = timedelta(hours=self.max_age_hours)
        return datetime.now() - timestamp <= max_age

    def _discover_bot_names(self) -> List[str]:
        """
        Descubre nombres de bots desde archivos de log.

        Returns:
            Lista de nombres de bots
        """
        if not self.logs_dir.exists():
            return []

        bot_names = set()
        for path in self.logs_dir.iterdir():
            if path.is_file() and path.suffix == '.log':
                match = re.match(r'^(.+)_\d{8}\.log$', path.name)
                if match:
                    bot_names.add(match.group(1))

        return list(bot_names)