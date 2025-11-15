"""
ReevaluationTracker - T28
Registro de trazabilidad de cada reevaluación

Este módulo implementa el sistema de trazabilidad completa para reevaluaciones
de posiciones, registrando decisiones de IA, tokens consumidos, costos y contexto
de mercado en cada evaluación.

Características:
- Registro persistente de cada reevaluación
- Tracking de decisiones (MANTENER/ACTUALIZAR/CERRAR)
- Registro de tokens input/output y costos
- Historial completo por posición o símbolo
- Estadísticas agregadas de reevaluaciones
- Persistencia en JSON para trazabilidad

Tickets relacionados: T28 (trazabilidad), T11 (tokens/costo), T26 (reevaluación)

Author: Botrading Team
Date: 2025-11-13
"""

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import logging


class ReevaluationAction(Enum):
    """
    Acciones posibles en una reevaluación
    
    Values:
        MANTENER: Mantener la posición sin cambios
        ACTUALIZAR: Modificar SL/TP
        CERRAR: Cerrar la posición
    """
    MANTENER = "MANTENER"
    ACTUALIZAR = "ACTUALIZAR"
    CERRAR = "CERRAR"
    
    @classmethod
    def from_string(cls, value: str) -> 'ReevaluationAction':
        """
        Convierte string a ReevaluationAction
        
        Args:
            value: Acción como string
            
        Returns:
            ReevaluationAction enum correspondiente
            
        Raises:
            ValueError: Si la acción no es válida
        """
        value_upper = value.upper()
        for action in cls:
            if action.value == value_upper:
                return action
        raise ValueError(
            f"Acción inválida: {value}. Válidas: {[a.value for a in cls]}"
        )


@dataclass
class ReevaluationRecord:
    """
    Registro de una reevaluación individual
    
    Atributos:
        position_id: ID de la posición reevaluada
        symbol: Símbolo del activo (EURUSD, GBPUSD, etc.)
        action: Acción tomada (MANTENER/ACTUALIZAR/CERRAR)
        current_price: Precio actual del mercado
        profit_pips: Profit/Loss actual en pips
        reasoning: Razonamiento de la IA
        new_sl: Nuevo Stop Loss (si se actualizó)
        new_tp: Nuevo Take Profit (si se actualizó)
        conversation_id: ID de conversación de IA
        reevaluation_mode: Modo de reevaluación (persistent/new)
        tokens_input: Tokens de entrada consumidos
        tokens_output: Tokens de salida generados
        cost: Costo de la consulta en USD
        reevaluation_count: Número de reevaluación (1, 2, 3...)
        time_since_last: Segundos desde última reevaluación
        timestamp: Momento de la reevaluación
    """
    position_id: str
    symbol: str
    action: ReevaluationAction
    current_price: float
    profit_pips: float
    reasoning: str
    new_sl: Optional[float] = None
    new_tp: Optional[float] = None
    conversation_id: Optional[str] = None
    reevaluation_mode: str = "new"
    tokens_input: int = 0
    tokens_output: int = 0
    cost: float = 0.0
    reevaluation_count: int = 0
    time_since_last: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """
        Convierte el record a diccionario
        
        Returns:
            Diccionario con todos los campos serializable
        """
        data = asdict(self)
        # Convertir enum a string
        data['action'] = self.action.value
        # Convertir datetime a ISO string
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReevaluationRecord':
        """
        Crea un record desde un diccionario
        
        Args:
            data: Diccionario con datos del record
            
        Returns:
            ReevaluationRecord creado
        """
        # Convertir string a enum
        if isinstance(data.get('action'), str):
            data['action'] = ReevaluationAction.from_string(data['action'])
        
        # Convertir ISO string a datetime
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)


