# 📋 FORMATO DE RESPUESTAS IA - Sistema Botrading

**Documento de Referencia para Construcción de Prompts**

Este documento define los formatos JSON exactos que el sistema entiende y valida.
**IMPORTANTE**: La IA debe responder EXACTAMENTE con estos formatos para evitar errores de parsing.

---

## 🎯 Tipos de Respuestas Soportadas

El sistema soporta **2 tipos** de consultas a la IA:

1. **Evaluación Inicial**: ¿Debo operar? → `OPERAR` o `NO_OPERAR`
2. **Reevaluación**: ¿Qué hago con la operación abierta? → `MANTENER`, `ACTUALIZAR`, `CERRAR`

---

## 📤 FORMATO 1: Evaluación Inicial

### Opción A: NO_OPERAR

Cuando NO hay señal clara para operar:

```json
{
  "accion": "NO_OPERAR",
  "razonamiento": "Mercado lateral sin tendencia clara. RSI neutral en 52. Volumen bajo."
}
```

**Campos Requeridos:**
- ✅ `accion`: DEBE ser exactamente `"NO_OPERAR"` (mayúsculas, sin tildes)
- ⚠️ `razonamiento`: OPCIONAL pero recomendado (string)

---

### Opción B: OPERAR con Orden MARKET

Cuando hay señal para operar inmediatamente al precio de mercado:

```json
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "tipo_orden": "MARKET",
  "stop_loss": 1.2300,
  "take_profit": 1.2500,
  "riesgo_porcentaje": 2.0,
  "razonamiento": "Ruptura alcista confirmada. EMA 20 cruzó EMA 50 al alza. RSI en 65 con momentum."
}
```

**Campos Requeridos:**
- ✅ `accion`: DEBE ser `"OPERAR"`
- ✅ `direccion`: DEBE ser `"BUY"` o `"SELL"` (mayúsculas)
- ✅ `tipo_orden`: OPCIONAL, por defecto es `"MARKET"` (mayúsculas)
- ✅ `stop_loss`: NÚMERO decimal (float/int), NO string
- ✅ `take_profit`: NÚMERO decimal (float/int), NO string
- ✅ `riesgo_porcentaje`: NÚMERO entre 1.0 y 5.0
- ⚠️ `razonamiento`: OPCIONAL (string)

**Validaciones Automáticas para BUY:**
- ✅ `stop_loss` DEBE ser MENOR que el precio de entrada
- ✅ `take_profit` DEBE ser MAYOR que el precio de entrada

**Ejemplo BUY (Precio actual ~1.2400):**
```json
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "stop_loss": 1.2350,
  "take_profit": 1.2500,
  "riesgo_porcentaje": 2.0
}
```
✅ Válido: SL(1.2350) < Entrada(~1.2400) < TP(1.2500)

---

### Opción C: OPERAR con Orden LIMIT

Cuando quieres esperar un precio específico de entrada:

```json
{
  "accion": "OPERAR",
  "direccion": "SELL",
  "tipo_orden": "LIMIT",
  "precio_entrada": 1.2450,
  "stop_loss": 1.2500,
  "take_profit": 1.2350,
  "riesgo_porcentaje": 1.5,
  "razonamiento": "Resistencia fuerte en 1.2450. Esperar rechazo para vender."
}
```

**Campos Requeridos (adicional a MARKET):**
- ✅ `precio_entrada`: REQUERIDO cuando `tipo_orden` = `"LIMIT"` (NÚMERO)

**Validaciones Automáticas para SELL:**
- ✅ `stop_loss` DEBE ser MAYOR que `precio_entrada`
- ✅ `take_profit` DEBE ser MENOR que `precio_entrada`

**Ejemplo SELL con LIMIT:**
```json
{
  "accion": "OPERAR",
  "direccion": "SELL",
  "tipo_orden": "LIMIT",
  "precio_entrada": 1.2450,
  "stop_loss": 1.2500,
  "take_profit": 1.2350,
  "riesgo_porcentaje": 2.0
}
```
✅ Válido: TP(1.2350) < Entrada(1.2450) < SL(1.2500)

---

## 📥 FORMATO 2: Reevaluación de Operación Abierta

### Opción A: MANTENER

Cuando la operación va bien y no requiere cambios:

```json
{
  "accion": "MANTENER",
  "razonamiento": "La operación sigue la tendencia prevista. SL protege capital. TP alcanzable."
}
```

**Campos Requeridos:**
- ✅ `accion`: DEBE ser `"MANTENER"`
- ⚠️ `razonamiento`: OPCIONAL (string)

---

### Opción B: ACTUALIZAR

