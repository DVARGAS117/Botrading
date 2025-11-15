# Documentación: Módulo ReevaluationTracker

**Ticket:** T28 - Registro de trazabilidad de cada reevaluación  
**Fase:** 2 - Reevaluación  
**Prioridad:** P1  
**Fecha:** 2025-11-13  
**Desarrollador:** Sistema Botrading  

---

## 📋 Resumen

El módulo `reevaluation_tracker.py` implementa el sistema de **trazabilidad completa** para reevaluaciones de posiciones abiertas. Permite registrar cada reevaluación con su decisión, tokens consumidos, costos asociados y contexto de mercado, facilitando auditoría, análisis de costos y optimización del sistema.

---

## 🎯 Objetivos del Ticket T28

### Historia de Usuario
> Como auditor, quiero registrar cada reevaluación con decisión, tokens y costos asociados, para mantener trazabilidad completa.

### Criterios de Aceptación ✅

**Escenario:** Registrar trazabilidad de cada reevaluación
- ✅ **Dado que** se realizó una reevaluación
- ✅ **Cuando** se persisten decisión, tokens y costos
- ✅ **Entonces** la operación queda con historial completo de reevaluaciones

---

## 🏗️ Arquitectura

### Estructura de Archivos

```
BOTRADING/
├── src/
│   └── core/
│       ├── reevaluation_tracker.py      # ✅ Módulo principal (T28)
│       └── reevaluation_manager.py       # ✅ Integrado con tracker
├── tests/
│   └── unit/
│       └── test_reevaluation_tracker.py  # ✅ 23 tests (94% cobertura)
├── examples/
│   └── reevaluation_tracker_example.py   # ✅ Ejemplos de uso
├── data/
│   └── reevaluations/
│       └── reevaluations.json            # Persistencia de registros
└── context/
    └── DOCUMENTACION/
        └── T28_registro_trazabilidad_reevaluacion.md  # Este archivo
```

---

## 🔧 Componentes Principales

### 1. ReevaluationAction (Enum)

Acciones posibles en una reevaluación:

```python
class ReevaluationAction(Enum):
    MANTENER = "MANTENER"     # Mantener posición sin cambios
    ACTUALIZAR = "ACTUALIZAR"  # Modificar SL/TP
    CERRAR = "CERRAR"          # Cerrar la posición
```

**Métodos:**
- `from_string(value: str)` - Convierte string a enum

### 2. ReevaluationRecord (Dataclass)

Registro individual de una reevaluación:

```python
@dataclass
class ReevaluationRecord:
    position_id: str           # ID de la posición
    symbol: str                # Símbolo (EURUSD, GBPUSD, etc.)
    action: ReevaluationAction # Acción tomada
    current_price: float       # Precio actual
    profit_pips: float         # P/L en pips
    reasoning: str             # Razonamiento de IA
    new_sl: Optional[float]    # Nuevo SL (si actualiza)
    new_tp: Optional[float]    # Nuevo TP (si actualiza)
    conversation_id: Optional[str]  # ID de conversación
    reevaluation_mode: str     # persistent/new
    tokens_input: int          # Tokens de entrada
    tokens_output: int         # Tokens de salida
    cost: float                # Costo en USD
    reevaluation_count: int    # Número de reevaluación
    time_since_last: int       # Segundos desde última
    timestamp: datetime        # Timestamp
```

**Métodos:**
- `to_dict()` - Convierte a diccionario serializable
- `from_dict(data)` - Crea record desde diccionario

### 3. TrackerStatistics (Dataclass)

Estadísticas agregadas de reevaluaciones:

```python
@dataclass
class TrackerStatistics:
    total_reevaluations: int         # Total de reevaluaciones
    total_tokens_input: int          # Total tokens entrada
    total_tokens_output: int         # Total tokens salida
    total_cost: float                # Costo total acumulado
    unique_positions: int            # Posiciones únicas
    unique_symbols: int              # Símbolos únicos
    actions_count: Dict[str, int]    # Conteo por acción
    avg_cost_per_reevaluation: float # Costo promedio
```

### 4. ReevaluationTracker (Clase Principal)

Sistema de registro y consulta de trazabilidad:

```python
class ReevaluationTracker:
    def __init__(self, storage_dir: str = "data/reevaluations")
    def register(...)  # Registra nueva reevaluación
    def get_all_records() -> List[ReevaluationRecord]
    def get_history_by_position(position_id) -> List[ReevaluationRecord]
    def get_history_by_symbol(symbol) -> List[ReevaluationRecord]
    def get_statistics(...) -> TrackerStatistics
    def clear_history_by_position(position_id) -> int
    def clear_all() -> int
```

---

## 📖 Uso del Módulo

### Inicialización

```python
from src.core.reevaluation_tracker import (
    ReevaluationTracker,
    ReevaluationAction
)

# Crear tracker
tracker = ReevaluationTracker(storage_dir="data/reevaluations")
```

### Registrar Reevaluación

```python
# Ejemplo: Actualizar SL/TP
tracker.register(
    position_id="pos_001",
    symbol="EURUSD",
    action=ReevaluationAction.ACTUALIZAR,
    current_price=1.2580,
    profit_pips=80.0,
    reasoning="Profit +80 pips. Mover SL a breakeven.",
    new_sl=1.2420,
    new_tp=1.2650,
    conversation_id="conv_abc123",
    reevaluation_mode="persistent",
    tokens_input=500,
    tokens_output=150,
    cost=0.0045,
    reevaluation_count=2,
    time_since_last=600  # 10 minutos
)
```

### Consultar Historial

```python
# Por posición
history = tracker.get_history_by_position("pos_001")
print(f"Total reevaluaciones: {len(history)}")

for record in history:
    print(f"{record.action.value} - {record.profit_pips:+.1f} pips - ${record.cost:.4f}")

# Por símbolo
eurusd_history = tracker.get_history_by_symbol("EURUSD")

# Todas
all_records = tracker.get_all_records()
```

### Estadísticas

```python
# Generales
stats = tracker.get_statistics()

print(f"Total reevaluaciones: {stats.total_reevaluations}")
print(f"Costo total: ${stats.total_cost:.4f}")
print(f"Tokens totales: {stats.total_tokens_input + stats.total_tokens_output:,}")

# Por tipo de acción
for action, count in stats.actions_count.items():
    print(f"{action}: {count}")

# Filtradas por acción
stats_actualizar = tracker.get_statistics(
    action_filter=ReevaluationAction.ACTUALIZAR
)
```

### Limpieza

```python
# Limpiar posición específica
deleted = tracker.clear_history_by_position("pos_001")
print(f"Eliminados: {deleted} registros")

# Limpiar todos
total_deleted = tracker.clear_all()
```

---

## 🔄 Integración con ReevaluationManager

El `ReevaluationManager` ha sido modificado para integrar automáticamente el tracker:

```python
from src.core.reevaluation_manager import ReevaluationManager
from src.core.reevaluation_tracker import ReevaluationTracker

# Crear tracker
tracker = ReevaluationTracker(storage_dir="data/reevaluations")

# Crear manager con tracker integrado
manager = ReevaluationManager(
    mt5_connector=mt5_conn,
    data_extractor=extractor,
    prompt_builder=builder,
    gemini_client=client,
    response_parser=parser,
    position_manager=pos_mgr,
    tracker=tracker  # ✅ Tracker integrado
)

# Ahora cada reevaluación se registra automáticamente
results = await manager.reevaluate_positions(
    bot_id="bot_1",
    magic_number=100101
)

# Consultar trazabilidad
history = tracker.get_all_records()
```

**Registro Automático:**

Cada vez que `ReevaluationManager` ejecuta una reevaluación:
1. Obtiene datos del mercado
2. Consulta a IA
3. Parsea respuesta
4. **Registra en tracker (T28)** ✅
5. Ejecuta acción en MT5

---

## 📊 Tests y Cobertura

### Resultados de Tests

```
✅ 23/23 tests pasados
✅ 94% de cobertura de código
✅ 0.91s tiempo de ejecución
```

### Tests Implementados

**ReevaluationRecord:**
1. `test_create_record_minimal` - Creación con datos mínimos
2. `test_create_record_complete` - Creación con todos los campos
3. `test_to_dict` - Conversión a diccionario
4. `test_from_dict` - Creación desde diccionario

