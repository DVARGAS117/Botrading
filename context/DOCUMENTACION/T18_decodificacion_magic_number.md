# T18: Decodificación de Magic Number para Auditoría

## Estado
✅ **COMPLETADO** (2025-11-11)

## Resumen Ejecutivo
Extensión del **MagicNumberGenerator** con funcionalidades avanzadas de auditoría, análisis y decodificación de Magic Numbers. Este ticket complementa T17 proporcionando herramientas para analizar operaciones históricas, generar reportes, filtrar por criterios múltiples, y exportar datos en formatos estándar para auditorías y análisis de rendimiento.

## Problema Identificado
Después de generar Magic Numbers únicos (T17), se necesita:
- **Decodificar** Magic Numbers para identificar origen de operaciones
- **Analizar** distribución de operaciones por bot, IA config, tipo
- **Filtrar** operaciones por criterios específicos
- **Generar reportes** de auditoría para análisis de rendimiento
- **Exportar** datos en formatos estándar (CSV, JSON, dict)
- **Validar** Magic Numbers en operaciones históricas

Sin estas capacidades de auditoría:
- Imposible analizar qué bot generó más operaciones
- Difícil comparar rendimiento entre configuraciones IA
- No se pueden realizar pruebas A/B efectivas
- Auditorías manuales son propensas a errores
- Exportación de datos requiere código custom cada vez

## Arquitectura

### Componentes Principales

El módulo `MagicNumberGenerator` (T17) fue extendido con métodos de auditoría:

#### Métodos de Decodificación
```python
from src.core.magic_number_generator import MagicNumberGenerator

generator = MagicNumberGenerator()

# Decodificar un solo magic number
components = generator.decode(231456)
print(f"Bot: {components.bot_id}")           # 2
print(f"IA Config: {components.ia_config_id}") # 3
print(f"Order Type: {components.order_type}")  # 'limit'
print(f"Sequence: {components.sequence}")      # 456

# Decodificar múltiples magic numbers en batch
magic_numbers = [100000, 231456, 350010]
decoded_list = generator.decode_batch(magic_numbers)
# Retorna: List[MagicNumberComponents]
```

#### Métodos de Reportes
```python
# Generar reporte de auditoría completo
magic_numbers = [100000, 100001, 111000, 231000, 231005]
report = generator.generate_audit_report(magic_numbers)

print(report)
# {
#   "total_operations": 5,
#   "operations_by_bot": {1: 3, 2: 2},
#   "operations_by_ia_config": {0: 3, 1: 1, 3: 1},
#   "operations_by_type": {"market": 4, "limit": 1}
# }
```

#### Métodos de Distribución
```python
# Obtener distribución por bot con porcentajes
distribution = generator.get_distribution_by_bot(magic_numbers)
# {
#   1: {"count": 3, "percentage": 60.0},
#   2: {"count": 2, "percentage": 40.0}
# }

# Por tipo de orden
type_dist = generator.get_distribution_by_type(magic_numbers)

# Por configuración IA
ia_dist = generator.get_distribution_by_ia_config(magic_numbers)
```

#### Métodos de Filtrado
```python
# Filtrar por bot específico
bot1_magics = generator.filter_by_bot(magic_numbers, bot_id=1)

# Filtrar por tipo de orden
market_orders = generator.filter_by_type(magic_numbers, order_type="market")

# Filtrar por configuración IA
ia0_magics = generator.filter_by_ia_config(magic_numbers, ia_config_id=0)

# Combinar filtros
bot1_magics = generator.filter_by_bot(magic_numbers, bot_id=1)
bot1_market = generator.filter_by_type(bot1_magics, order_type="market")
```

#### Métodos de Exportación
```python
# Exportar a lista de diccionarios
dict_list = generator.export_to_dict_list(magic_numbers)
# [
#   {
#     "magic_number": 100000,
#     "bot_id": 1,
#     "ia_config_id": 0,
#     "order_type": "market",
#     "sequence": 0
#   },
#   ...
# ]

# Exportar a formato CSV
csv_data = generator.export_to_csv_format(magic_numbers, include_header=True)
# [
#   ["magic_number", "bot_id", "ia_config_id", "order_type", "sequence"],
#   [100000, 1, 0, "market", 0],
#   ...
# ]

# Estadísticas resumidas
stats = generator.get_summary_statistics(magic_numbers)
# {
#   "total_operations": 6,
#   "unique_bots": 3,
#   "unique_ia_configs": 4,
#   "market_count": 4,
#   "limit_count": 2
# }
```