Cuando quieres modificar el Stop Loss o Take Profit:

```json
{
  "accion": "ACTUALIZAR",
  "nuevo_stop_loss": 1.2380,
  "nuevo_take_profit": 1.2550,
  "razonamiento": "Mover SL a breakeven. Operación en profit +50 pips. Extender TP por momentum."
}
```

**Campos Requeridos (AL MENOS UNO):**
- ✅ `nuevo_stop_loss`: NÚMERO (opcional, si quieres cambiar SL)
- ✅ `nuevo_take_profit`: NÚMERO (opcional, si quieres cambiar TP)
- ⚠️ `razonamiento`: OPCIONAL (string)

**Nota:** Puedes actualizar solo SL, solo TP, o ambos:

```json
// Solo actualizar SL (mover a breakeven)
{
  "accion": "ACTUALIZAR",
  "nuevo_stop_loss": 1.2400,
  "razonamiento": "Proteger capital. Mover SL a punto de entrada."
}

// Solo actualizar TP (extender objetivo)
{
  "accion": "ACTUALIZAR",
  "nuevo_take_profit": 1.2600,
  "razonamiento": "Tendencia fuerte. Extender objetivo."
}

// Actualizar ambos
{
  "accion": "ACTUALIZAR",
  "nuevo_stop_loss": 1.2420,
  "nuevo_take_profit": 1.2580,
  "razonamiento": "Trailing stop + extensión de TP."
}
```

---

### Opción C: CERRAR

Cuando detectas señales de reversión o pérdida:

```json
{
  "accion": "CERRAR",
  "razonamiento": "Señales de reversión confirmadas. RSI divergencia bajista. Mejor cerrar con profit actual."
}
```

**Campos Requeridos:**
- ✅ `accion`: DEBE ser `"CERRAR"`
- ⚠️ `razonamiento`: OPCIONAL (string)

---

## ⚠️ ERRORES COMUNES A EVITAR

### ❌ Error 1: Valores como STRING en lugar de NÚMERO

```json
// ❌ INCORRECTO
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "stop_loss": "1.2300",        // ❌ STRING
  "take_profit": "1.2500",      // ❌ STRING
  "riesgo_porcentaje": "2.0"    // ❌ STRING
}

// ✅ CORRECTO
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "stop_loss": 1.2300,          // ✅ NUMBER
  "take_profit": 1.2500,        // ✅ NUMBER
  "riesgo_porcentaje": 2.0      // ✅ NUMBER
}
```

---

### ❌ Error 2: Palabras en MINÚSCULAS o con TILDES

```json
// ❌ INCORRECTO
{
  "accion": "operar",           // ❌ minúsculas
  "direccion": "buy",           // ❌ minúsculas
  "tipo_orden": "market"        // ❌ minúsculas
}

// ✅ CORRECTO
{
  "accion": "OPERAR",           // ✅ MAYÚSCULAS
  "direccion": "BUY",           // ✅ MAYÚSCULAS
  "tipo_orden": "MARKET"        // ✅ MAYÚSCULAS
}
```

---

### ❌ Error 3: Acciones INVÁLIDAS

```json
// ❌ INCORRECTO
{
  "accion": "COMPRAR"           // ❌ No existe
}
{
  "accion": "VENDER"            // ❌ No existe
}
{
  "accion": "ESPERAR"           // ❌ No existe
}

// ✅ CORRECTO - Solo estas 5 acciones existen:
{
  "accion": "OPERAR"            // ✅ Para evaluación inicial
}
{
  "accion": "NO_OPERAR"         // ✅ Para evaluación inicial
}
{
  "accion": "MANTENER"          // ✅ Para reevaluación
}
{
  "accion": "ACTUALIZAR"        // ✅ Para reevaluación
}
{
  "accion": "CERRAR"            // ✅ Para reevaluación
}
```

---

### ❌ Error 4: Direcciones INVÁLIDAS

```json
// ❌ INCORRECTO
{
  "direccion": "LONG"           // ❌ No existe
}
{
  "direccion": "SHORT"          // ❌ No existe
}
{
  "direccion": "COMPRA"         // ❌ No existe
}

// ✅ CORRECTO - Solo estas 2 direcciones existen:
{
  "direccion": "BUY"            // ✅ Compra
}
{
  "direccion": "SELL"           // ✅ Venta
}
```

---

### ❌ Error 5: Riesgo FUERA DE RANGO

