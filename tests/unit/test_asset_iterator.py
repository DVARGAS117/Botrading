"""
Tests unitarios para AssetIterator - T22: Iteración determinista de activos
Garantiza iteración ordenada y consistente de activos en cada ciclo
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock

# Importar el módulo a testear
from src.core.asset_iterator import (
    AssetIterator,
    AssetIterationError,
    Asset
)


class TestAssetIteratorInitialization:
    """Tests de inicialización del AssetIterator"""
    
    def test_initialization_with_valid_config(self):
        """Debe inicializar correctamente con configuración válida"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        
        assert iterator is not None
        assert len(iterator.get_enabled_assets()) == 2
    
    def test_initialization_with_config_file(self):
        """Debe inicializar correctamente desde archivo de configuración"""
        # Crear archivo temporal
        config_data = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": False},
                {"symbol": "USDJPY", "enabled": True}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            iterator = AssetIterator(config_path=temp_path)
            assert len(iterator.get_enabled_assets()) == 2
            assert iterator.get_enabled_assets()[0].symbol == "EURUSD"
            assert iterator.get_enabled_assets()[1].symbol == "USDJPY"
        finally:
            Path(temp_path).unlink()
    
    def test_initialization_without_config_raises_error(self):
        """Debe lanzar error si no se proporciona configuración"""
        with pytest.raises(AssetIterationError, match="config or config_path required"):
            AssetIterator()
    
    def test_initialization_with_invalid_config_file(self):
        """Debe lanzar error si el archivo de configuración no existe"""
        with pytest.raises(AssetIterationError, match="Config file not found"):
            AssetIterator(config_path="/path/that/does/not/exist.json")
    
    def test_initialization_with_invalid_json(self):
        """Debe lanzar error si el JSON es inválido"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with pytest.raises(AssetIterationError, match="Invalid JSON"):
                AssetIterator(config_path=temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_initialization_with_empty_assets_list(self):
        """Debe manejar lista de activos vacía"""
        config = {"assets": []}
        iterator = AssetIterator(config=config)
        assert len(iterator.get_enabled_assets()) == 0
    
    def test_initialization_with_all_disabled_assets(self):
        """Debe manejar caso donde todos los activos están deshabilitados"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": False},
                {"symbol": "GBPUSD", "enabled": False}
            ]
        }
        iterator = AssetIterator(config=config)
        assert len(iterator.get_enabled_assets()) == 0


class TestAssetDataclass:
    """Tests del dataclass Asset"""
    
    def test_asset_creation_with_all_fields(self):
        """Debe crear Asset con todos los campos"""
        asset = Asset(
            symbol="EURUSD",
            enabled=True,
            timeframes=["5M", "15M", "1H"],
            lot_size=0.01,
            max_positions=3
        )
        
        assert asset.symbol == "EURUSD"
        assert asset.enabled is True
        assert asset.timeframes == ["5M", "15M", "1H"]
        assert asset.lot_size == 0.01
        assert asset.max_positions == 3
    
    def test_asset_creation_with_minimal_fields(self):
        """Debe crear Asset con campos mínimos (solo symbol y enabled)"""
        asset = Asset(symbol="GBPUSD", enabled=False)
        
        assert asset.symbol == "GBPUSD"
        assert asset.enabled is False
        assert asset.timeframes is None
        assert asset.lot_size is None
        assert asset.max_positions is None
    
    def test_asset_to_dict(self):
        """Debe convertir Asset a diccionario"""
        asset = Asset(symbol="USDJPY", enabled=True, lot_size=0.02)
        asset_dict = asset.to_dict()
        
        assert asset_dict["symbol"] == "USDJPY"
        assert asset_dict["enabled"] is True
        assert asset_dict["lot_size"] == 0.02


