"""
OperationVerifier - Verificador de operaciones abiertas por activo y Magic Number.

Este módulo implementa la lógica de verificación de operaciones abiertas,
permitiendo al orquestador decidir entre evaluación nueva o reevaluación.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T04 - Verificación de operación abierta por activo y Magic Number
"""
from dataclasses import dataclass
from typing import List, Optional
import logging


class OperationVerifierError(Exception):
    """Excepción personalizada para errores del verificador de operaciones."""
    pass


@dataclass
class OperationInfo:
    """
    Información resumida de una operación abierta.
    
    Attributes:
        ticket: Número de ticket de la posición
        symbol: Símbolo del instrumento
        magic: Magic Number de la posición
        type: Tipo de posición (BUY/SELL)
        volume: Volumen en lotes
        profit: Profit/Loss actual
    """
    ticket: int
    symbol: str
    magic: int
    type: str
    volume: float
    profit: float
    
    def to_dict(self) -> dict:
        """
        Convierte OperationInfo a diccionario.
        
        Returns:
            Dict con todos los campos de la operación
        """
        return {
            'ticket': self.ticket,
            'symbol': self.symbol,
            'magic': self.magic,
            'type': self.type,
            'volume': self.volume,
            'profit': self.profit
        }


@dataclass
class VerificationResult:
    """
    Resultado de la verificación de operaciones.
    
    Attributes:
        has_operation: True si hay al menos una operación abierta
        should_reevaluate: True si debe entrar en ruta de reevaluación
        operation_count: Cantidad de operaciones encontradas
        operations: Lista de OperationInfo de las operaciones encontradas
    """
    has_operation: bool
    should_reevaluate: bool
    operation_count: int
    operations: List[OperationInfo]
    
    def to_dict(self) -> dict:
        """
        Convierte VerificationResult a diccionario.
        
        Returns:
            Dict con todos los campos del resultado
        """
        return {
            'has_operation': self.has_operation,
            'should_reevaluate': self.should_reevaluate,
            'operation_count': self.operation_count,
            'operations': [op.to_dict() for op in self.operations]
        }


