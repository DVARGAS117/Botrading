# 🎯 Análisis de Orden y Dependencias - Issues Abiertas

**Fecha de análisis:** 13 de noviembre de 2025  
**Rama:** desarrollo  
**Enfoque:** Fase 2 en adelante

---

## 📊 Resumen Ejecutivo

### Estado General
- **Fase 1:** ✅ **COMPLETADA AL 100%** (T19 y T21 ya cerrados)
- **Fase 2:** 🔴 **11 issues abiertas** (0% completado)
- **Fase 3:** 🔴 **3 issues abiertas** (33% completado - solo métricas diarias)
- **Fase 4:** 🔴 **2 issues abiertas** (0% completado)

### Prioridad de Ejecución
Este documento establece el **orden numérico** de implementación basado en:
1. **Dependencias técnicas** entre componentes
2. **Criticidad funcional** (P0 vs P1)
3. **Flujo lógico** del sistema (datos → IA → ejecución → persistencia)

---

## 🎯 FASE 2: IA y Estrategias (11 issues)

### 🔴 GRUPO 1: Fundamentos de IA (Prioridad Máxima)
**Deben implementarse PRIMERO** porque todo el resto depende de ellos.

#### **ORDEN-1** | Issue #26 - [T10] Construcción de prompt y recepción de JSON de decisión
- **Fase:** 2
- **Prioridad:** P0 (Crítica)
- **Estado:** 🔴 OPEN (in-progress)
- **Dependencias:** NINGUNA
- **Bloquea a:** TODO (es la base del sistema de IA)

**¿Por qué es primero?**
- Sin esto, no hay decisiones de la IA
- Todos los demás tickets de IA/Reevaluación/Dual dependen de este
- Es el corazón del sistema de trading

**Criterios de aceptación:**
```gherkin
Dado que el bot prepara payload numérico/visual según su tipo
Cuando envía el prompt a Gemini 2.5 Pro con parámetros configurados
Entonces recibe una respuesta JSON válida con dirección, SL, TP y riesgo
```

**Componentes a crear:**
- `src/core/ai_prompt_builder.py` (construcción de prompts)
- `src/core/gemini_client.py` (cliente API Gemini)
- `tests/unit/test_ai_prompt_builder.py`
- `tests/unit/test_gemini_client.py`

---

#### **ORDEN-2** | Issue #29 - [T13] Parametrización de modelo y tiempo de espera
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T10 (necesita cliente IA funcionando)
- **Bloquea a:** Operación productiva robusta

**¿Por qué es segundo?**
- Complementa T10 con configurabilidad
- Permite experimentar sin cambiar código
- Necesario antes de escalar a múltiples bots

**Criterios de aceptación:**
```gherkin
Dado que el archivo de configuración define modelo, temperatura, max tokens y timeout
Cuando se actualiza la configuración
Entonces la siguiente llamada a IA usa los nuevos parámetros
```

**Componentes a crear:**
- Extensión de `ia_config_manager.py` (ya existe pero hay que validar)
- Tests adicionales en `test_ia_config_manager.py`

---

#### **ORDEN-3** | Issue #27 - [T11] Registro de tokens y costo por consulta (CERRADO pero sin implementar)
- **Fase:** 2
- **Prioridad:** P0 (Crítica)
- **Estado:** ✅ CLOSED (pero marcado como in-progress, revisar)
- **Dependencias:** T10 (necesita respuestas de IA)
- **Bloquea a:** T33, T34 (persistencia y métricas)

**NOTA IMPORTANTE:** Esta issue aparece CERRADA pero con etiqueta "in-progress". Hay que verificar si realmente está implementada.

**¿Por qué es tercero?**
- Necesita que T10 esté funcionando para capturar datos de IA
- Crítico para análisis de costos
- Base para métricas de Fase 3

**Criterios de aceptación:**
```gherkin
Dado que se realiza una consulta a IA
Cuando el proveedor devuelve uso de tokens input/output y costo
Entonces se persiste tokens y costo asociados a la operación o reevaluación
```

---

### 🟡 GRUPO 2: Indicadores y Datos (Soporte a IA)
**Pueden ejecutarse en PARALELO** después del Grupo 1.

