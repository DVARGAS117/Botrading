"""
DualPerformanceTracker - Registro y comparación de desempeño Market vs Limit - T15

Este módulo implementa la funcionalidad del Ticket T15: Registro y comparación
de desempeño entre órdenes Market y Limit, incluyendo P/L y tasas de activación.

Características:
- Registro de performance para órdenes Market y Limit
- Comparación de P/L por operación individual
- Comparación de métricas diarias consolidadas
- Cálculo de tasas de activación (especialmente para Limit)
- Métricas agregadas por símbolo, bot y período
- Persistencia en SQLite

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T15 - Registro y comparación de desempeño Market vs Limit
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
import logging


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class DualPerformanceTrackerError(Exception):
    """Excepción base para errores del DualPerformanceTracker"""
    pass


class InvalidPerformanceDataError(DualPerformanceTrackerError):
    """Excepción para datos de performance inválidos"""
    pass


# ==================== DATA CLASSES ====================

@dataclass
class PerformanceRecord:
    """
    Registro de performance para una orden individual (Market o Limit).
    
    Attributes:
        symbol: Símbolo del instrumento (ej: "EURUSD")
        bot_id: ID del bot (1-5)
        order_type: Tipo de orden ("market" o "limit")
        magic_number: Magic Number único de la orden
        open_time: Timestamp de apertura de la orden
        close_time: Timestamp de cierre (None si no se activó/cerró)
        entry_price: Precio de entrada
        exit_price: Precio de salida (None si no se cerró)
        lot_size: Tamaño del lote
        profit_loss: Ganancia o pérdida en valor monetario
        is_winner: True si ganó, False si perdió
        activation_status: Estado de activación ("activated", "not_activated", "pending")
    """
    symbol: str
    bot_id: int
    order_type: str  # "market" o "limit"
    magic_number: int
    open_time: datetime
    close_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    lot_size: float
    profit_loss: float
    is_winner: bool
    activation_status: str  # "activated", "not_activated", "pending"
    
    def validate(self) -> None:
        """
        Valida los datos del record.
        
        Raises:
            InvalidPerformanceDataError: Si algún dato es inválido
        """
        # Validar símbolo
        if not self.symbol or not self.symbol.strip():
            raise InvalidPerformanceDataError(
                "El símbolo es requerido y no puede estar vacío"
            )
        
        # Validar order_type
        if self.order_type.lower() not in ('market', 'limit'):
            raise InvalidPerformanceDataError(
                f"order_type debe ser 'market' o 'limit', recibido: '{self.order_type}'"
            )
        
        # Validar activation_status
        valid_statuses = ('activated', 'not_activated', 'pending')
        if self.activation_status.lower() not in valid_statuses:
            raise InvalidPerformanceDataError(
                f"activation_status debe ser uno de {valid_statuses}, "
                f"recibido: '{self.activation_status}'"
            )
        
        # Validar bot_id
        if not isinstance(self.bot_id, int) or not (1 <= self.bot_id <= 5):
            raise InvalidPerformanceDataError(
                f"bot_id debe estar entre 1 y 5, recibido: {self.bot_id}"
            )
        
        # Validar magic_number
        if not isinstance(self.magic_number, int) or self.magic_number < 0:
            raise InvalidPerformanceDataError(
                f"magic_number debe ser un entero positivo, recibido: {self.magic_number}"
            )
        
        # Validar lot_size
        if self.lot_size <= 0:
            raise InvalidPerformanceDataError(
                f"lot_size debe ser mayor a 0, recibido: {self.lot_size}"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el record a diccionario.
        
        Returns:
            Dict con todos los campos
        """
        return {
            'symbol': self.symbol,
            'bot_id': self.bot_id,
            'order_type': self.order_type,
            'magic_number': self.magic_number,
            'open_time': self.open_time.isoformat() if self.open_time else None,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'lot_size': self.lot_size,
            'profit_loss': self.profit_loss,
            'is_winner': self.is_winner,
            'activation_status': self.activation_status
        }


