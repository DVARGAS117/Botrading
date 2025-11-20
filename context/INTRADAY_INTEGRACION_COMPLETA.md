# 📊 INTEGRACIÓN COMPLETA - Estrategia INTRADAY Bot 1

## ✅ Resumen de Integración

Se ha integrado completamente el sistema INTRADAY Bot 1 con los siguientes componentes:

### 1. **Sistema de Prompts** 📝

Se creó la carpeta `prompts/` con 3 archivos template donde deberás escribir tus prompts:

```
src/bots/strategies/intraday/gemini_3_pro/bot_1/prompts/
├── system_prompt.txt             # Prompt del sistema
├── user_prompt_evaluation.txt    # Para evaluaciones iniciales (SIN operación activa)
└── user_prompt_reevaluation.txt  # Para reevaluaciones (CON operación activa)
```

#### **Variables Disponibles en User Prompts**

Puedes usar estas variables en tus prompts, y se reemplazarán automáticamente:

- `{symbol}`: Símbolo a analizar (ej: EURUSD)
- `{operation_id}`: ID único de la operación (formato: INTRADAY_5_EURUSD_20251119_215500_abc123)
- `{current_time}`: Hora actual (formato: 2025-11-19 21:55:00)
- `{tactical_package}`: JSON con 200 velas M15 y todos los indicadores
- `{strategic_package}`: JSON con 30 velas D1 CERRADAS y todos los indicadores
- `{current_position}`: Info de la posición activa (solo en reevaluación)

#### **Ejemplo de Uso**

```
Analiza {symbol} en el momento {current_time}.
Operation ID: {operation_id}

Paquete Estratégico (D1):
{strategic_package}

Paquete Táctico (M15):
{tactical_package}
```

---

### 2. **Paquetes de Indicadores** 📈

#### **Paquete Táctico (M15)**: 200 velas
- Timeframe: M15
- Cantidad: 200 velas
- Cálculo: Inicial COMPLETO con todos los indicadores pre-calculados
- Formato: JSON con array de objetos, cada vela incluye:
  - OHLCV: `open`, `high`, `low`, `close`, `volume`, `tick_volume`, `spread`, `real_volume`
  - Indicadores: `ema_200`, `rsi`, `adx`, `plus_di`, `minus_di`, `atr`

#### **Paquete Estratégico (D1)**: 30 velas CERRADAS
- Timeframe: D1
- Cantidad: 30 velas
- **IMPORTANTE**: Excluye el día actual (solo velas completas/cerradas)
- Formato: JSON con array de objetos, misma estructura que M15

---

### 3. **Flujo de Ejecución** ⚙️

#### **Método: `execute_cycle(symbol)`**

Flujo completo:

```python
1. prepare_data_for_ai()
   ├── Generar operation_id único
   ├── Calcular paquetes M15 (200) y D1 (30 cerradas)
   ├── Cargar prompts desde archivos
   ├── Reemplazar variables en user_prompt
   └── Retornar diccionario completo
   
2. Consultar Gemini 3 Pro (TODO: Implementar)
   └── Usar system_prompt y user_prompt
   
3. parse_ai_response()
   └── Parsear respuesta JSON de Gemini
   
4. IAQueryRepository.create_query()
   ├── Registrar consulta con operation_id
   ├── Guardar tokens y costo
   └── Asociar acción decidida
   
5. Retornar decisión con metadata
```

---

### 4. **Tracking de Costos** 💰

Cada consulta se registra en la base de datos con:

- `operation_id`: ID único de la operación
- `prompt`: Prompt completo enviado (system + user)
- `response`: Respuesta de Gemini 3 Pro
- `tokens_input`: Tokens de entrada
- `tokens_output`: Tokens de salida
- `cost_usd`: Costo en USD
- `action_decided`: Acción decidida (COMPRAR/VENDER/NO_OPERAR/MANTENER/CERRAR)

**Base de datos**: `data/consultas_ia.db`

Puedes consultar costos por operación:

```python
ia_query_repository.get_queries_by_operation_id(operation_id)
```

---

### 5. **Configuración del Bot** ⚙️

**Archivo**: `src/bots/strategies/intraday/gemini_3_pro/bot_1/config.py`

```python
bot_id = 5
bot_name = "INTRADAY Baseline"
bot_type = "numerico"
symbols = ["EURUSD"]
trading_hours = ("08:00", "16:00")
risk_per_trade = 1.0  # 1% por operación
max_daily_risk = 3.0  # Máximo 3R de pérdida
enable_dual_orders = False  # Una orden por señal
```

