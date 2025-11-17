# 📋 PLAN DE IMPLEMENTACIÓN - METODOLOGÍA VWAP INTRADÍA

**Fecha:** 17 de noviembre de 2025  
**Objetivo:** Implementar indicadores VWAP y prompts especializados para metodología trend-following intradía

---

## 🎯 RESUMEN EJECUTIVO

Implementar 5 nuevos indicadores técnicos y sistema de prompts especializado para metodología VWAP trend-following exclusiva en EURUSD, con soporte completo numérico y visual.

---

## 📦 ENTREGABLES

### 1. Nuevos Indicadores (CORE)
- [x] VWAP de sesión con pendiente
- [x] Bandas VWAP (±1σ, ±2σ)
- [x] EMA 9 (adicional a 20 y 50 existentes)
- [x] ATR (14 y 21 períodos)
- [x] Opening Range (OR) 08:00-08:30 GMT

### 2. Sistema de Prompts
- [ ] System Prompt VWAP Methodology
- [ ] User Prompt Template con variables
- [ ] Parser de respuestas AI especializado
- [ ] Validador de respuestas

### 3. Configuración
- [ ] `config/vwap_sessions.json` - Sesiones por activo
- [ ] `config/prompt_templates.json` - Templates actualizados
- [ ] Actualizar `indicator_calculator.py`

### 4. Visualización
- [ ] Dibujo de VWAP + bandas en gráficos
- [ ] Marcado de Opening Range
- [ ] Estilos específicos para metodología

### 5. Tests
- [ ] Tests unitarios indicadores VWAP
- [ ] Tests prompts y parser
- [ ] Tests integración completa

---

## 🔄 FLUJO DE TRABAJO (SEGÚN agents.md)

### PASO 0: Preparación
- [x] Actualizar rama desarrollo
- [x] Crear documento de tareas
- [ ] Crear rama nueva: `feature/vwap-methodology`

### PASO 1: Tests (TDD)
- [ ] Escribir tests para VWAP calculator
- [ ] Escribir tests para bandas VWAP
- [ ] Escribir tests para ATR
- [ ] Escribir tests para Opening Range
- [ ] Escribir tests para prompt builder VWAP
- [ ] Escribir tests para parser VWAP response

### PASO 2: Implementación Core
- [ ] Extender `IndicatorCalculator` con VWAP
- [ ] Extender `IndicatorCalculator` con ATR
- [ ] Extender `IndicatorCalculator` con EMA 9
- [ ] Implementar Opening Range calculator
- [ ] Actualizar `IndicatorData` dataclass

### PASO 3: Sistema de Prompts
- [ ] Crear `VWAPPromptBuilder` clase
- [ ] Implementar system prompt VWAP
- [ ] Implementar user prompt template
- [ ] Crear parser para respuesta estructurada
- [ ] Validador de formato JSON respuesta

### PASO 4: Configuración
- [ ] Crear `vwap_sessions.json` con sesiones
- [ ] Actualizar `prompt_templates.json`
- [ ] Documentar configuración

### PASO 5: Visualización
- [ ] Extender `ChartGenerator` con VWAP
- [ ] Dibujar bandas VWAP
- [ ] Marcar Opening Range en gráficos
- [ ] Estilos y colores

### PASO 6: Integración
- [ ] Integrar en `prompt_builder.py`
- [ ] Actualizar ejemplos
- [ ] Documentación técnica

### PASO 7: Testing y Validación
- [ ] Ejecutar todos los tests
- [ ] Validar en modo demo
- [ ] Ajustes finales

---

## 📝 TAREAS DETALLADAS

### TAREA 1: Extender IndicatorCalculator con VWAP
**Archivo:** `src/core/indicator_calculator.py`
**Prioridad:** P0
**Tiempo estimado:** 2h

**Subtareas:**
1. [ ] Agregar método `_calculate_vwap(data, session_start_time)`
2. [ ] Agregar método `_calculate_vwap_slope(vwap_series)`
3. [ ] Agregar método `_calculate_vwap_bands(data, vwap)`
4. [ ] Actualizar `IndicatorData` dataclass con campos VWAP
5. [ ] Actualizar `calculate_indicators_for_timeframe()` para incluir VWAP
6. [ ] Tests unitarios completos

