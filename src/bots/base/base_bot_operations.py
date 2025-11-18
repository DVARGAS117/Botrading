"""
BaseBotOperations - Clase base para operaciones comunes de los 5 bots

Proporciona funcionalidad compartida entre todos los bots:
- Inicialización y configuración
- Validación de horarios de trading
- Consulta a IA (con retry y manejo de errores)
- Apertura dual (Market + Limit)
- Reevaluación de posiciones abiertas
- Registro en base de datos
- Logging estructurado

Todos los bots heredan de esta clase y solo necesitan implementar
los métodos específicos de su tipo (numérico/visual/híbrido).

Author: Botrading Team
Date: 2025-11-17
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, time
from enum import Enum
import logging
from pathlib import Path
import os

from src.core.mt5_connection import MT5Connection
from src.core.mt5_data_extractor import MT5DataExtractor, Timeframe
from src.core.indicator_calculator import IndicatorCalculator
from src.core.opening_range_calculator import OpeningRangeCalculator
from src.core.prompt_builder import PromptBuilder
from src.core.vwap_response_parser import VWAPResponseParser
from src.core.vwap_prompt_builder import MarketContext
from src.core.vertex_ai_client import VertexAIClient, VertexAIConfig
from src.core.gemini_client import GeminiClient, GeminiConfig  # Fallback opcional si se requiere en futuro
from src.core.dual_order_manager import DualOrderManager
from src.core.logger import get_bot_logger


class BotOperationError(Exception):
    """Excepción base para errores de operación de bot"""
    pass


class BotMode(Enum):
    """Modo de operación del bot"""
    DEMO = "demo"
    LIVE = "live"


@dataclass
class BotConfig:
    """
    Configuración común para todos los bots
    
    Attributes:
        bot_id: Identificador único del bot (1-5)
        bot_name: Nombre descriptivo del bot
        bot_type: Tipo de bot ("numerico", "visual", "hibrido")
        mode: Modo de operación (DEMO o LIVE)
        symbols: Lista de símbolos a operar
        timeframes: Lista de timeframes a analizar
        trading_hours: Horario de trading (inicio, fin en formato HH:MM)
        timezone_local: Zona horaria local (ej: "America/Lima")
        risk_per_trade: Riesgo por trade en porcentaje
        max_daily_risk: Riesgo máximo diario en múltiplos de R
        reevaluation_interval_minutes: Intervalo de reevaluación en minutos
        ai_model: Modelo de IA a usar (ej: "gemini-2.0-flash-exp")
        enable_dual_orders: Si habilitar órdenes duales (Market + Limit)
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    """
    bot_id: int
    bot_name: str
    bot_type: str
    mode: BotMode = BotMode.DEMO
    symbols: List[str] = field(default_factory=lambda: ["EURUSD"])
    timeframes: List[Timeframe] = field(default_factory=lambda: [Timeframe.M1, Timeframe.M5, Timeframe.H1])
    trading_hours: Tuple[str, str] = ("06:00", "13:00")  # Lima time
    timezone_local: str = "America/Lima"
    risk_per_trade: float = 0.5  # 0.5%
    max_daily_risk: float = 2.0  # 2R
    reevaluation_interval_minutes: int = 10
    ai_model: str = "gemini-2.5-pro"  # Enforced por VertexAIConfig
    enable_dual_orders: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Validar configuración"""
        if self.bot_id not in [1, 2, 3, 4, 5]:
            raise ValueError(f"bot_id debe estar entre 1 y 5, recibido: {self.bot_id}")
        
        if self.bot_type not in ["numerico", "visual", "hibrido"]:
            raise ValueError(f"bot_type inválido: {self.bot_type}")
        
        if not self.symbols:
            raise ValueError("symbols no puede estar vacío")
        
        if self.risk_per_trade <= 0 or self.risk_per_trade > 5.0:
            raise ValueError(f"risk_per_trade debe estar entre 0 y 5.0, recibido: {self.risk_per_trade}")


