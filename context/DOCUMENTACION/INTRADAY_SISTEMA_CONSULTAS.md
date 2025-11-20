# Sistema de Consultas y Almacenamiento - Estrategia INTRADAY

## 📋 Información

- **Estrategia**: INTRADAY Gemini 3 Pro Bot 1
- **Bot ID**: 101
- **Módulo**: IAQueryRepository
- **Base de Datos**: `data/ia_queries.db`

## 🎯 Objetivo

Documentar cómo la estrategia INTRADAY utilizará el sistema de registro de consultas (`IAQueryRepository`) para almacenar cada interacción con Gemini 3 Pro, incluyendo:
- Hora de envío
- Tokens consumidos (input/output/total)
- Costo USD
- ID del chat/conversación
- Prompt completo enviado
- Respuesta completa recibida
- Decisión tomada

## 🏗️ Arquitectura del Sistema

### IAQueryRepository (T33)

El sistema de consultas ya está implementado y listo para usarse. Proporciona:

#### Modelo de Datos: IAQuery

```python
@dataclass
class IAQuery:
    id: Optional[int]              # ID autoincremental (asignado por BD)
    operation_id: Optional[int]    # FK a operaciones (NULL hasta que se abra)
    bot_id: int                    # 101 para INTRADAY Bot 1
    ia_id: int                     # ID de configuración de IA
    symbol: str                    # "EURUSD", "GBPUSD", etc.
    
    query_type: QueryType          # EVALUATION o REEVALUATION
    
    prompt: str                    # Prompt completo enviado (JSON con indicadores)
    response: str                  # Respuesta JSON de Gemini 3 Pro
    
    tokens_input: int              # Tokens del prompt
    tokens_output: int             # Tokens de la respuesta
    tokens_total: int              # Suma automática
    cost_usd: float                # Costo calculado según pricing
    
    action_decided: str            # "OPERAR", "NO_OPERAR", "MANTENER", "CERRAR"
    
    created_at: datetime           # Timestamp automático de la consulta
```

#### Funcionalidades Disponibles

1. **Crear consulta**: `create_query()`
2. **Consultar por ID**: `get_query_by_id()`
3. **Consultar por operación**: `get_queries_by_operation_id()`
4. **Consultar por bot**: `get_queries_by_bot(bot_id=101)`
5. **Consultar por símbolo**: `get_queries_by_symbol("EURUSD")`
6. **Consultar por tipo**: `get_queries_by_type(QueryType.EVALUATION)`
7. **Estadísticas**: `get_statistics()`, `get_statistics_by_bot()`
8. **Vincular a operación**: `update_operation_id(query_id, operation_id)`

## 🔄 Flujo de Consultas INTRADAY

### Fase 1: Consulta Inicial (EVALUATION)

```python
from pathlib import Path
from src.core.ia_query_repository import IAQueryRepository, QueryType
from src.bots.strategies.intraday.gemini_3_pro.bot_1.intraday_indicators import IntradayIndicatorCalculator

# 1. Calcular indicadores
indicator_calc = IntradayIndicatorCalculator(symbol="EURUSD")
packages = indicator_calc.get_full_intraday_packages()

# 2. Construir prompt (prepare_data_for_ai)
prompt_data = {
    "paquete_tactico": packages["paquete_tactico_m15"],
    "paquete_estrategico": packages["paquete_estrategico_d1"],
    "instrucciones": "Analiza oportunidad de entrada INTRADAY..."
}
prompt_json = json.dumps(prompt_data, indent=2)

# 3. Enviar a Gemini 3 Pro
gemini_response = gemini_client.query(
    prompt=prompt_json,
    thinking_level="HIGH",
    code_execution=True
)

# 4. Registrar consulta
ia_repo = IAQueryRepository(db_path=Path("data/ia_queries.db"))
query = ia_repo.create_query(
    bot_id=101,                           # INTRADAY Bot 1
    ia_id=1,                              # Gemini 3 Pro config ID
    symbol="EURUSD",
    query_type=QueryType.EVALUATION,      # Primera consulta
    prompt=prompt_json,                   # Prompt completo
    response=gemini_response.text,        # Respuesta completa
    tokens_input=gemini_response.usage_metadata.prompt_token_count,
    tokens_output=gemini_response.usage_metadata.candidates_token_count,
    cost_usd=calculate_cost(gemini_response.usage_metadata),
    action_decided="OPERAR",              # Parseado de la respuesta
    operation_id=None                     # Todavía no hay operación
)

print(f"✅ Consulta registrada: ID={query.id}")
print(f"   Timestamp: {query.created_at}")
print(f"   Tokens: {query.tokens_total}")
print(f"   Costo: ${query.cost_usd:.6f}")
```