**Criterios de Aceptación:**
- VWAP se calcula acumulativamente desde session_start
- VWAP se reinicia cada sesión
- Pendiente se calcula correctamente (derivada)
- Bandas ±1σ y ±2σ calculadas con desviación estándar ponderada por volumen
- Tests pasan al 100%

---

### TAREA 2: Implementar ATR Calculator
**Archivo:** `src/core/indicator_calculator.py`
**Prioridad:** P0
**Tiempo estimado:** 1h

**Subtareas:**
1. [ ] Agregar método `_calculate_atr(data, period)`
2. [ ] Soportar períodos 14 y 21
3. [ ] Actualizar `IndicatorData` con campos ATR
4. [ ] Tests unitarios

**Criterios de Aceptación:**
- ATR calculado según fórmula de Wilder
- Soporta múltiples períodos
- Tests verifican valores conocidos

---

### TAREA 3: Implementar Opening Range Calculator
**Archivo:** `src/core/opening_range_calculator.py` (NUEVO)
**Prioridad:** P0
**Tiempo estimado:** 2h

**Subtareas:**
1. [ ] Crear clase `OpeningRangeCalculator`
2. [ ] Método `calculate_or(data, session_start, or_duration_minutes)`
3. [ ] Método `get_breakout_status(current_price, or_high, or_low)`
4. [ ] Configuración por activo desde JSON
5. [ ] Tests completos

**Criterios de Aceptación:**
- OR se calcula correctamente para ventana 08:00-08:30 GMT
- Detecta breakouts (above/below/inside)
- Soporta configuración por activo
- Tests con datos reales

---

### TAREA 4: Agregar EMA 9
**Archivo:** `src/core/indicator_calculator.py`
**Prioridad:** P1
**Tiempo estimado:** 30min

**Subtareas:**
1. [ ] Agregar campo `ema9` a `IndicatorData`
2. [ ] Calcular EMA 9 en `calculate_indicators_for_timeframe()`
3. [ ] Actualizar JSON formatter
4. [ ] Tests

**Criterios de Aceptación:**
- EMA 9 se calcula junto a EMA 20 y 50
- Aparece en JSON para IA

---

### TAREA 5: Crear VWAPPromptBuilder
**Archivo:** `src/core/vwap_prompt_builder.py` (NUEVO)
**Prioridad:** P0
**Tiempo estimado:** 3h

**Subtareas:**
1. [ ] Crear clase `VWAPPromptBuilder`
2. [ ] Método `build_system_prompt()` - Prompt fijo de metodología
3. [ ] Método `build_user_prompt(data)` - Template con variables
4. [ ] Formateo de velas según timeframe:
   - 5M: todas las de sesión actual
   - 1M: 200 velas de sesión
   - 1H: 30 velas máximo
5. [ ] Tests de construcción de prompts

**Estructura de Variables:**
```python
{
    "activo": "EURUSD",
    "fecha_sesion": "2025-11-17",
    "hora_actual_peru": "10:30",
    "hora_actual_gmt": "15:30",
    "vwap": 1.1045,
    "vwap_pendiente": "ascendente",
    "vwap_bandas": {
        "upper_1": 1.1050,
        "upper_2": 1.1055,
        "lower_1": 1.1040,
        "lower_2": 1.1035
    },
    "ema_fast_5m": 1.1048,
    "atr_5m": 0.0008,
    "or_high": 1.1060,
    "or_low": 1.1040,
    "or_status": "above",
    "precio_actual": 1.1055,
    "velas_5m": [...],  # Todas de sesión
    "velas_1m": [...],  # 200 últimas
    "velas_1h": [...],  # 30 últimas
    "posiciones_abiertas": [...],
    "capital": 10000,
    "riesgo_por_trade": "0.5%",
    "pnl_dia_r": 0.0
}
```

**Criterios de Aceptación:**
- System prompt es idéntico al proporcionado (sin modificar naturaleza)
- User prompt contiene todas las variables necesarias
- Formato claro y parseble
- Tests validan estructura

---

### TAREA 6: Crear Parser de Respuesta VWAP
**Archivo:** `src/core/vwap_response_parser.py` (NUEVO)
**Prioridad:** P0
**Tiempo estimado:** 2h

**Subtareas:**
1. [ ] Crear clase `VWAPResponseParser`
2. [ ] Método `parse_response(ai_response_text)`
3. [ ] Validación de estructura requerida:
   - ESTADO_DEL_MERCADO
   - PLAN_DE_TRADING_ACTUAL
   - GESTIÓN_DE_POSICIONES_ABIERTAS
   - JOURNAL_Y_SCORE