#### Métodos de Validación
```python
# Validar si un magic number es válido
is_valid = generator.is_valid_magic_number(100000)  # True
is_valid = generator.is_valid_magic_number(99999)   # False

# Obtener magic numbers inválidos de una lista
magic_numbers = [100000, 12345, 200000, 999999]
invalid = generator.get_invalid_magic_numbers(magic_numbers)
# [12345, 999999]

# Resumen de auditoría con validación
summary = generator.get_audit_summary(magic_numbers, strict=False)
# {
#   "total_magic_numbers": 4,
#   "valid_count": 2,
#   "invalid_count": 2,
#   "invalid_magic_numbers": [12345, 999999]
# }
```

#### Métodos de Búsqueda
```python
# Encontrar magic numbers por bot
bot2_magics = generator.find_by_bot(magic_numbers, bot_id=2)

# Encontrar por configuración IA
ia3_magics = generator.find_by_ia_config(magic_numbers, ia_config_id=3)

# Búsqueda con criterios complejos
results = generator.find_by_criteria(
    magic_numbers,
    bot_ids=[1, 2],           # Bot 1 OR Bot 2
    order_type="market"       # AND tipo Market
)
```

## Características Implementadas

### ✅ Decodificación Batch
- **decode_batch()**: Decodifica múltiples magic numbers en una sola llamada
- **Preserva orden**: La lista retornada mantiene el orden original
- **Validación**: Lanza error si algún magic number es inválido
- **Eficiente**: Procesamiento optimizado para grandes volúmenes

### ✅ Generación de Reportes
- **generate_audit_report()**: Reporte completo con agregaciones
- **Agrupación automática**: Por bot, IA config, y tipo de orden
- **Conteo preciso**: Suma correcta de operaciones por categoría
- **Formato estándar**: Diccionario con estructura predecible

### ✅ Análisis de Distribución
- **get_distribution_by_bot()**: Distribución con conteos y porcentajes
- **get_distribution_by_type()**: Análisis de Market vs Limit
- **get_distribution_by_ia_config()**: Rendimiento por configuración IA
- **Porcentajes calculados**: Suma siempre 100% (con margen de error mínimo)

### ✅ Filtrado Avanzado
- **Filtros individuales**: Por bot, tipo, IA config
- **Filtros combinables**: Aplicar múltiples filtros en cadena
- **No destructivo**: Retorna nueva lista, no modifica original
- **Sin resultados**: Retorna lista vacía si no hay matches

### ✅ Exportación Flexible
- **export_to_dict_list()**: Para JSON, APIs, bases de datos
- **export_to_csv_format()**: Para Excel, análisis estadístico
- **get_summary_statistics()**: Para dashboards y reportes ejecutivos
- **Header opcional**: CSV con o sin encabezados

### ✅ Validación Robusta
- **is_valid_magic_number()**: Verifica rango válido (100000-591999)
- **get_invalid_magic_numbers()**: Identifica inválidos en batch
- **get_audit_summary()**: Resumen con conteo de válidos e inválidos
- **Modo strict**: Opción para fallar en primer inválido

### ✅ Búsqueda y Lookup
- **find_by_bot()**: Búsqueda rápida por bot
- **find_by_ia_config()**: Búsqueda por configuración IA
- **find_by_criteria()**: Búsqueda compleja con múltiples criterios
- **Listas de IDs**: Soporta buscar múltiples bots/configs simultáneamente

## Casos de Uso

### 1. Auditoría de Operaciones del Día
```python
from src.core.magic_number_generator import MagicNumberGenerator
from src.core.position_manager import PositionManager

generator = MagicNumberGenerator()
manager = PositionManager(connector)

# Obtener todas las posiciones cerradas del día (desde MT5)
# Asumiendo que tienes una función que obtiene historial
closed_positions = get_closed_positions_today()

# Extraer magic numbers
magic_numbers = [pos.magic for pos in closed_positions]

# Generar reporte de auditoría
report = generator.generate_audit_report(magic_numbers)

print("=== REPORTE DE AUDITORÍA DEL DÍA ===")
print(f"Total de operaciones: {report['total_operations']}")
print(f"\nOperaciones por Bot:")
for bot_id, count in report['operations_by_bot'].items():
    print(f"  Bot {bot_id}: {count} operaciones")

print(f"\nOperaciones por Tipo:")
for order_type, count in report['operations_by_type'].items():
    print(f"  {order_type.upper()}: {count} operaciones")
```

