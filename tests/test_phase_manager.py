"""
Tests para el módulo PhaseManager.

Este módulo contiene las pruebas unitarias para el gestor de fases del proyecto,
validando la gestión de criterios de salida y transiciones entre fases.

Autor: GitHub Copilot
Fecha: 15 de noviembre de 2025
Ticket: #66 (T50)
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.core.phase_manager import PhaseManager, Phase, PhaseCriteria


class TestPhase:
    """Tests para la clase Phase."""

    def test_phase_creation(self):
        """Test: Crear una fase con sus atributos básicos."""
        phase = Phase(
            phase_number=0,
            name="Fundamentos",
            description="Configuración inicial del proyecto",
            priority="P0"
        )
        
        assert phase.phase_number == 0
        assert phase.name == "Fundamentos"
        assert phase.description == "Configuración inicial del proyecto"
        assert phase.priority == "P0"
        assert phase.criteria == []
        assert phase.is_completed == False

    def test_phase_add_criteria(self):
        """Test: Agregar criterios a una fase."""
        phase = Phase(0, "Fundamentos", "Descripción", "P0")
        criteria = PhaseCriteria("REQ001", "Repo + estructura base", "critical")
        
        phase.add_criteria(criteria)
        
        assert len(phase.criteria) == 1
        assert phase.criteria[0].id == "REQ001"

    def test_phase_check_completion_all_met(self):
        """Test: Verificar que la fase esté completa cuando todos los criterios se cumplen."""
        phase = Phase(0, "Fundamentos", "Descripción", "P0")
        criteria1 = PhaseCriteria("REQ001", "Criterio 1", "critical")
        criteria2 = PhaseCriteria("REQ002", "Criterio 2", "critical")
        
        criteria1.mark_completed()
        criteria2.mark_completed()
        
        phase.add_criteria(criteria1)
        phase.add_criteria(criteria2)
        
        assert phase.check_completion() == True
        assert phase.is_completed == True

    def test_phase_check_completion_not_all_met(self):
        """Test: Verificar que la fase no esté completa si faltan criterios."""
        phase = Phase(0, "Fundamentos", "Descripción", "P0")
        criteria1 = PhaseCriteria("REQ001", "Criterio 1", "critical")
        criteria2 = PhaseCriteria("REQ002", "Criterio 2", "critical")
        
        criteria1.mark_completed()
        # criteria2 no está completado
        
        phase.add_criteria(criteria1)
        phase.add_criteria(criteria2)
        
        assert phase.check_completion() == False
        assert phase.is_completed == False

    def test_phase_check_completion_optional_criteria(self):
        """Test: La fase puede completarse aunque criterios opcionales no estén cumplidos."""
        phase = Phase(0, "Fundamentos", "Descripción", "P0")
        criteria1 = PhaseCriteria("REQ001", "Criterio crítico", "critical")
        criteria2 = PhaseCriteria("REQ002", "Criterio opcional", "optional")
        
        criteria1.mark_completed()
        # criteria2 opcional no completado
        
        phase.add_criteria(criteria1)
        phase.add_criteria(criteria2)
        
        assert phase.check_completion() == True

    def test_phase_get_pending_criteria(self):
        """Test: Obtener lista de criterios pendientes."""
        phase = Phase(0, "Fundamentos", "Descripción", "P0")
        criteria1 = PhaseCriteria("REQ001", "Completado", "critical")
        criteria2 = PhaseCriteria("REQ002", "Pendiente", "critical")
        
        criteria1.mark_completed()
        
        phase.add_criteria(criteria1)
        phase.add_criteria(criteria2)
        
        pending = phase.get_pending_criteria()
        assert len(pending) == 1
        assert pending[0].id == "REQ002"


class TestPhaseCriteria:
    """Tests para la clase PhaseCriteria."""

    def test_criteria_creation(self):
        """Test: Crear un criterio de salida."""
        criteria = PhaseCriteria(
            id="REQ001",
            description="Tests unitarios > 80% cobertura",
            requirement_type="critical"
        )
        
        assert criteria.id == "REQ001"
        assert criteria.description == "Tests unitarios > 80% cobertura"
        assert criteria.requirement_type == "critical"
        assert criteria.is_completed == False

    def test_criteria_mark_completed(self):
        """Test: Marcar un criterio como completado."""
        criteria = PhaseCriteria("REQ001", "Descripción", "critical")
        
        assert criteria.is_completed == False
        criteria.mark_completed()
        assert criteria.is_completed == True

    def test_criteria_mark_uncompleted(self):
        """Test: Marcar un criterio como no completado."""
        criteria = PhaseCriteria("REQ001", "Descripción", "critical")
        criteria.mark_completed()
        
        assert criteria.is_completed == True
        criteria.mark_uncompleted()
        assert criteria.is_completed == False

    def test_criteria_is_optional(self):
        """Test: Verificar si un criterio es opcional."""
        criteria_critical = PhaseCriteria("REQ001", "Crítico", "critical")
        criteria_optional = PhaseCriteria("REQ002", "Opcional", "optional")
        
        assert criteria_critical.is_optional() == False
        assert criteria_optional.is_optional() == True


class TestPhaseManager:
    """Tests para la clase PhaseManager."""

    @pytest.fixture
    def sample_config(self):
        """Configuración de ejemplo para tests."""
        return {
            "phases": [
                {
                    "phase_number": 0,
                    "name": "Fundamentos",
                    "description": "Configuración inicial",
                    "priority": "P0",
                    "criteria": [
                        {
                            "id": "P0_001",
                            "description": "Repo + estructura base",
                            "requirement_type": "critical"
                        },
                        {
                            "id": "P0_002",
                            "description": "Tests unitarios > 80%",
                            "requirement_type": "critical"
                        }
                    ]
                },
                {
                    "phase_number": 1,
                    "name": "Núcleo",
                    "description": "Bot 1 operacional",
                    "priority": "P0",
                    "criteria": [
                        {
                            "id": "P1_001",
                            "description": "Bot 1 ejecuta ciclos",
                            "requirement_type": "critical"
                        }
                    ]
                }
            ]
        }

    def test_phase_manager_initialization(self, sample_config):
        """Test: Inicializar PhaseManager con configuración."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        assert len(manager.phases) == 2
        assert manager.current_phase == 0
        assert manager.phases[0].name == "Fundamentos"

    def test_phase_manager_get_phase(self, sample_config):
        """Test: Obtener una fase específica."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        phase = manager.get_phase(0)
        assert phase is not None
        assert phase.name == "Fundamentos"
        
        phase_invalid = manager.get_phase(99)
        assert phase_invalid is None

    def test_phase_manager_get_current_phase(self, sample_config):
        """Test: Obtener la fase actual."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        current = manager.get_current_phase()
        assert current.phase_number == 0
        assert current.name == "Fundamentos"

    def test_phase_manager_can_advance_to_next_phase_success(self, sample_config):
        """Test: Avanzar a la siguiente fase cuando la actual está completa."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        # Completar todos los criterios de la fase 0
        phase0 = manager.get_phase(0)
        for criteria in phase0.criteria:
            criteria.mark_completed()
        
        can_advance, message = manager.can_advance_to_next_phase()
        assert can_advance == True
        assert "completados exitosamente" in message.lower()

    def test_phase_manager_can_advance_to_next_phase_failure(self, sample_config):
        """Test: No se puede avanzar si faltan criterios."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        # No completar criterios
        can_advance, message = manager.can_advance_to_next_phase()
        assert can_advance == False
        assert "pendientes" in message.lower()

    def test_phase_manager_advance_to_next_phase_success(self, sample_config):
        """Test: Avanzar exitosamente a la siguiente fase."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        # Completar fase 0
        phase0 = manager.get_phase(0)
        for criteria in phase0.criteria:
            criteria.mark_completed()
        
        success, message = manager.advance_to_next_phase()
        assert success == True
        assert manager.current_phase == 1

    def test_phase_manager_advance_to_next_phase_failure(self, sample_config):
        """Test: Fallar al avanzar si no se cumplen criterios."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        # No completar criterios
        success, message = manager.advance_to_next_phase()
        assert success == False
        assert manager.current_phase == 0

    def test_phase_manager_advance_to_next_phase_already_at_last(self, sample_config):
        """Test: No se puede avanzar si ya se está en la última fase."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        # Avanzar a la última fase
        manager.current_phase = 1
        
        # Completar fase 1
        phase1 = manager.get_phase(1)
        for criteria in phase1.criteria:
            criteria.mark_completed()
        
        success, message = manager.advance_to_next_phase()
        assert success == False
        assert "última fase" in message.lower()

    def test_phase_manager_get_phase_progress(self, sample_config):
        """Test: Obtener el progreso de una fase."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        phase0 = manager.get_phase(0)
        phase0.criteria[0].mark_completed()
        
        progress = manager.get_phase_progress(0)
        assert progress["completed"] == 1
        assert progress["total"] == 2
        assert progress["percentage"] == 50.0

    def test_phase_manager_get_overall_progress(self, sample_config):
        """Test: Obtener el progreso general del proyecto."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        # Completar 1 criterio de fase 0
        phase0 = manager.get_phase(0)
        phase0.criteria[0].mark_completed()
        
        progress = manager.get_overall_progress()
        assert progress["total_phases"] == 2
        assert progress["current_phase"] == 0
        assert progress["total_criteria"] == 3
        assert progress["completed_criteria"] == 1

    def test_phase_manager_save_state(self, sample_config, tmp_path):
        """Test: Guardar el estado del PhaseManager."""
        config_file = tmp_path / "phases.json"
        state_file = tmp_path / "phase_state.json"
        
        # Crear archivo de configuración
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        manager = PhaseManager(str(config_file))
        
        # Completar un criterio
        phase0 = manager.get_phase(0)
        phase0.criteria[0].mark_completed()
        
        # Guardar estado
        manager.save_state(str(state_file))
        
        # Verificar que el archivo existe
        assert state_file.exists()
        
        # Verificar contenido
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        assert state["current_phase"] == 0
        assert len(state["phases"]) == 2

    def test_phase_manager_load_state(self, sample_config, tmp_path):
        """Test: Cargar el estado del PhaseManager."""
        config_file = tmp_path / "phases.json"
        state_file = tmp_path / "phase_state.json"
        
        # Crear archivo de configuración
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Estado guardado
        saved_state = {
            "current_phase": 1,
            "phases": [
                {
                    "phase_number": 0,
                    "is_completed": True,
                    "criteria": [
                        {"id": "P0_001", "is_completed": True},
                        {"id": "P0_002", "is_completed": True}
                    ]
                }
            ]
        }
        
        with open(state_file, 'w') as f:
            json.dump(saved_state, f)
        
        manager = PhaseManager(str(config_file))
        manager.load_state(str(state_file))
        
        assert manager.current_phase == 1
        phase0 = manager.get_phase(0)
        assert phase0.is_completed == True
        assert all(c.is_completed for c in phase0.criteria)

    def test_phase_manager_validate_phase_transition(self, sample_config):
        """
        Test Gherkin: Avanzar por fases con criterios de salida
        Dado que el roadmap define fases y entregables
        Cuando un entregable cumple sus criterios
        Entonces la fase se da por completada y se inicia la siguiente
        """
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        # Dado que el roadmap define fases y entregables
        assert len(manager.phases) > 0
        current_phase = manager.get_current_phase()
        assert current_phase is not None
        assert len(current_phase.criteria) > 0
        
        # Cuando un entregable cumple sus criterios
        for criteria in current_phase.criteria:
            criteria.mark_completed()
        
        # Entonces la fase se da por completada
        assert current_phase.check_completion() == True
        
        # Y se puede iniciar la siguiente
        can_advance, _ = manager.can_advance_to_next_phase()
        assert can_advance == True
        
        success, _ = manager.advance_to_next_phase()
        assert success == True
        assert manager.current_phase == current_phase.phase_number + 1

    def test_phase_manager_mark_criteria_completed(self, sample_config):
        """Test: Marcar un criterio específico como completado."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        success, message = manager.mark_criteria_completed(0, "P0_001")
        assert success == True
        assert "completado" in message.lower()
        
        phase0 = manager.get_phase(0)
        criteria = next(c for c in phase0.criteria if c.id == "P0_001")
        assert criteria.is_completed == True

    def test_phase_manager_mark_criteria_completed_invalid_phase(self, sample_config):
        """Test: Intentar marcar criterio en fase inexistente."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        success, message = manager.mark_criteria_completed(99, "P0_001")
        assert success == False
        assert "no encontrada" in message.lower()

    def test_phase_manager_mark_criteria_completed_invalid_criteria(self, sample_config):
        """Test: Intentar marcar criterio inexistente."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        success, message = manager.mark_criteria_completed(0, "INVALID_ID")
        assert success == False
        assert "no encontrado" in message.lower()

    def test_phase_manager_get_phase_report(self, sample_config):
        """Test: Generar reporte de una fase."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        report = manager.get_phase_report(0)
        assert "FASE 0" in report
        assert "Fundamentos" in report
        assert "P0_001" in report

    def test_phase_manager_get_phase_report_invalid(self, sample_config):
        """Test: Generar reporte de fase inexistente."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_config))):
            with patch("os.path.exists", return_value=True):
                manager = PhaseManager("dummy_path.json")
        
        report = manager.get_phase_report(99)
        assert "no encontrada" in report.lower()

    def test_phase_get_completion_percentage(self):
        """Test: Calcular porcentaje de completitud."""
        phase = Phase(0, "Test", "Descripción", "P0")
        
        # Sin criterios
        assert phase.get_completion_percentage() == 0.0
        
        # Con criterios
        phase.add_criteria(PhaseCriteria("C1", "Desc1", "critical"))
        phase.add_criteria(PhaseCriteria("C2", "Desc2", "critical"))
        
        assert phase.get_completion_percentage() == 0.0
        
        # Completar uno
        phase.criteria[0].mark_completed()
        assert phase.get_completion_percentage() == 50.0
        
        # Completar todos
        phase.criteria[1].mark_completed()
        assert phase.get_completion_percentage() == 100.0
