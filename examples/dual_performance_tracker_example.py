"""
Ejemplo de uso del DualPerformanceTracker - T15

Este ejemplo demuestra cómo usar el DualPerformanceTracker para:
1. Registrar performance de órdenes Market y Limit
2. Comparar performance por operación individual
3. Comparar performance diaria consolidada
4. Obtener métricas agregadas

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T15 - Registro y comparación de desempeño Market vs Limit
"""

from datetime import datetime, date, timedelta
from src.core.dual_performance_tracker import (
    DualPerformanceTracker,
    PerformanceRecord,
    OperationPerformance,
    DailyPerformanceComparison
)


def ejemplo_basico():
    """
    Ejemplo básico: Registrar y comparar un par Market/Limit
    """
    print("=" * 80)
    print("EJEMPLO 1: Registro y comparación básica de un par Market/Limit")
    print("=" * 80)
    
    # Crear tracker (usar BD temporal para el ejemplo)
    tracker = DualPerformanceTracker(db_path="examples/temp_performance.db")
    
    # Simular apertura dual: Market + Limit
    # Ambas se ejecutaron y ganaron
    
    # 1. Registrar orden Market
    market_record = PerformanceRecord(
        symbol="EURUSD",
        bot_id=1,
        order_type="market",
        magic_number=101000,
        open_time=datetime(2025, 11, 13, 10, 0, 0),
        close_time=datetime(2025, 11, 13, 14, 30, 0),
        entry_price=1.1000,
        exit_price=1.1050,
        lot_size=0.1,
        profit_loss=50.0,
        is_winner=True,
        activation_status="activated"
    )
    
    tracker.register_performance(market_record)
    print(f"✓ Orden Market registrada - Magic: {market_record.magic_number}, P/L: ${market_record.profit_loss}")
    
    # 2. Registrar orden Limit
    limit_record = PerformanceRecord(
        symbol="EURUSD",
        bot_id=1,
        order_type="limit",
        magic_number=101001,
        open_time=datetime(2025, 11, 13, 10, 0, 0),
        close_time=datetime(2025, 11, 13, 15, 0, 0),
        entry_price=1.0990,  # Precio límite mejor
        exit_price=1.1040,
        lot_size=0.1,
        profit_loss=50.0,
        is_winner=True,
        activation_status="activated"
    )
    
    tracker.register_performance(limit_record)
    print(f"✓ Orden Limit registrada - Magic: {limit_record.magic_number}, P/L: ${limit_record.profit_loss}")
    
    # 3. Comparar el par
    print("\n--- Comparación de la operación ---")
    comparison = tracker.compare_operation_performance(
        market_magic=101000,
        limit_magic=101001
    )
    
    print(f"Símbolo: {comparison.symbol}")
    print(f"Bot ID: {comparison.bot_id}")
    print(f"Market P/L: ${comparison.market_pl:.2f}")
    print(f"Limit P/L: ${comparison.limit_pl:.2f}")
    print(f"Market activada: {comparison.market_activated}")
    print(f"Limit activada: {comparison.limit_activated}")
    print(f"Diferencia P/L: ${comparison.pl_difference:.2f}")
    print(f"Mejor performer: {comparison.better_performer.upper()}")
    print()


