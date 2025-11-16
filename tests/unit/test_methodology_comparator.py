"""
Tests unitarios para MethodologyComparator - T42

Este módulo contiene las pruebas unitarias para el comparador de metodologías,
validando la comparación de desempeño entre bots numéricos, visuales e híbridos.

Autor: Sistema Botrading
Fecha: 2025-11-15
Ticket: T42 - Comparación de desempeño entre metodologías
"""

import pytest
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
import tempfile
import os
from typing import List

# Importaciones del sistema
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analytics.methodology_comparator import (
    MethodologyComparator,
    MethodologyComparison,
    BotMethodology,
    MethodologyComparatorError
)
from src.core.daily_metrics_repository import DailyMetricsRepository, DailyMetrics


# ==================== FIXTURES ====================

@pytest.fixture
def temp_db():
    """Crea una base de datos temporal para pruebas"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def metrics_repo(temp_db):
    """Crea un repositorio de métricas con datos de prueba"""
    repo = DailyMetricsRepository(db_path=Path(temp_db))
    
    # Insertar métricas de prueba para diferentes bots
    today = date.today()
    
    # Bot 1: Numérico - Buen desempeño
    for i in range(5):
        metrics_date = today - timedelta(days=i)
        repo.create_daily_metrics(
            bot_id=1,
            date=metrics_date,
            total_operations=10,
            winning_operations=7,
            losing_operations=3,
            profit_loss_total=1500.0,
            profit_loss_market=800.0,
            profit_loss_limit=700.0,
            total_queries=20,
            total_tokens=5000,
            total_ia_cost=2.5
        )
    
    # Bot 2: Visual - Desempeño moderado
    for i in range(5):
        metrics_date = today - timedelta(days=i)
        repo.create_daily_metrics(
            bot_id=2,
            date=metrics_date,
            total_operations=8,
            winning_operations=5,
            losing_operations=3,
            profit_loss_total=800.0,
            profit_loss_market=400.0,
            profit_loss_limit=400.0,
            total_queries=16,
            total_tokens=8000,
            total_ia_cost=4.0
        )
    
    # Bot 3: Híbrido - Mejor desempeño
    for i in range(5):
        metrics_date = today - timedelta(days=i)
        repo.create_daily_metrics(
            bot_id=3,
            date=metrics_date,
            total_operations=12,
            winning_operations=9,
            losing_operations=3,
            profit_loss_total=2000.0,
            profit_loss_market=1100.0,
            profit_loss_limit=900.0,
            total_queries=24,
            total_tokens=10000,
            total_ia_cost=5.0
        )
    
    return repo


@pytest.fixture
def comparator(metrics_repo):
    """Crea una instancia del comparador con el repositorio de métricas"""
    return MethodologyComparator(metrics_repository=metrics_repo)


# ==================== TESTS DE INICIALIZACIÓN ====================

def test_comparator_initialization(comparator):
    """Verifica que el comparador se inicializa correctamente"""
    assert comparator is not None
    assert comparator.metrics_repository is not None


def test_comparator_requires_repository():
    """Verifica que el comparador requiere un repositorio"""
    with pytest.raises(TypeError):
        MethodologyComparator()


# ==================== TESTS DE COMPARACIÓN POR METODOLOGÍA ====================

def test_compare_methodologies_by_bot_type(comparator):
    """
    Escenario: Comparar desempeño entre metodologías
      Dado que existen métricas para bots numéricos, visuales e híbridos
      Cuando se consulta el comparativo
      Entonces se muestran indicadores clave por bot para decisiones de continuidad
    """
    # Dado
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    # Cuando
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    # Entonces
    assert comparison is not None
    assert len(comparison.methodology_stats) == 3
    
    # Verificar que se incluyen todas las metodologías
    methodologies = [stat.methodology for stat in comparison.methodology_stats]
    assert "numerical" in methodologies
    assert "visual" in methodologies
    assert "hybrid" in methodologies


def test_comparison_includes_key_metrics(comparator):
    """Verifica que la comparación incluye métricas clave"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    for stat in comparison.methodology_stats:
        assert hasattr(stat, 'methodology')
        assert hasattr(stat, 'total_operations')
        assert hasattr(stat, 'avg_winrate')
        assert hasattr(stat, 'avg_profit_factor')
        assert hasattr(stat, 'total_profit_loss')
        assert hasattr(stat, 'total_ia_cost')
        assert hasattr(stat, 'roi')
        assert hasattr(stat, 'cost_per_operation')


