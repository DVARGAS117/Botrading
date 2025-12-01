"""Estrategia Kamikaze: Ruptura de volatilidad M5 alineada con tendencia H1 (Gemini)."""

import time
import pandas as pd
from datetime import datetime, time as dt_time
from typing import Dict, Optional, Any

from src.bots.base.base_bot_operations import BaseBotOperations, BotConfig
from src.core.gemini_client import GeminiClient, GeminiConfig
from src.core.mt5_data_extractor import Timeframe, MT5DataError
from src.core.order_manager import OrderRequest, OrderType
from src.core.logger import get_bot_logger
from src.core.enhanced_magic_number_generator import EnhancedMagicNumberGenerator

class KamikazeStrategy(BaseBotOperations):
    """
    Implementación de la estrategia Kamikaze.
    
    Lógica:
    1. Consultar a Gemini cada 30 min para obtener Bias (BULLISH/BEARISH/NEUTRAL) usando velas H1.
    2. En cada ciclo (aprox 10s), verificar gatillo técnico en M5.
    3. Detector de Patrones Matemático:
       - HAMMER: Mecha inferior larga (≥2x cuerpo), señal alcista
       - SHOOTING_STAR: Mecha superior larga (≥2x cuerpo), señal bajista
       - BULLISH_ENGULFING: Vela alcista envuelve bajista anterior
       - BEARISH_ENGULFING: Vela bajista envuelve alcista anterior
    4. Gatillo:
       - COMPRA: Bias BULLISH + (HAMMER o BULLISH_ENGULFING)
       - VENTA: Bias BEARISH + (SHOOTING_STAR o BEARISH_ENGULFING)
    """

    def __init__(self, config: BotConfig):
        super().__init__(config)
        self.market_bias: Dict[str, str] = {s: "NEUTRAL" for s in config.symbols}
        self.last_gemini_call = 0
        self.gemini_interval = 1800  # 30 minutos
        self.gemini_client: Optional[GeminiClient] = None
        
        # Configuración específica de Kamikaze (hardcoded por ahora o desde config)
        self.lot_size = 0.01
        self.sl_points = 300  # 30 pips - Ajustado para volatilidad intradía M5
        self.tp_points = 600  # 60 pips - Ratio 1:2 realista
        self.deviation = 20
        
        # Enhanced Magic Number Generator (v2)
        self._magic_v2 = EnhancedMagicNumberGenerator()
        self._sequence_counter: Dict[str, int] = {}  # Secuencia por símbolo
        
        # Horarios de Trading (EST - Eastern Standard Time)
        # London Open: 2am - 5am EST
        # New York Open: 8am - 11am EST
        self.trading_sessions = [
            (dt_time(2, 0), dt_time(5, 0)),   # London Open
            (dt_time(8, 0), dt_time(11, 0)),  # New York Open
        ]

    def is_trading_time(self) -> bool:
        """
        Verifica si estamos en horario de trading permitido.
        
        Returns:
            True si estamos en London Open (2am-5am EST) o NY Open (8am-11am EST)
        """
        # Obtener hora actual en EST (asumimos que el sistema está configurado en EST,
        # o se puede ajustar según sea necesario)
        current_time = datetime.now().time()
        
        for start_time, end_time in self.trading_sessions:
            if start_time <= current_time < end_time:
                return True
        
        return False

    def initialize(self) -> bool:
        """Inicializa la estrategia y el cliente Gemini."""
        if not super().initialize():
            return False
        
        # Inicializar cliente Gemini 2.5 Pro
        # Asumimos que la API Key ya está disponible en self.ai_client.api_key si se usó BaseBotOperations
        api_key = self.ai_client.api_key if self.ai_client else None
        
        gemini_config = GeminiConfig(
            model="gemini-2.5-pro",
            temperature=0.1, # Baja temperatura para respuestas concisas
            max_tokens=100,
            top_p=0.8,
            top_k=40,
            use_vertex_ai=False # Usar cliente estándar por defecto
        )
        
        self.gemini_client = GeminiClient(api_key=api_key, config=gemini_config)
        self.logger.info("✅ Estrategia Kamikaze inicializada con Gemini 2.5 Pro")
        return True

    def run_trading_cycle(self) -> None:
        """Ciclo principal de trading."""
        if not self.is_initialized:
            self.logger.error("Bot no inicializado.")
            return

        # 1. Actualizar Bias con Gemini si es necesario
        # Si nunca se ha llamado (0) o pasó el intervalo
        if time.time() - self.last_gemini_call > self.gemini_interval:
            self.logger.info("⏰ Hora de actualizar Bias de Mercado con Gemini...")
            self.update_market_bias()
            self.last_gemini_call = time.time()

        # 2. Ejecutar lógica técnica para cada símbolo
        for symbol in self.config.symbols:
            try:
                self.execute_strategy(symbol)
            except Exception as e:
                self.logger.error(f"Error ejecutando estrategia para {symbol}: {e}")

    def update_market_bias(self) -> None:
        """Consulta a Gemini para actualizar el bias de cada símbolo."""
        for symbol in self.config.symbols:
            try:
                bias = self.ask_gemini_bias(symbol)
                self.market_bias[symbol] = bias
                self.logger.info(f"🧠 Nuevo Bias para {symbol}: {bias}")
            except Exception as e:
                self.logger.error(f"Error actualizando bias para {symbol}: {e}")
                # Mantener bias anterior o poner NEUTRAL en caso de error crítico?
                # Por seguridad, si falla Gemini, mejor no operar o mantener anterior.
                # Estrategia.md dice "return NEUTRAL" en except.
                self.market_bias[symbol] = "NEUTRAL"

    def ask_gemini_bias(self, symbol: str) -> str:
        """
        Obtiene datos H1 y consulta a Gemini.
        Incluye estado de la vela (Abierta/Cerrada) y Timestamp.
        """
        # Obtener últimas 10 velas H1
        # Usamos exclude_current=False para ver la vela actual en formación si queremos,
        # pero estrategia.md usa "copy_rates_from_pos(..., 0, 10)" que incluye la actual.
        # El usuario pide: "decirle a gemini si la ultima vela es abierta o cerrada".
        # Si pedimos las ultimas 10 desde pos 0, la ultima (índice 9) es la actual (abierta).
        
        try:
            ohlcv = self.data_extractor.get_ohlcv(
                symbol=symbol,
                timeframe=Timeframe.H1,
                count=10,
                exclude_current=False # Incluir la vela actual
            )
        except MT5DataError:
            self.logger.warning(f"No se pudieron obtener datos H1 para {symbol}")
            return "NEUTRAL"

        df = ohlcv.data
        if df.empty:
            return "NEUTRAL"

        # Preparar string de datos
        # Añadir columna de estado
        # La última fila es la vela actual (Abierta), las anteriores son Cerradas.
        df['status'] = 'CLOSED'
        df.iloc[-1, df.columns.get_loc('status')] = 'OPEN'
        
        # Formatear para el prompt
        data_str = df[['time', 'open', 'high', 'low', 'close', 'status']].to_string(index=False)
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        prompt = f"""
        Eres un trader experto en Smart Money Concepts. Analiza estos datos de precios (H1) para {symbol}.
        Hora actual del servidor: {current_time}
        
        Datos recientes (La última vela marcada como OPEN está en formación):
        {data_str}
        
        Determina la TENDENCIA INMEDIATA basándote en máximos y mínimos recientes.
        Responde SOLO con una palabra: "BULLISH" (si debo buscar compras), "BEARISH" (si debo buscar ventas), o "RANGING" (si no hay claridad).
        No des explicaciones.
        """
        
        response = self.gemini_client.send_prompt(prompt)
        
        if not response.success:
            self.logger.error(f"Fallo Gemini para {symbol}: {response.error_message}")
            return "NEUTRAL"
            
        text = response.content.strip().upper()
        
        if "BULLISH" in text: return "BULLISH"
        if "BEARISH" in text: return "BEARISH"
        return "NEUTRAL"

    def detect_pattern(self, df: pd.DataFrame) -> Optional[str]:
        """
        Analiza las últimas 2 velas para detectar patrones de reversión.
        
        Args:
            df: DataFrame con datos OHLC
            
        Returns:
            Patrón detectado: "BULLISH_ENGULFING", "BEARISH_ENGULFING", 
                             "HAMMER", "SHOOTING_STAR" o None
        """
        if len(df) < 2:
            return None
            
        # Datos vela actual (última cerrada)
        curr = df.iloc[-1]
        curr_body = abs(curr['close'] - curr['open'])
        curr_range = curr['high'] - curr['low']
        curr_bullish = curr['close'] > curr['open']

        # Datos vela anterior
        prev = df.iloc[-2]
        prev_body = abs(prev['close'] - prev['open'])
        prev_bullish = prev['close'] > prev['open']

        # 1. DETECCIÓN DE ENVOLVENTE (ENGULFING)
        # Una vela grande se come a una pequeña anterior del color opuesto
        if curr_bullish and not prev_bullish:
            if curr['close'] > prev['open'] and curr['open'] < prev['close']:
                return "BULLISH_ENGULFING"
        
        if not curr_bullish and prev_bullish:
            if curr['close'] < prev['open'] and curr['open'] > prev['close']:
                return "BEARISH_ENGULFING"

        # 2. DETECCIÓN DE PINBAR (HAMMER / SHOOTING STAR)
        # El cuerpo debe ser pequeño y estar en un extremo. La mecha de rechazo debe ser larga.
        
        # Ratio: La mecha debe ser al menos 2 veces el cuerpo
        min_wick_ratio = 2.0 
        
        # Hammer (Alcista): Mecha inferior larga, cuerpo arriba
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        
        if lower_wick > (curr_body * min_wick_ratio) and upper_wick < curr_body:
            return "HAMMER"  # Señal de compra

        # Shooting Star (Bajista): Mecha superior larga, cuerpo abajo
        if upper_wick > (curr_body * min_wick_ratio) and lower_wick < curr_body:
            return "SHOOTING_STAR"  # Señal de venta

        return None

    def execute_strategy(self, symbol: str) -> None:
        """Verifica gatillos técnicos M5 y ejecuta operaciones usando reconocimiento de patrones."""
        # 0. Verificar horario de trading (Sniper Mode)
        if not self.is_trading_time():
            return
        
        # 1. Verificar si ya hay posición abierta para este símbolo
        if self.check_open_positions(symbol):
            return

        # 2. Verificar límite de posiciones totales (máximo 2 posiciones abiertas)
        total_positions = len(self.mt5_connection.get_positions())
        if total_positions >= 2:
            self.logger.debug(f"Límite de posiciones alcanzado ({total_positions}/2)")
            return

        # 3. Obtener Bias actual de Gemini
        bias = self.market_bias.get(symbol, "NEUTRAL")
        if bias == "NEUTRAL":
            return

        # 4. Obtener datos M5 (últimas 20 velas cerradas)
        try:
            ohlcv_m5 = self.data_extractor.get_ohlcv(
                symbol=symbol,
                timeframe=Timeframe.M5,
                count=20,
                exclude_current=True  # Solo velas cerradas para evitar repinte
            )
        except MT5DataError:
            return

        df_m5 = ohlcv_m5.data
        if len(df_m5) < 2:
            return

        # 5. Detectar patrón de velas
        pattern = self.detect_pattern(df_m5)
        
        if pattern:
            self.logger.info(f"📊 Patrón detectado en {symbol}: {pattern} | Bias Gemini: {bias}")

        # 6. LÓGICA DE FRANCOTIRADOR: Confluencia de Bias + Patrón
        
        # ESCENARIO DE COMPRA (LONG)
        # Gemini dice que H1 es Alcista Y tenemos patrón de reversión alcista en M5
        valid_long_patterns = ["BULLISH_ENGULFING", "HAMMER"]
        if bias == "BULLISH" and pattern in valid_long_patterns:
            self.logger.info(f"🎯 GATILLO DE COMPRA en {symbol}: {pattern} + Bias {bias}")
            self.place_order(symbol, OrderType.BUY)
            return

        # ESCENARIO DE VENTA (SHORT)
        # Gemini dice que H1 es Bajista Y tenemos patrón de reversión bajista en M5
        valid_short_patterns = ["BEARISH_ENGULFING", "SHOOTING_STAR"]
        if bias == "BEARISH" and pattern in valid_short_patterns:
            self.logger.info(f"🎯 GATILLO DE VENTA en {symbol}: {pattern} + Bias {bias}")
            self.place_order(symbol, OrderType.SELL)
            return

    def check_open_positions(self, symbol: str) -> bool:
        """Verifica si hay posiciones abiertas para el símbolo."""
        positions = self.mt5_connection.get_positions(symbol=symbol)
        return len(positions) > 0

    def place_order(self, symbol: str, order_type: OrderType) -> None:
        """Envía la orden al mercado con magic number v2."""
        tick = self.mt5_connection._mt5.symbol_info_tick(symbol)
        if not tick:
            return
            
        price = tick.ask if order_type == OrderType.BUY else tick.bid
        point = self.mt5_connection.get_symbol_info(symbol).point
        
        # Calcular SL/TP
        sl_dist = self.sl_points * point
        tp_dist = self.tp_points * point
        
        if order_type == OrderType.BUY:
            sl = price - sl_dist
            tp = price + tp_dist
        else:
            sl = price + sl_dist
            tp = price - tp_dist
        
        # Generar Magic Number v2 usando EnhancedMagicNumberGenerator
        # Estructura: D1=family, D2=strategy, D3=type, D4=agent, D5D6=sequence
        # Para Kamikaze: family=1 (Gemini), strategy=6 (Kamikaze), agent=1
        if symbol not in self._sequence_counter:
            self._sequence_counter[symbol] = 0
        
        sequence = self._sequence_counter[symbol]
        magic = self._magic_v2.generate(
            family_id=1,      # Familia Gemini/IA
            strategy_id=6,    # Estrategia Kamikaze (asignar ID único)
            order_type="market",
            agent_id=1,       # Agente 1 dentro de Kamikaze
            sequence=sequence
        )
        
        # Incrementar secuencia para próxima orden en este símbolo
        self._sequence_counter[symbol] = (sequence + 1) % 100  # 0-99
        
        request = OrderRequest(
            symbol=symbol,
            order_type=order_type,
            volume=self.lot_size,
            price=price,
            sl=sl,
            tp=tp,
            magic=magic,
            comment="Kamikaze AI",
            deviation=self.deviation
        )
        
        result = self.order_manager.send_market_order(request)
        if result:
            self.logger.info(f"✅ Orden ejecutada: {result.order} | Magic: {magic}")
        else:
            self.logger.error(f"❌ Error ejecutando orden en {symbol}")

    def prepare_data_for_ai(
        self,
        symbol: str,
        indicators: Dict,
        or_data: Optional[Any],
        market_context: Any,
        ohlcv_data: Optional[Dict] = None
    ) -> tuple[str, str]:
        """No usado en Kamikaze (usamos ask_gemini_bias directamente)."""
        return "", ""

    def parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """No usado en Kamikaze."""
        return {}