class TestDeterministicIteration:
    """Tests de iteración determinista - CASO CRÍTICO"""
    
    def test_iteration_order_is_consistent(self):
        """Debe iterar activos en el mismo orden en múltiples ciclos"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": True},
                {"symbol": "USDJPY", "enabled": True},
                {"symbol": "AUDUSD", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        
        # Primera iteración
        first_cycle = [asset.symbol for asset in iterator]
        
        # Segunda iteración
        second_cycle = [asset.symbol for asset in iterator]
        
        # Tercera iteración
        third_cycle = [asset.symbol for asset in iterator]
        
        # Todas deben ser idénticas
        assert first_cycle == second_cycle == third_cycle
        assert first_cycle == ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    
    def test_iteration_skips_disabled_assets(self):
        """Debe omitir activos deshabilitados en la iteración"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": False},
                {"symbol": "USDJPY", "enabled": True},
                {"symbol": "AUDUSD", "enabled": False}
            ]
        }
        
        iterator = AssetIterator(config=config)
        symbols = [asset.symbol for asset in iterator]
        
        assert symbols == ["EURUSD", "USDJPY"]
        assert "GBPUSD" not in symbols
        assert "AUDUSD" not in symbols
    
    def test_iteration_with_for_loop(self):
        """Debe soportar iteración con for loop estándar"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        symbols = []
        
        for asset in iterator:
            symbols.append(asset.symbol)
        
        assert symbols == ["EURUSD", "GBPUSD"]
    
    def test_iteration_preserves_order_from_config(self):
        """Debe preservar el orden especificado en la configuración"""
        config = {
            "assets": [
                {"symbol": "ZZTEST", "enabled": True},
                {"symbol": "AATEST", "enabled": True},
                {"symbol": "MMTEST", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        symbols = [asset.symbol for asset in iterator]
        
        # Debe mantener orden ZZTEST, AATEST, MMTEST (no alfabético)
        assert symbols == ["ZZTEST", "AATEST", "MMTEST"]


class TestAssetRetrieval:
    """Tests de obtención de activos"""
    
    def test_get_enabled_assets_returns_list(self):
        """Debe retornar lista de activos habilitados"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": False},
                {"symbol": "USDJPY", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        enabled = iterator.get_enabled_assets()
        
        assert isinstance(enabled, list)
        assert len(enabled) == 2
        assert all(isinstance(asset, Asset) for asset in enabled)
        assert all(asset.enabled for asset in enabled)
    
    def test_get_all_assets_returns_all(self):
        """Debe retornar todos los activos (habilitados y deshabilitados)"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": False},
                {"symbol": "USDJPY", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        all_assets = iterator.get_all_assets()
        
        assert len(all_assets) == 3
        assert all_assets[0].symbol == "EURUSD"
        assert all_assets[1].symbol == "GBPUSD"
        assert all_assets[2].symbol == "USDJPY"
    
    def test_get_asset_by_symbol(self):
        """Debe obtener un activo específico por símbolo"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True, "lot_size": 0.01},
                {"symbol": "GBPUSD", "enabled": True, "lot_size": 0.02}
            ]
        }
        
        iterator = AssetIterator(config=config)
        asset = iterator.get_asset_by_symbol("GBPUSD")
        
        assert asset is not None
        assert asset.symbol == "GBPUSD"
        assert asset.lot_size == 0.02
    
    def test_get_asset_by_symbol_returns_none_if_not_found(self):
        """Debe retornar None si el símbolo no existe"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        asset = iterator.get_asset_by_symbol("NONEXISTENT")
        
        assert asset is None
    
    def test_get_asset_count(self):
        """Debe retornar conteo correcto de activos"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": False},
                {"symbol": "USDJPY", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        
        assert iterator.get_asset_count() == 3
        assert iterator.get_enabled_count() == 2


class TestAssetValidation:
    """Tests de validación de activos"""
    
    def test_validates_symbol_is_required(self):
        """Debe validar que symbol es obligatorio"""
        config = {
            "assets": [
                {"enabled": True}  # Falta symbol
            ]
        }
        
        with pytest.raises(AssetIterationError, match="symbol.*required"):
            AssetIterator(config=config)
    
    def test_validates_symbol_is_string(self):
        """Debe validar que symbol es string"""
        config = {
            "assets": [
                {"symbol": 123, "enabled": True}  # symbol no es string
            ]
        }
        
        with pytest.raises(AssetIterationError, match="symbol.*string"):
            AssetIterator(config=config)
    
    def test_validates_enabled_is_boolean(self):
        """Debe validar que enabled es boolean"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": "yes"}  # enabled no es bool
            ]
        }
        
        with pytest.raises(AssetIterationError, match="enabled.*boolean"):
            AssetIterator(config=config)
    
    def test_validates_duplicate_symbols(self):
        """Debe validar que no haya símbolos duplicados"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "EURUSD", "enabled": False}  # Duplicado
            ]
        }
        
        with pytest.raises(AssetIterationError, match="Duplicate symbol"):
            AssetIterator(config=config)


