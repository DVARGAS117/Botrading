"""
Ejemplo de uso de MethodologyComparator - T42

Este script demuestra cómo utilizar el comparador de metodologías para
analizar el desempeño de diferentes tipos de bots (numéricos, visuales, híbridos).

Autor: Sistema Botrading
Fecha: 2025-11-15
Ticket: T42 - Comparación de desempeño entre metodologías
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Añadir el directorio raíz al path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from src.analytics.methodology_comparator import (
    MethodologyComparator,
    BotMethodology,
    create_methodology_comparator
)
from src.core.daily_metrics_repository import DailyMetricsRepository


def print_section(title: str):
    """Imprime un título de sección"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def example_1_basic_comparison():
    """Ejemplo 1: Comparación básica entre metodologías"""
    print_section("EJEMPLO 1: Comparación Básica entre Metodologías")
    
    # Crear comparador usando factory function
    db_path = "data/botrading.db"  # Ruta a tu base de datos
    comparator = create_methodology_comparator(db_path)
    
    # Definir bots y sus metodologías
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    # Comparar últimos 7 días
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=7
    )
    
    # Mostrar resultados
    print(f"Período analizado: {comparison.period_days} días")
    print(f"Mejor metodología: {comparison.best_methodology}")
    print(f"Peor metodología: {comparison.worst_methodology}\n")
    
    print("Estadísticas por metodología:")
    print("-" * 70)
    for stat in comparison.methodology_stats:
        print(f"\nMetodología: {stat.methodology.upper()}")
        print(f"  Operaciones totales: {stat.total_operations}")
        print(f"  Winrate promedio: {stat.avg_winrate:.2f}%")
        print(f"  Profit Factor: {stat.avg_profit_factor:.2f}")
        print(f"  P/L Total: ${stat.total_profit_loss:.2f}")
        print(f"  Costo IA: ${stat.total_ia_cost:.2f}")
        print(f"  ROI: {stat.roi:.2f}%")
        print(f"  Ganancia Neta: ${stat.net_profit:.2f}")


def example_2_date_range_comparison():
    """Ejemplo 2: Comparación por rango de fechas específico"""
    print_section("EJEMPLO 2: Comparación por Rango de Fechas")
    
    db_path = "data/botrading.db"
    comparator = create_methodology_comparator(db_path)
    
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual")
    ]
    
    # Definir rango de fechas (última semana completa)
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=6)
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"Período: {start_date} a {end_date}")
    print(f"\nResultados:")
    for stat in comparison.methodology_stats:
        print(f"\n{stat.methodology}: ROI={stat.roi:.2f}%, P/L=${stat.total_profit_loss:.2f}")


def example_3_methodology_ranking():
    """Ejemplo 3: Ranking de metodologías por diferentes criterios"""
    print_section("EJEMPLO 3: Ranking de Metodologías")
    
    db_path = "data/botrading.db"
    comparator = create_methodology_comparator(db_path)
    
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    # Ranking por ROI
    print("Ranking por ROI:")
    ranking_roi = comparator.get_methodology_ranking(
        bot_methodologies=bot_methodologies,
        days=7,
        sort_by='roi'
    )
    for i, stat in enumerate(ranking_roi, 1):
        print(f"  {i}. {stat.methodology}: {stat.roi:.2f}%")
    
    # Ranking por Winrate
    print("\nRanking por Winrate:")
    ranking_winrate = comparator.get_methodology_ranking(
        bot_methodologies=bot_methodologies,
        days=7,
        sort_by='avg_winrate'
    )
    for i, stat in enumerate(ranking_winrate, 1):
        print(f"  {i}. {stat.methodology}: {stat.avg_winrate:.2f}%")
    
    # Ranking por Profit/Loss
    print("\nRanking por Profit/Loss Total:")
    ranking_pl = comparator.get_methodology_ranking(
        bot_methodologies=bot_methodologies,
        days=7,
        sort_by='total_profit_loss'
    )
    for i, stat in enumerate(ranking_pl, 1):
        print(f"  {i}. {stat.methodology}: ${stat.total_profit_loss:.2f}")


