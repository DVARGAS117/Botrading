"""
Tests unitarios para la clase base CoreModule.

Este módulo prueba la funcionalidad de la clase base que todos los módulos
core deben heredar para garantizar consistencia y reutilizabilidad.
"""
import pytest
from unittest.mock import Mock, patch
from src.core.core_module import CoreModule, ModuleMetadata


class TestCoreModule:
    """Tests para la clase base CoreModule."""
    
    def test_core_module_initialization(self):
        """Test que CoreModule se inicializa correctamente con metadata."""
        # Arrange & Act
        module = CoreModule(
            name="TestModule",
            version="1.0.0",
            description="Test module"
        )
        
        # Assert
        assert module.name == "TestModule"
        assert module.version == "1.0.0"
        assert module.description == "Test module"
        assert module.metadata.name == "TestModule"
    
    def test_core_module_requires_name(self):
        """Test que CoreModule requiere un nombre."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Module name is required"):
            CoreModule(name="", version="1.0.0")
    
    def test_core_module_requires_version(self):
        """Test que CoreModule requiere una versión."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Module version is required"):
            CoreModule(name="TestModule", version="")
    
    def test_core_module_has_default_description(self):
        """Test que CoreModule tiene descripción por defecto."""
        # Arrange & Act
        module = CoreModule(name="TestModule", version="1.0.0")
        
        # Assert
        assert module.description is not None
        assert len(module.description) > 0
    
    def test_core_module_get_info(self):
        """Test que get_info retorna información del módulo."""
        # Arrange
        module = CoreModule(
            name="TestModule",
            version="1.0.0",
            description="Test description"
        )
        
        # Act
        info = module.get_info()
        
        # Assert
        assert info["name"] == "TestModule"
        assert info["version"] == "1.0.0"
        assert info["description"] == "Test description"
        assert "initialized_at" in info
    
    def test_core_module_is_initialized(self):
        """Test que is_initialized retorna el estado correcto."""
        # Arrange
        module = CoreModule(name="TestModule", version="1.0.0")
        
        # Act & Assert
        assert module.is_initialized() is True
    
    def test_core_module_shutdown(self):
        """Test que shutdown marca el módulo como no inicializado."""
        # Arrange
        module = CoreModule(name="TestModule", version="1.0.0")
        
        # Act
        module.shutdown()
        
        # Assert
        assert module.is_initialized() is False
    
    def test_core_module_restart(self):
        """Test que restart reinicializa el módulo."""
        # Arrange
        module = CoreModule(name="TestModule", version="1.0.0")
        module.shutdown()
        
        # Act
        module.restart()
        
        # Assert
        assert module.is_initialized() is True
    
    def test_core_module_can_be_subclassed(self):
        """Test que CoreModule puede ser heredado correctamente."""
        # Arrange
        class CustomModule(CoreModule):
            def __init__(self):
                super().__init__(name="CustomModule", version="2.0.0")
                self.custom_data = "test"
        
        # Act
        module = CustomModule()
        
        # Assert
        assert module.name == "CustomModule"
        assert module.version == "2.0.0"
        assert module.custom_data == "test"
        assert isinstance(module, CoreModule)
    
    def test_core_module_metadata_is_immutable(self):
        """Test que metadata no puede ser modificado directamente."""
        # Arrange
        module = CoreModule(name="TestModule", version="1.0.0")
        
        # Act & Assert
        with pytest.raises(AttributeError):
            module.metadata.name = "NewName"
    
    def test_core_module_str_representation(self):
        """Test que __str__ retorna representación legible."""
        # Arrange
        module = CoreModule(name="TestModule", version="1.0.0")
        
        # Act
        str_repr = str(module)
        
        # Assert
        assert "TestModule" in str_repr
        assert "1.0.0" in str_repr
    
    def test_core_module_dependencies(self):
        """Test que se pueden declarar dependencias entre módulos."""
        # Arrange & Act
        module = CoreModule(
            name="TestModule",
            version="1.0.0",
            dependencies=["config_loader", "logger"]
        )
        
        # Assert
        assert len(module.dependencies) == 2
        assert "config_loader" in module.dependencies
        assert "logger" in module.dependencies
    
    def test_core_module_validate_dependencies(self):
        """Test que validate_dependencies verifica módulos requeridos."""
        # Arrange
        module = CoreModule(
            name="TestModule",
            version="1.0.0",
            dependencies=["config_loader", "logger"]
        )
        available_modules = {"config_loader": Mock(), "logger": Mock()}
        
        # Act
        result = module.validate_dependencies(available_modules)
        
        # Assert
        assert result is True
    
    def test_core_module_validate_dependencies_fails_when_missing(self):
        """Test que validate_dependencies falla si falta un módulo."""
        # Arrange
        module = CoreModule(
            name="TestModule",
            version="1.0.0",
            dependencies=["config_loader", "logger", "missing_module"]
        )
        available_modules = {"config_loader": Mock(), "logger": Mock()}
        
        # Act & Assert
        with pytest.raises(ValueError, match="Missing required dependencies"):
            module.validate_dependencies(available_modules)


class TestModuleMetadata:
    """Tests para la clase ModuleMetadata."""
    
    def test_module_metadata_initialization(self):
        """Test que ModuleMetadata se inicializa correctamente."""
        # Arrange & Act
        metadata = ModuleMetadata(
            name="TestModule",
            version="1.0.0",
            description="Test description"
        )
        
        # Assert
        assert metadata.name == "TestModule"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test description"
        assert metadata.initialized_at is not None
    
    def test_module_metadata_to_dict(self):
        """Test que to_dict retorna diccionario con toda la info."""
        # Arrange
        metadata = ModuleMetadata(
            name="TestModule",
            version="1.0.0",
            description="Test description"
        )
        
        # Act
        data = metadata.to_dict()
        
        # Assert
        assert data["name"] == "TestModule"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Test description"
        assert "initialized_at" in data
    
    def test_module_metadata_is_frozen(self):
        """Test que ModuleMetadata es inmutable (frozen)."""
        # Arrange
        metadata = ModuleMetadata(
            name="TestModule",
            version="1.0.0",
            description="Test description"
        )
        
        # Act & Assert
        with pytest.raises(AttributeError):
            metadata.name = "NewName"
