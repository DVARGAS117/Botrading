"""
Módulo de generación de Magic Numbers únicos.

Este módulo implementa el Ticket T17: Generación de Magic Number único con estructura,
permitiendo identificar inequívocamente cada operación mediante un código de 6 dígitos
que codifica: [Bot][IA][Tipo][Secuencia]

Estructura del Magic Number (6 dígitos):
- Dígito 1: Bot ID (1-5)
- Dígito 2: IA Config ID (0-9)
- Dígito 3: Order Type (0=Market, 1=Limit)
- Dígitos 4-6: Sequence Number (000-999)

Ejemplo: 231456
- Bot ID: 2
- IA Config: 3
- Order Type: 1 (Limit)
- Sequence: 456

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T17 - Generación de Magic Number único con estructura
"""

import logging
from dataclasses import dataclass
from typing import Optional


# ==================== EXCEPCIONES PERSONALIZADAS ====================

class MagicNumberError(Exception):
    """Excepción base para errores de Magic Number"""
    pass


class InvalidBotIdError(MagicNumberError):
    """Excepción para bot_id inválido"""
    pass


class InvalidIAConfigIdError(MagicNumberError):
    """Excepción para ia_config_id inválido"""
    pass


class InvalidOrderTypeError(MagicNumberError):
    """Excepción para order_type inválido"""
    pass


# ==================== DATACLASSES ====================

@dataclass
class MagicNumberComponents:
    """
    Componentes decodificados de un Magic Number.
    
    Attributes:
        bot_id: ID del bot (1-5)
        ia_config_id: ID de configuración IA (0-9)
        order_type: Tipo de orden ('market' o 'limit')
        sequence: Número de secuencia (0-999)
        magic_number: Magic Number completo (6 dígitos)
    """
    bot_id: int
    ia_config_id: int
    order_type: str
    sequence: int
    magic_number: int
    
    def to_dict(self) -> dict:
        """
        Convierte los componentes a diccionario.
        
        Returns:
            Diccionario con todos los componentes
        """
        return {
            "bot_id": self.bot_id,
            "ia_config_id": self.ia_config_id,
            "order_type": self.order_type,
            "sequence": self.sequence,
            "magic_number": self.magic_number
        }
    
    def __str__(self) -> str:
        """Representación en string"""
        return (
            f"MagicNumber: {self.magic_number}\n"
            f"  Bot: {self.bot_id}\n"
            f"  IA Config: {self.ia_config_id}\n"
            f"  Order Type: {self.order_type}\n"
            f"  Sequence: {self.sequence}"
        )


# ==================== CLASE PRINCIPAL ====================