#### **ORDEN-4** | Issue #39 - [T23] Cálculo y formato de indicadores por timeframe
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T10 (necesita saber formato de entrada IA)
- **Bloquea a:** Bots numéricos, T25 (entradas híbridas)

**¿Por qué ORDEN-4?**
- Los indicadores alimentan los prompts de T10
- Puede trabajarse en paralelo con T11 si T10 está listo
- Necesario para bots numéricos e híbridos

**Criterios de aceptación:**
```gherkin
Dado que existen velas cerradas 5M, 15M y 1H
Cuando el bot numérico calcula EMA 20/50, RSI, MACD y volumen
Entonces construye un JSON consistente para la IA por cada timeframe
```

**Componentes a crear:**
- `src/core/indicator_calculator.py` (cálculo de indicadores)
- `src/core/indicator_formatter.py` (formateo para IA)
- `tests/unit/test_indicator_calculator.py`
- `tests/unit/test_indicator_formatter.py`

---

#### **ORDEN-5** | Issue #40 - [T24] Generación de imágenes por timeframe
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T10 (necesita saber formato de entrada IA)
- **Bloquea a:** Bots visuales, T25 (entradas híbridas)

**¿Por qué ORDEN-5?**
- Independiente de T23 (indicadores numéricos)
- Puede trabajarse en PARALELO con T23
- Necesario para bots visuales e híbridos

**Criterios de aceptación:**
```gherkin
Dado que el bot visual tiene configurado estilo con/sin indicadores
Cuando genera imágenes de 5M, 15M y 1H
Entonces produce archivos compatibles con Gemini con el estilo definido
```

**Componentes a crear:**
- `src/core/chart_generator.py` (generación de gráficos)
- `src/core/image_formatter.py` (preparación para IA)
- `tests/unit/test_chart_generator.py`
- `tests/unit/test_image_formatter.py`

---

### 🟢 GRUPO 3: Dual Market/Limit (Estrategia Dual)
**Requiere T10 funcionando** para tomar decisiones.

#### **ORDEN-6** | Issue #30 - [T14] Apertura simultánea de órdenes Market y Limit
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T10 (necesita decisión de IA)
- **Bloquea a:** T15, T16 (comparación y reevaluación dual)

**¿Por qué ORDEN-6?**
- Requiere que la IA funcione (T10)
- Base de la estrategia dual market/limit
- Independiente de indicadores (T23/T24)

**Criterios de aceptación:**
```gherkin
Dado que la IA decide OPERAR con parámetros válidos
Cuando el bot ejecuta la apertura
Entonces se crean dos órdenes: una Market y una Limit con mismos SL/TP y riesgo
```

**Componentes a crear:**
- `src/core/dual_order_executor.py` (ejecución dual)
- `tests/unit/test_dual_order_executor.py`

---

#### **ORDEN-7** | Issue #31 - [T15] Registro y comparación de desempeño Market vs Limit
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T14 (necesita órdenes duales existiendo)
- **Bloquea a:** Análisis de efectividad

**¿Por qué ORDEN-7?**
- Complementa T14 con análisis
- Puede hacerse DESPUÉS de T14
- Necesita persistencia (T32) para ser útil

**Criterios de aceptación:**
```gherkin
Dado que existen resultados P/L para ambos tipos de orden
Cuando se consolidan métricas por operación y por día
Entonces queda disponible la comparación de P/L y activación entre Market y Limit
```

**Componentes a crear:**
- `src/core/dual_performance_tracker.py`
- `tests/unit/test_dual_performance_tracker.py`

---

### 🔵 GRUPO 4: Reevaluación (Gestión Activa)
**Crítico para gestión de riesgo**, requiere T10 + T14.

#### **ORDEN-8** | Issue #42 - [T26] Reevaluación cada 10 minutos con datos actualizados
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T10 (necesita consultas a IA), T14 (necesita operaciones abiertas)
- **Bloquea a:** T27, T28, T16 (gestión y trazabilidad)

**¿Por qué ORDEN-8?**
- Base del ciclo de reevaluación
- Requiere IA funcionando y operaciones abiertas
- Crítico para gestión activa de riesgo

**Criterios de aceptación:**
```gherkin
Dado que existe una posición abierta
Cuando se cumple el intervalo de 10 minutos desde la última reevaluación
Entonces el bot envía nueva evaluación con velas cerradas e indicadores actuales
```