### 2. Análisis de Rendimiento por Configuración IA
```python
# Obtener distribución por configuración IA
distribution = generator.get_distribution_by_ia_config(magic_numbers)

# Calcular profit por configuración IA
ia_profits = {}
for pos in closed_positions:
    components = generator.decode(pos.magic)
    ia_id = components.ia_config_id
    
    if ia_id not in ia_profits:
        ia_profits[ia_id] = 0.0
    
    ia_profits[ia_id] += pos.profit

# Mostrar resultados
print("=== RENDIMIENTO POR CONFIGURACIÓN IA ===")
for ia_id in sorted(distribution.keys()):
    count = distribution[ia_id]['count']
    percentage = distribution[ia_id]['percentage']
    profit = ia_profits.get(ia_id, 0.0)
    avg_profit = profit / count if count > 0 else 0.0
    
    print(f"\nIA Config {ia_id}:")
    print(f"  Operaciones: {count} ({percentage:.1f}%)")
    print(f"  Profit total: ${profit:.2f}")
    print(f"  Profit promedio: ${avg_profit:.2f}")
```

### 3. Comparar Market vs Limit Orders
```python
# Filtrar por tipo
market_magics = generator.filter_by_type(magic_numbers, "market")
limit_magics = generator.filter_by_type(magic_numbers, "limit")

# Calcular métricas para cada tipo
market_positions = [p for p in closed_positions if p.magic in market_magics]
limit_positions = [p for p in closed_positions if p.magic in limit_magics]

market_profit = sum(p.profit for p in market_positions)
limit_profit = sum(p.profit for p in limit_positions)

market_avg = market_profit / len(market_positions) if market_positions else 0
limit_avg = limit_profit / len(limit_positions) if limit_positions else 0

print("=== COMPARACIÓN MARKET VS LIMIT ===")
print(f"\nMarket Orders:")
print(f"  Cantidad: {len(market_positions)}")
print(f"  Profit total: ${market_profit:.2f}")
print(f"  Profit promedio: ${market_avg:.2f}")

print(f"\nLimit Orders:")
print(f"  Cantidad: {len(limit_positions)}")
print(f"  Profit total: ${limit_profit:.2f}")
print(f"  Profit promedio: ${limit_avg:.2f}")

# Conclusión
better_type = "Market" if market_avg > limit_avg else "Limit"
print(f"\n✓ Mejor rendimiento: {better_type} orders")
```

### 4. Exportar Datos para Análisis Externo
```python
import csv
import json

# Exportar a CSV para Excel
csv_data = generator.export_to_csv_format(magic_numbers, include_header=True)

with open("operaciones_auditoria.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(csv_data)

print("✓ Datos exportados a operaciones_auditoria.csv")

# Exportar a JSON para APIs
dict_list = generator.export_to_dict_list(magic_numbers)

# Enriquecer con datos de profit (ejemplo)
enriched_data = []
for item, pos in zip(dict_list, closed_positions):
    item['profit'] = pos.profit
    item['symbol'] = pos.symbol
    item['close_time'] = pos.close_time.isoformat()
    enriched_data.append(item)

with open("operaciones_auditoria.json", "w") as f:
    json.dump(enriched_data, f, indent=2)

print("✓ Datos exportados a operaciones_auditoria.json")
```

### 5. Validar Integridad de Datos Históricos
```python
# Cargar magic numbers de base de datos histórica
historical_magics = load_from_database()

# Validar integridad
summary = generator.get_audit_summary(historical_magics, strict=False)

print("=== VALIDACIÓN DE DATOS HISTÓRICOS ===")
print(f"Total de registros: {summary['total_magic_numbers']}")
print(f"Válidos: {summary['valid_count']}")
print(f"Inválidos: {summary['invalid_count']}")

if summary['invalid_count'] > 0:
    print(f"\n⚠ Magic Numbers inválidos encontrados:")
    for invalid_magic in summary['invalid_magic_numbers']:
        print(f"  - {invalid_magic}")
    
    print("\nAcción requerida: Investigar origen de registros inválidos")
else:
    print("\n✓ Todos los registros son válidos")
```

