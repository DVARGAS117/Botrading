"""Estrategia del Bot 1 (INTRADAY Gemini 3 Pro).

Esta clase implementa la lógica específica de la estrategia INTRADAY,
heredando de BaseBotOperations para aprovechar la funcionalidad común.

La estrategia INTRADAY se enfoca en operaciones dentro del día, buscando
aprovechar movimientos de precio en marcos temporales cortos (M1, M5, M15, H1).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Tuple

from src.bots.base.base_bot_operations import BaseBotOperations, BotConfig
from src.bots.strategies.intraday.gemini_3_pro.bot_1.intraday_indicators import (
    IntradayIndicatorCalculator,
    generate_operation_id,
)
from src.core.ia_query_repository import IAQueryRepository, QueryType
from src.core.mt5_data_extractor import MT5DataExtractor
from src.core.operations_repository import (
    Direction,
    OperationsRepository,
    OperationStatus,
    OrderType as DBOrderType,
)
from src.core.order_manager import OrderRequest, OrderType
from src.core.position_manager import PositionManager
from src.core.vertex_ai_client import VertexAIClient, VertexAIConfig
from src.core.enhanced_magic_number_generator import EnhancedMagicNumberGenerator
from src.core.agent_variant_codes import resolve_codes
from src.core.sequence_manager import SequenceManager
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
        
        # Indicador de que necesitamos IntradayIndicatorCalculator
        self._use_intraday_calculator = True
        
        # Inicializar repositorio de consultas IA
        db_path = Path(__file__).parent.parent.parent.parent.parent.parent / "data" / "consultas_ia.db"
        self.ia_query_repository = IAQueryRepository(db_path)
        
        # Inicializar repositorio de operaciones
        ops_db_path = Path(__file__).parent.parent.parent.parent.parent.parent / "data" / "operations.db"
        self.operations_repo = OperationsRepository(ops_db_path)
        
        # Inicializar cliente Vertex AI (Gemini 3 Pro) - se hará en initialize()
        # vertex_config = VertexAIConfig(
        #     model="gemini-3-pro-preview",
        #     temperature=0.7,
        #     max_tokens=8192,
        #     top_p=0.95,
        #     timeout=120,
        # )
        # self.vertex_client = VertexAIClient(config=vertex_config)
        self.vertex_client = None  # Se inicializará en initialize()
        
        # Inicializar _position_manager (lazy loading)
        self._position_manager = None

        # Enhanced magic v2 helpers
        self._magic_v2 = EnhancedMagicNumberGenerator()
        self._seq_manager = SequenceManager()
        
        # Configurar logger específico del bot con directorio propio
        from src.core.logger import LogConfig, LogLevel
        
        bot_dir = Path(__file__).parent
        log_dir = bot_dir / "logs"
        
        # Convertir log_level string a LogLevel enum
        try:
            level_enum = LogLevel[self.config.log_level.upper()]
        except KeyError:
            level_enum = LogLevel.INFO  # Default fallback
        
        log_config = LogConfig(
            level=level_enum,
            log_dir=str(log_dir),
            log_to_console=True,
            log_to_file=True,
            format_json=False
        )
        
        # Reemplazar el logger de la clase base
        from src.core.logger import get_bot_logger
        self.logger = get_bot_logger(f"Bot{self.config.bot_id}_{self.config.bot_name}", log_config)
        
        # Ruta a los prompts (usar config/prompt_templates/)
        # Subir 6 niveles desde strategy.py hasta raíz del proyecto
        self.prompts_dir = Path(__file__).parent.parent.parent.parent.parent.parent.parent / "config" / "prompt_templates"

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
    
    def initialize(self) -> bool:
        """Inicializa componentes base y luego crea IntradayIndicatorCalculator.
        
        Returns:
            True si la inicialización fue exitosa, False en caso contrario
        """
        # Primero inicializar componentes base (MT5, data_extractor, etc.)
        if not super().initialize():
            return False
        
        # Ahora que data_extractor está disponible, crear IntradayIndicatorCalculator
        self.indicator_calculator = IntradayIndicatorCalculator(self.data_extractor)
        
        # Inicializar cliente Vertex AI (Gemini 3 Pro) ahora que tenemos la API key
        vertex_config = VertexAIConfig(
            model="gemini-3-pro-preview",
            temperature=0.7,
            max_tokens=8192,
            top_p=0.95,
            timeout=120,
        )
        self.vertex_client = VertexAIClient(config=vertex_config)
        
        self.logger.info(
            "IntradayIndicatorCalculator inicializado",
            extra={
                "calculator_type": "IntradayIndicatorCalculator",
            },
        )
        
        return True
    
    def run_trading_cycle(self) -> None:
        """
        Sobrescribe el ciclo de trading base para usar execute_cycle específico de INTRADAY.
        
        Este método verifica las condiciones base (horario, límites) y luego
        delega la ejecución específica del ciclo INTRADAY a execute_cycle.
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
        
        # 3. Obtener símbolos activos en la sesión actual
        active_symbols = self._get_active_symbols_for_trading()
        
        if not active_symbols:
            session_info = self.session_manager.get_current_session() if self.session_manager else {}
            session_name = session_info.get('name', 'desconocida')
            self.logger.info(
                f"⏸️  No hay símbolos permitidos en la sesión actual ({session_name})",
                extra={'session': session_name, 'time': datetime.now().strftime('%H:%M')}
            )
            return
        
        self.logger.info(
            f"✅ Símbolos activos para operar: {', '.join(active_symbols)}",
            extra={'symbols': active_symbols, 'count': len(active_symbols)}
        )
        
        # 4. Ejecutar ciclo INTRADAY para cada símbolo activo
        for symbol in active_symbols:
            try:
                self.logger.info(f"📊 Procesando {symbol}...")
                
                # Ejecutar ciclo INTRADAY específico (prepara datos, consulta IA, ejecuta decisión)
                decision = self.execute_cycle(symbol)
                
                # Ejecutar la decisión tomada por la IA
                self._execute_decision(symbol, decision)
                
                # Actualizar métricas de rendimiento
                self._update_performance_metrics(symbol, decision)
                
            except Exception as e:
                self.logger.error(
                    f"Error procesando {symbol}: {str(e)}",
                    extra={'symbol': symbol, 'error': str(e)}
                )
                continue

    def prepare_data_for_ai(
        self,
        symbol: str,
        indicators: Dict,
        or_data: Optional[Any],
        market_context: MarketContext,
        ohlcv_data: Optional[Dict] = None,
    ) -> Tuple[str, str]:
        """
        Sobrescribe método base para retornar tupla (system_prompt, user_prompt).
        
        El método base espera una tupla de dos strings, pero la implementación
        INTRADAY necesita más datos. Este método extrae solo los prompts
        del diccionario completo retornado por _prepare_intraday_data_for_ai.
        
        Args:
            symbol: Símbolo a analizar (ej: "EURUSD")
            indicators: Diccionario con valores de indicadores técnicos (NO USADO)
            or_data: Datos del Opening Range (opcional, NO USADO en INTRADAY)
            market_context: Contexto de mercado actual
            ohlcv_data: Datos OHLCV históricos (opcional, NO USADO)
            
        Returns:
            Tupla (system_prompt, user_prompt) para compatibilidad con código base
        """
        # Obtener datos completos INTRADAY
        intraday_data = self._prepare_intraday_data_for_ai(
            symbol=symbol,
            indicators=indicators,
            or_data=or_data,
            market_context=market_context,
            ohlcv_data=ohlcv_data
        )
        
        # Retornar solo los prompts como tupla para compatibilidad
        return intraday_data["system_prompt"], intraday_data["user_prompt"]

    def _prepare_intraday_data_for_ai(
        self,
        symbol: str,
        indicators: Dict,
        or_data: Optional[Any],
        market_context: MarketContext,
        ohlcv_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Método interno que prepara datos completos INTRADAY para la IA.
        
        Este método contiene la lógica completa de preparación de datos
        específica de INTRADAY, retornando un diccionario con toda la
        información necesaria.
        
        Args:
            symbol: Símbolo a analizar (ej: "EURUSD")
            indicators: Diccionario con valores de indicadores técnicos (NO USADO)
            or_data: Datos del Opening Range (opcional, NO USADO en INTRADAY)
            market_context: Contexto de mercado actual
            ohlcv_data: Datos OHLCV históricos (opcional, NO USADO)
            
        Returns:
            Diccionario con toda la información INTRADAY
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
            tactical_package = packages["tactical_m15"]
            strategic_package = packages["strategic_d1"]
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
        system_prompt_path = self.prompts_dir / "intraday_gemini_3_pro_bot_1_system.txt"
        user_prompt_path = self.prompts_dir / "intraday_gemini_3_pro_bot_1_user.txt"
        
        # Determinar si hay operación activa
        has_active_position = self._has_active_position(symbol)
        
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
        
        # Construir información de posición
        if has_active_position:
            current_position = self._get_current_position_info(symbol)
            
            # Obtener SL inicial desde BD
            sl_inicial = self._get_initial_sl_from_db(symbol)
            if sl_inicial is None:
                sl_inicial = current_position['sl']
            
            # Calcular riesgo inicial (R) con SL inicial
            pip_value = 0.01 if "JPY" in symbol else 0.0001
            risk_points = abs(current_position['price_open'] - sl_inicial)
            risk_pips = risk_points / pip_value
            
            # Calcular PnL en R basado en SL inicial
            if current_position['type'] == "LONG":
                pnl_points = current_position['price_current'] - current_position['price_open']
            else:
                pnl_points = current_position['price_open'] - current_position['price_current']
            pnl_r = pnl_points / risk_points if risk_points > 0 else 0.0
            
            # Determinar si SL fue ajustado
            sl_ajustado_nota = ""
            if abs(current_position['sl'] - sl_inicial) > pip_value * 0.1:
                sl_ajustado_nota = f" (⚠️ SL inicial: {sl_inicial}, ajustado a: {current_position['sl']})"
            
            # Recuperar riesgo persistido (si existe operación)
            riesgo_linea = ""
            if current_position.get('magic') and self.operations_repo:
                try:
                    op = self.operations_repo.get_operation_by_magic_number(int(current_position['magic']))
                    if op:
                        riesgo_linea = f"- Riesgo Objetivo: {op.risk_percentage:.2f}% (~${op.risk_amount:.2f})\n"
                except Exception:
                    pass
            if not riesgo_linea:
                riesgo_linea = f"- Riesgo Objetivo: {self.config.risk_per_trade:.2f}% (config)\n"

            position_text = f"""POSICIÓN ACTIVA: {current_position['type']} @ {current_position['price_open']}
- Volumen: {current_position['volume']} lotes
- PnL Actual: ${current_position['profit']:.2f} USD ({current_position['pnl_pips']:.1f} pips = {pnl_r:.2f}R)
- Stop Loss Actual: {current_position['sl']}{sl_ajustado_nota}
- Take Profit: {current_position['tp']}
- Precio Actual: {current_position['price_current']}
- Duración: {current_position.get('duration', 'N/A')}
- Riesgo Inicial (1R): {risk_pips:.1f} pips (basado en SL inicial: {sl_inicial})
{riesgo_linea}
⚠️ PRIORIDAD: Gestiona esta posición. Evalúa si debe CERRARSE, AJUSTAR_SL_TP o MANTENERSE."""
        else:
            position_text = """POSICIÓN ACTUAL: NONE (Sin posición abierta)

✅ Puedes evaluar nuevas oportunidades de entrada (COMPRAR/VENDER) si hay setup válido."""
        
        user_prompt = user_prompt.replace("{current_position}", position_text)
        
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

    @property
    def position_manager(self) -> PositionManager:
        """Property lazy para position_manager.
        
        Se inicializa solo cuando se accede por primera vez,
        garantizando que mt5_connection ya esté disponible.
        """
        if self._position_manager is None:
            if self.mt5_connection is None:
                raise ValueError(
                    "mt5_connection no está inicializada. "
                    "Llama a initialize() antes de usar position_manager"
                )
            self._position_manager = PositionManager(self.mt5_connection)
        return self._position_manager

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
            tactical_package = packages["tactical_m15"]
            strategic_package = packages["strategic_d1"]
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
        # Usar los archivos reales de config/prompt_templates/
        system_prompt_path = self.prompts_dir / "intraday_gemini_3_pro_bot_1_system.txt"
        user_prompt_path = self.prompts_dir / "intraday_gemini_3_pro_bot_1_user.txt"
        
        # Determinar si hay operación activa (siempre usamos el mismo user prompt)
        has_active_position = self._has_active_position(symbol)
        
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
        
        # Construir información de posición (con o sin posición activa)
        if has_active_position:
            current_position = self._get_current_position_info(symbol)
            
            # Obtener SL inicial desde BD (operations table)
            sl_inicial = self._get_initial_sl_from_db(symbol)
            if sl_inicial is None:
                # Fallback: usar SL actual
                sl_inicial = current_position['sl']
            
            # Calcular riesgo inicial (R) con SL inicial
            pip_value = 0.01 if "JPY" in symbol else 0.0001
            risk_points = abs(current_position['price_open'] - sl_inicial)
            risk_pips = risk_points / pip_value
            
            # Calcular PnL en R basado en SL inicial
            if current_position['type'] == "LONG":
                pnl_points = current_position['price_current'] - current_position['price_open']
            else:
                pnl_points = current_position['price_open'] - current_position['price_current']
            pnl_r = pnl_points / risk_points if risk_points > 0 else 0.0
            
            # Determinar si SL fue ajustado
            sl_ajustado_nota = ""
            if abs(current_position['sl'] - sl_inicial) > pip_value * 0.1:  # Diferencia significativa
                sl_ajustado_nota = f" (⚠️ SL inicial: {sl_inicial}, ajustado a: {current_position['sl']})"
            
            position_text = f"""POSICIÓN ACTIVA: {current_position['type']} @ {current_position['price_open']}
- Volumen: {current_position['volume']} lotes
- PnL Actual: ${current_position['profit']:.2f} USD ({current_position['pnl_pips']:.1f} pips = {pnl_r:.2f}R)
- Stop Loss Actual: {current_position['sl']}{sl_ajustado_nota}
- Take Profit: {current_position['tp']}
- Precio Actual: {current_position['price_current']}
- Duración: {current_position.get('duration', 'N/A')}
- Riesgo Inicial (1R): {risk_pips:.1f} pips (basado en SL inicial: {sl_inicial})

⚠️ PRIORIDAD: Gestiona esta posición. Evalúa si debe CERRARSE, AJUSTAR_SL_TP o MANTENERSE."""
        else:
            position_text = """POSICIÓN ACTUAL: NONE (Sin posición abierta)

✅ Puedes evaluar nuevas oportunidades de entrada (COMPRAR/VENDER) si hay setup válido."""
        
        user_prompt = user_prompt.replace("{current_position}", position_text)
        
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
            prepared_data = self._prepare_intraday_data_for_ai(
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
        
        # Construir prompt completo para Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Guardar prompt si está habilitado (antes de consultar a Gemini)
        if self.config.save_prompts:
            self._save_prompt_to_file(system_prompt, user_prompt, full_prompt, symbol, 1)
            self.logger.info("✅ Modo validación: Prompt generado sin consultar a Gemini (--save-prompts activo)")
            # Retornar respuesta simulada sin consultar a Gemini (ahorra tokens)
            from src.core.gemini_client import GeminiResponse
            dummy = GeminiResponse(success=True, content="[PROMPT_ONLY_MODE]", tokens_input=0, tokens_output=0, cost=0.0)
            
            # Crear respuesta simulada con estructura esperada
            ai_response = {
                "response_text": "[PROMPT_ONLY_MODE]",
                "tokens_input": 0,
                "tokens_output": 0,
                "cost_usd": 0.0,
            }
        else:
            # Llamar a Vertex AI (Gemini 3 Pro)
            try:
                gemini_response = self.vertex_client.send_prompt(full_prompt)
                
                if not gemini_response.success:
                    self.logger.error(
                        f"Error en respuesta de Gemini para {symbol}: {gemini_response.error_message}",
                        extra={
                            "symbol": symbol,
                            "operation_id": operation_id,
                            "error_type": gemini_response.error_type,
                        },
                    )
                    raise Exception(f"Gemini API error: {gemini_response.error_message}")
                
                ai_response = {
                    "response_text": gemini_response.content,
                    "tokens_input": gemini_response.tokens_input or 0,
                    "tokens_output": gemini_response.tokens_output or 0,
                    "cost_usd": gemini_response.cost or 0.0,
                }
                
                self.logger.info(
                    f"Respuesta de Gemini recibida para {symbol}",
                    extra={
                        "symbol": symbol,
                        "operation_id": operation_id,
                        "tokens_total": gemini_response.total_tokens,
                        "cost_usd": ai_response["cost_usd"],
                        "latency": gemini_response.latency,
                    },
                )
                
            except Exception as e:
                self.logger.error(
                    f"Error consultando Gemini para {symbol}: {e}",
                    extra={
                        "symbol": symbol,
                        "operation_id": operation_id,
                        "error": str(e),
                    },
                )
                raise
        
        # 3. Parsear respuesta
        try:
            # Log respuesta cruda antes de parsear
            raw_response = ai_response["response_text"]
            self.logger.info(f"Respuesta cruda de Gemini: {raw_response[:1000]}{'...' if len(raw_response) > 1000 else ''}")
            
            parsed_decision = self.parse_ai_response(raw_response)
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
            "accion": parsed_decision["accion"],  # Corregido: usar "accion" en lugar de "action"
            "reasoning": parsed_decision["razonamiento"],
            "direccion": parsed_decision.get("direccion"),
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
        
        Gemini 3 Pro retorna JSON con la siguiente estructura esperada:
        {
            "accion": "COMPRAR" | "VENDER" | "NO_OPERAR" | "MANTENER" | "CERRAR" | "AJUSTAR_SL_TP",
            "razonamiento": str,
            "direccion": "LONG" | "SHORT" | None,
            "stop_loss": float (opcional),
            "take_profit": float (opcional),
            "confianza": float (opcional, 0-100),
            "estrategia_usada": str (opcional),
            "diagnostico_mercado": str (opcional),
        }
        
        Args:
            response_text: Texto de respuesta de Gemini 3 Pro (JSON)
            
        Returns:
            Diccionario con decisión estructurada
            
        Raises:
            ValueError: Si el JSON es inválido o falta campo requerido
        """
        self.logger.info(
            "Parseando respuesta IA INTRADAY",
            extra={"response_length": len(response_text)},
        )
        
        try:
            # Parsear JSON
            parsed = json.loads(response_text)
            
            # Validar campos requeridos
            if "accion" not in parsed:
                raise ValueError("Respuesta JSON no contiene campo 'accion'")
            
            if "razonamiento" not in parsed:
                raise ValueError("Respuesta JSON no contiene campo 'razonamiento'")
            
            # Validar acción
            acciones_validas = ["COMPRAR", "VENDER", "NO_OPERAR", "MANTENER", "CERRAR", "AJUSTAR_SL_TP"]
            if parsed["accion"] not in acciones_validas:
                raise ValueError(
                    f"Acción inválida: {parsed['accion']}. Debe ser una de: {acciones_validas}"
                )
            
            # Extraer campos opcionales con valores por defecto
            result = {
                "accion": parsed["accion"],
                "razonamiento": parsed["razonamiento"],
                "direccion": parsed.get("direccion"),
                "stop_loss": parsed.get("stop_loss"),
                "take_profit": parsed.get("take_profit"),
                "confianza": parsed.get("confianza"),
                "estrategia_usada": parsed.get("estrategia_usada"),
                "diagnostico_mercado": parsed.get("diagnostico_mercado"),
            }
            
            self.logger.info(
                f"Respuesta parseada: {result['accion']}",
                extra={
                    "accion": result["accion"],
                    "direccion": result["direccion"],
                    "confianza": result["confianza"],
                },
            )
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(
                f"Error parseando JSON de respuesta IA: {e}",
                extra={"response_text": response_text[:200]},
            )
            raise ValueError(f"Respuesta no es JSON válido: {e}") from e
        
        except Exception as e:
            self.logger.error(
                f"Error procesando respuesta IA: {e}",
                extra={"response_text": response_text[:200]},
            )
            raise

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

    def _get_initial_sl_from_db(self, symbol: str) -> Optional[float]:
        """Recupera el SL inicial desde la BD para el símbolo activo.
        
        Args:
            symbol: Símbolo de la posición
            
        Returns:
            SL inicial o None si no se encuentra
        """
        try:
            # Intentar obtener la posición actual y, con su magic, buscar en BD
            positions = self.mt5_connection.get_positions(symbol=symbol) if self.mt5_connection else []
            current_magic = None

            if positions:
                # Resolver códigos v2 de este agente
                family_id, strategy_id, agent_variant_id = resolve_codes(
                    ai_model=self.config.ai_model, strategy_name="INTRADAY", data_mode="raw"
                )
                for pos in positions:
                    try:
                        comp = self._magic_v2.decode(int(pos.magic))
                        if (
                            comp.family_id == family_id and
                            comp.strategy_id == strategy_id and
                            comp.agent_id == agent_variant_id
                        ):
                            current_magic = int(pos.magic)
                            break
                    except Exception:
                        # Fallback legacy por primer dígito mapeado
                        try:
                            mapped_bot_id = self.config.bot_id - 100 if self.config.bot_id >= 101 else self.config.bot_id
                            magic_str = str(pos.magic)
                            if magic_str and int(magic_str[0]) == mapped_bot_id:
                                current_magic = int(pos.magic)
                                break
                        except Exception:
                            continue

            if current_magic is None:
                return None

            operation = self.operations_repo.get_operation_by_magic_number(current_magic)
            # Verificar que el símbolo almacenado coincide; si no, fue una colisión legacy
            if operation and operation.symbol == symbol and getattr(operation, 'stop_loss_initial', None):
                return float(operation.stop_loss_initial)
            return None
            
        except Exception as e:
            self.logger.warning(
                f"Error obteniendo SL inicial desde BD para {symbol}: {e}",
                extra={"symbol": symbol, "error": str(e)},
            )
            return None

    def _has_active_position(self, symbol: str) -> bool:
        """Verifica si hay una posición activa para el símbolo.
        
        Args:
            symbol: Símbolo a verificar
            
        Returns:
            True si hay posición activa, False en caso contrario
        """
        try:
            # Verificar si position_manager está disponible (podría no estar inicializado aún)
            if not hasattr(self, '_position_manager') or self._position_manager is None:
                # Si no está inicializado, intentar inicializarlo
                if hasattr(self, 'mt5_connection') and self.mt5_connection is not None:
                    self._position_manager = PositionManager(self.mt5_connection)
                else:
                    # Si no hay conexión MT5, asumir que no hay posiciones
                    return False
            
            all_positions = self.mt5_connection.get_positions(symbol=symbol)

            # Resolver códigos v2 de este agente (default data_mode='raw')
            family_id, strategy_id, agent_variant_id = resolve_codes(
                ai_model=self.config.ai_model, strategy_name="INTRADAY", data_mode="raw"
            )

            bot_positions = []
            for pos in all_positions:
                try:
                    # Intentar decodificar como v2
                    comp = self._magic_v2.decode(int(pos.magic))
                    if (
                        comp.family_id == family_id and
                        comp.strategy_id == strategy_id and
                        comp.agent_id == agent_variant_id
                    ):
                        bot_positions.append(pos)
                        continue
                except Exception:
                    # Legacy o inválido: fallback al mapeo por bot_id (v1)
                    pass
                # Fallback legacy por primer dígito mapeado
                try:
                    mapped_bot_id = self.config.bot_id - 100 if self.config.bot_id >= 101 else self.config.bot_id
                    magic_str = str(pos.magic)
                    if magic_str and int(magic_str[0]) == mapped_bot_id:
                        bot_positions.append(pos)
                except Exception:
                    continue

            has_position = len(bot_positions) > 0
            
            self.logger.debug(
                f"Verificación de posición activa para {symbol}: {has_position}",
                extra={
                    "symbol": symbol,
                    "has_position": has_position,
                    "all_positions_count": len(all_positions),
                    "bot_positions_count": len(bot_positions),
                    "family_id": family_id,
                    "strategy_id": strategy_id,
                    "agent_variant_id": agent_variant_id,
                },
            )
            
            return has_position
            
        except Exception as e:
            self.logger.warning(
                f"Error verificando posición activa para {symbol}: {e}",
                extra={"symbol": symbol, "error": str(e)},
            )
            # En caso de error, asumir que no hay posición
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
            - pnl_usd: PnL en USD
            - pnl_r: PnL en múltiplos de R
            - volume: Volumen (lotes)
            - open_time: Timestamp de apertura
            - ticket: Ticket de la orden
        """
        try:
            all_positions = self.mt5_connection.get_positions(symbol=symbol)

            # Filtrar por Magic v2 de este agente (con fallback legacy)
            family_id, strategy_id, agent_variant_id = resolve_codes(
                ai_model=self.config.ai_model, strategy_name="INTRADAY", data_mode="raw"
            )
            bot_positions = []
            for pos in all_positions:
                try:
                    comp = self._magic_v2.decode(int(pos.magic))
                    if (
                        comp.family_id == family_id and
                        comp.strategy_id == strategy_id and
                        comp.agent_id == agent_variant_id
                    ):
                        bot_positions.append(pos)
                        continue
                except Exception:
                    pass
                # Fallback legacy por primer dígito mapeado
                try:
                    mapped_bot_id = self.config.bot_id - 100 if self.config.bot_id >= 101 else self.config.bot_id
                    magic_str = str(pos.magic)
                    if magic_str and int(magic_str[0]) == mapped_bot_id:
                        bot_positions.append(pos)
                except Exception:
                    continue
            
            if not bot_positions:
                self.logger.warning(
                    f"No se encontró posición activa para {symbol}",
                    extra={"symbol": symbol},
                )
                # Retornar estructura vacía
                return {
                    "type": None,
                    "price_open": 0.0,
                    "price_current": 0.0,
                    "sl": 0.0,
                    "tp": 0.0,
                    "pnl_points": 0.0,
                    "pnl_pips": 0.0,
                    "profit": 0.0,
                    "pnl_r": 0.0,
                    "volume": 0.0,
                    "open_time": datetime.now().isoformat(),
                    "ticket": 0,
                    "duration": "0m",
                }
            
            # Tomar la primera posición (debería haber solo una por símbolo)
            position = bot_positions[0]
            
            # Determinar tipo de posición
            position_type = "LONG" if position.type == 0 else "SHORT"  # 0=BUY, 1=SELL
            
            # Calcular PnL en puntos
            if position_type == "LONG":
                pnl_points = position.price_current - position.price_open
            else:
                pnl_points = position.price_open - position.price_current
            
            # Calcular PnL en pips (para pares forex: 1 pip = 0.0001, excepto JPY = 0.01)
            pip_value = 0.01 if "JPY" in symbol else 0.0001
            pnl_pips = pnl_points / pip_value
            
            # Calcular PnL en R (asumiendo que SL representa 1R)
            risk_points = abs(position.price_open - position.sl) if position.sl > 0 else 0.0
            pnl_r = pnl_points / risk_points if risk_points > 0 else 0.0
            
            # Calcular duración de la posición (manejar ausencia de time_open)
            # MetaTrader5 positions suelen tener 'time' (segundos epoch)
            open_time_raw = None
            if hasattr(position, 'time_open'):
                open_time_raw = getattr(position, 'time_open')
            elif hasattr(position, 'time'):
                open_time_raw = getattr(position, 'time')

            open_time_dt = None
            if isinstance(open_time_raw, (int, float)):
                try:
                    open_time_dt = datetime.fromtimestamp(open_time_raw)
                except Exception:
                    open_time_dt = datetime.now()
            elif hasattr(open_time_raw, 'timestamp'):
                try:
                    open_time_dt = datetime.fromtimestamp(open_time_raw.timestamp())
                except Exception:
                    open_time_dt = datetime.now()
            else:
                open_time_dt = datetime.now()

            duration_seconds = (datetime.now() - open_time_dt).total_seconds()
            
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            result = {
                "type": position_type,
                "price_open": position.price_open,
                "price_current": position.price_current,
                "sl": position.sl,
                "tp": position.tp,
                "pnl_points": pnl_points,
                "pnl_pips": round(pnl_pips, 1),
                "profit": position.profit,  # USD
                "pnl_r": round(pnl_r, 2),
                "volume": position.volume,
                "open_time": open_time_dt.isoformat(),
                "ticket": position.ticket,
                "duration": duration_str,
                "magic": getattr(position, 'magic', 0),
            }
            
            self.logger.info(
                f"Información de posición obtenida para {symbol}",
                extra={
                    "symbol": symbol,
                    "position_type": position_type,
                    "pnl_r": result["pnl_r"],
                    "profit": result["profit"],
                    "pnl_pips": result["pnl_pips"],
                    "duration": result["duration"],
                },
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Error obteniendo información de posición para {symbol}: {e}",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise
    
    def _execute_open_position(self, symbol: str, decision: Dict[str, Any]) -> None:
        """Sobrescribe método base para registrar operación en BD con valores iniciales de SL/TP.
        
        Este método:
        1. Llama a la implementación base para abrir la posición en MT5
        2. Registra la operación en la base de datos con stop_loss_initial y take_profit_initial
        
        Args:
            symbol: Símbolo del activo (ej: EURUSD)
            decision: Diccionario con la decisión de la IA incluyendo SL, TP, dirección, etc.
        """
        self.logger.info(
            f"🟢 Abriendo posición INTRADAY en {symbol}",
            extra={"symbol": symbol, "decision": decision}
        )
        
        try:
            # 1. Extraer y normalizar parámetros de la decisión
            direccion_raw = decision.get("direccion", "").lower()
            stop_loss = decision.get("stop_loss")
            take_profit = decision.get("take_profit") or decision.get("take_profit_1")
            entry_price = decision.get("precio_entrada")

            if direccion_raw in ("long", "comprar"):
                direction = "buy"
            elif direccion_raw in ("short", "vender"):
                direction = "sell"
            elif direccion_raw in ("buy", "sell"):
                direction = direccion_raw
            else:
                self.logger.warning(f"Dirección inválida/ausente en decisión: '{direccion_raw}'")
                return

            if not stop_loss or not take_profit:
                self.logger.warning("Decisión sin SL/TP válidos; no se abrirá operación")
                return

            if not self.mt5_connection or not self.order_manager:
                self.logger.error("Gestores de órdenes no inicializados")
                return

            # Verificar símbolo disponible y extraer specs
            try:
                symbol_info = self.mt5_connection.get_symbol_info(symbol)
                if symbol_info is None:
                    self.logger.error(f"Símbolo {symbol} no está disponible en MT5")
                    return
            except ValueError as e:
                self.logger.error(f"Error obteniendo información del símbolo {symbol}: {e}")
                return

            if self.symbol_spec_extractor is None:
                self.logger.error("SymbolSpecificationExtractor no inicializado")
                return
            symbol_spec = self.symbol_spec_extractor.get_symbol_specification(symbol)

            # Precio actual si no hay entrada explícita
            tick = self.mt5_connection._mt5.symbol_info_tick(symbol)
            if entry_price is None and tick is not None:
                entry_price = tick.ask if direction == "buy" else tick.bid
            if entry_price is None:
                self.logger.error(f"No se pudo determinar precio de entrada para {symbol}")
                return

            # 2. Resolver codes v2 (data_mode='raw' por defecto) y secuencia
            family_id, strategy_id, agent_variant_id = resolve_codes(
                ai_model=self.config.ai_model, strategy_name="INTRADAY", data_mode="raw"
            )
            seq = self._seq_manager.next_sequence(
                repo=self.operations_repo,
                family_id=family_id,
                strategy_id=strategy_id,
                agent_variant_id=agent_variant_id,
                symbol=symbol,
            )

            # 3. Generar magic v2
            magic_v2 = self._magic_v2.generate(
                family_id=family_id,
                strategy_id=strategy_id,
                order_type="market",
                agent_id=agent_variant_id,
                sequence=seq,
            )

            # 4. Calcular lote dinámico según riesgo (IA > config > mínimo)
            account_info = self.mt5_connection.get_account_info()
            balance = float(getattr(account_info, 'balance', 0.0))
            riesgo_ia = decision.get("riesgo_porcentaje") or decision.get("riesgo_pct")
            risk_pct = float(riesgo_ia) if riesgo_ia else float(self.config.risk_per_trade)
            lot_size_calc = max(symbol_spec.volume_min, symbol_spec.volume_step)
            risk_amount = balance * (risk_pct / 100.0)
            try:
                if self.position_sizer:
                    from src.core.position_sizer import RiskParameters
                    rp = RiskParameters(
                        account_balance=balance,
                        risk_percentage=risk_pct,
                        entry_price=float(entry_price),
                        stop_loss=float(stop_loss),
                        symbol_spec=symbol_spec
                    )
                    ps_result = self.position_sizer.calculate_lot_size(rp)
                    lot_size_calc = ps_result.lot_size
                    # Recalcular riesgo real usando lote ajustado
                    risk_amount = ps_result.risk_amount
            except Exception as e:
                self.logger.warning(
                    f"Fallo cálculo lote dinámico, usando mínimo: {e}",
                    extra={"symbol": symbol, "error": str(e)}
                )
            # 5. Enviar orden Market con lote dinámico
            order_type = OrderType.BUY if direction == "buy" else OrderType.SELL
            request = OrderRequest(
                symbol=symbol,
                order_type=order_type,
                volume=round(lot_size_calc, 2),
                price=float(entry_price),
                sl=float(stop_loss),
                tp=float(take_profit),
                magic=magic_v2,
                # MT5 restringe comentario (<31 chars, sin caracteres inválidos). Usamos formato corto.
                comment=f"B{self.config.bot_id}_INTRA"[:15]
            )
            result = self.order_manager.send_market_order(request)
            if not result or not getattr(result, 'order', None):
                # Log detallado de fallo
                trade_stops_level = getattr(symbol_info, 'trade_stops_level', None)
                point = getattr(symbol_info, 'point', None)
                min_stop_distance = None
                if trade_stops_level is not None and point is not None:
                    try:
                        min_stop_distance = trade_stops_level * point
                    except Exception:
                        min_stop_distance = None
                sl_distance_points = abs(entry_price - float(stop_loss)) if stop_loss else None
                tp_distance_points = abs(float(take_profit) - entry_price) if take_profit else None
                free_margin = getattr(account_info, 'margin_free', None)
                last_error = None
                try:
                    if hasattr(self.mt5_connection, '_mt5') and hasattr(self.mt5_connection._mt5, 'last_error'):
                        last_error = self.mt5_connection._mt5.last_error()
                except Exception:
                    last_error = None
                self.logger.error(
                    "Fallo envío orden Market (None)",
                    extra={
                        'symbol': symbol,
                        'direction': direction,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_pct': risk_pct,
                        'risk_amount': risk_amount,
                        'lot_size_attempt': lot_size_calc,
                        'trade_stops_level': trade_stops_level,
                        'min_stop_distance_points': min_stop_distance,
                        'sl_distance_points': sl_distance_points,
                        'tp_distance_points': tp_distance_points,
                        'free_margin': free_margin,
                        'last_error': last_error,
                        'magic_v2': magic_v2,
                        'sequence': seq,
                    }
                )
                return
            else:
                self.logger.info(
                    "Orden Market enviada (v2)",
                    extra={
                        'ticket': result.order,
                        'price': result.price,
                        'volume': result.volume,
                        'magic_v2': magic_v2,
                        'risk_pct': risk_pct,
                        'risk_amount': risk_amount,
                    }
                )

            # 5. Registrar en base de datos con valores iniciales
            if not self.position_manager:
                self.logger.warning("PositionManager no disponible, no se registrará en BD")
                return

            positions = self.position_manager.get_positions_by_symbol(symbol)
            if not positions:
                self.logger.warning(
                    f"No se encontró posición recién abierta para {symbol}, no se registrará en BD"
                )
                return

            # Seleccionar la posición recién abierta buscando magic_v2
            position_match = None
            for pos in positions:
                if int(getattr(pos, 'magic', 0)) == int(magic_v2):
                    position_match = pos
                    break
            if position_match is None:
                # Fallback: primera posición
                position_match = positions[0]
                self.logger.warning(
                    "No se encontró posición con magic_v2 esperado; usando primera posición",
                    extra={"expected_magic": magic_v2, "used_magic": position_match.magic}
                )
            position = position_match

            # 4. Crear registro en operations_repository
            db_direction = Direction.BUY if direction == "buy" else Direction.SELL
            
            # Calcular lot size y riesgo (usar resultado dinámico ya aplicado)
            lot_size = float(position.volume)
            # risk_pct ya calculado arriba
            risk_amount = risk_amount
            
            # Generar operation_id único
            operation_id = generate_operation_id(
                bot_id=self.config.bot_id,
                symbol=symbol
            )
            
            # Usar precio real de ejecución para todos los cálculos
            actual_price = float(position.price_open)
            
            # Recalcular SL/TP basado en precio real de ejecución (más preciso)
            # Para BUY: SL por debajo, TP por encima
            # Para SELL: SL por encima, TP por debajo
            if direction == "buy":
                # SL: precio_real - riesgo, TP: precio_real + objetivo
                actual_sl = actual_price - (200 * 0.00001)  # 200 pips de riesgo
                actual_tp = actual_price + (400 * 0.00001)  # 400 pips de objetivo
            else:
                # SL: precio_real + riesgo, TP: precio_real - objetivo
                actual_sl = actual_price + (200 * 0.00001)
                actual_tp = actual_price - (400 * 0.00001)
            
            self.logger.info(
                f"Registrando operación en BD: {operation_id}",
                extra={
                    "symbol": symbol,
                    "direction": db_direction.value,
                    "execution_price": actual_price,
                    "calculated_sl": actual_sl,
                    "calculated_tp": actual_tp,
                    "stop_loss_initial": actual_sl,  # Guardar SL calculado con precio real
                    "take_profit_initial": actual_tp,  # Guardar TP calculado con precio real
                }
            )
            
            # Crear operación en BD con valores recalculados
            operation = self.operations_repo.create_operation(
                magic_number=position.magic,  # Usar magic v2 aplicado a la orden
                bot_id=self.config.bot_id,
                ia_id=1,  # Usar 1 como default (ia_config_id no está en BotConfig)
                order_type=DBOrderType.MARKET,
                symbol=symbol,
                direction=db_direction,
                suggested_price=float(entry_price or actual_price),  # Precio sugerido (tick)
                actual_entry_price=actual_price,  # Precio real de ejecución
                stop_loss=actual_sl,  # SL recalculado con precio real
                take_profit=actual_tp,  # TP recalculado con precio real
                stop_loss_initial=actual_sl,  # 🔑 Valor inicial de SL (con precio real)
                take_profit_initial=actual_tp,  # 🔑 Valor inicial de TP (con precio real)
                lot_size=lot_size,
                risk_percentage=risk_pct,
                risk_amount=risk_amount,
                status=OperationStatus.OPEN,
                conversation_id=operation_id,
            )
            
            self.logger.info(
                f"✅ Operación registrada en BD: ID={operation.id}, Magic={operation.magic_number}",
                extra={
                    "operation_id": operation_id,
                    "db_id": operation.id,
                    "magic_number": operation.magic_number,
                    "stop_loss_initial": operation.stop_loss_initial,
                    "take_profit_initial": operation.take_profit_initial,
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Error al abrir/registrar posición en {symbol}: {e}",
                extra={"symbol": symbol, "error": str(e)}
            )
    
    def _execute_update_position(self, symbol: str, decision: Dict[str, Any]) -> None:
        """Sobrescribe método base para actualizar BD después de ajustar SL/TP.
        
        Este método:
        1. Llama a la implementación base para modificar SL/TP en MT5
        2. Actualiza el registro en la base de datos con los nuevos valores
        
        Args:
            symbol: Símbolo del activo (ej: EURUSD)
            decision: Diccionario con la decisión de la IA incluyendo stop_loss y take_profit
        """
        # 1. Ejecutar ajuste en MT5 (método base)
        super()._execute_update_position(symbol, decision)
        
        # 2. Actualizar registro en BD
        try:
            # Obtener posición de MT5
            if not self.position_manager:
                self.logger.warning("PositionManager no disponible, no se actualizará BD")
                return
            
            positions = self.position_manager.get_positions_by_symbol(symbol)
            if not positions:
                self.logger.warning(f"No se encontró posición para {symbol}, no se actualizará BD")
                return
            
            position = positions[0]
            ticket = position.ticket
            
            # Buscar operación en BD por magic_number (ticket)
            operation = self.operations_repo.get_operation_by_magic_number(ticket)
            
            if not operation:
                self.logger.warning(
                    f"No se encontró operación en BD con ticket {ticket}",
                    extra={"ticket": ticket, "symbol": symbol}
                )
                return
            
            if operation.id is None:
                self.logger.error("Operación sin ID, no se puede actualizar")
                return
            
            # Extraer nuevos valores de SL/TP
            new_sl = decision.get("stop_loss")
            new_tp = decision.get("take_profit")
            
            # Si no se especifica uno, mantener el actual
            if new_sl is None:
                new_sl = operation.stop_loss
            if new_tp is None:
                new_tp = operation.take_profit
            
            self.logger.info(
                f"Actualizando operación en BD: ID={operation.id}",
                extra={
                    "operation_id": operation.id,
                    "sl_anterior": operation.stop_loss,
                    "sl_nuevo": new_sl,
                    "tp_anterior": operation.take_profit,
                    "tp_nuevo": new_tp,
                    "sl_inicial": operation.stop_loss_initial,  # Se mantiene sin cambios
                }
            )
            
            # Actualizar operación en BD (SL inicial NO se modifica)
            updated_operation = self.operations_repo.update_operation(
                operation_id=operation.id,
                stop_loss=float(new_sl),
                take_profit=float(new_tp),
                # stop_loss_initial y take_profit_initial NO se modifican
            )
            
            if updated_operation:
                self.logger.info(
                    f"✅ Operación actualizada en BD: ID={updated_operation.id}",
                    extra={
                        "operation_id": updated_operation.id,
                        "stop_loss": updated_operation.stop_loss,
                        "take_profit": updated_operation.take_profit,
                        "stop_loss_initial": updated_operation.stop_loss_initial,  # Sin cambios
                    }
                )
            else:
                self.logger.warning(f"No se pudo actualizar operación en BD: ID={operation.id}")
            
        except Exception as e:
            self.logger.error(
                f"Error al actualizar operación en BD para {symbol}: {e}",
                extra={"symbol": symbol, "error": str(e)}
            )
    
    def _update_performance_metrics(self, symbol: str, decision: Dict[str, Any]) -> None:
        """
        Actualiza las métricas de rendimiento del bot basadas en la decisión.
        
        Args:
            symbol: Símbolo procesado
            decision: Decisión tomada por la IA
        """
        # Actualizar trades_today si se abrió una posición
        if decision.get("accion") in ["COMPRAR", "VENDER"]:
            self.trades_today += 1
        
        # Aquí se podrían actualizar otras métricas como current_pnl_r
        # basado en las posiciones abiertas, pero por simplicidad
        # se deja para implementación futura

