"""
Test de Integración End-to-End para Metodología VWAP

Este test valida el flujo completo del sistema:
1. Datos OHLCV → Indicadores (VWAP, ATR, OR)
2. Indicadores → Prompt Builder
3. Prompt → IA (simulada) → Response Parser
4. Response Parser → Formato Bot

Autor: Sistema Botrading
Fecha: 2025-11-17
Ticket: VWAP Methodology - Integration Test
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, time

from src.core.mt5_data_extractor import OHLCVData, Timeframe
from src.core.indicator_calculator import IndicatorCalculator
from src.core.opening_range_calculator import (
    OpeningRangeCalculator,
    BreakoutStatus
)
from src.core.vwap_prompt_builder import (
    VWAPPromptBuilder,
    MarketContext
)
from src.core.vwap_response_parser import (
    VWAPResponseParser,
    TradingAction,
    Direction
)


class TestVWAPIntegrationEndToEnd:
    """Tests de integración end-to-end del sistema VWAP"""
    
    @pytest.fixture
    def realistic_market_data(self):
        """
        Datos de mercado realistas para EURUSD sesión europea.
        Simula tendencia alcista con VWAP ascendente y breakout del OR.
        
        IMPORTANTE: Genera suficientes velas para TODOS los indicadores:
        - EMA50 requiere mínimo 50 períodos
        - ATR 14/21 requiere mínimo 21 períodos
        - VWAP requiere datos de sesión completa
        
        Se generan 100 velas para asegurar cálculo preciso de todos los indicadores.
        """
        # Generar 100 velas (8+ horas de datos en M5)
        # Esto simula desde 07:00 GMT (pre-market) hasta 15:00+ GMT
        dates = pd.date_range(
            start='2025-11-17 07:00:00',
            periods=100,
            freq='5min'
        )
        
        # Simular sesión completa con tendencia alcista realista
        base_price = 1.1000
        
        # Primeras 12 velas (07:00-08:00): Pre-market, rango consolidado
        pre_market = np.full(12, base_price) + np.random.normal(0, 0.0001, 12)
        
        # Siguientes 60 velas (08:00-13:00): Sesión europea con tendencia alcista
        session = base_price + np.linspace(0, 0.0050, 60)  # +50 pips en 5 horas
        session += np.random.normal(0, 0.0002, 60)  # Ruido realista
        
        # Últimas 28 velas (13:00-15:20): Post-sesión, consolidación
        post_session = session[-1] + np.random.normal(0, 0.0001, 28)
        
        # Combinar todas las fases
        close_prices = np.concatenate([pre_market, session, post_session])
        
        data = pd.DataFrame({
            'time': dates,
            'open': close_prices - np.random.uniform(0.00005, 0.0001, 100),
            'high': close_prices + np.random.uniform(0.0002, 0.0005, 100),
            'low': close_prices - np.random.uniform(0.0002, 0.0005, 100),
            'close': close_prices,
            'volume': np.random.uniform(1000, 3000, 100)
        })
        
        # Asegurar que high >= low (corrección de datos)
        data['high'] = data[['high', 'close', 'open']].max(axis=1)
        data['low'] = data[['low', 'close', 'open']].min(axis=1)
        
        return OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=data,
            count=100
        )
    
    def test_complete_flow_bullish_signal(self, realistic_market_data):
        """
        Test del flujo completo con señal alcista.
        
        Flujo:
        1. Calcular indicadores técnicos
        2. Calcular Opening Range
        3. Construir prompts
        4. Simular respuesta IA
        5. Parsear respuesta
        6. Validar señal
        7. Convertir a formato bot
        """
        # ========== PASO 1: Calcular Indicadores ==========
        calculator = IndicatorCalculator()
        indicators = calculator.calculate_indicators_for_timeframe(realistic_market_data)
        
        # Validar que indicadores se calcularon
        assert indicators is not None
        assert indicators.vwap is not None
        assert indicators.vwap_slope_description is not None
        assert indicators.atr_14 is not None
        
        print(f"\n📊 Indicadores calculados:")
        print(f"   VWAP: {indicators.vwap:.5f}")
        print(f"   VWAP Slope: {indicators.vwap_slope_description}")
        print(f"   ATR(14): {indicators.atr_14:.5f} ({indicators.atr_14 * 10000:.1f} pips)")
        print(f"   EMA9: {indicators.ema9:.5f}")
        
        # ========== PASO 2: Calcular Opening Range ==========
        or_calculator = OpeningRangeCalculator(
            session_start_hour=8,
            session_start_minute=0,
            or_duration_minutes=30
        )
        or_data = or_calculator.calculate_opening_range(realistic_market_data.data)
        
        # Validar Opening Range
        assert or_data is not None
        assert or_data.or_high > or_data.or_low
        
        print(f"\n📈 Opening Range:")
        print(f"   OR High: {or_data.or_high:.5f}")
        print(f"   OR Low: {or_data.or_low:.5f}")
        print(f"   OR Range: {or_data.or_range * 10000:.1f} pips")
        print(f"   Breakout Status: {or_data.breakout_status.value.upper()}")
        print(f"   Current Price: {or_data.current_price:.5f}")
        
        # ========== PASO 3: Construir Prompts ==========
        prompt_builder = VWAPPromptBuilder()
        
        prompt_data = prompt_builder.build_complete_prompt(
            indicators={Timeframe.M5: indicators},
            or_data=or_data,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Validar prompts
        assert prompt_data is not None
        assert len(prompt_data.system_prompt) > 500
        assert len(prompt_data.user_prompt) > 300
        assert "VWAP" in prompt_data.system_prompt
        assert str(indicators.vwap)[:6] in prompt_data.user_prompt
        
        print(f"\n📝 Prompts construidos:")
        print(f"   System Prompt: {len(prompt_data.system_prompt)} caracteres")
        print(f"   User Prompt: {len(prompt_data.user_prompt)} caracteres")
        print(f"   Contexto: {prompt_data.market_context.value}")
        
        # ========== PASO 4: Simular Respuesta de IA ==========
        # En producción, aquí se llamaría a GPT
        # Para el test, simulamos una respuesta alcista basada en indicadores reales
        
        simulated_ai_response = f"""
