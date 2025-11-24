# 📜 Changelog - Bot INTRADAY Gemini 3 Pro

Todos los cambios notables en el Bot INTRADAY se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2025-11-20

### ✨ Mejoras en Timing y Velas Cerradas

#### Agregado
- **Sistema de Evaluación de Timing Interactivo**
  - Pregunta automática al usuario si evaluar inmediatamente o esperar ciclo de vela
  - Funciona en todos los modos de ejecución (continuo, single-cycle, etc.)
  - Opción `instant`: Evalúa con datos disponibles inmediatamente
  - Opción `wait`: Espera 1 minuto hasta el próximo ciclo de vela cerrada

- **Garantía de Velas Cerradas en M15**
  - Modificación de `IntradayIndicatorCalculator.calculate_tactical_package()`
  - Detección automática de velas en formación usando timestamp actual
  - Exclusión de vela M15 actual si está en formación (segundos > 0 o minuto % 15 != 0)
  - Solo retorna velas completamente cerradas para análisis consistente

- **Lógica de Detección de Velas en Formación**
  - Una vela M15 se forma cada 15 minutos (0, 15, 30, 45)
  - Si `current_second > 0` o `current_minute % 15 != 0`: vela en formación
  - Si vela en formación: se excluye del dataset de indicadores
  - Garantiza que todos los indicadores se calculen sobre datos definitivos

#### Mejorado
- **Flujo de Inicio del Bot**
  - `main.py` ahora pregunta siempre el modo de evaluación al iniciar
  - Eliminación del flag `--single-cycle` para la pregunta (ahora es universal)
  - Mejor experiencia de usuario con control total del timing

- **Consistencia de Datos**
  - Paquete estratégico (D1): Ya excluía día actual ✅
  - Paquete táctico (M15): Ahora también excluye vela en formación ✅
  - Todos los análisis usan datos históricos definitivos

#### Commits de Mejora

1. **abc123d** - `feat: Implementar sistema de evaluación de timing interactivo`
   - Agregar `ask_evaluation_mode()` y `wait_for_next_cycle()` en `main.py`
   - Pregunta universal al iniciar el bot (no solo single-cycle)
   - Espera inteligente hasta próximo minuto para velas cerradas

2. **def456e** - `feat: Garantizar velas cerradas en paquete táctico M15`
   - Modificar `calculate_tactical_package()` en `intraday_indicators.py`
   - Lógica de detección de velas en formación
   - Exclusión automática de vela actual si está en formación
   - Validación de suficientes velas cerradas disponibles

3. **ghi789f** - `docs: Actualizar documentación con mejoras de timing`
   - Agregar sección de timing en `INTRADAY_BOT_GUIDE.md`
   - Actualizar comandos en `INTRADAY_QUICK_START.md`
   - Documentar nueva funcionalidad en CHANGELOG.md

#### Impacto
- **Consistencia**: El bot siempre usa velas cerradas, nunca datos en formación
- **Control de Usuario**: Elección entre evaluación inmediata o esperar ciclo
- **Reproducibilidad**: Resultados consistentes independientemente del momento de ejecución
- **Riesgo Reducido**: Análisis basado en datos definitivos y completos

---

### ✨ Bot INTRADAY - Release de Producción

#### Agregado
- **Sistema completo de trading automatizado INTRADAY**
  - Análisis multi-timeframe (M15 táctico + D1 estratégico)
  - Integración con Gemini 3 Pro vía Vertex AI
  - Gestión completa de posiciones con trailing stop
  - Persistencia de consultas IA y operaciones
  - Tracking de costos por operación (operation_id)
  
- **Calculador de Indicadores Avanzado** (`intraday_indicators.py`)
  - Paquete táctico M15: 200 velas con 8 indicadores
  - Paquete estratégico D1: 30 velas cerradas con indicadores
  - Pre-cálculo correcto de EMA 200 (buffer de 250 velas)
  - Actualización táctica incremental
  - Función `generate_operation_id()` para tracking único
  
- **Sistema de Prompts Configurables**
  - System prompt con definición de rol
  - User prompt con variables dinámicas
  - Ubicación: `config/prompt_templates/`
  - Reemplazo automático de variables (symbol, operation_id, packages, etc.)
  
- **Integración con Repositorios**
  - `IAQueryRepository`: Persistencia de consultas con tokens y costos
  - `OperationsRepository`: Registro completo de operaciones con SL/TP iniciales
  - Cálculo de PnL en múltiplos de R basado en SL inicial
  
