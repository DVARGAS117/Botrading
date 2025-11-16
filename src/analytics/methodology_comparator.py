"""
MethodologyComparator - Comparación de desempeño entre metodologías - T42

Este módulo implementa la funcionalidad del Ticket T42: Comparación de desempeño
entre metodologías (bots numéricos, visuales e híbridos) para decisiones de continuidad.

Características:
- Comparación de indicadores clave por metodología
- Análisis de ROI y costo-beneficio
- Ranking de metodologías por diferentes criterios
- Comparación Market vs Limit por metodología
- Estadísticas agregadas y tendencias
- Generación de recomendaciones basadas en datos

Autor: Sistema Botrading
Fecha: 2025-11-15
Ticket: T42 - Comparación de desempeño entre metodologías
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from ..core.daily_metrics_repository import DailyMetricsRepository, DailyMetrics


# ==================== CONFIGURACIÓN DE LOGGING ====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== EXCEPCIONES ====================

class MethodologyComparatorError(Exception):
    """Excepción base para errores del comparador de metodologías"""
    pass


# ==================== ENUMS ====================

class TrendDirection(str, Enum):
    """Direcciones de tendencia"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


# ==================== MODELOS ====================

@dataclass
class BotMethodology:
    """
    Representa la asociación entre un bot y su metodología.
    
    Attributes:
        bot_id: ID del bot
        methodology: Tipo de metodología (numerical, visual, hybrid)
    """
    bot_id: int
    methodology: str
    
    def __post_init__(self):
        """Valida la metodología"""
        valid_methodologies = ['numerical', 'visual', 'hybrid']
        if self.methodology not in valid_methodologies:
            raise ValueError(
                f"Metodología '{self.methodology}' inválida. "
                f"Debe ser una de: {valid_methodologies}"
            )


@dataclass
class MethodologyStats:
    """
    Estadísticas agregadas de una metodología.
    
    Incluye todas las métricas necesarias para comparar desempeño
    entre diferentes metodologías de trading.
    """
    methodology: str
    total_operations: int = 0
    winning_operations: int = 0
    losing_operations: int = 0
    avg_winrate: float = 0.0
    avg_profit_factor: float = 0.0
    total_profit_loss: float = 0.0
    market_profit_loss: float = 0.0
    limit_profit_loss: float = 0.0
    total_ia_cost: float = 0.0
    total_tokens: int = 0
    roi: float = 0.0
    cost_per_operation: float = 0.0
    net_profit: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las estadísticas a diccionario"""
        return {
            'methodology': self.methodology,
            'total_operations': self.total_operations,
            'winning_operations': self.winning_operations,
            'losing_operations': self.losing_operations,
            'avg_winrate': round(self.avg_winrate, 2),
            'avg_profit_factor': round(self.avg_profit_factor, 2),
            'total_profit_loss': round(self.total_profit_loss, 2),
            'market_profit_loss': round(self.market_profit_loss, 2),
            'limit_profit_loss': round(self.limit_profit_loss, 2),
            'total_ia_cost': round(self.total_ia_cost, 2),
            'total_tokens': self.total_tokens,
            'roi': round(self.roi, 2),
            'cost_per_operation': round(self.cost_per_operation, 2),
            'net_profit': round(self.net_profit, 2)
        }


@dataclass
class MarketLimitComparison:
    """
    Comparación de desempeño entre órdenes Market y Limit por metodología.
    """
    methodology: str
    market_profit_loss: float = 0.0
    limit_profit_loss: float = 0.0
    market_percentage: float = 0.0
    limit_percentage: float = 0.0
    market_operations: int = 0
    limit_operations: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la comparación a diccionario"""
        return {
            'methodology': self.methodology,
            'market_profit_loss': round(self.market_profit_loss, 2),
            'limit_profit_loss': round(self.limit_profit_loss, 2),
            'market_percentage': round(self.market_percentage, 2),
            'limit_percentage': round(self.limit_percentage, 2),
            'market_operations': self.market_operations,
            'limit_operations': self.limit_operations
        }


