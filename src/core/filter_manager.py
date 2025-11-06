"""
FilterManager - T36: Sistema de filtros configurables
Permite habilitar/deshabilitar filtros de volatilidad, spread y otros sin modificar código
"""

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime


class FilterValidationError(Exception):
    """Excepción para errores de validación de filtros"""
    pass


class FilterType(Enum):
    """Tipos de filtros soportados"""
    VOLATILITY = "volatility"
    SPREAD = "spread"
    ECONOMIC_EVENTS = "economic_events"
    DRAWDOWN = "drawdown"
    TIME_FILTER = "time_filter"
    CORRELATION = "correlation"
    CUSTOM = "custom"
    
    @classmethod
    def from_string(cls, value: str) -> 'FilterType':
        """Convertir string a FilterType (case-insensitive)"""
        value_upper = value.upper()
        for filter_type in cls:
            if filter_type.name == value_upper:
                return filter_type
        raise ValueError(f"Invalid filter type: {value}")


@dataclass
class FilterResult:
    """Resultado de aplicación de un filtro"""
    passed: bool
    filter_name: str
    reason: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            "passed": self.passed,
            "filter_name": self.filter_name,
            "reason": self.reason,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat()
        }


class BaseFilter:
    """Clase base para todos los filtros"""
    
    def __init__(self, config: Dict[str, Any], name: str):
        self.config = config
        self.name = name
        self.enabled = config.get("enabled", False)
        self._validate_config()
    
    def _validate_config(self):
        """Validar configuración del filtro"""
        if not isinstance(self.config, dict):
            raise FilterValidationError(f"Invalid filter configuration for {self.name}")
    
    def is_enabled(self) -> bool:
        """Verificar si el filtro está habilitado"""
        return self.enabled
    
    def apply(self, market_data: Dict[str, Any]) -> FilterResult:
        """Aplicar el filtro (debe ser implementado por subclases)"""
        raise NotImplementedError("Subclasses must implement apply()")


class VolatilityFilter(BaseFilter):
    """Filtro de volatilidad basado en ATR"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "volatility")
        self.atr_minimum = config.get("atr_minimum", 0.001)
    
    def apply(self, market_data: Dict[str, Any]) -> FilterResult:
        """
        Aplicar filtro de volatilidad
        
        Args:
            market_data: Diccionario con "atr" key
            
        Returns:
            FilterResult indicando si pasó el filtro
        """
        if "atr" not in market_data:
            return FilterResult(
                passed=False,
                filter_name=self.name,
                reason="ATR value not found in market data",
                value=None,
                threshold=self.atr_minimum
            )
        
        atr_value = market_data["atr"]
        
        # Validar tipo de dato (None se trata como missing)
        if atr_value is None:
            return FilterResult(
                passed=False,
                filter_name=self.name,
                reason="ATR value is None",
                value=None,
                threshold=self.atr_minimum
            )
        
        if not isinstance(atr_value, (int, float)):
            raise FilterValidationError(f"Invalid data type for ATR: {type(atr_value)}")
        
        passed = atr_value >= self.atr_minimum
        
        return FilterResult(
            passed=passed,
            filter_name=self.name,
            reason="ATR above minimum" if passed else "ATR below minimum",
            value=float(atr_value),
            threshold=self.atr_minimum
        )


class SpreadFilter(BaseFilter):
    """Filtro de spread máximo"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "spread")
        self.spread_maximum_pips = config.get("spread_maximum_pips", 3)
    
    def apply(self, market_data: Dict[str, Any]) -> FilterResult:
        """
        Aplicar filtro de spread
        
        Args:
            market_data: Diccionario con "spread_pips" key
            
        Returns:
            FilterResult indicando si pasó el filtro
        """
        if "spread_pips" not in market_data:
            return FilterResult(
                passed=False,
                filter_name=self.name,
                reason="Spread value not found in market data",
                value=None,
                threshold=self.spread_maximum_pips
            )
        
        spread_value = market_data["spread_pips"]
        
        # Validar tipo de dato (None se trata como missing)
        if spread_value is None:
            return FilterResult(
                passed=False,
                filter_name=self.name,
                reason="Spread value is None",
                value=None,
                threshold=self.spread_maximum_pips
            )
        
        if not isinstance(spread_value, (int, float)):
            raise FilterValidationError(f"Invalid data type for spread: {type(spread_value)}")
        
        passed = spread_value <= self.spread_maximum_pips
        
        return FilterResult(
            passed=passed,
            filter_name=self.name,
            reason="Spread within limit" if passed else "Spread exceeds maximum",
            value=float(spread_value),
            threshold=self.spread_maximum_pips
        )


