# 📍 MAPA DE UBICACIÓN DE LOS 5 BOTS

## 🗂️ **ESTRUCTURA ACTUAL DEL PROYECTO**

```
BOTRADING/
│
├── config/                          # ⚙️ Configuraciones
│   ├── credentials.json             # ✅ TUS CREDENCIALES (MT5 + Gemini)
│   ├── settings.json                # ✅ Configuración general
│   ├── schedule.json                # ✅ Horarios de trading
│   ├── demo_mode.json               # ✅ Modo demo activado
│   ├── filters.json                 # ✅ Filtros configurables
│   └── prompt_templates.json        # 📝 Templates de prompts por bot
│
├── src/                             # 📦 Código fuente
│   │
│   ├── core/                        # 🔧 Módulos reutilizables (CORE)
│   │   ├── bot_instance.py          # ✅ Clase base para instancias
│   │   ├── mt5_connector.py         # ✅ Conexión a MT5
│   │   ├── config_loader.py         # ✅ Cargador de configs
│   │   ├── credential_manager.py    # ✅ Gestor de credenciales
│   │   ├── logger.py                # ✅ Sistema de logging
│   │   ├── time_validator.py        # ✅ Validación de horarios
│   │   ├── ai_response_parser.py    # ✅ Parser respuestas IA
│   │   ├── prompt_builder.py        # ✅ Constructor de prompts
│   │   ├── filter_manager.py        # ✅ Gestor de filtros
│   │   └── ... (30+ módulos más)
│   │
│   ├── bots/                        # 🤖 LOS 5 BOTS (AQUÍ ESTÁN)
│   │   │
│   │   ├── README.md                # 📖 Documentación de bots
│   │   ├── __init__.py              # Inicializador del paquete
│   │   │
│   │   ├── base/                    # 📐 Clases base compartidas
│   │   │   └── __init__.py          # BaseBot y BaseStrategy
│   │   │
│   │   ├── bot_1/                   # 🤖 BOT 1: NUMÉRICO BASELINE
│   │   │   ├── __init__.py          # Info del bot
│   │   │   ├── main.py              # 🔜 Punto de entrada (CREAR)
│   │   │   ├── config.py            # 🔜 Config específica (CREAR)
│   │   │   └── strategy.py          # 🔜 Lógica de estrategia (CREAR)
│   │   │
│   │   ├── bot_2/                   # 🤖 BOT 2: NUMÉRICO ALTERNATIVO
│   │   │   ├── __init__.py          # Info del bot
│   │   │   ├── main.py              # 🔜 Punto de entrada (CREAR)
│   │   │   ├── config.py            # 🔜 Config específica (CREAR)
│   │   │   └── strategy.py          # 🔜 Lógica de estrategia (CREAR)
│   │   │
│   │   ├── bot_3/                   # 🤖 BOT 3: VISUAL COMPLETO
│   │   │   ├── __init__.py          # Info del bot
│   │   │   ├── main.py              # 🔜 Punto de entrada (CREAR)
│   │   │   ├── config.py            # 🔜 Config específica (CREAR)
│   │   │   ├── strategy.py          # 🔜 Lógica de estrategia (CREAR)
│   │   │   └── chart_analyzer.py    # 🔜 Análisis de gráficos (CREAR)
│   │   │
│   │   ├── bot_4/                   # 🤖 BOT 4: HÍBRIDO
│   │   │   ├── __init__.py          # Info del bot
│   │   │   ├── main.py              # 🔜 Punto de entrada (CREAR)
│   │   │   ├── config.py            # 🔜 Config específica (CREAR)
│   │   │   └── hybrid_strategy.py   # 🔜 Estrategia híbrida (CREAR)
│   │   │
│   │   ├── bot_5/                   # 🤖 BOT 5: VISUAL SEPARADO
│   │   │   ├── __init__.py          # Info del bot
│   │   │   ├── main.py              # 🔜 Punto de entrada (CREAR)
│   │   │   ├── config.py            # 🔜 Config específica (CREAR)
│   │   │   └── visual_strategy.py   # 🔜 Estrategia visual (CREAR)
│   │   │
│   │   └── orchestrator.py          # 🎭 Orquestador (ejecuta todos)
│   │
│   ├── analytics/                   # 📊 Análisis y métricas
│   │   └── methodology_comparator.py
│   │
│   └── db/                          # 💾 Base de datos (CREAR)
│       ├── models.py                # 🔜 Modelos SQLAlchemy
│       └── repositories.py          # 🔜 Repositorios de datos
│
├── tests/                           # 🧪 Tests
│   ├── unit/                        # Tests unitarios
│   └── integration/                 # Tests de integración
│
├── logs/                            # 📝 Logs del sistema
│   └── bot_X.log                    # Log por cada bot
│
└── data/                            # 💾 Datos persistentes
    ├── examples/                    # Ejemplos
    └── reevaluations/              # Datos de reevaluaciones
```