### Fase 2: Abrir Operación y Vincular Consulta

```python
# 5. Si la decisión fue OPERAR, crear la operación
if query.action_decided == "OPERAR":
    # Abrir posición en MT5
    ticket = mt5_connector.open_position(...)
    
    # Registrar en OperationsRepository
    operation = operations_repo.create_operation(
        bot_id=101,
        symbol="EURUSD",
        ticket=ticket,
        ...
    )
    
    # 6. Vincular consulta a operación
    ia_repo.update_operation_id(query.id, operation.id)
    print(f"✅ Consulta {query.id} vinculada a operación {operation.id}")
```

### Fase 3: Actualización Táctica (cada 15 minutos)

```python
# 7. Calcular actualización táctica (solo nuevas velas M15)
last_query = ia_repo.get_queries_by_operation_id(operation.id)[0]
last_timestamp = last_query.created_at

# Obtener solo velas nuevas
tactical_update = indicator_calc.calculate_tactical_update(
    last_timestamp=last_timestamp,
    current_timestamp=datetime.now()
)

# 8. Construir prompt de actualización
update_prompt = {
    "tipo": "actualizacion_tactica",
    "velas_nuevas": tactical_update,
    "operacion_activa": {
        "ticket": operation.ticket,
        "entry": operation.price_open,
        "sl": operation.price_sl,
        "tp": operation.price_tp,
        "pips": calculate_current_pips(operation)
    },
    "instrucciones": "Evalúa si mantener, ajustar SL/TP o cerrar..."
}

# 9. Enviar y registrar
gemini_response = gemini_client.query(prompt=json.dumps(update_prompt))

reeval_query = ia_repo.create_query(
    bot_id=101,
    ia_id=1,
    symbol="EURUSD",
    query_type=QueryType.REEVALUATION,    # Actualización
    prompt=json.dumps(update_prompt),
    response=gemini_response.text,
    tokens_input=gemini_response.usage_metadata.prompt_token_count,
    tokens_output=gemini_response.usage_metadata.candidates_token_count,
    cost_usd=calculate_cost(gemini_response.usage_metadata),
    action_decided="MANTENER",            # Parseado
    operation_id=operation.id             # Ya vinculada
)

print(f"✅ Reevaluación registrada: ID={reeval_query.id}")
```

## 📊 Datos Almacenados

### Tabla: `consultas_ia`

Cada consulta registra:

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | INTEGER | ID autoincremental | `1`, `2`, `3`... |
| `operation_id` | INTEGER | FK a operaciones (nullable) | `456`, `NULL` |
| `bot_id` | INTEGER | ID del bot (101) | `101` |
| `ia_id` | INTEGER | Config de IA | `1` |
| `activo` | TEXT | Símbolo | `"EURUSD"` |
| `tipo_consulta` | TEXT | Tipo | `"evaluacion"`, `"reevaluacion"` |
| `prompt` | TEXT | Prompt JSON completo | `{"paquete_tactico": [...]}` |
| `respuesta` | TEXT | Respuesta JSON | `{"decision": "OPERAR", ...}` |
| `tokens_input` | INTEGER | Tokens del prompt | `2500` |
| `tokens_output` | INTEGER | Tokens de respuesta | `350` |
| `tokens_total` | INTEGER | Suma total | `2850` |
| `costo_usd` | REAL | Costo calculado | `0.02375` |
| `accion_decidida` | TEXT | Decisión | `"OPERAR"`, `"MANTENER"` |
| `created_at` | DATETIME | Timestamp | `2025-11-19 14:23:45.123456` |

### Índices Optimizados

```sql
-- Consultas por operación (más frecuente)
CREATE INDEX idx_operacion ON consultas_ia(operacion_id);

-- Consultas por bot + IA
CREATE INDEX idx_bot_ia ON consultas_ia(bot_id, ia_id);
```

## 🔍 Consultas Útiles para INTRADAY

### Historial de una Operación

```python
# Ver todas las consultas de una operación
operation_id = 456
queries = ia_repo.get_queries_by_operation_id(operation_id)

print(f"Historial de operación {operation_id}:")
for query in queries:
    print(f"\n[{query.created_at}] {query.query_type.value}")
    print(f"  Decisión: {query.action_decided}")
    print(f"  Tokens: {query.tokens_total}")
    print(f"  Costo: ${query.cost_usd:.6f}")
```