```json
// ❌ INCORRECTO
{
  "riesgo_porcentaje": 0.5      // ❌ Menor que 1.0
}
{
  "riesgo_porcentaje": 10.0     // ❌ Mayor que 5.0
}

// ✅ CORRECTO - Debe estar entre 1.0 y 5.0:
{
  "riesgo_porcentaje": 1.0      // ✅ Mínimo
}
{
  "riesgo_porcentaje": 2.5      // ✅ Moderado
}
{
  "riesgo_porcentaje": 5.0      // ✅ Máximo
}
```

---

### ❌ Error 6: SL/TP Inconsistentes con Dirección

```json
// ❌ INCORRECTO para BUY
{
  "direccion": "BUY",
  "precio_entrada": 1.2400,
  "stop_loss": 1.2450,          // ❌ SL debe estar DEBAJO
  "take_profit": 1.2390         // ❌ TP debe estar ARRIBA
}

// ✅ CORRECTO para BUY
{
  "direccion": "BUY",
  "precio_entrada": 1.2400,
  "stop_loss": 1.2350,          // ✅ SL DEBAJO (1.2350 < 1.2400)
  "take_profit": 1.2500         // ✅ TP ARRIBA (1.2500 > 1.2400)
}

// ❌ INCORRECTO para SELL
{
  "direccion": "SELL",
  "precio_entrada": 1.2400,
  "stop_loss": 1.2350,          // ❌ SL debe estar ARRIBA
  "take_profit": 1.2450         // ❌ TP debe estar ABAJO
}

// ✅ CORRECTO para SELL
{
  "direccion": "SELL",
  "precio_entrada": 1.2400,
  "stop_loss": 1.2450,          // ✅ SL ARRIBA (1.2450 > 1.2400)
  "take_profit": 1.2350         // ✅ TP ABAJO (1.2350 < 1.2400)
}
```

---

### ❌ Error 7: Campos Faltantes para OPERAR

```json
// ❌ INCORRECTO - Faltan campos requeridos
{
  "accion": "OPERAR",
  "direccion": "BUY"
  // ❌ Falta: stop_loss, take_profit, riesgo_porcentaje
}

// ✅ CORRECTO - Todos los campos presentes
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "stop_loss": 1.2300,
  "take_profit": 1.2500,
  "riesgo_porcentaje": 2.0
}
```

---

### ❌ Error 8: Orden LIMIT sin precio_entrada

```json
// ❌ INCORRECTO - Falta precio_entrada
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "tipo_orden": "LIMIT",
  // ❌ Falta: precio_entrada
  "stop_loss": 1.2300,
  "take_profit": 1.2500,
  "riesgo_porcentaje": 2.0
}

// ✅ CORRECTO - precio_entrada presente
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "tipo_orden": "LIMIT",
  "precio_entrada": 1.2400,     // ✅ Requerido para LIMIT
  "stop_loss": 1.2300,
  "take_profit": 1.2500,
  "riesgo_porcentaje": 2.0
}
```

---

## 📝 PLANTILLAS PARA PROMPTS

### Para Evaluación Inicial

```
Analiza los siguientes datos de mercado y decide si operar.

RESPONDE ÚNICAMENTE CON UN JSON EN ESTE FORMATO EXACTO:

Si NO hay señal clara:
{
  "accion": "NO_OPERAR",
  "razonamiento": "tu explicación aquí"
}

Si hay señal para operar:
{
  "accion": "OPERAR",
  "direccion": "BUY" o "SELL",
  "tipo_orden": "MARKET" o "LIMIT",
  "precio_entrada": 1.2400 (solo si tipo_orden es LIMIT),
  "stop_loss": número (NO string),
  "take_profit": número (NO string),
  "riesgo_porcentaje": número entre 1.0 y 5.0,
  "razonamiento": "tu explicación aquí"
}

REGLAS CRÍTICAS:
1. Todos los precios deben ser NÚMEROS, NO strings
2. Para BUY: stop_loss < precio_entrada < take_profit
3. Para SELL: stop_loss > precio_entrada > take_profit
4. riesgo_porcentaje entre 1.0 y 5.0
5. Palabras en MAYÚSCULAS: OPERAR, NO_OPERAR, BUY, SELL, MARKET, LIMIT
```

---

### Para Reevaluación

