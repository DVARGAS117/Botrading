# 🎯 Orden de Implementación - Vista Rápida

**Última actualización:** 13 de noviembre de 2025

---

## 📊 Resumen Ejecutivo

- **Total de issues abiertas:** 16 (Fase 2 en adelante)
- **Orden de implementación:** 1-18
- **Tiempo estimado:** 10-12 semanas

---

## 🏗️ FASE 2: IA y Estrategias (12 issues)

### 🔴 Sprint 1: Fundamentos IA (2-3 semanas)

| Orden | Issue | Título | Prioridad | Dependencias | Estado |
|-------|-------|--------|-----------|--------------|--------|
| **1** | #26 | **[T10] Construcción de prompt IA** | P0 | NINGUNA | 🔴 IN-PROGRESS |
| **2** | #29 | [T13] Parametrización modelo IA | P1 | T10 | 🔴 OPEN |
| **3** | #27 | [T11] Registro tokens y costo | P0 | T10 | ⚠️ VERIFICAR |

**🎯 Entregable:** IA básica funcionando, bot puede tomar decisiones

---

### 🟡 Sprint 2: Datos para IA (1-2 semanas) - PARALELO

| Orden | Issue | Título | Prioridad | Dependencias | Paralelo |
|-------|-------|--------|-----------|--------------|----------|
| **4** | #39 | [T23] Cálculo indicadores | P1 | T10 | ✅ SÍ |
| **5** | #40 | [T24] Generación imágenes | P1 | T10 | ✅ SÍ |

**🎯 Entregable:** Bots numéricos, visuales e híbridos con datos completos

---

### 🟢 Sprint 3: Estrategia Dual (1 semana)

| Orden | Issue | Título | Prioridad | Dependencias | Estado |
|-------|-------|--------|-----------|--------------|--------|
| **6** | #30 | [T14] Apertura dual Market/Limit | P1 | T10 | 🔴 OPEN |
| **7** | #31 | [T15] Comparación Market vs Limit | P1 | T14 | 🔴 OPEN |

**🎯 Entregable:** Estrategia dual operativa

---

### 🔵 Sprint 4: Reevaluación Básica (2 semanas)

| Orden | Issue | Título | Prioridad | Dependencias | Estado |
|-------|-------|--------|-----------|--------------|--------|
| **8** | #42 | [T26] Reevaluación cada 10 min | P1 | T10, T14 | 🔴 OPEN |
| **9** | #43 | [T27] Aplicar decisión SL/TP | P1 | T26 | 🔴 OPEN |
| **10** | #28 | [T12] Contexto conversación | P1 | T10, T26 | 🔴 OPEN |

**🎯 Entregable:** Gestión activa de operaciones

---

### 🟣 Sprint 5: Reevaluación Completa (1 semana)

| Orden | Issue | Título | Prioridad | Dependencias | Estado |
|-------|-------|--------|-----------|--------------|--------|
| **11** | #44 | [T28] Trazabilidad reevaluación | P1 | T26, T11, T33 | 🔴 OPEN |
| **12** | #32 | [T16] Reevaluación dual independiente | P1 | T14, T26 | 🔴 OPEN |

**🎯 Entregable:** Fase 2 COMPLETA ✅

---

## 💾 FASE 3: Persistencia y Métricas (4 issues)

### 🟠 Sprint 6: Base de Datos y Análisis (2 semanas)

| Orden | Issue | Título | Prioridad | Dependencias | Estado |
|-------|-------|--------|-----------|--------------|--------|
| **13** | #48 | **[T32] Persistencia operaciones** | P0 | T10 | 🔴 OPEN |
| **14** | #49 | [T33] Registro consultas IA | P0 | T10, T11, T32 | 🔴 OPEN |
| **15** | #50 | [T34] Consolidación métricas | P0 | T32, T33 | 🔴 OPEN |
| **16** | #58 | [T42] Comparación metodologías | P1 | T34, T15 | 🔴 OPEN |

**🎯 Entregable:** Fase 3 COMPLETA ✅

---

## ✅ FASE 4: Calidad y Despliegue (2 issues)

### ⚫ Sprint 7: Validación Final (1-2 semanas)

| Orden | Issue | Título | Prioridad | Dependencias | Estado |
|-------|-------|--------|-----------|--------------|--------|
| **17** | #67 | [T51] Tests E2E por bot | P0 | TODO | 🔴 OPEN |
| **18** | #66 | [T50] Roadmap y criterios | P0 | T51 | 🔴 OPEN |

**🎯 Entregable:** Sistema listo para DEMO/REAL ✅

---

## 🗺️ Mapa de Dependencias Críticas

