"""
Configuración global de pytest para el proyecto Botrading.

Este módulo proporciona fixtures reutilizables y configuración compartida
para todos los tests del proyecto.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import json


# ==================== FIXTURES DE DIRECTORIOS ====================

@pytest.fixture
def temp_dir():
    """
    Crea un directorio temporal para tests.
    
    Se limpia automáticamente después del test.
    
    Yields:
        Path: Ruta al directorio temporal
    """
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_config_dir(temp_dir):
    """
    Crea un directorio temporal para archivos de configuración.
    
    Args:
        temp_dir: Fixture del directorio temporal base
        
    Yields:
        Path: Ruta al directorio config temporal
    """
    config_path = temp_dir / "config"
    config_path.mkdir(exist_ok=True)
    yield config_path


@pytest.fixture
def temp_logs_dir(temp_dir):
    """
    Crea un directorio temporal para archivos de log.
    
    Args:
        temp_dir: Fixture del directorio temporal base
        
    Yields:
        Path: Ruta al directorio logs temporal
    """
    logs_path = temp_dir / "logs"
    logs_path.mkdir(exist_ok=True)
    yield logs_path


# ==================== FIXTURES DE ARCHIVOS JSON ====================

@pytest.fixture
def sample_config_data() -> Dict[str, Any]:
    """
    Datos de configuración de ejemplo para tests.
    
    Returns:
        Dict con configuración de ejemplo
    """
    return {
        "bot_name": "TestBot",
        "trading": {
            "timeframe": "5M",
            "risk_percent": 2.0,
            "max_positions": 3
        },
        "mt5": {
            "login": 12345678,
            "server": "TestServer-Demo"
        }
    }


@pytest.fixture
def sample_credentials_data() -> Dict[str, Any]:
    """
    Datos de credenciales de ejemplo para tests.
    
    Returns:
        Dict con credenciales de ejemplo
    """
    return {
        "mt5": {
            "login": 12345678,
            "password": "test_password",
            "server": "TestServer-Demo"
        },
        "gemini": {
            "api_key": "test_api_key_12345"
        }
    }


@pytest.fixture
def sample_ia_config_data() -> Dict[str, Any]:
    """
    Datos de configuración de IA de ejemplo para tests.
    
    Returns:
        Dict con configuración de IA de ejemplo
    """
    return {
        "model": "gemini-2.0-flash-exp",
        "temperature": 0.7,
        "max_tokens": 2000,
        "timeout": 30
    }


@pytest.fixture
def json_config_file(temp_config_dir, sample_config_data):
    """
    Crea un archivo JSON de configuración temporal.
    
    Args:
        temp_config_dir: Directorio temporal para config
        sample_config_data: Datos de configuración
        
    Yields:
        Path: Ruta al archivo JSON creado
    """
    config_file = temp_config_dir / "settings.json"
    with open(config_file, "w") as f:
        json.dump(sample_config_data, f, indent=2)
    yield config_file


@pytest.fixture
def json_credentials_file(temp_config_dir, sample_credentials_data):
    """
    Crea un archivo JSON de credenciales temporal.
    
    Args:
        temp_config_dir: Directorio temporal para config
        sample_credentials_data: Datos de credenciales
        
    Yields:
        Path: Ruta al archivo JSON creado
    """
    creds_file = temp_config_dir / "credentials.json"
    with open(creds_file, "w") as f:
        json.dump(sample_credentials_data, f, indent=2)
    yield creds_file


# ==================== FIXTURES DE VARIABLES DE ENTORNO ====================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Configura variables de entorno de ejemplo para tests.
    
    Args:
        monkeypatch: Fixture de pytest para modificar entorno
        
    Returns:
        Dict con las variables configuradas
    """
    env_vars = {
        "MT5_LOGIN": "12345678",
        "MT5_PASSWORD": "test_password",
        "MT5_SERVER": "TestServer-Demo",
        "GEMINI_API_KEY": "test_api_key_12345"
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


# ==================== FIXTURES DE MÓDULOS CORE ====================

@pytest.fixture
def mock_config_loader():
    """
    Crea un mock del ConfigLoader para tests.
    
    Returns:
        Mock object con métodos del ConfigLoader
    """
    from unittest.mock import Mock
    
    loader = Mock()
    loader.get_config_value = Mock(return_value="test_value")
    loader.get_all_config = Mock(return_value={})
    loader.reload_config = Mock()
    
    return loader


@pytest.fixture
def mock_logger():
    """
    Crea un mock del Logger para tests.
    
    Returns:
        Mock object con métodos del Logger
    """
    from unittest.mock import Mock
    
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    
    return logger


# ==================== FIXTURES DE DATOS DE PRUEBA ====================

@pytest.fixture
def sample_ohlcv_data():
    """
    Datos OHLCV de ejemplo para tests de trading.
    
    Returns:
        List de tuplas (timestamp, open, high, low, close, volume)
    """
    return [
        ("2025-11-06 10:00:00", 1.1000, 1.1050, 1.0980, 1.1020, 1000),
        ("2025-11-06 10:05:00", 1.1020, 1.1080, 1.1010, 1.1060, 1200),
        ("2025-11-06 10:10:00", 1.1060, 1.1100, 1.1040, 1.1090, 1100),
        ("2025-11-06 10:15:00", 1.1090, 1.1120, 1.1070, 1.1100, 900),
        ("2025-11-06 10:20:00", 1.1100, 1.1130, 1.1085, 1.1110, 1050),
    ]


@pytest.fixture
def sample_magic_number_data():
    """
    Datos de Magic Numbers de ejemplo para tests.
    
    Returns:
        Dict con estructura: bot_id, ia_id, order_type
    """
    return {
        "bot_id": 1,
        "ia_id": 2,
        "order_type": 1,  # 1: Market, 2: Limit
        "expected_magic": 121000
    }


# ==================== CONFIGURACIÓN DE PYTEST ====================

def pytest_configure(config):
    """
    Configuración inicial de pytest.
    
    Registra markers personalizados para el proyecto.
    """
    config.addinivalue_line(
        "markers", "unit: Tests unitarios de componentes individuales"
    )
    config.addinivalue_line(
        "markers", "integration: Tests de integración entre componentes"
    )
    config.addinivalue_line(
        "markers", "slow: Tests que toman más tiempo en ejecutarse"
    )
    config.addinivalue_line(
        "markers", "requires_mt5: Tests que requieren conexión a MT5"
    )
    config.addinivalue_line(
        "markers", "requires_ia: Tests que requieren conexión a API de IA"
    )


# ==================== HELPERS DE TESTING ====================

def assert_dict_contains(actual: Dict, expected: Dict, path: str = ""):
    """
    Helper para verificar que un diccionario contiene otro.
    
    Args:
        actual: Diccionario actual
        expected: Diccionario con valores esperados
        path: Ruta actual para mensajes de error (interno)
        
    Raises:
        AssertionError: Si algún valor no coincide
    """
    for key, expected_value in expected.items():
        current_path = f"{path}.{key}" if path else key
        
        assert key in actual, f"Missing key: {current_path}"
        actual_value = actual[key]
        
        if isinstance(expected_value, dict):
            assert isinstance(actual_value, dict), \
                f"{current_path} should be dict, got {type(actual_value)}"
            assert_dict_contains(actual_value, expected_value, current_path)
        else:
            assert actual_value == expected_value, \
                f"{current_path}: expected {expected_value}, got {actual_value}"


def create_temp_json_file(directory: Path, filename: str, data: Dict) -> Path:
    """
    Helper para crear archivos JSON temporales en tests.
    
    Args:
        directory: Directorio donde crear el archivo
        filename: Nombre del archivo
        data: Datos a escribir en JSON
        
    Returns:
        Path al archivo creado
    """
    file_path = directory / filename
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    return file_path