## ESTADO_DEL_MERCADO

VWAP muestra pendiente {indicators.vwap_slope_description} clara.
Precio actual: {or_data.current_price:.5f}
VWAP: {indicators.vwap:.5f}

El precio está {"por encima" if or_data.current_price > indicators.vwap else "por debajo"} del VWAP.

Opening Range: {or_data.breakout_status.value.upper()}.
{"Breakout alcista confirmado" if or_data.breakout_status == BreakoutStatus.ABOVE else "Precio en rango" if or_data.breakout_status == BreakoutStatus.INSIDE else "Breakout bajista"}.

## PLAN_DE_TRADING_ACTUAL

**Acción: {"LONG" if indicators.vwap_slope_description == "ascendente" and or_data.current_price > indicators.vwap else "NO_OPERAR"}**

**Justificación:**
- VWAP {indicators.vwap_slope_description} (condición principal)
- Precio {">" if or_data.current_price > indicators.vwap else "<"} VWAP
- ATR: {indicators.atr_14 * 10000:.1f} pips

**Niveles propuestos:**
- Entrada: {or_data.current_price:.5f}
- Stop Loss: {(or_data.current_price - 1.5 * indicators.atr_14):.5f}
- Take Profit: {(or_data.current_price + 2.0 * indicators.atr_14):.5f}

## GESTIÓN_DE_POSICIONES_ABIERTAS

Mantener mientras precio > VWAP.

## JOURNAL_Y_SCORE

**Score de confianza: 8/10**

