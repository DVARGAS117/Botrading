"""
Tests unitarios para el módulo retry_handler.

Implementa pruebas para el Ticket T38: Reintentos automáticos con backoff,
verificando que las llamadas a MT5 o IA fallen temporalmente se reintenten
automáticamente con backoff exponencial.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T38 - Reintentos automáticos con backoff
"""
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any


# ==================== FIXTURES ====================

@pytest.fixture
def retry_config():
    """Configuración básica de reintentos para tests"""
    from src.core.retry_handler import RetryConfig
    return RetryConfig(
        max_attempts=3,
        initial_delay=0.1,  # 100ms para tests rápidos
        max_delay=1.0,
        backoff_factor=2.0,
        exponential_base=2
    )


@pytest.fixture
def retry_handler(retry_config):
    """Handler de reintentos configurado para tests"""
    from src.core.retry_handler import RetryHandler
    return RetryHandler(retry_config)


# ==================== TESTS DE CONFIGURACIÓN ====================

class TestRetryConfig:
    """Tests para la configuración de reintentos"""
    
    def test_default_config_values(self):
        """Debe crear configuración con valores por defecto"""
        from src.core.retry_handler import RetryConfig
        
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.backoff_factor == 2.0
        assert config.exponential_base == 2
        assert config.jitter is True
    
    def test_custom_config_values(self):
        """Debe permitir configuración personalizada"""
        from src.core.retry_handler import RetryConfig
        
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=60.0,
            backoff_factor=3.0,
            exponential_base=2,
            jitter=False
        )
        
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 60.0
        assert config.backoff_factor == 3.0
        assert config.exponential_base == 2
        assert config.jitter is False
    
    def test_config_validation_max_attempts(self):
        """Debe validar que max_attempts sea al menos 1"""
        from src.core.retry_handler import RetryConfig, RetryConfigError
        
        with pytest.raises(RetryConfigError, match="max_attempts debe ser al menos 1"):
            RetryConfig(max_attempts=0)
    
    def test_config_validation_delays(self):
        """Debe validar que los delays sean positivos"""
        from src.core.retry_handler import RetryConfig, RetryConfigError
        
        with pytest.raises(RetryConfigError, match="initial_delay debe ser positivo"):
            RetryConfig(initial_delay=-1.0)
        
        with pytest.raises(RetryConfigError, match="max_delay debe ser positivo"):
            RetryConfig(max_delay=-1.0)
    
    def test_config_validation_backoff_factor(self):
        """Debe validar que backoff_factor sea mayor que 1"""
        from src.core.retry_handler import RetryConfig, RetryConfigError
        
        with pytest.raises(RetryConfigError, match="backoff_factor debe ser mayor que 1"):
            RetryConfig(backoff_factor=0.5)


# ==================== TESTS DE REINTENTOS EXITOSOS ====================

