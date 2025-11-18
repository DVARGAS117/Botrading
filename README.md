# 🤖 Botrading - Sistema de Trading Automatizado con IA

> Sistema de trading automatizado con múltiples bots orquestadores, integración MT5 y decisiones impulsadas por IA Gemini

[![Tests](https://img.shields.io/badge/tests-711%20passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.13+-blue)]()
[![License](https://img.shields.io/badge/license-Private-red)]()

---

## 📋 Estado del Proyecto

**Fase Actual:** Fase 0 - Fundamentos  
**Último Ticket Completado:** T52 - Operación demo antes de real ✅  
**Fecha:** 7 de Noviembre de 2025

---

## 🎯 Visión General

Botrading es un sistema de trading automatizado que:

- 🔄 **Orquesta múltiples bots** independientes con ciclos a inicio de hora
- 💱 **Integra MetaTrader 5** para datos OHLCV, consulta de posiciones y gestión de órdenes
- 🧠 **Utiliza IA Gemini** para tomar decisiones de entrada, reevaluación y gestión de riesgo
  - ✅ **Soporte dual**: Vertex AI (Google Cloud) y Google AI Studio
  - ✅ **Configurable**: Cambia entre APIs sin modificar código
  - ✅ **Recomendado**: Vertex AI para producción, Google AI Studio para desarrollo
- 📊 **Compara metodologías** mediante pares simultáneos Market/Limit
- 💾 **Persiste datos** con SQLite para trazabilidad y análisis
- ⚙️ **Configurable vía JSON** sin tocar código

---

## 📁 Estructura del Proyecto

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
│   ├── bots/                     # Instancias de bots
│   │   ├── bot_1.py              # 🔜 Bot numérico
│   │   ├── bot_2.py              # 🔜 Bot visual
│   │   └── orchestrator.py       # 🔜 Orquestador
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
- API Key de Gemini

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

---

## 🛠️ Tecnologías

- **Python 3.13** - Lenguaje principal
- **pytest** - Framework de testing
- **cryptography** - Encriptación de credenciales (Fernet/AES-128)
- **pydantic** - Validación de datos
- **python-dotenv** - Variables de entorno
- **MetaTrader 5** - Plataforma de trading (próximamente)
- **Google Gemini AI** - IA para decisiones (próximamente)
- **SQLite** - Base de datos (próximamente)

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

### Fase 1: Núcleo (Próximamente)
- [ ] Orquestación de bots
- [ ] Integración MT5
- [ ] Magic Numbers
- [ ] Multi-activo

### Fase 2: IA y Estrategias (Futuro)
- [ ] Integración Gemini
- [ ] Dual Market/Limit
- [ ] Reevaluación
- [ ] Indicadores

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
| Tickets Completados | 12 |
| Tests | 711 |
| Cobertura | 87% |
| Líneas de Código | ~4,700 |

---

**Última actualización:** 7 de Noviembre de 2025  
**Versión:** 0.1.0  
**Estado:** 🚀 En desarrollo activo
