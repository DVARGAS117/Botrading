"""
SymbolSpecificationExtractor - Obtención de especificaciones desde MT5 - T31

Este módulo extrae especificaciones de símbolos directamente desde MT5,
convirtiendo la información de MT5 a SymbolSpecification para PositionSizer
y LotAdjuster.

Evita supuestos incorrectos y garantiza que el cálculo de lotes use
datos reales del broker.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T31 - Obtención de especificaciones del símbolo desde MT5
"""

from typing import Optional, Dict
import logging

from src.core.mt5_connector import MT5Connector
from src.core.position_sizer import SymbolSpecification as PositionSizerSpec
from src.core.lot_adjuster import SymbolSpecification as LotAdjusterSpec


# ============================================================================
# EXCEPCIONES
# ============================================================================

class SymbolSpecificationError(Exception):
    """Excepción base para errores de especificación de símbolos"""
    pass


class SymbolNotFoundError(SymbolSpecificationError):
    """Excepción cuando el símbolo no se encuentra en MT5"""
    pass


class InvalidSymbolDataError(SymbolSpecificationError):
    """Excepción cuando los datos del símbolo son inválidos"""
    pass


# ============================================================================
# SYMBOL SPECIFICATION EXTRACTOR
# ============================================================================

class SymbolSpecificationExtractor:
    """
    Extractor de especificaciones de símbolos desde MT5.
    
    Obtiene información real del broker sobre:
    - Point, tick_size, tick_value
    - Volume limits (min, max, step)
    - Contract size
    
    Y la convierte a SymbolSpecification para uso en PositionSizer
    y LotAdjuster.
    
    Attributes:
        connector: MT5Connector para obtener información
        logger: Logger para registrar operaciones
        _cache: Caché de especificaciones ya obtenidas
    
    Example:
        >>> connector = MT5Connector(config)
        >>> extractor = SymbolSpecificationExtractor(connector)
        >>> 
        >>> # Obtener especificación para PositionSizer
        >>> spec = extractor.get_symbol_specification("EURUSD")
        >>> print(f"Min lot: {spec.volume_min}, Max: {spec.volume_max}")
        >>> 
        >>> # Obtener especificación para LotAdjuster
        >>> lot_spec = extractor.get_lot_adjuster_specification("EURUSD")
    """
    
    def __init__(
        self,
        connector: MT5Connector,
        logger: Optional[logging.Logger] = None,
        enable_cache: bool = True
    ):
        """
        Inicializar SymbolSpecificationExtractor.
        
        Args:
            connector: MT5Connector ya conectado a MT5
            logger: Logger opcional para registrar operaciones
            enable_cache: Si True, cachea especificaciones (default: True)
        
        Raises:
            ValueError: Si connector es None
        """
        if connector is None:
            raise ValueError("MT5Connector is required")
        
        self.connector = connector
        self.logger = logger or self._create_default_logger()
        self._enable_cache = enable_cache
        self._cache: Dict[str, PositionSizerSpec] = {}
    
    def _create_default_logger(self) -> logging.Logger:
        """Crear logger por defecto"""
        logger = logging.getLogger("SymbolSpecExtractor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_symbol_specification(
        self,
        symbol: str,
        use_cache: bool = True
    ) -> PositionSizerSpec:
        """
        Obtener especificación completa de un símbolo desde MT5.
        
        Extrae información de MT5 y la convierte a SymbolSpecification
        para uso en PositionSizer.
        
        Args:
            symbol: Nombre del símbolo (ej: "EURUSD", "XAUUSD")
            use_cache: Si True, usa caché si está disponible
        
        Returns:
            SymbolSpecification con datos reales de MT5
        
        Raises:
            ValueError: Si symbol está vacío
            SymbolNotFoundError: Si el símbolo no existe en MT5
            SymbolSpecificationError: Si hay error obteniendo datos
        
        Example:
            >>> spec = extractor.get_symbol_specification("EURUSD")
            >>> print(f"Point: {spec.point}")
            >>> print(f"Contract size: {spec.contract_size}")
        """
        # Validar entrada
        if not symbol or not symbol.strip():
            raise ValueError("Symbol name cannot be empty")
        
        symbol = symbol.strip().upper()
        
        # Verificar caché
        if self._enable_cache and use_cache and symbol in self._cache:
            self.logger.debug(f"Returning cached specification for {symbol}")
            return self._cache[symbol]
        
        # Obtener información de MT5
        try:
            self.logger.debug(f"Fetching symbol info for {symbol} from MT5")
            symbol_info = self.connector.get_symbol_info(symbol)
            
            if symbol_info is None:
                raise SymbolSpecificationError(
                    f"No symbol info returned from MT5 for '{symbol}'"
                )
        
        except ValueError as e:
            # MT5Connector lanza ValueError si el símbolo no existe
            raise SymbolNotFoundError(str(e))
        
        except Exception as e:
            raise SymbolSpecificationError(
                f"Error getting symbol info for '{symbol}': {e}"
            )
        
        # Validar datos antes de crear la especificación
        self._validate_symbol_info(symbol_info)
        
        # Convertir a SymbolSpecification
        try:
            spec = PositionSizerSpec(
                symbol=symbol,
                point=symbol_info.point,
                tick_size=symbol_info.tick_size,
                tick_value=symbol_info.tick_value,
                volume_min=symbol_info.volume_min,
                volume_max=symbol_info.volume_max,
                volume_step=symbol_info.volume_step,
                contract_size=symbol_info.contract_size
            )
            
            # Guardar en caché
            if self._enable_cache:
                self._cache[symbol] = spec
            
            self.logger.info(
                f"Successfully extracted specification for {symbol}: "
                f"min={spec.volume_min}, max={spec.volume_max}, "
                f"step={spec.volume_step}"
            )
            
            return spec
        
        except Exception as e:
            raise SymbolSpecificationError(
                f"Error creating SymbolSpecification for '{symbol}': {e}"
            )
    
    def get_lot_adjuster_specification(
        self,
        symbol: str,
        use_cache: bool = True
    ) -> LotAdjusterSpec:
        """
        Obtener especificación para LotAdjuster desde MT5.
        
        LotAdjuster solo necesita volume_min, volume_max y volume_step,
        por lo que se retorna un objeto más ligero.
        
        Args:
            symbol: Nombre del símbolo
            use_cache: Si True, usa caché si está disponible
        
        Returns:
            LotAdjusterSpec con límites de volumen
        
        Raises:
            ValueError: Si symbol está vacío
            SymbolNotFoundError: Si el símbolo no existe
            SymbolSpecificationError: Si hay error obteniendo datos
        
        Example:
            >>> lot_spec = extractor.get_lot_adjuster_specification("EURUSD")
            >>> print(f"Step: {lot_spec.volume_step}")
        """
        # Obtener especificación completa
        full_spec = self.get_symbol_specification(symbol, use_cache)
        
        # Convertir a LotAdjusterSpec (más ligero)
        return LotAdjusterSpec(
            symbol=full_spec.symbol,
            volume_min=full_spec.volume_min,
            volume_max=full_spec.volume_max,
            volume_step=full_spec.volume_step
        )
    
    def _validate_symbol_info(self, symbol_info) -> None:
        """
        Validar que la información del símbolo sea válida.
        
        Args:
            symbol_info: Información del símbolo de MT5
        
        Raises:
            InvalidSymbolDataError: Si los datos son inválidos
        """
        # Validar point
        if not hasattr(symbol_info, 'point') or symbol_info.point <= 0:
            raise InvalidSymbolDataError(
                f"Invalid point value: {getattr(symbol_info, 'point', None)}"
            )
        
        # Validar tick_size
        if not hasattr(symbol_info, 'tick_size') or symbol_info.tick_size <= 0:
            raise InvalidSymbolDataError(
                f"Invalid tick_size: {getattr(symbol_info, 'tick_size', None)}"
            )
        
        # Validar tick_value
        if not hasattr(symbol_info, 'tick_value') or symbol_info.tick_value <= 0:
            raise InvalidSymbolDataError(
                f"Invalid tick_value: {getattr(symbol_info, 'tick_value', None)}"
            )
        
        # Validar volume_min
        if not hasattr(symbol_info, 'volume_min') or symbol_info.volume_min <= 0:
            raise InvalidSymbolDataError(
                f"Invalid volume_min: {getattr(symbol_info, 'volume_min', None)}"
            )
        
        # Validar volume_max
        if not hasattr(symbol_info, 'volume_max') or symbol_info.volume_max <= 0:
            raise InvalidSymbolDataError(
                f"Invalid volume_max: {getattr(symbol_info, 'volume_max', None)}"
            )
        
        # Validar volume_step
        if not hasattr(symbol_info, 'volume_step') or symbol_info.volume_step <= 0:
            raise InvalidSymbolDataError(
                f"Invalid volume_step: {getattr(symbol_info, 'volume_step', None)}"
            )
        
        # Validar contract_size
        if not hasattr(symbol_info, 'contract_size') or symbol_info.contract_size <= 0:
            raise InvalidSymbolDataError(
                f"Invalid contract_size: {getattr(symbol_info, 'contract_size', None)}"
            )
        
        # Validar relación min/max
        if symbol_info.volume_min > symbol_info.volume_max:
            raise InvalidSymbolDataError(
                f"volume_min ({symbol_info.volume_min}) cannot be greater than "
                f"volume_max ({symbol_info.volume_max})"
            )
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Limpiar caché de especificaciones.
        
        Args:
            symbol: Si se especifica, solo limpia ese símbolo.
                   Si es None, limpia todo el caché.
        
        Example:
            >>> # Limpiar caché completo
            >>> extractor.clear_cache()
            >>> 
            >>> # Limpiar solo EURUSD
            >>> extractor.clear_cache("EURUSD")
        """
        if symbol:
            symbol = symbol.strip().upper()
            if symbol in self._cache:
                del self._cache[symbol]
                self.logger.debug(f"Cleared cache for {symbol}")
        else:
            self._cache.clear()
            self.logger.debug("Cleared all symbol specification cache")
    
    def is_cached(self, symbol: str) -> bool:
        """
        Verificar si un símbolo está en caché.
        
        Args:
            symbol: Nombre del símbolo
        
        Returns:
            True si está en caché, False en caso contrario
        """
        return symbol.strip().upper() in self._cache
    
    def get_cached_symbols(self) -> list:
        """
        Obtener lista de símbolos en caché.
        
        Returns:
            Lista de nombres de símbolos cacheados
        """
        return list(self._cache.keys())
    
    def prefetch_symbols(self, symbols: list) -> Dict[str, PositionSizerSpec]:
        """
        Pre-cargar especificaciones de múltiples símbolos.
        
        Útil para cargar todas las especificaciones al inicio
        y evitar llamadas a MT5 durante la operación.
        
        Args:
            symbols: Lista de nombres de símbolos
        
        Returns:
            Diccionario {symbol: SymbolSpecification}
        
        Example:
            >>> symbols = ["EURUSD", "GBPUSD", "XAUUSD"]
            >>> specs = extractor.prefetch_symbols(symbols)
            >>> print(f"Loaded {len(specs)} specifications")
        """
        specs = {}
        
        for symbol in symbols:
            try:
                spec = self.get_symbol_specification(symbol)
                specs[symbol] = spec
            except Exception as e:
                self.logger.warning(
                    f"Failed to prefetch {symbol}: {e}"
                )
        
        self.logger.info(
            f"Prefetched {len(specs)} symbol specifications"
        )
        
        return specs
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        cache_size = len(self._cache)
        return (
            f"<SymbolSpecificationExtractor("
            f"cached_symbols={cache_size}, "
            f"cache_enabled={self._enable_cache})>"
        )


# ============================================================================
# FUNCIONES HELPER
# ============================================================================

def create_extractor_from_connector(
    connector: MT5Connector,
    logger: Optional[logging.Logger] = None
) -> SymbolSpecificationExtractor:
    """
    Crear un SymbolSpecificationExtractor desde un MT5Connector.
    
    Args:
        connector: MT5Connector ya conectado
        logger: Logger opcional
    
    Returns:
        SymbolSpecificationExtractor configurado
    
    Example:
        >>> connector = MT5Connector(config)
        >>> connector.verify_connection()
        >>> extractor = create_extractor_from_connector(connector)
    """
    return SymbolSpecificationExtractor(connector, logger=logger)
