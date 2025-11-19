"""
Tests unitarios para IAConfigManager - Alternancia de configuraciones de IA por bot

Este módulo contiene todos los tests para validar la funcionalidad del gestor
de configuraciones de IA que permite alternar entre diferentes perfiles (modelos,
providers, parámetros) por bot.

Tickets relacionados: T49, T48 (QuotaValidator), T44 (ConfigLoader)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import json

# Imports del módulo a testear (aún no existe - TDD Red)
from src.core.ia_config_manager import (
    IAConfigManager,
    IAProfile,
    IAProvider,
    IAConfigError
)


class TestIAConfigManagerInitialization:
    """Tests de inicialización del IAConfigManager"""
    
    def test_init_with_valid_config(self):
        """Debe inicializar correctamente con configuración válida"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {
                        "provider": "gemini",
                        "model": "gemini-2.5-pro",
                        "temperature": 0.7
                    }
                }
            }
        }
        
        manager = IAConfigManager(config=config)
        
        assert manager is not None
        assert manager.default_profile == "gemini-pro"
        assert len(manager.profiles) == 1
    
    def test_init_loads_multiple_profiles(self):
        """Debe cargar múltiples perfiles correctamente"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"},
                    "gpt-4": {"provider": "openai", "model": "gpt-4"},
                    "claude": {"provider": "anthropic", "model": "claude-3"}
                }
            }
        }
        
        manager = IAConfigManager(config=config)
        
        assert len(manager.profiles) == 3
        assert "gemini-pro" in manager.profiles
        assert "gpt-4" in manager.profiles
        assert "claude" in manager.profiles
    
    def test_init_validates_default_profile_exists(self):
        """Debe validar que el perfil por defecto exista"""
        config = {
            "ia_profiles": {
                "default_profile": "non-existent",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"}
                }
            }
        }
        
        with pytest.raises(IAConfigError, match="Perfil por defecto.*no existe"):
            IAConfigManager(config=config)
    
    def test_init_with_empty_profiles_raises_error(self):
        """Debe fallar si no hay perfiles configurados"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {}
            }
        }
        
        with pytest.raises(IAConfigError, match="No hay perfiles.*configurados"):
            IAConfigManager(config=config)
    
    def test_init_uses_defaults_if_no_config(self):
        """Debe usar configuración por defecto si no se proporciona"""
        manager = IAConfigManager()
        
        assert manager.default_profile is not None
        assert len(manager.profiles) > 0
        assert "gemini-pro" in manager.profiles  # Default


