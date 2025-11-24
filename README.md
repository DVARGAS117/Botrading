# 🤖 Botrading - Sistema de Trading Automatizado con IA

> Sistema de trading automatizado con múltiples bots orquestadores, integración MT5 y decisiones impulsadas por IA vía Vertex AI (Gemini)

[![Tests](https://img.shields.io/badge/tests-711%20passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.13+-blue)]()
[![License](https://img.shields.io/badge/license-Private-red)]()

---

## 📋 Estado del Proyecto

**Fase Actual:** Fase 0 - Fundamentos  
**Último Ticket Completado:** T53 - Persistencia ticket MT5 y cierre determinístico ✅  
**Fecha:** 24 de Noviembre de 2025

---

## 🎯 Visión General

Botrading es un sistema de trading automatizado que:

- 🔄 **Orquesta múltiples bots** independientes con ciclos a inicio de hora
- 💱 **Integra MetaTrader 5** para datos OHLCV, consulta de posiciones y gestión de órdenes
-- 🧠 **IA Gemini vía Vertex AI (producción) con fallback opcional Google AI Studio**
   - Modelo forzado por defecto: `gemini-3-pro-preview` (override con `ALLOW_CUSTOM_GEMINI_MODEL=1`)
   - Fallback opcional: activar `ALLOW_GEMINI_FALLBACK=1` (requiere `GEMINI_API_KEY`)
   - Soporte dual: Vertex AI (Google Cloud) y Gemini API Studio (desarrollo)
   - Configurable sin cambiar código (variables de entorno)
- 📊 **Compara metodologías** mediante pares simultáneos Market/Limit
- 💾 **Persiste datos** con SQLite para trazabilidad y análisis
- ⚙️ **Configurable vía JSON** sin tocar código

---

## 📁 Estructura del Proyecto (Estado Actual Parcial)

```
BOTRADING/
├── src/                          # Código fuente
│   ├── core/                     # Módulos reutilizables
│   │   ├── core_module.py        # ✅ Clase base módulos core
│   │   ├── config_loader.py      # ✅ Gestión de configuración
│   │   ├── credential_manager.py # ✅ Gestión segura credenciales
│   │   ├── logger.py             # ✅ Sistema de logging
│   │   ├── time_validator.py     # ✅ Validación horarios Lima
│   │   ├── candle_waiter.py      # ✅ Espera cierre de vela
│   │   ├── quota_validator.py    # ✅ Validación cuota IA
│   │   ├── ia_config_manager.py  # ✅ Alternancia config IA por bot
│   │   ├── ai_response_parser.py # ✅ Parsing y validación respuestas IA
│   │   ├── filter_manager.py     # ✅ Gestión de filtros configurables
│   │   ├── demo_mode_validator.py # ✅ Validación demo antes de real
│   │   ├── mt5_connector.py      # 🔜 Conexión MT5
│   │   ├── ia_agent.py           # 🔜 Agente IA Gemini
│   │   └── risk_manager.py       # 🔜 Gestión de riesgo
│   ├── bots/                     # Bots de trading
│   │   ├── base/                 # Lógica base compartida (Vertex integrado)
│   │   │   └── base_bot_operations.py  # Clase base usa VertexAIClient
│   │   ├── bot_1/                # Bot 1 numérico (estrategia activa)
│   │   │   ├── strategy.py       # Estrategia basada en VWAP (usa flujo Vertex vía base)
│   │   │   ├── config.py         # Config específica Bot1
│   │   │   └── main.py           # Entrada específica (WIP)
│   │   ├── bot_2/..bot_5/        # (Pendiente) Próximos bots aún no implementados
│   │   └── orchestrator/         # (Pendiente) Orquestador multi-bot
│   └── db/                       # Base de datos
│       ├── models.py             # 🔜 Modelos SQLAlchemy
│       └── queries.py            # 🔜 Consultas
├── config/                       # Archivos de configuración
│   ├── settings.example.json     # Configuración general
│   ├── credentials.example.json  # Credenciales
│   ├── schedule.example.json     # ✅ Horarios de trading
│   ├── candle_wait.example.json  # ✅ Config espera de velas
│   ├── quota_validation.example.json # ✅ Config validación cuota IA
│   ├── ia_profiles.example.json  # ✅ Perfiles IA alternantes
│   ├── ai_response_schema.example.json # ✅ Schema validación respuestas IA
│   ├── filters.example.json      # ✅ Config filtros de volatilidad/spread
│   ├── demo_mode.example.json    # ✅ Config validación demo antes de real
│   └── ia_config.example.json    # Configuración IA
├── tests/                        # Tests
│   ├── unit/                     # Tests unitarios
│   │   ├── test_core_module.py   # ✅ Tests clase base
│   │   ├── test_config_loader.py # ✅ Tests configuración
│   │   ├── test_credential_manager.py # ✅ Tests credenciales
│   │   ├── test_logger.py        # ✅ Tests logging
│   │   ├── test_time_validator.py # ✅ Tests validador tiempo
│   │   ├── test_candle_waiter.py # ✅ Tests espera de velas
│   │   ├── test_quota_validator.py # ✅ Tests validación cuota IA
│   │   ├── test_ia_config_manager.py # ✅ Tests config IA alternante
│   │   ├── test_ai_response_parser.py # ✅ Tests parsing respuestas IA
│   │   └── test_filter_manager.py # ✅ Tests filtros configurables
│   │   └── test_demo_mode_validator.py # ✅ Tests validación demo
│   ├── integration/              # ✅ Tests de integración
│   │   └── test_core_integration.py # ✅ Tests integración
│   └── e2e/                      # 🔜 Tests end-to-end
├── context/                      # Documentación
│   ├── DOCUMENTACION/            # Documentación técnica
│   │   ├── T45_reusabilidad_modulos_core.md  # ✅ Doc arquitectura
│   │   ├── T46_tests_unitarios_por_componente.md  # ✅ Doc testing
│   │   ├── T47_almacenamiento_seguro_credenciales.md  # ✅ Doc seguridad
│   │   ├── T44_config_loader.md  # ✅ Doc config_loader
│   │   ├── T39_logger.md         # ✅ Doc logger
│   │   ├── T35_validacion_hora_lima.md  # ✅ Doc validador tiempo
│   │   ├── T37_espera_cierre_vela.md  # ✅ Doc espera de velas
│   │   ├── T48_validacion_cuota_ia.md  # ✅ Doc validación cuota IA
│   │   ├── T49_config_alternante_ia.md  # ✅ Doc config IA alternante
│   │   └── T36_filtros_configurables.md  # ✅ Doc filtros configurables
│   │   └── T52_operacion_demo_antes_real.md  # ✅ Doc validación demo
│   ├── FORMATO_RESPUESTAS_IA.md  # ✅ Formato respuestas IA validadas
│   ├── agents.md                 # Reglas del agente
│   ├── RESUMEN_EJECUTIVO.md      # Resumen del proyecto
│   └── TICKETS_LIST.md           # Lista de tickets
├── .gitignore                    # Exclusiones Git
├── .env.example                  # Variables de entorno
├── requirements.txt              # Dependencias Python
├── pytest.ini                    # Configuración pytest
└── README.md                     # Este archivo
```

---

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.13 o superior
- Git
- Cuenta MT5 (demo o real)
- API Key de Vertex (Google Cloud) o alternativa Gemini API Studio
 API Key de Vertex (Google Cloud) obligatoria (`GOOGLE_API_KEY`). Fallback opcional Gemini API Studio (`GEMINI_API_KEY`) sólo si activas `ALLOW_GEMINI_FALLBACK=1`. Modelo por defecto: `gemini-3-pro-preview` (override con `ALLOW_CUSTOM_GEMINI_MODEL=1`).

### Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/DVARGAS117/Botrading.git
cd Botrading
```

2. **Crear entorno virtual:**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar credenciales:**
```bash
# Copiar archivos de ejemplo
cp config/settings.example.json config/settings.json
cp config/credentials.example.json config/credentials.json
cp config/schedule.example.json config/schedule.json
cp config/candle_wait.example.json config/candle_wait.json
cp config/quota_validation.example.json config/quota_validation.json
cp config/ia_profiles.example.json config/ia_profiles.json
cp config/ai_response_schema.example.json config/ai_response_schema.json
cp config/filters.example.json config/filters.json
cp config/ia_config.example.json config/ia_config.json
cp .env.example .env

# Editar con tus credenciales reales
notepad config/credentials.json
notepad config/schedule.json
notepad config/candle_wait.json
notepad config/quota_validation.json
notepad config/ia_profiles.json
notepad config/filters.json
notepad .env
```

5. **Ejecutar tests:**
```bash
pytest tests/ -v --cov=src
```

### 🧠 Migración a gemini-3-pro-preview

Cambios principales:
- Límites ampliados: Vertex `max_tokens=5120`, SDK `max_tokens=10240`
- Timeout extendido: 120s
- Cálculo de costos integrado (SDK y Vertex)
- Parser REST robusto y logging de respuesta cruda + decisión
- Prompt VWAP enriquecido (pendiente, bandas, EMAs) para tests
- Horario Bot1 ajustado (09:00–13:00 Lima)

#### 💲 Precios gemini-3-pro-preview (por 1M tokens)
| Nivel de Contexto | Input | Output |
| ------------------ | ----- | ------ |
| Estándar (≤ 128k)  | $2.00 | $12.00 |
| Largo (> 128k)     | $4.00 | $18.00 |

Conversión interna (por 1K tokens): estándar (0.002 / 0.012) · largo (0.004 / 0.018). Umbral largo: 128,000 tokens de entrada. Overrides: `G3_STD_INPUT_PER_1K`, `G3_STD_OUTPUT_PER_1K`.

Archivo adicional sugerido: `docs/GEMINI_PRICING.md` (detalles y futuras extensiones).
### 🗄️ Persistencia de Costos por Consulta (T33 Integrado)

Cada consulta a la IA se persiste automáticamente en SQLite (`data/ia_queries.db`) mediante `IAQueryRepository` con:

Campos principales:
- `bot_id`, `ia_id`, `symbol`, `tipo_consulta`
- `prompt`, `respuesta`
- `tokens_input`, `tokens_output`, `tokens_total`
- `costo_usd` (tarifa estándar vs largo contexto detectada dinámicamente)
- `accion_decidida`, `created_at`

Lógica:
- El cálculo de costo se realiza en `GeminiClient` y `VertexAIClient` aplicando el umbral de 128k tokens de entrada.
- Después de parsear la respuesta se registra la acción decidida normalizada (OPERAR / NO_OPERAR / CERRAR / ACTUALIZAR / MANTENER).
- Modo `--save-prompts` evita consumo de tokens; en ese modo no se persiste costo real.

Consultas futuras:
- Consolidación diaria en `DailyMetricsRepository` (ya suma `costo_ia_total`).
- Próximas extensiones: alertas de presupuesto, agregaciones por símbolo, dashboard mensual.

Test asociado: `test_ia_query_persistence.py` verifica almacenamiento de tokens y costo por consulta.

---

## ✅ Tickets Completados

### Fase 0: Fundamentos

| # | Ticket | Estado | Cobertura |
|---|--------|--------|-----------|
| T44 | Gestión de credenciales y parámetros en JSON | ✅ | 98% |
| T39 | Logging por bot y nivel | ✅ | 85% |
| T45 | Reutilización de módulos core | ✅ | 98% |
| T46 | Tests unitarios por componente | ✅ | 93% |
| T47 | Almacenamiento seguro de credenciales | ✅ | 86% |
| T35 | Validación de hora local de Lima y días hábiles | ✅ | 100% |
| T37 | Espera por cierre de vela antes de extraer datos | ✅ | 90% |
| T48 | Validación de cuota y disponibilidad de modelo IA | ✅ | 87% |
| T49 | Alternancia de configuraciones de IA por bot | ✅ | 91% |
| T40 | Registro de errores de parsing de respuestas IA | ✅ | 87% |
| T36 | Activación de filtros vía configuración | ✅ | 86% |
| T52 | Operación demo antes de real | ✅ | 88% |
| T53 | Persistencia ticket MT5 y cierre determinístico | ✅ | 84% |

---

## 🧪 Testing

### Ejecutar todos los tests
```bash
pytest tests/ -v
```

### Ejecutar tests con cobertura
```bash
pytest tests/ -v --cov=src --cov-report=html
```

### Ver reporte de cobertura
```bash
# Abre: htmlcov/index.html
```

### Ejecutar tests específicos
```bash
pytest tests/unit/test_config_loader.py -v
```

---

## 📖 Documentación

- **[Resumen Ejecutivo](context/RESUMEN_EJECUTIVO.md)** - Visión general del proyecto
- **[Lista de Tickets](context/TICKETS_LIST.md)** - 52 tickets en 16 épicas
- **[Reglas del Agente](context/agents.md)** - Metodología TDD y estándares
- **[T47 - Credential Manager](context/DOCUMENTACION/T47_almacenamiento_seguro_credenciales.md)** - Almacenamiento seguro
- **[T46 - Testing Infrastructure](context/DOCUMENTACION/T46_tests_unitarios_por_componente.md)** - Infraestructura de testing
- **[T45 - Arquitectura Core](context/DOCUMENTACION/T45_reusabilidad_modulos_core.md)** - Patrones de reutilización
- **[T44 - Config Loader](context/DOCUMENTACION/T44_config_loader.md)** - Gestión de configuración
- **[T39 - Logger](context/DOCUMENTACION/T39_logger.md)** - Sistema de logging
- **[T35 - Time Validator](context/DOCUMENTACION/T35_validacion_hora_lima.md)** - Validación de horarios
- **[T37 - Candle Waiter](context/DOCUMENTACION/T37_espera_cierre_vela.md)** - Espera de cierre de velas
- **[T48 - Quota Validator](context/DOCUMENTACION/T48_validacion_cuota_ia.md)** - Validación de cuota IA
- **[T49 - IA Config Manager](context/DOCUMENTACION/T49_config_alternante_ia.md)** - Alternancia de configuraciones IA
- **[T36 - Filter Manager](context/DOCUMENTACION/T36_filtros_configurables.md)** - Filtros configurables
- **[T52 - Demo Mode Validator](context/DOCUMENTACION/T52_operacion_demo_antes_real.md)** - Validación demo antes de real
- **[Formato Respuestas IA](context/FORMATO_RESPUESTAS_IA.md)** - Formato JSON para prompts IA
- **[T53 - Persistencia Ticket MT5](context/DOCUMENTACION/T53_persistencia_ticket_mt5_cierre_deterministico.md)** - Ticket real y cierre confiable

---

## 🛠️ Tecnologías

- **Python 3.13** - Lenguaje principal
- **pytest** - Framework de testing
- **cryptography** - Encriptación de credenciales (Fernet/AES-128)
- **pydantic** - Validación de datos
- **python-dotenv** - Variables de entorno
- **MetaTrader 5** - Plataforma de trading (próximamente)
- **Google Vertex AI (Gemini)** - IA para decisiones (oficial)
- **SQLite** - Base de datos (operaciones, consultas IA, tickets MT5)

---

## 🔒 Seguridad

- ✅ Encriptación AES-128 para credenciales (Fernet)
- ✅ Credenciales nunca en código fuente
- ✅ Archivos sensibles en `.gitignore`
- ✅ Logging seguro sin exponer secretos
- ✅ Variables de entorno para claves de encriptación
- ✅ Permisos restrictivos en archivos (Unix 0o600)
- ✅ Archivos `.example` para documentación

**Archivos a NO commitear:**
- `config/credentials.enc` (encriptado, pero mejor excluir)
- `config/credentials.json` (texto plano, NUNCA commitear)
- `config/settings.json`
- `config/encryption_key.txt`
- `.env`
- `*.log`
- `*.db`

---

## 📊 Estado de Desarrollo

### Fase 0: Fundamentos (En Progreso)
- [x] T44 - Gestión de credenciales
- [x] T39 - Sistema de logging
- [x] T45 - Módulos core reutilizables
- [x] T46 - Tests unitarios
- [x] T47 - Almacenamiento seguro
- [x] T35 - Validación horarios
- [x] T35 - Validación horarios
- [x] T37 - Espera cierre de vela
- [x] T48 - Validación cuota IA
- [x] T49 - Alternancia configuración IA
- [x] T40 - Registro errores parsing IA
- [x] T36 - Filtros vía configuración
- [x] T52 - Operación demo antes de real

### Fase 1: Núcleo (En Progreso)
- [x] Integración parcial MT5 (apertura/actualización/cierre posiciones)
- [x] Persistencia ticket MT5 (T53)
- [x] Cache magic_number activo por símbolo
- [ ] Orquestación de bots
- [ ] Multi-activo

### Fase 2: IA y Estrategias (Futuro)
- [x] Integración Vertex (REST) en clase base bots (en producción)
- [ ] Fallback Gemini consolidado (variable `ALLOW_GEMINI_FALLBACK` documentada, pendiente pruebas multi-bot)
- [ ] Dual Market/Limit
- [ ] Reevaluación
- [ ] Indicadores

### Estado Migración Vertex
| Componente | Estado | Detalle |
|------------|--------|---------|
| Cliente REST bajo nivel | ✅ | `generate_vertex_response` estable |
| Cliente alto nivel Vertex | ✅ | `VertexAIClient` (modelo forzado) |
| BaseBotOperations | ✅ | Migrado a Vertex, fallback opcional |
| Bot1 (numérico) | ✅ | Ejecuta vía Vertex (estrategia lista) |
| Bot2-Bot5 | ⏳ | No implementados aún |
| Orquestador multi-bot | ⏳ | Pendiente de diseño |
| Métricas de coste Vertex | ⏳ | Por definir (sin cálculo actual) |
| Documentación de fallback | ✅ | README y guía Vertex actualizados |

Nota: Actualmente sólo Bot1 está disponible; cualquier referencia a ejecución multi-bot es futura. Ticket T53 agrega robustez al cierre sin requerir ticket en respuesta IA.

---

## 🔁 Scripts Operativos Nuevos (Post T53)

Estos scripts ayudan a inspeccionar y sanear posiciones reales cuando se ejecutan pruebas o ciclos manuales:

| Script | Propósito | Uso Rápido |
|--------|-----------|------------|
| `scripts/list_open_positions.py` | Listar todas las posiciones abiertas en MT5 con ticket y magic v2 | `python scripts/list_open_positions.py` |
| `scripts/close_residual_positions.py` | Cerrar posiciones intraday residuales por símbolo o todas | `python scripts/close_residual_positions.py --symbol BTCUSD` |

Ejemplo en PowerShell:
```powershell
python scripts/list_open_positions.py
python scripts/close_residual_positions.py --symbol BTCUSD
```

Ambos scripts dependen de una conexión MT5 activa y credenciales correctas. Úsalos después de pruebas que abortan antes del cierre normal.

---

## 🔐 Persistencia del Ticket MT5 (T53)

Antes de T53 el cierre dependía de heurísticas (búsqueda por símbolo y magic_number) porque la IA no proveía el campo `ticket`. Ahora:

1. `operations_repository` almacena columna `ticket` e índice `idx_ticket`.
2. Estrategias intraday guardan el `position.ticket` al abrir y recuperan por `get_operation_by_ticket` en actualización/cierre.
3. Fallback seguro: cache `_active_magic_by_symbol` para escenarios donde no se pudo guardar ticket (compatibilidad retro).
4. Comportamiento en cuentas Netting: Dos aperturas mismas condiciones pueden compartir ticket; segundo update puede devolver retcode de “No changes” (`10025`) que ahora se considera benigno.

Beneficios: Cierre determinístico, reducción de ambigüedad multi-posición y trazabilidad exacta entre MT5 y SQLite.

---

---

## 🤝 Contribución

### Flujo de Trabajo

1. **Crear rama desde `desarrollo`:**
```bash
git checkout desarrollo
git pull origin desarrollo
git checkout -b feature/TXX-nombre-ticket
```

2. **Desarrollo con TDD:**
   - Escribir tests primero
   - Implementar código
   - Asegurar > 90% cobertura

3. **Commit y Push:**
```bash
git add .
git commit -m "feat: implementar TXX - Nombre del ticket"
git push origin feature/TXX-nombre-ticket
```

4. **Pull Request:**
   - Crear PR a `desarrollo`
   - Esperar revisión
   - Merge después de aprobación

### Estándares de Código

- ✅ TDD obligatorio
- ✅ Cobertura de tests > 90%
- ✅ PEP 8 para estilo
- ✅ Type hints en funciones
- ✅ Docstrings en módulos y clases
- ✅ Documentación en `context/DOCUMENTACION/`

---

## 📞 Enlaces

- **Repositorio:** https://github.com/DVARGAS117/Botrading
- **Proyecto GitHub:** https://github.com/users/DVARGAS117/projects/2
- **Issues:** https://github.com/DVARGAS117/Botrading/issues

---

## 📄 Licencia

Este proyecto es privado. Todos los derechos reservados.

---

## 📈 Estadísticas

| Métrica | Valor |
|---------|-------|
| Tickets Totales | 52 |
| Épicas | 16 |
| Tickets Completados | 20+ |
| Tests | 1303+ |
| Cobertura | 87% (ver htmlcov) |
| Líneas de Código | ~8,000 |
| Bots Activos | 1 (INTRADAY Bot 1) |

---

**Última actualización:** 20 de noviembre de 2025  
**Versión:** 1.0.0  
**Estado:** ✅ Bot INTRADAY en producción