class FilterManager:
    """
    Gestor de filtros configurables
    
    Permite habilitar/deshabilitar filtros vía configuración sin modificar código.
    Soporta filtros de volatilidad, spread y filtros custom extensibles.
    """
    
    DEFAULT_CONFIG = {
        "volatility": {"enabled": False, "atr_minimum": 0.001},
        "spread": {"enabled": False, "spread_maximum_pips": 3}
    }
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        logger: Optional[Any] = None,
        allow_custom: bool = False
    ):
        """
        Inicializar FilterManager
        
        Args:
            config: Diccionario de configuración
            config_path: Ruta al archivo de configuración JSON
            logger: Logger opcional (BotLogger de T39)
            allow_custom: Permitir filtros custom
        """
        self.logger = logger
        self.allow_custom = allow_custom
        self.config_path = config_path
        self.filters: Dict[str, BaseFilter] = {}
        self.statistics = {
            "total_applications": 0,
            "total_passed": 0,
            "total_failed": 0,
            "filter_details": {}
        }
        
        # Cargar configuración
        if config_path:
            self.config = self._load_config_from_file(config_path)
        elif config:
            self.config = config
        else:
            self.config = self.DEFAULT_CONFIG.copy()
        
        # Validar y construir filtros
        self._validate_and_build_filters()
    
    def _load_config_from_file(self, config_path: str) -> Dict[str, Any]:
        """Cargar configuración desde archivo JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Filtrar comentarios (keys que empiezan con _)
            return {k: v for k, v in config.items() if not k.startswith('_')}
        except FileNotFoundError:
            raise FilterValidationError(f"Config file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise FilterValidationError(f"Invalid JSON in config file: {e}")
    
    def _validate_and_build_filters(self):
        """Validar configuración y construir instancias de filtros"""
        for filter_name, filter_config in self.config.items():
            # Validar estructura
            if not isinstance(filter_config, dict):
                raise FilterValidationError(f"Invalid filter configuration for {filter_name}")
            
            # Construir filtro según tipo
            if filter_name == "volatility":
                self.filters[filter_name] = VolatilityFilter(filter_config)
            elif filter_name == "spread":
                self.filters[filter_name] = SpreadFilter(filter_config)
            elif filter_name == "custom" and self.allow_custom:
                # Para custom, solo validar enabled por ahora
                self.filters[filter_name] = BaseFilter(filter_config, "custom")
            # Otros filtros (economic_events, drawdown, etc.) se pueden agregar aquí
            
            # Inicializar estadísticas del filtro
            if filter_name not in self.statistics["filter_details"]:
                self.statistics["filter_details"][filter_name] = {
                    "applications": 0,
                    "passed": 0,
                    "failed": 0
                }
    
    def is_filter_enabled(self, filter_name: str) -> bool:
        """
        Verificar si un filtro está habilitado
        
        Args:
            filter_name: Nombre del filtro
            
        Returns:
            True si el filtro existe y está habilitado
        """
        if filter_name not in self.filters:
            return False
        return self.filters[filter_name].is_enabled()
    
    def apply_filters(self, market_data: Dict[str, Any]) -> List[FilterResult]:
        """
        Aplicar todos los filtros habilitados
        
        Args:
            market_data: Datos de mercado con ATR, spread, etc.
            
        Returns:
            Lista de FilterResult para cada filtro aplicado
        """
        results = []
        
        for filter_name, filter_instance in self.filters.items():
            if not filter_instance.is_enabled():
                continue
            
            try:
                result = filter_instance.apply(market_data)
                results.append(result)
                
                # Actualizar estadísticas
                self.statistics["total_applications"] += 1
                self.statistics["filter_details"][filter_name]["applications"] += 1
                
                if result.passed:
                    self.statistics["total_passed"] += 1
                    self.statistics["filter_details"][filter_name]["passed"] += 1
                else:
                    self.statistics["total_failed"] += 1
                    self.statistics["filter_details"][filter_name]["failed"] += 1
                
                # Log si hay logger
                if self.logger:
                    level = "info" if result.passed else "warning"
                    message = f"Filter '{filter_name}': {'PASS' if result.passed else 'FAIL'} - {result.reason}"
                    
                    if level == "info":
                        self.logger.info(message, extra={
                            "filter": filter_name,
                            "passed": result.passed,
                            "value": result.value,
                            "threshold": result.threshold
                        })
                    else:
                        self.logger.warning(message, extra={
                            "filter": filter_name,
                            "passed": result.passed,
                            "value": result.value,
                            "threshold": result.threshold
                        })
            
            except FilterValidationError as e:
                # Re-lanzar errores de validación
                raise
            except Exception as e:
                # Capturar otros errores y crear resultado fallido
                result = FilterResult(
                    passed=False,
                    filter_name=filter_name,
                    reason=f"Filter error: {str(e)}",
                    value=None,
                    threshold=None
                )
                results.append(result)
                
                if self.logger:
                    self.logger.error(f"Error applying filter '{filter_name}': {e}", extra={
                        "filter": filter_name,
                        "error": str(e)
                    })
        
        return results
    
    def all_filters_pass(self, market_data: Dict[str, Any]) -> bool:
        """
        Verificar si todos los filtros pasan
        
        Args:
            market_data: Datos de mercado
            
        Returns:
            True si todos los filtros habilitados pasan
        """
        results = self.apply_filters(market_data)
        
        # Si no hay filtros habilitados, retornar True (sin restricciones)
        if not results:
            return True
        
        return all(r.passed for r in results)
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen de filtros configurados
        
        Returns:
            Diccionario con filtros habilitados/deshabilitados
        """
        enabled_filters = []
        disabled_filters = []
        
        for filter_name, filter_instance in self.filters.items():
            filter_info = {
                "name": filter_name,
                "config": filter_instance.config
            }
            
            if filter_instance.is_enabled():
                enabled_filters.append(filter_info)
            else:
                disabled_filters.append(filter_info)
        
        return {
            "enabled_filters": enabled_filters,
            "disabled_filters": disabled_filters,
            "total_filters": len(self.filters)
        }
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de aplicación de filtros
        
        Returns:
            Diccionario con estadísticas globales y por filtro
        """
        stats = self.statistics.copy()
        
        # Calcular tasa de paso
        if stats["total_applications"] > 0:
            stats["pass_rate"] = stats["total_passed"] / stats["total_applications"]
            stats["fail_rate"] = stats["total_failed"] / stats["total_applications"]
        else:
            stats["pass_rate"] = 0.0
            stats["fail_rate"] = 0.0
        
        # Calcular tasas por filtro
        for filter_name, filter_stats in stats["filter_details"].items():
            if filter_stats["applications"] > 0:
                filter_stats["pass_rate"] = filter_stats["passed"] / filter_stats["applications"]
                filter_stats["fail_rate"] = filter_stats["failed"] / filter_stats["applications"]
            else:
                filter_stats["pass_rate"] = 0.0
                filter_stats["fail_rate"] = 0.0
        
        return stats
    
    def reload_config(self):
        """
        Recargar configuración desde archivo
        
        Las estadísticas se preservan tras la recarga
        """
        if not self.config_path:
            raise FilterValidationError("Cannot reload: no config_path specified")
        
        # Recargar config
        self.config = self._load_config_from_file(self.config_path)
        
        # Reconstruir filtros
        self.filters = {}
        self._validate_and_build_filters()
        
        if self.logger:
            self.logger.info("Filter configuration reloaded", extra={
                "config_path": self.config_path,
                "total_filters": len(self.filters)
            })
    
    def clear_statistics(self):
        """Limpiar estadísticas acumuladas"""
        self.statistics = {
            "total_applications": 0,
            "total_passed": 0,
            "total_failed": 0,
            "filter_details": {}
        }
        
        # Reinicializar estadísticas por filtro
        for filter_name in self.filters.keys():
            self.statistics["filter_details"][filter_name] = {
                "applications": 0,
                "passed": 0,
                "failed": 0
            }
