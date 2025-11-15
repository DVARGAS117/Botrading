"""
Ejemplo de uso del DailyMetricsRepository (T34)

Este ejemplo demuestra cómo usar el repositorio de métricas diarias
para consolidar y consultar estadísticas de trading por bot.

Autor: Botrading Team
Fecha: 2025-11-15
Ticket: T34 - Consolidación de métricas diarias por bot
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from src.core.daily_metrics_repository import DailyMetricsRepository
from src.core.operations_repository import (
    OperationsRepository,
    OrderType,
    Direction,
    OperationStatus
)
from src.core.ia_query_repository import IAQueryRepository, QueryType


def print_separator(title: str = ""):
    """Imprime un separador visual"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def ejemplo_1_creacion_manual():
    """
    Ejemplo 1: Crear métricas diarias manualmente
    """
    print_separator("Ejemplo 1: Crear Métricas Diarias Manualmente")
    
    repo = DailyMetricsRepository(db_path=Path("data/examples/metrics_manual.db"))
    
    today = date.today()
    
    # Crear métrica diaria para Bot 1
    metric = repo.create_daily_metrics(
        bot_id=1,
        date=today,
        total_operations=20,
        winning_operations=14,
        losing_operations=6,
        profit_loss_total=850.50,
        profit_loss_market=500.25,
        profit_loss_limit=350.25,
        total_queries=25,
        total_tokens=7500,
        total_ia_cost=3.75
    )
    
    print(f"✅ Métrica creada para Bot {metric.bot_id} - {metric.date}")
    print(f"   Total operaciones: {metric.total_operations}")
    print(f"   Winrate: {metric.winrate:.2f}%")
    print(f"   Profit Factor: {metric.profit_factor:.2f}")
    print(f"   P/L Total: ${metric.profit_loss_total:.2f}")
    print(f"   Costo IA: ${metric.total_ia_cost:.4f}")
    
    repo.close()


def ejemplo_2_consolidacion_automatica():
    """
    Ejemplo 2: Consolidar métricas automáticamente desde operaciones y consultas IA
    """
    print_separator("Ejemplo 2: Consolidación Automática de Métricas")
    
    # Configurar repositorios
    metrics_repo = DailyMetricsRepository(db_path=Path("data/examples/metrics_auto.db"))
    operations_repo = OperationsRepository(db_path=Path("data/examples/operations_auto.db"))
    ia_repo = IAQueryRepository(db_path=Path("data/examples/ia_queries_auto.db"))
    
    today = date.today()
    bot_id = 1
    
    print("📊 Creando operaciones de prueba...")
    
    # Crear 5 operaciones ganadoras
    for i in range(5):
        op = operations_repo.create_operation(
            magic_number=1000 + i,
            bot_id=bot_id,
            ia_id=1,
            order_type=OrderType.MARKET if i % 2 == 0 else OrderType.LIMIT,
            symbol="EURUSD",
            direction=Direction.BUY,
            suggested_price=1.0850,
            actual_entry_price=1.0851,
            stop_loss=1.0800,
            take_profit=1.0950,
            lot_size=0.10,
            risk_percentage=1.0,
            status=OperationStatus.OPEN
        )
        if op.id is not None:
            operations_repo.close_operation(op.id, profit_loss=100.0 + (i * 10))
    
    # Crear 3 operaciones perdedoras
    for i in range(3):
        op = operations_repo.create_operation(
            magic_number=2000 + i,
            bot_id=bot_id,
            ia_id=1,
            order_type=OrderType.MARKET,
            symbol="GBPUSD",
            direction=Direction.SELL,
            suggested_price=1.2500,
            actual_entry_price=1.2501,
            stop_loss=1.2550,
            take_profit=1.2400,
            lot_size=0.10,
            risk_percentage=1.0,
            status=OperationStatus.OPEN
        )
        if op.id is not None:
            operations_repo.close_operation(op.id, profit_loss=-50.0 - (i * 5))
    
    # Crear consultas IA
    print("🤖 Creando consultas IA de prueba...")
    for i in range(10):
        ia_repo.create_query(
            bot_id=bot_id,
            ia_id=1,
            symbol="EURUSD" if i % 2 == 0 else "GBPUSD",
            query_type=QueryType.EVALUATION if i < 8 else QueryType.REEVALUATION,
            prompt=f"Analizar mercado - Prueba {i}",
            response='{"decision": "OPERAR", "direction": "BUY"}',
            tokens_input=100 + (i * 10),
            tokens_output=50 + (i * 5),
            cost_usd=0.50 + (i * 0.05),
            action_decided="OPERAR" if i < 8 else "MANTENER"
        )
    
    # Consolidar métricas
    print("\n🔄 Consolidando métricas del día...")
    metric = metrics_repo.consolidate_metrics_for_date(
        bot_id=bot_id,
        target_date=today,
        operations_repo=operations_repo,
        ia_repo=ia_repo
    )
    
    print(f"\n✅ Métricas consolidadas para Bot {metric.bot_id} - {metric.date}")
    print(f"\n📈 OPERACIONES:")
    print(f"   Total: {metric.total_operations}")
    print(f"   Ganadoras: {metric.winning_operations}")
    print(f"   Perdedoras: {metric.losing_operations}")
    print(f"   Winrate: {metric.winrate:.2f}%")
    
    print(f"\n💰 RESULTADOS:")
    print(f"   P/L Total: ${metric.profit_loss_total:.2f}")
    print(f"   P/L Market: ${metric.profit_loss_market:.2f}")
    print(f"   P/L Limit: ${metric.profit_loss_limit:.2f}")
    print(f"   Profit Factor: {metric.profit_factor:.2f}")
    
    print(f"\n🤖 IA:")
    print(f"   Consultas: {metric.total_queries}")
    print(f"   Tokens: {metric.total_tokens:,}")
    print(f"   Costo: ${metric.total_ia_cost:.4f}")
    
    metrics_repo.close()
    operations_repo.close()
    ia_repo.close()


