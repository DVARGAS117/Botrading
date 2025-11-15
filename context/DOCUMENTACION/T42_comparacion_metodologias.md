# 📊 T42 - Comparación de Desempeño entre Metodologías

**Ticket:** #58 (T42)  
**Fase:** 3  
**Prioridad:** P1 (Alta)  
**Épica:** Métricas y monitoreo  
**Fecha:** 2025-11-15  
**Estado:** ✅ Completado

---

## 📋 Descripción

Este ticket implementa la comparación de desempeño entre diferentes metodologías de trading (bots numéricos, visuales e híbridos) para facilitar decisiones de continuidad, ajustes de prompts y optimización de señales.

---

## 🎯 Historia de Usuario

**Como** PM  
**Quiero** comparar desempeño entre bots numéricos, visuales e híbridos  
**Para** decidir continuidad o ajustes de prompts y señales

---

## ✅ Criterios de Aceptación

```gherkin
Escenario: Comparar desempeño entre metodologías
  Dado que existen métricas para bots numéricos, visuales e híbridos
  Cuando se consulta el comparativo
  Entonces se muestran indicadores clave por bot para decisiones de continuidad
```

**Estado:** ✅ Cumplido

---

## 🏗️ Arquitectura

### Componentes Creados

1. **`MethodologyComparator`** (`src/analytics/methodology_comparator.py`)
   - Comparador principal de metodologías
   - Análisis de ROI y costo-beneficio
   - Ranking por diferentes criterios
   - Generación de recomendaciones
   - Análisis de tendencias

2. **Modelos de Datos**
   - `BotMethodology`: Asociación bot-metodología
   - `MethodologyStats`: Estadísticas por metodología
   - `MethodologyComparison`: Resultado de comparación
   - `MarketLimitComparison`: Comparación Market vs Limit
   - `MethodologyTrend`: Análisis de tendencias

3. **Archivo de Ejemplos** (`examples/methodology_comparator_example.py`)
   - 9 ejemplos prácticos de uso
   - Casos de uso reales
   - Exportación a JSON

### Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────┐
│                  MethodologyComparator                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input:                                                     │
│    - List[BotMethodology]                                   │
│    - days / start_date + end_date                           │
│                                                             │
│  ┌─────────────────────────────────────────┐               │
│  │  1. Agrupar bots por metodología        │               │
│  └────────────┬────────────────────────────┘               │
│               ↓                                             │
│  ┌─────────────────────────────────────────┐               │
│  │  2. Obtener métricas por bot/rango      │               │
│  │     (DailyMetricsRepository)            │               │
│  └────────────┬────────────────────────────┘               │
│               ↓                                             │
│  ┌─────────────────────────────────────────┐               │
│  │  3. Calcular estadísticas por metodolog │               │
│  │     - Total operations                  │               │
│  │     - Winrate promedio                  │               │
│  │     - Profit Factor                     │               │
│  │     - ROI                               │               │
│  │     - Costo por operación               │               │
│  └────────────┬────────────────────────────┘               │
│               ↓                                             │
│  ┌─────────────────────────────────────────┐               │
│  │  4. Identificar mejor/peor metodología  │               │
│  └────────────┬────────────────────────────┘               │
│               ↓                                             │
│  Output:                                                    │
│    - MethodologyComparison                                  │
│      - methodology_stats                                    │
│      - best_methodology                                     │
│      - worst_methodology                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementación

### Características Principales

#### 1. **Comparación de Metodologías**

Compara diferentes metodologías calculando:
- Total de operaciones
- Operaciones ganadoras/perdedoras
- Winrate promedio
- Profit Factor promedio
- Profit/Loss total (general, market, limit)
- Costos de IA (total, tokens)
- ROI (Return on Investment)
- Costo por operación
- Ganancia neta

