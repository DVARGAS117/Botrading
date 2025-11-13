# T10 - Construcción de Prompts e Integración con IA

**Ticket:** #26  
**Fase:** 2  
**Prioridad:** P0  
**Estado:** ✅ Implementado

---

## 📋 Resumen

Este ticket implementa el sistema de construcción de prompts y comunicación con Gemini 2.5 Pro API, permitiendo:

- Construcción de prompts estructurados por tipo de bot (numérico, visual, híbrido)
- Envío de consultas a Gemini 2.5 Pro con parámetros configurables
- Recepción y validación de respuestas JSON con decisiones de trading
- Tracking de tokens y costos
- Manejo robusto de errores con reintentos

---

## 🏗️ Arquitectura

### Componentes Principales

```
┌─────────────────────┐
│  PromptBuilder      │  Construye prompts específicos
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  GeminiClient       │  Comunica con API de Gemini
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ AIResponseParser    │  Parsea y valida respuestas JSON
└─────────────────────┘
```

### Flujo de Datos

1. **Preparación**: Se recopilan datos del mercado (indicadores, precios, imágenes)
2. **Construcción**: `PromptBuilder` genera un prompt estructurado
3. **Envío**: `GeminiClient` envía el prompt a Gemini 2.5 Pro
4. **Recepción**: Se recibe la respuesta JSON de la IA
5. **Parseo**: `AIResponseParser` valida y extrae la decisión
6. **Ejecución**: El sistema actúa según la decisión (OPERAR/NO_OPERAR/MANTENER/etc.)

---

## 📦 Módulos Implementados

### 1. PromptBuilder (`src/core/prompt_builder.py`)

**Responsabilidad:** Construir prompts específicos por tipo de bot

**Clases principales:**
- `BotType`: Enum (NUMERICO, VISUAL, HIBRIDO)
- `PromptType`: Enum (EVALUACION, REEVALUACION)
- `PromptData`: Dataclass con datos para el prompt
- `PromptTemplate`: Plantilla configurable
- `PromptBuilder`: Constructor principal

**Uso básico:**

```python
from src.core.prompt_builder import PromptBuilder, PromptData, BotType, PromptType

# Inicializar builder
builder = PromptBuilder()

# Preparar datos
data = PromptData(
    symbol="EURUSD",
    timeframe="5M",
    indicators={
        "rsi": 65.0,
        "ema_20": 1.2345,
        "ema_50": 1.2340,
        "macd": 0.0012
    },
    current_price=1.2350
)

# Construir prompt
prompt = builder.build_prompt(
    bot_type=BotType.NUMERICO,
    prompt_type=PromptType.EVALUACION,
    data=data,
    include_json_instructions=True
)
```

### 2. GeminiClient (`src/core/gemini_client.py`)

**Responsabilidad:** Comunicación con Gemini 2.5 Pro API

**Clases principales:**
- `GeminiConfig`: Configuración del cliente
- `GeminiResponse`: Respuesta de la API
- `GeminiClient`: Cliente principal

**Uso básico:**

```python
from src.core.gemini_client import GeminiClient, GeminiConfig

# Configurar cliente
config = GeminiConfig(
    model="gemini-2.0-flash-exp",
    temperature=0.7,
    max_tokens=2048,
    timeout=30,
    retry_attempts=3
)

client = GeminiClient(
    api_key="YOUR_API_KEY",
    config=config
)

# Enviar prompt
response = client.send_prompt(prompt)

if response.success:
    print(f"Respuesta: {response.content}")
    print(f"Tokens: {response.total_tokens}")
    print(f"Costo: ${response.cost}")
else:
    print(f"Error: {response.error_message}")
```

### 3. Integración con AIResponseParser

**Parser ya existente:** `src/core/ai_response_parser.py`

```python
from src.core.ai_response_parser import AIResponseParser

parser = AIResponseParser()

# Parsear respuesta de evaluación
parsed = parser.parse_evaluation(response.content)

if parsed.is_valid:
    if parsed.decision_type == AIDecisionType.OPERAR:
        print(f"Dirección: {parsed.direction.value}")
        print(f"SL: {parsed.stop_loss}, TP: {parsed.take_profit}")
    elif parsed.decision_type == AIDecisionType.NO_OPERAR:
        print(f"No operar: {parsed.reasoning}")
```

---

## 🔧 Configuración

### Archivo: `config/prompt_templates.example.json`

Define plantillas personalizadas para diferentes tipos de bots:

```json
{
    "prompt_templates": {
        "numerico_evaluacion": {
            "bot_type": "numerico",
            "prompt_type": "evaluacion",
            "template": "Analiza {symbol}..."
        }
    }
}
```

### Variables de Entorno

```bash
# API Key de Google Gemini
export GEMINI_API_KEY="your_api_key_here"
```

---

## 📊 Tipos de Bots Soportados

### Bot Numérico
- **Entrada:** Indicadores técnicos (RSI, EMAs, MACD, volumen)
- **Salida:** Decisión basada en datos numéricos
- **Plantilla:** `numerico_evaluacion`, `numerico_reevaluacion`

### Bot Visual
- **Entrada:** Imágenes de gráficos
- **Salida:** Decisión basada en análisis visual
- **Plantilla:** `visual_evaluacion`, `visual_reevaluacion`

