"""
DailyMetricsRepository - Consolidación de métricas diarias por bot - T34

Este módulo implementa la funcionalidad del Ticket T34: Consolidación de métricas
diarias por bot incluyendo winrate, profit factor, costos IA y estadísticas agregadas.

Características:
- Consolidación automática de métricas desde operaciones y consultas IA
- Cálculo de winrate, profit factor, P/L por tipo de orden
- Registro de costos y tokens de IA
- Consultas por bot, fecha y rangos
- Estadísticas agregadas para análisis

Autor: Sistema Botrading
Fecha: 2025-11-15
Ticket: T34 - Consolidación de métricas diarias por bot
"""

import sqlite3
from dataclasses import dataclass
from datetime import date as date_type, datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging


# ==================== CONFIGURACIÓN DE LOGGING ====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== EXCEPCIONES ====================

class DailyMetricsRepositoryError(Exception):
    """Excepción base para errores del repositorio de métricas"""
    pass


# ==================== MODELOS ====================

@dataclass
class DailyMetrics:
    """
    Modelo de datos para métricas diarias consolidadas.
    
    Representa las métricas agregadas de un bot en un día específico,
    incluyendo operaciones, resultados y costos de IA.
    """
    # Identificación
    id: Optional[int] = None
    bot_id: int = 0
    date: Optional[date_type] = None
    
    # Operaciones
    total_operations: int = 0
    winning_operations: int = 0
    losing_operations: int = 0
    
    # Resultados financieros
    profit_loss_total: float = 0.0
    profit_loss_market: float = 0.0
    profit_loss_limit: float = 0.0
    
    # Costos IA
    total_queries: int = 0
    total_tokens: int = 0
    total_ia_cost: float = 0.0
    
    # Ratios calculados
    winrate: float = 0.0
    profit_factor: float = 0.0
    
    # Timestamp
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las métricas a diccionario"""
        return {
            'id': self.id,
            'bot_id': self.bot_id,
            'date': self.date.isoformat() if self.date else None,
            'total_operations': self.total_operations,
            'winning_operations': self.winning_operations,
            'losing_operations': self.losing_operations,
            'profit_loss_total': self.profit_loss_total,
            'profit_loss_market': self.profit_loss_market,
            'profit_loss_limit': self.profit_loss_limit,
            'total_queries': self.total_queries,
            'total_tokens': self.total_tokens,
            'total_ia_cost': self.total_ia_cost,
            'winrate': self.winrate,
            'profit_factor': self.profit_factor,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ==================== REPOSITORIO ====================

class DailyMetricsRepository:
    """
    Repositorio para consolidación y persistencia de métricas diarias.
    
    Gestiona la consolidación de métricas diarias por bot:
    - Consolidación automática desde operaciones y consultas IA
    - Cálculo de winrate y profit factor
    - Consultas por bot, fecha y rangos
    - Estadísticas agregadas
    
    Ejemplo:
        >>> from pathlib import Path
        >>> from datetime import date
        >>> 
        >>> repo = DailyMetricsRepository(db_path=Path("data/metrics.db"))
        >>> 
        >>> # Consolidar métricas del día
        >>> metric = repo.consolidate_metrics_for_date(
        ...     bot_id=1,
        ...     target_date=date.today(),
        ...     operations_repo=operations_repo,
        ...     ia_repo=ia_repo
        ... )
        >>> 
        >>> # Consultar métricas
        >>> today_metrics = repo.get_metrics_by_bot_and_date(1, date.today())
        >>> print(f"Winrate: {today_metrics.winrate}%")
        >>> print(f"P/L: ${today_metrics.profit_loss_total}")
    """
    
    def __init__(self, db_path: Path):
        """
        Inicializa el repositorio y crea la estructura de BD.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info(f"DailyMetricsRepository initialized at {self.db_path}")
    
    def _init_database(self):
        """Crea la tabla y los índices si no existen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Crear tabla metricas_diarias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metricas_diarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                fecha DATE NOT NULL,
                
                -- Operaciones
                total_operaciones INTEGER DEFAULT 0,
                operaciones_ganadoras INTEGER DEFAULT 0,
                operaciones_perdedoras INTEGER DEFAULT 0,
                
                -- Resultados
                profit_loss_total REAL DEFAULT 0,
                profit_loss_market REAL DEFAULT 0,
                profit_loss_limit REAL DEFAULT 0,
                
                -- Costos IA
                total_consultas INTEGER DEFAULT 0,
                tokens_totales INTEGER DEFAULT 0,
                costo_ia_total REAL DEFAULT 0,
                
                -- Ratios
                winrate REAL,
                profit_factor REAL,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(bot_id, fecha)
            )
        """)
        
        # Crear índices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bot_fecha 
            ON metricas_diarias(bot_id, fecha)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fecha 
            ON metricas_diarias(fecha)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Database schema created successfully")
    
    def create_daily_metrics(
        self,
        bot_id: int,
        date: date_type,
        total_operations: int = 0,
        winning_operations: int = 0,
        losing_operations: int = 0,
        profit_loss_total: float = 0.0,
        profit_loss_market: float = 0.0,
        profit_loss_limit: float = 0.0,
        total_queries: int = 0,
        total_tokens: int = 0,
        total_ia_cost: float = 0.0
    ) -> DailyMetrics:
        """
        Crea un nuevo registro de métricas diarias.
        
        Args:
            bot_id: ID del bot
            date: Fecha de las métricas
            total_operations: Total de operaciones
            winning_operations: Operaciones ganadoras
            losing_operations: Operaciones perdedoras
            profit_loss_total: Profit/Loss total
            profit_loss_market: P/L de órdenes Market
            profit_loss_limit: P/L de órdenes Limit
            total_queries: Total de consultas a IA
            total_tokens: Total de tokens consumidos
            total_ia_cost: Costo total de IA en USD
            
        Returns:
            DailyMetrics: Objeto con las métricas creadas
            
        Raises:
            ValueError: Si los valores son inválidos
            DailyMetricsRepositoryError: Si hay error en la BD
        """
        # Validaciones
        if bot_id <= 0:
            raise ValueError("bot_id must be positive")
        
        if winning_operations + losing_operations != total_operations:
            raise ValueError("Winning + losing operations must equal total operations")
        
        if total_operations < 0 or winning_operations < 0 or losing_operations < 0:
            raise ValueError("Operation counts must be non-negative")
        
        # Calcular ratios
        winrate = (winning_operations / total_operations * 100) if total_operations > 0 else 0.0
        profit_factor = self._calculate_profit_factor(
            total_operations, winning_operations, losing_operations,
            profit_loss_total
        )
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO metricas_diarias (
                    bot_id, fecha,
                    total_operaciones, operaciones_ganadoras, operaciones_perdedoras,
                    profit_loss_total, profit_loss_market, profit_loss_limit,
                    total_consultas, tokens_totales, costo_ia_total,
                    winrate, profit_factor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bot_id, date.isoformat(),
                total_operations, winning_operations, losing_operations,
                profit_loss_total, profit_loss_market, profit_loss_limit,
                total_queries, total_tokens, total_ia_cost,
                winrate, profit_factor
            ))
            
            metric_id = cursor.lastrowid
            
            # Recuperar el registro creado
            cursor.execute("""
                SELECT * FROM metricas_diarias WHERE id = ?
            """, (metric_id,))
            
            row = cursor.fetchone()
            conn.commit()
            conn.close()
            
            metric = self._row_to_metrics(row)
            
            logger.info(f"Created daily metrics: bot_id={bot_id}, date={date}, "
                       f"operations={total_operations}, winrate={winrate:.2f}%")
            
            return metric
            
        except sqlite3.IntegrityError as e:
            raise DailyMetricsRepositoryError(
                f"Duplicate metrics for bot {bot_id} on {date}: {str(e)}"
            )
        except Exception as e:
            raise DailyMetricsRepositoryError(f"Error creating metrics: {str(e)}")
    
    def _calculate_profit_factor(
        self,
        total_operations: int,
        winning_operations: int,
        losing_operations: int,
        profit_loss_total: float
    ) -> float:
        """
        Calcula el profit factor.
        
        Profit Factor = Ganancias Totales / Pérdidas Totales
        
        Nota: Para calcular correctamente, necesitamos separar ganancias y pérdidas.
        Por ahora, usamos una aproximación basada en el P/L total.
        """
        if total_operations == 0:
            return 0.0
        
        # Si no hay pérdidas, profit factor es infinito (usamos 999.0)
        if losing_operations == 0:
            return 999.0 if winning_operations > 0 else 0.0
        
        # Aproximación: asumimos distribución equitativa
        # En implementación real, se debe calcular desde operaciones individuales
        if profit_loss_total <= 0:
            return 0.0
        
        # Estimación simple: ratio basado en operaciones
        # Esto se refinará en consolidate_metrics_for_date()
        estimated_factor = winning_operations / losing_operations if losing_operations > 0 else 999.0
        
        return round(estimated_factor, 2)
    
    def consolidate_metrics_for_date(
        self,
        bot_id: int,
        target_date: date_type,
        operations_repo,
        ia_repo
    ) -> DailyMetrics:
        """
        Consolida métricas para una fecha específica desde los repositorios.
        
        Lee todas las operaciones y consultas IA del día y calcula las métricas.
        
        Args:
            bot_id: ID del bot
            target_date: Fecha a consolidar
            operations_repo: Instancia de OperationsRepository
            ia_repo: Instancia de IAQueryRepository
            
        Returns:
            DailyMetrics: Métricas consolidadas
        """
        from src.core.operations_repository import OperationStatus, OrderType
        
        # Obtener operaciones cerradas del día
        all_operations = operations_repo.list_operations(
            status=OperationStatus.CLOSED,
            bot_id=bot_id
        )
        
        # Filtrar por fecha
        date_operations = [
            op for op in all_operations
            if op.close_time and op.close_time.date() == target_date
        ]
        
        # Calcular métricas de operaciones
        total_ops = len(date_operations)
        winning_ops = sum(1 for op in date_operations if op.profit_loss and op.profit_loss > 0)
        losing_ops = sum(1 for op in date_operations if op.profit_loss and op.profit_loss < 0)
        
        # P/L total y por tipo
        pl_total = sum(op.profit_loss for op in date_operations if op.profit_loss)
        pl_market = sum(
            op.profit_loss for op in date_operations
            if op.profit_loss and op.order_type == OrderType.MARKET
        )
        pl_limit = sum(
            op.profit_loss for op in date_operations
            if op.profit_loss and op.order_type == OrderType.LIMIT
        )
        
        # Calcular profit factor real
        gross_profit = sum(op.profit_loss for op in date_operations if op.profit_loss and op.profit_loss > 0)
        gross_loss = abs(sum(op.profit_loss for op in date_operations if op.profit_loss and op.profit_loss < 0))
        profit_factor_real = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
        
        # Obtener consultas IA del día
        all_queries = ia_repo.get_queries_by_bot(bot_id=bot_id)
        
        # Filtrar por fecha
        date_queries = [
            q for q in all_queries
            if q.created_at and q.created_at.date() == target_date
        ]
        
        # Métricas de IA
        total_queries = len(date_queries)
        total_tokens = sum(q.tokens_total for q in date_queries)
        total_cost = sum(q.cost_usd for q in date_queries)
        
        # Crear métricas diarias
        winrate = (winning_ops / total_ops * 100) if total_ops > 0 else 0.0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Intentar actualizar primero (si ya existe)
            cursor.execute("""
                UPDATE metricas_diarias SET
                    total_operaciones = ?,
                    operaciones_ganadoras = ?,
                    operaciones_perdedoras = ?,
                    profit_loss_total = ?,
                    profit_loss_market = ?,
                    profit_loss_limit = ?,
                    total_consultas = ?,
                    tokens_totales = ?,
                    costo_ia_total = ?,
                    winrate = ?,
                    profit_factor = ?
                WHERE bot_id = ? AND fecha = ?
            """, (
                total_ops, winning_ops, losing_ops,
                pl_total, pl_market, pl_limit,
                total_queries, total_tokens, total_cost,
                winrate, profit_factor_real,
                bot_id, target_date.isoformat()
            ))
            
            if cursor.rowcount == 0:
                # No existe, insertar nuevo
                cursor.execute("""
                    INSERT INTO metricas_diarias (
                        bot_id, fecha,
                        total_operaciones, operaciones_ganadoras, operaciones_perdedoras,
                        profit_loss_total, profit_loss_market, profit_loss_limit,
                        total_consultas, tokens_totales, costo_ia_total,
                        winrate, profit_factor
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bot_id, target_date.isoformat(),
                    total_ops, winning_ops, losing_ops,
                    pl_total, pl_market, pl_limit,
                    total_queries, total_tokens, total_cost,
                    winrate, profit_factor_real
                ))
                metric_id = cursor.lastrowid
            else:
                # Recuperar ID del registro actualizado
                cursor.execute("""
                    SELECT id FROM metricas_diarias 
                    WHERE bot_id = ? AND fecha = ?
                """, (bot_id, target_date.isoformat()))
                metric_id = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            # Recuperar el registro completo
            result = self.get_metrics_by_bot_and_date(bot_id, target_date)
            if result is None:
                raise DailyMetricsRepositoryError("Failed to retrieve consolidated metrics")
            return result
            
        except Exception as e:
            raise DailyMetricsRepositoryError(f"Error consolidating metrics: {str(e)}")
    
    def get_metrics_by_bot_and_date(
        self,
        bot_id: int,
        date: date_type
    ) -> Optional[DailyMetrics]:
        """
        Obtiene las métricas de un bot en una fecha específica.
        
        Args:
            bot_id: ID del bot
            date: Fecha de las métricas
            
        Returns:
            DailyMetrics o None si no existe
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM metricas_diarias 
            WHERE bot_id = ? AND fecha = ?
        """, (bot_id, date.isoformat()))
        
        row = cursor.fetchone()
        conn.close()
        
        return self._row_to_metrics(row) if row else None
    
    def get_metrics_by_bot(self, bot_id: int) -> List[DailyMetrics]:
        """
        Obtiene todas las métricas de un bot.
        
        Args:
            bot_id: ID del bot
            
        Returns:
            Lista de DailyMetrics ordenadas por fecha descendente
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM metricas_diarias 
            WHERE bot_id = ?
            ORDER BY fecha DESC
        """, (bot_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_metrics(row) for row in rows]
    
    def get_metrics_by_date_range(
        self,
        bot_id: int,
        start_date: date_type,
        end_date: date_type
    ) -> List[DailyMetrics]:
        """
        Obtiene métricas de un bot en un rango de fechas.
        
        Args:
            bot_id: ID del bot
            start_date: Fecha inicial (incluida)
            end_date: Fecha final (incluida)
            
        Returns:
            Lista de DailyMetrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM metricas_diarias 
            WHERE bot_id = ? AND fecha BETWEEN ? AND ?
            ORDER BY fecha DESC
        """, (bot_id, start_date.isoformat(), end_date.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_metrics(row) for row in rows]
    
    def get_all_metrics(self) -> List[DailyMetrics]:
        """
        Obtiene todas las métricas del sistema.
        
        Returns:
            Lista de todas las DailyMetrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM metricas_diarias 
            ORDER BY fecha DESC, bot_id
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_metrics(row) for row in rows]
    
    def get_statistics_by_bot(self, bot_id: int) -> Dict[str, Any]:
        """
        Calcula estadísticas agregadas de un bot.
        
        Args:
            bot_id: ID del bot
            
        Returns:
            Diccionario con estadísticas agregadas
        """
        metrics = self.get_metrics_by_bot(bot_id)
        
        if not metrics:
            return {
                'total_days': 0,
                'total_operations': 0,
                'total_winning': 0,
                'total_losing': 0,
                'total_profit_loss': 0.0,
                'total_ia_cost': 0.0,
                'average_winrate': 0.0,
                'average_profit_factor': 0.0
            }
        
        total_days = len(metrics)
        total_ops = sum(m.total_operations for m in metrics)
        total_winning = sum(m.winning_operations for m in metrics)
        total_losing = sum(m.losing_operations for m in metrics)
        total_pl = sum(m.profit_loss_total for m in metrics)
        total_cost = sum(m.total_ia_cost for m in metrics)
        
        avg_winrate = sum(m.winrate for m in metrics) / total_days
        avg_pf = sum(m.profit_factor for m in metrics if m.profit_factor < 999) / total_days
        
        return {
            'total_days': total_days,
            'total_operations': total_ops,
            'total_winning': total_winning,
            'total_losing': total_losing,
            'total_profit_loss': round(total_pl, 2),
            'total_ia_cost': round(total_cost, 4),
            'average_winrate': round(avg_winrate, 2),
            'average_profit_factor': round(avg_pf, 2)
        }
    
    def get_total_statistics(self) -> Dict[str, Any]:
        """
        Calcula estadísticas totales del sistema.
        
        Returns:
            Diccionario con estadísticas globales
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT bot_id) as total_bots,
                COUNT(*) as total_days,
                SUM(total_operaciones) as total_operations,
                SUM(operaciones_ganadoras) as total_winning,
                SUM(operaciones_perdedoras) as total_losing,
                SUM(profit_loss_total) as total_profit_loss,
                SUM(costo_ia_total) as total_ia_cost,
                AVG(winrate) as avg_winrate,
                AVG(CASE WHEN profit_factor < 999 THEN profit_factor END) as avg_profit_factor
            FROM metricas_diarias
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {}
        
        return {
            'total_bots': row[0] or 0,
            'total_days': row[1] or 0,
            'total_operations': row[2] or 0,
            'total_winning': row[3] or 0,
            'total_losing': row[4] or 0,
            'total_profit_loss': round(row[5] or 0.0, 2),
            'total_ia_cost': round(row[6] or 0.0, 4),
            'average_winrate': round(row[7] or 0.0, 2),
            'average_profit_factor': round(row[8] or 0.0, 2)
        }
    
    def _row_to_metrics(self, row) -> DailyMetrics:
        """
        Convierte una fila de BD a objeto DailyMetrics.
        
        Args:
            row: Tupla con datos de la BD
            
        Returns:
            DailyMetrics
        """
        return DailyMetrics(
            id=row[0],
            bot_id=row[1],
            date=datetime.fromisoformat(row[2]).date(),
            total_operations=row[3],
            winning_operations=row[4],
            losing_operations=row[5],
            profit_loss_total=row[6],
            profit_loss_market=row[7],
            profit_loss_limit=row[8],
            total_queries=row[9],
            total_tokens=row[10],
            total_ia_cost=row[11],
            winrate=row[12],
            profit_factor=row[13],
            created_at=datetime.fromisoformat(row[14]) if row[14] else None
        )
    
    def close(self):
        """Cierra cualquier conexión abierta (compatibilidad con context manager)"""
        # SQLite cierra automáticamente las conexiones
        # Este método es para compatibilidad con tests
        pass


# ==================== FUNCIONES DE UTILIDAD ====================

def consolidate_all_bots_for_date(
    target_date: date_type,
    bot_ids: List[int],
    metrics_repo: DailyMetricsRepository,
    operations_repo,
    ia_repo
) -> List[DailyMetrics]:
    """
    Consolida métricas de todos los bots para una fecha.
    
    Args:
        target_date: Fecha a consolidar
        bot_ids: Lista de IDs de bots
        metrics_repo: Repositorio de métricas
        operations_repo: Repositorio de operaciones
        ia_repo: Repositorio de consultas IA
        
    Returns:
        Lista de DailyMetrics consolidadas
    """
    results = []
    
    for bot_id in bot_ids:
        try:
            metric = metrics_repo.consolidate_metrics_for_date(
                bot_id=bot_id,
                target_date=target_date,
                operations_repo=operations_repo,
                ia_repo=ia_repo
            )
            results.append(metric)
            logger.info(f"Consolidated metrics for bot {bot_id} on {target_date}")
        except Exception as e:
            logger.error(f"Error consolidating bot {bot_id}: {str(e)}")
    
    return results
