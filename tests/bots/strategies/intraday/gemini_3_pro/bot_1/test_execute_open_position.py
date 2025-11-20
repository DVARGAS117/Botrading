"""Tests para _execute_open_position con registro de stop_loss_initial y take_profit_initial.

Este test verifica que al abrir una posición:
1. Se ejecuta la orden en MT5 (mock)
2. Se registra en la base de datos
3. Se guardan los valores iniciales de SL/TP para trailing stop
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.operations_repository import OperationsRepository, OperationStatus, Direction, OrderType as DBOrderType


@pytest.fixture
def mock_position():
    """Mock de una posición de MT5"""
    position = Mock()
    position.ticket = 123456
    position.symbol = "EURUSD"
    position.type = 0  # BUY
    position.volume = 0.1
    position.price_open = 1.1000
    position.price_current = 1.1005
    position.sl = 1.0950
    position.tp = 1.1100
    position.profit = 5.0
    position.swap = 0.0
    position.magic = 100001
    position.comment = "Bot5-INTRADAY"
    position.time_open = datetime.now()
    return position


@pytest.fixture
def bot_config():
    """Configuración básica del bot para tests"""
    config = BotConfig(
        bot_id=5,
        bot_name="INTRADAY",
        symbols=["EURUSD"],
        mode=BotMode.DEMO,
        risk_per_trade=1.0,
        ai_model="gemini-3-pro-preview",
    )
    return config


@pytest.fixture
def test_db_path(tmp_path):
    """Path temporal para base de datos de test"""
    return tmp_path / "test_operations.db"


@pytest.fixture
def intraday_bot(bot_config, test_db_path, mock_position):
    """Bot INTRADAY con mocks configurados"""
    with patch('src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy.VertexAIClient'):
        bot = IntradayBot1Strategy(bot_config)
        
        # Reemplazar repositorio con uno de test
        bot.operations_repo = OperationsRepository(db_path=test_db_path)
        
        # Mock de position_manager
        bot._position_manager = Mock()
        bot._position_manager.get_positions_by_symbol.return_value = [mock_position]
        
        # Mock de mt5_connection
        bot.mt5_connection = Mock()
        bot.mt5_connection._mt5 = Mock()
        tick_mock = Mock()
        tick_mock.ask = 1.1000
        tick_mock.bid = 1.0999
        bot.mt5_connection._mt5.symbol_info_tick.return_value = tick_mock
        
        # Mock del método base _execute_open_position
        with patch.object(IntradayBot1Strategy.__bases__[0], '_execute_open_position'):
            yield bot


def test_execute_open_position_saves_initial_sl_tp(intraday_bot, test_db_path):
    """Test: _execute_open_position guarda stop_loss_initial y take_profit_initial"""
    
    # Decisión de la IA para abrir posición BUY
    decision = {
        "direccion": "buy",
        "stop_loss": 1.0950,
        "take_profit": 1.1100,
        "precio_entrada": 1.1000,
    }
    
    # Ejecutar
    intraday_bot._execute_open_position("EURUSD", decision)
    
    # Verificar que se registró en BD
    operations = intraday_bot.operations_repo.get_all_operations()
    
    assert len(operations) == 1, "Debe haber 1 operación registrada"
    
    operation = operations[0]
    
    # Verificar campos básicos
    assert operation.symbol == "EURUSD"
    assert operation.direction == Direction.BUY
    assert operation.stop_loss == 1.0950
    assert operation.take_profit == 1.1100
    assert operation.status == OperationStatus.OPEN
    
    # 🔑 Verificar valores iniciales guardados
    assert operation.stop_loss_initial == 1.0950, "stop_loss_initial debe guardarse"
    assert operation.take_profit_initial == 1.1100, "take_profit_initial debe guardarse"
    
    # Verificar que se guardó el ticket de MT5
    assert operation.magic_number == 123456


def test_execute_open_position_handles_no_position_manager(intraday_bot):
    """Test: Manejar caso donde PositionManager no está disponible"""
    
    # Simular que no hay position_manager
    intraday_bot._position_manager = None
    
    decision = {
        "direccion": "buy",
        "stop_loss": 1.0950,
        "take_profit": 1.1100,
    }
    
    # No debe lanzar excepción
    intraday_bot._execute_open_position("EURUSD", decision)
    
    # No debe crear operación en BD
    operations = intraday_bot.operations_repo.get_all_operations()
    assert len(operations) == 0


def test_execute_open_position_handles_no_sl_tp(intraday_bot):
    """Test: No abrir posición si falta SL o TP"""
    
    # Decisión sin SL
    decision_no_sl = {
        "direccion": "buy",
        "take_profit": 1.1100,
    }
    
    intraday_bot._execute_open_position("EURUSD", decision_no_sl)
    
    # No debe crear operación
    operations = intraday_bot.operations_repo.get_all_operations()
    assert len(operations) == 0
    
    # Decisión sin TP
    decision_no_tp = {
        "direccion": "buy",
        "stop_loss": 1.0950,
    }
    
    intraday_bot._execute_open_position("EURUSD", decision_no_tp)
    
    # Aún no debe crear operación
    operations = intraday_bot.operations_repo.get_all_operations()
    assert len(operations) == 0


def test_execute_open_position_sell_direction(intraday_bot, mock_position):
    """Test: Registrar correctamente operación SELL"""
    
    # Modificar mock para posición SELL
    mock_position.type = 1  # SELL
    
    decision = {
        "direccion": "sell",
        "stop_loss": 1.1050,
        "take_profit": 1.0900,
        "precio_entrada": 1.1000,
    }
    
    intraday_bot._execute_open_position("EURUSD", decision)
    
    operations = intraday_bot.operations_repo.get_all_operations()
    assert len(operations) == 1
    
    operation = operations[0]
    assert operation.direction == Direction.SELL
    assert operation.stop_loss == 1.1050
    assert operation.take_profit == 1.0900
    assert operation.stop_loss_initial == 1.1050
    assert operation.take_profit_initial == 1.0900


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
