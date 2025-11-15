"""
IAQueryRepository - Persistencia de consultas IA en SQLite - T33

Este módulo implementa la funcionalidad del Ticket T33: Registro de consultas
a IA con prompts, respuesta, tokens y costo para evaluar eficiencia y calidad
de decisión.

Características:
- Creación y almacenamiento de consultas IA
- Consulta por ID, operación, bot, símbolo y tipo
- Estadísticas de uso y costos
- Índices optimizados para consultas eficientes
- Validación de tipos y constraints
- Manejo robusto de errores

Autor: Sistema Botrading
Fecha: 2025-11-15
Ticket: T33 - Registro de consultas a IA con prompts, respuesta, tokens y costo
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
import logging


# ==================== ENUMS ====================

class QueryType(str, Enum):
    """Tipos de consulta a IA soportados"""
    EVALUATION = "evaluacion"
    REEVALUATION = "reevaluacion"


# ==================== EXCEPCIONES ====================

class IAQueryRepositoryError(Exception):
    """Excepción base para errores del repositorio de consultas IA"""
    pass


# ==================== MODELOS ====================

@dataclass
class IAQuery:
    """
    Modelo de datos para una consulta a IA.
    
    Representa una consulta completa con prompt, respuesta, tokens y costo.
    """
    # Identificación
    id: Optional[int] = None
    operation_id: Optional[int] = None
    bot_id: int = 0
    ia_id: int = 0
    symbol: str = ""
    
    # Tipo de consulta
    query_type: QueryType = QueryType.EVALUATION
    
    # Prompt y respuesta
    prompt: str = ""
    response: str = ""
    
    # Tokens y costos
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    cost_usd: float = 0.0
    
    # Decisión tomada
    action_decided: str = ""
    
    # Timestamp
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la consulta a diccionario"""
        return {
            'id': self.id,
            'operation_id': self.operation_id,
            'bot_id': self.bot_id,
            'ia_id': self.ia_id,
            'symbol': self.symbol,
            'query_type': self.query_type.value if isinstance(self.query_type, QueryType) else self.query_type,
            'prompt': self.prompt,
            'response': self.response,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'tokens_total': self.tokens_total,
            'cost_usd': self.cost_usd,
            'action_decided': self.action_decided,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ==================== REPOSITORIO ====================

class IAQueryRepository:
    """
    Repositorio para persistencia de consultas IA en SQLite.
    
    Gestiona el ciclo de vida completo de las consultas a IA:
    - Creación de nuevas consultas
    - Consulta por diversos criterios
    - Actualización de referencias a operaciones
    - Estadísticas y métricas de uso/costo
    
    Ejemplo:
        >>> repo = IAQueryRepository(db_path=Path("data/ia_queries.db"))
        >>> query = repo.create_query(
        ...     bot_id=1,
        ...     ia_id=1,
        ...     symbol="EURUSD",
        ...     query_type=QueryType.EVALUATION,
        ...     prompt="Analiza EURUSD...",
        ...     response='{"decision": "OPERAR"}',
        ...     tokens_input=150,
        ...     tokens_output=80,
        ...     cost_usd=0.0023,
        ...     action_decided="OPERAR"
        ... )
        >>> print(f"Consulta creada con ID: {query.id}")
    """
    
    def __init__(self, db_path: Path):
        """
        Inicializa el repositorio de consultas IA.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._initialize_database()
    
    def _initialize_database(self):
        """Crea la base de datos y tablas si no existen"""
        # Crear directorio si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Crear tabla consultas_ia
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consultas_ia (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operacion_id INTEGER,
                    bot_id INTEGER NOT NULL,
                    ia_id INTEGER NOT NULL,
                    activo TEXT NOT NULL,
                    
                    tipo_consulta TEXT NOT NULL,
                    
                    prompt TEXT NOT NULL,
                    respuesta TEXT NOT NULL,
                    
                    tokens_input INTEGER NOT NULL,
                    tokens_output INTEGER NOT NULL,
                    tokens_total INTEGER NOT NULL,
                    costo_usd REAL NOT NULL,
                    
                    accion_decidida TEXT NOT NULL,
                    
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear índices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_operacion 
                ON consultas_ia(operacion_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bot_ia 
                ON consultas_ia(bot_id, ia_id)
            """)
            
            conn.commit()
    
    def create_query(
        self,
        bot_id: int,
        ia_id: int,
        symbol: str,
        query_type: QueryType,
        prompt: str,
        response: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        action_decided: str,
        operation_id: Optional[int] = None
    ) -> IAQuery:
        """
        Crea y persiste una nueva consulta IA.
        
        Args:
            bot_id: ID del bot que realizó la consulta
            ia_id: ID de la configuración de IA utilizada
            symbol: Símbolo del activo (ej: "EURUSD")
            query_type: Tipo de consulta (EVALUATION o REEVALUATION)
            prompt: Texto del prompt enviado a la IA
            response: Respuesta JSON de la IA
            tokens_input: Número de tokens de entrada
            tokens_output: Número de tokens de salida
            cost_usd: Costo de la consulta en USD
            action_decided: Acción decidida (ej: "OPERAR", "NO_OPERAR")
            operation_id: ID de operación asociada (opcional)
        
        Returns:
            IAQuery: Consulta creada con ID asignado
        
        Raises:
            ValueError: Si los datos no son válidos
            TypeError: Si los tipos no son correctos
            IAQueryRepositoryError: Si hay error en la BD
        """
        # Validación de tipos
        if not isinstance(bot_id, int):
            raise TypeError("bot_id debe ser int")
        if not isinstance(ia_id, int):
            raise TypeError("ia_id debe ser int")
        if not isinstance(symbol, str):
            raise TypeError("symbol debe ser str")
        if not isinstance(query_type, QueryType):
            raise TypeError("query_type debe ser QueryType enum")
        if not isinstance(prompt, str):
            raise TypeError("prompt debe ser str")
        if not isinstance(response, str):
            raise TypeError("response debe ser str")
        if not isinstance(tokens_input, int):
            raise TypeError("tokens_input debe ser int")
        if not isinstance(tokens_output, int):
            raise TypeError("tokens_output debe ser int")
        if not isinstance(cost_usd, (int, float)):
            raise TypeError("cost_usd debe ser int o float")
        if not isinstance(action_decided, str):
            raise TypeError("action_decided debe ser str")
        
        # Validación de valores
        if bot_id <= 0:
            raise ValueError("bot_id debe ser > 0")
        if ia_id <= 0:
            raise ValueError("ia_id debe ser > 0")
        if not symbol.strip():
            raise ValueError("symbol no puede estar vacío")
        if not prompt.strip():
            raise ValueError("prompt no puede estar vacío")
        if not response.strip():
            raise ValueError("response no puede estar vacío")
        if tokens_input < 0:
            raise ValueError("tokens_input debe ser >= 0")
        if tokens_output < 0:
            raise ValueError("tokens_output debe ser >= 0")
        if cost_usd < 0:
            raise ValueError("cost_usd debe ser >= 0")
        if not action_decided.strip():
            raise ValueError("action_decided no puede estar vacío")
        
        # Calcular tokens totales
        tokens_total = tokens_input + tokens_output
        
        # Timestamp actual
        created_at = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO consultas_ia (
                        operacion_id, bot_id, ia_id, activo,
                        tipo_consulta, prompt, respuesta,
                        tokens_input, tokens_output, tokens_total,
                        costo_usd, accion_decidida, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation_id,
                    bot_id,
                    ia_id,
                    symbol,
                    query_type.value,
                    prompt,
                    response,
                    tokens_input,
                    tokens_output,
                    tokens_total,
                    float(cost_usd),
                    action_decided,
                    created_at.isoformat()
                ))
                
                query_id = cursor.lastrowid
                conn.commit()
            
            # Retornar objeto IAQuery
            return IAQuery(
                id=query_id,
                operation_id=operation_id,
                bot_id=bot_id,
                ia_id=ia_id,
                symbol=symbol,
                query_type=query_type,
                prompt=prompt,
                response=response,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_total=tokens_total,
                cost_usd=cost_usd,
                action_decided=action_decided,
                created_at=created_at
            )
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al crear consulta: {e}")
    
    def get_query_by_id(self, query_id: int) -> Optional[IAQuery]:
        """
        Obtiene una consulta por su ID.
        
        Args:
            query_id: ID de la consulta
        
        Returns:
            IAQuery si se encuentra, None si no existe
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM consultas_ia WHERE id = ?
                """, (query_id,))
                
                row = cursor.fetchone()
                
                if row is None:
                    return None
                
                return self._row_to_query(row)
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al obtener consulta: {e}")
    
    def get_queries_by_operation_id(self, operation_id: int) -> List[IAQuery]:
        """
        Obtiene todas las consultas asociadas a una operación.
        
        Args:
            operation_id: ID de la operación
        
        Returns:
            Lista de consultas, ordenadas por timestamp descendente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM consultas_ia 
                    WHERE operacion_id = ?
                    ORDER BY created_at DESC
                """, (operation_id,))
                
                rows = cursor.fetchall()
                return [self._row_to_query(row) for row in rows]
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al obtener consultas: {e}")
    
    def get_queries_by_bot(self, bot_id: int) -> List[IAQuery]:
        """
        Obtiene todas las consultas de un bot.
        
        Args:
            bot_id: ID del bot
        
        Returns:
            Lista de consultas, ordenadas por timestamp descendente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM consultas_ia 
                    WHERE bot_id = ?
                    ORDER BY created_at DESC
                """, (bot_id,))
                
                rows = cursor.fetchall()
                return [self._row_to_query(row) for row in rows]
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al obtener consultas: {e}")
    
    def get_queries_by_symbol(self, symbol: str) -> List[IAQuery]:
        """
        Obtiene todas las consultas para un símbolo.
        
        Args:
            symbol: Símbolo del activo (ej: "EURUSD")
        
        Returns:
            Lista de consultas, ordenadas por timestamp descendente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM consultas_ia 
                    WHERE activo = ?
                    ORDER BY created_at DESC
                """, (symbol,))
                
                rows = cursor.fetchall()
                return [self._row_to_query(row) for row in rows]
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al obtener consultas: {e}")
    
    def get_queries_by_type(self, query_type: QueryType) -> List[IAQuery]:
        """
        Obtiene todas las consultas de un tipo específico.
        
        Args:
            query_type: Tipo de consulta (EVALUATION o REEVALUATION)
        
        Returns:
            Lista de consultas, ordenadas por timestamp descendente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM consultas_ia 
                    WHERE tipo_consulta = ?
                    ORDER BY created_at DESC
                """, (query_type.value,))
                
                rows = cursor.fetchall()
                return [self._row_to_query(row) for row in rows]
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al obtener consultas: {e}")
    
    def get_all_queries(self) -> List[IAQuery]:
        """
        Obtiene todas las consultas.
        
        Returns:
            Lista de todas las consultas, ordenadas por timestamp descendente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM consultas_ia 
                    ORDER BY created_at DESC
                """)
                
                rows = cursor.fetchall()
                return [self._row_to_query(row) for row in rows]
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al obtener consultas: {e}")
    
    def update_operation_id(self, query_id: int, operation_id: int) -> IAQuery:
        """
        Actualiza el operation_id de una consulta.
        
        Útil cuando la consulta se crea antes de la operación y luego
        se vincula una vez que se abre la posición.
        
        Args:
            query_id: ID de la consulta
            operation_id: ID de la operación a vincular
        
        Returns:
            IAQuery actualizada
        
        Raises:
            IAQueryRepositoryError: Si la consulta no existe
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE consultas_ia 
                    SET operacion_id = ?
                    WHERE id = ?
                """, (operation_id, query_id))
                
                if cursor.rowcount == 0:
                    raise IAQueryRepositoryError(f"Consulta {query_id} no encontrada")
                
                conn.commit()
            
            # Retornar consulta actualizada
            query = self.get_query_by_id(query_id)
            if query is None:
                raise IAQueryRepositoryError(f"Error al recuperar consulta {query_id}")
            
            return query
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al actualizar consulta: {e}")
    
    def get_total_cost(self) -> float:
        """
        Calcula el costo total de todas las consultas.
        
        Returns:
            Costo total en USD
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COALESCE(SUM(costo_usd), 0.0) as total
                    FROM consultas_ia
                """)
                
                result = cursor.fetchone()
                return float(result[0]) if result else 0.0
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al calcular costo total: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Calcula estadísticas generales de uso.
        
        Returns:
            Diccionario con estadísticas:
            - total_queries: Número total de consultas
            - total_cost: Costo total en USD
            - total_tokens_input: Total tokens de entrada
            - total_tokens_output: Total tokens de salida
            - total_tokens_total: Total de todos los tokens
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_queries,
                        COALESCE(SUM(costo_usd), 0.0) as total_cost,
                        COALESCE(SUM(tokens_input), 0) as total_input,
                        COALESCE(SUM(tokens_output), 0) as total_output,
                        COALESCE(SUM(tokens_total), 0) as total_tokens
                    FROM consultas_ia
                """)
                
                row = cursor.fetchone()
                
                return {
                    'total_queries': row[0],
                    'total_cost': round(float(row[1]), 6),
                    'total_tokens_input': row[2],
                    'total_tokens_output': row[3],
                    'total_tokens_total': row[4]
                }
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al calcular estadísticas: {e}")
    
    def get_statistics_by_bot(self, bot_id: int) -> Dict[str, Any]:
        """
        Calcula estadísticas de uso para un bot específico.
        
        Args:
            bot_id: ID del bot
        
        Returns:
            Diccionario con estadísticas del bot
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_queries,
                        COALESCE(SUM(costo_usd), 0.0) as total_cost,
                        COALESCE(SUM(tokens_input), 0) as total_input,
                        COALESCE(SUM(tokens_output), 0) as total_output,
                        COALESCE(SUM(tokens_total), 0) as total_tokens
                    FROM consultas_ia
                    WHERE bot_id = ?
                """, (bot_id,))
                
                row = cursor.fetchone()
                
                return {
                    'total_queries': row[0],
                    'total_cost': round(float(row[1]), 6),
                    'total_tokens_input': row[2],
                    'total_tokens_output': row[3],
                    'total_tokens_total': row[4]
                }
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al calcular estadísticas: {e}")
    
    def get_cost_by_type(self, query_type: QueryType) -> float:
        """
        Calcula el costo total por tipo de consulta.
        
        Args:
            query_type: Tipo de consulta (EVALUATION o REEVALUATION)
        
        Returns:
            Costo total en USD para ese tipo
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COALESCE(SUM(costo_usd), 0.0) as total
                    FROM consultas_ia
                    WHERE tipo_consulta = ?
                """, (query_type.value,))
                
                result = cursor.fetchone()
                return float(result[0]) if result else 0.0
        
        except sqlite3.Error as e:
            raise IAQueryRepositoryError(f"Error al calcular costo por tipo: {e}")
    
    def _row_to_query(self, row: sqlite3.Row) -> IAQuery:
        """
        Convierte una fila de SQLite a objeto IAQuery.
        
        Args:
            row: Fila de resultado SQLite
        
        Returns:
            Objeto IAQuery
        """
        return IAQuery(
            id=row['id'],
            operation_id=row['operacion_id'],
            bot_id=row['bot_id'],
            ia_id=row['ia_id'],
            symbol=row['activo'],
            query_type=QueryType(row['tipo_consulta']),
            prompt=row['prompt'],
            response=row['respuesta'],
            tokens_input=row['tokens_input'],
            tokens_output=row['tokens_output'],
            tokens_total=row['tokens_total'],
            cost_usd=row['costo_usd'],
            action_decided=row['accion_decidida'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
