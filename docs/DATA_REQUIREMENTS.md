# 📊 Requerimientos de Datos para Indicadores

**Versión:** 1.0  
**Fecha:** 17 de Noviembre, 2025  
**Autor:** Sistema Botrading  

---

## 🎯 Principio Fundamental

> **"Los indicadores SIEMPRE deben ser precisos. Si necesitas 100 velas para un indicador y solo tienes 50, NO cambies el indicador, cambia la recolección de datos."**

Este documento especifica los requerimientos mínimos y recomendados de datos para cada indicador técnico utilizado en el sistema.

---

## 📋 Tabla de Requerimientos por Indicador

| Indicador | Períodos Mínimos | Períodos Recomendados | Buffer | Razón |
|-----------|------------------|----------------------|---------|-------|
| **EMA 9**     | 9   | 30  | 21  | EMA rápida requiere pocos datos pero buffer ayuda con estabilidad inicial |
| **EMA 50**    | 50  | 100 | 50  | EMA lenta requiere al menos 50 períodos, buffer 2x para precisión óptima |
| **ATR 14**    | 14  | 50  | 36  | ATR requiere historia de volatilidad, buffer permite suavizado Wilder adecuado |
| **ATR 21**    | 21  | 50  | 29  | Período más largo requiere más datos históricos de True Range |
| **VWAP**      | Sesión | 100 | 20+ | Anclado a inicio de sesión, necesita todas las velas + pre-market |
| **VWAP Slope** | 10  | 50  | 40  | Usa lookback de 10 períodos sobre VWAP ya establecido |
| **VWAP Bands** | 20  | 50  | 30  | Desviación estándar ponderada requiere datos estables |
| **Opening Range** | Tiempo | Sesión | N/A | Basado en tiempo (08:00-08:30 GMT), necesita datos desde inicio |

---

## 🔍 Detalle por Indicador

### EMA (Exponential Moving Average)

**EMA 9 (Rápida)**
- **Mínimo:** 9 períodos
- **Recomendado:** 30 períodos
- **Razón:** Aunque se puede calcular con 9 velas, los primeros valores tendrán alta variabilidad. Con 30 períodos, el indicador se estabiliza.

**EMA 50 (Lenta)**
- **Mínimo:** 50 períodos
- **Recomendado:** 100 períodos
- **Razón:** La EMA50 es un indicador de tendencia clave. Con exactamente 50 velas, solo tendríamos 1 valor final. Con 100 velas, tenemos 50 valores históricos para analizar cruces y pendiente.
- **⚠️ CRÍTICO:** `indicator_calculator.py` valida mínimo 50 velas antes de calcular.

### ATR (Average True Range)

**ATR 14**
- **Mínimo:** 14 períodos
- **Recomendado:** 50 períodos
- **Razón:** El ATR usa suavizado de Wilder que requiere history. Con solo 14 velas, el primer valor es correcto pero sin contexto histórico.

**ATR 21**
- **Mínimo:** 21 períodos
- **Recomendado:** 50 períodos
- **Razón:** Similar al ATR 14, pero con período más largo que captura volatilidad de más largo plazo.

### VWAP (Volume Weighted Average Price)

**VWAP de Sesión**
- **Mínimo:** Todas las velas desde inicio de sesión (08:00 GMT)
- **Recomendado:** 100 velas en M5 (cubre pre-market + sesión completa)
- **Cálculo:**
  - Sesión VWAP: 08:00 - 13:00 GMT = 5 horas
  - En M5: 5h × 12 velas/hora = 60 velas mínimo
  - Con pre-market (07:00-08:00): 60 + 12 = 72 velas
  - Recomendado: 100 velas (incluye buffer para análisis pre-sesión)
- **Razón:** VWAP es un indicador anclado que se reinicia cada sesión. Necesita datos desde el inicio para ser preciso.

**VWAP Slope (Pendiente)**
- **Mínimo:** 10 períodos de lookback
- **Recomendado:** 50 velas totales
- **Razón:** Calcula la pendiente comparando VWAP actual vs VWAP de hace 10 períodos. Requiere VWAP ya establecido.
- **Threshold:** 0.00005 para EURUSD (5 pips en 10 períodos)

**VWAP Bands (Bandas)**
- **Mínimo:** 20 períodos
- **Recomendado:** 50 períodos
- **Razón:** Calcula desviación estándar ponderada por volumen. Requiere suficientes datos para estadística confiable.
- **Bandas:** ±1σ y ±2σ

### Opening Range (OR)

**Opening Range 08:00-08:30 GMT**
- **Mínimo:** Datos desde 08:00 GMT
- **Recomendado:** Datos desde 07:00 GMT (incluye pre-market)
- **Razón:** El OR se calcula de los primeros 30 minutos de sesión europea. Necesita datos desde inicio de sesión.
- **Breakout Detection:** Requiere datos actuales para comparar precio vs OR high/low