```
Tienes una operación abierta. Analiza si debes mantenerla, actualizarla o cerrarla.

RESPONDE ÚNICAMENTE CON UN JSON EN ESTE FORMATO EXACTO:

Si todo va bien:
{
  "accion": "MANTENER",
  "razonamiento": "tu explicación aquí"
}

Si quieres modificar SL/TP:
{
  "accion": "ACTUALIZAR",
  "nuevo_stop_loss": número (opcional),
  "nuevo_take_profit": número (opcional),
  "razonamiento": "tu explicación aquí"
}

Si detectas señales de salida:
{
  "accion": "CERRAR",
  "razonamiento": "tu explicación aquí"
}

REGLAS CRÍTICAS:
1. Solo 3 acciones válidas: MANTENER, ACTUALIZAR, CERRAR
2. nuevo_stop_loss y nuevo_take_profit deben ser NÚMEROS, NO strings
3. Para ACTUALIZAR, proporciona al menos uno: nuevo_stop_loss O nuevo_take_profit
4. Palabras en MAYÚSCULAS
```

---

## 🔍 Validaciones que el Sistema Ejecuta

El sistema valida automáticamente:

### ✅ Nivel 1: Sintaxis JSON
- El JSON debe ser válido sintácticamente

### ✅ Nivel 2: Campos Requeridos
- Evaluación: `accion` OBLIGATORIO
- OPERAR: `direccion`, `stop_loss`, `take_profit`, `riesgo_porcentaje` OBLIGATORIOS
- ACTUALIZAR: `nuevo_stop_loss` O `nuevo_take_profit` (al menos uno)

### ✅ Nivel 3: Tipos de Datos
- `stop_loss`: float/int (NO string)
- `take_profit`: float/int (NO string)
- `riesgo_porcentaje`: float/int (NO string)
- `accion`: string
- `direccion`: string
- `razonamiento`: string

### ✅ Nivel 4: Valores Válidos
- `accion`: solo ["OPERAR", "NO_OPERAR", "MANTENER", "ACTUALIZAR", "CERRAR"]
- `direccion`: solo ["BUY", "SELL"]
- `tipo_orden`: solo ["MARKET", "LIMIT"]
- `riesgo_porcentaje`: entre 1.0 y 5.0

### ✅ Nivel 5: Lógica de Negocio
- **BUY**: SL < Entrada < TP
- **SELL**: SL > Entrada > TP
- **LIMIT**: debe tener `precio_entrada`

---

## 🎯 Ejemplos Completos Válidos

### Ejemplo 1: Evaluación - NO_OPERAR
```json
{
  "accion": "NO_OPERAR",
  "razonamiento": "Mercado lateral. RSI en 50, sin tendencia clara. Volumen bajo. Mejor esperar confirmación."
}
```
✅ **VÁLIDO**: Campo accion correcto, razonamiento opcional presente

---

### Ejemplo 2: Evaluación - OPERAR BUY MARKET
```json
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "tipo_orden": "MARKET",
  "stop_loss": 1.2350,
  "take_profit": 1.2550,
  "riesgo_porcentaje": 2.5,
  "razonamiento": "Ruptura alcista del canal. EMA 20 > EMA 50. RSI 68 con momentum. MACD cruce alcista. Volumen creciente. Target 200 pips."
}
```
✅ **VÁLIDO**: Todos los campos presentes, tipos correctos, SL < TP para BUY

---

### Ejemplo 3: Evaluación - OPERAR SELL LIMIT
```json
{
  "accion": "OPERAR",
  "direccion": "SELL",
  "tipo_orden": "LIMIT",
  "precio_entrada": 1.2480,
  "stop_loss": 1.2530,
  "take_profit": 1.2380,
  "riesgo_porcentaje": 1.5,
  "razonamiento": "Resistencia histórica en 1.2480. Doble techo formado. RSI sobrecomprado en 72. Esperar rechazo en resistencia para vender."
}
```
✅ **VÁLIDO**: LIMIT con precio_entrada, SL > Entrada > TP para SELL

---

### Ejemplo 4: Reevaluación - MANTENER
```json
{
  "accion": "MANTENER",
  "razonamiento": "Operación en profit +80 pips. Tendencia alcista intacta. SL protegiendo capital. TP alcanzable. No hay señales de reversión."
}
```
✅ **VÁLIDO**: Accion correcta, razonamiento claro

---

### Ejemplo 5: Reevaluación - ACTUALIZAR solo SL
```json
{
  "accion": "ACTUALIZAR",
  "nuevo_stop_loss": 1.2420,
  "razonamiento": "Operación en profit +70 pips. Mover SL a breakeven para proteger capital. Mantener TP original."
}
```
✅ **VÁLIDO**: ACTUALIZAR con solo nuevo_stop_loss (válido)

---

### Ejemplo 6: Reevaluación - ACTUALIZAR solo TP
```json
{
  "accion": "ACTUALIZAR",
  "nuevo_take_profit": 1.2650,
  "razonamiento": "Momentum muy fuerte. Volumen creciente. Extender objetivo a siguiente resistencia en 1.2650."
}
```
✅ **VÁLIDO**: ACTUALIZAR con solo nuevo_take_profit (válido)

