"""Test de integración para strategy.py - Verificar carga de prompts y flujo completo.

Este test verifica que:
1. Se puedan cargar los archivos de prompts
2. El método prepare_data_for_ai() funcione correctamente
3. Se genere operation_id correctamente
4. Se reemplacen las variables en los prompts
5. Se pueda consultar el API real de Gemini 3 Pro (tests de integración)

NOTA: Los tests que requieren API real están marcados con @pytest.mark.integration
y requieren que esté configurado GOOGLE_API_KEY en el entorno.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.bots.strategies.intraday.gemini_3_pro.bot_1.config import get_bot_1_config
from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import (
    IntradayBot1Strategy,
)
from src.core.gemini_client import GeminiResponse


@pytest.fixture
def bot_config():
    """Fixture que retorna configuración del bot."""
    return get_bot_1_config(mode=BotMode.DEMO)


@pytest.fixture
def strategy(bot_config):
    """Fixture que retorna instancia de IntradayBot1Strategy con conexiones reales.
    
    Usa:
    - API real de Gemini 3 Pro (requiere GOOGLE_API_KEY)
    - Conexión real a MT5 (requiere MT5 instalado y configurado)
    
    Si falta alguna configuración, se salta el test.
    """
    # Verificar que existe API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY no está configurada - se requiere para tests con API real")
    
    # Crear estrategia con API real de Gemini y MT5 real
    strategy_instance = IntradayBot1Strategy(bot_config)
    
    # Inicializar conexiones (MT5, extractores, etc.)
    if not strategy_instance.initialize():
        pytest.skip("No se pudo inicializar MT5 - se requiere MT5 instalado y conectado")
    
    return strategy_instance


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
    """Verifica que execute_cycle() retorna la estructura correcta con API real.
    
    IMPORTANTE: Este test hace una llamada REAL a Gemini 3 Pro API y usa MT5 real.
    Requiere:
    - GOOGLE_API_KEY configurada
    - MT5 instalado y conectado
    """
    symbol = "EURUSD"
    
    # Mock SOLO del IAQueryRepository (para no registrar en BD durante test)
    with patch.object(
        strategy.ia_query_repository,
        "create_query",
        return_value=MagicMock(
            id=1,
            cost_usd=0.0,
            tokens_total=0,
        ),
    ):
        # LLAMADA REAL A:
        # - IntradayIndicatorCalculator (obtiene datos reales de MT5)
        # - Gemini 3 Pro API (consulta real)
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
    
    # Verificar que action es una acción válida
    valid_actions = ["COMPRAR", "VENDER", "NO_OPERAR", "MANTENER", "CERRAR"]
    assert result["action"] in valid_actions
    
    # Verificar que tenemos reasoning
    assert isinstance(result["reasoning"], str)
    assert len(result["reasoning"]) > 0
    
    # Verificar que cost_usd es un número positivo
    assert isinstance(result["cost_usd"], (int, float))
    assert result["cost_usd"] >= 0
    
    # Verificar que tokens_total es un número
    assert isinstance(result["tokens_total"], (int, float))
    assert result["tokens_total"] > 0
    
    # Log de información para debugging
    print(f"\n✅ Test con API real completado:")
    print(f"   Operation ID: {result['operation_id']}")
    print(f"   Acción: {result['action']}")
    print(f"   Razonamiento: {result['reasoning'][:100]}...")
    print(f"   Costo: ${result['cost_usd']:.4f}")
    print(f"   Tokens: {result['tokens_total']}")


def test_parse_ai_response_valid_json(strategy):
    """Verifica que parse_ai_response parsea JSON válido correctamente."""
    response_json = json.dumps({
        "accion": "COMPRAR",
        "razonamiento": "RSI sobrevendido y tendencia alcista",
        "direccion": "LONG",
        "stop_loss": 1.0950,
        "take_profit": 1.1050,
        "confianza": 85.5,
    })
    
    result = strategy.parse_ai_response(response_json)
    
    assert result["accion"] == "COMPRAR"
    assert result["razonamiento"] == "RSI sobrevendido y tendencia alcista"
    assert result["direccion"] == "LONG"
    assert result["stop_loss"] == 1.0950
    assert result["take_profit"] == 1.1050
    assert result["confianza"] == 85.5


def test_parse_ai_response_minimal_json(strategy):
    """Verifica que parse_ai_response funciona con campos mínimos."""
    response_json = json.dumps({
        "accion": "NO_OPERAR",
        "razonamiento": "Condiciones no favorables",
    })
    
    result = strategy.parse_ai_response(response_json)
    
    assert result["accion"] == "NO_OPERAR"
    assert result["razonamiento"] == "Condiciones no favorables"
    assert result["direccion"] is None
    assert result["stop_loss"] is None
    assert result["take_profit"] is None


def test_parse_ai_response_invalid_json(strategy):
    """Verifica que parse_ai_response falla con JSON inválido."""
    with pytest.raises(ValueError, match="Respuesta no es JSON válido"):
        strategy.parse_ai_response("Esto no es JSON")


def test_parse_ai_response_missing_accion(strategy):
    """Verifica que parse_ai_response falla si falta 'accion'."""
    response_json = json.dumps({
        "razonamiento": "Análisis completo",
    })
    
    with pytest.raises(ValueError, match="no contiene campo 'accion'"):
        strategy.parse_ai_response(response_json)


def test_parse_ai_response_invalid_accion(strategy):
    """Verifica que parse_ai_response falla con acción inválida."""
    response_json = json.dumps({
        "accion": "OPERACION_INVALIDA",
        "razonamiento": "Test",
    })
    
    with pytest.raises(ValueError, match="Acción inválida"):
        strategy.parse_ai_response(response_json)


def test_has_active_position_true(strategy):
    """Verifica que _has_active_position retorna True cuando hay posición."""
    symbol = "EURUSD"
    
    # Mock de position_manager con posición activa
    mock_position = MagicMock()
    mock_position.ticket = 12345
    
    with patch.object(
        strategy.position_manager,
        "get_positions_by_symbol_and_magic",
        return_value=[mock_position],
    ):
        result = strategy._has_active_position(symbol)
    
    assert result is True


def test_has_active_position_false(strategy):
    """Verifica que _has_active_position retorna False cuando no hay posición."""
    symbol = "EURUSD"
    
    # Mock de position_manager sin posiciones
    with patch.object(
        strategy.position_manager,
        "get_positions_by_symbol_and_magic",
        return_value=[],
    ):
        result = strategy._has_active_position(symbol)
    
    assert result is False


def test_get_current_position_info_with_position(strategy):
    """Verifica que _get_current_position_info retorna datos correctos."""
    symbol = "EURUSD"
    
    # Mock de posición LONG
    mock_position = MagicMock()
    mock_position.type = 0  # BUY
    mock_position.price_open = 1.1000
    mock_position.price_current = 1.1050
    mock_position.sl = 1.0950
    mock_position.tp = 1.1100
    mock_position.profit = 50.0
    mock_position.volume = 0.1
    mock_position.ticket = 12345
    mock_position.time = datetime(2025, 11, 19, 10, 0, 0)
    
    with patch.object(
        strategy.position_manager,
        "get_positions_by_symbol_and_magic",
        return_value=[mock_position],
    ):
        result = strategy._get_current_position_info(symbol)
    
    assert result["type"] == "LONG"
    assert result["entry_price"] == 1.1000
    assert result["current_price"] == 1.1050
    assert result["sl"] == 1.0950
    assert result["tp"] == 1.1100
    assert result["pnl_usd"] == 50.0
    assert result["volume"] == 0.1
    assert result["ticket"] == 12345
    # PnL en puntos: 1.1050 - 1.1000 = 0.0050
    assert result["pnl_points"] == 0.0050
    # Risk points: 1.1000 - 1.0950 = 0.0050
    # PnL en R: 0.0050 / 0.0050 = 1.0R
    assert result["pnl_r"] == 1.0


def test_get_current_position_info_short(strategy):
    """Verifica que _get_current_position_info maneja posiciones SHORT."""
    symbol = "EURUSD"
    
    # Mock de posición SHORT
    mock_position = MagicMock()
    mock_position.type = 1  # SELL
    mock_position.price_open = 1.1000
    mock_position.price_current = 1.0950
    mock_position.sl = 1.1050
    mock_position.tp = 1.0900
    mock_position.profit = 50.0
    mock_position.volume = 0.1
    mock_position.ticket = 12346
    mock_position.time = datetime(2025, 11, 19, 10, 0, 0)
    
    with patch.object(
        strategy.position_manager,
        "get_positions_by_symbol_and_magic",
        return_value=[mock_position],
    ):
        result = strategy._get_current_position_info(symbol)
    
    assert result["type"] == "SHORT"
    # PnL en puntos para SHORT: 1.1000 - 1.0950 = 0.0050
    assert result["pnl_points"] == 0.0050
    # Risk points: 1.1050 - 1.1000 = 0.0050
    # PnL en R: 0.0050 / 0.0050 = 1.0R
    assert result["pnl_r"] == 1.0


@pytest.mark.integration
def test_gemini_api_real_call(strategy):
    """Test de integración: Llamada REAL a Gemini 3 Pro API.
    
    Este test valida que:
    1. El API de Gemini 3 Pro está disponible
    2. La configuración de API key es correcta
    3. La respuesta se recibe correctamente
    4. El formato JSON es válido
    
    IMPORTANTE: Requiere GOOGLE_API_KEY configurada.
    Se marca como @pytest.mark.integration para ejecutarse solo cuando se solicita.
    """
    # Verificar que existe API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY no está configurada - skipping test de integración")
    
    symbol = "EURUSD"
    
    # Mock SOLO del calculador de indicadores (datos realistas)
    mock_tactical_data = []
    for i in range(200):
        mock_tactical_data.append({
            "time": f"2025-11-19 {8 + i//4:02d}:{i%4*15:02d}",
            "open": 1.1000 + (i * 0.00001),
            "high": 1.1010 + (i * 0.00001),
            "low": 1.0990 + (i * 0.00001),
            "close": 1.1005 + (i * 0.00001),
            "volume": 1500 + i,
            "ema_200": 1.0980 + (i * 0.00001),
            "rsi": 50.0 + (i % 30),
            "adx": 25.0,
            "plus_di": 22.0,
            "minus_di": 18.0,
            "atr": 0.0015,
        })
    
    mock_strategic_data = []
    for i in range(30):
        mock_strategic_data.append({
            "time": f"2025-11-{19-i:02d}",
            "open": 1.0950 + (i * 0.0005),
            "high": 1.1020 + (i * 0.0005),
            "low": 1.0940 + (i * 0.0005),
            "close": 1.0995 + (i * 0.0005),
            "volume": 50000 + (i * 1000),
            "ema_200": 1.0970 + (i * 0.0005),
            "rsi": 52.0 + (i % 20),
            "adx": 28.0,
            "plus_di": 24.0,
            "minus_di": 19.0,
            "atr": 0.0018,
        })
    
    with patch.object(
        strategy.indicator_calculator,
        "get_full_intraday_packages",
        return_value={
            "tactical": mock_tactical_data,
            "strategic": mock_strategic_data,
        },
    ):
        with patch.object(
            strategy.ia_query_repository,
            "create_query",
            return_value=MagicMock(
                id=1,
                cost_usd=0.0,
                tokens_total=0,
            ),
        ):
            # LLAMADA REAL A GEMINI 3 PRO
            result = strategy.execute_cycle(symbol)
    
    # Validaciones de respuesta real
    assert result["action"] in ["COMPRAR", "VENDER", "NO_OPERAR", "MANTENER", "CERRAR"]
    assert len(result["reasoning"]) > 10  # Razonamiento debe tener contenido
    assert result["cost_usd"] > 0  # Debe tener costo real
    assert result["tokens_total"] > 0  # Debe haber usado tokens
    
    print(f"\n✅ Respuesta real de Gemini 3 Pro:")
    print(f"   Acción: {result['action']}")
    print(f"   Razonamiento: {result['reasoning'][:100]}...")
    print(f"   Costo: ${result['cost_usd']:.4f}")
    print(f"   Tokens: {result['tokens_total']}")