class TestProfileLoading:
    """Tests de carga de perfiles de IA"""
    
    def test_load_profile_returns_correct_data(self):
        """Debe cargar un perfil específico correctamente"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {
                        "provider": "gemini",
                        "model": "gemini-1.5-pro",
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        profile = manager.load_profile("gemini-pro")
        
        assert isinstance(profile, IAProfile)
        assert profile.provider == IAProvider.GEMINI
        assert profile.model == "gemini-1.5-pro"
        assert profile.temperature == 0.7
        assert profile.max_tokens == 1000
    
    def test_load_profile_with_nonexistent_name_raises_error(self):
        """Debe fallar al intentar cargar perfil inexistente"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"}
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        with pytest.raises(IAConfigError, match="Perfil.*no encontrado"):
            manager.load_profile("non-existent-profile")
    
    def test_get_default_profile(self):
        """Debe retornar el perfil por defecto"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"},
                    "gpt-4": {"provider": "openai", "model": "gpt-4"}
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        profile = manager.get_default_profile()
        
        assert profile.model == "gemini-1.5-pro"


class TestBotProfileAssignment:
    """Tests de asignación de perfiles a bots específicos"""
    
    def test_get_profile_for_bot_returns_assigned_profile(self):
        """Debe retornar el perfil asignado a un bot específico"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"},
                    "gpt-4": {"provider": "openai", "model": "gpt-4"}
                },
                "bot_assignments": {
                    "bot_1": "gemini-pro",
                    "bot_2": "gpt-4"
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        profile_bot1 = manager.get_profile_for_bot("bot_1")
        profile_bot2 = manager.get_profile_for_bot("bot_2")
        
        assert profile_bot1.model == "gemini-1.5-pro"
        assert profile_bot2.model == "gpt-4"
    
    def test_get_profile_for_bot_returns_default_if_not_assigned(self):
        """Debe retornar perfil por defecto si bot no tiene asignación"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"}
                },
                "bot_assignments": {}
            }
        }
        manager = IAConfigManager(config=config)
        
        profile = manager.get_profile_for_bot("bot_3")
        
        assert profile.model == "gemini-1.5-pro"  # Default
    
    def test_assign_profile_to_bot(self):
        """Debe permitir asignar un perfil a un bot"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"},
                    "gpt-4": {"provider": "openai", "model": "gpt-4"}
                },
                "bot_assignments": {}
            }
        }
        manager = IAConfigManager(config=config)
        
        manager.assign_profile_to_bot("bot_1", "gpt-4")
        profile = manager.get_profile_for_bot("bot_1")
        
        assert profile.model == "gpt-4"
    
    def test_assign_profile_validates_profile_exists(self):
        """Debe validar que el perfil existe al asignar"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"}
                },
                "bot_assignments": {}
            }
        }
        manager = IAConfigManager(config=config)
        
        with pytest.raises(IAConfigError, match="Perfil.*no existe"):
            manager.assign_profile_to_bot("bot_1", "non-existent")


class TestProfileSwitching:
    """Tests de alternancia de perfiles"""
    
    def test_switch_profile_for_bot(self):
        """Debe permitir cambiar el perfil de un bot"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"},
                    "gpt-4": {"provider": "openai", "model": "gpt-4"}
                },
                "bot_assignments": {
                    "bot_1": "gemini-pro"
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        # Verificar perfil inicial
        initial = manager.get_profile_for_bot("bot_1")
        assert initial.model == "gemini-1.5-pro"
        
        # Cambiar perfil
        manager.switch_profile("bot_1", "gpt-4")
        
        # Verificar nuevo perfil
        updated = manager.get_profile_for_bot("bot_1")
        assert updated.model == "gpt-4"
    
    def test_switch_profile_logs_change(self):
        """Debe registrar el cambio de perfil en logs"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"},
                    "gpt-4": {"provider": "openai", "model": "gpt-4"}
                },
                "bot_assignments": {"bot_1": "gemini-pro"}
            }
        }
        manager = IAConfigManager(config=config)
        
        with patch.object(manager, 'logger') as mock_logger:
            manager.switch_profile("bot_1", "gpt-4")
            
            mock_logger.info.assert_called()
    
    def test_switch_profile_tracks_history(self):
        """Debe mantener historial de cambios de perfil"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"},
                    "gpt-4": {"provider": "openai", "model": "gpt-4"}
                },
                "bot_assignments": {"bot_1": "gemini-pro"}
            }
        }
        manager = IAConfigManager(config=config)
        
        manager.switch_profile("bot_1", "gpt-4")
        history = manager.get_profile_history("bot_1")
        
        assert len(history) >= 1
        assert history[-1]["new_profile"] == "gpt-4"
        assert "timestamp" in history[-1]


