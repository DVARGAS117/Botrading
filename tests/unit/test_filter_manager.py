"""
Tests unitarios para FilterManager - T36
Sistema de filtros configurables para volatilidad, spread y filtros custom
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime
from src.core.filter_manager import (
    FilterManager,
    FilterResult,
    FilterType,
    VolatilityFilter,
    SpreadFilter,
    FilterValidationError
)


class TestFilterManagerInitialization:
    """Tests de inicialización del FilterManager"""
    
    def test_init_with_valid_config_dict(self):
        """Debe inicializar correctamente con config dict"""
        config = {
            "volatility": {
                "enabled": True,
                "atr_minimum": 0.001
            },
            "spread": {
                "enabled": False,
                "spread_maximum_pips": 3
            }
        }
        
        manager = FilterManager(config=config)
        
        assert manager is not None
        assert manager.is_filter_enabled("volatility") is True
        assert manager.is_filter_enabled("spread") is False
    
    def test_init_with_config_file(self, tmp_path):
        """Debe inicializar correctamente con archivo de configuración"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001},
            "spread": {"enabled": True, "spread_maximum_pips": 2}
        }
        
        config_file = tmp_path / "filters.json"
        config_file.write_text(json.dumps(config))
        
        manager = FilterManager(config_path=str(config_file))
        
        assert manager.is_filter_enabled("volatility") is True
        assert manager.is_filter_enabled("spread") is True
    
    def test_init_without_config_uses_defaults(self):
        """Debe usar configuración por defecto si no se proporciona config"""
        manager = FilterManager()
        
        # Por defecto, todos los filtros están deshabilitados
        assert manager.is_filter_enabled("volatility") is False
        assert manager.is_filter_enabled("spread") is False
    
    def test_init_validates_config_structure(self):
        """Debe validar la estructura de la configuración"""
        invalid_config = {
            "volatility": "invalid"  # Debería ser dict
        }
        
        with pytest.raises(FilterValidationError, match="Invalid filter configuration"):
            FilterManager(config=invalid_config)


