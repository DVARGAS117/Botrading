"""
Validador de tiempo para operaciones de trading.

Este módulo implementa el Ticket T35: Validación de hora local de Lima y días hábiles.
Incluye soporte para horarios configurables y buffer de tiempo para respuesta de IA.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T35 - Validación de hora local de Lima y días hábiles
"""
import json
from datetime import datetime, time, timedelta, date
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
from zoneinfo import ZoneInfo


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class TimeValidationError(Exception):
    """Excepción para errores de validación de tiempo"""
    pass


# ==================== DATACLASSES ====================

@dataclass
class ValidationResult:
    """
    Resultado de una validación de tiempo.
    
    Attributes:
        is_valid (bool): Indica si la validación fue exitosa
        reason (Optional[str]): Razón del resultado (especialmente útil en rechazos)
        timestamp (datetime): Momento en que se realizó la validación
    """
    is_valid: bool
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __bool__(self) -> bool:
        """Permite usar el resultado en contextos booleanos"""
        return self.is_valid
    
    def __repr__(self) -> str:
        """Representación string del resultado"""
        status = "VÁLIDO" if self.is_valid else "INVÁLIDO"
        return f"ValidationResult(is_valid={self.is_valid}, status={status}, reason='{self.reason}')"


# ==================== CLASE PRINCIPAL ====================