class TestSuccessfulRetry:
    """Tests para reintentos que eventualmente tienen éxito"""
    
    def test_retry_succeeds_on_first_attempt(self, retry_handler):
        """Debe ejecutar sin reintentos si tiene éxito la primera vez"""
        mock_func = Mock(return_value="success")
        
        result = retry_handler.execute(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_succeeds_on_second_attempt(self, retry_handler):
        """Debe reintentar y tener éxito en el segundo intento"""
        mock_func = Mock(side_effect=[Exception("Temp error"), "success"])
        
        result = retry_handler.execute(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_succeeds_on_last_attempt(self, retry_config):
        """Debe tener éxito en el último intento antes de agotar reintentos"""
        from src.core.retry_handler import RetryHandler
        
        handler = RetryHandler(retry_config)
        mock_func = Mock(side_effect=[
            Exception("Error 1"),
            Exception("Error 2"),
            "success"  # Tercer intento (último)
        ])
        
        result = handler.execute(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_retry_with_args_and_kwargs(self, retry_handler):
        """Debe pasar correctamente args y kwargs en reintentos"""
        mock_func = Mock(side_effect=[Exception("Error"), "success"])
        
        result = retry_handler.execute(
            mock_func,
            "arg1", "arg2",
            key1="value1",
            key2="value2"
        )
        
        assert result == "success"
        assert mock_func.call_count == 2
        
        # Verificar que los argumentos se pasaron correctamente
        mock_func.assert_called_with("arg1", "arg2", key1="value1", key2="value2")


# ==================== TESTS DE REINTENTOS AGOTADOS ====================

class TestExhaustedRetries:
    """Tests para cuando se agotan los reintentos"""
    
    def test_retry_exhausted_raises_exception(self, retry_handler):
        """Debe lanzar excepción cuando se agotan los reintentos"""
        from src.core.retry_handler import RetryExhaustedError
        
        mock_func = Mock(side_effect=Exception("Persistent error"))
        
        with pytest.raises(RetryExhaustedError) as exc_info:
            retry_handler.execute(mock_func)
        
        assert "agotados todos los intentos" in str(exc_info.value).lower()
        assert mock_func.call_count == 3  # max_attempts
    
    def test_retry_exhausted_includes_original_exception(self, retry_handler):
        """Debe incluir la excepción original en RetryExhaustedError"""
        from src.core.retry_handler import RetryExhaustedError
        
        original_error = ValueError("Original error message")
        mock_func = Mock(side_effect=original_error)
        
        with pytest.raises(RetryExhaustedError) as exc_info:
            retry_handler.execute(mock_func)
        
        assert exc_info.value.last_exception == original_error
        assert exc_info.value.attempts == 3
    
    def test_retry_exhausted_logs_all_attempts(self, retry_handler):
        """Debe registrar todos los intentos fallidos"""
        mock_func = Mock(side_effect=Exception("Error"))
        
        with pytest.raises(Exception):
            retry_handler.execute(mock_func)
        
        # Verificar que se registraron todos los intentos
        attempts = retry_handler.get_last_attempts()
        assert len(attempts) == 3
        assert all(not attempt["success"] for attempt in attempts)


# ==================== TESTS DE BACKOFF EXPONENCIAL ====================

class TestExponentialBackoff:
    """Tests para el mecanismo de backoff exponencial"""
    
    def test_backoff_delay_increases_exponentially(self, retry_config):
        """Debe incrementar el delay exponencialmente entre reintentos"""
        from src.core.retry_handler import RetryHandler
        
        handler = RetryHandler(retry_config)
        mock_func = Mock(side_effect=Exception("Error"))
        
        start_time = time.time()
        
        with pytest.raises(Exception):
            handler.execute(mock_func)
        
        elapsed_time = time.time() - start_time
        
        # Calcular tiempo mínimo esperado con backoff exponencial
        # initial_delay = 0.1, backoff_factor = 2.0
        # Intento 1: falla (sin delay antes)
        # Intento 2: falla después de 0.1s delay
        # Intento 3: falla después de 0.2s delay
        # Total mínimo: ~0.3s
        expected_min_time = retry_config.initial_delay + (
            retry_config.initial_delay * retry_config.backoff_factor
        )
        
        assert elapsed_time >= expected_min_time * 0.8  # Permitir 20% margen
    
    def test_backoff_respects_max_delay(self):
        """Debe respetar el max_delay configurado"""
        from src.core.retry_handler import RetryConfig, RetryHandler
        
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.1,
            max_delay=0.2,  # Límite bajo
            backoff_factor=2.0,
            jitter=False
        )
        handler = RetryHandler(config)
        
        # Calcular delays esperados
        delays = []
        for attempt in range(1, 5):
            delay = handler._calculate_delay(attempt)
            delays.append(delay)
        
        # Ningún delay debe exceder max_delay
        assert all(delay <= config.max_delay for delay in delays)
    
    def test_backoff_with_jitter_adds_randomness(self):
        """Debe agregar jitter aleatorio al delay"""
        from src.core.retry_handler import RetryConfig, RetryHandler
        
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
            backoff_factor=2.0,
            jitter=True
        )
        handler = RetryHandler(config)
        
        # Calcular múltiples delays para el mismo intento
        delays = [handler._calculate_delay(1) for _ in range(10)]
        
        # Debe haber variación debido al jitter
        unique_delays = set(delays)
        assert len(unique_delays) > 1  # No todos deben ser iguales


# ==================== TESTS DE EXCEPCIONES ESPECÍFICAS ====================

class TestSpecificExceptions:
    """Tests para manejo de excepciones específicas"""
    
    def test_retry_only_on_specified_exceptions(self):
        """Debe reintentar solo para excepciones especificadas"""
        from src.core.retry_handler import RetryConfig, RetryHandler
        
        config = RetryConfig(
            max_attempts=3,
            retry_on=(ConnectionError, TimeoutError)
        )
        handler = RetryHandler(config)
        
        # Debe reintentar ConnectionError
        mock_func = Mock(side_effect=[ConnectionError("Error"), "success"])
        result = handler.execute(mock_func)
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_no_retry_on_non_specified_exceptions(self):
        """No debe reintentar para excepciones no especificadas"""
        from src.core.retry_handler import RetryConfig, RetryHandler
        
        config = RetryConfig(
            max_attempts=3,
            retry_on=(ConnectionError,)
        )
        handler = RetryHandler(config)
        
        # No debe reintentar ValueError
        mock_func = Mock(side_effect=ValueError("Error"))
        
        with pytest.raises(ValueError):
            handler.execute(mock_func)
        
        assert mock_func.call_count == 1  # Solo un intento


# ==================== TESTS DEL DECORADOR ====================

class TestRetryDecorator:
    """Tests para el decorador @with_retry"""
    
    def test_decorator_basic_usage(self):
        """Debe funcionar como decorador básico"""
        from src.core.retry_handler import with_retry, RetryConfig
        
        call_count = {"count": 0}
        
        @with_retry(RetryConfig(max_attempts=3, initial_delay=0.1))
        def test_function():
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise Exception("Temp error")
            return "success"
        
        result = test_function()
        
        assert result == "success"
        assert call_count["count"] == 2
    
    def test_decorator_with_default_config(self):
        """Debe usar configuración por defecto si no se especifica"""
        from src.core.retry_handler import with_retry
        
        @with_retry()
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_decorator_preserves_function_metadata(self):
        """Debe preservar metadata de la función decorada"""
        from src.core.retry_handler import with_retry
        
        @with_retry()
        def test_function():
            """Test docstring"""
            return "success"
        
        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test docstring"


# ==================== TESTS DE REGISTRO DE INTENTOS ====================

class TestAttemptLogging:
    """Tests para el registro de intentos"""
    
    def test_records_all_attempts(self, retry_handler):
        """Debe registrar todos los intentos realizados"""
        mock_func = Mock(side_effect=[
            Exception("Error 1"),
            Exception("Error 2"),
            "success"
        ])
        
        result = retry_handler.execute(mock_func)
        
        attempts = retry_handler.get_last_attempts()
        assert len(attempts) == 3
        
        # Verificar estructura de cada intento
        for attempt in attempts:
            assert "attempt_number" in attempt
            assert "success" in attempt
            assert "timestamp" in attempt
    
    def test_attempt_includes_exception_info(self, retry_handler):
        """Debe incluir información de la excepción en intentos fallidos"""
        mock_func = Mock(side_effect=[
            ValueError("Specific error"),
            "success"
        ])
        
        result = retry_handler.execute(mock_func)
        
        attempts = retry_handler.get_last_attempts()
        failed_attempt = attempts[0]
        
        assert not failed_attempt["success"]
        assert "exception_type" in failed_attempt
        assert "exception_message" in failed_attempt
        assert failed_attempt["exception_type"] == "ValueError"
        assert "Specific error" in failed_attempt["exception_message"]
    
    def test_successful_attempt_marked_correctly(self, retry_handler):
        """Debe marcar correctamente los intentos exitosos"""
        mock_func = Mock(return_value="success")
        
        result = retry_handler.execute(mock_func)
        
        attempts = retry_handler.get_last_attempts()
        assert len(attempts) == 1
        assert attempts[0]["success"] is True
        assert "exception_type" not in attempts[0]


# ==================== TESTS DE INTEGRACIÓN ====================

class TestIntegration:
    """Tests de integración con otros componentes"""
    
    def test_integration_with_logger(self, retry_handler):
        """Debe integrarse correctamente con el sistema de logging"""
        from src.core.logger import BotLogger, LogConfig
        
        logger = BotLogger("test_bot", LogConfig(log_to_file=False))
        
        with patch.object(logger, 'warning') as mock_warning:
            mock_func = Mock(side_effect=[Exception("Error"), "success"])
            
            retry_handler.execute(mock_func, logger=logger)
            
            # Debe loggear el reintento
            assert mock_warning.called
    
    def test_mt5_connection_retry_scenario(self):
        """Debe manejar escenario de reconexión MT5"""
        from src.core.retry_handler import RetryHandler, RetryConfig
        
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
            retry_on=(ConnectionError,)
        )
        handler = RetryHandler(config)
        
        # Simular fallo de conexión seguido de éxito
        mock_mt5_connect = Mock(side_effect=[
            ConnectionError("MT5 not available"),
            {"connected": True}
        ])
        
        result = handler.execute(mock_mt5_connect)
        
        assert result == {"connected": True}
        assert mock_mt5_connect.call_count == 2
    
    def test_ia_api_retry_scenario(self):
        """Debe manejar escenario de reintento de API de IA"""
        from src.core.retry_handler import RetryHandler, RetryConfig
        
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
            retry_on=(TimeoutError, ConnectionError)
        )
        handler = RetryHandler(config)
        
        # Simular timeout seguido de respuesta exitosa
        mock_ia_query = Mock(side_effect=[
            TimeoutError("Request timeout"),
            {"decision": "BUY", "confidence": 0.85}
        ])
        
        result = handler.execute(mock_ia_query)
        
        assert result["decision"] == "BUY"
        assert mock_ia_query.call_count == 2