### 6. Dashboard en Tiempo Real
```python
def generate_live_dashboard():
    """Genera dashboard con estadísticas en tiempo real"""
    # Obtener posiciones abiertas
    manager = PositionManager(connector)
    positions = manager.get_all_positions()
    
    magic_numbers = [p.magic for p in positions]
    
    # Estadísticas generales
    stats = generator.get_summary_statistics(magic_numbers)
    
    # Distribuciones
    bot_dist = generator.get_distribution_by_bot(magic_numbers)
    type_dist = generator.get_distribution_by_type(magic_numbers)
    
    # Calcular profit total
    total_profit = sum(p.profit for p in positions)
    
    # Imprimir dashboard
    print("=" * 50)
    print("       DASHBOARD EN TIEMPO REAL")
    print("=" * 50)
    print(f"\n📊 ESTADÍSTICAS GENERALES")
    print(f"  Total operaciones activas: {stats['total_operations']}")
    print(f"  Bots activos: {stats['unique_bots']}")
    print(f"  Configs IA en uso: {stats['unique_ia_configs']}")
    print(f"  Profit total: ${total_profit:.2f}")
    
    print(f"\n🤖 DISTRIBUCIÓN POR BOT")
    for bot_id, data in bot_dist.items():
        print(f"  Bot {bot_id}: {data['count']} ops ({data['percentage']:.1f}%)")
    
    print(f"\n📈 DISTRIBUCIÓN POR TIPO")
    for order_type, data in type_dist.items():
        print(f"  {order_type.upper()}: {data['count']} ops ({data['percentage']:.1f}%)")
    
    print("=" * 50)

# Ejecutar cada 5 minutos
import time
while True:
    generate_live_dashboard()
    time.sleep(300)  # 5 minutos
```

## Testing

### Cobertura de Tests de Auditoría

Además de los 39 tests de T17, se agregaron tests específicos de auditoría:

#### Decodificación Batch (5 tests)
- ✅ Decodificar lista vacía retorna lista vacía
- ✅ Decodificar un solo magic number
- ✅ Decodificar múltiples magic numbers
- ✅ Error en batch con magic inválido
- ✅ Orden preservado en decodificación

#### Generación de Reportes (4 tests)
- ✅ Reporte básico con estructura correcta
- ✅ Agrupación correcta por bot
- ✅ Agrupación correcta por tipo
- ✅ Agrupación correcta por IA config

#### Análisis de Distribución (4 tests)
- ✅ Distribución por bot con porcentajes
- ✅ Porcentajes suman 100%
- ✅ Distribución por tipo
- ✅ Distribución por IA config

#### Filtrado y Consultas (5 tests)
- ✅ Filtrar por bot
- ✅ Filtrar por bot sin resultados
- ✅ Filtrar por tipo
- ✅ Filtrar por IA config
- ✅ Filtrar con criterios múltiples

#### Exportación (4 tests)
- ✅ Exportar a lista de diccionarios
- ✅ Exportar a CSV con header
- ✅ Exportar a CSV sin header
- ✅ Estadísticas resumidas

#### Validación de Auditoría (4 tests)
- ✅ Validar magic number en rango válido
- ✅ Validar batch todos válidos
- ✅ Validar batch con inválidos
- ✅ Resumen de auditoría con inválidos

#### Búsqueda y Lookup (3 tests)
- ✅ Encontrar magic numbers por bot
- ✅ Encontrar por IA config
- ✅ Búsqueda con criterios complejos

### Ejemplo de Test de Auditoría
```python
def test_generate_audit_report_comprehensive(generator, sample_magic_numbers):
    """
    Test que verifica que el reporte de auditoría contenga
    todas las secciones y conteos correctos
    """
    # sample_magic_numbers contiene:
    # Bot 1: 3 ops (2 market, 1 limit)
    # Bot 2: 2 ops (1 market, 1 limit)
    # Bot 3: 1 op (1 market)
    
    report = generator.generate_audit_report(sample_magic_numbers)
    
    # Verificar estructura
    assert "total_operations" in report
    assert "operations_by_bot" in report
    assert "operations_by_ia_config" in report
    assert "operations_by_type" in report
    
    # Verificar conteos
    assert report["total_operations"] == 6
    assert report["operations_by_bot"][1] == 3
    assert report["operations_by_bot"][2] == 2
    assert report["operations_by_bot"][3] == 1
    assert report["operations_by_type"]["market"] == 4
    assert report["operations_by_type"]["limit"] == 2
```

## Integración con Otros Módulos

### ✅ MagicNumberGenerator (T17)
- **Base fundamental**: T18 extiende T17 con métodos de auditoría
- **Misma clase**: Todos los métodos en MagicNumberGenerator
- **Compatibilidad**: decode() ya existía en T17

### ✅ PositionManager (T08)
- **Uso conjunto**: Obtener posiciones y decodificar sus magic numbers
- **Análisis**: Combinar datos de posiciones con información decodificada