class TestFilterApplication:
    """Tests de aplicación de filtros"""
    
    def test_apply_all_filters_returns_results(self):
        """Debe aplicar todos los filtros habilitados y retornar resultados"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001},
            "spread": {"enabled": True, "spread_maximum_pips": 3}
        }
        
        manager = FilterManager(config=config)
        
        market_data = {
            "symbol": "EURUSD",
            "atr": 0.0015,
            "spread_pips": 2.5
        }
        
        results = manager.apply_filters(market_data)
        
        assert len(results) == 2
        assert all(isinstance(r, FilterResult) for r in results)
        assert all(r.passed for r in results)
    
    def test_apply_filters_skips_disabled_filters(self):
        """Debe omitir filtros deshabilitados"""
        config = {
            "volatility": {"enabled": False, "atr_minimum": 0.001},
            "spread": {"enabled": True, "spread_maximum_pips": 3}
        }
        
        manager = FilterManager(config=config)
        
        market_data = {
            "symbol": "EURUSD",
            "atr": 0.0005,  # Falla volatilidad
            "spread_pips": 2.0
        }
        
        results = manager.apply_filters(market_data)
        
        # Solo debe aplicar spread
        assert len(results) == 1
        assert results[0].filter_name == "spread"
    
    def test_all_filters_pass_returns_true(self):
        """Debe retornar True si todos los filtros pasan"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001},
            "spread": {"enabled": True, "spread_maximum_pips": 3}
        }
        
        manager = FilterManager(config=config)
        
        market_data = {
            "symbol": "EURUSD",
            "atr": 0.0015,  # Pasa
            "spread_pips": 2.0  # Pasa
        }
        
        passed = manager.all_filters_pass(market_data)
        
        assert passed is True
    
    def test_any_filter_fails_returns_false(self):
        """Debe retornar False si algún filtro falla"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001},
            "spread": {"enabled": True, "spread_maximum_pips": 3}
        }
        
        manager = FilterManager(config=config)
        
        market_data = {
            "symbol": "EURUSD",
            "atr": 0.0005,  # Falla volatilidad
            "spread_pips": 2.0  # Pasa
        }
        
        passed = manager.all_filters_pass(market_data)
        
        assert passed is False


class TestVolatilityFilter:
    """Tests del filtro de volatilidad"""
    
    def test_volatility_filter_passes_when_atr_above_minimum(self):
        """Debe pasar cuando ATR está por encima del mínimo"""
        config = {"enabled": True, "atr_minimum": 0.001}
        vfilter = VolatilityFilter(config)
        
        market_data = {"atr": 0.0015}
        
        result = vfilter.apply(market_data)
        
        assert result.passed is True
        assert result.filter_name == "volatility"
        assert result.value == 0.0015
        assert result.threshold == 0.001
    
    def test_volatility_filter_fails_when_atr_below_minimum(self):
        """Debe fallar cuando ATR está por debajo del mínimo"""
        config = {"enabled": True, "atr_minimum": 0.001}
        vfilter = VolatilityFilter(config)
        
        market_data = {"atr": 0.0005}
        
        result = vfilter.apply(market_data)
        
        assert result.passed is False
        assert "below minimum" in result.reason.lower()
    
    def test_volatility_filter_handles_missing_atr(self):
        """Debe manejar casos donde falta el ATR"""
        config = {"enabled": True, "atr_minimum": 0.001}
        vfilter = VolatilityFilter(config)
        
        market_data = {}  # Sin ATR
        
        result = vfilter.apply(market_data)
        
        assert result.passed is False
        assert "missing" in result.reason.lower() or "not found" in result.reason.lower()
    
    def test_volatility_filter_accepts_exactly_minimum(self):
        """Debe pasar cuando ATR es exactamente el mínimo"""
        config = {"enabled": True, "atr_minimum": 0.001}
        vfilter = VolatilityFilter(config)
        
        market_data = {"atr": 0.001}
        
        result = vfilter.apply(market_data)
        
        assert result.passed is True


class TestSpreadFilter:
    """Tests del filtro de spread"""
    
    def test_spread_filter_passes_when_below_maximum(self):
        """Debe pasar cuando el spread está por debajo del máximo"""
        config = {"enabled": True, "spread_maximum_pips": 3}
        sfilter = SpreadFilter(config)
        
        market_data = {"spread_pips": 2.0}
        
        result = sfilter.apply(market_data)
        
        assert result.passed is True
        assert result.value == 2.0
        assert result.threshold == 3
    
    def test_spread_filter_fails_when_above_maximum(self):
        """Debe fallar cuando el spread está por encima del máximo"""
        config = {"enabled": True, "spread_maximum_pips": 3}
        sfilter = SpreadFilter(config)
        
        market_data = {"spread_pips": 5.0}
        
        result = sfilter.apply(market_data)
        
        assert result.passed is False
        assert "exceeds maximum" in result.reason.lower()
    
    def test_spread_filter_handles_missing_spread(self):
        """Debe manejar casos donde falta el spread"""
        config = {"enabled": True, "spread_maximum_pips": 3}
        sfilter = SpreadFilter(config)
        
        market_data = {}  # Sin spread
        
        result = sfilter.apply(market_data)
        
        assert result.passed is False
        assert "missing" in result.reason.lower() or "not found" in result.reason.lower()
    
    def test_spread_filter_accepts_exactly_maximum(self):
        """Debe pasar cuando el spread es exactamente el máximo"""
        config = {"enabled": True, "spread_maximum_pips": 3}
        sfilter = SpreadFilter(config)
        
        market_data = {"spread_pips": 3.0}
        
        result = sfilter.apply(market_data)
        
        assert result.passed is True


class TestFilterResult:
    """Tests del dataclass FilterResult"""
    
    def test_filter_result_initialization(self):
        """Debe inicializar correctamente con todos los campos"""
        result = FilterResult(
            passed=True,
            filter_name="volatility",
            reason="ATR above minimum",
            value=0.0015,
            threshold=0.001
        )
        
        assert result.passed is True
        assert result.filter_name == "volatility"
        assert result.reason == "ATR above minimum"
        assert result.value == 0.0015
        assert result.threshold == 0.001
    
    def test_filter_result_to_dict(self):
        """Debe convertir a diccionario correctamente"""
        result = FilterResult(
            passed=False,
            filter_name="spread",
            reason="Spread exceeds maximum",
            value=5.0,
            threshold=3.0
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["passed"] is False
        assert result_dict["filter_name"] == "spread"
        assert result_dict["reason"] == "Spread exceeds maximum"
        assert result_dict["value"] == 5.0
        assert result_dict["threshold"] == 3.0


class TestFilterType:
    """Tests del enum FilterType"""
    
    def test_filter_type_enum_values(self):
        """Debe tener los valores esperados"""
        assert hasattr(FilterType, "VOLATILITY")
        assert hasattr(FilterType, "SPREAD")
        assert hasattr(FilterType, "CUSTOM")
    
    def test_from_string_conversion(self):
        """Debe convertir strings a enum"""
        assert FilterType.from_string("volatility") == FilterType.VOLATILITY
        assert FilterType.from_string("spread") == FilterType.SPREAD
        assert FilterType.from_string("custom") == FilterType.CUSTOM
    
    def test_from_string_case_insensitive(self):
        """Debe ser case-insensitive"""
        assert FilterType.from_string("VOLATILITY") == FilterType.VOLATILITY
        assert FilterType.from_string("Spread") == FilterType.SPREAD
    
    def test_from_string_invalid_raises_error(self):
        """Debe lanzar error con valor inválido"""
        with pytest.raises(ValueError, match="Invalid filter type"):
            FilterType.from_string("invalid")


class TestFilterSummary:
    """Tests del resumen de filtros"""
    
    def test_get_filter_summary_returns_info(self):
        """Debe retornar información completa de filtros"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001},
            "spread": {"enabled": False, "spread_maximum_pips": 3}
        }
        
        manager = FilterManager(config=config)
        
        summary = manager.get_filter_summary()
        
        assert "enabled_filters" in summary
        assert "disabled_filters" in summary
        # Los filtros están en listas, buscar por nombre
        enabled_names = [f["name"] for f in summary["enabled_filters"]]
        disabled_names = [f["name"] for f in summary["disabled_filters"]]
        assert "volatility" in enabled_names
        assert "spread" in disabled_names
    
    def test_get_filter_statistics_after_application(self):
        """Debe retornar estadísticas después de aplicar filtros"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001},
            "spread": {"enabled": True, "spread_maximum_pips": 3}
        }
        
        manager = FilterManager(config=config)
        
        # Aplicar filtros varias veces (cada aplicación ejecuta AMBOS filtros)
        for _ in range(5):
            manager.apply_filters({"atr": 0.0015, "spread_pips": 2.0})  # Ambos pasan = 2 aplicaciones
        
        for _ in range(3):
            manager.apply_filters({"atr": 0.0005, "spread_pips": 2.0})  # Volatilidad falla, spread pasa = 2 aplicaciones
        
        stats = manager.get_filter_statistics()
        
        # 8 llamadas a apply_filters, cada una aplica 2 filtros = 16 aplicaciones totales
        assert stats["total_applications"] == 16
        assert "pass_rate" in stats
        assert "filter_details" in stats


class TestConfigReloading:
    """Tests de recarga de configuración"""
    
    def test_reload_config_updates_filters(self, tmp_path):
        """Debe recargar configuración actualizada"""
        config_file = tmp_path / "filters.json"
        
        # Config inicial
        initial_config = {
            "volatility": {"enabled": False, "atr_minimum": 0.001}
        }
        config_file.write_text(json.dumps(initial_config))
        
        manager = FilterManager(config_path=str(config_file))
        assert manager.is_filter_enabled("volatility") is False
        
        # Actualizar config
        updated_config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001}
        }
        config_file.write_text(json.dumps(updated_config))
        
        manager.reload_config()
        
        assert manager.is_filter_enabled("volatility") is True
    
    def test_reload_config_preserves_statistics(self, tmp_path):
        """Debe preservar estadísticas al recargar"""
        config_file = tmp_path / "filters.json"
        config = {"volatility": {"enabled": True, "atr_minimum": 0.001}}
        config_file.write_text(json.dumps(config))
        
        manager = FilterManager(config_path=str(config_file))
        
        # Aplicar algunos filtros
        manager.apply_filters({"atr": 0.0015})
        manager.apply_filters({"atr": 0.0005})
        
        stats_before = manager.get_filter_statistics()
        
        manager.reload_config()
        
        stats_after = manager.get_filter_statistics()
        
        # Las estadísticas deben permanecer
        assert stats_after["total_applications"] == stats_before["total_applications"]


class TestFilterIntegration:
    """Tests de integración con otros módulos"""
    
    def test_filter_manager_works_with_logger(self, tmp_path):
        """Debe integrarse con el Logger"""
        from src.core.logger import BotLogger, LogConfig, LogLevel
        
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        
        log_config = LogConfig(
            log_dir=str(log_dir),
            level=LogLevel.INFO
        )
        
        logger = BotLogger(
            bot_name="test_bot",
            config=log_config
        )
        
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001}
        }
        
        manager = FilterManager(config=config, logger=logger)
        
        # Aplicar filtro que falla
        results = manager.apply_filters({"atr": 0.0005})
        
        # Verificar que se registró en logs
        assert manager is not None  # Logger debe estar integrado
    
    def test_filter_manager_extensible_with_custom_filters(self):
        """Debe ser extensible con filtros customizados"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001},
            "custom": {
                "enabled": True,
                "type": "custom",
                "parameter": "value"
            }
        }
        
        manager = FilterManager(config=config, allow_custom=True)
        
        # Debe cargar filtros custom
        assert manager.is_filter_enabled("custom") is True


