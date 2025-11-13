"""
Tests unitarios para MetricsCalculator - T41 Disponibilización de métricas diarias por bot.

Este módulo implementa tests para el cálculo de métricas diarias de trading:
- Winrate (tasa de victorias)
- Profit factor (relación beneficio/riesgo)
- P/L por tipo de orden (Market/Limit)
- Costo IA total

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T41 - Disponibilización de métricas diarias por bot
"""
import pytest
from datetime import datetime, date
from typing import List
from src.core.metrics_calculator import MetricsCalculator, DailyMetrics, Operation


class TestMetricsCalculator:
    """Tests para MetricsCalculator."""

    @pytest.fixture
    def calculator(self):
        """Fixture que proporciona una instancia de MetricsCalculator."""
        return MetricsCalculator()

    @pytest.fixture
    def sample_operations(self):
        """Fixture con operaciones de ejemplo para testing."""
        base_date = date(2025, 11, 13)

        return [
            # Bot 1 - operaciones ganadoras
            Operation("bot_1", "EURUSD", "MARKET", 100.0, 0.05, datetime.combine(base_date, datetime.min.time()), 100001),
            Operation("bot_1", "GBPUSD", "LIMIT", 50.0, 0.03, datetime.combine(base_date, datetime.min.time()), 100001),

            # Bot 1 - operaciones perdedoras
            Operation("bot_1", "EURUSD", "MARKET", -75.0, 0.04, datetime.combine(base_date, datetime.min.time()), 100001),
            Operation("bot_1", "USDJPY", "LIMIT", -25.0, 0.02, datetime.combine(base_date, datetime.min.time()), 100001),

            # Bot 2 - operaciones
            Operation("bot_2", "EURUSD", "MARKET", 200.0, 0.06, datetime.combine(base_date, datetime.min.time()), 100002),
            Operation("bot_2", "GBPUSD", "MARKET", -100.0, 0.05, datetime.combine(base_date, datetime.min.time()), 100002),

            # Operación de otro día (debe ser ignorada)
            Operation("bot_1", "EURUSD", "MARKET", 50.0, 0.03, datetime.combine(date(2025, 11, 12), datetime.min.time()), 100001),
        ]

    def test_calculate_daily_metrics_bot1(self, calculator, sample_operations):
        """Test cálculo de métricas para bot_1."""
        target_date = date(2025, 11, 13)
        metrics = calculator.calculate_daily_metrics(sample_operations, target_date, "bot_1")

        assert metrics.bot_id == "bot_1"
        assert metrics.date == target_date
        assert metrics.total_operations == 4  # 4 operaciones de bot_1 en la fecha
        assert metrics.winning_operations == 2  # 100 + 50 > 0
        assert metrics.losing_operations == 2  # -75 -25 < 0
        assert metrics.winrate == 50.0  # 2/4 * 100
        assert metrics.total_profit == 150.0  # 100 + 50
        assert metrics.total_loss == 100.0  # 75 + 25
        assert metrics.profit_factor == 1.5  # 150 / 100
        assert metrics.market_orders_pl == 25.0  # 100 - 75
        assert metrics.limit_orders_pl == 25.0  # 50 - 25
        assert metrics.total_ia_cost == 0.14  # 0.05 + 0.03 + 0.04 + 0.02

    def test_calculate_daily_metrics_bot2(self, calculator, sample_operations):
        """Test cálculo de métricas para bot_2."""
        target_date = date(2025, 11, 13)
        metrics = calculator.calculate_daily_metrics(sample_operations, target_date, "bot_2")

        assert metrics.bot_id == "bot_2"
        assert metrics.total_operations == 2
        assert metrics.winning_operations == 1
        assert metrics.losing_operations == 1
        assert metrics.winrate == 50.0
        assert metrics.total_profit == 200.0
        assert metrics.total_loss == 100.0
        assert metrics.profit_factor == 2.0
        assert metrics.market_orders_pl == 100.0  # 200 - 100
        assert metrics.limit_orders_pl == 0.0
        assert metrics.total_ia_cost == 0.11

    def test_calculate_daily_metrics_no_operations(self, calculator, sample_operations):
        """Test cuando no hay operaciones para el bot en la fecha."""
        target_date = date(2025, 11, 13)
        metrics = calculator.calculate_daily_metrics(sample_operations, target_date, "bot_3")

        assert metrics.total_operations == 0
        assert metrics.winrate == 0.0
        assert metrics.profit_factor == 0.0
        assert metrics.total_ia_cost == 0.0

    def test_calculate_daily_metrics_all_winners(self, calculator):
        """Test cuando todas las operaciones son ganadoras."""
        operations = [
            Operation("bot_1", "EURUSD", "MARKET", 100.0, 0.05, datetime(2025, 11, 13, 10, 0), 100001),
            Operation("bot_1", "GBPUSD", "LIMIT", 50.0, 0.03, datetime(2025, 11, 13, 11, 0), 100001),
        ]
        target_date = date(2025, 11, 13)
        metrics = calculator.calculate_daily_metrics(operations, target_date, "bot_1")

        assert metrics.total_operations == 2
        assert metrics.winning_operations == 2
        assert metrics.winrate == 100.0
        assert metrics.profit_factor == float('inf')  # No hay pérdidas

    def test_calculate_daily_metrics_all_losers(self, calculator):
        """Test cuando todas las operaciones son perdedoras."""
        operations = [
            Operation("bot_1", "EURUSD", "MARKET", -100.0, 0.05, datetime(2025, 11, 13, 10, 0), 100001),
            Operation("bot_1", "GBPUSD", "LIMIT", -50.0, 0.03, datetime(2025, 11, 13, 11, 0), 100001),
        ]
        target_date = date(2025, 11, 13)
        metrics = calculator.calculate_daily_metrics(operations, target_date, "bot_1")

        assert metrics.total_operations == 2
        assert metrics.winning_operations == 0
        assert metrics.winrate == 0.0
        assert metrics.total_profit == 0.0
        assert metrics.total_loss == 150.0
        assert metrics.profit_factor == 0.0  # No hay ganancias

    def test_calculate_daily_metrics_different_dates_ignored(self, calculator, sample_operations):
        """Test que operaciones de otras fechas son ignoradas."""
        # La operación del día 12 debe ser ignorada
        target_date = date(2025, 11, 13)
        metrics = calculator.calculate_daily_metrics(sample_operations, target_date, "bot_1")

        # Debe incluir solo las 4 operaciones del día 13
        assert metrics.total_operations == 4
        # La operación del día 12 no cuenta
        assert sum(1 for op in sample_operations
                  if op.bot_id == "bot_1" and op.close_time.date() == date(2025, 11, 12)) == 1
        # Pero no está incluida en las métricas del día 13

    def test_calculate_multiple_bots_metrics(self, calculator, sample_operations):
        """Test cálculo de métricas para múltiples bots."""
        target_date = date(2025, 11, 13)
        bot_ids = ["bot_1", "bot_2", "bot_3"]
        metrics_list = calculator.calculate_multiple_bots_metrics(sample_operations, target_date, bot_ids)

        assert len(metrics_list) == 3
        assert metrics_list[0].bot_id == "bot_1"
        assert metrics_list[0].total_operations == 4
        assert metrics_list[1].bot_id == "bot_2"
        assert metrics_list[1].total_operations == 2
        assert metrics_list[2].bot_id == "bot_3"
        assert metrics_list[2].total_operations == 0

    def test_get_metrics_summary(self, calculator):
        """Test generación de resumen legible de métricas."""
        metrics = DailyMetrics(
            bot_id="bot_1",
            date=date(2025, 11, 13),
            total_operations=10,
            winning_operations=6,
            losing_operations=4,
            winrate=60.0,
            total_profit=300.0,
            total_loss=200.0,
            profit_factor=1.5,
            market_orders_pl=150.0,
            limit_orders_pl=-50.0,
            total_ia_cost=1.2345
        )

        summary = calculator.get_metrics_summary(metrics)

        assert summary["bot_id"] == "bot_1"
        assert summary["fecha"] == "2025-11-13"
        assert summary["operaciones_totales"] == 10
        assert summary["winrate"] == "60.0%"
        assert summary["profit_factor"] == "1.50"
        assert summary["costo_ia_total"] == "$1.2345"

    def test_calculate_daily_metrics_invalid_bot_id(self, calculator, sample_operations):
        """Test manejo de bot_id inválido."""
        target_date = date(2025, 11, 13)

        with pytest.raises(Exception):  # MetricsCalculatorError
            calculator.calculate_daily_metrics(sample_operations, target_date, "")

    def test_calculate_daily_metrics_empty_operations_list(self, calculator):
        """Test cálculo con lista de operaciones vacía."""
        target_date = date(2025, 11, 13)
        metrics = calculator.calculate_daily_metrics([], target_date, "bot_1")

        assert metrics.total_operations == 0
        assert metrics.winrate == 0.0
        assert metrics.profit_factor == 0.0

    def test_calculate_daily_metrics_infinite_profit_factor(self, calculator):
        """Test profit factor infinito cuando no hay losses."""
        operations = [
            Operation("bot_1", "EURUSD", "MARKET", 100.0, 0.05, datetime(2025, 11, 13, 10, 0), 100001),
            Operation("bot_1", "GBPUSD", "LIMIT", 50.0, 0.03, datetime(2025, 11, 13, 11, 0), 100001),
        ]
        target_date = date(2025, 11, 13)
        metrics = calculator.calculate_daily_metrics(operations, target_date, "bot_1")

        assert metrics.profit_factor == float('inf')
        summary = calculator.get_metrics_summary(metrics)
        assert summary["profit_factor"] == "∞"