def example_4_market_vs_limit():
    """Ejemplo 4: Comparación Market vs Limit por metodología"""
    print_section("EJEMPLO 4: Comparación Market vs Limit")
    
    db_path = "data/botrading.db"
    comparator = create_methodology_comparator(db_path)
    
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    ml_comparison = comparator.compare_market_vs_limit(
        bot_methodologies=bot_methodologies,
        days=7
    )
    
    print("Desempeño Market vs Limit por metodología:\n")
    for comp in ml_comparison:
        print(f"{comp.methodology.upper()}:")
        print(f"  Market P/L: ${comp.market_profit_loss:.2f} ({comp.market_percentage:.1f}%)")
        print(f"  Limit P/L:  ${comp.limit_profit_loss:.2f} ({comp.limit_percentage:.1f}%)")
        
        # Determinar cuál es mejor
        if comp.market_profit_loss > comp.limit_profit_loss:
            print(f"  → Market es mejor por ${comp.market_profit_loss - comp.limit_profit_loss:.2f}")
        else:
            print(f"  → Limit es mejor por ${comp.limit_profit_loss - comp.market_profit_loss:.2f}")
        print()


def example_5_aggregate_statistics():
    """Ejemplo 5: Estadísticas agregadas de todas las metodologías"""
    print_section("EJEMPLO 5: Estadísticas Agregadas")
    
    db_path = "data/botrading.db"
    comparator = create_methodology_comparator(db_path)
    
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    stats = comparator.get_aggregate_statistics(
        bot_methodologies=bot_methodologies,
        days=7
    )
    
    print("Estadísticas Globales (todas las metodologías):\n")
    print(f"  Total de operaciones: {stats['total_operations']}")
    print(f"  Operaciones ganadoras: {stats['total_winning_operations']}")
    print(f"  Winrate general: {stats['overall_winrate']:.2f}%")
    print(f"  Profit/Loss total: ${stats['total_profit_loss']:.2f}")
    print(f"  Costo IA total: ${stats['total_ia_cost']:.2f}")
    print(f"  Ganancia neta: ${stats['net_profit']:.2f}")
    print(f"  ROI general: {stats['overall_roi']:.2f}%")
    print(f"  Metodologías analizadas: {stats['methodologies_count']}")
    print(f"  Período: {stats['period_days']} días")


def example_6_recommendations():
    """Ejemplo 6: Generación de recomendaciones"""
    print_section("EJEMPLO 6: Recomendaciones Basadas en Datos")
    
    db_path = "data/botrading.db"
    comparator = create_methodology_comparator(db_path)
    
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    recommendations = comparator.get_recommendations(
        bot_methodologies=bot_methodologies,
        days=7
    )
    
    print(f"Se generaron {len(recommendations)} recomendaciones:\n")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. [{rec['type'].upper()}]")
        print(f"   Metodología: {rec.get('methodology', 'General')}")
        print(f"   {rec['message']}\n")


def example_7_trends_analysis():
    """Ejemplo 7: Análisis de tendencias"""
    print_section("EJEMPLO 7: Análisis de Tendencias")
    
    db_path = "data/botrading.db"
    comparator = create_methodology_comparator(db_path)
    
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    trends = comparator.get_methodology_trends(
        bot_methodologies=bot_methodologies,
        days=10  # Mínimo 4 días para análisis de tendencias
    )
    
    print("Análisis de tendencias (primera vs segunda mitad del período):\n")
    for trend in trends:
        print(f"{trend.methodology.upper()}:")
        print(f"  Tendencia general: {trend.trend_direction.value.upper()}")
        print(f"  Winrate: {trend.winrate_trend} (cambio: {trend.winrate_change:+.2f}%)")
        print(f"  Profit/Loss: {trend.profit_loss_trend} (cambio: ${trend.profit_loss_change:+.2f})")
        
        # Interpretación
        if trend.trend_direction.value == 'improving':
            print(f"  ✓ La metodología está mejorando")
        elif trend.trend_direction.value == 'declining':
            print(f"  ✗ La metodología está en declive")
        else:
            print(f"  ≈ La metodología se mantiene estable")
        print()


