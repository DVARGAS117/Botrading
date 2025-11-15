"""
Tests unitarios para IAQueryRepository - T33

Este módulo contiene tests unitarios para el registro de consultas a IA
con prompts, respuestas, tokens y costo, siguiendo metodología TDD.

Autor: Sistema Botrading
Fecha: 2025-11-15
Ticket: T33 - Registro de consultas a IA con prompts, respuesta, tokens y costo
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import tempfile

# Importar el repositorio (que aún no existe, pero lo crearemos)
from src.core.ia_query_repository import (
    IAQueryRepository,
    IAQueryRepositoryError,
    IAQuery,
    QueryType
)


# ==================== FIXTURES ====================

@pytest.fixture
def temp_db_path():
    """Crea una base de datos temporal para tests"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        db_path = Path(f.name)
    
    yield db_path
    
    # Limpieza (ignorar errores en Windows)
    try:
        if db_path.exists():
            db_path.unlink()
    except PermissionError:
        pass  # En Windows, a veces SQLite mantiene el archivo bloqueado


@pytest.fixture
def repository(temp_db_path):
    """Crea una instancia del repositorio para tests"""
    repo = IAQueryRepository(db_path=temp_db_path)
    yield repo


@pytest.fixture
def sample_query_data() -> Dict[str, Any]:
    """Datos de ejemplo para crear una consulta IA"""
    return {
        'bot_id': 1,
        'ia_id': 1,
        'symbol': 'EURUSD',
        'query_type': QueryType.EVALUATION,
        'prompt': 'Analiza EURUSD con EMA(20)=1.0850, RSI=65',
        'response': '{"decision": "OPERAR", "direction": "BUY", "sl": 1.0800, "tp": 1.0950}',
        'tokens_input': 150,
        'tokens_output': 80,
        'cost_usd': 0.0023,
        'action_decided': 'OPERAR',
        'operation_id': None  # Sin operación asociada inicialmente
    }


@pytest.fixture
def sample_query(repository, sample_query_data) -> IAQuery:
    """Crea y persiste una consulta IA de ejemplo"""
    return repository.create_query(**sample_query_data)


# ==================== TESTS DE INICIALIZACIÓN ====================