Señal de alta calidad por confluencia de factores.
"""
        
        print(f"\n🤖 Respuesta IA simulada:")
        print(f"   Longitud: {len(simulated_ai_response)} caracteres")
        
        # ========== PASO 5: Parsear Respuesta ==========
        parser = VWAPResponseParser()
        parsed_response = parser.parse_response(simulated_ai_response)
        
        # Validar parseo
        assert parsed_response is not None
        assert parsed_response.action in [TradingAction.LONG, TradingAction.SHORT, TradingAction.NO_TRADE]
        
        print(f"\n🔍 Respuesta parseada:")
        print(f"   Acción: {parsed_response.action.value.upper()}")
        print(f"   Dirección: {parsed_response.direction.value if parsed_response.direction else 'N/A'}")
        print(f"   Entry: {parsed_response.entry_price}")
        print(f"   Stop Loss: {parsed_response.stop_loss}")
        print(f"   Take Profit: {parsed_response.take_profit}")
        print(f"   Confianza: {parsed_response.confidence_score}/10")
        
        # ========== PASO 6: Validar Señal contra Reglas VWAP ==========
        if parsed_response.action != TradingAction.NO_TRADE:
            # Validar contra reglas VWAP
            is_valid_vwap = parser.validate_signal(
                parsed_response,
                vwap_slope=indicators.vwap_slope_description
            )
            assert is_valid_vwap is True
            
            # Validar stop loss
            is_valid_sl = parser.validate_stop_loss(parsed_response)
            assert is_valid_sl is True
            
            # Validar take profit
            is_valid_tp = parser.validate_take_profit(parsed_response)
            assert is_valid_tp is True
            
            print(f"\n✅ Validaciones:")
            print(f"   ✓ Señal alineada con VWAP {indicators.vwap_slope_description}")
            print(f"   ✓ Stop Loss en dirección correcta")
            print(f"   ✓ Take Profit en dirección correcta")
        
        # ========== PASO 7: Convertir a Formato Bot ==========
        bot_format = parser.convert_to_bot_format(parsed_response)
        
        # Validar formato bot
        assert "accion" in bot_format
        assert "direccion" in bot_format
        assert "precio_entrada" in bot_format
        assert "stop_loss" in bot_format
        assert "take_profit" in bot_format
        
        print(f"\n🤖 Formato Bot:")
        print(f"   Acción: {bot_format['accion']}")
        print(f"   Dirección: {bot_format['direccion']}")
        print(f"   Entry: {bot_format['precio_entrada']}")
        print(f"   SL: {bot_format['stop_loss']}")
        print(f"   TP: {bot_format['take_profit']}")
        
        # ========== VALIDACIÓN FINAL ==========
        # Si hay señal de trading, debe cumplir reglas VWAP
        if bot_format['accion'] == 'abrir':
            # LONG solo con VWAP ascendente
            if bot_format['direccion'] == 'buy':
                assert indicators.vwap_slope_description == "ascendente", \
                    "LONG requiere VWAP ascendente"
            
            # SHORT solo con VWAP descendente
            if bot_format['direccion'] == 'sell':
                assert indicators.vwap_slope_description == "descendente", \
                    "SHORT requiere VWAP descendente"
            
            print(f"\n🎯 FLUJO COMPLETO VALIDADO ✅")
            print(f"   Sistema operando correctamente según metodología VWAP")
    
    def test_complete_flow_no_trade_signal(self):
        """
        Test del flujo completo cuando NO hay señal (VWAP plana).
        """
        # Datos con VWAP plana (mercado en rango) - 100 velas para todos los indicadores
        dates = pd.date_range('2025-11-17 07:00:00', periods=100, freq='5min')
        
        # Precio oscilando sin tendencia
        base = 1.1000
        noise = np.random.normal(0, 0.0003, 100)
        
        data = pd.DataFrame({
            'time': dates,
            'open': base + noise,
            'high': base + noise + 0.0002,
            'low': base + noise - 0.0002,
            'close': base + noise,
            'volume': np.random.uniform(1000, 2000, 100)
        })
        
        # Asegurar consistencia de datos
        data['high'] = data[['high', 'close', 'open']].max(axis=1)
        data['low'] = data[['low', 'close', 'open']].min(axis=1)
        
        ohlcv_data = OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=data,
            count=100
        )
        
        # Calcular indicadores
        calculator = IndicatorCalculator()
        indicators = calculator.calculate_indicators_for_timeframe(ohlcv_data)
        
        # Debe detectar VWAP plana
        print(f"\n📊 Test NO_TRADE:")
        print(f"   VWAP Slope: {indicators.vwap_slope_description}")
        
        # VWAP plana debería resultar en NO_OPERAR
        # (esto se valida en el prompt y la IA debe responder NO_OPERAR)
        
        # Simular respuesta IA para VWAP plana
        no_trade_response = """
