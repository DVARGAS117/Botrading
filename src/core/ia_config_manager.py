"""
IAConfigManager - Gestión de configuraciones alternantes de IA por bot

Este módulo permite administrar diferentes perfiles de IA (modelos, providers, parámetros)
y asignarlos dinámicamente a bots específicos para comparar impacto en costo y calidad.

Características:
- Múltiples perfiles de IA (Gemini, GPT-4, Claude, etc.)
- Asignación de perfiles por bot
- Alternancia dinámica de configuraciones
- Validación de perfiles
- Integración con QuotaValidator (T48)
- Seguimiento de costos por perfil
- Historial de cambios

Tickets relacionados: T49, T48 (QuotaValidator), T44 (ConfigLoader)

Autor: BOTRADING
Fecha: 6 de Noviembre de 2025
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json


class IAConfigError(Exception):
    """Excepción personalizada para errores de configuración de IA"""
    pass


class IAProvider(Enum):
    """
    Enum de providers de IA soportados
    
    Values:
        GEMINI: Google Gemini
        OPENAI: OpenAI (GPT-3.5, GPT-4)
        ANTHROPIC: Anthropic (Claude)
    """
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    
    @classmethod
    def from_string(cls, value: str) -> 'IAProvider':
        """
        Convierte string a IAProvider (case-insensitive)
        
        Args:
            value: Nombre del provider
            
        Returns:
            IAProvider enum correspondiente
            
        Raises:
            ValueError: Si el provider no es soportado
        """
        value_lower = value.lower()
        for provider in cls:
            if provider.value == value_lower:
                return provider
        raise ValueError(f"Provider '{value}' no soportado. Soportados: {[p.value for p in cls]}")


@dataclass
class IAProfile:
    """
    Perfil de configuración de IA
    
    Atributos:
        name: Nombre identificador del perfil
        provider: Provider de IA (gemini, openai, anthropic)
        model: Modelo específico (gemini-2.5-pro, gpt-4, claude-3, etc.)
        temperature: Temperatura del modelo (0-2, default 0.7)
        max_tokens: Máximo de tokens por respuesta (default 1000)
        top_p: Top-p sampling (default 0.9)
        frequency_penalty: Penalización por frecuencia (default 0.0)
        presence_penalty: Penalización por presencia (default 0.0)
        cost_per_1k_tokens: Costo por 1000 tokens (default 0.005)
        quota_limits: Límites de cuota específicos del perfil
        fallback_profile: Perfil alternativo si este falla
    """
    name: str
    provider: IAProvider
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    cost_per_1k_tokens: float = 0.005
    quota_limits: Optional[Dict[str, int]] = None
    fallback_profile: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el perfil a diccionario"""
        data = asdict(self)
        data['provider'] = self.provider.value  # Enum a string
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IAProfile':
        """
        Crea un IAProfile desde diccionario
        
        Args:
            data: Diccionario con datos del perfil
            
        Returns:
            IAProfile instanciado
        """
        # Convertir provider string a enum
        if 'provider' in data and isinstance(data['provider'], str):
            data['provider'] = IAProvider.from_string(data['provider'])
        
        return cls(**data)


