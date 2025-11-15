"""
Ejemplo de uso del ReevaluationTracker (T28)

Este ejemplo demuestra cómo usar el sistema de trazabilidad de reevaluaciones
para registrar decisiones de IA, tokens consumidos y costos asociados.

Autor: Sistema Botrading
Fecha: 2025-11-13
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.core.reevaluation_tracker import (
    ReevaluationTracker,
    ReevaluationAction,
    TrackerStatistics
)
from datetime import datetime


def ejemplo_basico():
    """
    Ejemplo básico de registro de reevaluaciones
    """
    print("=" * 70)
    print("EJEMPLO 1: Registro Básico de Reevaluaciones")
    print("=" * 70)
    
    # Inicializar tracker
    tracker = ReevaluationTracker(storage_dir="data/examples/reevaluations")
    
    # Escenario 1: Posición que se mantiene
    print("\n1. Registrando reevaluación con acción MANTENER...")
    tracker.register(
        position_id="pos_001",
        symbol="EURUSD",
        action=ReevaluationAction.MANTENER,
        current_price=1.2500,
        profit_pips=30.0,
        reasoning="Mercado estable, tendencia alcista continua. Mantener posición.",
        conversation_id="conv_abc123",
        reevaluation_mode="persistent",
        tokens_input=450,
        tokens_output=120,
        cost=0.0038,
        reevaluation_count=1,
        time_since_last=600  # 10 minutos
    )
    print("   ✓ Reevaluación registrada exitosamente")
    
    # Escenario 2: Actualizar SL/TP (trailing stop)
    print("\n2. Registrando reevaluación con acción ACTUALIZAR...")
    tracker.register(
        position_id="pos_001",
        symbol="EURUSD",
        action=ReevaluationAction.ACTUALIZAR,
        current_price=1.2580,
        profit_pips=80.0,
        reasoning="Profit alcanzado +80 pips. Mover SL a breakeven +20 pips.",
        new_sl=1.2420,  # Breakeven + 20 pips
        new_tp=1.2650,  # Mantener TP
        conversation_id="conv_abc123",
        reevaluation_mode="persistent",
        tokens_input=500,
        tokens_output=150,
        cost=0.0045,
        reevaluation_count=2,
        time_since_last=600
    )
    print("   ✓ Actualización de SL/TP registrada")
    
    # Escenario 3: Cerrar posición
    print("\n3. Registrando reevaluación con acción CERRAR...")
    tracker.register(
        position_id="pos_002",
        symbol="GBPUSD",
        action=ReevaluationAction.CERRAR,
        current_price=1.3200,
        profit_pips=-25.0,
        reasoning="Señal de reversión detectada. Cerrar antes de alcanzar SL.",
        conversation_id="conv_def456",
        reevaluation_mode="new",
        tokens_input=480,
        tokens_output=130,
        cost=0.0040,
        reevaluation_count=1,
        time_since_last=300
    )
    print("   ✓ Cierre registrado")
    
    print("\n" + "=" * 70)


def ejemplo_consultas():
    """
    Ejemplo de consultas y filtros
    """
    print("=" * 70)
    print("EJEMPLO 2: Consultas y Filtros")
    print("=" * 70)
    
    tracker = ReevaluationTracker(storage_dir="data/examples/reevaluations")
    
    # Consultar todas las reevaluaciones
    print("\n1. Todas las reevaluaciones registradas:")
    all_records = tracker.get_all_records()
    print(f"   Total: {len(all_records)} registros")
    
    for i, record in enumerate(all_records[:3], 1):  # Mostrar primeras 3
        print(f"\n   Registro {i}:")
        print(f"   - Posición: {record.position_id}")
        print(f"   - Símbolo: {record.symbol}")
        print(f"   - Acción: {record.action.value}")
        print(f"   - Precio: {record.current_price}")
        print(f"   - P/L: {record.profit_pips:+.1f} pips")
        print(f"   - Razonamiento: {record.reasoning[:60]}...")
        print(f"   - Tokens: {record.tokens_input}/{record.tokens_output}")
        print(f"   - Costo: ${record.cost:.4f}")
    
    # Consultar por posición específica
    print("\n2. Historial de la posición 'pos_001':")
    history = tracker.get_history_by_position("pos_001")
    print(f"   Total reevaluaciones: {len(history)}")
    
    for i, record in enumerate(history, 1):
        print(f"   Reevaluación {i}: {record.action.value} - "
              f"{record.profit_pips:+.1f} pips - ${record.cost:.4f}")
    
    # Consultar por símbolo
    print("\n3. Reevaluaciones de EURUSD:")
    eurusd_history = tracker.get_history_by_symbol("EURUSD")
    print(f"   Total: {len(eurusd_history)} reevaluaciones")
    
    print("\n" + "=" * 70)


def ejemplo_estadisticas():
    """
    Ejemplo de estadísticas agregadas
    """
    print("=" * 70)
    print("EJEMPLO 3: Estadísticas Agregadas")
    print("=" * 70)
    
    tracker = ReevaluationTracker(storage_dir="data/examples/reevaluations")
    
    # Estadísticas generales
    print("\n1. Estadísticas Generales:")
    stats = tracker.get_statistics()
    
    print(f"   Total reevaluaciones: {stats.total_reevaluations}")
    print(f"   Posiciones únicas: {stats.unique_positions}")
    print(f"   Símbolos únicos: {stats.unique_symbols}")
    print(f"   Tokens totales input: {stats.total_tokens_input:,}")
    print(f"   Tokens totales output: {stats.total_tokens_output:,}")
    print(f"   Costo total: ${stats.total_cost:.4f}")
    print(f"   Costo promedio por reevaluación: ${stats.avg_cost_per_reevaluation:.4f}")
    
    print("\n   Distribución por acción:")
    for action, count in stats.actions_count.items():
        percentage = (count / stats.total_reevaluations * 100) if stats.total_reevaluations > 0 else 0
        print(f"   - {action}: {count} ({percentage:.1f}%)")
    
    # Estadísticas filtradas por acción
    print("\n2. Estadísticas solo de actualizaciones (ACTUALIZAR):")
    stats_actualizar = tracker.get_statistics(action_filter=ReevaluationAction.ACTUALIZAR)
    
    print(f"   Total actualizaciones: {stats_actualizar.total_reevaluations}")
    print(f"   Tokens consumidos: {stats_actualizar.total_tokens_input + stats_actualizar.total_tokens_output:,}")
    print(f"   Costo total: ${stats_actualizar.total_cost:.4f}")
    
    print("\n" + "=" * 70)


def ejemplo_completo_caso_real():
    """
    Ejemplo de caso real: múltiples reevaluaciones de una posición
    """
    print("=" * 70)
    print("EJEMPLO 4: Caso Real - Ciclo de Vida de una Posición")
    print("=" * 70)
    
    tracker = ReevaluationTracker(storage_dir="data/examples/reevaluations_caso_real")
    
    print("\nSimulando ciclo de vida de posición BUY EURUSD...")
    
    # Reevaluación 1: Mantener (después de 10 min)
    print("\n[10 min] Reevaluación #1 - MANTENER")
    tracker.register(
        position_id="pos_real_001",
        symbol="EURUSD",
        action=ReevaluationAction.MANTENER,
        current_price=1.2420,
        profit_pips=20.0,
        reasoning="Movimiento alcista inicial. Mantener y esperar más desarrollo.",
        conversation_id="conv_real_123",
        reevaluation_mode="persistent",
        tokens_input=450,
        tokens_output=120,
        cost=0.0038,
        reevaluation_count=1,
        time_since_last=600
    )
    print("   ✓ Profit: +20 pips - Decisión: MANTENER")
    
    # Reevaluación 2: Mantener (después de 20 min)
    print("\n[20 min] Reevaluación #2 - MANTENER")
    tracker.register(
        position_id="pos_real_001",
        symbol="EURUSD",
        action=ReevaluationAction.MANTENER,
        current_price=1.2450,
        profit_pips=50.0,
        reasoning="Tendencia confirmada. Mantener sin cambios.",
        conversation_id="conv_real_123",
        reevaluation_mode="persistent",
        tokens_input=470,
        tokens_output=125,
        cost=0.0039,
        reevaluation_count=2,
        time_since_last=600
    )
    print("   ✓ Profit: +50 pips - Decisión: MANTENER")
    
    # Reevaluación 3: Actualizar SL (después de 30 min)
    print("\n[30 min] Reevaluación #3 - ACTUALIZAR (Trailing Stop)")
    tracker.register(
        position_id="pos_real_001",
        symbol="EURUSD",
        action=ReevaluationAction.ACTUALIZAR,
        current_price=1.2480,
        profit_pips=80.0,
        reasoning="Profit considerable. Mover SL a breakeven para proteger.",
        new_sl=1.2400,  # Breakeven
        new_tp=1.2600,  # Mantener TP original
        conversation_id="conv_real_123",
        reevaluation_mode="persistent",
        tokens_input=500,
        tokens_output=150,
        cost=0.0045,
        reevaluation_count=3,
        time_since_last=600
    )
    print("   ✓ Profit: +80 pips - Decisión: ACTUALIZAR SL a breakeven")
    
    # Reevaluación 4: Actualizar SL y TP (después de 40 min)
    print("\n[40 min] Reevaluación #4 - ACTUALIZAR (Trailing + Extensión TP)")
    tracker.register(
        position_id="pos_real_001",
        symbol="EURUSD",
        action=ReevaluationAction.ACTUALIZAR,
        current_price=1.2520,
        profit_pips=120.0,
        reasoning="Momentum fuerte. Trailing stop +40 pips y extender TP.",
        new_sl=1.2440,  # Breakeven + 40 pips
        new_tp=1.2650,  # Extender TP
        conversation_id="conv_real_123",
        reevaluation_mode="persistent",
        tokens_input=520,
        tokens_output=160,
        cost=0.0048,
        reevaluation_count=4,
        time_since_last=600
    )
    print("   ✓ Profit: +120 pips - Decisión: ACTUALIZAR SL y TP")
    
    # Reevaluación 5: Cerrar (después de 50 min)
    print("\n[50 min] Reevaluación #5 - CERRAR (TP alcanzado)")
    tracker.register(
        position_id="pos_real_001",
        symbol="EURUSD",
        action=ReevaluationAction.CERRAR,
        current_price=1.2650,
        profit_pips=250.0,
        reasoning="TP alcanzado. Cerrar con profit de +250 pips.",
        conversation_id="conv_real_123",
        reevaluation_mode="persistent",
        tokens_input=490,
        tokens_output=135,
        cost=0.0041,
        reevaluation_count=5,
        time_since_last=600
    )
    print("   ✓ Profit: +250 pips - Decisión: CERRAR (TP alcanzado)")
    
    # Mostrar resumen
    print("\n" + "-" * 70)
    print("RESUMEN DEL CICLO:")
    print("-" * 70)
    
    history = tracker.get_history_by_position("pos_real_001")
    total_tokens = sum(r.tokens_input + r.tokens_output for r in history)
    total_cost = sum(r.cost for r in history)
    
    print(f"\nTotal de reevaluaciones: {len(history)}")
    print(f"Tokens totales consumidos: {total_tokens:,}")
    print(f"Costo total de IA: ${total_cost:.4f}")
    print(f"Resultado final: +250 pips")
    print(f"Ratio Costo/Beneficio: Excelente (${total_cost:.4f} por +250 pips)")
    
    print("\nHistorial de decisiones:")
    for i, record in enumerate(history, 1):
        print(f"{i}. [{record.timestamp.strftime('%H:%M')}] "
              f"{record.action.value:10} - {record.profit_pips:+6.1f} pips - "
              f"${record.cost:.4f} - {record.reasoning[:40]}...")
    
    print("\n" + "=" * 70)


def ejemplo_limpieza():
    """
    Ejemplo de limpieza de historial
    """
    print("=" * 70)
    print("EJEMPLO 5: Limpieza de Historial")
    print("=" * 70)
    
    tracker = ReevaluationTracker(storage_dir="data/examples/reevaluations")
    
    print("\n1. Estado actual:")
    all_records = tracker.get_all_records()
    print(f"   Total registros: {len(all_records)}")
    
    # Limpiar historial de una posición específica
    print("\n2. Limpiando historial de 'pos_001'...")
    deleted = tracker.clear_history_by_position("pos_001")
    print(f"   ✓ {deleted} registros eliminados")
    
    print("\n3. Estado después de limpieza:")
    all_records = tracker.get_all_records()
    print(f"   Total registros: {len(all_records)}")
    
    print("\n" + "=" * 70)


def main():
    """
    Función principal que ejecuta todos los ejemplos
    """
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + " " * 15 + "REEVALUATION TRACKER - EJEMPLOS" + " " * 21 + "*")
    print("*" + " " * 20 + "Ticket T28 - Trazabilidad" + " " * 23 + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    # Ejecutar ejemplos
    ejemplo_basico()
    print("\n")
    
    ejemplo_consultas()
    print("\n")
    
    ejemplo_estadisticas()
    print("\n")
    
    ejemplo_completo_caso_real()
    print("\n")
    
    # ejemplo_limpieza()  # Comentado para no borrar datos de ejemplo
    
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + " " * 21 + "EJEMPLOS COMPLETADOS" + " " * 27 + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")


if __name__ == "__main__":
    main()