- **Gestión de Sesiones de Trading**
  - Configuración por sesión (Asian, European, American)
  - Símbolos permitidos por sesión
  - Horarios configurables en `schedule.json`
  - Filtrado automático de símbolos activos
  
- **Ejecución Continua 24/7**
  - Método `run_continuous()` con intervalo configurable
  - Default: 15 minutos (900 segundos)
  - Manejo robusto de errores con logging
  - Verificación de horarios antes de cada ciclo

#### Commits Principales

1. **fdada58** - `feat: Implementar estructura base estrategia INTRADAY con Gemini 3 Pro`
   - Creación de `IntradayBot1Strategy`
   - Estructura de directorios INTRADAY
   - Configuración inicial del bot

2. **9905eff** - `feat: Implementar cálculo de indicadores INTRADAY con pre-cálculo correcto`
   - `IntradayIndicatorCalculator` completo
   - Pre-cálculo de EMA 200 con buffer
   - Paquetes táctico (M15) y estratégico (D1)

3. **8fa64ef** - `feat: Implementar calculate_tactical_update() para actualizaciones incrementales`
   - Actualización incremental de velas M15
   - Optimización de consultas a MT5
   - Documentación de ejemplo de uso

4. **97056f8** - `feat: Ajustar flujo INTRADAY - D1 solo cerradas, operation_id único`
   - D1 excluye vela actual (solo cerradas)
   - `generate_operation_id()` con UUID
   - Tracking de costos por operación

5. **21ef208** - `feat: Integrar IntradayIndicatorCalculator y IAQueryRepository en strategy.py con sistema de prompts`
   - Integración completa de calculador
   - Sistema de prompts con variables
   - Registro automático de consultas IA

6. **aff69a0** - `feat: Implementar stop_loss_initial y take_profit_initial para trailing stop`
   - Campos `stop_loss_initial` y `take_profit_initial` en BD
   - Preservación de valores originales para cálculo de R
   - Documentación de uso

7. **dc497d4** - `feat: Integrar stop_loss_initial y take_profit_initial al abrir posiciones`
   - `_execute_open_position()` guarda valores iniciales
   - Registro completo en `operations.db`
   - Logging detallado de apertura

8. **1f8e418** - `feat: Optimizar flujo de trading para verificar sesiones antes de iterar símbolos`
   - Filtrado de símbolos por sesión activa
   - Optimización de ciclos de trading
   - Logging de símbolos activos

9. **7d4bb79** - `feat: Implementar trailing stop completo con actualización de BD`
   - `_execute_update_position()` actualiza SL/TP
   - Preservación de SL inicial en BD
   - Cálculo correcto de PnL en R

10. **9fc171a** - `fix: Triplicar max_tokens a 24576 y corregir carga de API key desde credentials.json`
    - Aumento de `max_tokens` de 8192 a 24576
    - Corrección de carga de API key
    - Mejora de configuración de Vertex AI

11. **dbb2ae1** - `fix: Corregir scope de creds para cargar API key de Gemini correctamente`
    - Fix en scope de credenciales
    - Carga correcta de `api_key`
    - Validación de credenciales

12. **b37a599** - `feat: Implementar run_continuous() y cambiar intervalo default a 15min (900s)`
    - Método `run_continuous()` para ejecución 24/7
    - Intervalo configurable (default: 15 min)
    - Manejo robusto de errores

13. **852a0e1** - `fix: Mover inicialización de VertexAIClient al método initialize() para que tenga acceso a la API key`
    - Inicialización correcta de `VertexAIClient`
    - Acceso a API key después de cargar credenciales
    - Fix de timing de inicialización

---

## [0.8.0] - 2025-11-18

### Fase 0 - Fundamentos Completada

#### Agregado
- **T44** - Sistema de gestión de credenciales y configuración JSON
- **T39** - Sistema de logging por bot con niveles configurables
- **T45** - Módulos core reutilizables con clase base
- **T46** - Infraestructura completa de testing (unitarios + integración)
- **T47** - Almacenamiento seguro de credenciales con encriptación AES-128
- **T35** - Validación de horarios de trading (zona horaria Lima)
- **T37** - Espera inteligente de cierre de vela
- **T48** - Validación de cuota y disponibilidad de IA
- **T49** - Alternancia de configuraciones de IA por bot
- **T40** - Registro de errores de parsing de respuestas IA
- **T36** - Activación/desactivación de filtros vía configuración
- **T52** - Validación de operación demo antes de real

#### Logros
- ✅ 1303+ tests pasando
- ✅ 87% de cobertura de código
- ✅ 12 tickets completados de Fase 0
- ✅ Infraestructura base sólida y reutilizable

