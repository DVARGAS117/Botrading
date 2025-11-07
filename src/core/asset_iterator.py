"""
AssetIterator - T22: Iteración determinista de activos
Garantiza iteración ordenada y consistente de activos en cada ciclo de trading
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Iterator
from pathlib import Path
from datetime import datetime


class AssetIterationError(Exception):
    """Excepción para errores de iteración de activos"""
    pass


@dataclass
class Asset:
    """
    Representa un activo (instrumento financiero) para trading
    
    Attributes:
        symbol: Símbolo del activo (ej: "EURUSD", "BTCUSD")
        enabled: Si el activo está habilitado para trading
        timeframes: Timeframes a analizar (ej: ["5M", "15M", "1H"])
        lot_size: Tamaño de lote predeterminado
        max_positions: Número máximo de posiciones simultáneas
    """
    symbol: str
    enabled: bool
    timeframes: Optional[List[str]] = None
    lot_size: Optional[float] = None
    max_positions: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir Asset a diccionario"""
        return asdict(self)


class AssetIterator:
    """
    Iterador determinista de activos
    
    Garantiza que en cada ciclo de trading, los activos se procesen
    en el mismo orden definido en la configuración, evitando sesgos
    y comportamiento impredecible.
    
    Características:
    - Iteración consistente (mismo orden en cada ciclo)
    - Omite activos deshabilitados automáticamente
    - Recarga de configuración sin perder estadísticas
    - Validación de configuración al inicio
    - Tracking de estadísticas de iteración
    
    Example:
        >>> config = {
        ...     "assets": [
        ...         {"symbol": "EURUSD", "enabled": True},
        ...         {"symbol": "GBPUSD", "enabled": True}
        ...     ]
        ... }
        >>> iterator = AssetIterator(config=config)
        >>> for asset in iterator:
        ...     print(f"Processing {asset.symbol}")
        Processing EURUSD
        Processing GBPUSD
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        logger: Optional[Any] = None
    ):
        """
        Inicializar AssetIterator
        
        Args:
            config: Diccionario de configuración con lista de assets
            config_path: Ruta al archivo de configuración JSON
            logger: Logger opcional (BotLogger de T39)
            
        Raises:
            AssetIterationError: Si no se proporciona config ni config_path,
                                 o si la configuración es inválida
        """
        if config is None and config_path is None:
            raise AssetIterationError("Either config or config_path required")
        
        self.logger = logger
        self.config_path = config_path
        self.assets: List[Asset] = []
        self.statistics = {
            "total_iterations": 0,
            "assets_processed_per_iteration": 0
        }
        
        # Cargar configuración
        if config_path:
            self.config = self._load_config_from_file(config_path)
        else:
            self.config = config
        
        # Validar y construir lista de activos
        self._validate_and_build_assets()
    
    def _load_config_from_file(self, config_path: str) -> Dict[str, Any]:
        """
        Cargar configuración desde archivo JSON
        
        Args:
            config_path: Ruta al archivo JSON
            
        Returns:
            Diccionario de configuración
            
        Raises:
            AssetIterationError: Si el archivo no existe o JSON es inválido
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            raise AssetIterationError(f"Config file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise AssetIterationError(f"Invalid JSON in config file: {e}")
    
    def _validate_and_build_assets(self):
        """
        Validar configuración y construir lista de Asset objects
        
        Raises:
            AssetIterationError: Si la configuración es inválida
        """
        if "assets" not in self.config:
            raise AssetIterationError("Config must contain 'assets' key")
        
        assets_config = self.config["assets"]
        
        if not isinstance(assets_config, list):
            raise AssetIterationError("'assets' must be a list")
        
        seen_symbols = set()
        
        for idx, asset_data in enumerate(assets_config):
            if not isinstance(asset_data, dict):
                raise AssetIterationError(f"Asset at index {idx} must be a dictionary")
            
            # Validar campos obligatorios
            if "symbol" not in asset_data:
                raise AssetIterationError(f"Asset at index {idx}: 'symbol' field is required")
            
            symbol = asset_data["symbol"]
            
            # Validar tipos de datos
            if not isinstance(symbol, str):
                raise AssetIterationError(f"Asset '{symbol}': 'symbol' must be a string")
            
            # Validar símbolos duplicados
            if symbol in seen_symbols:
                raise AssetIterationError(f"Duplicate symbol found: {symbol}")
            seen_symbols.add(symbol)
            
            # Validar 'enabled' si está presente
            if "enabled" in asset_data:
                enabled = asset_data["enabled"]
                if not isinstance(enabled, bool):
                    raise AssetIterationError(f"Asset '{symbol}': 'enabled' must be a boolean")
            else:
                # Default: enabled=True si no se especifica
                asset_data["enabled"] = True
            
            # Crear objeto Asset
            asset = Asset(
                symbol=symbol,
                enabled=asset_data["enabled"],
                timeframes=asset_data.get("timeframes"),
                lot_size=asset_data.get("lot_size"),
                max_positions=asset_data.get("max_positions")
            )
            
            self.assets.append(asset)
        
        # Log de inicialización
        if self.logger:
            self.logger.info(
                f"AssetIterator initialized with {len(self.assets)} assets "
                f"({len(self.get_enabled_assets())} enabled)",
                extra={
                    "total_assets": len(self.assets),
                    "enabled_assets": len(self.get_enabled_assets())
                }
            )
    
    def __iter__(self) -> Iterator[Asset]:
        """
        Iniciar iteración sobre activos habilitados
        
        Returns:
            Iterator de Asset objects habilitados en orden determinista
        """
        # Incrementar contador de iteraciones
        self.statistics["total_iterations"] += 1
        
        # Obtener activos habilitados
        enabled_assets = self.get_enabled_assets()
        self.statistics["assets_processed_per_iteration"] = len(enabled_assets)
        
        # Log de inicio de iteración
        if self.logger:
            self.logger.info(
                f"Starting iteration #{self.statistics['total_iterations']} "
                f"with {len(enabled_assets)} enabled assets",
                extra={
                    "iteration_number": self.statistics["total_iterations"],
                    "enabled_assets_count": len(enabled_assets),
                    "asset_symbols": [a.symbol for a in enabled_assets]
                }
            )
        
        # Iterar sobre activos habilitados
        for asset in enabled_assets:
            if self.logger:
                self.logger.debug(
                    f"Processing asset: {asset.symbol}",
                    extra={"symbol": asset.symbol, "asset_data": asset.to_dict()}
                )
            yield asset
    
    def get_enabled_assets(self) -> List[Asset]:
        """
        Obtener lista de activos habilitados
        
        Returns:
            Lista de Asset objects con enabled=True, en orden original
        """
        return [asset for asset in self.assets if asset.enabled]
    
    def get_all_assets(self) -> List[Asset]:
        """
        Obtener todos los activos (habilitados y deshabilitados)
        
        Returns:
            Lista completa de Asset objects en orden original
        """
        return self.assets.copy()
    
    def get_asset_by_symbol(self, symbol: str) -> Optional[Asset]:
        """
        Obtener un activo específico por su símbolo
        
        Args:
            symbol: Símbolo del activo a buscar
            
        Returns:
            Asset object si se encuentra, None si no existe
        """
        for asset in self.assets:
            if asset.symbol == symbol:
                return asset
        return None
    
    def get_asset_count(self) -> int:
        """
        Obtener número total de activos (habilitados + deshabilitados)
        
        Returns:
            Número total de activos configurados
        """
        return len(self.assets)
    
    def get_enabled_count(self) -> int:
        """
        Obtener número de activos habilitados
        
        Returns:
            Número de activos con enabled=True
        """
        return len(self.get_enabled_assets())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de iteración
        
        Returns:
            Diccionario con estadísticas:
            - total_iterations: Número de ciclos completados
            - assets_processed_per_iteration: Activos procesados por ciclo
            - total_assets: Total de activos configurados
            - enabled_assets: Activos habilitados actualmente
        """
        return {
            "total_iterations": self.statistics["total_iterations"],
            "assets_processed_per_iteration": self.statistics["assets_processed_per_iteration"],
            "total_assets": len(self.assets),
            "enabled_assets": len(self.get_enabled_assets())
        }
    
    def clear_statistics(self):
        """Limpiar estadísticas de iteración"""
        self.statistics["total_iterations"] = 0
        self.statistics["assets_processed_per_iteration"] = 0
        
        if self.logger:
            self.logger.debug("AssetIterator statistics cleared")
    
    def reload_config(self):
        """
        Recargar configuración desde archivo
        
        Las estadísticas se preservan tras la recarga.
        
        Raises:
            AssetIterationError: Si no hay config_path o el archivo es inválido
        """
        if not self.config_path:
            raise AssetIterationError("Cannot reload: no config_path specified")
        
        # Recargar config
        self.config = self._load_config_from_file(self.config_path)
        
        # Reconstruir lista de activos
        self.assets = []
        self._validate_and_build_assets()
        
        if self.logger:
            self.logger.info(
                "Asset configuration reloaded",
                extra={
                    "config_path": self.config_path,
                    "total_assets": len(self.assets),
                    "enabled_assets": len(self.get_enabled_assets())
                }
            )
