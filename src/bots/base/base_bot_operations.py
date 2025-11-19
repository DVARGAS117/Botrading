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

from src.core.mt5_data_extractor import MT5DataExtractor, Timeframe
from src.core.indicator_calculator import IndicatorCalculator
from src.core.opening_range_calculator import OpeningRangeCalculator
from src.core.prompt_builder import PromptBuilder
from src.core.vwap_response_parser import VWAPResponseParser
from src.core.vwap_prompt_builder import MarketContext
from src.core.vertex_ai_client import VertexAIClient, VertexAIConfig
from src.core.gemini_client import GeminiClient, GeminiConfig  # Fallback opcional si se requiere en futuro
from src.core.ia_query_repository import IAQueryRepository, QueryType
from src.core.dual_order_manager import DualOrderManager, DualOrderRequest
from src.core.order_manager import OrderManager, OrderRequest, OrderType
from src.core.position_sizer import PositionSizer
from src.core.symbol_spec_extractor import SymbolSpecificationExtractor
from src.core.magic_number_generator import MagicNumberGenerator
from src.core.mt5_connector import MT5Connector, create_connector_from_credentials
from src.core.mt5_connection import MT5Connection as _LegacyMT5Connection  # Compat para tests antiguos

# Export legacy symbol esperado por algunos tests (@patch('src.bots.base.base_bot_operations.MT5Connection'))
MT5Connection = _LegacyMT5Connection
from src.core.config_loader import ConfigLoader, ConfigurationError
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
        ai_model: Modelo de IA a usar (ej: "gemini-2.5-pro")
        enable_dual_orders: Si habilitar órdenes duales (Market + Limit)
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    """
    bot_id: int
    bot_name: str
    bot_type: str
    mode: BotMode = BotMode.DEMO
    symbols: List[str] = field(default_factory=lambda: ["EURUSD"])
    timeframes: List[Timeframe] = field(default_factory=lambda: [Timeframe.M1, Timeframe.M5, Timeframe.H1])
    trading_hours: Tuple[str, str] = ("00:00", "23:59")  # 24/7 para testing
    timezone_local: str = "America/Lima"
    risk_per_trade: float = 0.5  # 0.5%
    max_daily_risk: float = 2.0  # 2R
    reevaluation_interval_minutes: int = 10
    ai_model: str = "gemini-3-pro-preview"  # Enforced por VertexAIConfig
    enable_dual_orders: bool = True
    log_level: str = "INFO"
    save_prompts: bool = False  # Si True: solo genera .txt SIN consultar Gemini (modo validación)
    
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
        self.mt5_connection: Optional[MT5Connector] = None
        self.data_extractor: Optional[MT5DataExtractor] = None
        self.indicator_calculator: Optional[IndicatorCalculator] = None
        self.or_calculator: Optional[OpeningRangeCalculator] = None
        self.prompt_builder: Optional[PromptBuilder] = None
        self.response_parser: Optional[VWAPResponseParser] = None
        # Cliente IA (Vertex por defecto)
        self.ai_client: Optional[VertexAIClient] = None
        # Repositorio de consultas IA (tokens y costos)
        self.ia_query_repo: Optional[IAQueryRepository] = None
        # Gestión de órdenes / sizing / specs / magic
        self.order_manager: Optional[OrderManager] = None
        self.dual_order_manager: Optional[DualOrderManager] = None
        self.position_sizer: Optional[PositionSizer] = None
        self.symbol_spec_extractor: Optional[SymbolSpecificationExtractor] = None
        self.magic_number_generator: Optional[MagicNumberGenerator] = None
        
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
            # Log de diagnóstico de intérprete y versión
            import sys
            self.logger.debug(
                "Diagnóstico intérprete Python",
                extra={
                    'python_executable': sys.executable,
                    'python_version': sys.version,
                }
            )
            
            # 1. Conexión real a MT5 (sin mocks)
            try:
                creds_path = Path("config/credentials.json")
                if not creds_path.exists():
                    raise BotOperationError("No se encontró config/credentials.json para MT5")
                loader = ConfigLoader()
                creds = loader.load_json_config(str(creds_path))
                # Soporte para estructuras {mt5: {...}} o planas
                mt5_creds = creds.get("mt5", creds)
                self.mt5_connection = create_connector_from_credentials(mt5_creds, logger=self.logger)
                self.mt5_connection.verify_connection()
            except (ConfigurationError, Exception) as e:
                raise BotOperationError(f"Error al configurar/conectar MT5: {e}")

            # 2. Extractor de datos MT5
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
                # Load API key from credentials
                gemini_creds = creds.get("gemini", {})
                api_key = gemini_creds.get("api_key")
                if not api_key:
                    raise BotOperationError("Falta API key de Gemini en config/credentials.json")
                
                model_to_use = self.config.ai_model
                if model_to_use != "gemini-3-pro-preview" and os.getenv("ALLOW_CUSTOM_GEMINI_MODEL") != "1":
                    self.logger.warning(
                        f"Modelo '{model_to_use}' reemplazado por 'gemini-3-pro-preview' (enforcement)"
                    )
                    model_to_use = "gemini-3-pro-preview"
                    self.config.ai_model = model_to_use
                self.ai_client = VertexAIClient(
                    api_key=api_key,
                    config=VertexAIConfig(model=model_to_use)
                )
                # Inicializar repositorio de consultas IA (persistencia costo por consulta)
                self.ia_query_repo = IAQueryRepository(Path("data/ia_queries.db"))
            except Exception as e:
                # Fallback a Gemini solo si explícitamente disponible y variable de entorno lo permite
                allow_fallback = os.getenv("ALLOW_GEMINI_FALLBACK") == "1"
                if allow_fallback:
                    self.logger.warning(
                        f"VertexAIClient fallo ({e}). Intentando fallback GeminiClient..."
                    )
                    try:
                        self.ai_client = GeminiClient(
                            api_key=api_key,
                            config=GeminiConfig(model=self.config.ai_model)
                        )
                        self.ia_query_repo = IAQueryRepository(Path("data/ia_queries.db"))
                    except Exception as eg:
                        raise BotOperationError(f"Fallo inicializando ambos clientes IA: {eg}") from eg
                else:
                    raise BotOperationError(f"Fallo inicializando VertexAIClient: {e}") from e
            
            # 8. Order Manager + DualOrderManager + helpers
            try:
                self.order_manager = OrderManager(self.mt5_connection, logger=self.logger)
                self.position_sizer = PositionSizer(logger=self.logger)
                self.magic_number_generator = MagicNumberGenerator(logger=self.logger)
                self.symbol_spec_extractor = SymbolSpecificationExtractor(self.mt5_connection, logger=self.logger)
                if self.config.enable_dual_orders:
                    self.dual_order_manager = DualOrderManager(
                        order_manager=self.order_manager,
                        position_sizer=self.position_sizer,
                        magic_number_generator=self.magic_number_generator,
                        logger=self.logger
                    )
            except Exception as oe:
                self.logger.warning(
                    f"No se pudo inicializar gestores de órdenes: {oe}",
                    extra={'error': str(oe)}
                )
            
            self.is_initialized = True
            self.logger.info("✅ Todos los componentes inicializados correctamente")
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"❌ Error en inicialización: {str(e)}",
                extra={'error': str(e)}
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
        market_context: MarketContext,
        ohlcv_data: Optional[Dict] = None
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
                indicators, ohlcv_data_dict = self._calculate_all_indicators(symbol)
                
                # Calcular Opening Range
                or_data = self._calculate_opening_range(symbol)
                
                # Obtener contexto de mercado
                market_context = self.get_market_context()
                
                # Preparar datos para IA (implementado por subclase)
                system_prompt, user_prompt = self.prepare_data_for_ai(
                    symbol=symbol,
                    indicators=indicators,
                    or_data=or_data,
                    market_context=market_context,
                    ohlcv_data=ohlcv_data_dict
                )
                
                # Consultar IA
                response_obj, combined_prompt = self._query_ai(system_prompt, user_prompt)

                if not response_obj or not response_obj.success:
                    self.logger.warning(f"No se obtuvo respuesta de IA para {symbol}")
                    continue
                
                # Parsear respuesta
                # Log línea adicional: respuesta cruda antes de parsear
                ai_raw_text = response_obj.content or ""
                try:
                    trimmed = ai_raw_text.strip()
                    if len(trimmed) > 800:
                        trimmed = trimmed[:800] + "... [truncado]"
                    self.logger.info(f"respuesta original IA: {trimmed}")
                except Exception:
                    self.logger.info("respuesta original IA: [no disponible por error de decodificación]")
                decision = self.parse_ai_response(ai_raw_text)

                # Log línea adicional: resumen de decisión parseada
                try:
                    accion = decision.get('accion')
                    direccion = decision.get('direccion')
                    razonamiento = decision.get('razonamiento') or ''
                    resumen = f"accion={accion} direccion={direccion} razonamiento={razonamiento[:120]}"
                    self.logger.info(f"decision parseada: {resumen}")
                except Exception:
                    self.logger.info("decision parseada: [error al acceder a campos]")
                
                # Ejecutar decisión
                self._execute_decision(symbol, decision)

                # Persistir consulta IA con costos/tokens si repo disponible
                try:
                    if self.ia_query_repo and isinstance(response_obj.tokens_input, int):
                        accion_decidida = str(decision.get('accion') or '').upper()
                        # Normalizar acción para almacenamiento
                        if accion_decidida in ("ABRIR",):
                            accion_decidida = "OPERAR"
                        elif accion_decidida in ("ESPERAR",):
                            accion_decidida = "NO_OPERAR"
                        self.ia_query_repo.create_query(
                            bot_id=self.config.bot_id,
                            ia_id=1,  # Config única actual
                            symbol=symbol,
                            query_type=QueryType.EVALUATION,
                            prompt=combined_prompt,
                            response=ai_raw_text,
                            tokens_input=response_obj.tokens_input or 0,
                            tokens_output=response_obj.tokens_output or 0,
                            cost_usd=response_obj.cost or 0.0,
                            action_decided=accion_decidida
                        )
                        self.logger.info(
                            "Consulta IA persistida",
                            extra={
                                'tokens_input': response_obj.tokens_input or 0,
                                'tokens_output': response_obj.tokens_output or 0,
                                'cost_usd': response_obj.cost or 0.0
                            }
                        )
                except Exception as pe:
                    self.logger.warning(f"No se pudo persistir consulta IA: {pe}")
                
            except Exception as e:
                self.logger.error(
                    f"Error procesando {symbol}: {str(e)}",
                    extra={'symbol': symbol, 'error': str(e)}
                )
                continue
    
    def _calculate_all_indicators(self, symbol: str) -> Tuple[Dict, Dict]:
        """
        Extrae datos y calcula indicadores para todos los timeframes.
        
        Args:
            symbol: Símbolo del activo
        
        Returns:
            Tuple: (indicators dict, ohlcv_data dict) por timeframe
        """
        indicators = {}
        ohlcv_data_dict = {}
        
        for timeframe in self.config.timeframes:
            # Determinar cantidad de velas según timeframe
            if timeframe == Timeframe.M1:
                count = 200  # Timeframe de timing: 200 velas M1
            elif timeframe == Timeframe.M5:
                count = 100  # Timeframe principal: velas de sesión (aprox 60-100)
            elif timeframe == Timeframe.H1:
                count = 50   # Timeframe de contexto: mínimo 50 para EMA50 (aunque user dijo 30 max)
            else:
                count = 100  # Default
            
            # Extraer datos OHLCV
            ohlcv_data = self.data_extractor.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                count=count
            )
            
            # Calcular indicadores
            indicator_data = self.indicator_calculator.calculate_indicators_for_timeframe(
                ohlcv_data=ohlcv_data
            )
            
            indicators[timeframe] = indicator_data
            ohlcv_data_dict[timeframe] = ohlcv_data
        
        return indicators, ohlcv_data_dict
    
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
            
            or_data = self.or_calculator.calculate_opening_range(ohlcv_data.data)
            
            return or_data
            
        except Exception as e:
            self.logger.warning(
                f"No se pudo calcular Opening Range para {symbol}: {str(e)}",
                extra={'symbol': symbol, 'error': str(e)}
            )
            return None
    
    def _query_ai(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> Tuple[Optional[Any], str]:
        """
        Consulta a la IA con retry automático.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_retries: Máximo número de reintentos
        
        Returns:
            Tuple (GeminiResponse|None, combined_prompt)
        """
        for attempt in range(1, max_retries + 1):
            try:
                # Unificar prompts para Vertex (no soporta system separado en nuestro wrapper)
                combined_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
                
                # Guardar prompt si está habilitado
                if self.config.save_prompts:
                    from datetime import datetime
                    from pathlib import Path
                    
                    # Crear carpeta de prompts dentro del directorio del bot
                    # Estructura: src/bots/bot_X/prompts/YYYYMMDD/
                    bot_dir = Path(__file__).parent.parent / f"bot_{self.config.bot_id}"
                    prompts_dir = bot_dir / "prompts" / datetime.now().strftime("%Y%m%d")
                    prompts_dir.mkdir(parents=True, exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    symbol = self.config.symbols[0] if self.config.symbols else 'unknown'
                    filename = prompts_dir / f"prompt_{timestamp}_{symbol}.txt"
                    
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"=== PROMPT ENVIADO A IA ===\n")
                            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                            f.write(f"Bot: {self.config.bot_name} (ID: {self.config.bot_id})\n")
                            f.write(f"Símbolo: {symbol}\n")
                            f.write(f"Modo: {self.config.mode.value}\n")
                            f.write(f"Intento: {attempt}\n\n")
                            f.write("=== SYSTEM PROMPT ===\n")
                            f.write(system_prompt or "None")
                            f.write("\n\n=== USER PROMPT ===\n")
                            f.write(user_prompt)
                            f.write("\n\n=== COMBINED PROMPT ===\n")
                            f.write(combined_prompt)
                        self.logger.info(f"💾 Prompt guardado en: {filename}")
                        self.logger.info("✅ Modo validación: Prompt generado sin consultar a Gemini (--save-prompts activo)")
                        # Retornar respuesta simulada sin consultar a Gemini (ahorra tokens)
                        from src.core.gemini_client import GeminiResponse
                        dummy = GeminiResponse(success=True, content="[PROMPT_ONLY_MODE]", tokens_input=0, tokens_output=0, cost=0.0)
                        return dummy, combined_prompt
                    except Exception as e:
                        self.logger.warning(f"No se pudo guardar prompt: {e}")
                        return None
                
                response_obj = self.ai_client.send_prompt(combined_prompt)

                if response_obj and response_obj.success:
                    self.logger.info(f"✅ Respuesta IA obtenida (intento {attempt})")
                    return response_obj, combined_prompt
                
            except Exception as e:
                self.logger.warning(
                    f"Intento {attempt}/{max_retries} falló: {str(e)}",
                    extra={'attempt': attempt, 'error': str(e)}
                )
                
                if attempt == max_retries:
                    self.logger.error(
                        f"❌ No se pudo obtener respuesta de IA después de {max_retries} intentos"
                    )
                    return None, combined_prompt
        return None, combined_prompt
    
    def _execute_decision(self, symbol: str, decision: Dict[str, Any]) -> None:
        """
        Ejecuta la decisión tomada por la IA.
        
        Args:
            symbol: Símbolo del activo
            decision: Decisión parseada de la IA
        """
        accion_raw = decision.get("accion", "NO_OPERAR")
        accion = str(accion_raw).upper()
        # Aceptar sinónimos provenientes de parseadores alternativos
        if accion in ("ABRIR",):
            accion = "OPERAR"
        if accion in ("ESPERAR",):
            accion = "NO_OPERAR"

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
        
        try:
            if not self.mt5_connection or not self.order_manager:
                self.logger.error("Gestores de órdenes no inicializados")
                return

            # Dirección
            dir_raw = (decision.get("direccion") or "").lower()
            if dir_raw in ("comprar", "long"):
                direction = "buy"
            elif dir_raw in ("vender", "short"):
                direction = "sell"
            elif dir_raw in ("buy", "sell"):
                direction = dir_raw
            else:
                self.logger.warning(f"Dirección inválida/ausente en decisión: '{dir_raw}'")
                return

            # Precios
            entry_price = decision.get("precio_entrada")
            stop_loss = decision.get("stop_loss")
            take_profit = decision.get("take_profit") or decision.get("take_profit_1")

            if not stop_loss or not take_profit:
                self.logger.warning("Decisión sin SL/TP válidos; no se abrirá operación")
                return

            # Precio actual si no hay entrada explícita
            tick = self.mt5_connection._mt5.symbol_info_tick(symbol)
            if entry_price is None and tick is not None:
                entry_price = tick.ask if direction == "buy" else tick.bid

            # Balance de cuenta y especificaciones
            account = self.mt5_connection.get_account_info()
            balance = float(getattr(account, 'balance', 0.0))
            symbol_spec = self.symbol_spec_extractor.get_symbol_specification(symbol)

            risk_pct = float(self.config.risk_per_trade)

            # Intentar apertura dual si está habilitado y tenemos precio límite
            limit_price = decision.get("precio_limite")
            use_dual = self.config.enable_dual_orders and self.dual_order_manager is not None and limit_price is not None

            if use_dual:
                req = DualOrderRequest(
                    symbol=symbol,
                    direction=direction,
                    account_balance=balance,
                    risk_percentage=risk_pct,
                    entry_price=float(entry_price),
                    stop_loss=float(stop_loss),
                    take_profit=float(take_profit),
                    limit_price=float(limit_price),
                    bot_id=self.config.bot_id,
                    ia_config_id=0,
                    symbol_spec=symbol_spec,
                    comment=f"Bot{self.config.bot_id}-{self.config.bot_name}"
                )
                result = self.dual_order_manager.open_dual_orders(req)
                self.logger.info(
                    "Órdenes duales enviadas",
                    extra={
                        'market_ticket': result.market_order.order if result.market_order else None,
                        'limit_ticket': result.limit_order.order if result.limit_order else None,
                        'lot_size': result.lot_size
                    }
                )
            else:
                # Apertura Market simple
                order_type = OrderType.BUY if direction == "buy" else OrderType.SELL
                # Magic number para orden simple
                magic = 0
                if self.magic_number_generator:
                    magic = self.magic_number_generator.generate(
                        bot_id=self.config.bot_id,
                        ia_config_id=0,
                        order_type="market"
                    )
                request = OrderRequest(
                    symbol=symbol,
                    order_type=order_type,
                    volume=max(symbol_spec.volume_min, symbol_spec.volume_step),
                    price=float(entry_price),
                    sl=float(stop_loss),
                    tp=float(take_profit),
                    magic=magic,
                    comment=f"Bot{self.config.bot_id}-{self.config.bot_name}"
                )
                result = self.order_manager.send_market_order(request)
                self.logger.info(
                    "Orden Market enviada",
                    extra={
                        'ticket': result.order,
                        'price': result.price,
                        'volume': result.volume
                    }
                )
        except Exception as e:
            self.logger.error(
                f"Error al abrir posición en {symbol}: {e}",
                extra={'error': str(e)}
            )
    
    def _execute_close_position(self, symbol: str, decision: Dict[str, Any]) -> None:
        """Cierra posición abierta"""
        self.logger.info(
            f"🔴 Cerrando posición en {symbol}",
            extra={'decision': decision}
        )
        
        try:
            if not self.order_manager:
                self.logger.error("OrderManager no inicializado")
                return
            ticket = decision.get("ticket")
            if ticket:
                self.order_manager.close_position(ticket=int(ticket))
            else:
                # Sin ticket explícito, evitar cerrar en masa por seguridad
                self.logger.warning("Sin 'ticket' en decisión; cierre manual requerido")
        except Exception as e:
            self.logger.error(
                f"Error al cerrar posición en {symbol}: {e}",
                extra={'error': str(e)}
            )
    
    def _execute_update_position(self, symbol: str, decision: Dict[str, Any]) -> None:
        """Actualiza SL/TP de posición abierta"""
        self.logger.info(
            f"🔄 Actualizando posición en {symbol}",
            extra={'decision': decision}
        )
        
        try:
            if not self.order_manager:
                self.logger.error("OrderManager no inicializado")
                return
            ticket = decision.get("ticket")
            new_sl = decision.get("nuevo_stop_loss")
            new_tp = decision.get("nuevo_take_profit")
            if not ticket or (new_sl is None and new_tp is None):
                self.logger.warning("Faltan 'ticket' o nuevos valores SL/TP para actualizar")
                return
            self.order_manager.modify_position(
                ticket=int(ticket),
                sl=float(new_sl) if new_sl is not None else 0.0,
                tp=float(new_tp) if new_tp is not None else 0.0
            )
        except Exception as e:
            self.logger.error(
                f"Error al actualizar posición en {symbol}: {e}",
                extra={'error': str(e)}
            )
    
    def shutdown(self) -> None:
        """
        Cierra conexiones y limpia recursos.
        """
        self.logger.info("Cerrando bot...")
        
        if self.mt5_connection:
            self.mt5_connection.disconnect()
        
        self.logger.info("✅ Bot cerrado correctamente")