@dataclass
class OperationPerformance:
    """
    Comparación de performance para un par Market/Limit de una misma operación.
    
    Attributes:
        market_magic: Magic Number de la orden Market
        limit_magic: Magic Number de la orden Limit
        symbol: Símbolo del par
        bot_id: ID del bot
        market_pl: P/L de la orden Market
        limit_pl: P/L de la orden Limit
        market_activated: True si Market se activó
        limit_activated: True si Limit se activó
        pl_difference: Diferencia de P/L (Market - Limit)
        better_performer: "market", "limit" o "tie"
    """
    market_magic: int
    limit_magic: int
    symbol: str
    bot_id: int
    market_pl: float
    limit_pl: float
    market_activated: bool
    limit_activated: bool
    pl_difference: float = field(init=False)
    better_performer: str = field(init=False)
    
    def __post_init__(self):
        """Calcula campos derivados después de la inicialización"""
        self.pl_difference = self.market_pl - self.limit_pl
        
        if self.market_pl > self.limit_pl:
            self.better_performer = "market"
        elif self.limit_pl > self.market_pl:
            self.better_performer = "limit"
        else:
            self.better_performer = "tie"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            'market_magic': self.market_magic,
            'limit_magic': self.limit_magic,
            'symbol': self.symbol,
            'bot_id': self.bot_id,
            'market_pl': self.market_pl,
            'limit_pl': self.limit_pl,
            'market_activated': self.market_activated,
            'limit_activated': self.limit_activated,
            'pl_difference': self.pl_difference,
            'better_performer': self.better_performer
        }


@dataclass
class DailyPerformanceComparison:
    """
    Comparación de performance diaria entre Market y Limit.
    
    Attributes:
        bot_id: ID del bot
        target_date: Fecha objetivo
        market_total_pl: P/L total de órdenes Market
        limit_total_pl: P/L total de órdenes Limit
        market_count: Cantidad de órdenes Market
        limit_count: Cantidad de órdenes Limit
        market_activated_count: Cantidad de Market activadas
        limit_activated_count: Cantidad de Limit activadas
        market_activation_rate: Tasa de activación Market (0.0 - 1.0)
        limit_activation_rate: Tasa de activación Limit (0.0 - 1.0)
        market_avg_pl: P/L promedio Market
        limit_avg_pl: P/L promedio Limit
        better_daily_performer: "market", "limit" o "tie"
    """
    bot_id: int
    target_date: date
    market_total_pl: float
    limit_total_pl: float
    market_count: int
    limit_count: int
    market_activated_count: int
    limit_activated_count: int
    market_activation_rate: float = field(init=False)
    limit_activation_rate: float = field(init=False)
    market_avg_pl: float = field(init=False)
    limit_avg_pl: float = field(init=False)
    better_daily_performer: str = field(init=False)
    
    def __post_init__(self):
        """Calcula campos derivados"""
        # Tasas de activación
        self.market_activation_rate = (
            self.market_activated_count / self.market_count
            if self.market_count > 0 else 0.0
        )
        
        self.limit_activation_rate = (
            self.limit_activated_count / self.limit_count
            if self.limit_count > 0 else 0.0
        )
        
        # P/L promedio
        self.market_avg_pl = (
            self.market_total_pl / self.market_activated_count
            if self.market_activated_count > 0 else 0.0
        )
        
        self.limit_avg_pl = (
            self.limit_total_pl / self.limit_activated_count
            if self.limit_activated_count > 0 else 0.0
        )
        
        # Mejor performer
        if self.market_total_pl > self.limit_total_pl:
            self.better_daily_performer = "market"
        elif self.limit_total_pl > self.market_total_pl:
            self.better_daily_performer = "limit"
        else:
            self.better_daily_performer = "tie"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        return {
            'bot_id': self.bot_id,
            'target_date': self.target_date.isoformat(),
            'market_total_pl': self.market_total_pl,
            'limit_total_pl': self.limit_total_pl,
            'market_count': self.market_count,
            'limit_count': self.limit_count,
            'market_activated_count': self.market_activated_count,
            'limit_activated_count': self.limit_activated_count,
            'market_activation_rate': self.market_activation_rate,
            'limit_activation_rate': self.limit_activation_rate,
            'market_avg_pl': self.market_avg_pl,
            'limit_avg_pl': self.limit_avg_pl,
            'better_daily_performer': self.better_daily_performer
        }


# ==================== DUAL PERFORMANCE TRACKER ====================

