# T40: Registro de Errores de Parsing de IA

## Estado
✅ **COMPLETADO** (2025-11-06)

## Resumen Ejecutivo
Implementación del **AIResponseParser**, un módulo robusto para parsear, validar y registrar respuestas JSON de la IA (Google Gemini). Este componente maneja decisiones de evaluación (OPERAR/NO_OPERAR) y reevaluación (MANTENER/ACTUALIZAR/CERRAR), validando estructura, tipos y lógica de negocio, registrando errores detallados cuando el parsing falla, y proporcionando estadísticas de errores para mejorar la robustez del sistema.

## Problema Identificado
Las respuestas de IA generativa (Gemini) pueden contener:
- **JSON malformado**: Sintaxis incorrecta, comas faltantes, comillas sin cerrar
- **Campos faltantes**: `accion` ausente, `direccion` no especificada
- **Valores inválidos**: `accion: "COMPRAR"` (debería ser "OPERAR")
- **Tipos incorrectos**: `stop_loss: "1.2300"` (string en lugar de float)
- **Lógica de negocio incorrecta**: SL > TP en operaciones BUY
- **Campos condicionales faltantes**: `precio_entrada` ausente en orden LIMIT

Sin manejo robusto de errores:
- Sistema crashea por JSON inválido
- Operaciones erróneas por validación débil
- Imposible diagnosticar problemas de IA
- No se pueden mejorar prompts de IA
- Pérdidas financieras por operaciones mal configuradas

## Arquitectura

### Componentes Principales

#### 1. **AIResponseParser**
Clase principal para parsear y validar respuestas de IA:

```python
from src.core.ai_response_parser import AIResponseParser

# Inicializar parser
parser = AIResponseParser()

# Parsear respuesta de evaluación
response = '''
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "tipo_orden": "MARKET",
  "stop_loss": 1.2300,
  "take_profit": 1.2500,
  "riesgo_porcentaje": 2.0,
  "razonamiento": "Tendencia alcista clara"
}
'''

result = parser.parse_evaluation(response)

if result.is_valid:
    print(f"Decisión: {result.decision_type}")
    print(f"Dirección: {result.direction}")
    print(f"SL: {result.stop_loss}, TP: {result.take_profit}")
else:
    print(f"Error: {result.error_message}")
```

#### 2. **Enums para Decisiones**

```python
from src.core.ai_response_parser import (
    AIDecisionType,   # OPERAR, NO_OPERAR, MANTENER, ACTUALIZAR, CERRAR
    AIDirection,      # BUY, SELL
    AIOrderType       # MARKET, LIMIT
)

# Todos los enums son case-insensitive
decision = AIDecisionType.from_string("operar")  # Funciona
direction = AIDirection.from_string("BUY")       # Funciona
order_type = AIOrderType.from_string("limit")    # Funciona
```

#### 3. **ParsedDecision** (Dataclass)
Resultado del parsing con toda la información:

```python
from src.core.ai_response_parser import ParsedDecision

# Decisión válida
valid_decision = ParsedDecision(
    is_valid=True,
    decision_type=AIDecisionType.OPERAR,
    direction=AIDirection.BUY,
    stop_loss=1.2300,
    take_profit=1.2500,
    risk_percentage=2.0
)

# Decisión inválida (con error)
invalid_decision = ParsedDecision(
    is_valid=False,
    error_type="json_decode_error",
    error_message="JSON malformado: coma faltante",
    raw_response="{accion: OPERAR invalid}"
)

# Convertir a diccionario
data = valid_decision.to_dict()
```

#### 4. **AIParsingError** (Excepción)
Excepción específica con información detallada:

```python
from src.core.ai_response_parser import AIParsingError

try:
    parser.parse_evaluation(invalid_json)
except AIParsingError as e:
    print(f"Tipo de error: {e.error_type}")
    print(f"Mensaje: {e.message}")
    print(f"Campo: {e.field_name}")
    print(f"Timestamp: {e.timestamp}")
    print(f"Response: {e.raw_response[:100]}")
```

### Flujo de Parsing con Registro de Errores

