"""
Tests unitarios para DailyMetricsRepository (T34)

Este módulo prueba la funcionalidad de consolidación de métricas diarias por bot,
incluyendo cálculo de winrate, profit factor, costos IA y estadísticas agregadas.

Autor: Botrading Team
Fecha: 2025-11-15
Ticket: T34 - Issue #50
"""

import unittest
import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
import tempfile
import os
import time
import gc


class TestDailyMetricsRepositoryInitialization(unittest.TestCase):
    """Tests para inicialización del repositorio"""
    
    def setUp(self):
        """Crear BD temporal para cada test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_metrics.db"
    
    def tearDown(self):
        """Limpiar archivos temporales"""
        # Forzar garbage collection para cerrar conexiones
        gc.collect()
        time.sleep(0.1)  # Pequeño delay para Windows
        
        try:
            if self.db_path.exists():
                self.db_path.unlink()
            os.rmdir(self.temp_dir)
        except (PermissionError, OSError):
            # Ignorar en Windows si está bloqueado
            pass
    
    def test_initialization_creates_database_file(self):
        """Test: Inicialización crea archivo de BD"""
        from src.core.daily_metrics_repository import DailyMetricsRepository
        
        repo = DailyMetricsRepository(db_path=self.db_path)
        
        self.assertTrue(self.db_path.exists())
        repo.close()
    
    def test_initialization_creates_table(self):
        """Test: Inicialización crea tabla metricas_diarias"""
        from src.core.daily_metrics_repository import DailyMetricsRepository
        
        repo = DailyMetricsRepository(db_path=self.db_path)
        
        # Verificar que la tabla existe
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='metricas_diarias'
        """)
        result = cursor.fetchone()
        conn.close()
        repo.close()
        
        self.assertIsNotNone(result)
    
    def test_initialization_creates_indexes(self):
        """Test: Inicialización crea índices"""
        from src.core.daily_metrics_repository import DailyMetricsRepository
        
        repo = DailyMetricsRepository(db_path=self.db_path)
        
        # Verificar índices
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name IN ('idx_bot_fecha', 'idx_fecha')
        """)
        indexes = cursor.fetchall()
        conn.close()
        repo.close()
        
        self.assertEqual(len(indexes), 2)


class TestDailyMetricsCreation(unittest.TestCase):
    """Tests para creación de métricas diarias"""
    
    def setUp(self):
        """Configurar repositorio temporal"""
        from src.core.daily_metrics_repository import DailyMetricsRepository
        
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_metrics.db"
        self.repo = DailyMetricsRepository(db_path=self.db_path)
    
    def tearDown(self):
        """Limpiar recursos"""
        self.repo.close()
        
        # Forzar garbage collection para cerrar conexiones
        gc.collect()
        time.sleep(0.1)  # Pequeño delay para Windows
        
        try:
            if self.db_path.exists():
                self.db_path.unlink()
            os.rmdir(self.temp_dir)
        except (PermissionError, OSError):
            # Ignorar en Windows si está bloqueado
            pass
    
    def test_create_daily_metrics_basic(self):
        """Test: Crear métrica diaria básica"""
        today = date.today()
        
        metric = self.repo.create_daily_metrics(
            bot_id=1,
            date=today,
            total_operations=10,
            winning_operations=7,
            losing_operations=3,
            profit_loss_total=500.0,
            profit_loss_market=300.0,
            profit_loss_limit=200.0,
            total_queries=15,
            total_tokens=5000,
            total_ia_cost=2.50
        )
        
        self.assertIsNotNone(metric)
        self.assertIsNotNone(metric.id)
        self.assertEqual(metric.bot_id, 1)
        self.assertEqual(metric.date, today)
        self.assertEqual(metric.total_operations, 10)
        self.assertEqual(metric.winning_operations, 7)
        self.assertEqual(metric.losing_operations, 3)
        self.assertEqual(metric.profit_loss_total, 500.0)
        self.assertEqual(metric.winrate, 70.0)  # 7/10 = 70%
    
    def test_create_metrics_calculates_winrate(self):
        """Test: Cálculo automático de winrate"""
        metric = self.repo.create_daily_metrics(
            bot_id=1,
            date=date.today(),
            total_operations=20,
            winning_operations=15,
            losing_operations=5,
            profit_loss_total=1000.0
        )
        
        # 15/20 = 75%
        self.assertEqual(metric.winrate, 75.0)
    
    def test_create_metrics_calculates_profit_factor(self):
        """Test: Cálculo automático de profit factor"""
        # Necesitamos crear operaciones para calcular profit factor
        # Por ahora, el profit factor se calcula basado en P/L
        metric = self.repo.create_daily_metrics(
            bot_id=1,
            date=date.today(),
            total_operations=10,
            winning_operations=6,
            losing_operations=4,
            profit_loss_total=200.0,
            profit_loss_market=150.0,
            profit_loss_limit=50.0
        )
        
        # Profit factor se calcula como: ganancias_totales / perdidas_totales
        # Será calculado desde las operaciones individuales
        self.assertIsNotNone(metric.profit_factor)
    
    def test_create_metrics_with_zero_operations(self):
        """Test: Crear métricas con cero operaciones"""
        metric = self.repo.create_daily_metrics(
            bot_id=1,
            date=date.today(),
            total_operations=0,
            winning_operations=0,
            losing_operations=0,
            profit_loss_total=0.0
        )
        
        self.assertEqual(metric.winrate, 0.0)
        self.assertEqual(metric.profit_factor, 0.0)
    
    def test_create_metrics_prevents_duplicate_bot_date(self):
        """Test: Prevenir duplicados de bot_id + fecha"""
        today = date.today()
        
        # Primera métrica
        self.repo.create_daily_metrics(
            bot_id=1,
            date=today,
            total_operations=5,
            winning_operations=3,
            losing_operations=2,
            profit_loss_total=100.0
        )
        
        # Intentar crear duplicado (debería fallar o actualizar)
        with self.assertRaises(Exception):
            self.repo.create_daily_metrics(
                bot_id=1,
                date=today,
                total_operations=10,
                winning_operations=5,
                losing_operations=5,
                profit_loss_total=200.0
            )
    
    def test_create_metrics_validates_positive_values(self):
        """Test: Validar valores positivos"""
        with self.assertRaises(ValueError):
            self.repo.create_daily_metrics(
                bot_id=-1,  # Inválido
                date=date.today(),
                total_operations=5,
                winning_operations=3,
                losing_operations=2,
                profit_loss_total=100.0
            )
    
    def test_create_metrics_validates_winning_losing_sum(self):
        """Test: Validar que ganadoras + perdedoras = total"""
        with self.assertRaises(ValueError):
            self.repo.create_daily_metrics(
                bot_id=1,
                date=date.today(),
                total_operations=10,
                winning_operations=7,
                losing_operations=5,  # 7 + 5 = 12 > 10
                profit_loss_total=100.0
            )


class TestDailyMetricsConsolidation(unittest.TestCase):
    """Tests para consolidación de métricas desde operaciones y consultas IA"""
    
    def setUp(self):
        """Configurar repositorios temporales"""
        from src.core.daily_metrics_repository import DailyMetricsRepository
        from src.core.operations_repository import OperationsRepository
        from src.core.ia_query_repository import IAQueryRepository
        
        self.temp_dir = tempfile.mkdtemp()
        self.metrics_db = Path(self.temp_dir) / "metrics.db"
        self.operations_db = Path(self.temp_dir) / "operations.db"
        self.ia_db = Path(self.temp_dir) / "ia_queries.db"
        
        self.metrics_repo = DailyMetricsRepository(db_path=self.metrics_db)
        self.operations_repo = OperationsRepository(db_path=self.operations_db)
        self.ia_repo = IAQueryRepository(db_path=self.ia_db)
    
    def tearDown(self):
        """Limpiar recursos"""
        self.metrics_repo.close()
        self.operations_repo.close()
        self.ia_repo.close()
        
        # Forzar garbage collection para cerrar conexiones
        gc.collect()
        time.sleep(0.1)  # Pequeño delay para Windows
        
        for db in [self.metrics_db, self.operations_db, self.ia_db]:
            try:
                if db.exists():
                    db.unlink()
            except PermissionError:
                # Ignorar en Windows si está bloqueado
                pass
        
        try:
            os.rmdir(self.temp_dir)
        except (OSError, PermissionError):
            pass
    
    def test_consolidate_metrics_from_operations(self):
        """Test: Consolidar métricas desde operaciones"""
        from src.core.operations_repository import OrderType, Direction, OperationStatus
        
        today = date.today()
        bot_id = 1
        
        # Crear operaciones de prueba
        # 3 ganadoras
        for i in range(3):
            op = self.operations_repo.create_operation(
                magic_number=1000 + i,
                bot_id=bot_id,
                ia_id=1,
                order_type=OrderType.MARKET,
                symbol="EURUSD",
                direction=Direction.BUY,
                suggested_price=1.0850,
                actual_entry_price=1.0851,
                stop_loss=1.0800,
                take_profit=1.0950,
                lot_size=0.10,
                risk_percentage=1.0,
                status=OperationStatus.OPEN
            )
            # Cerrar la operación
            if op.id is not None:
                self.operations_repo.close_operation(op.id, profit_loss=100.0)
        
        # 2 perdedoras
        for i in range(2):
            op = self.operations_repo.create_operation(
                magic_number=2000 + i,
                bot_id=bot_id,
                ia_id=1,
                order_type=OrderType.MARKET,
                symbol="GBPUSD",
                direction=Direction.SELL,
                suggested_price=1.2500,
                actual_entry_price=1.2501,
                stop_loss=1.2550,
                take_profit=1.2400,
                lot_size=0.10,
                risk_percentage=1.0,
                status=OperationStatus.OPEN
            )
            # Cerrar la operación
            if op.id is not None:
                self.operations_repo.close_operation(op.id, profit_loss=-50.0)
        
        # Consolidar métricas
        metric = self.metrics_repo.consolidate_metrics_for_date(
            bot_id=bot_id,
            target_date=today,
            operations_repo=self.operations_repo,
            ia_repo=self.ia_repo
        )
        
        self.assertIsNotNone(metric)
        self.assertEqual(metric.total_operations, 5)
        self.assertEqual(metric.winning_operations, 3)
        self.assertEqual(metric.losing_operations, 2)
        self.assertEqual(metric.profit_loss_total, 200.0)  # 300 - 100
        self.assertEqual(metric.winrate, 60.0)  # 3/5 = 60%
    
    def test_consolidate_metrics_includes_ia_costs(self):
        """Test: Consolidar métricas incluye costos de IA"""
        from src.core.ia_query_repository import QueryType
        
        today = date.today()
        bot_id = 1
        
        # Crear consultas IA
        for i in range(5):
            self.ia_repo.create_query(
                bot_id=bot_id,
                ia_id=1,
                symbol="EURUSD",
                query_type=QueryType.EVALUATION,
                prompt=f"Test prompt {i}",
                response='{"decision": "OPERAR"}',
                tokens_input=100,
                tokens_output=50,
                cost_usd=0.50,
                action_decided="OPERAR"
            )
        
        # Consolidar métricas
        metric = self.metrics_repo.consolidate_metrics_for_date(
            bot_id=bot_id,
            target_date=today,
            operations_repo=self.operations_repo,
            ia_repo=self.ia_repo
        )
        
        self.assertEqual(metric.total_queries, 5)
        self.assertEqual(metric.total_tokens, 750)  # 5 * (100 + 50)
        self.assertEqual(metric.total_ia_cost, 2.50)  # 5 * 0.50
    
    def test_consolidate_metrics_separates_market_limit(self):
        """Test: Consolidar métricas separa Market y Limit"""
        from src.core.operations_repository import OrderType, Direction, OperationStatus
        
        today = date.today()
        bot_id = 1
        
        # Operación Market
        op1 = self.operations_repo.create_operation(
            magic_number=1001,
            bot_id=bot_id,
            ia_id=1,
            order_type=OrderType.MARKET,
            symbol="EURUSD",
            direction=Direction.BUY,
            suggested_price=1.0850,
            actual_entry_price=1.0851,
            stop_loss=1.0800,
            take_profit=1.0950,
            lot_size=0.10,
            risk_percentage=1.0,
            status=OperationStatus.OPEN
        )
        if op1.id is not None:
            self.operations_repo.close_operation(op1.id, profit_loss=150.0)
        
        # Operación Limit
        op2 = self.operations_repo.create_operation(
            magic_number=1002,
            bot_id=bot_id,
            ia_id=1,
            order_type=OrderType.LIMIT,
            symbol="EURUSD",
            direction=Direction.BUY,
            suggested_price=1.0850,
            actual_entry_price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0950,
            lot_size=0.10,
            risk_percentage=1.0,
            status=OperationStatus.OPEN
        )
        if op2.id is not None:
            self.operations_repo.close_operation(op2.id, profit_loss=200.0)
        
        # Consolidar
        metric = self.metrics_repo.consolidate_metrics_for_date(
            bot_id=bot_id,
            target_date=today,
            operations_repo=self.operations_repo,
            ia_repo=self.ia_repo
        )
        
        self.assertEqual(metric.profit_loss_market, 150.0)
        self.assertEqual(metric.profit_loss_limit, 200.0)
        self.assertEqual(metric.profit_loss_total, 350.0)


class TestDailyMetricsQueries(unittest.TestCase):
    """Tests para consultas de métricas diarias"""
    
    def setUp(self):
        """Configurar repositorio con datos de prueba"""
        from src.core.daily_metrics_repository import DailyMetricsRepository
        
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_metrics.db"
        self.repo = DailyMetricsRepository(db_path=self.db_path)
        
        # Crear métricas de prueba
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        self.repo.create_daily_metrics(
            bot_id=1, date=today, total_operations=10,
            winning_operations=7, losing_operations=3,
            profit_loss_total=500.0
        )
        
        self.repo.create_daily_metrics(
            bot_id=1, date=yesterday, total_operations=8,
            winning_operations=5, losing_operations=3,
            profit_loss_total=300.0
        )
        
        self.repo.create_daily_metrics(
            bot_id=2, date=today, total_operations=15,
            winning_operations=10, losing_operations=5,
            profit_loss_total=800.0
        )
    
    def tearDown(self):
        """Limpiar recursos"""
        self.repo.close()
        
        # Forzar garbage collection para cerrar conexiones
        gc.collect()
        time.sleep(0.1)  # Pequeño delay para Windows
        
        try:
            if self.db_path.exists():
                self.db_path.unlink()
            os.rmdir(self.temp_dir)
        except (PermissionError, OSError):
            # Ignorar en Windows si está bloqueado
            pass
    
    def test_get_metrics_by_bot_and_date(self):
        """Test: Obtener métricas por bot y fecha"""
        today = date.today()
        
        metric = self.repo.get_metrics_by_bot_and_date(bot_id=1, date=today)
        
        self.assertIsNotNone(metric)
        self.assertEqual(metric.bot_id, 1)
        self.assertEqual(metric.date, today)
        self.assertEqual(metric.total_operations, 10)
    
    def test_get_metrics_by_bot(self):
        """Test: Obtener todas las métricas de un bot"""
        metrics = self.repo.get_metrics_by_bot(bot_id=1)
        
        self.assertEqual(len(metrics), 2)
        self.assertTrue(all(m.bot_id == 1 for m in metrics))
    
    def test_get_metrics_by_date_range(self):
        """Test: Obtener métricas por rango de fechas"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        metrics = self.repo.get_metrics_by_date_range(
            bot_id=1,
            start_date=yesterday,
            end_date=today
        )
        
        self.assertEqual(len(metrics), 2)
    
    def test_get_all_metrics(self):
        """Test: Obtener todas las métricas"""
        metrics = self.repo.get_all_metrics()
        
        self.assertEqual(len(metrics), 3)
    
    def test_get_metrics_returns_none_when_not_found(self):
        """Test: Retorna None cuando no encuentra métricas"""
        future_date = date.today() + timedelta(days=30)
        
        metric = self.repo.get_metrics_by_bot_and_date(
            bot_id=999,
            date=future_date
        )
        
        self.assertIsNone(metric)


