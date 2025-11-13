"""
Módulo para cálculo de métricas diarias por bot.

Este módulo implementa la funcionalidad para calcular métricas diarias
como winrate, profit factor, P/L por tipo de orden y costo total de IA,
cumpliendo con el Ticket T41.
"""
import sqlite3
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from pathlib import Path


class DailyMetricsCalculator:
    """
    Calculadora de métricas diarias por bot.

    Esta clase se encarga de calcular métricas diarias de rendimiento
    para cada bot basado en operaciones cerradas y costos de IA.
    """

    def __init__(self, db_path: str = "data/trading.db"):
        """
        Inicializa la calculadora con la ruta a la base de datos.

        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)

    def calculate_daily_metrics(self, bot_id: int, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calcula métricas diarias para un bot específico.

        Args:
            bot_id: ID del bot
            target_date: Fecha objetivo (por defecto hoy)

        Returns:
            Diccionario con métricas: winrate, profit_factor, pl_by_order_type, total_ia_cost
        """
        if target_date is None:
            target_date = date.today()

        operations = self._get_operations_for_bot(bot_id, target_date)
        ia_queries = self._get_ia_queries_for_bot(bot_id, target_date)

        # Calcular winrate
        if operations:
            winning_trades = sum(1 for op in operations if op['profit'] > 0)
            winrate = winning_trades / len(operations)
        else:
            winrate = 0.0

        # Calcular profit factor
        profits = [op['profit'] for op in operations if op['profit'] > 0]
        losses = [abs(op['profit']) for op in operations if op['profit'] < 0]

        total_profit = sum(profits)
        total_loss = sum(losses)

        if total_loss > 0:
            profit_factor = total_profit / total_loss
        elif total_profit > 0:
            profit_factor = float('inf')
        else:
            profit_factor = 0.0

        # Calcular P/L por tipo de orden
        pl_by_order_type = {}
        for op in operations:
            order_type = op['order_type']
            if order_type not in pl_by_order_type:
                pl_by_order_type[order_type] = 0.0
            pl_by_order_type[order_type] += op['profit']

        # Calcular costo total de IA
        total_ia_cost = sum(query['cost'] for query in ia_queries)

        return {
            "winrate": winrate,
            "profit_factor": profit_factor,
            "pl_by_order_type": pl_by_order_type,
            "total_ia_cost": total_ia_cost
        }

    def _get_operations_for_bot(self, bot_id: int, target_date: date) -> List[Dict[str, Any]]:
        """
        Obtiene operaciones cerradas para un bot en una fecha específica.

        Args:
            bot_id: ID del bot
            target_date: Fecha objetivo

        Returns:
            Lista de operaciones
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT order_type, profit
                    FROM operations
                    WHERE bot_id = ? AND DATE(close_date) = ? AND status = 'closed'
                """, (bot_id, target_date.isoformat()))
                
                operations = []
                for row in cursor.fetchall():
                    operations.append({
                        'order_type': row[0],
                        'profit': row[1]
                    })
                return operations
        except sqlite3.Error as e:
            # Log error and return empty list
            print(f"Error querying operations: {e}")
            return []

    def _get_ia_queries_for_bot(self, bot_id: int, target_date: date) -> List[Dict[str, Any]]:
        """
        Obtiene consultas IA para un bot en una fecha específica.

        Args:
            bot_id: ID del bot
            target_date: Fecha objetivo

        Returns:
            Lista de consultas IA
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cost
                    FROM ia_queries
                    WHERE bot_id = ? AND DATE(query_date) = ?
                """, (bot_id, target_date.isoformat()))
                
                queries = []
                for row in cursor.fetchall():
                    queries.append({
                        'cost': row[0]
                    })
                return queries
        except sqlite3.Error as e:
            # Log error and return empty list
            print(f"Error querying IA queries: {e}")
            return []