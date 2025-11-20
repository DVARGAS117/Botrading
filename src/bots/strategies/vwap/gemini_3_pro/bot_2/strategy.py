"""
Bot 2 - Estrategia (Numérico Alternativo)

Implementa una variante de la estrategia numérica de Bot 1.
La diferencia principal está en cómo se construyen los prompts:
- Prompts más concisos
- Solo indicadores (sin velas OHLCV)
- Énfasis en disciplina y contra-ejemplos

Author: Botrading Team
Date: 2025-11-17
"""

from typing import Dict, Any, Optional, Tuple

from src.bots.base.base_bot_operations import BaseBotOperations, BotConfig
from src.core.vwap_prompt_builder import MarketContext


class Bot2Strategy(BaseBotOperations):
    """
    Estrategia de Bot 2 - Numérico Alternativo.
    
    Similar a Bot 1 pero con prompts alternativos para comparación.
    """
    
    def __init__(self, config: BotConfig):
        super().__init__(config)
        
        self.logger.info(
            "Bot 2 (Numérico Alternativo) inicializado",
            extra={
                'strategy': 'VWAP Methodology - Prompts Alternativos',
                'data_type': 'numeric_only',
                'variant': 'concise_prompts'
            }
        )
    
    def prepare_data_for_ai(
        self,
        symbol: str,
        indicators: Dict,
        or_data: Optional[Any],
        market_context: MarketContext
    ) -> Tuple[str, str]:
        """
        Prepara datos con PROMPTS ALTERNATIVOS.
        
        Diferencias vs Bot 1:
        - System prompt con énfasis en disciplina
        - User prompt más conciso (solo indicadores clave)
        - NO incluye velas OHLCV
        
        Args:
            symbol: Símbolo del activo
            indicators: Diccionario de indicadores por timeframe
            or_data: Datos del Opening Range
            market_context: Contexto de mercado actual
        
        Returns:
            tuple: (system_prompt_alternativo, user_prompt_conciso)
        """
        try:
            # Construir system prompt con énfasis en disciplina
            system_prompt = self._build_alternative_system_prompt()
            
            # Construir user prompt conciso (solo indicadores clave)
            user_prompt = self._build_concise_user_prompt(
                symbol=symbol,
                indicators=indicators,
                or_data=or_data,
                market_context=market_context
            )
            
            self.logger.debug(
                f"Prompts alternativos preparados para {symbol}",
                extra={
                    'symbol': symbol,
                    'market_context': market_context.value,
                    'prompt_variant': 'concise',
                    'system_prompt_length': len(system_prompt),
                    'user_prompt_length': len(user_prompt)
                }
            )
            
            return system_prompt, user_prompt
            
        except Exception as e:
            self.logger.error(
                f"Error preparando datos alternativos: {str(e)}",
                extra={'symbol': symbol, 'error': str(e)}
            )
            raise
    
    def _build_alternative_system_prompt(self) -> str:
        """
        Construye system prompt alternativo con énfasis en disciplina.
        
        Returns:
            System prompt modificado
        """
        return """Eres un motor de decisión de TRADING INTRADÍA disciplinado y conservador.

REGLAS ABSOLUTAS:
1. SOLO operar A FAVOR de la tendencia VWAP (NUNCA contra-tendencia)
2. Si VWAP sube → SOLO buscar compras
3. Si VWAP baja → SOLO buscar ventas
4. Si VWAP plano → NO operar

DISCIPLINA ANTES QUE GANANCIAS:
- Es mejor NO operar que forzar una entrada
- Prefiere perder oportunidades que tomar malas decisiones
- Rechaza setups que no cumplan TODOS los criterios

INDICADORES CLAVE:
- VWAP y su pendiente = Ancla de dirección
- Opening Range (OR) = Niveles de confirmación
- ATR = Dimensionamiento de riesgo
- EMA 9 = Timing de entrada

PROHIBIDO:
❌ Operar contra VWAP
❌ Anticipar reversiones
❌ Entrar sin confirmación de breakout OR
❌ Stops demasiado ajustados (<1.5 ATR)

Tu objetivo: Proteger el capital, NO maximizar trades.
Responde SOLO con JSON en el formato especificado."""
    
    def _build_concise_user_prompt(
        self,
        symbol: str,
        indicators: Dict,
        or_data: Optional[Any],
        market_context: MarketContext
    ) -> str:
        """
        Construye user prompt CONCISO (solo indicadores clave).
        
        Args:
            symbol: Símbolo
            indicators: Indicadores
            or_data: Opening Range
            market_context: Contexto
        
        Returns:
            User prompt conciso
        """
        from datetime import datetime
        
        lines = []
        lines.append(f"# Análisis {symbol} - {market_context.value.upper()}")
        lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M GMT')}")
        lines.append("")
        
        # Opening Range (si existe)
        if or_data:
            lines.append("## Opening Range")
            lines.append(f"High: {or_data.or_high:.5f} | Low: {or_data.or_low:.5f}")
            lines.append(f"Status: {or_data.breakout_status.value.upper()}")
            lines.append("")
        
        # Indicadores clave (solo M5 principal)
        from src.core.mt5_data_extractor import Timeframe
        if Timeframe.M5 in indicators:
            data_5m = indicators[Timeframe.M5]
            lines.append("## Indicadores 5M (Principal)")
            
            if data_5m.vwap is not None:
                lines.append(f"VWAP: {data_5m.vwap:.5f} ({data_5m.vwap_slope_description})")
                if data_5m.vwap_upper_1:
                    lines.append(f"Bandas: +1σ={data_5m.vwap_upper_1:.5f}, -1σ={data_5m.vwap_lower_1:.5f}")
            
            if data_5m.ema9:
                lines.append(f"EMA9: {data_5m.ema9:.5f}")
            
            if data_5m.atr_14:
                lines.append(f"ATR14: {data_5m.atr_14:.5f}")
            
            lines.append("")
        
        # Contexto adicional 1H (solo EMA50)
        if Timeframe.H1 in indicators:
            data_1h = indicators[Timeframe.H1]
            lines.append("## Contexto 1H")
            if data_1h.ema50:
                lines.append(f"EMA50: {data_1h.ema50:.5f}")
            lines.append("")
        
        lines.append("## Decisión")
        lines.append("Analiza y decide: ¿Hay setup válido siguiendo TODAS las reglas?")
        lines.append("Responde SOLO con JSON.")
        
        return "\n".join(lines)
    
    def parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea respuesta IA (idéntico a Bot 1).
        """
        try:
            parsed_response = self.response_parser.parse_response(response_text)
            bot_decision = self.response_parser.convert_to_bot_format(parsed_response)
            
            self.logger.info(
                f"✅ Respuesta IA parseada (Bot 2)",
                extra={
                    'accion': bot_decision.get('accion'),
                    'direccion': bot_decision.get('direccion')
                }
            )
            
            return bot_decision
            
        except Exception as e:
            self.logger.error(f"Error parseando respuesta: {str(e)}")
            return {
                'accion': 'NO_OPERAR',
                'razonamiento': f'Error de parsing: {str(e)}'
            }