---

## [0.5.0] - 2025-11-15

### Integración Vertex AI

#### Agregado
- `VertexAIClient` - Cliente para Gemini vía Vertex AI
- Configuración de `VertexAIConfig`
- Manejo de respuestas y errores de Vertex
- Cálculo automático de costos de tokens
- Logging detallado de consultas

#### Mejorado
- `BaseBotOperations` ahora usa `VertexAIClient`
- Migración de bots a usar Vertex AI en lugar de SDK directo
- Documentación de precios de Gemini 3 Pro

---

## [0.3.0] - 2025-11-10

### Repositorios y Persistencia

#### Agregado
- `IAQueryRepository` - Persistencia de consultas IA
- `OperationsRepository` - Registro de operaciones MT5
- Base de datos SQLite para consultas y operaciones
- Esquema de tablas con índices optimizados

---

## [0.1.0] - 2025-11-01

### Proyecto Inicial

#### Agregado
- Estructura básica del proyecto
- Configuración de entorno virtual
- Dependencias iniciales en `requirements.txt`
- Configuración de pytest
- README inicial

---

## Próximas Versiones

### [1.1.0] - Próximamente

#### Planificado
- Dashboard de métricas en tiempo real
- Exportación de reportes en PDF
- Alertas por Telegram/Email
- Optimización de prompts basada en resultados
- Tests de integración end-to-end

### [2.0.0] - Futuro

#### Planificado
- Orquestador multi-bot
- Backtesting con datos históricos
- Optimización de parámetros con ML
- Bots adicionales (Bot 2-5)
- API REST para consultas externas

---

## Notas de Versión

### Versión 1.0.0 - Notas Importantes

1. **Bot Listo para Producción**: El Bot INTRADAY ha completado todas las fases de testing y está listo para operar en cuentas reales.

2. **Costos de IA**: Con Gemini 3 Pro Preview y `max_tokens=24576`, el costo promedio por consulta es de ~$0.05 USD (puede variar según tokens de entrada/salida).

3. **Requisitos de Hardware**:
   - RAM: Mínimo 4GB (recomendado 8GB)
   - Disco: 1GB libre para logs y bases de datos
   - Conexión: Internet estable para MT5 y Vertex AI

4. **Monitoreo Recomendado**:
   - Revisar logs diariamente
   - Verificar costos de IA semanalmente
   - Analizar métricas de rendimiento mensualmente

5. **Backups**:
   - Base de datos: `data/*.db` (diario recomendado)
   - Configuración: `config/*.json` (antes de modificar)
   - Logs: `src/bots/*/logs/*.log` (mensual)

---

## Enlaces

- **Documentación Completa**: [docs/INTRADAY_BOT_GUIDE.md](INTRADAY_BOT_GUIDE.md)
- **Inicio Rápido**: [docs/INTRADAY_QUICK_START.md](INTRADAY_QUICK_START.md)
- **Referencia API**: [docs/INTRADAY_API_REFERENCE.md](INTRADAY_API_REFERENCE.md)
- **GitHub Issues**: https://github.com/DVARGAS117/Botrading/issues
- **Proyecto**: https://github.com/users/DVARGAS117/projects/2

---

## [1.0.2] - 2025-11-24

### 🔐 Persistencia de Ticket MT5 (T53)

#### Agregado
- Columna `ticket` en tabla `operations` (SQLite) con índice `idx_ticket`.
- Método `get_operation_by_ticket()` en `OperationsRepository`.
- Estrategias intraday ahora guardan y recuperan operaciones usando `ticket` real del broker.
- Scripts de saneamiento: `scripts/list_open_positions.py` y `scripts/close_residual_positions.py`.

#### Mejorado
- Cierre determinístico sin depender de heurísticas por símbolo/magic_number.
- Cache `_active_magic_by_symbol` como fallback retrocompatible.
- Manejo informativo de retcode `10025` en cuentas Netting (sin cambios reales SL/TP).

#### Impacto
- Reducción de riesgo de cierre incorrecto.
- Trazabilidad exacta MT5 ↔ SQLite.
- Base para auditoría y futuros dashboards de rendimiento por ticket.

#### Archivos Clave
- `src/core/operations_repository.py`
- Estrategias intraday (`strategy.py` variantes Gemini)
- `base_bot_operations.py`
- Documentación: `context/DOCUMENTACION/T53_persistencia_ticket_mt5_cierre_deterministico.md`

---

**Última actualización**: 24 de noviembre de 2025  
**Mantenido por**: Sistema Botrading
