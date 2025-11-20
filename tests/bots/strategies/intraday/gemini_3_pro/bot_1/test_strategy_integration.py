"""Test de integración para strategy.py - Verificar carga de prompts y flujo completo.

Este test verifica que:
1. Se puedan cargar los archivos de prompts
2. El método prepare_data_for_ai() funcione correctamente
3. Se genere operation_id correctamente
4. Se reemplacen las variables en los prompts
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.bots.strategies.intraday.gemini_3_pro.bot_1.config import get_bot_1_config
from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import (
    IntradayBot1Strategy,
)


@pytest.fixture
def bot_config():
    """Fixture que retorna configuración del bot."""
    return get_bot_1_config(mode=BotMode.DEMO)


@pytest.fixture
def strategy(bot_config):
    """Fixture que retorna instancia de IntradayBot1Strategy."""
    return IntradayBot1Strategy(bot_config)


def test_prompts_directory_exists(strategy):
    """Verifica que el directorio de prompts existe."""
    assert strategy.prompts_dir.exists()
    assert strategy.prompts_dir.is_dir()


def test_prompt_files_exist(strategy):
    """Verifica que los archivos de prompts existen."""
    system_prompt_path = strategy.prompts_dir / "system_prompt.txt"
    user_prompt_eval_path = strategy.prompts_dir / "user_prompt_evaluation.txt"
    user_prompt_reeval_path = strategy.prompts_dir / "user_prompt_reevaluation.txt"
    
    assert system_prompt_path.exists()
    assert user_prompt_eval_path.exists()
    assert user_prompt_reeval_path.exists()


def test_prepare_data_for_ai_structure(strategy):
    """Verifica que prepare_data_for_ai() retorna la estructura correcta."""
    symbol = "EURUSD"
    
    # Mock del calculador de indicadores para evitar llamadas reales a MT5
    with patch.object(
        strategy.indicator_calculator,
        "get_full_intraday_packages",
        return_value={
            "tactical": [{"time": "2025-01-01", "close": 1.1000}],
            "strategic": [{"time": "2025-01-01", "close": 1.1000}],
        },
    ):
        result = strategy.prepare_data_for_ai(
            symbol=symbol,
            indicators={},
            or_data=None,
            market_context=strategy.get_market_context(),
            ohlcv_data=None,
        )
    
    # Verificar estructura del resultado
    assert isinstance(result, dict)
    assert "operation_id" in result
    assert "system_prompt" in result
    assert "user_prompt" in result
    assert "tactical_package" in result
    assert "strategic_package" in result
    assert "symbol" in result
    assert "timestamp" in result
    assert "has_active_position" in result
    
    # Verificar que operation_id tiene formato correcto
    operation_id = result["operation_id"]
    assert operation_id.startswith("INTRADAY_5_EURUSD_")
    parts = operation_id.split("_")
    assert len(parts) == 6  # INTRADAY, 5, EURUSD, fecha, hora, uuid
    
    # Verificar que prompts no están vacíos
    assert len(result["system_prompt"]) > 0
    assert len(result["user_prompt"]) > 0


def test_prepare_data_for_ai_variable_replacement(strategy):
    """Verifica que las variables se reemplazan correctamente en user_prompt."""
    symbol = "EURUSD"
    
    # Mock del calculador de indicadores
    mock_tactical = [{"time": "2025-01-01 10:00", "close": 1.1000}]
    mock_strategic = [{"time": "2025-01-01", "close": 1.1000}]
    
    with patch.object(
        strategy.indicator_calculator,
        "get_full_intraday_packages",
        return_value={
            "tactical": mock_tactical,
            "strategic": mock_strategic,
        },
    ):
        result = strategy.prepare_data_for_ai(
            symbol=symbol,
            indicators={},
            or_data=None,
            market_context=strategy.get_market_context(),
            ohlcv_data=None,
        )
    
    user_prompt = result["user_prompt"]
    
    # Verificar que las variables fueron reemplazadas
    # (ya no deben aparecer como {variable})
    assert "{symbol}" not in user_prompt
    assert "{operation_id}" not in user_prompt
    assert "{current_time}" not in user_prompt
    assert "{tactical_package}" not in user_prompt
    assert "{strategic_package}" not in user_prompt
    
    # Verificar que los valores reales sí aparecen
    assert symbol in user_prompt
    assert result["operation_id"] in user_prompt


def test_operation_id_generation_unique(strategy):
    """Verifica que cada llamada genera un operation_id único."""
    symbol = "EURUSD"
    
    with patch.object(
        strategy.indicator_calculator,
        "get_full_intraday_packages",
        return_value={
            "tactical": [{"time": "2025-01-01", "close": 1.1000}],
            "strategic": [{"time": "2025-01-01", "close": 1.1000}],
        },
    ):
        result1 = strategy.prepare_data_for_ai(
            symbol=symbol,
            indicators={},
            or_data=None,
            market_context=strategy.get_market_context(),
            ohlcv_data=None,
        )
        
        result2 = strategy.prepare_data_for_ai(
            symbol=symbol,
            indicators={},
            or_data=None,
            market_context=strategy.get_market_context(),
            ohlcv_data=None,
        )
    
    # Los operation_id deben ser diferentes
    assert result1["operation_id"] != result2["operation_id"]


def test_execute_cycle_structure(strategy):
    """Verifica que execute_cycle() retorna la estructura correcta."""
    symbol = "EURUSD"
    
    # Mock de todos los componentes
    with patch.object(
        strategy.indicator_calculator,
        "get_full_intraday_packages",
        return_value={
            "tactical": [{"time": "2025-01-01", "close": 1.1000}],
            "strategic": [{"time": "2025-01-01", "close": 1.1000}],
        },
    ):
        with patch.object(
            strategy.ia_query_repository,
            "create_query",
            return_value=MagicMock(
                id=1,
                cost_usd=0.05,
                tokens_total=1500,
            ),
        ):
            result = strategy.execute_cycle(symbol)
    
    # Verificar estructura del resultado
    assert isinstance(result, dict)
    assert "operation_id" in result
    assert "action" in result
    assert "reasoning" in result
    assert "query_id" in result
    assert "cost_usd" in result
    assert "tokens_total" in result
    assert "timestamp" in result
    
    # Verificar que action es válida (actualmente placeholder retorna NO_OPERAR)
    assert result["action"] == "NO_OPERAR"