class TestProfileValidation:
    """Tests de validación de perfiles"""
    
    def test_validate_profile_checks_required_fields(self):
        """Debe validar que el perfil tenga todos los campos requeridos"""
        manager = IAConfigManager()
        
        # Perfil incompleto
        invalid_profile = {
            "model": "gemini-1.5-pro"
            # Falta provider
        }
        
        is_valid, errors = manager.validate_profile(invalid_profile)
        
        assert not is_valid
        assert "provider" in str(errors).lower()
    
    def test_validate_profile_checks_provider_enum(self):
        """Debe validar que el provider sea uno soportado"""
        manager = IAConfigManager()
        
        invalid_profile = {
            "provider": "invalid-provider",
            "model": "some-model"
        }
        
        is_valid, errors = manager.validate_profile(invalid_profile)
        
        assert not is_valid
        assert "provider" in str(errors).lower()
    
    def test_validate_profile_checks_temperature_range(self):
        """Debe validar que temperature esté en rango válido (0-2)"""
        manager = IAConfigManager()
        
        invalid_profile = {
            "provider": "gemini",
            "model": "gemini-1.5-pro",
            "temperature": 3.0  # Fuera de rango
        }
        
        is_valid, errors = manager.validate_profile(invalid_profile)
        
        assert not is_valid
        assert "temperature" in str(errors).lower()
    
    def test_validate_profile_accepts_valid_profile(self):
        """Debe aceptar un perfil válido"""
        manager = IAConfigManager()
        
        valid_profile = {
            "provider": "gemini",
            "model": "gemini-1.5-pro",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        is_valid, errors = manager.validate_profile(valid_profile)
        
        assert is_valid
        assert errors is None or len(errors) == 0


class TestQuotaValidatorIntegration:
    """Tests de integración con QuotaValidator (T48)"""
    
    def test_get_profile_includes_quota_info(self):
        """Debe incluir información de cuota del provider en el perfil"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {
                        "provider": "gemini",
                        "model": "gemini-1.5-pro",
                        "quota_limits": {
                            "requests_per_minute": 60,
                            "tokens_per_minute": 32000
                        }
                    }
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        profile = manager.load_profile("gemini-pro")
        
        assert hasattr(profile, 'quota_limits')
        assert profile.quota_limits['requests_per_minute'] == 60
    
    @patch('src.core.quota_validator.QuotaValidator')
    def test_validate_profile_quota_before_use(self, mock_quota_validator):
        """Debe validar cuota antes de usar un perfil"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"}
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        # Mock QuotaValidator
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_quota.return_value.is_valid = True
        mock_quota_validator.return_value = mock_validator_instance
        
        profile = manager.get_profile_for_bot("bot_1", validate_quota=True)
        
        assert profile is not None
    
    @patch('src.core.quota_validator.QuotaValidator')
    def test_switches_to_fallback_profile_if_quota_exceeded(self, mock_quota_validator):
        """Debe cambiar a perfil alternativo si se excede cuota"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {
                        "provider": "gemini",
                        "model": "gemini-1.5-pro",
                        "fallback_profile": "gpt-4"
                    },
                    "gpt-4": {"provider": "openai", "model": "gpt-4"}
                },
                "bot_assignments": {"bot_1": "gemini-pro"}
            }
        }
        manager = IAConfigManager(config=config)
        
        # Mock QuotaValidator - cuota excedida
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_quota.return_value.is_valid = False
        mock_quota_validator.return_value = mock_validator_instance
        
        profile = manager.get_profile_for_bot("bot_1", validate_quota=True, auto_fallback=True)
        
        # Debe haber cambiado a fallback
        assert profile.model == "gpt-4"


class TestCostTracking:
    """Tests de seguimiento de costos por perfil"""
    
    def test_track_usage_records_cost(self):
        """Debe registrar el costo de uso de un perfil"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {
                        "provider": "gemini",
                        "model": "gemini-1.5-pro",
                        "cost_per_1k_tokens": 0.005
                    }
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        manager.track_usage("bot_1", "gemini-pro", tokens_used=1000)
        
        stats = manager.get_usage_stats("bot_1")
        assert stats['total_tokens'] == 1000
        assert stats['total_cost'] > 0
    
    def test_get_cost_comparison_between_profiles(self):
        """Debe permitir comparar costos entre perfiles"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {
                        "provider": "gemini",
                        "model": "gemini-1.5-pro",
                        "cost_per_1k_tokens": 0.005
                    },
                    "gpt-4": {
                        "provider": "openai",
                        "model": "gpt-4",
                        "cost_per_1k_tokens": 0.03
                    }
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        manager.track_usage("bot_1", "gemini-pro", tokens_used=1000)
        manager.track_usage("bot_2", "gpt-4", tokens_used=1000)
        
        comparison = manager.get_cost_comparison(["bot_1", "bot_2"])
        
        assert "bot_1" in comparison
        assert "bot_2" in comparison
        assert comparison["bot_2"]["total_cost"] > comparison["bot_1"]["total_cost"]


class TestConfigReloading:
    """Tests de recarga de configuración"""
    
    def test_reload_config_updates_profiles(self):
        """Debe recargar perfiles desde configuración"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"}
                }
            }
        }
        manager = IAConfigManager(config=config)
        
        # Configuración actualizada
        new_config = {
            "ia_profiles": {
                "default_profile": "gpt-4",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"},
                    "gpt-4": {"provider": "openai", "model": "gpt-4"}
                }
            }
        }
        
        manager.reload_config(new_config)
        
        assert manager.default_profile == "gpt-4"
        assert len(manager.profiles) == 2
    
    def test_reload_config_preserves_bot_assignments(self):
        """Debe preservar asignaciones de bots al recargar"""
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro"}
                },
                "bot_assignments": {"bot_1": "gemini-pro"}
            }
        }
        manager = IAConfigManager(config=config)
        
        new_config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {"provider": "gemini", "model": "gemini-1.5-pro-002"}  # Actualizado
                }
                # Sin bot_assignments
            }
        }
        
        manager.reload_config(new_config, preserve_assignments=True)
        
        # Debe mantener asignación
        profile = manager.get_profile_for_bot("bot_1")
        assert profile.model == "gemini-1.5-pro-002"