class TestInitialization:
    """Tests para inicialización del repositorio"""
    
    def test_repository_initialization(self, temp_db_path):
        """Test: El repositorio se inicializa correctamente"""
        repo = IAQueryRepository(db_path=temp_db_path)
        
        assert repo is not None
        assert repo.db_path == temp_db_path
        assert temp_db_path.exists()
    
    def test_database_schema_created(self, repository):
        """Test: El schema de la BD se crea correctamente"""
        # Verificar que la tabla existe
        with sqlite3.connect(repository.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='consultas_ia'"
            )
            result = cursor.fetchone()
            
        assert result is not None
        assert result[0] == 'consultas_ia'
    
    def test_indexes_created(self, repository):
        """Test: Los índices se crean correctamente"""
        with sqlite3.connect(repository.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='consultas_ia'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
        
        # Debe tener índices para operacion_id y bot_id/ia_id
        assert 'idx_operacion' in indexes
        assert 'idx_bot_ia' in indexes


# ==================== TESTS DE CREACIÓN ====================

class TestCreateQuery:
    """Tests para creación de consultas IA"""
    
    def test_create_query_success(self, repository, sample_query_data):
        """Test: Se crea una consulta correctamente"""
        query = repository.create_query(**sample_query_data)
        
        assert query.id is not None
        assert query.id > 0
        assert query.bot_id == sample_query_data['bot_id']
        assert query.ia_id == sample_query_data['ia_id']
        assert query.symbol == sample_query_data['symbol']
        assert query.query_type == sample_query_data['query_type']
        assert query.prompt == sample_query_data['prompt']
        assert query.response == sample_query_data['response']
        assert query.tokens_input == sample_query_data['tokens_input']
        assert query.tokens_output == sample_query_data['tokens_output']
        assert query.tokens_total == 230  # 150 + 80
        assert query.cost_usd == sample_query_data['cost_usd']
        assert query.action_decided == sample_query_data['action_decided']
        assert query.created_at is not None
    
    def test_create_query_with_operation_id(self, repository, sample_query_data):
        """Test: Se crea una consulta con operación asociada"""
        sample_query_data['operation_id'] = 42
        query = repository.create_query(**sample_query_data)
        
        assert query.operation_id == 42
    
    def test_create_query_calculates_total_tokens(self, repository, sample_query_data):
        """Test: Los tokens totales se calculan automáticamente"""
        sample_query_data['tokens_input'] = 100
        sample_query_data['tokens_output'] = 50
        
        query = repository.create_query(**sample_query_data)
        
        assert query.tokens_total == 150
    
    def test_create_query_sets_timestamp(self, repository, sample_query_data):
        """Test: Se establece timestamp automáticamente"""
        before = datetime.now()
        query = repository.create_query(**sample_query_data)
        after = datetime.now()
        
        assert query.created_at is not None
        assert before <= query.created_at <= after
    
    def test_create_query_validates_required_fields(self, repository):
        """Test: Valida campos requeridos"""
        with pytest.raises(TypeError):
            repository.create_query()  # Sin parámetros
    
    def test_create_query_validates_tokens_positive(self, repository, sample_query_data):
        """Test: Valida que tokens sean positivos"""
        sample_query_data['tokens_input'] = -10
        
        with pytest.raises(ValueError, match="tokens_input debe ser >= 0"):
            repository.create_query(**sample_query_data)
    
    def test_create_query_validates_cost_positive(self, repository, sample_query_data):
        """Test: Valida que costo sea positivo"""
        sample_query_data['cost_usd'] = -0.5
        
        with pytest.raises(ValueError, match="cost_usd debe ser >= 0"):
            repository.create_query(**sample_query_data)
    
    def test_create_query_validates_bot_id_positive(self, repository, sample_query_data):
        """Test: Valida que bot_id sea positivo"""
        sample_query_data['bot_id'] = 0
        
        with pytest.raises(ValueError, match="bot_id debe ser > 0"):
            repository.create_query(**sample_query_data)


# ==================== TESTS DE CONSULTA ====================

class TestGetQuery:
    """Tests para obtener consultas IA"""
    
    def test_get_query_by_id_success(self, repository, sample_query):
        """Test: Obtiene una consulta por ID"""
        query = repository.get_query_by_id(sample_query.id)
        
        assert query is not None
        assert query.id == sample_query.id
        assert query.bot_id == sample_query.bot_id
        assert query.prompt == sample_query.prompt
    
    def test_get_query_by_id_not_found(self, repository):
        """Test: Retorna None si no encuentra la consulta"""
        query = repository.get_query_by_id(99999)
        
        assert query is None
    
    def test_get_queries_by_operation_id(self, repository, sample_query_data):
        """Test: Obtiene consultas por operation_id"""
        # Crear varias consultas para la misma operación
        sample_query_data['operation_id'] = 100
        query1 = repository.create_query(**sample_query_data)
        
        sample_query_data['query_type'] = QueryType.REEVALUATION
        query2 = repository.create_query(**sample_query_data)
        
        # Consultar
        queries = repository.get_queries_by_operation_id(100)
        
        assert len(queries) == 2
        assert all(q.operation_id == 100 for q in queries)
    
    def test_get_queries_by_bot(self, repository, sample_query_data):
        """Test: Obtiene consultas por bot_id"""
        # Crear consultas para diferentes bots
        sample_query_data['bot_id'] = 1
        repository.create_query(**sample_query_data)
        repository.create_query(**sample_query_data)
        
        sample_query_data['bot_id'] = 2
        repository.create_query(**sample_query_data)
        
        # Consultar bot 1
        queries = repository.get_queries_by_bot(bot_id=1)
        
        assert len(queries) == 2
        assert all(q.bot_id == 1 for q in queries)
    
    def test_get_queries_by_symbol(self, repository, sample_query_data):
        """Test: Obtiene consultas por símbolo"""
        sample_query_data['symbol'] = 'EURUSD'
        repository.create_query(**sample_query_data)
        repository.create_query(**sample_query_data)
        
        sample_query_data['symbol'] = 'GBPUSD'
        repository.create_query(**sample_query_data)
        
        # Consultar EURUSD
        queries = repository.get_queries_by_symbol('EURUSD')
        
        assert len(queries) == 2
        assert all(q.symbol == 'EURUSD' for q in queries)
    
    def test_get_queries_by_type(self, repository, sample_query_data):
        """Test: Obtiene consultas por tipo (evaluación/reevaluación)"""
        sample_query_data['query_type'] = QueryType.EVALUATION
        repository.create_query(**sample_query_data)
        
        sample_query_data['query_type'] = QueryType.REEVALUATION
        repository.create_query(**sample_query_data)
        repository.create_query(**sample_query_data)
        
        # Consultar reevaluaciones
        queries = repository.get_queries_by_type(QueryType.REEVALUATION)
        
        assert len(queries) == 2
        assert all(q.query_type == QueryType.REEVALUATION for q in queries)
    
    def test_get_all_queries(self, repository, sample_query_data):
        """Test: Obtiene todas las consultas"""
        repository.create_query(**sample_query_data)
        repository.create_query(**sample_query_data)
        repository.create_query(**sample_query_data)
        
        queries = repository.get_all_queries()
        
        assert len(queries) == 3
    
    def test_get_queries_sorted_by_timestamp(self, repository, sample_query_data):
        """Test: Las consultas se ordenan por timestamp descendente"""
        query1 = repository.create_query(**sample_query_data)
        query2 = repository.create_query(**sample_query_data)
        query3 = repository.create_query(**sample_query_data)
        
        queries = repository.get_all_queries()
        
        # Más reciente primero
        assert queries[0].id == query3.id
        assert queries[1].id == query2.id
        assert queries[2].id == query1.id


# ==================== TESTS DE ESTADÍSTICAS ====================

class TestStatistics:
    """Tests para estadísticas de consultas IA"""
    
    def test_get_total_cost(self, repository, sample_query_data):
        """Test: Calcula el costo total de consultas"""
        sample_query_data['cost_usd'] = 0.001
        repository.create_query(**sample_query_data)
        
        sample_query_data['cost_usd'] = 0.002
        repository.create_query(**sample_query_data)
        
        sample_query_data['cost_usd'] = 0.003
        repository.create_query(**sample_query_data)
        
        total_cost = repository.get_total_cost()
        
        assert total_cost == pytest.approx(0.006, rel=1e-5)
    
    def test_get_statistics(self, repository, sample_query_data):
        """Test: Calcula estadísticas generales"""
        sample_query_data['cost_usd'] = 0.001
        sample_query_data['tokens_input'] = 100
        sample_query_data['tokens_output'] = 50
        repository.create_query(**sample_query_data)
        
        sample_query_data['cost_usd'] = 0.002
        sample_query_data['tokens_input'] = 200
        sample_query_data['tokens_output'] = 100
        repository.create_query(**sample_query_data)
        
        stats = repository.get_statistics()
        
        assert stats['total_queries'] == 2
        assert stats['total_cost'] == pytest.approx(0.003, rel=1e-5)
        assert stats['total_tokens_input'] == 300
        assert stats['total_tokens_output'] == 150
        assert stats['total_tokens_total'] == 450
    
    def test_get_statistics_empty_database(self, repository):
        """Test: Estadísticas con BD vacía"""
        stats = repository.get_statistics()
        
        assert stats['total_queries'] == 0
        assert stats['total_cost'] == 0.0
        assert stats['total_tokens_input'] == 0
        assert stats['total_tokens_output'] == 0
    
    def test_get_statistics_by_bot(self, repository, sample_query_data):
        """Test: Estadísticas por bot"""
        sample_query_data['bot_id'] = 1
        sample_query_data['cost_usd'] = 0.001
        repository.create_query(**sample_query_data)
        repository.create_query(**sample_query_data)
        
        sample_query_data['bot_id'] = 2
        sample_query_data['cost_usd'] = 0.002
        repository.create_query(**sample_query_data)
        
        stats_bot1 = repository.get_statistics_by_bot(bot_id=1)
        
        assert stats_bot1['total_queries'] == 2
        assert stats_bot1['total_cost'] == pytest.approx(0.002, rel=1e-5)
    
    def test_get_cost_by_query_type(self, repository, sample_query_data):
        """Test: Costo por tipo de consulta"""
        sample_query_data['query_type'] = QueryType.EVALUATION
        sample_query_data['cost_usd'] = 0.005
        repository.create_query(**sample_query_data)
        
        sample_query_data['query_type'] = QueryType.REEVALUATION
        sample_query_data['cost_usd'] = 0.002
        repository.create_query(**sample_query_data)
        repository.create_query(**sample_query_data)
        
        eval_cost = repository.get_cost_by_type(QueryType.EVALUATION)
        reeval_cost = repository.get_cost_by_type(QueryType.REEVALUATION)
        
        assert eval_cost == pytest.approx(0.005, rel=1e-5)
        assert reeval_cost == pytest.approx(0.004, rel=1e-5)


# ==================== TESTS DE ACTUALIZACIÓN ====================

class TestUpdateQuery:
    """Tests para actualización de consultas IA"""
    
    def test_update_operation_id(self, repository, sample_query):
        """Test: Actualiza operation_id de una consulta"""
        # Inicialmente sin operación
        assert sample_query.operation_id is None
        
        # Actualizar
        updated = repository.update_operation_id(sample_query.id, 123)
        
        assert updated.operation_id == 123
        
        # Verificar persistencia
        query = repository.get_query_by_id(sample_query.id)
        assert query.operation_id == 123
    
    def test_update_nonexistent_query(self, repository):
        """Test: Actualizar consulta inexistente lanza error"""
        with pytest.raises(IAQueryRepositoryError, match="no encontrada"):
            repository.update_operation_id(99999, 123)


# ==================== TESTS DE INTEGRACIÓN ====================

class TestIntegration:
    """Tests de integración con escenarios reales"""
    
    def test_complete_evaluation_flow(self, repository):
        """
        Test: Flujo completo de evaluación
        
        Escenario:
          Dado que se envía una consulta a IA
          Cuando se recibe la respuesta
          Entonces se guarda prompt, respuesta, tokens, costo
        """
        # 1. Crear consulta de evaluación
        query = repository.create_query(
            bot_id=1,
            ia_id=1,
            symbol='EURUSD',
            query_type=QueryType.EVALUATION,
            prompt='Analiza EURUSD con indicadores técnicos',
            response='{"decision": "OPERAR", "direction": "BUY"}',
            tokens_input=120,
            tokens_output=60,
            cost_usd=0.0018,
            action_decided='OPERAR',
            operation_id=None
        )
        
        assert query.id is not None
        
        # 2. Si se operó, vincular a operación
        operation_id = 456
        updated_query = repository.update_operation_id(query.id, operation_id)
        
        assert updated_query.operation_id == 456
        
        # 3. Verificar consulta completa
        retrieved = repository.get_query_by_id(query.id)
        assert retrieved.prompt is not None
        assert retrieved.response is not None
        assert retrieved.tokens_total == 180
        assert retrieved.cost_usd > 0
    
    def test_reevaluation_flow(self, repository):
        """
        Test: Flujo de reevaluación
        
        Escenario:
          Dado que existe una operación abierta
          Cuando se reevalúa cada 10 minutos
          Entonces se registran múltiples consultas vinculadas a la operación
        """
        operation_id = 100
        
        # Primera reevaluación
        query1 = repository.create_query(
            bot_id=1,
            ia_id=1,
            symbol='EURUSD',
            query_type=QueryType.REEVALUATION,
            prompt='Reevaluar posición EURUSD - ciclo 1',
            response='{"decision": "MANTENER"}',
            tokens_input=100,
            tokens_output=40,
            cost_usd=0.0014,
            action_decided='MANTENER',
            operation_id=operation_id
        )
        
        # Segunda reevaluación
        query2 = repository.create_query(
            bot_id=1,
            ia_id=1,
            symbol='EURUSD',
            query_type=QueryType.REEVALUATION,
            prompt='Reevaluar posición EURUSD - ciclo 2',
            response='{"decision": "ACTUALIZAR_SL", "new_sl": 1.0820}',
            tokens_input=110,
            tokens_output=50,
            cost_usd=0.0016,
            action_decided='ACTUALIZAR_SL',
            operation_id=operation_id
        )
        
        # Obtener todas las reevaluaciones de la operación
        queries = repository.get_queries_by_operation_id(operation_id)
        
        assert len(queries) == 2
        assert all(q.query_type == QueryType.REEVALUATION for q in queries)
        assert all(q.operation_id == operation_id for q in queries)
    
    def test_cost_tracking_scenario(self, repository):
        """
        Test: Escenario de seguimiento de costos
        
        Escenario:
          Dado múltiples bots operando
          Cuando se consultan estadísticas
          Entonces se obtiene el desglose de costos por bot
        """
        # Bot 1: 3 consultas
        for i in range(3):
            repository.create_query(
                bot_id=1,
                ia_id=1,
                symbol='EURUSD',
                query_type=QueryType.EVALUATION,
                prompt=f'Consulta {i}',
                response='{"decision": "NO_OPERAR"}',
                tokens_input=100,
                tokens_output=50,
                cost_usd=0.0015,
                action_decided='NO_OPERAR'
            )
        
        # Bot 2: 2 consultas
        for i in range(2):
            repository.create_query(
                bot_id=2,
                ia_id=1,
                symbol='GBPUSD',
                query_type=QueryType.EVALUATION,
                prompt=f'Consulta {i}',
                response='{"decision": "OPERAR"}',
                tokens_input=120,
                tokens_output=60,
                cost_usd=0.0018,
                action_decided='OPERAR'
            )
        
        # Estadísticas por bot
        stats_bot1 = repository.get_statistics_by_bot(1)
        stats_bot2 = repository.get_statistics_by_bot(2)
        
        assert stats_bot1['total_queries'] == 3
        assert stats_bot1['total_cost'] == pytest.approx(0.0045, rel=1e-5)
        
        assert stats_bot2['total_queries'] == 2
        assert stats_bot2['total_cost'] == pytest.approx(0.0036, rel=1e-5)
        
        # Costo total
        total = repository.get_total_cost()
        assert total == pytest.approx(0.0081, rel=1e-5)


# ==================== TESTS DE VALIDACIÓN ====================

class TestValidation:
    """Tests de validación de datos"""
    
    def test_validates_query_type_enum(self, repository, sample_query_data):
        """Test: Valida que query_type sea del enum correcto"""
        sample_query_data['query_type'] = "INVALID_TYPE"
        
        with pytest.raises((ValueError, TypeError)):
            repository.create_query(**sample_query_data)
    
    def test_validates_prompt_not_empty(self, repository, sample_query_data):
        """Test: Valida que prompt no esté vacío"""
        sample_query_data['prompt'] = ""
        
        with pytest.raises(ValueError, match="prompt no puede estar vacío"):
            repository.create_query(**sample_query_data)
    
    def test_validates_response_not_empty(self, repository, sample_query_data):
        """Test: Valida que response no esté vacío"""
        sample_query_data['response'] = ""
        
        with pytest.raises(ValueError, match="response no puede estar vacío"):
            repository.create_query(**sample_query_data)
    
    def test_validates_symbol_not_empty(self, repository, sample_query_data):
        """Test: Valida que symbol no esté vacío"""
        sample_query_data['symbol'] = ""
        
        with pytest.raises(ValueError, match="symbol no puede estar vacío"):
            repository.create_query(**sample_query_data)
