#!/usr/bin/env python3
"""
Test de simulación de respuesta real de Gemini que dice COMPRAR (Caso de Error Reportado).

Este test simula la respuesta exacta que generó el error:
"[WARNING] Dirección inválida/ausente en decisión: ''"
y verifica que con los fixes aplicados, ahora SÍ abre la operación.
"""

import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode


def test_simulate_real_gemini_comprar_error_case():
    """Simula la respuesta real de Gemini que falló al abrir operación."""

    # Respuesta JSON exacta del log proporcionado
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
        bot_id=5,
        bot_name="INTRADAY Baseline",
        bot_type="numerico"
    )

    # Crear instancia del bot
    bot = IntradayBot1Strategy(config)

    # Simular inicialización completa - mockear componentes
    bot.mt5_connection = MagicMock()
    bot.order_manager = MagicMock()
    bot.position_sizer = MagicMock()
    bot.magic_number_generator = MagicMock()
    bot.symbol_spec_extractor = MagicMock()
    bot._position_manager = MagicMock()
    bot.operations_repo = MagicMock()
    bot.ia_query_repository = MagicMock()

    # Configurar mocks para USDCHF (datos del log)
    mock_tick = MagicMock()
    mock_tick.ask = 0.8066  # Precio mencionado en razonamiento
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

    bot.magic_number_generator.generate.return_value = 5

    mock_result = MagicMock()
    mock_result.order = 123456
    mock_result.price = 0.8066
    mock_result.volume = 0.01
    bot.order_manager.send_market_order.return_value = mock_result

    # Simular que no hay posición activa
    bot._position_manager.get_positions_by_symbol_and_magic.return_value = []

    print("🔍 1. Parseando respuesta de Gemini...")
    # Parsear la respuesta de Gemini
    parsed_decision = bot.parse_ai_response(json.dumps(gemini_response))

    print(f"   JSON Original: {json.dumps(gemini_response)}")
    print(f"   Parseado: {parsed_decision}")

    # Crear decisión completa (simulando lo que hace execute_cycle)
    # NOTA: Aquí es donde ocurría el error antes, si 'direccion' no se mapeaba correctamente
    decision = {
        "operation_id": "test_op_usdchf_1",
        "accion": parsed_decision["accion"],
        "reasoning": parsed_decision["razonamiento"],
        "direccion": parsed_decision.get("direccion"), 
        "stop_loss": parsed_decision.get("stop_loss"),
        "take_profit": parsed_decision.get("take_profit"),
        "confidence": parsed_decision.get("confianza"),
        "query_id": 123,
        "cost_usd": 0.01,
        "tokens_total": 1500,
        "timestamp": "2025-11-20T10:53:42",
    }

    print("\n🔍 2. Verificando decisión antes de ejecución...")
    print(f"   Acción: {decision['accion']}")
    print(f"   Dirección: {decision['direccion']}") # Esto debería ser 'LONG' o 'BUY'
    
    if not decision['direccion']:
        print("❌ ERROR: La dirección está vacía en la decisión (reproducción del bug)")
    else:
        print("✅ Dirección presente en la decisión")

    print("\n🚀 3. Ejecutando _execute_open_position...")
    # Ejecutar la apertura
    bot._execute_open_position("USDCHF", decision)

    # Verificar resultado
    if bot.order_manager.send_market_order.called:
        print("\n✅ ¡ÉXITO! Se llamó a send_market_order")
        call_args = bot.order_manager.send_market_order.call_args
        order_request = call_args[0][0]
        print(f"   Símbolo: {order_request.symbol}")
        print(f"   Tipo Orden: {order_request.order_type}")
        print(f"   Precio: {order_request.price}")
        print(f"   SL: {order_request.sl}")
        print(f"   TP: {order_request.tp}")
        print("   --> El bot ABRIRÍA la operación en tiempo real.")
        return True
    else:
        print("\n❌ FALLO: No se llamó a send_market_order")
        print("   --> El bot NO abriría la operación.")
        return False

if __name__ == '__main__':
    print("🧪 Test de Reproducción de Error: Gemini COMPRAR USDCHF")
    print("=======================================================")
    
    try:
        success = test_simulate_real_gemini_comprar_error_case()
        if success:
            print("\n🎉 PRUEBA APROBADA: El fix funciona para el caso reportado.")
        else:
            print("\n💥 PRUEBA FALLIDA: El error persiste.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Excepción durante el test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