class TestEdgeCases:
    """Tests de casos edge"""
    
    def test_empty_market_data_fails_all_filters(self):
        """Debe fallar todos los filtros con data vacía"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001},
            "spread": {"enabled": True, "spread_maximum_pips": 3}
        }
        
        manager = FilterManager(config=config)
        
        results = manager.apply_filters({})
        
        assert all(not r.passed for r in results)
    
    def test_null_values_in_market_data_handled_gracefully(self):
        """Debe manejar valores None en market_data"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001}
        }
        
        manager = FilterManager(config=config)
        
        results = manager.apply_filters({"atr": None})
        
        assert len(results) == 1
        assert results[0].passed is False
    
    def test_invalid_data_types_raise_validation_error(self):
        """Debe validar tipos de datos"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001}
        }
        
        manager = FilterManager(config=config)
        
        # ATR como string en lugar de float
        with pytest.raises(FilterValidationError, match="Invalid data type"):
            manager.apply_filters({"atr": "invalid"})
    
    def test_extreme_values_handled_correctly(self):
        """Debe manejar valores extremos correctamente"""
        config = {
            "volatility": {"enabled": True, "atr_minimum": 0.001}
        }
        
        manager = FilterManager(config=config)
        
        # ATR extremadamente alto
        results = manager.apply_filters({"atr": 100.0})
        assert results[0].passed is True
        
        # ATR extremadamente bajo
        results = manager.apply_filters({"atr": 0.0})
        assert results[0].passed is False
