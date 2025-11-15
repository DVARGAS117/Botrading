# T33 - Registro de Consultas a IA con Prompts, Respuesta, Tokens y Costo

## 📋 Información del Ticket

- **ID**: T33
- **Issue**: #49
- **Fase**: 3 (Persistencia y trazabilidad)
- **Prioridad**: P0 (Crítica)
- **Épica**: #10 (Persistencia y trazabilidad)
- **Estado**: ✅ IMPLEMENTADO

## 🎯 Objetivo

Implementar un sistema de registro de consultas a IA que persista prompts, respuestas JSON, tokens consumidos y costos asociados, para evaluar eficiencia económica y calidad de decisiones.

## 📝 Historia de Usuario

> Como analista, quiero registrar consultas a IA con prompt, respuesta, tokens y costo, para evaluar eficiencia y calidad de decisión.

## ✅ Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Registrar consultas a IA con prompts, respuesta, tokens y costo
  Dado que se envía una consulta a IA
  Cuando se recibe la respuesta
  Entonces se guarda prompt, respuesta, tokens, costo y referencias a la operación
```

## 🏗️ Arquitectura

### Componentes Implementados

1. **IAQueryRepository** (`src/core/ia_query_repository.py`)
   - Repositorio para persistencia en SQLite
   - Gestión de consultas a IA
   - Estadísticas y métricas

2. **IAQuery** (modelo de datos)
   - Dataclass con toda la información de la consulta
   - Conversión a diccionario para serialización

3. **QueryType** (enum)
   - `EVALUATION`: Consulta de evaluación inicial
   - `REEVALUATION`: Consulta de reevaluación periódica

### Esquema de Base de Datos

```sql
CREATE TABLE IF NOT EXISTS consultas_ia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operacion_id INTEGER,                  -- FK a operaciones (puede ser NULL)
    bot_id INTEGER NOT NULL,
    ia_id INTEGER NOT NULL,
    activo TEXT NOT NULL,
    
    tipo_consulta TEXT NOT NULL,           -- 'evaluacion' o 'reevaluacion'
    
    prompt TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    tokens_total INTEGER NOT NULL,
    costo_usd REAL NOT NULL,
    
    accion_decidida TEXT NOT NULL,         -- 'OPERAR', 'NO_OPERAR', 'MANTENER', etc.
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_operacion ON consultas_ia(operacion_id);
CREATE INDEX IF NOT EXISTS idx_bot_ia ON consultas_ia(bot_id, ia_id);
```

## 🔧 Uso del Módulo

### Inicialización

```python
from pathlib import Path
from src.core.ia_query_repository import (
    IAQueryRepository,
    QueryType
)

# Crear instancia del repositorio
repo = IAQueryRepository(db_path=Path("data/ia_queries.db"))
```

### Registrar Consulta de Evaluación

```python
# Registrar consulta inicial (sin operación todavía)
query = repo.create_query(
    bot_id=1,
    ia_id=1,
    symbol="EURUSD",
    query_type=QueryType.EVALUATION,
    prompt="Analiza EURUSD con EMA(20)=1.0850, RSI=65",
    response='{"decision": "OPERAR", "direction": "BUY", "sl": 1.0800, "tp": 1.0950}',
    tokens_input=150,
    tokens_output=80,
    cost_usd=0.0023,
    action_decided="OPERAR",
    operation_id=None  # Aún no hay operación
)

print(f"Consulta creada con ID: {query.id}")
```

### Vincular a Operación

```python
# Si se decidió operar, vincular la consulta a la operación
operation_id = 456  # ID de la operación creada
updated_query = repo.update_operation_id(query.id, operation_id)
```

### Registrar Reevaluación

```python
# Registrar reevaluación cada 10 minutos
reeval_query = repo.create_query(
    bot_id=1,
    ia_id=1,
    symbol="EURUSD",
    query_type=QueryType.REEVALUATION,
    prompt="Reevaluar EURUSD - Precio: 1.0870, SL: 1.0800, TP: 1.0950",
    response='{"decision": "MANTENER", "reason": "Operación saludable"}',
    tokens_input=100,
    tokens_output=40,
    cost_usd=0.0014,
    action_decided="MANTENER",
    operation_id=operation_id  # Vinculado a operación existente
)
```

### Consultas

```python
# Obtener por ID
query = repo.get_query_by_id(1)

