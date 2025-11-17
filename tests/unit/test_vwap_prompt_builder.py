"""
Tests unitarios para VWAP Prompt Builder

Tests para construcción de prompts especializados para metodología VWAP.
El sistema genera prompts que combinan indicadores técnicos, velas y contexto
de mercado en formato optimizado para IA.

Autor: Sistema Botrading
Fecha: 2025-11-17
Ticket: VWAP Methodology - Prompt Builder System
"""

import pytest
from datetime import datetime
from src.core.vwap_prompt_builder import (
    VWAPPromptBuilder,
    VWAPPromptData,
    MarketContext
)
from src.core.indicator_calculator import IndicatorData, TimeframeIndicators
from src.core.opening_range_calculator import OpeningRangeData, BreakoutStatus
from src.core.mt5_data_extractor import Timeframe
from datetime import time


class TestVWAPPromptBuilder:
    """Tests para construcción de prompts VWAP"""
    
    @pytest.fixture
    def builder(self):
        """Fixture del constructor de prompts"""
        return VWAPPromptBuilder()
    
    @pytest.fixture
    def sample_indicator_data(self):
        """Datos de indicadores de ejemplo"""
        return IndicatorData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            ema9=1.1005,
            ema20=1.1000,
            ema50=1.0995,
            rsi=55.0,
            macd=0.0002,
            signal=0.0001,
            histogram=0.0001,
            volume_avg=1500.0,
            vwap=1.1003,
            vwap_slope=0.00008,
            vwap_slope_description="ascendente",
            vwap_upper_1=1.1008,
            vwap_lower_1=1.0998,
            vwap_upper_2=1.1013,
            vwap_lower_2=1.0993,
            atr_14=0.0015,
            atr_21=0.0018
        )
    
    @pytest.fixture
    def sample_or_data(self):
        """Datos de Opening Range de ejemplo"""
        return OpeningRangeData(
            or_high=1.1010,
            or_low=1.0995,
            or_range=0.0015,
            or_midpoint=1.10025,
            current_price=1.1005,
            breakout_status=BreakoutStatus.INSIDE,
            distance_from_or_high=0.0005,
            distance_from_or_low=0.0010,
            session_start=time(8, 0),
            or_duration_minutes=30
        )
    
    def test_build_system_prompt(self, builder):
        """Test construcción de system prompt (fijo)"""
        # Act
        system_prompt = builder.build_system_prompt()
        
        # Assert
        assert system_prompt is not None
        assert len(system_prompt) > 0
        
        # Debe contener keywords de metodología VWAP
        assert "VWAP" in system_prompt
        assert "tendencia" in system_prompt.lower() or "trend" in system_prompt.lower()
        assert "sesión" in system_prompt.lower() or "session" in system_prompt.lower()
    
    def test_system_prompt_structure(self, builder):
        """Test estructura del system prompt"""
        # Act
        system_prompt = builder.build_system_prompt()
        
        # Assert - Debe tener secciones clave
        assert "metodología" in system_prompt.lower() or "methodology" in system_prompt.lower()
        assert "EURUSD" in system_prompt or "EUR/USD" in system_prompt
        assert "08:00" in system_prompt or "8:00" in system_prompt  # Horario sesión
    
    def test_build_user_prompt_basic(self, builder, sample_indicator_data, sample_or_data):
        """Test construcción básica de user prompt"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert
        assert user_prompt is not None
        assert len(user_prompt) > 0
    
    def test_user_prompt_includes_vwap(self, builder, sample_indicator_data, sample_or_data):
        """Test que user prompt incluye datos VWAP"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert
        assert "VWAP" in user_prompt or "vwap" in user_prompt
        assert "1.1003" in user_prompt  # Valor de VWAP
        assert "ascendente" in user_prompt  # Slope description
    
    def test_user_prompt_includes_vwap_bands(self, builder, sample_indicator_data, sample_or_data):
        """Test que user prompt incluye bandas VWAP"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert
        assert "banda" in user_prompt.lower() or "band" in user_prompt.lower()
        # Debe incluir valores de bandas
        assert "1.1008" in user_prompt or "1.0998" in user_prompt
    
    def test_user_prompt_includes_opening_range(self, builder, sample_indicator_data, sample_or_data):
        """Test que user prompt incluye Opening Range"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert
        assert "Opening Range" in user_prompt or "OR" in user_prompt
        assert "1.1010" in user_prompt  # OR high
        assert "1.0995" in user_prompt  # OR low
        assert "INSIDE" in user_prompt or "inside" in user_prompt  # Breakout status
    
    def test_user_prompt_includes_atr(self, builder, sample_indicator_data, sample_or_data):
        """Test que user prompt incluye ATR"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert
        assert "ATR" in user_prompt
        assert "0.0015" in user_prompt or "0.0018" in user_prompt
    
    def test_user_prompt_includes_ema(self, builder, sample_indicator_data, sample_or_data):
        """Test que user prompt incluye EMAs"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert
        assert "EMA" in user_prompt or "ema" in user_prompt
        assert "1.1005" in user_prompt  # EMA9
    
    def test_user_prompt_market_context_european(self, builder, sample_indicator_data, sample_or_data):
        """Test contexto de mercado: sesión europea"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert
        assert "europea" in user_prompt.lower() or "european" in user_prompt.lower()
    
    def test_user_prompt_market_context_premarket(self, builder, sample_indicator_data, sample_or_data):
        """Test contexto de mercado: pre-market"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.PRE_MARKET
        )
        
        # Assert
        assert "pre" in user_prompt.lower() or "apertura" in user_prompt.lower()
    
    def test_build_complete_prompt_data(self, builder, sample_indicator_data, sample_or_data):
        """Test construcción de VWAPPromptData completo"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act
        prompt_data = builder.build_complete_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert
        assert isinstance(prompt_data, VWAPPromptData)
        assert prompt_data.system_prompt is not None
        assert prompt_data.user_prompt is not None
        assert prompt_data.timestamp is not None
        assert prompt_data.market_context == MarketContext.EUROPEAN_SESSION
    
    def test_prompt_formatting_consistency(self, builder, sample_indicator_data, sample_or_data):
        """Test consistencia de formato entre múltiples generaciones"""
        # Arrange
        indicators = {Timeframe.M5: sample_indicator_data}
        
        # Act - Generar dos veces
        prompt1 = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        prompt2 = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert - Formato debe ser idéntico (excluyendo timestamps)
        # Contamos secciones clave
        sections_1 = prompt1.count("###") + prompt1.count("##")
        sections_2 = prompt2.count("###") + prompt2.count("##")
        
        assert sections_1 == sections_2
    
    def test_prompt_with_multiple_timeframes(self, builder, sample_indicator_data, sample_or_data):
        """Test prompt con múltiples timeframes"""
        # Arrange
        indicators = {
            Timeframe.M1: sample_indicator_data,
            Timeframe.M5: sample_indicator_data,
            Timeframe.H1: sample_indicator_data
        }
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=sample_or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert - Debe incluir los tres timeframes
        assert "M1" in user_prompt or "1M" in user_prompt
        assert "M5" in user_prompt or "5M" in user_prompt
        assert "H1" in user_prompt or "1H" in user_prompt
    
    def test_prompt_respects_vwap_methodology(self, builder):
        """Test que prompt respeta principios de metodología VWAP"""
        # Act
        system_prompt = builder.build_system_prompt()
        
        # Assert - Debe enfatizar trend-following, NO counter-trend
        system_lower = system_prompt.lower()
        
        # Debe mencionar seguimiento de tendencia
        assert any(word in system_lower for word in ["tendencia", "trend", "dirección"])
        
        # NO debe promover counter-trend trading
        assert "reversión" not in system_lower or "contra" not in system_lower


class TestVWAPPromptEdgeCases:
    """Tests de casos edge para VWAP Prompt Builder"""
    
    @pytest.fixture
    def builder(self):
        return VWAPPromptBuilder()
    
    def test_prompt_with_missing_or_data(self, builder):
        """Test construcción de prompt sin datos de OR"""
        # Arrange
        indicators = {
            Timeframe.M5: IndicatorData(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                vwap=1.1000,
                vwap_slope=0.0001,
                vwap_slope_description="ascendente"
            )
        }
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=None,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert - Debe generar prompt sin crashear
        assert user_prompt is not None
        assert "VWAP" in user_prompt or "vwap" in user_prompt
    
    def test_prompt_with_flat_vwap(self, builder):
        """Test prompt con VWAP plana"""
        # Arrange
        indicators = {
            Timeframe.M5: IndicatorData(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                vwap=1.1000,
                vwap_slope=0.00001,  # Muy pequeña
                vwap_slope_description="plana"
            )
        }
        
        or_data = OpeningRangeData(
            or_high=1.1005,
            or_low=1.0995,
            or_range=0.0010,
            or_midpoint=1.1000,
            current_price=1.1000,
            breakout_status=BreakoutStatus.INSIDE,
            distance_from_or_high=0.0005,
            distance_from_or_low=0.0005,
            session_start=time(8, 0),
            or_duration_minutes=30
        )
        
        # Act
        user_prompt = builder.build_user_prompt(
            indicators=indicators,
            or_data=or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert
        assert "plana" in user_prompt or "flat" in user_prompt.lower()
    
    def test_prompt_length_reasonable(self, builder):
        """Test que el prompt no sea excesivamente largo"""
        # Arrange
        indicators = {
            Timeframe.M1: IndicatorData(
                symbol="EURUSD",
                timeframe=Timeframe.M1,
                vwap=1.1000
            ),
            Timeframe.M5: IndicatorData(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                vwap=1.1001
            ),
            Timeframe.H1: IndicatorData(
                symbol="EURUSD",
                timeframe=Timeframe.H1,
                vwap=1.1002
            )
        }
        
        or_data = OpeningRangeData(
            or_high=1.1005,
            or_low=1.0995,
            or_range=0.0010,
            or_midpoint=1.1000,
            current_price=1.1000,
            breakout_status=BreakoutStatus.INSIDE,
            distance_from_or_high=0.0005,
            distance_from_or_low=0.0005,
            session_start=time(8, 0),
            or_duration_minutes=30
        )
        
        # Act
        prompt_data = builder.build_complete_prompt(
            indicators=indicators,
            or_data=or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Assert - Prompts deben estar en rango razonable
        # System prompt: 500-5000 chars
        assert 500 < len(prompt_data.system_prompt) < 5000
        
        # User prompt: 300-3000 chars (depende de datos)
        assert 300 < len(prompt_data.user_prompt) < 3000