```python
comparison = comparator.compare_methodologies(
    bot_methodologies=[
        BotMethodology(bot_id=1, methodology="numerical"),
        BotMethodology(bot_id=2, methodology="visual"),
        BotMethodology(bot_id=3, methodology="hybrid")
    ],
    days=7
)

print(f"Mejor: {comparison.best_methodology}")
print(f"Peor: {comparison.worst_methodology}")
```

#### 2. **Ranking de Metodologías**

Ordena metodologías por diferentes criterios:
- `total_profit_loss`: Ganancia total
- `avg_winrate`: Winrate promedio
- `avg_profit_factor`: Profit Factor
- `roi`: Return on Investment
- `net_profit`: Ganancia neta
- `total_operations`: Volumen

```python
ranking = comparator.get_methodology_ranking(
    bot_methodologies=bot_methodologies,
    days=7,
    sort_by='roi'
)

for i, stat in enumerate(ranking, 1):
    print(f"{i}. {stat.methodology}: ROI={stat.roi:.2f}%")
```

#### 3. **Comparación Market vs Limit**

Analiza el desempeño de órdenes Market vs Limit por metodología:

```python
ml_comparison = comparator.compare_market_vs_limit(
    bot_methodologies=bot_methodologies,
    days=7
)

for comp in ml_comparison:
    print(f"{comp.methodology}:")
    print(f"  Market: ${comp.market_profit_loss:.2f}")
    print(f"  Limit: ${comp.limit_profit_loss:.2f}")
```

#### 4. **Estadísticas Agregadas**

Proporciona vista consolidada de todas las metodologías:

```python
stats = comparator.get_aggregate_statistics(
    bot_methodologies=bot_methodologies,
    days=7
)

print(f"Operaciones totales: {stats['total_operations']}")
print(f"Winrate general: {stats['overall_winrate']:.2f}%")
print(f"ROI general: {stats['overall_roi']:.2f}%")
```

#### 5. **Recomendaciones Automáticas**

Genera recomendaciones basadas en métricas:

```python
recommendations = comparator.get_recommendations(
    bot_methodologies=bot_methodologies,
    days=7
)

for rec in recommendations:
    print(f"{rec['type']}: {rec['message']}")
```

Tipos de recomendaciones:
- `best_performer`: Mejor metodología
- `needs_improvement`: Requiere mejoras
- `negative_roi`: ROI negativo
- `low_winrate`: Winrate bajo

#### 6. **Análisis de Tendencias**

Compara primera vs segunda mitad del período:

```python
trends = comparator.get_methodology_trends(
    bot_methodologies=bot_methodologies,
    days=10
)

for trend in trends:
    print(f"{trend.methodology}: {trend.trend_direction.value}")
    print(f"  Winrate: {trend.winrate_change:+.2f}%")
    print(f"  P/L: ${trend.profit_loss_change:+.2f}")
```

Direcciones de tendencia:
- `improving`: Mejorando
- `declining`: En declive
- `stable`: Estable

---

## 📊 Métricas Calculadas

### Por Metodología

| Métrica | Descripción | Cálculo |
|---------|-------------|---------|
| `total_operations` | Total de operaciones | Suma de operaciones de todos los bots |
| `winning_operations` | Operaciones ganadoras | Suma de ganadoras |
| `losing_operations` | Operaciones perdedoras | Suma de perdedoras |
| `avg_winrate` | Winrate promedio | Promedio de winrates diarios |
| `avg_profit_factor` | Profit Factor promedio | Promedio de PF diarios |
| `total_profit_loss` | P/L total | Suma de P/L |
| `market_profit_loss` | P/L Market | Suma de P/L Market |
| `limit_profit_loss` | P/L Limit | Suma de P/L Limit |
| `total_ia_cost` | Costo IA total | Suma de costos IA |
| `total_tokens` | Tokens totales | Suma de tokens |
| `roi` | Return on Investment | `((P/L - Costo) / Costo) * 100` |
| `cost_per_operation` | Costo por operación | `Costo IA / Total ops` |
| `net_profit` | Ganancia neta | `P/L - Costo IA` |

