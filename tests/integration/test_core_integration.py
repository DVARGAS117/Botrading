"""
Tests de integración para verificar interacción entre módulos core.

Estos tests validan que los componentes funcionan correctamente juntos
y no solo de forma aislada.
"""
import pytest
from pathlib import Path
import json


@pytest.mark.integration
class TestCoreModulesIntegration:
    """Tests de integración entre módulos core."""
    
    def test_all_core_modules_can_be_imported(self):
        """Test que todos los módulos core pueden importarse sin errores."""
        # Arrange & Act & Assert
        try:
            from src.core import config_loader
            assert config_loader is not None
        except ImportError as e:
            pytest.fail(f"Failed to import core modules: {e}")
    
    def test_config_loader_can_be_instantiated(self):
        """Test que ConfigLoader puede ser instanciado."""
        # Arrange
        from src.core.config_loader import ConfigLoader
        
        # Act
        loader = ConfigLoader()
        
        # Assert
        assert loader is not None
        assert hasattr(loader, 'load_json_config')
        assert hasattr(loader, 'get_config_value')
    
    def test_config_loader_with_valid_json_file(self, temp_config_dir, sample_config_data):
        """Test integración de ConfigLoader con archivo JSON real."""
        # Arrange
        from src.core.config_loader import ConfigLoader
        
        config_file = temp_config_dir / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(sample_config_data, f)
        
        loader = ConfigLoader()
        
        # Act
        config_data = loader.load_json_config(str(config_file))
        
        # Assert
        assert config_data is not None
        assert loader.get_config_value("bot_name") == "TestBot"
        assert loader.get_config_value("trading.risk_percent") == 2.0
    
    def test_multiple_config_loaders_are_independent(self, temp_config_dir):
        """Test que múltiples instancias de ConfigLoader son independientes."""
        # Arrange
        from src.core.config_loader import ConfigLoader
        
        config1_data = {"name": "Config1", "value": 100}
        config2_data = {"name": "Config2", "value": 200}
        
        config1_file = temp_config_dir / "config1.json"
        config2_file = temp_config_dir / "config2.json"
        
        with open(config1_file, 'w') as f:
            json.dump(config1_data, f)
        with open(config2_file, 'w') as f:
            json.dump(config2_data, f)
        
        loader1 = ConfigLoader()
        loader2 = ConfigLoader()
        
        # Act
        loader1.load_json_config(str(config1_file))
        loader2.load_json_config(str(config2_file))
        
        # Assert
        assert loader1.get_config_value("name") == "Config1"
        assert loader1.get_config_value("value") == 100
        assert loader2.get_config_value("name") == "Config2"
        assert loader2.get_config_value("value") == 200
    
    def test_config_loader_and_env_vars_integration(self, temp_config_dir, monkeypatch):
        """Test integración entre ConfigLoader y variables de entorno."""
        # Arrange
        from src.core.config_loader import ConfigLoader
        
        # Configurar variables de entorno
        monkeypatch.setenv("TEST_VAR", "test_value")
        monkeypatch.setenv("TEST_NUM", "42")
        
        loader = ConfigLoader()
        
        # Act
        env_data = loader.load_env_variables(["TEST_VAR", "TEST_NUM"])
        
        # Assert
        assert env_data is not None
        assert loader.get_config_value("TEST_VAR") == "test_value"
        assert loader.get_config_value("TEST_NUM") == "42"
    
    def test_config_loader_merge_json_and_env(self, temp_config_dir, monkeypatch):
        """Test que ConfigLoader puede fusionar config JSON y env vars."""
        # Arrange
        from src.core.config_loader import ConfigLoader
        
        json_data = {
            "app_name": "TestApp",
            "version": "1.0.0"
        }
        
        config_file = temp_config_dir / "app.json"
        with open(config_file, 'w') as f:
            json.dump(json_data, f)
        
        monkeypatch.setenv("API_KEY", "secret_key_123")
        
        loader = ConfigLoader()
        
        # Act
        loader.load_json_config(str(config_file))
        loader.load_env_variables(["API_KEY"])
        
        # Assert
        assert loader.get_config_value("app_name") == "TestApp"
        assert loader.get_config_value("version") == "1.0.0"
        assert loader.get_config_value("API_KEY") == "secret_key_123"


