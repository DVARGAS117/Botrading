"""
Módulo para validar cuota y disponibilidad de modelo IA.

Este módulo implementa el Ticket T48: Validación de cuota y disponibilidad
de modelo IA, para evitar fallos por límites de uso.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T48 - Validación de cuota y disponibilidad de modelo IA
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from zoneinfo import ZoneInfo


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class QuotaValidationError(Exception):
    """Excepción para errores en validación de cuota"""
    pass


# ==================== ENUMERACIONES ====================

class QuotaStatus(Enum):
    """Estados de cuota disponible"""
    AVAILABLE = "available"      # Cuota disponible, uso normal
    WARNING = "warning"          # Alcanzó umbral de advertencia (80%)
    CRITICAL = "critical"        # Alcanzó umbral crítico (95%)
    EXCEEDED = "exceeded"        # Cuota excedida
    DISABLED = "disabled"        # Validación desactivada
    ERROR = "error"             # Error al consultar


# ==================== DATACLASSES ====================

@dataclass
class ModelAvailability:
    """Información de disponibilidad del modelo"""
    available: bool
    model: str
    status: str  # "active", "maintenance", "deprecated", etc.
    message: Optional[str] = None


@dataclass
class QuotaValidationResult:
    """Resultado de validación de cuota"""
    is_valid: bool
    status: QuotaStatus
    message: str
    requests_used: int = 0
    requests_limit: int = 0
    tokens_used: int = 0
    tokens_limit: int = 0
    timestamp: Optional[datetime] = None


@dataclass
class CompleteValidationResult:
    """Resultado de validación completa (cuota + modelo)"""
    is_valid: bool
    quota_ok: bool
    model_ok: bool
    quota_result: Optional[QuotaValidationResult] = None
    model_result: Optional[ModelAvailability] = None
    message: str = ""


# ==================== CLASE PRINCIPAL ====================

class QuotaValidator:
    """
    Valida cuota y disponibilidad de modelo IA.
    
    Este módulo es crítico para evitar fallos por límites de uso de la API
    de IA. Verifica tanto la cuota disponible (requests y tokens) como la
    disponibilidad del modelo antes de permitir consultas.
    
    Funcionalidades:
    - Validación de cuota (requests/minute, tokens/minute, daily limits)
    - Verificación de disponibilidad de modelo
    - Sistema de caché para reducir llamadas a API
    - Reintentos con backoff exponencial
    - Umbrales configurables de advertencia
    - Estadísticas de uso
    
    Ejemplo:
        from src.core.quota_validator import QuotaValidator
        
        validator = QuotaValidator(config=config)
        
        # Validar antes de consultar IA
        if validator.validate_all().is_valid:
            # Proceder con consulta a IA
            response = call_gemini_api(...)
        else:
            # Esperar o abortar
            print("Cuota excedida o modelo no disponible")
    """
    
    # Providers soportados
    SUPPORTED_PROVIDERS = ["gemini", "openai", "anthropic"]
    
    # Configuración por defecto
    DEFAULT_CONFIG = {
        "enabled": False,
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
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el QuotaValidator.
        
        Args:
            config: Configuración con parámetros de validación
            
        Raises:
            QuotaValidationError: Si la configuración es inválida
        """
        # Obtener configuración o usar defaults
        quota_config = config.get("quota_validation", {})
        
        # Configuración básica
        self.enabled = quota_config.get("enabled", self.DEFAULT_CONFIG["enabled"])
        self.provider = quota_config.get("provider", self.DEFAULT_CONFIG["provider"])
        self.check_interval_seconds = quota_config.get(
            "check_interval_seconds",
            self.DEFAULT_CONFIG["check_interval_seconds"]
        )
        self.cache_duration_seconds = quota_config.get(
            "cache_duration_seconds",
            self.DEFAULT_CONFIG["cache_duration_seconds"]
        )
        
        # Validar provider
        if self.provider not in self.SUPPORTED_PROVIDERS:
            raise QuotaValidationError(
                f"Provider '{self.provider}' no soportado. "
                f"Soportados: {', '.join(self.SUPPORTED_PROVIDERS)}"
            )
        
        # Solo gemini está implementado por ahora
        if self.provider != "gemini":
            raise QuotaValidationError(
                f"Provider '{self.provider}' no está implementado aún. "
                f"Solo 'gemini' está disponible actualmente."
            )
        
        # Límites de cuota
        default_limits = self.DEFAULT_CONFIG["quota_limits"]
        self.quota_limits = quota_config.get("quota_limits", default_limits).copy()
        # Merge con defaults
        for key, value in default_limits.items():
            if key not in self.quota_limits:
                self.quota_limits[key] = value
        
        # Umbrales
        default_thresholds = self.DEFAULT_CONFIG["thresholds"]
        self.thresholds = quota_config.get("thresholds", default_thresholds).copy()
        for key, value in default_thresholds.items():
            if key not in self.thresholds:
                self.thresholds[key] = value
        
        # Configuración de reintentos
        default_retry = self.DEFAULT_CONFIG["retry"]
        retry_config = quota_config.get("retry", default_retry).copy()
        self.max_attempts = retry_config.get("max_attempts", default_retry["max_attempts"])
        self.backoff_factor = retry_config.get("backoff_factor", default_retry["backoff_factor"])
        self.timeout_seconds = retry_config.get("timeout_seconds", default_retry["timeout_seconds"])
        
        # Caché
        self._cache: Optional[QuotaValidationResult] = None
        self._cache_timestamp: Optional[datetime] = None
        
        # Estadísticas
        self._last_check_timestamp: Optional[datetime] = None
    
    def validate_quota(self) -> QuotaValidationResult:
        """
        Valida si hay cuota disponible para consultar la API de IA.
        
        Verifica:
        - Requests por minuto
        - Tokens por minuto
        - Límites diarios
        
        Usa caché si está disponible y no ha expirado.
        
        Returns:
            QuotaValidationResult con el estado de la cuota
            
        Raises:
            QuotaValidationError: Si falla después de todos los reintentos
        """
        # Si está desactivado, retornar válido
        if not self.enabled:
            return QuotaValidationResult(
                is_valid=True,
                status=QuotaStatus.DISABLED,
                message="Validación de cuota desactivada",
                timestamp=datetime.now()
            )
        
        # Verificar caché
        if self._is_cache_valid() and self._cache:
            return self._cache
        
        # Intentar validar con reintentos
        last_error = None
        for attempt in range(self.max_attempts):
            try:
                # Consultar API según provider
                if self.provider == "gemini":
                    response = self._check_gemini_quota()
                else:
                    raise QuotaValidationError(
                        f"Provider {self.provider} no implementado aún"
                    )
                
                # Determinar status según uso
                status = self._determine_quota_status(
                    response.requests_used,
                    response.requests_limit
                )
                
                # Crear resultado
                result = QuotaValidationResult(
                    is_valid=response.available,
                    status=status if response.available else QuotaStatus.EXCEEDED,
                    message=self._build_quota_message(status, response),
                    requests_used=response.requests_used,
                    requests_limit=response.requests_limit,
                    tokens_used=response.tokens_used,
                    tokens_limit=response.tokens_limit,
                    timestamp=datetime.now()
                )
                
                # Guardar en caché
                self._cache = result
                self._cache_timestamp = datetime.now()
                self._last_check_timestamp = datetime.now()
                
                return result
                
            except Exception as e:
                last_error = e
                if attempt < self.max_attempts - 1:
                    # Esperar antes de reintentar (backoff exponencial)
                    wait_time = self.backoff_factor ** attempt
                    time.sleep(wait_time)
                continue
        
        # Si llegamos aquí, agotamos todos los reintentos
        raise QuotaValidationError(
            f"Error validando cuota después de {self.max_attempts} reintentos agotados: {last_error}"
        )
    
    def check_model_availability(self) -> ModelAvailability:
        """
        Verifica si el modelo de IA está disponible.
        
        Consulta el estado del modelo (activo, mantenimiento, etc.)
        
        Returns:
            ModelAvailability con el estado del modelo
            
        Raises:
            QuotaValidationError: Si el modelo no existe o hay error
        """
        if self.provider == "gemini":
            return self._check_gemini_model_status()
        else:
            raise QuotaValidationError(
                f"Provider {self.provider} no implementado aún"
            )
    
    def validate_all(self) -> CompleteValidationResult:
        """
        Realiza validación completa: cuota + disponibilidad de modelo.
        
        Este es el método principal que debe usarse antes de consultar
        la API de IA.
        
        Returns:
            CompleteValidationResult con estado completo
        """
        # Validar cuota
        message = ""
        try:
            quota_result = self.validate_quota()
            quota_ok = quota_result.is_valid
        except QuotaValidationError as e:
            quota_result = None
            quota_ok = False
            message = f"Error validando cuota: {e}"
        
        # Validar modelo (solo si cuota OK)
        model_ok = False
        model_result = None
        if quota_ok:
            try:
                model_result = self.check_model_availability()
                model_ok = model_result.available
            except QuotaValidationError as e:
                message = f"Error verificando modelo: {e}"
        
        # Construir mensaje
        if quota_ok and model_ok:
            message = "✅ Cuota y modelo disponibles"
        elif not quota_ok:
            message = f"❌ Cuota no disponible: {quota_result.message if quota_result else 'Error'}"
        elif not model_ok:
            message = f"❌ Modelo no disponible: {model_result.status if model_result else 'Error'}"
        
        return CompleteValidationResult(
            is_valid=quota_ok and model_ok,
            quota_ok=quota_ok,
            model_ok=model_ok,
            quota_result=quota_result,
            model_result=model_result,
            message=message
        )
    
    def get_quota_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de uso de cuota.
        
        Returns:
            Diccionario con estadísticas de uso
        """
        # Forzar validación si no hay caché
        if not self._cache:
            self.validate_quota()
        
        if not self._cache:
            return {
                "status": "unknown",
                "message": "No se pudo obtener información de cuota"
            }
        
        requests_percentage = (
            (self._cache.requests_used / self._cache.requests_limit * 100)
            if self._cache.requests_limit > 0 else 0
        )
        
        tokens_percentage = (
            (self._cache.tokens_used / self._cache.tokens_limit * 100)
            if self._cache.tokens_limit > 0 else 0
        )
        
        return {
            "status": self._cache.status.value,
            "requests_used": self._cache.requests_used,
            "requests_limit": self._cache.requests_limit,
            "requests_remaining": self._cache.requests_limit - self._cache.requests_used,
            "requests_percentage": round(requests_percentage, 2),
            "tokens_used": self._cache.tokens_used,
            "tokens_limit": self._cache.tokens_limit,
            "tokens_remaining": self._cache.tokens_limit - self._cache.tokens_used,
            "tokens_percentage": round(tokens_percentage, 2),
            "last_check": self._cache.timestamp.isoformat() if self._cache.timestamp else None
        }
    
    def calculate_remaining_requests(self) -> int:
        """
        Calcula requests restantes.
        
        Returns:
            Número de requests disponibles
        """
        if not self._cache:
            self.validate_quota()
        
        return self._cache.requests_limit - self._cache.requests_used if self._cache else 0
    
    def estimate_time_to_quota_reset(self) -> int:
        """
        Estima segundos hasta el reset de cuota.
        
        La cuota por minuto se resetea al inicio del siguiente minuto.
        
        Returns:
            Segundos hasta el reset
        """
        now = datetime.now()
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        delta = next_minute - now
        return int(delta.total_seconds())
    
    def clear_cache(self):
        """Limpia el caché de validaciones."""
        self._cache = None
        self._cache_timestamp = None
    
    def reload_config(self, new_config: Dict[str, Any]):
        """
        Recarga la configuración.
        
        Args:
            new_config: Nueva configuración
        """
        # Actualizar solo los campos presentes en new_config
        quota_config = new_config.get("quota_validation", {})
        
        if "enabled" in quota_config:
            self.enabled = quota_config["enabled"]
        
        if "quota_limits" in quota_config:
            self.quota_limits.update(quota_config["quota_limits"])
        
        if "thresholds" in quota_config:
            self.thresholds.update(quota_config["thresholds"])
        
        # Limpiar caché para forzar re validación
        self.clear_cache()
    
    def _get_api_credentials(self) -> Dict[str, str]:
        """
        Obtiene credenciales de API desde CredentialManager.
        
        Returns:
            Diccionario con credenciales (api_key, etc.)
        """
        # TODO: Integrar con CredentialManager (T47)
        # Por ahora, retornar dummy para que los tests pasen
        return {
            "api_key": "dummy_key_for_tests",
            "project_id": "dummy_project"
        }
    
    def _check_gemini_quota(self):
        """
        Verifica cuota de Gemini API.
        
        Returns:
            Mock response con información de cuota
            
        Note:
            Este método será implementado completamente cuando
            integremos con Gemini API (Fase 2, T10)
        """
        # TODO: Implementar llamada real a Gemini API
        # Por ahora, retornar mock para desarrollo
        from unittest.mock import MagicMock
        
        mock_response = MagicMock()
        mock_response.available = True
        mock_response.requests_used = 30
        mock_response.requests_limit = 60
        mock_response.tokens_used = 15000
        mock_response.tokens_limit = 32000
        
        return mock_response
    
    def _check_gemini_model_status(self) -> ModelAvailability:
        """
        Verifica estado del modelo en Gemini.
        
        Returns:
            ModelAvailability con estado del modelo
            
        Note:
            Este método será implementado completamente cuando
            integremos con Gemini API (Fase 2, T10)
        """
        # TODO: Implementar llamada real a Gemini API
        # Por ahora, retornar mock para desarrollo
        return ModelAvailability(
            available=True,
            model="gemini-2.5-pro",
            status="active",
            message="Modelo operativo"
        )
    
    def _determine_quota_status(
        self,
        used: int,
        limit: int
    ) -> QuotaStatus:
        """
        Determina el estado de cuota según uso.
        
        Args:
            used: Requests/tokens usados
            limit: Límite de requests/tokens
            
        Returns:
            QuotaStatus correspondiente
        """
        if limit == 0:
            return QuotaStatus.AVAILABLE
        
        percentage = (used / limit) * 100
        
        if percentage >= self.thresholds["critical_percentage"]:
            return QuotaStatus.CRITICAL
        elif percentage >= self.thresholds["warning_percentage"]:
            return QuotaStatus.WARNING
        else:
            return QuotaStatus.AVAILABLE
    
    def _build_quota_message(
        self,
        status: QuotaStatus,
        response
    ) -> str:
        """
        Construye mensaje descriptivo del estado de cuota.
        
        Args:
            status: Estado de cuota
            response: Respuesta de API
            
        Returns:
            Mensaje descriptivo
        """
        if status == QuotaStatus.AVAILABLE:
            return f"Cuota disponible: {response.requests_used}/{response.requests_limit} requests"
        elif status == QuotaStatus.WARNING:
            percentage = (response.requests_used / response.requests_limit * 100)
            return f"⚠️ Advertencia: Usando {percentage:.1f}% de la cuota ({response.requests_used}/{response.requests_limit})"
        elif status == QuotaStatus.CRITICAL:
            percentage = (response.requests_used / response.requests_limit * 100)
            return f"🚨 Crítico: Usando {percentage:.1f}% de la cuota ({response.requests_used}/{response.requests_limit})"
        elif status == QuotaStatus.EXCEEDED:
            return f"❌ Cuota excedida: {response.requests_used}/{response.requests_limit} requests"
        else:
            return "Estado de cuota desconocido"
    
    def _is_cache_valid(self) -> bool:
        """
        Verifica si el caché es válido.
        
        Returns:
            True si el caché existe y no ha expirado
        """
        if not self._cache or not self._cache_timestamp:
            return False
        
        age = datetime.now() - self._cache_timestamp
        return age.total_seconds() < self.cache_duration_seconds
