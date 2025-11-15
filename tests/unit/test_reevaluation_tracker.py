"""
Tests unitarios para ReevaluationTracker.

Ticket: T28 - Registro de trazabilidad de cada reevaluación
Autor: Sistema Botrading
Fecha: 2025-11-13
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Importación del módulo a testear
from src.core.reevaluation_tracker import (
    ReevaluationTracker,
    ReevaluationRecord,
    ReevaluationAction,
    TrackerStatistics
)


class TestReevaluationRecord:
    """Tests para la clase ReevaluationRecord"""
    
    def test_create_record_minimal(self):
        """
        Escenario: Crear registro mínimo de reevaluación
        Dado que se proporciona información básica
        Cuando se crea un ReevaluationRecord
        Entonces se crea con valores correctos
        """
        record = ReevaluationRecord(
            position_id="12345",
            symbol="EURUSD",
            action=ReevaluationAction.MANTENER,
            current_price=1.2500,
            profit_pips=45.5,
            reasoning="Mercado estable, mantener posición"
        )
        
        assert record.position_id == "12345"
        assert record.symbol == "EURUSD"
        assert record.action == ReevaluationAction.MANTENER
        assert record.current_price == 1.2500
        assert record.profit_pips == 45.5
        assert record.reasoning == "Mercado estable, mantener posición"
        assert record.tokens_input == 0
        assert record.tokens_output == 0
        assert record.cost == 0.0
        assert isinstance(record.timestamp, datetime)
    
    def test_create_record_complete(self):
        """
        Escenario: Crear registro completo con todos los datos
        Dado que se proporciona información completa
        Cuando se crea un ReevaluationRecord
        Entonces todos los campos están presentes
        """
        timestamp = datetime.now()
        record = ReevaluationRecord(
            position_id="12345",
            symbol="EURUSD",
            action=ReevaluationAction.ACTUALIZAR,
            current_price=1.2500,
            profit_pips=45.5,
            reasoning="Mover SL a breakeven",
            new_sl=1.2400,
            new_tp=1.2650,
            conversation_id="conv_abc123",
            reevaluation_mode="persistent",
            tokens_input=500,
            tokens_output=150,
            cost=0.0045,
            reevaluation_count=3,
            time_since_last=600,
            timestamp=timestamp
        )
        
        assert record.new_sl == 1.2400
        assert record.new_tp == 1.2650
        assert record.conversation_id == "conv_abc123"
        assert record.reevaluation_mode == "persistent"
        assert record.tokens_input == 500
        assert record.tokens_output == 150
        assert record.cost == 0.0045
        assert record.reevaluation_count == 3
        assert record.time_since_last == 600
        assert record.timestamp == timestamp
    
    def test_to_dict(self):
        """
        Escenario: Convertir record a diccionario
        Dado que existe un ReevaluationRecord
        Cuando se llama to_dict()
        Entonces retorna diccionario con todos los campos
        """
        record = ReevaluationRecord(
            position_id="12345",
            symbol="EURUSD",
            action=ReevaluationAction.CERRAR,
            current_price=1.2500,
            profit_pips=45.5,
            reasoning="Señal de reversión"
        )
        
        data = record.to_dict()
        
        assert isinstance(data, dict)
        assert data["position_id"] == "12345"
        assert data["symbol"] == "EURUSD"
        assert data["action"] == "CERRAR"
        assert data["current_price"] == 1.2500
        assert data["profit_pips"] == 45.5
        assert "timestamp" in data
    
    def test_from_dict(self):
        """
        Escenario: Crear record desde diccionario
        Dado que existe un diccionario con datos de reevaluación
        Cuando se llama from_dict()
        Entonces se crea ReevaluationRecord correctamente
        """
        data = {
            "position_id": "12345",
            "symbol": "GBPUSD",
            "action": "ACTUALIZAR",
            "current_price": 1.3200,
            "profit_pips": 80.0,
            "reasoning": "Extender TP",
            "new_tp": 1.3350,
            "timestamp": "2025-11-13T10:30:00"
        }
        
        record = ReevaluationRecord.from_dict(data)
        
        assert record.position_id == "12345"
        assert record.symbol == "GBPUSD"
        assert record.action == ReevaluationAction.ACTUALIZAR
        assert record.new_tp == 1.3350


class TestReevaluationTracker:
    """Tests para la clase ReevaluationTracker"""
    
    @pytest.fixture
    def temp_dir(self):
        """Crea un directorio temporal para los tests"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def tracker(self, temp_dir):
        """Crea un tracker para tests"""
        return ReevaluationTracker(storage_dir=temp_dir)
    
    def test_initialization(self, temp_dir):
        """
        Escenario: Inicializar ReevaluationTracker
        Dado que se proporciona un directorio de almacenamiento
        Cuando se crea un ReevaluationTracker
        Entonces se inicializa correctamente
        """
        tracker = ReevaluationTracker(storage_dir=temp_dir)
        
        assert tracker.storage_dir == Path(temp_dir)
        assert tracker.storage_file.exists()
    
    def test_register_reevaluation_mantener(self, tracker):
        """
        Escenario: Registrar reevaluación con acción MANTENER
        Dado que se reevaluó una posición y la IA decidió MANTENER
        Cuando se registra la reevaluación
        Entonces queda persistida con todos los detalles
        """
        tracker.register(
            position_id="pos_001",
            symbol="EURUSD",
            action=ReevaluationAction.MANTENER,
            current_price=1.2500,
            profit_pips=30.0,
            reasoning="Mercado estable",
            tokens_input=450,
            tokens_output=120,
            cost=0.0038
        )
        
        # Verificar que se registró
        records = tracker.get_all_records()
        assert len(records) == 1
        
        record = records[0]
        assert record.position_id == "pos_001"
        assert record.symbol == "EURUSD"
        assert record.action == ReevaluationAction.MANTENER
        assert record.tokens_input == 450
        assert record.tokens_output == 120
        assert record.cost == 0.0038
    
    def test_register_reevaluation_actualizar(self, tracker):
        """
        Escenario: Registrar reevaluación con acción ACTUALIZAR
        Dado que se reevaluó una posición y la IA decidió ACTUALIZAR SL/TP
        Cuando se registra la reevaluación con nuevo_sl y nuevo_tp
        Entonces queda persistida con los nuevos valores
        """
        tracker.register(
            position_id="pos_002",
            symbol="GBPUSD",
            action=ReevaluationAction.ACTUALIZAR,
            current_price=1.3200,
            profit_pips=70.0,
            reasoning="Trailing stop a breakeven",
            new_sl=1.3150,
            new_tp=1.3400,
            tokens_input=500,
            tokens_output=150,
            cost=0.0045
        )
        
        records = tracker.get_all_records()
        assert len(records) == 1
        
        record = records[0]
        assert record.action == ReevaluationAction.ACTUALIZAR
        assert record.new_sl == 1.3150
        assert record.new_tp == 1.3400
    
    def test_register_reevaluation_cerrar(self, tracker):
        """
        Escenario: Registrar reevaluación con acción CERRAR
        Dado que se reevaluó una posición y la IA decidió CERRAR
        Cuando se registra la reevaluación
        Entonces queda persistida la decisión de cierre
        """
        tracker.register(
            position_id="pos_003",
            symbol="USDJPY",
            action=ReevaluationAction.CERRAR,
            current_price=150.50,
            profit_pips=-25.0,
            reasoning="Señal de reversión, cerrar antes del SL",
            tokens_input=480,
            tokens_output=130,
            cost=0.0040
        )
        
        records = tracker.get_all_records()
        record = records[0]
        
        assert record.action == ReevaluationAction.CERRAR
        assert record.profit_pips == -25.0
    
    def test_get_history_by_position(self, tracker):
        """
        Escenario: Obtener historial de reevaluaciones por posición
        Dado que existen múltiples reevaluaciones de una misma posición
        Cuando se consulta el historial por position_id
        Entonces se obtienen todas las reevaluaciones de esa posición
        """
        # Registrar 3 reevaluaciones para pos_001
        for i in range(3):
            tracker.register(
                position_id="pos_001",
                symbol="EURUSD",
                action=ReevaluationAction.MANTENER,
                current_price=1.2500 + (i * 0.0010),
                profit_pips=30.0 + (i * 5),
                reasoning=f"Reevaluación {i+1}",
                tokens_input=450,
                tokens_output=120,
                cost=0.0038
            )
        
        # Registrar 2 reevaluaciones para pos_002
        for i in range(2):
            tracker.register(
                position_id="pos_002",
                symbol="GBPUSD",
                action=ReevaluationAction.MANTENER,
                current_price=1.3200,
                profit_pips=50.0,
                reasoning=f"Reevaluación {i+1}",
                tokens_input=450,
                tokens_output=120,
                cost=0.0038
            )
        
        # Consultar historial de pos_001
        history = tracker.get_history_by_position("pos_001")
        
        assert len(history) == 3
        assert all(r.position_id == "pos_001" for r in history)
    
    def test_get_history_by_symbol(self, tracker):
        """
        Escenario: Obtener historial de reevaluaciones por símbolo
        Dado que existen reevaluaciones de diferentes símbolos
        Cuando se consulta el historial por symbol
        Entonces se obtienen solo las del símbolo especificado
        """
        # EURUSD
        tracker.register(
            position_id="pos_001",
            symbol="EURUSD",
            action=ReevaluationAction.MANTENER,
            current_price=1.2500,
            profit_pips=30.0,
            reasoning="Test",
            tokens_input=450,
            tokens_output=120,
            cost=0.0038
        )
        
        # GBPUSD
        tracker.register(
            position_id="pos_002",
            symbol="GBPUSD",
            action=ReevaluationAction.MANTENER,
            current_price=1.3200,
            profit_pips=50.0,
            reasoning="Test",
            tokens_input=450,
            tokens_output=120,
            cost=0.0038
        )
        
        # EURUSD otra vez
        tracker.register(
            position_id="pos_003",
            symbol="EURUSD",
            action=ReevaluationAction.ACTUALIZAR,
            current_price=1.2550,
            profit_pips=80.0,
            reasoning="Test",
            new_sl=1.2500,
            tokens_input=500,
            tokens_output=150,
            cost=0.0045
        )
        
        history = tracker.get_history_by_symbol("EURUSD")
        
        assert len(history) == 2
        assert all(r.symbol == "EURUSD" for r in history)
    
    def test_get_statistics(self, tracker):
        """
        Escenario: Obtener estadísticas de reevaluaciones
        Dado que existen múltiples reevaluaciones registradas
        Cuando se solicitan estadísticas
        Entonces se retornan métricas agregadas correctas
        """
        # Registrar varias reevaluaciones
        tracker.register(
            position_id="pos_001",
            symbol="EURUSD",
            action=ReevaluationAction.MANTENER,
            current_price=1.2500,
            profit_pips=30.0,
            reasoning="Test 1",
            tokens_input=400,
            tokens_output=100,
            cost=0.0030
        )
        
        tracker.register(
            position_id="pos_002",
            symbol="GBPUSD",
            action=ReevaluationAction.ACTUALIZAR,
            current_price=1.3200,
            profit_pips=70.0,
            reasoning="Test 2",
            new_sl=1.3150,
            tokens_input=500,
            tokens_output=150,
            cost=0.0045
        )
        
        tracker.register(
            position_id="pos_003",
            symbol="USDJPY",
            action=ReevaluationAction.CERRAR,
            current_price=150.50,
            profit_pips=-20.0,
            reasoning="Test 3",
            tokens_input=450,
            tokens_output=130,
            cost=0.0040
        )
        
        stats = tracker.get_statistics()
        
        assert stats.total_reevaluations == 3
        assert stats.total_tokens_input == 1350  # 400 + 500 + 450
        assert stats.total_tokens_output == 380  # 100 + 150 + 130
        assert stats.total_cost == pytest.approx(0.0115)  # 0.003 + 0.0045 + 0.004
        assert stats.unique_positions == 3
        assert stats.unique_symbols == 3
        assert stats.actions_count["MANTENER"] == 1
        assert stats.actions_count["ACTUALIZAR"] == 1
        assert stats.actions_count["CERRAR"] == 1
    
    def test_get_statistics_by_action(self, tracker):
        """
        Escenario: Filtrar estadísticas por acción
        Dado que existen reevaluaciones con diferentes acciones
        Cuando se solicitan estadísticas filtradas por acción
        Entonces se retornan solo las de esa acción
        """
        # 2 MANTENER
        for i in range(2):
            tracker.register(
                position_id=f"pos_{i}",
                symbol="EURUSD",
                action=ReevaluationAction.MANTENER,
                current_price=1.2500,
                profit_pips=30.0,
                reasoning="Mantener",
                tokens_input=400,
                tokens_output=100,
                cost=0.0030
            )
        
        # 1 ACTUALIZAR
        tracker.register(
            position_id="pos_2",
            symbol="GBPUSD",
            action=ReevaluationAction.ACTUALIZAR,
            current_price=1.3200,
            profit_pips=70.0,
            reasoning="Actualizar",
            new_sl=1.3150,
            tokens_input=500,
            tokens_output=150,
            cost=0.0045
        )
        
        stats_mantener = tracker.get_statistics(action_filter=ReevaluationAction.MANTENER)
        
        assert stats_mantener.total_reevaluations == 2
        assert stats_mantener.total_tokens_input == 800
        assert stats_mantener.total_cost == pytest.approx(0.0060)
    
    def test_persistence(self, temp_dir):
        """
        Escenario: Persistencia de datos entre instancias
        Dado que se registran reevaluaciones en una instancia
        Cuando se crea una nueva instancia con el mismo directorio
        Entonces los datos persisten
        """
        # Primera instancia
        tracker1 = ReevaluationTracker(storage_dir=temp_dir)
        tracker1.register(
            position_id="pos_001",
            symbol="EURUSD",
            action=ReevaluationAction.MANTENER,
            current_price=1.2500,
            profit_pips=30.0,
            reasoning="Test persistencia",
            tokens_input=400,
            tokens_output=100,
            cost=0.0030
        )
        
        # Segunda instancia (nuevo objeto)
        tracker2 = ReevaluationTracker(storage_dir=temp_dir)
        records = tracker2.get_all_records()
        
        assert len(records) == 1
        assert records[0].position_id == "pos_001"
    
    def test_clear_history_by_position(self, tracker):
        """
        Escenario: Limpiar historial de una posición específica
        Dado que existen reevaluaciones de múltiples posiciones
        Cuando se limpia el historial de una posición
        Entonces solo se eliminan las de esa posición
        """
        # Registrar para pos_001
        tracker.register(
            position_id="pos_001",
            symbol="EURUSD",
            action=ReevaluationAction.MANTENER,
            current_price=1.2500,
            profit_pips=30.0,
            reasoning="Test",
            tokens_input=400,
            tokens_output=100,
            cost=0.0030
        )
        
        # Registrar para pos_002
        tracker.register(
            position_id="pos_002",
            symbol="GBPUSD",
            action=ReevaluationAction.MANTENER,
            current_price=1.3200,
            profit_pips=50.0,
            reasoning="Test",
            tokens_input=400,
            tokens_output=100,
            cost=0.0030
        )
        
        # Limpiar pos_001
        tracker.clear_history_by_position("pos_001")
        
        all_records = tracker.get_all_records()
        assert len(all_records) == 1
        assert all_records[0].position_id == "pos_002"
    
    def test_validation_negative_tokens(self, tracker):
        """
        Escenario: Validar que tokens no sean negativos
        Dado que se intenta registrar con tokens negativos
        Cuando se llama register()
        Entonces se lanza ValueError
        """
        with pytest.raises(ValueError, match="tokens_input debe ser >= 0"):
            tracker.register(
                position_id="pos_001",
                symbol="EURUSD",
                action=ReevaluationAction.MANTENER,
                current_price=1.2500,
                profit_pips=30.0,
                reasoning="Test",
                tokens_input=-100,  # Negativo inválido
                tokens_output=100,
                cost=0.0030
            )
    
    def test_validation_negative_cost(self, tracker):
        """
        Escenario: Validar que cost no sea negativo
        Dado que se intenta registrar con cost negativo
        Cuando se llama register()
        Entonces se lanza ValueError
        """
        with pytest.raises(ValueError, match="cost debe ser >= 0"):
            tracker.register(
                position_id="pos_001",
                symbol="EURUSD",
                action=ReevaluationAction.MANTENER,
                current_price=1.2500,
                profit_pips=30.0,
                reasoning="Test",
                tokens_input=400,
                tokens_output=100,
                cost=-0.0030  # Negativo inválido
            )


