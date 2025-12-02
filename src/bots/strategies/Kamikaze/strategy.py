"""Estrategia Kamikaze: Ruptura de volatilidad M5 alineada con tendencia H1 (Gemini)."""

import time
import pandas as pd
from datetime import datetime, time as dt_time, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # Fallback si no disponible
from typing import Dict, Optional, Any

from src.bots.base.base_bot_operations import BaseBotOperations, BotConfig
from src.core.gemini_client import GeminiClient, GeminiConfig
from src.core.mt5_data_extractor import Timeframe, MT5DataError
from src.core.order_manager import OrderRequest, OrderType
from src.core.logger import get_bot_logger, LogLevel
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
        self.force_trading: bool = False
        # Modo verbose para elevar algunos logs a INFO
        self.verbose: bool = False
        
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
        # Forzar trading ignora ventanas horarias
        if self.force_trading:
            return True
        # Obtener hora actual convertida a EST independientemente de la zona local
        try:
            if ZoneInfo is not None:
                now_est = datetime.now(tz=ZoneInfo("America/New_York"))
                current_time = now_est.time()
            else:
                # Fallback: asumir hora local como aproximación si zoneinfo no está disponible
                current_time = datetime.now().time()
                self.logger.debug("ZoneInfo no disponible; usando hora local como fallback para horario de trading")
        except Exception:
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
            max_tokens=2048,  # Incrementado para evitar restricciones
            top_p=0.8,
            top_k=40,
            use_vertex_ai=False # Usar cliente estándar por defecto
        )
        
        self.gemini_client = GeminiClient(api_key=api_key, config=gemini_config)
        # Elevar nivel de log a DEBUG para mayor visibilidad de ciclos/decisiones
        try:
            self.logger.set_level(LogLevel.DEBUG)
        except Exception:
            pass
        self.logger.info("✅ Estrategia Kamikaze inicializada con Gemini 2.5 Pro")
        # Pregunta inicial a Gemini para establecer bias de inmediato, solo si dentro de horario o forzado
        try:
            if self.is_trading_time():
                self.logger.info("🚀 Solicitud inicial de Bias a Gemini para arrancar operación")
                self.update_market_bias()
                self.last_gemini_call = time.time()
            else:
                self.logger.info("⏳ Fuera de horario habilitado; se omitirá la consulta inicial a Gemini para ahorrar tokens")
        except Exception as e:
            self.logger.warning(f"No se pudo establecer Bias inicial con Gemini: {e}")
        return True

    def run_continuous(self, interval_seconds: int = 300) -> None:
        """Ejecuta el bot en modo continuo sincronizado con velas M5.

        Ciclos programados: :01, :06, :11, :16, ... de cada hora
        (1 minuto después del cierre de vela M5) según documentación Kamikaze.
        La consulta a Gemini para Bias se mantiene cada 30 minutos.
        """
        if not self.is_initialized:
            self.logger.error("Bot no inicializado.")
            return

        import time as _time
        from datetime import datetime as _dt, timedelta as _td

        self.logger.info("Iniciando modo continuo Kamikaze (ciclos M5 a :01/:06/:11/:16/...)")

        def _next_cycle_time() -> _dt:
            now = _dt.now()
            # Cierres M5 en :00, :05, :10, ... :55 -> ciclo en +1 minuto
            minute = now.minute
            # Próximo múltiplo de 5
            next_close = ((minute // 5) * 5 + 5) % 60
            cycle_min = (next_close + 1) % 60
            next_time = now.replace(minute=cycle_min, second=0, microsecond=0)
            # Ajuste de hora si cruzamos 60
            if next_close == 0 and minute >= 55:
                next_time += _td(hours=1)
            # Si ya pasó, sumar 5 minutos
            if next_time <= now:
                next_time += _td(minutes=5)
            return next_time

        try:
            while True:
                next_cycle = _next_cycle_time()
                wait_seconds = (next_cycle - _dt.now()).total_seconds()
                if wait_seconds > 0:
                    self.logger.info(
                        f"⏳ Próximo ciclo: {next_cycle.strftime('%H:%M:%S')} (en {wait_seconds:.0f}s)"
                    )
                    _time.sleep(wait_seconds)

                start_ts = _dt.now().strftime('%H:%M:%S')
                if self.verbose:
                    self.logger.info(f"🔄 Inicio ciclo técnico {start_ts}")
                else:
                    self.logger.debug(f"🔄 Inicio ciclo técnico {start_ts}")
                try:
                    self.run_trading_cycle()
                except Exception as e:
                    self.logger.error(f"Error en ciclo de trading: {e}")
        except KeyboardInterrupt:
            self.logger.info("Modo continuo interrumpido por usuario")
            raise

    def run_trading_cycle(self) -> None:
        """Ciclo principal de trading."""
        if not self.is_initialized:
            self.logger.error("Bot no inicializado.")
            return
        # Inicio de ciclo técnico
        now_ts = datetime.now().strftime("%H:%M:%S")
        # Mostrar inicio de ciclo siempre en verbose
        if self.verbose:
            self.logger.info(f"🔄 Inicio ciclo técnico {now_ts}")
        else:
            self.logger.debug(f"🔄 Inicio ciclo técnico {now_ts}")

        # 1. Actualizar Bias con Gemini si es necesario
        # Si nunca se ha llamado (0) o pasó el intervalo
        # Evitar consultas fuera de horario para ahorrar tokens, salvo force_trading
        if time.time() - self.last_gemini_call > self.gemini_interval:
            if self.is_trading_time():
                self.logger.info("⏰ Hora de actualizar Bias de Mercado con Gemini...")
                self.update_market_bias()
                self.last_gemini_call = time.time()
            else:
                if self.verbose:
                    self.logger.info("🪙 Fuera de horario; se evita consulta a Gemini para ahorrar tokens")
                else:
                    self.logger.debug("🪙 Fuera de horario; se evita consulta a Gemini para ahorrar tokens")

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
        
        prompt = f"""You are a technical market analyst. Analyze H1 price data for {symbol}.

Server time: {current_time}

H1 Candlestick Data (OPEN status = still forming):
{data_str}

Task: Determine the immediate trend direction based on price structure.

IMPORTANT: Respond ONLY with valid JSON in this exact format:
{{
  "trend": "BULLISH or BEARISH or RANGING"
}}

Do not include any other text or explanation."""
        
        response = self.gemini_client.send_prompt(prompt)
        
        if not response.success:
            self.logger.error(f"Fallo Gemini para {symbol}: {response.error_message}")
            return "NEUTRAL"
            
        # Parse JSON response
        try:
            import json
            # Remove markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            data = json.loads(content)
            text = data.get("trend", "NEUTRAL").strip().upper()
        except Exception as e:
            self.logger.warning(f"Error parseando JSON de Gemini: {e}. Respuesta raw: {response.content[:200]}")
            # Fallback: buscar las palabras clave en el texto
            text = response.content.strip().upper()
        
        if "BULLISH" in text: return "BULLISH"
        if "BEARISH" in text: return "BEARISH"
        return "NEUTRAL"

    def calculate_ema(self, df: pd.DataFrame, span: int = 50) -> float:
        """
        Calcula la EMA (Exponential Moving Average) para el período especificado.
        
        Args:
            df: DataFrame con datos OHLC
            span: Período de la EMA (default 50)
            
        Returns:
            Valor actual de la EMA o None si no hay suficientes datos
        """
        if len(df) < span:
            return None
        
        ema = df['close'].ewm(span=span, adjust=False).mean()
        return ema.iloc[-1]

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
            # Log visible para confirmar si está fuera de horario
            if self.verbose:
                self.logger.info(f"⏱️ Fuera de horario de trading para {symbol}. Sesiones EST: 02:00-05:00 y 08:00-11:00")
            else:
                self.logger.debug(f"⏱️ Fuera de horario de trading para {symbol}. Sesiones EST: 02:00-05:00 y 08:00-11:00")
            return
        
        # 1. Verificar si ya hay posición abierta para este símbolo
        if self.check_open_positions(symbol):
            if self.verbose:
                self.logger.info(f"🛡️ Posición ya abierta en {symbol}; se omite nuevo gatillo")
            else:
                self.logger.debug(f"🛡️ Posición ya abierta en {symbol}; se omite nuevo gatillo")
            return

        # 2. Verificar límite de posiciones totales (máximo 2 posiciones abiertas)
        total_positions = len(self.mt5_connection.get_positions())
        if total_positions >= 2:
            if self.verbose:
                self.logger.info(f"🚫 Límite de posiciones alcanzado ({total_positions}/2); no se abrirán nuevas")
            else:
                self.logger.debug(f"🚫 Límite de posiciones alcanzado ({total_positions}/2); no se abrirán nuevas")
            return

        # 3. Obtener Bias actual de Gemini
        bias = self.market_bias.get(symbol, "NEUTRAL")
        if bias == "NEUTRAL":
            if self.verbose:
                self.logger.info(f"⚖️ Bias NEUTRAL para {symbol}; se omite apertura")
            else:
                self.logger.debug(f"⚖️ Bias NEUTRAL para {symbol}; se omite apertura")
            return

        # 4. Obtener datos M5 (100 velas para calcular EMA 50 con datos suficientes)
        try:
            ohlcv_m5 = self.data_extractor.get_ohlcv(
                symbol=symbol,
                timeframe=Timeframe.M5,
                count=100,  # Suficiente para EMA 50 y contexto
                exclude_current=True  # Solo velas cerradas para evitar repinte
            )
        except MT5DataError:
            if self.verbose:
                self.logger.info(f"📉 No se pudieron obtener datos M5 para {symbol}; se omite ciclo")
            else:
                self.logger.debug(f"📉 No se pudieron obtener datos M5 para {symbol}; se omite ciclo")
            return

        df_m5 = ohlcv_m5.data
        if len(df_m5) < 2:
            if self.verbose:
                self.logger.info(f"📊 Datos insuficientes M5 ({len(df_m5)} velas) en {symbol}; se omite")
            else:
                self.logger.debug(f"📊 Datos insuficientes M5 ({len(df_m5)} velas) en {symbol}; se omite")
            return

        # 4.1 Calcular EMA 50 para contexto (NO como filtro bloqueante)
        ema_50 = self.calculate_ema(df_m5, span=50)
        current_price = df_m5.iloc[-1]['close']
        
        # Determinar posición relativa al EMA (solo para logging)
        price_vs_ema = "N/A"
        if ema_50 is not None:
            if current_price > ema_50:
                price_vs_ema = "ABOVE EMA" # Precio por encima, zona de compras más favorable
            else:
                price_vs_ema = "BELOW EMA" # Precio por debajo, zona de ventas más favorable

        # 5. Detectar patrón de velas
        pattern = self.detect_pattern(df_m5)
        
        # Formatear EMA para logging
        ema_str = f"{ema_50:.5f}" if ema_50 is not None else "N/A"
        
        if pattern:
            self.logger.info(
                f"📊 Patrón detectado en {symbol}: {pattern} | Bias={bias} | "
                f"Price={current_price:.5f}, EMA50={ema_str}, Position={price_vs_ema}"
            )
        else:
            # En verbose, mostrar este resumen como INFO para confirmar evaluación
            if self.verbose:
                self.logger.info(
                    f"🔎 Sin patrón válido en {symbol} | Bias={bias} | Price={current_price:.5f}, EMA50={ema_str}, Position={price_vs_ema}"
                )
            else:
                self.logger.debug(
                    f"🔎 Sin patrón válido en {symbol} | Bias={bias} | Price={current_price:.5f}, EMA50={ema_str}, Position={price_vs_ema}"
                )

        # 6. LÓGICA DE FRANCOTIRADOR: Confluencia de Bias + Patrón
        
        # ESCENARIO DE COMPRA (LONG)
        # Gemini dice que H1 es Alcista Y tenemos patrón de reversión alcista en M5
        valid_long_patterns = ["BULLISH_ENGULFING", "HAMMER"]
        if bias == "BULLISH" and pattern in valid_long_patterns:
            self.logger.info(
                f"🎯 GATILLO DE COMPRA en {symbol}: {pattern} + Bias {bias} | "
                f"Price={current_price:.5f}, EMA50={ema_str}, Position={price_vs_ema}"
            )
            self.place_order(symbol, OrderType.BUY)
            return

        # ESCENARIO DE VENTA (SHORT)
        # Gemini dice que H1 es Bajista Y tenemos patrón de reversión bajista en M5
        valid_short_patterns = ["BEARISH_ENGULFING", "SHOOTING_STAR"]
        if bias == "BEARISH" and pattern in valid_short_patterns:
            self.logger.info(
                f"🎯 GATILLO DE VENTA en {symbol}: {pattern} + Bias {bias} | "
                f"Price={current_price:.5f}, EMA50={ema_str}, Position={price_vs_ema}"
            )
            self.place_order(symbol, OrderType.SELL)
            return

        # 7. Reporte cuando hay confluencia insuficiente
        if self.verbose:
            self.logger.info(
                f"🧩 Sin confluencia suficiente para {symbol}: Bias={bias}, Pattern={pattern or 'None'}"
            )
        else:
            self.logger.debug(
                f"🧩 Sin confluencia suficiente para {symbol}: Bias={bias}, Pattern={pattern or 'None'}"
            )

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

