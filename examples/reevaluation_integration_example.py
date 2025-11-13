"""
Ejemplo de uso de ReevaluationIntegration - T26
Integración del sistema de reevaluación periódica con BotInstance

Este ejemplo demuestra cómo integrar el sistema de reevaluación
periódica en un bot de trading.

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
    data_extractor.extract_market_data = AsyncMock(return_value={
        "symbol": "EURUSD",
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
    gemini_client.send_prompt = AsyncMock(return_value={
        "content": '{"decision": "MANTENER"}',
        "tokens": 150,
        "cost": 0.001
    })
    
    # Response Parser mock
    response_parser = Mock()
    response_parser.parse = Mock(return_value={
        "decision": "MANTENER",
        "sl": None,
        "tp": None
    })
    
    # Position Manager mock
    position_manager = Mock()
    position_manager.get_positions = Mock(return_value=[])
    position_manager.get_open_positions = Mock(return_value=[])
    position_manager.modify_position = Mock(return_value=True)
    position_manager.close_position = Mock(return_value=True)
    
    return {
        "mt5_connector": mt5_connector,
        "data_extractor": data_extractor,
        "prompt_builder": prompt_builder,
        "gemini_client": gemini_client,
        "response_parser": response_parser,
        "position_manager": position_manager
    }


async def ejemplo_1_configuracion_basica():
    """
    Ejemplo 1: Configuración básica de integración
    """
    print("\n" + "="*70)
    print("EJEMPLO 1: Configuración básica")
    print("="*70)
    
    # Configuración simple
    config = IntegrationConfig(
        enabled=True,
        interval_minutes=10,
        mode="persistent"
    )
    
    # Crear componentes mock
    components = create_mock_components()
    
    # Crear integración
    integration = ReevaluationIntegration(
        bot_id=1,
        bot_name="ScalpingBot",
        magic_number=100101,
        config=config,
        **components
    )
    
    print(f"\n✓ Integración creada: {integration}")
    print(f"  - Intervalo: {config.interval_minutes} minutos")
    print(f"  - Modo: {config.mode}")
    print(f"  - Estado: {'Habilitado' if config.enabled else 'Deshabilitado'}")


async def ejemplo_2_iniciar_y_detener():
    """
    Ejemplo 2: Iniciar y detener reevaluación periódica
    """
    print("\n" + "="*70)
    print("EJEMPLO 2: Iniciar y detener reevaluación")
    print("="*70)
    
    config = IntegrationConfig(
        enabled=True,
        interval_minutes=10,
        mode="persistent"
    )
    
    components = create_mock_components()
    
    integration = ReevaluationIntegration(
        bot_id=1,
        bot_name="ScalpingBot",
        magic_number=100101,
        config=config,
        **components
    )
    
    # Iniciar
    print("\n1. Iniciando reevaluación periódica...")
    started = await integration.start()
    print(f"   {'✓' if started else '✗'} Estado: {'Iniciado' if started else 'Error'}")
    print(f"   Running: {integration.is_running()}")
    
    # Esperar un momento
    print("\n2. Esperando 2 segundos...")
    await asyncio.sleep(2)
    
    # Detener
    print("\n3. Deteniendo reevaluación periódica...")
    stopped = await integration.stop()
    print(f"   {'✓' if stopped else '✗'} Estado: {'Detenido' if stopped else 'Error'}")
    print(f"   Running: {integration.is_running()}")


async def ejemplo_3_configuracion_avanzada():
    """
    Ejemplo 3: Configuración avanzada con ventana de trading y límites
    """
    print("\n" + "="*70)
    print("EJEMPLO 3: Configuración avanzada")
    print("="*70)
    
    config = IntegrationConfig(
        enabled=True,
        interval_minutes=15,
        mode="new",
        trading_window={
            "timezone": "America/Lima",
            "start": "06:00",
            "end": "13:00",
            "days": ["MON", "TUE", "WED", "THU", "FRI"]
        },
        limits={
            "max_reevaluations_per_position": 50,
            "max_cost_per_position_usd": 2.0
        }
    )
    
    components = create_mock_components()
    
    integration = ReevaluationIntegration(
        bot_id=2,
        bot_name="VisualBot",
        magic_number=200201,
        config=config,
        **components
    )
    
    print(f"\n✓ Integración creada con configuración avanzada")
    print(f"\n  Configuración:")
    print(f"  - Intervalo: {config.interval_minutes} minutos")
    print(f"  - Modo: {config.mode} (nueva conversación cada vez)")
    if config.trading_window:
        print(f"  - Ventana: {config.trading_window['start']} - {config.trading_window['end']}")
        print(f"  - Timezone: {config.trading_window['timezone']}")
        print(f"  - Días: {', '.join(config.trading_window['days'])}")
    if config.limits:
        print(f"\n  Límites:")
        print(f"  - Max reevaluaciones: {config.limits['max_reevaluations_per_position']}")
        print(f"  - Max costo: ${config.limits['max_cost_per_position_usd']}")


async def ejemplo_4_estadisticas():
    """
    Ejemplo 4: Obtener estadísticas de reevaluación
    """
    print("\n" + "="*70)
    print("EJEMPLO 4: Estadísticas de reevaluación")
    print("="*70)
    
    config = IntegrationConfig(
        enabled=True,
        interval_minutes=10,
        mode="persistent"
    )
    
    components = create_mock_components()
    
    integration = ReevaluationIntegration(
        bot_id=1,
        bot_name="ScalpingBot",
        magic_number=100101,
        config=config,
        **components
    )
    
    # Obtener estadísticas
    stats = integration.get_stats()
    
    print(f"\n✓ Estadísticas de integración:")
    print(f"\n  General:")
    print(f"  - Total ciclos: {stats['total_cycles']}")
    print(f"  - Total posiciones evaluadas: {stats['total_positions_evaluated']}")
    print(f"  - Reevaluaciones exitosas: {stats['successful_reevaluations']}")
    print(f"  - Reevaluaciones fallidas: {stats['failed_reevaluations']}")
    print(f"  - Tasa de éxito: {stats['success_rate']:.1f}%")
    print(f"\n  Costos:")
    print(f"  - Total tokens: {stats['total_tokens']}")
    print(f"  - Total costo: ${stats['total_cost_usd']:.4f}")
    print(f"  - Costo promedio: ${stats['avg_cost_per_reevaluation']:.4f}")


async def ejemplo_5_multiples_bots():
    """
    Ejemplo 5: Múltiples bots con configuraciones diferentes
    """
    print("\n" + "="*70)
    print("EJEMPLO 5: Múltiples bots con diferentes modos")
    print("="*70)
    
    components = create_mock_components()
    
    # Bot 1: Numérico con conversación persistente
    config1 = IntegrationConfig(
        enabled=True,
        interval_minutes=10,
        mode="persistent"
    )
    
    bot1 = ReevaluationIntegration(
        bot_id=1,
        bot_name="NumericBot",
        magic_number=100101,
        config=config1,
        **components
    )
    
    # Bot 2: Visual con nueva conversación
    config2 = IntegrationConfig(
        enabled=True,
        interval_minutes=15,
        mode="new"
    )
    
    bot2 = ReevaluationIntegration(
        bot_id=2,
        bot_name="VisualBot",
        magic_number=200201,
        config=config2,
        **components
    )
    
    # Bot 3: Híbrido con conversación persistente
    config3 = IntegrationConfig(
        enabled=True,
        interval_minutes=20,
        mode="persistent"
    )
    
    bot3 = ReevaluationIntegration(
        bot_id=3,
        bot_name="HybridBot",
        magic_number=300301,
        config=config3,
        **components
    )
    
    print(f"\n✓ Tres bots configurados con modos diferentes:")
    print(f"\n  Bot 1 ({bot1.bot_name}):")
    print(f"  - Modo: {config1.mode} (contexto persistente)")
    print(f"  - Intervalo: {config1.interval_minutes} min")
    
    print(f"\n  Bot 2 ({bot2.bot_name}):")
    print(f"  - Modo: {config2.mode} (nueva conversación)")
    print(f"  - Intervalo: {config2.interval_minutes} min")
    
    print(f"\n  Bot 3 ({bot3.bot_name}):")
    print(f"  - Modo: {config3.mode} (contexto persistente)")
    print(f"  - Intervalo: {config3.interval_minutes} min")


async def ejemplo_6_uso_completo():
    """
    Ejemplo 6: Caso de uso completo con ciclo de vida
    """
    print("\n" + "="*70)
    print("EJEMPLO 6: Caso de uso completo")
    print("="*70)
    
    # 1. Configurar
    print("\n1. Configurando integración...")
    config = IntegrationConfig(
        enabled=True,
        interval_minutes=10,
        mode="persistent",
        trading_window={
            "timezone": "America/Lima",
            "start": "06:00",
            "end": "13:00",
            "days": ["MON", "TUE", "WED", "THU", "FRI"]
        }
    )
    
    components = create_mock_components()
    
    integration = ReevaluationIntegration(
        bot_id=1,
        bot_name="ProductionBot",
        magic_number=100101,
        config=config,
        **components
    )
    print(f"   ✓ Integración configurada: {integration}")
    
    # 2. Iniciar
    print("\n2. Iniciando reevaluación periódica...")
    await integration.start()
    print(f"   ✓ Running: {integration.is_running()}")
    
    # 3. Simular operación durante 5 segundos
    print("\n3. Operando (simulando 5 segundos)...")
    await asyncio.sleep(5)
    
    # 4. Obtener estadísticas intermedias
    print("\n4. Estadísticas intermedias:")
    stats = integration.get_stats()
    print(f"   - Ciclos ejecutados: {stats['total_cycles']}")
    print(f"   - Posiciones evaluadas: {stats['total_positions_evaluated']}")
    
    # 5. Detener
    print("\n5. Deteniendo...")
    await integration.stop()
    print(f"   ✓ Running: {integration.is_running()}")
    
    # 6. Estadísticas finales
    print("\n6. Estadísticas finales:")
    final_stats = integration.get_stats()
    print(f"   - Total ciclos: {final_stats['total_cycles']}")
    print(f"   - Total costo: ${final_stats['total_cost_usd']:.4f}")
    print(f"   - Tasa de éxito: {final_stats['success_rate']:.1f}%")


async def main():
    """Ejecutar todos los ejemplos"""
    print("\n" + "="*70)
    print("EJEMPLOS DE REEVALUATION INTEGRATION - T26")
    print("="*70)
    
    try:
        await ejemplo_1_configuracion_basica()
        await ejemplo_2_iniciar_y_detener()
        await ejemplo_3_configuracion_avanzada()
        await ejemplo_4_estadisticas()
        await ejemplo_5_multiples_bots()
        await ejemplo_6_uso_completo()
        
        print("\n" + "="*70)
        print("✓ TODOS LOS EJEMPLOS EJECUTADOS EXITOSAMENTE")
        print("="*70 + "\n")
    
    except Exception as e:
        print(f"\n✗ Error en ejemplos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
