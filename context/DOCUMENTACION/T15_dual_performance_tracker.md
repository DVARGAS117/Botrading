# T15 - DualPerformanceTracker: Registro y Comparación Market vs Limit

**Ticket:** #31  
**Fase:** 2  
**Prioridad:** P1  
**Épica:** 4 - Dual Market/Limit  
**Autor:** Sistema Botrading  
**Fecha:** 2025-11-13

---

## 📋 Descripción General

El **DualPerformanceTracker** es un módulo crítico para el análisis comparativo de desempeño entre órdenes **Market** y **Limit** en el sistema de trading automatizado. Permite registrar, comparar y analizar el rendimiento de ambos tipos de órdenes para extraer conclusiones de efectividad por bot y activo.

### Funcionalidades Principales

✅ **Registro de Performance:** Almacena P/L, tasas de activación y métricas de cada orden  
✅ **Comparación por Operación:** Compara pares individuales Market/Limit  
✅ **Comparación Diaria:** Consolida métricas diarias por bot  
✅ **Tasas de Activación:** Especialmente importante para órdenes Limit  
✅ **Métricas Agregadas:** Análisis por símbolo, bot y período  
✅ **Persistencia:** Base de datos SQLite para trazabilidad completa

---

## 🎯 Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Registrar y comparar desempeño Market vs Limit
  Dado que existen resultados P/L para ambos tipos de orden
  Cuando se consolidan métricas por operación y por día
  Entonces queda disponible la comparación de P/L y activación entre Market y Limit
```

**Estado:** ✅ **COMPLETADO** - Todas las pruebas unitarias pasaron (29/29)

---

## 🏗️ Arquitectura

### Estructura de Clases

```
DualPerformanceTracker
├── PerformanceRecord (dataclass)
│   ├── Atributos: symbol, bot_id, order_type, magic_number, etc.
│   ├── validate()
│   └── to_dict()
│
├── OperationPerformance (dataclass)
│   ├── Comparación de un par Market/Limit
│   └── Calcula better_performer automáticamente
│
└── DailyPerformanceComparison (dataclass)
    ├── Métricas consolidadas diarias
    └── Calcula tasas de activación y promedios
```

### Flujo de Datos

```
┌─────────────────┐
│ Dual Order      │
│ Manager (T14)   │
└────────┬────────┘
         │ Envía órdenes Market + Limit
         ▼
┌─────────────────┐
│   MT5 Broker    │
└────────┬────────┘
         │ Ejecuta/Cierra órdenes
         ▼
┌─────────────────┐
│ Performance     │◄─── Registra P/L y estado
│ Tracker (T15)   │
└────────┬────────┘
         │
         ├─► Comparación por operación
         ├─► Comparación diaria
         └─► Métricas agregadas
```

---

## 📊 Base de Datos

### Tabla: `dual_performance`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER | Primary Key (auto-increment) |
| `symbol` | TEXT | Símbolo del instrumento (ej: "EURUSD") |
| `bot_id` | INTEGER | ID del bot (1-5) |
| `order_type` | TEXT | "market" o "limit" |
| `magic_number` | INTEGER | Magic Number único (UNIQUE) |
| `open_time` | TEXT | Timestamp de apertura (ISO) |
| `close_time` | TEXT | Timestamp de cierre (NULL si no cerró) |
| `entry_price` | REAL | Precio de entrada |
| `exit_price` | REAL | Precio de salida (NULL si no cerró) |
| `lot_size` | REAL | Tamaño del lote |
| `profit_loss` | REAL | Ganancia/Pérdida monetaria |
| `is_winner` | INTEGER | 1=ganó, 0=perdió |
| `activation_status` | TEXT | "activated", "not_activated", "pending" |
| `created_at` | TEXT | Timestamp de registro |

### Índices

```sql
-- Por bot y fecha (consultas diarias)
CREATE INDEX idx_dual_perf_bot_date ON dual_performance(bot_id, open_time);

-- Por símbolo (análisis por activo)
CREATE INDEX idx_dual_perf_symbol ON dual_performance(symbol);

-- Por Magic Number (búsquedas rápidas)
CREATE INDEX idx_dual_perf_magic ON dual_performance(magic_number);

-- Por tipo de orden
CREATE INDEX idx_dual_perf_order_type ON dual_performance(order_type);
```

---

## 🔧 API del Módulo

### 1. Inicialización

```python
from src.core.dual_performance_tracker import DualPerformanceTracker

# Con ruta por defecto
tracker = DualPerformanceTracker()

# Con ruta personalizada
tracker = DualPerformanceTracker(db_path="data/custom_db.db")
```

### 2. Registro de Performance

```python
from src.core.dual_performance_tracker import PerformanceRecord
from datetime import datetime

# Crear record de Market
market_record = PerformanceRecord(
    symbol="EURUSD",
    bot_id=1,
    order_type="market",
    magic_number=101000,
    open_time=datetime(2025, 11, 13, 10, 0, 0),
    close_time=datetime(2025, 11, 13, 14, 0, 0),
    entry_price=1.1000,
    exit_price=1.1050,
    lot_size=0.1,
    profit_loss=50.0,
    is_winner=True,
    activation_status="activated"
)