# ==================== TESTS DE CASOS EXTREMOS ====================

class TestEdgeCases:
    """Tests para casos extremos"""
    
    def test_zero_delay_between_retries(self):
        """Debe manejar delay cero sin errores"""
        from src.core.retry_handler import RetryConfig, RetryHandler
        
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.0,
            backoff_factor=2.0
        )
        handler = RetryHandler(config)
        
        mock_func = Mock(side_effect=[Exception("Error"), "success"])
        result = handler.execute(mock_func)
        
        assert result == "success"
    
    def test_very_high_max_attempts(self):
        """Debe manejar número muy alto de intentos"""
        from src.core.retry_handler import RetryConfig, RetryHandler
        
        config = RetryConfig(
            max_attempts=100,
            initial_delay=0.001  # Muy rápido para test
        )
        handler = RetryHandler(config)
        
        call_count = {"count": 0}
        
        def func_that_succeeds_eventually():
            call_count["count"] += 1
            if call_count["count"] < 10:
                raise Exception("Not yet")
            return "success"
        
        result = handler.execute(func_that_succeeds_eventually)
        
        assert result == "success"
        assert call_count["count"] == 10
    
    def test_function_with_no_return_value(self, retry_handler):
        """Debe manejar funciones sin valor de retorno"""
        mock_func = Mock(return_value=None)
        
        result = retry_handler.execute(mock_func)
        
        assert result is None
        assert mock_func.call_count == 1


