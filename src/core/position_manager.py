"""
PositionManager - Módulo para consulta y gestión de posiciones en MT5.

Este módulo implementa la consulta y filtrado de posiciones abiertas en
MetaTrader 5, permitiendo filtrar por símbolo, Magic Number, o combinación
de ambos para identificar posiciones relevantes de cada bot.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T08 - Consulta de posiciones por símbolo y Magic Number
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from datetime import datetime
import logging

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # Para entorno de testing


class PositionManagerError(Exception):
    """Excepción personalizada para errores de gestión de posiciones."""
    pass


class PositionType(Enum):
    """
    Enum para representar tipos de posición en MT5.
    
    Los valores corresponden a las constantes POSITION_TYPE de MT5.
    """
    BUY = 0   # POSITION_TYPE_BUY
    SELL = 1  # POSITION_TYPE_SELL
    
    @classmethod
    def from_int(cls, type_int: int) -> 'PositionType':
        """
        Convierte un entero a PositionType enum.
        
        Args:
            type_int: Entero del tipo de posición (0=BUY, 1=SELL)
            
        Returns:
            PositionType: El enum correspondiente
            
        Raises:
            ValueError: Si el entero no corresponde a un tipo válido
        """
        try:
            return cls(type_int)
        except ValueError:
            raise ValueError(
                f"Tipo de posición inválido: {type_int}. "
                "Valores válidos: 0 (BUY), 1 (SELL)"
            )
    
    def __str__(self) -> str:
        """Retorna el nombre del tipo (BUY o SELL)"""
        return self.name


@dataclass
class Position:
    """
    Clase para representar una posición abierta en MT5.
    
    Attributes:
        ticket: Número de ticket único de la posición
        symbol: Símbolo del instrumento (ej: "EURUSD")
        type: Tipo de posición (BUY o SELL)
        volume: Volumen en lotes
        price_open: Precio de apertura
        price_current: Precio actual de mercado
        sl: Stop Loss (0 si no tiene)
        tp: Take Profit (0 si no tiene)
        profit: Profit/Loss actual en divisa de la cuenta
        swap: Swap acumulado
        magic: Magic Number asociado a la posición
        comment: Comentario de la posición
        time_open: Timestamp de apertura
    """
    ticket: int
    symbol: str
    type: PositionType
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    swap: float
    magic: int
    comment: str
    time_open: datetime
    
    def to_dict(self) -> dict:
        """
        Convierte Position a diccionario.
        
        Returns:
            Dict con todos los campos de la posición
        """
        return {
            'ticket': self.ticket,
            'symbol': self.symbol,
            'type': str(self.type),
            'volume': self.volume,
            'price_open': self.price_open,
            'price_current': self.price_current,
            'sl': self.sl,
            'tp': self.tp,
            'profit': self.profit,
            'swap': self.swap,
            'magic': self.magic,
            'comment': self.comment,
            'time_open': self.time_open.isoformat() if isinstance(self.time_open, datetime) else str(self.time_open)
        }


class PositionManager:
    """
    Gestor de posiciones abiertas en MetaTrader 5.
    
    Proporciona métodos para consultar, filtrar y analizar posiciones
    abiertas, permitiendo identificar posiciones relevantes por símbolo,
    Magic Number, o combinación de criterios.
    
    Example:
        >>> from src.core.mt5_connector import MT5Connector
        >>> from src.core.position_manager import PositionManager
        >>> 
        >>> connector = MT5Connector(broker_config)
        >>> connector.verify_connection()
        >>> 
        >>> manager = PositionManager(connector)
        >>> 
        >>> # Consultar posiciones de EURUSD con magic 100001
        >>> positions = manager.get_positions_by_symbol_and_magic("EURUSD", 100001)
        >>> print(f"Posiciones activas: {len(positions)}")
    """
    
    def __init__(
        self,
        connector,
        logger: Optional[object] = None
    ):
        """
        Inicializa el PositionManager.
        
        Args:
            connector: Instancia de MT5Connector con conexión activa
            logger: Logger personalizado (usa el default si no se proporciona)
            
        Raises:
            PositionManagerError: Si el connector no está conectado
        """
        if not connector.is_connected():
            raise PositionManagerError(
                "MT5 no está conectado. Asegúrese de que el connector "
                "esté conectado antes de crear el manager."
            )
        
        self.connector = connector
        self._mt5 = connector._mt5
        
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
        
        self.logger.debug("PositionManager inicializado correctamente")
    
    def get_all_positions(self) -> List[Position]:
        """
        Obtiene todas las posiciones abiertas.
        
        Returns:
            List[Position]: Lista de todas las posiciones abiertas
            
        Raises:
            PositionManagerError: Si hay error al consultar MT5
        """
        try:
            self.logger.info("Consultando todas las posiciones abiertas")
            
            positions = self._mt5.positions_get()
            
            if positions is None or len(positions) == 0:
                self.logger.info("No hay posiciones abiertas")
                return []
            
            result = [self._convert_to_position(p) for p in positions]
            
            self.logger.info(f"Se encontraron {len(result)} posiciones abiertas")
            return result
            
        except Exception as e:
            self.logger.error(f"Error al consultar posiciones: {e}")
            raise PositionManagerError(f"Error al obtener posiciones: {e}") from e
    
    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """
        Obtiene posiciones filtradas por símbolo.
        
        Args:
            symbol: Símbolo del instrumento (ej: "EURUSD")
            
        Returns:
            List[Position]: Lista de posiciones del símbolo especificado
            
        Raises:
            ValueError: Si el símbolo es inválido
            PositionManagerError: Si hay error al consultar MT5
        """
        if not symbol or not symbol.strip():
            raise ValueError("El símbolo es requerido y no puede estar vacío")
        
        try:
            self.logger.info(f"Consultando posiciones de {symbol}")
            
            positions = self._mt5.positions_get(symbol=symbol)
            
            if positions is None or len(positions) == 0:
                self.logger.info(f"No hay posiciones abiertas de {symbol}")
                return []
            
            result = [self._convert_to_position(p) for p in positions]
            
            self.logger.info(f"Se encontraron {len(result)} posiciones de {symbol}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error al consultar posiciones de {symbol}: {e}")
            raise PositionManagerError(f"Error al obtener posiciones: {e}") from e
    
    def get_positions_by_magic(self, magic: int) -> List[Position]:
        """
        Obtiene posiciones filtradas por Magic Number.
        
        Args:
            magic: Magic Number del bot
            
        Returns:
            List[Position]: Lista de posiciones con ese magic number
            
        Raises:
            ValueError: Si el magic number es inválido
            PositionManagerError: Si hay error al consultar MT5
        """
        if magic < 0:
            raise ValueError("Magic number debe ser mayor o igual a 0")
        
        try:
            self.logger.info(f"Consultando posiciones con magic {magic}")
            
            # MT5 no soporta filtrar directamente por magic, 
            # obtenemos todas y filtramos en Python
            all_positions = self._mt5.positions_get()
            
            if all_positions is None or len(all_positions) == 0:
                self.logger.info("No hay posiciones abiertas")
                return []
            
            # Filtrar por magic
            filtered = [p for p in all_positions if p.magic == magic]
            
            result = [self._convert_to_position(p) for p in filtered]
            
            self.logger.info(f"Se encontraron {len(result)} posiciones con magic {magic}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error al consultar posiciones con magic {magic}: {e}")
            raise PositionManagerError(f"Error al obtener posiciones: {e}") from e
    
    def get_positions_by_symbol_and_magic(
        self,
        symbol: str,
        magic: int
    ) -> List[Position]:
        """
        Obtiene posiciones filtradas por símbolo Y Magic Number.
        
        Este es el método principal del ticket T08, permitiendo identificar
        posiciones relevantes para un bot específico en un símbolo específico.
        
        Args:
            symbol: Símbolo del instrumento
            magic: Magic Number del bot
            
        Returns:
            List[Position]: Lista de posiciones que cumplen ambos criterios
            
        Raises:
            ValueError: Si los parámetros son inválidos
            PositionManagerError: Si hay error al consultar MT5
        """
        if not symbol or not symbol.strip():
            raise ValueError("El símbolo es requerido")
        
        if magic < 0:
            raise ValueError("Magic number debe ser mayor o igual a 0")
        
        try:
            self.logger.info(f"Consultando posiciones de {symbol} con magic {magic}")
            
            # Primero filtrar por símbolo (más eficiente en MT5)
            positions = self._mt5.positions_get(symbol=symbol)
            
            if positions is None or len(positions) == 0:
                self.logger.info(f"No hay posiciones de {symbol}")
                return []
            
            # Luego filtrar por magic en Python
            filtered = [p for p in positions if p.magic == magic]
            
            result = [self._convert_to_position(p) for p in filtered]
            
            self.logger.info(
                f"Se encontraron {len(result)} posiciones de {symbol} con magic {magic}"
            )
            return result
            
        except Exception as e:
            self.logger.error(
                f"Error al consultar posiciones de {symbol} con magic {magic}: {e}"
            )
            raise PositionManagerError(f"Error al obtener posiciones: {e}") from e
    
    def get_position_by_ticket(self, ticket: int) -> Optional[Position]:
        """
        Obtiene una posición específica por su ticket.
        
        Args:
            ticket: Número de ticket de la posición
            
        Returns:
            Position si existe, None si no se encuentra
            
        Raises:
            ValueError: Si el ticket es inválido
            PositionManagerError: Si hay error al consultar MT5
        """
        if ticket <= 0:
            raise ValueError("Ticket debe ser mayor a 0")
        
        try:
            self.logger.debug(f"Consultando posición con ticket {ticket}")
            
            positions = self._mt5.positions_get(ticket=ticket)
            
            if positions is None or len(positions) == 0:
                self.logger.debug(f"No se encontró posición con ticket {ticket}")
                return None
            
            result = self._convert_to_position(positions[0])
            
            self.logger.debug(f"Posición {ticket} encontrada: {result.symbol}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error al consultar posición {ticket}: {e}")
            raise PositionManagerError(f"Error al obtener posición: {e}") from e
    
    def get_positions_by_type(self, position_type: PositionType) -> List[Position]:
        """
        Obtiene posiciones filtradas por tipo (BUY o SELL).
        
        Args:
            position_type: Tipo de posición a filtrar
            
        Returns:
            List[Position]: Lista de posiciones del tipo especificado
            
        Raises:
            PositionManagerError: Si hay error al consultar MT5
        """
        try:
            self.logger.info(f"Consultando posiciones de tipo {position_type}")
            
            all_positions = self._mt5.positions_get()
            
            if all_positions is None or len(all_positions) == 0:
                return []
            
            # Filtrar por tipo
            filtered = [p for p in all_positions if p.type == position_type.value]
            
            result = [self._convert_to_position(p) for p in filtered]
            
            self.logger.info(f"Se encontraron {len(result)} posiciones {position_type}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error al consultar posiciones por tipo: {e}")
            raise PositionManagerError(f"Error al obtener posiciones: {e}") from e
    
    def get_total_positions(self) -> int:
        """
        Obtiene el número total de posiciones abiertas.
        
        Returns:
            int: Cantidad de posiciones abiertas
        """
        positions = self.get_all_positions()
        return len(positions)
    
    def get_total_profit(self) -> float:
        """
        Calcula el profit/loss total de todas las posiciones abiertas.
        
        Returns:
            float: Suma de profits de todas las posiciones
        """
        positions = self.get_all_positions()
        return sum(p.profit for p in positions)
    
    def has_positions(
        self,
        symbol: Optional[str] = None,
        magic: Optional[int] = None
    ) -> bool:
        """
        Verifica si existen posiciones abiertas con los filtros opcionales.
        
        Args:
            symbol: Símbolo opcional para filtrar
            magic: Magic number opcional para filtrar
            
        Returns:
            bool: True si existen posiciones, False en caso contrario
        """
        if symbol and magic is not None:
            positions = self.get_positions_by_symbol_and_magic(symbol, magic)
        elif symbol:
            positions = self.get_positions_by_symbol(symbol)
        elif magic is not None:
            positions = self.get_positions_by_magic(magic)
        else:
            positions = self.get_all_positions()
        
        return len(positions) > 0
    
    def _convert_to_position(self, mt5_position) -> Position:
        """
        Convierte una posición de MT5 a objeto Position.
        
        Args:
            mt5_position: Posición en formato MT5
            
        Returns:
            Position: Objeto Position con datos mapeados
        """
        return Position(
            ticket=mt5_position.ticket,
            symbol=mt5_position.symbol,
            type=PositionType.from_int(mt5_position.type),
            volume=mt5_position.volume,
            price_open=mt5_position.price_open,
            price_current=mt5_position.price_current,
            sl=mt5_position.sl,
            tp=mt5_position.tp,
            profit=mt5_position.profit,
            swap=mt5_position.swap,
            magic=mt5_position.magic,
            comment=mt5_position.comment,
            time_open=datetime.fromtimestamp(mt5_position.time)
        )
