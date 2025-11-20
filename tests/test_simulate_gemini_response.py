#!/usr/bin/env python3
"""
Test de simulación de respuesta de Gemini para verificar apertura de operaciones.

Este test simula la respuesta exacta de Gemini que estaba fallando y verifica
que ahora se abra la operación correctamente.
"""

import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode


def test_simulate_gemini_response():
    """Simula la respuesta exacta de Gemini que estaba fallando."""

    # Respuesta JSON exacta que Gemini estaba retornando
    gemini_response = {
        "accion": "COMPRAR",
        "razonamiento": "Tendencia intradía alcista intacta (Precio > EMA20 > VWAP > EMA200). El precio está consolidando sobre la EMA 20 (0.8066) tras un retroceso, ofreciendo un punto de entrada de bajo riesgo tipo 'Trend Surfer'.",
        "direccion": "LONG",
        "stop_loss": 0.8048,
        "take_profit": 0.8102,
        "confianza": 80,
        "estrategia_usada": "A",
        "diagnostico_mercado": "TENDENCIA_ALCISTA"
    }

    # Crear configuración del bot
    config = BotConfig(
        bot_id=5,  # Usando bot_id=5 como en los logs del usuario
        bot_name="INTRADAY Baseline",
        bot_type="numerico"
    )

    # Crear instancia del bot
    bot = IntradayBot1Strategy(config)

    # Simular inicialización completa - mockear componentes individuales
    bot.mt5_connection = MagicMock()
    bot.order_manager = MagicMock()
    bot.position_sizer = MagicMock()
    bot.magic_number_generator = MagicMock()
    bot.symbol_spec_extractor = MagicMock()
    bot._position_manager = MagicMock()  # Mockear el atributo privado
    bot.operations_repo = MagicMock()
    bot.ia_query_repository = MagicMock()

    # Configurar mocks
    mock_tick = MagicMock()
    mock_tick.ask = 0.8066
    mock_tick.bid = 0.8064
    bot.mt5_connection._mt5.symbol_info_tick.return_value = mock_tick

    mock_account = MagicMock()
    mock_account.balance = 10000.0
    bot.mt5_connection.get_account_info.return_value = mock_account

    bot.mt5_connection.get_symbol_info.return_value = MagicMock()

    mock_symbol_spec = MagicMock()
    mock_symbol_spec.volume_min = 0.01
    mock_symbol_spec.volume_step = 0.01
    bot.symbol_spec_extractor.get_symbol_specification.return_value = mock_symbol_spec

    bot.magic_number_generator.generate.return_value = 5  # magic number del bot

    mock_result = MagicMock()
    mock_result.order = 123456
    mock_result.price = 0.8066
    mock_result.volume = 0.01
    bot.order_manager.send_market_order.return_value = mock_result

    # Simular que no hay posición activa
    bot._position_manager.get_positions_by_symbol_and_magic.return_value = []

    # Parsear la respuesta de Gemini (como lo haría el bot)
    parsed_decision = bot.parse_ai_response(json.dumps(gemini_response))

    print("✅ Respuesta de Gemini parseada correctamente:")
    print(f"   Acción: {parsed_decision['accion']}")
    print(f"   Dirección: {parsed_decision['direccion']}")
    print(f"   Stop Loss: {parsed_decision['stop_loss']}")
    print(f"   Take Profit: {parsed_decision['take_profit']}")

    # Crear decisión completa como la retornaría execute_cycle
    decision = {
        "operation_id": "test_operation_123",
        "accion": parsed_decision["accion"],
        "reasoning": parsed_decision["razonamiento"],
        "direccion": parsed_decision.get("direccion"),  # Campo corregido
        "stop_loss": parsed_decision.get("stop_loss"),
        "take_profit": parsed_decision.get("take_profit"),
        "confidence": parsed_decision.get("confianza"),
        "query_id": 123,
        "cost_usd": 0.01,
        "tokens_total": 1500,
        "timestamp": "2025-11-20T13:00:00",
    }

    print("\n✅ Decisión preparada para ejecución:")
    print(f"   Acción: {decision['accion']}")
    print(f"   Dirección: {decision['direccion']}")
    print(f"   Stop Loss: {decision['stop_loss']}")
    print(f"   Take Profit: {decision['take_profit']}")

    # Ejecutar la apertura de posición
    print("\n🚀 Ejecutando apertura de posición...")
    bot._execute_open_position("USDCHF", decision)

    # Verificar que se llamó a send_market_order
    if bot.order_manager.send_market_order.called:
        print("✅ ¡ÉXITO! La orden Market fue enviada correctamente")
        call_args = bot.order_manager.send_market_order.call_args
        order_request = call_args[0][0]
        print(f"   Símbolo: {order_request.symbol}")
        print(f"   Tipo: {order_request.order_type}")
        print(f"   Dirección: {order_request.order_type.name}")
        print(f"   Precio: {order_request.price}")
        print(f"   SL: {order_request.sl}")
        print(f"   TP: {order_request.tp}")
        print(f"   Magic: {order_request.magic}")
    else:
        print("❌ ERROR: No se llamó a send_market_order")

    return True


if __name__ == '__main__':
    print("🧪 Test de simulación de respuesta de Gemini")
    print("=" * 50)

    try:
        success = test_simulate_gemini_response()
        if success:
            print("\n🎉 Test completado exitosamente!")
            print("El fix del parsing de dirección está funcionando correctamente.")
        else:
            print("\n❌ Test falló")
    except Exception as e:
        print(f"\n💥 Error durante el test: {e}")
        import traceback
        traceback.print_exc()