class BaseBotOperations(ABC):
    """
    Clase base abstracta para todos los bots.
    
    Proporciona funcionalidad común y define la interfaz que deben
    implementar los bots específicos.
    
    Example:
        ```python
        class Bot1Numerico(BaseBotOperations):
            def prepare_data_for_ai(self, symbol, indicators, or_data):
                # Preparar datos numéricos
                return system_prompt, user_prompt
            
            def parse_ai_response(self, response_text):
                # Parsear respuesta IA
                return decision
        
        # Uso
        bot = Bot1Numerico(config)
        bot.initialize()
        bot.run_trading_cycle()
        ```
    """
    
    def __init__(self, config: BotConfig):
        """
        Inicializa el bot con configuración.
        
        Args:
            config: Configuración del bot
        """
        self.config = config
        self.logger = get_bot_logger(f"Bot{config.bot_id}_{config.bot_name}")
        
        # Componentes core (se inicializan en initialize())
        self.mt5_connection: Optional[MT5Connection] = None
        self.data_extractor: Optional[MT5DataExtractor] = None
        self.indicator_calculator: Optional[IndicatorCalculator] = None
        self.or_calculator: Optional[OpeningRangeCalculator] = None
        self.prompt_builder: Optional[PromptBuilder] = None
        self.response_parser: Optional[VWAPResponseParser] = None
        # Cliente IA (Vertex por defecto)
        self.ai_client: Optional[VertexAIClient] = None
        self.order_manager: Optional[DualOrderManager] = None
        
        # Estado del bot
        self.is_initialized = False
        self.current_pnl_r = 0.0
        self.trades_today = 0
        
        self.logger.info(
            f"Bot inicializado",
            extra={
                'bot_id': config.bot_id,
                'bot_name': config.bot_name,
                'bot_type': config.bot_type,
                'mode': config.mode.value
            }
        )
    
    def initialize(self) -> bool:
        """
        Inicializa todos los componentes del bot.
        
        Returns:
            bool: True si inicialización exitosa, False en caso contrario
        
        Raises:
            BotOperationError: Si hay error crítico en inicialización
        """
        try:
            self.logger.info("Iniciando inicialización de componentes...")
            
            # 1. Conexión MT5
            self.mt5_connection = MT5Connection()
            if not self.mt5_connection.connect():
                raise BotOperationError("No se pudo conectar a MT5")
            
            # 2. Data Extractor
            self.data_extractor = MT5DataExtractor(self.mt5_connection)
            
            # 3. Indicator Calculator
            self.indicator_calculator = IndicatorCalculator()
            
            # 4. Opening Range Calculator
            self.or_calculator = OpeningRangeCalculator()
            
            # 5. Prompt Builder
            self.prompt_builder = PromptBuilder()
            
            # 6. Response Parser
            self.response_parser = VWAPResponseParser()
            
            # 7. AI Client (Vertex por defecto)
            try:
                self.ai_client = VertexAIClient(
                    api_key=os.getenv("GOOGLE_API_KEY"),
                    config=VertexAIConfig(model=self.config.ai_model)
                )
            except Exception as e:
                # Fallback a Gemini solo si explícitamente disponible y variable de entorno lo permite
                allow_fallback = os.getenv("ALLOW_GEMINI_FALLBACK") == "1"
                if allow_fallback:
                    self.logger.warning(
                        f"VertexAIClient fallo ({e}). Intentando fallback GeminiClient..."
                    )
                    try:
                        self.ai_client = GeminiClient(
                            api_key=os.getenv("GEMINI_API_KEY"),
                            config=GeminiConfig(model=self.config.ai_model)
                        )
                    except Exception as eg:
                        raise BotOperationError(f"Fallo inicializando ambos clientes IA: {eg}") from eg
                else:
                    raise BotOperationError(f"Fallo inicializando VertexAIClient: {e}") from e
            
            # 8. Order Manager (si dual orders habilitado)
            if self.config.enable_dual_orders:
                self.order_manager = DualOrderManager(self.mt5_connection)
            
            self.is_initialized = True
            self.logger.info("✅ Todos los componentes inicializados correctamente")
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"❌ Error en inicialización: {str(e)}",
                extra={'error': str(e)},
                exc_info=True
            )
            return False
    
    def is_trading_hours(self) -> bool:
        """
        Verifica si estamos dentro del horario de trading permitido.
        
        Returns:
            bool: True si estamos en horario de trading
        """
        now = datetime.now()
        current_time = now.time()
        
        start_hour, start_min = map(int, self.config.trading_hours[0].split(":"))
        end_hour, end_min = map(int, self.config.trading_hours[1].split(":"))
        
        start_time = time(start_hour, start_min)
        end_time = time(end_hour, end_min)
        
        is_within_hours = start_time <= current_time <= end_time
        
        if not is_within_hours:
            self.logger.debug(
                f"Fuera de horario de trading",
                extra={
                    'current_time': current_time.strftime("%H:%M"),
                    'trading_hours': f"{self.config.trading_hours[0]} - {self.config.trading_hours[1]}"
                }
            )
        
        return is_within_hours
    
    def should_stop_trading_today(self) -> bool:
        """
        Verifica si debemos detener el trading por hoy.
        
        Criterios:
        - PnL del día alcanzó el límite negativo
        - PnL del día alcanzó objetivo positivo (opcional)
        
        Returns:
            bool: True si debemos detener trading
        """
        if self.current_pnl_r <= -self.config.max_daily_risk:
            self.logger.warning(
                f"⛔ Límite de pérdida diaria alcanzado",
                extra={
                    'current_pnl_r': self.current_pnl_r,
                    'max_daily_risk': self.config.max_daily_risk
                }
            )
            return True
        
        # TODO: Agregar lógica de objetivo diario si se desea
        
        return False
    
    def get_market_context(self) -> MarketContext:
        """
        Determina el contexto actual del mercado basado en la hora GMT.
        
        Returns:
            MarketContext: Contexto de mercado actual
        """
        now_gmt = datetime.utcnow()
        hour_gmt = now_gmt.hour
        minute_gmt = now_gmt.minute
        
        # Antes de la sesión europea
        if hour_gmt < 8:
            return MarketContext.PRE_MARKET
        
        # Durante Opening Range (08:00-08:30 GMT)
        elif hour_gmt == 8 and minute_gmt < 30:
            return MarketContext.OPENING_RANGE
        
        # Después de OR, sesión europea activa
        elif hour_gmt == 8 and minute_gmt >= 30:
            return MarketContext.POST_OR
        
        elif 9 <= hour_gmt < 16:
            return MarketContext.EUROPEAN_SESSION
        
        # Fin de sesión (16:00-17:00 GMT)
        elif 16 <= hour_gmt < 17:
            return MarketContext.END_OF_SESSION
        
        # Después de la sesión
        else:
            return MarketContext.POST_MARKET
    
    @abstractmethod
    def prepare_data_for_ai(
        self,
        symbol: str,
        indicators: Dict,
        or_data: Optional[Any],
        market_context: MarketContext
    ) -> Tuple[str, str]:
        """
        Prepara los datos para enviar a la IA.
        
        Este método debe ser implementado por cada bot específico
        según su tipo (numérico/visual/híbrido).
        
        Args:
            symbol: Símbolo del activo
            indicators: Diccionario de indicadores por timeframe
            or_data: Datos del Opening Range
            market_context: Contexto de mercado actual
        
        Returns:
            tuple: (system_prompt, user_prompt) o (system_prompt, user_prompt_with_images)
        """
        pass
    
    @abstractmethod
    def parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta de la IA y convierte a formato bot.
        
        Args:
            response_text: Texto de respuesta de la IA
        
        Returns:
            Dict con decisión parseada
        """
        pass
    
    def run_trading_cycle(self) -> None:
        """
        Ejecuta un ciclo completo de trading para todos los símbolos configurados.
        
        Flujo:
        1. Verificar horario de trading
        2. Verificar límites diarios
        3. Para cada símbolo:
           a. Extraer datos
           b. Calcular indicadores
           c. Consultar IA
           d. Ejecutar decisión (apertura/reevaluación)
        4. Registrar resultados
        """
        if not self.is_initialized:
            self.logger.error("Bot no inicializado. Ejecuta initialize() primero.")
            return
        
        # 1. Verificar horario
        if not self.is_trading_hours():
            self.logger.info("Fuera de horario de trading. Esperando...")
            return
        
        # 2. Verificar límites diarios
        if self.should_stop_trading_today():
            self.logger.warning("Trading detenido por límites diarios alcanzados")
            return
        
        # 3. Iterar por símbolos
        for symbol in self.config.symbols:
            try:
                self.logger.info(f"📊 Procesando {symbol}...")
                
                # Extraer datos y calcular indicadores
                indicators = self._calculate_all_indicators(symbol)
                
                # Calcular Opening Range
                or_data = self._calculate_opening_range(symbol)
                
                # Obtener contexto de mercado
                market_context = self.get_market_context()
                
                # Preparar datos para IA (implementado por subclase)
                system_prompt, user_prompt = self.prepare_data_for_ai(
                    symbol=symbol,
                    indicators=indicators,
                    or_data=or_data,
                    market_context=market_context
                )
                
                # Consultar IA
                ai_response = self._query_ai(system_prompt, user_prompt)
                
                if not ai_response:
                    self.logger.warning(f"No se obtuvo respuesta de IA para {symbol}")
                    continue
                
                # Parsear respuesta
                decision = self.parse_ai_response(ai_response)
                
                # Ejecutar decisión
                self._execute_decision(symbol, decision)
                
            except Exception as e:
                self.logger.error(
                    f"Error procesando {symbol}: {str(e)}",
                    extra={'symbol': symbol, 'error': str(e)},
                    exc_info=True
                )
                continue
    
    def _calculate_all_indicators(self, symbol: str) -> Dict:
        """
        Extrae datos y calcula indicadores para todos los timeframes.
        
        Args:
            symbol: Símbolo del activo
        
        Returns:
            Dict con indicadores por timeframe
        """
        indicators = {}
        
        for timeframe in self.config.timeframes:
            # Extraer datos OHLCV
            ohlcv_data = self.data_extractor.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                count=100  # Suficiente para EMA50 (ver DATA_REQUIREMENTS.md)
            )
            
            # Calcular indicadores
            indicator_data = self.indicator_calculator.calculate_indicators_for_timeframe(
                ohlcv_data=ohlcv_data
            )
            
            indicators[timeframe] = indicator_data
        
        return indicators
    
    def _calculate_opening_range(self, symbol: str) -> Optional[Any]:
        """
        Calcula el Opening Range para el símbolo.
        
        Args:
            symbol: Símbolo del activo
        
        Returns:
            OpeningRangeData o None si no aplica
        """
        try:
            # Extraer datos de la sesión actual (desde 08:00 GMT)
            ohlcv_data = self.data_extractor.get_ohlcv(
                symbol=symbol,
                timeframe=Timeframe.M5,
                count=100
            )
            
            or_data = self.or_calculator.calculate_opening_range(ohlcv_data)
            
            return or_data
            
        except Exception as e:
            self.logger.warning(
                f"No se pudo calcular Opening Range para {symbol}: {str(e)}",
                extra={'symbol': symbol, 'error': str(e)}
            )
            return None
    
    def _query_ai(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Consulta a la IA con retry automático.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_retries: Máximo número de reintentos
        
        Returns:
            Respuesta de la IA o None si falla
        """
        for attempt in range(1, max_retries + 1):
            try:
                # Unificar prompts para Vertex (no soporta system separado en nuestro wrapper)
                combined_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
                response_obj = self.ai_client.send_prompt(combined_prompt)

                if response_obj and response_obj.success:
                    self.logger.info(f"✅ Respuesta IA obtenida (intento {attempt})")
                    return response_obj.content or ""
                
            except Exception as e:
                self.logger.warning(
                    f"Intento {attempt}/{max_retries} falló: {str(e)}",
                    extra={'attempt': attempt, 'error': str(e)}
                )
                
                if attempt == max_retries:
                    self.logger.error(
                        f"❌ No se pudo obtener respuesta de IA después de {max_retries} intentos"
                    )
                    return None
        
        return None
    
    def _execute_decision(self, symbol: str, decision: Dict[str, Any]) -> None:
        """
        Ejecuta la decisión tomada por la IA.
        
        Args:
            symbol: Símbolo del activo
            decision: Decisión parseada de la IA
        """
        accion = decision.get("accion", "NO_OPERAR")
        
        if accion == "OPERAR":
            self._execute_open_position(symbol, decision)
        elif accion == "MANTENER":
            self.logger.info(f"Mantener posiciones actuales en {symbol}")
        elif accion == "CERRAR":
            self._execute_close_position(symbol, decision)
        elif accion == "ACTUALIZAR":
            self._execute_update_position(symbol, decision)
        else:  # NO_OPERAR
            self.logger.info(f"No operar en {symbol}")
    
    def _execute_open_position(self, symbol: str, decision: Dict[str, Any]) -> None:
        """Abre nueva posición (dual si está habilitado)"""
        self.logger.info(
            f"🚀 Abriendo posición en {symbol}",
            extra={'decision': decision}
        )
        
        # TODO: Implementar apertura usando DualOrderManager
        # if self.config.enable_dual_orders:
        #     self.order_manager.open_dual_position(...)
        # else:
        #     # Orden simple
        
        pass
    
    def _execute_close_position(self, symbol: str, decision: Dict[str, Any]) -> None:
        """Cierra posición abierta"""
        self.logger.info(
            f"🔴 Cerrando posición en {symbol}",
            extra={'decision': decision}
        )
        
        # TODO: Implementar cierre
        pass
    
    def _execute_update_position(self, symbol: str, decision: Dict[str, Any]) -> None:
        """Actualiza SL/TP de posición abierta"""
        self.logger.info(
            f"🔄 Actualizando posición en {symbol}",
            extra={'decision': decision}
        )
        
        # TODO: Implementar actualización
        pass
    
    def shutdown(self) -> None:
        """
        Cierra conexiones y limpia recursos.
        """
        self.logger.info("Cerrando bot...")
        
        if self.mt5_connection:
            self.mt5_connection.disconnect()
        
        self.logger.info("✅ Bot cerrado correctamente")
