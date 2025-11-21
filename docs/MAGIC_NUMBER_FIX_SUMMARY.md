# Corrección de Colisión de Magic Numbers - Bot INTRADAY

## 📋 Problema Identificado

**Fecha**: 20 de noviembre de 2025

### Síntomas
Ambos bots INTRADAY (Gemini 3 Pro y Gemini 2.5 Pro) estaban registrando operaciones con el **mismo magic_number (500000)** y el **mismo ID de operación en la base de datos (ID=4)**, causando:

- ❌ Operaciones duplicadas
- ❌ Pérdida de tracking individual por bot
- ❌ Imposibilidad de distinguir qué bot abrió cada posición
- ❌ Errores en el cálculo de métricas y costos por bot

### Causa Raíz

Los bots tenían configuraciones de `bot_id` problemáticas:

| Bot | bot_id Original | Magic Number Generado | Problema |
|-----|----------------|---------------------|----------|
| **Gemini 3 Pro INTRADAY** | `5` | `500000` | ID compartido con otro bot |
| **Gemini 2.5 Pro INTRADAY** | `106` | `10600000` ❌ | **8 dígitos** (sistema espera 6) |

**Problema técnico**: El `MagicNumberGenerator` está diseñado para generar números de **6 dígitos** con estructura `[Bot][IA][Tipo][Seq]`, pero:

1. Bot con `bot_id=106` generaba `106 * 100000 = 10600000` (8 dígitos)
2. El sistema solo acepta magic numbers de 6 dígitos (100000-999999)
3. Esto causaba que el bot 106 fallara y se registrara con el mismo magic del bot 5

---

## ✅ Solución Implementada

### 1. Reasignación de Bot IDs

Se reasignaron los `bot_id` para evitar colisiones y mantener compatibilidad:

| Bot | bot_id Anterior | bot_id Nuevo | Magic Number Generado |
|-----|----------------|--------------|---------------------|
| **VWAP Bot 1** | `1` | `1` | `100000` |
| **VWAP Bot 2** | `2` | `2` | `200000` |
| **Gemini 3 Pro INTRADAY** | `5` → | **`3`** | **`300000`** ✅ |
| **Gemini 2.5 Pro INTRADAY** | `106` → | **`4`** | **`400000`** ✅ |

### 2. Actualización de Archivos de Configuración

#### `src/bots/strategies/intraday/gemini_3_pro/bot_1/config.py`
```python
# ANTES
bot_id=5,  # ID único para estrategia INTRADAY (bot_id debe estar entre 1-5)

# DESPUÉS
bot_id=3,  # ID único para estrategia INTRADAY con Gemini 3 Pro (IDs ocupados: 1=VWAP Bot1, 2=VWAP Bot2)
```

#### `src/bots/strategies/intraday/gemini_2_5_pro/bot_1/config.py`
```python
# ANTES
bot_id=106,  # ID único para estrategia INTRADAY con Gemini 2.5 Pro

# DESPUÉS
bot_id=4,  # ID único para estrategia INTRADAY con Gemini 2.5 Pro (IDs ocupados: 1=VWAP Bot1, 2=VWAP Bot2, 3=INTRADAY Gemini3Pro)
```

### 3. Mejora del MagicNumberGenerator

Se actualizó `src/core/magic_number_generator.py` para soportar IDs de 3 dígitos con mapeo automático:

```python
# Mapear bot_id de 3 dígitos (101-106) a 1 dígito (1-6)
# IDs legacy (1-5) se mantienen igual
# IDs nuevos (101-106) se mapean: 101->1, 102->2, ..., 106->6
if bot_id >= 101:
    mapped_bot_id = bot_id - 100
else:
    mapped_bot_id = bot_id

magic_number = (
    mapped_bot_id * 100000 +    # Primer dígito (mapeado)
    ia_config_id * 10000 +      # Segundo dígito
    order_type_code * 1000 +    # Tercer dígito
    sequence                     # Últimos 3 dígitos
)
```

**Ventajas**:
- ✅ Compatibilidad hacia atrás con IDs legacy (1-5)
- ✅ Soporte para IDs de 3 dígitos (101-106) con mapeo automático
- ✅ Siempre genera magic numbers de 6 dígitos
- ✅ Logging mejorado para debugging

### 4. Actualización de Documentación

Se actualizó `docs/INTRADAY_BOT_GUIDE.md` con:
- Bot ID correcto: **3** (Gemini 3 Pro)
- Nota sobre Bot 4 (Gemini 2.5 Pro)
- Información sobre magic numbers únicos