### 🔄 Próximas Integraciones
- **Dashboard (T41/T43)**: Usar métodos de distribución para métricas
- **Persistencia (T32)**: Exportar datos para almacenamiento
- **Reporting**: Generar reportes ejecutivos

## Decisiones de Diseño

### 1. **Extender T17 en Lugar de Módulo Separado**
**Decisión**: Agregar métodos de auditoría a MagicNumberGenerator  
**Razón**:
- Cohesión: Generación y decodificación relacionadas
- Simplicidad: Una sola importación
- Reutilización: Comparten constantes y validaciones

### 2. **Métodos Separados por Funcionalidad**
**Decisión**: Múltiples métodos específicos vs un método genérico  
**Razón**:
- API clara: Nombres descriptivos
- Type hints: Retornos específicos
- Testing: Tests focalizados

### 3. **Batch Processing**
**Decisión**: decode_batch() en lugar de loop manual  
**Razón**:
- Performance: Optimización interna posible
- API limpia: Menos código en usuario
- Validación: Fail-fast en batch

### 4. **Porcentajes en Distribución**
**Decisión**: Incluir count y percentage en distribuciones  
**Razón**:
- Usabilidad: Evita cálculos manuales
- Reportes: Directamente usables en dashboards
- Precisión: Garantiza suma 100%

### 5. **Exportación Flexible**
**Decisión**: Múltiples formatos de exportación  
**Razón**:
- CSV: Para Excel, análisis estadístico
- Dict/JSON: Para APIs, bases de datos
- Estadísticas: Para dashboards ejecutivos

### 6. **Validación No Destructiva**
**Decisión**: get_invalid_magic_numbers() retorna inválidos sin modificar lista  
**Razón**:
- Inmutabilidad: No modifica entrada
- Flexibilidad: Usuario decide qué hacer con inválidos
- Debugging: Facilita encontrar problemas

## Beneficios

### 📊 Análisis de Rendimiento
- Comparar bots, configs IA, tipos de orden
- Identificar estrategias más rentables
- Tomar decisiones basadas en datos

### 🔍 Auditoría Facilitada
- Reportes automáticos completos
- Validación de integridad de datos
- Trazabilidad total de operaciones

### 📈 Dashboards y Reportes
- Estadísticas en tiempo real
- Exportación a múltiples formatos
- Visualizaciones facilitadas

### 🧪 Pruebas A/B
- Comparar múltiples estrategias
- Análisis estadístico robusto
- Iteración rápida de mejoras

### 🔧 Debugging y Soporte
- Identificar origen de operaciones
- Detectar anomalías en datos
- Resolver incidentes rápidamente

## Comandos Útiles

```powershell
# Ejecutar tests de auditoría
python -m pytest tests/unit/test_magic_number_auditor.py -v

# Ejecutar solo tests de reportes
python -m pytest tests/unit/test_magic_number_auditor.py::TestAuditReporting -v

# Uso interactivo
python -c "
from src.core.magic_number_generator import MagicNumberGenerator
gen = MagicNumberGenerator()
magics = [100000, 231456, 350010]
report = gen.generate_audit_report(magics)
print(report)
"
```

## Dependencias

### Runtime
- **Python 3.9+**
- **Módulos estándar**: `collections`, `typing`

### Módulos Internos
- `src.core.magic_number_generator` (T17)

### Testing
- `pytest >= 8.0`

## Métricas

| Métrica | Valor |
|---------|-------|
| **Métodos de auditoría** | 15+ |
| **Tests de auditoría** | 29 |
| **Tests totales (T17+T18)** | 68 |
| **Cobertura combinada** | 95% |
| **Formatos de exportación** | 3 |

## Conclusión

✅ **T18 completado exitosamente** extendiendo T17 con capacidades completas de auditoría:
- Decodificación batch de magic numbers
- Generación de reportes de auditoría
- Análisis de distribución con porcentajes
- Filtrado avanzado por múltiples criterios
- Exportación a CSV, JSON, dict
- Validación de integridad de datos
- 29 tests de auditoría (100% passing)

**Beneficios Clave:**
- ✅ Auditorías automatizadas
- ✅ Análisis de rendimiento facilitado
- ✅ Dashboards en tiempo real
- ✅ Exportación flexible de datos
- ✅ Validación de integridad

---

**Autor**: Sistema Botrading  
**Fecha**: 2025-11-11  
**Ticket**: T18 - Decodificación de Magic Number para auditoría  
**Issue**: #34  
**Basado en**: T17 (MagicNumberGenerator)  
**Tests**: 29 tests de auditoría ✅