### Agregadas (Global)

- `total_operations`: Suma de todas las operaciones
- `total_winning_operations`: Suma de todas las ganadoras
- `overall_winrate`: Winrate general
- `total_profit_loss`: P/L total
- `total_ia_cost`: Costo IA total
- `overall_roi`: ROI general
- `net_profit`: Ganancia neta global

---

## 🧪 Pruebas Unitarias

Se implementaron 21 pruebas unitarias que cubren:

1. ✅ Inicialización del comparador
2. ✅ Validación de parámetros requeridos
3. ✅ Comparación básica entre metodologías
4. ✅ Inclusión de métricas clave
5. ✅ Cálculo correcto de ROI
6. ✅ Identificación de mejor metodología
7. ✅ Identificación de peor metodología
8. ✅ Comparación por rango de fechas
9. ✅ Uso del parámetro `days`
10. ✅ Ranking de metodologías
11. ✅ Ranking por diferentes criterios
12. ✅ Comparación Market vs Limit
13. ✅ Estadísticas agregadas
14. ✅ Validación de lista vacía
15. ✅ Validación de días inválidos
16. ✅ Validación de rango de fechas inválido
17. ✅ Manejo de bot sin métricas
18. ✅ Serialización a diccionario
19. ✅ Serialización a JSON
20. ✅ Generación de recomendaciones
21. ✅ Análisis de tendencias

**Cobertura:** 100% de funcionalidades críticas

---

## 📖 Uso

### Instalación

No requiere dependencias adicionales. Utiliza:
- `DailyMetricsRepository` (T34)
- SQLite (integrado)

### Ejemplo Básico

```python
from src.analytics.methodology_comparator import (
    MethodologyComparator,
    BotMethodology,
    create_methodology_comparator
)

# Crear comparador
comparator = create_methodology_comparator("data/botrading.db")

# Definir bots y metodologías
bot_methodologies = [
    BotMethodology(bot_id=1, methodology="numerical"),
    BotMethodology(bot_id=2, methodology="visual"),
    BotMethodology(bot_id=3, methodology="hybrid")
]

# Comparar últimos 7 días
comparison = comparator.compare_methodologies(
    bot_methodologies=bot_methodologies,
    days=7
)

# Resultados
print(f"Mejor metodología: {comparison.best_methodology}")
for stat in comparison.methodology_stats:
    print(f"{stat.methodology}: ROI={stat.roi:.2f}%")
```

### Caso de Uso: Decisión de Continuidad

```python
# Analizar 30 días
comparison = comparator.compare_methodologies(
    bot_methodologies=bot_methodologies,
    days=30
)

# Criterios de decisión
MIN_ROI = 50.0
MIN_WINRATE = 55.0

for stat in comparison.methodology_stats:
    if stat.roi >= MIN_ROI and stat.avg_winrate >= MIN_WINRATE:
        print(f"{stat.methodology}: CONTINUAR ✓")
    elif stat.roi >= MIN_ROI * 0.7:
        print(f"{stat.methodology}: AJUSTAR ⚠")
    else:
        print(f"{stat.methodology}: PAUSAR ✗")
```

---

## 🔗 Dependencias

### Internas
- `src.core.daily_metrics_repository.DailyMetricsRepository` (T34)
- `src.core.daily_metrics_repository.DailyMetrics` (T34)

### Externas
- `sqlite3` (estándar)
- `dataclasses` (estándar)
- `datetime` (estándar)
- `json` (estándar)
- `logging` (estándar)

---

## 🚀 Beneficios

1. **Decisiones Informadas**: Datos objetivos para decidir continuidad
2. **Optimización de Recursos**: Identificar metodologías más eficientes
3. **Análisis Costo-Beneficio**: ROI claro por metodología
4. **Comparación Justa**: Métricas normalizadas
5. **Recomendaciones Automáticas**: Insights sin análisis manual
6. **Tendencias**: Detectar mejoras o declives
7. **Flexibilidad**: Múltiples criterios de análisis