### Estadísticas del Bot INTRADAY

```python
# Estadísticas completas del bot 101
stats = ia_repo.get_statistics_by_bot(bot_id=101)

print(f"📊 Estadísticas Bot INTRADAY (101):")
print(f"   Total consultas: {stats['total_queries']}")
print(f"   Costo total: ${stats['total_cost']:.4f}")
print(f"   Tokens input: {stats['total_tokens_input']:,}")
print(f"   Tokens output: {stats['total_tokens_output']:,}")
print(f"   Tokens totales: {stats['total_tokens_total']:,}")
```

### Consultas por Símbolo

```python
# Ver todas las consultas de EURUSD
eurusd_queries = ia_repo.get_queries_by_symbol("EURUSD")

print(f"EURUSD: {len(eurusd_queries)} consultas")
for query in eurusd_queries[:5]:  # Últimas 5
    print(f"  - {query.created_at}: {query.action_decided}")
```

### Costo por Tipo de Consulta

```python
# Análisis de costos
eval_cost = ia_repo.get_cost_by_type(QueryType.EVALUATION)
reeval_cost = ia_repo.get_cost_by_type(QueryType.REEVALUATION)

print(f"💰 Costos por tipo:")
print(f"   Evaluaciones iniciales: ${eval_cost:.4f}")
print(f"   Reevaluaciones: ${reeval_cost:.4f}")
print(f"   Total: ${eval_cost + reeval_cost:.4f}")
```

## 🔗 Integración con Conversaciones (Chat ID)

### ConversationContext (T28)

El sistema de conversaciones (T28) gestiona el `conversation_id` para mantener contexto:

```python
from src.core.conversation_context import ConversationContext

# 1. Crear contexto de conversación
conv_context = ConversationContext(position_id=ticket)
conversation_id = conv_context.conversation_id  # "conv_pos123_abc456"

# 2. Asociar conversation_id al gemini_client
gemini_client.create_conversation(conversation_id)

# 3. Todas las consultas de esa operación usan el mismo conversation_id
# Esto permite a Gemini 3 Pro mantener contexto entre mensajes
```

### Relación: IAQuery ↔ ConversationID

Actualmente, el `conversation_id` NO se almacena en `consultas_ia`, pero podemos:

**Opción 1: Inferir desde operation_id**
```python
# El conversation_id se genera a partir del position_id (ticket)
# conversation_id = f"conv_pos{position.ticket}_{unique_id}"
# Por lo tanto, si tenemos operation_id → ticket → conversation_id
```

**Opción 2: Agregar columna (mejora futura)**
```sql
ALTER TABLE consultas_ia ADD COLUMN conversation_id TEXT;
CREATE INDEX idx_conversation ON consultas_ia(conversation_id);
```

## 📈 Análisis y Métricas

### Tracking de Eficiencia

```python
# Análisis de eficiencia de decisiones
queries = ia_repo.get_queries_by_bot(bot_id=101)

decisions = {}
for query in queries:
    action = query.action_decided
    decisions[action] = decisions.get(action, 0) + 1

print("Distribución de decisiones:")
for action, count in decisions.items():
    print(f"  {action}: {count} veces")
```

### Costo Promedio por Consulta

```python
stats = ia_repo.get_statistics_by_bot(bot_id=101)

if stats['total_queries'] > 0:
    avg_cost = stats['total_cost'] / stats['total_queries']
    avg_tokens = stats['total_tokens_total'] / stats['total_queries']
    
    print(f"Promedios por consulta:")
    print(f"  Costo: ${avg_cost:.6f}")
    print(f"  Tokens: {avg_tokens:.0f}")
```

### Análisis Temporal

```python
# Consultas por día
queries = ia_repo.get_all_queries()

by_date = {}
for query in queries:
    date = query.created_at.date()
    by_date[date] = by_date.get(date, 0) + 1

print("Consultas por día:")
for date in sorted(by_date.keys(), reverse=True):
    print(f"  {date}: {by_date[date]} consultas")
```

## 🛠️ Implementación en Strategy

### En IntradayBot1Strategy.prepare_data_for_ai()

