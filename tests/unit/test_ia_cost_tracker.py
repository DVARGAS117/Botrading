"""
Tests unitarios para el módulo ia_cost_tracker.

Este módulo implementa tests para el Ticket T11: Registro de tokens y costo
por consulta, para medir la eficiencia económica de cada metodología.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T11 - Registro de tokens y costo por consulta
"""
import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock


# Importar clase a testear (TDD Red - aún no existe)
from src.core.ia_cost_tracker import IACostTracker


# ==================== FIXTURES ====================

@pytest.fixture
def temp_log_dir():
    """Directorio temporal para logs"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def cost_tracker(temp_log_dir):
    """IACostTracker configurado para tests"""
    return IACostTracker(log_dir=temp_log_dir)


@pytest.fixture
def sample_query_data():
    """Datos de ejemplo para una consulta"""
    return {
        "operation_id": "op_123",
        "tokens_input": 100,
        "tokens_output": 50,
        "cost": 0.002,
        "timestamp": datetime(2025, 11, 13, 10, 30, 0)
    }


# ==================== TESTS DE INICIALIZACIÓN ====================

@pytest.mark.unit
class TestIACostTrackerInitialization:
    """Tests para la inicialización de IACostTracker"""

    def test_init_with_default_log_dir(self):
        """Debe inicializar con directorio de logs por defecto"""
        tracker = IACostTracker()
        assert tracker.log_dir == Path("logs")
        assert tracker.log_file.exists() is False  # No crea archivo hasta registrar

    def test_init_with_custom_log_dir(self, temp_log_dir):
        """Debe inicializar con directorio de logs personalizado"""
        tracker = IACostTracker(log_dir=temp_log_dir)
        assert tracker.log_dir == temp_log_dir
        assert isinstance(tracker.log_file, Path)

    def test_log_file_path_construction(self, temp_log_dir):
        """Debe construir correctamente la ruta del archivo de logs"""
        tracker = IACostTracker(log_dir=temp_log_dir)
        expected_file = temp_log_dir / "ia_costs.json"
        assert tracker.log_file == expected_file


# ==================== TESTS DE REGISTRO ====================

@pytest.mark.unit
class TestIACostTrackerRegistration:
    """Tests para el registro de consultas"""

    def test_register_query_basic(self, cost_tracker, sample_query_data):
        """Debe registrar una consulta básica correctamente"""
        tracker = cost_tracker
        data = sample_query_data

        tracker.register_query(
            operation_id=data["operation_id"],
            tokens_input=data["tokens_input"],
            tokens_output=data["tokens_output"],
            cost=data["cost"]
        )

        # Verificar que se creó el archivo
        assert tracker.log_file.exists()

        # Verificar contenido
        queries = tracker.get_all_queries()
        assert len(queries) == 1

        query = queries[0]
        assert query["operation_id"] == data["operation_id"]
        assert query["tokens_input"] == data["tokens_input"]
        assert query["tokens_output"] == data["tokens_output"]
        assert query["cost"] == data["cost"]
        assert "timestamp" in query

    def test_register_query_with_custom_timestamp(self, cost_tracker, sample_query_data):
        """Debe registrar consulta con timestamp personalizado"""
        tracker = cost_tracker
        data = sample_query_data

        custom_timestamp = datetime(2025, 11, 13, 12, 0, 0)
        tracker.register_query(
            operation_id=data["operation_id"],
            tokens_input=data["tokens_input"],
            tokens_output=data["tokens_output"],
            cost=data["cost"],
            timestamp=custom_timestamp
        )

        queries = tracker.get_all_queries()
        assert len(queries) == 1
        assert queries[0]["timestamp"] == custom_timestamp.isoformat()

    def test_register_multiple_queries_same_operation(self, cost_tracker):
        """Debe permitir múltiples consultas para la misma operación"""
        tracker = cost_tracker

        # Registrar dos consultas para la misma operación
        tracker.register_query("op_123", 100, 50, 0.002)
        tracker.register_query("op_123", 80, 40, 0.001)

        queries = tracker.get_all_queries()
        assert len(queries) == 2

        # Verificar que ambas tienen el mismo operation_id
        assert all(q["operation_id"] == "op_123" for q in queries)

    def test_register_query_creates_log_directory(self, tmp_path):
        """Debe crear el directorio de logs si no existe"""
        log_dir = tmp_path / "nonexistent" / "logs"
        tracker = IACostTracker(log_dir=log_dir)

        tracker.register_query("op_123", 100, 50, 0.002)

        assert log_dir.exists()
        assert tracker.log_file.exists()


# ==================== TESTS DE CONSULTA ====================

@pytest.mark.unit
class TestIACostTrackerQueries:
    """Tests para consultas de datos"""

    def test_get_queries_for_operation(self, cost_tracker):
        """Debe retornar consultas para una operación específica"""
        tracker = cost_tracker

        # Registrar consultas para diferentes operaciones
        tracker.register_query("op_123", 100, 50, 0.002)
        tracker.register_query("op_456", 200, 100, 0.004)
        tracker.register_query("op_123", 80, 40, 0.001)

        # Consultar para op_123
        queries = tracker.get_queries_for_operation("op_123")
        assert len(queries) == 2
        assert all(q["operation_id"] == "op_123" for q in queries)

        # Consultar para op_456
        queries = tracker.get_queries_for_operation("op_456")
        assert len(queries) == 1
        assert queries[0]["operation_id"] == "op_456"

        # Consultar operación inexistente
        queries = tracker.get_queries_for_operation("op_999")
        assert len(queries) == 0

    def test_get_all_queries(self, cost_tracker):
        """Debe retornar todas las consultas"""
        tracker = cost_tracker

        # Registrar varias consultas
        tracker.register_query("op_123", 100, 50, 0.002)
        tracker.register_query("op_456", 200, 100, 0.004)

        queries = tracker.get_all_queries()
        assert len(queries) == 2

        # Verificar orden (más reciente primero)
        assert queries[0]["operation_id"] == "op_456"
        assert queries[1]["operation_id"] == "op_123"

    def test_get_all_queries_empty(self, cost_tracker):
        """Debe retornar lista vacía si no hay consultas"""
        tracker = cost_tracker

        queries = tracker.get_all_queries()
        assert queries == []


# ==================== TESTS DE ESTADÍSTICAS ====================

@pytest.mark.unit
class TestIACostTrackerStatistics:
    """Tests para estadísticas de costos"""

    def test_get_total_cost(self, cost_tracker):
        """Debe calcular el costo total de todas las consultas"""
        tracker = cost_tracker

        tracker.register_query("op_123", 100, 50, 0.002)
        tracker.register_query("op_456", 200, 100, 0.004)
        tracker.register_query("op_789", 50, 25, 0.001)

        total_cost = tracker.get_total_cost()
        assert total_cost == 0.007  # 0.002 + 0.004 + 0.001

    def test_get_total_cost_empty(self, cost_tracker):
        """Debe retornar 0 si no hay consultas"""
        tracker = cost_tracker

        total_cost = tracker.get_total_cost()
        assert total_cost == 0.0

    def test_get_statistics_basic(self, cost_tracker):
        """Debe calcular estadísticas básicas"""
        tracker = cost_tracker

        tracker.register_query("op_123", 100, 50, 0.002)
        tracker.register_query("op_456", 200, 100, 0.004)
        tracker.register_query("op_123", 80, 40, 0.001)

        stats = tracker.get_statistics()

        assert stats["total_queries"] == 3
        assert stats["total_cost"] == 0.007
        assert stats["total_tokens_input"] == 380  # 100 + 200 + 80
        assert stats["total_tokens_output"] == 190  # 50 + 100 + 40
        assert stats["unique_operations"] == 2  # op_123 y op_456

    def test_get_statistics_empty(self, cost_tracker):
        """Debe retornar estadísticas vacías si no hay consultas"""
        tracker = cost_tracker

        stats = tracker.get_statistics()

        assert stats["total_queries"] == 0
        assert stats["total_cost"] == 0.0
        assert stats["total_tokens_input"] == 0
        assert stats["total_tokens_output"] == 0
        assert stats["unique_operations"] == 0


# ==================== TESTS DE PERSISTENCIA ====================

@pytest.mark.unit
class TestIACostTrackerPersistence:
    """Tests para persistencia de datos"""

    def test_persistence_across_instances(self, temp_log_dir):
        """Debe persistir datos entre instancias"""
        # Primera instancia
        tracker1 = IACostTracker(log_dir=temp_log_dir)
        tracker1.register_query("op_123", 100, 50, 0.002)

        # Segunda instancia (misma ubicación)
        tracker2 = IACostTracker(log_dir=temp_log_dir)

        queries = tracker2.get_all_queries()
        assert len(queries) == 1
        assert queries[0]["operation_id"] == "op_123"

    def test_load_existing_file(self, temp_log_dir):
        """Debe cargar datos desde archivo existente"""
        log_file = temp_log_dir / "ia_costs.json"

        # Crear archivo con datos
        existing_data = [
            {
                "operation_id": "op_existing",
                "tokens_input": 150,
                "tokens_output": 75,
                "cost": 0.003,
                "timestamp": "2025-11-13T10:00:00"
            }
        ]
        log_file.write_text(json.dumps(existing_data, indent=2))

        # Cargar con nueva instancia
        tracker = IACostTracker(log_dir=temp_log_dir)

        queries = tracker.get_all_queries()
        assert len(queries) == 1
        assert queries[0]["operation_id"] == "op_existing"

    def test_corrupted_file_handling(self, temp_log_dir):
        """Debe manejar archivos JSON corruptos"""
        log_file = temp_log_dir / "ia_costs.json"
        log_file.write_text("invalid json content")

        # Debe inicializar sin errores, ignorando archivo corrupto
        tracker = IACostTracker(log_dir=temp_log_dir)

        # Archivo corrupto debería ser ignorado
        queries = tracker.get_all_queries()
        assert queries == []


# ==================== TESTS DE VALIDACIÓN ====================

@pytest.mark.unit
class TestIACostTrackerValidation:
    """Tests para validación de entrada"""

    def test_register_query_validates_positive_values(self, cost_tracker):
        """Debe validar que tokens y costo sean positivos"""
        tracker = cost_tracker

        # Valores válidos
        tracker.register_query("op_123", 100, 50, 0.002)

        # Valores inválidos deberían lanzar excepción
        with pytest.raises(ValueError):
            tracker.register_query("op_123", -100, 50, 0.002)

        with pytest.raises(ValueError):
            tracker.register_query("op_123", 100, -50, 0.002)

        with pytest.raises(ValueError):
            tracker.register_query("op_123", 100, 50, -0.002)

    def test_register_query_validates_types(self, cost_tracker):
        """Debe validar tipos de parámetros"""
        tracker = cost_tracker

        # Tipos correctos
        tracker.register_query("op_123", 100, 50, 0.002)

        # Tipos incorrectos
        with pytest.raises(TypeError):
            tracker.register_query(123, 100, 50, 0.002)  # operation_id no string

        with pytest.raises(TypeError):
            tracker.register_query("op_123", "100", 50, 0.002)  # tokens_input no int

        with pytest.raises(TypeError):
            tracker.register_query("op_123", 100, 50.5, 0.002)  # tokens_output no int