```
1. Bot recibe respuesta de IA
   │
2. Llamar a parse_evaluation() o parse_reevaluation()
   │
3. Parsing de JSON
   ├─ ✅ JSON válido → Continuar
   └─ ❌ JSON inválido → AIParsingError
       └─ Registrar error en historial
       └─ Lanzar excepción
   │
4. Validar campo 'accion'
   ├─ ✅ Campo presente y válido → Continuar
   └─ ❌ Campo faltante o inválido → AIParsingError
       └─ Registrar error en historial
       └─ Lanzar excepción
   │
5. Validar campos condicionales (según acción)
   ├─ OPERAR → Validar direccion, SL, TP, riesgo
   ├─ NO_OPERAR → Solo razonamiento
   ├─ ACTUALIZAR → Validar nuevo SL/TP
   └─ MANTENER/CERRAR → Solo razonamiento
   │
6. Validar tipos de campos
   ├─ stop_loss, take_profit → float
   ├─ riesgo_porcentaje → float
   └─ Cualquier error → AIParsingError + registro
   │
7. Validar lógica de negocio
   ├─ BUY: SL < Entry < TP
   ├─ SELL: SL > Entry > TP
   └─ Cualquier error → AIParsingError + registro
   │
8. Retornar ParsedDecision
   └─ is_valid=True con datos parseados
```

## Características Implementadas

### ✅ Parsing de Evaluación Inicial
- **parse_evaluation()**: Para decisiones OPERAR/NO_OPERAR
- **Validación completa**: Todos los campos requeridos
- **Lógica de negocio**: SL/TP coherentes con dirección

### ✅ Parsing de Reevaluación
- **parse_reevaluation()**: Para MANTENER/ACTUALIZAR/CERRAR
- **Campos opcionales**: nuevo_stop_loss y/o nuevo_take_profit
- **Flexibilidad**: Al menos uno de los dos debe estar presente

### ✅ Validación Multi-Nivel

**Nivel 1: JSON Syntax**
- Detecta JSON malformado
- Error: `json_decode_error`

**Nivel 2: Campos Requeridos**
- `accion` siempre requerido
- Campos condicionales según tipo de decisión
- Error: `missing_required_field` o `missing_conditional_field`

**Nivel 3: Valores Válidos**
- `accion` en ["OPERAR", "NO_OPERAR", ...]
- `direccion` en ["BUY", "SELL"]
- `tipo_orden` en ["MARKET", "LIMIT"]
- Error: `invalid_field_value`

**Nivel 4: Tipos de Datos**
- stop_loss, take_profit, riesgo_porcentaje → float
- enabled, valid flags → boolean
- Error: `invalid_field_type`

**Nivel 5: Lógica de Negocio**
- BUY: SL < Entry < TP
- SELL: SL > Entry > TP
- riesgo_porcentaje en rango 1-5%
- Error: `invalid_business_logic`

### ✅ Registro de Errores
- **Historial completo**: Todos los errores se registran
- **Información detallada**: Tipo, mensaje, campo, timestamp, response
- **get_error_history()**: Retorna lista completa de errores
- **get_error_statistics()**: Estadísticas agregadas por tipo

### ✅ Parsing Seguro (Safe Mode)
- **safe_parse_evaluation()**: No lanza excepciones
- **safe_parse_reevaluation()**: No lanza excepciones
- **Retorna ParsedDecision**: is_valid=False con información de error
- **Uso recomendado**: En loops donde se procesan múltiples respuestas

### ✅ Schema Personalizable
- **DEFAULT_SCHEMA**: Schema por defecto con reglas estándar
- **Constructor con schema**: Permite inyectar schema personalizado
- **Flexibilidad**: Adaptar validación sin cambiar código

## Casos de Uso

### 1. Parsear Decisión OPERAR (Caso Normal)
```python
from src.core.ai_response_parser import AIResponseParser

parser = AIResponseParser()

# Respuesta de IA
ia_response = '''
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "tipo_orden": "MARKET",
  "stop_loss": 1.2300,
  "take_profit": 1.2500,
  "riesgo_porcentaje": 2.0,
  "razonamiento": "Tendencia alcista confirmada"
}
'''

# Parsear
result = parser.parse_evaluation(ia_response)

if result.is_valid:
    # Usar decisión para abrir operación
    order_manager.send_order(
        symbol="EURUSD",
        direction=result.direction.value,  # "BUY"
        sl=result.stop_loss,
        tp=result.take_profit,
        risk=result.risk_percentage
    )
else:
    logger.error(f"Error de IA: {result.error_message}")
```

### 2. Parsear Decisión NO_OPERAR
```python
ia_response = '''
{
  "accion": "NO_OPERAR",
  "razonamiento": "Mercado lateral sin señales claras"
}
'''

result = parser.parse_evaluation(ia_response)

if result.is_valid:
    logger.info(f"IA decidió NO OPERAR: {result.reasoning}")
    # No hacer nada, esperar al siguiente ciclo
else:
    logger.error(f"Error: {result.error_message}")
```

