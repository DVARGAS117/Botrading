# 🤖 Botrading - Sistema de Trading Automatizado con IA

> Sistema de trading automatizado con múltiples bots orquestadores, integración MT5 y decisiones impulsadas por IA Gemini

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-94%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.13+-blue)]()
[![License](https://img.shields.io/badge/license-Private-red)]()

---

## 📋 Estado del Proyecto

**Fase Actual:** Fase 0 - Fundamentos  
**Último Ticket Completado:** T44 - Gestión de credenciales y parámetros en JSON ✅  
**Fecha:** 6 de Noviembre de 2025

---

## 🎯 Visión General

Botrading es un sistema de trading automatizado que:

- 🔄 **Orquesta múltiples bots** independientes con ciclos a inicio de hora
- 💱 **Integra MetaTrader 5** para datos OHLCV, consulta de posiciones y gestión de órdenes
- 🧠 **Utiliza IA Gemini** para tomar decisiones de entrada, reevaluación y gestión de riesgo
- 📊 **Compara metodologías** mediante pares simultáneos Market/Limit
- 💾 **Persiste datos** con SQLite para trazabilidad y análisis
- ⚙️ **Configurable vía JSON** sin tocar código

---

## 📁 Estructura del Proyecto

```
BOTRADING/
├── src/                          # Código fuente
│   ├── core/                     # Módulos reutilizables
│   │   ├── config_loader.py      # ✅ Gestión de configuración
│   │   ├── mt5_connector.py      # 🔜 Conexión MT5
│   │   ├── ia_agent.py           # 🔜 Agente IA Gemini
│   │   ├── risk_manager.py       # 🔜 Gestión de riesgo
│   │   └── logger.py             # 🔜 Sistema de logging
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
│   └── ia_config.example.json    # Configuración IA
├── tests/                        # Tests
│   ├── unit/                     # Tests unitarios
│   │   └── test_config_loader.py # ✅ Tests configuración
│   ├── integration/              # 🔜 Tests de integración
│   └── e2e/                      # 🔜 Tests end-to-end
├── context/                      # Documentación
│   ├── DOCUMENTACION/            # Documentación técnica
│   │   └── T44_config_loader.md  # ✅ Doc config_loader
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
cp config/ia_config.example.json config/ia_config.json
cp .env.example .env

# Editar con tus credenciales reales
notepad config/credentials.json
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
| T44 | Gestión de credenciales y parámetros en JSON | ✅ | 94% |
| T39 | Logging por bot y nivel | ✅ | 85% |
| T45 | Reutilización de módulos core | 🔜 | - |
| T46 | Tests unitarios por componente | 🔜 | - |
| T47 | Almacenamiento seguro de credenciales | 🔜 | - |
| T35 | Validación de hora local de Lima y días hábiles | 🔜 | - |
| T37 | Espera por cierre de vela antes de extraer datos | 🔜 | - |

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
- **[T44 - Config Loader](context/DOCUMENTACION/T44_config_loader.md)** - Documentación técnica

---

## 🛠️ Tecnologías

- **Python 3.13** - Lenguaje principal
- **pytest** - Framework de testing
- **pydantic** - Validación de datos
- **python-dotenv** - Variables de entorno
- **MetaTrader 5** - Plataforma de trading (próximamente)
- **Google Gemini AI** - IA para decisiones (próximamente)
- **SQLite** - Base de datos (próximamente)

---

## 🔒 Seguridad

- ✅ Credenciales nunca en código fuente
- ✅ Archivos sensibles en `.gitignore`
- ✅ Logging seguro sin exponer secretos
- ✅ Variables de entorno para configuración sensible
- ✅ Archivos `.example` para documentación

**Archivos a NO commitear:**
- `config/credentials.json`
- `config/settings.json`
- `.env`
- `*.log`
- `*.db`

---

## 📊 Estado de Desarrollo

### Fase 0: Fundamentos (En Progreso)
- [x] T44 - Gestión de credenciales
- [x] T39 - Logging por bot y nivel
- [ ] T45 - Módulos core reutilizables
- [ ] T46 - Tests unitarios
- [ ] T47 - Almacenamiento seguro

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
| Tickets Completados | 2 |
| Tests | 30 |
| Cobertura | 89% |
| Líneas de Código | ~700 |

---

**Última actualización:** 6 de Noviembre de 2025  
**Versión:** 0.1.0  
**Estado:** 🚀 En desarrollo activo
