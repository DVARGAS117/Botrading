"""
DemoModeValidator - T52: Operación en demo antes de real

Este módulo implementa la validación para asegurar que las estrategias de trading
se prueben en modo demo antes de operar con dinero real, minimizando riesgos financieros.

Permite:
- Configurar modo demo/real
- Requerir validación previa en demo
- Registrar operaciones demo
- Validar criterios de rendimiento
- Cambiar a modo real solo después de validación

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T52 - Operación en demo antes de real
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum


class DemoValidationError(Exception):
    """Excepción para errores de validación de modo demo"""
    pass


class ValidationStatus(Enum):
    """Estados posibles de validación"""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"


@dataclass
class ValidationResult:
    """
    Resultado de una validación de operación.
    
    Attributes:
        is_valid (bool): Indica si la operación es válida
        reason (str): Razón del resultado
        timestamp (datetime): Momento de la validación
        demo_mode (bool): Si está en modo demo
    """
    is_valid: bool
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)
    demo_mode: bool = False
    
    def __bool__(self) -> bool:
        """Permite usar en contextos booleanos"""
        return self.is_valid


class DemoModeValidator:
    """
    Validador para operaciones en modo demo antes de real.
    
    Garantiza que las estrategias se validen en entorno demo antes
    de permitir operaciones con dinero real.
    
    Attributes:
        demo_enabled (bool): Si el modo demo está habilitado
        require_validation (bool): Si requiere validación previa
        min_demo_operations (int): Mínimo de operaciones demo requeridas
        min_demo_days (int): Mínimo de días de operación demo
        validation_criteria (Dict): Criterios de validación
        is_validated (bool): Si ya fue validado
        demo_operations (List): Historial de operaciones demo
    """
    
    def __init__(self, config: Any):
        """
        Inicializa el validador con configuración.
        
        Args:
            config: Diccionario de configuración o path a archivo JSON
            
        Raises:
            DemoValidationError: Si la configuración es inválida
        """
        self.demo_operations: List[Dict[str, Any]] = []
        self.is_validated = False
        
        if isinstance(config, str):
            # Es un path a archivo
            self._load_config_from_file(config)
        elif isinstance(config, dict):
            # Es un diccionario
            self._load_config_from_dict(config)
        else:
            raise DemoValidationError("Config debe ser dict o path a archivo JSON")
    
    def _load_config_from_file(self, file_path: str) -> None:
        """Carga configuración desde archivo JSON"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise DemoValidationError(f"Archivo de configuración no encontrado: {file_path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._load_config_from_dict(config_data)
            
        except json.JSONDecodeError as e:
            raise DemoValidationError(f"JSON inválido en {file_path}: {str(e)}")
        except Exception as e:
            raise DemoValidationError(f"Error cargando config desde {file_path}: {str(e)}")
    
    def _load_config_from_dict(self, config: Dict[str, Any]) -> None:
        """Carga configuración desde diccionario"""
        demo_config = config.get("demo_mode", {})
        
        self.demo_enabled = demo_config.get("enabled", True)
        self.require_validation = demo_config.get("require_validation", True)
        self.min_demo_operations = demo_config.get("min_demo_operations", 10)
        self.min_demo_days = demo_config.get("min_demo_days", 3)
        self.validation_criteria = demo_config.get("validation_criteria", {
            "min_win_rate": 0.6,
            "max_drawdown_percent": 5.0,
            "min_total_operations": 50
        })
    
    def validate_operation(self) -> ValidationResult:
        """
        Valida si una operación puede ejecutarse.
        
        Returns:
            ValidationResult con el resultado de la validación
        """
        if self.demo_enabled:
            return ValidationResult(
                is_valid=True,
                reason="Operación permitida en modo demo",
                demo_mode=True
            )
        
        if not self.require_validation:
            return ValidationResult(
                is_valid=True,
                reason="Modo real sin requerir validación",
                demo_mode=False
            )
        
        if self.is_validated:
            return ValidationResult(
                is_valid=True,
                reason="Validado previamente en modo demo",
                demo_mode=False
            )
        
        return ValidationResult(
            is_valid=False,
            reason="Se requiere validación en modo demo antes de operar en real",
            demo_mode=False
        )
    
    def mark_as_validated(self) -> None:
        """
        Marca la configuración como validada.
        
        Permite operaciones en modo real después de validación manual.
        """
        self.is_validated = True
    
    def is_ready_for_real_trading(self) -> bool:
        """
        Verifica si está listo para operar en modo real.
        
        Returns:
            True si cumple con los criterios de validación
        """
        if not self.require_validation:
            return True
        
        stats = self.get_demo_statistics()
        
        # Verificar mínimo de operaciones
        if stats["total_operations"] < self.min_demo_operations:
            return False
        
        # Verificar win rate mínimo
        if stats["win_rate"] < self.validation_criteria["min_win_rate"]:
            return False
        
        # Verificar días de operación
        if len(self._get_unique_days()) < self.min_demo_days:
            return False
        
        return True
    
    def record_demo_operation(self, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra una operación demo.
        
        Args:
            success: Si la operación fue exitosa
            details: Detalles adicionales de la operación
        """
        operation = {
            "timestamp": datetime.now(),
            "success": success,
            "details": details or {}
        }
        self.demo_operations.append(operation)
    
    def get_demo_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de las operaciones demo.
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.demo_operations:
            return {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "win_rate": 0.0,
                "total_days": 0
            }
        
        total = len(self.demo_operations)
        successful = sum(1 for op in self.demo_operations if op["success"])
        failed = total - successful
        win_rate = successful / total if total > 0 else 0.0
        total_days = len(self._get_unique_days())
        
        return {
            "total_operations": total,
            "successful_operations": successful,
            "failed_operations": failed,
            "win_rate": win_rate,
            "total_days": total_days
        }
    
    def _get_unique_days(self) -> set:
        """Obtiene los días únicos de operación"""
        days = set()
        for op in self.demo_operations:
            days.add(op["timestamp"].date())
        return days
    
    def get_validation_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado completo de validación.
        
        Returns:
            Diccionario con estado de validación
        """
        stats = self.get_demo_statistics()
        
        return {
            "demo_mode": self.demo_enabled,
            "validation_required": self.require_validation,
            "is_validated": self.is_validated,
            "ready_for_real": self.is_ready_for_real_trading(),
            "demo_statistics": stats,
            "validation_criteria": self.validation_criteria
        }
    
    def switch_to_real_mode(self) -> None:
        """
        Cambia a modo real después de validación.
        
        Raises:
            DemoValidationError: Si no está validado
        """
        if self.require_validation and not self.is_validated:
            raise DemoValidationError(
                "No se puede cambiar a modo real sin validación previa en demo"
            )
        
        self.demo_enabled = False
    
    def save_validation_state(self, file_path: str) -> None:
        """
        Guarda el estado de validación en archivo.
        
        Args:
            file_path: Path donde guardar el estado
        """
        state = {
            "is_validated": self.is_validated,
            "demo_operations": [
                {
                    "timestamp": op["timestamp"].isoformat(),
                    "success": op["success"],
                    "details": op["details"]
                }
                for op in self.demo_operations
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, default=str)
    
    def load_validation_state(self, file_path: str) -> None:
        """
        Carga el estado de validación desde archivo.
        
        Args:
            file_path: Path desde donde cargar el estado
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.is_validated = state.get("is_validated", False)
            
            self.demo_operations = []
            for op in state.get("demo_operations", []):
                operation = {
                    "timestamp": datetime.fromisoformat(op["timestamp"]),
                    "success": op["success"],
                    "details": op["details"]
                }
                self.demo_operations.append(operation)
                
        except FileNotFoundError:
            # Si no existe el archivo, mantener estado por defecto
            pass
        except Exception as e:
            raise DemoValidationError(f"Error cargando estado: {str(e)}")