class TestDailyMetricsStatistics(unittest.TestCase):
    """Tests para estadísticas agregadas"""
    
    def setUp(self):
        """Configurar repositorio con datos de prueba"""
        from src.core.daily_metrics_repository import DailyMetricsRepository
        
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_metrics.db"
        self.repo = DailyMetricsRepository(db_path=self.db_path)
        
        # Crear métricas de varios días
        today = date.today()
        for i in range(5):
            target_date = today - timedelta(days=i)
            self.repo.create_daily_metrics(
                bot_id=1,
                date=target_date,
                total_operations=10,
                winning_operations=6,
                losing_operations=4,
                profit_loss_total=100.0 * (i + 1),
                total_queries=5,
                total_tokens=1000,
                total_ia_cost=1.0
            )
    
    def tearDown(self):
        """Limpiar recursos"""
        self.repo.close()
        
        # Forzar garbage collection para cerrar conexiones
        gc.collect()
        time.sleep(0.1)  # Pequeño delay para Windows
        
        try:
            if self.db_path.exists():
                self.db_path.unlink()
            os.rmdir(self.temp_dir)
        except (PermissionError, OSError):
            # Ignorar en Windows si está bloqueado
            pass
    
    def test_get_statistics_by_bot(self):
        """Test: Obtener estadísticas agregadas por bot"""
        stats = self.repo.get_statistics_by_bot(bot_id=1)
        
        self.assertIsNotNone(stats)
        self.assertEqual(stats['total_days'], 5)
        self.assertEqual(stats['total_operations'], 50)  # 10 * 5
        self.assertEqual(stats['total_winning'], 30)  # 6 * 5
        self.assertEqual(stats['total_losing'], 20)  # 4 * 5
        self.assertEqual(stats['total_profit_loss'], 1500.0)  # 100+200+300+400+500
        self.assertEqual(stats['average_winrate'], 60.0)
    
    def test_get_total_statistics(self):
        """Test: Obtener estadísticas totales del sistema"""
        stats = self.repo.get_total_statistics()
        
        self.assertIsNotNone(stats)
        self.assertIn('total_bots', stats)
        self.assertIn('total_operations', stats)
        self.assertIn('total_profit_loss', stats)


if __name__ == '__main__':
    unittest.main()