def ejemplo_3_consultas_metricas():
    """
    Ejemplo 3: Consultar métricas almacenadas
    """
    print_separator("Ejemplo 3: Consultar Métricas Almacenadas")
    
    repo = DailyMetricsRepository(db_path=Path("data/examples/metrics_queries.db"))
    
    # Crear métricas de varios días
    today = date.today()
    print("📊 Creando métricas de los últimos 7 días...")
    
    for i in range(7):
        target_date = today - timedelta(days=i)
        winning = 12 - i
        losing = 5 + i
        
        repo.create_daily_metrics(
            bot_id=1,
            date=target_date,
            total_operations=winning + losing,
            winning_operations=winning,
            losing_operations=losing,
            profit_loss_total=500.0 - (i * 50),
            profit_loss_market=300.0 - (i * 30),
            profit_loss_limit=200.0 - (i * 20),
            total_queries=20 - i,
            total_tokens=6000 - (i * 500),
            total_ia_cost=3.0 - (i * 0.25)
        )
    
    # Consulta 1: Métricas de hoy
    print(f"\n🔍 Métricas de hoy ({today}):")
    today_metric = repo.get_metrics_by_bot_and_date(bot_id=1, date=today)
    if today_metric:
        print(f"   Operaciones: {today_metric.total_operations}")
        print(f"   Winrate: {today_metric.winrate:.2f}%")
        print(f"   P/L: ${today_metric.profit_loss_total:.2f}")
    
    # Consulta 2: Todas las métricas del bot
    print(f"\n🔍 Todas las métricas del Bot 1:")
    all_metrics = repo.get_metrics_by_bot(bot_id=1)
    for m in all_metrics[:3]:  # Mostrar solo las 3 más recientes
        print(f"   {m.date}: {m.total_operations} ops, WR={m.winrate:.1f}%, P/L=${m.profit_loss_total:.2f}")
    print(f"   ... ({len(all_metrics)} días en total)")
    
    # Consulta 3: Rango de fechas
    print(f"\n🔍 Métricas de los últimos 3 días:")
    three_days_ago = today - timedelta(days=2)
    range_metrics = repo.get_metrics_by_date_range(
        bot_id=1,
        start_date=three_days_ago,
        end_date=today
    )
    for m in range_metrics:
        print(f"   {m.date}: {m.winning_operations}W/{m.losing_operations}L = {m.winrate:.1f}%")
    
    repo.close()


