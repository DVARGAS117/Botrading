# 🔧 Referencia API - Bot INTRADAY

## Índice
- [IntradayBot1Strategy](#intradaybot1strategy)
- [IntradayIndicatorCalculator](#intradayindicatorcalculator)
- [Repositorios](#repositorios)
- [Estructuras de Datos](#estructuras-de-datos)

---

## IntradayBot1Strategy

### Descripción
Clase principal que implementa la estrategia INTRADAY Bot 1. Hereda de `BaseBotOperations` y orquesta el ciclo completo de trading.

### Constructor

```python
def __init__(self, config: BotConfig) -> None
```

**Parámetros**:
- `config` (BotConfig): Configuración del bot con parámetros de operación

**Inicializa**:
- Logger específico del bot
- VertexAIClient (Gemini 3 Pro)
- IAQueryRepository
- OperationsRepository
- Rutas a prompts

---

### Métodos Principales

#### `initialize()`

```python
def initialize(self) -> bool
```

Inicializa componentes base y crea IntradayIndicatorCalculator.

**Returns**: `True` si éxito, `False` en caso contrario

**Flujo**:
1. Llama a `super().initialize()` para componentes base
2. Crea `IntradayIndicatorCalculator` con `data_extractor`
3. Inicializa `VertexAIClient` con configuración
4. Registra inicialización en logs

---

#### `run_trading_cycle()`

```python
def run_trading_cycle(self) -> None
```

Ejecuta un ciclo completo de trading para todos los símbolos activos.

**Flujo**:
1. Verifica horario de trading
2. Verifica límites diarios (max_daily_risk/profit)
3. Obtiene símbolos activos para sesión actual
4. Por cada símbolo:
   - Ejecuta `execute_cycle(symbol)`
   - Ejecuta decisión de IA
   - Actualiza métricas

**Raises**: Ninguna (errores se logean pero no detienen el ciclo)

---

#### `execute_cycle(symbol)`

```python
def execute_cycle(self, symbol: str) -> Dict[str, Any]
```

Ejecuta un ciclo completo de análisis y decisión para un símbolo.

**Parámetros**:
- `symbol` (str): Símbolo a analizar (ej: "EURUSD")

**Returns**: Diccionario con decisión y metadata

```python
{
    "operation_id": "INTRADAY_101_EURUSD_...",
    "action": "COMPRAR | VENDER | NO_OPERAR | ...",
    "reasoning": "Análisis de la IA...",
    "direction": "LONG | SHORT",
    "stop_loss": 1.04900,
    "take_profit": 1.05300,
    "confidence": 85.0,
    "query_id": 123,
    "cost_usd": 0.05,
    "tokens_total": 5000,
    "timestamp": "2025-11-20 10:30:00"
}
```

**Flujo**:
1. Prepara datos para IA (paquetes + prompts)
2. Consulta Gemini 3 Pro vía Vertex AI
3. Parsea respuesta JSON
4. Registra consulta en IAQueryRepository
5. Retorna decisión completa

**Raises**:
- `ValueError`: Si datos insuficientes
- `Exception`: Si error en IA o parsing

---

#### `prepare_data_for_ai()`

```python
def prepare_data_for_ai(
    symbol: str,
    indicators: Dict,
    or_data: Optional[Any],
    market_context: MarketContext,
    ohlcv_data: Optional[Dict] = None
) -> Tuple[str, str]
```

Prepara datos de mercado para enviar a la IA.

**Parámetros**:
- `symbol`: Símbolo a analizar
- `indicators`: No usado (calculamos propios)
- `or_data`: No usado en INTRADAY
- `market_context`: Contexto actual del mercado
- `ohlcv_data`: No usado (obtenemos propios)

**Returns**: Tupla `(system_prompt, user_prompt)`

**Nota**: Internamente llama a `_prepare_intraday_data_for_ai()` que retorna estructura completa.

---

#### `parse_ai_response(response_text)`

```python
def parse_ai_response(self, response_text: str) -> Dict[str, Any]
```

Parsea la respuesta JSON de Gemini 3 Pro.

**Parámetros**:
- `response_text` (str): Respuesta JSON de Gemini

**Returns**: Diccionario con decisión estructurada

```python
{
    "accion": "COMPRAR",
    "razonamiento": "...",
    "direccion": "LONG",
    "stop_loss": 1.04900,
    "take_profit": 1.05300,
    "confianza": 85.0,
    "estrategia_usada": "Breakout de rango",
    "diagnostico_mercado": "Tendencia alcista..."
}
```

**Raises**:
- `ValueError`: Si JSON inválido o falta campo requerido

---

### Métodos Internos

#### `_has_active_position(symbol)`

```python
def _has_active_position(self, symbol: str) -> bool
```

Verifica si hay una posición activa para el símbolo usando `PositionManager`.

---

#### `_get_current_position_info(symbol)`

```python
def _get_current_position_info(self, symbol: str) -> Dict[str, Any]
```

Obtiene información completa de la posición activa.

**Returns**:
```python
{
    "type": "LONG",
    "price_open": 1.05000,
    "price_current": 1.05150,
    "sl": 1.04900,
    "tp": 1.05300,
    "pnl_points": 0.00150,
    "pnl_pips": 15.0,
    "profit": 15.00,
    "pnl_r": 1.5,
    "volume": 0.01,
    "open_time": "2025-11-20 09:00:00",
    "ticket": 123456789,
    "duration": "1h 30m"
}
```

---

#### `_get_initial_sl_from_db(symbol)`

```python
def _get_initial_sl_from_db(self, symbol: str) -> Optional[float]
```

Recupera el SL inicial desde operations.db para calcular PnL en R.

**Returns**: SL inicial o `None` si no se encuentra

---

#### `_execute_open_position(symbol, decision)`

```python
def _execute_open_position(self, symbol: str, decision: Dict[str, Any]) -> None
```

Abre una nueva posición y la registra en BD con valores iniciales de SL/TP.

**Importante**: Guarda `stop_loss_initial` y `take_profit_initial` para tracking de R.

---

#### `_execute_update_position(symbol, decision)`

```python
def _execute_update_position(self, symbol: str, decision: Dict[str, Any]) -> None
```

Actualiza SL/TP de posición existente (trailing stop).

**Importante**: NO modifica `stop_loss_initial` en BD, solo `stop_loss` y `take_profit`.

---

## IntradayIndicatorCalculator

### Descripción
Calculador especializado de indicadores técnicos para estrategia INTRADAY. Genera paquetes pre-calculados de M15 y D1.

### Constructor

```python
def __init__(self, data_extractor: MT5DataExtractor)
```

**Parámetros**:
- `data_extractor`: Extractor de datos MT5 para obtener históricos

---

### Métodos Principales

#### `calculate_tactical_package(symbol, candles_to_return=200)`

```python
def calculate_tactical_package(
    symbol: str,
    candles_to_return: int = 200
) -> List[IntradayCandle_M15]
```

Calcula el paquete táctico (M15) con 200 velas pre-calculadas.

**Parámetros**:
- `symbol`: Símbolo a analizar
- `candles_to_return`: Número de velas a retornar (default: 200)

**Returns**: Lista de `IntradayCandle_M15` con indicadores

**Indicadores Calculados**:
- EMA 20, EMA 200
- VWAP
- RSI 14
- ATR 14
- Bollinger Bands (upper, lower, width)

**Pre-Cálculo**: Obtiene 450 velas (200 + 250 buffer) para garantizar EMA 200 válida en todas las velas retornadas.

**Raises**:
- `ValueError`: Si datos insuficientes

---

#### `calculate_strategic_package(symbol, candles_to_return=30)`

```python
def calculate_strategic_package(
    symbol: str,
    candles_to_return: int = 30
) -> List[IntradayCandle_D1]
```

Calcula el paquete estratégico (D1) con 30 velas CERRADAS.

**Parámetros**:
- `symbol`: Símbolo a analizar
- `candles_to_return`: Número de velas cerradas a retornar (default: 30)

**Returns**: Lista de `IntradayCandle_D1` con indicadores

**Indicadores Calculados**:
- EMA 200
- ATR 14
- Previous OHLC (close, high, low del día anterior)

**Importante**: Excluye la última vela (día actual en formación) para garantizar datos definitivos.

**Raises**:
- `ValueError`: Si datos insuficientes

---

#### `calculate_tactical_update(symbol, last_timestamp, current_timestamp=None)`

```python
def calculate_tactical_update(
    symbol: str,
    last_timestamp: datetime,
    current_timestamp: Optional[datetime] = None
) -> List[IntradayCandle_M15]
```

Calcula actualización táctica incremental con solo velas nuevas.

**Parámetros**:
- `symbol`: Símbolo a analizar
- `last_timestamp`: Timestamp de última consulta
- `current_timestamp`: Timestamp actual (default: now())

**Returns**: Lista de velas M15 nuevas cerradas desde `last_timestamp`

**Ejemplo**:
```python
# Última consulta: 2025-11-20 14:00:00
# Consulta actual: 2025-11-20 14:30:00
# Resultado: 2 velas (14:00 y 14:15) con indicadores completos
```

**Raises**:
- `ValueError`: Si timestamps inválidos o datos insuficientes

---

#### `get_full_intraday_packages(symbol, tactical_candles=200, strategic_candles=30)`

```python
def get_full_intraday_packages(
    symbol: str,
    tactical_candles: int = 200,
    strategic_candles: int = 30
) -> Dict[str, List]
```

Obtiene ambos paquetes INTRADAY en formato JSON-ready.

**Returns**:
```python
{
    "tactical_m15": [
        {
            "timestamp": "2025-11-20 10:00:00",
            "open": 1.05123,
            ...
            "ema_20": 1.05100,
            "ema_200": 1.05000,
            ...
        },
        # ... 199 velas más
    ],
    "strategic_d1": [
        {
            "date": "2025-11-19",
            "close": 1.05156,
            "ema_200": 1.05000,
            ...
        },
        # ... 29 velas más
    ]
}
```

---

## Repositorios

### IAQueryRepository

#### `create_query(...)`

```python
def create_query(
    bot_id: int,
    ia_id: int,
    symbol: str,
    query_type: QueryType,
    prompt: str,
    response: str,
    tokens_input: int,
    tokens_output: int,
    cost_usd: float,
    action_decided: str,
    operation_id: str
) -> IAQuery
```

Crea un nuevo registro de consulta IA.

**QueryType Enum**:
- `EVALUATION`: Evaluación inicial (sin posición)
- `REEVALUATION`: Reevaluación (con posición activa)

---

#### `get_queries_by_operation_id(operation_id)`

```python
def get_queries_by_operation_id(self, operation_id: str) -> List[IAQuery]
```

Obtiene todas las consultas asociadas a un operation_id.

---

### OperationsRepository

#### `create_operation(...)`

```python
def create_operation(
    magic_number: int,
    bot_id: int,
    ia_id: int,
    order_type: OrderType,
    symbol: str,
    direction: Direction,
    suggested_price: float,
    actual_entry_price: float,
    stop_loss: float,
    take_profit: float,
    stop_loss_initial: float,
    take_profit_initial: float,
    lot_size: float,
    risk_percentage: float,
    status: OperationStatus,
    conversation_id: str
) -> Operation
```

Crea un nuevo registro de operación.

**OperationStatus Enum**:
- `OPEN`: Posición abierta
- `CLOSED`: Posición cerrada
- `CANCELLED`: Orden cancelada

---

#### `update_operation(operation_id, **kwargs)`

```python
def update_operation(
    operation_id: int,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    exit_price: Optional[float] = None,
    pnl_usd: Optional[float] = None,
    pnl_r: Optional[float] = None,
    status: Optional[OperationStatus] = None
) -> Operation
```

Actualiza campos específicos de una operación.

**Importante**: `stop_loss_initial` y `take_profit_initial` NO se pueden actualizar (preservar para cálculo de R).

---

## Estructuras de Datos

### IntradayCandle_M15

```python
@dataclass
class IntradayCandle_M15:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    ema_20: Optional[float] = None
    ema_200: Optional[float] = None
    vwap: Optional[float] = None
    rsi_14: Optional[float] = None
    atr_14: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None
```

---

### IntradayCandle_D1

```python
@dataclass
class IntradayCandle_D1:
    date: str
    close: float
    ema_200: Optional[float] = None
    atr_14: Optional[float] = None
    prev_close: Optional[float] = None
    prev_high: Optional[float] = None
    prev_low: Optional[float] = None
```

---

### BotConfig

```python
@dataclass
class BotConfig:
    bot_id: int
    bot_name: str
    bot_type: str
    symbols: List[str]
    strategy_type: str
    risk_per_trade: float
    max_daily_risk: float
    max_daily_profit: float
    enable_dual_orders: bool
    ai_model: str
    log_level: str
```

---

### VertexAIConfig

```python
@dataclass
class VertexAIConfig:
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    timeout: int
```

---

## Utilidades

### `generate_operation_id(bot_id, symbol)`

```python
def generate_operation_id(bot_id: int, symbol: str) -> str
```

Genera un ID único para tracking de operaciones.

**Formato**: `"INTRADAY_{bot_id}_{symbol}_{timestamp}_{uuid}"`

**Ejemplo**: `"INTRADAY_101_EURUSD_20251120_103000_a3f7c2d1"`

---

**Última actualización**: 20 de noviembre de 2025