---

## 📈 Casos de Uso

### 1. Revisión Semanal de PM
```python
comparison = comparator.compare_methodologies(
    bot_methodologies=all_bots,
    days=7
)
recommendations = comparator.get_recommendations(
    bot_methodologies=all_bots,
    days=7
)
```

### 2. Análisis Mensual
```python
ranking = comparator.get_methodology_ranking(
    bot_methodologies=all_bots,
    days=30,
    sort_by='roi'
)
```

### 3. Optimización de Costos IA
```python
stats = comparator.get_aggregate_statistics(
    bot_methodologies=all_bots,
    days=30
)
cost_efficiency = stats['net_profit'] / stats['total_ia_cost']
```

### 4. Detección de Problemas
```python
trends = comparator.get_methodology_trends(
    bot_methodologies=all_bots,
    days=14
)
declining = [t for t in trends if t.trend_direction == 'declining']
```

---

## 🔮 Mejoras Futuras

1. **Visualizaciones**: Gráficos de comparación
2. **Alertas**: Notificaciones de declives
3. **Exportación**: PDF/Excel de reportes
4. **Análisis Predictivo**: ML para proyecciones
5. **Dashboard**: Interfaz web interactiva
6. **Comparación por Activo**: Desempeño por símbolo
7. **Análisis de Correlación**: Entre metodologías

---

## ✅ Checklist de Implementación

- [x] Modelo de datos `BotMethodology`
- [x] Modelo de datos `MethodologyStats`
- [x] Modelo de datos `MethodologyComparison`
- [x] Modelo de datos `MarketLimitComparison`
- [x] Modelo de datos `MethodologyTrend`
- [x] Clase `MethodologyComparator`
- [x] Método `compare_methodologies`
- [x] Método `get_methodology_ranking`
- [x] Método `compare_market_vs_limit`
- [x] Método `get_aggregate_statistics`
- [x] Método `get_recommendations`
- [x] Método `get_methodology_trends`
- [x] Validaciones de parámetros
- [x] Manejo de errores
- [x] Logging
- [x] Factory function
- [x] Serialización a dict/JSON
- [x] 21 pruebas unitarias (100% pass)
- [x] Archivo de ejemplos (9 ejemplos)
- [x] Documentación técnica

---

## 📝 Notas de Desarrollo

### Decisiones de Diseño

1. **ROI como Criterio Principal**: El ROI se usa para identificar mejor/peor metodología porque refleja rentabilidad considerando costos.

2. **Promedios de Métricas**: Winrate y Profit Factor se promedian (no se recalculan globalmente) para mantener consistencia con T34.

3. **Tendencias**: Se compara primera vs segunda mitad del período (no día a día) para reducir ruido.

4. **Recomendaciones**: Basadas en umbrales configurables, fáciles de ajustar.

5. **Flexibilidad de Fechas**: Soporta tanto `days` como `start_date/end_date` para máxima flexibilidad.

### Lecciones Aprendidas

- La integración con `DailyMetricsRepository` fue directa y sin fricción
- Las pruebas unitarias detectaron un bug en la lógica de tendencias
- El uso de dataclasses simplificó la serialización
- El patrón factory function facilitó la creación del comparador

---

## 🎯 Cumplimiento de Criterios

✅ **Comparación entre metodologías**: Implementado  
✅ **Indicadores clave**: Winrate, PF, ROI, P/L, costos  
✅ **Decisiones de continuidad**: Recomendaciones automáticas  
✅ **Pruebas unitarias**: 21 tests, 100% pass  
✅ **Documentación**: Completa con ejemplos  
✅ **Ejemplo de uso**: 9 casos prácticos  

---

**Documento generado:** 15 de Noviembre de 2025  
**Desarrollado usando:** Metodología TDD  
**Cobertura de pruebas:** 100%  
**Estado:** ✅ Completado y probado