def ejemplo_4_estadisticas_agregadas():
    """
    Ejemplo 4: Estadísticas agregadas de un bot
    """
    print_separator("Ejemplo 4: Estadísticas Agregadas")
    
    repo = DailyMetricsRepository(db_path=Path("data/examples/metrics_stats.db"))
    
    # Crear métricas de 30 días
    today = date.today()
    print("📊 Creando métricas de los últimos 30 días...")
    
    for i in range(30):
        target_date = today - timedelta(days=i)
        
        # Variar los resultados
        winning = 10 + (i % 5)
        losing = 5 + (i % 3)
        pl = 400.0 + (i * 10) - (i * i * 0.5)
        
        repo.create_daily_metrics(
            bot_id=1,
            date=target_date,
            total_operations=winning + losing,
            winning_operations=winning,
            losing_operations=losing,
            profit_loss_total=pl,
            profit_loss_market=pl * 0.6,
            profit_loss_limit=pl * 0.4,
            total_queries=15 + (i % 3),
            total_tokens=5000 + (i * 100),
            total_ia_cost=2.5 + (i * 0.05)
        )
    
    # Obtener estadísticas agregadas
    print("\n📈 ESTADÍSTICAS AGREGADAS - BOT 1 (30 días)")
    stats = repo.get_statistics_by_bot(bot_id=1)
    
    print(f"\n⏱️  TIEMPO:")
    print(f"   Días operados: {stats['total_days']}")
    
    print(f"\n📊 OPERACIONES:")
    print(f"   Total: {stats['total_operations']}")
    print(f"   Ganadoras: {stats['total_winning']}")
    print(f"   Perdedoras: {stats['total_losing']}")
    print(f"   Winrate promedio: {stats['average_winrate']:.2f}%")
    
    print(f"\n💰 RESULTADOS:")
    print(f"   P/L Total: ${stats['total_profit_loss']:.2f}")
    print(f"   Profit Factor promedio: {stats['average_profit_factor']:.2f}")
    
    print(f"\n🤖 COSTOS IA:")
    print(f"   Costo Total: ${stats['total_ia_cost']:.4f}")
    print(f"   Promedio diario: ${stats['total_ia_cost'] / stats['total_days']:.4f}")
    
    # Calcular ROI
    if stats['total_ia_cost'] > 0:
        roi = (stats['total_profit_loss'] / stats['total_ia_cost']) * 100
        print(f"\n📈 ROI IA: {roi:.2f}%")
        print(f"   Por cada $1 en IA, se generaron ${stats['total_profit_loss'] / stats['total_ia_cost']:.2f}")
    
    repo.close()


def ejemplo_5_comparacion_bots():
    """
    Ejemplo 5: Comparar desempeño entre múltiples bots
    """
    print_separator("Ejemplo 5: Comparación Entre Bots")
    
    repo = DailyMetricsRepository(db_path=Path("data/examples/metrics_comparison.db"))
    
    today = date.today()
    
    # Crear métricas para 3 bots diferentes
    print("📊 Creando métricas para 3 bots...")
    
    bots_data = [
        {"bot_id": 1, "name": "Aggressive", "win": 15, "lose": 10, "pl": 800.0},
        {"bot_id": 2, "name": "Conservative", "win": 20, "lose": 5, "pl": 650.0},
        {"bot_id": 3, "name": "Balanced", "win": 18, "lose": 7, "pl": 720.0},
    ]
    
    for bot in bots_data:
        repo.create_daily_metrics(
            bot_id=bot["bot_id"],
            date=today,
            total_operations=bot["win"] + bot["lose"],
            winning_operations=bot["win"],
            losing_operations=bot["lose"],
            profit_loss_total=bot["pl"],
            total_queries=bot["win"] + bot["lose"] + 5,
            total_tokens=5000,
            total_ia_cost=2.5
        )
    
    # Comparar resultados
    print(f"\n📊 COMPARACIÓN DE BOTS - {today}")
    print("-" * 80)
    print(f"{'Bot':<15} {'Ops':<6} {'W/L':<10} {'WR%':<8} {'P/L':<12} {'$/Op':<10}")
    print("-" * 80)
    
    for bot in bots_data:
        metric = repo.get_metrics_by_bot_and_date(bot_id=bot["bot_id"], date=today)
        if metric:
            pl_per_op = metric.profit_loss_total / metric.total_operations
            print(f"{bot['name']:<15} "
                  f"{metric.total_operations:<6} "
                  f"{metric.winning_operations}/{metric.losing_operations:<8} "
                  f"{metric.winrate:<8.1f} "
                  f"${metric.profit_loss_total:<11.2f} "
                  f"${pl_per_op:<10.2f}")
    
    print("-" * 80)
    
    # Estadísticas totales del sistema
    print("\n🌐 ESTADÍSTICAS TOTALES DEL SISTEMA:")
    total_stats = repo.get_total_statistics()
    print(f"   Bots activos: {total_stats['total_bots']}")
    print(f"   Total operaciones: {total_stats['total_operations']}")
    print(f"   Winrate promedio: {total_stats['average_winrate']:.2f}%")
    print(f"   P/L Total: ${total_stats['total_profit_loss']:.2f}")
    
    repo.close()