def test_comparison_calculates_roi(comparator):
    """Verifica que se calcula el ROI correctamente"""
    bot_methodologies = [
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    hybrid_stat = comparison.methodology_stats[0]
    
    # ROI = (profit_loss - ia_cost) / ia_cost * 100
    expected_roi = ((2000.0 * 5) - (5.0 * 5)) / (5.0 * 5) * 100
    assert abs(hybrid_stat.roi - expected_roi) < 0.01


def test_comparison_identifies_best_methodology(comparator):
    """Verifica que se identifica la mejor metodología"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    assert comparison.best_methodology is not None
    # La mejor metodología debe ser la de mayor ROI
    best_stat = max(comparison.methodology_stats, key=lambda x: x.roi)
    assert comparison.best_methodology == best_stat.methodology


def test_comparison_identifies_worst_methodology(comparator):
    """Verifica que se identifica la peor metodología"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    assert comparison.worst_methodology is not None
    assert comparison.worst_methodology == "visual"


# ==================== TESTS DE COMPARACIÓN POR RANGO DE FECHAS ====================

def test_compare_by_date_range(comparator):
    """Verifica comparación por rango de fechas"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual")
    ]
    
    end_date = date.today()
    start_date = end_date - timedelta(days=3)
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        start_date=start_date,
        end_date=end_date
    )
    
    assert comparison is not None
    assert len(comparison.methodology_stats) == 2


def test_compare_uses_days_parameter(comparator):
    """Verifica que el parámetro days funciona correctamente"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical")
    ]
    
    # Comparar últimos 2 días vs últimos 5 días
    comparison_2_days = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=2
    )
    
    comparison_5_days = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    # El de 5 días debe tener más operaciones
    assert comparison_5_days.methodology_stats[0].total_operations > \
           comparison_2_days.methodology_stats[0].total_operations


# ==================== TESTS DE RANKING ====================

def test_get_methodology_ranking(comparator):
    """Verifica que se puede obtener ranking de metodologías"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    ranking = comparator.get_methodology_ranking(
        bot_methodologies=bot_methodologies,
        days=5,
        sort_by='total_profit_loss'
    )
    
    assert len(ranking) == 3
    # Debe estar ordenado de mayor a menor profit_loss
    assert ranking[0].total_profit_loss >= ranking[1].total_profit_loss
    assert ranking[1].total_profit_loss >= ranking[2].total_profit_loss


def test_ranking_by_different_criteria(comparator):
    """Verifica ranking por diferentes criterios"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    # Ranking por winrate
    ranking_winrate = comparator.get_methodology_ranking(
        bot_methodologies=bot_methodologies,
        days=5,
        sort_by='avg_winrate'
    )
    
    # Ranking por ROI
    ranking_roi = comparator.get_methodology_ranking(
        bot_methodologies=bot_methodologies,
        days=5,
        sort_by='roi'
    )
    
    assert len(ranking_winrate) == 3
    assert len(ranking_roi) == 3
    
    # Verificar orden descendente
    assert ranking_winrate[0].avg_winrate >= ranking_winrate[1].avg_winrate
    assert ranking_roi[0].roi >= ranking_roi[1].roi


# ==================== TESTS DE COMPARACIÓN MARKET VS LIMIT ====================