# Registrar
tracker.register_performance(market_record)
```

### 3. Comparación por Operación

```python
# Comparar un par Market/Limit
comparison = tracker.compare_operation_performance(
    market_magic=101000,
    limit_magic=101001
)

print(f"Market P/L: ${comparison.market_pl}")
print(f"Limit P/L: ${comparison.limit_pl}")
print(f"Winner: {comparison.better_performer}")
```

### 4. Comparación Diaria

```python
from datetime import date

# Comparar performance diaria del Bot 1
daily = tracker.compare_daily_performance(
    bot_id=1,
    target_date=date(2025, 11, 13)
)

print(f"Market total P/L: ${daily.market_total_pl}")
print(f"Limit total P/L: ${daily.limit_total_pl}")
print(f"Market activation rate: {daily.market_activation_rate:.1%}")
print(f"Limit activation rate: {daily.limit_activation_rate:.1%}")
```

### 5. Métricas Agregadas

```python
# Obtener métricas por símbolo
metrics = tracker.get_aggregated_metrics(
    group_by="symbol",
    start_date=date(2025, 11, 1),
    end_date=date(2025, 11, 30)
)

for symbol, data in metrics.items():
    print(f"{symbol}:")
    print(f"  Total P/L: ${data['total_pl']}")
    print(f"  Win rate: {data['win_rate']:.1%}")
    print(f"  Activation rate: {data['activation_rate']:.1%}")
```

---

## 📈 Métricas Clave

### Tasa de Activación

**Fórmula:**
```
Activation Rate = (Órdenes Activadas / Total Órdenes) × 100
```

**Importancia:**
- **Market:** Siempre 100% (se ejecutan inmediatamente)
- **Limit:** Varía según condiciones de mercado
- **Análisis:** Una tasa baja de activación Limit puede indicar precios límite muy agresivos

### Comparación de P/L

**Métricas:**
- **Total P/L:** Suma de todas las ganancias/pérdidas
- **Average P/L:** Promedio por operación activada
- **Win Rate:** Porcentaje de operaciones ganadoras
- **Profit Factor:** (Total Ganancias / Total Pérdidas)

### Better Performer

**Criterio:**
```python
if market_pl > limit_pl:
    better_performer = "market"
elif limit_pl > market_pl:
    better_performer = "limit"
else:
    better_performer = "tie"
```

---

## 🔍 Casos de Uso

### Caso 1: Ambas Órdenes Activadas y Ganadoras

```python
# Market: +$50
# Limit: +$50
# Resultado: TIE (mismo rendimiento)
```

**Análisis:** Ambas estrategias fueron igualmente efectivas.

### Caso 2: Market Ganadora, Limit No Activada

```python
# Market: +$50 (activada)
# Limit: $0 (no activada)
# Resultado: Market es mejor
```

**Análisis:** El precio límite era muy agresivo y nunca se alcanzó.

### Caso 3: Market Perdedora, Limit Ganadora

```python
# Market: -$50 (activada inmediatamente en mal momento)
# Limit: +$60 (activada con mejor precio)
# Resultado: Limit es mejor
```

**Análisis:** Esperar por el precio límite mejoró el resultado.

### Caso 4: Ambas Perdedoras pero Limit Perdió Menos

```python
# Market: -$80
# Limit: -$40 (entrada con mejor precio)
# Resultado: Limit es mejor (menor pérdida)
```

**Análisis:** El precio límite ayudó a reducir la pérdida.

---

## ⚡ Integración con Otros Módulos

### Con DualOrderManager (T14)

```python
from src.core.dual_order_manager import DualOrderManager, DualOrderRequest
from src.core.dual_performance_tracker import DualPerformanceTracker, PerformanceRecord

# 1. Abrir órdenes duales
dual_manager = DualOrderManager(...)
result = dual_manager.open_dual_orders(request)

# 2. Almacenar magic numbers
market_magic = result.market_magic
limit_magic = result.limit_magic

# 3. Al cerrar, registrar performance
tracker = DualPerformanceTracker()

market_record = PerformanceRecord(
    magic_number=market_magic,
    # ... datos de cierre
)
tracker.register_performance(market_record)
```

### Con DailyMetrics (T34)

```python
from src.core.daily_metrics import DailyMetricsCalculator
from src.core.dual_performance_tracker import DualPerformanceTracker

# El DualPerformanceTracker alimenta métricas diarias
tracker = DualPerformanceTracker()
daily_comp = tracker.compare_daily_performance(bot_id=1, target_date=today)

# Usar en consolidado general
metrics_calc = DailyMetricsCalculator()
# ... integrar datos de dual performance
```

---

## 🧪 Testing

### Cobertura de Pruebas

```
29 Tests Unitarios - 100% PASSED
├── Inicialización (3 tests)
├── PerformanceRecord (5 tests)
├── Registro de Performance (5 tests)
├── Comparación por Operación (3 tests)
├── Comparación Diaria (4 tests)
├── Métricas Agregadas (3 tests)
├── Persistencia (2 tests)
├── Edge Cases (3 tests)
└── Criterios de Aceptación (1 test)
```

### Ejecutar Tests

```bash
# Todos los tests del módulo
pytest tests/unit/test_dual_performance_tracker.py -v