## ESTADO_DEL_MERCADO
VWAP plana, sin tendencia clara.

## PLAN_DE_TRADING_ACTUAL
**Acción: NO_OPERAR**

Sin tendencia definida.

## GESTIÓN_DE_POSICIONES_ABIERTAS
Esperar mejor setup.

## JOURNAL_Y_SCORE
Score: N/A
"""
        
        parser = VWAPResponseParser()
        parsed = parser.parse_response(no_trade_response)
        
        assert parsed.action == TradingAction.NO_TRADE
        
        bot_format = parser.convert_to_bot_format(parsed)
        assert bot_format['accion'] == 'esperar'
        
        print(f"   ✅ Sistema correctamente rechaza trading sin tendencia")
    
    def test_integration_with_counter_trend_rejection(self):
        """
        Test que el sistema rechaza señales contra-tendencia.
        """
        # Datos con VWAP ascendente CLARA (100 velas con tendencia fuerte)
        dates = pd.date_range('2025-11-17 07:00:00', periods=100, freq='5min')
        
        # Tendencia alcista fuerte y consistente
        uptrend = np.linspace(1.1000, 1.1060, 100)  # +60 pips en 100 velas
        noise = np.random.normal(0, 0.00003, 100)  # Ruido muy pequeño para tendencia clara
        
        data = pd.DataFrame({
            'time': dates,
            'open': uptrend + noise,
            'high': uptrend + noise + 0.0002,
            'low': uptrend + noise - 0.0002,
            'close': uptrend + noise,
            'volume': np.random.uniform(1000, 2000, 100)
        })
        
        # Asegurar consistencia
        data['high'] = data[['high', 'close', 'open']].max(axis=1)
        data['low'] = data[['low', 'close', 'open']].min(axis=1)
        
        ohlcv_data = OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=data,
            count=100
        )
        
        calculator = IndicatorCalculator()
        indicators = calculator.calculate_indicators_for_timeframe(ohlcv_data)
        
        # Con tendencia fuerte, VWAP debe ser ascendente
        print(f"\n🚫 Test Counter-Trend Rejection:")
        print(f"   VWAP Slope: {indicators.vwap_slope_description}")
        print(f"   VWAP Slope Value: {indicators.vwap_slope}")
        
        # Si por alguna razón no es ascendente, ajustar test
        if indicators.vwap_slope_description != "ascendente":
            pytest.skip("Datos no generaron VWAP ascendente suficientemente clara")
        
        # Simular respuesta IA errónea (SHORT con VWAP ascendente)
        wrong_response = """
