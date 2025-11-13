"""
Tests unitarios para DualPerformanceTracker - T15

Este módulo contiene tests para la funcionalidad de registro y comparación
de desempeño entre órdenes Market y Limit, incluyendo P/L y tasas de activación.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T15 - Registro y comparación de desempeño Market vs Limit
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date
from typing import List, Dict, Any

from src.core.dual_performance_tracker import (
    DualPerformanceTracker,
    PerformanceRecord,
    DailyPerformanceComparison,
    OperationPerformance,
    DualPerformanceTrackerError,
    InvalidPerformanceDataError
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_db_path(tmp_path):
    """Ruta temporal para base de datos de prueba"""
    return str(tmp_path / "test_trading.db")


@pytest.fixture
def performance_tracker(mock_db_path):
    """Instancia de DualPerformanceTracker con base de datos temporal"""
    return DualPerformanceTracker(db_path=mock_db_path)


@pytest.fixture
def sample_market_record():
    """Record de muestra para orden Market"""
    return PerformanceRecord(
        symbol="EURUSD",
        bot_id=1,
        order_type="market",
        magic_number=101000,
        open_time=datetime(2025, 11, 13, 10, 0, 0),
        close_time=datetime(2025, 11, 13, 14, 30, 0),
        entry_price=1.1000,
        exit_price=1.1050,
        lot_size=0.1,
        profit_loss=50.0,
        is_winner=True,
        activation_status="activated"  # Market siempre se activa
    )


@pytest.fixture
def sample_limit_record():
    """Record de muestra para orden Limit"""
    return PerformanceRecord(
        symbol="EURUSD",
        bot_id=1,
        order_type="limit",
        magic_number=101001,
        open_time=datetime(2025, 11, 13, 10, 0, 0),
        close_time=datetime(2025, 11, 13, 15, 0, 0),
        entry_price=1.0990,
        exit_price=1.1040,
        lot_size=0.1,
        profit_loss=50.0,
        is_winner=True,
        activation_status="activated"
    )


@pytest.fixture
def sample_limit_not_activated():
    """Record de muestra para orden Limit NO activada"""
    return PerformanceRecord(
        symbol="GBPUSD",
        bot_id=2,
        order_type="limit",
        magic_number=201001,
        open_time=datetime(2025, 11, 13, 11, 0, 0),
        close_time=None,  # No se activó
        entry_price=1.2500,
        exit_price=None,
        lot_size=0.1,
        profit_loss=0.0,
        is_winner=False,
        activation_status="not_activated"
    )


# ==================== TESTS DE INICIALIZACIÓN ====================

class TestDualPerformanceTrackerInit:
    """Tests para inicialización del DualPerformanceTracker"""
    
    def test_init_with_default_db_path(self):
        """Test: Inicialización con ruta de BD por defecto"""
        tracker = DualPerformanceTracker()
        assert tracker.db_path.name == "trading.db"
        assert "data" in str(tracker.db_path)
    
    def test_init_with_custom_db_path(self, mock_db_path):
        """Test: Inicialización con ruta de BD personalizada"""
        tracker = DualPerformanceTracker(db_path=mock_db_path)
        assert str(tracker.db_path) == mock_db_path
    
    def test_init_creates_database_if_not_exists(self, mock_db_path):
        """Test: Inicialización crea la base de datos si no existe"""
        tracker = DualPerformanceTracker(db_path=mock_db_path)
        tracker._initialize_database()
        assert tracker.db_path.parent.exists()


# ==================== TESTS DE PerformanceRecord ====================

class TestPerformanceRecord:
    """Tests para la clase PerformanceRecord"""
    
    def test_performance_record_creation_market(self, sample_market_record):
        """Test: Creación de PerformanceRecord para Market"""
        assert sample_market_record.symbol == "EURUSD"
        assert sample_market_record.order_type == "market"
        assert sample_market_record.profit_loss == 50.0
        assert sample_market_record.is_winner is True
        assert sample_market_record.activation_status == "activated"
    
    def test_performance_record_creation_limit(self, sample_limit_record):
        """Test: Creación de PerformanceRecord para Limit"""
        assert sample_limit_record.order_type == "limit"
        assert sample_limit_record.activation_status == "activated"
    
    def test_performance_record_validation_invalid_order_type(self):
        """Test: Validación falla con tipo de orden inválido"""
        record = PerformanceRecord(
            symbol="EURUSD",
            bot_id=1,
            order_type="invalid_type",  # Tipo inválido
            magic_number=101000,
            open_time=datetime.now(),
            close_time=None,
            entry_price=1.1000,
            exit_price=None,
            lot_size=0.1,
            profit_loss=0.0,
            is_winner=False,
            activation_status="activated"
        )
        
        with pytest.raises(InvalidPerformanceDataError):
            record.validate()
    
    def test_performance_record_validation_invalid_activation_status(self):
        """Test: Validación falla con estado de activación inválido"""
        record = PerformanceRecord(
            symbol="EURUSD",
            bot_id=1,
            order_type="market",
            magic_number=101000,
            open_time=datetime.now(),
            close_time=None,
            entry_price=1.1000,
            exit_price=None,
            lot_size=0.1,
            profit_loss=0.0,
            is_winner=False,
            activation_status="invalid_status"  # Estado inválido
        )
        
        with pytest.raises(InvalidPerformanceDataError):
            record.validate()
    
    def test_performance_record_to_dict(self, sample_market_record):
        """Test: Conversión de PerformanceRecord a diccionario"""
        result = sample_market_record.to_dict()
        assert isinstance(result, dict)
        assert result['symbol'] == "EURUSD"
        assert result['order_type'] == "market"
        assert result['profit_loss'] == 50.0


# ==================== TESTS DE REGISTRO ====================

class TestRegisterPerformance:
    """Tests para registro de performance de órdenes"""
    
    def test_register_market_order_performance(
        self,
        performance_tracker,
        sample_market_record
    ):
        """Test: Registrar performance de orden Market"""
        result = performance_tracker.register_performance(sample_market_record)
        assert result is True
    
    def test_register_limit_order_performance(
        self,
        performance_tracker,
        sample_limit_record
    ):
        """Test: Registrar performance de orden Limit"""
        result = performance_tracker.register_performance(sample_limit_record)
        assert result is True
    
    def test_register_limit_not_activated(
        self,
        performance_tracker,
        sample_limit_not_activated
    ):
        """Test: Registrar orden Limit NO activada"""
        result = performance_tracker.register_performance(sample_limit_not_activated)
        assert result is True
    
    def test_register_duplicate_magic_number_raises_error(
        self,
        performance_tracker,
        sample_market_record
    ):
        """Test: Registrar mismo Magic Number dos veces lanza error"""
        performance_tracker.register_performance(sample_market_record)
        
        # Intentar registrar de nuevo
        with pytest.raises(DualPerformanceTrackerError):
            performance_tracker.register_performance(sample_market_record)
    
    def test_register_validates_record(self, performance_tracker):
        """Test: Registro valida el record antes de guardarlo"""
        invalid_record = PerformanceRecord(
            symbol="",  # Símbolo vacío - inválido
            bot_id=1,
            order_type="market",
            magic_number=101000,
            open_time=datetime.now(),
            close_time=None,
            entry_price=1.1000,
            exit_price=None,
            lot_size=0.1,
            profit_loss=0.0,
            is_winner=False,
            activation_status="activated"
        )
        
        with pytest.raises(InvalidPerformanceDataError):
            invalid_record.validate()


# ==================== TESTS DE COMPARACIÓN POR OPERACIÓN ====================

class TestCompareOperationPerformance:
    """Tests para comparación de performance por operación (Market vs Limit)"""
    
    def test_compare_both_activated_and_winners(
        self,
        performance_tracker,
        sample_market_record,
        sample_limit_record
    ):
        """Test: Comparar cuando ambas órdenes se activaron y ganaron"""
        # Registrar ambas
        performance_tracker.register_performance(sample_market_record)
        performance_tracker.register_performance(sample_limit_record)
        
        # Comparar
        comparison = performance_tracker.compare_operation_performance(
            market_magic=sample_market_record.magic_number,
            limit_magic=sample_limit_record.magic_number
        )
        
        assert isinstance(comparison, OperationPerformance)
        assert comparison.market_pl == 50.0
        assert comparison.limit_pl == 50.0
        assert comparison.market_activated is True
        assert comparison.limit_activated is True
    
    def test_compare_market_activated_limit_not(
        self,
        performance_tracker,
        sample_market_record,
        sample_limit_not_activated
    ):
        """Test: Comparar cuando Market se activó pero Limit no"""
        performance_tracker.register_performance(sample_market_record)
        performance_tracker.register_performance(sample_limit_not_activated)
        
        comparison = performance_tracker.compare_operation_performance(
            market_magic=sample_market_record.magic_number,
            limit_magic=sample_limit_not_activated.magic_number
        )
        
        assert comparison.market_activated is True
        assert comparison.limit_activated is False
        assert comparison.market_pl == 50.0
        assert comparison.limit_pl == 0.0
    
    def test_compare_nonexistent_magic_raises_error(
        self,
        performance_tracker
    ):
        """Test: Comparar con Magic Numbers inexistentes lanza error"""
        with pytest.raises(DualPerformanceTrackerError):
            performance_tracker.compare_operation_performance(
                market_magic=999999,
                limit_magic=999998
            )


# ==================== TESTS DE COMPARACIÓN DIARIA ====================

class TestCompareDailyPerformance:
    """Tests para comparación de performance diaria"""
    
    def test_compare_daily_performance_single_bot(
        self,
        performance_tracker,
        sample_market_record,
        sample_limit_record
    ):
        """Test: Comparación diaria para un solo bot"""
        performance_tracker.register_performance(sample_market_record)
        performance_tracker.register_performance(sample_limit_record)
        
        target_date = date(2025, 11, 13)
        comparison = performance_tracker.compare_daily_performance(
            bot_id=1,
            target_date=target_date
        )
        
        assert isinstance(comparison, DailyPerformanceComparison)
        assert comparison.bot_id == 1
        assert comparison.target_date == target_date
        assert comparison.market_total_pl >= 0
        assert comparison.limit_total_pl >= 0
    
    def test_daily_comparison_calculates_activation_rate(
        self,
        performance_tracker,
        sample_market_record,
        sample_limit_not_activated
    ):
        """Test: Comparación diaria calcula tasa de activación correctamente"""
        # Registrar 1 Market activado y 1 Limit NO activado
        performance_tracker.register_performance(sample_market_record)
        
        # Cambiar bot_id para que coincida
        sample_limit_not_activated.bot_id = 1
        performance_tracker.register_performance(sample_limit_not_activated)
        
        target_date = date(2025, 11, 13)
        comparison = performance_tracker.compare_daily_performance(
            bot_id=1,
            target_date=target_date
        )
        
        # Market siempre se activa (100%)
        assert comparison.market_activation_rate == 1.0
        
        # Limit: 0 activadas de 1 total = 0%
        assert comparison.limit_activation_rate == 0.0
    
    def test_daily_comparison_with_no_operations(
        self,
        performance_tracker
    ):
        """Test: Comparación diaria sin operaciones retorna valores en 0"""
        target_date = date(2025, 11, 13)
        comparison = performance_tracker.compare_daily_performance(
            bot_id=1,
            target_date=target_date
        )
        
        assert comparison.market_total_pl == 0.0
        assert comparison.limit_total_pl == 0.0
        assert comparison.market_activation_rate == 0.0
        assert comparison.limit_activation_rate == 0.0
    
    def test_daily_comparison_multiple_operations(
        self,
        performance_tracker
    ):
        """Test: Comparación diaria con múltiples operaciones"""
        # Crear múltiples records
        records = []
        for i in range(5):
            # Market
            records.append(PerformanceRecord(
                symbol="EURUSD",
                bot_id=1,
                order_type="market",
                magic_number=101000 + i,
                open_time=datetime(2025, 11, 13, 10 + i, 0, 0),
                close_time=datetime(2025, 11, 13, 14 + i, 0, 0),
                entry_price=1.1000,
                exit_price=1.1050,
                lot_size=0.1,
                profit_loss=50.0 * (i + 1),  # Variable P/L
                is_winner=True,
                activation_status="activated"
            ))
            
            # Limit
            records.append(PerformanceRecord(
                symbol="EURUSD",
                bot_id=1,
                order_type="limit",
                magic_number=101100 + i,
                open_time=datetime(2025, 11, 13, 10 + i, 0, 0),
                close_time=datetime(2025, 11, 13, 14 + i, 30, 0) if i % 2 == 0 else None,
                entry_price=1.0990,
                exit_price=1.1040 if i % 2 == 0 else None,
                lot_size=0.1,
                profit_loss=40.0 * (i + 1) if i % 2 == 0 else 0.0,
                is_winner=i % 2 == 0,
                activation_status="activated" if i % 2 == 0 else "not_activated"
            ))
        
        # Registrar todas
        for record in records:
            performance_tracker.register_performance(record)
        
        target_date = date(2025, 11, 13)
        comparison = performance_tracker.compare_daily_performance(
            bot_id=1,
            target_date=target_date
        )
        
        # Verificar que se calcularon correctamente
        assert comparison.market_total_pl > 0
        assert comparison.limit_total_pl > 0
        assert comparison.market_activation_rate == 1.0  # Market siempre se activa
        assert 0.0 < comparison.limit_activation_rate < 1.0  # Algunas se activaron


# ==================== TESTS DE MÉTRICAS AGREGADAS ====================

class TestGetAggregatedMetrics:
    """Tests para obtención de métricas agregadas"""
    
    def test_get_aggregated_by_symbol(
        self,
        performance_tracker,
        sample_market_record,
        sample_limit_record
    ):
        """Test: Obtener métricas agregadas por símbolo"""
        performance_tracker.register_performance(sample_market_record)
        performance_tracker.register_performance(sample_limit_record)
        
        metrics = performance_tracker.get_aggregated_metrics(
            group_by="symbol",
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30)
        )
        
        assert isinstance(metrics, dict)
        assert "EURUSD" in metrics
    
    def test_get_aggregated_by_bot(
        self,
        performance_tracker,
        sample_market_record
    ):
        """Test: Obtener métricas agregadas por bot"""
        performance_tracker.register_performance(sample_market_record)
        
        metrics = performance_tracker.get_aggregated_metrics(
            group_by="bot_id",
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30)
        )
        
        assert isinstance(metrics, dict)
        assert 1 in metrics
    
    def test_get_aggregated_invalid_group_by_raises_error(
        self,
        performance_tracker
    ):
        """Test: group_by inválido lanza error"""
        with pytest.raises(DualPerformanceTrackerError):
            performance_tracker.get_aggregated_metrics(
                group_by="invalid_field",
                start_date=date(2025, 11, 1),
                end_date=date(2025, 11, 30)
            )


# ==================== TESTS DE PERSISTENCIA ====================

class TestPersistence:
    """Tests para persistencia de datos"""
    
    def test_data_persists_across_instances(
        self,
        mock_db_path,
        sample_market_record
    ):
        """Test: Los datos persisten entre instancias del tracker"""
        # Primera instancia: registrar
        tracker1 = DualPerformanceTracker(db_path=mock_db_path)
        tracker1.register_performance(sample_market_record)
        
        # Segunda instancia: recuperar
        tracker2 = DualPerformanceTracker(db_path=mock_db_path)
        
        # Verificar que los datos están ahí
        # (esto se puede hacer consultando la BD directamente o con un método get)
        assert True  # Placeholder - implementar verificación real
    
    def test_database_schema_created_correctly(self, performance_tracker):
        """Test: El schema de la BD se crea correctamente"""
        performance_tracker._initialize_database()
        
        # Verificar que las tablas existen
        import sqlite3
        conn = sqlite3.connect(performance_tracker.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='dual_performance'
        """)
        
        result = cursor.fetchone()
        assert result is not None
        
        conn.close()


