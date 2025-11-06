"""
Tests unitarios para el módulo quota_validator.

Este módulo implementa tests para el Ticket T48: Validación de cuota y 
disponibilidad de modelo IA, para evitar fallos por límites de uso.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T48 - Validación de cuota y disponibilidad de modelo IA
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from zoneinfo import ZoneInfo


# Importar clase a testear (TDD Red - aún no existe)
from src.core.quota_validator import (
    QuotaValidator,
    QuotaValidationError,
    QuotaStatus,
    ModelAvailability
)


# ==================== FIXTURES ====================

@pytest.fixture
def sample_quota_config():
    """Configuración de ejemplo para QuotaValidator"""
    return {
        "quota_validation": {
            "enabled": True,
            "provider": "gemini",
            "check_interval_seconds": 300,
            "cache_duration_seconds": 60,
            "quota_limits": {
                "requests_per_minute": 60,
                "requests_per_day": 1500,
                "tokens_per_minute": 32000,
                "tokens_per_day": 500000
            },
            "thresholds": {
                "warning_percentage": 80,
                "critical_percentage": 95
            },
            "retry": {
                "max_attempts": 3,
                "backoff_factor": 2,
                "timeout_seconds": 10
            }
        }
    }


@pytest.fixture
def mock_gemini_response():
    """Mock de respuesta de Gemini API"""
    def _create_response(
        available=True,
        requests_used=50,
        requests_limit=60,
        tokens_used=20000,
        tokens_limit=32000
    ):
        response = MagicMock()
        response.available = available
        response.requests_used = requests_used
        response.requests_limit = requests_limit
        response.tokens_used = tokens_used
        response.tokens_limit = tokens_limit
        return response
    return _create_response


@pytest.fixture
def quota_validator(sample_quota_config):
    """QuotaValidator configurado para tests"""
    return QuotaValidator(config=sample_quota_config)


# ==================== TESTS DE INICIALIZACIÓN ====================

@pytest.mark.unit
class TestQuotaValidatorInitialization:
    """Tests para la inicialización de QuotaValidator"""
    
    def test_init_with_valid_config(self, sample_quota_config):
        """Debe inicializar con configuración válida"""
        validator = QuotaValidator(config=sample_quota_config)
        
        assert validator.provider == "gemini"
        assert validator.enabled is True
        assert validator.check_interval_seconds == 300
    
    def test_init_with_disabled_validation(self):
        """Debe permitir desactivar validación"""
        config = {
            "quota_validation": {
                "enabled": False,
                "provider": "gemini"
            }
        }
        validator = QuotaValidator(config=config)
        
        assert validator.enabled is False
    
    def test_init_with_custom_limits(self):
        """Debe permitir límites personalizados"""
        config = {
            "quota_validation": {
                "enabled": True,
                "provider": "gemini",
                "quota_limits": {
                    "requests_per_minute": 100,
                    "tokens_per_day": 1000000
                }
            }
        }
        validator = QuotaValidator(config=config)
        
        assert validator.quota_limits["requests_per_minute"] == 100
        assert validator.quota_limits["tokens_per_day"] == 1000000
    
    def test_init_validates_provider(self):
        """Debe validar que el provider sea soportado"""
        config = {
            "quota_validation": {
                "enabled": True,
                "provider": "invalid_provider"
            }
        }
        
        with pytest.raises(QuotaValidationError, match="Provider.*no soportado"):
            QuotaValidator(config=config)
    
    def test_init_with_defaults_if_no_config(self):
        """Debe usar valores por defecto si no hay configuración"""
        validator = QuotaValidator(config={})
        
        assert validator.enabled is False  # Desactivado por defecto por seguridad


# ==================== TESTS DE VALIDACIÓN DE CUOTA ====================

@pytest.mark.unit
class TestQuotaValidation:
    """Tests para validación de cuota"""
    
    def test_validate_quota_returns_true_when_available(
        self, quota_validator, mock_gemini_response
    ):
        """Debe retornar True cuando hay cuota disponible"""
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_gemini_response(
                available=True,
                requests_used=30,
                requests_limit=60
            )
        ):
            result = quota_validator.validate_quota()
            
            assert result.is_valid is True
            assert result.status == QuotaStatus.AVAILABLE
    
    def test_validate_quota_returns_false_when_exceeded(
        self, quota_validator, mock_gemini_response
    ):
        """Debe retornar False cuando se excedió la cuota"""
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_gemini_response(
                available=False,
                requests_used=60,
                requests_limit=60
            )
        ):
            result = quota_validator.validate_quota()
            
            assert result.is_valid is False
            assert result.status == QuotaStatus.EXCEEDED
    
    def test_validate_quota_warns_at_threshold(
        self, quota_validator, mock_gemini_response
    ):
        """Debe advertir cuando se alcanza el umbral de warning"""
        # 80% threshold: 48 de 60 requests
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_gemini_response(
                available=True,
                requests_used=48,
                requests_limit=60
            )
        ):
            result = quota_validator.validate_quota()
            
            assert result.is_valid is True
            assert result.status == QuotaStatus.WARNING
            assert "80.0%" in result.message or "advertencia" in result.message.lower()
    
    def test_validate_quota_critical_at_high_threshold(
        self, quota_validator, mock_gemini_response
    ):
        """Debe marcar como crítico cuando se alcanza el umbral alto"""
        # 95% threshold: 57 de 60 requests
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_gemini_response(
                available=True,
                requests_used=57,
                requests_limit=60
            )
        ):
            result = quota_validator.validate_quota()
            
            assert result.is_valid is True
            assert result.status == QuotaStatus.CRITICAL
    
    def test_validate_quota_skips_when_disabled(self):
        """Debe saltarse validación cuando está desactivada"""
        config = {
            "quota_validation": {"enabled": False}
        }
        validator = QuotaValidator(config=config)
        
        result = validator.validate_quota()
        
        assert result.is_valid is True
        assert result.status == QuotaStatus.DISABLED


# ==================== TESTS DE DISPONIBILIDAD DE MODELO ====================

@pytest.mark.unit
class TestModelAvailability:
    """Tests para verificar disponibilidad del modelo"""
    
    def test_check_model_availability_returns_true_when_available(
        self, quota_validator
    ):
        """Debe retornar True cuando el modelo está disponible"""
        with patch.object(
            quota_validator, '_check_gemini_model_status',
            return_value=ModelAvailability(
                available=True,
                model="gemini-2.5-pro",
                status="active"
            )
        ):
            result = quota_validator.check_model_availability()
            
            assert result.available is True
            assert result.status == "active"
    
    def test_check_model_availability_returns_false_when_maintenance(
        self, quota_validator
    ):
        """Debe retornar False cuando el modelo está en mantenimiento"""
        with patch.object(
            quota_validator, '_check_gemini_model_status',
            return_value=ModelAvailability(
                available=False,
                model="gemini-2.5-pro",
                status="maintenance"
            )
        ):
            result = quota_validator.check_model_availability()
            
            assert result.available is False
            assert result.status == "maintenance"
    
    def test_check_model_availability_handles_invalid_model(
        self, quota_validator
    ):
        """Debe manejar modelo inválido o no encontrado"""
        with patch.object(
            quota_validator, '_check_gemini_model_status',
            side_effect=QuotaValidationError("Modelo no encontrado")
        ):
            with pytest.raises(QuotaValidationError, match="Modelo no encontrado"):
                quota_validator.check_model_availability()


# ==================== TESTS DE CACHÉ ====================

@pytest.mark.unit
class TestQuotaCache:
    """Tests para el sistema de caché de validaciones"""
    
    def test_validate_quota_uses_cache_within_duration(
        self, quota_validator, mock_gemini_response
    ):
        """Debe usar caché si está dentro del tiempo de validez"""
        mock_response = mock_gemini_response(available=True)
        
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_response
        ) as mock_check:
            # Primera llamada: consulta API
            result1 = quota_validator.validate_quota()
            
            # Segunda llamada inmediata: debe usar caché
            result2 = quota_validator.validate_quota()
            
            # Solo debe haber consultado la API una vez
            assert mock_check.call_count == 1
            assert result1.is_valid == result2.is_valid
    
    def test_validate_quota_refreshes_after_cache_expiry(
        self, quota_validator, mock_gemini_response
    ):
        """Debe refrescar caché cuando expira"""
        mock_response = mock_gemini_response(available=True)
        
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_response
        ) as mock_check:
            # Primera llamada
            quota_validator.validate_quota()
            
            # Simular expiración de caché (modificar timestamp)
            quota_validator._cache_timestamp = datetime.now() - timedelta(seconds=120)
            
            # Segunda llamada después de expiración
            quota_validator.validate_quota()
            
            # Debe haber consultado la API dos veces
            assert mock_check.call_count == 2
    
    def test_clear_cache_forces_revalidation(
        self, quota_validator, mock_gemini_response
    ):
        """Debe forzar revalidación cuando se limpia el caché"""
        mock_response = mock_gemini_response(available=True)
        
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_response
        ) as mock_check:
            # Primera llamada
            quota_validator.validate_quota()
            
            # Limpiar caché
            quota_validator.clear_cache()
            
            # Segunda llamada
            quota_validator.validate_quota()
            
            # Debe haber consultado la API dos veces
            assert mock_check.call_count == 2


# ==================== TESTS DE REINTENTOS ====================

@pytest.mark.unit
class TestQuotaRetry:
    """Tests para reintentos ante fallos"""
    
    def test_validate_quota_retries_on_network_error(
        self, quota_validator
    ):
        """Debe reintentar ante errores de red"""
        mock_responses = [
            Exception("Network error"),
            Exception("Network error"),
            MagicMock(available=True, requests_used=10, requests_limit=60)
        ]
        
        with patch.object(
            quota_validator, '_check_gemini_quota',
            side_effect=mock_responses
        ) as mock_check:
            result = quota_validator.validate_quota()
            
            # Debe haber intentado 3 veces
            assert mock_check.call_count == 3
            # Finalmente debe haber tenido éxito
            assert result.is_valid is True
    
    def test_validate_quota_fails_after_max_retries(
        self, quota_validator
    ):
        """Debe fallar después de agotar reintentos"""
        with patch.object(
            quota_validator, '_check_gemini_quota',
            side_effect=Exception("Network error")
        ) as mock_check:
            with pytest.raises(QuotaValidationError, match="reintentos agotados"):
                quota_validator.validate_quota()
            
            # Debe haber intentado max_attempts veces
            assert mock_check.call_count == 3


# ==================== TESTS DE ESTADÍSTICAS ====================

@pytest.mark.unit
class TestQuotaStatistics:
    """Tests para estadísticas de uso"""
    
    def test_get_quota_summary_returns_complete_info(
        self, quota_validator, mock_gemini_response
    ):
        """Debe retornar resumen completo de cuota"""
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_gemini_response(
                available=True,
                requests_used=30,
                requests_limit=60,
                tokens_used=15000,
                tokens_limit=32000
            )
        ):
            summary = quota_validator.get_quota_summary()
            
            assert "requests_used" in summary
            assert "requests_limit" in summary
            assert "requests_percentage" in summary
            assert summary["requests_percentage"] == 50.0
            assert "tokens_used" in summary
            assert "status" in summary
    
    def test_calculate_remaining_requests(
        self, quota_validator, mock_gemini_response
    ):
        """Debe calcular requests restantes correctamente"""
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_gemini_response(
                requests_used=45,
                requests_limit=60
            )
        ):
            remaining = quota_validator.calculate_remaining_requests()
            
            assert remaining == 15
    
    def test_estimate_time_to_quota_reset(
        self, quota_validator
    ):
        """Debe estimar tiempo hasta reset de cuota"""
        # El método calcula hasta el próximo minuto
        time_to_reset = quota_validator.estimate_time_to_quota_reset()
        
        # Debe ser entre 0 y 60 segundos (0 si estamos exactamente al inicio del minuto)
        assert 0 <= time_to_reset <= 60


# ==================== TESTS DE VALIDACIÓN COMPLETA ====================

@pytest.mark.unit
class TestCompleteValidation:
    """Tests para validación completa (cuota + modelo)"""
    
    def test_validate_all_returns_true_when_everything_ok(
        self, quota_validator, mock_gemini_response
    ):
        """Debe retornar True cuando cuota y modelo están OK"""
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_gemini_response(available=True)
        ):
            with patch.object(
                quota_validator, '_check_gemini_model_status',
                return_value=ModelAvailability(
                    available=True,
                    model="gemini-2.5-pro",
                    status="active"
                )
            ):
                result = quota_validator.validate_all()
                
                assert result.is_valid is True
                assert result.quota_ok is True
                assert result.model_ok is True
    
    def test_validate_all_returns_false_if_quota_exceeded(
        self, quota_validator, mock_gemini_response
    ):
        """Debe retornar False si la cuota está excedida"""
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_gemini_response(
                available=False,
                requests_used=60,
                requests_limit=60
            )
        ):
            result = quota_validator.validate_all()
            
            assert result.is_valid is False
            assert result.quota_ok is False
    
    def test_validate_all_returns_false_if_model_unavailable(
        self, quota_validator, mock_gemini_response
    ):
        """Debe retornar False si el modelo no está disponible"""
        with patch.object(
            quota_validator, '_check_gemini_quota',
            return_value=mock_gemini_response(available=True)
        ):
            with patch.object(
                quota_validator, '_check_gemini_model_status',
                return_value=ModelAvailability(
                    available=False,
                    model="gemini-2.5-pro",
                    status="maintenance"
                )
            ):
                result = quota_validator.validate_all()
                
                assert result.is_valid is False
                assert result.model_ok is False


# ==================== TESTS DE INTEGRACIÓN ====================

@pytest.mark.integration
class TestCredentialManagerIntegration:
    """Tests de integración con CredentialManager"""
    
    def test_loads_api_key_from_credential_manager(self, sample_quota_config):
        """Debe cargar API key desde CredentialManager"""
        from src.core.credential_manager import CredentialManager
        
        # Este test verifica la integración pero requiere
        # que CredentialManager esté disponible
        validator = QuotaValidator(config=sample_quota_config)
        
        # Verificar que tiene método para obtener credenciales
        assert hasattr(validator, '_get_api_credentials')


# ==================== TESTS DE CONFIGURACIÓN ====================

@pytest.mark.unit
class TestConfiguration:
    """Tests para manejo de configuración"""
    
    def test_reload_config_updates_limits(self, quota_validator):
        """Debe actualizar límites al recargar configuración"""
        new_config = {
            "quota_validation": {
                "enabled": True,
                "provider": "gemini",
                "quota_limits": {
                    "requests_per_minute": 120
                }
            }
        }
        
        quota_validator.reload_config(new_config)
        
        assert quota_validator.quota_limits["requests_per_minute"] == 120
    
    def test_supports_multiple_providers(self):
        """Debe soportar múltiples providers (extensibilidad futura)"""
        # Gemini está implementado
        config_gemini = {
            "quota_validation": {
                "enabled": True,
                "provider": "gemini"
            }
        }
        validator = QuotaValidator(config=config_gemini)
        assert validator.provider == "gemini"
        
        # Otros providers lanzan error por ahora
        unsupported_providers = ["openai", "anthropic"]
        for provider in unsupported_providers:
            config = {
                "quota_validation": {
                    "enabled": True,
                    "provider": provider
                }
            }
            with pytest.raises(QuotaValidationError, match="no (soportado|está implementado)"):
                QuotaValidator(config=config)