# ==================== TESTS DE CONTEXTO ====================

class TestContextManager:
    """Tests para uso como context manager"""
    
    def test_retry_handler_as_context_manager(self):
        """Debe funcionar como context manager"""
        from src.core.retry_handler import RetryHandler, RetryConfig
        
        config = RetryConfig(max_attempts=3, initial_delay=0.1)
        
        with RetryHandler(config) as handler:
            mock_func = Mock(side_effect=[Exception("Error"), "success"])
            result = handler.execute(mock_func)
            
            assert result == "success"
    
    def test_context_manager_cleanup(self):
        """Debe realizar cleanup al salir del contexto"""
        from src.core.retry_handler import RetryHandler, RetryConfig
        
        config = RetryConfig(max_attempts=3, initial_delay=0.1)
        handler = RetryHandler(config)
        
        with handler as h:
            mock_func = Mock(return_value="success")
            h.execute(mock_func)
        
        # Después de salir del contexto, debe limpiar intentos
        attempts = handler.get_last_attempts()
        assert len(attempts) == 0 or attempts is None


# ==================== TESTS DE CRITERIOS DE ACEPTACIÓN ====================

class TestAcceptanceCriteria:
    """
    Tests que verifican los criterios de aceptación del Ticket T38.
    
    Escenario: Reintentos automáticos con backoff
        Dado que una llamada a MT5 o IA falla temporalmente
        Cuando el bot aplica hasta tres reintentos con backoff
        Entonces la operación continúa si el reintento tiene éxito
        O se aborta con registro si no
    """
    
    def test_acceptance_temporary_failure_then_success(self):
        """
        Criterio de aceptación: Operación continúa si reintento tiene éxito
        """
        from src.core.retry_handler import RetryHandler, RetryConfig
        
        # DADO que una llamada a MT5 o IA falla temporalmente
        config = RetryConfig(max_attempts=3, initial_delay=0.1)
        handler = RetryHandler(config)
        
        mock_operation = Mock(side_effect=[
            ConnectionError("MT5 connection failed"),  # Fallo temporal
            "operation_successful"  # Éxito en reintento
        ])
        
        # CUANDO el bot aplica hasta tres reintentos con backoff
        result = handler.execute(mock_operation)
        
        # ENTONCES la operación continúa si el reintento tiene éxito
        assert result == "operation_successful"
        assert mock_operation.call_count == 2
    
    def test_acceptance_all_retries_exhausted(self):
        """
        Criterio de aceptación: Se aborta con registro si no tiene éxito
        """
        from src.core.retry_handler import (
            RetryHandler, 
            RetryConfig, 
            RetryExhaustedError
        )
        
        # DADO que una llamada falla persistentemente
        config = RetryConfig(max_attempts=3, initial_delay=0.1)
        handler = RetryHandler(config)
        
        mock_operation = Mock(side_effect=ConnectionError("Persistent failure"))
        
        # CUANDO el bot aplica hasta tres reintentos con backoff
        # ENTONCES se aborta con registro si no tiene éxito
        with pytest.raises(RetryExhaustedError) as exc_info:
            handler.execute(mock_operation)
        
        # Verificar que se registraron todos los intentos
        assert mock_operation.call_count == 3
        assert exc_info.value.attempts == 3
        
        # Verificar que hay registro de los intentos
        attempts = handler.get_last_attempts()
        assert len(attempts) == 3
        assert all(not attempt["success"] for attempt in attempts)
    
    def test_acceptance_backoff_applied(self):
        """
        Criterio de aceptación: Se aplica backoff entre reintentos
        """
        from src.core.retry_handler import RetryHandler, RetryConfig
        
        # DADO que una llamada falla temporalmente
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.1,
            backoff_factor=2.0
        )
        handler = RetryHandler(config)
        
        mock_operation = Mock(side_effect=Exception("Temp error"))
        
        # CUANDO el bot aplica reintentos con backoff
        start_time = time.time()
        
        with pytest.raises(Exception):
            handler.execute(mock_operation)
        
        elapsed_time = time.time() - start_time
        
        # ENTONCES debe haber delay exponencial entre intentos
        # Delay esperado: 0.1 + 0.2 = 0.3s mínimo
        expected_min_time = 0.3
        assert elapsed_time >= expected_min_time * 0.8  # Margen 20%
