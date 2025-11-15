"""
Paquete analytics - Análisis y métricas avanzadas

Este paquete contiene módulos para análisis comparativo y métricas
de desempeño entre diferentes metodologías de trading.

Autor: Sistema Botrading
Fecha: 2025-11-15
"""

from .methodology_comparator import (
    MethodologyComparator,
    MethodologyComparison,
    BotMethodology,
    MethodologyStats,
    MarketLimitComparison,
    MethodologyTrend,
    MethodologyComparatorError
)

__all__ = [
    'MethodologyComparator',
    'MethodologyComparison',
    'BotMethodology',
    'MethodologyStats',
    'MarketLimitComparison',
    'MethodologyTrend',
    'MethodologyComparatorError'
]