### Bot Híbrido
- **Entrada:** Indicadores + Imágenes
- **Salida:** Decisión combinando ambos
- **Plantilla:** `hibrido_evaluacion`, `hibrido_reevaluacion`

---

## 🎯 Tipos de Consultas

### Evaluación Inicial
**¿Debo operar?**

**Respuestas posibles:**
- `OPERAR`: Con dirección (BUY/SELL), SL, TP, riesgo
- `NO_OPERAR`: Sin acción

### Reevaluación
**¿Qué hago con la posición abierta?**

**Respuestas posibles:**
- `MANTENER`: Sin cambios
- `ACTUALIZAR`: Modificar SL/TP
- `CERRAR`: Cerrar posición

---

## 📈 Métricas y Costos

El sistema trackea automáticamente:

- **Tokens de entrada**: Tamaño del prompt
- **Tokens de salida**: Tamaño de la respuesta
- **Costo**: Calculado según tarifas de Gemini
- **Latencia**: Tiempo de respuesta
- **Tasa de éxito**: Requests exitosos vs fallidos

```python
# Obtener estadísticas
stats = client.get_usage_statistics()

print(f"Total requests: {stats['total_requests']}")
print(f"Tokens totales: {stats['total_tokens_input'] + stats['total_tokens_output']}")
print(f"Costo total: ${stats['total_cost']}")
print(f"Latencia promedio: {stats['average_latency']}s")
```

---

## 🚨 Manejo de Errores

### Errores de API
- **Timeout**: Reintentos con backoff exponencial
- **Rate limit**: Espera y reintenta
- **Errores de autenticación**: Verificar API key

### Errores de Parseo
- **JSON inválido**: Registrado en historial de errores
- **Campos faltantes**: Detectado y reportado
- **Validación de negocio**: SL/TP vs dirección

```python
# Parseo seguro (sin excepciones)
parsed = parser.safe_parse_evaluation(response.content)

if not parsed.is_valid:
    print(f"Error: {parsed.error_type} - {parsed.error_message}")
    # Continuar con siguiente ciclo
```

---

## 🧪 Tests

### Tests Unitarios
- `tests/unit/test_prompt_builder.py`: 30+ tests
- `tests/unit/test_gemini_client.py`: 25+ tests

### Tests de Integración
- `tests/integration/test_ia_integration.py`: Flujo completo end-to-end

**Ejecutar tests:**

```bash
# Todos los tests
pytest tests/unit/test_prompt_builder.py -v
pytest tests/unit/test_gemini_client.py -v

# Con coverage
pytest tests/ --cov=src/core --cov-report=html
```

---

## 📋 Ejemplo Completo

Ver: `examples/prompt_builder_example.py`

```python
from src.core.prompt_builder import PromptBuilder, PromptData, BotType, PromptType
from src.core.gemini_client import GeminiClient, GeminiConfig
from src.core.ai_response_parser import AIResponseParser, AIDecisionType

# 1. Preparar datos
data = PromptData(
    symbol="EURUSD",
    timeframe="5M",
    indicators={"rsi": 65.0, "ema_20": 1.2345},
    current_price=1.2350
)

# 2. Construir prompt
builder = PromptBuilder()
prompt = builder.build_prompt(
    bot_type=BotType.NUMERICO,
    prompt_type=PromptType.EVALUACION,
    data=data
)

# 3. Enviar a IA
config = GeminiConfig(model="gemini-2.0-flash-exp")
client = GeminiClient(api_key="YOUR_API_KEY", config=config)
response = client.send_prompt(prompt)

# 4. Parsear respuesta
if response.success:
    parser = AIResponseParser()
    parsed = parser.parse_evaluation(response.content)
    
    if parsed.is_valid and parsed.decision_type == AIDecisionType.OPERAR:
        # Ejecutar operación
        print(f"Operar {parsed.direction.value}")
        print(f"SL: {parsed.stop_loss}, TP: {parsed.take_profit}")
```

---

## 🔗 Tickets Relacionados

- **T11**: Registro de tokens y costo por consulta ✅
- **T13**: Parametrización de modelo y tiempo de espera ✅
- **T23**: Cálculo y formato de indicadores (pendiente)
- **T24**: Generación de imágenes (pendiente)
- **T40**: Registro de errores de parsing ✅

---

## ✅ Criterios de Aceptación

**Escenario:** Construir prompt y recibir JSON de decisión

- ✅ **Dado** que el bot prepara payload numérico/visual según su tipo
- ✅ **Cuando** envía el prompt a Gemini 2.5 Pro con parámetros configurados
- ✅ **Entonces** recibe una respuesta JSON válida con dirección, SL, TP y riesgo

---

## 📝 Notas de Implementación

### Dependencias Agregadas

Agregar a `requirements.txt`:

```txt
google-generativeai>=0.3.0
Pillow>=10.0.0  # Para manejo de imágenes
```

### Variables de Configuración

Las plantillas se pueden personalizar en `config/prompt_templates.example.json`.

### Extensibilidad

- Agregar nuevos tipos de bots: Extender `BotType` enum
- Agregar nuevas plantillas: Usar `builder.add_template()`
- Cambiar modelo de IA: Modificar `GeminiConfig.model`

---

**Autor:** Botrading Team  
**Fecha:** 13 de Noviembre de 2025  
**Versión:** 1.0