def ejemplo_limit_no_activada():
    """
    Ejemplo: Comparar cuando la orden Limit NO se activó
    """
    print("=" * 80)
    print("EJEMPLO 2: Comparación cuando Limit NO se activó")
    print("=" * 80)
    
    tracker = DualPerformanceTracker(db_path="examples/temp_performance.db")
    
    # Market se activó y ganó
    market_record = PerformanceRecord(
        symbol="GBPUSD",
        bot_id=2,
        order_type="market",
        magic_number=201000,
        open_time=datetime(2025, 11, 13, 11, 0, 0),
        close_time=datetime(2025, 11, 13, 15, 0, 0),
        entry_price=1.2500,
        exit_price=1.2550,
        lot_size=0.1,
        profit_loss=50.0,
        is_winner=True,
        activation_status="activated"
    )
    
    tracker.register_performance(market_record)
    print(f"✓ Market activada - P/L: ${market_record.profit_loss}")
    
    # Limit NO se activó (precio nunca llegó al límite)
    limit_record = PerformanceRecord(
        symbol="GBPUSD",
        bot_id=2,
        order_type="limit",
        magic_number=201001,
        open_time=datetime(2025, 11, 13, 11, 0, 0),
        close_time=None,  # No se cerró porque no se activó
        entry_price=1.2480,  # Precio límite que no se alcanzó
        exit_price=None,
        lot_size=0.1,
        profit_loss=0.0,  # Sin P/L
        is_winner=False,
        activation_status="not_activated"
    )
    
    tracker.register_performance(limit_record)
    print(f"✓ Limit NO activada - P/L: ${limit_record.profit_loss}")
    
    # Comparar
    print("\n--- Comparación ---")
    comparison = tracker.compare_operation_performance(
        market_magic=201000,
        limit_magic=201001
    )
    
    print(f"Market activada: {comparison.market_activated} → P/L: ${comparison.market_pl:.2f}")
    print(f"Limit activada: {comparison.limit_activated} → P/L: ${comparison.limit_pl:.2f}")
    print(f"⚠️ En este caso, Market generó ganancia pero Limit nunca se ejecutó")
    print()


def ejemplo_comparacion_diaria():
    """
    Ejemplo: Comparación de performance diaria con múltiples operaciones
    """
    print("=" * 80)
    print("EJEMPLO 3: Comparación diaria con múltiples operaciones")
    print("=" * 80)
    
    tracker = DualPerformanceTracker(db_path="examples/temp_performance.db")
    
    # Simular 5 pares de órdenes duales del Bot 1
    target_date = date(2025, 11, 13)
    
    print(f"Registrando operaciones del {target_date}...\n")
    
    for i in range(5):
        # Market (siempre se activa)
        market = PerformanceRecord(
            symbol="EURUSD",
            bot_id=1,
            order_type="market",
            magic_number=101000 + i * 10,
            open_time=datetime.combine(target_date, datetime.min.time()) + timedelta(hours=10 + i),
            close_time=datetime.combine(target_date, datetime.min.time()) + timedelta(hours=14 + i),
            entry_price=1.1000,
            exit_price=1.1050 if i % 2 == 0 else 1.0950,  # Alterna ganancia/pérdida
            lot_size=0.1,
            profit_loss=50.0 if i % 2 == 0 else -50.0,
            is_winner=i % 2 == 0,
            activation_status="activated"
        )
        tracker.register_performance(market)
        
        # Limit (algunas se activan, otras no)
        limit_activated = i % 3 != 0  # 2 de cada 3 se activan
        
        limit = PerformanceRecord(
            symbol="EURUSD",
            bot_id=1,
            order_type="limit",
            magic_number=101001 + i * 10,
            open_time=datetime.combine(target_date, datetime.min.time()) + timedelta(hours=10 + i),
            close_time=datetime.combine(target_date, datetime.min.time()) + timedelta(hours=14 + i) if limit_activated else None,
            entry_price=1.0990,
            exit_price=1.1040 if limit_activated else None,
            lot_size=0.1,
            profit_loss=50.0 if limit_activated and i % 2 == 0 else (-50.0 if limit_activated else 0.0),
            is_winner=limit_activated and i % 2 == 0,
            activation_status="activated" if limit_activated else "not_activated"
        )
        tracker.register_performance(limit)
        
        status_market = "✓" if market.is_winner else "✗"
        status_limit = "✓" if limit.activation_status == "activated" else "⏸"
        
        print(f"  Par {i+1}: Market {status_market} ${market.profit_loss:+.0f} | Limit {status_limit} ${limit.profit_loss:+.0f}")
    
    # Comparar performance diaria
    print("\n--- Comparación Diaria ---")
    daily = tracker.compare_daily_performance(bot_id=1, target_date=target_date)
    
    print(f"Bot ID: {daily.bot_id}")
    print(f"Fecha: {daily.target_date}")
    print(f"\nMARKET:")
    print(f"  Total operaciones: {daily.market_count}")
    print(f"  Activadas: {daily.market_activated_count}")
    print(f"  Tasa de activación: {daily.market_activation_rate:.1%}")
    print(f"  P/L total: ${daily.market_total_pl:+.2f}")
    print(f"  P/L promedio: ${daily.market_avg_pl:+.2f}")
    
    print(f"\nLIMIT:")
    print(f"  Total operaciones: {daily.limit_count}")
    print(f"  Activadas: {daily.limit_activated_count}")
    print(f"  Tasa de activación: {daily.limit_activation_rate:.1%}")
    print(f"  P/L total: ${daily.limit_total_pl:+.2f}")
    print(f"  P/L promedio: ${daily.limit_avg_pl:+.2f}")
    
    print(f"\n🏆 Mejor performer del día: {daily.better_daily_performer.upper()}")
    print()


