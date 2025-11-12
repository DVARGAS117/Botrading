"""
Tests unitarios para GlobalConfigManager.

Ticket: T05 - Parámetros globales centralizados
Fecha: 2025-11-11
"""
import pytest
import json
import tempfile
from pathlib import Path
from src.core.global_config_manager import GlobalConfigManager, ConfigurationError


class TestGlobalConfigManager:
    """Tests para GlobalConfigManager - Parámetros globales centralizados (T05)"""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Crea un directorio temporal con archivos de configuración de prueba"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # settings.json
        settings = {
            "timezone": "America/Lima",
            "trading_window": {
                "start": "06:00",
                "end": "13:00"
            },
            "bots": {
                "bot_1": {
                    "enabled": True,
                    "instruments": ["EURUSD", "GBPUSD"]
                }
            }
        }
        (config_dir / "settings.json").write_text(json.dumps(settings))
        
        # schedule.json
        schedule = {
            "trading_schedule": {
                "timezone": "America/Lima",
                "trading_hours": {
                    "start_time": "06:00",
                    "end_time": "13:00"
                }
            }
        }
        (config_dir / "schedule.json").write_text(json.dumps(schedule))
        
        # credentials.json
        credentials = {
            "mt5": {
                "account_id": "12345",
                "password": "secret",
                "server": "Broker-Demo"
            },
            "gemini": {
                "api_key": "test_key_123"
            }
        }
        (config_dir / "credentials.json").write_text(json.dumps(credentials))
        
        return config_dir
    
    def test_initialization_loads_all_configs(self, temp_config_dir):
        """
        GIVEN archivos de configuración válidos en el directorio
        WHEN se inicializa GlobalConfigManager
        THEN carga todos los archivos automáticamente
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        # Verificar que se cargaron las configuraciones
        assert manager.get_value("timezone") == "America/Lima"
        assert manager.get_value("trading_schedule.timezone") == "America/Lima"
        assert manager.get_value("mt5.account_id") == "12345"
    
    def test_get_value_with_dot_notation(self, temp_config_dir):
        """
        GIVEN una configuración cargada
        WHEN se accede a valores usando notación de punto
        THEN retorna los valores correctos
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        assert manager.get_value("trading_window.start") == "06:00"
        assert manager.get_value("bots.bot_1.enabled") is True
        assert manager.get_value("bots.bot_1.instruments") == ["EURUSD", "GBPUSD"]
    
    def test_get_value_with_default(self, temp_config_dir):
        """
        GIVEN una configuración cargada
        WHEN se accede a una clave que no existe con default
        THEN retorna el valor por defecto
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        result = manager.get_value("nonexistent.key", default="default_value")
        assert result == "default_value"
    
    def test_get_value_without_default_raises_error(self, temp_config_dir):
        """
        GIVEN una configuración cargada
        WHEN se accede a una clave que no existe sin default
        THEN lanza ConfigurationError
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        with pytest.raises(ConfigurationError, match="not found"):
            manager.get_value("nonexistent.key")
    
    def test_get_bot_config(self, temp_config_dir):
        """
        GIVEN una configuración con múltiples bots
        WHEN se solicita la configuración de un bot específico
        THEN retorna solo la configuración de ese bot
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        bot_config = manager.get_bot_config("bot_1")
        
        assert bot_config["enabled"] is True
        assert bot_config["instruments"] == ["EURUSD", "GBPUSD"]
    
    def test_get_bot_config_nonexistent_raises_error(self, temp_config_dir):
        """
        GIVEN una configuración cargada
        WHEN se solicita un bot que no existe
        THEN lanza ConfigurationError
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        with pytest.raises(ConfigurationError, match="Bot 'nonexistent_bot' not found"):
            manager.get_bot_config("nonexistent_bot")
    
    def test_list_enabled_bots(self, temp_config_dir):
        """
        GIVEN una configuración con bots habilitados y deshabilitados
        WHEN se solicita lista de bots habilitados
        THEN retorna solo los habilitados
        """
        # Agregar bot_2 deshabilitado
        settings_path = temp_config_dir / "settings.json"
        settings = json.loads(settings_path.read_text())
        settings["bots"]["bot_2"] = {"enabled": False, "instruments": ["USDJPY"]}
        settings_path.write_text(json.dumps(settings))
        
        manager = GlobalConfigManager(str(temp_config_dir))
        
        enabled_bots = manager.list_enabled_bots()
        
        assert "bot_1" in enabled_bots
        assert "bot_2" not in enabled_bots
        assert len(enabled_bots) == 1
    
    def test_get_credentials_sanitized_in_logs(self, temp_config_dir, caplog):
        """
        GIVEN credenciales cargadas
        WHEN se accede a credenciales
        THEN no aparecen en logs (sanitizadas)
        """
        import logging
        caplog.set_level(logging.INFO)
        
        manager = GlobalConfigManager(str(temp_config_dir))
        
        # Acceder a credenciales
        password = manager.get_value("mt5.password")
        
        assert password == "secret"
        
        # Verificar que no aparece en logs
        assert "secret" not in caplog.text
    
    def test_reload_config_applies_changes(self, temp_config_dir):
        """
        GIVEN una configuración ya cargada
        WHEN se modifica un archivo y se recarga
        THEN aplica los nuevos valores (criterio T05)
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        # Valor original
        original = manager.get_value("timezone")
        assert original == "America/Lima"
        
        # Modificar archivo
        settings_path = temp_config_dir / "settings.json"
        settings = json.loads(settings_path.read_text())
        settings["timezone"] = "America/New_York"
        settings_path.write_text(json.dumps(settings))
        
        # Recargar
        manager.reload_config()
        
        # Verificar nuevo valor
        new_value = manager.get_value("timezone")
        assert new_value == "America/New_York"
    
    def test_get_trading_window(self, temp_config_dir):
        """
        GIVEN una configuración con ventana de trading
        WHEN se solicita la ventana de trading
        THEN retorna start, end y days
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        window = manager.get_trading_window()
        
        assert window["start"] == "06:00"
        assert window["end"] == "13:00"
    
    def test_initialization_with_missing_file_raises_error(self, tmp_path):
        """
        GIVEN un directorio sin archivos de configuración
        WHEN se intenta inicializar GlobalConfigManager
        THEN lanza ConfigurationError indicando archivo faltante
        """
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        with pytest.raises(ConfigurationError, match="not found"):
            GlobalConfigManager(str(empty_dir))
    
    def test_get_all_instruments(self, temp_config_dir):
        """
        GIVEN una configuración con múltiples bots
        WHEN se solicita lista de todos los instrumentos
        THEN retorna lista única de instrumentos de bots habilitados
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        instruments = manager.get_all_instruments()
        
        assert "EURUSD" in instruments
        assert "GBPUSD" in instruments
        assert len(instruments) == 2
    
    def test_validate_required_keys_success(self, temp_config_dir):
        """
        GIVEN una configuración completa
        WHEN se validan claves requeridas que existen
        THEN retorna True sin errores
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        required = ["timezone", "trading_window.start", "mt5.account_id"]
        result = manager.validate_required_keys(required)
        
        assert result is True
    
    def test_validate_required_keys_failure(self, temp_config_dir):
        """
        GIVEN una configuración cargada
        WHEN se validan claves requeridas que no existen
        THEN lanza ConfigurationError con lista de faltantes
        """
        manager = GlobalConfigManager(str(temp_config_dir))
        
        required = ["timezone", "nonexistent.key", "another.missing"]
        
        with pytest.raises(ConfigurationError, match="missing"):
            manager.validate_required_keys(required)
