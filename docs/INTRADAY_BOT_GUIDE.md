# 📊 Guía Completa - Bot INTRADAY Gemini 3 Pro

## 📋 Índice
1. [Introducción](#introducción)
2. [Arquitectura del Bot](#arquitectura-del-bot)
3. [Configuración](#configuración)
4. [Flujo de Operación](#flujo-de-operación)
5. [Sistema de Indicadores](#sistema-de-indicadores)
6. [Integración con IA](#integración-con-ia)
7. [Gestión de Posiciones](#gestión-de-posiciones)
8. [Persistencia de Datos](#persistencia-de-datos)
9. [Métricas y Costos](#métricas-y-costos)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

El **Bot INTRADAY Gemini 3 Pro** (Bot 1) es una estrategia de trading automatizada que opera en marcos temporales intradía, utilizando análisis técnico avanzado y decisiones impulsadas por IA mediante Vertex AI (Gemini 3 Pro).

### Características Principales

- ✅ **Análisis Multi-Timeframe**: Combina análisis táctico (M15) y estratégico (D1)
- ✅ **IA Avanzada**: Utiliza Gemini 3 Pro para toma de decisiones
- ✅ **Gestión de Riesgo**: Stop loss inicial y trailing stop automático
- ✅ **Persistencia Completa**: Registra todas las operaciones y consultas IA
- ✅ **Sesiones de Trading**: Respeta horarios y símbolos por sesión
- ✅ **Tracking de Costos**: Monitorea costos de IA por operación
- ✅ **Timing Inteligente**: Control total del momento de evaluación con velas cerradas garantizadas

### Datos Técnicos

| Parámetro | Valor |
|-----------|-------|
| Bot ID | 3 |
| Estrategia | INTRADAY Baseline |
| Tipo | Numérico |
| Modelo IA | gemini-3-pro-preview |
| Timeframes | M15 (táctico), D1 (estratégico) |
| Max Tokens | 24,576 |
| Temperatura | 0.7 |
| Timeout | 120s |

**NOTA**: Existe también un **Bot 4 - INTRADAY Gemini 2.5 Pro** con la misma estrategia pero usando el modelo `gemini-2.5-pro`. Ambos bots generan magic numbers únicos (Bot 3 → 300000, Bot 4 → 400000) para evitar colisiones.

---

## ⏰ Sistema de Timing y Velas Cerradas

### Control de Momento de Evaluación

El bot implementa un **sistema inteligente de timing** que garantiza el uso exclusivo de **velas cerradas** para todos los análisis, asegurando consistencia y reproducibilidad de resultados.

#### Modos de Evaluación

**1. Evaluación Inmediata (`instant`)**
- Evalúa inmediatamente con datos disponibles
- Usa velas cerradas hasta el momento actual
- Ideal para testing y análisis en tiempo real

**2. Espera de Ciclo (`wait`)**
- Espera hasta el próximo minuto completo
- Garantiza que todas las velas del último período estén cerradas
- Recomendado para operación en producción

#### Lógica de Velas Cerradas

**Paquete Estratégico (D1)**
- ✅ Siempre usa solo velas cerradas (excluye día actual)
- No hay riesgo de datos en formación

**Paquete Táctico (M15)**
- ✅ Detecta automáticamente velas en formación
- Una vela M15 se forma cada 15 minutos (0, 15, 30, 45)
- Si `current_second > 0` o `current_minute % 15 != 0`: vela en formación
- Si vela en formación: se excluye del análisis
- Garantiza indicadores calculados sobre datos definitivos

#### Ejemplo de Funcionamiento

```
Hora actual: 09:17:30
├─► Vela M15 actual (09:15-09:30): EN FORMACIÓN ❌
├─► Última vela cerrada: 09:15-09:30 (completa) ✅
└─► Análisis usa datos hasta 09:15

Después de esperar ciclo (09:18:00):
├─► Vela M15 09:15-09:30: CERRADA ✅
└─► Análisis incluye vela completa de 09:15-09:30
```

### Interfaz de Usuario

Al iniciar el bot, siempre verás:

```
⏰ MODO DE EVALUACIÓN
============================================================
El bot puede:
• INSTANT: Evaluar inmediatamente con datos disponibles
• WAIT: Esperar el próximo ciclo de vela cerrada (1 min después)
============================================================
IMPORTANTE: El bot siempre usa velas CERRADAS, nunca velas en formación.
Si ejecutas a las 9:17, usará datos hasta la vela cerrada a las 9:15.
============================================================

¿Deseas evaluar al INSTANTE o ESPERAR el ciclo? (instant/wait):
```

---

## 🏗️ Arquitectura del Bot

### Estructura de Directorios

```
src/bots/strategies/intraday/gemini_3_pro/bot_1/
├── strategy.py                      # Clase principal del bot
├── intraday_indicators.py           # Calculador de indicadores
├── logs/                            # Logs específicos del bot
└── config/
    └── prompt_templates/
        ├── intraday_gemini_3_pro_bot_1_system.txt
        └── intraday_gemini_3_pro_bot_1_user.txt
```

### Componentes Principales

#### 1. **IntradayBot1Strategy** (strategy.py)
- Hereda de `BaseBotOperations`
- Orquesta el ciclo completo de trading
- Gestiona comunicación con IA
- Ejecuta decisiones de trading

#### 2. **IntradayIndicatorCalculator** (intraday_indicators.py)
- Calcula paquetes de indicadores tácticos (M15)
- Calcula paquetes de indicadores estratégicos (D1)
- Pre-calcula todos los indicadores técnicos
- Genera actualizaciones incrementales

#### 3. **Repositorios**
- `IAQueryRepository`: Persistencia de consultas IA
- `OperationsRepository`: Registro de operaciones MT5

---

## ⚙️ Configuración

### 1. Configuración del Bot

**Archivo**: `src/bots/base/base_bot_operations.py` (BotConfig)

```python
BotConfig(
    bot_id=101,
    bot_name="INTRADAY Bot 1",
    bot_type="numerico",
    symbols=["EURUSD", "GBPUSD", "USDJPY"],
    strategy_type="INTRADAY",
    risk_per_trade=1.0,         # 1% riesgo por operación
    max_daily_risk=3.0,         # Máx 3R pérdida diaria
    max_daily_profit=5.0,       # Detener en +5R ganancia
    enable_dual_orders=False,   # Sin órdenes duales
    ai_model="gemini-3-pro-preview",
    log_level="INFO",
)
```

### 2. Horarios de Trading

**Archivo**: `config/schedule.json`

```json
{
  "sessions": {
    "asian": {
      "name": "Asian Session",
      "start": "00:00",
      "end": "09:00",
      "timezone": "America/Lima",
      "symbols": ["USDJPY", "AUDUSD"]
    },
    "european": {
      "name": "European Session",
      "start": "02:00",
      "end": "12:00",
      "timezone": "America/Lima",
      "symbols": ["EURUSD", "GBPUSD"]
    },
    "american": {
      "name": "American Session",
      "start": "08:00",
      "end": "17:00",
      "timezone": "America/Lima",
      "symbols": ["EURUSD", "GBPUSD", "USDJPY"]
    }
  }
}
```

### 3. Configuración de IA

**Archivo**: `config/ia_config.json`

```json
{
  "default_profile": "gemini-3-pro",
  "profiles": {
    "gemini-3-pro": {
      "model": "gemini-3-pro-preview",
      "temperature": 0.7,
      "max_tokens": 24576,
      "top_p": 0.95,
      "timeout": 120
    }
  }
}
```

### 4. Credenciales

**Archivo**: `config/credentials.json`

```json
{
  "google_cloud": {
    "project_id": "tu-proyecto-id",
    "location": "us-central1",
    "api_key": "tu-api-key-vertex-ai"
  },
  "mt5": {
    "login": 12345678,
    "password": "tu-password",
    "server": "MetaQuotes-Demo"
  }
}
```

---

## 🔄 Flujo de Operación

### Ciclo Principal: `run_trading_cycle()`

```
┌─────────────────────────────────────────┐
│  1. Verificar Horario de Trading       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Verificar Límites Diarios           │
│     - Max daily risk (-3R)              │
│     - Max daily profit (+5R)            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. Obtener Símbolos Activos            │
│     - Filtrar por sesión actual         │
│     - Verificar spreads y volatilidad   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. Por Cada Símbolo Activo:            │
│     ├─► execute_cycle(symbol)           │
│     ├─► _execute_decision(decision)     │
│     └─► _update_performance_metrics()   │
└─────────────────────────────────────────┘
```

### Ciclo de Análisis: `execute_cycle(symbol)`

```
┌─────────────────────────────────────────┐
│  1. Preparar Datos para IA              │
│     ├─► Generar operation_id            │
│     ├─► Calcular paquetes indicadores   │
│     │   - Táctico: 200 velas M15        │
│     │   - Estratégico: 30 velas D1      │
│     ├─► Cargar prompts                  │
│     └─► Reemplazar variables            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Consultar Gemini 3 Pro              │
│     ├─► Enviar system + user prompt     │
│     ├─► Recibir respuesta JSON          │
│     └─► Capturar tokens y costo         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. Parsear Respuesta IA                │
│     ├─► Extraer acción                  │
│     ├─► Extraer parámetros (SL, TP)     │
│     └─► Validar formato                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. Registrar Consulta IA               │
│     ├─► Guardar en ia_queries.db        │
│     ├─► Asociar operation_id            │
│     └─► Registrar costo y tokens        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. Retornar Decisión                   │
│     └─► Con metadata completa           │
└─────────────────────────────────────────┘
```

### Ejecución de Decisión: `_execute_decision(symbol, decision)`

```
┌─────────────────────────────────────────┐
│  Evaluar Acción Decidida                │
└──────────────┬──────────────────────────┘
               │
               ├─► COMPRAR/VENDER
               │   └─► _execute_open_position()
               │       ├─► Enviar orden MT5
               │       ├─► Registrar en operations.db
               │       └─► Guardar SL/TP iniciales
               │
               ├─► AJUSTAR_SL_TP
               │   └─► _execute_update_position()
               │       ├─► Modificar posición MT5
               │       └─► Actualizar operations.db
               │
               ├─► CERRAR
               │   └─► _execute_close_position()
               │       ├─► Cerrar posición MT5
               │       └─► Marcar como CLOSED en BD
               │
               ├─► MANTENER
               │   └─► (No acción, continuar)
               │
               └─► NO_OPERAR
                   └─► (Sin posición, esperar)
```

---

## 📊 Sistema de Indicadores

### Paquete Táctico (M15) - 200 Velas Cerradas

**Período**: Últimas 200 velas de 15 minutos (50 horas de datos)

**Características**:
- ✅ **Solo velas cerradas**: Excluye vela actual si está en formación
- ✅ **Detección automática**: Algoritmo inteligente de timing
- ✅ **Consistencia**: Indicadores calculados sobre datos definitivos

**Indicadores Calculados**:
- **EMA 20**: Media móvil exponencial 20 períodos
- **EMA 200**: Media móvil exponencial 200 períodos
- **VWAP**: Volume Weighted Average Price
- **RSI 14**: Relative Strength Index
- **ATR 14**: Average True Range
- **Bollinger Bands**: Superior, inferior, ancho (20 períodos, 2 std)

**Estructura de Datos**:
```json
{
  "timestamp": "2025-11-20 10:00:00",
  "open": 1.05123,
  "high": 1.05234,
  "low": 1.05089,
  "close": 1.05156,
  "volume": 1234.0,
  "ema_20": 1.05100,
  "ema_200": 1.05000,
  "vwap": 1.05120,
  "rsi_14": 55.3,
  "atr_14": 0.00125,
  "bb_upper": 1.05300,
  "bb_lower": 1.04900,
  "bb_width": 0.00400
}
```

### Paquete Estratégico (D1) - 30 Velas Cerradas

**Período**: Últimas 30 velas diarias COMPLETAS (excluye día actual)

**Características**:
- ✅ **Solo velas cerradas**: Excluye automáticamente el día actual
- ✅ **Datos definitivos**: No cambia después del cierre diario
- ✅ **Consistencia**: Resultados reproducibles en cualquier momento

**Indicadores Calculados**:
- **EMA 200**: Media móvil exponencial 200 períodos
- **ATR 14**: Average True Range
- **Previous OHLC**: Datos del día anterior (close, high, low)

**Estructura de Datos**:
```json
{
  "date": "2025-11-19",
  "close": 1.05156,
  "ema_200": 1.05000,
  "atr_14": 0.00125,
  "prev_close": 1.05100,
  "prev_high": 1.05200,
  "prev_low": 1.05000
}
```

### Pre-Cálculo de Indicadores

**Problema**: Calcular EMA 200 requiere 200 velas de histórico previo.

**Solución**: Se obtienen velas adicionales para garantizar cálculo correcto:

```python
# Para 200 velas M15 con EMA 200 válida:
# - Velas a retornar: 200
# - Histórico necesario: +250
# - Total obtenido: 450 velas
total_candles_needed = candles_to_return + 250

# Calcular indicadores sobre 450 velas
ema_200 = calculate_ema(df['close'], 200)

# Retornar solo las últimas 200 con indicadores completos
return df.tail(200)
```

---

## 🤖 Integración con IA

### Sistema de Prompts

**Ubicación**: `config/prompt_templates/`

#### 1. System Prompt
**Archivo**: `intraday_gemini_3_pro_bot_1_system.txt`

Define el rol y comportamiento de la IA:
- Personalidad del asistente
- Metodología de análisis
- Formato de respuesta esperado
- Restricciones y reglas

#### 2. User Prompt
**Archivo**: `intraday_gemini_3_pro_bot_1_user.txt`

Contiene el contexto específico de cada consulta:
- Símbolo a analizar
- Operation ID único
- Timestamp actual
- Paquetes de indicadores (M15 y D1)
- Información de posición activa (si existe)

### Variables del Prompt

```python
{
    "{symbol}": "EURUSD",
    "{operation_id}": "INTRADAY_101_EURUSD_20251120_103000_a3f7c2d1",
    "{current_time}": "2025-11-20 10:30:00",
    "{tactical_package}": "[...200 velas M15...]",
    "{strategic_package}": "[...30 velas D1...]",
    "{current_position}": "LONG @ 1.05000 (+1.5R)" o "NONE"
}
```

### Formato de Respuesta IA

**Estructura JSON Esperada**:

```json
{
  "accion": "COMPRAR | VENDER | NO_OPERAR | MANTENER | CERRAR | AJUSTAR_SL_TP",
  "razonamiento": "Análisis detallado del mercado...",
  "direccion": "LONG | SHORT",
  "stop_loss": 1.04900,
  "take_profit": 1.05300,
  "confianza": 85.0,
  "estrategia_usada": "Breakout de rango con confirmación EMA",
  "diagnostico_mercado": "Tendencia alcista confirmada en D1..."
}
```

### Configuración de Vertex AI

```python
VertexAIConfig(
    model="gemini-3-pro-preview",
    temperature=0.7,           # Balance creatividad/precisión
    max_tokens=24576,          # 3x el estándar para análisis profundo
    top_p=0.95,               # Diversidad de respuestas
    timeout=120,              # 2 minutos para razonamiento profundo
)
```

---

## 🎯 Gestión de Posiciones

### Apertura de Posición

**Método**: `_execute_open_position(symbol, decision)`

**Flujo**:
1. Validar decisión (dirección, SL, TP obligatorios)
2. Calcular tamaño de lote según riesgo
3. Enviar orden a MT5 via `OrderManager`
4. Esperar confirmación de ejecución
5. Registrar operación en `operations.db` con valores iniciales:
   - `stop_loss_initial`: SL original (para cálculo de R)
   - `take_profit_initial`: TP original
   - `actual_entry_price`: Precio real de entrada
   - `magic_number`: Ticket de MT5
   - `conversation_id`: operation_id para tracking

### Actualización de Posición (Trailing Stop)

**Método**: `_execute_update_position(symbol, decision)`

**Flujo**:
1. Obtener posición activa de MT5
2. Extraer nuevos valores de SL/TP de la decisión IA
3. Modificar posición en MT5 via `PositionManager`
4. Actualizar registro en `operations.db`:
   - `stop_loss`: Nuevo SL (actualizado)
   - `take_profit`: Nuevo TP (actualizado)
   - `stop_loss_initial`: **NO CAMBIA** (preserva valor original)
   - `updated_at`: Timestamp de actualización

**Importante**: El SL inicial NUNCA se modifica, permitiendo calcular correctamente el PnL en términos de R.

### Cálculo de PnL en R

```python
# Obtener SL inicial desde BD
sl_inicial = operation.stop_loss_initial

# Calcular riesgo inicial (1R)
risk_points = abs(entry_price - sl_inicial)
risk_pips = risk_points / pip_value

# Calcular PnL actual en puntos
if direction == "LONG":
    pnl_points = current_price - entry_price
else:
    pnl_points = entry_price - current_price

# Calcular PnL en R
pnl_r = pnl_points / risk_points if risk_points > 0 else 0.0
```

### Cierre de Posición

**Método**: `_execute_close_position(symbol, decision)`

**Flujo**:
1. Obtener posición activa de MT5
2. Enviar orden de cierre via `OrderManager`
3. Esperar confirmación de cierre
4. Actualizar registro en `operations.db`:
   - `status`: CLOSED
   - `exit_price`: Precio de cierre
   - `pnl_usd`: PnL final en USD
   - `pnl_r`: PnL final en múltiplos de R
   - `closed_at`: Timestamp de cierre

---

## 💾 Persistencia de Datos

### Base de Datos: Consultas IA

**Archivo**: `data/consultas_ia.db`  
**Tabla**: `ia_queries`

**Esquema**:
```sql
CREATE TABLE ia_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id INTEGER NOT NULL,
    ia_id INTEGER NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    query_type VARCHAR(20) NOT NULL,  -- 'EVALUATION' | 'REEVALUATION'
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    tokens_input INTEGER,
    tokens_output INTEGER,
    tokens_total INTEGER,
    cost_usd REAL,
    action_decided VARCHAR(50),
    operation_id VARCHAR(100),        -- Para agrupar consultas
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Índices**:
- `idx_operation_id`: Para consultar por operation_id
- `idx_bot_symbol`: Para consultar por bot y símbolo
- `idx_created_at`: Para consultas temporales

### Base de Datos: Operaciones

**Archivo**: `data/operations.db`  
**Tabla**: `operations`

**Esquema**:
```sql
CREATE TABLE operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    magic_number INTEGER NOT NULL UNIQUE,  -- Ticket MT5
    bot_id INTEGER NOT NULL,
    ia_id INTEGER NOT NULL,
    order_type VARCHAR(10) NOT NULL,       -- 'MARKET' | 'PENDING'
    symbol VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,        -- 'BUY' | 'SELL'
    suggested_price REAL NOT NULL,
    actual_entry_price REAL,
    stop_loss REAL NOT NULL,
    take_profit REAL NOT NULL,
    stop_loss_initial REAL NOT NULL,       -- ⭐ SL original (nunca cambia)
    take_profit_initial REAL NOT NULL,     -- ⭐ TP original (nunca cambia)
    lot_size REAL NOT NULL,
    risk_percentage REAL NOT NULL,
    status VARCHAR(20) NOT NULL,           -- 'OPEN' | 'CLOSED' | 'CANCELLED'
    conversation_id VARCHAR(100),          -- operation_id
    exit_price REAL,
    pnl_usd REAL,
    pnl_r REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);
```

**Índices**:
- `idx_magic_number`: Para búsqueda rápida por ticket
- `idx_bot_symbol_status`: Para consultas de posiciones abiertas
- `idx_conversation_id`: Para agrupar operaciones

---

## 📈 Métricas y Costos

### Tracking de Costos por Operación

**Concepto**: Un `operation_id` agrupa múltiples consultas IA:

```
INTRADAY_101_EURUSD_20251120_103000_a3f7c2d1
├─► Consulta 1: Evaluación inicial (COMPRAR)  $0.05
├─► Consulta 2: Reevaluación +0.5R (MANTENER) $0.05
├─► Consulta 3: Reevaluación +1.2R (MANTENER) $0.05
├─► Consulta 4: Reevaluación +2.0R (CERRAR)   $0.05
└─► Costo Total: $0.20
```

**Consulta de Costos**:
```python
# Obtener todas las consultas de una operación
queries = ia_query_repository.get_queries_by_operation_id(operation_id)

# Calcular costo total
total_cost = sum(q.cost_usd for q in queries)
total_tokens = sum(q.tokens_total for q in queries)

print(f"Costo total: ${total_cost:.4f}")
print(f"Tokens totales: {total_tokens}")
```

### Precios Gemini 3 Pro Preview

| Nivel de Contexto | Input (por 1M tokens) | Output (por 1M tokens) |
|-------------------|----------------------|------------------------|
| Estándar (≤128K)  | $2.00 | $12.00 |
| Largo (>128K)     | $4.00 | $18.00 |

**Conversión a 1K tokens**:
- Estándar Input: $0.002
- Estándar Output: $0.012
- Largo Input: $0.004
- Largo Output: $0.018

**Cálculo Automático**:
```python
# El sistema detecta automáticamente el nivel según tokens input
if tokens_input > 128_000:
    input_rate = 0.004  # Largo contexto
    output_rate = 0.018
else:
    input_rate = 0.002  # Estándar
    output_rate = 0.012

cost_usd = (tokens_input * input_rate + tokens_output * output_rate) / 1000
```

### Métricas de Rendimiento

**Archivo**: `data/daily_metrics.db`

```python
# Métricas diarias del bot
daily_metrics = {
    "bot_id": 101,
    "date": "2025-11-20",
    "trades_executed": 5,
    "trades_won": 3,
    "trades_lost": 2,
    "total_pnl_r": 2.5,
    "total_pnl_usd": 125.00,
    "ia_cost_total": 1.25,
    "max_drawdown_r": -1.5,
    "win_rate": 60.0,
    "avg_trade_duration": "4h 30m"
}
```

---

## 🔧 Troubleshooting

### Problema 1: Bot no ejecuta operaciones

**Síntomas**:
- Bot inicia pero no abre posiciones
- Logs muestran "Fuera de horario de trading"

**Solución**:
1. Verificar `config/schedule.json`
2. Confirmar zona horaria correcta (America/Lima)
3. Verificar que el símbolo esté en la sesión activa
4. Revisar filtros de spread y volatilidad

```bash
# Ver logs del bot
tail -f src/bots/strategies/intraday/gemini_3_pro/bot_1/logs/bot_101.log
```

### Problema 2: Error al calcular indicadores

**Síntomas**:
- Error: "Datos insuficientes para EURUSD M15"
- Stack trace en `calculate_tactical_package()`

**Solución**:
1. Verificar conexión a MT5
2. Confirmar que el símbolo existe en la cuenta
3. Verificar que hay suficiente histórico (mín. 450 velas M15)

```python
# Test de conexión MT5
from src.core.mt5_connector import MT5Connector
mt5 = MT5Connector()
mt5.initialize()
info = mt5.symbol_info("EURUSD")
print(f"Símbolo disponible: {info is not None}")
```

### Problema 3: Costos IA muy altos

**Síntomas**:
- Costos >$0.10 por consulta
- Muchas reevaluaciones innecesarias

**Solución**:
1. Revisar configuración `max_tokens` (reducir si es necesario)
2. Ajustar intervalo de reevaluación (default: 15 min)
3. Optimizar prompts (reducir texto redundante)

```python
# Consultar costos por operación
queries = ia_query_repository.get_queries_by_operation_id(operation_id)
for q in queries:
    print(f"{q.query_type}: ${q.cost_usd:.4f} ({q.tokens_total} tokens)")
```

### Problema 4: SL/TP no se actualizan

**Síntomas**:
- IA decide AJUSTAR_SL_TP pero no hay cambio en MT5
- Error en `_execute_update_position()`

**Solución**:
1. Verificar que `PositionManager` está inicializado
2. Confirmar que la posición existe en MT5
3. Revisar permisos de la cuenta (algunos brokers bloquean modificaciones)

```python
# Verificar posición en MT5
positions = position_manager.get_positions_by_symbol("EURUSD")
if positions:
    pos = positions[0]
    print(f"SL actual: {pos.sl}, TP actual: {pos.tp}")
```

### Problema 5: Operation ID duplicado

**Síntomas**:
- Error: "operation_id ya existe"
- Colisión de IDs en la base de datos

**Solución**:
1. El UUID garantiza unicidad, pero si persiste:
2. Verificar sincronización de timestamp del sistema
3. Regenerar operation_id

```python
# Forzar generación de nuevo operation_id
import uuid
from datetime import datetime

operation_id = f"INTRADAY_{bot_id}_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
```

---

## 📚 Referencias

### Archivos Clave

- `src/bots/strategies/intraday/gemini_3_pro/bot_1/strategy.py`
- `src/bots/strategies/intraday/gemini_3_pro/bot_1/intraday_indicators.py`
- `src/bots/base/base_bot_operations.py`
- `src/core/vertex_ai_client.py`
- `src/core/ia_query_repository.py`
- `src/core/operations_repository.py`

### Documentación Relacionada

- [Vertex AI Setup](VERTEX_AI_SETUP.md)
- [Gemini Pricing](GEMINI_PRICING.md)
- [Trading Sessions Implementation](TRADING_SESSIONS_IMPLEMENTATION.md)
- [Prompts Intraday Implementation](PROMPTS_INTRADAY_IMPLEMENTATION.md)
- [Integración Completa INTRADAY](../context/INTRADAY_INTEGRACION_COMPLETA.md)

### Commits Relevantes

1. `fdada58` - Implementar estructura base estrategia INTRADAY
2. `9905eff` - Implementar cálculo de indicadores con pre-cálculo correcto
3. `8fa64ef` - Implementar calculate_tactical_update() para actualizaciones incrementales
4. `97056f8` - Ajustar flujo INTRADAY - D1 solo cerradas, operation_id único
5. `21ef208` - Integrar IntradayIndicatorCalculator y IAQueryRepository
6. `aff69a0` - Implementar stop_loss_initial y take_profit_initial
7. `dc497d4` - Integrar valores iniciales SL/TP al abrir posiciones
8. `7d4bb79` - Implementar trailing stop completo con actualización de BD

---

## 📞 Soporte

Para reportar bugs o solicitar features:
- **GitHub Issues**: https://github.com/DVARGAS117/Botrading/issues
- **Proyecto**: https://github.com/users/DVARGAS117/projects/2

---

**Última actualización**: 20 de noviembre de 2025  
**Versión**: 1.0.0  
**Estado**: ✅ Producción