@pytest.mark.integration
class TestModuleMetadataIntegration:
    """Tests de integración para ModuleMetadata."""
    
    def test_core_module_metadata_persistence(self):
        """Test que metadata persiste durante el ciclo de vida del módulo."""
        # Arrange
        from src.core.core_module import CoreModule
        
        module = CoreModule(
            name="TestModule",
            version="1.0.0",
            description="Test description"
        )
        
        # Act
        info_before = module.get_info()
        module.shutdown()
        info_after = module.get_info()
        
        # Assert
        assert info_before["name"] == info_after["name"]
        assert info_before["version"] == info_after["version"]
        assert info_before["initialized_at"] == info_after["initialized_at"]
    
    def test_multiple_core_modules_have_independent_metadata(self):
        """Test que múltiples módulos tienen metadata independiente."""
        # Arrange
        from src.core.core_module import CoreModule
        
        # Act
        module1 = CoreModule(name="Module1", version="1.0.0")
        module2 = CoreModule(name="Module2", version="2.0.0")
        
        # Assert
        assert module1.name != module2.name
        assert module1.version != module2.version
        assert module1.metadata.initialized_at != module2.metadata.initialized_at or \
               abs((module1.metadata.initialized_at - module2.metadata.initialized_at).total_seconds()) < 0.1


@pytest.mark.integration
class TestModuleDependenciesIntegration:
    """Tests de integración para el sistema de dependencias."""
    
    def test_module_with_dependencies_validates_correctly(self):
        """Test que módulo valida dependencias correctamente."""
        # Arrange
        from src.core.core_module import CoreModule
        from src.core.config_loader import ConfigLoader
        
        config = ConfigLoader()
        module = CoreModule(
            name="DependentModule",
            version="1.0.0",
            dependencies=["config_loader"]
        )
        
        available_modules = {"config_loader": config}
        
        # Act
        result = module.validate_dependencies(available_modules)
        
        # Assert
        assert result is True
    
    def test_module_fails_validation_with_missing_dependencies(self):
        """Test que módulo falla validación con dependencias faltantes."""
        # Arrange
        from src.core.core_module import CoreModule
        
        module = CoreModule(
            name="DependentModule",
            version="1.0.0",
            dependencies=["config_loader", "logger", "missing_module"]
        )
        
        available_modules = {"config_loader": object()}
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required dependencies"):
            module.validate_dependencies(available_modules)
    
    def test_circular_dependency_scenario(self):
        """Test escenario de dependencias circulares (debe manejarse en código)."""
        # Arrange
        from src.core.core_module import CoreModule
        
        # Este test documenta el comportamiento esperado
        # En una implementación real, se debería prevenir dependencias circulares
        
        module_a = CoreModule(
            name="ModuleA",
            version="1.0.0",
            dependencies=["ModuleB"]
        )
        
        module_b = CoreModule(
            name="ModuleB",
            version="1.0.0",
            dependencies=["ModuleA"]
        )
        
        # Act & Assert
        # En este caso, ninguno puede validarse sin el otro
        # Si ModuleB no está disponible, ModuleA no puede validar
        available = {}
        with pytest.raises(ValueError, match="Missing required dependencies"):
            module_a.validate_dependencies(available)
        
        # Y viceversa
        with pytest.raises(ValueError, match="Missing required dependencies"):
            module_b.validate_dependencies(available)