**Componentes a crear:**
- `src/core/reevaluation_scheduler.py`
- `src/core/reevaluation_engine.py`
- `tests/unit/test_reevaluation_scheduler.py`
- `tests/unit/test_reevaluation_engine.py`

---

#### **ORDEN-9** | Issue #43 - [T27] Aplicación de decisión de actualizar SL/TP o cerrar
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T26 (necesita reevaluaciones existiendo)
- **Bloquea a:** Operación productiva completa

**¿Por qué ORDEN-9?**
- Ejecuta las decisiones de T26
- Complemento directo de la reevaluación
- Necesario para cerrar el ciclo de vida de operaciones

**Criterios de aceptación:**
```gherkin
Dado que la IA devuelve una decisión de gestión
Cuando la decisión es actualizar SL/TP o cerrar
Entonces el bot ejecuta la acción en MT5 y registra el resultado
```

**Componentes a crear:**
- Extensión de `order_manager.py` (ya existe, agregar funciones)
- Tests adicionales en `test_order_manager.py`

---

#### **ORDEN-10** | Issue #28 - [T12] Mantenimiento de contexto de conversación en reevaluación
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T10 (cliente IA), T26 (reevaluación)
- **Bloquea a:** Mejora de calidad de decisiones IA

**¿Por qué ORDEN-10?**
- Mejora la IA pero no es crítico
- Puede agregarse DESPUÉS de tener reevaluación básica
- Requiere modificar el cliente de Gemini (T10)

**Criterios de aceptación:**
```gherkin
Dado que existe un ID de conversación previo para la operación
Cuando el bot envía una reevaluación
Entonces la IA recibe y utiliza el contexto histórico de esa operación
```

**Componentes a crear:**
- Extensión de `gemini_client.py` (contexto conversacional)
- `src/core/conversation_manager.py`
- Tests correspondientes

---

#### **ORDEN-11** | Issue #44 - [T28] Registro de trazabilidad de cada reevaluación
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T26 (reevaluaciones), T11 (registro tokens), T33 (persistencia IA)
- **Bloquea a:** Auditoría completa

**¿Por qué ORDEN-11?**
- Auditoría y trazabilidad
- Puede agregarse al final de Fase 2
- Depende de persistencia (T33)

**Criterios de aceptación:**
```gherkin
Dado que se realizó una reevaluación
Cuando se persisten decisión, tokens y costos
Entonces la operación queda con historial completo de reevaluaciones
```

**Componentes a crear:**
- Extensión de modelo de persistencia
- `src/core/reevaluation_auditor.py`
- Tests correspondientes

---

#### **ORDEN-12** | Issue #32 - [T16] Reevaluación independiente de Market y Limit
- **Fase:** 2
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T14 (dual), T26 (reevaluación base)
- **Bloquea a:** Estrategia dual completa

**¿Por qué ORDEN-12?**
- Combina dual + reevaluación
- Requiere ambos componentes funcionando
- Último componente de Fase 2

**Criterios de aceptación:**
```gherkin
Dado que hay un par Market y Limit abiertos
Cuando el bot solicita reevaluación para cada uno
Entonces puede mantener, actualizar o cerrar cada orden de manera independiente
```

**Componentes a crear:**
- Extensión de `reevaluation_engine.py` (reevaluación dual)
- Tests adicionales

---

## 💾 FASE 3: Persistencia y Métricas (3 issues)

### 🟣 GRUPO 5: Base de Datos (Fundamento)

#### **ORDEN-13** | Issue #48 - [T32] Persistencia de operaciones con parámetros y estados
- **Fase:** 3
- **Prioridad:** P0 (Crítica)
- **Estado:** 🔴 OPEN
- **Dependencias:** T10 (operaciones existiendo)
- **Bloquea a:** T33, T34 (todo lo demás de Fase 3)

**¿Por qué ORDEN-13?**
- **BASE DE DATOS principal**
- Sin esto, no hay trazabilidad ni métricas
- Debe implementarse ANTES de T33 y T34

**Criterios de aceptación:**
```gherkin
Dado que se abre o modifica una operación
Cuando se registra en SQLite con índices definidos
Entonces quedan almacenados parámetros, estados, tiempos y resultados
```

