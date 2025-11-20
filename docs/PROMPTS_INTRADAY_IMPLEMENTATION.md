# Prompts INTRADAY - Implementación Completa

## Fecha
2025-11-19

## Estado
✅ **IMPLEMENTADO Y ADAPTADO**

## Descripción

Prompts profesionales estilo "trader institucional ALPHA" adaptados al formato de parseo existente del sistema INTRADAY con Gemini 3 Pro.

---

## 📋 SYSTEM PROMPT

**Archivo:** `config/prompt_templates/intraday_gemini_3_pro_bot_1_system.txt`

### Características

**Personalidad:**
- Nombre: "ALPHA"
- Rol: Trader institucional senior con 20 años de experiencia
- Filosofía: "El precio es la verdad. Menos es más."

**Herramientas:**
- VWAP (juez de tendencia intradía)
- EMA 20 y 200 (corriente del río)
- RSI 14 (sobrecompra/sobreventa)
- Bandas de Bollinger (volatilidad)
- ATR y Volumen (momentum)

**3 Estrategias:**

1. **ESTRATEGIA A - "TREND SURFER"** (Tendencia)
   - Condición: Precio > VWAP > EMA200 (alcista) o inverso
   - Entry: Pullback a EMA20/VWAP con rechazo
   - Volumen: Bajo en retroceso, alto en confirmación

2. **ESTRATEGIA B - "PING PONG"** (Rango)
   - Condición: EMA200 plana, precio cruza VWAP constantemente
   - Entry: BB Superior + RSI>70 (Venta) / BB Inferior + RSI<30 (Compra)
   - Objetivo: Retorno al VWAP

3. **ESTRATEGIA C - "VOLCANO"** (Breakout)
   - Condición: BB_Width en mínimos (squeeze)
   - Entry: Cierre FUERA de bandas con volumen > 1.5x promedio

**Reglas de Gestión:**
- Conservador en horarios de baja liquidez
- No operar contra tendencia D1 (excepto scalp rápido)
- Priorizar gestión de posición abierta sobre nuevas entradas

**Formato de Respuesta (JSON):**
```json
{
  "accion": "COMPRAR | VENDER | NO_OPERAR | MANTENER | CERRAR",
  "razonamiento": "string",
  "direccion": "LONG | SHORT | null",
  "stop_loss": número o null,
  "take_profit": número o null,
  "confianza": 0-100,
  "estrategia_usada": "A | B | C | NONE",
  "diagnostico_mercado": "string"
}
```

---

## 📨 USER PROMPT

**Archivo:** `config/prompt_templates/intraday_gemini_3_pro_bot_1_user.txt`

### Variables Reemplazadas Dinámicamente

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `{current_time}` | Timestamp actual PET | "2025-11-19 09:15:00" |
| `{symbol}` | Par a analizar | "EURUSD" |
| `{operation_id}` | ID único de operación | "INTRADAY_EURUSD_20251119_091500" |
| `{current_position}` | Estado de posición (texto formateado) | Ver sección abajo |
| `{tactical_package}` | JSON M15 (200 velas) | Array con OHLCV + indicadores |
| `{strategic_package}` | JSON D1 (30 velas) | Array con OHLCV + indicadores |

### Formato de `{current_position}`

**Cuando HAY posición abierta:**
```
POSICIÓN ACTIVA: LONG @ 1.05000
- Volumen: 0.1 lotes
- PnL Actual: $25.50 USD (25.5 pips)
- Stop Loss: 1.04800 | Take Profit: 1.05500
- Precio Actual: 1.05255
- Duración: 1h 23m

⚠️ PRIORIDAD: Gestiona esta posición. Evalúa si debe CERRARSE o MANTENERSE.
```

**Cuando NO HAY posición:**
```
POSICIÓN ACTUAL: NONE (Sin posición abierta)

✅ Puedes evaluar nuevas oportunidades de entrada (COMPRAR/VENDER) si hay setup válido.
```

---

## 🔧 Implementación en Código

### Archivo: `strategy.py`

**Método actualizado:** `prepare_data_for_ai()`

```python
# Construir información de posición (con o sin posición activa)
if has_active_position:
    current_position = self._get_current_position_info(symbol)
    position_text = f"""POSICIÓN ACTIVA: {current_position['type']} @ {current_position['price_open']}
- Volumen: {current_position['volume']} lotes
- PnL Actual: ${current_position['profit']:.2f} USD ({current_position['profit_pips']:.1f} pips)
- Stop Loss: {current_position['sl']} | Take Profit: {current_position['tp']}
- Precio Actual: {current_position['price_current']}
- Duración: {current_position.get('duration', 'N/A')}

⚠️ PRIORIDAD: Gestiona esta posición. Evalúa si debe CERRARSE o MANTENERSE."""
else:
    position_text = """POSICIÓN ACTUAL: NONE (Sin posición abierta)

✅ Puedes evaluar nuevas oportunidades de entrada (COMPRAR/VENDER) si hay setup válido."""

user_prompt = user_prompt.replace("{current_position}", position_text)
```

**Método mejorado:** `_get_current_position_info()`

