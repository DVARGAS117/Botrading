"""
Tests unitarios para el módulo time_validator.

Este módulo implementa tests para el Ticket T35: Validación de hora local de Lima
y días hábiles, con horarios configurables y buffer de tiempo para respuesta de IA.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T35 - Validación de hora local de Lima y días hábiles
"""
import pytest
from datetime import datetime, time, date
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo


# Importar clase a testear (aún no existe, TDD Red)
from src.core.time_validator import (
    TimeValidator,
    TimeValidationError,
    ValidationResult
)


# ==================== FIXTURES ====================

@pytest.fixture
def sample_schedule_config():
    """Configuración de horario de ejemplo"""
    return {
        "trading_schedule": {
            "timezone": "America/Lima",
            "trading_hours": {
                "start_time": "06:00",
                "end_time": "13:00",
                "ia_response_buffer_minutes": 3
            },
            "business_days": {
                "enabled": [1, 2, 3, 4, 5]  # Lunes a Viernes
            },
            "holidays": {
                "enabled": True,
                "dates": ["2025-12-25", "2025-01-01"]
            }
        },
        "validation_rules": {
            "strict_mode": True,
            "log_rejections": True
        }
    }


@pytest.fixture
def time_validator(sample_schedule_config):
    """TimeValidator con configuración de ejemplo"""
    return TimeValidator(config=sample_schedule_config)


@pytest.fixture
def mock_lima_time():
    """Helper para mockear la hora de Lima"""
    def _mock_time(year, month, day, hour, minute, second=0):
        """Retorna datetime en timezone Lima"""
        return datetime(year, month, day, hour, minute, second,
                       tzinfo=ZoneInfo("America/Lima"))
    return _mock_time


# ==================== TESTS DE INICIALIZACIÓN ====================

@pytest.mark.unit
class TestTimeValidatorInitialization:
    """Tests para la inicialización del TimeValidator"""
    
    def test_init_with_config_dict(self, sample_schedule_config):
        """Debe inicializar con diccionario de configuración"""
        validator = TimeValidator(config=sample_schedule_config)
        
        assert validator is not None
        assert validator.timezone.key == "America/Lima"
        assert validator.start_time == time(6, 0)
        assert validator.end_time == time(13, 0)
        assert validator.ia_buffer_minutes == 3
    
    def test_init_with_config_file(self, temp_dir):
        """Debe cargar configuración desde archivo JSON"""
        import json
        config_file = temp_dir / "schedule.json"
        
        config = {
            "trading_schedule": {
                "timezone": "America/Lima",
                "trading_hours": {
                    "start_time": "08:00",
                    "end_time": "15:00",
                    "ia_response_buffer_minutes": 5
                },
                "business_days": {"enabled": [1, 2, 3, 4, 5]},
                "holidays": {"enabled": False, "dates": []}
            },
            "validation_rules": {"strict_mode": True, "log_rejections": True}
        }
        
        config_file.write_text(json.dumps(config))
        
        validator = TimeValidator(config_file=str(config_file))
        
        assert validator.start_time == time(8, 0)
        assert validator.end_time == time(15, 0)
        assert validator.ia_buffer_minutes == 5
    
    def test_init_without_config_uses_defaults(self):
        """Debe usar valores por defecto si no hay configuración"""
        validator = TimeValidator()
        
        assert validator.timezone.key == "America/Lima"
        assert validator.start_time == time(6, 0)
        assert validator.end_time == time(13, 0)
        assert validator.ia_buffer_minutes == 3
        assert validator.business_days == [1, 2, 3, 4, 5]
    
    def test_init_validates_timezone(self):
        """Debe validar que el timezone sea válido"""
        invalid_config = {
            "trading_schedule": {
                "timezone": "Invalid/Timezone",
                "trading_hours": {"start_time": "06:00", "end_time": "13:00"},
                "business_days": {"enabled": [1, 2, 3, 4, 5]}
            }
        }
        
        with pytest.raises(TimeValidationError, match="Timezone inválido"):
            TimeValidator(config=invalid_config)
    
    def test_init_validates_time_format(self):
        """Debe validar formato de horas"""
        invalid_config = {
            "trading_schedule": {
                "timezone": "America/Lima",
                "trading_hours": {
                    "start_time": "25:00",  # Hora inválida
                    "end_time": "13:00"
                },
                "business_days": {"enabled": [1, 2, 3, 4, 5]}
            }
        }
        
        with pytest.raises(TimeValidationError, match="Formato de hora inválido"):
            TimeValidator(config=invalid_config)
    
    def test_init_validates_end_after_start(self):
        """Debe validar que end_time sea posterior a start_time"""
        invalid_config = {
            "trading_schedule": {
                "timezone": "America/Lima",
                "trading_hours": {
                    "start_time": "13:00",
                    "end_time": "06:00"  # Antes del start
                },
                "business_days": {"enabled": [1, 2, 3, 4, 5]}
            }
        }
        
        with pytest.raises(TimeValidationError, match=r"end_time.*debe ser posterior.*start_time"):
            TimeValidator(config=invalid_config)