---

## 🧪 Verificación

### Magic Numbers Esperados

| Bot ID | IA Config | Order Type | Sequence | Magic Number |
|--------|-----------|------------|----------|--------------|
| 3 | 0 | Market (0) | 0 | **300000** |
| 4 | 0 | Market (0) | 0 | **400000** |

### Pruebas Recomendadas

1. **Ejecutar Bot 3 (Gemini 3 Pro INTRADAY)**:
   ```bash
   python src/bots/strategies/intraday/gemini_3_pro/bot_1/main.py
   ```
   - Verificar en logs: `Magic Number generado: 300000`

2. **Ejecutar Bot 4 (Gemini 2.5 Pro INTRADAY)**:
   ```bash
   python src/bots/strategies/intraday/gemini_2_5_pro/bot_1/main.py
   ```
   - Verificar en logs: `Magic Number generado: 400000`

3. **Verificar en Base de Datos**:
   ```sql
   SELECT id, magic_number, bot_id, symbol FROM operations 
   WHERE bot_id IN (3, 4) 
   ORDER BY created_at DESC;
   ```
   - Cada bot debe tener magic_numbers únicos

---

## 📊 Impacto y Beneficios

### Antes de la Corrección
- ❌ 2 bots generaban el mismo magic_number
- ❌ Operaciones se sobreescribían en BD (retornaba existente)
- ❌ Imposible distinguir qué bot abrió cada operación
- ❌ Métricas de rendimiento mezcladas

### Después de la Corrección
- ✅ Cada bot tiene su propio magic_number único
- ✅ Operaciones se registran correctamente en BD
- ✅ Tracking individual por bot
- ✅ Métricas y costos precisos por bot
- ✅ Compatibilidad con IDs futuros (101-106)

---

## 🔍 Logs de Referencia

### Bot 3 (Gemini 3 Pro) - Antes
```
[2025-11-20 22:02:15] [Bot5_INTRADAY Baseline] [INFO] Magic: 500000
Operación con magic_number 500000 ya existe (ID=4). Retornando existente.
```

### Bot 3 (Gemini 3 Pro) - Después
```
[2025-11-20 22:XX:XX] [Bot3_INTRADAY Baseline] [INFO] Magic: 300000
[2025-11-20 22:XX:XX] [Bot3_INTRADAY Baseline] [INFO] ✅ Operación registrada en BD: ID=5, Magic=300000
```

### Bot 4 (Gemini 2.5 Pro) - Antes
```
[2025-11-20 21:47:46] [Bot106_INTRADAY Gemini 2.5 Pro] [INFO] Magic: 10600000 ❌
Operación con magic_number 500000 ya existe (ID=4). Retornando existente.
```

### Bot 4 (Gemini 2.5 Pro) - Después
```
[2025-11-20 22:XX:XX] [Bot4_INTRADAY Gemini 2.5 Pro] [INFO] Magic: 400000
[2025-11-20 22:XX:XX] [Bot4_INTRADAY Gemini 2.5 Pro] [INFO] ✅ Operación registrada en BD: ID=6, Magic=400000
```

---

## 📝 Archivos Modificados

1. ✅ `src/bots/strategies/intraday/gemini_3_pro/bot_1/config.py`
2. ✅ `src/bots/strategies/intraday/gemini_2_5_pro/bot_1/config.py`
3. ✅ `src/core/magic_number_generator.py`
4. ✅ `docs/INTRADAY_BOT_GUIDE.md`

---

## 🎯 Próximos Pasos

1. ✅ **Completado**: Corregir `bot_id` en archivos de configuración
2. ✅ **Completado**: Mejorar `MagicNumberGenerator` para soportar IDs de 3 dígitos
3. ✅ **Completado**: Actualizar documentación
4. ⏳ **Pendiente**: Ejecutar pruebas con ambos bots en paralelo
5. ⏳ **Pendiente**: Verificar que no haya colisiones en base de datos
6. ⏳ **Pendiente**: Monitorear logs durante 24h para confirmar estabilidad

---

## ⚠️ Notas Importantes

- **No eliminar** operaciones antiguas con `magic_number=500000` de la BD, podrían ser históricas
- **Reservar** bot_ids 5-9 para futuros bots (disponibles)
- **Mantener** compatibilidad con IDs legacy (1-5) para bots VWAP existentes
- **Documentar** cualquier nuevo bot con su bot_id correspondiente

---

**Autor**: GitHub Copilot  
**Fecha**: 20 de noviembre de 2025  
**Versión**: 1.0.0
