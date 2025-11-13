"""
MetricsCalculator - Cálculo de métricas diarias de trading por bot.

Este módulo implementa el cálculo de métricas diarias de rendimiento para
cada bot de trading, incluyendo winrate, profit factor, P/L por tipo de
orden y costo total de IA.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T41 - Disponibilización de métricas diarias por bot
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Optional
import logging


@dataclass
class Operation:
    """
    Representa una operación de trading cerrada.

    Attributes:
        bot_id: ID único del bot que ejecutó la operación
        symbol: Símbolo del instrumento (ej: "EURUSD")
        order_type: Tipo de orden ('MARKET' o 'LIMIT')
        profit: Profit/Loss de la operación
        ia_cost: Costo incurrido por consultas a IA
        close_time: Timestamp de cierre de la operación
        magic_number: Magic Number asociado a la operación
    """
    bot_id: str
    symbol: str
    order_type: str  # 'MARKET' o 'LIMIT'
    profit: float
    ia_cost: float
    close_time: datetime
    magic_number: int


@dataclass
class DailyMetrics:
    """
    Métricas diarias calculadas para un bot específico.

    Attributes:
        bot_id: ID del bot
        date: Fecha para la cual se calculan las métricas
        total_operations: Número total de operaciones
        winning_operations: Número de operaciones ganadoras
        losing_operations: Número de operaciones perdedoras
        winrate: Tasa de victorias (porcentaje)
        total_profit: Suma de profits de operaciones ganadoras
        total_loss: Suma absoluta de losses de operaciones perdedoras
        profit_factor: Relación beneficio/riesgo (total_profit/total_loss)
        market_orders_pl: P/L total de órdenes Market
        limit_orders_pl: P/L total de órdenes Limit
        total_ia_cost: Costo total de consultas IA
    """
    bot_id: str
    date: date
    total_operations: int
    winning_operations: int
    losing_operations: int
    winrate: float
    total_profit: float
    total_loss: float
    profit_factor: float
    market_orders_pl: float
    limit_orders_pl: float
    total_ia_cost: float


class MetricsCalculatorError(Exception):
    """Excepción personalizada para errores de cálculo de métricas."""
    pass


class MetricsCalculator:
    """
    Calculadora de métricas diarias de trading.

    Proporciona métodos para calcular métricas de rendimiento diarias
    por bot, incluyendo winrate, profit factor, P/L desglosado por
    tipo de orden y costos de IA.

    Example:
        >>> calculator = MetricsCalculator()
        >>> metrics = calculator.calculate_daily_metrics(operations, date.today(), "bot_1")
        >>> print(f"Winrate: {metrics.winrate}%")
        >>> print(f"Profit Factor: {metrics.profit_factor}")
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializa el MetricsCalculator.

        Args:
            logger: Logger personalizado (usa el default si no se proporciona)
        """
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

        self.logger.debug("MetricsCalculator inicializado correctamente")

    def calculate_daily_metrics(
        self,
        operations: List[Operation],
        target_date: date,
        bot_id: str
    ) -> DailyMetrics:
        """
        Calcula métricas diarias para un bot específico.

        Args:
            operations: Lista de operaciones cerradas
            target_date: Fecha para la cual calcular métricas
            bot_id: ID del bot

        Returns:
            DailyMetrics: Métricas calculadas

        Raises:
            MetricsCalculatorError: Si hay errores en el cálculo
        """
        try:
            self.logger.info(
                f"Calculando métricas diarias para bot {bot_id} en fecha {target_date}"
            )

            # Validar parámetros
            if not operations:
                self.logger.warning(f"No hay operaciones para calcular métricas")
                return self._create_empty_metrics(bot_id, target_date)

            if not bot_id or not bot_id.strip():
                raise MetricsCalculatorError("bot_id es requerido y no puede estar vacío")

            # Filtrar operaciones del bot y fecha
            bot_operations = [
                op for op in operations
                if op.bot_id == bot_id and op.close_time.date() == target_date
            ]

            if not bot_operations:
                self.logger.info(f"No hay operaciones para bot {bot_id} en fecha {target_date}")
                return self._create_empty_metrics(bot_id, target_date)

            # Calcular métricas básicas
            total_operations = len(bot_operations)
            winning_operations = len([op for op in bot_operations if op.profit > 0])
            losing_operations = total_operations - winning_operations
            winrate = (winning_operations / total_operations) * 100 if total_operations > 0 else 0.0

            # Profit/Loss
            total_profit = sum(op.profit for op in bot_operations if op.profit > 0)
            total_loss = abs(sum(op.profit for op in bot_operations if op.profit < 0))
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf') if total_profit > 0 else 0.0

            # P/L por tipo de orden
            market_operations = [op for op in bot_operations if op.order_type.upper() == 'MARKET']
            limit_operations = [op for op in bot_operations if op.order_type.upper() == 'LIMIT']

            market_orders_pl = sum(op.profit for op in market_operations)
            limit_orders_pl = sum(op.profit for op in limit_operations)

            # Costo IA total
            total_ia_cost = sum(op.ia_cost for op in bot_operations)

            metrics = DailyMetrics(
                bot_id=bot_id,
                date=target_date,
                total_operations=total_operations,
                winning_operations=winning_operations,
                losing_operations=losing_operations,
                winrate=round(winrate, 2),
                total_profit=round(total_profit, 2),
                total_loss=round(total_loss, 2),
                profit_factor=round(profit_factor, 2) if profit_factor != float('inf') else profit_factor,
                market_orders_pl=round(market_orders_pl, 2),
                limit_orders_pl=round(limit_orders_pl, 2),
                total_ia_cost=round(total_ia_cost, 4)
            )

            self.logger.info(
                f"Métricas calculadas para bot {bot_id}: "
                f"{total_operations} operaciones, winrate {metrics.winrate}%"
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculando métricas para bot {bot_id}: {e}")
            raise MetricsCalculatorError(f"Error en cálculo de métricas: {e}") from e

    def _create_empty_metrics(self, bot_id: str, target_date: date) -> DailyMetrics:
        """
        Crea métricas vacías cuando no hay operaciones.

        Args:
            bot_id: ID del bot
            target_date: Fecha objetivo

        Returns:
            DailyMetrics: Métricas con valores cero
        """
        return DailyMetrics(
            bot_id=bot_id,
            date=target_date,
            total_operations=0,
            winning_operations=0,
            losing_operations=0,
            winrate=0.0,
            total_profit=0.0,
            total_loss=0.0,
            profit_factor=0.0,
            market_orders_pl=0.0,
            limit_orders_pl=0.0,
            total_ia_cost=0.0
        )

    def calculate_multiple_bots_metrics(
        self,
        operations: List[Operation],
        target_date: date,
        bot_ids: List[str]
    ) -> List[DailyMetrics]:
        """
        Calcula métricas diarias para múltiples bots.

        Args:
            operations: Lista de todas las operaciones
            target_date: Fecha objetivo
            bot_ids: Lista de IDs de bots

        Returns:
            List[DailyMetrics]: Lista de métricas por bot
        """
        metrics_list = []
        for bot_id in bot_ids:
            try:
                metrics = self.calculate_daily_metrics(operations, target_date, bot_id)
                metrics_list.append(metrics)
            except MetricsCalculatorError as e:
                self.logger.error(f"Error calculando métricas para bot {bot_id}: {e}")
                # Agregar métricas vacías en caso de error
                metrics_list.append(self._create_empty_metrics(bot_id, target_date))

        return metrics_list

    def get_metrics_summary(self, metrics: DailyMetrics) -> dict:
        """
        Genera un resumen legible de las métricas.

        Args:
            metrics: Métricas a resumir

        Returns:
            dict: Resumen con formato legible
        """
        return {
            "bot_id": metrics.bot_id,
            "fecha": metrics.date.isoformat(),
            "operaciones_totales": metrics.total_operations,
            "operaciones_ganadoras": metrics.winning_operations,
            "operaciones_perdedoras": metrics.losing_operations,
            "winrate": f"{metrics.winrate}%",
            "profit_total": f"${metrics.total_profit:.2f}",
            "loss_total": f"${metrics.total_loss:.2f}",
            "profit_factor": f"{metrics.profit_factor:.2f}" if metrics.profit_factor != float('inf') else "∞",
            "pl_market_orders": f"${metrics.market_orders_pl:.2f}",
            "pl_limit_orders": f"${metrics.limit_orders_pl:.2f}",
            "costo_ia_total": f"${metrics.total_ia_cost:.4f}"
        }