# ==================== TESTS DE OBTENCIÓN DE HORA ====================

@pytest.mark.unit
class TestGetCurrentTime:
    """Tests para obtener hora actual en Lima"""
    
    def test_get_current_lima_time(self, time_validator):
        """Debe retornar hora actual en timezone Lima"""
        lima_time = time_validator.get_current_lima_time()
        
        assert isinstance(lima_time, datetime)
        assert lima_time.tzinfo is not None
        assert lima_time.tzinfo.key == "America/Lima"
    
    def test_lima_time_is_utc_minus_5(self, time_validator, mock_lima_time):
        """Lima debe estar UTC-5"""
        # Mock de tiempo UTC
        utc_time = datetime(2025, 11, 6, 15, 0, 0, tzinfo=ZoneInfo("UTC"))
        
        with patch('src.core.time_validator.datetime') as mock_dt:
            mock_dt.now.return_value = utc_time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Lima time debería ser 10:00 (UTC-5)
            expected_lima = utc_time.astimezone(ZoneInfo("America/Lima"))
            assert expected_lima.hour == 10
    
    def test_get_current_time_only(self, time_validator):
        """Debe retornar solo la hora (sin fecha)"""
        current_time = time_validator.get_current_time_only()
        
        assert isinstance(current_time, time)
        assert 0 <= current_time.hour <= 23
        assert 0 <= current_time.minute <= 59


# ==================== TESTS DE VALIDACIÓN DE DÍAS HÁBILES ====================

