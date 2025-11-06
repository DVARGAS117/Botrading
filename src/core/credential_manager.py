"""
Módulo de gestión segura de credenciales para el sistema Botrading.

Este módulo implementa la funcionalidad del Ticket T47: Almacenamiento seguro
de credenciales, proporcionando encriptación, desencriptación y gestión segura
de credenciales sensibles como claves de MT5 y API keys de Gemini.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T47 - Almacenamiento seguro de credenciales
"""
import os
import json
import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from cryptography.fernet import Fernet, InvalidToken


# Configurar logging
logger = logging.getLogger(__name__)


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class CredentialError(Exception):
    """Excepción base para errores de credenciales"""
    pass


class EncryptionError(CredentialError):
    """Excepción para errores de encriptación"""
    pass


class DecryptionError(CredentialError):
    """Excepción para errores de desencriptación"""
    pass


# ==================== CREDENTIAL MANAGER ====================

class CredentialManager:
    """
    Gestor de credenciales con encriptación usando Fernet (AES-128).
    
    Proporciona funcionalidad para:
    - Encriptar y desencriptar credenciales
    - Guardar y cargar credenciales desde archivos encriptados
    - Gestionar credenciales en memoria de forma segura
    - Validar credenciales requeridas para MT5 y Gemini
    
    Attributes:
        _encryption_key (bytes): Clave de encriptación Fernet
        _fernet (Fernet): Instancia de Fernet para operaciones criptográficas
        _credentials (Dict): Credenciales en memoria (nunca se loguean)
    
    Security Features:
        - Encriptación simétrica AES-128 via Fernet
        - Claves no se exponen en __repr__ o __str__
        - Soporte para variables de entorno
        - Permisos restrictivos en archivos (Unix)
    
    Example:
        >>> # Generar y usar una clave
        >>> manager = CredentialManager()
        >>> manager.set_credential("mt5.login", "12345678")
        >>> manager.save_to_file(manager.get_all_credentials(), "creds.enc")
        
        >>> # Cargar desde archivo
        >>> manager2 = CredentialManager(encryption_key=manager._encryption_key)
        >>> creds = manager2.load_from_file("creds.enc")
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Inicializa el gestor de credenciales.
        
        Args:
            encryption_key: Clave de encriptación Fernet. Si no se proporciona,
                          se intenta cargar desde BOTRADING_ENCRYPTION_KEY o
                          se genera una nueva.
        
        Raises:
            CredentialError: Si la clave es inválida
        """
        self._credentials: Dict[str, Any] = {}
        
        # Cargar o generar clave
        if encryption_key is None:
            encryption_key = self._load_key_from_env()
        
        if encryption_key is None:
            # Generar nueva clave
            encryption_key = Fernet.generate_key()
            logger.warning(
                "Se generó una nueva clave de encriptación. "
                "Guárdela en BOTRADING_ENCRYPTION_KEY para reutilizarla."
            )
        
        # Validar clave
        if not isinstance(encryption_key, bytes):
            raise CredentialError(
                f"La clave de encriptación debe ser de tipo bytes, "
                f"se recibió {type(encryption_key).__name__}"
            )
        
        try:
            self._fernet = Fernet(encryption_key)
            self._encryption_key = encryption_key
        except Exception as e:
            raise CredentialError(f"La clave de encriptación inválida: {e}")
        
        logger.info("CredentialManager inicializado correctamente")
    
    def _load_key_from_env(self) -> Optional[bytes]:
        """
        Carga la clave de encriptación desde la variable de entorno.
        
        Returns:
            Clave de encriptación o None si no está definida
        """
        key_str = os.environ.get("BOTRADING_ENCRYPTION_KEY")
        if key_str:
            try:
                # La clave en env debe estar en base64
                return base64.b64decode(key_str)
            except Exception as e:
                logger.error(f"Error decodificando clave desde env: {e}")
                return None
        return None
    
    # ==================== ENCRIPTACIÓN/DESENCRIPTACIÓN ====================
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> bytes:
        """
        Encripta un diccionario de credenciales.
        
        Args:
            credentials: Diccionario con credenciales a encriptar
        
        Returns:
            Datos encriptados en bytes
        
        Raises:
            EncryptionError: Si falla la encriptación
        """
        if not isinstance(credentials, dict):
            raise EncryptionError(
                f"Las credenciales debe ser un diccionario, "
                f"se recibió {type(credentials).__name__}"
            )
        
        try:
            # Convertir a JSON y encriptar
            json_data = json.dumps(credentials).encode('utf-8')
            encrypted_data = self._fernet.encrypt(json_data)
            
            logger.debug("Credenciales encriptadas exitosamente")
            return encrypted_data
        
        except Exception as e:
            raise EncryptionError(f"Error al encriptar credenciales: {e}")
    
    def decrypt_credentials(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Desencripta datos de credenciales.
        
        Args:
            encrypted_data: Datos encriptados en bytes
        
        Returns:
            Diccionario con credenciales desencriptadas
        
        Raises:
            DecryptionError: Si falla la desencriptación
        """
        try:
            # Desencriptar y parsear JSON
            decrypted_data = self._fernet.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode('utf-8'))
            
            logger.debug("Credenciales desencriptadas exitosamente")
            return credentials
        
        except InvalidToken:
            raise DecryptionError(
                "Error de desencriptación: clave incorrecta o datos corruptos"
            )
        except json.JSONDecodeError as e:
            raise DecryptionError(f"Error parseando credenciales: datos corruptos - {e}")
        except Exception as e:
            raise DecryptionError(f"Error al desencriptar credenciales: {e}")
    
    # ==================== OPERACIONES DE ARCHIVO ====================
    
    def save_to_file(
        self, 
        credentials: Dict[str, Any], 
        file_path: Union[str, Path]
    ) -> None:
        """
        Guarda credenciales encriptadas en un archivo.
        
        Args:
            credentials: Diccionario con credenciales
            file_path: Ruta del archivo donde guardar
        
        Raises:
            EncryptionError: Si falla la encriptación o escritura
        """
        file_path = Path(file_path)
        
        try:
            # Crear directorio padre si no existe
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Encriptar credenciales
            encrypted_data = self.encrypt_credentials(credentials)
            
            # Escribir archivo
            file_path.write_bytes(encrypted_data)
            
            # Establecer permisos restrictivos (solo en Unix)
            self._set_file_permissions(file_path)
            
            logger.info(f"Credenciales guardadas en {file_path}")
        
        except Exception as e:
            raise EncryptionError(f"Error guardando credenciales: {e}")
    
    def load_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Carga credenciales desde un archivo encriptado.
        
        Args:
            file_path: Ruta del archivo a cargar
        
        Returns:
            Diccionario con credenciales desencriptadas
        
        Raises:
            CredentialError: Si el archivo no existe
            DecryptionError: Si falla la desencriptación
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise CredentialError(f"El archivo {file_path} no existe")
        
        try:
            # Leer archivo encriptado
            encrypted_data = file_path.read_bytes()
            
            # Desencriptar
            credentials = self.decrypt_credentials(encrypted_data)
            
            logger.info(f"Credenciales cargadas desde {file_path}")
            return credentials
        
        except DecryptionError:
            raise
        except Exception as e:
            raise CredentialError(f"Error cargando credenciales: {e}")
    
    def _set_file_permissions(self, file_path: Path) -> None:
        """
        Establece permisos restrictivos en el archivo (solo Unix).
        
        Args:
            file_path: Ruta del archivo
        """
        import platform
        if platform.system() != "Windows":
            try:
                import stat
                # 0o600 = rw------- (solo dueño puede leer/escribir)
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
                logger.debug(f"Permisos restrictivos establecidos en {file_path}")
            except Exception as e:
                logger.warning(f"No se pudieron establecer permisos: {e}")
    
    # ==================== GESTIÓN DE CREDENCIALES ====================
    
    def set_credential(self, key: str, value: Any) -> None:
        """
        Establece una credencial en memoria.
        
        Soporta dot notation para claves anidadas:
        - "api_key" -> {"api_key": value}
        - "mt5.login" -> {"mt5": {"login": value}}
        
        Args:
            key: Clave de la credencial (soporta dot notation)
            value: Valor de la credencial
        """
        keys = key.split('.')
        current = self._credentials
        
        # Navegar/crear estructura anidada
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Establecer valor final
        current[keys[-1]] = value
        logger.debug(f"Credencial '{key}' establecida")
    
    def get_credential(self, key: str, default: Any = None) -> Any:
        """
        Obtiene una credencial de memoria.
        
        Args:
            key: Clave de la credencial (soporta dot notation)
            default: Valor por defecto si no existe
        
        Returns:
            Valor de la credencial o default si no existe
        """
        keys = key.split('.')
        current = self._credentials
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def delete_credential(self, key: str) -> None:
        """
        Elimina una credencial de memoria.
        
        Args:
            key: Clave de la credencial (soporta dot notation)
        """
        keys = key.split('.')
        current = self._credentials
        
        try:
            # Navegar hasta el penúltimo nivel
            for k in keys[:-1]:
                current = current[k]
            
            # Eliminar clave final
            if keys[-1] in current:
                del current[keys[-1]]
                logger.debug(f"Credencial '{key}' eliminada")
        except (KeyError, TypeError):
            logger.warning(f"Credencial '{key}' no existe")
    
    def has_credential(self, key: str) -> bool:
        """
        Verifica si existe una credencial.
        
        Args:
            key: Clave de la credencial (soporta dot notation)
        
        Returns:
            True si existe, False en caso contrario
        """
        return self.get_credential(key) is not None
    
    def get_all_credentials(self) -> Dict[str, Any]:
        """
        Obtiene todas las credenciales.
        
        Returns:
            Diccionario con todas las credenciales
        """
        return self._credentials.copy()
    
    def clear_credentials(self) -> None:
        """
        Limpia todas las credenciales de memoria.
        """
        self._credentials.clear()
        logger.info("Credenciales limpiadas de memoria")
    
    # ==================== VALIDACIÓN ====================
    
    def validate_required_keys(self, required_keys: List[str]) -> bool:
        """
        Valida que existan todas las claves requeridas.
        
        Args:
            required_keys: Lista de claves requeridas (soporta dot notation)
        
        Returns:
            True si todas las claves existen
        
        Raises:
            CredentialError: Si faltan claves requeridas
        """
        missing_keys = [
            key for key in required_keys 
            if not self.has_credential(key)
        ]
        
        if missing_keys:
            raise CredentialError(
                f"Credenciales faltantes: {', '.join(missing_keys)}"
            )
        
        logger.debug("Todas las credenciales requeridas están presentes")
        return True
    
    def validate_mt5_credentials(self) -> bool:
        """
        Valida que existan las credenciales de MT5.
        
        Returns:
            True si todas las credenciales de MT5 existen
        
        Raises:
            CredentialError: Si faltan credenciales de MT5
        """
        required = ["mt5.login", "mt5.password", "mt5.server"]
        
        try:
            return self.validate_required_keys(required)
        except CredentialError as e:
            raise CredentialError(f"Credenciales MT5 incompletas: {e}")
    
    def validate_gemini_credentials(self) -> bool:
        """
        Valida que existan las credenciales de Gemini.
        
        Returns:
            True si existe la API key de Gemini
        
        Raises:
            CredentialError: Si falta la API key de Gemini
        """
        required = ["gemini.api_key"]
        
        try:
            return self.validate_required_keys(required)
        except CredentialError as e:
            raise CredentialError(f"Credenciales Gemini incompletas: {e}")
    
    # ==================== REPRESENTACIÓN ====================
    
    def __repr__(self) -> str:
        """
        Representación del objeto sin exponer credenciales.
        """
        num_creds = len(self._credentials)
        return f"<CredentialManager(credenciales={num_creds})>"
    
    def __str__(self) -> str:
        """
        Representación en string sin exponer credenciales.
        """
        keys = list(self._credentials.keys())
        return f"CredentialManager con {len(keys)} categorías: {keys}"