### 3. Manejar Errores de Parsing
```python
# Respuesta de IA con JSON inválido
ia_response = '{ accion: OPERAR, invalid }'

try:
    result = parser.parse_evaluation(ia_response)
except AIParsingError as e:
    logger.error(f"Error de parsing: {e.error_type}")
    logger.error(f"Mensaje: {e.message}")
    logger.error(f"Timestamp: {e.timestamp}")
    
    # Registrar en base de datos para análisis
    db.save_parsing_error({
        "error_type": e.error_type,
        "message": e.message,
        "raw_response": e.raw_response,
        "timestamp": e.timestamp
    })
    
    # Continuar sin operar
    logger.info("Saltando ciclo debido a error de parsing")
```

### 4. Safe Parsing en Loops
```python
# Escenario: Procesar múltiples respuestas de IA
# No queremos que un error detenga todo el loop

ia_responses = [response1, response2, response3]  # De diferentes símbolos

for symbol, response in zip(symbols, ia_responses):
    # Safe parse: No lanza excepciones
    result = parser.safe_parse_evaluation(response)
    
    if result.is_valid:
        logger.info(f"{symbol}: {result.decision_type}")
        # Procesar decisión...
    else:
        logger.warning(f"{symbol}: Error de parsing - {result.error_message}")
        # Continuar con siguiente símbolo
        continue
```

### 5. Parsear Reevaluación ACTUALIZAR
```python
# Respuesta de IA para reevaluación de posición abierta
ia_response = '''
{
  "accion": "ACTUALIZAR",
  "nuevo_stop_loss": 1.2350,
  "nuevo_take_profit": 1.2550,
  "razonamiento": "Mover SL a breakeven"
}
'''

result = parser.parse_reevaluation(ia_response)

if result.is_valid and result.decision_type == AIDecisionType.ACTUALIZAR:
    # Modificar posición
    order_manager.modify_position(
        ticket=position.ticket,
        new_sl=result.new_stop_loss,
        new_tp=result.new_take_profit
    )
    logger.info(f"Posición actualizada: {result.reasoning}")
```

### 6. Análisis de Errores de IA
```python
# Escenario: Analizar qué tipos de errores comete la IA

# Procesar múltiples respuestas
for response in historical_responses:
    try:
        parser.parse_evaluation(response)
    except AIParsingError:
        pass  # Ya se registró en historial

# Obtener estadísticas
stats = parser.get_error_statistics()

print("=== ESTADÍSTICAS DE ERRORES DE IA ===")
print(f"Total de errores: {stats['total_errors']}")
print("\nPor tipo:")
for error_type, count in stats['by_type'].items():
    print(f"  {error_type}: {count}")

# Resultado ejemplo:
# Total de errores: 15
# Por tipo:
#   json_decode_error: 3
#   missing_required_field: 5
#   invalid_field_value: 2
#   invalid_business_logic: 5
```

### 7. Validar Lógica de Negocio en LIMIT Orders
```python
# BUY LIMIT con validación completa
ia_response = '''
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "tipo_orden": "LIMIT",
  "precio_entrada": 1.2400,
  "stop_loss": 1.2350,
  "take_profit": 1.2500,
  "riesgo_porcentaje": 1.5
}
'''

try:
    result = parser.parse_evaluation(ia_response)
    
    # Validación automática verifica:
    # - SL (1.2350) < Entry (1.2400) < TP (1.2500) ✓
    
    logger.info("✓ Lógica de negocio válida")
    # Proceder con orden LIMIT
    
except AIParsingError as e:
    if e.error_type == "invalid_business_logic":
        logger.error(f"IA configuró mal SL/TP: {e.message}")
        # Notificar para mejorar prompt de IA
```

### 8. Schema Personalizado para Testing
```python
# Escenario: Testing con riesgo máximo de 10% (en lugar de 5%)

custom_schema = {
    "required_fields": ["accion"],
    "valid_actions": ["OPERAR", "NO_OPERAR"],
    "risk_percentage_range": [1.0, 10.0],  # ← Customizado
    # ... resto del schema
}

parser = AIResponseParser(schema=custom_schema)

# Ahora acepta hasta 10% de riesgo
result = parser.parse_evaluation('''
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "stop_loss": 1.2000,
  "take_profit": 1.2800,
  "riesgo_porcentaje": 8.0
}
''')

assert result.is_valid  # Pasa con custom schema
```

## Testing

### Cobertura Completa (70+ tests)

#### Inicialización (3 tests)
- ✅ Con schema válido
- ✅ Sin schema (usa default)
- ✅ Con logger personalizado

#### Parsing de Evaluación (7 tests)
- ✅ OPERAR válido (Market y Limit)
- ✅ NO_OPERAR válido
- ✅ Campos opcionales (tipo_orden default a MARKET)
- ✅ Razonamiento incluido