---

## 📐 Configuración por Timeframe

### M1 (1 Minuto)

**Uso:** Timing micro, análisis de estructura interna  
**Count Recomendado:** 200 velas  
**Tiempo Cubierto:** ~3.3 horas  
**Casos de Uso:**
- Timing preciso de entradas
- Confirmación de breakouts
- Análisis de micro-estructura de mercado

### M5 (5 Minutos) - **TIMEFRAME PRINCIPAL**

**Uso:** Señales principales, gestión de operaciones  
**Count Recomendado:** 100 velas  
**Tiempo Cubierto:** ~8.3 horas  
**Casos de Uso:**
- Cálculo de todos los indicadores VWAP
- Señales de entrada/salida
- Gestión activa de posiciones
- Reevaluaciones

**Detalle de 100 velas:**
- EMA50: 50 períodos de cálculo + 50 de buffer ✅
- ATR 21: 21 períodos + 79 de buffer ✅
- VWAP: Sesión completa (60) + pre-market (12) + buffer (28) ✅
- VWAP Slope: 10 lookback + 90 de historia ✅

### M15 (15 Minutos)

**Uso:** Contexto de tendencia, confirmación  
**Count Recomendado:** 100 velas  
**Tiempo Cubierto:** ~25 horas  
**Casos de Uso:**
- Contexto de tendencia intradía
- Confirmación de señales M5
- Niveles de soporte/resistencia

### H1 (1 Hora)

**Uso:** Contexto macro, tendencia de mediano plazo  
**Count Recomendado:** 50 velas  
**Tiempo Cubierto:** ~2 días  
**Casos de Uso:**
- Tendencia de mediano plazo
- Niveles clave diarios/semanales
- Contexto para decisiones intradía

---

## ⚙️ Validación en Código

### Validación Automática en `indicator_calculator.py`

```python
def calculate_indicators_for_timeframe(self, ohlcv_data: OHLCVData) -> IndicatorData:
    """
    Calcula indicadores con validación de datos mínimos.
    
    Raises:
        ValueError: Si hay menos de 50 velas
    """
    # VALIDACIÓN CRÍTICA
    if ohlcv_data.count < 50:  # Mínimo para EMA50
        raise ValueError(
            f"Datos insuficientes para {ohlcv_data.symbol} {ohlcv_data.timeframe.name}. "
            f"Se requieren al menos 50 velas, se tienen {ohlcv_data.count}"
        )
    
    # Proceder con cálculos...
```

Esta validación asegura que **NUNCA** se calculen indicadores con datos insuficientes.

---

## 📝 Guías de Uso en Producción

### ✅ USO CORRECTO

```python
# Ejemplo 1: Extracción M5 con count adecuado
data_m5 = extractor.get_ohlcv(
    symbol="EURUSD",
    timeframe=Timeframe.M5,
    count=100  # ✅ Suficiente para todos los indicadores
)

# Ejemplo 2: Multi-timeframe con counts apropiados
timeframes_data = extractor.get_ohlcv_multi_timeframe(
    symbol="EURUSD",
    timeframes=[Timeframe.M5, Timeframe.M15, Timeframe.H1],
    count=100  # ✅ Suficiente para M5 y M15, más que suficiente para H1
)

# Ejemplo 3: M1 para análisis micro
data_m1 = extractor.get_ohlcv(
    symbol="EURUSD",
    timeframe=Timeframe.M1,
    count=200  # ✅ 3.3 horas de datos micro
)
```

### ❌ USO INCORRECTO

```python
# ❌ EVITAR: Count mínimo sin buffer
data = extractor.get_ohlcv(
    symbol="EURUSD",
    timeframe=Timeframe.M5,
    count=50  # ❌ Justo el mínimo, EMA50 tendrá 1 solo valor
)

# ❌ EVITAR: Count insuficiente
data = extractor.get_ohlcv(
    symbol="EURUSD",
    timeframe=Timeframe.M5,
    count=30  # ❌ Lanzará ValueError en indicator_calculator
)

# ❌ EVITAR: Usar valores hardcodeados arbitrarios
data = extractor.get_ohlcv(
    symbol="EURUSD",
    timeframe=Timeframe.M5,
    count=42  # ❌ Número arbitrario sin justificación
)
```

---

## 🎯 Metodología VWAP: Especificaciones

### Definición de Sesión

- **Inicio:** 08:00 GMT
- **Fin:** 13:00 GMT  
- **Duración:** 5 horas
- **Opening Range:** 08:00 - 08:30 GMT (primeros 30 min)

### Extracción de Datos por Timeframe