class OperationVerifier:
    """
    Verificador de operaciones abiertas por activo y Magic Number.
    
    Este módulo es el corazón de la lógica de orquestación, permitiendo
    al bot decidir entre evaluación nueva o reevaluación según la existencia
    de posiciones abiertas.
    
    Criterios de Aceptación (Gherkin):
        Escenario: Verificar operación abierta por activo y Magic Number
            Dado que el bot conoce el símbolo actual y su Magic Number
            Cuando consulta posiciones abiertas en MT5 filtrando por símbolo y Magic Number
            Entonces decide ruta de reevaluación si existe al menos una posición abierta
    
    Example:
        >>> from src.core.mt5_connector import MT5Connector
        >>> from src.core.position_manager import PositionManager
        >>> from src.core.operation_verifier import OperationVerifier
        >>> 
        >>> connector = MT5Connector(broker_config)
        >>> connector.verify_connection()
        >>> 
        >>> position_manager = PositionManager(connector)
        >>> verifier = OperationVerifier(connector, position_manager)
        >>> 
        >>> # Verificar si hay operación de EURUSD con magic 100001
        >>> result = verifier.verify_operation("EURUSD", 100001)
        >>> 
        >>> if result.should_reevaluate:
        >>>     print(f"Reevaluar {result.operation_count} operaciones")
        >>>     for op in result.operations:
        >>>         print(f"  Ticket: {op.ticket}, Profit: {op.profit}")
        >>> else:
        >>>     print("Nueva evaluación para entrada")
    """
    
    def __init__(
        self,
        connector,
        position_manager,
        logger: Optional[object] = None
    ):
        """
        Inicializa el OperationVerifier.
        
        Args:
            connector: Instancia de MT5Connector con conexión activa
            position_manager: Instancia de PositionManager configurada
            logger: Logger personalizado (usa el default si no se proporciona)
            
        Raises:
            OperationVerifierError: Si el connector no está conectado
        """
        if not connector.is_connected():
            raise OperationVerifierError(
                "MT5 no está conectado. Asegúrese de que el connector "
                "esté conectado antes de crear el verifier."
            )
        
        self.connector = connector
        self.position_manager = position_manager
        
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
        
        self.logger.debug("OperationVerifier inicializado correctamente")
    
    def verify_operation(
        self,
        symbol: str,
        magic: int
    ) -> VerificationResult:
        """
        Verifica si existen operaciones abiertas para un símbolo y Magic Number.
        
        Este es el método principal del ticket T04. Consulta las posiciones
        abiertas en MT5 filtrando por símbolo y Magic Number, y retorna
        un resultado que permite al orquestador decidir la ruta a seguir.
        
        Args:
            symbol: Símbolo del instrumento (ej: "EURUSD")
            magic: Magic Number del bot
            
        Returns:
            VerificationResult con:
                - has_operation: True si hay operaciones
                - should_reevaluate: True si debe reevaluar
                - operation_count: Cantidad de operaciones
                - operations: Lista de OperationInfo
        
        Raises:
            ValueError: Si los parámetros son inválidos
            OperationVerifierError: Si hay error al consultar posiciones
        
        Example:
            >>> result = verifier.verify_operation("EURUSD", 100001)
            >>> if result.should_reevaluate:
            >>>     # Entrar en ruta de reevaluación
            >>>     for op in result.operations:
            >>>         reevaluate_position(op)
            >>> else:
            >>>     # Evaluar nueva entrada
            >>>     evaluate_new_entry("EURUSD")
        """
        # Validación de parámetros
        if not symbol or not symbol.strip():
            raise ValueError("El símbolo es requerido y no puede estar vacío")
        
        if magic < 0:
            raise ValueError("Magic number debe ser mayor o igual a 0")
        
        try:
            self.logger.info(
                f"Verificando operaciones de {symbol} con magic {magic}"
            )
            
            # Consultar posiciones usando PositionManager
            positions = self.position_manager.get_positions_by_symbol_and_magic(
                symbol, magic
            )
            
            # Determinar si hay operaciones
            has_operation = len(positions) > 0
            should_reevaluate = has_operation  # Si hay operación, reevaluar
            operation_count = len(positions)
            
            # Convertir posiciones a OperationInfo
            operations = []
            for pos in positions:
                op_info = OperationInfo(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    magic=pos.magic,
                    type=str(pos.type),
                    volume=pos.volume,
                    profit=pos.profit
                )
                operations.append(op_info)
            
            # Crear resultado
            result = VerificationResult(
                has_operation=has_operation,
                should_reevaluate=should_reevaluate,
                operation_count=operation_count,
                operations=operations
            )
            
            # Logging del resultado
            if has_operation:
                self.logger.info(
                    f"Se encontraron {operation_count} operaciones de {symbol} "
                    f"con magic {magic}. Debe reevaluar."
                )
            else:
                self.logger.info(
                    f"No hay operaciones de {symbol} con magic {magic}. "
                    "Nueva evaluación."
                )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Error al verificar operaciones de {symbol} con magic {magic}: {e}"
            )
            raise OperationVerifierError(
                f"Error al verificar operaciones: {e}"
            ) from e
    
    def has_open_operation(
        self,
        symbol: str,
        magic: int
    ) -> bool:
        """
        Método auxiliar para verificación rápida de existencia de operación.
        
        Args:
            symbol: Símbolo del instrumento
            magic: Magic Number del bot
            
        Returns:
            bool: True si hay al menos una operación abierta, False si no
        
        Example:
            >>> if verifier.has_open_operation("EURUSD", 100001):
            >>>     print("Hay operación abierta, reevaluar")
            >>> else:
            >>>     print("No hay operación, evaluar nueva entrada")
        """
        result = self.verify_operation(symbol, magic)
        return result.has_operation
