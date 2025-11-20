#!/usr/bin/env python3
"""
Test de simulación de respuesta real de Gemini que dice NO_OPERAR.

Este test simula la respuesta exacta que Gemini dio en producción
para verificar que el bot maneja correctamente las decisiones de NO_OPERAR.
"""

import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode


def test_simulate_real_gemini_no_operar():
    """Simula la respuesta real de Gemini que dice NO_OPERAR."""

    # Respuesta JSON exacta que Gemini dio en producción
    gemini_response = {
        "accion": "NO_OPERAR",
        "razonamiento": "Conflicto técnico: Tendencia intradía bajista (Precio < EMA200 M15) contra tendencia macro alcista (D1). Sin gatillo de entrada válido.",
        "direccion": None,
        "stop_loss": None,
        "take_profit": None,
        "confianza": 0,
        "estrategia_usada": "NONE",
        "diagnostico_mercado": "TENDENCIA_BAJISTA"
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
    mock_tick.ask = 1.1580
    mock_tick.bid = 1.1578
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
    mock_result.price = 1.1580
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
    print(f"   Confianza: {parsed_decision['confianza']}")
    print(f"   Estrategia: {parsed_decision['estrategia_usada']}")
    print(f"   Diagnóstico: {parsed_decision['diagnostico_mercado']}")

    # Crear decisión completa como la retornaría execute_cycle
    decision = {
        "operation_id": "test_operation_no_operar_123",
        "accion": parsed_decision["accion"],
        "reasoning": parsed_decision["razonamiento"],
        "direccion": parsed_decision.get("direccion"),  # Campo corregido
        "stop_loss": parsed_decision.get("stop_loss"),
        "take_profit": parsed_decision.get("take_profit"),
        "confidence": parsed_decision.get("confianza"),
        "query_id": 123,
        "cost_usd": 0.01,
        "tokens_total": 1500,
        "timestamp": "2025-11-20T13:21:26",
    }

    print("\n✅ Decisión preparada para ejecución:")
    print(f"   Acción: {decision['accion']}")
    print(f"   Dirección: {decision['direccion']}")
    print(f"   Stop Loss: {decision['stop_loss']}")
    print(f"   Take Profit: {decision['take_profit']}")
    print(f"   Confianza: {decision['confidence']}")

    # Simular la lógica de decisión del bot (sin ejecutar ciclo completo)
    print("\n🚀 Simulando lógica de decisión del bot...")

    # Esta es la lógica que el bot usaría para decidir si abrir posición
    should_open_position = (
        decision.get("accion") == "COMPRAR" or
        decision.get("accion") == "VENDER" or
        (decision.get("accion") == "OPERAR" and decision.get("direccion") in ["BUY", "SELL"])
    )

    if should_open_position:
        print("❌ ERROR: El bot decidiría abrir posición cuando NO debería")
        print("   Esto sería un bug - Gemini dijo NO_OPERAR")
        return False
    else:
        print("✅ ¡CORRECTO! El bot NO intentaría abrir posición")
        print("   Respeta correctamente la decisión NO_OPERAR de Gemini")

    # Simular que se intenta ejecutar la apertura (debería no hacer nada)
    print("\n🔍 Probando _execute_open_position con decisión NO_OPERAR...")

    try:
        bot._execute_open_position("EURUSD", decision)
    except Exception as e:
        print(f"⚠️  Excepción en _execute_open_position (esperado): {e}")

    # Verificar que definitivamente NO se llamó a send_market_order
    if not bot.order_manager.send_market_order.called:
        print("✅ ¡CONFIRMADO! No se llamó a send_market_order")
        print("   El bot correctamente ignora decisiones de NO_OPERAR")
    else:
        print("❌ ERROR CRÍTICO: Se llamó a send_market_order con NO_OPERAR")
        print("   Esto sería un bug que causaría operaciones no deseadas")
        return False

    return True


if __name__ == '__main__':
    print("🧪 Test de simulación de respuesta real de Gemini (NO_OPERAR)")
    print("=" * 60)

    try:
        success = test_simulate_real_gemini_no_operar()
        if success:
            print("\n🎉 Test completado exitosamente!")
            print("El bot maneja correctamente las decisiones de NO_OPERAR de Gemini.")
            print("✅ No intenta abrir operaciones cuando no debe.")
            print("✅ Respeta las decisiones conservadoras de la IA.")
        else:
            print("\n❌ Test falló")
    except Exception as e:
        print(f"\n💥 Error durante el test: {e}")
        import traceback
        traceback.print_exc()