def test_compare_market_vs_limit_performance(comparator):
    """Verifica comparación de desempeño Market vs Limit por metodología"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    comparison = comparator.compare_market_vs_limit(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    assert comparison is not None
    assert len(comparison) == 2
    
    for method_comparison in comparison:
        assert hasattr(method_comparison, 'methodology')
        assert hasattr(method_comparison, 'market_profit_loss')
        assert hasattr(method_comparison, 'limit_profit_loss')
        assert hasattr(method_comparison, 'market_percentage')
        assert hasattr(method_comparison, 'limit_percentage')


# ==================== TESTS DE ESTADÍSTICAS AGREGADAS ====================

def test_get_aggregate_statistics(comparator):
    """Verifica obtención de estadísticas agregadas"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    stats = comparator.get_aggregate_statistics(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    assert stats is not None
    assert 'total_operations' in stats
    assert 'total_profit_loss' in stats
    assert 'total_ia_cost' in stats
    assert 'overall_winrate' in stats
    assert 'overall_roi' in stats


# ==================== TESTS DE VALIDACIÓN ====================

def test_compare_with_empty_bot_list(comparator):
    """Verifica manejo de lista vacía de bots"""
    with pytest.raises(MethodologyComparatorError, match="Al menos un bot es requerido"):
        comparator.compare_methodologies(
            bot_methodologies=[],
            days=5
        )


def test_compare_with_invalid_days(comparator):
    """Verifica validación de días"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical")
    ]
    
    with pytest.raises(MethodologyComparatorError, match="días debe ser mayor a 0"):
        comparator.compare_methodologies(
            bot_methodologies=bot_methodologies,
            days=0
        )


def test_compare_with_invalid_date_range(comparator):
    """Verifica validación de rango de fechas"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical")
    ]
    
    start_date = date.today()
    end_date = date.today() - timedelta(days=5)
    
    with pytest.raises(MethodologyComparatorError, match="fecha de inicio debe ser anterior"):
        comparator.compare_methodologies(
            bot_methodologies=bot_methodologies,
            start_date=start_date,
            end_date=end_date
        )


def test_compare_with_nonexistent_bot(comparator):
    """Verifica manejo de bot sin métricas"""
    bot_methodologies = [
        BotMethodology(bot_id=999, methodology="numerical")
    ]
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    # Debe retornar comparación con estadísticas en cero
    assert comparison is not None
    assert len(comparison.methodology_stats) == 1
    assert comparison.methodology_stats[0].total_operations == 0


# ==================== TESTS DE SERIALIZACIÓN ====================

def test_comparison_to_dict(comparator):
    """Verifica serialización de comparación a diccionario"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual")
    ]
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    comparison_dict = comparison.to_dict()
    
    assert isinstance(comparison_dict, dict)
    assert 'methodology_stats' in comparison_dict
    assert 'best_methodology' in comparison_dict
    assert 'worst_methodology' in comparison_dict
    assert 'comparison_date' in comparison_dict


def test_comparison_to_json(comparator):
    """Verifica serialización de comparación a JSON"""
    import json
    
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical")
    ]
    
    comparison = comparator.compare_methodologies(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    json_str = comparison.to_json()
    
    assert isinstance(json_str, str)
    # Debe ser JSON válido
    parsed = json.loads(json_str)
    assert 'methodology_stats' in parsed


# ==================== TESTS DE RECOMENDACIONES ====================

def test_get_recommendations(comparator):
    """Verifica generación de recomendaciones basadas en comparación"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ]
    
    recommendations = comparator.get_recommendations(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    assert recommendations is not None
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    
    # Cada recomendación debe tener tipo y mensaje
    for rec in recommendations:
        assert 'type' in rec
        assert 'message' in rec
        assert 'methodology' in rec or 'general' in rec['type']


# ==================== TESTS DE TENDENCIAS ====================

def test_get_methodology_trends(comparator):
    """Verifica análisis de tendencias de metodología"""
    bot_methodologies = [
        BotMethodology(bot_id=1, methodology="numerical")
    ]
    
    trends = comparator.get_methodology_trends(
        bot_methodologies=bot_methodologies,
        days=5
    )
    
    assert trends is not None
    assert len(trends) == 1
    
    trend = trends[0]
    assert hasattr(trend, 'methodology')
    assert hasattr(trend, 'winrate_trend')
    assert hasattr(trend, 'profit_loss_trend')
    assert hasattr(trend, 'trend_direction')  # 'improving', 'declining', 'stable'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
