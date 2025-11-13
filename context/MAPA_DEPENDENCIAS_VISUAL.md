# 🗺️ Mapa Visual de Dependencias - Botrading

**Fecha:** 13 de noviembre de 2025

---

## 🎯 FASE 2: IA y Estrategias

### Sprint 1: Fundamentos IA (Semanas 1-3)

```
┌─────────────────────────────────────────┐
│  🔴 ORDEN-1: Issue #26 - T10           │
│  Construcción de prompt IA              │
│  Estado: IN-PROGRESS                    │
│  Dependencias: NINGUNA                  │
│  Bloquea: TODO EL RESTO                 │
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐
│ ORDEN-2 │ │ ORDEN-3 │ │  ORDEN-4/5  │
│  #29    │ │  #27 ⚠️ │ │ #39 + #40   │
│  T13    │ │  T11    │ │ T23 + T24   │
│ Config  │ │ Tokens  │ │ Indicadores │
│   IA    │ │VERIFICAR│ │  [PARALELO] │
└─────────┘ └─────────┘ └─────────────┘
```

**Etiquetas utilizadas:**
- 🔴 ORDEN-1: `orden-01`, `bloqueante`, `in-progress`
- 🟡 ORDEN-2: `orden-02`
- ⚠️ ORDEN-3: `requiere-validacion` (Issue #27 cerrada pero in-progress)
- 🟢 ORDEN-4/5: `orden-04`, `orden-05`, `puede-paralelo`

---

### Sprint 2: Datos para IA (Semanas 4-5)

```
        ORDEN-4 + ORDEN-5 (PARALELO)
              ┌────────────────┐
              │   Issue #39    │
              │   T23          │
    ┌─────────┤   Indicadores  │
    │         │   Numéricos    │
    │         └────────────────┘
    │
    │         ┌────────────────┐
    │         │   Issue #40    │
    │         │   T24          │
    └─────────┤   Generación   │
              │   Imágenes     │
              └────────────────┘
                      │
                      ▼
              Bots Numéricos,
              Visuales e Híbridos
              con datos completos
```

**Pueden ejecutarse simultáneamente** si hay recursos.

---

### Sprint 3: Estrategia Dual (Semana 6)

```
┌─────────────────────────────────────────┐
│  🔶 ORDEN-6: Issue #30 - T14           │
│  Apertura simultánea Market/Limit       │
│  Dependencias: T10 (IA funcionando)     │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  ORDEN-7: Issue #31 - T15              │
│  Comparación Market vs Limit            │
│  Dependencias: T14 (dual funcionando)   │
└─────────────────────────────────────────┘
```

**Resultado:** Sistema dual Market/Limit operativo.

---

### Sprint 4: Reevaluación Básica (Semanas 7-8)

```
┌─────────────────────────────────────────┐
│  🔵 ORDEN-8: Issue #42 - T26           │
│  Reevaluación cada 10 minutos           │
│  Dependencias: T10 + T14                │
│  Bloquea: Gestión activa                │
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ ORDEN-9 │ │ORDEN-10 │ │ORDEN-11 │
│  #43    │ │  #28    │ │  #44    │
│  T27    │ │  T12    │ │  T28    │
│Aplicar  │ │Contexto │ │ Traza   │
│Decisión │ │  Conv.  │ │  Reev.  │
└─────────┘ └─────────┘ └─────────┘
```

**Resultado:** Gestión activa de operaciones con IA.

---

### Sprint 5: Reevaluación Completa (Semana 9)

```
        ORDEN-11 + ORDEN-12
              │
              ▼
┌─────────────────────────────────────────┐
│  ORDEN-12: Issue #32 - T16             │
│  Reevaluación dual independiente        │
│  Dependencias: T14 + T26                │
│  (Combina Dual + Reevaluación)          │
└─────────────────────────────────────────┘
              │
              ▼
      🎉 FASE 2 COMPLETA 🎉
```

**Resultado:** Sistema de IA completo con reevaluación dual.

---

## 💾 FASE 3: Persistencia y Métricas

### Sprint 6: Base de Datos (Semanas 10-11)

```
┌─────────────────────────────────────────┐
│  🟣 ORDEN-13: Issue #48 - T32          │
│  Persistencia de operaciones (SQLite)   │
│  Dependencias: T10 (operaciones)        │
│  Bloquea: TODO de Fase 3                │
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ORDEN-14 │ │ORDEN-15 │ │ORDEN-16 │
│  #49    │ │  #50    │ │  #58    │
│  T33    │ │  T34    │ │  T42    │
│Registro │ │Consol.  │ │Compar.  │
│Consultas│ │Métricas │ │Metodol. │
│   IA    │ │ Diarias │ │         │
└─────────┘ └─────────┘ └─────────┘
```

**Etiquetas utilizadas:**
- 🟣 ORDEN-13: `orden-13`, `bloqueante`, `P0`
- ORDEN-14/15/16: `orden-14/15/16`, `P0`/`P1`

**Resultado:** Sistema con persistencia completa y métricas.

---

## ✅ FASE 4: Calidad y Despliegue

### Sprint 7: Validación Final (Semana 12)

```
┌─────────────────────────────────────────┐
│  ⚫ ORDEN-17: Issue #67 - T51          │
│  Pruebas de integración E2E             │
│  Dependencias: TODO (Fase 2 + 3)        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  ORDEN-18: Issue #66 - T50             │
│  Roadmap y criterios de salida          │
│  Dependencias: T51 (tests)              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
        🚀 LISTO PARA DEMO/REAL 🚀
```

**Resultado:** Sistema validado y listo para producción.

---

## 🔄 Flujo Completo End-to-End

```
INICIO
  │
  ▼
🔴 ORDEN-1: IA Base (T10) ─────────┐
  │                               │
  ├─→ 🟡 ORDEN-2: Config (T13)    │
  ├─→ ⚠️ ORDEN-3: Tokens (T11)    │ Sprint 1
  │                               │ (3 sem)
  ├─→ 🟢 ORDEN-4: Indicadores      │
  └─→ 🟢 ORDEN-5: Imágenes ────────┘
        │
        ▼
  🔶 ORDEN-6: Dual Market/Limit ──┐
        │                         │ Sprint 3
  🔶 ORDEN-7: Comparación ─────────┘ (1 sem)
        │
        ▼
  🔵 ORDEN-8: Reevaluación 10min ─┐
        │                         │
  🔵 ORDEN-9: Aplicar decisión    │
  🔵 ORDEN-10: Contexto conv.     │ Sprint 4-5
  🔵 ORDEN-11: Trazabilidad       │ (3 sem)
  🔵 ORDEN-12: Reeval dual ───────┘
        │
        ▼
  🟣 ORDEN-13: BD Operaciones ────┐
        │                         │
  🟣 ORDEN-14: BD Consultas IA    │
  🟣 ORDEN-15: Métricas diarias   │ Sprint 6
  🟣 ORDEN-16: Comparación ───────┘ (2 sem)
        │
        ▼
  ⚫ ORDEN-17: Tests E2E ──────────┐
        │                         │ Sprint 7
  ⚫ ORDEN-18: Roadmap ────────────┘ (1 sem)
        │
        ▼
      FIN
```

**Tiempo total estimado:** 12 semanas (3 meses)

---

## 🚦 Semáforo de Criticidad

### 🔴 BLOQUEANTES (No pueden omitirse)
```
ORDEN-1  (T10) → Sin esto, NO HAY IA
ORDEN-6  (T14) → Sin esto, NO HAY DUAL
ORDEN-8  (T26) → Sin esto, NO HAY REEVALUACIÓN
ORDEN-13 (T32) → Sin esto, NO HAY PERSISTENCIA
```

### 🟡 IMPORTANTES (Pueden posponerse levemente)
```
ORDEN-2  (T13) → Mejora flexibilidad
ORDEN-10 (T12) → Mejora calidad IA
ORDEN-16 (T42) → Análisis comparativo
```

### 🟢 COMPLEMENTARIAS (Pueden ejecutarse en paralelo)
```
ORDEN-4 + ORDEN-5 → Datos IA
ORDEN-9 + ORDEN-10 → Gestión y contexto
ORDEN-14 + ORDEN-15 → BD complementaria
```

---

## ⚠️ Puntos de Atención

### Issue #27 (T11) - ORDEN-3
**Estado:** CERRADO pero etiqueta `in-progress`

**Opciones de resolución:**
```
┌─────────────────────────────────┐
│ Verificar estado real           │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
Implementado  No implementado
    │         │
    ▼         ▼
Remover de  REABRIR issue
análisis    Aplicar ORDEN-3
```

**Impacto si no está implementado:**
- Bloquea ORDEN-11 (T28) - Trazabilidad
- Bloquea ORDEN-14 (T33) - Registro consultas IA
- Afecta cálculo de métricas de Fase 3

---

## 📊 Métricas de Progreso Sugeridas

### Por Sprint
```
Sprint 1: [░░░░░░░░░░] 0/3 (0%)
Sprint 2: [░░░░░░░░░░] 0/2 (0%)
Sprint 3: [░░░░░░░░░░] 0/2 (0%)
Sprint 4: [░░░░░░░░░░] 0/3 (0%)
Sprint 5: [░░░░░░░░░░] 0/2 (0%)
Sprint 6: [░░░░░░░░░░] 0/4 (0%)
Sprint 7: [░░░░░░░░░░] 0/2 (0%)
```

### Global
```
Fase 2: [░░░░░░░░░░] 0/12 (0%)
Fase 3: [░░░░░░░░░░] 0/4  (0%)
Fase 4: [░░░░░░░░░░] 0/2  (0%)
TOTAL:  [░░░░░░░░░░] 0/18 (0%)
```

---

## 🎯 Reglas de Oro

### 1. Nunca Saltar Dependencias
❌ **INCORRECTO:** Empezar ORDEN-4 sin completar ORDEN-1  
✅ **CORRECTO:** Completar ORDEN-1, 2, 3 antes de ORDEN-4

### 2. Validar Antes de Avanzar
❌ **INCORRECTO:** Marcar completo sin tests  
✅ **CORRECTO:** Tests + Documentación + Revisión

### 3. Aprovechar Paralelización
❌ **INCORRECTO:** Hacer ORDEN-4 y ORDEN-5 secuencialmente  
✅ **CORRECTO:** Asignar a desarrolladores diferentes

### 4. Comunicar Bloqueos
❌ **INCORRECTO:** Quedarse bloqueado sin avisar  
✅ **CORRECTO:** Reportar bloqueo y pivotear si posible

---

## 📋 Checklist de Inicio de Cada ORDEN

Antes de empezar cualquier ORDEN, verificar:

- [ ] ✅ Todas las dependencias están 100% completas
- [ ] 🧪 Tests de dependencias pasan correctamente
- [ ] 📖 Documentación de dependencias existe
- [ ] 👀 Código revisado y aprobado
- [ ] 🏷️ Issue etiquetada correctamente
- [ ] 📊 Estimación de tiempo realizada
- [ ] 👥 Desarrollador asignado
- [ ] 🎯 Criterios de aceptación claros

---

## 🎉 Conclusión

Este mapa visual muestra la **ruta crítica** de implementación de las 18 issues pendientes.

**Clave del éxito:**
1. ✅ Seguir el orden numérico
2. ✅ No saltar dependencias
3. ✅ Validar continuamente
4. ✅ Aprovechar paralelización

**Próximo paso inmediato:**  
Completar **ORDEN-1** (Issue #26 - T10) que es la piedra angular del sistema.

---

**Generado:** 13 de noviembre de 2025  
**Herramienta:** GitHub Copilot  
**Referencia:** Sistema de etiquetado orden-01 a orden-18