#### Parsing de Reevaluación (7 tests)
- ✅ MANTENER válido
- ✅ ACTUALIZAR con ambos SL/TP
- ✅ ACTUALIZAR con solo SL
- ✅ ACTUALIZAR con solo TP
- ✅ CERRAR válido

#### Manejo de Errores (15 tests)
- ✅ JSON inválido
- ✅ Campo requerido faltante
- ✅ Acción inválida
- ✅ Dirección inválida
- ✅ Tipo de orden inválido
- ✅ Riesgo fuera de rango
- ✅ Campos condicionales faltantes
- ✅ Tipos de datos incorrectos

#### Validación de Lógica de Negocio (6 tests)
- ✅ BUY: SL debe ser < Entry
- ✅ BUY: TP debe ser > Entry
- ✅ SELL: SL debe ser > Entry
- ✅ SELL: TP debe ser < Entry
- ✅ Validación con orden MARKET
- ✅ Validación con orden LIMIT

#### Registro de Errores (5 tests)
- ✅ Error se registra en historial
- ✅ Timestamp incluido
- ✅ get_error_history() funciona
- ✅ get_error_statistics() calcula correctamente
- ✅ clear_error_history() limpia

#### Safe Parsing (4 tests)
- ✅ safe_parse_evaluation() no lanza excepción
- ✅ safe_parse_evaluation() retorna is_valid=False
- ✅ safe_parse_reevaluation() no lanza excepción
- ✅ safe_parse_reevaluation() retorna error info

#### Enums (9 tests)
- ✅ AIDecisionType valores correctos
- ✅ AIDirection valores correctos
- ✅ AIOrderType valores correctos
- ✅ from_string() conversiones
- ✅ Case-insensitive
- ✅ Errores en valores inválidos

#### ParsedDecision (4 tests)
- ✅ Inicialización válida
- ✅ Inicialización inválida con error
- ✅ to_dict() conversión
- ✅ Campos opcionales None

#### Edge Cases (10+ tests)
- ✅ String vacío
- ✅ JSON vacío {}
- ✅ Campos extra (aceptados)
- ✅ Limit sin precio_entrada (error)
- ✅ Actualizar sin ningún SL/TP (error)

### Ejemplo de Test Crítico
```python
def test_parse_evaluation_with_invalid_business_logic_buy():
    """
    Test crítico para T40: Validar lógica de negocio
    
    Para BUY: SL debe ser menor que Entry, TP debe ser mayor
    """
    parser = AIResponseParser()
    
    # BUY con SL por encima de Entry (inválido)
    response = '''
    {
      "accion": "OPERAR",
      "direccion": "BUY",
      "tipo_orden": "LIMIT",
      "precio_entrada": 1.2400,
      "stop_loss": 1.2450,
      "take_profit": 1.2500,
      "riesgo_porcentaje": 2.0
    }
    '''
    
    with pytest.raises(AIParsingError) as exc_info:
        parser.parse_evaluation(response)
    
    assert exc_info.value.error_type == "invalid_business_logic"
    assert "stop_loss" in exc_info.value.message.lower()
    
    # Verificar que el error se registró
    errors = parser.get_error_history()
    assert len(errors) == 1
    assert errors[0]["error_type"] == "invalid_business_logic"
```

## Integración con Otros Módulos

### ✅ BotLogger (T39)
- **Logging de errores**: Parser usa logger para registrar errores
- **Información estructurada**: Extra data con tipo de error y campo

### 🔄 Próximas Integraciones
- **IAConfigManager (T25)**: Usar parser para validar respuestas de Gemini
- **CycleScheduler (T01)**: Parser en cada ciclo de evaluación
- **Reevaluación (T26)**: Parser para decisiones de reevaluación
- **Métricas (T41)**: Estadísticas de errores en dashboard

## Decisiones de Diseño

### 1. **Excepciones vs Safe Mode**
**Decisión**: Ofrecer ambas opciones (parse_* y safe_parse_*)  
**Razón**:
- parse_*: Para control de flujo explícito con try/except
- safe_parse_*: Para loops donde un error no debe detener todo
- Flexibilidad: Usuario elige según caso de uso

### 2. **Registro Automático de Errores**
**Decisión**: Registrar todos los errores automáticamente en historial  
**Razón**:
- Análisis: Permite analizar qué errores comete la IA
- Debugging: Facilita encontrar patrones de errores
- Mejora continua: Identificar áreas para mejorar prompts

