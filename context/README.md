# 🤖 Botrading - Sistema de Trading Automatizado con IA

> **Sistema de trading automatizado con múltiples bots orquestadores, integración MT5 y decisiones impulsadas por IA Gemini**

## 📋 Estado del Proyecto

**Creado:** 5 de Noviembre de 2025  
**Tickets:** 52 creados ✅  
**Épicas:** 16 creadas ✅  
**Repository:** https://github.com/DVARGAS117/Botrading  
**Project Board:** https://github.com/users/DVARGAS117/projects/2

---

## 🎯 Resumen Ejecutivo

Este proyecto implementa un **sistema de trading automatizado** que:

- 🔄 **Orquesta múltiples bots** independientes con ciclos a inicio de hora
- 💱 **Integra MetaTrader 5** para datos OHLCV, consulta de posiciones y gestión de órdenes
- 🧠 **Utiliza IA Gemini** para tomar decisiones de entrada, reevaluación y gestión de riesgo
- 📊 **Compara metodologías** mediante pares simultáneos Market/Limit
- 💾 **Persiste datos** con SQLite para trazabilidad y análisis
- ⚙️ **Configurable vía JSON** sin tocar código

---

## 📊 Estructura de Épicas (16 épicas)

### **Fase 0: Fundamentos** (Crítica - Sin esto no se puede avanzar)

| Épica | Descripción | Tickets |
|-------|-------------|---------|
| 🔐 **Seguridad y cuentas** | Gestión de credenciales y validación de cuotas | 3 |
| 📋 **Configuración y modularidad** | Arquitetura modular y tests unitarios | 3 |
| 🕐 **Filtros y horarios** | Validación de horarios (06:00-13:00 Lima) | 3 |

**→ Entrega Fase 0:** Estructura, configuración, seguridad

---

### **Fase 1: Núcleo de Ejecución** (P0)

| Épica | Descripción | Tickets |
|-------|-------------|---------|
| 🤖 **Orquestación** | Ciclos de bot, instancias independientes | 5 |
| 🔗 **Integración MT5** | Datos OHLCV, posiciones, órdenes | 4 |
| 🎫 **Magic Numbers** | Generación y decodificación [Bot][IA][Tipo] | 3 |
| 🌐 **Multi-activo** | Administración de lista de activos | 3 |
| ⚠️ **Errores y logging** | Reintentos, logs estructurados | 3 |

**→ Entrega Fase 1:** Bot 1 operacional en horario regulado

---

### **Fase 2: IA y Estrategias** (P0/P1)

| Épica | Descripción | Tickets |
|-------|-------------|---------|
| 🧠 **IA (Gemini)** | Prompts, JSON, tokens, contexto | 4 |
| 👯 **Dual Market/Limit** | Pares simultáneos, comparación | 3 |
| 📈 **Indicadores e imágenes** | EMA, RSI, MACD, visualización | 3 |
| 🔄 **Reevaluación** | Ciclos de 10 min, decisiones | 3 |
| 💰 **Riesgo y conversión** | Cálculo de lote por % riesgo | 3 |

**→ Entrega Fase 2:** Bot 1 con IA y Dual Market/Limit en demo

---

### **Fase 3: Análisis y Persistencia** (P0)

| Épica | Descripción | Tickets |
|-------|-------------|---------|
| 💾 **Persistencia** | SQLite, operaciones, consultas IA, métricas | 3 |
| 📊 **Métricas y monitoreo** | Dashboard, comparación de metodologías | 3 |

**→ Entrega Fase 3:** Dashboard operacional, análisis histórico

---

### **Fase 4: Escalabilidad y Calidad** (P0)

| Épica | Descripción | Tickets |
|-------|-------------|---------|
| ✅ **Roadmap y calidad** | E2E tests, demo vs. real, documentación | 3 |

**→ Entrega Fase 4:** Bots 2-5 operacionales, producción

---

## 📌 Tickets por Prioridad

### **P0 - Crítica (34 tickets)**
Funcionalidad esencial del sistema.

### **P1 - Alta (18 tickets)**
Mejoras y optimizaciones importantes.

---

## 🗂️ Distribución de Trabajo

### Por Fase
- **Fase 0:** 9 tickets (Fundamentos)
- **Fase 1:** 18 tickets (Núcleo)
- **Fase 2:** 16 tickets (IA/Estrategias)
- **Fase 3:** 6 tickets (Análisis)
- **Fase 4:** 3 tickets (Calidad/Escalabilidad)

### Por Épica (Top 5)
1. **IA (Gemini):** 4 tickets
2. **Orquestación:** 5 tickets
3. **Integración MT5:** 4 tickets
4. **Persistencia:** 3 tickets
5. **Configuración y modularidad:** 3 tickets

---

## 🚀 Cómo Usar Este Repositorio

### 1️⃣ Ver Issues Creados
```bash
# Todos los issues
https://github.com/DVARGAS117/Botrading/issues

# Filtrar por etiqueta
- https://github.com/DVARGAS117/Botrading/issues?labels=phase-1
- https://github.com/DVARGAS117/Botrading/issues?labels=epic
- https://github.com/DVARGAS117/Botrading/issues?labels=P0
```

### 2️⃣ Vincular Issues a GitHub Projects

