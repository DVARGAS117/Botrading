"""
Tests unitarios para el módulo demo_mode_validator.

Este módulo implementa tests para el Ticket T52: Operación en demo antes de real.
Permite validar que las estrategias se prueben en modo demo antes de operar con dinero real.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T52 - Operación en demo antes de real
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path
import json


# Importar clase a testear (aún no existe, TDD Red)
from src.core.demo_mode_validator import (
    DemoModeValidator,
    DemoValidationError,
    ValidationStatus
)


class TestDemoModeValidator:
    """Tests para la clase DemoModeValidator"""

    @pytest.fixture
    def sample_demo_config(self):
        """Configuración de demo de ejemplo"""
        return {
            "demo_mode": {
                "enabled": True,
                "require_validation": True,
                "min_demo_operations": 10,
                "min_demo_days": 3,
                "validation_criteria": {
                    "min_win_rate": 0.6,
                    "max_drawdown_percent": 5.0,
                    "min_total_operations": 50
                }
            }
        }

    def test_demo_mode_validator_init_with_config_dict(self, sample_demo_config):
        """
        Test: Debe inicializarse correctamente con diccionario de configuración

        Dado que se proporciona configuración como diccionario
        Cuando se crea DemoModeValidator
        Entonces debe inicializarse con los valores correctos
        """
        # Act
        validator = DemoModeValidator(sample_demo_config)

        # Assert
        assert validator.demo_enabled == True
        assert validator.require_validation == True
        assert validator.min_demo_operations == 10
        assert validator.min_demo_days == 3

    def test_demo_mode_validator_init_with_config_file(self, tmp_path, sample_demo_config):
        """
        Test: Debe cargar configuración desde archivo JSON

        Dado que existe un archivo JSON con configuración
        Cuando se crea DemoModeValidator con path al archivo
        Entonces debe cargar la configuración correctamente
        """
        # Arrange
        config_file = tmp_path / "demo_config.json"
        config_file.write_text(json.dumps(sample_demo_config))

        # Act
        validator = DemoModeValidator(str(config_file))

        # Assert
        assert validator.demo_enabled == True
        assert validator.require_validation == True

    def test_demo_mode_validator_init_file_not_found(self):
        """
        Test: Debe lanzar error si el archivo de configuración no existe

        Dado que se proporciona path a archivo inexistente
        Cuando se crea DemoModeValidator
        Entonces debe lanzar DemoValidationError
        """
        # Act & Assert
        with pytest.raises(DemoValidationError) as exc_info:
            DemoModeValidator("non_existent_file.json")

        assert "no encontrado" in str(exc_info.value).lower()

    def test_validate_operation_in_demo_mode(self, sample_demo_config):
        """
        Test: Debe permitir operaciones cuando demo_mode está habilitado

        Dado que demo_mode está habilitado
        Cuando se valida una operación
        Entonces debe retornar ValidationStatus válido
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)

        # Act
        result = validator.validate_operation()

        # Assert
        assert result.is_valid == True
        assert "modo demo" in result.reason.lower()

    def test_validate_operation_real_mode_without_validation(self, sample_demo_config):
        """
        Test: Debe rechazar operaciones en modo real sin validación previa

        Dado que demo_mode está deshabilitado y no hay validación
        Cuando se valida una operación
        Entonces debe retornar ValidationStatus inválido
        """
        # Arrange
        config = sample_demo_config.copy()
        config["demo_mode"]["enabled"] = False
        validator = DemoModeValidator(config)

        # Act
        result = validator.validate_operation()

        # Assert
        assert result.is_valid == False
        assert "validación" in result.reason.lower()

    def test_validate_operation_real_mode_with_validation(self, sample_demo_config):
        """
        Test: Debe permitir operaciones en modo real con validación previa

        Dado que demo_mode está deshabilitado pero hay validación
        Cuando se valida una operación
        Entonces debe retornar ValidationStatus válido
        """
        # Arrange
        config = sample_demo_config.copy()
        config["demo_mode"]["enabled"] = False
        validator = DemoModeValidator(config)
        validator.mark_as_validated()  # Simular validación previa

        # Act
        result = validator.validate_operation()

        # Assert
        assert result.is_valid == True
        assert "validado" in result.reason.lower()

    def test_mark_as_validated(self, sample_demo_config):
        """
        Test: Debe marcar la configuración como validada

        Dado que la configuración requiere validación
        Cuando se marca como validada
        Entonces debe actualizar el estado interno
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)

        # Act
        validator.mark_as_validated()

        # Assert
        assert validator.is_validated == True

    def test_is_ready_for_real_trading_insufficient_operations(self, sample_demo_config):
        """
        Test: Debe retornar False si no hay suficientes operaciones demo

        Dado que se requieren 10 operaciones pero solo hay 5
        Cuando se verifica readiness para real trading
        Entonces debe retornar False
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)
        validator.record_demo_operation(success=True)  # Solo 1 operación

        # Act
        ready = validator.is_ready_for_real_trading()

        # Assert
        assert ready == False

    def test_is_ready_for_real_trading_sufficient_operations(self, sample_demo_config):
        """
        Test: Debe retornar True si hay suficientes operaciones demo exitosas

        Dado que se requieren 10 operaciones y hay 15 exitosas en días diferentes
        Cuando se verifica readiness para real trading
        Entonces debe retornar True
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)
        
        # Registrar operaciones en diferentes días
        base_time = datetime(2025, 11, 1, 10, 0, 0)
        for i in range(15):
            with patch('src.core.demo_mode_validator.datetime') as mock_datetime:
                mock_datetime.now.return_value = base_time + timedelta(days=i//5)  # 5 operaciones por día
                validator.record_demo_operation(success=True)

        # Act
        ready = validator.is_ready_for_real_trading()

        # Assert
        assert ready == True

    def test_record_demo_operation_success(self, sample_demo_config):
        """
        Test: Debe registrar operaciones demo exitosas

        Dado que se registra una operación exitosa
        Cuando se consulta el historial
        Entonces debe incluir la operación exitosa
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)

        # Act
        validator.record_demo_operation(success=True)

        # Assert
        stats = validator.get_demo_statistics()
        assert stats["total_operations"] == 1
        assert stats["successful_operations"] == 1
        assert stats["win_rate"] == 1.0

    def test_record_demo_operation_failure(self, sample_demo_config):
        """
        Test: Debe registrar operaciones demo fallidas

        Dado que se registra una operación fallida
        Cuando se consulta el historial
        Entonces debe incluir la operación fallida
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)

        # Act
        validator.record_demo_operation(success=False)

        # Assert
        stats = validator.get_demo_statistics()
        assert stats["total_operations"] == 1
        assert stats["successful_operations"] == 0
        assert stats["win_rate"] == 0.0

    def test_get_validation_status_demo_mode(self, sample_demo_config):
        """
        Test: Debe retornar estado de validación para modo demo

        Dado que está en modo demo
        Cuando se obtiene el estado de validación
        Entonces debe indicar que está en demo
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)

        # Act
        status = validator.get_validation_status()

        # Assert
        assert status["demo_mode"] == True
        assert status["validation_required"] == True
        assert status["is_validated"] == False

    def test_switch_to_real_mode_after_validation(self, sample_demo_config):
        """
        Test: Debe permitir cambiar a modo real después de validación

        Dado que está validado en demo
        Cuando se cambia a modo real
        Entonces debe permitir operaciones en real
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)
        validator.mark_as_validated()

        # Act
        validator.switch_to_real_mode()
        result = validator.validate_operation()

        # Assert
        assert validator.demo_enabled == False
        assert result.is_valid == True

    def test_switch_to_real_mode_without_validation_should_fail(self, sample_demo_config):
        """
        Test: No debe permitir cambiar a modo real sin validación

        Dado que no está validado
        Cuando se intenta cambiar a modo real
        Entonces debe lanzar error
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)

        # Act & Assert
        with pytest.raises(DemoValidationError) as exc_info:
            validator.switch_to_real_mode()

        assert "validación" in str(exc_info.value).lower()

    def test_get_demo_statistics_empty(self, sample_demo_config):
        """
        Test: Debe retornar estadísticas vacías inicialmente

        Dado que no hay operaciones registradas
        Cuando se obtienen estadísticas
        Entonces debe retornar valores cero
        """
        # Arrange
        validator = DemoModeValidator(sample_demo_config)

        # Act
        stats = validator.get_demo_statistics()

        # Assert
        assert stats["total_operations"] == 0
        assert stats["successful_operations"] == 0
        assert stats["win_rate"] == 0.0

    def test_persist_validation_state(self, tmp_path, sample_demo_config):
        """
        Test: Debe persistir el estado de validación

        Dado que se marca como validado
        Cuando se guarda el estado
        Entonces debe poder restaurarse
        """
        # Arrange
        state_file = tmp_path / "validation_state.json"
        validator = DemoModeValidator(sample_demo_config)
        validator.mark_as_validated()

        # Act
        validator.save_validation_state(str(state_file))
        new_validator = DemoModeValidator(sample_demo_config)
        new_validator.load_validation_state(str(state_file))

        # Assert
        assert new_validator.is_validated == True