@dataclass
class TrackerStatistics:
    """
    Estadísticas agregadas de reevaluaciones
    
    Atributos:
        total_reevaluations: Total de reevaluaciones registradas
        total_tokens_input: Total de tokens de entrada
        total_tokens_output: Total de tokens de salida
        total_cost: Costo total acumulado
        unique_positions: Número de posiciones únicas
        unique_symbols: Número de símbolos únicos
        actions_count: Conteo por tipo de acción
        avg_cost_per_reevaluation: Costo promedio por reevaluación
    """
    total_reevaluations: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost: float = 0.0
    unique_positions: int = 0
    unique_symbols: int = 0
    actions_count: Dict[str, int] = field(default_factory=dict)
    avg_cost_per_reevaluation: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convierte estadísticas a diccionario"""
        return asdict(self)


class ReevaluationTracker:
    """
    Sistema de registro y trazabilidad de reevaluaciones
    
    Este tracker mantiene un historial completo de todas las reevaluaciones
    realizadas, permitiendo auditoría, análisis de costos y optimización.
    
    Uso básico:
        >>> tracker = ReevaluationTracker(storage_dir="data/reevaluations")
        >>> 
        >>> # Registrar una reevaluación
        >>> tracker.register(
        >>>     position_id="pos_001",
        >>>     symbol="EURUSD",
        >>>     action=ReevaluationAction.ACTUALIZAR,
        >>>     current_price=1.2500,
        >>>     profit_pips=50.0,
        >>>     reasoning="Mover SL a breakeven",
        >>>     new_sl=1.2400,
        >>>     tokens_input=500,
        >>>     tokens_output=150,
        >>>     cost=0.0045
        >>> )
        >>> 
        >>> # Consultar historial
        >>> history = tracker.get_history_by_position("pos_001")
        >>> stats = tracker.get_statistics()
    """
    
    def __init__(self, storage_dir: str = "data/reevaluations"):
        """
        Inicializa el tracker
        
        Args:
            storage_dir: Directorio donde se almacenarán los registros
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.storage_file = self.storage_dir / "reevaluations.json"
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"ReevaluationTracker inicializado en {self.storage_dir}")
        
        # Inicializar archivo si no existe
        if not self.storage_file.exists():
            self._save_records([])
    
    def register(
        self,
        position_id: str,
        symbol: str,
        action: ReevaluationAction,
        current_price: float,
        profit_pips: float,
        reasoning: str,
        new_sl: Optional[float] = None,
        new_tp: Optional[float] = None,
        conversation_id: Optional[str] = None,
        reevaluation_mode: str = "new",
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost: float = 0.0,
        reevaluation_count: int = 0,
        time_since_last: int = 0
    ) -> None:
        """
        Registra una nueva reevaluación
        
        Args:
            position_id: ID de la posición
            symbol: Símbolo del activo
            action: Acción tomada
            current_price: Precio actual
            profit_pips: Profit/Loss en pips
            reasoning: Razonamiento de la IA
            new_sl: Nuevo Stop Loss (opcional)
            new_tp: Nuevo Take Profit (opcional)
            conversation_id: ID de conversación (opcional)
            reevaluation_mode: Modo de reevaluación
            tokens_input: Tokens de entrada
            tokens_output: Tokens de salida
            cost: Costo de la consulta
            reevaluation_count: Número de reevaluación
            time_since_last: Segundos desde última reevaluación
            
        Raises:
            ValueError: Si los valores son inválidos
        """
        # Validaciones
        if tokens_input < 0:
            raise ValueError("tokens_input debe ser >= 0")
        if tokens_output < 0:
            raise ValueError("tokens_output debe ser >= 0")
        if cost < 0:
            raise ValueError("cost debe ser >= 0")
        
        # Crear record
        record = ReevaluationRecord(
            position_id=position_id,
            symbol=symbol,
            action=action,
            current_price=current_price,
            profit_pips=profit_pips,
            reasoning=reasoning,
            new_sl=new_sl,
            new_tp=new_tp,
            conversation_id=conversation_id,
            reevaluation_mode=reevaluation_mode,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost=cost,
            reevaluation_count=reevaluation_count,
            time_since_last=time_since_last,
            timestamp=datetime.now()
        )
        
        # Cargar registros existentes
        records = self._load_records()
        
        # Agregar nuevo registro
        records.append(record)
        
        # Guardar
        self._save_records(records)
        
        self.logger.debug(
            f"Reevaluación registrada: {position_id} ({symbol}) - "
            f"{action.value} - Tokens: {tokens_input}/{tokens_output} - "
            f"Costo: ${cost:.4f}"
        )
    
    def get_all_records(self) -> List[ReevaluationRecord]:
        """
        Obtiene todos los registros de reevaluación
        
        Returns:
            Lista de todos los registros, ordenados por timestamp descendente
        """
        return self._load_records()
    
    def get_history_by_position(self, position_id: str) -> List[ReevaluationRecord]:
        """
        Obtiene el historial de reevaluaciones de una posición
        
        Args:
            position_id: ID de la posición
            
        Returns:
            Lista de reevaluaciones de esa posición
        """
        all_records = self._load_records()
        return [r for r in all_records if r.position_id == position_id]
    
    def get_history_by_symbol(self, symbol: str) -> List[ReevaluationRecord]:
        """
        Obtiene el historial de reevaluaciones de un símbolo
        
        Args:
            symbol: Símbolo del activo
            
        Returns:
            Lista de reevaluaciones de ese símbolo
        """
        all_records = self._load_records()
        return [r for r in all_records if r.symbol == symbol]
    
    def get_statistics(
        self,
        action_filter: Optional[ReevaluationAction] = None
    ) -> TrackerStatistics:
        """
        Calcula estadísticas de reevaluaciones
        
        Args:
            action_filter: Filtrar por acción específica (opcional)
            
        Returns:
            Estadísticas agregadas
        """
        all_records = self._load_records()
        
        # Filtrar si es necesario
        if action_filter is not None:
            records = [r for r in all_records if r.action == action_filter]
        else:
            records = all_records
        
        if not records:
            return TrackerStatistics()
        
        # Calcular estadísticas
        total_tokens_input = sum(r.tokens_input for r in records)
        total_tokens_output = sum(r.tokens_output for r in records)
        total_cost = sum(r.cost for r in records)
        
        unique_positions = len(set(r.position_id for r in records))
        unique_symbols = len(set(r.symbol for r in records))
        
        # Conteo por acción
        actions_count = {}
        for action in ReevaluationAction:
            count = sum(1 for r in records if r.action == action)
            actions_count[action.value] = count
        
        avg_cost = total_cost / len(records) if records else 0.0
        
        return TrackerStatistics(
            total_reevaluations=len(records),
            total_tokens_input=total_tokens_input,
            total_tokens_output=total_tokens_output,
            total_cost=round(total_cost, 6),
            unique_positions=unique_positions,
            unique_symbols=unique_symbols,
            actions_count=actions_count,
            avg_cost_per_reevaluation=round(avg_cost, 6)
        )
    
    def clear_history_by_position(self, position_id: str) -> int:
        """
        Limpia el historial de una posición específica
        
        Args:
            position_id: ID de la posición
            
        Returns:
            Número de registros eliminados
        """
        all_records = self._load_records()
        
        # Filtrar (mantener los que NO son de esta posición)
        filtered_records = [r for r in all_records if r.position_id != position_id]
        
        deleted_count = len(all_records) - len(filtered_records)
        
        # Guardar
        self._save_records(filtered_records)
        
        self.logger.info(
            f"Historial de {position_id} limpiado. "
            f"{deleted_count} registros eliminados."
        )
        
        return deleted_count
    
    def clear_all(self) -> int:
        """
        Limpia todos los registros
        
        Returns:
            Número de registros eliminados
        """
        all_records = self._load_records()
        count = len(all_records)
        
        self._save_records([])
        
        self.logger.warning(f"Todos los registros limpiados. {count} eliminados.")
        
        return count
    
    def _load_records(self) -> List[ReevaluationRecord]:
        """
        Carga registros desde el archivo JSON
        
        Returns:
            Lista de registros
        """
        if not self.storage_file.exists():
            return []
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                self.logger.warning("Archivo JSON no contiene lista. Retornando vacío.")
                return []
            
            # Convertir diccionarios a ReevaluationRecord
            records = []
            for item in data:
                try:
                    record = ReevaluationRecord.from_dict(item)
                    records.append(record)
                except Exception as e:
                    self.logger.error(f"Error parseando record: {e}")
                    continue
            
            # Ordenar por timestamp descendente (más reciente primero)
            records.sort(key=lambda r: r.timestamp, reverse=True)
            
            return records
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decodificando JSON: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error cargando registros: {e}")
            return []
    
    def _save_records(self, records: List[ReevaluationRecord]) -> None:
        """
        Guarda registros en el archivo JSON
        
        Args:
            records: Lista de registros a guardar
        """
        try:
            # Convertir a diccionarios
            data = [r.to_dict() for r in records]
            
            # Guardar
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando registros: {e}", exc_info=True)
            raise