#### **Opción A: Manualmente desde Web**
1. Ir a https://github.com/users/DVARGAS117/projects/2
2. Click en "+ Add item"
3. Buscar cada issue (#17-#68) y añadirlo
4. Asignar a columnas según estado

#### **Opción B: Script Automatizado (Recomendado)**
```bash
python add_issues_to_project.py
```

Ver instrucciones detalladas en `add_issues_to_project.py`

### 3️⃣ Crear Estructura del Código

```
botrading/
├── config/
│   ├── settings.json           # Parámetros globales
│   ├── assets.json             # Lista de activos
│   ├── filters.json            # Filtros (horario, volatilidad)
│   ├── ia_config.json          # Config de Gemini
│   └── environment.example     # Variables de entorno
├── src/
│   ├── core/                   # Módulos reutilizables
│   │   ├── mt5_connector.py
│   │   ├── ia_agent.py
│   │   ├── risk_manager.py
│   │   ├── logger.py
│   │   └── config_loader.py
│   ├── bots/                   # Instancias de bots
│   │   ├── bot_1.py            # Bot numérico
│   │   ├── bot_2.py            # Bot visual
│   │   └── orchestrator.py
│   └── db/
│       ├── models.py           # SQLAlchemy models
│       ├── migrations/
│       └── queries.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DEPLOYMENT.md
└── README.md
```

---

## 📂 Archivos de Configuración

### `config/settings.json`
```json
{
  "timezone": "America/Lima",
  "trading_window": {
    "start": "06:00",
    "end": "13:00",
    "days": ["MON", "TUE", "WED", "THU", "FRI"]
  },
  "bots": {
    "bot_1": {
      "type": "numeric",
      "instruments": ["EURUSD", "GBPUSD"],
      "timeframes": ["5M", "15M", "1H"]
    }
  }
}
```

### `config/ia_config.json`
```json
{
  "provider": "gemini",
  "model": "gemini-2.5-pro",
  "temperature": 0.7,
  "max_tokens": 2048,
  "timeout": 30,
  "retry_attempts": 3
}
```

---

## 🔐 Variables de Entorno

```bash
# MT5
MT5_ACCOUNT_ID=1234567
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server

# Gemini API
GEMINI_API_KEY=your_api_key

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/botrading.log
```

---

## 📊 Estructura de Base de Datos (SQLite)

### Tablas Principales
- **operations** - Órdenes abiertas/cerradas
- **ia_queries** - Consultas a IA (prompts, respuestas, costos)
- **metrics_daily** - Métricas diarias por bot
- **positions** - Posiciones en tiempo real

---

## 🔄 Flujo de Trabajo Recomendado

### Sprint 1 (Fase 0): Fundamentos
1. ✅ Configurar repo, estructura, tests
2. ✅ Gestión de credenciales
3. ✅ Sistema de logging

### Sprint 2-3 (Fase 1): Núcleo
1. Conectar MT5 (datos OHLCV, posiciones)
2. Orquestador + Bot 1 (numérico o visual)
3. Magic Numbers + Multi-activo

### Sprint 4-5 (Fase 2): IA
1. Integrar Gemini (prompts, JSON)
2. Implementar Dual Market/Limit
3. Reevaluación cada 10 min

### Sprint 6 (Fase 3): Persistencia
1. SQLite schema + migrations
2. Consolidación de métricas diarias

### Sprint 7+ (Fase 4): Demo & Producción
1. E2E tests
2. Operación en demo
3. Escalabilidad a Bots 2-5

---

## 🎯 Criterios de Salida por Fase

### ✅ Fase 0
- [ ] Repo + estructura base
- [ ] Tests unitarios > 80% cobertura
- [ ] Credenciales en .env
- [ ] Logging funcional

### ✅ Fase 1
- [ ] Bot 1 ejecuta ciclos a HH:00
- [ ] MT5 conexión estable
- [ ] Operaciones abiertas/cerradas correctamente
- [ ] Magic Numbers funcionando

### ✅ Fase 2
- [ ] Gemini responde con JSON válido
- [ ] Pares Market/Limit se abren simultáneamente
- [ ] Reevaluación cada 10 min
- [ ] Demo operando sin pérdidas críticas

### ✅ Fase 3
- [ ] SQLite almacena datos sin pérdidas
- [ ] Dashboard con métricas diarias
- [ ] Análisis Market vs Limit

### ✅ Fase 4
- [ ] Bots 2-5 en paralelo
- [ ] Documentación completa
- [ ] Producción

---

## 📖 Documentación

- **TICKETS_DETAILED.md** - Descripción completa de cada ticket
- **ARCHITECTURE.md** - Diseño técnico
- **API_INTEGRATION.md** - MT5 + Gemini APIs
- **DEPLOYMENT.md** - Guía de despliegue

---

## 🤝 Contribuciones

1. Clonar repo
2. Crear rama para el ticket: `git checkout -b T##-descripcion`
3. Implementar + tests
4. Push y crear PR
5. Review + merge

---

## 📞 Contacto

- **Repository:** https://github.com/DVARGAS117/Botrading
- **Project Board:** https://github.com/users/DVARGAS117/projects/2
- **Issues:** https://github.com/DVARGAS117/Botrading/issues

---

## 📄 Licencia

Este proyecto es privado. Todos los derechos reservados.

---

**Última actualización:** 5 de Noviembre de 2025  
**Estado:** 🚀 En planificación y setup inicial