class TestAssetReloading:
    """Tests de recarga de configuración"""
    
    def test_reload_config_updates_assets(self):
        """Debe recargar configuración y actualizar activos"""
        config_data = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            iterator = AssetIterator(config_path=temp_path)
            assert len(iterator.get_enabled_assets()) == 1
            
            # Actualizar archivo
            new_config = {
                "assets": [
                    {"symbol": "EURUSD", "enabled": True},
                    {"symbol": "GBPUSD", "enabled": True}
                ]
            }
            
            with open(temp_path, 'w') as f:
                json.dump(new_config, f)
            
            # Recargar
            iterator.reload_config()
            assert len(iterator.get_enabled_assets()) == 2
        finally:
            Path(temp_path).unlink()
    
    def test_reload_preserves_statistics(self):
        """Debe preservar estadísticas tras recarga"""
        config_data = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            iterator = AssetIterator(config_path=temp_path)
            
            # Hacer algunas iteraciones
            for _ in iterator:
                pass
            for _ in iterator:
                pass
            
            stats = iterator.get_statistics()
            iterations_before = stats["total_iterations"]
            
            # Recargar
            iterator.reload_config()
            
            stats_after = iterator.get_statistics()
            assert stats_after["total_iterations"] == iterations_before
        finally:
            Path(temp_path).unlink()


class TestStatistics:
    """Tests de estadísticas de iteración"""
    
    def test_tracks_total_iterations(self):
        """Debe rastrear número total de iteraciones"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        
        # Primera iteración
        list(iterator)
        stats = iterator.get_statistics()
        assert stats["total_iterations"] == 1
        
        # Segunda iteración
        list(iterator)
        stats = iterator.get_statistics()
        assert stats["total_iterations"] == 2
    
    def test_tracks_assets_processed(self):
        """Debe rastrear activos procesados por iteración"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": True},
                {"symbol": "USDJPY", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        list(iterator)
        
        stats = iterator.get_statistics()
        assert stats["assets_processed_per_iteration"] == 3
    
    def test_clear_statistics(self):
        """Debe limpiar estadísticas"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        list(iterator)
        list(iterator)
        
        stats = iterator.get_statistics()
        assert stats["total_iterations"] == 2
        
        iterator.clear_statistics()
        stats = iterator.get_statistics()
        assert stats["total_iterations"] == 0


class TestIntegrationWithLogger:
    """Tests de integración con Logger (T39)"""
    
    def test_logs_iteration_start(self):
        """Debe loggear inicio de iteración"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True}
            ]
        }
        
        mock_logger = Mock()
        iterator = AssetIterator(config=config, logger=mock_logger)
        
        list(iterator)
        
        # Verificar que se llamó al logger
        assert mock_logger.info.called
    
    def test_logs_disabled_assets_skipped(self):
        """Debe loggear cuando se omiten activos deshabilitados"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": False}
            ]
        }
        
        mock_logger = Mock()
        iterator = AssetIterator(config=config, logger=mock_logger)
        
        list(iterator)
        
        # Verificar logging de activo omitido
        assert mock_logger.debug.called


class TestEdgeCases:
    """Tests de casos edge"""
    
    def test_handles_empty_iteration(self):
        """Debe manejar iteración sin activos habilitados"""
        config = {"assets": []}
        iterator = AssetIterator(config=config)
        
        result = list(iterator)
        assert result == []
    
    def test_reset_iteration_midway(self):
        """Debe poder reiniciar iteración a la mitad"""
        config = {
            "assets": [
                {"symbol": "EURUSD", "enabled": True},
                {"symbol": "GBPUSD", "enabled": True},
                {"symbol": "USDJPY", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        iter_obj = iter(iterator)
        
        # Obtener primeros 2 elementos
        next(iter_obj)
        next(iter_obj)
        
        # Nueva iteración desde el inicio
        symbols = [asset.symbol for asset in iterator]
        assert symbols == ["EURUSD", "GBPUSD", "USDJPY"]
    
    def test_handles_special_characters_in_symbols(self):
        """Debe manejar símbolos con caracteres especiales"""
        config = {
            "assets": [
                {"symbol": "EUR/USD", "enabled": True},
                {"symbol": "BTC-USD", "enabled": True}
            ]
        }
        
        iterator = AssetIterator(config=config)
        symbols = [asset.symbol for asset in iterator]
        assert symbols == ["EUR/USD", "BTC-USD"]
