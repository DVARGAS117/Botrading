"""
Ejemplo de uso de Reevaluación Independiente de Market y Limit - T16
Demostración de la funcionalidad de reevaluación dual independiente

Este ejemplo muestra cómo utilizar la nueva funcionalidad de reevaluación
independiente para órdenes Market y Limit, permitiendo decisiones divergentes
en cada tipo de orden.

Author: Botrading Team
Date: 2025-11-13
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.reevaluation_integration import (
    ReevaluationIntegration,
    IntegrationConfig
)
from unittest.mock import Mock, AsyncMock


def create_mock_components():
    """Crear mocks de componentes necesarios"""
    # MT5 Connector mock
    mt5_connector = Mock()
    mt5_connector.verify_connection = Mock(return_value=True)
    mt5_connector.disconnect = Mock()

    # Data Extractor mock
    data_extractor = Mock()
    data_extractor.extract_current_data = AsyncMock(return_value={
        "symbol": "EURUSD",
        "current_price": 1.1000,
        "timeframes": {
            "5M": [],
            "15M": [],
            "1H": []
        }
    })

    # Prompt Builder mock
    prompt_builder = Mock()
    prompt_builder.build_reevaluation_prompt = Mock(return_value="prompt")

    # Gemini Client mock
    gemini_client = Mock()
    gemini_client.send_prompt = AsyncMock(return_value=Mock(
        success=True,
        content='{"decision": "MANTENER"}',
        tokens_input=100,
        tokens_output=50,
        cost=0.001,
        error_message=""
    ))

    # Response Parser mock
    response_parser = Mock()
    response_parser.parse_reevaluation = Mock(return_value=Mock(
        is_valid=True,
        decision_type=Mock(value="MANTENER"),
        reasoning="Condiciones estables",
        new_stop_loss=None,
        new_take_profit=None,
        error_message=""
    ))

    # Position Manager mock
    position_manager = Mock()

    return {
        "mt5_connector": mt5_connector,
        "data_extractor": data_extractor,
        "prompt_builder": prompt_builder,
        "gemini_client": gemini_client,
        "response_parser": response_parser,
        "position_manager": position_manager
    }


async def ejemplo_1_deteccion_ordenes_duales():
    """
    Ejemplo 1: Detección automática de órdenes duales
    """
    print("\n" + "="*70)
    print("EJEMPLO 1: Detección de Órdenes Duales")
    print("="*70)

    # Configurar posiciones mock con órdenes duales
    mock_positions = [
        {
            "ticket": "12345",
            "symbol": "EURUSD",
            "magic": 100000,  # Market
            "direction": "BUY",
            "entry_price": 1.0950,
            "current_sl": 1.0900,
            "current_tp": 1.1100,
            "current_price": 1.1000,
            "profit_pips": 50.0
        },
        {
            "ticket": "12346",
            "symbol": "EURUSD",
            "magic": 100001,  # Limit
            "direction": "BUY",
            "entry_price": 1.0950,
            "current_sl": 1.0900,
            "current_tp": 1.1100,
            "current_price": 1.1000,
            "profit_pips": 50.0
        }
    ]

    components = create_mock_components()
    components["position_manager"].get_positions = Mock(return_value=mock_positions)

    # Crear integración
    config = IntegrationConfig(enabled=True, interval_minutes=10, mode="persistent")
    integration = ReevaluationIntegration(
        bot_id=1,
        bot_name="DualBot",
        magic_number=100000,
        config=config,
        **components
    )

    # Detectar grupos duales
    dual_groups = integration._detect_dual_order_groups()

    print(f"\n✅ Detección completada:")
    print(f"   Grupos duales encontrados: {len(dual_groups)}")

    if dual_groups:
        group = dual_groups[0]
        print(f"\n   Grupo Dual #1:")
        print(f"   - Market Magic: {group['market_magic']}")
        print(f"   - Limit Magic: {group['limit_magic']}")
        print(f"   - Total posiciones: {len(group['positions'])}")
        print(f"   - Posiciones: {[p['ticket'] for p in group['positions']]}")


async def ejemplo_2_reevaluacion_dual_independiente():
    """
    Ejemplo 2: Reevaluación dual con decisiones divergentes
    """
    print("\n" + "="*70)
    print("EJEMPLO 2: Reevaluación Dual Independiente")
    print("="*70)

    # Configurar posiciones duales
    mock_positions = [
        {
            "ticket": "12345",
            "symbol": "EURUSD",
            "magic": 100000,  # Market
            "direction": "BUY",
            "entry_price": 1.0950,
            "current_sl": 1.0900,
            "current_tp": 1.1100,
            "current_price": 1.1000,
            "profit_pips": 50.0
        },
        {
            "ticket": "12346",
            "symbol": "EURUSD",
            "magic": 100001,  # Limit
            "direction": "BUY",
            "entry_price": 1.0950,
            "current_sl": 1.0900,
            "current_tp": 1.1100,
            "current_price": 1.1000,
            "profit_pips": 50.0
        }
    ]

    components = create_mock_components()
    components["position_manager"].get_positions = Mock(return_value=mock_positions)

    # Configurar respuestas diferentes para Market y Limit
    from src.core.reevaluation_manager import ReevaluationResult

    market_result = ReevaluationResult(
        success=True,
        action_taken="MANTENER",
        reasoning="Tendencia alcista fuerte, mantener Market",
        tokens_used=150,
        cost=0.001
    )

    limit_result = ReevaluationResult(
        success=True,
        action_taken="CERRAR",
        reasoning="Limit no activada después de tiempo, cerrar para liberar capital",
        tokens_used=120,
        cost=0.0008
    )

    # Mock del manager con respuestas diferentes
    async def mock_reevaluate_positions(bot_id, magic_number):
        if magic_number == 100000:  # Market
            return [market_result]
        elif magic_number == 100001:  # Limit
            return [limit_result]
        return []

    components["position_manager"].reevaluate_positions = mock_reevaluate_positions

    # Crear integración
    config = IntegrationConfig(enabled=True, interval_minutes=10, mode="persistent")
    integration = ReevaluationIntegration(
        bot_id=1,
        bot_name="DualBot",
        magic_number=100000,
        config=config,
        **components
    )

    # Reemplazar manager con mock
    mock_manager = Mock()
    mock_manager.reevaluate_positions = mock_reevaluate_positions
    integration.manager = mock_manager

    # Ejecutar reevaluación dual
    print("\n🔄 Ejecutando reevaluación dual independiente...")
    results = await integration.reevaluate_dual_orders()

    print(f"\n✅ Reevaluación completada: {len(results)} resultados")

    # Mostrar resultados
    for result in results:
        print(f"\n📊 {result['type']} (Magic: {result['magic']}):")
        print(f"   Acción: {result['action']}")
        print(f"   Razonamiento: {result['reasoning']}")
        print(f"   Tokens: {result['tokens']}")
        print(f"   Costo: ${result['cost']:.4f}")
        print(f"   Éxito: {'✅' if result['success'] else '❌'}")

    # Resumen
    market_action = next((r['action'] for r in results if r['type'] == 'Market'), None)
    limit_action = next((r['action'] for r in results if r['type'] == 'Limit'), None)

    print(f"\n🎯 Resumen de decisiones:")
    print(f"   Market: {market_action}")
    print(f"   Limit: {limit_action}")

    if market_action != limit_action:
        print("   💡 ¡Decisiones divergentes! Flexibilidad estratégica lograda.")
    else:
        print("   📋 Decisiones consistentes en ambas órdenes.")


async def ejemplo_3_estadisticas_dual():
    """
    Ejemplo 3: Estadísticas de reevaluación dual
    """
    print("\n" + "="*70)
    print("EJEMPLO 3: Estadísticas de Reevaluación Dual")
    print("="*70)

    components = create_mock_components()

    # Crear integración
    config = IntegrationConfig(enabled=True, interval_minutes=10, mode="persistent")
    integration = ReevaluationIntegration(
        bot_id=1,
        bot_name="DualBot",
        magic_number=100000,
        config=config,
        **components
    )

    # Simular estadísticas de varias reevaluaciones
    integration._dual_stats = {
        "total_dual_groups": 10,
        "successful_market_reevaluations": 8,
        "successful_limit_reevaluations": 6,
        "failed_market_reevaluations": 2,
        "failed_limit_reevaluations": 4,
        "total_dual_cost_usd": 0.025,
        "total_dual_tokens": 2500
    }

    # Obtener estadísticas
    stats = integration.get_dual_stats()

    print(f"\n📈 Estadísticas de Reevaluación Dual:")
    print(f"\n  General:")
    print(f"  - Grupos duales procesados: {stats['total_dual_groups']}")
    print(f"  - Costo total: ${stats['total_dual_cost_usd']:.4f}")
    print(f"  - Tokens totales: {stats['total_dual_tokens']}")

    print(f"\n  Tasas de Éxito:")
    print(f"  - Market: {stats['market_success_rate']:.1f}% ({stats['successful_market_reevaluations']}/{stats['total_dual_groups']})")
    print(f"  - Limit: {stats['limit_success_rate']:.1f}% ({stats['successful_limit_reevaluations']}/{stats['total_dual_groups']})")
    print(f"  - General: {stats['overall_success_rate']:.1f}%")

    print(f"\n  Análisis:")
    if stats['market_success_rate'] > stats['limit_success_rate']:
        print("  💪 Market tiene mejor rendimiento que Limit")
    elif stats['limit_success_rate'] > stats['market_success_rate']:
        print("  🎯 Limit tiene mejor rendimiento que Market")
    else:
        print("  ⚖️  Market y Limit tienen rendimiento similar")


async def ejemplo_4_manejo_errores_parciales():
    """
    Ejemplo 4: Manejo de errores parciales en reevaluación dual
    """
    print("\n" + "="*70)
    print("EJEMPLO 4: Manejo de Errores Parciales")
    print("="*70)

    # Configurar posiciones duales
    mock_positions = [
        {
            "ticket": "12345",
            "symbol": "EURUSD",
            "magic": 100000,  # Market
            "direction": "BUY",
            "entry_price": 1.0950,
            "current_sl": 1.0900,
            "current_tp": 1.1100,
            "current_price": 1.1000,
            "profit_pips": 50.0
        },
        {
            "ticket": "12346",
            "symbol": "EURUSD",
            "magic": 100001,  # Limit
            "direction": "BUY",
            "entry_price": 1.0950,
            "current_sl": 1.0900,
            "current_tp": 1.1100,
            "current_price": 1.1000,
            "profit_pips": 50.0
        }
    ]

    components = create_mock_components()
    components["position_manager"].get_positions = Mock(return_value=mock_positions)

    # Configurar: Market OK, Limit falla
    from src.core.reevaluation_manager import ReevaluationResult

    market_result = ReevaluationResult(
        success=True,
        action_taken="MANTENER",
        reasoning="Market funcionando correctamente",
        tokens_used=150,
        cost=0.001
    )

    limit_result = ReevaluationResult(
        success=False,
        action_taken="ERROR",
        error_message="Error de conexión con IA para Limit",
        tokens_used=0,
        cost=0.0
    )

    async def mock_reevaluate_positions(bot_id, magic_number):
        if magic_number == 100000:  # Market
            return [market_result]
        elif magic_number == 100001:  # Limit
            return [limit_result]
        return []

    components["position_manager"].reevaluate_positions = mock_reevaluate_positions

    # Crear integración
    config = IntegrationConfig(enabled=True, interval_minutes=10, mode="persistent")
    integration = ReevaluationIntegration(
        bot_id=1,
        bot_name="DualBot",
        magic_number=100000,
        config=config,
        **components
    )

    # Reemplazar manager
    mock_manager = Mock()
    mock_manager.reevaluate_positions = mock_reevaluate_positions
    integration.manager = mock_manager

    # Ejecutar reevaluación dual
    print("\n🔄 Ejecutando reevaluación dual con error parcial...")
    results = await integration.reevaluate_dual_orders()

    print(f"\n✅ Reevaluación completada: {len(results)} resultados")

    # Mostrar resultados
    success_count = 0
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"\n{status} {result['type']} (Magic: {result['magic']}):")
        if result['success']:
            print(f"   Acción: {result['action']}")
            print(f"   Razonamiento: {result['reasoning']}")
            success_count += 1
        else:
            print(f"   Error: {result['error']}")

    print(f"\n🛡️  Resumen de robustez:")
    print(f"   Resultados exitosos: {success_count}/{len(results)}")
    print("   💪 Sistema continuó operando a pesar del error parcial")


async def main():
    """Ejecutar todos los ejemplos"""
    print("\n" + "="*70)
    print("EJEMPLOS DE REEVALUACIÓN DUAL INDEPENDIENTE - T16")
    print("="*70)

    try:
        await ejemplo_1_deteccion_ordenes_duales()
        await ejemplo_2_reevaluacion_dual_independiente()
        await ejemplo_3_estadisticas_dual()
        await ejemplo_4_manejo_errores_parciales()

        print("\n" + "="*70)
        print("✅ TODOS LOS EJEMPLOS EJECUTADOS EXITOSAMENTE")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error en ejemplos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())