class TestIAProfile:
    """Tests del dataclass IAProfile"""
    
    def test_ia_profile_initialization(self):
        """Debe inicializar correctamente un IAProfile"""
        profile = IAProfile(
            name="gemini-pro",
            provider=IAProvider.GEMINI,
            model="gemini-1.5-pro",
            temperature=0.7,
            max_tokens=1000
        )
        
        assert profile.name == "gemini-pro"
        assert profile.provider == IAProvider.GEMINI
        assert profile.temperature == 0.7
    
    def test_ia_profile_to_dict(self):
        """Debe convertir IAProfile a diccionario"""
        profile = IAProfile(
            name="gemini-pro",
            provider=IAProvider.GEMINI,
            model="gemini-1.5-pro",
            temperature=0.7
        )
        
        profile_dict = profile.to_dict()
        
        assert isinstance(profile_dict, dict)
        assert profile_dict['name'] == "gemini-pro"
        assert profile_dict['model'] == "gemini-1.5-pro"
    
    def test_ia_profile_from_dict(self):
        """Debe crear IAProfile desde diccionario"""
        data = {
            "name": "gpt-4",
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.5
        }
        
        profile = IAProfile.from_dict(data)
        
        assert profile.name == "gpt-4"
        assert profile.provider == IAProvider.OPENAI
        assert profile.temperature == 0.5


class TestIAProvider:
    """Tests del enum IAProvider"""
    
    def test_ia_provider_enum_values(self):
        """Debe tener los providers soportados"""
        assert IAProvider.GEMINI.value == "gemini"
        assert IAProvider.OPENAI.value == "openai"
        assert IAProvider.ANTHROPIC.value == "anthropic"
    
    def test_ia_provider_from_string(self):
        """Debe convertir string a IAProvider"""
        provider = IAProvider.from_string("gemini")
        
        assert provider == IAProvider.GEMINI
    
    def test_ia_provider_from_string_case_insensitive(self):
        """Debe ser case-insensitive"""
        provider = IAProvider.from_string("GEMINI")
        
        assert provider == IAProvider.GEMINI
    
    def test_ia_provider_from_string_invalid_raises_error(self):
        """Debe fallar con provider inválido"""
        with pytest.raises(ValueError, match="Provider.*no soportado"):
            IAProvider.from_string("invalid-provider")