**ReevaluationTracker:**
5. `test_initialization` - Inicialización correcta
6. `test_register_reevaluation_mantener` - Registro acción MANTENER
7. `test_register_reevaluation_actualizar` - Registro acción ACTUALIZAR
8. `test_register_reevaluation_cerrar` - Registro acción CERRAR
9. `test_get_history_by_position` - Consulta por posición
10. `test_get_history_by_symbol` - Consulta por símbolo
11. `test_get_statistics` - Estadísticas generales
12. `test_get_statistics_by_action` - Estadísticas filtradas
13. `test_persistence` - Persistencia entre instancias
14. `test_clear_history_by_position` - Limpieza selectiva
15. `test_validation_negative_tokens` - Validación tokens
16. `test_validation_negative_cost` - Validación costo

**Integración:**
17. `test_track_reevaluations_automatically` - Registro automático

**Cobertura Adicional:**
18. `test_clear_all_records` - Limpieza total
19. `test_invalid_action_from_string` - Acción inválida
20. `test_statistics_empty` - Stats sin registros
21. `test_corrupted_json_file` - JSON corrupto
22. `test_non_list_json` - JSON no-lista
23. `test_record_with_parse_error` - Record inválido

---

## 💾 Persistencia

### Formato JSON

Los registros se almacenan en `data/reevaluations/reevaluations.json`:

```json
[
  {
    "position_id": "pos_001",
    "symbol": "EURUSD",
    "action": "ACTUALIZAR",
    "current_price": 1.258,
    "profit_pips": 80.0,
    "reasoning": "Profit +80 pips. Mover SL a breakeven.",
    "new_sl": 1.242,
    "new_tp": 1.265,
    "conversation_id": "conv_abc123",
    "reevaluation_mode": "persistent",
    "tokens_input": 500,
    "tokens_output": 150,
    "cost": 0.0045,
    "reevaluation_count": 2,
    "time_since_last": 600,
    "timestamp": "2025-11-13T12:30:00"
  }
]
```

**Características:**
- ✅ Formato legible y editable
- ✅ Ordenado por timestamp (más reciente primero)
- ✅ UTF-8 con soporte de caracteres especiales
- ✅ Manejo robusto de archivos corruptos

---

## 📈 Casos de Uso

### Caso 1: Auditoría de Decisiones

```python
# Consultar todas las decisiones de cierre
stats = tracker.get_statistics(action_filter=ReevaluationAction.CERRAR)

print(f"Total cierres: {stats.total_reevaluations}")
print(f"Costo total: ${stats.total_cost:.4f}")
```

### Caso 2: Análisis de Costos por Posición

```python
# Historial de una posición específica
history = tracker.get_history_by_position("pos_001")

total_cost = sum(r.cost for r in history)
total_tokens = sum(r.tokens_input + r.tokens_output for r in history)

print(f"Costo total IA: ${total_cost:.4f}")
print(f"Tokens consumidos: {total_tokens:,}")
```

### Caso 3: Comparación de Eficiencia

```python
# Comparar costos entre símbolos
eurusd_history = tracker.get_history_by_symbol("EURUSD")
gbpusd_history = tracker.get_history_by_symbol("GBPUSD")

eurusd_cost = sum(r.cost for r in eurusd_history)
gbpusd_cost = sum(r.cost for r in gbpusd_history)

print(f"EURUSD: ${eurusd_cost:.4f} ({len(eurusd_history)} reevaluaciones)")
print(f"GBPUSD: ${gbpusd_cost:.4f} ({len(gbpusd_history)} reevaluaciones)")
```

### Caso 4: Optimización de Prompts

```python
# Identificar reevaluaciones con alto consumo
all_records = tracker.get_all_records()

high_cost = [r for r in all_records if r.cost > 0.005]
high_tokens = [r for r in all_records if r.tokens_input > 600]

print(f"Reevaluaciones costosas: {len(high_cost)}")
print(f"Reevaluaciones con muchos tokens: {len(high_tokens)}")

# Analizar razonamientos para optimizar prompts
for record in high_tokens:
    print(f"{record.symbol} - {record.tokens_input} tokens")
    print(f"Razonamiento: {record.reasoning[:100]}...")
```

---

## 🎓 Mejores Prácticas

### ✅ DO (Hacer)

1. **Registrar cada reevaluación** - Usar el tracker automáticamente
2. **Revisar estadísticas regularmente** - Para optimización
3. **Analizar costos por bot** - Evaluar eficiencia económica
4. **Limpiar registros antiguos** - Mantener base de datos ligera
5. **Validar datos antes de registrar** - Evitar datos corruptos