def ejemplo_6_flujo_completo():
    """
    Ejemplo 6: Flujo completo de consolidación diaria
    """
    print_separator("Ejemplo 6: Flujo Completo de Consolidación Diaria")
    
    # Simular el proceso completo de un día de trading
    metrics_repo = DailyMetricsRepository(db_path=Path("data/examples/metrics_complete.db"))
    operations_repo = OperationsRepository(db_path=Path("data/examples/operations_complete.db"))
    ia_repo = IAQueryRepository(db_path=Path("data/examples/ia_queries_complete.db"))
    
    today = date.today()
    bot_id = 1
    
    print("🚀 Simulando día completo de trading para Bot 1...")
    print("\n⏰ 06:00 - Inicio de operaciones")
    
    # Simular operaciones durante el día
    symbols = ["EURUSD", "GBPUSD", "XAUUSD"]
    operations_created = 0
    
    for symbol in symbols:
        print(f"\n📊 Analizando {symbol}...")
        
        # Consulta IA
        query = ia_repo.create_query(
            bot_id=bot_id,
            ia_id=1,
            symbol=symbol,
            query_type=QueryType.EVALUATION,
            prompt=f"Analizar {symbol} con indicadores técnicos",
            response='{"decision": "OPERAR", "direction": "BUY", "confidence": 0.85}',
            tokens_input=120,
            tokens_output=60,
            cost_usd=0.54,
            action_decided="OPERAR"
        )
        
        # Crear operación
        op = operations_repo.create_operation(
            magic_number=3000 + operations_created,
            bot_id=bot_id,
            ia_id=1,
            order_type=OrderType.MARKET if operations_created % 2 == 0 else OrderType.LIMIT,
            symbol=symbol,
            direction=Direction.BUY,
            suggested_price=1.0850 if symbol == "EURUSD" else (1.2500 if symbol == "GBPUSD" else 2080.00),
            actual_entry_price=1.0851 if symbol == "EURUSD" else (1.2501 if symbol == "GBPUSD" else 2080.50),
            stop_loss=1.0800 if symbol == "EURUSD" else (1.2450 if symbol == "GBPUSD" else 2070.00),
            take_profit=1.0950 if symbol == "EURUSD" else (1.2600 if symbol == "GBPUSD" else 2100.00),
            lot_size=0.10,
            risk_percentage=1.0,
            status=OperationStatus.OPEN,
            conversation_id=str(query.id)
        )
        
        # Vincular consulta a operación
        if op.id is not None and query.id is not None:
            ia_repo.update_operation_id(query.id, op.id)
            operations_created += 1
            print(f"   ✅ Operación abierta: {symbol} (ID: {op.id})")
        
        # Simular reevaluaciones
        for i in range(2):
            ia_repo.create_query(
                bot_id=bot_id,
                ia_id=1,
                symbol=symbol,
                query_type=QueryType.REEVALUATION,
                prompt=f"Reevaluar {symbol} - Iteración {i+1}",
                response='{"decision": "MANTENER"}',
                tokens_input=80,
                tokens_output=40,
                cost_usd=0.36,
                action_decided="MANTENER",
                operation_id=op.id
            )
    
    # Cerrar operaciones con resultados variados
    print(f"\n⏰ 13:00 - Cierre de operaciones")
    results = [150.0, -50.0, 200.0]  # 2 ganadoras, 1 perdedora
    
    all_ops = operations_repo.list_operations(status=OperationStatus.OPEN, bot_id=bot_id)
    for i, op in enumerate(all_ops):
        if op.id is not None:
            operations_repo.close_operation(op.id, profit_loss=results[i])
            status = "ganadora" if results[i] > 0 else "perdedora"
            print(f"   {'✅' if results[i] > 0 else '❌'} {op.symbol}: ${results[i]:.2f} ({status})")
    
    # Consolidar métricas del día
    print(f"\n⏰ 14:00 - Consolidación de métricas")
    metric = metrics_repo.consolidate_metrics_for_date(
        bot_id=bot_id,
        target_date=today,
        operations_repo=operations_repo,
        ia_repo=ia_repo
    )
    
    print(f"\n📊 RESUMEN DEL DÍA - Bot {bot_id} ({today})")
    print("=" * 80)
    print(f"\n📈 OPERACIONES:")
    print(f"   Total ejecutadas: {metric.total_operations}")
    print(f"   Ganadoras: {metric.winning_operations} ({'✅' * metric.winning_operations})")
    print(f"   Perdedoras: {metric.losing_operations} ({'❌' * metric.losing_operations})")
    print(f"   Winrate: {metric.winrate:.2f}%")
    
    print(f"\n💰 RESULTADOS:")
    print(f"   P/L Total: ${metric.profit_loss_total:.2f}")
    print(f"   P/L Market: ${metric.profit_loss_market:.2f}")
    print(f"   P/L Limit: ${metric.profit_loss_limit:.2f}")
    print(f"   Profit Factor: {metric.profit_factor:.2f}")
    print(f"   Promedio por operación: ${metric.profit_loss_total / metric.total_operations:.2f}")
    
    print(f"\n🤖 CONSULTAS IA:")
    print(f"   Evaluaciones: {metric.total_queries - (metric.total_operations * 2)}")
    print(f"   Reevaluaciones: {metric.total_operations * 2}")
    print(f"   Total consultas: {metric.total_queries}")
    print(f"   Tokens consumidos: {metric.total_tokens:,}")
    print(f"   Costo total IA: ${metric.total_ia_cost:.4f}")
    
    # Calcular eficiencia
    if metric.total_ia_cost > 0:
        efficiency = metric.profit_loss_total / metric.total_ia_cost
        print(f"\n🎯 EFICIENCIA:")
        print(f"   ROI IA: {(efficiency - 1) * 100:.2f}%")
        print(f"   Por cada $1 en IA: ${efficiency:.2f} de ganancia")
    
    print("\n✅ Consolidación completada exitosamente")
    
    metrics_repo.close()
    operations_repo.close()
    ia_repo.close()


def main():
    """Ejecutar todos los ejemplos"""
    print("\n" + "🎯" * 40)
    print("  EJEMPLOS DE USO - DailyMetricsRepository (T34)")
    print("  Consolidación de Métricas Diarias por Bot")
    print("🎯" * 40 + "\n")
    
    # Crear directorio de datos
    Path("data/examples").mkdir(parents=True, exist_ok=True)
    
    # Ejecutar ejemplos
    ejemplo_1_creacion_manual()
    ejemplo_2_consolidacion_automatica()
    ejemplo_3_consultas_metricas()
    ejemplo_4_estadisticas_agregadas()
    ejemplo_5_comparacion_bots()
    ejemplo_6_flujo_completo()
    
    print_separator("✅ Todos los ejemplos ejecutados exitosamente")
    print("\n💡 Próximos pasos:")
    print("   1. Integrar con el ciclo de ejecución diaria del bot")
    print("   2. Crear dashboard para visualización de métricas")
    print("   3. Implementar alertas basadas en umbrales de desempeño")
    print("   4. Exportar métricas a formatos de análisis (CSV, Excel)")
    print()


if __name__ == "__main__":
    main()