def ejemplo_metricas_agregadas():
    """
    Ejemplo: Obtener métricas agregadas por símbolo
    """
    print("=" * 80)
    print("EJEMPLO 4: Métricas agregadas por símbolo")
    print("=" * 80)
    
    tracker = DualPerformanceTracker(db_path="examples/temp_performance.db")
    
    # Agregar operaciones de diferentes símbolos
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    
    for idx, symbol in enumerate(symbols):
        for i in range(3):
            # Market
            market = PerformanceRecord(
                symbol=symbol,
                bot_id=1,
                order_type="market",
                magic_number=300000 + idx * 100 + i * 10,
                open_time=datetime(2025, 11, 13, 10 + i, 0, 0),
                close_time=datetime(2025, 11, 13, 14 + i, 0, 0),
                entry_price=1.1000,
                exit_price=1.1050,
                lot_size=0.1,
                profit_loss=50.0 + idx * 10,  # Varía por símbolo
                is_winner=True,
                activation_status="activated"
            )
            tracker.register_performance(market)
            
            # Limit
            limit = PerformanceRecord(
                symbol=symbol,
                bot_id=1,
                order_type="limit",
                magic_number=300001 + idx * 100 + i * 10,
                open_time=datetime(2025, 11, 13, 10 + i, 0, 0),
                close_time=datetime(2025, 11, 13, 14 + i, 0, 0) if i % 2 == 0 else None,
                entry_price=1.0990,
                exit_price=1.1040 if i % 2 == 0 else None,
                lot_size=0.1,
                profit_loss=(40.0 + idx * 10) if i % 2 == 0 else 0.0,
                is_winner=i % 2 == 0,
                activation_status="activated" if i % 2 == 0 else "not_activated"
            )
            tracker.register_performance(limit)
    
    # Obtener métricas agregadas
    print("Métricas agregadas por símbolo (2025-11-01 a 2025-11-30):\n")
    
    metrics = tracker.get_aggregated_metrics(
        group_by="symbol",
        start_date=date(2025, 11, 1),
        end_date=date(2025, 11, 30)
    )
    
    for symbol, data in sorted(metrics.items()):
        print(f"{symbol}:")
        print(f"  Total operaciones: {data['count']}")
        print(f"  P/L total: ${data['total_pl']:+.2f}")
        print(f"  P/L promedio: ${data['avg_pl']:+.2f}")
        print(f"  Operaciones ganadoras: {data['winners']}")
        print(f"  Win rate: {data['win_rate']:.1%}")
        print(f"  Activadas: {data['activated']}")
        print(f"  Tasa de activación: {data['activation_rate']:.1%}")
        print()