### ❌ DON'T (No Hacer)

1. **No omitir registro de reevaluaciones** - Perder trazabilidad
2. **No ignorar errores de tracking** - Revisar logs
3. **No acumular infinitos registros** - Implementar limpieza periódica
4. **No exponer datos sensibles** - Sanitizar si es necesario
5. **No modificar archivos JSON manualmente** - Usar la API

---

## 🔄 Flujo de Trabajo Típico

```
1. Bot detecta posición abierta
         ↓
2. ReevaluationManager inicia reevaluación
         ↓
3. Obtiene datos actualizados de MT5
         ↓
4. Construye prompt y envía a IA
         ↓
5. Parsea respuesta de IA
         ↓
6. ✅ REGISTRA EN TRACKER (T28)
         ↓
7. Ejecuta acción en MT5
         ↓
8. Retorna resultado
```

---

## 📊 Métricas

| Métrica | Valor |
|---------|-------|
| Líneas de código | 372 |
| Tests | 23 |
| Cobertura | 94% |
| Complejidad ciclomática | Baja |
| Mantenibilidad | Alta |
| Acoplamiento | Bajo |

---

## 🚀 Próximos Pasos

### Completado ✅
1. ✅ **T28** - Registro de trazabilidad de cada reevaluación
2. ✅ **Integración** - ReevaluationManager + ReevaluationTracker
3. ✅ **Tests** - 23 tests con 94% cobertura
4. ✅ **Ejemplos** - 5 ejemplos completos de uso
5. ✅ **Documentación** - Documentación técnica completa

### Futuras Mejoras 🔮
1. **Dashboard de métricas** - Visualización de estadísticas
2. **Alertas de costos** - Notificaciones si excede presupuesto
3. **Exportación a CSV/Excel** - Para análisis externo
4. **Integración con base de datos** - Migrar de JSON a SQLite
5. **API REST** - Consultas remotas de trazabilidad

---

## 🔗 Relaciones con Otros Tickets

### Dependencias
- ✅ **T26** - Reevaluación cada 10 minutos (base para tracking)
- ✅ **T11** - Registro de tokens y costo (datos registrados)
- ✅ **T10** - Construcción de prompts (contexto de IA)
- ✅ **T12** - Mantenimiento de contexto (conversation_id)

### Habilita
- ⏭️ **T41** - Disponibilización de métricas diarias
- ⏭️ **T42** - Comparación de desempeño entre metodologías
- ⏭️ **Fase 3** - Optimización de prompts y costos

---

## 📝 Notas Adicionales

### Seguridad

- ✅ Validación de inputs (tokens, cost no negativos)
- ✅ Manejo robusto de archivos corruptos
- ✅ Logs sanitizados (no expone datos sensibles)
- ✅ Excepciones controladas (no crashea el sistema)

### Performance

- ✅ Escritura en JSON (O(1) append)
- ✅ Lectura en memoria (O(n) pero eficiente)
- ✅ Filtros optimizados (list comprehension)
- ✅ Ordenamiento por timestamp (eficiente)

### Escalabilidad

El sistema actual usa JSON para simplicidad y trazabilidad. Para producción con alto volumen:

```python
# Migración futura a SQLite (propuesta)
class ReevaluationTrackerDB:
    """Versión con base de datos para alto volumen"""
    
    def __init__(self, db_path="data/reevaluations.db"):
        # Usar SQLAlchemy + SQLite
        # Índices: position_id, symbol, timestamp, action
        # Soporte para millones de registros
        pass
```

---

## 🤝 Contribuciones

Para modificar o extender este módulo:

1. **Escribir tests primero** (TDD)
2. **Mantener cobertura > 90%**
3. **Documentar cambios** en este archivo
4. **Seguir PEP 8** y type hints
5. **Actualizar ejemplos** si cambia la API

---

## 📞 Soporte y Referencias

- **Documentación de tickets:** `context/DOCUMENTACION/`
- **Tests unitarios:** `tests/unit/test_reevaluation_tracker.py`
- **Ejemplos:** `examples/reevaluation_tracker_example.py`
- **Issue en GitHub:** #44 (T28)

---

**Documento generado:** 2025-11-13  
**Versión:** 1.0  
**Estado:** ✅ Completado y testeado  
**Autor:** Sistema Botrading