**Indicadores configurados**:
- EMA 200
- RSI (14)
- ADX (14)
- +DI (14)
- -DI (14)
- ATR (14)

---

### 6. **Tests de Integración** ✅

**Archivo**: `tests/bots/strategies/intraday/gemini_3_pro/bot_1/test_strategy_integration.py`

```bash
6/6 tests passing:
✅ test_prompts_directory_exists
✅ test_prompt_files_exist
✅ test_prepare_data_for_ai_structure
✅ test_prepare_data_for_ai_variable_replacement
✅ test_operation_id_generation_unique
✅ test_execute_cycle_structure
```

---

## 📋 Próximos Pasos

### 1. **Escribir Prompts** ✍️

Edita los siguientes archivos con tus prompts personalizados:

```
src/bots/strategies/intraday/gemini_3_pro/bot_1/prompts/
├── system_prompt.txt             # Define el rol de la IA
├── user_prompt_evaluation.txt    # Análisis para nueva operación
└── user_prompt_reevaluation.txt  # Análisis de operación activa
```

### 2. **Implementar Conexión a Gemini 3 Pro**

En `strategy.py`, método `execute_cycle()`, línea ~150:

```python
# TODO: Implementar llamada real a Gemini 3 Pro
ai_response = {
    "response_text": "...",
    "tokens_input": ...,
    "tokens_output": ...,
    "cost_usd": ...,
}
```

### 3. **Implementar Parser de Respuesta**

En `strategy.py`, método `parse_ai_response()`:

```python
def parse_ai_response(self, response_text: str) -> Dict[str, Any]:
    # TODO: Implementar parser real
    # Retornar estructura:
    return {
        "accion": "COMPRAR" | "VENDER" | "NO_OPERAR" | "MANTENER" | "CERRAR",
        "razonamiento": str,
        "direccion": "LONG" | "SHORT" | None,
        "stop_loss": float,
        "take_profit": float,
        "confianza": float,
    }
```

### 4. **Implementar Helpers de Posición**

En `strategy.py`:

- `_has_active_position(symbol)`: Verificar con MetaTrader 5
- `_get_current_position_info(symbol)`: Obtener datos reales de la posición

---

## 🔍 Ejemplo de Operation ID

Formato: `INTRADAY_5_EURUSD_20251119_215500_abc123`

Partes:
1. `INTRADAY`: Tipo de estrategia
2. `5`: Bot ID
3. `EURUSD`: Símbolo
4. `20251119`: Fecha (YYYYMMDD)
5. `215500`: Hora (HHMMSS)
6. `abc123`: UUID (primeros 8 caracteres)

---

## 📊 Estructura de Datos JSON

### Ejemplo de una vela en el paquete:

```json
{
  "time": "2025-11-19 10:00:00",
  "open": 1.05123,
  "high": 1.05234,
  "low": 1.05089,
  "close": 1.05156,
  "volume": 1234,
  "tick_volume": 567,
  "spread": 12,
  "real_volume": 1234,
  "ema_200": 1.05000,
  "rsi": 55.3,
  "adx": 28.5,
  "plus_di": 25.3,
  "minus_di": 18.7,
  "atr": 0.00125
}
```

---

## 🎯 Commits Realizados

1. ✅ **feat: Implementar cálculo de indicadores INTRADAY con pre-cálculo correcto**
2. ✅ **feat: Implementar calculate_tactical_update() para actualizaciones incrementales**
3. ✅ **feat: Ajustar flujo INTRADAY - D1 solo cerradas, operation_id único**
4. ✅ **feat: Integrar IntradayIndicatorCalculator y IAQueryRepository en strategy.py con sistema de prompts**

---

## 📝 Notas Importantes

1. **No hay persistencia de conversation_id**: Cada consulta crea una nueva conversación en Gemini
2. **operation_id es único por operación**: Permite agrupar múltiples consultas (evaluación + reevaluaciones)
3. **D1 excluye día actual**: Solo velas cerradas para estabilidad de datos
4. **M15 siempre 200 velas**: Paquete completo en cada consulta (no incremental)
5. **Bot ID = 5**: Limitación de validación (1-5), ajustado desde 101

---

## 🚀 ¿Listo para escribir tus prompts?

Ahora puedes editar los 3 archivos de prompts en:

```
src/bots/strategies/intraday/gemini_3_pro/bot_1/prompts/
```

Usa las variables disponibles y define cómo quieres que Gemini 3 Pro analice los datos.

¡Buena suerte! 🎉
