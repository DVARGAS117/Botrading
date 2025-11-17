"""
VWAPPromptBuilder - Construcción de prompts especializados para metodología VWAP.

Este módulo genera prompts optimizados que combinan:
- System Prompt: Metodología VWAP completa (fijo)
- User Prompt: Indicadores actuales + contexto de mercado (variable)

El objetivo es proporcionar a la IA todo el contexto necesario para tomar
decisiones de trading alineadas con la metodología VWAP trend-following.

Autor: Sistema Botrading
Fecha: 2025-11-17
Ticket: VWAP Methodology - Prompt Builder System
"""
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
from datetime import datetime

from src.core.indicator_calculator import IndicatorData
from src.core.opening_range_calculator import OpeningRangeData
from src.core.mt5_data_extractor import Timeframe


class MarketContext(Enum):
    """Contexto de mercado para construcción de prompt"""
    PRE_MARKET = "pre_market"  # Antes de apertura europea
    EUROPEAN_SESSION = "european_session"  # Sesión europea activa
    POST_OR = "post_or"  # Después de Opening Range
    END_OF_SESSION = "end_of_session"  # Cerca del cierre


@dataclass
class VWAPPromptData:
    """
    Datos completos del prompt VWAP.
    
    Attributes:
        system_prompt: Prompt del sistema (metodología VWAP)
        user_prompt: Prompt del usuario (indicadores + contexto)
        timestamp: Timestamp de generación
        market_context: Contexto de mercado actual
    """
    system_prompt: str
    user_prompt: str
    timestamp: datetime
    market_context: MarketContext