---

## 📍 **UBICACIÓN EXACTA DE CADA BOT:**

### **🤖 BOT 1: Numérico Baseline**
```
📁 Ubicación: src/bots/bot_1/
├── __init__.py          ✅ Creado (info del bot)
├── main.py              ❌ Pendiente (ejecutar bot)
├── config.py            ❌ Pendiente (configuración)
└── strategy.py          ❌ Pendiente (lógica trading)
```

### **🤖 BOT 2: Numérico Alternativo**
```
📁 Ubicación: src/bots/bot_2/
├── __init__.py          ✅ Creado (info del bot)
├── main.py              ❌ Pendiente (ejecutar bot)
├── config.py            ❌ Pendiente (configuración)
└── strategy.py          ❌ Pendiente (lógica trading)
```

### **🤖 BOT 3: Visual Completo**
```
📁 Ubicación: src/bots/bot_3/
├── __init__.py          ✅ Creado (info del bot)
├── main.py              ❌ Pendiente (ejecutar bot)
├── config.py            ❌ Pendiente (configuración)
├── strategy.py          ❌ Pendiente (lógica trading)
└── chart_analyzer.py    ❌ Pendiente (análisis visual)
```

### **🤖 BOT 4: Híbrido**
```
📁 Ubicación: src/bots/bot_4/
├── __init__.py          ✅ Creado (info del bot)
├── main.py              ❌ Pendiente (ejecutar bot)
├── config.py            ❌ Pendiente (configuración)
└── hybrid_strategy.py   ❌ Pendiente (estrategia híbrida)
```

### **🤖 BOT 5: Visual Separado**
```
📁 Ubicación: src/bots/bot_5/
├── __init__.py          ✅ Creado (info del bot)
├── main.py              ❌ Pendiente (ejecutar bot)
├── config.py            ❌ Pendiente (configuración)
└── visual_strategy.py   ❌ Pendiente (estrategia visual)
```

---

## 🚀 **CÓMO EJECUTAR CADA BOT (Una vez implementado):**

```bash
# Ejecutar Bot 1 individualmente
python -m src.bots.bot_1.main

# Ejecutar Bot 2 individualmente
python -m src.bots.bot_2.main

# Ejecutar Bot 3 individualmente
python -m src.bots.bot_3.main

# Ejecutar Bot 4 individualmente
python -m src.bots.bot_4.main

# Ejecutar Bot 5 individualmente
python -m src.bots.bot_5.main

# Ejecutar TODOS los bots al mismo tiempo
python -m src.bots.orchestrator
```

---

## 📊 **RESUMEN DE LOS 5 BOTS:**

| Bot | Tipo | Ubicación | Datos | Prompts |
|-----|------|-----------|-------|---------|
| **Bot 1** | Numérico | `src/bots/bot_1/` | Indicadores numéricos | `numerico_evaluacion` |
| **Bot 2** | Numérico Alt | `src/bots/bot_2/` | Indicadores numéricos | `numerico_evaluacion` (custom) |
| **Bot 3** | Visual | `src/bots/bot_3/` | Imágenes + indicadores | `visual_evaluacion` |
| **Bot 4** | Híbrido | `src/bots/bot_4/` | Imagen (apertura) + Numérico (reeval) | `hibrido_evaluacion` |
| **Bot 5** | Visual/Num | `src/bots/bot_5/` | Imágenes limpias + JSON | `hibrido_evaluacion` |

---

## ✅ **ESTADO ACTUAL:**

- ✅ **Carpetas creadas** para los 5 bots
- ✅ **Archivos `__init__.py`** con información de cada bot
- ✅ **Clase base `BaseBot`** en `src/bots/base/`
- ✅ **README.md** con documentación
- ❌ **Archivos `main.py`** pendientes (próximo paso)
- ❌ **Archivos `config.py`** pendientes
- ❌ **Archivos `strategy.py`** pendientes

---

## 🎯 **PRÓXIMOS PASOS:**

1. **Implementar `main.py`** para Bot 1 (empezar con el más simple)
2. **Implementar `strategy.py`** para Bot 1
3. **Probar Bot 1** en modo demo
4. **Replicar** la estructura para Bots 2-5
5. **Implementar `orchestrator.py`** para ejecutar todos

---

## 📝 **NOTAS IMPORTANTES:**

- Cada bot es **independiente** y puede ejecutarse por separado
- Todos los bots usan los **mismos módulos core** (`src/core/`)
- La configuración de cada bot está en `config/` con su ID
- Los logs se guardan en `logs/bot_X.log`
- Todos usan **estrategia dual** (Market + Limit)

---

**Fecha de creación:** 17 de noviembre de 2025  
**Estado:** Estructura base creada ✅  
**Próximo paso:** Implementar Bot 1
