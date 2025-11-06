"""
Tests unitarios para el módulo candle_waiter.

Este módulo implementa tests para el Ticket T37: Espera por cierre de vela
antes de extraer datos, para evitar inconsistencias en indicadores.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T37 - Espera por cierre de vela antes de extraer datos
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo


# Importar clase a testear (aún no existe, TDD Red)
from src.core.candle_waiter import (
    CandleWaiter,
    CandleWaitError,
    TimeframeNotSupportedError
)


# ==================== FIXTURES ====================

@pytest.fixture
def sample_candle_config():
    """Configuración de ejemplo para CandleWaiter"""
    return {
        "candle_wait": {
            "delay_seconds": 3,
            "timeout_seconds": 300,
            "strict_mode": True
        },
        "timeframes": {
            "M1": 60,
            "M5": 300,
            "M15": 900,
            "M30": 1800,
            "H1": 3600,
            "H4": 14400,
            "D1": 86400
        }
    }


@pytest.fixture
def mock_time_validator():
    """Mock de TimeValidator"""
    validator = MagicMock()
    validator.get_current_lima_time.return_value = datetime(
        2025, 11, 6, 10, 30, 0, tzinfo=ZoneInfo("America/Lima")
    )
    validator.is_trading_time.return_value.is_valid = True
    return validator


@pytest.fixture
def candle_waiter_m1(sample_candle_config, mock_time_validator):
    """CandleWaiter configurado para M1"""
    return CandleWaiter(
        timeframe="M1",
        config=sample_candle_config,
        time_validator=mock_time_validator
    )


@pytest.fixture
def candle_waiter_h1(sample_candle_config, mock_time_validator):
    """CandleWaiter configurado para H1"""
    return CandleWaiter(
        timeframe="H1",
        config=sample_candle_config,
        time_validator=mock_time_validator
    )


@pytest.fixture
def mock_lima_time():
    """Helper para crear datetime en Lima"""
    def _create(year, month, day, hour, minute, second=0):
        return datetime(year, month, day, hour, minute, second,
                       tzinfo=ZoneInfo("America/Lima"))
    return _create


# ==================== TESTS DE INICIALIZACIÓN ====================

@pytest.mark.unit
class TestCandleWaiterInitialization:
    """Tests para la inicialización de CandleWaiter"""
    
    def test_init_with_valid_timeframe(self, sample_candle_config, mock_time_validator):
        """Debe inicializar con timeframe válido"""
        waiter = CandleWaiter("M5", sample_candle_config, mock_time_validator)
        
        assert waiter.timeframe == "M5"
        assert waiter.delay_seconds == 3
        assert waiter.time_validator == mock_time_validator
    
    def test_init_with_all_supported_timeframes(self, sample_candle_config, mock_time_validator):
        """Debe soportar todos los timeframes MT5"""
        timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
        
        for tf in timeframes:
            waiter = CandleWaiter(tf, sample_candle_config, mock_time_validator)
            assert waiter.timeframe == tf
    
    def test_init_with_invalid_timeframe(self, sample_candle_config, mock_time_validator):
        """Debe rechazar timeframes inválidos"""
        with pytest.raises(TimeframeNotSupportedError, match="Timeframe.*no soportado"):
            CandleWaiter("INVALID", sample_candle_config, mock_time_validator)
    
    def test_init_with_custom_delay(self, mock_time_validator):
        """Debe permitir delay personalizado"""
        config = {
            "candle_wait": {"delay_seconds": 10},
            "timeframes": {"M1": 60}
        }
        waiter = CandleWaiter("M1", config, mock_time_validator)
        
        assert waiter.delay_seconds == 10
    
    def test_init_uses_default_delay_if_not_provided(self, mock_time_validator):
        """Debe usar delay por defecto si no se especifica"""
        config = {"timeframes": {"M1": 60}}
        waiter = CandleWaiter("M1", config, mock_time_validator)
        
        assert waiter.delay_seconds == 3  # Default


# ==================== TESTS DE CÁLCULO DE PRÓXIMO CIERRE ====================

@pytest.mark.unit
class TestNextCandleCloseCalculation:
    """Tests para el cálculo del próximo cierre de vela"""
    
    def test_next_close_m1_basic(self, candle_waiter_m1, mock_lima_time):
        """Debe calcular próximo cierre para M1"""
        # Actual: 10:30:25 → Próximo cierre: 10:31:00
        current = mock_lima_time(2025, 11, 6, 10, 30, 25)
        
        next_close = candle_waiter_m1.get_next_candle_close_time(current)
        
        assert next_close.hour == 10
        assert next_close.minute == 31
        assert next_close.second == 0
    
    def test_next_close_m5_basic(self, sample_candle_config, mock_time_validator, mock_lima_time):
        """Debe calcular próximo cierre para M5"""
        waiter = CandleWaiter("M5", sample_candle_config, mock_time_validator)
        
        # Actual: 10:32:45 → Próximo cierre: 10:35:00
        current = mock_lima_time(2025, 11, 6, 10, 32, 45)
        
        next_close = waiter.get_next_candle_close_time(current)
        
        assert next_close.hour == 10
        assert next_close.minute == 35
        assert next_close.second == 0
    
    def test_next_close_m15(self, sample_candle_config, mock_time_validator, mock_lima_time):
        """Debe calcular próximo cierre para M15"""
        waiter = CandleWaiter("M15", sample_candle_config, mock_time_validator)
        
        # Actual: 10:47:30 → Próximo cierre: 11:00:00
        current = mock_lima_time(2025, 11, 6, 10, 47, 30)
        
        next_close = waiter.get_next_candle_close_time(current)
        
        assert next_close.hour == 11
        assert next_close.minute == 0
    
    def test_next_close_h1(self, candle_waiter_h1, mock_lima_time):
        """Debe calcular próximo cierre para H1"""
        # Actual: 10:45:00 → Próximo cierre: 11:00:00
        current = mock_lima_time(2025, 11, 6, 10, 45, 0)
        
        next_close = candle_waiter_h1.get_next_candle_close_time(current)
        
        assert next_close.hour == 11
        assert next_close.minute == 0
        assert next_close.second == 0
    
    def test_next_close_h4(self, sample_candle_config, mock_time_validator, mock_lima_time):
        """Debe calcular próximo cierre para H4"""
        waiter = CandleWaiter("H4", sample_candle_config, mock_time_validator)
        
        # Actual: 10:30:00 → Próximo cierre: 12:00:00 (velas H4 a 00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
        current = mock_lima_time(2025, 11, 6, 10, 30, 0)
        
        next_close = waiter.get_next_candle_close_time(current)
        
        assert next_close.hour == 12
        assert next_close.minute == 0
    
    def test_next_close_d1(self, sample_candle_config, mock_time_validator, mock_lima_time):
        """Debe calcular próximo cierre para D1"""
        waiter = CandleWaiter("D1", sample_candle_config, mock_time_validator)
        
        # Actual: 6 nov 10:30 → Próximo cierre: 7 nov 00:00
        current = mock_lima_time(2025, 11, 6, 10, 30, 0)
        
        next_close = waiter.get_next_candle_close_time(current)
        
        assert next_close.day == 7
        assert next_close.hour == 0
        assert next_close.minute == 0
    
    def test_next_close_exactly_at_close_time(self, candle_waiter_m1, mock_lima_time):
        """Si estamos justo en el cierre, debe calcular el siguiente"""
        # Actual: 10:30:00 (justo en el cierre)
        current = mock_lima_time(2025, 11, 6, 10, 30, 0)
        
        next_close = candle_waiter_m1.get_next_candle_close_time(current)
        
        # Debería dar el siguiente cierre: 10:31:00
        assert next_close.minute == 31


# ==================== TESTS DE VALIDACIÓN DE VELA CERRADA ====================

@pytest.mark.unit
class TestCandleClosedValidation:
    """Tests para validar si una vela está cerrada"""
    
    def test_is_candle_closed_m1_true(self, candle_waiter_m1, mock_lima_time):
        """Debe detectar vela M1 cerrada"""
        # Verificar en 10:31:00 (justo cerró la vela 10:30)
        check_time = mock_lima_time(2025, 11, 6, 10, 31, 0)
        
        assert candle_waiter_m1.is_candle_closed(check_time) is True
    
    def test_is_candle_closed_m1_false(self, candle_waiter_m1, mock_lima_time):
        """Debe detectar vela M1 abierta"""
        # Verificar en 10:30:45 (vela 10:30 aún abierta)
        check_time = mock_lima_time(2025, 11, 6, 10, 30, 45)
        
        assert candle_waiter_m1.is_candle_closed(check_time) is False
    
    def test_is_candle_closed_m5(self, sample_candle_config, mock_time_validator, mock_lima_time):
        """Debe detectar vela M5 cerrada"""
        waiter = CandleWaiter("M5", sample_candle_config, mock_time_validator)
        
        # Verificar en 10:35:00 (cerró vela 10:30-10:35)
        check_time = mock_lima_time(2025, 11, 6, 10, 35, 0)
        
        assert waiter.is_candle_closed(check_time) is True
    
    def test_is_candle_closed_h1(self, candle_waiter_h1, mock_lima_time):
        """Debe detectar vela H1 cerrada"""
        # Verificar en 11:00:00 (cerró vela 10:00-11:00)
        check_time = mock_lima_time(2025, 11, 6, 11, 0, 0)
        
        assert candle_waiter_h1.is_candle_closed(check_time) is True


# ==================== TESTS DE SEGUNDOS HASTA CIERRE ====================

@pytest.mark.unit
class TestSecondsUntilClose:
    """Tests para calcular segundos hasta próximo cierre"""
    
    def test_seconds_until_close_m1(self, candle_waiter_m1, mock_lima_time):
        """Debe calcular segundos hasta cierre M1"""
        # Actual: 10:30:25 → Cierre: 10:31:00 → 35 segundos
        current = mock_lima_time(2025, 11, 6, 10, 30, 25)
        
        with patch.object(candle_waiter_m1.time_validator, 'get_current_lima_time', return_value=current):
            seconds = candle_waiter_m1.get_seconds_until_close()
        
        assert seconds == 35
    
    def test_seconds_until_close_h1(self, candle_waiter_h1, mock_lima_time):
        """Debe calcular segundos hasta cierre H1"""
        # Actual: 10:45:00 → Cierre: 11:00:00 → 900 segundos (15 min)
        current = mock_lima_time(2025, 11, 6, 10, 45, 0)
        
        with patch.object(candle_waiter_h1.time_validator, 'get_current_lima_time', return_value=current):
            seconds = candle_waiter_h1.get_seconds_until_close()
        
        assert seconds == 900
    
    def test_seconds_until_close_zero_if_past(self, candle_waiter_m1, mock_lima_time):
        """Debe retornar 0 si ya pasó el cierre"""
        # Actual: 10:31:05 (ya pasó cierre de 10:31:00)
        current = mock_lima_time(2025, 11, 6, 10, 31, 5)
        
        with patch.object(candle_waiter_m1.time_validator, 'get_current_lima_time', return_value=current):
            seconds = candle_waiter_m1.get_seconds_until_close()
        
        # Debe calcular para el PRÓXIMO cierre (10:32:00), no negativo
        assert seconds > 0


# ==================== TESTS DE WAIT FOR CANDLE CLOSE ====================

@pytest.mark.unit
class TestWaitForCandleClose:
    """Tests para esperar cierre de vela"""
    
    def test_wait_for_candle_close_immediate(self, candle_waiter_m1, mock_lima_time):
        """Si ya cerró, debe retornar inmediatamente después del delay"""
        # Configurar que ya cerró la vela hace 1 segundo (10:31:01)
        # La vela M1 cierra a las 10:31:00, así que 10:31:01 significa que ya cerró
        closed_time = mock_lima_time(2025, 11, 6, 10, 31, 1)
        
        # Mock para validación de trading time
        candle_waiter_m1.time_validator.is_trading_time.return_value.is_valid = True
        
        with patch.object(candle_waiter_m1.time_validator, 'get_current_lima_time', return_value=closed_time):
            with patch('time.sleep') as mock_sleep:
                result = candle_waiter_m1.wait_for_candle_close(max_iterations=5)
        
        assert result is True
        # Debe haber aplicado el delay (3 segundos)
        mock_sleep.assert_called_with(3)
    
    def test_wait_for_candle_close_with_wait(self, candle_waiter_m1, mock_lima_time):
        """Debe esperar si la vela aún no cierra"""
        # Simular que primero falta tiempo, luego cierra
        times = [
            mock_lima_time(2025, 11, 6, 10, 30, 55),  # Primera llamada (inicial): falta 5 seg
            mock_lima_time(2025, 11, 6, 10, 30, 59),  # Segunda llamada (en loop): falta 1 seg
            mock_lima_time(2025, 11, 6, 10, 31, 0)    # Tercera llamada (en loop): cerró
        ]
        
        # Mock de is_trading_time
        candle_waiter_m1.time_validator.is_trading_time.return_value.is_valid = True
        
        with patch.object(candle_waiter_m1.time_validator, 'get_current_lima_time', side_effect=times):
            with patch('time.sleep') as mock_sleep:
                result = candle_waiter_m1.wait_for_candle_close(max_iterations=5)
        
        assert result is True
        # Debe haber dormido al menos 2 veces (espera + delay final)
        assert mock_sleep.call_count >= 2
    
    def test_wait_respects_trading_hours(self, candle_waiter_m1, mock_lima_time):
        """Debe validar horario de trading antes de esperar"""
        closed_time = mock_lima_time(2025, 11, 6, 14, 0, 0)  # Fuera de horario
        
        # Configurar que NO es horario de trading
        candle_waiter_m1.time_validator.is_trading_time.return_value.is_valid = False
        
        with patch.object(candle_waiter_m1.time_validator, 'get_current_lima_time', return_value=closed_time):
            result = candle_waiter_m1.wait_for_candle_close(max_iterations=5)
        
        # Debe retornar False (no es horario de trading)
        assert result is False
    
    def test_wait_for_candle_close_timeout(self, candle_waiter_m1, mock_lima_time):
        """Debe timeout si espera demasiado"""
        # Configurar timeout de 5 segundos
        candle_waiter_m1.timeout_seconds = 5
        
        # Simular que nunca cierra
        never_closes = mock_lima_time(2025, 11, 6, 10, 30, 55)
        
        with patch.object(candle_waiter_m1.time_validator, 'get_current_lima_time', return_value=never_closes):
            with patch('time.sleep'):
                with patch('time.time', side_effect=[0, 6]):  # Simular 6 segundos transcurridos
                    result = candle_waiter_m1.wait_for_candle_close(max_iterations=5)
        
        # Debe retornar False por timeout
        assert result is False


# ==================== TESTS DE INTEGRACIÓN CON TIMEVALIDATOR ====================

@pytest.mark.integration
class TestTimeValidatorIntegration:
    """Tests de integración con TimeValidator"""
    
    def test_uses_time_validator_for_current_time(self, candle_waiter_m1):
        """Debe usar TimeValidator para obtener hora actual"""
        candle_waiter_m1.get_seconds_until_close()
        
        # Verificar que llamó a TimeValidator
        candle_waiter_m1.time_validator.get_current_lima_time.assert_called()
    
    def test_respects_trading_hours_validation(self, candle_waiter_m1, mock_lima_time):
        """Debe respetar validación de horario de trading"""
        # Configurar fuera de horario
        candle_waiter_m1.time_validator.is_trading_time.return_value.is_valid = False
        
        with patch('time.sleep'):
            result = candle_waiter_m1.wait_for_candle_close()
        
        assert result is False


# ==================== TESTS DE CASOS EDGE ====================

@pytest.mark.unit
class TestEdgeCases:
    """Tests para casos límite"""
    
    def test_midnight_crossing_d1(self, sample_candle_config, mock_time_validator, mock_lima_time):
        """Vela D1 debe cerrar a medianoche"""
        waiter = CandleWaiter("D1", sample_candle_config, mock_time_validator)
        
        # 23:59:00 del 6 nov
        current = mock_lima_time(2025, 11, 6, 23, 59, 0)
        
        next_close = waiter.get_next_candle_close_time(current)
        
        # Debe cerrar a las 00:00 del 7 nov
        assert next_close.day == 7
        assert next_close.hour == 0
        assert next_close.minute == 0
    
    def test_month_end_d1(self, sample_candle_config, mock_time_validator, mock_lima_time):
        """Debe manejar fin de mes correctamente"""
        waiter = CandleWaiter("D1", sample_candle_config, mock_time_validator)
        
        # 30 de noviembre 23:00
        current = mock_lima_time(2025, 11, 30, 23, 0, 0)
        
        next_close = waiter.get_next_candle_close_time(current)
        
        # Debe pasar a diciembre
        assert next_close.month == 12
        assert next_close.day == 1
    
    def test_handles_weekend_gracefully(self, candle_waiter_m1, mock_lima_time):
        """Debe manejar fin de semana (aunque TimeValidator lo rechazará)"""
        # Sábado 10:30
        saturday = mock_lima_time(2025, 11, 8, 10, 30, 0)
        
        # Debe poder calcular cierre aunque sea fin de semana
        next_close = candle_waiter_m1.get_next_candle_close_time(saturday)
        
        assert next_close.minute == 31
        # TimeValidator se encargará de rechazarlo


# ==================== TESTS DE CONFIGURACIÓN ====================

@pytest.mark.unit
class TestConfiguration:
    """Tests para manejo de configuración"""
    
    def test_strict_mode_enabled(self, sample_candle_config, mock_time_validator):
        """Debe respetar strict_mode"""
        sample_candle_config["candle_wait"]["strict_mode"] = True
        
        waiter = CandleWaiter("M1", sample_candle_config, mock_time_validator)
        
        assert waiter.strict_mode is True
    
    def test_custom_timeout(self, mock_time_validator):
        """Debe permitir timeout personalizado"""
        config = {
            "candle_wait": {"timeout_seconds": 600},
            "timeframes": {"M1": 60}
        }
        
        waiter = CandleWaiter("M1", config, mock_time_validator)
        
        assert waiter.timeout_seconds == 600
    
    def test_default_timeout_if_not_provided(self, mock_time_validator):
        """Debe usar timeout por defecto"""
        config = {"timeframes": {"M1": 60}}
        
        waiter = CandleWaiter("M1", config, mock_time_validator)
        
        assert waiter.timeout_seconds == 300  # Default


# ==================== TESTS DE FORMATO DE SALIDA ====================

@pytest.mark.unit
class TestOutputFormat:
    """Tests para formato de salida"""
    
    def test_get_wait_summary(self, candle_waiter_m1, mock_lima_time):
        """Debe retornar resumen de espera"""
        current = mock_lima_time(2025, 11, 6, 10, 30, 25)
        
        with patch.object(candle_waiter_m1.time_validator, 'get_current_lima_time', return_value=current):
            summary = candle_waiter_m1.get_wait_summary()
        
        assert isinstance(summary, dict)
        assert "timeframe" in summary
        assert "seconds_until_close" in summary
        assert "next_close_time" in summary
        assert "is_trading_time" in summary