class MagicNumberGenerator:
    """
    Generador de Magic Numbers únicos con estructura [Bot][IA][Tipo][Seq].
    
    Este generador crea números de 6 dígitos que identifican inequívocamente
    cada operación de trading, codificando información sobre el bot que la
    realizó, la configuración de IA usada y el tipo de orden.
    
    Características:
    - Generación determinista (mismos parámetros = mismo magic number)
    - Validación estricta de parámetros
    - Decodificación inversa (magic number -> componentes)
    - Soporte para secuencias (múltiples operaciones con mismos parámetros)
    
    Example:
        >>> generator = MagicNumberGenerator()
        >>> 
        >>> # Generar Magic Number para Bot 1, IA Config 0, Market order
        >>> magic = generator.generate(bot_id=1, ia_config_id=0, order_type="market")
        >>> print(magic)  # 100000
        >>> 
        >>> # Decodificar Magic Number
        >>> components = generator.decode(magic)
        >>> print(components.bot_id)  # 1
        >>> print(components.order_type)  # 'market'
    """
    
    # Constantes
    ORDER_TYPE_MARKET = 0
    ORDER_TYPE_LIMIT = 1
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Inicializa el generador de Magic Numbers.
        
        Args:
            logger: Logger opcional para registro de eventos
        """
        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger
        
        self.logger.debug("MagicNumberGenerator inicializado")
    
    # ==================== GENERACIÓN ====================
    
    def generate(
        self,
        bot_id: int,
        ia_config_id: int,
        order_type: str,
        sequence: int = 0
    ) -> int:
        """
        Genera un Magic Number único de 6 dígitos.
        
        Estructura: [Bot][IA][Tipo][Secuencia]
        - Dígito 1: Bot ID (1-5)
        - Dígito 2: IA Config ID (0-9)
        - Dígito 3: Order Type (0=Market, 1=Limit)
        - Dígitos 4-6: Sequence (000-999)
        
        Args:
            bot_id: ID del bot (1-5)
            ia_config_id: ID de configuración IA (0-9)
            order_type: Tipo de orden ('market' o 'limit', case-insensitive)
            sequence: Número de secuencia (0-999, default: 0)
        
        Returns:
            Magic Number de 6 dígitos
        
        Raises:
            InvalidBotIdError: Si bot_id no está entre 1 y 5
            InvalidIAConfigIdError: Si ia_config_id no está entre 0 y 9
            InvalidOrderTypeError: Si order_type no es 'market' o 'limit'
            MagicNumberError: Si sequence no está entre 0 y 999
        
        Example:
            >>> generator = MagicNumberGenerator()
            >>> generator.generate(1, 0, "market")  # 100000
            >>> generator.generate(2, 3, "limit", 456)  # 231456
        """
        # Validar parámetros
        self._validate_bot_id(bot_id)
        self._validate_ia_config_id(ia_config_id)
        order_type_code = self._validate_and_encode_order_type(order_type)
        self._validate_sequence(sequence)
        
        # Construir Magic Number
        # Formato: BITSSS
        # B = Bot ID (1 dígito)
        # I = IA Config ID (1 dígito)
        # T = Type (1 dígito)
        # SSS = Sequence (3 dígitos)
        
        magic_number = (
            bot_id * 100000 +           # Primer dígito
            ia_config_id * 10000 +      # Segundo dígito
            order_type_code * 1000 +    # Tercer dígito
            sequence                     # Últimos 3 dígitos
        )
        
        self.logger.debug(
            f"Magic Number generado: {magic_number} "
            f"(Bot={bot_id}, IA={ia_config_id}, Type={order_type}, Seq={sequence})"
        )
        
        return magic_number
    
    # ==================== DECODIFICACIÓN ====================
    
    def decode(self, magic_number: int) -> MagicNumberComponents:
        """
        Decodifica un Magic Number en sus componentes.
        
        Args:
            magic_number: Magic Number de 6 dígitos
        
        Returns:
            Componentes decodificados del Magic Number
        
        Raises:
            MagicNumberError: Si el Magic Number no tiene 6 dígitos
            InvalidBotIdError: Si el bot_id decodificado es inválido
            InvalidIAConfigIdError: Si el ia_config_id decodificado es inválido
        
        Example:
            >>> generator = MagicNumberGenerator()
            >>> components = generator.decode(231456)
            >>> print(components.bot_id)  # 2
            >>> print(components.order_type)  # 'limit'
        """
        # Validar longitud
        if not (100000 <= magic_number <= 999999):
            raise MagicNumberError(
                f"Magic Number debe tener exactamente 6 dígitos. "
                f"Recibido: {magic_number}"
            )
        
        # Extraer componentes
        bot_id = magic_number // 100000
        ia_config_id = (magic_number // 10000) % 10
        order_type_code = (magic_number // 1000) % 10
        sequence = magic_number % 1000
        
        # Validar componentes decodificados
        self._validate_bot_id(bot_id)
        self._validate_ia_config_id(ia_config_id)
        
        # Decodificar tipo de orden
        if order_type_code == self.ORDER_TYPE_MARKET:
            order_type = "market"
        elif order_type_code == self.ORDER_TYPE_LIMIT:
            order_type = "limit"
        else:
            raise MagicNumberError(
                f"Código de tipo de orden inválido: {order_type_code}. "
                f"Debe ser 0 (market) o 1 (limit)"
            )
        
        components = MagicNumberComponents(
            bot_id=bot_id,
            ia_config_id=ia_config_id,
            order_type=order_type,
            sequence=sequence,
            magic_number=magic_number
        )
        
        self.logger.debug(
            f"Magic Number decodificado: {magic_number} -> "
            f"Bot={bot_id}, IA={ia_config_id}, Type={order_type}, Seq={sequence}"
        )
        
        return components
    
    # ==================== UTILIDADES ====================
    
    def format_magic_number(self, magic_number: int) -> str:
        """
        Formatea un Magic Number como string de 6 dígitos con ceros leading.
        
        Args:
            magic_number: Magic Number a formatear
        
        Returns:
            String de 6 dígitos
        
        Example:
            >>> generator = MagicNumberGenerator()
            >>> generator.format_magic_number(100005)  # "100005"
        """
        return f"{magic_number:06d}"
    
    # ==================== VALIDACIONES PRIVADAS ====================
    
    def _validate_bot_id(self, bot_id: int) -> None:
        """
        Valida que bot_id esté entre 1 y 5.
        
        Args:
            bot_id: ID del bot a validar
        
        Raises:
            InvalidBotIdError: Si bot_id no está entre 1 y 5
        """
        if not isinstance(bot_id, int) or not (1 <= bot_id <= 5):
            raise InvalidBotIdError(
                f"bot_id debe estar entre 1 y 5. Recibido: {bot_id}"
            )
    
    def _validate_ia_config_id(self, ia_config_id: int) -> None:
        """
        Valida que ia_config_id esté entre 0 y 9.
        
        Args:
            ia_config_id: ID de configuración IA a validar
        
        Raises:
            InvalidIAConfigIdError: Si ia_config_id no está entre 0 y 9
        """
        if not isinstance(ia_config_id, int) or not (0 <= ia_config_id <= 9):
            raise InvalidIAConfigIdError(
                f"ia_config_id debe estar entre 0 y 9. Recibido: {ia_config_id}"
            )
    
    def _validate_and_encode_order_type(self, order_type: str) -> int:
        """
        Valida y codifica el tipo de orden.
        
        Args:
            order_type: Tipo de orden ('market' o 'limit', case-insensitive)
        
        Returns:
            Código del tipo de orden (0=market, 1=limit)
        
        Raises:
            InvalidOrderTypeError: Si order_type no es 'market' o 'limit'
        """
        if not isinstance(order_type, str):
            raise InvalidOrderTypeError(
                f"order_type debe ser un string. Recibido: {type(order_type).__name__}"
            )
        
        order_type_lower = order_type.lower().strip()
        
        if order_type_lower == "market":
            return self.ORDER_TYPE_MARKET
        elif order_type_lower == "limit":
            return self.ORDER_TYPE_LIMIT
        else:
            raise InvalidOrderTypeError(
                f"order_type debe ser 'market' o 'limit'. Recibido: '{order_type}'"
            )
    
    def _validate_sequence(self, sequence: int) -> None:
        """
        Valida que sequence esté entre 0 y 999.
        
        Args:
            sequence: Número de secuencia a validar
        
        Raises:
            MagicNumberError: Si sequence no está entre 0 y 999
        """
        if not isinstance(sequence, int) or not (0 <= sequence <= 999):
            raise MagicNumberError(
                f"sequence debe estar entre 0 y 999. Recibido: {sequence}"
            )
    
    # ==================== REPRESENTACIÓN ====================
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        return "<MagicNumberGenerator>"
    
    def __str__(self) -> str:
        """Representación en string"""
        return "MagicNumberGenerator - Generador de Magic Numbers únicos [Bot][IA][Tipo][Seq]"
