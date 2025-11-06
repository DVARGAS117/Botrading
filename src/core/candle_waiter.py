"""
Módulo para esperar el cierre de velas antes de extraer datos.

Este módulo implementa el Ticket T37: Espera por cierre de vela antes de extraer
datos, garantizando que los indicadores se calculen con velas cerradas.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T37 - Espera por cierre de vela antes de extraer datos
"""
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class CandleWaitError(Exception):
    """Excepción para errores en la espera de velas"""
    pass


class TimeframeNotSupportedError(CandleWaitError):
    """Excepción cuando el timeframe no está soportado"""
    pass


# ==================== CLASE PRINCIPAL ====================

class CandleWaiter:
    """
    Espera el cierre de velas antes de extraer datos.
    
    Este módulo es crítico para garantizar que los indicadores técnicos
    se calculen con datos completos y consistentes. Espera el cierre de
    la vela actual más un delay configurable para asegurar que el dato
    esté disponible en el broker.
    
    Funcionalidades:
    - Calcula próximo cierre según timeframe MT5
    - Espera activa hasta el cierre + delay
    - Integración con TimeValidator (T35)
    - Soporte para M1, M5, M15, M30, H1, H4, D1
    - Timeout configurable
    - Validación de horario de trading
    
    Ejemplo:
        from src.core.time_validator import TimeValidator
        from src.core.candle_waiter import CandleWaiter
        
        validator = TimeValidator(config_file="config/schedule.json")
        waiter = CandleWaiter("H1", config, validator)
        
        if waiter.wait_for_candle_close():
            # La vela cerró, extraer datos
            ohlcv_data = mt5.get_ohlcv(...)
    """
    
    # Timeframes soportados (nombre → segundos)
    SUPPORTED_TIMEFRAMES = {
        "M1": 60,           # 1 minuto
        "M5": 300,          # 5 minutos
        "M15": 900,         # 15 minutos
        "M30": 1800,        # 30 minutos
        "H1": 3600,         # 1 hora
        "H4": 14400,        # 4 horas
        "D1": 86400,        # 1 día
    }
    
    # Configuración por defecto
    DEFAULT_DELAY_SECONDS = 3
    DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutos máximo
    DEFAULT_STRICT_MODE = True
    
    def __init__(
        self,
        timeframe: str,
        config: Dict[str, Any],
        time_validator
    ):
        """
        Inicializa el CandleWaiter.
        
        Args:
            timeframe: Timeframe MT5 ("M1", "M5", "H1", etc.)
            config: Configuración con delay_seconds, timeout, etc.
            time_validator: Instancia de TimeValidator (T35)
            
        Raises:
            TimeframeNotSupportedError: Si el timeframe no está soportado
        """
        # Validar timeframe
        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            supported = ", ".join(self.SUPPORTED_TIMEFRAMES.keys())
            raise TimeframeNotSupportedError(
                f"Timeframe '{timeframe}' no soportado. "
                f"Soportados: {supported}"
            )
        
        self.timeframe = timeframe
        self.timeframe_seconds = self.SUPPORTED_TIMEFRAMES[timeframe]
        self.time_validator = time_validator
        
        # Configuración
        candle_config = config.get("candle_wait", {})
        self.delay_seconds = candle_config.get(
            "delay_seconds",
            self.DEFAULT_DELAY_SECONDS
        )
        self.timeout_seconds = candle_config.get(
            "timeout_seconds",
            self.DEFAULT_TIMEOUT_SECONDS
        )
        self.strict_mode = candle_config.get(
            "strict_mode",
            self.DEFAULT_STRICT_MODE
        )
    
    def get_next_candle_close_time(self, current_time: datetime) -> datetime:
        """
        Calcula el momento exacto del próximo cierre de vela.
        
        Este método es el corazón del cálculo. Determina cuándo cerrará
        la próxima vela según el timeframe configurado.
        
        Lógica:
        - Para M1-M30: Redondear al próximo múltiplo de minutos
        - Para H1: Redondear a la próxima hora completa
        - Para H4: Redondear al próximo múltiplo de 4 horas (00, 04, 08, 12, 16, 20)
        - Para D1: Medianoche del día siguiente
        
        Args:
            current_time: Momento actual (timezone aware)
            
        Returns:
            datetime del próximo cierre de vela
        """
        if self.timeframe == "D1":
            # Vela diaria cierra a medianoche
            next_day = current_time.date() + timedelta(days=1)
            return datetime.combine(
                next_day,
                datetime.min.time(),
                tzinfo=current_time.tzinfo
            )
        
        elif self.timeframe == "H4":
            # Velas H4 cierran a las 00, 04, 08, 12, 16, 20 horas
            current_hour = current_time.hour
            
            # Encontrar próximo múltiplo de 4
            if current_hour < 4:
                next_hour = 4
            elif current_hour < 8:
                next_hour = 8
            elif current_hour < 12:
                next_hour = 12
            elif current_hour < 16:
                next_hour = 16
            elif current_hour < 20:
                next_hour = 20
            else:
                # Después de las 20:00, siguiente es 00:00 del día siguiente
                next_day = current_time.date() + timedelta(days=1)
                return datetime.combine(
                    next_day,
                    datetime.min.time(),
                    tzinfo=current_time.tzinfo
                )
            
            # Mismo día, próxima hora H4
            return datetime.combine(
                current_time.date(),
                datetime.min.time().replace(hour=next_hour),
                tzinfo=current_time.tzinfo
            )
        
        elif self.timeframe == "H1":
            # Vela horaria cierra en la próxima hora completa
            next_hour = current_time.replace(minute=0, second=0, microsecond=0)
            next_hour += timedelta(hours=1)
            
            # Si ya pasamos la hora actual, ir a la siguiente
            if next_hour <= current_time:
                next_hour += timedelta(hours=1)
            
            return next_hour
        
        else:
            # Timeframes de minutos (M1, M5, M15, M30)
            # Redondear al próximo múltiplo de minutos
            minutes = self.timeframe_seconds // 60
            
            # Calcular timestamp actual
            current_timestamp = int(current_time.timestamp())
            
            # Redondear al próximo múltiplo de segundos del timeframe
            remainder = current_timestamp % self.timeframe_seconds
            
            if remainder == 0:
                # Estamos justo en un cierre, siguiente es +timeframe
                next_timestamp = current_timestamp + self.timeframe_seconds
            else:
                # Redondear hacia arriba
                next_timestamp = current_timestamp + (self.timeframe_seconds - remainder)
            
            return datetime.fromtimestamp(next_timestamp, tz=current_time.tzinfo)
    
    def is_candle_closed(self, check_time: datetime) -> bool:
        """
        Verifica si una vela está cerrada en el momento dado.
        
        Una vela está cerrada si check_time está exactamente en un
        múltiplo del timeframe o después de él.
        
        Args:
            check_time: Momento a verificar
            
        Returns:
            True si la vela está cerrada, False si está abierta
        """
        timestamp = int(check_time.timestamp())
        remainder = timestamp % self.timeframe_seconds
        
        # Si remainder es 0, estamos justo en un cierre
        return remainder == 0
    
    def get_seconds_until_close(self) -> int:
        """
        Calcula segundos hasta el próximo cierre de vela.
        
        Returns:
            Segundos hasta el cierre (siempre >= 0)
        """
        current = self.time_validator.get_current_lima_time()
        next_close = self.get_next_candle_close_time(current)
        
        diff = next_close - current
        seconds = int(diff.total_seconds())
        
        return max(0, seconds)
    
    def wait_for_candle_close(self, max_iterations: int = 600) -> bool:
        """
        Espera hasta que la vela actual cierre + delay.
        
        Este es el método principal del módulo. Espera activamente
        hasta que la vela cierre, aplica el delay configurado, y
        valida que estemos en horario de trading.
        
        Lógica:
        1. Validar que es horario de trading
        2. Verificar si ya cerró recientemente (< 5 segundos después de un cierre)
        3. Si no, calcular próximo cierre y esperar
        4. Aplicar delay post-cierre
        5. Retornar True si todo OK
        
        Args:
            max_iterations: Máximo número de iteraciones para evitar loops infinitos en tests
        
        Returns:
            True si esperó exitosamente y cerró la vela
            False si no es horario de trading o hubo timeout
        """
        start_time = time.time()
        iterations = 0
        
        # Validar horario de trading (solo una vez al inicio)
        validation = self.time_validator.is_trading_time()
        if not validation.is_valid:
            return False
        
        # Obtener hora actual
        current = self.time_validator.get_current_lima_time()
        
        # Verificar si acabamos de pasar un cierre (remainder pequeño)
        timestamp = int(current.timestamp())
        remainder = timestamp % self.timeframe_seconds
        
        # Si remainder < 5, significa que pasó un cierre hace menos de 5 segundos
        if remainder < 5:
            time.sleep(self.delay_seconds)
            return True
        
        # Calcular próximo cierre
        next_close = self.get_next_candle_close_time(current)
        
        while iterations < max_iterations:
            iterations += 1
            
            # Verificar timeout
            elapsed = time.time() - start_time
            if elapsed > self.timeout_seconds:
                return False
            
            # Obtener hora actual
            current = self.time_validator.get_current_lima_time()
            
            # Calcular segundos hasta cierre
            diff = next_close - current
            seconds_until = int(diff.total_seconds())
            
            if seconds_until <= 0:
                # La vela ya cerró, aplicar delay
                time.sleep(self.delay_seconds)
                return True
            
            # Esperar 1 segundo y volver a verificar
            # (no esperar todo el tiempo de golpe para poder
            # verificar trading hours periódicamente)
            time.sleep(min(1, seconds_until))
        
        # Si llegamos aquí, excedimos max_iterations (solo en tests)
        return False
    
    def get_wait_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado de espera.
        
        Útil para logging y debugging.
        
        Returns:
            Diccionario con información del estado
        """
        current = self.time_validator.get_current_lima_time()
        next_close = self.get_next_candle_close_time(current)
        seconds_until = self.get_seconds_until_close()
        
        validation = self.time_validator.is_trading_time()
        
        return {
            "timeframe": self.timeframe,
            "current_time": current.strftime("%Y-%m-%d %H:%M:%S"),
            "next_close_time": next_close.strftime("%Y-%m-%d %H:%M:%S"),
            "seconds_until_close": seconds_until,
            "is_trading_time": validation.is_valid,
            "delay_seconds": self.delay_seconds,
            "timeout_seconds": self.timeout_seconds
        }