class VWAPPromptBuilder:
    """
    Constructor de prompts para metodología VWAP intradía.
    
    Genera prompts especializados que guían a la IA para:
    - Operar SOLO a favor de tendencia VWAP
    - Respetar Opening Range como nivel clave
    - Usar bandas VWAP para timing de entradas
    - Gestionar riesgo con ATR
    """
    
    def __init__(self):
        """Inicializa el constructor de prompts"""
        pass
    
    def build_system_prompt(self) -> str:
        """
        Construye el system prompt (fijo) con metodología VWAP completa.
        
        Returns:
            System prompt en formato markdown
        """
        return """# Metodología VWAP Intradía - Sistema de Trading Trend-Following

Eres un asistente de trading especializado en metodología VWAP intradía para EURUSD.
Tu objetivo es analizar el mercado y proporcionar señales de trading basadas EXCLUSIVAMENTE
en seguimiento de tendencia (trend-following), NUNCA en reversiones.

## Principios Fundamentales

### 1. VWAP como Ancla de Tendencia
- El VWAP de sesión es el indicador PRINCIPAL del sistema
- La pendiente del VWAP determina el bias direccional:
  * **VWAP ascendente**: SOLO buscar compras
  * **VWAP descendente**: SOLO buscar ventas
  * **VWAP plana**: NO operar (sin tendencia definida)

### 2. Operativa NUNCA Counter-Trend
- PROHIBIDO operar contra la dirección del VWAP
- NO buscar reversiones en niveles de soporte/resistencia
- NO anticipar cambios de tendencia
- Si el VWAP sube, NO vender; si baja, NO comprar

### 3. Bandas VWAP para Timing
- Bandas ±1σ y ±2σ definen zonas de valor
- **Entradas en pullbacks**: Precio retrocede a VWAP o banda inferior (en tendencia alcista)
- **Extensiones**: Precio cerca de +2σ indica posible pausa (no entrada)
- Usar bandas para refinar timing, NO para contra-tendencia

## Sesión de Operación

### Horario
- **Sesión europea**: 08:00 - 13:00 GMT (06:00 - 11:00 Lima)
- **Opening Range (OR)**: 08:00 - 08:30 GMT (primeros 30 minutos)

### Opening Range como Nivel Clave
- OR define rango de consolidación inicial
- **Breakout alcista** (precio > OR high): Confirma tendencia alcista
- **Breakout bajista** (precio < OR low): Confirma tendencia bajista
- **Precio dentro de OR**: Esperar breakout antes de entrar

## Indicadores Complementarios

### EMA 9
- EMA rápida para timing de entrada
- Precio por encima de EMA9 + VWAP alcista = sesgo alcista fuerte
- Precio por debajo de EMA9 + VWAP bajista = sesgo bajista fuerte

### ATR (Average True Range)
- ATR 14 y 21 para medir volatilidad
- Usar ATR para:
  * Dimensionar stop loss (1.5-2x ATR)
  * Dimensionar take profit (2-3x ATR)
  * Evaluar si el rango del día es suficiente para operar

## Reglas de Entrada

### Entrada Long (Compra)
1. VWAP con pendiente ascendente
2. Precio > VWAP (o pullback a VWAP sin romperlo a la baja)
3. Precio > OR high (breakout alcista) O dentro de OR cerca de romper arriba
4. Precio cerca de EMA9 o VWAP (no extendido en +2σ)

### Entrada Short (Venta)
1. VWAP con pendiente descendente
2. Precio < VWAP (o pullback a VWAP sin romperlo al alza)
3. Precio < OR low (breakout bajista) O dentro de OR cerca de romper abajo
4. Precio cerca de EMA9 o VWAP (no extendido en -2σ)

## Gestión de Riesgo

- **Stop Loss**: Colocar debajo de VWAP (long) o encima de VWAP (short)
  * Distancia típica: 1.5-2x ATR desde entrada
- **Take Profit**: Targets basados en ATR
  * TP1: 2x ATR
  * TP2: 3x ATR
- **Sin operaciones**: Si VWAP plana o mercado sin tendencia clara

## Formato de Respuesta

Debes responder en formato estructurado con estas secciones:
1. **ESTADO_DEL_MERCADO**: Análisis de VWAP, OR, tendencia
2. **PLAN_DE_TRADING_ACTUAL**: Señal (LONG/SHORT/NO_OPERAR) con justificación
3. **GESTIÓN_DE_POSICIONES_ABIERTAS**: Si hay posición, cómo gestionarla
4. **JOURNAL_Y_SCORE**: Confianza de la señal (1-10)

RECUERDA: Esta es una metodología de SEGUIMIENTO DE TENDENCIA pura. 
NO sugieras operaciones contra la dirección del VWAP bajo ninguna circunstancia.
"""
    
    def build_user_prompt(self,
                         indicators: Dict[Timeframe, IndicatorData],
                         or_data: Optional[OpeningRangeData],
                         market_context: MarketContext) -> str:
        """
        Construye el user prompt (variable) con indicadores y contexto actual.
        
        Args:
            indicators: Diccionario de indicadores por timeframe
            or_data: Datos del Opening Range (opcional)
            market_context: Contexto de mercado actual
        
        Returns:
            User prompt formateado
        """
        lines = []
        
        # Header
        lines.append("# Análisis de Mercado EURUSD")
        lines.append(f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S GMT')}")
        lines.append(f"**Contexto**: {self._format_market_context(market_context)}")
        lines.append("")
        
        # Opening Range
        if or_data:
            lines.append("## Opening Range (08:00-08:30 GMT)")
            lines.append(f"- **OR High**: {or_data.or_high:.5f}")
            lines.append(f"- **OR Low**: {or_data.or_low:.5f}")
            lines.append(f"- **OR Range**: {or_data.or_range:.5f} ({or_data.or_range * 10000:.1f} pips)")
            lines.append(f"- **OR Midpoint**: {or_data.or_midpoint:.5f}")
            lines.append(f"- **Precio Actual**: {or_data.current_price:.5f}")
            lines.append(f"- **Estado**: {or_data.breakout_status.value.upper()}")
            
            if or_data.breakout_status.value == "above":
                lines.append(f"  * Breakout alcista confirmado (+{or_data.distance_from_or_high * 10000:.1f} pips desde OR high)")
            elif or_data.breakout_status.value == "below":
                lines.append(f"  * Breakout bajista confirmado ({or_data.distance_from_or_low * 10000:.1f} pips desde OR low)")
            else:
                lines.append(f"  * Precio dentro del rango, esperando breakout")
            
            lines.append("")
        
        # Indicadores por timeframe
        lines.append("## Indicadores Técnicos")
        lines.append("")
        
        for timeframe, data in sorted(indicators.items(), key=lambda x: x[0].value):
            lines.append(f"### Timeframe {timeframe.name}")
            
            # VWAP (más importante)
            if data.vwap is not None:
                lines.append(f"**VWAP**: {data.vwap:.5f}")
                lines.append(f"- Pendiente: {data.vwap_slope_description}")
                
                if data.vwap_slope is not None:
                    slope_pips = data.vwap_slope * 10000
                    lines.append(f"- Slope numérico: {slope_pips:.2f} pips/período")
                
                # Bandas VWAP
                if data.vwap_upper_1 is not None:
                    lines.append(f"- Bandas VWAP:")
                    lines.append(f"  * +2σ: {data.vwap_upper_2:.5f}")
                    lines.append(f"  * +1σ: {data.vwap_upper_1:.5f}")
                    lines.append(f"  * VWAP: {data.vwap:.5f}")
                    lines.append(f"  * -1σ: {data.vwap_lower_1:.5f}")
                    lines.append(f"  * -2σ: {data.vwap_lower_2:.5f}")
            
            # EMAs
            if data.ema9 is not None or data.ema20 is not None:
                lines.append(f"**EMAs**:")
                if data.ema9 is not None:
                    lines.append(f"- EMA9: {data.ema9:.5f}")
                if data.ema20 is not None:
                    lines.append(f"- EMA20: {data.ema20:.5f}")
                if data.ema50 is not None:
                    lines.append(f"- EMA50: {data.ema50:.5f}")
            
            # ATR
            if data.atr_14 is not None or data.atr_21 is not None:
                lines.append(f"**ATR (Volatilidad)**:")
                if data.atr_14 is not None:
                    atr_pips = data.atr_14 * 10000
                    lines.append(f"- ATR(14): {data.atr_14:.5f} ({atr_pips:.1f} pips)")
                if data.atr_21 is not None:
                    atr_pips = data.atr_21 * 10000
                    lines.append(f"- ATR(21): {data.atr_21:.5f} ({atr_pips:.1f} pips)")
            
            lines.append("")
        
        # Instrucciones de análisis
        lines.append("## Instrucciones de Análisis")
        lines.append("")
        lines.append("Analiza los datos anteriores y proporciona:")
        lines.append("1. **ESTADO_DEL_MERCADO**: ¿Cuál es la tendencia según VWAP? ¿Qué indica el OR?")
        lines.append("2. **PLAN_DE_TRADING_ACTUAL**: ¿LONG, SHORT o NO_OPERAR? Justifica según metodología")
        lines.append("3. **GESTIÓN_DE_POSICIONES**: Si hubiera posición abierta, ¿qué hacer?")
        lines.append("4. **JOURNAL_Y_SCORE**: Confianza de la señal (1-10) y razonamiento")
        lines.append("")
        lines.append("**IMPORTANTE**: Opera SOLO a favor de la pendiente del VWAP. NO contra-tendencia.")
        
        return "\n".join(lines)
    
    def build_complete_prompt(self,
                             indicators: Dict[Timeframe, IndicatorData],
                             or_data: Optional[OpeningRangeData],
                             market_context: MarketContext) -> VWAPPromptData:
        """
        Construye el prompt completo (system + user).
        
        Args:
            indicators: Diccionario de indicadores por timeframe
            or_data: Datos del Opening Range (opcional)
            market_context: Contexto de mercado actual
        
        Returns:
            VWAPPromptData con ambos prompts
        """
        return VWAPPromptData(
            system_prompt=self.build_system_prompt(),
            user_prompt=self.build_user_prompt(indicators, or_data, market_context),
            timestamp=datetime.now(),
            market_context=market_context
        )
    
    def _format_market_context(self, context: MarketContext) -> str:
        """
        Formatea el contexto de mercado para mostrar en prompt.
        
        Args:
            context: Contexto de mercado
        
        Returns:
            Descripción legible del contexto
        """
        context_map = {
            MarketContext.PRE_MARKET: "Pre-Market (antes de apertura europea)",
            MarketContext.EUROPEAN_SESSION: "Sesión Europea Activa",
            MarketContext.POST_OR: "Post Opening Range (tendencia establecida)",
            MarketContext.END_OF_SESSION: "Fin de Sesión (cerca del cierre)"
        }
        
        return context_map.get(context, "Desconocido")