```
┌─────────────────────────────────────────────────────────┐
│                    ORDEN-1: T10 (IA)                    │
│              🔴 BASE DE TODO EL SISTEMA                 │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    ORDEN-2         ORDEN-4         ORDEN-6
    T13 (Config)    T23 (Indic.)    T14 (Dual)
        │           [PARALELO]           │
        │           ORDEN-5              │
        │           T24 (Img.)           │
        │               │                │
        └───────┬───────┴────────────┬───┘
                │                    │
                ▼                    ▼
            ORDEN-8              ORDEN-7
            T26 (Reeval)         T15 (Compar.)
                │
                ├──► ORDEN-9: T27
                ├──► ORDEN-10: T12
                ├──► ORDEN-11: T28
                └──► ORDEN-12: T16
                        │
                        ▼
                    ORDEN-13
                    T32 (BD) 🔴
                        │
                        ├──► ORDEN-14: T33
                        ├──► ORDEN-15: T34
                        └──► ORDEN-16: T42
                                │
                                ▼
                            ORDEN-17
                            T51 (E2E) 🔴
                                │
                                ▼
                            ORDEN-18
                            T50 (Roadmap)
```

---

## 🚦 Semáforo de Prioridades

### 🔴 CRÍTICAS - Empezar YA
- **ORDEN-1:** T10 - Construcción prompt IA (Issue #26) ← **EMPEZAR AQUÍ**
- **ORDEN-13:** T32 - Persistencia operaciones (Issue #48)
- **ORDEN-17:** T51 - Tests E2E (Issue #67)

### 🟡 IMPORTANTES - Siguiente Sprint
- **ORDEN-2:** T13 - Config modelo (Issue #29)
- **ORDEN-3:** T11 - Tokens (Issue #27) ← **VERIFICAR ESTADO**
- **ORDEN-4/5:** T23/T24 - Indicadores e imágenes (Issues #39, #40)

### 🟢 PUEDEN ESPERAR
- Todo lo demás depende de los anteriores

---

## ⚡ Oportunidades de Paralelización

### Pueden ejecutarse simultáneamente:

**Sprint 2:**
- ✅ ORDEN-4 (T23 - Indicadores) + ORDEN-5 (T24 - Imágenes)

**Sprint 4:**
- ✅ ORDEN-9 (T27) + ORDEN-10 (T12) si ORDEN-8 está completo

**Sprint 6:**
- ✅ ORDEN-14 (T33) + ORDEN-15 (T34) si ORDEN-13 está completo

---

## 📋 Checklist de Inicio

Antes de empezar cada ORDEN, verificar:

- [ ] ✅ **Todas las dependencias están 100% completadas**
- [ ] 🧪 **Tests de las dependencias pasan**
- [ ] 📖 **Documentación de dependencias existe**
- [ ] 🔍 **Revisión de código de dependencias aprobada**

---

## 🎯 Próximas Acciones

### Hoy (13 nov 2025):
1. ✅ Ejecutar script `aplicar_etiquetas_orden.ps1`
2. ⚠️ Verificar estado real de Issue #27 (T11)
3. 🔴 Enfocarse en ORDEN-1 (T10) si no está 100% completo

### Esta semana:
1. Completar Sprint 1 (ORDEN 1-3)
2. Planificar Sprint 2 (ORDEN 4-5)

### Este mes:
1. Completar Fase 2 (ORDEN 1-12)
2. Iniciar Fase 3 (ORDEN 13)

---

## 📊 Métricas de Progreso

### Por Sprint
- **Sprint 1 (Fundamentos IA):** 0/3 (0%)
- **Sprint 2 (Datos IA):** 0/2 (0%)
- **Sprint 3 (Dual):** 0/2 (0%)
- **Sprint 4 (Reeval Básica):** 0/3 (0%)
- **Sprint 5 (Reeval Completa):** 0/2 (0%)
- **Sprint 6 (Persistencia):** 0/4 (0%)
- **Sprint 7 (Validación):** 0/2 (0%)

### Por Fase
- **Fase 2:** 0/12 (0%)
- **Fase 3:** 0/4 (0%)
- **Fase 4:** 0/2 (0%)

### Global
- **Total:** 0/18 (0%)
- **Tiempo estimado restante:** 10-12 semanas

---

## ⚠️ Notas Importantes

### Issue #27 (T11) - REQUIERE ATENCIÓN
- Estado en GitHub: CERRADO
- Etiqueta: in-progress
- **ACCIÓN:** Verificar si realmente está implementado antes de continuar con ORDEN-3

### Issue #26 (T10) - EN PROGRESO
- Estado: IN-PROGRESS
- **Crítico:** Es la base de todo
- **Prioridad:** Completar antes que todo lo demás

---

## 🎉 Hitos Clave

| Sprint | Hito | Fecha Objetivo | Entregable |
|--------|------|----------------|------------|
| 1 | IA Básica | Semana 3 | Bot puede decidir |
| 2 | Datos Completos | Semana 5 | Indicadores + Imágenes |
| 3 | Dual Operativa | Semana 6 | Market + Limit funcionando |
| 4 | Reevaluación Básica | Semana 8 | Gestión activa SL/TP |
| 5 | Fase 2 Completa | Semana 9 | Sistema IA completo ✅ |
| 6 | Persistencia | Semana 11 | BD + Métricas ✅ |
| 7 | Validación E2E | Semana 12 | Listo para DEMO ✅ |

---

**📌 RECORDATORIO:**  
Este orden está basado en **dependencias técnicas reales**.  
**NO saltarse pasos** para evitar bloqueos y retrabajos.

---

**Documento generado:** 13 de noviembre de 2025  
**Analista:** GitHub Copilot  
**Referencia completa:** `ORDEN_PRIORIDAD_ISSUES.md`
