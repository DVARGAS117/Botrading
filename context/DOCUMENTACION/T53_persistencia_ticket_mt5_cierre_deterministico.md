# T53 - Persistencia de Ticket MT5 y Cierre Determinístico

> Fecha: 24/11/2025  
> Estado: Completado ✅  
> Autor: Sistema Botrading  
> Impacto: Alto (fiabilidad en cierre y actualización de posiciones)

---
## 1. Contexto del Problema

Las respuestas de la IA (Gemini vía Vertex) no incluían el campo `ticket` del broker. El flujo de cierre dependía de heurísticas:
- Búsqueda de posición abierta por `symbol` y `magic_number`.
- Suposición de única posición abierta por símbolo/estrategia.

Riesgos detectados:
- Ambigüedad en cuentas Netting (mismo ticket para múltiples ajustes).
- Cierre incorrecto o manual cuando la IA ordenaba `CIERRE` sin ticket.
- Dificultad para correlacionar operaciones en MT5 con registros SQLite.

---
## 2. Objetivos

1. Persistir el `ticket` real de MT5 en la base de datos `operations.db`.
2. Usar el `ticket` como clave principal para actualizar SL/TP y cerrar.
3. Mantener compatibilidad con operaciones antiguas sin columna `ticket`.
4. Minimizar cambios en prompts (requisito del usuario).

---
## 3. Cambios Implementados

### 3.1 Base de Datos
- Tabla `operations`: Se añadió columna `ticket INTEGER`.
- Índice nuevo: `idx_ticket` para búsqueda rápida.
- Migración ligera automática: `ALTER TABLE` si la columna no existe.
- Verificación dinámica de columnas mediante `PRAGMA table_info(operations)`.

### 3.2 Modelo y Repositorio
Archivo: `src/core/operations_repository.py`
- Dataclass `Operation` ampliada con atributo `ticket`.
- Método nuevo: `get_operation_by_ticket(ticket: int)`.
- Inserción: `create_operation()` ahora guarda el `ticket` recibido del objeto posición MT5.
- Método `_row_to_operation()` incluye extracción segura del `ticket`.

### 3.3 Estrategias Intraday
Archivos afectados:
- `strategy.py` de variantes Gemini 3 Pro y Gemini 2.5 Pro.

Cambios:
- Al abrir posición: se obtiene `position.ticket` y se pasa a `create_operation()`.
- Al actualizar/cerrar: se busca primero por `get_operation_by_ticket()`.
- Fallback: si `ticket` no está disponible, se usa lookup por `magic_number` + cache `_active_magic_by_symbol`.

### 3.4 Cache de Magic Numbers
Archivo: `base_bot_operations.py`
- Campo `_active_magic_by_symbol`: almacena el último `magic_number` asociado al símbolo.
- Usado sólo como fallback para operaciones sin ticket (retrocompatibilidad).

### 3.5 Scripts Operativos
Nuevos para saneamiento y verificación:
- `scripts/list_open_positions.py`: lista posiciones abiertas con `ticket`, `magic_number` y símbolo.
- `scripts/close_residual_positions.py`: cierra posiciones intraday residuales filtrando por símbolo.

---
## 4. Flujo Antes vs Después

Antes (CIERRE sin ticket):
1. IA ordena cierre → respuesta sin `ticket`.
2. Bot busca posición por símbolo y primer match.
3. Si múltiples posiciones similares → riesgo de cierre incorrecto.

Después (CIERRE sin ticket):
1. IA ordena cierre → respuesta sin `ticket` (sin cambios en prompt).
2. Bot consulta BD: operación abierta con ese símbolo y `ticket` persistido.
3. Cierra mediante `OrderManager` usando el `ticket` exacto.
4. Fallback solo si `ticket` faltó al persistir (proceso antiguo).

---
## 5. Consideraciones de Cuentas Netting
- En cuentas Netting, dos aperturas consecutivas pueden referenciar un solo `ticket` si se consolidan.
- Segundo update puede devolver retcode `10025` ("No changes"). Se registra como benigno.
- Estrategia: persistir sólo el primer estado y marcar updates sin cambio como informativos.

---
## 6. Retcodes Relevantes
| Código | Significado | Manejo Actual |
|--------|-------------|---------------|
| 10009  | Cierre exitoso | Actualiza BD a `closed` |
| 10025  | Sin cambios en modificación SL/TP | Log nivel info (no error) |
| 10004  | Error genérico | Log advertencia y mantiene estado |

---
## 7. Beneficios Obtenidos
- Cierre determinístico y confiable sin modificar prompt IA.
- Eliminación de necesidad de heurísticas frágiles multi-posición.
- Auditoría exacta entre MT5 y `operations.db`.
- Base preparada para futuras métricas de desempeño por `ticket`.

---
## 8. Pruebas Realizadas
1. Apertura dual BTCUSD con dos variantes → tickets registrados en BD.
2. Actualización SL/TP usando `get_operation_by_ticket()` → primera exitosa, segunda con `10025`.
3. Cierre manual/residual con script → posición eliminada, BD actualizada.
4. Verificación de índice `idx_ticket` existente vía `PRAGMA`.

---
## 9. Checklist de Verificación
- [x] Tabla incluye columna `ticket`.
- [x] Índice `idx_ticket` creado.
- [x] Estrategia guarda `ticket` al abrir.
- [x] Update busca por `ticket`.
- [x] Cierre busca por `ticket`.
- [x] Fallback por magic_number disponible.
- [x] Scripts operativos funcionales.

---
## 10. Próximas Extensiones
- Añadir campo `ticket` al schema de respuesta IA (cuando se modifique prompt).
- Manejo consolidado de posiciones Netting (tracking de volumen acumulado).
- Dashboard de discrepancias entre MT5 y BD.
- Silenciar logs repetidos de retcode `10025` (nivel debug). 

---
## 11. Riesgos Mitigados
| Riesgo | Estado Previo | Estado Actual |
|--------|---------------|---------------|
| Cierre erróneo multi-posición | Alto | Mitigado (clave por ticket) |
| Falta de trazabilidad | Alto | Bajo |
| Dependencia del prompt IA | Medio | Bajo |
| Ambigüedad Netting | Medio | Controlado |

---
## 12. Referencias
- `src/core/operations_repository.py`
- `base_bot_operations.py`
- Estrategias intraday (`strategy.py` variantes Gemini)
- Scripts en `scripts/`

---
## 13. Conclusión
La persistencia del `ticket` MT5 (T53) refuerza el ciclo operativo del bot, elimina ambigüedades críticas y sienta la base para métricas avanzadas y auditorías externas. El cierre determinístico ya no depende de la estructura de la respuesta IA.

---
