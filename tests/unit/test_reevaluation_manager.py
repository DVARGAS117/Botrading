"""
Tests unitarios para ReevaluationManager (T26)

Este módulo contiene tests para el manager que coordina el proceso
completo de reevaluación de posiciones.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import List

from src.core.reevaluation_manager import (
    ReevaluationManager,
    ReevaluationMode,
    ReevaluationContext,
    ReevaluationResult,
    ReevaluationManagerError
)
from src.core.ai_response_parser import AIDecisionType


class TestReevaluationMode:
    """Tests para el enum ReevaluationMode"""
    
    def test_persistent_mode(self):
        """Debe tener modo PERSISTENT_CONVERSATION"""
        assert ReevaluationMode.PERSISTENT_CONVERSATION.value == "persistent"
    
    def test_new_mode(self):
        """Debe tener modo NEW_CONVERSATION"""
        assert ReevaluationMode.NEW_CONVERSATION.value == "new"
    
    def test_from_string_persistent(self):
        """Debe convertir string a enum (persistent)"""
        mode = ReevaluationMode.from_string("persistent")
        assert mode == ReevaluationMode.PERSISTENT_CONVERSATION
    
    def test_from_string_new(self):
        """Debe convertir string a enum (new)"""
        mode = ReevaluationMode.from_string("new")
        assert mode == ReevaluationMode.NEW_CONVERSATION
    
    def test_from_string_invalid(self):
        """Debe fallar con string inválido"""
        with pytest.raises(ValueError):
            ReevaluationMode.from_string("invalid")


class TestReevaluationContext:
    """Tests para el dataclass ReevaluationContext"""
    
    def test_create_context(self):
        """Debe crear contexto correctamente"""
        context = ReevaluationContext(
            position_id="test_123",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2450,
            profit_pips=50.0
        )
        
        assert context.position_id == "test_123"
        assert context.symbol == "EURUSD"
        assert context.magic_number == 100101
        assert context.direction == "BUY"
        assert context.entry_price == 1.2400
        assert context.current_sl == 1.2350
        assert context.current_tp == 1.2550
        assert context.current_price == 1.2450
        assert context.profit_pips == 50.0
        assert context.conversation_id is None
        assert context.reevaluation_count == 0
    
    def test_context_with_conversation(self):
        """Debe soportar conversation_id"""
        context = ReevaluationContext(
            position_id="test_123",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2450,
            profit_pips=50.0,
            conversation_id="conv_abc123",
            reevaluation_count=3
        )
        
        assert context.conversation_id == "conv_abc123"
        assert context.reevaluation_count == 3


class TestReevaluationResult:
    """Tests para el dataclass ReevaluationResult"""
    
    def test_create_success_result(self):
        """Debe crear resultado exitoso"""
        result = ReevaluationResult(
            success=True,
            action_taken="MANTENER",
            reasoning="Todo va bien",
            tokens_used=150,
            cost=0.0015
        )
        
        assert result.success is True
        assert result.action_taken == "MANTENER"
        assert result.reasoning == "Todo va bien"
        assert result.tokens_used == 150
        assert result.cost == 0.0015
        assert result.new_sl is None
        assert result.new_tp is None
    
    def test_create_update_result(self):
        """Debe crear resultado de actualización"""
        result = ReevaluationResult(
            success=True,
            action_taken="ACTUALIZAR",
            new_sl=1.2420,
            new_tp=1.2600,
            reasoning="Trailing stop",
            tokens_used=200,
            cost=0.002
        )
        
        assert result.success is True
        assert result.action_taken == "ACTUALIZAR"
        assert result.new_sl == 1.2420
        assert result.new_tp == 1.2600
    
    def test_create_error_result(self):
        """Debe crear resultado de error"""
        result = ReevaluationResult(
            success=False,
            action_taken="ERROR",
            error_message="API timeout"
        )
        
        assert result.success is False
        assert result.error_message == "API timeout"


class TestReevaluationManager:
    """Tests para el ReevaluationManager"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Crea mocks de todas las dependencias"""
        return {
            'mt5_connector': Mock(),
            'data_extractor': Mock(),
            'prompt_builder': Mock(),
            'gemini_client': AsyncMock(),
            'response_parser': Mock(),
            'position_manager': Mock()
        }
    
    @pytest.fixture
    def manager_persistent(self, mock_dependencies):
        """Manager con modo persistente"""
        return ReevaluationManager(
            **mock_dependencies,
            mode=ReevaluationMode.PERSISTENT_CONVERSATION
        )
    
    @pytest.fixture
    def manager_new(self, mock_dependencies):
        """Manager con modo nueva conversación"""
        return ReevaluationManager(
            **mock_dependencies,
            mode=ReevaluationMode.NEW_CONVERSATION
        )
    
    def test_init_persistent_mode(self, manager_persistent):
        """Debe inicializar en modo persistente"""
        assert manager_persistent.mode == ReevaluationMode.PERSISTENT_CONVERSATION
        assert manager_persistent.conversation_sessions == {}
    
    def test_init_new_mode(self, manager_new):
        """Debe inicializar en modo nueva conversación"""
        assert manager_new.mode == ReevaluationMode.NEW_CONVERSATION
    
    @pytest.mark.asyncio
    async def test_reevaluate_single_position_maintain(self, manager_persistent, mock_dependencies):
        """Debe manejar decisión MANTENER correctamente"""
        # Preparar contexto
        context = ReevaluationContext(
            position_id="test_1",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2450,
            profit_pips=50.0
        )
        
        # Mock de extracción de datos
        mock_dependencies['data_extractor'].extract_current_data.return_value = {
            'price': 1.2450,
            'indicators': {'rsi': 55.0, 'ema_20': 1.2445}
        }
        
        # Mock de construcción de prompt
        mock_dependencies['prompt_builder'].build_reevaluation_prompt.return_value = "Test prompt"
        
        # Mock de respuesta de IA
        mock_dependencies['gemini_client'].send_prompt.return_value = Mock(
            success=True,
            content='{"accion": "MANTENER", "razonamiento": "Todo bien"}',
            tokens_input=100,
            tokens_output=50,
            cost=0.0015
        )
        
        # Mock de parser
        parsed_decision = Mock()
        parsed_decision.is_valid = True
        parsed_decision.decision_type = AIDecisionType.MANTENER
        parsed_decision.reasoning = "Todo bien"
        parsed_decision.new_stop_loss = None
        parsed_decision.new_take_profit = None
        mock_dependencies['response_parser'].parse_reevaluation.return_value = parsed_decision
        
        # Ejecutar
        result = await manager_persistent.reevaluate_single_position(context)
        
        # Verificar
        assert result.success is True
        assert result.action_taken == "MANTENER"
        assert result.reasoning == "Todo bien"
        assert result.tokens_used == 150
        assert result.cost == 0.0015
        assert result.new_sl is None
        assert result.new_tp is None
        
        # Verificar que NO se llamó a position_manager
        mock_dependencies['position_manager'].modify_position.assert_not_called()
        mock_dependencies['position_manager'].close_position.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reevaluate_single_position_update_sl(self, manager_persistent, mock_dependencies):
        """Debe ejecutar actualización de SL en MT5"""
        context = ReevaluationContext(
            position_id="test_2",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2480,
            profit_pips=80.0
        )
        
        # Mock de datos
        mock_dependencies['data_extractor'].extract_current_data.return_value = {
            'price': 1.2480,
            'indicators': {'rsi': 65.0}
        }
        
        mock_dependencies['prompt_builder'].build_reevaluation_prompt.return_value = "Test prompt"
        
        mock_dependencies['gemini_client'].send_prompt.return_value = Mock(
            success=True,
            content='{"accion": "ACTUALIZAR", "nuevo_stop_loss": 1.2420}',
            tokens_input=100,
            tokens_output=60,
            cost=0.0016
        )
        
        # Mock de parser
        parsed_decision = Mock()
        parsed_decision.is_valid = True
        parsed_decision.decision_type = AIDecisionType.ACTUALIZAR
        parsed_decision.new_stop_loss = 1.2420
        parsed_decision.new_take_profit = None
        parsed_decision.reasoning = "Trailing stop"
        mock_dependencies['response_parser'].parse_reevaluation.return_value = parsed_decision
        
        # Mock de modificación exitosa
        mock_dependencies['position_manager'].modify_position.return_value = True
        
        # Ejecutar
        result = await manager_persistent.reevaluate_single_position(context)
        
        # Verificar
        assert result.success is True
        assert result.action_taken == "ACTUALIZAR"
        assert result.new_sl == 1.2420
        assert result.new_tp is None
        
        # Verificar que se llamó a modify_position
        mock_dependencies['position_manager'].modify_position.assert_called_once()
        call_kwargs = mock_dependencies['position_manager'].modify_position.call_args[1]
        assert call_kwargs['new_sl'] == 1.2420
    
    @pytest.mark.asyncio
    async def test_reevaluate_single_position_update_both(self, manager_persistent, mock_dependencies):
        """Debe actualizar SL y TP simultáneamente"""
        context = ReevaluationContext(
            position_id="test_3",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2480,
            profit_pips=80.0
        )
        
        mock_dependencies['data_extractor'].extract_current_data.return_value = {'price': 1.2480}
        mock_dependencies['prompt_builder'].build_reevaluation_prompt.return_value = "Test prompt"
        mock_dependencies['gemini_client'].send_prompt.return_value = Mock(
            success=True,
            content='{"accion": "ACTUALIZAR"}',
            tokens_input=100,
            tokens_output=70,
            cost=0.0017
        )
        
        parsed_decision = Mock()
        parsed_decision.is_valid = True
        parsed_decision.decision_type = AIDecisionType.ACTUALIZAR
        parsed_decision.new_stop_loss = 1.2420
        parsed_decision.new_take_profit = 1.2600
        parsed_decision.reasoning = "Trailing stop + TP"
        mock_dependencies['response_parser'].parse_reevaluation.return_value = parsed_decision
        
        mock_dependencies['position_manager'].modify_position.return_value = True
        
        result = await manager_persistent.reevaluate_single_position(context)
        
        assert result.success is True
        assert result.action_taken == "ACTUALIZAR"
        assert result.new_sl == 1.2420
        assert result.new_tp == 1.2600
    
    @pytest.mark.asyncio
    async def test_reevaluate_single_position_close(self, manager_persistent, mock_dependencies):
        """Debe cerrar posición cuando IA decide CERRAR"""
        context = ReevaluationContext(
            position_id="test_4",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2480,
            profit_pips=80.0
        )
        
        mock_dependencies['data_extractor'].extract_current_data.return_value = {'price': 1.2480}
        mock_dependencies['prompt_builder'].build_reevaluation_prompt.return_value = "Test prompt"
        mock_dependencies['gemini_client'].send_prompt.return_value = Mock(
            success=True,
            content='{"accion": "CERRAR"}',
            tokens_input=100,
            tokens_output=50,
            cost=0.0015
        )
        
        parsed_decision = Mock()
        parsed_decision.is_valid = True
        parsed_decision.decision_type = AIDecisionType.CERRAR
        parsed_decision.reasoning = "Reversión detectada"
        mock_dependencies['response_parser'].parse_reevaluation.return_value = parsed_decision
        
        mock_dependencies['position_manager'].close_position.return_value = True
        
        result = await manager_persistent.reevaluate_single_position(context)
        
        assert result.success is True
        assert result.action_taken == "CERRAR"
        
        # Verificar que se llamó a close_position
        mock_dependencies['position_manager'].close_position.assert_called_once_with("test_4")
    
    @pytest.mark.asyncio
    async def test_reevaluate_single_position_api_error(self, manager_persistent, mock_dependencies):
        """Debe manejar error de API correctamente"""
        context = ReevaluationContext(
            position_id="test_5",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2450,
            profit_pips=50.0
        )
        
        mock_dependencies['data_extractor'].extract_current_data.return_value = {'price': 1.2450}
        mock_dependencies['prompt_builder'].build_reevaluation_prompt.return_value = "Test prompt"
        
        # Simular error de API
        mock_dependencies['gemini_client'].send_prompt.return_value = Mock(
            success=False,
            error_message="API timeout"
        )
        
        result = await manager_persistent.reevaluate_single_position(context)
        
        assert result.success is False
        assert "API timeout" in result.error_message
    
    @pytest.mark.asyncio
    async def test_reevaluate_single_position_invalid_response(self, manager_persistent, mock_dependencies):
        """Debe manejar respuesta inválida de IA"""
        context = ReevaluationContext(
            position_id="test_6",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2450,
            profit_pips=50.0
        )
        
        mock_dependencies['data_extractor'].extract_current_data.return_value = {'price': 1.2450}
        mock_dependencies['prompt_builder'].build_reevaluation_prompt.return_value = "Test prompt"
        mock_dependencies['gemini_client'].send_prompt.return_value = Mock(
            success=True,
            content='invalid json',
            tokens_input=100,
            tokens_output=50,
            cost=0.0015
        )
        
        # Parser retorna decisión inválida
        parsed_decision = Mock()
        parsed_decision.is_valid = False
        parsed_decision.error_message = "JSON inválido"
        mock_dependencies['response_parser'].parse_reevaluation.return_value = parsed_decision
        
        result = await manager_persistent.reevaluate_single_position(context)
        
        assert result.success is False
        assert "JSON inválido" in result.error_message
    
    def test_get_or_create_conversation_persistent_first_time(self, manager_persistent):
        """Modo persistente debe crear nueva conversación primera vez"""
        position_id = "pos_1"
        
        conv_id = manager_persistent._get_or_create_conversation(position_id)
        
        assert conv_id is not None
        assert position_id in manager_persistent.conversation_sessions
        assert manager_persistent.conversation_sessions[position_id] == conv_id
    
    def test_get_or_create_conversation_persistent_reuse(self, manager_persistent):
        """Modo persistente debe reutilizar conversación existente"""
        position_id = "pos_2"
        
        # Primera llamada
        conv_id_1 = manager_persistent._get_or_create_conversation(position_id)
        
        # Segunda llamada
        conv_id_2 = manager_persistent._get_or_create_conversation(position_id)
        
        # Debe ser la misma
        assert conv_id_1 == conv_id_2
        assert len(manager_persistent.conversation_sessions) == 1
    
    def test_get_or_create_conversation_new_mode(self, manager_new):
        """Modo new debe retornar None siempre"""
        position_id = "pos_3"
        
        conv_id_1 = manager_new._get_or_create_conversation(position_id)
        conv_id_2 = manager_new._get_or_create_conversation(position_id)
        
        assert conv_id_1 is None
        assert conv_id_2 is None
        assert len(manager_new.conversation_sessions) == 0
    
    def test_clear_conversation(self, manager_persistent):
        """Debe limpiar conversación de posición"""
        position_id = "pos_4"
        
        # Crear conversación
        manager_persistent._get_or_create_conversation(position_id)
        assert position_id in manager_persistent.conversation_sessions
        
        # Limpiar
        manager_persistent.clear_conversation(position_id)
        assert position_id not in manager_persistent.conversation_sessions
    
    def test_clear_all_conversations(self, manager_persistent):
        """Debe limpiar todas las conversaciones"""
        positions = ["pos_1", "pos_2", "pos_3"]
        
        # Crear varias conversaciones
        for pos in positions:
            manager_persistent._get_or_create_conversation(pos)
        
        assert len(manager_persistent.conversation_sessions) == 3
        
        # Limpiar todas
        manager_persistent.clear_all_conversations()
        assert len(manager_persistent.conversation_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_reevaluate_positions_multiple(self, manager_persistent, mock_dependencies):
        """Debe reevaluar múltiples posiciones"""
        # Mock de posiciones abiertas
        mock_positions = [
            {
                'position_id': 'pos_1',
                'symbol': 'EURUSD',
                'direction': 'BUY',
                'entry_price': 1.2400,
                'current_sl': 1.2350,
                'current_tp': 1.2550,
                'current_price': 1.2450,
                'profit_pips': 50.0
            },
            {
                'position_id': 'pos_2',
                'symbol': 'GBPUSD',
                'direction': 'SELL',
                'entry_price': 1.3200,
                'current_sl': 1.3250,
                'current_tp': 1.3100,
                'current_price': 1.3150,
                'profit_pips': 50.0
            }
        ]
        
        mock_dependencies['position_manager'].get_open_positions.return_value = mock_positions
        mock_dependencies['data_extractor'].extract_current_data.return_value = {'price': 1.2450}
        mock_dependencies['prompt_builder'].build_reevaluation_prompt.return_value = "Test"
        mock_dependencies['gemini_client'].send_prompt.return_value = Mock(
            success=True,
            content='{"accion": "MANTENER"}',
            tokens_input=100,
            tokens_output=50,
            cost=0.0015
        )
        
        parsed_decision = Mock()
        parsed_decision.is_valid = True
        parsed_decision.decision_type = AIDecisionType.MANTENER
        parsed_decision.reasoning = "OK"
        mock_dependencies['response_parser'].parse_reevaluation.return_value = parsed_decision
        
        results = await manager_persistent.reevaluate_positions(
            bot_id="bot_1",
            magic_number=100101
        )
        
        assert len(results) == 2
        assert all(r.success for r in results)
    
    def test_get_stats(self, manager_persistent):
        """Debe retornar estadísticas del manager"""
        stats = manager_persistent.get_stats()
        
        assert 'mode' in stats
        assert 'active_conversations' in stats
        assert stats['mode'] == "persistent"
        assert stats['active_conversations'] == 0
        
        # Agregar conversaciones
        manager_persistent._get_or_create_conversation("pos_1")
        manager_persistent._get_or_create_conversation("pos_2")
        
        stats = manager_persistent.get_stats()
        assert stats['active_conversations'] == 2


class TestReevaluationManagerEdgeCases:
    """Tests de casos extremos"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Crea mocks de todas las dependencias"""
        return {
            'mt5_connector': Mock(),
            'data_extractor': Mock(),
            'prompt_builder': Mock(),
            'gemini_client': AsyncMock(),
            'response_parser': Mock(),
            'position_manager': Mock()
        }
    
    @pytest.mark.asyncio
    async def test_reevaluate_with_retry_on_failure(self, mock_dependencies):
        """Debe reintentar en caso de fallo temporal"""
        manager = ReevaluationManager(**mock_dependencies)
        
        context = ReevaluationContext(
            position_id="test_retry",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2450,
            profit_pips=50.0
        )
        
        mock_dependencies['data_extractor'].extract_current_data.return_value = {'price': 1.2450}
        mock_dependencies['prompt_builder'].build_reevaluation_prompt.return_value = "Test"
        
        # Primera llamada falla, segunda éxito
        mock_dependencies['gemini_client'].send_prompt.side_effect = [
            Mock(success=False, error_message="Temporary error"),
            Mock(success=True, content='{"accion": "MANTENER"}', tokens_input=100, tokens_output=50, cost=0.0015)
        ]
        
        parsed_decision = Mock()
        parsed_decision.is_valid = True
        parsed_decision.decision_type = AIDecisionType.MANTENER
        mock_dependencies['response_parser'].parse_reevaluation.return_value = parsed_decision
        
        # Debería funcionar después del retry
        # (Esta funcionalidad requeriría implementación de retry en el manager)
        pass
