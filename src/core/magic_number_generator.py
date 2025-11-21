"""
Módulo de generación de Magic Numbers únicos.

Este módulo implementa el Ticket T17: Generación de Magic Number único con estructura,
permitiendo identificar inequívocamente cada operación mediante un código de 6 dígitos
que codifica: [Bot][IA][Tipo][Secuencia]

T18: Agrega utilidades de auditoría y decodificación para análisis de operaciones.

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
Tickets: T17, T18
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from collections import defaultdict


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
        - Dígito 1: Bot ID (1-5 o mapeado de 101-106)
        - Dígito 2: IA Config ID (0-9)
        - Dígito 3: Order Type (0=Market, 1=Limit)
        - Dígitos 4-6: Sequence (000-999)
        
        Args:
            bot_id: ID del bot (1-5 o 101-106, se mapean a 1-6)
            ia_config_id: ID de configuración IA (0-9)
            order_type: Tipo de orden ('market' o 'limit', case-insensitive)
            sequence: Número de secuencia (0-999, default: 0)
        
        Returns:
            Magic Number de 6 dígitos
        
        Raises:
            InvalidBotIdError: Si bot_id no es válido
            InvalidIAConfigIdError: Si ia_config_id no está entre 0 y 9
            InvalidOrderTypeError: Si order_type no es 'market' o 'limit'
            MagicNumberError: Si sequence no está entre 0 y 999
        
        Example:
            >>> generator = MagicNumberGenerator()
            >>> generator.generate(1, 0, "market")  # 100000
            >>> generator.generate(2, 3, "limit", 456)  # 231456
            >>> generator.generate(101, 0, "market")  # 100000 (101 se mapea a 1)
            >>> generator.generate(106, 0, "market")  # 600000 (106 se mapea a 6)
        """
        # Validar parámetros
        self._validate_bot_id(bot_id)
        self._validate_ia_config_id(ia_config_id)
        order_type_code = self._validate_and_encode_order_type(order_type)
        self._validate_sequence(sequence)
        
        # ✅ Mapear bot_id de 3 dígitos (101-106) a 1 dígito (1-6)
        # IDs legacy (1-5) se mantienen igual
        # IDs nuevos (101-106) se mapean: 101->1, 102->2, ..., 106->6
        if bot_id >= 101:
            mapped_bot_id = bot_id - 100
        else:
            mapped_bot_id = bot_id
        
        # Construir Magic Number
        # Formato: BITSSS
        # B = Bot ID (1 dígito)
        # I = IA Config ID (1 dígito)
        # T = Type (1 dígito)
        # SSS = Sequence (3 dígitos)
        
        magic_number = (
            mapped_bot_id * 100000 +    # Primer dígito (mapeado)
            ia_config_id * 10000 +      # Segundo dígito
            order_type_code * 1000 +    # Tercer dígito
            sequence                     # Últimos 3 dígitos
        )
        
        self.logger.debug(
            f"Magic Number generado: {magic_number} "
            f"(Bot={bot_id} [mapped to {mapped_bot_id}], IA={ia_config_id}, Type={order_type}, Seq={sequence})"
        )
        
        return magic_number
    
    # ==================== DECODIFICACIÓN ====================
    
    def decode(self, magic_number: int) -> MagicNumberComponents:
        """
        Decodifica un Magic Number en sus componentes.
        
        NOTA: El bot_id retornado es siempre el ID mapeado (1-6), no el ID original.
        Si necesitas distinguir entre IDs legacy (1-5) e IDs nuevos (101-106),
        usa contexto adicional.
        
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
            >>> components = generator.decode(600000)
            >>> print(components.bot_id)  # 6 (podría ser bot 6 o bot 106)
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
        # NOTA: bot_id aquí es el valor mapeado (1-6), no validamos con _validate_bot_id
        # porque aceptaría 101-106 que no son el valor decodificado correcto
        if bot_id < 1 or bot_id > 9:
            raise InvalidBotIdError(
                f"bot_id decodificado inválido: {bot_id}. "
                f"Debe estar entre 1 y 9 (valores mapeados)"
            )
        
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
            f"Bot={bot_id} [mapped], IA={ia_config_id}, Type={order_type}, Seq={sequence}"
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
            InvalidBotIdError: Si bot_id no es válido
        """
        # Aceptar bot_id de 1-5 (legacy) o 101-106 (nuevos IDs)
        valid_ids = [1, 2, 3, 4, 5, 101, 102, 103, 104, 105, 106]
        if not isinstance(bot_id, int) or bot_id not in valid_ids:
            raise InvalidBotIdError(
                f"bot_id debe ser uno de {valid_ids}. Recibido: {bot_id}"
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
    
    # ==================== AUDITORÍA Y ANÁLISIS ====================
    
    def decode_batch(self, magic_numbers: List[int]) -> List[MagicNumberComponents]:
        """
        Decodifica un lote de Magic Numbers.
        
        Args:
            magic_numbers: Lista de Magic Numbers a decodificar
        
        Returns:
            Lista de MagicNumberComponents con información decodificada
        
        Raises:
            TypeError: Si magic_numbers no es una lista
            InvalidMagicNumberError: Si algún magic number es inválido
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        results = []
        for mn in magic_numbers:
            decoded = self.decode(mn)
            results.append(decoded)
        
        return results
    
    def generate_audit_report(self, magic_numbers: List[int]) -> Dict[str, Any]:
        """
        Genera un reporte de auditoría completo de un conjunto de Magic Numbers.
        
        Args:
            magic_numbers: Lista de Magic Numbers a auditar
        
        Returns:
            Diccionario con estadísticas y análisis completo
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        decoded_batch = self.decode_batch(magic_numbers)
        
        # Contadores simples (valores enteros, no diccionarios)
        operations_by_bot = defaultdict(int)
        operations_by_ia = defaultdict(int)
        operations_by_type = defaultdict(int)
        
        for item in decoded_batch:
            operations_by_bot[item.bot_id] += 1
            operations_by_ia[item.ia_config_id] += 1
            operations_by_type[item.order_type] += 1
        
        return {
            'total_operations': len(magic_numbers),
            'operations_by_bot': dict(operations_by_bot),
            'operations_by_ia_config': dict(operations_by_ia),
            'operations_by_type': dict(operations_by_type)
        }
    
    def get_distribution_by_bot(self, magic_numbers: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Obtiene la distribución de Magic Numbers por Bot ID.
        
        Args:
            magic_numbers: Lista de Magic Numbers
        
        Returns:
            Diccionario {bot_id: {"count": count, "percentage": percentage}}
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        total = len(magic_numbers)
        if total == 0:
            return {}
        
        bot_counts = defaultdict(int)
        for mn in magic_numbers:
            decoded = self.decode(mn)
            bot_counts[decoded.bot_id] += 1
        
        return {
            bot_id: {
                "count": count,
                "percentage": (count / total) * 100
            }
            for bot_id, count in bot_counts.items()
        }
    
    def get_distribution_by_ia_config(self, magic_numbers: List[int]) -> Dict[int, Dict[str, int]]:
        """
        Obtiene la distribución de Magic Numbers por IA Config ID.
        
        Args:
            magic_numbers: Lista de Magic Numbers
        
        Returns:
            Diccionario {ia_config_id: {"count": count}}
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        ia_counts = defaultdict(int)
        for mn in magic_numbers:
            decoded = self.decode(mn)
            ia_counts[decoded.ia_config_id] += 1
        
        return {ia_id: {"count": count} for ia_id, count in ia_counts.items()}
    
    def get_distribution_by_type(self, magic_numbers: List[int]) -> Dict[str, Dict[str, int]]:
        """
        Obtiene la distribución de Magic Numbers por tipo de orden.
        
        Args:
            magic_numbers: Lista de Magic Numbers
        
        Returns:
            Diccionario {order_type: {"count": count}}
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        type_counts = defaultdict(int)
        for mn in magic_numbers:
            decoded = self.decode(mn)
            type_counts[decoded.order_type] += 1
        
        return {order_type: {"count": count} for order_type, count in type_counts.items()}
    
    def filter_by_bot(self, magic_numbers: List[int], bot_id: int) -> List[int]:
        """
        Filtra Magic Numbers por Bot ID.
        
        Args:
            magic_numbers: Lista de Magic Numbers
            bot_id: ID del bot a filtrar
        
        Returns:
            Lista de Magic Numbers que pertenecen al bot especificado
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        if not isinstance(bot_id, int):
            raise TypeError("bot_id debe ser un entero")
        
        filtered = []
        for mn in magic_numbers:
            decoded = self.decode(mn)
            if decoded.bot_id == bot_id:
                filtered.append(mn)
        
        return filtered
    
    def filter_by_ia_config(self, magic_numbers: List[int], ia_config_id: int) -> List[int]:
        """
        Filtra Magic Numbers por IA Config ID.
        
        Args:
            magic_numbers: Lista de Magic Numbers
            ia_config_id: ID de configuración de IA a filtrar
        
        Returns:
            Lista de Magic Numbers que usan la configuración de IA especificada
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        if not isinstance(ia_config_id, int):
            raise TypeError("ia_config_id debe ser un entero")
        
        filtered = []
        for mn in magic_numbers:
            decoded = self.decode(mn)
            if decoded.ia_config_id == ia_config_id:
                filtered.append(mn)
        
        return filtered
    
    def filter_by_type(self, magic_numbers: List[int], order_type: str) -> List[int]:
        """
        Filtra Magic Numbers por tipo de orden.
        
        Args:
            magic_numbers: Lista de Magic Numbers
            order_type: Tipo de orden ('market' o 'limit')
        
        Returns:
            Lista de Magic Numbers del tipo especificado
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        if not isinstance(order_type, str):
            raise TypeError("order_type debe ser una cadena")
        
        order_type_lower = order_type.lower()
        if order_type_lower not in ['market', 'limit']:
            raise InvalidOrderTypeError(
                f"order_type debe ser 'market' o 'limit'. Recibido: '{order_type}'"
            )
        
        filtered = []
        for mn in magic_numbers:
            decoded = self.decode(mn)
            if decoded.order_type == order_type_lower:
                filtered.append(mn)
        
        return filtered
    
    def export_to_dict_list(self, magic_numbers: List[int]) -> List[Dict[str, Any]]:
        """
        Exporta Magic Numbers decodificados a lista de diccionarios.
        
        Args:
            magic_numbers: Lista de Magic Numbers
        
        Returns:
            Lista de diccionarios con información decodificada
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        decoded_batch = self.decode_batch(magic_numbers)
        
        result = []
        for comp in decoded_batch:
            result.append({
                'magic_number': comp.magic_number,
                'bot_id': comp.bot_id,
                'ia_config_id': comp.ia_config_id,
                'order_type': comp.order_type,
                'sequence': comp.sequence
            })
        
        return result
    
    def export_to_csv_format(self, magic_numbers: List[int], include_header: bool = False) -> List[List[Any]]:
        """
        Exporta Magic Numbers decodificados a formato CSV (lista de listas).
        
        Args:
            magic_numbers: Lista de Magic Numbers
            include_header: Si True, incluye header como primera fila
        
        Returns:
            Lista de listas con datos en formato CSV
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        decoded_batch = self.decode_batch(magic_numbers)
        
        result = []
        
        # Agregar header si se solicita
        if include_header:
            result.append(['magic_number', 'bot_id', 'ia_config_id', 'order_type', 'sequence'])
        
        # Agregar datos
        for comp in decoded_batch:
            result.append([
                comp.magic_number,
                comp.bot_id,
                comp.ia_config_id,
                comp.order_type,
                comp.sequence
            ])
        
        return result
    
    def validate_magic_number_integrity(self, magic_number: int) -> Dict[str, Any]:
        """
        Valida la integridad de un Magic Number.
        
        Args:
            magic_number: Magic Number a validar
        
        Returns:
            Diccionario con resultado de validación y detalles
        """
        result = {
            'magic_number': magic_number,
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'decoded': None
        }
        
        try:
            # Validar rango
            if not isinstance(magic_number, int):
                result['errors'].append("No es un entero")
                return result
            
            if magic_number < 100000 or magic_number > 999999:
                result['errors'].append("No está en el rango de 6 dígitos (100000-999999)")
                return result
            
            # Intentar decodificar
            decoded = self.decode(magic_number)
            result['decoded'] = decoded
            
            # Validar componentes
            if decoded.bot_id < 0 or decoded.bot_id > 9:
                result['warnings'].append(f"bot_id fuera de rango esperado: {decoded.bot_id}")
            
            if decoded.ia_config_id < 0 or decoded.ia_config_id > 9:
                result['warnings'].append(f"ia_config_id fuera de rango esperado: {decoded.ia_config_id}")
            
            if decoded.order_type not in ['market', 'limit']:
                result['errors'].append(f"order_type inválido: {decoded.order_type}")
                return result
            
            if decoded.sequence < 0 or decoded.sequence > 999:
                result['warnings'].append(f"sequence fuera de rango: {decoded.sequence}")
            
            # Si llegamos aquí, es válido
            result['is_valid'] = True
            
        except Exception as e:
            result['errors'].append(str(e))
        
        return result
    
    def validate_batch_integrity(self, magic_numbers: List[int]) -> Dict[str, Any]:
        """
        Valida la integridad de un lote de Magic Numbers.
        
        Args:
            magic_numbers: Lista de Magic Numbers
        
        Returns:
            Diccionario con resultado de validación del lote
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        results = {
            'total': len(magic_numbers),
            'valid': 0,
            'invalid': 0,
            'duplicates': 0,
            'validation_details': []
        }
        
        seen = set()
        for mn in magic_numbers:
            validation = self.validate_magic_number_integrity(mn)
            results['validation_details'].append(validation)
            
            if validation['is_valid']:
                results['valid'] += 1
            else:
                results['invalid'] += 1
            
            if mn in seen:
                results['duplicates'] += 1
            seen.add(mn)
        
        return results
    
    def find_by_components(
        self,
        magic_numbers: List[int],
        bot_id: int | None = None,
        ia_config_id: int | None = None,
        order_type: str | None = None,
        min_sequence: int | None = None,
        max_sequence: int | None = None
    ) -> List[int]:
        """
        Busca Magic Numbers por componentes específicos.
        
        Args:
            magic_numbers: Lista de Magic Numbers donde buscar
            bot_id: Filtrar por bot_id (opcional)
            ia_config_id: Filtrar por ia_config_id (opcional)
            order_type: Filtrar por order_type (opcional)
            min_sequence: Secuencia mínima (opcional)
            max_sequence: Secuencia máxima (opcional)
        
        Returns:
            Lista de Magic Numbers que cumplen los criterios
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        filtered = []
        for mn in magic_numbers:
            try:
                decoded = self.decode(mn)
                
                # Aplicar filtros
                if bot_id is not None and decoded.bot_id != bot_id:
                    continue
                
                if ia_config_id is not None and decoded.ia_config_id != ia_config_id:
                    continue
                
                if order_type is not None and decoded.order_type != order_type.lower():
                    continue
                
                if min_sequence is not None and decoded.sequence < min_sequence:
                    continue
                
                if max_sequence is not None and decoded.sequence > max_sequence:
                    continue
                
                # Si pasa todos los filtros, agregar
                filtered.append(mn)
                
            except Exception:
                # Si no se puede decodificar, omitir
                continue
        
        return filtered
    
    def lookup(self, magic_numbers: List[int], target: int) -> Dict[str, Any]:
        """
        Busca un Magic Number específico en una lista y retorna información detallada.
        
        Args:
            magic_numbers: Lista donde buscar
            target: Magic Number a buscar
        
        Returns:
            Diccionario con información de búsqueda
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        if not isinstance(target, int):
            raise TypeError("target debe ser un entero")
        
        result = {
            'found': False,
            'target': target,
            'count': 0,
            'positions': [],
            'decoded': None
        }
        
        # Buscar en la lista
        for idx, mn in enumerate(magic_numbers):
            if mn == target:
                result['found'] = True
                result['count'] += 1
                result['positions'].append(idx)
        
        # Si se encontró, decodificar
        if result['found']:
            try:
                result['decoded'] = self.decode(target)
            except Exception:
                pass
        
        return result
    
    def get_summary_statistics(self, magic_numbers: List[int]) -> Dict[str, int]:
        """
        Obtiene estadísticas resumen de Magic Numbers.
        
        Args:
            magic_numbers: Lista de Magic Numbers
        
        Returns:
            Diccionario con estadísticas resumidas
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        decoded_batch = self.decode_batch(magic_numbers)
        
        unique_bots = set()
        unique_ia_configs = set()
        market_count = 0
        limit_count = 0
        
        for comp in decoded_batch:
            unique_bots.add(comp.bot_id)
            unique_ia_configs.add(comp.ia_config_id)
            if comp.order_type == "market":
                market_count += 1
            else:
                limit_count += 1
        
        return {
            'total_operations': len(magic_numbers),
            'unique_bots': len(unique_bots),
            'unique_ia_configs': len(unique_ia_configs),
            'market_count': market_count,
            'limit_count': limit_count
        }
    
    def is_valid_magic_number(self, magic_number: int) -> bool:
        """
        Verifica si un Magic Number es válido.
        
        Args:
            magic_number: Magic Number a validar
        
        Returns:
            True si es válido, False en caso contrario
        """
        try:
            # Validar que sea entero y esté en rango
            if not isinstance(magic_number, int):
                return False
            
            if magic_number < 100000 or magic_number > 999999:
                return False
            
            # Intentar decodificar - si falla, no es válido
            self.decode(magic_number)
            return True
            
        except Exception:
            return False
    
    def get_invalid_magic_numbers(self, magic_numbers: List[int]) -> List[int]:
        """
        Obtiene lista de Magic Numbers inválidos.
        
        Args:
            magic_numbers: Lista de Magic Numbers a validar
        
        Returns:
            Lista de Magic Numbers inválidos
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        invalid = []
        for mn in magic_numbers:
            if not self.is_valid_magic_number(mn):
                invalid.append(mn)
        
        return invalid
    
    def get_audit_summary(self, magic_numbers: List[int], strict: bool = True) -> Dict[str, Any]:
        """
        Genera un resumen de auditoría con validación.
        
        Args:
            magic_numbers: Lista de Magic Numbers
            strict: Si True, lanza error si hay inválidos. Si False, los incluye en el reporte.
        
        Returns:
            Diccionario con resumen de auditoría
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        invalid_mns = self.get_invalid_magic_numbers(magic_numbers)
        valid_count = len(magic_numbers) - len(invalid_mns)
        
        if strict and len(invalid_mns) > 0:
            raise MagicNumberError(
                f"Se encontraron {len(invalid_mns)} Magic Numbers inválidos en modo strict"
            )
        
        return {
            'total_magic_numbers': len(magic_numbers),
            'valid_count': valid_count,
            'invalid_count': len(invalid_mns),
            'invalid_magic_numbers': invalid_mns
        }
    
    def find_by_bot(self, magic_numbers: List[int], bot_id: int) -> List[int]:
        """
        Alias para filter_by_bot (para compatibilidad).
        
        Args:
            magic_numbers: Lista de Magic Numbers
            bot_id: ID del bot a buscar
        
        Returns:
            Lista de Magic Numbers del bot especificado
        """
        return self.filter_by_bot(magic_numbers, bot_id)
    
    def find_by_ia_config(self, magic_numbers: List[int], ia_config_id: int) -> List[int]:
        """
        Alias para filter_by_ia_config (para compatibilidad).
        
        Args:
            magic_numbers: Lista de Magic Numbers
            ia_config_id: ID de configuración IA a buscar
        
        Returns:
            Lista de Magic Numbers con la configuración IA especificada
        """
        return self.filter_by_ia_config(magic_numbers, ia_config_id)
    
    def find_by_criteria(
        self,
        magic_numbers: List[int],
        bot_ids: List[int] | None = None,
        ia_config_ids: List[int] | None = None,
        order_type: str | None = None,
        min_sequence: int | None = None,
        max_sequence: int | None = None
    ) -> List[int]:
        """
        Busca Magic Numbers por criterios múltiples (con lógica OR para listas).
        
        Args:
            magic_numbers: Lista de Magic Numbers donde buscar
            bot_ids: Lista de bot_ids a buscar (OR)
            ia_config_ids: Lista de ia_config_ids a buscar (OR)
            order_type: Tipo de orden a filtrar
            min_sequence: Secuencia mínima
            max_sequence: Secuencia máxima
        
        Returns:
            Lista de Magic Numbers que cumplen los criterios
        """
        if not isinstance(magic_numbers, list):
            raise TypeError("magic_numbers debe ser una lista")
        
        filtered = []
        for mn in magic_numbers:
            try:
                decoded = self.decode(mn)
                
                # Filtro de bot_ids (OR)
                if bot_ids is not None and decoded.bot_id not in bot_ids:
                    continue
                
                # Filtro de ia_config_ids (OR)
                if ia_config_ids is not None and decoded.ia_config_id not in ia_config_ids:
                    continue
                
                # Filtro de order_type
                if order_type is not None and decoded.order_type != order_type.lower():
                    continue
                
                # Filtro de sequence range
                if min_sequence is not None and decoded.sequence < min_sequence:
                    continue
                
                if max_sequence is not None and decoded.sequence > max_sequence:
                    continue
                
                # Si pasa todos los filtros, agregar
                filtered.append(mn)
                
            except Exception:
                # Si no se puede decodificar, omitir
                continue
        
        return filtered
    
    # ==================== REPRESENTACIÓN ====================
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        return "<MagicNumberGenerator>"
    
    def __str__(self) -> str:
        """Representación en string"""
        return "MagicNumberGenerator - Generador de Magic Numbers únicos [Bot][IA][Tipo][Seq]"

    