class DualPerformanceTracker:
    """
    Tracker de performance para comparar órdenes Market vs Limit.
    
    Registra y compara el desempeño de pares Market/Limit considerando:
    - P/L individual y agregado
    - Tasas de activación (especialmente importante para Limit)
    - Métricas diarias consolidadas
    - Análisis por bot, símbolo y período
    
    Example:
        >>> from src.core.dual_performance_tracker import (
        ...     DualPerformanceTracker,
        ...     PerformanceRecord
        ... )
        >>> from datetime import datetime, date
        >>> 
        >>> # Crear tracker
        >>> tracker = DualPerformanceTracker()
        >>> 
        >>> # Registrar orden Market
        >>> market_record = PerformanceRecord(
        ...     symbol="EURUSD",
        ...     bot_id=1,
        ...     order_type="market",
        ...     magic_number=101000,
        ...     open_time=datetime.now(),
        ...     close_time=datetime.now(),
        ...     entry_price=1.1000,
        ...     exit_price=1.1050,
        ...     lot_size=0.1,
        ...     profit_loss=50.0,
        ...     is_winner=True,
        ...     activation_status="activated"
        ... )
        >>> tracker.register_performance(market_record)
        >>> 
        >>> # Comparar performance diaria
        >>> daily_comp = tracker.compare_daily_performance(
        ...     bot_id=1,
        ...     target_date=date.today()
        ... )
        >>> print(f"Market total P/L: {daily_comp.market_total_pl}")
        >>> print(f"Limit total P/L: {daily_comp.limit_total_pl}")
    """
    
    def __init__(
        self,
        db_path: str = "data/trading.db",
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa el DualPerformanceTracker.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
            logger: Logger personalizado (opcional)
        """
        self.db_path = Path(db_path)
        
        # Configurar logger
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
        
        # Inicializar base de datos
        self._initialize_database()
        
        self.logger.debug("DualPerformanceTracker inicializado correctamente")
    
    # ==================== MÉTODOS PÚBLICOS ====================
    
    def register_performance(self, record: PerformanceRecord) -> bool:
        """
        Registra la performance de una orden (Market o Limit).
        
        Args:
            record: PerformanceRecord con los datos de la orden
        
        Returns:
            True si el registro fue exitoso
        
        Raises:
            InvalidPerformanceDataError: Si los datos son inválidos
            DualPerformanceTrackerError: Si el Magic Number ya está registrado
        
        Example:
            >>> record = PerformanceRecord(...)
            >>> success = tracker.register_performance(record)
        """
        # Validar record
        record.validate()
        
        # Verificar que no exista duplicado
        if self._magic_number_exists(record.magic_number):
            raise DualPerformanceTrackerError(
                f"Magic Number {record.magic_number} ya está registrado"
            )
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO dual_performance (
                        symbol, bot_id, order_type, magic_number,
                        open_time, close_time, entry_price, exit_price,
                        lot_size, profit_loss, is_winner, activation_status,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.symbol,
                    record.bot_id,
                    record.order_type.lower(),
                    record.magic_number,
                    record.open_time.isoformat(),
                    record.close_time.isoformat() if record.close_time else None,
                    record.entry_price,
                    record.exit_price,
                    record.lot_size,
                    record.profit_loss,
                    1 if record.is_winner else 0,
                    record.activation_status.lower(),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
            
            self.logger.info(
                f"Performance registrada - Magic: {record.magic_number}, "
                f"Type: {record.order_type}, P/L: {record.profit_loss}"
            )
            
            return True
        
        except sqlite3.Error as e:
            error_msg = f"Error registrando performance: {e}"
            self.logger.error(error_msg)
            raise DualPerformanceTrackerError(error_msg) from e
    
    def compare_operation_performance(
        self,
        market_magic: int,
        limit_magic: int
    ) -> OperationPerformance:
        """
        Compara la performance de un par Market/Limit.
        
        Args:
            market_magic: Magic Number de la orden Market
            limit_magic: Magic Number de la orden Limit
        
        Returns:
            OperationPerformance con la comparación
        
        Raises:
            DualPerformanceTrackerError: Si algún Magic Number no existe
        
        Example:
            >>> comparison = tracker.compare_operation_performance(
            ...     market_magic=101000,
            ...     limit_magic=101001
            ... )
            >>> print(f"Market P/L: {comparison.market_pl}")
            >>> print(f"Limit P/L: {comparison.limit_pl}")
            >>> print(f"Winner: {comparison.better_performer}")
        """
        # Obtener datos de Market
        market_data = self._get_performance_by_magic(market_magic)
        if not market_data:
            raise DualPerformanceTrackerError(
                f"Magic Number Market {market_magic} no encontrado"
            )
        
        # Obtener datos de Limit
        limit_data = self._get_performance_by_magic(limit_magic)
        if not limit_data:
            raise DualPerformanceTrackerError(
                f"Magic Number Limit {limit_magic} no encontrado"
            )
        
        # Crear comparación
        comparison = OperationPerformance(
            market_magic=market_magic,
            limit_magic=limit_magic,
            symbol=market_data['symbol'],
            bot_id=market_data['bot_id'],
            market_pl=market_data['profit_loss'],
            limit_pl=limit_data['profit_loss'],
            market_activated=market_data['activation_status'] == 'activated',
            limit_activated=limit_data['activation_status'] == 'activated'
        )
        
        self.logger.debug(
            f"Comparación de operación - Market: {market_magic}, "
            f"Limit: {limit_magic}, Winner: {comparison.better_performer}"
        )
        
        return comparison
    
    def compare_daily_performance(
        self,
        bot_id: int,
        target_date: Optional[date] = None
    ) -> DailyPerformanceComparison:
        """
        Compara la performance diaria entre Market y Limit para un bot.
        
        Args:
            bot_id: ID del bot
            target_date: Fecha objetivo (por defecto hoy)
        
        Returns:
            DailyPerformanceComparison con métricas consolidadas
        
        Example:
            >>> daily = tracker.compare_daily_performance(
            ...     bot_id=1,
            ...     target_date=date(2025, 11, 13)
            ... )
            >>> print(f"Market activation rate: {daily.market_activation_rate:.2%}")
            >>> print(f"Limit activation rate: {daily.limit_activation_rate:.2%}")
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener métricas de Market
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(profit_loss), 0) as total_pl,
                        COUNT(*) as total_count,
                        COALESCE(SUM(CASE WHEN activation_status = 'activated' THEN 1 ELSE 0 END), 0) as activated_count
                    FROM dual_performance
                    WHERE bot_id = ?
                      AND order_type = 'market'
                      AND DATE(open_time) = ?
                """, (bot_id, target_date.isoformat()))
                
                market_row = cursor.fetchone()
                market_total_pl = float(market_row[0]) if market_row and market_row[0] is not None else 0.0
                market_count = int(market_row[1]) if market_row and market_row[1] is not None else 0
                market_activated = int(market_row[2]) if market_row and market_row[2] is not None else 0
                
                # Obtener métricas de Limit
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(profit_loss), 0) as total_pl,
                        COUNT(*) as total_count,
                        COALESCE(SUM(CASE WHEN activation_status = 'activated' THEN 1 ELSE 0 END), 0) as activated_count
                    FROM dual_performance
                    WHERE bot_id = ?
                      AND order_type = 'limit'
                      AND DATE(open_time) = ?
                """, (bot_id, target_date.isoformat()))
                
                limit_row = cursor.fetchone()
                limit_total_pl = float(limit_row[0]) if limit_row and limit_row[0] is not None else 0.0
                limit_count = int(limit_row[1]) if limit_row and limit_row[1] is not None else 0
                limit_activated = int(limit_row[2]) if limit_row and limit_row[2] is not None else 0
            
            # Crear comparación diaria
            comparison = DailyPerformanceComparison(
                bot_id=bot_id,
                target_date=target_date,
                market_total_pl=market_total_pl,
                limit_total_pl=limit_total_pl,
                market_count=market_count,
                limit_count=limit_count,
                market_activated_count=market_activated,
                limit_activated_count=limit_activated
            )
            
            self.logger.info(
                f"Comparación diaria - Bot: {bot_id}, Fecha: {target_date}, "
                f"Market P/L: {market_total_pl:.2f}, Limit P/L: {limit_total_pl:.2f}"
            )
            
            return comparison
        
        except sqlite3.Error as e:
            error_msg = f"Error comparando performance diaria: {e}"
            self.logger.error(error_msg)
            raise DualPerformanceTrackerError(error_msg) from e
    
    def get_aggregated_metrics(
        self,
        group_by: str,
        start_date: date,
        end_date: date
    ) -> Dict[Any, Dict[str, Any]]:
        """
        Obtiene métricas agregadas por grupo.
        
        Args:
            group_by: Campo para agrupar ("symbol", "bot_id", "order_type")
            start_date: Fecha de inicio del período
            end_date: Fecha de fin del período
        
        Returns:
            Dict con métricas agregadas por grupo
        
        Raises:
            DualPerformanceTrackerError: Si group_by es inválido
        
        Example:
            >>> metrics = tracker.get_aggregated_metrics(
            ...     group_by="symbol",
            ...     start_date=date(2025, 11, 1),
            ...     end_date=date(2025, 11, 30)
            ... )
            >>> for symbol, data in metrics.items():
            ...     print(f"{symbol}: P/L = {data['total_pl']}")
        """
        valid_groups = ['symbol', 'bot_id', 'order_type']
        if group_by not in valid_groups:
            raise DualPerformanceTrackerError(
                f"group_by debe ser uno de {valid_groups}, recibido: '{group_by}'"
            )
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = f"""
                    SELECT 
                        {group_by},
                        COUNT(*) as count,
                        SUM(profit_loss) as total_pl,
                        AVG(profit_loss) as avg_pl,
                        SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) as winners,
                        SUM(CASE WHEN activation_status = 'activated' THEN 1 ELSE 0 END) as activated
                    FROM dual_performance
                    WHERE DATE(open_time) BETWEEN ? AND ?
                    GROUP BY {group_by}
                """
                
                cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
                
                results = {}
                for row in cursor.fetchall():
                    group_value = row[0]
                    results[group_value] = {
                        'count': row[1],
                        'total_pl': row[2] if row[2] else 0.0,
                        'avg_pl': row[3] if row[3] else 0.0,
                        'winners': row[4] if row[4] else 0,
                        'activated': row[5] if row[5] else 0,
                        'win_rate': (row[4] / row[1]) if row[1] > 0 else 0.0,
                        'activation_rate': (row[5] / row[1]) if row[1] > 0 else 0.0
                    }
                
                return results
        
        except sqlite3.Error as e:
            error_msg = f"Error obteniendo métricas agregadas: {e}"
            self.logger.error(error_msg)
            raise DualPerformanceTrackerError(error_msg) from e
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    def _initialize_database(self) -> None:
        """Inicializa la base de datos y crea las tablas si no existen"""
        # Crear directorio si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Crear tabla dual_performance
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dual_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        bot_id INTEGER NOT NULL,
                        order_type TEXT NOT NULL,
                        magic_number INTEGER NOT NULL UNIQUE,
                        open_time TEXT NOT NULL,
                        close_time TEXT,
                        entry_price REAL NOT NULL,
                        exit_price REAL,
                        lot_size REAL NOT NULL,
                        profit_loss REAL NOT NULL,
                        is_winner INTEGER NOT NULL,
                        activation_status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        CONSTRAINT chk_order_type CHECK (order_type IN ('market', 'limit')),
                        CONSTRAINT chk_activation CHECK (activation_status IN ('activated', 'not_activated', 'pending'))
                    )
                """)
                
                # Crear índices para consultas eficientes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_dual_perf_bot_date 
                    ON dual_performance(bot_id, open_time)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_dual_perf_symbol 
                    ON dual_performance(symbol)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_dual_perf_magic 
                    ON dual_performance(magic_number)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_dual_perf_order_type 
                    ON dual_performance(order_type)
                """)
                
                conn.commit()
            
            self.logger.debug("Base de datos inicializada correctamente")
        
        except sqlite3.Error as e:
            error_msg = f"Error inicializando base de datos: {e}"
            self.logger.error(error_msg)
            raise DualPerformanceTrackerError(error_msg) from e
    
    def _magic_number_exists(self, magic_number: int) -> bool:
        """Verifica si un Magic Number ya existe en la BD"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM dual_performance WHERE magic_number = ?",
                    (magic_number,)
                )
                count = cursor.fetchone()[0]
                return count > 0
        
        except sqlite3.Error:
            return False
    
    def _get_performance_by_magic(self, magic_number: int) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de performance por Magic Number"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        symbol, bot_id, order_type, magic_number,
                        open_time, close_time, entry_price, exit_price,
                        lot_size, profit_loss, is_winner, activation_status
                    FROM dual_performance
                    WHERE magic_number = ?
                """, (magic_number,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    'symbol': row[0],
                    'bot_id': row[1],
                    'order_type': row[2],
                    'magic_number': row[3],
                    'open_time': row[4],
                    'close_time': row[5],
                    'entry_price': row[6],
                    'exit_price': row[7],
                    'lot_size': row[8],
                    'profit_loss': row[9],
                    'is_winner': bool(row[10]),
                    'activation_status': row[11]
                }
        
        except sqlite3.Error:
            return None
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        return f"<DualPerformanceTracker(db='{self.db_path}')>"
    
    def __str__(self) -> str:
        """Representación en string"""
        return "DualPerformanceTracker - Comparador de performance Market vs Limit"
