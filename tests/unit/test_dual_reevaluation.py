"""
Tests para Reevaluación Independiente de Market y Limit - T16
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.core.reevaluation_integration import (
    ReevaluationIntegration,
    IntegrationConfig
)
from src.core.reevaluation_manager import ReevaluationResult


class TestDualReevaluation:
    """Tests para reevaluación independiente de órdenes duales"""

    @pytest.fixture
    def mock_components(self):
        """Fixture con componentes mockeados"""
        return {
            "mt5_connector": Mock(),
            "data_extractor": Mock(),
            "prompt_builder": Mock(),
            "gemini_client": Mock(),
            "response_parser": Mock(),
            "position_manager": Mock()
        }

    @pytest.fixture
    def integration_config(self):
        """Fixture con configuración de integración"""
        return IntegrationConfig(
            enabled=True,
            interval_minutes=10,
            mode="persistent"
        )

    def test_detect_dual_orders_consecutive_magic(self, mock_components, integration_config):
        """Test: Detectar órdenes duales por magic numbers consecutivos"""
        # Configurar posiciones mock
        mock_positions = [
            {"ticket": "12345", "symbol": "EURUSD", "magic": 100000},  # Market
            {"ticket": "12346", "symbol": "EURUSD", "magic": 100001}   # Limit
        ]

        mock_components["position_manager"].get_positions = Mock(return_value=mock_positions)

        # Crear integración
        integration = ReevaluationIntegration(
            bot_id=1,
            bot_name="TestBot",
            magic_number=100000,  # Magic base del bot
            config=integration_config,
            **mock_components
        )

        # Ejecutar detección
        dual_groups = integration._detect_dual_order_groups()

        # Verificar que se detectó el grupo dual
        assert len(dual_groups) == 1
        group = dual_groups[0]
        assert group["market_magic"] == 100000
        assert group["limit_magic"] == 100001
        assert len(group["positions"]) == 2

    def test_detect_dual_orders_no_consecutive(self, mock_components, integration_config):
        """Test: No detectar duales cuando magic numbers no son consecutivos"""
        # Configurar posiciones no consecutivas
        mock_positions = [
            {"ticket": "12345", "symbol": "EURUSD", "magic": 100000},  # Market
            {"ticket": "12346", "symbol": "EURUSD", "magic": 100003}   # No consecutiva
        ]

        mock_components["position_manager"].get_positions = Mock(return_value=mock_positions)

        # Crear integración
        integration = ReevaluationIntegration(
            bot_id=1,
            bot_name="TestBot",
            magic_number=100000,
            config=integration_config,
            **mock_components
        )

        # Ejecutar detección
        dual_groups = integration._detect_dual_order_groups()

        # Verificar que no se detectaron grupos duales
        assert len(dual_groups) == 0

    def test_get_dual_reevaluation_stats(self, mock_components, integration_config):
        """Test: Obtener estadísticas de reevaluación dual"""
        # Crear integración
        integration = ReevaluationIntegration(
            bot_id=1,
            bot_name="TestBot",
            magic_number=100000,
            config=integration_config,
            **mock_components
        )

        # Simular estadísticas
        integration._dual_stats = {
            "total_dual_groups": 5,
            "successful_market_reevaluations": 4,
            "successful_limit_reevaluations": 3,
            "failed_market_reevaluations": 1,
            "failed_limit_reevaluations": 2,
            "total_dual_cost_usd": 0.015,
            "total_dual_tokens": 1200
        }

        # Obtener estadísticas
        stats = integration.get_dual_stats()

        # Verificar estadísticas
        assert stats["total_dual_groups"] == 5
        assert stats["market_success_rate"] == 80.0  # 4/5
        assert stats["limit_success_rate"] == 60.0   # 3/5
        assert stats["overall_success_rate"] == 70.0  # (4+3)/(5+5)
        assert stats["total_dual_cost_usd"] == 0.015
        assert stats["total_dual_tokens"] == 1200

    @pytest.mark.asyncio
    async def test_reevaluate_dual_orders_independently(self, mock_components, integration_config):
        """Test: Reevaluar órdenes duales independientemente"""
        # Configurar posiciones duales
        mock_positions = [
            {"ticket": "12345", "symbol": "EURUSD", "magic": 100000},  # Market
            {"ticket": "12346", "symbol": "EURUSD", "magic": 100001}   # Limit
        ]

        mock_components["position_manager"].get_positions = Mock(return_value=mock_positions)

        # Mock resultados diferentes para Market y Limit
        market_result = ReevaluationResult(
            success=True,
            action_taken="MANTENER",
            reasoning="Condiciones estables para Market",
            tokens_used=150,
            cost=0.001
        )

        limit_result = ReevaluationResult(
            success=True,
            action_taken="CERRAR",
            reasoning="Limit no activada, cerrar",
            tokens_used=120,
            cost=0.0008
        )

        # Mock el manager para devolver resultados diferentes por magic
        async def mock_reevaluate_positions(bot_id, magic_number):
            if magic_number == 100000:  # Market
                return [market_result]
            elif magic_number == 100001:  # Limit
                return [limit_result]
            return []

        # Reemplazar el manager mock con uno que tenga el método async
        mock_manager = Mock()
        mock_manager.reevaluate_positions = mock_reevaluate_positions
        mock_components["position_manager"].reevaluate_positions = mock_reevaluate_positions

        # Crear integración
        integration = ReevaluationIntegration(
            bot_id=1,
            bot_name="TestBot",
            magic_number=100000,
            config=integration_config,
            **mock_components
        )

        # Reemplazar el manager con el mock
        integration.manager = mock_manager

        # Ejecutar reevaluación dual
        results = await integration.reevaluate_dual_orders()

        # Verificar que se reevaluaron ambas órdenes independientemente
        assert len(results) == 2

        # Verificar resultados
        market_found = False
        limit_found = False

        for result in results:
            if result["type"] == "Market":
                assert result["action"] == "MANTENER"
                assert result["magic"] == 100000
                market_found = True
            elif result["type"] == "Limit":
                assert result["action"] == "CERRAR"
                assert result["magic"] == 100001
                limit_found = True

        assert market_found and limit_found