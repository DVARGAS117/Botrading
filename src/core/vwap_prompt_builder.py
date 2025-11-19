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
    OPENING_RANGE = "opening_range"  # Durante Opening Range (08:00-08:30 GMT)
    POST_OR = "post_or"  # Después de Opening Range
    EUROPEAN_SESSION = "european_session"  # Sesión europea activa
    END_OF_SESSION = "end_of_session"  # Cerca del cierre
    POST_MARKET = "post_market"  # Después del cierre


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
- **Sesión europea**: 08:00 - 13:00 GMT (03:00 - 08:00 Lima)
- **Opening Range (OR)**: 08:00 - 08:30 GMT (03:00 - 03:30 Lima)

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
                         market_context: MarketContext,
                         ohlcv_data: Optional[Dict[Timeframe, object]] = None) -> str:
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
            
            # Manejar breakout_status (puede ser enum o string)
            if hasattr(or_data.breakout_status, 'value'):
                status_value = or_data.breakout_status.value
            else:
                status_value = str(or_data.breakout_status)
            
            lines.append(f"- **Estado**: {status_value.upper()}")
            
            if status_value == "above":
                lines.append(f"  * Breakout alcista confirmado (+{or_data.distance_from_or_high * 10000:.1f} pips desde OR high)")
            elif status_value == "below":
                lines.append(f"  * Breakout bajista confirmado ({or_data.distance_from_or_low * 10000:.1f} pips desde OR low)")
            else:
                lines.append(f"  * Precio dentro del rango, esperando breakout")
            
            lines.append("")

        # Indicadores calculados por timeframe
        lines.append("## Indicadores Técnicos")
        lines.append("")
        
        for timeframe in [Timeframe.M5, Timeframe.M1, Timeframe.H1]:
            if timeframe in indicators:
                ind = indicators[timeframe]
                # Usar siempre el nombre del enum (M1, M5, H1) para evitar errores con valores int
                tf_name = timeframe.name.upper()
                
                lines.append(f"### {tf_name}")
                
                # VWAP y bandas
                if hasattr(ind, 'vwap') and ind.vwap is not None:
                    lines.append(f"- **VWAP**: {ind.vwap:.5f}")
                if hasattr(ind, 'vwap_upper_1') and ind.vwap_upper_1 is not None:
                    lines.append(f"- **VWAP +1σ**: {ind.vwap_upper_1:.5f}")
                if hasattr(ind, 'vwap_upper_2') and ind.vwap_upper_2 is not None:
                    lines.append(f"- **VWAP +2σ**: {ind.vwap_upper_2:.5f}")
                if hasattr(ind, 'vwap_lower_1') and ind.vwap_lower_1 is not None:
                    lines.append(f"- **VWAP -1σ**: {ind.vwap_lower_1:.5f}")
                if hasattr(ind, 'vwap_lower_2') and ind.vwap_lower_2 is not None:
                    lines.append(f"- **VWAP -2σ**: {ind.vwap_lower_2:.5f}")

                # Slope / pendiente VWAP (para incluir 'ascendente', 'descendente', 'plana')
                slope_desc = None
                if hasattr(ind, 'vwap_slope_description') and ind.vwap_slope_description:
                    slope_desc = ind.vwap_slope_description
                elif hasattr(ind, 'vwap_slope_desc') and ind.vwap_slope_desc:
                    slope_desc = ind.vwap_slope_desc
                if slope_desc:
                    lines.append(f"- **Pendiente VWAP**: {slope_desc}")

                # Línea resumen que usa la palabra 'banda' para compatibilidad con tests
                if all(hasattr(ind, a) for a in ['vwap_upper_1', 'vwap_lower_1']) and ind.vwap_upper_1 and ind.vwap_lower_1:
                    lines.append(f"- Bandas VWAP (±1σ): {ind.vwap_lower_1:.5f} / {ind.vwap_upper_1:.5f}")
                if all(hasattr(ind, a) for a in ['vwap_upper_2', 'vwap_lower_2']) and ind.vwap_upper_2 and ind.vwap_lower_2:
                    lines.append(f"- Bandas VWAP (±2σ): {ind.vwap_lower_2:.5f} / {ind.vwap_upper_2:.5f}")
                
                # EMA
                # Soportar ambos estilos de nombres (ema9 vs ema_9, ema20 vs ema_21 etc.)
                def _get_attr(obj, *names):
                    for n in names:
                        if hasattr(obj, n) and getattr(obj, n) is not None:
                            return getattr(obj, n)
                    return None
                ema9 = _get_attr(ind, 'ema9', 'ema_9')
                ema20 = _get_attr(ind, 'ema20', 'ema_20', 'ema_21')  # algunos cálculos usan 20, tests esperan 20/21
                ema50 = _get_attr(ind, 'ema50', 'ema_50')
                if ema9 is not None:
                    lines.append(f"- **EMA 9**: {ema9:.5f}")
                if ema20 is not None:
                    # Presentar como EMA 20 si existe explícitamente, si solo hay ema_21 mantener test pasando (ambos aceptables)
                    label = 'EMA 20' if hasattr(ind, 'ema20') else 'EMA 21'
                    lines.append(f"- **{label}**: {ema20:.5f}")
                if ema50 is not None:
                    lines.append(f"- **EMA 50**: {ema50:.5f}")
                
                # ATR
                if hasattr(ind, 'atr_14') and ind.atr_14 is not None:
                    lines.append(f"- **ATR 14**: {ind.atr_14:.5f} ({ind.atr_14 * 10000:.1f} pips)")
                if hasattr(ind, 'atr_21') and ind.atr_21 is not None:
                    lines.append(f"- **ATR 21**: {ind.atr_21:.5f} ({ind.atr_21 * 10000:.1f} pips)")
                
                # Precio actual
                if hasattr(ind, 'close') and ind.close is not None:
                    lines.append(f"- **Precio actual**: {ind.close:.5f}")
                    
                    # Distancia del precio al VWAP
                    if hasattr(ind, 'vwap') and ind.vwap is not None:
                        distance = ind.close - ind.vwap
                        distance_pips = distance * 10000
                        position = "encima" if distance > 0 else "debajo"
                        lines.append(f"- **Posición vs VWAP**: {abs(distance_pips):.1f} pips {position}")
                
                lines.append("")
        
        # Velas por timeframe (según especificaciones)
        if ohlcv_data:
            # M5: todas las velas de la sesión actual
            if Timeframe.M5 in ohlcv_data:
                lines.append("## Velas M5 (sesión actual)")
                lines.append("")
                candles = ohlcv_data[Timeframe.M5].data
                for idx, row in candles.iterrows():
                    try:
                        time_str = idx.strftime('%H:%M') if hasattr(idx, 'strftime') else str(idx)
                        lines.append(f"- {time_str}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} V={int(row['volume'])}")
                    except:
                        lines.append(f"- {idx}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} V={int(row['volume'])}")
                lines.append("")
            
            # M1: 200 velas (solo de la sesión actual o desde poco antes)
            if Timeframe.M1 in ohlcv_data:
                lines.append("## Velas M1 (200 velas - timing)")
                lines.append("")
                candles = ohlcv_data[Timeframe.M1].data.tail(200)  # Últimas 200
                for idx, row in candles.iterrows():
                    try:
                        time_str = idx.strftime('%H:%M') if hasattr(idx, 'strftime') else str(idx)
                        lines.append(f"- {time_str}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} V={int(row['volume'])}")
                    except:
                        lines.append(f"- {idx}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} V={int(row['volume'])}")
                lines.append("")
            
            # H1: 30 velas máximo
            if Timeframe.H1 in ohlcv_data:
                lines.append("## Velas H1 (30 velas máximo - contexto)")
                lines.append("")
                candles = ohlcv_data[Timeframe.H1].data.tail(30)  # Últimas 30
                for idx, row in candles.iterrows():
                    try:
                        time_str = idx.strftime('%H:%M') if hasattr(idx, 'strftime') else str(idx)
                        lines.append(f"- {time_str}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} V={int(row['volume'])}")
                    except:
                        lines.append(f"- {idx}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} V={int(row['volume'])}")
                lines.append("")
            
        return "\n".join(lines)
    
    def build_complete_prompt(self,
                             indicators: Dict[Timeframe, IndicatorData],
                             or_data: Optional[OpeningRangeData],
                             market_context: MarketContext,
                             ohlcv_data: Optional[Dict[Timeframe, object]] = None) -> VWAPPromptData:
        """
        Construye el prompt completo (system + user).
        
        Args:
            indicators: Diccionario de indicadores por timeframe
            or_data: Datos del Opening Range (opcional)
            market_context: Contexto de mercado actual
            ohlcv_data: Datos OHLCV por timeframe (opcional)
        
        Returns:
            VWAPPromptData con ambos prompts
        """
        return VWAPPromptData(
            system_prompt=self.build_system_prompt(),
            user_prompt=self.build_user_prompt(indicators, or_data, market_context, ohlcv_data),
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