4. [ ] Extracción de valores clave para decisión bot
5. [ ] Conversión a formato parseble por sistema

**Formato Esperado de Salida (para el bot):**
```json
{
  "accion": "OPERAR|NO_OPERAR|MANTENER|ACTUALIZAR|CERRAR",
  "tipo_dia": "Trend Up|Trend Down|Choppy",
  "sesgo": "Largo|Corto|No-trading",
  "permite_nuevas_entradas": true/false,
  "setup_disponible": {
    "tipo": "breakout|pullback|ninguno",
    "direccion": "BUY|SELL",
    "zona_entrada": 1.1050,
    "stop_tecnico": 1.1034,
    "objetivos": [1.1066, 1.1080],
    "justificacion": "Ruptura OR High + VWAP alcista..."
  },
  "gestion_posiciones": [
    {
      "ticket": 12345,
      "accion": "MANTENER|CERRAR_PARCIAL|CERRAR_TOTAL",
      "ajuste_stop": 1.1045,
      "justificacion": "..."
    }
  ],
  "score_disciplina": 9,
  "puntos_mejora": ["...", "..."],
  "razonamiento_completo": "TEXTO COMPLETO DE LA RESPUESTA IA"
}
```

**Criterios de Aceptación:**
- Parser extrae todas las secciones correctamente
- Convierte a JSON estructurado
- Maneja errores de formato IA
- Validación de campos obligatorios
- Tests con respuestas reales y malformadas

---

### TAREA 7: Configuración VWAP Sessions
**Archivo:** `config/vwap_sessions.json` (NUEVO)
**Prioridad:** P0
**Tiempo estimado:** 30min

**Contenido:**
```json
{
  "EURUSD": {
    "session_name": "European Session",
    "session_start_gmt": "08:00",
    "session_end_gmt": "17:00",
    "or_window": {
      "start_gmt": "08:00",
      "end_gmt": "08:30",
      "duration_minutes": 30
    },
    "trading_hours_local": {
      "timezone": "America/Lima",
      "start": "06:00",
      "end": "13:00"
    },
    "vwap_reset_time_gmt": "08:00"
  },
  "XAUUSD": {
    "session_name": "Asian/European Session",
    "session_start_gmt": "01:00",
    "or_window": {
      "start_gmt": "08:00",
      "end_gmt": "08:30",
      "duration_minutes": 30
    },
    "trading_hours_local": {
      "timezone": "America/Lima",
      "start": "06:00",
      "end": "13:00"
    },
    "vwap_reset_time_gmt": "00:00"
  }
}
```

**Criterios de Aceptación:**
- JSON válido
- Configuración por activo
- Documentado inline

---

### TAREA 8: Actualizar PromptBuilder Principal
**Archivo:** `src/core/prompt_builder.py`
**Prioridad:** P1
**Tiempo estimado:** 1h

**Subtareas:**
1. [ ] Importar `VWAPPromptBuilder`
2. [ ] Agregar método `build_vwap_prompt()` en `PromptBuilder`
3. [ ] Integrar con flujo existente
4. [ ] Tests de integración

**Criterios de Aceptación:**
- PromptBuilder puede generar prompts VWAP
- Compatible con sistema existente
- Tests pasan

---

### TAREA 9: Visualización VWAP
**Archivo:** `src/core/chart_generator.py`
**Prioridad:** P1
**Tiempo estimado:** 2h

**Subtareas:**
1. [ ] Método `plot_vwap_with_bands(ax, data, vwap_data)`
2. [ ] Método `plot_opening_range(ax, or_high, or_low)`
3. [ ] Estilos y colores diferenciados
4. [ ] Leyendas claras
5. [ ] Tests visuales (generación de imágenes)

**Criterios de Aceptación:**
- VWAP dibujada como línea azul gruesa
- Bandas ±1σ en naranja (líneas discontinuas)
- Bandas ±2σ en rojo (líneas punteadas)
- OR marcado con líneas horizontales verdes
- Áreas sombreadas entre bandas
- Legible y profesional

---

### TAREA 10: Documentación Técnica
**Archivo:** `context/DOCUMENTACION/T23_EXTENDED_VWAP_METHODOLOGY.md` (NUEVO)
**Prioridad:** P1
**Tiempo estimado:** 1h

