"""
Tests unitarios para el módulo credential_manager.

Este módulo implementa tests para el Ticket T47: Almacenamiento seguro de credenciales,
validando la encriptación, desencriptación y gestión segura de credenciales.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T47 - Almacenamiento seguro de credenciales
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from cryptography.fernet import Fernet, InvalidToken


# Importar la clase a testear (aún no existe, TDD Red)
from src.core.credential_manager import (
    CredentialManager,
    CredentialError,
    EncryptionError,
    DecryptionError
)


# ==================== FIXTURES ====================

@pytest.fixture
def encryption_key():
    """Genera una clave de encriptación válida para tests"""
    return Fernet.generate_key()


@pytest.fixture
def credential_manager(encryption_key):
    """Crea una instancia de CredentialManager con clave de test"""
    return CredentialManager(encryption_key=encryption_key)


@pytest.fixture
def sample_credentials():
    """Credenciales de ejemplo para tests"""
    return {
        "mt5": {
            "login": "12345678",
            "password": "SecurePassword123!",
            "server": "MetaQuotes-Demo"
        },
        "gemini": {
            "api_key": "AIzaSyABC123XYZ789-example_key_string"
        }
    }


@pytest.fixture
def encrypted_file(temp_dir, encryption_key, sample_credentials):
    """Crea un archivo encriptado de ejemplo"""
    file_path = temp_dir / "credentials.enc"
    
    # Encriptar manualmente para el test
    fernet = Fernet(encryption_key)
    json_data = json.dumps(sample_credentials).encode()
    encrypted_data = fernet.encrypt(json_data)
    
    file_path.write_bytes(encrypted_data)
    return file_path


# ==================== TESTS DE INICIALIZACIÓN ====================

@pytest.mark.unit
class TestCredentialManagerInitialization:
    """Tests para la inicialización del CredentialManager"""
    
    def test_init_with_valid_key(self, encryption_key):
        """Debe inicializar correctamente con una clave válida"""
        manager = CredentialManager(encryption_key=encryption_key)
        assert manager is not None
        assert manager._credentials == {}
    
    def test_init_with_invalid_key_type(self):
        """Debe lanzar error si la clave no es bytes"""
        with pytest.raises(CredentialError, match="debe ser de tipo bytes"):
            CredentialManager(encryption_key="not_bytes")
    
    def test_init_with_invalid_key_format(self):
        """Debe lanzar error si la clave no es un formato Fernet válido"""
        with pytest.raises(CredentialError, match="clave de encriptación inválida"):
            CredentialManager(encryption_key=b"invalid_key")
    
    def test_init_generates_key_if_none_provided(self):
        """Debe generar una clave automáticamente si no se proporciona"""
        manager = CredentialManager()
        assert manager is not None
        assert manager._encryption_key is not None
        assert isinstance(manager._encryption_key, bytes)
    
    def test_init_from_env_variable(self, monkeypatch, encryption_key):
        """Debe cargar clave desde variable de entorno BOTRADING_ENCRYPTION_KEY"""
        # Convertir key a string base64 para la env var
        import base64
        key_str = base64.b64encode(encryption_key).decode()
        
        monkeypatch.setenv("BOTRADING_ENCRYPTION_KEY", key_str)
        manager = CredentialManager()
        
        assert manager._encryption_key == encryption_key


# ==================== TESTS DE ENCRIPTACIÓN/DESENCRIPTACIÓN ====================

@pytest.mark.unit
class TestEncryptionDecryption:
    """Tests para encriptación y desencriptación de credenciales"""
    
    def test_encrypt_credentials_success(self, credential_manager, sample_credentials):
        """Debe encriptar credenciales correctamente"""
        encrypted = credential_manager.encrypt_credentials(sample_credentials)
        
        assert isinstance(encrypted, bytes)
        assert encrypted != json.dumps(sample_credentials).encode()
        assert len(encrypted) > 0
    
    def test_encrypt_credentials_with_empty_dict(self, credential_manager):
        """Debe encriptar correctamente un diccionario vacío"""
        encrypted = credential_manager.encrypt_credentials({})
        
        assert isinstance(encrypted, bytes)
        assert len(encrypted) > 0
    
    def test_encrypt_credentials_invalid_type(self, credential_manager):
        """Debe lanzar error si las credenciales no son un diccionario"""
        with pytest.raises(EncryptionError, match="debe ser un diccionario"):
            credential_manager.encrypt_credentials("not_a_dict")
    
    def test_decrypt_credentials_success(self, credential_manager, sample_credentials):
        """Debe desencriptar credenciales correctamente"""
        encrypted = credential_manager.encrypt_credentials(sample_credentials)
        decrypted = credential_manager.decrypt_credentials(encrypted)
        
        assert decrypted == sample_credentials
    
    def test_decrypt_credentials_with_wrong_key(self, sample_credentials):
        """Debe lanzar error al desencriptar con clave incorrecta"""
        # Encriptar con una clave
        key1 = Fernet.generate_key()
        manager1 = CredentialManager(encryption_key=key1)
        encrypted = manager1.encrypt_credentials(sample_credentials)
        
        # Intentar desencriptar con otra clave
        key2 = Fernet.generate_key()
        manager2 = CredentialManager(encryption_key=key2)
        
        with pytest.raises(DecryptionError, match="clave incorrecta"):
            manager2.decrypt_credentials(encrypted)
    
    def test_decrypt_credentials_corrupted_data(self, credential_manager):
        """Debe lanzar error si los datos están corruptos"""
        corrupted_data = b"corrupted_encrypted_data"
        
        with pytest.raises(DecryptionError, match="datos corruptos"):
            credential_manager.decrypt_credentials(corrupted_data)
    
    def test_encryption_is_deterministic(self, credential_manager, sample_credentials):
        """La encriptación debe ser no-determinística (distinto cada vez)"""
        encrypted1 = credential_manager.encrypt_credentials(sample_credentials)
        encrypted2 = credential_manager.encrypt_credentials(sample_credentials)
        
        # Fernet incluye timestamp, por lo que debe ser diferente
        assert encrypted1 != encrypted2
        
        # Pero ambos deben desencriptar al mismo valor
        assert credential_manager.decrypt_credentials(encrypted1) == sample_credentials
        assert credential_manager.decrypt_credentials(encrypted2) == sample_credentials


# ==================== TESTS DE ALMACENAMIENTO EN ARCHIVO ====================

@pytest.mark.unit
class TestFileOperations:
    """Tests para operaciones de archivo (save/load)"""
    
    def test_save_to_file_success(self, credential_manager, sample_credentials, temp_dir):
        """Debe guardar credenciales encriptadas en archivo"""
        file_path = temp_dir / "test_credentials.enc"
        
        credential_manager.save_to_file(sample_credentials, file_path)
        
        assert file_path.exists()
        assert file_path.stat().st_size > 0
        # Verificar que no es texto plano
        content = file_path.read_text(errors='ignore')
        assert "SecurePassword123!" not in content
    
    def test_save_to_file_creates_directories(self, credential_manager, sample_credentials, temp_dir):
        """Debe crear directorios padre si no existen"""
        file_path = temp_dir / "nested" / "dir" / "credentials.enc"
        
        credential_manager.save_to_file(sample_credentials, file_path)
        
        assert file_path.exists()
        assert file_path.parent.exists()
    
    def test_save_to_file_overwrites_existing(self, credential_manager, sample_credentials, temp_dir):
        """Debe sobrescribir archivo existente"""
        file_path = temp_dir / "credentials.enc"
        
        # Primera escritura
        credential_manager.save_to_file(sample_credentials, file_path)
        original_size = file_path.stat().st_size
        
        # Segunda escritura con datos diferentes
        new_credentials = {"test": "data"}
        credential_manager.save_to_file(new_credentials, file_path)
        
        assert file_path.exists()
        # El tamaño debería cambiar
        assert file_path.stat().st_size != original_size
    
    def test_load_from_file_success(self, credential_manager, encrypted_file):
        """Debe cargar credenciales desde archivo encriptado"""
        credentials = credential_manager.load_from_file(encrypted_file)
        
        assert "mt5" in credentials
        assert "gemini" in credentials
        assert credentials["mt5"]["login"] == "12345678"
    
    def test_load_from_file_not_found(self, credential_manager, temp_dir):
        """Debe lanzar error si el archivo no existe"""
        non_existent = temp_dir / "not_exists.enc"
        
        with pytest.raises(CredentialError, match="no existe"):
            credential_manager.load_from_file(non_existent)
    
    def test_load_from_file_corrupted(self, credential_manager, temp_dir):
        """Debe lanzar error si el archivo está corrupto"""
        corrupted_file = temp_dir / "corrupted.enc"
        corrupted_file.write_bytes(b"not_encrypted_data")
        
        with pytest.raises(DecryptionError):
            credential_manager.load_from_file(corrupted_file)
    
    def test_roundtrip_save_and_load(self, credential_manager, sample_credentials, temp_dir):
        """Debe poder guardar y cargar credenciales sin pérdida"""
        file_path = temp_dir / "roundtrip.enc"
        
        credential_manager.save_to_file(sample_credentials, file_path)
        loaded = credential_manager.load_from_file(file_path)
        
        assert loaded == sample_credentials


# ==================== TESTS DE GESTIÓN DE CREDENCIALES ====================

@pytest.mark.unit
class TestCredentialManagement:
    """Tests para get/set/delete de credenciales individuales"""
    
    def test_set_credential_simple_key(self, credential_manager):
        """Debe establecer una credencial con clave simple"""
        credential_manager.set_credential("api_key", "test_value")
        
        assert credential_manager.get_credential("api_key") == "test_value"
    
    def test_set_credential_nested_key(self, credential_manager):
        """Debe establecer credencial con clave anidada (dot notation)"""
        credential_manager.set_credential("mt5.login", "12345678")
        credential_manager.set_credential("mt5.password", "secret")
        
        assert credential_manager.get_credential("mt5.login") == "12345678"
        assert credential_manager.get_credential("mt5.password") == "secret"
    
    def test_get_credential_not_found(self, credential_manager):
        """Debe retornar None si la credencial no existe"""
        result = credential_manager.get_credential("non_existent")
        assert result is None
    
    def test_get_credential_with_default(self, credential_manager):
        """Debe retornar valor por defecto si la credencial no existe"""
        result = credential_manager.get_credential("non_existent", default="default_value")
        assert result == "default_value"
    
    def test_delete_credential_simple_key(self, credential_manager):
        """Debe eliminar una credencial con clave simple"""
        credential_manager.set_credential("temp_key", "temp_value")
        credential_manager.delete_credential("temp_key")
        
        assert credential_manager.get_credential("temp_key") is None
    
    def test_delete_credential_nested_key(self, credential_manager):
        """Debe eliminar credencial con clave anidada"""
        credential_manager.set_credential("mt5.login", "12345678")
        credential_manager.delete_credential("mt5.login")
        
        assert credential_manager.get_credential("mt5.login") is None
    
    def test_has_credential(self, credential_manager):
        """Debe verificar si existe una credencial"""
        credential_manager.set_credential("test_key", "test_value")
        
        assert credential_manager.has_credential("test_key") is True
        assert credential_manager.has_credential("non_existent") is False
    
    def test_get_all_credentials(self, credential_manager, sample_credentials):
        """Debe retornar todas las credenciales"""
        for key, value in sample_credentials.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    credential_manager.set_credential(f"{key}.{sub_key}", sub_value)
            else:
                credential_manager.set_credential(key, value)
        
        all_creds = credential_manager.get_all_credentials()
        assert "mt5" in all_creds
        assert "gemini" in all_creds


# ==================== TESTS DE VALIDACIÓN ====================

@pytest.mark.unit
class TestCredentialValidation:
    """Tests para validación de credenciales requeridas"""
    
    def test_validate_required_keys_success(self, credential_manager, sample_credentials):
        """Debe validar exitosamente cuando todas las claves requeridas existen"""
        # Cargar credenciales
        for key, value in sample_credentials.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    credential_manager.set_credential(f"{key}.{sub_key}", sub_value)
        
        required = ["mt5.login", "mt5.password", "gemini.api_key"]
        result = credential_manager.validate_required_keys(required)
        
        assert result is True
    
    def test_validate_required_keys_missing(self, credential_manager):
        """Debe lanzar error si faltan claves requeridas"""
        credential_manager.set_credential("mt5.login", "12345678")
        
        required = ["mt5.login", "mt5.password", "gemini.api_key"]
        
        with pytest.raises(CredentialError, match="Credenciales faltantes"):
            credential_manager.validate_required_keys(required)
    
    def test_validate_mt5_credentials(self, credential_manager, sample_credentials):
        """Debe validar credenciales específicas de MT5"""
        for sub_key, sub_value in sample_credentials["mt5"].items():
            credential_manager.set_credential(f"mt5.{sub_key}", sub_value)
        
        result = credential_manager.validate_mt5_credentials()
        assert result is True
    
    def test_validate_mt5_credentials_incomplete(self, credential_manager):
        """Debe fallar validación de MT5 si faltan credenciales"""
        credential_manager.set_credential("mt5.login", "12345678")
        # Falta password y server
        
        with pytest.raises(CredentialError, match="MT5"):
            credential_manager.validate_mt5_credentials()
    
    def test_validate_gemini_credentials(self, credential_manager, sample_credentials):
        """Debe validar credenciales de Gemini"""
        credential_manager.set_credential("gemini.api_key", sample_credentials["gemini"]["api_key"])
        
        result = credential_manager.validate_gemini_credentials()
        assert result is True
    
    def test_validate_gemini_credentials_missing(self, credential_manager):
        """Debe fallar validación de Gemini si falta API key"""
        with pytest.raises(CredentialError, match="Gemini"):
            credential_manager.validate_gemini_credentials()


# ==================== TESTS DE SEGURIDAD ====================

@pytest.mark.unit
class TestSecurity:
    """Tests relacionados con seguridad y buenas prácticas"""
    
    def test_credentials_not_logged_in_repr(self, credential_manager, sample_credentials):
        """El __repr__ no debe mostrar credenciales sensibles"""
        for key, value in sample_credentials.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    credential_manager.set_credential(f"{key}.{sub_key}", sub_value)
        
        repr_str = repr(credential_manager)
        
        assert "SecurePassword123!" not in repr_str
        assert "AIzaSyABC123XYZ789" not in repr_str
        assert "CredentialManager" in repr_str
    
    def test_credentials_not_logged_in_str(self, credential_manager, sample_credentials):
        """El __str__ no debe mostrar credenciales sensibles"""
        for key, value in sample_credentials.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    credential_manager.set_credential(f"{key}.{sub_key}", sub_value)
        
        str_repr = str(credential_manager)
        
        assert "SecurePassword123!" not in str_repr
        assert "AIzaSyABC123XYZ789" not in str_repr
    
    def test_clear_credentials(self, credential_manager, sample_credentials):
        """Debe poder limpiar todas las credenciales de memoria"""
        for key, value in sample_credentials.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    credential_manager.set_credential(f"{key}.{sub_key}", sub_value)
        
        credential_manager.clear_credentials()
        
        all_creds = credential_manager.get_all_credentials()
        assert all_creds == {}
    
    def test_file_permissions_are_restrictive(self, credential_manager, sample_credentials, temp_dir):
        """El archivo de credenciales debe tener permisos restrictivos (Unix)"""
        import platform
        if platform.system() == "Windows":
            pytest.skip("Test de permisos no aplicable en Windows")
        
        file_path = temp_dir / "secure_credentials.enc"
        credential_manager.save_to_file(sample_credentials, file_path)
        
        # Verificar que solo el dueño tiene permisos de lectura/escritura
        import stat
        file_stat = file_path.stat()
        mode = stat.S_IMODE(file_stat.st_mode)
        
        # 0o600 = rw------- (solo dueño puede leer/escribir)
        assert mode == 0o600
    
    def test_get_encryption_key_raises_error(self, credential_manager):
        """No debe exponer la clave de encriptación directamente"""
        with pytest.raises(AttributeError):
            _ = credential_manager.encryption_key


# ==================== TESTS DE INTEGRACIÓN CON ConfigLoader ====================

@pytest.mark.integration
class TestConfigLoaderIntegration:
    """Tests de integración con ConfigLoader"""
    
    def test_load_credentials_from_encrypted_file_to_config(
        self, credential_manager, sample_credentials, temp_dir
    ):
        """Debe poder cargar credenciales encriptadas y usarlas en ConfigLoader"""
        from src.core.config_loader import ConfigLoader
        
        # Guardar credenciales encriptadas
        cred_file = temp_dir / "credentials.enc"
        credential_manager.save_to_file(sample_credentials, cred_file)
        
        # Cargar y usar en ConfigLoader
        loaded_creds = credential_manager.load_from_file(cred_file)
        
        config_loader = ConfigLoader()
        # Simular que ConfigLoader carga estas credenciales
        config_loader._config["credentials"] = loaded_creds
        
        assert config_loader.get_config_value("credentials.mt5.login") == "12345678"
        assert config_loader.get_config_value("credentials.gemini.api_key") is not None
