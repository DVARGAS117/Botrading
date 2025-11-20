"""
OperationsRepository - Persistencia de operaciones en SQLite - T32

Este módulo implementa la funcionalidad del Ticket T32: Persistencia de operaciones
con todos los parámetros, estados y resultados para análisis posterior y cumplimiento.

Características:
- Creación y almacenamiento de operaciones
- Consulta por ID, Magic Number, símbolo y estado
- Actualización de operaciones (SL/TP, estado, profit/loss)
- Índices optimizados para consultas eficientes
- Validación de tipos y constraines
- Manejo robusto de errores

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T32 - Persistencia de operaciones con parámetros y estados
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
import logging


# ==================== ENUMS ====================

class OrderType(str, Enum):
    """Tipos de orden soportados"""
    MARKET = "market"
    LIMIT = "limit"


class Direction(str, Enum):
    """Direcciones de operación"""
    BUY = "BUY"
    SELL = "SELL"


class OperationStatus(str, Enum):
    """Estados de operación"""
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"


# ==================== EXCEPCIONES ====================

class OperationsRepositoryError(Exception):
    """Excepción base para errores del repositorio"""
    pass


# ==================== MODELOS ====================

@dataclass
class Operation:
    """
    Modelo de datos para una operación de trading.
    
    Representa una operación completa con todos sus parámetros,
    desde la apertura hasta el cierre.
    """
    # Identificación
    id: Optional[int] = None
    magic_number: int = 0
    bot_id: int = 0
    ia_id: int = 0
    
    # Tipo y dirección
    order_type: OrderType = OrderType.MARKET
    symbol: str = ""
    direction: Direction = Direction.BUY
    
    # Precios y parámetros
    suggested_price: float = 0.0
    actual_entry_price: Optional[float] = None
    stop_loss: float = 0.0
    take_profit: float = 0.0
    stop_loss_initial: Optional[float] = None  # SL al momento de apertura (para trailing stop)
    take_profit_initial: Optional[float] = None  # TP al momento de apertura
    lot_size: float = 0.0
    risk_percentage: float = 0.0
    
    # Estado y resultados
    status: OperationStatus = OperationStatus.PENDING
    profit_loss: Optional[float] = None
    
    # Tiempos
    open_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    
    # Referencia a IA
    conversation_id: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la operación a diccionario"""
        return {
            'id': self.id,
            'magic_number': self.magic_number,
            'bot_id': self.bot_id,
            'ia_id': self.ia_id,
            'order_type': self.order_type.value if isinstance(self.order_type, OrderType) else self.order_type,
            'symbol': self.symbol,
            'direction': self.direction.value if isinstance(self.direction, Direction) else self.direction,
            'suggested_price': self.suggested_price,
            'actual_entry_price': self.actual_entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'lot_size': self.lot_size,
            'risk_percentage': self.risk_percentage,
            'status': self.status.value if isinstance(self.status, OperationStatus) else self.status,
            'profit_loss': self.profit_loss,
            'open_time': self.open_time.isoformat() if self.open_time else None,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'conversation_id': self.conversation_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ==================== REPOSITORIO ====================

class OperationsRepository:
    """
    Repositorio para persistencia de operaciones en SQLite.
    
    Gestiona el ciclo de vida completo de las operaciones:
    - Creación de nuevas operaciones
    - Consulta por diversos criterios
    - Actualización de parámetros y estados
    - Eliminación (soft delete recomendado)
    - Estadísticas y métricas
    
    Ejemplo:
        >>> repo = OperationsRepository(db_path=Path("data/operations.db"))
        >>> operation = repo.create_operation(
        ...     magic_number=123456,
        ...     bot_id=1,
        ...     ia_id=1,
        ...     order_type=OrderType.MARKET,
        ...     symbol="EURUSD",
        ...     direction=Direction.BUY,
        ...     suggested_price=1.0850,
        ...     stop_loss=1.0800,
        ...     take_profit=1.0950,
        ...     lot_size=0.10,
        ...     risk_percentage=1.0,
        ...     status=OperationStatus.OPEN
        ... )
        >>> print(f"Operación creada con ID: {operation.id}")
    """
    
    def __init__(self, db_path: Path = Path("data/operations.db")):
        """
        Inicializa el repositorio y la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        
        Raises:
            OperationsRepositoryError: Si hay error al inicializar la BD
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        try:
            self._initialize_database()
            self.logger.info(f"Repositorio inicializado en {db_path}")
        except Exception as e:
            error_msg = f"Error inicializando repositorio: {e}"
            self.logger.error(error_msg)
            raise OperationsRepositoryError(error_msg) from e
    
    # ==================== MÉTODOS PÚBLICOS - CREATE ====================
    
    def create_operation(
        self,
        magic_number: int,
        bot_id: int,
        ia_id: int,
        order_type: OrderType,
        symbol: str,
        direction: Direction,
        suggested_price: float,
        stop_loss: float,
        take_profit: float,
        lot_size: float,
        risk_percentage: float,
        status: OperationStatus,
        actual_entry_price: Optional[float] = None,
        profit_loss: Optional[float] = None,
        open_time: Optional[datetime] = None,
        close_time: Optional[datetime] = None,
        conversation_id: Optional[str] = None,
        stop_loss_initial: Optional[float] = None,
        take_profit_initial: Optional[float] = None
    ) -> Operation:
        """
        Crea una nueva operación en la base de datos.
        
        Args:
            magic_number: Número mágico único de la operación
            bot_id: ID del bot que ejecuta la operación
            ia_id: ID de la configuración de IA
            order_type: Tipo de orden (MARKET o LIMIT)
            symbol: Símbolo del activo (ej: "EURUSD")
            direction: Dirección (BUY o SELL)
            suggested_price: Precio sugerido por la IA
            stop_loss: Precio de stop loss
            take_profit: Precio de take profit
            lot_size: Tamaño del lote
            risk_percentage: Porcentaje de riesgo
            status: Estado de la operación
            actual_entry_price: Precio real de entrada (opcional)
            profit_loss: Profit/Loss actual (opcional)
            open_time: Tiempo de apertura (opcional, usa datetime.now() si no se provee)
            close_time: Tiempo de cierre (opcional)
            conversation_id: ID de conversación con IA (opcional)
            stop_loss_initial: SL inicial al abrir (opcional, usa stop_loss si no se provee)
            take_profit_initial: TP inicial al abrir (opcional, usa take_profit si no se provee)
        
        Returns:
            Operation: La operación creada con su ID asignado
        
        Raises:
            OperationsRepositoryError: Si hay error en la creación
        """
        # Validar tipos enum
        if isinstance(order_type, str):
            order_type = OrderType(order_type)
        if isinstance(direction, str):
            direction = Direction(direction)
        if isinstance(status, str):
            status = OperationStatus(status)
        
        # Usar tiempo actual si no se provee
        if open_time is None:
            open_time = datetime.now()
        
        # Usar SL/TP actuales como iniciales si no se proveen
        if stop_loss_initial is None:
            stop_loss_initial = stop_loss
        if take_profit_initial is None:
            take_profit_initial = take_profit
        
        now = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO operations (
                        magic_number, bot_id, ia_id, order_type, symbol, direction,
                        suggested_price, actual_entry_price, stop_loss, take_profit,
                        stop_loss_initial, take_profit_initial,
                        lot_size, risk_percentage, status, profit_loss,
                        open_time, close_time, conversation_id,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    magic_number, bot_id, ia_id,
                    order_type.value, symbol, direction.value,
                    suggested_price, actual_entry_price,
                    stop_loss, take_profit,
                    stop_loss_initial, take_profit_initial,
                    lot_size, risk_percentage,
                    status.value, profit_loss,
                    open_time.isoformat() if open_time else None,
                    close_time.isoformat() if close_time else None,
                    conversation_id,
                    now.isoformat(), now.isoformat()
                ))
                
                operation_id = cursor.lastrowid
                conn.commit()
            
            if operation_id is None:
                raise OperationsRepositoryError("Error: no se pudo obtener el ID de la operación creada")
            
            self.logger.debug(f"Operación creada con ID: {operation_id}")
            
            # Retornar la operación completa
            created_operation = self.get_operation_by_id(operation_id)
            if created_operation is None:
                raise OperationsRepositoryError(f"Error: operación creada pero no se pudo recuperar (ID: {operation_id})")
            return created_operation
        
        except sqlite3.IntegrityError as e:
            error_msg = f"Error de integridad al crear operación (magic_number duplicado?): {e}"
            self.logger.error(error_msg)
            raise OperationsRepositoryError(error_msg) from e
        except Exception as e:
            error_msg = f"Error creando operación: {e}"
            self.logger.error(error_msg)
            raise OperationsRepositoryError(error_msg) from e
    
    # ==================== MÉTODOS PÚBLICOS - READ ====================
    
    def get_operation_by_id(self, operation_id: int) -> Optional[Operation]:
        """
        Obtiene una operación por su ID.
        
        Args:
            operation_id: ID de la operación
        
        Returns:
            Operation si existe, None si no se encuentra
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM operations WHERE id = ?
                """, (operation_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_operation(row)
                return None
        
        except Exception as e:
            self.logger.error(f"Error obteniendo operación por ID {operation_id}: {e}")
            return None
    
    def get_operation_by_magic_number(self, magic_number: int) -> Optional[Operation]:
        """
        Obtiene una operación por su Magic Number.
        
        Args:
            magic_number: Magic Number de la operación
        
        Returns:
            Operation si existe, None si no se encuentra
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM operations WHERE magic_number = ?
                """, (magic_number,))
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_operation(row)
                return None
        
        except Exception as e:
            self.logger.error(f"Error obteniendo operación por magic_number {magic_number}: {e}")
            return None
    
    def get_open_operation_for_symbol_and_magic(
        self,
        symbol: str,
        magic_number: int
    ) -> Optional[Operation]:
        """
        Obtiene una operación abierta para un símbolo y Magic Number específicos.
        
        Útil para verificar si existe una operación abierta antes de crear una nueva.
        
        Args:
            symbol: Símbolo del activo
            magic_number: Magic Number
        
        Returns:
            Operation si existe y está abierta, None si no
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM operations 
                    WHERE symbol = ? AND magic_number = ? AND status = ?
                """, (symbol, magic_number, OperationStatus.OPEN.value))
                
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_operation(row)
                return None
        
        except Exception as e:
            self.logger.error(f"Error buscando operación abierta: {e}")
            return None
    
    def list_operations(
        self,
        status: Optional[OperationStatus] = None,
        symbol: Optional[str] = None,
        bot_id: Optional[int] = None,
        order_type: Optional[OrderType] = None,
        limit: Optional[int] = None
    ) -> List[Operation]:
        """
        Lista operaciones con filtros opcionales.
        
        Args:
            status: Filtrar por estado (opcional)
            symbol: Filtrar por símbolo (opcional)
            bot_id: Filtrar por bot (opcional)
            order_type: Filtrar por tipo de orden (opcional)
            limit: Límite de resultados (opcional)
        
        Returns:
            Lista de operaciones que cumplen los criterios
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Construir query dinámicamente
                query = "SELECT * FROM operations WHERE 1=1"
                params = []
                
                if status is not None:
                    query += " AND status = ?"
                    params.append(status.value if isinstance(status, OperationStatus) else status)
                
                if symbol is not None:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                if bot_id is not None:
                    query += " AND bot_id = ?"
                    params.append(bot_id)
                
                if order_type is not None:
                    query += " AND order_type = ?"
                    params.append(order_type.value if isinstance(order_type, OrderType) else order_type)
                
                query += " ORDER BY created_at DESC"
                
                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_operation(row) for row in rows]
        
        except Exception as e:
            self.logger.error(f"Error listando operaciones: {e}")
            return []
    
    # ==================== MÉTODOS PÚBLICOS - UPDATE ====================
    
    def update_operation(
        self,
        operation_id: int,
        **kwargs
    ) -> Optional[Operation]:
        """
        Actualiza una operación existente.
        
        Args:
            operation_id: ID de la operación a actualizar
            **kwargs: Campos a actualizar (ej: status, profit_loss, close_time, etc.)
        
        Returns:
            Operation actualizada, o None si no existe
        
        Raises:
            OperationsRepositoryError: Si hay error en la actualización
        """
        if not kwargs:
            return self.get_operation_by_id(operation_id)
        
        try:
            # Construir query dinámicamente
            set_clauses = []
            params = []
            
            for key, value in kwargs.items():
                # Convertir enums a valores
                if isinstance(value, Enum):
                    value = value.value
                # Convertir datetime a ISO string
                elif isinstance(value, datetime):
                    value = value.isoformat()
                
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            # Agregar updated_at
            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            # Agregar operation_id al final
            params.append(operation_id)
            
            query = f"UPDATE operations SET {', '.join(set_clauses)} WHERE id = ?"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                
                if cursor.rowcount == 0:
                    self.logger.warning(f"No se encontró operación con ID {operation_id}")
                    return None
            
            self.logger.debug(f"Operación {operation_id} actualizada")
            return self.get_operation_by_id(operation_id)
        
        except Exception as e:
            error_msg = f"Error actualizando operación {operation_id}: {e}"
            self.logger.error(error_msg)
            raise OperationsRepositoryError(error_msg) from e
    
    def close_operation(
        self,
        operation_id: int,
        profit_loss: float
    ) -> Optional[Operation]:
        """
        Cierra una operación estableciendo profit/loss, estado y tiempo de cierre.
        
        Args:
            operation_id: ID de la operación
            profit_loss: Ganancia o pérdida final
        
        Returns:
            Operation actualizada, o None si no existe
        """
        return self.update_operation(
            operation_id,
            status=OperationStatus.CLOSED,
            profit_loss=profit_loss,
            close_time=datetime.now()
        )
    
    # ==================== MÉTODOS PÚBLICOS - DELETE ====================
    
    def delete_operation(self, operation_id: int) -> bool:
        """
        Elimina una operación de la base de datos.
        
        Nota: Se recomienda usar soft delete (cambiar estado) en producción.
        
        Args:
            operation_id: ID de la operación a eliminar
        
        Returns:
            True si se eliminó, False si no existía
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM operations WHERE id = ?", (operation_id,))
                conn.commit()
                
                deleted = cursor.rowcount > 0
                
                if deleted:
                    self.logger.debug(f"Operación {operation_id} eliminada")
                
                return deleted
        
        except Exception as e:
            self.logger.error(f"Error eliminando operación {operation_id}: {e}")
            return False
    
    # ==================== MÉTODOS PÚBLICOS - ESTADÍSTICAS ====================
    
    def count_operations(
        self,
        status: Optional[OperationStatus] = None,
        symbol: Optional[str] = None,
        bot_id: Optional[int] = None
    ) -> int:
        """
        Cuenta operaciones con filtros opcionales.
        
        Args:
            status: Filtrar por estado (opcional)
            symbol: Filtrar por símbolo (opcional)
            bot_id: Filtrar por bot (opcional)
        
        Returns:
            Número de operaciones que cumplen los criterios
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT COUNT(*) FROM operations WHERE 1=1"
                params = []
                
                if status is not None:
                    query += " AND status = ?"
                    params.append(status.value if isinstance(status, OperationStatus) else status)
                
                if symbol is not None:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                if bot_id is not None:
                    query += " AND bot_id = ?"
                    params.append(bot_id)
                
                cursor.execute(query, params)
                count = cursor.fetchone()[0]
                
                return count
        
        except Exception as e:
            self.logger.error(f"Error contando operaciones: {e}")
            return 0
    
    # ==================== MÉTODOS PRIVADOS ====================
    
    def _initialize_database(self) -> None:
        """
        Inicializa la base de datos y crea las tablas si no existen.
        
        Raises:
            OperationsRepositoryError: Si hay error en la inicialización
        """
        # Crear directorio si no existe
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OperationsRepositoryError(f"No se pudo crear directorio {self.db_path.parent}: {e}") from e
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Crear tabla operations
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        magic_number INTEGER NOT NULL UNIQUE,
                        bot_id INTEGER NOT NULL,
                        ia_id INTEGER NOT NULL,
                        order_type TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        
                        -- Precios y parámetros
                        suggested_price REAL NOT NULL,
                        actual_entry_price REAL,
                        stop_loss REAL NOT NULL,
                        take_profit REAL NOT NULL,
                        stop_loss_initial REAL,
                        take_profit_initial REAL,
                        lot_size REAL NOT NULL,
                        risk_percentage REAL NOT NULL,
                        
                        -- Estado y resultados
                        status TEXT NOT NULL,
                        profit_loss REAL,
                        
                        -- Tiempos
                        open_time TEXT NOT NULL,
                        close_time TEXT,
                        
                        -- Referencia a IA
                        conversation_id TEXT,
                        
                        -- Timestamps
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        
                        CONSTRAINT chk_order_type CHECK (order_type IN ('market', 'limit')),
                        CONSTRAINT chk_direction CHECK (direction IN ('BUY', 'SELL')),
                        CONSTRAINT chk_status CHECK (status IN ('open', 'closed', 'pending'))
                    )
                """)
                
                # Crear índices para consultas eficientes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_magic_symbol 
                    ON operations(magic_number, symbol)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_status 
                    ON operations(status)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_bot_id 
                    ON operations(bot_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_symbol 
                    ON operations(symbol)
                """)
                
                conn.commit()
            
            self.logger.debug("Base de datos inicializada correctamente")
        
        except sqlite3.Error as e:
            error_msg = f"Error inicializando base de datos: {e}"
            self.logger.error(error_msg)
            raise OperationsRepositoryError(error_msg) from e
    
    def _row_to_operation(self, row: sqlite3.Row) -> Operation:
        """
        Convierte una fila de la BD a un objeto Operation.
        
        Args:
            row: Fila de SQLite
        
        Returns:
            Operation construida desde la fila
        """
        return Operation(
            id=row['id'],
            magic_number=row['magic_number'],
            bot_id=row['bot_id'],
            ia_id=row['ia_id'],
            order_type=OrderType(row['order_type']),
            symbol=row['symbol'],
            direction=Direction(row['direction']),
            suggested_price=row['suggested_price'],
            actual_entry_price=row['actual_entry_price'],
            stop_loss=row['stop_loss'],
            take_profit=row['take_profit'],
            stop_loss_initial=row.get('stop_loss_initial'),
            take_profit_initial=row.get('take_profit_initial'),
            lot_size=row['lot_size'],
            risk_percentage=row['risk_percentage'],
            status=OperationStatus(row['status']),
            profit_loss=row['profit_loss'],
            open_time=datetime.fromisoformat(row['open_time']) if row['open_time'] else None,
            close_time=datetime.fromisoformat(row['close_time']) if row['close_time'] else None,
            conversation_id=row['conversation_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def close(self):
        """Cierra cualquier conexión abierta (compatibilidad con context manager)"""
        # SQLite cierra automáticamente las conexiones
        # Este método es para compatibilidad con tests
        pass
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        return f"<OperationsRepository(db='{self.db_path}')>"
    
    def __str__(self) -> str:
        """Representación en string"""
        return f"OperationsRepository - Base de datos de operaciones en {self.db_path}"