### 3. **Enums en Lugar de Strings**
**Decisión**: Usar enums (AIDecisionType, etc.) en lugar de strings  
**Razón**:
- Type safety: Evita typos
- Autocompletado: IDEs pueden sugerir valores
- Validación: Conversión automática valida valores

### 4. **Validación de Lógica de Negocio**
**Decisión**: Validar relación SL/Entry/TP en el parser  
**Razón**:
- Prevención: Detectar errores antes de enviar a MT5
- Centralización: Una sola validación para todos los bots
- Seguridad: Evitar operaciones mal configuradas

### 5. **Schema Customizable**
**Decisión**: Permitir inyectar schema personalizado  
**Razón**:
- Testing: Diferentes reglas en tests
- Flexibilidad: Adaptar a diferentes estrategias
- Evolución: Cambiar reglas sin cambiar código

### 6. **ParsedDecision con Todos los Campos**
**Decisión**: Un solo dataclass para todas las decisiones  
**Razón**:
- Simplicidad: Menos clases que gestionar
- Opcionalidad: Campos opcionales con None
- Uniformidad: API consistente

## Beneficios

### 🛡️ Prevención de Errores
- Detecta problemas antes de ejecutar operaciones
- Evita pérdidas por configuraciones incorrectas
- Validación multi-nivel exhaustiva

### 📊 Análisis de IA
- Historial completo de errores de parsing
- Estadísticas por tipo de error
- Identificación de problemas en prompts

### 🔧 Debugging Facilitado
- Mensajes de error descriptivos
- Campo específico que causó error
- Raw response incluida para análisis

### 🧪 Mejora Continua
- Identificar qué instrucciones la IA no entiende
- Iterar y mejorar prompts
- Reducir tasa de errores progresivamente

### 🔒 Seguridad Operacional
- No crashea por respuestas inválidas
- Safe mode para robustez
- Logging completo para auditoría

## Comandos Útiles

```powershell
# Ejecutar tests de AIResponseParser
python -m pytest tests/unit/test_ai_response_parser.py -v

# Ejecutar solo tests de errores
python -m pytest tests/unit/test_ai_response_parser.py -k "error" -v

# Ejecutar tests de validación de negocio
python -m pytest tests/unit/test_ai_response_parser.py -k "business_logic" -v

# Uso interactivo
python -c "
from src.core.ai_response_parser import AIResponseParser
parser = AIResponseParser()
response = '{\"accion\": \"NO_OPERAR\"}'
result = parser.safe_parse_evaluation(response)
print(f'Válido: {result.is_valid}')
print(f'Decisión: {result.decision_type}')
"
```

## Dependencias

### Runtime
- **Python 3.9+**
- **Módulos estándar**: `json`, `enum`, `dataclasses`, `datetime`, `typing`

### Módulos Internos
- `src.core.logger` (BotLogger) - opcional

### Testing
- `pytest >= 8.0`

## Archivos Creados

```
src/core/ai_response_parser.py              (600 líneas)
tests/unit/test_ai_response_parser.py       (1000+ líneas)
context/DOCUMENTACION/T40_errores_parsing_ia.md  (Este archivo)
config/ai_response_schema.example.json      (Schema ejemplo)
```

## Métricas

| Métrica | Valor |
|---------|-------|
| **Tests implementados** | 70+ |
| **Tests pasando** | 100% |
| **Cobertura** | ~95% |
| **Líneas de código** | 600 |
| **Líneas de tests** | 1000+ |
| **Niveles de validación** | 5 |
| **Tipos de error** | 6 |
| **Enums definidos** | 3 |

## Conclusión

✅ **T40 completado exitosamente** con parser robusto de respuestas IA:
- Validación multi-nivel (JSON, campos, tipos, lógica)
- Registro automático de errores con historial
- Safe mode para robustez en loops
- Enums para type safety
- 70+ tests cubriendo todos los casos
- Estadísticas de errores para mejora continua

**Beneficios Clave:**
- ✅ Prevención de operaciones erróneas
- ✅ Análisis de problemas de IA
- ✅ Debugging facilitado
- ✅ Mejora continua de prompts
- ✅ Seguridad operacional

**Próximos Pasos:**
- Integrar con IAConfigManager (T25)
- Usar en CycleScheduler (T01) para evaluación
- Implementar reevaluación (T26)
- Dashboard de estadísticas de errores

---

**Autor**: Sistema Botrading  
**Fecha**: 2025-11-06  
**Ticket**: T40 - Registro de errores de parsing de IA  
**Issue**: #56  
**Fase**: 1 (aunque técnicamente relacionado con Fase 2 - IA)  
**Tests**: 70+ ✅ | Cobertura: ~95%
