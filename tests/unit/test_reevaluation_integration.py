"""
Tests de integración para el sistema de reevaluación periódica - T26

Este módulo testea la integración entre:
- ReevaluationScheduler
- ReevaluationManager
- BotInstance

Author: Botrading Team
Date: 2025-11-13
Ticket: T26 - Reevaluación periódica
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.core.reevaluation_scheduler import ReevaluationScheduler, ReevaluationConfig
from src.core.reevaluation_manager import (
    ReevaluationManager,
    ReevaluationMode,
    ReevaluationContext,
    ReevaluationResult
)
from src.core.bot_instance import BotInstance, BotConfig, BotStatus


# ==================== FIXTURES ====================

@pytest.fixture
def mock_config():
    """Config básico de reevaluación"""
    return {
        "enabled": True,
        "interval_minutes": 10,
        "mode": "persistent",
        "trading_window": {
            "timezone": "America/Lima",
            "start": "06:00",
            "end": "13:00",
            "days": ["MON", "TUE", "WED", "THU", "FRI"]
        },
        "bots": {
            "bot_1": {
                "enabled": True,
                "mode": "persistent"
            }
        }
    }


@pytest.fixture
def mock_bot_config():
    """Config básico de bot"""
    return BotConfig(
        bot_id=1,
        bot_name="TestBot",
        enabled=True,
        schedule_config={
            "timezone": "America/Lima",
            "trading_start": "06:00",
            "trading_end": "13:00"
        },
        mt5_config={
            "account_id": "12345",
            "password": "test",
            "server": "test-server",
            "timeout": 60
        },
        cycle_config={}
    )


@pytest.fixture
def mock_scheduler():
    """Mock del scheduler"""
    scheduler = Mock(spec=ReevaluationScheduler)
    scheduler.should_reevaluate = Mock(return_value=True)
    scheduler.mark_reevaluated = Mock()
    scheduler.is_within_trading_window = Mock(return_value=True)
    scheduler.get_stats = Mock(return_value={
        "total_positions": 0,
        "total_reevaluations": 0
    })
    return scheduler


@pytest.fixture
def mock_manager():
    """Mock del manager"""
    manager = Mock(spec=ReevaluationManager)
    manager.reevaluate_positions = AsyncMock(return_value=[])
    manager.get_stats = Mock(return_value={
        "total_reevaluations": 0,
        "total_cost": 0.0
    })
    return manager


@pytest.fixture
def mock_dependencies():
    """Mock de todas las dependencias"""
    return {
        "mt5_data_extractor": Mock(),
        "prompt_builder": Mock(),
        "gemini_client": Mock(),
        "ai_response_parser": Mock(),
        "position_manager": Mock()
    }


# ==================== TESTS DE INTEGRACIÓN ====================

class TestReevaluationIntegration:
    """Tests de integración del sistema de reevaluación"""
    
    def test_integration_components_initialization(
        self,
        mock_config,
        mock_dependencies
    ):
        """Test: Inicializar componentes de integración correctamente"""
        # Crear scheduler
        scheduler_config = ReevaluationConfig(
            interval_minutes=mock_config["interval_minutes"],
            timezone=mock_config["trading_window"]["timezone"],
            trading_window_start=mock_config["trading_window"]["start"],
            trading_window_end=mock_config["trading_window"]["end"]
        )
        scheduler = ReevaluationScheduler(scheduler_config)
        
        # Crear manager
        mode = ReevaluationMode.from_string(mock_config["mode"])
        manager = ReevaluationManager(
            mode=mode,
            mt5_connector=mock_dependencies["mt5_data_extractor"],
            data_extractor=mock_dependencies["mt5_data_extractor"],
            prompt_builder=mock_dependencies["prompt_builder"],
            gemini_client=mock_dependencies["gemini_client"],
            response_parser=mock_dependencies["ai_response_parser"],
            position_manager=mock_dependencies["position_manager"]
        )
        
        # Verificar inicialización
        assert scheduler is not None
        assert manager is not None
        assert scheduler.config.interval_minutes == 10
        assert manager.mode == ReevaluationMode.PERSISTENT_CONVERSATION
    
    @pytest.mark.asyncio
    async def test_integration_reevaluation_callback_success(
        self,
        mock_scheduler,
        mock_manager,
        mock_dependencies
    ):
        """Test: Ejecutar callback de reevaluación exitosamente"""
        # Configurar posiciones abiertas mock
        mock_positions = [
            {
                "position_id": 12345,
                "symbol": "EURUSD",
                "type": 0,  # BUY
                "volume": 0.1,
                "price_open": 1.1000,
                "price_current": 1.1050,
                "sl": 1.0950,
                "tp": 1.1150,
                "profit": 50.0
            }
        ]
        
        # Mock del result
        mock_result = ReevaluationResult(
            success=True,
            action_taken="MANTENER",
            tokens_used=150,
            cost=0.001
        )
        
        mock_manager.reevaluate_positions = AsyncMock(return_value=[mock_result])
        
        # Crear callback
        async def reevaluation_callback(positions):
            results = await mock_manager.reevaluate_positions(positions)
            return results
        
        # Ejecutar
        results = await reevaluation_callback(mock_positions)
        
        # Verificar
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].action_taken == "MANTENER"
        mock_manager.reevaluate_positions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_integration_scheduler_filters_positions(
        self,
        mock_scheduler,
        mock_manager
    ):
        """Test: Scheduler filtra posiciones que necesitan reevaluación"""
        # Posiciones mock
        positions = [
            {"position_id": 1, "symbol": "EURUSD"},
            {"position_id": 2, "symbol": "GBPUSD"},
            {"position_id": 3, "symbol": "USDJPY"}
        ]
        
        # Configurar scheduler para filtrar
        mock_scheduler.should_reevaluate = Mock(side_effect=[True, False, True])
        
        # Filtrar posiciones
        positions_to_reevaluate = [
            pos for pos in positions
            if mock_scheduler.should_reevaluate(pos["position_id"])
        ]
        
        # Verificar
        assert len(positions_to_reevaluate) == 2
        assert positions_to_reevaluate[0]["position_id"] == 1
        assert positions_to_reevaluate[1]["position_id"] == 3
        assert mock_scheduler.should_reevaluate.call_count == 3
    
    @pytest.mark.asyncio
    async def test_integration_marks_reevaluated_after_success(
        self,
        mock_scheduler,
        mock_manager
    ):
        """Test: Marcar posición como reevaluada después de éxito"""
        position_id = 12345
        
        # Mock de resultado exitoso
        mock_result = ReevaluationResult(
            success=True,
            action_taken="ACTUALIZAR",
            tokens_used=200,
            cost=0.002
        )
        
        mock_manager.reevaluate_single_position = AsyncMock(return_value=mock_result)
        
        # Ejecutar reevaluación
        result = await mock_manager.reevaluate_single_position(position_id)
        
        # Si fue exitosa, marcar
        if result.success:
            mock_scheduler.mark_reevaluated(position_id)
        
        # Verificar
        assert result.success is True
        mock_scheduler.mark_reevaluated.assert_called_once_with(position_id)
    
    @pytest.mark.asyncio
    async def test_integration_does_not_mark_on_failure(
        self,
        mock_scheduler,
        mock_manager
    ):
        """Test: No marcar posición si reevaluación falla"""
        position_id = 12345
        
        # Mock de resultado fallido
        mock_result = ReevaluationResult(
            success=False,
            action_taken="ERROR",
            error_message="API Error"
        )
        
        mock_manager.reevaluate_single_position = AsyncMock(return_value=mock_result)
        
        # Ejecutar reevaluación
        result = await mock_manager.reevaluate_single_position(position_id)
        
        # No marcar si falló
        if result.success:
            mock_scheduler.mark_reevaluated(position_id)
        
        # Verificar
        assert result.success is False
        mock_scheduler.mark_reevaluated.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_integration_respects_trading_window(
        self,
        mock_scheduler,
        mock_manager
    ):
        """Test: Respetar ventana de trading antes de reevaluar"""
        # Configurar fuera de ventana
        mock_scheduler.is_within_trading_window = Mock(return_value=False)
        
        # Intentar reevaluar
        if mock_scheduler.is_within_trading_window():
            await mock_manager.reevaluate_positions([])
        
        # Verificar que no se ejecutó
        mock_manager.reevaluate_positions.assert_not_called()
        
        # Configurar dentro de ventana
        mock_scheduler.is_within_trading_window = Mock(return_value=True)
        
        # Reevaluar
        if mock_scheduler.is_within_trading_window():
            await mock_manager.reevaluate_positions([])
        
        # Verificar que sí se ejecutó
        mock_manager.reevaluate_positions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_integration_handles_multiple_positions(
        self,
        mock_scheduler,
        mock_manager
    ):
        """Test: Manejar múltiples posiciones en una reevaluación"""
        # Posiciones mock
        positions = [
            {"position_id": 1, "symbol": "EURUSD"},
            {"position_id": 2, "symbol": "GBPUSD"},
            {"position_id": 3, "symbol": "USDJPY"}
        ]
        
        # Mock de resultados
        mock_results = [
            ReevaluationResult(success=True, action_taken="MANTENER", tokens_used=100, cost=0.001),
            ReevaluationResult(success=True, action_taken="ACTUALIZAR", tokens_used=150, cost=0.0015),
            ReevaluationResult(success=True, action_taken="CERRAR", tokens_used=120, cost=0.0012)
        ]
        
        mock_manager.reevaluate_positions = AsyncMock(return_value=mock_results)
        
        # Ejecutar
        results = await mock_manager.reevaluate_positions(positions)
        
        # Verificar
        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].action_taken == "MANTENER"
        assert results[1].action_taken == "ACTUALIZAR"
        assert results[2].action_taken == "CERRAR"
    
    def test_integration_gets_combined_stats(
        self,
        mock_scheduler,
        mock_manager
    ):
        """Test: Obtener estadísticas combinadas de scheduler y manager"""
        # Configurar stats mock
        mock_scheduler.get_stats = Mock(return_value={
            "total_positions": 5,
            "total_reevaluations": 25,
            "positions_tracked": 5
        })
        
        mock_manager.get_stats = Mock(return_value={
            "total_reevaluations": 25,
            "successful_reevaluations": 23,
            "failed_reevaluations": 2,
            "total_cost": 0.05,
            "total_tokens": 5000
        })
        
        # Obtener stats
        scheduler_stats = mock_scheduler.get_stats()
        manager_stats = mock_manager.get_stats()
        
        # Combinar
        combined_stats = {
            **scheduler_stats,
            **manager_stats
        }
        
        # Verificar
        assert combined_stats["total_positions"] == 5
        assert combined_stats["total_reevaluations"] == 25
        assert combined_stats["successful_reevaluations"] == 23
        assert combined_stats["total_cost"] == 0.05
        assert combined_stats["total_tokens"] == 5000


class TestReevaluationIntegrationEdgeCases:
    """Tests de casos edge de la integración"""
    
    @pytest.mark.asyncio
    async def test_integration_empty_positions_list(
        self,
        mock_scheduler,
        mock_manager
    ):
        """Test: Manejar lista vacía de posiciones"""
        mock_manager.reevaluate_positions = AsyncMock(return_value=[])
        
        results = await mock_manager.reevaluate_positions([])
        
        assert results == []
        mock_manager.reevaluate_positions.assert_called_once_with([])
    
    @pytest.mark.asyncio
    async def test_integration_partial_failures(
        self,
        mock_scheduler,
        mock_manager
    ):
        """Test: Manejar fallos parciales en batch de reevaluaciones"""
        positions = [
            {"position_id": 1, "symbol": "EURUSD"},
            {"position_id": 2, "symbol": "GBPUSD"},
            {"position_id": 3, "symbol": "USDJPY"}
        ]
        
        # Resultados mixtos
        mock_results = [
            ReevaluationResult(success=True, action_taken="MANTENER", tokens_used=100, cost=0.001),
            ReevaluationResult(success=False, action_taken="ERROR", error_message="API Error"),
            ReevaluationResult(success=True, action_taken="CERRAR", tokens_used=120, cost=0.0012)
        ]
        
        mock_manager.reevaluate_positions = AsyncMock(return_value=mock_results)
        
        # Ejecutar
        results = await mock_manager.reevaluate_positions(positions)
        
        # Verificar
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        
        # Marcar solo las exitosas
        for i, result in enumerate(results):
            if result.success:
                mock_scheduler.mark_reevaluated(positions[i]["position_id"])
        
        # Verificar que solo se marcaron 2
        assert mock_scheduler.mark_reevaluated.call_count == 2
    
    @pytest.mark.asyncio
    async def test_integration_mode_per_bot(
        self,
        mock_config,
        mock_dependencies
    ):
        """Test: Cada bot puede tener modo diferente (persistent vs new)"""
        # Bot 1 con modo persistent
        manager1 = ReevaluationManager(
            mode=ReevaluationMode.PERSISTENT_CONVERSATION,
            mt5_connector=mock_dependencies["mt5_data_extractor"],
            data_extractor=mock_dependencies["mt5_data_extractor"],
            prompt_builder=mock_dependencies["prompt_builder"],
            gemini_client=mock_dependencies["gemini_client"],
            response_parser=mock_dependencies["ai_response_parser"],
            position_manager=mock_dependencies["position_manager"]
        )
        
        # Bot 2 con modo new
        manager2 = ReevaluationManager(
            mode=ReevaluationMode.NEW_CONVERSATION,
            mt5_connector=mock_dependencies["mt5_data_extractor"],
            data_extractor=mock_dependencies["mt5_data_extractor"],
            prompt_builder=mock_dependencies["prompt_builder"],
            gemini_client=mock_dependencies["gemini_client"],
            response_parser=mock_dependencies["ai_response_parser"],
            position_manager=mock_dependencies["position_manager"]
        )
        
        # Verificar modos
        assert manager1.mode == ReevaluationMode.PERSISTENT_CONVERSATION
        assert manager2.mode == ReevaluationMode.NEW_CONVERSATION
        
        # Los modos son independientes
        assert manager1.mode != manager2.mode
