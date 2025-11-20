"""Estrategia del Bot 1 (INTRADAY Gemini 3 Pro).

Esta clase implementa la lógica específica de la estrategia INTRADAY,
heredando de BaseBotOperations para aprovechar la funcionalidad común.

La estrategia INTRADAY se enfoca en operaciones dentro del día, buscando
aprovechar movimientos de precio en marcos temporales cortos (M1, M5, M15, H1).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.bots.base.base_bot_operations import BaseBotOperations, BotConfig
from src.bots.strategies.intraday.gemini_3_pro.bot_1.intraday_indicators import (
    IntradayIndicatorCalculator,
    generate_operation_id,
)
from src.core.ia_query_repository import IAQueryRepository, QueryType
from src.core.mt5_data_extractor import MT5DataExtractor
from src.core.vwap_prompt_builder import MarketContext


class IntradayBot1Strategy(BaseBotOperations):
    """Estrategia de Bot 1 - INTRADAY Baseline.
    
    Esta estrategia implementa operaciones intradía utilizando Gemini 3 Pro
    con parámetros optimizados para razonamiento profundo y cálculos precisos.
    
    Características principales:
    - Análisis multi-timeframe (M1, M5, M15, H1)
    - Identificación de niveles clave intraday
    - Gestión de riesgo dinámica
    - Reevaluación continua de posiciones
    - Una orden por señal (sin dual orders)
    """

    def __init__(self, config: BotConfig) -> None:
        """Inicializa el bot de estrategia INTRADAY.
        
        Args:
            config: Configuración del bot con parámetros de Gemini 3 Pro
        """
        super().__init__(config)

        # Inicializar calculador de indicadores INTRADAY (usa self.data_extractor de la clase base)
        self.indicator_calculator = IntradayIndicatorCalculator(self.data_extractor)
        
        # Inicializar repositorio de consultas IA
        db_path = Path(__file__).parent.parent.parent.parent.parent.parent / "data" / "consultas_ia.db"
        self.ia_query_repository = IAQueryRepository(db_path)
        
        # Ruta a los prompts
        self.prompts_dir = Path(__file__).parent / "prompts"

        self.logger.info(
            "Bot 1 (INTRADAY Baseline) inicializado",
            extra={
                "strategy": "INTRADAY",
                "data_type": "multi_timeframe",
                "ai_model": config.ai_model,
                "thinking_level": "HIGH",
                "code_execution": "enabled",
                "prompts_dir": str(self.prompts_dir),
            },
        )

    def prepare_data_for_ai(
        self,
        symbol: str,
        indicators: Dict,
        or_data: Optional[Any],
        market_context: MarketContext,
        ohlcv_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Prepara datos de mercado para enviar a la IA.
        
        Esta función construye los prompts (system y user) que se enviarán
        a Gemini 3 Pro para análisis y generación de señales de trading.
        
        Flujo:
        1. Genera operation_id único para rastrear costos
        2. Calcula paquetes de indicadores (M15: 200 velas, D1: 30 velas cerradas)
        3. Carga prompts desde archivos (system_prompt.txt y user_prompt_*.txt)
        4. Reemplaza variables en los prompts con datos reales
        5. Retorna diccionario con toda la información
        
        Args:
            symbol: Símbolo a analizar (ej: "EURUSD")
            indicators: Diccionario con valores de indicadores técnicos (NO USADO, calculamos propios)
            or_data: Datos del Opening Range (opcional, NO USADO en INTRADAY)
            market_context: Contexto de mercado actual
            ohlcv_data: Datos OHLCV históricos (opcional, NO USADO, obtenemos propios)
            
        Returns:
            Diccionario con:
            - operation_id: ID único de la operación
            - system_prompt: System prompt cargado desde archivo
            - user_prompt: User prompt con variables reemplazadas
            - tactical_package: Paquete M15 (200 velas)
            - strategic_package: Paquete D1 (30 velas cerradas)
            - symbol: Símbolo analizado
            - timestamp: Timestamp de la preparación
        """
        # 1. Generar operation_id único
        operation_id = generate_operation_id(self.config.bot_id, symbol)
        
        # 2. Calcular paquetes de indicadores
        self.logger.info(
            f"Calculando paquetes INTRADAY para {symbol}",
            extra={
                "symbol": symbol,
                "operation_id": operation_id,
                "bot_id": self.config.bot_id,
            },
        )
        
        try:
            packages = self.indicator_calculator.get_full_intraday_packages(symbol)
            tactical_package = packages["tactical"]
            strategic_package = packages["strategic"]
        except Exception as e:
            self.logger.error(
                f"Error calculando paquetes INTRADAY para {symbol}: {e}",
                extra={
                    "symbol": symbol,
                    "operation_id": operation_id,
                    "error": str(e),
                },
            )
            raise
        
        # 3. Cargar prompts desde archivos
        system_prompt_path = self.prompts_dir / "system_prompt.txt"
        
        # Determinar si hay operación activa para elegir prompt correcto
        has_active_position = self._has_active_position(symbol)
        
        if has_active_position:
            user_prompt_path = self.prompts_dir / "user_prompt_reevaluation.txt"
        else:
            user_prompt_path = self.prompts_dir / "user_prompt_evaluation.txt"
        
        try:
            with open(system_prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
            
            with open(user_prompt_path, "r", encoding="utf-8") as f:
                user_prompt_template = f.read()
        except FileNotFoundError as e:
            self.logger.error(
                f"Error: No se encontró archivo de prompt: {e.filename}",
                extra={
                    "symbol": symbol,
                    "operation_id": operation_id,
                    "missing_file": e.filename,
                },
            )
            raise
        
        # 4. Reemplazar variables en user_prompt
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        user_prompt = user_prompt_template.replace("{symbol}", symbol)
        user_prompt = user_prompt.replace("{operation_id}", operation_id)
        user_prompt = user_prompt.replace("{current_time}", current_time)
        user_prompt = user_prompt.replace(
            "{tactical_package}", json.dumps(tactical_package, indent=2)
        )
        user_prompt = user_prompt.replace(
            "{strategic_package}", json.dumps(strategic_package, indent=2)
        )
        
        # Si hay posición activa, agregar información de la posición
        if has_active_position:
            current_position = self._get_current_position_info(symbol)
            user_prompt = user_prompt.replace(
                "{current_position}", json.dumps(current_position, indent=2)
            )
        
        # 5. Retornar diccionario completo
        self.logger.info(
            f"Datos INTRADAY preparados para {symbol}",
            extra={
                "symbol": symbol,
                "operation_id": operation_id,
                "has_active_position": has_active_position,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
                "tactical_candles": len(tactical_package),
                "strategic_candles": len(strategic_package),
            },
        )
        
        return {
            "operation_id": operation_id,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "tactical_package": tactical_package,
            "strategic_package": strategic_package,
            "symbol": symbol,
            "timestamp": current_time,
            "has_active_position": has_active_position,
        }

    def execute_cycle(self, symbol: str) -> Dict[str, Any]:
        """Ejecuta un ciclo completo de análisis y decisión INTRADAY.
        
        Flujo completo:
        1. Preparar datos (paquetes M15/D1, prompts)
        2. Consultar Gemini 3 Pro
        3. Parsear respuesta
        4. Registrar consulta en IAQueryRepository
        5. Retornar decisión
        
        Args:
            symbol: Símbolo a analizar (ej: "EURUSD")
            
        Returns:
            Diccionario con:
            - operation_id: ID único de la operación
            - action: Acción decidida (COMPRAR/VENDER/NO_OPERAR/MANTENER/CERRAR)
            - reasoning: Razonamiento de la IA
            - query_id: ID de la consulta registrada en BD
            - cost_usd: Costo de la consulta
            - tokens_total: Total de tokens usados
        """
        self.logger.info(
            f"Iniciando ciclo INTRADAY para {symbol}",
            extra={
                "symbol": symbol,
                "bot_id": self.config.bot_id,
            },
        )
        
        # 1. Preparar datos para IA
        try:
            prepared_data = self.prepare_data_for_ai(
                symbol=symbol,
                indicators={},  # No usado, calculamos propios
                or_data=None,
                market_context=self.get_market_context(),
                ohlcv_data=None,  # No usado, calculamos propios
            )
        except Exception as e:
            self.logger.error(
                f"Error preparando datos para {symbol}: {e}",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                },
            )
            raise
        
        operation_id = prepared_data["operation_id"]
        system_prompt = prepared_data["system_prompt"]
        user_prompt = prepared_data["user_prompt"]
        has_active_position = prepared_data["has_active_position"]
        
        # 2. Consultar Gemini 3 Pro
        self.logger.info(
            f"Consultando Gemini 3 Pro para {symbol}",
            extra={
                "symbol": symbol,
                "operation_id": operation_id,
                "has_active_position": has_active_position,
            },
        )
        
        # TODO: Implementar llamada real a Gemini 3 Pro
        # Por ahora usamos placeholder
        ai_response = {
            "response_text": "Placeholder response from Gemini 3 Pro",
            "tokens_input": 1000,
            "tokens_output": 500,
            "cost_usd": 0.05,
        }
        
        # 3. Parsear respuesta
        try:
            parsed_decision = self.parse_ai_response(ai_response["response_text"])
        except Exception as e:
            self.logger.error(
                f"Error parseando respuesta IA para {symbol}: {e}",
                extra={
                    "symbol": symbol,
                    "operation_id": operation_id,
                    "error": str(e),
                },
            )
            raise
        
        # 4. Registrar consulta en IAQueryRepository
        query_type = QueryType.REEVALUATION if has_active_position else QueryType.EVALUATION
        
        try:
            ia_query = self.ia_query_repository.create_query(
                bot_id=self.config.bot_id,
                ia_id=1,  # TODO: Obtener de configuración
                symbol=symbol,
                query_type=query_type,
                prompt=f"{system_prompt}\n\n{user_prompt}",
                response=ai_response["response_text"],
                tokens_input=ai_response["tokens_input"],
                tokens_output=ai_response["tokens_output"],
                cost_usd=ai_response["cost_usd"],
                action_decided=parsed_decision["accion"],
                operation_id=operation_id,
            )
            
            self.logger.info(
                f"Consulta IA registrada para {symbol}",
                extra={
                    "symbol": symbol,
                    "operation_id": operation_id,
                    "query_id": ia_query.id,
                    "query_type": query_type.value,
                    "action_decided": parsed_decision["accion"],
                    "cost_usd": ia_query.cost_usd,
                    "tokens_total": ia_query.tokens_total,
                },
            )
        except Exception as e:
            self.logger.error(
                f"Error registrando consulta IA para {symbol}: {e}",
                extra={
                    "symbol": symbol,
                    "operation_id": operation_id,
                    "error": str(e),
                },
            )
            raise
        
        # 5. Retornar decisión completa
        return {
            "operation_id": operation_id,
            "action": parsed_decision["accion"],
            "reasoning": parsed_decision["razonamiento"],
            "direction": parsed_decision.get("direccion"),
            "stop_loss": parsed_decision.get("stop_loss"),
            "take_profit": parsed_decision.get("take_profit"),
            "confidence": parsed_decision.get("confianza"),
            "query_id": ia_query.id,
            "cost_usd": ia_query.cost_usd,
            "tokens_total": ia_query.tokens_total,
            "timestamp": prepared_data["timestamp"],
        }

    def parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parsea la respuesta de la IA.
        
        Convierte la respuesta en texto de Gemini 3 Pro a un formato
        estructurado que el bot puede ejecutar.
        
        TODO: Implementar parser específico para respuestas INTRADAY
        
        Args:
            response_text: Texto de respuesta de Gemini 3 Pro
            
        Returns:
            Diccionario con decisión estructurada:
            {
                "accion": "COMPRAR" | "VENDER" | "NO_OPERAR",
                "razonamiento": str,
                "direccion": "LONG" | "SHORT" | None,
                "stop_loss": float (opcional),
                "take_profit": float (opcional),
                "confianza": float (opcional),
            }
        """
        # TODO: Implementar parser real cuando se definan los indicadores y formato de respuesta
        # Por ahora retornamos estructura placeholder
        
        self.logger.info(
            "Parseando respuesta IA INTRADAY (placeholder)",
            extra={"response_length": len(response_text)},
        )
        
        # Placeholder: NO_OPERAR hasta que se implemente el parser
        return {
            "accion": "NO_OPERAR",
            "razonamiento": "Parser INTRADAY pendiente de implementación",
            "direccion": None,
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento del bot INTRADAY.
        
        Returns:
            Diccionario con métricas actuales del bot:
            - bot_id: ID del bot
            - bot_name: Nombre del bot
            - strategy: Nombre de la estrategia
            - current_pnl_r: PnL actual en múltiplos de R
            - trades_today: Número de trades ejecutados hoy
            - is_trading_hours: Si está en horario de trading
            - should_stop: Si debe detener trading por límites
            - market_context: Contexto actual del mercado
            - timestamp: Timestamp ISO de la métrica
        """
        return {
            "bot_id": self.config.bot_id,
            "bot_name": self.config.bot_name,
            "strategy": "INTRADAY",
            "current_pnl_r": self.current_pnl_r,
            "trades_today": self.trades_today,
            "is_trading_hours": self.is_trading_hours(),
            "should_stop": self.should_stop_trading_today(),
            "market_context": self.get_market_context().value,
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_intraday_levels(self, ohlcv_data: Dict) -> Dict[str, Any]:
        """Analiza niveles clave intraday (soporte, resistencia, pivotes).
        
        TODO: Implementar análisis de niveles específicos de INTRADAY
        
        Args:
            ohlcv_data: Datos OHLCV históricos
            
        Returns:
            Diccionario con niveles identificados
        """
        # Placeholder para futura implementación
        return {
            "support_levels": [],
            "resistance_levels": [],
            "pivot_points": {},
        }

    def calculate_intraday_volatility(self, ohlcv_data: Dict) -> float:
        """Calcula volatilidad intraday para ajuste dinámico de stops.
        
        TODO: Implementar cálculo de volatilidad intraday
        
        Args:
            ohlcv_data: Datos OHLCV históricos
            
        Returns:
            Valor de volatilidad (ATR, desviación estándar, etc.)
        """
        # Placeholder para futura implementación
        return 0.0

    def _has_active_position(self, symbol: str) -> bool:
        """Verifica si hay una posición activa para el símbolo.
        
        Args:
            symbol: Símbolo a verificar
            
        Returns:
            True si hay posición activa, False en caso contrario
        """
        # TODO: Implementar verificación real con MetaTrader 5
        # Por ahora retorna False (modo evaluación)
        return False

    def _get_current_position_info(self, symbol: str) -> Dict[str, Any]:
        """Obtiene información de la posición activa.
        
        Args:
            symbol: Símbolo de la posición
            
        Returns:
            Diccionario con información de la posición:
            - type: "LONG" o "SHORT"
            - entry_price: Precio de entrada
            - current_price: Precio actual
            - sl: Stop Loss
            - tp: Take Profit
            - pnl_points: PnL en puntos
            - pnl_r: PnL en múltiplos de R
            - open_time: Timestamp de apertura
        """
        # TODO: Implementar obtención real con MetaTrader 5
        # Por ahora retorna estructura placeholder
        return {
            "type": "LONG",
            "entry_price": 0.0,
            "current_price": 0.0,
            "sl": 0.0,
            "tp": 0.0,
            "pnl_points": 0.0,
            "pnl_r": 0.0,
            "open_time": datetime.now().isoformat(),
        }
