"""
Tests unitarios para el módulo config_loader.

Este módulo prueba la funcionalidad de carga de configuración desde archivos JSON
y variables de entorno, asegurando el cumplimiento del Ticket T44.
"""
import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from src.core.config_loader import ConfigLoader, ConfigurationError


class TestConfigLoader:
    """Tests para la clase ConfigLoader"""
    
    def test_load_json_config_success(self, tmp_path):
        """
        Test: Debe cargar exitosamente un archivo JSON válido
        
        Dado que existe un archivo JSON válido con configuración
        Cuando se carga el archivo
        Entonces debe retornar un diccionario con la configuración
        """
        # Arrange
        config_data = {
            "timezone": "America/Lima",
            "trading_window": {"start": "06:00", "end": "13:00"}
        }
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Act
        loader = ConfigLoader()
        result = loader.load_json_config(str(config_file))
        
        # Assert
        assert result == config_data
        assert result["timezone"] == "America/Lima"
    
    def test_load_json_config_file_not_found(self):
        """
        Test: Debe lanzar ConfigurationError si el archivo no existe
        
        Dado que se intenta cargar un archivo que no existe
        Cuando se ejecuta load_json_config
        Entonces debe lanzar ConfigurationError
        """
        # Arrange
        loader = ConfigLoader()
        non_existent_file = "non_existent_config.json"
        
        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_json_config(non_existent_file)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_json_config_invalid_json(self, tmp_path):
        """
        Test: Debe lanzar ConfigurationError si el JSON es inválido
        
        Dado que existe un archivo con JSON malformado
        Cuando se intenta cargar
        Entonces debe lanzar ConfigurationError
        """
        # Arrange
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")
        
        loader = ConfigLoader()
        
        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_json_config(str(config_file))
        
        assert "invalid json" in str(exc_info.value).lower()
    
    def test_load_env_variables_success(self):
        """
        Test: Debe cargar variables de entorno correctamente
        
        Dado que existen variables de entorno definidas
        Cuando se cargan las variables
        Entonces debe retornar un diccionario con los valores
        """
        # Arrange
        loader = ConfigLoader()
        env_vars = {
            "MT5_ACCOUNT_ID": "12345",
            "MT5_PASSWORD": "secret",
            "GEMINI_API_KEY": "api_key_123"
        }
        
        # Act
        with patch.dict(os.environ, env_vars, clear=False):
            result = loader.load_env_variables(list(env_vars.keys()))
        
        # Assert
        assert result == env_vars
    
    def test_load_env_variables_missing_required(self):
        """
        Test: Debe lanzar ConfigurationError si falta una variable requerida
        
        Dado que se requiere una variable de entorno que no existe
        Cuando se intenta cargar
        Entonces debe lanzar ConfigurationError
        """
        # Arrange
        loader = ConfigLoader()
        required_vars = ["MISSING_VAR"]
        
        # Act & Assert
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_env_variables(required_vars)
            
            assert "MISSING_VAR" in str(exc_info.value)
    
    def test_get_config_value_success(self):
        """
        Test: Debe obtener un valor de configuración por ruta de clave
        
        Dado que existe una configuración cargada
        Cuando se solicita un valor por su ruta (ej: 'trading_window.start')
        Entonces debe retornar el valor correcto
        """
        # Arrange
        config_data = {
            "trading_window": {
                "start": "06:00",
                "end": "13:00"
            }
        }
        loader = ConfigLoader()
        loader._config = config_data
        
        # Act
        result = loader.get_config_value("trading_window.start")
        
        # Assert
        assert result == "06:00"
    
    def test_get_config_value_not_found(self):
        """
        Test: Debe lanzar ConfigurationError si la clave no existe
        
        Dado que se busca una clave que no existe en la configuración
        Cuando se ejecuta get_config_value
        Entonces debe lanzar ConfigurationError
        """
        # Arrange
        loader = ConfigLoader()
        loader._config = {"key": "value"}
        
        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            loader.get_config_value("non_existent.key")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_get_config_value_with_default(self):
        """
        Test: Debe retornar valor por defecto si la clave no existe
        
        Dado que se proporciona un valor por defecto
        Cuando la clave no existe
        Entonces debe retornar el valor por defecto
        """
        # Arrange
        loader = ConfigLoader()
        loader._config = {}
        default_value = "default"
        
        # Act
        result = loader.get_config_value("missing.key", default=default_value)
        
        # Assert
        assert result == default_value
    
    def test_validate_required_keys_success(self):
        """
        Test: Debe validar exitosamente que todas las claves requeridas existen
        
        Dado que la configuración contiene todas las claves requeridas
        Cuando se valida
        Entonces debe retornar True
        """
        # Arrange
        config_data = {
            "timezone": "America/Lima",
            "trading_window": {"start": "06:00"}
        }
        loader = ConfigLoader()
        loader._config = config_data
        required_keys = ["timezone", "trading_window.start"]
        
        # Act
        result = loader.validate_required_keys(required_keys)
        
        # Assert
        assert result is True
    
    def test_validate_required_keys_missing(self):
        """
        Test: Debe lanzar ConfigurationError si falta una clave requerida
        
        Dado que la configuración no contiene todas las claves requeridas
        Cuando se valida
        Entonces debe lanzar ConfigurationError
        """
        # Arrange
        loader = ConfigLoader()
        loader._config = {"timezone": "America/Lima"}
        required_keys = ["timezone", "missing_key"]
        
        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            loader.validate_required_keys(required_keys)
        
        assert "missing_key" in str(exc_info.value).lower()
    
    def test_reload_config(self, tmp_path):
        """
        Test: Debe poder recargar la configuración sin reiniciar el sistema
        
        Dado que se actualiza un archivo de configuración
        Cuando se ejecuta reload_config
        Entonces debe cargar los nuevos valores
        """
        # Arrange
        config_file = tmp_path / "config.json"
        initial_config = {"value": "initial"}
        config_file.write_text(json.dumps(initial_config))
        
        loader = ConfigLoader()
        loader.load_json_config(str(config_file))
        
        # Modificar el archivo
        updated_config = {"value": "updated"}
        config_file.write_text(json.dumps(updated_config))
        
        # Act
        loader.load_json_config(str(config_file))
        result = loader.get_config_value("value")
        
        # Assert
        assert result == "updated"
    
    def test_merge_configs(self):
        """
        Test: Debe fusionar múltiples configuraciones correctamente
        
        Dado que existen múltiples fuentes de configuración
        Cuando se fusionan
        Entonces los valores deben combinarse correctamente con prioridad definida
        """
        # Arrange
        loader = ConfigLoader()
        config1 = {"key1": "value1", "shared": "from_config1"}
        config2 = {"key2": "value2", "shared": "from_config2"}
        
        # Act
        result = loader.merge_configs(config1, config2)
        
        # Assert
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert result["shared"] == "from_config2"  # config2 tiene prioridad
    
    def test_credentials_not_exposed_in_logs(self, tmp_path, caplog):
        """
        Test: Las credenciales NO deben exponerse en logs
        
        Dado que se cargan credenciales sensibles
        Cuando se registran logs
        Entonces las credenciales NO deben aparecer en texto plano
        """
        # Arrange
        config_data = {
            "mt5": {
                "password": "super_secret_password",
                "api_key": "secret_api_key"
            }
        }
        config_file = tmp_path / "credentials.json"
        config_file.write_text(json.dumps(config_data))
        
        loader = ConfigLoader()
        
        # Act
        loader.load_json_config(str(config_file))
        
        # Assert
        log_output = caplog.text
        assert "super_secret_password" not in log_output
        assert "secret_api_key" not in log_output
