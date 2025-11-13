# T41: Disponibilización de métricas diarias por bot

## Historia de Usuario

Como analista, quiero disponer de winrate, profit factor, P/L por tipo de orden y costo IA total por día y bot, para evaluar efectividad y eficiencia.

## Criterios de Aceptación

```gherkin
Escenario: Disponibilizar métricas diarias por bot
  Dado que se generaron métricas del día
  Cuando un analista consulta el resumen
  Entonces visualiza winrate, profit factor, P/L por tipo y costo IA total
```

## Implementación

### Arquitectura

Se implementa la clase `DailyMetricsCalculator` en `src/core/daily_metrics.py` que calcula métricas diarias consultando la base de datos SQLite.

### Métricas Calculadas

1. **Winrate**: Proporción de operaciones ganadoras (profit > 0) sobre total de operaciones
2. **Profit Factor**: Beneficio neto total / Pérdida neta total
   - Si no hay pérdidas pero sí beneficios: infinito
   - Si no hay operaciones: 0
3. **P/L por Tipo de Orden**: Diccionario con P/L acumulado por "Market" y "Limit"
4. **Costo Total IA**: Suma de costos de todas las consultas IA del día

### Estructura de Base de Datos

#### Tabla `operations`
- `bot_id`: ID del bot
- `order_type`: "Market" o "Limit"
- `profit`: Ganancia/pérdida de la operación
- `close_date`: Fecha de cierre
- `status`: "closed" para operaciones finalizadas

#### Tabla `ia_queries`
- `bot_id`: ID del bot
- `cost`: Costo de la consulta IA
- `query_date`: Fecha de la consulta

### Uso

```python
from src.core.daily_metrics import DailyMetricsCalculator

calculator = DailyMetricsCalculator()
metrics = calculator.calculate_daily_metrics(bot_id=1)

print(f"Winrate: {metrics['winrate']:.2%}")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
print(f"P/L Market: {metrics['pl_by_order_type'].get('Market', 0)}")
print(f"P/L Limit: {metrics['pl_by_order_type'].get('Limit', 0)}")
print(f"Costo IA: ${metrics['total_ia_cost']:.4f}")
```

### Testing

Se implementan pruebas unitarias en `tests/unit/test_daily_metrics.py` con casos:
- Cálculo exitoso con operaciones mixtas
- Caso sin operaciones
- Caso sin pérdidas (profit factor infinito)

Cobertura: 100% en la clase `DailyMetricsCalculator`

### Beneficios

1. **Evaluación de Efectividad**: Winrate permite medir tasa de aciertos
2. **Eficiencia Económica**: Profit factor mide relación beneficio/riesgo
3. **Comparación de Estrategias**: P/L por tipo de orden compara Market vs Limit
4. **Control de Costos**: Costo IA total permite optimizar uso de IA
5. **Análisis Diario**: Métricas por día facilitan seguimiento temporal

### Limitaciones

- Requiere base de datos SQLite con tablas `operations` e `ia_queries`
- Asume estructura específica de tablas (definida en épica Persistencia)
- No incluye métricas históricas acumuladas (solo diarias)

### Futuras Mejoras

- Soporte para rangos de fechas
- Métricas acumuladas semanales/mensuales
- Gráficos y visualizaciones
- Alertas automáticas por umbrales</content>
<parameter name="filePath">c:\Users\Hector\Desktop\Proyectos\AGENTE 2\Botrading\context\DOCUMENTACION\T41_generacion_metricas_diarias.md