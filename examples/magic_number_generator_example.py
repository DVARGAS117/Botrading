"""
Ejemplos de uso del MagicNumberGenerator

Este archivo demuestra cómo usar el MagicNumberGenerator para generar
y decodificar Magic Numbers únicos en el sistema de trading.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T17 - Generación de Magic Number único con estructura
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para poder importar src
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.core.magic_number_generator import (
    MagicNumberGenerator,
    MagicNumberError,
    InvalidBotIdError,
    InvalidIAConfigIdError,
    InvalidOrderTypeError
)


def example_1_basic_generation():
    """
    Ejemplo 1: Generación básica de Magic Numbers
    
    Demuestra cómo generar Magic Numbers para diferentes bots,
    configuraciones de IA y tipos de órdenes.
    """
    print("=" * 70)
    print("EJEMPLO 1: Generación Básica de Magic Numbers")
    print("=" * 70)
    
    generator = MagicNumberGenerator()
    
    # Bot 1, IA Config 0, Market Order
    magic1 = generator.generate(bot_id=1, ia_config_id=0, order_type="market")
    print(f"\nBot 1, IA 0, Market: {magic1}")
    print(f"  -> Estructura: [1][0][0][000]")
    
    # Bot 2, IA Config 3, Limit Order
    magic2 = generator.generate(bot_id=2, ia_config_id=3, order_type="limit")
    print(f"\nBot 2, IA 3, Limit: {magic2}")
    print(f"  -> Estructura: [2][3][1][000]")
    
    # Bot 5, IA Config 9, Market Order
    magic3 = generator.generate(bot_id=5, ia_config_id=9, order_type="market")
    print(f"\nBot 5, IA 9, Market: {magic3}")
    print(f"  -> Estructura: [5][9][0][000]")
    
    print(f"\n[OK] Todos los Magic Numbers son unicos y de 6 digitos")


def example_2_sequences():
    """
    Ejemplo 2: Uso de secuencias para múltiples operaciones
    
    Demuestra cómo usar secuencias cuando un bot necesita abrir
    múltiples operaciones con los mismos parámetros.
    """
    print("\n\n" + "=" * 70)
    print("EJEMPLO 2: Secuencias para Múltiples Operaciones")
    print("=" * 70)
    
    generator = MagicNumberGenerator()
    
    print("\nBot 1 abre 5 órdenes Market con IA Config 0:")
    
    for i in range(5):
        magic = generator.generate(
            bot_id=1,
            ia_config_id=0,
            order_type="market",
            sequence=i
        )
        print(f"  Operación {i+1}: {magic} (Secuencia: {i})")
    
    print(f"\n✅ Cada operación tiene un Magic Number único")


def example_3_decoding():
    """
    Ejemplo 3: Decodificación de Magic Numbers
    
    Demuestra cómo decodificar Magic Numbers para obtener
    información sobre el bot, configuración IA, tipo y secuencia.
    """
    print("\n\n" + "=" * 70)
    print("EJEMPLO 3: Decodificación de Magic Numbers")
    print("=" * 70)
    
    generator = MagicNumberGenerator()
    
    # Generar algunos magic numbers
    magic_numbers = [
        generator.generate(1, 0, "market", 0),
        generator.generate(2, 3, "limit", 456),
        generator.generate(5, 9, "market", 999)
    ]
    
    print("\nDecodificando Magic Numbers:")
    
    for magic in magic_numbers:
        components = generator.decode(magic)
        print(f"\n  Magic Number: {magic}")
        print(f"    Bot ID: {components.bot_id}")
        print(f"    IA Config ID: {components.ia_config_id}")
        print(f"    Order Type: {components.order_type}")
        print(f"    Sequence: {components.sequence}")
    
    print(f"\n✅ Decodificación exitosa de todos los Magic Numbers")


def example_4_filtering_positions():
    """
    Ejemplo 4: Filtrado de posiciones por bot
    
    Simula cómo filtrar posiciones de MT5 usando Magic Numbers
    para identificar operaciones de un bot específico.
    """
    print("\n\n" + "=" * 70)
    print("EJEMPLO 4: Filtrado de Posiciones por Bot")
    print("=" * 70)
    
    generator = MagicNumberGenerator()
    
    # Simular posiciones de diferentes bots
    simulated_positions = [
        {"symbol": "EURUSD", "magic": generator.generate(1, 0, "market", 0), "profit": 15.50},
        {"symbol": "GBPUSD", "magic": generator.generate(2, 3, "limit", 0), "profit": -5.20},
        {"symbol": "USDJPY", "magic": generator.generate(1, 0, "market", 1), "profit": 23.40},
        {"symbol": "AUDUSD", "magic": generator.generate(3, 5, "market", 0), "profit": 8.90},
        {"symbol": "EURJPY", "magic": generator.generate(1, 1, "limit", 0), "profit": 12.30},
    ]
    
    print("\nPosiciones totales:", len(simulated_positions))
    
    # Filtrar posiciones del Bot 1
    bot1_positions = []
    for position in simulated_positions:
        components = generator.decode(position["magic"])
        if components.bot_id == 1:
            bot1_positions.append(position)
    
    print(f"\nPosiciones del Bot 1: {len(bot1_positions)}")
    for pos in bot1_positions:
        components = generator.decode(pos["magic"])
        print(f"  {pos['symbol']}: ${pos['profit']:.2f} "
              f"(IA {components.ia_config_id}, {components.order_type})")
    
    # Calcular P/L del Bot 1
    bot1_pl = sum(pos["profit"] for pos in bot1_positions)
    print(f"\nP/L total Bot 1: ${bot1_pl:.2f}")
    print(f"\n✅ Filtrado exitoso por Bot ID")


def example_5_performance_analysis():
    """
    Ejemplo 5: Análisis de rendimiento por configuración de IA
    
    Demuestra cómo analizar el rendimiento de diferentes
    configuraciones de IA usando Magic Numbers.
    """
    print("\n\n" + "=" * 70)
    print("EJEMPLO 5: Análisis de Rendimiento por Configuración IA")
    print("=" * 70)
    
    generator = MagicNumberGenerator()
    
    # Simular resultados de diferentes configuraciones
    simulated_results = [
        {"magic": generator.generate(1, 0, "market", 0), "profit": 15.50},
        {"magic": generator.generate(1, 0, "market", 1), "profit": 23.40},
        {"magic": generator.generate(1, 0, "market", 2), "profit": -8.20},
        {"magic": generator.generate(1, 1, "limit", 0), "profit": 12.30},
        {"magic": generator.generate(1, 1, "limit", 1), "profit": 18.90},
        {"magic": generator.generate(1, 1, "limit", 2), "profit": 7.60},
        {"magic": generator.generate(1, 2, "market", 0), "profit": -15.40},
        {"magic": generator.generate(1, 2, "market", 1), "profit": 5.20},
    ]
    
    # Agrupar por configuración IA
    from collections import defaultdict
    results_by_ia = defaultdict(list)
    
    for result in simulated_results:
        components = generator.decode(result["magic"])
        results_by_ia[components.ia_config_id].append(result["profit"])
    
    print("\nRendimiento por Configuración IA (Bot 1):")
    
    for ia_config_id in sorted(results_by_ia.keys()):
        profits = results_by_ia[ia_config_id]
        total_pl = sum(profits)
        avg_pl = total_pl / len(profits)
        win_rate = len([p for p in profits if p > 0]) / len(profits) * 100
        
        print(f"\n  IA Config {ia_config_id}:")
        print(f"    Operaciones: {len(profits)}")
        print(f"    P/L Total: ${total_pl:.2f}")
        print(f"    P/L Promedio: ${avg_pl:.2f}")
        print(f"    Win Rate: {win_rate:.1f}%")
    
    print(f"\n✅ Análisis completado - IA Config 1 es la mejor")


def example_6_market_vs_limit():
    """
    Ejemplo 6: Comparación Market vs Limit
    
    Demuestra cómo comparar el rendimiento de órdenes Market
    vs Limit usando Magic Numbers.
    """
    print("\n\n" + "=" * 70)
    print("EJEMPLO 6: Comparación Market vs Limit")
    print("=" * 70)
    
    generator = MagicNumberGenerator()
    
    # Simular operaciones
    simulated_operations = [
        {"magic": generator.generate(1, 0, "market", 0), "profit": 15.50},
        {"magic": generator.generate(1, 0, "market", 1), "profit": 23.40},
        {"magic": generator.generate(1, 0, "market", 2), "profit": -8.20},
        {"magic": generator.generate(1, 0, "limit", 0), "profit": 12.30},
        {"magic": generator.generate(1, 0, "limit", 1), "profit": 18.90},
        {"magic": generator.generate(1, 0, "limit", 2), "profit": 7.60},
    ]
    
    # Separar por tipo
    market_ops = []
    limit_ops = []
    
    for op in simulated_operations:
        components = generator.decode(op["magic"])
        if components.order_type == "market":
            market_ops.append(op["profit"])
        else:
            limit_ops.append(op["profit"])
    
    # Calcular métricas
    market_total = sum(market_ops)
    limit_total = sum(limit_ops)
    market_avg = market_total / len(market_ops)
    limit_avg = limit_total / len(limit_ops)
    
    print("\n📊 Comparación de Rendimiento:")
    
    print(f"\n  Market Orders:")
    print(f"    Operaciones: {len(market_ops)}")
    print(f"    P/L Total: ${market_total:.2f}")
    print(f"    P/L Promedio: ${market_avg:.2f}")
    
    print(f"\n  Limit Orders:")
    print(f"    Operaciones: {len(limit_ops)}")
    print(f"    P/L Total: ${limit_total:.2f}")
    print(f"    P/L Promedio: ${limit_avg:.2f}")
    
    winner = "Market" if market_total > limit_total else "Limit"
    print(f"\n🏆 Ganador: {winner} Orders")
    print(f"\n✅ Comparación completada")


def example_7_error_handling():
    """
    Ejemplo 7: Manejo de errores
    
    Demuestra cómo el generador valida parámetros y lanza
    excepciones específicas para errores.
    """
    print("\n\n" + "=" * 70)
    print("EJEMPLO 7: Manejo de Errores")
    print("=" * 70)
    
    generator = MagicNumberGenerator()
    
    print("\nProbando validaciones:")
    
    # Bot ID inválido
    print("\n1. Bot ID inválido (bot_id=0):")
    try:
        generator.generate(bot_id=0, ia_config_id=0, order_type="market")
    except InvalidBotIdError as e:
        print(f"   ❌ Error capturado: {e}")
    
    # IA Config ID inválido
    print("\n2. IA Config ID inválido (ia_config_id=10):")
    try:
        generator.generate(bot_id=1, ia_config_id=10, order_type="market")
    except InvalidIAConfigIdError as e:
        print(f"   ❌ Error capturado: {e}")
    
    # Order Type inválido
    print("\n3. Order Type inválido (order_type='stop'):")
    try:
        generator.generate(bot_id=1, ia_config_id=0, order_type="stop")
    except InvalidOrderTypeError as e:
        print(f"   ❌ Error capturado: {e}")
    
    # Sequence overflow
    print("\n4. Sequence overflow (sequence=1000):")
    try:
        generator.generate(bot_id=1, ia_config_id=0, order_type="market", sequence=1000)
    except MagicNumberError as e:
        print(f"   ❌ Error capturado: {e}")
    
    # Magic Number inválido en decodificación
    print("\n5. Magic Number inválido (12345 - solo 5 dígitos):")
    try:
        generator.decode(12345)
    except MagicNumberError as e:
        print(f"   ❌ Error capturado: {e}")
    
    print(f"\n✅ Todas las validaciones funcionan correctamente")


def example_8_integration_workflow():
    """
    Ejemplo 8: Flujo de trabajo completo
    
    Demuestra un flujo de trabajo completo desde la generación
    del Magic Number hasta el análisis de resultados.
    """
    print("\n\n" + "=" * 70)
    print("EJEMPLO 8: Flujo de Trabajo Completo")
    print("=" * 70)
    
    generator = MagicNumberGenerator()
    
    # 1. Bot decide abrir operación
    print("\n📝 PASO 1: Bot decide abrir operación")
    bot_id = 1
    ia_config_id = 0
    order_type = "market"
    print(f"  Bot ID: {bot_id}")
    print(f"  IA Config: {ia_config_id}")
    print(f"  Tipo: {order_type}")
    
    # 2. Generar Magic Number
    print("\n🔢 PASO 2: Generar Magic Number")
    magic = generator.generate(bot_id, ia_config_id, order_type, sequence=0)
    print(f"  Magic Number: {magic}")
    
    # 3. Simular envío a MT5
    print("\n📤 PASO 3: Enviar orden a MT5")
    order_params = {
        "symbol": "EURUSD",
        "volume": 0.01,
        "sl": 1.0500,
        "tp": 1.0600,
        "magic": magic
    }
    print(f"  Parámetros: {order_params}")
    
    # 4. Simular consulta de posición
    print("\n🔍 PASO 4: Consultar posición en MT5")
    simulated_position = {
        "ticket": 12345,
        "symbol": "EURUSD",
        "magic": magic,
        "profit": 15.50
    }
    print(f"  Posición encontrada: Ticket {simulated_position['ticket']}")
    
    # 5. Decodificar Magic Number
    print("\n🔓 PASO 5: Decodificar Magic Number")
    components = generator.decode(simulated_position["magic"])
    print(f"  Bot: {components.bot_id}")
    print(f"  IA Config: {components.ia_config_id}")
    print(f"  Tipo: {components.order_type}")
    print(f"  Secuencia: {components.sequence}")
    
    # 6. Verificar que es del bot correcto
    print("\n✅ PASO 6: Verificar pertenencia")
    if components.bot_id == bot_id:
        print(f"  ✓ La posición pertenece al Bot {bot_id}")
        print(f"  ✓ Profit: ${simulated_position['profit']:.2f}")
    
    print(f"\n🎉 Flujo completado exitosamente")


def example_9_components_to_dict():
    """
    Ejemplo 9: Exportar componentes a diccionario
    
    Demuestra cómo convertir componentes decodificados a
    diccionario para persistencia o API responses.
    """
    print("\n\n" + "=" * 70)
    print("EJEMPLO 9: Exportar Componentes a Diccionario")
    print("=" * 70)
    
    generator = MagicNumberGenerator()
    
    # Generar y decodificar
    magic = generator.generate(2, 5, "limit", 123)
    components = generator.decode(magic)
    
    # Convertir a diccionario
    components_dict = components.to_dict()
    
    print("\nComponentes como diccionario:")
    print(f"  {components_dict}")
    
    # Simular uso en API o persistencia
    print("\nUso en persistencia/API:")
    import json
    json_str = json.dumps(components_dict, indent=2)
    print(json_str)
    
    print(f"\n✅ Componentes exportados exitosamente")


def main():
    """
    Función principal que ejecuta todos los ejemplos
    """
    print("\n" + "=" * 70)
    print("EJEMPLOS DE USO: MagicNumberGenerator")
    print("=" * 70)
    
    try:
        example_1_basic_generation()
        example_2_sequences()
        example_3_decoding()
        example_4_filtering_positions()
        example_5_performance_analysis()
        example_6_market_vs_limit()
        example_7_error_handling()
        example_8_integration_workflow()
        example_9_components_to_dict()
        
        print("\n\n" + "=" * 70)
        print("✅ TODOS LOS EJEMPLOS COMPLETADOS EXITOSAMENTE")
        print("=" * 70)
        print("\nPróximos pasos:")
        print("  1. Integrar con OrderManager para enviar órdenes")
        print("  2. Usar en PositionManager para filtrar posiciones")
        print("  3. Implementar T18 (Decodificación para auditoría)")
        print("  4. Implementar T19 (Filtrado de posiciones por Magic Number)")
        print()
        
    except Exception as e:
        print(f"\n❌ Error en ejemplos: {e}")
        raise


if __name__ == "__main__":
    main()