class TestIntegrationWithReevaluationManager:
    """Tests de integración con ReevaluationManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Crea un directorio temporal para los tests"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    def test_track_reevaluations_automatically(self, temp_dir):
        """
        Escenario: ReevaluationManager registra automáticamente cada reevaluación
        Dado que ReevaluationManager tiene un tracker integrado
        Cuando se ejecuta una reevaluación
        Entonces se registra automáticamente en el tracker
        """
        # Este test será implementado cuando se integre con ReevaluationManager
        # Por ahora es un placeholder que valida la interfaz esperada
        
        tracker = ReevaluationTracker(storage_dir=temp_dir)
        
        # Simular que ReevaluationManager registra después de reevaluar
        tracker.register(
            position_id="pos_001",
            symbol="EURUSD",
            action=ReevaluationAction.ACTUALIZAR,
            current_price=1.2500,
            profit_pips=50.0,
            reasoning="Decisión automática de IA",
            new_sl=1.2450,
            conversation_id="conv_abc123",
            reevaluation_mode="persistent",
            tokens_input=500,
            tokens_output=150,
            cost=0.0045,
            reevaluation_count=2,
            time_since_last=600
        )
        
        history = tracker.get_history_by_position("pos_001")
        assert len(history) == 1
        assert history[0].reevaluation_count == 2
        assert history[0].time_since_last == 600


class TestAdditionalCoverage:
    """Tests adicionales para mejorar cobertura"""
    
    @pytest.fixture
    def temp_dir(self):
        """Crea un directorio temporal para los tests"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def tracker(self, temp_dir):
        """Crea un tracker para tests"""
        return ReevaluationTracker(storage_dir=temp_dir)
    
    def test_clear_all_records(self, tracker):
        """
        Escenario: Limpiar todos los registros
        Dado que existen múltiples registros
        Cuando se llama clear_all()
        Entonces se eliminan todos los registros
        """
        # Agregar varios registros
        for i in range(5):
            tracker.register(
                position_id=f"pos_{i}",
                symbol="EURUSD",
                action=ReevaluationAction.MANTENER,
                current_price=1.2500,
                profit_pips=30.0,
                reasoning="Test"
            )
        
        # Verificar que existen
        assert len(tracker.get_all_records()) == 5
        
        # Limpiar todos
        deleted = tracker.clear_all()
        
        assert deleted == 5
        assert len(tracker.get_all_records()) == 0
    
    def test_invalid_action_from_string(self):
        """
        Escenario: Convertir string inválido a ReevaluationAction
        Dado que se proporciona un string inválido
        Cuando se llama from_string()
        Entonces se lanza ValueError
        """
        with pytest.raises(ValueError, match="Acción inválida"):
            ReevaluationAction.from_string("INVALID_ACTION")
    
    def test_statistics_empty(self, tracker):
        """
        Escenario: Obtener estadísticas sin registros
        Dado que no hay registros
        Cuando se solicitan estadísticas
        Entonces se retornan valores en cero
        """
        stats = tracker.get_statistics()
        
        assert stats.total_reevaluations == 0
        assert stats.total_cost == 0.0
        assert stats.total_tokens_input == 0
        assert stats.total_tokens_output == 0
        assert stats.unique_positions == 0
        assert stats.unique_symbols == 0
    
    def test_corrupted_json_file(self, temp_dir):
        """
        Escenario: Manejar archivo JSON corrupto
        Dado que el archivo JSON está corrupto
        Cuando se intenta cargar
        Entonces retorna lista vacía sin crashear
        """
        tracker = ReevaluationTracker(storage_dir=temp_dir)
        
        # Corromper archivo
        with open(tracker.storage_file, 'w') as f:
            f.write("{ corrupted json [")
        
        # Debe retornar vacío sin crashear
        records = tracker.get_all_records()
        assert records == []
    
    def test_non_list_json(self, temp_dir):
        """
        Escenario: Archivo JSON que no contiene lista
        Dado que el archivo JSON contiene objeto en lugar de lista
        Cuando se intenta cargar
        Entonces retorna lista vacía
        """
        tracker = ReevaluationTracker(storage_dir=temp_dir)
        
        # Escribir objeto en lugar de lista
        with open(tracker.storage_file, 'w') as f:
            json.dump({"not": "a list"}, f)
        
        records = tracker.get_all_records()
        assert records == []
    
    def test_record_with_parse_error(self, temp_dir):
        """
        Escenario: Record con error de parseo
        Dado que hay un record con datos inválidos
        Cuando se carga
        Entonces se salta ese record y continúa con los demás
        """
        tracker = ReevaluationTracker(storage_dir=temp_dir)
        
        # Crear un record válido
        tracker.register(
            position_id="pos_001",
            symbol="EURUSD",
            action=ReevaluationAction.MANTENER,
            current_price=1.2500,
            profit_pips=30.0,
            reasoning="Valid"
        )
        
        # Agregar manualmente un record inválido
        data = []
        with open(tracker.storage_file, 'r') as f:
            data = json.load(f)
        
        # Agregar record corrupto (sin campo requerido)
        data.append({"invalid": "record"})
        
        with open(tracker.storage_file, 'w') as f:
            json.dump(data, f)
        
        # Cargar debe retornar solo el válido
        records = tracker.get_all_records()
        assert len(records) == 1
        assert records[0].position_id == "pos_001"