@pytest.mark.unit
class TestBusinessDayValidation:
    """Tests para validación de días hábiles"""
    
    def test_is_business_day_monday_to_friday(self, time_validator, mock_lima_time):
        """Lunes a Viernes deben ser días hábiles"""
        test_cases = [
            (2025, 11, 3, 1, "Lunes"),      # Lunes
            (2025, 11, 4, 2, "Martes"),     # Martes
            (2025, 11, 5, 3, "Miércoles"),  # Miércoles
            (2025, 11, 6, 4, "Jueves"),     # Jueves
            (2025, 11, 7, 5, "Viernes"),    # Viernes
        ]
        
        for year, month, day, weekday, name in test_cases:
            test_date = mock_lima_time(year, month, day, 10, 0)
            
            with patch.object(time_validator, 'get_current_lima_time', return_value=test_date):
                result = time_validator.is_business_day()
                assert result is True, f"{name} debería ser día hábil"
    
    def test_is_not_business_day_weekend(self, time_validator, mock_lima_time):
        """Sábado y Domingo NO deben ser días hábiles"""
        # Sábado
        saturday = mock_lima_time(2025, 11, 8, 10, 0)
        with patch.object(time_validator, 'get_current_lima_time', return_value=saturday):
            result = time_validator.is_business_day()
            assert result is False, "Sábado no debería ser día hábil"
        
        # Domingo
        sunday = mock_lima_time(2025, 11, 9, 10, 0)
        with patch.object(time_validator, 'get_current_lima_time', return_value=sunday):
            result = time_validator.is_business_day()
            assert result is False, "Domingo no debería ser día hábil"
    
    def test_is_business_day_with_custom_days(self, sample_schedule_config):
        """Debe respetar días hábiles personalizados"""
        # Solo Lunes, Miércoles, Viernes
        sample_schedule_config["trading_schedule"]["business_days"]["enabled"] = [1, 3, 5]
        validator = TimeValidator(config=sample_schedule_config)
        
        # Martes (día 2) no debería ser hábil
        tuesday = datetime(2025, 11, 4, 10, 0, tzinfo=ZoneInfo("America/Lima"))
        with patch.object(validator, 'get_current_lima_time', return_value=tuesday):
            assert validator.is_business_day() is False
    
    def test_is_holiday(self, time_validator, mock_lima_time):
        """Debe detectar días festivos"""
        # 25 de diciembre (en config de ejemplo)
        christmas = mock_lima_time(2025, 12, 25, 10, 0)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=christmas):
            is_holiday = time_validator.is_holiday()
            assert is_holiday is True, "25 dic debería ser feriado"
            
            # También debe hacer que is_business_day retorne False
            is_business = time_validator.is_business_day()
            assert is_business is False, "Feriado no es día hábil"


# ==================== TESTS DE VALIDACIÓN DE HORARIO ====================

@pytest.mark.unit
class TestTradingHoursValidation:
    """Tests para validación de horario de trading"""
    
    def test_is_within_trading_hours_valid(self, time_validator, mock_lima_time):
        """Debe validar correctamente horas dentro del rango"""
        test_cases = [
            (6, 0, "Apertura exacta"),
            (9, 30, "Media mañana"),
            (12, 59, "Casi cierre"),
        ]
        
        for hour, minute, description in test_cases:
            test_time = mock_lima_time(2025, 11, 6, hour, minute)  # Jueves
            
            with patch.object(time_validator, 'get_current_lima_time', return_value=test_time):
                result = time_validator.is_within_trading_hours()
                assert result is True, f"{description} ({hour}:{minute:02d}) debería ser válido"
    
    def test_is_within_trading_hours_invalid(self, time_validator, mock_lima_time):
        """Debe rechazar horas fuera del rango"""
        test_cases = [
            (5, 59, "Antes de apertura"),
            (13, 1, "Después de cierre"),
            (0, 0, "Medianoche"),
            (23, 59, "Antes de medianoche"),
        ]
        
        for hour, minute, description in test_cases:
            test_time = mock_lima_time(2025, 11, 6, hour, minute)
            
            with patch.object(time_validator, 'get_current_lima_time', return_value=test_time):
                result = time_validator.is_within_trading_hours()
                assert result is False, f"{description} ({hour}:{minute:02d}) debería ser inválido"
    
    def test_is_within_trading_hours_with_ia_buffer(self, time_validator, mock_lima_time):
        """Debe considerar buffer de IA antes del cierre"""
        # Buffer de 3 minutos: cierre efectivo a las 12:57
        
        # 12:56 → OK (más de 3 min antes del cierre)
        before_buffer = mock_lima_time(2025, 11, 6, 12, 56)
        with patch.object(time_validator, 'get_current_lima_time', return_value=before_buffer):
            assert time_validator.is_within_trading_hours(consider_ia_buffer=True) is True
        
        # 12:58 → RECHAZADO (menos de 3 min antes del cierre)
        within_buffer = mock_lima_time(2025, 11, 6, 12, 58)
        with patch.object(time_validator, 'get_current_lima_time', return_value=within_buffer):
            assert time_validator.is_within_trading_hours(consider_ia_buffer=True) is False
    
    def test_ia_buffer_does_not_affect_start_time(self, time_validator, mock_lima_time):
        """El buffer de IA no debe afectar la hora de inicio"""
        # 06:01 siempre debe ser válido (independiente del buffer)
        start_time = mock_lima_time(2025, 11, 6, 6, 1)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=start_time):
            assert time_validator.is_within_trading_hours(consider_ia_buffer=True) is True
            assert time_validator.is_within_trading_hours(consider_ia_buffer=False) is True