def ejemplo_integracion_con_dual_order_manager():
    """
    Ejemplo: Integración con DualOrderManager
    
    Este ejemplo muestra cómo usar DualPerformanceTracker
    en conjunto con DualOrderManager para un flujo completo.
    """
    print("=" * 80)
    print("EJEMPLO 5: Integración con DualOrderManager (Flujo completo)")
    print("=" * 80)
    
    tracker = DualPerformanceTracker(db_path="examples/temp_performance.db")
    
    print("FLUJO COMPLETO:")
    print("-" * 80)
    
    # 1. APERTURA DUAL (simulada)
    print("\n1️⃣ Apertura dual de órdenes:")
    market_magic = 101000
    limit_magic = 101001
    print(f"   Market Magic: {market_magic}")
    print(f"   Limit Magic: {limit_magic}")
    print(f"   ✓ Ambas órdenes enviadas a MT5")
    
    # 2. MONITOREO Y CIERRE
    print("\n2️⃣ Monitoreo y cierre:")
    print(f"   • Market se activó inmediatamente")
    print(f"   • Limit se activó después de 30 minutos")
    print(f"   • Ambas se cerraron con ganancia")
    
    # 3. REGISTRO DE PERFORMANCE
    print("\n3️⃣ Registro de performance:")
    
    market_record = PerformanceRecord(
        symbol="EURUSD",
        bot_id=1,
        order_type="market",
        magic_number=market_magic,
        open_time=datetime(2025, 11, 13, 10, 0, 0),
        close_time=datetime(2025, 11, 13, 14, 0, 0),
        entry_price=1.1000,
        exit_price=1.1050,
        lot_size=0.1,
        profit_loss=50.0,
        is_winner=True,
        activation_status="activated"
    )
    
    limit_record = PerformanceRecord(
        symbol="EURUSD",
        bot_id=1,
        order_type="limit",
        magic_number=limit_magic,
        open_time=datetime(2025, 11, 13, 10, 0, 0),
        close_time=datetime(2025, 11, 13, 14, 30, 0),
        entry_price=1.0990,
        exit_price=1.1040,
        lot_size=0.1,
        profit_loss=50.0,
        is_winner=True,
        activation_status="activated"
    )
    
    tracker.register_performance(market_record)
    tracker.register_performance(limit_record)
    print(f"   ✓ Performance de Market registrada")
    print(f"   ✓ Performance de Limit registrada")
    
    # 4. ANÁLISIS
    print("\n4️⃣ Análisis comparativo:")
    comparison = tracker.compare_operation_performance(
        market_magic=market_magic,
        limit_magic=limit_magic
    )
    
    print(f"   Market P/L: ${comparison.market_pl:+.2f}")
    print(f"   Limit P/L: ${comparison.limit_pl:+.2f}")
    print(f"   Resultado: {comparison.better_performer.upper()}")
    
    # 5. CONSOLIDADO DIARIO
    print("\n5️⃣ Consolidado diario:")
    daily = tracker.compare_daily_performance(
        bot_id=1,
        target_date=date(2025, 11, 13)
    )
    
    print(f"   Total operaciones Market: {daily.market_count}")
    print(f"   Total operaciones Limit: {daily.limit_count}")
    print(f"   P/L total Market: ${daily.market_total_pl:+.2f}")
    print(f"   P/L total Limit: ${daily.limit_total_pl:+.2f}")
    print(f"   Tasa activación Limit: {daily.limit_activation_rate:.1%}")
    
    print("\n✅ Flujo completo ejecutado correctamente")
    print()


def main():
    """Ejecutar todos los ejemplos"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "DUAL PERFORMANCE TRACKER - EJEMPLOS" + " " * 28 + "║")
    print("║" + " " * 20 + "Ticket T15 - Sistema Botrading" + " " * 29 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")
    
    # Ejecutar ejemplos
    ejemplo_basico()
    ejemplo_limit_no_activada()
    ejemplo_comparacion_diaria()
    ejemplo_metricas_agregadas()
    ejemplo_integracion_con_dual_order_manager()
    
    print("=" * 80)
    print("✅ Todos los ejemplos ejecutados correctamente")
    print("=" * 80)
    print("\n📊 Para más información, consulta:")
    print("   - Documentación: context/DOCUMENTACION/T15_dual_performance_tracker.md")
    print("   - Tests unitarios: tests/unit/test_dual_performance_tracker.py")
    print("   - Código fuente: src/core/dual_performance_tracker.py")
    print()


if __name__ == "__main__":
    main()