| Timeframe | Velas a Extraer | Desde | Propósito |
|-----------|-----------------|-------|-----------|
| **M5** | 100 velas | Pre-market + Sesión | Timeframe principal, todos los indicadores |
| **M1** | 200 velas | Últimas 3.3h | Timing micro, confirmación de entradas |
| **H1** | 30-50 velas | Últimos 1-2 días | Contexto macro, tendencia mediano plazo |

### Cálculo de Velas Necesarias

**Para M5 en sesión VWAP:**
```
Sesión completa: 5 horas × 12 velas/hora = 60 velas
Pre-market (1h): 1 hora × 12 velas/hora = 12 velas
Buffer recomendado: 28 velas
──────────────────────────────────────────────────
TOTAL RECOMENDADO: 100 velas ✅
```

Esto garantiza:
- ✅ VWAP con datos desde inicio de sesión
- ✅ EMA50 con 50 períodos de buffer
- ✅ ATR con suficiente historia de volatilidad
- ✅ VWAP Slope con lookback completo
- ✅ Opening Range con datos pre y post OR

---

## 🚨 Manejo de Errores

### Estrategia de Validación

1. **Antes de extraer:**
   ```python
   # Usar configuración centralizada
   from config import data_extraction_config
   min_count = data_extraction_config["timeframes"]["M5"]["min_required"]
   recommended_count = data_extraction_config["timeframes"]["M5"]["default_count"]
   ```

2. **Después de extraer:**
   ```python
   if data.count < min_required:
       raise MT5DataError(
           f"MT5 devolvió {data.count} velas, se requieren al menos {min_required}"
       )
   
   if data.count < recommended_count:
       logger.warning(
           f"Datos por debajo de lo recomendado: {data.count} < {recommended_count}. "
           "Los indicadores pueden tener menos precisión."
       )
   ```

3. **En cálculo de indicadores:**
   ```python
   # indicator_calculator.py ya valida automáticamente
   try:
       indicators = calculator.calculate_indicators_for_timeframe(data)
   except ValueError as e:
       logger.error(f"Datos insuficientes para calcular indicadores: {e}")
       # NO intentar calcular con menos datos
       # Rechazar señal o esperar más datos
   ```

---

## 📊 Consideraciones de Performance

### Impacto de Memoria

| Timeframe | Velas | Tamaño Aprox. | RAM Típica |
|-----------|-------|---------------|------------|
| M1 × 200  | 200   | ~200 KB       | Negligible |
| M5 × 100  | 100   | ~100 KB       | Negligible |
| M15 × 100 | 100   | ~100 KB       | Negligible |
| H1 × 50   | 50    | ~50 KB        | Negligible |
| **TOTAL** | 450   | **~450 KB**   | **< 1 MB** |

### Impacto de Tiempo

- **Extracción MT5:** ~50-100ms por timeframe
- **Cálculo Indicadores:** ~10-50ms por timeframe
- **Total Multi-TF:** < 500ms típicamente

**Conclusión:** El costo de extraer datos extra (100 vs 50 velas) es **negligible** comparado con el beneficio de indicadores precisos.

---

## 🔄 Actualización y Mantenimiento

### Cuándo Revisar Este Documento

- ✅ Al agregar nuevos indicadores
- ✅ Al cambiar períodos de indicadores existentes
- ✅ Al modificar definición de sesión VWAP
- ✅ Al implementar nuevas metodologías de trading
- ✅ Si se detectan problemas de precisión en backtesting

### Control de Versiones

Este documento está bajo control de versiones Git. Cada cambio debe:
1. Actualizarse en este archivo
2. Actualizarse en `config/data_extraction.json`
3. Documentarse en commit con tag `[DOCS][DATA]`

---

## 📚 Referencias

- **Archivo de Configuración:** `config/data_extraction.json`
- **Código de Validación:** `src/core/indicator_calculator.py` (líneas 318-326)
- **Extracción de Datos:** `src/core/mt5_data_extractor.py`
- **Metodología VWAP:** `context/prompt_IA.md`
- **Tests de Integración:** `tests/integration/test_vwap_end_to_end.py`

---

## ✅ Checklist de Implementación

Antes de implementar código de producción que use indicadores, verificar:

- [ ] `count` >= valor en `data_extraction.json` para el timeframe
- [ ] Manejo de error si MT5 devuelve menos velas que `min_required`
- [ ] Logging de warning si `count` < `recommended`
- [ ] Validación de `data.count` antes de pasar a `indicator_calculator`
- [ ] Tests de integración con datos reales de MT5
- [ ] Documentación de por qué se eligió ese `count` específico

---

**Última Actualización:** 17 de Noviembre, 2025  
**Próxima Revisión:** Al completar implementación de bots de producción