# ==================== TESTS DE VALIDACIÓN COMPLETA ====================

@pytest.mark.unit
class TestCompleteValidation:
    """Tests para validación completa (día + hora)"""
    
    def test_is_trading_time_valid_case(self, time_validator, mock_lima_time):
        """Debe validar correctamente caso válido (día hábil + horario válido)"""
        # Jueves 10:00 AM
        valid_time = mock_lima_time(2025, 11, 6, 10, 0)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=valid_time):
            result = time_validator.is_trading_time()
            
            assert isinstance(result, ValidationResult)
            assert result.is_valid is True
            assert result.reason is None or "válido" in result.reason.lower()
    
    def test_is_trading_time_weekend(self, time_validator, mock_lima_time):
        """Debe rechazar fin de semana"""
        # Sábado 10:00 AM
        weekend = mock_lima_time(2025, 11, 8, 10, 0)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=weekend):
            result = time_validator.is_trading_time()
            
            assert result.is_valid is False
            assert "sábado" in result.reason.lower() or "fin de semana" in result.reason.lower()
    
    def test_is_trading_time_outside_hours(self, time_validator, mock_lima_time):
        """Debe rechazar fuera de horario"""
        # Jueves 14:00 (fuera de horario)
        after_hours = mock_lima_time(2025, 11, 6, 14, 0)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=after_hours):
            result = time_validator.is_trading_time()
            
            assert result.is_valid is False
            assert "horario" in result.reason.lower()
    
    def test_is_trading_time_holiday(self, time_validator, mock_lima_time):
        """Debe rechazar días festivos"""
        # 25 diciembre 10:00
        holiday = mock_lima_time(2025, 12, 25, 10, 0)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=holiday):
            result = time_validator.is_trading_time()
            
            assert result.is_valid is False
            assert "feriado" in result.reason.lower() or "festivo" in result.reason.lower()
    
    def test_is_trading_time_with_ia_buffer(self, time_validator, mock_lima_time):
        """Debe rechazar si está dentro del buffer de IA"""
        # Jueves 12:58 (2 min antes del cierre, buffer=3min)
        near_close = mock_lima_time(2025, 11, 6, 12, 58)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=near_close):
            result = time_validator.is_trading_time(consider_ia_buffer=True)
            
            assert result.is_valid is False
            assert "buffer" in result.reason.lower() or "cierre" in result.reason.lower()


# ==================== TESTS DE UTILIDADES ====================

@pytest.mark.unit
class TestUtilityMethods:
    """Tests para métodos utilitarios"""
    
    def test_get_minutes_until_close(self, time_validator, mock_lima_time):
        """Debe calcular minutos hasta el cierre"""
        # 12:45 → 15 minutos hasta las 13:00
        current = mock_lima_time(2025, 11, 6, 12, 45)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=current):
            minutes = time_validator.get_minutes_until_close()
            assert minutes == 15
    
    def test_get_minutes_until_close_negative(self, time_validator, mock_lima_time):
        """Debe retornar 0 si ya pasó el cierre"""
        # 14:00 → ya pasó el cierre
        after_close = mock_lima_time(2025, 11, 6, 14, 0)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=after_close):
            minutes = time_validator.get_minutes_until_close()
            assert minutes == 0
    
    def test_get_next_trading_session(self, time_validator, mock_lima_time):
        """Debe calcular próxima sesión de trading"""
        # Viernes 14:00 → próxima sesión: Lunes 06:00
        friday_afternoon = mock_lima_time(2025, 11, 7, 14, 0)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=friday_afternoon):
            next_session = time_validator.get_next_trading_session()
            
            assert isinstance(next_session, datetime)
            assert next_session.weekday() == 0  # Lunes
            assert next_session.hour == 6
            assert next_session.minute == 0
    
    def test_get_trading_status_summary(self, time_validator, mock_lima_time):
        """Debe retornar resumen del estado"""
        valid_time = mock_lima_time(2025, 11, 6, 10, 30)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=valid_time):
            status = time_validator.get_trading_status_summary()
            
            assert isinstance(status, dict)
            assert "is_trading_time" in status
            assert "is_business_day" in status
            assert "current_lima_time" in status
            assert "minutes_until_close" in status