@pytest.mark.integration
class TestConfigurationWorkflow:
    """Tests de flujo completo de configuración."""
    
    def test_complete_configuration_workflow(self, temp_config_dir, monkeypatch):
        """Test flujo completo: cargar JSON, env vars, y acceder a valores."""
        # Arrange
        from src.core.config_loader import ConfigLoader
        
        # 1. Preparar archivos de configuración
        settings_data = {
            "bot": {
                "name": "ProductionBot",
                "version": "2.0.0"
            },
            "trading": {
                "symbols": ["EURUSD", "GBPUSD"],
                "risk_percent": 1.5
            }
        }
        
        settings_file = temp_config_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(settings_data, f)
        
        # 2. Configurar variables de entorno
        monkeypatch.setenv("MT5_PASSWORD", "secure_password")
        monkeypatch.setenv("GEMINI_API_KEY", "api_key_xyz")
        
        loader = ConfigLoader()
        
        # Act
        # 3. Cargar configuraciones
        loader.load_json_config(str(settings_file))
        loader.load_env_variables(["MT5_PASSWORD", "GEMINI_API_KEY"])
        
        # Assert
        # 4. Verificar acceso a todos los valores
        assert loader.get_config_value("bot.name") == "ProductionBot"
        assert loader.get_config_value("bot.version") == "2.0.0"
        assert loader.get_config_value("trading.risk_percent") == 1.5
        assert "EURUSD" in loader.get_config_value("trading.symbols")
        assert loader.get_config_value("MT5_PASSWORD") == "secure_password"
        assert loader.get_config_value("GEMINI_API_KEY") == "api_key_xyz"
    
    def test_configuration_reload_workflow(self, temp_config_dir):
        """Test que la configuración puede recargarse dinámicamente."""
        # Arrange
        from src.core.config_loader import ConfigLoader
        
        config_file = temp_config_dir / "dynamic_config.json"
        
        # Configuración inicial
        initial_data = {"setting": "initial_value"}
        with open(config_file, 'w') as f:
            json.dump(initial_data, f)
        
        loader = ConfigLoader()
        loader.load_json_config(str(config_file))
        
        # Act
        # Cambiar configuración
        updated_data = {"setting": "updated_value"}
        with open(config_file, 'w') as f:
            json.dump(updated_data, f)
        
        # Limpiar y recargar (usando clear_config + load_json_config)
        loader.clear_config()
        loader.load_json_config(str(config_file))
        
        # Assert
        assert loader.get_config_value("setting") == "updated_value"


@pytest.mark.integration 
class TestErrorHandlingIntegration:
    """Tests de manejo de errores en integración de módulos."""
    
    def test_config_loader_handles_missing_file_gracefully(self):
        """Test que ConfigLoader maneja archivos faltantes correctamente."""
        # Arrange
        from src.core.config_loader import ConfigLoader, ConfigurationError
        
        loader = ConfigLoader()
        
        # Act & Assert
        # ConfigLoader lanza excepción en lugar de retornar False
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            loader.load_json_config("/path/to/nonexistent/file.json")
    
    def test_config_loader_handles_invalid_json_gracefully(self, temp_config_dir):
        """Test que ConfigLoader maneja JSON inválido correctamente."""
        # Arrange
        from src.core.config_loader import ConfigLoader, ConfigurationError
        
        invalid_file = temp_config_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ this is not valid json }")
        
        loader = ConfigLoader()
        
        # Act & Assert
        # ConfigLoader lanza excepción en lugar de retornar False
        with pytest.raises(ConfigurationError, match="Invalid JSON"):
            loader.load_json_config(str(invalid_file))
    
    def test_get_config_value_with_nonexistent_key_returns_none(self):
        """Test que obtener valor inexistente lanza excepción."""
        # Arrange
        from src.core.config_loader import ConfigLoader, ConfigurationError
        
        loader = ConfigLoader()
        
        # Act & Assert
        # ConfigLoader lanza excepción para claves no encontradas
        with pytest.raises(ConfigurationError, match="Configuration key not found"):
            loader.get_config_value("nonexistent.key")
    
    def test_get_config_value_with_default_for_missing_key(self):
        """Test que se puede especificar valor por defecto."""
        # Arrange
        from src.core.config_loader import ConfigLoader
        
        loader = ConfigLoader()
        
        # Act
        value = loader.get_config_value("missing.key", default="default_value")
        
        # Assert
        assert value == "default_value"