**Componentes a crear:**
- `src/db/operations_repository.py`
- `src/db/models/operation.py`
- `src/db/migrations/create_operations_table.sql`
- `tests/unit/test_operations_repository.py`
- `tests/integration/test_operations_persistence.py`

---

#### **ORDEN-14** | Issue #49 - [T33] Registro de consultas a IA con prompts, respuesta, tokens y costo
- **Fase:** 3
- **Prioridad:** P0 (Crítica)
- **Estado:** 🔴 OPEN
- **Dependencias:** T10 (consultas IA), T11 (cálculo tokens), T32 (BD)
- **Bloquea a:** T34 (métricas incluyen costos IA)

**¿Por qué ORDEN-14?**
- Complementa T32 con datos de IA
- Necesita BD funcionando (T32)
- Necesita T11 para capturar tokens

**Criterios de aceptación:**
```gherkin
Dado que se envía una consulta a IA
Cuando se recibe la respuesta
Entonces se guarda prompt, respuesta, tokens, costo y referencias a la operación
```

**Componentes a crear:**
- `src/db/ai_queries_repository.py`
- `src/db/models/ai_query.py`
- `src/db/migrations/create_ai_queries_table.sql`
- `tests/unit/test_ai_queries_repository.py`

---

#### **ORDEN-15** | Issue #50 - [T34] Consolidación de métricas diarias por bot
- **Fase:** 3
- **Prioridad:** P0 (Crítica)
- **Estado:** 🔴 OPEN
- **Dependencias:** T32 (operaciones), T33 (costos IA)
- **Bloquea a:** T42 (comparación metodologías)

**¿Por qué ORDEN-15?**
- Análisis agregado
- Requiere datos de T32 y T33
- Genera las métricas para dashboards

**Criterios de aceptación:**
```gherkin
Dado que existen operaciones y consultas registradas en el día
Cuando se ejecuta el consolidado diario
Entonces se calculan winrate, profit factor, P/L por tipo de orden y costo IA
```

**Componentes a crear:**
- `src/analytics/metrics_consolidator.py`
- `src/db/models/daily_metrics.py`
- `src/db/migrations/create_daily_metrics_table.sql`
- `tests/unit/test_metrics_consolidator.py`

---

#### **ORDEN-16** | Issue #58 - [T42] Comparación de desempeño entre metodologías
- **Fase:** 3
- **Prioridad:** P1 (Alta)
- **Estado:** 🔴 OPEN
- **Dependencias:** T34 (métricas diarias), T15 (comparación dual)
- **Bloquea a:** Decisiones de continuidad

**¿Por qué ORDEN-16?**
- Análisis comparativo
- Requiere métricas consolidadas (T34)
- No crítico para operación, sí para análisis

**Criterios de aceptación:**
```gherkin
Dado que existen métricas para bots numéricos, visuales e híbridos
Cuando se consulta el comparativo
Entonces se muestran indicadores clave por bot para decisiones de continuidad
```

**Componentes a crear:**
- `src/analytics/methodology_comparator.py`
- `tests/unit/test_methodology_comparator.py`

---

## ✅ FASE 4: Calidad y Despliegue (2 issues)

### ⚫ GRUPO 6: Validación Final

#### **ORDEN-17** | Issue #67 - [T51] Pruebas de integración E2E por bot
- **Fase:** 4
- **Prioridad:** P0 (Crítica)
- **Estado:** 🔴 OPEN
- **Dependencias:** TODO de Fase 2 y 3
- **Bloquea a:** Paso a producción

**¿Por qué ORDEN-17?**
- **Tests de integración completos**
- Requiere todo funcionando
- Valida extremo a extremo

**Criterios de aceptación:**
```gherkin
Dado que Bot 1 está implementado
Cuando se ejecutan pruebas de integración extremo a extremo
Entonces se valida la cadena datos→IA→ejecución→persistencia antes de avanzar
```

**Componentes a crear:**
- `tests/e2e/test_bot1_full_cycle.py`
- `tests/e2e/test_bot_reevaluation_flow.py`
- `tests/e2e/test_dual_orders_lifecycle.py`

---

#### **ORDEN-18** | Issue #66 - [T50] Avance por fases con criterios de salida
- **Fase:** 4
- **Prioridad:** P0 (Crítica)
- **Estado:** 🔴 OPEN
- **Dependencias:** T51 (validación E2E)
- **Bloquea a:** NADA (es gestión de proyecto)

