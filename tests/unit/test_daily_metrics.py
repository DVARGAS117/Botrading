"""
Tests unitarios para el módulo daily_metrics.

Este módulo prueba la funcionalidad de cálculo de métricas diarias por bot,
asegurando el cumplimiento del Ticket T41.
"""
import pytest
from unittest.mock import Mock, patch
from src.core.daily_metrics import DailyMetricsCalculator


class TestDailyMetricsCalculator:
    """Tests para la clase DailyMetricsCalculator"""

    def test_calculate_daily_metrics_success(self, tmp_path):
        """
        Test: Debe calcular métricas diarias exitosamente

        Dado que existen operaciones y consultas IA del día para un bot
        Cuando se calcula las métricas diarias
        Entonces debe retornar winrate, profit_factor, pl_by_order_type y total_ia_cost
        """
        # Arrange
        calculator = DailyMetricsCalculator()

        # Mock data for operations
        operations = [
            {"bot_id": 1, "order_type": "Market", "profit": 100.0, "status": "closed"},
            {"bot_id": 1, "order_type": "Market", "profit": -50.0, "status": "closed"},
            {"bot_id": 1, "order_type": "Limit", "profit": 200.0, "status": "closed"},
            {"bot_id": 1, "order_type": "Limit", "profit": -25.0, "status": "closed"},
        ]

        # Mock data for IA queries
        ia_queries = [
            {"bot_id": 1, "cost": 0.1},
            {"bot_id": 1, "cost": 0.15},
        ]

        # Act
        with patch.object(calculator, '_get_operations_for_bot', return_value=operations), \
             patch.object(calculator, '_get_ia_queries_for_bot', return_value=ia_queries):
            result = calculator.calculate_daily_metrics(1)

        # Assert
        assert "winrate" in result
        assert "profit_factor" in result
        assert "pl_by_order_type" in result
        assert "total_ia_cost" in result

        # Winrate: 2 wins out of 4 trades = 0.5
        assert result["winrate"] == 0.5

        # Profit factor: total profit / total loss = (100 + 200) / (50 + 25) = 300 / 75 = 4.0
        assert result["profit_factor"] == 4.0

        # P/L by order type
        assert result["pl_by_order_type"]["Market"] == 50.0  # 100 - 50
        assert result["pl_by_order_type"]["Limit"] == 175.0  # 200 - 25

        # Total IA cost
        assert result["total_ia_cost"] == 0.25

    def test_calculate_daily_metrics_no_operations(self):
        """
        Test: Debe manejar caso sin operaciones

        Dado que no hay operaciones para el bot
        Cuando se calcula las métricas
        Entonces debe retornar métricas con valores por defecto
        """
        # Arrange
        calculator = DailyMetricsCalculator()

        # Act
        with patch.object(calculator, '_get_operations_for_bot', return_value=[]), \
             patch.object(calculator, '_get_ia_queries_for_bot', return_value=[]):
            result = calculator.calculate_daily_metrics(1)

        # Assert
        assert result["winrate"] == 0.0
        assert result["profit_factor"] == 0.0
        assert result["pl_by_order_type"] == {}
        assert result["total_ia_cost"] == 0.0

    def test_calculate_daily_metrics_no_losses(self):
        """
        Test: Debe manejar caso sin pérdidas para profit factor

        Dado que todas las operaciones son ganadoras
        Cuando se calcula profit factor
        Entonces debe retornar infinito o valor alto
        """
        # Arrange
        calculator = DailyMetricsCalculator()
        operations = [
            {"bot_id": 1, "order_type": "Market", "profit": 100.0, "status": "closed"},
            {"bot_id": 1, "order_type": "Limit", "profit": 200.0, "status": "closed"},
        ]

        # Act
        with patch.object(calculator, '_get_operations_for_bot', return_value=operations), \
             patch.object(calculator, '_get_ia_queries_for_bot', return_value=[]):
            result = calculator.calculate_daily_metrics(1)

        # Assert
        assert result["winrate"] == 1.0
        assert result["profit_factor"] == float('inf')  # No losses
        assert result["pl_by_order_type"]["Market"] == 100.0
        assert result["pl_by_order_type"]["Limit"] == 200.0