# Obtener todas las consultas de una operación
operation_queries = repo.get_queries_by_operation_id(456)

# Obtener consultas de un bot
bot_queries = repo.get_queries_by_bot(bot_id=1)

# Obtener consultas de un símbolo
symbol_queries = repo.get_queries_by_symbol("EURUSD")

# Obtener por tipo
evaluations = repo.get_queries_by_type(QueryType.EVALUATION)
reevaluations = repo.get_queries_by_type(QueryType.REEVALUATION)

# Obtener todas
all_queries = repo.get_all_queries()
```

### Estadísticas

```python
# Estadísticas generales
stats = repo.get_statistics()
print(f"Total consultas: {stats['total_queries']}")
print(f"Costo total: ${stats['total_cost']:.4f}")
print(f"Tokens totales: {stats['total_tokens_total']:,}")

# Estadísticas por bot
bot_stats = repo.get_statistics_by_bot(bot_id=1)

# Costo por tipo de consulta
eval_cost = repo.get_cost_by_type(QueryType.EVALUATION)
reeval_cost = repo.get_cost_by_type(QueryType.REEVALUATION)

# Costo total
total_cost = repo.get_total_cost()
```

## 📊 Modelo de Datos

### IAQuery

```python
@dataclass
class IAQuery:
    id: Optional[int]              # ID autoincremental
    operation_id: Optional[int]    # FK a operaciones (puede ser NULL)
    bot_id: int                    # ID del bot
    ia_id: int                     # ID de config de IA
    symbol: str                    # Símbolo (ej: "EURUSD")
    
    query_type: QueryType          # EVALUATION o REEVALUATION
    
    prompt: str                    # Texto del prompt
    response: str                  # JSON de respuesta
    
    tokens_input: int              # Tokens de entrada
    tokens_output: int             # Tokens de salida
    tokens_total: int              # Total (calculado)
    cost_usd: float                # Costo en USD
    
    action_decided: str            # Acción decidida
    
    created_at: Optional[datetime] # Timestamp de creación
```

## ✅ Validaciones

El repositorio valida:

1. **Tipos de datos**: Todos los parámetros deben ser del tipo correcto
2. **Valores positivos**: `bot_id`, `ia_id`, `tokens_*`, `cost_usd` deben ser >= 0
3. **Campos no vacíos**: `symbol`, `prompt`, `response`, `action_decided`
4. **Enum correcto**: `query_type` debe ser `QueryType.EVALUATION` o `QueryType.REEVALUATION`

## 🧪 Tests

El módulo está completamente testeado (TDD):

```bash
pytest tests/unit/test_ia_query_repository.py -v
```

**Cobertura de tests:**
- ✅ Inicialización del repositorio
- ✅ Creación de schema y índices
- ✅ Creación de consultas (evaluación y reevaluación)
- ✅ Validaciones de datos
- ✅ Consultas por ID, operación, bot, símbolo, tipo
- ✅ Actualización de operation_id
- ✅ Estadísticas generales y por bot
- ✅ Cálculo de costos por tipo
- ✅ Flujos de integración completos

**Resultado:** 33/33 tests passing ✅

## 🔗 Integración con Otros Módulos

### Con OperationsRepository (T32)

```python
from src.core.operations_repository import OperationsRepository
from src.core.ia_query_repository import IAQueryRepository

# Flujo completo
operations_repo = OperationsRepository(db_path=Path("data/operations.db"))
ia_repo = IAQueryRepository(db_path=Path("data/ia_queries.db"))

# 1. Registrar consulta
query = ia_repo.create_query(...)

# 2. Si se decidió operar, crear operación
if query.action_decided == "OPERAR":
    operation = operations_repo.create_operation(...)
    
    # 3. Vincular consulta a operación
    ia_repo.update_operation_id(query.id, operation.id)
```

### Con GeminiClient (T10)

```python
from src.core.gemini_client import GeminiClient
from src.core.ia_query_repository import IAQueryRepository

gemini = GeminiClient(api_key="...")
ia_repo = IAQueryRepository(db_path=Path("data/ia_queries.db"))