@dataclass
class MethodologyTrend:
    """
    Análisis de tendencia de una metodología.
    """
    methodology: str
    winrate_trend: str  # 'improving', 'declining', 'stable'
    profit_loss_trend: str
    trend_direction: TrendDirection
    winrate_change: float = 0.0
    profit_loss_change: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la tendencia a diccionario"""
        return {
            'methodology': self.methodology,
            'winrate_trend': self.winrate_trend,
            'profit_loss_trend': self.profit_loss_trend,
            'trend_direction': self.trend_direction.value,
            'winrate_change': round(self.winrate_change, 2),
            'profit_loss_change': round(self.profit_loss_change, 2)
        }


@dataclass
class MethodologyComparison:
    """
    Resultado completo de la comparación entre metodologías.
    
    Incluye estadísticas por metodología, identificación de mejor/peor,
    y metadatos de la comparación.
    """
    methodology_stats: List[MethodologyStats] = field(default_factory=list)
    best_methodology: Optional[str] = None
    worst_methodology: Optional[str] = None
    comparison_date: datetime = field(default_factory=datetime.now)
    period_days: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la comparación a diccionario"""
        return {
            'methodology_stats': [stat.to_dict() for stat in self.methodology_stats],
            'best_methodology': self.best_methodology,
            'worst_methodology': self.worst_methodology,
            'comparison_date': self.comparison_date.isoformat(),
            'period_days': self.period_days
        }
    
    def to_json(self) -> str:
        """Convierte la comparación a JSON"""
        return json.dumps(self.to_dict(), indent=2)


# ==================== COMPARADOR ====================

