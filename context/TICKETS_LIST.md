# 📋 Listado Completo de Tickets Botrading

**Total: 52 Tickets organizados en 16 Épicas**

---

## 📌 Épica 1: Orquestación (5 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 1 | Ejecución de ciclo por bot a inicio de hora | 1 | P0 | 📝 |
| 2 | Aplicación de filtros de horario y días hábiles | 1 | P0 | 📝 |
| 3 | Instancias independientes por bot | 1 | P0 | 📝 |
| 4 | Verificación de operación abierta por activo y Magic Number | 1 | P0 | 📝 |
| 5 | Parámetros globales centralizados | 1 | P0 | 📝 |

---

## 🔗 Épica 2: Integración MT5 (4 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 6 | Verificación de conexión MT5 al inicio | 1 | P0 | 📝 |
| 7 | Extracción de velas cerradas OHLCV por timeframe | 1 | P0 | 📝 |
| 8 | Consulta de posiciones por símbolo y Magic Number | 1 | P0 | 📝 |
| 9 | Envío de órdenes y gestión de SL/TP/cierre | 1 | P0 | 📝 |

---

## 🧠 Épica 3: IA (Gemini) (4 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 10 | Construcción de prompt y recepción de JSON de decisión | 2 | P0 | 📝 |
| 11 | Registro de tokens y costo por consulta | 2 | P0 | 📝 |
| 12 | Mantenimiento de contexto de conversación en reevaluación | 2 | P1 | 📝 |
| 13 | Parametrización de modelo y tiempo de espera | 2 | P1 | 📝 |

---

## 👯 Épica 4: Dual Market/Limit (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 14 | Apertura simultánea de órdenes Market y Limit | 2 | P1 | 📝 |
| 15 | Registro y comparación de desempeño Market vs Limit | 2 | P1 | 📝 |
| 16 | Reevaluación independiente de Market y Limit | 2 | P1 | 📝 |

---

## 🎫 Épica 5: Magic Numbers (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 17 | Generación de Magic Number único con estructura | 1 | P0 | 📝 |
| 18 | Decodificación de Magic Number para auditoría | 1 | P0 | 📝 |
| 19 | Filtrado de posiciones por Magic Number en MT5 | 1 | P0 | 📝 |

---

## 🌐 Épica 6: Multi-activo (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 20 | Administración de lista de activos en configuración | 1 | P0 | 📝 |
| 21 | Garantía de una sola operación por activo y evento | 1 | P0 | 📝 |
| 22 | Iteración determinista de activos | 1 | P0 | 📝 |

---

## 📈 Épica 7: Indicadores e imágenes (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 23 | Cálculo y formato de indicadores por timeframe | 2 | P1 | 📝 |
| 24 | Generación de imágenes por timeframe con estilos consistentes | 2 | P1 | 📝 |
| 25 | Alternancia entre entradas numéricas, visuales o híbridas | 2 | P1 | 📝 |

---

## 🔄 Épica 8: Reevaluación (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 26 | Reevaluación cada 10 minutos con datos actualizados | 2 | P1 | 📝 |
| 27 | Aplicación de decisión de actualizar SL/TP o cerrar | 2 | P1 | 📝 |
| 28 | Registro de trazabilidad de cada reevaluación | 2 | P1 | 📝 |

---

## 💰 Épica 9: Riesgo y conversión de activos (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 29 | Cálculo de lote por % riesgo y distancia al SL | 2 | P0 | 📝 |
| 30 | Ajuste de lote a step y límites del símbolo | 2 | P0 | 📝 |
| 31 | Obtención de especificaciones del símbolo desde MT5 | 2 | P0 | 📝 |

---

## 💾 Épica 10: Persistencia y trazabilidad (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 32 | Persistencia de operaciones con parámetros y estados | 3 | P0 | 📝 |
| 33 | Registro de consultas a IA con prompts, respuesta, tokens y costo | 3 | P0 | 📝 |
| 34 | Consolidación de métricas diarias por bot | 3 | P0 | 📝 |