---

### Ejemplo 7: Reevaluación - ACTUALIZAR ambos
```json
{
  "accion": "ACTUALIZAR",
  "nuevo_stop_loss": 1.2450,
  "nuevo_take_profit": 1.2600,
  "razonamiento": "Trailing stop: mover SL siguiendo el precio. Profit actual +100 pips. Extender TP por momentum fuerte."
}
```
✅ **VÁLIDO**: ACTUALIZAR con ambos campos (válido)

---

### Ejemplo 8: Reevaluación - CERRAR
```json
{
  "accion": "CERRAR",
  "razonamiento": "Divergencia bajista en RSI confirmada. MACD cruce bajista. Velas de reversión. Mejor cerrar con profit actual de +120 pips antes de reversión."
}
```
✅ **VÁLIDO**: Accion CERRAR con razonamiento claro

---

## 📚 Resumen de Palabras Clave del Sistema

### Acciones (campo `accion`):
- `"OPERAR"` - Para evaluación inicial: hay señal para entrar
- `"NO_OPERAR"` - Para evaluación inicial: no hay señal clara
- `"MANTENER"` - Para reevaluación: dejar operación sin cambios
- `"ACTUALIZAR"` - Para reevaluación: modificar SL/TP
- `"CERRAR"` - Para reevaluación: cerrar operación ahora

### Direcciones (campo `direccion`):
- `"BUY"` - Compra (ir en largo)
- `"SELL"` - Venta (ir en corto)

### Tipos de Orden (campo `tipo_orden`):
- `"MARKET"` - Ejecutar al precio actual inmediatamente (por defecto)
- `"LIMIT"` - Esperar a precio específico (requiere `precio_entrada`)

### Campos Numéricos:
- `stop_loss` - Precio de stop loss (NÚMERO)
- `take_profit` - Precio de take profit (NÚMERO)
- `precio_entrada` - Precio deseado para LIMIT (NÚMERO)
- `riesgo_porcentaje` - Riesgo del capital (1.0 a 5.0)
- `nuevo_stop_loss` - Nuevo SL en reevaluación (NÚMERO)
- `nuevo_take_profit` - Nuevo TP en reevaluación (NÚMERO)

### Campos de Texto:
- `razonamiento` - Explicación de la decisión (string, opcional)

---

## 🚀 Uso en Prompts

### Instrucción Recomendada para Prompts:

```
FORMATO DE RESPUESTA OBLIGATORIO:

Debes responder ÚNICAMENTE con un objeto JSON válido.
NO incluyas texto adicional antes o después del JSON.
NO uses markdown ni bloques de código.
Solo el JSON puro.

Usa EXACTAMENTE las palabras clave del sistema:
- Acciones: "OPERAR", "NO_OPERAR", "MANTENER", "ACTUALIZAR", "CERRAR"
- Direcciones: "BUY", "SELL"
- Tipos: "MARKET", "LIMIT"

Todos los precios deben ser números (float/int), NO strings.

Ejemplo válido:
{
  "accion": "OPERAR",
  "direccion": "BUY",
  "stop_loss": 1.2300,
  "take_profit": 1.2500,
  "riesgo_porcentaje": 2.0,
  "razonamiento": "Señal alcista confirmada"
}
```

---

## ✅ Checklist Pre-Prompt

Antes de enviar el prompt a la IA, verifica:

- [ ] El prompt indica claramente el formato JSON esperado
- [ ] Incluye ejemplos con las palabras clave EXACTAS
- [ ] Especifica que los números NO deben ser strings
- [ ] Menciona las validaciones de SL/TP según dirección
- [ ] Indica el rango válido de riesgo_porcentaje (1.0-5.0)
- [ ] Aclara que solo ciertas acciones son válidas
- [ ] Pide solo JSON, sin texto adicional

---

**Documento creado para:** T40 - Registro de errores de parsing de respuestas IA  
**Fecha:** 2025-11-06  
**Versión:** 1.0  
**Módulo validador:** `src/core/ai_response_parser.py`  
**Tests:** `tests/unit/test_ai_response_parser.py` (42 tests, 100% passing)

---

## 📞 En Caso de Errores

Si la IA responde con formato inválido:

1. El sistema registrará el error en el historial
2. El ciclo se omitirá hasta la siguiente iteración
3. Revisa los logs para ver el error exacto
4. Ajusta el prompt para ser más específico
5. Considera cambiar de modelo/provider si persiste

**Ver:** `context/DOCUMENTACION/T40_errores_parsing_ia.md` (cuando se cree)