**Contenido:**
- Descripción de metodología VWAP
- Indicadores implementados
- Sistema de prompts
- Ejemplos de uso
- Configuración
- Tests

**Criterios de Aceptación:**
- Documentación completa
- Ejemplos de código
- Diagramas (si aplica)

---

### TAREA 11: Ejemplos de Uso
**Archivo:** `examples/vwap_methodology_example.py` (NUEVO)
**Prioridad:** P2
**Tiempo estimado:** 1h

**Contenido:**
- Ejemplo completo de uso de indicadores VWAP
- Ejemplo de construcción de prompts
- Ejemplo de parsing de respuestas
- Ejemplo visual

**Criterios de Aceptación:**
- Código ejecutable
- Comentado
- Demuestra todas las features

---

### TAREA 12: Tests de Integración
**Archivo:** `tests/integration/test_vwap_integration.py` (NUEVO)
**Prioridad:** P0
**Tiempo estimado:** 2h

**Subtareas:**
1. [ ] Test flujo completo: datos → indicadores → prompt → parsing
2. [ ] Test con datos reales EURUSD
3. [ ] Test casos edge (choppy days, gaps, etc.)
4. [ ] Test performance

**Criterios de Aceptación:**
- Todos los tests pasan
- Cobertura > 85%
- Tests con datos reales

---

## 🔧 CONSIDERACIONES TÉCNICAS

### Reinicio de VWAP por Sesión
```python
def should_reset_vwap(current_time, last_reset_time, reset_hour_gmt):
    """
    Determina si VWAP debe reiniciarse
    
    Returns:
        bool: True si es inicio de nueva sesión
    """
    if last_reset_time is None:
        return True
    
    current_date = current_time.date()
    last_reset_date = last_reset_time.date()
    
    # Nuevo día
    if current_date > last_reset_date:
        if current_time.hour >= reset_hour_gmt:
            return True
    
    return False
```

### Cálculo de Pendiente VWAP
```python
def calculate_vwap_slope(vwap_series, lookback=10):
    """
    Calcula pendiente de VWAP
    
    Args:
        vwap_series: Serie de valores VWAP
        lookback: Períodos para calcular pendiente
    
    Returns:
        float: Pendiente (positiva/negativa)
        str: Descripción ("ascendente"/"descendente"/"plana")
    """
    if len(vwap_series) < lookback:
        return 0.0, "insuficiente"
    
    recent_vwap = vwap_series[-lookback:]
    slope = (recent_vwap.iloc[-1] - recent_vwap.iloc[0]) / lookback
    
    if slope > 0.00005:  # Umbral para EURUSD
        return slope, "ascendente"
    elif slope < -0.00005:
        return slope, "descendente"
    else:
        return slope, "plana"
```

### Timeframes y Ventanas de Datos

| Timeframe | Uso | Velas a Enviar | Desde |
|-----------|-----|----------------|-------|
| 1M | Timing micro | 200 velas | Sesión actual |
| 5M | Principal | Todas de sesión | 08:00 GMT |
| 1H | Contexto | 30 velas | Días anteriores |

---

## 📊 MÉTRICAS DE ÉXITO

- [ ] Todos los tests unitarios pasan (100%)
- [ ] Cobertura de código > 85%
- [ ] Indicadores VWAP calculados correctamente vs. referencia
- [ ] Prompts generados son parseables por IA
- [ ] Parser extrae correctamente respuestas IA
- [ ] Visualización clara y profesional
- [ ] Documentación completa
- [ ] Performance: cálculo de indicadores < 500ms

---

## 🚀 PRÓXIMOS PASOS (EJECUCIÓN)

1. **AHORA:** Crear rama `feature/vwap-methodology`
2. **HOY:** Tareas 1-3 (Indicadores core)
3. **HOY:** Tarea 5 (Prompts)
4. **HOY:** Tarea 6 (Parser)
5. **MAÑANA:** Tareas 7-9 (Config y visualización)
6. **MAÑANA:** Tareas 10-12 (Docs y tests)
7. **FINAL:** PR para revisión

---

## 📝 NOTAS

- Seguir estrictamente TDD (tests primero)
- Commits frecuentes y descriptivos
- Documentar inline todo el código
- Revisar que prompts NO se modifiquen en su naturaleza
- Validar con usuario antes de PR final

---

**Última actualización:** 17/11/2025 - Documento inicial