class MethodologyComparator:
    """
    Comparador de metodologías para análisis de desempeño.
    
    Permite comparar diferentes metodologías de trading (numérico, visual, híbrido)
    basándose en métricas diarias consolidadas.
    
    Attributes:
        metrics_repository: Repositorio de métricas diarias
    """
    
    def __init__(self, metrics_repository: DailyMetricsRepository):
        """
        Inicializa el comparador de metodologías.
        
        Args:
            metrics_repository: Repositorio de métricas diarias
            
        Raises:
            TypeError: Si no se proporciona un repositorio válido
        """
        if not isinstance(metrics_repository, DailyMetricsRepository):
            raise TypeError("Se requiere una instancia de DailyMetricsRepository")
        
        self.metrics_repository = metrics_repository
        logger.info("MethodologyComparator inicializado correctamente")
    
    def compare_methodologies(
        self,
        bot_methodologies: List[BotMethodology],
        days: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> MethodologyComparison:
        """
        Compara desempeño entre diferentes metodologías.
        
        Args:
            bot_methodologies: Lista de asociaciones bot-metodología
            days: Número de días a analizar (desde hoy hacia atrás)
            start_date: Fecha de inicio del rango (opcional)
            end_date: Fecha de fin del rango (opcional)
            
        Returns:
            MethodologyComparison con estadísticas comparativas
            
        Raises:
            MethodologyComparatorError: Si los parámetros son inválidos
        """
        # Validaciones
        if not bot_methodologies:
            raise MethodologyComparatorError("Al menos un bot es requerido para comparación")
        
        if days is not None and days <= 0:
            raise MethodologyComparatorError("El número de días debe ser mayor a 0")
        
        if start_date and end_date and start_date > end_date:
            raise MethodologyComparatorError(
                "La fecha de inicio debe ser anterior a la fecha de fin"
            )
        
        # Determinar rango de fechas
        if days:
            end_date = date.today()
            start_date = end_date - timedelta(days=days - 1)
            period_days = days
        elif start_date and end_date:
            period_days = (end_date - start_date).days + 1
        else:
            raise MethodologyComparatorError(
                "Debe proporcionar 'days' o 'start_date' y 'end_date'"
            )
        
        logger.info(
            f"Comparando metodologías desde {start_date} hasta {end_date} "
            f"({period_days} días)"
        )
        
        # Agrupar bots por metodología
        methodology_groups = self._group_bots_by_methodology(bot_methodologies)
        
        # Calcular estadísticas por metodología
        methodology_stats = []
        for methodology, bot_ids in methodology_groups.items():
            stats = self._calculate_methodology_stats(
                methodology=methodology,
                bot_ids=bot_ids,
                start_date=start_date,
                end_date=end_date
            )
            methodology_stats.append(stats)
        
        # Identificar mejor y peor metodología
        best_methodology = self._identify_best_methodology(methodology_stats)
        worst_methodology = self._identify_worst_methodology(methodology_stats)
        
        comparison = MethodologyComparison(
            methodology_stats=methodology_stats,
            best_methodology=best_methodology,
            worst_methodology=worst_methodology,
            comparison_date=datetime.now(),
            period_days=period_days
        )
        
        logger.info(
            f"Comparación completada: Mejor={best_methodology}, "
            f"Peor={worst_methodology}"
        )
        
        return comparison
    
    def get_methodology_ranking(
        self,
        bot_methodologies: List[BotMethodology],
        days: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = 'total_profit_loss'
    ) -> List[MethodologyStats]:
        """
        Obtiene ranking de metodologías ordenado por criterio específico.
        
        Args:
            bot_methodologies: Lista de asociaciones bot-metodología
            days: Número de días a analizar
            start_date: Fecha de inicio
            end_date: Fecha de fin
            sort_by: Criterio de ordenamiento
            
        Returns:
            Lista de MethodologyStats ordenada descendentemente
        """
        comparison = self.compare_methodologies(
            bot_methodologies=bot_methodologies,
            days=days,
            start_date=start_date,
            end_date=end_date
        )
        
        # Ordenar por criterio especificado
        valid_criteria = [
            'total_profit_loss', 'avg_winrate', 'avg_profit_factor',
            'roi', 'total_operations', 'net_profit'
        ]
        
        if sort_by not in valid_criteria:
            raise MethodologyComparatorError(
                f"Criterio '{sort_by}' inválido. Debe ser uno de: {valid_criteria}"
            )
        
        ranked = sorted(
            comparison.methodology_stats,
            key=lambda x: getattr(x, sort_by),
            reverse=True
        )
        
        logger.info(f"Ranking generado por criterio '{sort_by}'")
        return ranked
    
    def compare_market_vs_limit(
        self,
        bot_methodologies: List[BotMethodology],
        days: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[MarketLimitComparison]:
        """
        Compara desempeño de órdenes Market vs Limit por metodología.
        
        Args:
            bot_methodologies: Lista de asociaciones bot-metodología
            days: Número de días a analizar
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de comparaciones Market vs Limit por metodología
        """
        comparison = self.compare_methodologies(
            bot_methodologies=bot_methodologies,
            days=days,
            start_date=start_date,
            end_date=end_date
        )
        
        market_limit_comparisons = []
        
        for stat in comparison.methodology_stats:
            total_profit = stat.market_profit_loss + stat.limit_profit_loss
            
            market_pct = 0.0
            limit_pct = 0.0
            if total_profit != 0:
                market_pct = (stat.market_profit_loss / total_profit) * 100
                limit_pct = (stat.limit_profit_loss / total_profit) * 100
            
            comparison_item = MarketLimitComparison(
                methodology=stat.methodology,
                market_profit_loss=stat.market_profit_loss,
                limit_profit_loss=stat.limit_profit_loss,
                market_percentage=market_pct,
                limit_percentage=limit_pct,
                market_operations=0,  # Se calculará con más detalle si es necesario
                limit_operations=0
            )
            market_limit_comparisons.append(comparison_item)
        
        logger.info("Comparación Market vs Limit completada")
        return market_limit_comparisons
    
    def get_aggregate_statistics(
        self,
        bot_methodologies: List[BotMethodology],
        days: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas agregadas de todas las metodologías.
        
        Args:
            bot_methodologies: Lista de asociaciones bot-metodología
            days: Número de días a analizar
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Diccionario con estadísticas agregadas
        """
        comparison = self.compare_methodologies(
            bot_methodologies=bot_methodologies,
            days=days,
            start_date=start_date,
            end_date=end_date
        )
        
        total_operations = sum(s.total_operations for s in comparison.methodology_stats)
        total_winning = sum(s.winning_operations for s in comparison.methodology_stats)
        total_profit_loss = sum(s.total_profit_loss for s in comparison.methodology_stats)
        total_ia_cost = sum(s.total_ia_cost for s in comparison.methodology_stats)
        
        overall_winrate = 0.0
        if total_operations > 0:
            overall_winrate = (total_winning / total_operations) * 100
        
        overall_roi = 0.0
        if total_ia_cost > 0:
            overall_roi = ((total_profit_loss - total_ia_cost) / total_ia_cost) * 100
        
        aggregate = {
            'total_operations': total_operations,
            'total_winning_operations': total_winning,
            'total_profit_loss': round(total_profit_loss, 2),
            'total_ia_cost': round(total_ia_cost, 2),
            'overall_winrate': round(overall_winrate, 2),
            'overall_roi': round(overall_roi, 2),
            'net_profit': round(total_profit_loss - total_ia_cost, 2),
            'methodologies_count': len(comparison.methodology_stats),
            'period_days': comparison.period_days
        }
        
        logger.info("Estadísticas agregadas calculadas")
        return aggregate
    
    def get_recommendations(
        self,
        bot_methodologies: List[BotMethodology],
        days: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones basadas en la comparación de metodologías.
        
        Args:
            bot_methodologies: Lista de asociaciones bot-metodología
            days: Número de días a analizar
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Lista de recomendaciones con tipo, metodología y mensaje
        """
        comparison = self.compare_methodologies(
            bot_methodologies=bot_methodologies,
            days=days,
            start_date=start_date,
            end_date=end_date
        )
        
        recommendations = []
        
        # Recomendación: Mejor metodología
        if comparison.best_methodology:
            best_stat = next(
                s for s in comparison.methodology_stats
                if s.methodology == comparison.best_methodology
            )
            recommendations.append({
                'type': 'best_performer',
                'methodology': comparison.best_methodology,
                'message': (
                    f"La metodología '{comparison.best_methodology}' presenta "
                    f"el mejor desempeño con ROI de {best_stat.roi:.2f}% "
                    f"y winrate de {best_stat.avg_winrate:.2f}%"
                )
            })
        
        # Recomendación: Metodología a mejorar
        if comparison.worst_methodology:
            worst_stat = next(
                s for s in comparison.methodology_stats
                if s.methodology == comparison.worst_methodology
            )
            recommendations.append({
                'type': 'needs_improvement',
                'methodology': comparison.worst_methodology,
                'message': (
                    f"La metodología '{comparison.worst_methodology}' requiere "
                    f"ajustes. Considere revisar prompts o estrategias."
                )
            })
        
        # Recomendación: ROI negativo
        for stat in comparison.methodology_stats:
            if stat.roi < 0:
                recommendations.append({
                    'type': 'negative_roi',
                    'methodology': stat.methodology,
                    'message': (
                        f"La metodología '{stat.methodology}' tiene ROI negativo "
                        f"({stat.roi:.2f}%). Se recomienda pausar o ajustar."
                    )
                })
        
        # Recomendación: Bajo winrate
        for stat in comparison.methodology_stats:
            if stat.avg_winrate < 50.0:
                recommendations.append({
                    'type': 'low_winrate',
                    'methodology': stat.methodology,
                    'message': (
                        f"La metodología '{stat.methodology}' tiene winrate bajo "
                        f"({stat.avg_winrate:.2f}%). Revisar señales de entrada."
                    )
                })
        
        logger.info(f"Generadas {len(recommendations)} recomendaciones")
        return recommendations
    
    def get_methodology_trends(
        self,
        bot_methodologies: List[BotMethodology],
        days: int = 10
    ) -> List[MethodologyTrend]:
        """
        Analiza tendencias de metodologías comparando primera y segunda mitad del período.
        
        Args:
            bot_methodologies: Lista de asociaciones bot-metodología
            days: Número de días totales a analizar
            
        Returns:
            Lista de tendencias por metodología
        """
        if days < 4:
            raise MethodologyComparatorError(
                "Se requieren al menos 4 días para análisis de tendencias"
            )
        
        half_days = days // 2
        
        # Comparar primera mitad vs segunda mitad
        end_date = date.today()
        mid_date = end_date - timedelta(days=half_days)
        start_date = end_date - timedelta(days=days - 1)
        
        # Primera mitad
        first_half = self.compare_methodologies(
            bot_methodologies=bot_methodologies,
            start_date=start_date,
            end_date=mid_date - timedelta(days=1)
        )
        
        # Segunda mitad
        second_half = self.compare_methodologies(
            bot_methodologies=bot_methodologies,
            start_date=mid_date,
            end_date=end_date
        )
        
        trends = []
        
        for methodology in set(bm.methodology for bm in bot_methodologies):
            first_stat = next(
                (s for s in first_half.methodology_stats if s.methodology == methodology),
                None
            )
            second_stat = next(
                (s for s in second_half.methodology_stats if s.methodology == methodology),
                None
            )
            
            if not first_stat or not second_stat:
                continue
            
            # Calcular cambios
            winrate_change = second_stat.avg_winrate - first_stat.avg_winrate
            profit_loss_change = second_stat.total_profit_loss - first_stat.total_profit_loss
            
            # Determinar tendencias
            winrate_trend = self._classify_trend(winrate_change)
            profit_loss_trend = self._classify_trend(profit_loss_change)
            
            # Tendencia general
            if winrate_trend == 'improving' and profit_loss_trend == 'improving':
                trend_direction = TrendDirection.IMPROVING
            elif winrate_trend == 'declining' and profit_loss_trend == 'declining':
                trend_direction = TrendDirection.DECLINING
            else:
                trend_direction = TrendDirection.STABLE
            
            trend = MethodologyTrend(
                methodology=methodology,
                winrate_trend=winrate_trend,
                profit_loss_trend=profit_loss_trend,
                trend_direction=trend_direction,
                winrate_change=winrate_change,
                profit_loss_change=profit_loss_change
            )
            trends.append(trend)
        
        logger.info(f"Análisis de tendencias completado para {len(trends)} metodologías")
        return trends
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    def _group_bots_by_methodology(
        self,
        bot_methodologies: List[BotMethodology]
    ) -> Dict[str, List[int]]:
        """Agrupa bot IDs por metodología"""
        groups = {}
        for bm in bot_methodologies:
            if bm.methodology not in groups:
                groups[bm.methodology] = []
            groups[bm.methodology].append(bm.bot_id)
        return groups
    
    def _calculate_methodology_stats(
        self,
        methodology: str,
        bot_ids: List[int],
        start_date: date,
        end_date: date
    ) -> MethodologyStats:
        """Calcula estadísticas agregadas para una metodología"""
        
        # Recopilar métricas de todos los bots en esta metodología
        all_metrics: List[DailyMetrics] = []
        
        for bot_id in bot_ids:
            bot_metrics = self.metrics_repository.get_metrics_by_date_range(
                bot_id=bot_id,
                start_date=start_date,
                end_date=end_date
            )
            all_metrics.extend(bot_metrics)
        
        # Si no hay métricas, retornar estadísticas vacías
        if not all_metrics:
            logger.warning(f"No se encontraron métricas para metodología '{methodology}'")
            return MethodologyStats(methodology=methodology)
        
        # Agregar estadísticas
        total_operations = sum(m.total_operations for m in all_metrics)
        winning_operations = sum(m.winning_operations for m in all_metrics)
        losing_operations = sum(m.losing_operations for m in all_metrics)
        total_profit_loss = sum(m.profit_loss_total for m in all_metrics)
        market_profit_loss = sum(m.profit_loss_market for m in all_metrics)
        limit_profit_loss = sum(m.profit_loss_limit for m in all_metrics)
        total_ia_cost = sum(m.total_ia_cost for m in all_metrics)
        total_tokens = sum(m.total_tokens for m in all_metrics)
        
        # Calcular promedios
        avg_winrate = 0.0
        avg_profit_factor = 0.0
        
        if all_metrics:
            # Promediar los winrates y profit factors disponibles
            winrates = [m.winrate for m in all_metrics if m.winrate > 0]
            profit_factors = [m.profit_factor for m in all_metrics if m.profit_factor > 0]
            
            if winrates:
                avg_winrate = sum(winrates) / len(winrates)
            
            if profit_factors:
                avg_profit_factor = sum(profit_factors) / len(profit_factors)
        
        # Calcular ROI
        roi = 0.0
        if total_ia_cost > 0:
            roi = ((total_profit_loss - total_ia_cost) / total_ia_cost) * 100
        
        # Calcular costo por operación
        cost_per_operation = 0.0
        if total_operations > 0:
            cost_per_operation = total_ia_cost / total_operations
        
        # Calcular ganancia neta
        net_profit = total_profit_loss - total_ia_cost
        
        stats = MethodologyStats(
            methodology=methodology,
            total_operations=total_operations,
            winning_operations=winning_operations,
            losing_operations=losing_operations,
            avg_winrate=avg_winrate,
            avg_profit_factor=avg_profit_factor,
            total_profit_loss=total_profit_loss,
            market_profit_loss=market_profit_loss,
            limit_profit_loss=limit_profit_loss,
            total_ia_cost=total_ia_cost,
            total_tokens=total_tokens,
            roi=roi,
            cost_per_operation=cost_per_operation,
            net_profit=net_profit
        )
        
        logger.debug(f"Estadísticas calculadas para '{methodology}': {stats.total_operations} ops")
        return stats
    
    def _identify_best_methodology(
        self,
        methodology_stats: List[MethodologyStats]
    ) -> Optional[str]:
        """Identifica la mejor metodología basándose en ROI"""
        if not methodology_stats:
            return None
        
        best = max(methodology_stats, key=lambda x: x.roi)
        return best.methodology
    
    def _identify_worst_methodology(
        self,
        methodology_stats: List[MethodologyStats]
    ) -> Optional[str]:
        """Identifica la peor metodología basándose en ROI"""
        if not methodology_stats:
            return None
        
        worst = min(methodology_stats, key=lambda x: x.roi)
        return worst.methodology
    
    def _classify_trend(self, change: float) -> str:
        """Clasifica tendencia basándose en cambio porcentual"""
        threshold = 5.0  # 5% de cambio para considerar mejora/declive
        
        if change > threshold:
            return 'improving'
        elif change < -threshold:
            return 'declining'
        else:
            return 'stable'


# ==================== FUNCIONES DE UTILIDAD ====================

def create_methodology_comparator(db_path: str) -> MethodologyComparator:
    """
    Factory function para crear un MethodologyComparator.
    
    Args:
        db_path: Ruta a la base de datos SQLite
        
    Returns:
        Instancia configurada de MethodologyComparator
    """
    from pathlib import Path
    metrics_repo = DailyMetricsRepository(db_path=Path(db_path))
    return MethodologyComparator(metrics_repository=metrics_repo)