class TimeValidator:
    """
    Validador de tiempo para operaciones de trading.
    
    Funcionalidades:
    - Validación de timezone (America/Lima UTC-5)
    - Validación de días hábiles (Lunes-Viernes, excluyendo feriados)
    - Validación de horario de trading (configurable)
    - Buffer de tiempo para respuesta de IA antes del cierre
    - Cálculo de tiempo restante hasta cierre
    - Determinación de próxima sesión de trading
    
    El buffer de IA es crítico: si la IA tarda 1-2 minutos en responder,
    la última operación debe iniciar con suficiente margen antes del cierre.
    
    Ejemplo:
        end_time = 13:00
        ia_buffer = 3 minutos
        → Última operación válida: 12:57
    """
    
    # Constantes por defecto
    DEFAULT_TIMEZONE = "America/Lima"
    DEFAULT_START_TIME = "06:00"
    DEFAULT_END_TIME = "13:00"
    DEFAULT_IA_BUFFER = 3  # minutos
    DEFAULT_BUSINESS_DAYS = [1, 2, 3, 4, 5]  # Lunes a Viernes
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_file: Optional[str] = None
    ):
        """
        Inicializa el validador de tiempo.
        
        Args:
            config: Diccionario con configuración de horarios
            config_file: Ruta a archivo JSON con configuración
            
        Raises:
            TimeValidationError: Si la configuración es inválida
        """
        # Cargar configuración
        if config_file:
            config = self._load_config_from_file(config_file)
        elif config is None:
            config = self._get_default_config()
        
        # Extraer y validar configuración
        try:
            schedule = config.get("trading_schedule", {})
            
            # Timezone
            tz_str = schedule.get("timezone", self.DEFAULT_TIMEZONE)
            self.timezone = self._parse_timezone(tz_str)
            
            # Horarios de trading
            trading_hours = schedule.get("trading_hours", {})
            start_str = trading_hours.get("start_time", self.DEFAULT_START_TIME)
            end_str = trading_hours.get("end_time", self.DEFAULT_END_TIME)
            
            self.start_time = self._parse_time(start_str)
            self.end_time = self._parse_time(end_str)
            
            # Validar que end_time sea posterior a start_time
            if self.end_time <= self.start_time:
                error_msg = f"end_time ({self.end_time}) debe ser posterior a start_time ({self.start_time})"
                # Re-raise como TimeValidationError directamente (sin wrapping)
                raise TimeValidationError(error_msg) from None
            
            # Buffer de IA
            self.ia_buffer_minutes = trading_hours.get(
                "ia_response_buffer_minutes",
                self.DEFAULT_IA_BUFFER
            )
            
            # Días hábiles
            business_days_config = schedule.get("business_days", {})
            self.business_days = business_days_config.get(
                "enabled",
                self.DEFAULT_BUSINESS_DAYS
            )
            
            # Feriados
            holidays_config = schedule.get("holidays", {})
            self.holidays_enabled = holidays_config.get("enabled", True)
            self.holidays = self._parse_holidays(holidays_config.get("dates", []))
            
            # Reglas de validación
            validation_rules = config.get("validation_rules", {})
            self.strict_mode = validation_rules.get("strict_mode", True)
            self.log_rejections = validation_rules.get("log_rejections", True)
            
        except KeyError as e:
            raise TimeValidationError(f"Configuración incompleta: {e}")
        except TimeValidationError:
            # Re-raise TimeValidationError sin wrapping
            raise
        except Exception as e:
            raise TimeValidationError(f"Error procesando configuración: {e}")
    
    # ==================== MÉTODOS PRIVADOS DE CONFIGURACIÓN ====================
    
    def _load_config_from_file(self, config_file: str) -> Dict[str, Any]:
        """Carga configuración desde archivo JSON"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise TimeValidationError(f"Archivo de configuración no encontrado: {config_file}")
        except json.JSONDecodeError as e:
            raise TimeValidationError(f"Error parseando JSON: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuración por defecto"""
        return {
            "trading_schedule": {
                "timezone": self.DEFAULT_TIMEZONE,
                "trading_hours": {
                    "start_time": self.DEFAULT_START_TIME,
                    "end_time": self.DEFAULT_END_TIME,
                    "ia_response_buffer_minutes": self.DEFAULT_IA_BUFFER
                },
                "business_days": {
                    "enabled": self.DEFAULT_BUSINESS_DAYS
                },
                "holidays": {
                    "enabled": True,
                    "dates": []
                }
            },
            "validation_rules": {
                "strict_mode": True,
                "log_rejections": True
            }
        }
    
    def _parse_timezone(self, tz_str: str) -> ZoneInfo:
        """
        Parsea y valida un timezone.
        
        Args:
            tz_str: String del timezone (ej: "America/Lima")
            
        Returns:
            Objeto ZoneInfo validado
            
        Raises:
            TimeValidationError: Si el timezone es inválido
        """
        try:
            return ZoneInfo(tz_str)
        except Exception as e:
            raise TimeValidationError(f"Timezone inválido '{tz_str}': {e}")
    
    def _parse_time(self, time_str: str) -> time:
        """
        Parsea un string de hora en formato HH:MM.
        
        Args:
            time_str: String con hora (ej: "06:00", "13:30")
            
        Returns:
            Objeto time
            
        Raises:
            TimeValidationError: Si el formato es inválido
        """
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError("Formato debe ser HH:MM")
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError("Hora o minuto fuera de rango")
            
            return time(hour, minute)
            
        except Exception as e:
            raise TimeValidationError(f"Formato de hora inválido '{time_str}': {e}")
    
    def _parse_holidays(self, holiday_dates: List[str]) -> List[date]:
        """
        Parsea lista de fechas de feriados.
        
        Args:
            holiday_dates: Lista de strings en formato YYYY-MM-DD
            
        Returns:
            Lista de objetos date
        """
        holidays = []
        for date_str in holiday_dates:
            try:
                year, month, day = map(int, date_str.split("-"))
                holidays.append(date(year, month, day))
            except Exception:
                # Ignorar fechas mal formateadas
                continue
        
        return holidays
    
    # ==================== MÉTODOS PÚBLICOS DE TIEMPO ====================
    
    def get_current_lima_time(self) -> datetime:
        """
        Obtiene la hora actual en timezone de Lima.
        
        Returns:
            datetime con timezone America/Lima
        """
        return datetime.now(self.timezone)
    
    def get_current_time_only(self) -> time:
        """
        Obtiene solo la hora actual (sin fecha).
        
        Returns:
            Objeto time con hora actual
        """
        current = self.get_current_lima_time()
        return current.time()
    
    # ==================== MÉTODOS DE VALIDACIÓN ====================
    
    def is_business_day(self, check_date: Optional[datetime] = None) -> bool:
        """
        Verifica si una fecha es día hábil.
        
        Un día es hábil si:
        1. Está en la lista de días hábiles configurados (ej: Lun-Vie)
        2. NO es feriado (si holidays_enabled=True)
        
        Args:
            check_date: Fecha a verificar (None = hoy)
            
        Returns:
            True si es día hábil, False caso contrario
        """
        if check_date is None:
            check_date = self.get_current_lima_time()
        
        # Verificar día de la semana (1=Lunes, 7=Domingo en isoweekday)
        weekday = check_date.isoweekday()
        if weekday not in self.business_days:
            return False
        
        # Verificar feriados
        if self.holidays_enabled and self.is_holiday(check_date):
            return False
        
        return True
    
    def is_holiday(self, check_date: Optional[datetime] = None) -> bool:
        """
        Verifica si una fecha es feriado.
        
        Args:
            check_date: Fecha a verificar (None = hoy)
            
        Returns:
            True si es feriado, False caso contrario
        """
        if check_date is None:
            check_date = self.get_current_lima_time()
        
        check_date_only = check_date.date()
        return check_date_only in self.holidays
    
    def is_within_trading_hours(
        self,
        check_time: Optional[datetime] = None,
        consider_ia_buffer: bool = False
    ) -> bool:
        """
        Verifica si una hora está dentro del horario de trading.
        
        Args:
            check_time: Hora a verificar (None = ahora)
            consider_ia_buffer: Si True, considera buffer de IA antes del cierre
            
        Returns:
            True si está dentro del horario, False caso contrario
            
        Example:
            start_time = 06:00
            end_time = 13:00
            ia_buffer = 3 minutos
            
            Sin buffer:
            - 12:59 → True
            - 13:00 → False
            
            Con buffer:
            - 12:56 → True
            - 12:58 → False (menos de 3 min antes del cierre)
        """
        if check_time is None:
            check_time = self.get_current_lima_time()
        
        current_time = check_time.time()
        
        # Determinar hora de cierre efectiva
        effective_end_time = self.end_time
        
        if consider_ia_buffer:
            # Restar buffer de IA al tiempo de cierre
            end_datetime = datetime.combine(date.today(), self.end_time)
            buffered_end = end_datetime - timedelta(minutes=self.ia_buffer_minutes)
            effective_end_time = buffered_end.time()
        
        # Verificar rango
        return self.start_time <= current_time < effective_end_time
    
    def is_trading_time(
        self,
        check_time: Optional[datetime] = None,
        consider_ia_buffer: bool = True
    ) -> ValidationResult:
        """
        Validación completa: día hábil + horario de trading.
        
        Esta es la función principal que combina todas las validaciones:
        1. Día hábil (Lun-Vie, excluyendo feriados)
        2. Dentro del horario de trading
        3. Considerando buffer de IA (por defecto)
        
        Args:
            check_time: Momento a validar (None = ahora)
            consider_ia_buffer: Considerar buffer de IA antes del cierre
            
        Returns:
            ValidationResult con is_valid=True/False y razón
        """
        if check_time is None:
            check_time = self.get_current_lima_time()
        
        # Verificar día hábil
        if not self.is_business_day(check_time):
            weekday_name = self._get_weekday_name(check_time.isoweekday())
            
            if self.is_holiday(check_time):
                reason = f"Día festivo: {check_time.date()}"
            else:
                reason = f"No es día hábil: {weekday_name}"
            
            return ValidationResult(
                is_valid=False,
                reason=reason,
                timestamp=check_time
            )
        
        # Verificar horario de trading
        if not self.is_within_trading_hours(check_time, consider_ia_buffer):
            current_time_str = check_time.strftime("%H:%M:%S")
            
            if consider_ia_buffer:
                effective_close = self._get_effective_close_time()
                reason = (
                    f"Fuera de horario de trading: {current_time_str}. "
                    f"Horario válido: {self.start_time.strftime('%H:%M')} - "
                    f"{effective_close.strftime('%H:%M')} "
                    f"(cierre a las {self.end_time.strftime('%H:%M')}, "
                    f"buffer IA: {self.ia_buffer_minutes} min)"
                )
            else:
                reason = (
                    f"Fuera de horario de trading: {current_time_str}. "
                    f"Horario válido: {self.start_time.strftime('%H:%M')} - "
                    f"{self.end_time.strftime('%H:%M')}"
                )
            
            return ValidationResult(
                is_valid=False,
                reason=reason,
                timestamp=check_time
            )
        
        # Todo OK
        return ValidationResult(
            is_valid=True,
            reason=f"Horario de trading válido: {check_time.strftime('%Y-%m-%d %H:%M:%S')}",
            timestamp=check_time
        )
    
    # ==================== MÉTODOS UTILITARIOS ====================
    
    def get_minutes_until_close(self, current_time: Optional[datetime] = None) -> int:
        """
        Calcula minutos restantes hasta el cierre del mercado.
        
        Args:
            current_time: Momento actual (None = ahora)
            
        Returns:
            Minutos hasta el cierre (0 si ya cerró)
        """
        if current_time is None:
            current_time = self.get_current_lima_time()
        
        # Construir datetime de cierre para hoy
        close_datetime = datetime.combine(
            current_time.date(),
            self.end_time,
            tzinfo=self.timezone
        )
        
        # Calcular diferencia
        diff = close_datetime - current_time
        minutes = int(diff.total_seconds() / 60)
        
        return max(0, minutes)  # No retornar negativos
    
    def get_next_trading_session(self, from_time: Optional[datetime] = None) -> datetime:
        """
        Calcula el inicio de la próxima sesión de trading.
        
        Args:
            from_time: Momento desde el cual calcular (None = ahora)
            
        Returns:
            datetime del inicio de la próxima sesión
        """
        if from_time is None:
            from_time = self.get_current_lima_time()
        
        # Empezar desde mañana
        next_day = from_time + timedelta(days=1)
        next_session = datetime.combine(
            next_day.date(),
            self.start_time,
            tzinfo=self.timezone
        )
        
        # Buscar siguiente día hábil
        max_attempts = 14  # Máximo 2 semanas
        attempts = 0
        
        while not self.is_business_day(next_session) and attempts < max_attempts:
            next_session += timedelta(days=1)
            attempts += 1
        
        return next_session
    
    def get_trading_status_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen completo del estado actual de trading.
        
        Returns:
            Diccionario con múltiples métricas de estado
        """
        current_time = self.get_current_lima_time()
        validation = self.is_trading_time(current_time)
        
        return {
            "current_lima_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_trading_time": validation.is_valid,
            "validation_reason": validation.reason,
            "is_business_day": self.is_business_day(current_time),
            "is_within_hours": self.is_within_trading_hours(current_time, consider_ia_buffer=True),
            "minutes_until_close": self.get_minutes_until_close(current_time),
            "next_trading_session": self.get_next_trading_session(current_time).strftime("%Y-%m-%d %H:%M:%S"),
            "trading_hours": f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}",
            "ia_buffer_minutes": self.ia_buffer_minutes,
            "effective_close_time": self._get_effective_close_time().strftime("%H:%M")
        }
    
    def _get_effective_close_time(self) -> time:
        """Calcula hora de cierre efectiva considerando buffer de IA"""
        end_datetime = datetime.combine(date.today(), self.end_time)
        buffered_end = end_datetime - timedelta(minutes=self.ia_buffer_minutes)
        return buffered_end.time()
    
    def _get_weekday_name(self, weekday: int) -> str:
        """Retorna nombre del día de la semana en español"""
        names = {
            1: "Lunes",
            2: "Martes",
            3: "Miércoles",
            4: "Jueves",
            5: "Viernes",
            6: "Sábado",
            7: "Domingo"
        }
        return names.get(weekday, f"Día {weekday}")
    
    # ==================== MÉTODOS DE CONFIGURACIÓN DINÁMICA ====================
    
    def update_trading_hours(self, start_time: str, end_time: str) -> None:
        """
        Actualiza horarios de trading en runtime.
        
        Args:
            start_time: Hora de inicio (formato HH:MM)
            end_time: Hora de cierre (formato HH:MM)
            
        Raises:
            TimeValidationError: Si los horarios son inválidos
        """
        new_start = self._parse_time(start_time)
        new_end = self._parse_time(end_time)
        
        if new_end <= new_start:
            raise TimeValidationError("end_time debe ser posterior a start_time")
        
        self.start_time = new_start
        self.end_time = new_end
    
    def update_ia_buffer(self, buffer_minutes: int) -> None:
        """
        Actualiza el buffer de IA en runtime.
        
        Args:
            buffer_minutes: Minutos de buffer (0-60)
            
        Raises:
            TimeValidationError: Si el valor es inválido
        """
        if not 0 <= buffer_minutes <= 60:
            raise TimeValidationError("Buffer debe estar entre 0 y 60 minutos")
        
        self.ia_buffer_minutes = buffer_minutes
    
    def reload_config(self, config_file: str) -> None:
        """
        Recarga configuración completa desde archivo.
        
        Args:
            config_file: Ruta al archivo de configuración JSON
        """
        config = self._load_config_from_file(config_file)
        self.__init__(config=config)