# Realizar consulta y registrar
response = gemini.query(prompt="Analiza EURUSD...")

# Registrar en BD
query = ia_repo.create_query(
    bot_id=1,
    ia_id=1,
    symbol="EURUSD",
    query_type=QueryType.EVALUATION,
    prompt=response.prompt,
    response=response.response_text,
    tokens_input=response.tokens_input,
    tokens_output=response.tokens_output,
    cost_usd=response.cost,
    action_decided=response.parsed_data.get("decision", "UNKNOWN")
)
```

### Con IACostTracker (T11)

Ambos módulos son complementarios:
- **IACostTracker**: Registro simple en JSON para tracking rápido
- **IAQueryRepository**: Persistencia completa en SQLite con relaciones

Opción: Unificar usando solo IAQueryRepository en el futuro.

## 📈 Métricas y Análisis

### Análisis de Costos

```python
# Por bot
for bot_id in range(1, 6):
    stats = repo.get_statistics_by_bot(bot_id)
    print(f"Bot {bot_id}: ${stats['total_cost']:.4f}")

# Por tipo
eval_cost = repo.get_cost_by_type(QueryType.EVALUATION)
reeval_cost = repo.get_cost_by_type(QueryType.REEVALUATION)
print(f"Evaluaciones: ${eval_cost:.4f}")
print(f"Reevaluaciones: ${reeval_cost:.4f}")
```

### Análisis de Eficiencia

```python
# Consultas por símbolo
symbols = ["EURUSD", "GBPUSD", "XAUUSD"]
for symbol in symbols:
    queries = repo.get_queries_by_symbol(symbol)
    print(f"{symbol}: {len(queries)} consultas")
```

### Historial de Decisiones

```python
# Ver decisiones de una operación
operation_id = 456
queries = repo.get_queries_by_operation_id(operation_id)

print(f"Historial de operación {operation_id}:")
for query in queries:
    print(f"  - {query.query_type.value}: {query.action_decided}")
    print(f"    Tokens: {query.tokens_total}, Costo: ${query.cost_usd:.4f}")
```

## 🚀 Ejemplo Completo

Ver: `examples/ia_query_repository_example.py`

Ejecutar:
```bash
python examples/ia_query_repository_example.py
```

## 📦 Dependencias

- Python 3.8+
- sqlite3 (incluido en Python)
- dataclasses (incluido en Python 3.7+)
- typing (incluido en Python 3.5+)

**Sin dependencias externas** ✅

## 🔐 Seguridad

- ✅ Validación de tipos y valores
- ✅ Manejo de excepciones robusto
- ✅ Prevención de SQL injection (uso de parámetros)
- ✅ Gestión de errores de BD

## 📝 Notas de Implementación

### Decisiones de Diseño

1. **operation_id nullable**: Permite crear consultas antes de la operación
2. **tokens_total calculado**: Se calcula automáticamente (input + output)
3. **Índices optimizados**: Para consultas frecuentes (operación, bot+ia)
4. **Timestamps automáticos**: SQLite gestiona created_at automáticamente
5. **Orden descendente**: Las consultas se retornan con más recientes primero

### Mejoras Futuras

- [ ] Agregar campo `model_version` para tracking de versiones de IA
- [ ] Implementar soft delete en lugar de DELETE
- [ ] Agregar índice en `created_at` para queries por fecha
- [ ] Implementar paginación para `get_all_queries()`
- [ ] Agregar filtros combinados (ej: bot + símbolo + fecha)

## 🔗 Referencias

- Ticket: [#49](https://github.com/DVARGAS117/Botrading/issues/49)
- Épica: [#10 - Persistencia y trazabilidad](https://github.com/DVARGAS117/Botrading/issues/10)
- Relacionado: T11 (tokens/costo), T32 (operaciones), T10 (prompt/IA)

## ✅ Estado del Ticket

- [x] Tests unitarios (33/33 passing)
- [x] Implementación completa
- [x] Ejemplo de uso
- [x] Documentación técnica
- [x] Validaciones robustas
- [x] Integración con otros módulos

**LISTO PARA PRODUCCIÓN** ✅

---

**Autor**: Sistema Botrading  
**Fecha**: 2025-11-15  
**Versión**: 1.0
