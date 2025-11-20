# 🤖 Bots de Trading - Botrading

## 📁 Estructura de Carpetas

Los bots ahora se organizan por **estrategia** y **agente IA**.

Para la estrategia VWAP con Gemini 3 Pro:

```
src/bots/
├── strategies/
│   └── vwap/
│       └── gemini_3_pro/
│           ├── __init__.py
│           ├── bot_1.py           # Numérico baseline VWAP
│           ├── bot_2.py           # Numérico con prompts alternativos
│           ├── bot_3.py           # Visual con indicadores en gráficos
│           ├── bot_4.py           # Híbrido (visual + numérico)
│           └── bot_5.py           # Visual + numérico separados
└── bot_X/                         # Ubicación original (compatibilidad)
  ├── __init__.py
  ├── main.py
  ├── config.py
  └── strategy.py
```

## 🎯 Los 5 Bots

### **Bot 1: Numérico Baseline**
- **Carpeta nueva:** `strategies/vwap/gemini_3_pro/bot_1.py`
- **Carpeta original:** `bot_1/`
- **Tipo:** Análisis numérico puro
- **Datos:** Indicadores técnicos (EMA, RSI, MACD, Volumen)
- **Estrategia:** Dual Market + Limit
- **Objetivo:** Establecer baseline de rendimiento numérico

### **Bot 2: Numérico Alternativo**
- **Carpeta nueva:** `strategies/vwap/gemini_3_pro/bot_2.py`
- **Carpeta original:** `bot_2/`
- **Tipo:** Análisis numérico con prompts diferentes
- **Datos:** Mismos indicadores que Bot 1
- **Estrategia:** Dual Market + Limit
- **Objetivo:** Comparar impacto de diferentes enfoques en prompts

### **Bot 3: Visual Completo**
- **Carpeta nueva:** `strategies/vwap/gemini_3_pro/bot_3.py`
- **Carpeta original:** `bot_3/`
- **Tipo:** Análisis visual de gráficos
- **Datos:** Imágenes de velas + indicadores dibujados
- **Estrategia:** Dual Market + Limit
- **Objetivo:** Evaluar capacidad de análisis visual de IA

### **Bot 4: Híbrido Estratégico**
- **Carpeta nueva:** `strategies/vwap/gemini_3_pro/bot_4.py`
- **Carpeta original:** `bot_4/`
- **Tipo:** Híbrido (visual + numérico)
- **Datos:** Imagen para apertura, numérico para reevaluación
- **Estrategia:** Dual Market + Limit
- **Objetivo:** Combinar ventajas de ambos enfoques

### **Bot 5: Visual + Numérico Separado**
- **Carpeta nueva:** `strategies/vwap/gemini_3_pro/bot_5.py`
- **Carpeta original:** `bot_5/`
- **Tipo:** Visual con datos numéricos separados
- **Datos:** Imágenes de velas limpias + JSON de indicadores
- **Estrategia:** Dual Market + Limit
- **Objetivo:** Evaluar procesamiento separado de información

## 🚀 Cómo Ejecutar un Bot

### Ejecución Individual

```bash
# Bot 1 (Numérico Baseline VWAP, compatibilidad actual)
python -m src.bots.bot_1.main

# Bot 2 (Numérico Alternativo)
python -m src.bots.bot_2.main

# Bot 3 (Visual Completo)
python -m src.bots.bot_3.main

# Bot 4 (Híbrido Estratégico)
python -m src.bots.bot_4.main

# Bot 5 (Visual + Numérico Separado)
python -m src.bots.bot_5.main

# Punto de entrada recomendado por estrategia/agente (VWAP + Gemini 3 Pro)
# (cuando se cree un orquestador o CLI específica por estrategia)
# from bots.strategies.vwap.gemini_3_pro.bot_1 import bot_1_main
```

### Ejecución Orquestada (Todos)

```bash
python -m src.bots.orchestrator
```

## ⚙️ Configuración

Cada bot tiene su configuración en:
- `config/bot_X_config.json` (crear cuando se implemente)

O usar la configuración global:
- `config/settings.json`

## 📊 Datos de Entrada

### Bots Numéricos (1, 2)
```json
{
  "symbol": "EURUSD",
  "timeframes": {
    "5M": { "ema_20": 1.1042, "ema_50": 1.1038, "rsi": 58.3, ... },
    "15M": { ... },
    "1H": { ... }
  }
}
```

### Bots Visuales (3, 4, 5)
- Imágenes PNG/JPG de gráficos
- JSON opcional con indicadores

## 🔄 Ciclo de Ejecución

1. **Validación de horario** (06:00-13:00 Lima)
2. **Iteración por activos** configurados
3. **Consulta a IA** (según tipo de bot)
4. **Apertura dual** (Market + Limit)
5. **Reevaluación** cada 10 minutos
6. **Registro en BD** de todas las operaciones

## 📝 Próximos Pasos

1. Implementar `base/base_bot.py` con clase base común
2. Implementar cada `bot_X/main.py`
3. Configurar prompts específicos en `config/prompt_templates.json`
4. Crear tests unitarios por bot
5. Implementar orchestrador para ejecución paralela
