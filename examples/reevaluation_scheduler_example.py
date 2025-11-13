"""
Ejemplo de uso del ReevaluationScheduler - T26
Demuestra cómo configurar y usar el scheduler de reevaluaciones periódicas

Este ejemplo muestra:
- Configuración del scheduler
- Verificación de reevaluaciones
- Integración con el flujo del bot
- Manejo de múltiples posiciones
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.reevaluation_scheduler import ReevaluationScheduler, ReevaluationConfig


def example_basic_usage():
    """Ejemplo básico de uso del scheduler"""
    print("=" * 60)
    print("EJEMPLO 1: Uso Básico del ReevaluationScheduler")
    print("=" * 60)
    
    # Configurar scheduler
    config = ReevaluationConfig(
        interval_minutes=10,
        enabled=True,
        timezone="America/Lima",
        trading_window_start="06:00",
        trading_window_end="13:00"
    )
    
    scheduler = ReevaluationScheduler(config)
    
    # Simular posiciones
    positions = ["pos_1", "pos_2", "pos_3"]
    
    print("\n📊 Estado Inicial:")
    print(f"Intervalo: {config.interval_minutes} minutos")
    print(f"Ventana de trading: {config.trading_window_start} - {config.trading_window_end}")
    print(f"Posiciones: {len(positions)}")
    
    print("\n🔍 Verificando qué posiciones deben reevaluarse...")
    for pos in positions:
        should = scheduler.should_reevaluate(pos)
        print(f"  {pos}: {'✅ Debe reevaluar' if should else '❌ No debe reevaluar'}")
    
    print("\n✅ Marcando pos_1 como reevaluada...")
    scheduler.mark_reevaluated("pos_1")
    
    print("\n🔍 Verificando nuevamente...")
    for pos in positions:
        should = scheduler.should_reevaluate(pos)
        print(f"  {pos}: {'✅ Debe reevaluar' if should else '❌ No debe reevaluar'}")
    
    print("\n📈 Estadísticas:")
    stats = scheduler.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


def example_trading_window():
    """Ejemplo de verificación de ventana de trading"""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Verificación de Ventana de Trading")
    print("=" * 60)
    
    config = ReevaluationConfig(
        interval_minutes=10,
        trading_window_start="06:00",
        trading_window_end="13:00",
        timezone="America/Lima"
    )
    
    scheduler = ReevaluationScheduler(config)
    
    print(f"\n📅 Hora actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Timezone: {config.timezone}")
    print(f"⏰ Ventana: {config.trading_window_start} - {config.trading_window_end}")
    
    in_window = scheduler.is_within_trading_window()
    print(f"\n{'✅' if in_window else '❌'} Dentro de ventana de trading: {in_window}")
    
    if not in_window:
        print("\n⚠️  Fuera de ventana de trading")
        print("   Las reevaluaciones están deshabilitadas automáticamente")


def example_multiple_positions():
    """Ejemplo con múltiples posiciones"""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Gestión de Múltiples Posiciones")
    print("=" * 60)
    
    config = ReevaluationConfig(interval_minutes=10)
    scheduler = ReevaluationScheduler(config)
    
    # Simular 10 posiciones
    positions = {
        "EURUSD_12345": {"magic": 100101, "profit": 50.5},
        "GBPUSD_12346": {"magic": 100101, "profit": -20.3},
        "USDJPY_12347": {"magic": 100102, "profit": 80.0},
        "AUDUSD_12348": {"magic": 100101, "profit": 30.2},
        "NZDUSD_12349": {"magic": 100102, "profit": -15.8}
    }
    
    print(f"\n📊 {len(positions)} posiciones abiertas:")
    for pos_id, data in positions.items():
        print(f"  {pos_id}: Magic={data['magic']}, P/L=${data['profit']:.2f}")
    
    print("\n🔄 Simulando ciclo de reevaluación...")
    
    reevaluated_count = 0
    for pos_id in positions.keys():
        if scheduler.should_reevaluate(pos_id):
            print(f"  ✅ Reevaluando {pos_id}...")
            # Aquí iría la lógica de reevaluación real
            scheduler.mark_reevaluated(pos_id)
            reevaluated_count += 1
        else:
            elapsed = scheduler.get_time_since_last_reevaluation(pos_id)
            if elapsed:
                print(f"  ⏳ {pos_id}: última reevaluación hace {elapsed.seconds}s")
    
    print(f"\n📈 Resultados: {reevaluated_count}/{len(positions)} posiciones reevaluadas")


async def example_scheduler_loop():
    """Ejemplo de loop asyncrono del scheduler"""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Loop Asíncrono del Scheduler")
    print("=" * 60)
    
    config = ReevaluationConfig(interval_minutes=1)  # 1 min para demo
    scheduler = ReevaluationScheduler(config)
    
    iteration_count = 0
    max_iterations = 3
    
    async def reevaluation_callback():
        """Callback que se ejecuta cada intervalo"""
        nonlocal iteration_count
        iteration_count += 1
        
        print(f"\n🔄 Iteración {iteration_count}/{max_iterations}")
        print(f"   Hora: {datetime.now().strftime('%H:%M:%S')}")
        print(f"   En ventana: {scheduler.is_within_trading_window()}")
        
        # Simular reevaluación de posiciones
        positions = ["pos_1", "pos_2"]
        for pos in positions:
            if scheduler.should_reevaluate(pos):
                print(f"   ✅ Reevaluando {pos}")
                scheduler.mark_reevaluated(pos)
        
        # Detener después de max_iterations
        if iteration_count >= max_iterations:
            scheduler.stop()
    
    print("\n🚀 Iniciando scheduler...")
    print(f"⏰ Intervalo: {config.interval_minutes} minuto(s)")
    print(f"🔢 Iteraciones máximas: {max_iterations}")
    
    try:
        await scheduler.start(reevaluation_callback)
    except asyncio.CancelledError:
        print("\n⛔ Scheduler cancelado")
    
    print(f"\n✅ Completadas {iteration_count} iteraciones")


def example_disabled_scheduler():
    """Ejemplo con scheduler deshabilitado"""
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Scheduler Deshabilitado")
    print("=" * 60)
    
    config = ReevaluationConfig(
        interval_minutes=10,
        enabled=False  # Deshabilitado
    )
    
    scheduler = ReevaluationScheduler(config)
    
    print(f"\n⚙️  Configuración:")
    print(f"   Habilitado: {config.enabled}")
    print(f"   Intervalo: {config.interval_minutes} minutos")
    
    print("\n🔍 Intentando reevaluar posiciones...")
    positions = ["pos_1", "pos_2", "pos_3"]
    
    for pos in positions:
        should = scheduler.should_reevaluate(pos)
        print(f"  {pos}: {should}")
    
    print("\n⚠️  Cuando está deshabilitado, nunca reevalúa (siempre False)")


def example_stats_monitoring():
    """Ejemplo de monitoreo con estadísticas"""
    print("\n" + "=" * 60)
    print("EJEMPLO 6: Monitoreo con Estadísticas")
    print("=" * 60)
    
    config = ReevaluationConfig(interval_minutes=10)
    scheduler = ReevaluationScheduler(config)
    
    # Simular actividad
    print("\n📊 Actividad inicial...")
    stats = scheduler.get_stats()
    print_stats(stats)
    
    print("\n➕ Agregando posiciones...")
    for i in range(5):
        scheduler.mark_reevaluated(f"pos_{i}")
    
    stats = scheduler.get_stats()
    print_stats(stats)
    
    print("\n🧹 Limpiando 2 posiciones...")
    scheduler.reset_position("pos_0")
    scheduler.reset_position("pos_1")
    
    stats = scheduler.get_stats()
    print_stats(stats)
    
    print("\n🗑️  Reset completo...")
    scheduler.reset_all()
    
    stats = scheduler.get_stats()
    print_stats(stats)


def print_stats(stats):
    """Helper para imprimir estadísticas"""
    print("   Estadísticas:")
    for key, value in stats.items():
        print(f"     {key}: {value}")


def main():
    """Ejecuta todos los ejemplos"""
    print("\n" + "=" * 60)
    print("EJEMPLOS DE USO - ReevaluationScheduler (T26)")
    print("=" * 60)
    
    # Ejemplo 1: Básico
    example_basic_usage()
    
    # Ejemplo 2: Ventana de trading
    example_trading_window()
    
    # Ejemplo 3: Múltiples posiciones
    example_multiple_positions()
    
    # Ejemplo 4: Loop asíncrono (comentado por defecto)
    # asyncio.run(example_scheduler_loop())
    
    # Ejemplo 5: Scheduler deshabilitado
    example_disabled_scheduler()
    
    # Ejemplo 6: Monitoreo
    example_stats_monitoring()
    
    print("\n" + "=" * 60)
    print("✅ EJEMPLOS COMPLETADOS")
    print("=" * 60)
    print("\nPara ejecutar el ejemplo async, descomenta la línea:")
    print("  asyncio.run(example_scheduler_loop())")
    print("\n")


if __name__ == "__main__":
    main()