class IAConfigManager:
    """
    Gestor de configuraciones de IA alternantes por bot
    
    Permite administrar múltiples perfiles de IA y asignarlos dinámicamente
    a bots específicos para comparar rendimiento y costos.
    
    Ejemplo:
        ```python
        # Inicializar con configuración
        config = {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini-pro": {
                        "provider": "gemini",
                        "model": "gemini-2.5-pro",
                        "temperature": 0.7
                    },
                    "gpt-4": {
                        "provider": "openai",
                        "model": "gpt-4",
                        "temperature": 0.5
                    }
                },
                "bot_assignments": {
                    "bot_1": "gemini-pro",
                    "bot_2": "gpt-4"
                }
            }
        }
        
        manager = IAConfigManager(config=config)
        
        # Obtener perfil para bot específico
        profile = manager.get_profile_for_bot("bot_1")
        
        # Cambiar perfil
        manager.switch_profile("bot_1", "gpt-4")
        ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el gestor de configuraciones de IA
        
        Args:
            config: Diccionario de configuración con perfiles de IA
            
        Raises:
            IAConfigError: Si la configuración es inválida
        """
        self.logger = logging.getLogger(__name__)
        self.profiles: Dict[str, IAProfile] = {}
        self.bot_assignments: Dict[str, str] = {}
        self.profile_history: Dict[str, List[Dict[str, Any]]] = {}
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        
        # Cargar configuración
        if config is None:
            config = self._get_default_config()
        
        self._load_config(config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Retorna configuración por defecto si no se proporciona
        
        Returns:
            Dict con configuración por defecto
        """
        return {
            "ia_profiles": {
                "default_profile": "gemini-pro",
                "profiles": {
                    "gemini_pro": {
                        "provider": "gemini",
                        "model": "gemini-2.5-pro",
                        "temperature": 0.7,
                        "max_tokens": 1000
                        "cost_per_1k_tokens": 0.005
                    }
                },
                "bot_assignments": {}
            }
        }
    
    def _load_config(self, config: Dict[str, Any]) -> None:
        """
        Carga y valida la configuración de perfiles
        
        Args:
            config: Diccionario con configuración
            
        Raises:
            IAConfigError: Si la configuración es inválida
        """
        ia_config = config.get("ia_profiles", {})
        
        # Validar que existan perfiles
        profiles_data = ia_config.get("profiles", {})
        if not profiles_data:
            raise IAConfigError("No hay perfiles de IA configurados")
        
        # Cargar perfiles
        for profile_name, profile_data in profiles_data.items():
            profile_data['name'] = profile_name
            self.profiles[profile_name] = IAProfile.from_dict(profile_data)
        
        # Configurar perfil por defecto
        self.default_profile = ia_config.get("default_profile", list(self.profiles.keys())[0])
        
        # Validar que el perfil por defecto exista
        if self.default_profile not in self.profiles:
            raise IAConfigError(
                f"Perfil por defecto '{self.default_profile}' no existe en perfiles configurados"
            )
        
        # Cargar asignaciones de bots
        self.bot_assignments = ia_config.get("bot_assignments", {})
        
        self.logger.info(
            f"Configuración de IA cargada: {len(self.profiles)} perfiles, "
            f"default='{self.default_profile}'"
        )
    
    def load_profile(self, profile_name: str) -> IAProfile:
        """
        Carga un perfil específico por nombre
        
        Args:
            profile_name: Nombre del perfil a cargar
            
        Returns:
            IAProfile correspondiente
            
        Raises:
            IAConfigError: Si el perfil no existe
        """
        if profile_name not in self.profiles:
            raise IAConfigError(
                f"Perfil '{profile_name}' no encontrado. "
                f"Perfiles disponibles: {list(self.profiles.keys())}"
            )
        
        return self.profiles[profile_name]
    
    def get_default_profile(self) -> IAProfile:
        """
        Retorna el perfil por defecto
        
        Returns:
            IAProfile por defecto
        """
        return self.profiles[self.default_profile]
    
    def get_profile_for_bot(
        self, 
        bot_name: str,
        validate_quota: bool = False,
        auto_fallback: bool = False
    ) -> IAProfile:
        """
        Obtiene el perfil asignado a un bot específico
        
        Args:
            bot_name: Nombre del bot
            validate_quota: Si True, valida cuota antes de retornar
            auto_fallback: Si True y cuota excedida, usa perfil fallback
            
        Returns:
            IAProfile asignado al bot o default si no tiene asignación
        """
        # Obtener perfil asignado o default
        profile_name = self.bot_assignments.get(bot_name, self.default_profile)
        profile = self.load_profile(profile_name)
        
        # Validar cuota si se solicita
        if validate_quota:
            try:
                from src.core.quota_validator import QuotaValidator
                
                validator = QuotaValidator(config={
                    "quota_validation": {
                        "enabled": True,
                        "provider": profile.provider.value
                    }
                })
                
                result = validator.validate_quota()
                
                if not result.is_valid and auto_fallback:
                    # Usar perfil fallback si está configurado
                    if profile.fallback_profile:
                        self.logger.warning(
                            f"Cuota excedida para perfil '{profile_name}', "
                            f"cambiando a fallback '{profile.fallback_profile}'"
                        )
                        return self.load_profile(profile.fallback_profile)
            except ImportError:
                self.logger.warning("QuotaValidator no disponible, saltando validación")
        
        return profile
    
    def assign_profile_to_bot(self, bot_name: str, profile_name: str) -> None:
        """
        Asigna un perfil específico a un bot
        
        Args:
            bot_name: Nombre del bot
            profile_name: Nombre del perfil a asignar
            
        Raises:
            IAConfigError: Si el perfil no existe
        """
        if profile_name not in self.profiles:
            raise IAConfigError(
                f"Perfil '{profile_name}' no existe. "
                f"Perfiles disponibles: {list(self.profiles.keys())}"
            )
        
        self.bot_assignments[bot_name] = profile_name
        self.logger.info(f"Perfil '{profile_name}' asignado a bot '{bot_name}'")
    
    def switch_profile(self, bot_name: str, new_profile_name: str) -> None:
        """
        Cambia el perfil de un bot (con registro en historial)
        
        Args:
            bot_name: Nombre del bot
            new_profile_name: Nombre del nuevo perfil
            
        Raises:
            IAConfigError: Si el perfil no existe
        """
        # Validar que el perfil exista
        if new_profile_name not in self.profiles:
            raise IAConfigError(f"Perfil '{new_profile_name}' no existe")
        
        # Obtener perfil anterior
        old_profile_name = self.bot_assignments.get(bot_name, self.default_profile)
        
        # Asignar nuevo perfil
        self.bot_assignments[bot_name] = new_profile_name
        
        # Registrar en historial
        if bot_name not in self.profile_history:
            self.profile_history[bot_name] = []
        
        self.profile_history[bot_name].append({
            "timestamp": datetime.now().isoformat(),
            "old_profile": old_profile_name,
            "new_profile": new_profile_name
        })
        
        self.logger.info(
            f"Bot '{bot_name}' cambió de perfil: '{old_profile_name}' → '{new_profile_name}'"
        )
    
    def get_profile_history(self, bot_name: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de cambios de perfil para un bot
        
        Args:
            bot_name: Nombre del bot
            
        Returns:
            Lista de cambios de perfil con timestamps
        """
        return self.profile_history.get(bot_name, [])
    
    def validate_profile(self, profile_data: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """
        Valida que un perfil tenga todos los campos requeridos
        
        Args:
            profile_data: Diccionario con datos del perfil
            
        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        errors = []
        
        # Campos requeridos
        required_fields = ["provider", "model"]
        for field in required_fields:
            if field not in profile_data:
                errors.append(f"Campo requerido '{field}' faltante")
        
        # Validar provider
        if "provider" in profile_data:
            try:
                IAProvider.from_string(profile_data["provider"])
            except ValueError as e:
                errors.append(str(e))
        
        # Validar temperature (0-2)
        if "temperature" in profile_data:
            temp = profile_data["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                errors.append(f"Temperature debe estar entre 0 y 2, recibido: {temp}")
        
        # Validar max_tokens (positivo)
        if "max_tokens" in profile_data:
            max_tokens = profile_data["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                errors.append(f"max_tokens debe ser entero positivo, recibido: {max_tokens}")
        
        is_valid = len(errors) == 0
        return is_valid, errors if errors else None
    
    def track_usage(self, bot_name: str, profile_name: str, tokens_used: int) -> None:
        """
        Registra el uso de un perfil para seguimiento de costos
        
        Args:
            bot_name: Nombre del bot
            profile_name: Nombre del perfil usado
            tokens_used: Cantidad de tokens utilizados
        """
        if bot_name not in self.usage_stats:
            self.usage_stats[bot_name] = {
                "total_tokens": 0,
                "total_cost": 0.0,
                "by_profile": {}
            }
        
        # Obtener costo del perfil
        if profile_name not in self.profiles:
            self.logger.warning(f"Perfil '{profile_name}' no encontrado para tracking")
            return
        
        profile = self.load_profile(profile_name)
        cost = (tokens_used / 1000) * profile.cost_per_1k_tokens
        
        # Actualizar totales
        self.usage_stats[bot_name]["total_tokens"] += tokens_used
        self.usage_stats[bot_name]["total_cost"] += cost
        
        # Actualizar por perfil
        if profile_name not in self.usage_stats[bot_name]["by_profile"]:
            self.usage_stats[bot_name]["by_profile"][profile_name] = {
                "tokens": 0,
                "cost": 0.0
            }
        
        self.usage_stats[bot_name]["by_profile"][profile_name]["tokens"] += tokens_used
        self.usage_stats[bot_name]["by_profile"][profile_name]["cost"] += cost
    
    def get_usage_stats(self, bot_name: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso para un bot
        
        Args:
            bot_name: Nombre del bot
            
        Returns:
            Dict con estadísticas de uso y costos
        """
        return self.usage_stats.get(bot_name, {
            "total_tokens": 0,
            "total_cost": 0.0,
            "by_profile": {}
        })
    
    def get_cost_comparison(self, bot_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Compara costos entre múltiples bots
        
        Args:
            bot_names: Lista de nombres de bots a comparar
            
        Returns:
            Dict con estadísticas por bot
        """
        comparison = {}
        for bot_name in bot_names:
            comparison[bot_name] = self.get_usage_stats(bot_name)
        return comparison
    
    def reload_config(
        self, 
        new_config: Dict[str, Any],
        preserve_assignments: bool = False
    ) -> None:
        """
        Recarga la configuración de perfiles
        
        Args:
            new_config: Nueva configuración
            preserve_assignments: Si True, mantiene asignaciones actuales de bots
        """
        # Guardar asignaciones actuales si se solicita
        old_assignments = self.bot_assignments.copy() if preserve_assignments else {}
        
        # Recargar configuración
        self._load_config(new_config)
        
        # Restaurar asignaciones si se solicitó
        if preserve_assignments:
            for bot_name, profile_name in old_assignments.items():
                # Solo restaurar si el perfil aún existe
                if profile_name in self.profiles:
                    self.bot_assignments[bot_name] = profile_name
        
        self.logger.info("Configuración de IA recargada exitosamente")