**¿Por qué ORDEN-18?**
- **Gestión de proyecto**
- Se ejecuta continuamente
- Documenta avance y criterios

**Criterios de aceptación:**
```gherkin
Dado que el roadmap define fases y entregables
Cuando un entregable cumple sus criterios
Entonces la fase se da por completada y se inicia la siguiente
```

**Componentes a crear:**
- Documentación de criterios de salida
- Checklists de validación
- Plan de migración a producción

---

## 📊 Resumen de Dependencias por Grupos

### Gráfico de Dependencias

```
FASE 2: IA y Estrategias
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Grupo 1: Fundamentos IA
┌──────────────┐
│  ORDEN-1     │
│  T10 (IA)    │ ◄── BASE DE TODO
└──────┬───────┘
       │
       ├──► ORDEN-2: T13 (Config IA)
       ├──► ORDEN-3: T11 (Tokens)
       │
       └──► Grupo 2: Indicadores
            ├──► ORDEN-4: T23 (Indicadores) ◄── Paralelo
            └──► ORDEN-5: T24 (Imágenes)    ◄── Paralelo
       
       └──► Grupo 3: Dual
            ├──► ORDEN-6: T14 (Apertura Dual)
            └──► ORDEN-7: T15 (Comparación)
       
       └──► Grupo 4: Reevaluación
            ├──► ORDEN-8: T26 (Ciclo 10min)
            ├──► ORDEN-9: T27 (Aplicar decisión)
            ├──► ORDEN-10: T12 (Contexto)
            ├──► ORDEN-11: T28 (Trazabilidad)
            └──► ORDEN-12: T16 (Reeval Dual)

FASE 3: Persistencia
━━━━━━━━━━━━━━━━━━━━━━

Grupo 5: Base de Datos
┌──────────────┐
│  ORDEN-13    │
│  T32 (BD)    │ ◄── BASE PERSISTENCIA
└──────┬───────┘
       │
       ├──► ORDEN-14: T33 (BD IA)
       ├──► ORDEN-15: T34 (Métricas)
       └──► ORDEN-16: T42 (Comparación)

FASE 4: Calidad
━━━━━━━━━━━━━━━━━

Grupo 6: Validación
ORDEN-17: T51 (Tests E2E) ◄── Requiere TODO
ORDEN-18: T50 (Roadmap)   ◄── Continuo
```

---

## 🎯 Plan de Implementación Recomendado

### Sprint 1: Fundamentos IA (2-3 semanas)
- ✅ **ORDEN-1:** T10 - Construcción de prompt y cliente Gemini
- ✅ **ORDEN-2:** T13 - Parametrización de modelo
- ✅ **ORDEN-3:** T11 - Registro de tokens (verificar si ya está)

**Objetivo:** IA básica funcionando, bot puede tomar decisiones

---

### Sprint 2: Datos para IA (1-2 semanas)
**EN PARALELO:**
- ✅ **ORDEN-4:** T23 - Cálculo de indicadores
- ✅ **ORDEN-5:** T24 - Generación de imágenes

**Objetivo:** Bots numéricos, visuales e híbridos con datos completos

---

### Sprint 3: Estrategia Dual (1 semana)
- ✅ **ORDEN-6:** T14 - Apertura dual Market/Limit
- ✅ **ORDEN-7:** T15 - Comparación de desempeño

**Objetivo:** Estrategia dual operativa

---

### Sprint 4: Reevaluación Básica (2 semanas)
- ✅ **ORDEN-8:** T26 - Ciclo de reevaluación cada 10min
- ✅ **ORDEN-9:** T27 - Aplicar decisiones SL/TP
- ✅ **ORDEN-10:** T12 - Contexto conversacional (opcional, P1)

**Objetivo:** Gestión activa de operaciones

---

### Sprint 5: Reevaluación Completa (1 semana)
- ✅ **ORDEN-11:** T28 - Trazabilidad reevaluación
- ✅ **ORDEN-12:** T16 - Reevaluación dual independiente

**Objetivo:** Fase 2 COMPLETA

---

### Sprint 6: Persistencia (2 semanas)
- ✅ **ORDEN-13:** T32 - Base de datos operaciones
- ✅ **ORDEN-14:** T33 - Base de datos consultas IA
- ✅ **ORDEN-15:** T34 - Consolidación métricas diarias
- ✅ **ORDEN-16:** T42 - Comparación metodologías