# Con cobertura
pytest tests/unit/test_dual_performance_tracker.py --cov=src.core.dual_performance_tracker

# Solo un test específico
pytest tests/unit/test_dual_performance_tracker.py::TestAcceptanceCriteria::test_acceptance_criteria_main_scenario
```

---

## 📝 Ejemplos Completos

Ver: `examples/dual_performance_tracker_example.py`

**Incluye:**
1. Registro básico Market/Limit
2. Límit no activada
3. Comparación diaria con múltiples operaciones
4. Métricas agregadas por símbolo
5. Integración completa con DualOrderManager

**Ejecutar:**
```bash
python examples/dual_performance_tracker_example.py
```

---

## 🔒 Validaciones y Excepciones

### Validaciones

✅ `symbol` no puede estar vacío  
✅ `order_type` debe ser "market" o "limit"  
✅ `activation_status` debe ser "activated", "not_activated" o "pending"  
✅ `bot_id` debe estar entre 1 y 5  
✅ `magic_number` debe ser único  
✅ `lot_size` debe ser mayor a 0

### Excepciones

```python
# Excepción base
DualPerformanceTrackerError

# Datos inválidos
InvalidPerformanceDataError

# Ejemplos de uso:
try:
    tracker.register_performance(record)
except InvalidPerformanceDataError as e:
    print(f"Datos inválidos: {e}")
except DualPerformanceTrackerError as e:
    print(f"Error del tracker: {e}")
```

---

## 📊 Dashboards y Reportes (Futuros)

### Métricas Recomendadas para Visualizar

1. **Gráfico de Línea:** P/L acumulado Market vs Limit por día
2. **Gráfico de Barras:** Tasa de activación Limit por bot
3. **Tabla Comparativa:** Performance por símbolo
4. **Pie Chart:** Distribución de ganancias Market vs Limit
5. **Heatmap:** Win rate por bot y símbolo

### Queries SQL Útiles

```sql
-- Top 10 operaciones más rentables
SELECT symbol, order_type, profit_loss, open_time
FROM dual_performance
WHERE profit_loss > 0
ORDER BY profit_loss DESC
LIMIT 10;

-- Tasa de activación Limit por símbolo
SELECT 
    symbol,
    COUNT(*) as total,
    SUM(CASE WHEN activation_status = 'activated' THEN 1 ELSE 0 END) as activated,
    ROUND(100.0 * SUM(CASE WHEN activation_status = 'activated' THEN 1 ELSE 0 END) / COUNT(*), 2) as activation_rate
FROM dual_performance
WHERE order_type = 'limit'
GROUP BY symbol;

-- Comparación Market vs Limit por mes
SELECT 
    strftime('%Y-%m', open_time) as month,
    order_type,
    COUNT(*) as operations,
    SUM(profit_loss) as total_pl,
    AVG(profit_loss) as avg_pl
FROM dual_performance
GROUP BY month, order_type
ORDER BY month, order_type;
```

---

## 🚀 Mejoras Futuras

### Fase 3
- [ ] Integración con sistema de alertas (cuando Limit supera consistentemente a Market)
- [ ] Export de reportes en CSV/Excel
- [ ] Análisis de correlación con volatilidad del mercado

### Fase 4
- [ ] Dashboard web interactivo con Dash/Plotly
- [ ] Análisis ML para predecir mejor tipo de orden según condiciones
- [ ] API REST para consultas externas

---

## 📚 Referencias

- **Ticket Original:** [#31 - T15](https://github.com/DVARGAS117/Botrading/issues/31)
- **Épica:** [#4 - Dual Market/Limit](https://github.com/DVARGAS117/Botrading/issues/4)
- **Documentación Relacionada:**
  - `T14_dual_order_manager.md` - Apertura simultánea
  - `T34_daily_metrics.md` - Consolidación diaria
  - `T08_consulta_posiciones.md` - Consulta de posiciones MT5

---

## ✅ Checklist de Implementación

- [x] Crear estructura de clases (PerformanceRecord, OperationPerformance, DailyPerformanceComparison)
- [x] Implementar registro de performance
- [x] Implementar comparación por operación
- [x] Implementar comparación diaria
- [x] Implementar métricas agregadas
- [x] Crear base de datos y schema
- [x] Crear índices para performance
- [x] Implementar validaciones
- [x] Crear 29 tests unitarios (100% passing)
- [x] Crear ejemplos de uso
- [x] Documentar API completa
- [x] Casos de uso y edge cases

**Estado:** ✅ **COMPLETADO**

---

## 👥 Contribución

**Autor Principal:** Sistema Botrading  
**Revisores:** Pendiente  
**Fecha de Implementación:** 2025-11-13  
**Versión:** 1.0.0

---

## 📄 Licencia

Este módulo es parte del sistema Botrading y está sujeto a las mismas condiciones de licencia del proyecto principal.