Retorna diccionario con:
- `type`: "LONG" o "SHORT"
- `price_open`: Precio de entrada
- `price_current`: Precio actual
- `sl`: Stop Loss
- `tp`: Take Profit
- `pnl_points`: PnL en puntos
- `pnl_pips`: PnL en pips (0.0001 para forex, 0.01 para JPY)
- `profit`: PnL en USD
- `pnl_r`: PnL en múltiplos de R (riesgo)
- `volume`: Volumen en lotes
- `open_time`: Timestamp ISO
- `ticket`: Número de ticket MT5
- `duration`: Duración en formato "Xh Ym"

**Cálculo de duración:**
```python
position_time = position.time
duration_seconds = (datetime.now().timestamp() - position_time.timestamp())
hours = int(duration_seconds // 3600)
minutes = int((duration_seconds % 3600) // 60)
duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
```

**Cálculo de pips:**
```python
pip_value = 0.01 if "JPY" in symbol else 0.0001
pnl_pips = pnl_points / pip_value
```

---

## 📊 Ejemplo de Flujo Completo

### Escenario 1: Sin Posición Abierta

**Input a Gemini:**
```
SYSTEM: [Prompt completo con estrategias A/B/C]

USER:
### CONTEXTO OPERATIVO ACTUAL
- HORA (PET): 2025-11-19 09:15:00
- PAR/ACTIVO: EURUSD
- ID OPERACIÓN: INTRADAY_EURUSD_20251119_091500

### ESTADO DE MI CARTERA
POSICIÓN ACTUAL: NONE (Sin posición abierta)
✅ Puedes evaluar nuevas oportunidades de entrada...

### DATOS DE MERCADO
1. CONTEXTO MACRO (D1): [30 velas con indicadores]
2. CONTEXTO TÁCTICO (M15): [200 velas con indicadores]

### TU MISIÓN:
¿Hay setup válido para entrar?
```

**Output esperado de Gemini:**
```json
{
  "accion": "COMPRAR",
  "razonamiento": "Precio retrocedió a EMA20 con rechazo. VWAP actúa como soporte. Volumen confirma.",
  "direccion": "LONG",
  "stop_loss": 1.04800,
  "take_profit": 1.05500,
  "confianza": 85,
  "estrategia_usada": "A",
  "diagnostico_mercado": "TENDENCIA_ALCISTA"
}
```

### Escenario 2: Con Posición Abierta

**Input a Gemini:**
```
SYSTEM: [Mismo prompt]

USER:
### CONTEXTO OPERATIVO ACTUAL
- HORA (PET): 2025-11-19 10:45:00
- PAR/ACTIVO: EURUSD

### ESTADO DE MI CARTERA
POSICIÓN ACTIVA: LONG @ 1.05000
- Volumen: 0.1 lotes
- PnL Actual: $45.00 USD (45.0 pips)
- Stop Loss: 1.04800 | Take Profit: 1.05500
- Precio Actual: 1.05450
- Duración: 1h 30m

⚠️ PRIORIDAD: Gestiona esta posición...

[Datos de mercado actualizados]
```

**Output esperado:**
```json
{
  "accion": "CERRAR",
  "razonamiento": "Precio cerca de TP. RSI sobrecomprado + rechazo en resistencia. Tomar ganancias.",
  "direccion": null,
  "stop_loss": null,
  "take_profit": null,
  "confianza": 90,
  "estrategia_usada": "A",
  "diagnostico_mercado": "TENDENCIA_ALCISTA"
}
```

---

## 🎯 Mapeo de Acciones

| Acción IA | Condición | Acción Bot |
|-----------|-----------|------------|
| `COMPRAR` | Sin posición + setup válido | Abrir LONG |
| `VENDER` | Sin posición + setup válido | Abrir SHORT |
| `NO_OPERAR` | Sin setup o sin liquidez | Skip, no hacer nada |
| `MANTENER` | Con posición + aún válida | No cerrar, dejar correr |
| `CERRAR` | Con posición + TP/SL alcanzado | Cerrar posición actual |

---

## ✅ Validaciones Implementadas

1. **Variable `{current_position}` siempre reemplazada:**
   - Con posición: Texto formateado con detalles
   - Sin posición: Mensaje indicando que puede abrir nuevas

2. **Cálculo correcto de pips:**
   - Forex estándar: 0.0001
   - Pares JPY: 0.01

3. **Duración legible:**
   - Formato: "2h 35m" o "45m"
   - Calculado desde `position.time` hasta ahora

4. **PnL en múltiples formatos:**
   - USD: `position.profit`
   - Pips: Calculado con `pip_value`
   - R: Ratio vs riesgo inicial (SL)

---

## 🚀 Próximos Pasos

1. **Escribir prompts reales en los archivos** ✅ COMPLETADO
2. **Probar con consulta real a Gemini:** Ejecutar `strategy.execute_cycle("EURUSD")`
3. **Validar parseo de respuesta:** Verificar que `parse_ai_response()` maneja correctamente los campos adicionales (`estrategia_usada`, `diagnostico_mercado`)
4. **Ajustar confianza:** Si Gemini retorna `confianza` < 70, considerar no ejecutar la orden

---

## 📝 Notas Importantes

- **Prompts ya escritos:** Los archivos TXT están listos con el contenido completo
- **Sin cambios en parseo:** El formato JSON ya era compatible con el parser existente
- **Información de posición mejorada:** Ahora incluye duración, pips, y formato legible
- **Compatible con sesiones:** Se integra con TradingSessionManager (implementado previamente)

---

**Autor:** Sistema Botrading  
**Fecha:** 2025-11-19  
**Versión:** 1.0