**Objetivo:** Fase 3 COMPLETA

---

### Sprint 7: Validación Final (1-2 semanas)
- ✅ **ORDEN-17:** T51 - Tests E2E
- ✅ **ORDEN-18:** T50 - Documentación y criterios

**Objetivo:** Sistema listo para DEMO/REAL

---

## 🏷️ Sistema de Etiquetado Propuesto

### Etiquetas Numéricas para GitHub

Crear etiquetas con este formato:
- `orden-01` hasta `orden-18` (color: azul `#0366d6`)

### Etiquetas de Dependencias
- `bloqueado-por-T##` (color: rojo `#d73a49`)
- `bloquea-a-T##` (color: naranja `#f1a208`)

### Etiquetas de Paralelización
- `puede-paralelo` (color: verde `#28a745`)

---

## 📋 Acciones Inmediatas Recomendadas

### 1. Crear Etiquetas Numéricas
```bash
# Crear etiquetas ORDEN-01 a ORDEN-18
gh label create "orden-01" --color "0366d6" -R DVARGAS117/Botrading
gh label create "orden-02" --color "0366d6" -R DVARGAS117/Botrading
# ... hasta orden-18
```

### 2. Aplicar Etiquetas a Issues
```bash
# Ejemplo para T10 (ORDEN-1)
gh issue edit 26 --add-label "orden-01" -R DVARGAS117/Botrading

# Ejemplo para T13 (ORDEN-2)
gh issue edit 29 --add-label "orden-02,bloqueado-por-T10" -R DVARGAS117/Botrading
```

### 3. Verificar T11 (Issue #27)
**URGENTE:** Issue #27 aparece CERRADA pero con etiqueta "in-progress"
```bash
# Verificar estado real
gh issue view 27 -R DVARGAS117/Botrading
```

### 4. Priorizar Sprint 1
Enfocarse en:
- **ORDEN-1:** T10 (ya en progreso)
- **ORDEN-2:** T13
- **ORDEN-3:** T11 (verificar estado)

---

## 💡 Recomendaciones Estratégicas

### 1. **Enfoque Incremental**
- ✅ Completar cada ORDEN antes de pasar al siguiente
- ✅ Los grupos pueden ejecutarse en PARALELO (Ej: T23 y T24)
- ❌ NO saltar dependencias

### 2. **Validación Continua**
- Cada ORDEN debe tener tests unitarios
- Ejecutar tests de integración al completar cada Sprint
- Documentar al completar (no al final)

### 3. **Revisión de Bloqueos**
- Antes de empezar un ORDEN, verificar que sus dependencias estén **100% completas**
- Si un ORDEN se bloquea, pivotear a otro del mismo grupo si existe

### 4. **Persistencia Temprana (Opcional)**
- **Consideración:** Podría implementarse T32 (BD) en Sprint 2-3 para capturar datos desde el inicio
- **Ventaja:** Datos históricos desde el primer bot operativo
- **Desventaja:** Añade complejidad temprana

---

## 📊 Métricas de Progreso

### Por Fase
- **Fase 2:** 0/12 issues (0%)
- **Fase 3:** 1/4 issues (25%) - Solo T41 (métricas diarias) cerrado
- **Fase 4:** 0/2 issues (0%)

### Por Prioridad
- **P0:** 5/18 issues abiertas críticas
- **P1:** 11/18 issues abiertas importantes

### Tiempo Estimado Total
- **Optimista:** 8 semanas (2 meses)
- **Realista:** 10-12 semanas (3 meses)
- **Conservador:** 14-16 semanas (4 meses)

---

## 🎉 Conclusión

Este plan establece un **orden lógico y técnico** para implementar las 18 issues abiertas:

1. **Clara jerarquía de dependencias**
2. **Oportunidades de paralelización**
3. **Sprints incrementales validables**
4. **Sistema de etiquetado numérico 1-18**

**Próximo paso:** Aplicar etiquetas `orden-##` a todas las issues y comenzar con **ORDEN-1** (T10).

---

**Documento generado:** 13 de noviembre de 2025  
**Analista:** GitHub Copilot  
**Versión:** 1.0