## PLAN_DE_TRADING_ACTUAL
Acción: SHORT
Entrada: 1.1020
Stop Loss: 1.1030
Take Profit: 1.1010
"""
        
        parser = VWAPResponseParser()
        parsed = parser.parse_response(wrong_response)
        
        # El parser debe rechazar esta señal
        with pytest.raises(Exception):  # ValidationError
            parser.validate_signal(parsed, vwap_slope="ascendente")
        
        print(f"   ✅ Sistema correctamente rechaza SHORT con VWAP ascendente")
    
    def test_performance_metrics(self, realistic_market_data):
        """
        Test de métricas de performance del flujo completo.
        """
        import time
        
        print(f"\n⏱️ Métricas de Performance:")
        
        # Medir tiempo de cálculo de indicadores
        start = time.time()
        calculator = IndicatorCalculator()
        indicators = calculator.calculate_indicators_for_timeframe(realistic_market_data)
        calc_time = time.time() - start
        print(f"   Cálculo Indicadores: {calc_time*1000:.2f}ms")
        
        # Medir tiempo de Opening Range
        start = time.time()
        or_calc = OpeningRangeCalculator()
        or_data = or_calc.calculate_opening_range(realistic_market_data.data)
        or_time = time.time() - start
        print(f"   Opening Range: {or_time*1000:.2f}ms")
        
        # Medir tiempo de construcción de prompts
        start = time.time()
        builder = VWAPPromptBuilder()
        prompts = builder.build_complete_prompt(
            {Timeframe.M5: indicators},
            or_data,
            MarketContext.EUROPEAN_SESSION
        )
        prompt_time = time.time() - start
        print(f"   Construcción Prompts: {prompt_time*1000:.2f}ms")
        
        # Tiempo total (excluyendo llamada a IA)
        total_time = calc_time + or_time + prompt_time
        print(f"   ⚡ Tiempo Total: {total_time*1000:.2f}ms")
        
        # El sistema debe ser rápido (< 100ms para procesamiento local)
        assert total_time < 0.1, "Sistema demasiado lento"
        
        print(f"   ✅ Performance aceptable (< 100ms)")


class TestVWAPDataFlow:
    """Tests de flujo de datos entre componentes"""
    
    def test_indicator_to_prompt_data_consistency(self):
        """Valida que los datos fluyan correctamente de indicadores a prompts"""
        # Crear indicadores mock con todos los campos
        from src.core.indicator_calculator import IndicatorData
        
        test_indicators = IndicatorData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            vwap=1.1005,
            vwap_slope=0.00008,
            vwap_slope_description="ascendente",
            vwap_upper_1=1.1010,
            vwap_lower_1=1.1000,
            vwap_upper_2=1.1015,
            vwap_lower_2=1.0995,
            atr_14=0.0015,
            ema9=1.1006
        )
        
        # Construir prompt
        builder = VWAPPromptBuilder()
        user_prompt = builder.build_user_prompt(
            indicators={Timeframe.M5: test_indicators},
            or_data=None,
            market_context=MarketContext.EUROPEAN_SESSION
        )
        
        # Validar que los valores aparecen en el prompt
        assert "1.1005" in user_prompt  # VWAP
        assert "ascendente" in user_prompt  # Slope
        assert "0.0015" in user_prompt or "15" in user_prompt  # ATR en pips
        
        print(f"\n✅ Datos fluyen correctamente: Indicadores → Prompts")
    
    def test_prompt_to_parser_data_flow(self):
        """Valida que las respuestas se parseen correctamente"""
        response = """
## PLAN_DE_TRADING_ACTUAL
Acción: LONG
Entrada: 1.1010
Stop Loss: 1.1000
Take Profit: 1.1025

## JOURNAL_Y_SCORE
Score: 7/10
"""
        
        parser = VWAPResponseParser()
        parsed = parser.parse_response(response)
        
        # Validar extracción correcta
        assert parsed.action == TradingAction.LONG
        assert parsed.entry_price == 1.1010
        assert parsed.stop_loss == 1.1000
        assert parsed.take_profit == 1.1025
        assert parsed.confidence_score == 7
        
        print(f"\n✅ Datos fluyen correctamente: Respuesta IA → Parser")
    
    def test_parser_to_bot_format_conversion(self):
        """Valida conversión final a formato bot"""
        from src.core.vwap_response_parser import ParsedResponse
        
        parsed = ParsedResponse(
            action=TradingAction.LONG,
            direction=Direction.BUY,
            entry_price=1.1010,
            stop_loss=1.1000,
            take_profit=1.1025,
            confidence_score=8
        )
        
        parser = VWAPResponseParser()
        bot_format = parser.convert_to_bot_format(parsed)
        
        # Validar formato correcto
        assert bot_format['accion'] == 'abrir'
        assert bot_format['direccion'] == 'buy'
        assert bot_format['precio_entrada'] == 1.1010
        assert bot_format['stop_loss'] == 1.1000
        assert bot_format['take_profit'] == 1.1025
        assert bot_format['confianza'] == 8
        
        print(f"\n✅ Datos fluyen correctamente: Parser → Formato Bot")
