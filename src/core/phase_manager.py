"""
Gestor de Fases del Proyecto (Phase Manager).

Este módulo proporciona funcionalidad para gestionar las fases del proyecto Botrading,
incluyendo la validación de criterios de salida y transiciones entre fases.

Componentes principales:
- PhaseCriteria: Representa un criterio de salida de una fase
- Phase: Representa una fase del proyecto con sus criterios
- PhaseManager: Gestor principal de fases y transiciones

Autor: GitHub Copilot
Fecha: 15 de noviembre de 2025
Ticket: #66 (T50) - Avance por fases con criterios de salida
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class PhaseCriteria:
    """
    Representa un criterio de salida para una fase del proyecto.
    
    Attributes:
        id (str): Identificador único del criterio (ej: P0_001)
        description (str): Descripción del criterio
        requirement_type (str): Tipo de requisito ('critical' u 'optional')
        validation_method (str): Método de validación (manual, automated, etc.)
        is_completed (bool): Estado de completitud del criterio
        completed_date (Optional[str]): Fecha de completitud en formato ISO
    """
    id: str
    description: str
    requirement_type: str = "critical"
    validation_method: str = "manual"
    is_completed: bool = False
    completed_date: Optional[str] = None
    
    def mark_completed(self) -> None:
        """Marca el criterio como completado."""
        self.is_completed = True
        self.completed_date = datetime.now().isoformat()
    
    def mark_uncompleted(self) -> None:
        """Marca el criterio como no completado."""
        self.is_completed = False
        self.completed_date = None
    
    def is_optional(self) -> bool:
        """Verifica si el criterio es opcional."""
        return self.requirement_type.lower() == "optional"
    
    def to_dict(self) -> Dict:
        """Convierte el criterio a diccionario."""
        return asdict(self)


@dataclass
class Phase:
    """
    Representa una fase del proyecto.
    
    Attributes:
        phase_number (int): Número de la fase (0-4)
        name (str): Nombre de la fase
        description (str): Descripción de la fase
        priority (str): Prioridad de la fase (P0, P1)
        estimated_duration_sprints (int): Duración estimada en sprints
        criteria (List[PhaseCriteria]): Lista de criterios de salida
        is_completed (bool): Estado de completitud de la fase
        completed_date (Optional[str]): Fecha de completitud
    """
    phase_number: int
    name: str
    description: str
    priority: str = "P0"
    estimated_duration_sprints: int = 1
    criteria: List[PhaseCriteria] = field(default_factory=list)
    is_completed: bool = False
    completed_date: Optional[str] = None
    
    def add_criteria(self, criteria: PhaseCriteria) -> None:
        """
        Agrega un criterio a la fase.
        
        Args:
            criteria: Criterio a agregar
        """
        self.criteria.append(criteria)
    
    def check_completion(self) -> bool:
        """
        Verifica si la fase está completa.
        
        Una fase está completa cuando todos los criterios críticos están completados.
        Los criterios opcionales no son obligatorios.
        
        Returns:
            bool: True si la fase está completa, False en caso contrario
        """
        critical_criteria = [c for c in self.criteria if not c.is_optional()]
        
        if not critical_criteria:
            return False
        
        all_critical_completed = all(c.is_completed for c in critical_criteria)
        
        if all_critical_completed:
            self.is_completed = True
            if not self.completed_date:
                self.completed_date = datetime.now().isoformat()
        else:
            self.is_completed = False
            self.completed_date = None
        
        return self.is_completed
    
    def get_pending_criteria(self) -> List[PhaseCriteria]:
        """
        Obtiene la lista de criterios pendientes.
        
        Returns:
            List[PhaseCriteria]: Lista de criterios no completados
        """
        return [c for c in self.criteria if not c.is_completed]
    
    def get_completion_percentage(self) -> float:
        """
        Calcula el porcentaje de completitud de la fase.
        
        Returns:
            float: Porcentaje de criterios completados (0-100)
        """
        if not self.criteria:
            return 0.0
        
        completed = len([c for c in self.criteria if c.is_completed])
        total = len(self.criteria)
        
        return (completed / total) * 100.0
    
    def to_dict(self) -> Dict:
        """Convierte la fase a diccionario."""
        return {
            "phase_number": self.phase_number,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "estimated_duration_sprints": self.estimated_duration_sprints,
            "is_completed": self.is_completed,
            "completed_date": self.completed_date,
            "criteria": [c.to_dict() for c in self.criteria]
        }


class PhaseManager:
    """
    Gestor de fases del proyecto Botrading.
    
    Maneja la carga de configuración, validación de criterios de salida,
    y transiciones entre fases del proyecto.
    
    Attributes:
        config_path (str): Ruta al archivo de configuración de fases
        phases (List[Phase]): Lista de fases del proyecto
        current_phase (int): Número de la fase actual
        validation_rules (Dict): Reglas de validación del proyecto
    """
    
    def __init__(self, config_path: str = "config/phases.json"):
        """
        Inicializa el gestor de fases.
        
        Args:
            config_path: Ruta al archivo JSON de configuración de fases
        
        Raises:
            FileNotFoundError: Si el archivo de configuración no existe
            ValueError: Si la configuración es inválida
        """
        self.config_path = config_path
        self.phases: List[Phase] = []
        self.current_phase: int = 0
        self.validation_rules: Dict = {}
        
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """
        Carga la configuración de fases desde el archivo JSON.
        
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el JSON es inválido
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear JSON: {e}")
        
        # Cargar reglas de validación
        self.validation_rules = config.get("validation_rules", {})
        
        # Cargar fases
        phases_config = config.get("phases", [])
        
        for phase_config in phases_config:
            phase = Phase(
                phase_number=phase_config["phase_number"],
                name=phase_config["name"],
                description=phase_config["description"],
                priority=phase_config.get("priority", "P0"),
                estimated_duration_sprints=phase_config.get("estimated_duration_sprints", 1)
            )
            
            # Cargar criterios de la fase
            for criteria_config in phase_config.get("criteria", []):
                criteria = PhaseCriteria(
                    id=criteria_config["id"],
                    description=criteria_config["description"],
                    requirement_type=criteria_config.get("requirement_type", "critical"),
                    validation_method=criteria_config.get("validation_method", "manual")
                )
                phase.add_criteria(criteria)
            
            self.phases.append(phase)
        
        # Ordenar fases por número
        self.phases.sort(key=lambda p: p.phase_number)
    
    def get_phase(self, phase_number: int) -> Optional[Phase]:
        """
        Obtiene una fase específica por su número.
        
        Args:
            phase_number: Número de la fase a obtener
        
        Returns:
            Phase o None si no existe
        """
        for phase in self.phases:
            if phase.phase_number == phase_number:
                return phase
        return None
    
    def get_current_phase(self) -> Phase:
        """
        Obtiene la fase actual del proyecto.
        
        Returns:
            Phase: Fase actual
        """
        return self.get_phase(self.current_phase)
    
    def can_advance_to_next_phase(self) -> Tuple[bool, str]:
        """
        Verifica si se puede avanzar a la siguiente fase.
        
        Returns:
            Tuple[bool, str]: (puede_avanzar, mensaje)
        """
        current = self.get_current_phase()
        
        if current is None:
            return False, "Fase actual no encontrada"
        
        # Verificar si es la última fase
        if current.phase_number >= len(self.phases) - 1:
            return False, "Ya se encuentra en la última fase del proyecto"
        
        # Verificar completitud de la fase actual
        if not current.check_completion():
            pending = current.get_pending_criteria()
            pending_critical = [c for c in pending if not c.is_optional()]
            
            if pending_critical:
                criteria_list = "\n".join([f"  - {c.id}: {c.description}" for c in pending_critical])
                return False, f"Criterios críticos pendientes en Fase {current.phase_number}:\n{criteria_list}"
            
        return True, f"Todos los criterios de Fase {current.phase_number} completados exitosamente"
    
    def advance_to_next_phase(self) -> Tuple[bool, str]:
        """
        Avanza a la siguiente fase del proyecto.
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        can_advance, message = self.can_advance_to_next_phase()
        
        if not can_advance:
            return False, message
        
        self.current_phase += 1
        next_phase = self.get_current_phase()
        
        return True, f"Avanzado exitosamente a Fase {next_phase.phase_number}: {next_phase.name}"
    
    def get_phase_progress(self, phase_number: int) -> Dict:
        """
        Obtiene el progreso de una fase específica.
        
        Args:
            phase_number: Número de la fase
        
        Returns:
            Dict con información de progreso
        """
        phase = self.get_phase(phase_number)
        
        if phase is None:
            return {"error": "Fase no encontrada"}
        
        completed = len([c for c in phase.criteria if c.is_completed])
        total = len(phase.criteria)
        percentage = phase.get_completion_percentage()
        
        return {
            "phase_number": phase.phase_number,
            "phase_name": phase.name,
            "completed": completed,
            "total": total,
            "percentage": percentage,
            "is_completed": phase.is_completed
        }
    
    def get_overall_progress(self) -> Dict:
        """
        Obtiene el progreso general del proyecto.
        
        Returns:
            Dict con estadísticas generales
        """
        total_criteria = sum(len(p.criteria) for p in self.phases)
        completed_criteria = sum(
            len([c for c in p.criteria if c.is_completed]) 
            for p in self.phases
        )
        
        completed_phases = len([p for p in self.phases if p.is_completed])
        
        return {
            "total_phases": len(self.phases),
            "completed_phases": completed_phases,
            "current_phase": self.current_phase,
            "current_phase_name": self.get_current_phase().name,
            "total_criteria": total_criteria,
            "completed_criteria": completed_criteria,
            "overall_percentage": (completed_criteria / total_criteria * 100) if total_criteria > 0 else 0
        }
    
    def save_state(self, state_file: str = "data/phase_state.json") -> None:
        """
        Guarda el estado actual del proyecto en un archivo JSON.
        
        Args:
            state_file: Ruta donde guardar el estado
        """
        state = {
            "current_phase": self.current_phase,
            "last_updated": datetime.now().isoformat(),
            "phases": [phase.to_dict() for phase in self.phases]
        }
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def load_state(self, state_file: str = "data/phase_state.json") -> None:
        """
        Carga el estado del proyecto desde un archivo JSON.
        
        Args:
            state_file: Ruta del archivo de estado
        
        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        if not os.path.exists(state_file):
            raise FileNotFoundError(f"Archivo de estado no encontrado: {state_file}")
        
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        # Restaurar fase actual
        self.current_phase = state.get("current_phase", 0)
        
        # Restaurar estado de fases y criterios
        for phase_state in state.get("phases", []):
            phase_num = phase_state["phase_number"]
            phase = self.get_phase(phase_num)
            
            if phase:
                phase.is_completed = phase_state.get("is_completed", False)
                phase.completed_date = phase_state.get("completed_date")
                
                # Restaurar estado de criterios
                for criteria_state in phase_state.get("criteria", []):
                    criteria_id = criteria_state["id"]
                    
                    for criteria in phase.criteria:
                        if criteria.id == criteria_id:
                            criteria.is_completed = criteria_state.get("is_completed", False)
                            criteria.completed_date = criteria_state.get("completed_date")
                            break
    
    def mark_criteria_completed(self, phase_number: int, criteria_id: str) -> Tuple[bool, str]:
        """
        Marca un criterio específico como completado.
        
        Args:
            phase_number: Número de la fase
            criteria_id: ID del criterio
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        phase = self.get_phase(phase_number)
        
        if phase is None:
            return False, f"Fase {phase_number} no encontrada"
        
        for criteria in phase.criteria:
            if criteria.id == criteria_id:
                criteria.mark_completed()
                return True, f"Criterio {criteria_id} marcado como completado"
        
        return False, f"Criterio {criteria_id} no encontrado en Fase {phase_number}"
    
    def get_phase_report(self, phase_number: int) -> str:
        """
        Genera un reporte detallado de una fase.
        
        Args:
            phase_number: Número de la fase
        
        Returns:
            str: Reporte formateado
        """
        phase = self.get_phase(phase_number)
        
        if phase is None:
            return f"Fase {phase_number} no encontrada"
        
        report = f"\n{'='*70}\n"
        report += f"FASE {phase.phase_number}: {phase.name}\n"
        report += f"{'='*70}\n"
        report += f"Descripción: {phase.description}\n"
        report += f"Prioridad: {phase.priority}\n"
        report += f"Duración estimada: {phase.estimated_duration_sprints} sprints\n"
        report += f"Estado: {'✅ COMPLETADA' if phase.is_completed else '⏳ EN PROGRESO'}\n"
        
        if phase.completed_date:
            report += f"Completada: {phase.completed_date}\n"
        
        report += f"\nProgreso: {phase.get_completion_percentage():.1f}%\n"
        report += f"Criterios: {len([c for c in phase.criteria if c.is_completed])}/{len(phase.criteria)}\n"
        
        report += f"\n{'─'*70}\n"
        report += "CRITERIOS DE SALIDA:\n"
        report += f"{'─'*70}\n"
        
        for criteria in phase.criteria:
            status = "✅" if criteria.is_completed else "❌"
            optional = " [OPCIONAL]" if criteria.is_optional() else ""
            report += f"{status} {criteria.id}: {criteria.description}{optional}\n"
            report += f"   Validación: {criteria.validation_method}\n"
        
        if phase.get_pending_criteria():
            report += f"\n{'─'*70}\n"
            report += "CRITERIOS PENDIENTES:\n"
            report += f"{'─'*70}\n"
            for criteria in phase.get_pending_criteria():
                if not criteria.is_optional():
                    report += f"⚠️  {criteria.id}: {criteria.description}\n"
        
        report += f"{'='*70}\n"
        
        return report