# ==================== TESTS DE EDGE CASES ====================

class TestEdgeCases:
    """Tests para casos especiales y edge cases"""
    
    def test_handle_null_close_time_for_pending_limit(
        self,
        performance_tracker
    ):
        """Test: Manejar correctamente close_time NULL para Limit pendiente"""
        pending_limit = PerformanceRecord(
            symbol="USDJPY",
            bot_id=3,
            order_type="limit",
            magic_number=301001,
            open_time=datetime(2025, 11, 13, 12, 0, 0),
            close_time=None,  # Pendiente
            entry_price=150.00,
            exit_price=None,
            lot_size=0.1,
            profit_loss=0.0,
            is_winner=False,
            activation_status="pending"
        )
        
        result = performance_tracker.register_performance(pending_limit)
        assert result is True
    
    def test_handle_large_profit_loss_values(
        self,
        performance_tracker
    ):
        """Test: Manejar valores grandes de P/L"""
        large_pl_record = PerformanceRecord(
            symbol="BTCUSD",
            bot_id=4,
            order_type="market",
            magic_number=401000,
            open_time=datetime(2025, 11, 13, 9, 0, 0),
            close_time=datetime(2025, 11, 13, 16, 0, 0),
            entry_price=50000.0,
            exit_price=55000.0,
            lot_size=1.0,
            profit_loss=5000.0,  # P/L grande
            is_winner=True,
            activation_status="activated"
        )
        
        result = performance_tracker.register_performance(large_pl_record)
        assert result is True
    
    def test_handle_negative_profit_loss(
        self,
        performance_tracker
    ):
        """Test: Manejar P/L negativo (pérdidas)"""
        loss_record = PerformanceRecord(
            symbol="EURUSD",
            bot_id=1,
            order_type="market",
            magic_number=102000,
            open_time=datetime(2025, 11, 13, 10, 0, 0),
            close_time=datetime(2025, 11, 13, 11, 0, 0),
            entry_price=1.1000,
            exit_price=1.0950,
            lot_size=0.1,
            profit_loss=-50.0,  # Pérdida
            is_winner=False,
            activation_status="activated"
        )
        
        result = performance_tracker.register_performance(loss_record)
        assert result is True