---

## 🕐 Épica 11: Filtros y horarios (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 35 | Validación de hora local de Lima y días hábiles | 0 | P0 | 📝 |
| 36 | Activación de filtros futuros vía configuración | 0 | P1 | 📝 |
| 37 | Espera por cierre de vela antes de extraer datos | 0 | P0 | 📝 |

---

## ⚠️ Épica 12: Errores y logging (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 38 | Reintentos automáticos con backoff | 1 | P0 | 📝 |
| 39 | Logging por bot y nivel | 1 | P0 | 📝 |
| 40 | Registro de errores de parsing de IA | 1 | P1 | 📝 |

---

## 📊 Épica 13: Métricas y monitoreo (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 41 | Disponibilización de métricas diarias por bot | 3 | P1 | 📝 |
| 42 | Comparación de desempeño entre metodologías | 3 | P1 | 📝 |
| 43 | Monitoreo de estado y logs de cada bot | 3 | P1 | ✅ |

---

## ⚙️ Épica 14: Configuración y modularidad (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 44 | Gestión de credenciales y parámetros en JSON | 0 | P0 | 📝 |
| 45 | Reutilización de módulos core | 0 | P0 | 📝 |
| 46 | Tests unitarios por componente | 0 | P0 | 📝 |

---

## 🔐 Épica 15: Seguridad y cuentas/APIs (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 47 | Almacenamiento seguro de credenciales | 0 | P0 | 📝 |
| 48 | Validación de cuota y disponibilidad de modelo IA | 0 | P1 | 📝 |
| 49 | Alternancia de configuraciones de IA por bot | 0 | P1 | 📝 |

---

## ✅ Épica 16: Roadmap y calidad (3 tickets)

| # | Ticket | Fase | Prioridad | Estado |
|---|--------|------|-----------|--------|
| 50 | Avance por fases con criterios de salida | 4 | P0 | 📝 |
| 51 | Pruebas de integración E2E por bot | 4 | P0 | 📝 |
| 52 | Operación en demo antes de real | 4 | P0 | 📝 |

---

## 📊 Resumen Estadístico

### Por Fase
- **Fase 0:** 9 tickets (Fundamentos)
- **Fase 1:** 18 tickets (Núcleo)
- **Fase 2:** 16 tickets (IA/Estrategias)
- **Fase 3:** 6 tickets (Análisis)
- **Fase 4:** 3 tickets (Calidad)
- **TOTAL:** 52 tickets

### Por Prioridad
- **P0 (Crítica):** 34 tickets
- **P1 (Alta):** 18 tickets
- **TOTAL:** 52 tickets

### Por Épica
Todas las épicas tienen entre 3 y 5 tickets, para equilibrar complejidad y enfoque.

---

## 🎯 Rutas Críticas

### Ruta 1: Núcleo de Ejecución (Fase 1)
```
T1-T5 (Orquestación) 
  ↓
T6-T9 (MT5)
  ↓
T17-T19 (Magic Numbers)
  ↓
T20-T22 (Multi-activo)
```

### Ruta 2: IA y Estrategias (Fase 2)
```
T10-T13 (IA Gemini)
  ↓
T14-T16 (Dual Market/Limit)
  ↓
T26-T28 (Reevaluación)
```

### Ruta 3: Persistencia (Fase 3)
```
T32-T34 (SQLite)
  ↓
T41-T43 (Métricas)
```

---

## 🚀 Próximas Acciones

1. ✅ **Creado:** 52 tickets + 16 épicas en GitHub
2. ✅ **Vinculado:** Todos al proyecto v2
3. ⏭️ **Siguiente:** Crear estructura de código
4. ⏭️ **Siguiente:** Empezar Fase 0 (fundamentos)
5. ⏭️ **Siguiente:** Desarrollar Bot 1 (Fase 1)

---

**Documento generado:** 5 de Noviembre de 2025  
**Herramienta:** GitHub Copilot + GitHub CLI  
**Ver en línea:** https://github.com/DVARGAS117/Botrading/issues