```python
def prepare_data_for_ai(
    self,
    symbol: str,
    timeframe: str,
    last_query_timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Prepara datos para enviar a Gemini 3 Pro.
    
    Returns:
        Dict con:
        - prompt: str (JSON para Gemini)
        - metadata: Dict (para registro)
    """
    # 1. Calcular indicadores
    indicator_calc = IntradayIndicatorCalculator(symbol=symbol)
    
    if last_query_timestamp is None:
        # Primera consulta: paquete completo
        packages = indicator_calc.get_full_intraday_packages()
    else:
        # Actualización: solo velas nuevas
        tactical_update = indicator_calc.calculate_tactical_update(
            last_timestamp=last_query_timestamp,
            current_timestamp=datetime.now()
        )
        packages = {
            "paquete_tactico_m15": tactical_update,
            "paquete_estrategico_d1": None  # No se actualiza intraday
        }
    
    # 2. Construir prompt
    prompt_data = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "datos": packages,
        "instrucciones": self._get_instructions(last_query_timestamp)
    }
    
    return {
        "prompt": json.dumps(prompt_data, indent=2),
        "metadata": {
            "is_initial": last_query_timestamp is None,
            "symbol": symbol,
            "timestamp": datetime.now()
        }
    }
```

### En IntradayBot1Strategy.execute_cycle()

```python
def execute_cycle(self):
    """Ejecuta un ciclo completo de evaluación"""
    
    # 1. Preparar datos
    data = self.prepare_data_for_ai(
        symbol=self.config.symbol,
        timeframe="M15"
    )
    
    # 2. Consultar Gemini
    response = self.gemini_client.query(prompt=data["prompt"])
    
    # 3. Registrar consulta
    query = self.ia_repo.create_query(
        bot_id=self.config.bot_id,
        ia_id=1,
        symbol=self.config.symbol,
        query_type=QueryType.EVALUATION,
        prompt=data["prompt"],
        response=response.text,
        tokens_input=response.usage_metadata.prompt_token_count,
        tokens_output=response.usage_metadata.candidates_token_count,
        cost_usd=self._calculate_cost(response.usage_metadata),
        action_decided=self._extract_decision(response.text),
        operation_id=None
    )
    
    # 4. Procesar respuesta
    decision = self.parse_ai_response(response.text)
    
    if decision["action"] == "OPERAR":
        # Abrir operación y vincular
        operation = self._open_position(decision)
        self.ia_repo.update_operation_id(query.id, operation.id)
    
    return query
```

## 📝 Notas Importantes

### ✅ Ventajas del Sistema

1. **Trazabilidad completa**: Cada consulta registrada con timestamp
2. **Control de costos**: Tracking preciso de tokens y USD
3. **Historial de decisiones**: Auditoría de todas las acciones tomadas
4. **Análisis de eficiencia**: Métricas por bot, símbolo, tipo
5. **Debugging facilitado**: Prompt y respuesta completos guardados
6. **Optimización**: Identificar consultas costosas o ineficientes

### ⚠️ Consideraciones

1. **Almacenamiento**: Los prompts/respuestas pueden ocupar espacio (considerar limpieza periódica)
2. **Privacidad**: Las respuestas contienen datos de trading (proteger BD)
3. **Performance**: Los índices optimizan queries frecuentes
4. **Consistencia**: Siempre registrar ANTES de tomar acción

### 🔄 Patrón Recomendado

```python
# SIEMPRE:
# 1. Calcular indicadores
# 2. Construir prompt
# 3. Consultar Gemini
# 4. REGISTRAR en IAQueryRepository
# 5. Parsear respuesta
# 6. Ejecutar acción
# 7. Si se abrió operación → update_operation_id()
```

## 🚀 Próximos Pasos

- [ ] Implementar `calculate_tactical_update()` en IntradayIndicatorCalculator
- [ ] Integrar IAQueryRepository en `strategy.py`
- [ ] Agregar cálculo de costos según pricing Gemini 3 Pro
- [ ] Implementar `parse_ai_response()` con extracción de decisión
- [ ] Crear método `_extract_decision()` para obtener acción
- [ ] Agregar logging de cada consulta registrada
- [ ] Implementar limpieza automática de consultas antiguas (opcional)

## 🔗 Referencias

- **T33**: [Registro de consultas a IA](./T33_registro_consultas_ia.md)
- **T28**: [Contexto de conversación](./T28_contexto_conversacion.md)
- **T32**: [Repositorio de operaciones](./T32_repositorio_operaciones.md)
- **Pricing**: [GEMINI_PRICING.md](../../docs/GEMINI_PRICING.md)

---

**Autor**: Sistema Botrading  
**Fecha**: 2025-11-19  
**Versión**: 1.0