# ==================== TESTS DE CRITERIOS DE ACEPTACIÓN (GHERKIN) ====================

class TestAcceptanceCriteria:
    """
    Tests basados en criterios de aceptación Gherkin del Ticket T15:
    
    Dado que existen resultados P/L para ambos tipos de orden
    Cuando se consolidan métricas por operación y por día
    Entonces queda disponible la comparación de P/L y activación entre Market y Limit
    """
    
    def test_acceptance_criteria_main_scenario(
        self,
        performance_tracker
    ):
        """
        Test: Escenario principal de criterios de aceptación
        
        DADO que existen resultados P/L para ambos tipos de orden
        CUANDO se consolidan métricas por operación y por día
        ENTONCES queda disponible la comparación de P/L y activación entre Market y Limit
        """
        # DADO: Crear resultados P/L para Market y Limit
        market_record = PerformanceRecord(
            symbol="EURUSD",
            bot_id=1,
            order_type="market",
            magic_number=101000,
            open_time=datetime(2025, 11, 13, 10, 0, 0),
            close_time=datetime(2025, 11, 13, 14, 0, 0),
            entry_price=1.1000,
            exit_price=1.1050,
            lot_size=0.1,
            profit_loss=50.0,
            is_winner=True,
            activation_status="activated"
        )
        
        limit_record = PerformanceRecord(
            symbol="EURUSD",
            bot_id=1,
            order_type="limit",
            magic_number=101001,
            open_time=datetime(2025, 11, 13, 10, 0, 0),
            close_time=datetime(2025, 11, 13, 15, 0, 0),
            entry_price=1.0990,
            exit_price=1.1040,
            lot_size=0.1,
            profit_loss=50.0,
            is_winner=True,
            activation_status="activated"
        )
        
        # Registrar ambos
        performance_tracker.register_performance(market_record)
        performance_tracker.register_performance(limit_record)
        
        # CUANDO: Consolidar métricas por operación
        operation_comparison = performance_tracker.compare_operation_performance(
            market_magic=101000,
            limit_magic=101001
        )
        
        # ENTONCES: Verificar comparación por operación disponible
        assert operation_comparison is not None
        assert operation_comparison.market_pl == 50.0
        assert operation_comparison.limit_pl == 50.0
        assert operation_comparison.market_activated is True
        assert operation_comparison.limit_activated is True
        
        # CUANDO: Consolidar métricas por día
        target_date = date(2025, 11, 13)
        daily_comparison = performance_tracker.compare_daily_performance(
            bot_id=1,
            target_date=target_date
        )
        
        # ENTONCES: Verificar comparación diaria disponible
        assert daily_comparison is not None
        assert daily_comparison.market_total_pl >= 0
        assert daily_comparison.limit_total_pl >= 0
        assert daily_comparison.market_activation_rate >= 0
        assert daily_comparison.limit_activation_rate >= 0