# ==================== TESTS DE INTEGRACIÓN CON LOGGER ====================

@pytest.mark.integration
class TestLoggerIntegration:
    """Tests de integración con BotLogger"""
    
    def test_logs_rejection_reasons(self, time_validator, mock_lima_time, caplog):
        """Debe loguear razones de rechazo"""
        # Sábado 10:00
        weekend = mock_lima_time(2025, 11, 8, 10, 0)
        
        with patch.object(time_validator, 'get_current_lima_time', return_value=weekend):
            result = time_validator.is_trading_time()
            
            assert result.is_valid is False
            # Verificar que se logueó el rechazo
            # (implementación depende de cómo integres con logger)


# ==================== TESTS DE CONFIGURACIÓN DINÁMICA ====================

@pytest.mark.unit
class TestDynamicConfiguration:
    """Tests para cambio dinámico de configuración"""
    
    def test_update_trading_hours(self, time_validator):
        """Debe permitir actualizar horarios en runtime"""
        # Cambiar horario a 08:00-15:00
        time_validator.update_trading_hours(
            start_time="08:00",
            end_time="15:00"
        )
        
        assert time_validator.start_time == time(8, 0)
        assert time_validator.end_time == time(15, 0)
    
    def test_update_ia_buffer(self, time_validator):
        """Debe permitir cambiar buffer de IA"""
        time_validator.update_ia_buffer(5)  # 5 minutos
        
        assert time_validator.ia_buffer_minutes == 5
    
    def test_reload_config_from_file(self, time_validator, temp_dir):
        """Debe poder recargar configuración desde archivo"""
        import json
        
        new_config = {
            "trading_schedule": {
                "timezone": "America/Lima",
                "trading_hours": {
                    "start_time": "07:00",
                    "end_time": "14:00",
                    "ia_response_buffer_minutes": 2
                },
                "business_days": {"enabled": [1, 2, 3, 4, 5]},
                "holidays": {"enabled": False, "dates": []}
            }
        }
        
        config_file = temp_dir / "new_schedule.json"
        config_file.write_text(json.dumps(new_config))
        
        time_validator.reload_config(str(config_file))
        
        assert time_validator.start_time == time(7, 0)
        assert time_validator.ia_buffer_minutes == 2


# ==================== TESTS DE VALIDATIONRESULT ====================

@pytest.mark.unit
class TestValidationResult:
    """Tests para la clase ValidationResult"""
    
    def test_validation_result_valid(self):
        """Debe crear resultado válido correctamente"""
        result = ValidationResult(is_valid=True, reason="Horario válido")
        
        assert result.is_valid is True
        assert result.reason == "Horario válido"
        assert bool(result) is True  # __bool__
    
    def test_validation_result_invalid(self):
        """Debe crear resultado inválido correctamente"""
        result = ValidationResult(is_valid=False, reason="Fuera de horario")
        
        assert result.is_valid is False
        assert result.reason == "Fuera de horario"
        assert bool(result) is False  # __bool__
    
    def test_validation_result_repr(self):
        """Debe tener representación string clara"""
        result = ValidationResult(is_valid=True, reason="OK")
        
        repr_str = repr(result)
        assert "ValidationResult" in repr_str
        assert "True" in repr_str