def example_8_json_export():
    """Ejemplo 8: Exportar resultados a JSON"""
    print_section("EJEMPLO 8: Exportar Resultados a JSON")
    
    db_path = "data/botrading.db"
    comparator = create_methodology_comparator(db_path)
    
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=7
    )
    
    # Exportar a JSON
    json_str = comparison.to_json()
    
    print("Resultados en formato JSON:")
    print(json_str[:500])  # Mostrar primeros 500 caracteres
    print("\n... (truncado)")
    
    # También se puede exportar a diccionario
    comparison_dict = comparison.to_dict()
    print(f"\nLlaves del diccionario: {list(comparison_dict.keys())}")


def example_9_practical_use_case():
    """Ejemplo 9: Caso de uso práctico - Decisión de continuidad"""
    print_section("EJEMPLO 9: Caso de Uso Práctico - Decisión de Continuidad")
    
    db_path = "data/botrading.db"
    comparator = create_methodology_comparator(db_path)
    
    # Scenario: PM quiere decidir qué metodologías continuar
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    # Analizar últimos 30 días
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=30
    )
    
    # Obtener recomendaciones
    recommendations = comparator.get_recommendations(
        bot_methodologies=bot_methodologies,
        days=30
    )
    
    print("INFORME PARA DECISIÓN DE CONTINUIDAD\n")
    print(f"Período analizado: {comparison.period_days} días\n")
    
    # Criterios de decisión
    MIN_ROI = 50.0  # 50% ROI mínimo
    MIN_WINRATE = 55.0  # 55% winrate mínimo
    
    print("Evaluación por metodología:\n")
    for stat in comparison.methodology_stats:
        print(f"{stat.methodology.upper()}:")
        print(f"  ROI: {stat.roi:.2f}% {'✓' if stat.roi >= MIN_ROI else '✗'}")
        print(f"  Winrate: {stat.avg_winrate:.2f}% {'✓' if stat.avg_winrate >= MIN_WINRATE else '✗'}")
        print(f"  Ganancia neta: ${stat.net_profit:.2f}")
        
        # Decisión
        if stat.roi >= MIN_ROI and stat.avg_winrate >= MIN_WINRATE:
            print(f"  → DECISIÓN: CONTINUAR ✓")
        elif stat.roi >= MIN_ROI * 0.7:  # 70% del ROI mínimo
            print(f"  → DECISIÓN: AJUSTAR PROMPTS Y MONITOREAR ⚠")
        else:
            print(f"  → DECISIÓN: PAUSAR Y REVISAR ✗")
        print()
    
    print("Recomendaciones automáticas:")
    for rec in recommendations[:3]:  # Top 3 recomendaciones
        print(f"  • {rec['message']}")


def main():
    """Función principal para ejecutar todos los ejemplos"""
    
    print("\n" + "="*70)
    print("  EJEMPLOS DE USO: MethodologyComparator (T42)")
    print("="*70)
    
    # Nota: Para ejecutar estos ejemplos, necesitas una base de datos
    # con métricas diarias. Si no existe, los ejemplos generarán errores.
    
    print("\nNOTA: Estos ejemplos requieren una base de datos con métricas.")
    print("Si la base de datos no existe, los ejemplos fallarán.")
    print("\nEjemplos disponibles:")
    print("  1. Comparación básica entre metodologías")
    print("  2. Comparación por rango de fechas")
    print("  3. Ranking de metodologías")
    print("  4. Comparación Market vs Limit")
    print("  5. Estadísticas agregadas")
    print("  6. Generación de recomendaciones")
    print("  7. Análisis de tendencias")
    print("  8. Exportar a JSON")
    print("  9. Caso de uso práctico")
    
    print("\nPara ejecutar un ejemplo, descomenta la función correspondiente.")
    print("="*70 + "\n")
    
    # Descomentar para ejecutar ejemplos individuales:
    # example_1_basic_comparison()
    # example_2_date_range_comparison()
    # example_3_methodology_ranking()
    # example_4_market_vs_limit()
    # example_5_aggregate_statistics()
    # example_6_recommendations()
    # example_7_trends_analysis()
    # example_8_json_export()
    # example_9_practical_use_case()


if __name__ == "__main__":
    main()
