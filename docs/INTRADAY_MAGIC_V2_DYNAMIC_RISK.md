# Guía Magic Number v2 y Riesgo Dinámico (Intraday Bots)

## 1. Objetivo
Esta guía documenta las mejoras introducidas en los bots Intraday (Gemini 3 Pro y Gemini 2.5 Pro):
- Unicidad y trazabilidad mediante **Magic Number v2** + secuencias.
- **Sizing dinámico de posición** usando porcentaje de riesgo enviado por la IA (`riesgo_porcentaje`).
- Persistencia ampliada en BD (`risk_percentage`, `risk_amount`, `stop_loss_initial`, `take_profit_initial`).
- Bloque enriquecido de **POSICIÓN ACTIVA** en los prompts para decisiones informadas.
- Logging diagnóstico profundo en fallos de `order_send`.

## 2. Magic Number v2
### 2.1. Estructura
Magic v2 codifica cinco componentes empaquetados en un entero:
```
family_id | strategy_id | order_type | agent_variant_id | sequence
```
Cada segmento ocupa dígitos específicos para garantizar unicidad por (bot, estrategia, tipo de orden, variante y número secuencial).

### 2.2. Beneficios
- Evita colisiones entre bots y estrategias.
- Permite filtrar posiciones con precisión (decodificación directa).
- Facilita auditoría y reconstrucción del contexto de apertura.

### 2.3. Secuencias
`SequenceManager` mantiene contadores independientes por clave compuesta `(family_id, strategy_id, agent_variant_id, symbol)`. Esto impide que operaciones de símbolos distintos compartan la misma porción secuencial.

## 3. Detección de Posición Activa
- `_has_active_position(symbol)` filtra posiciones por magic v2 (decodificación) y mantiene fallback legacy para operaciones antiguas.
- `_get_current_position_info(symbol)` expone: tipo, volumen, precio apertura, SL, TP, duración, PnL en USD y en "R" (riesgo inicial). Se incluye el `magic_number` para trazabilidad.
- El prompt reemplaza `{current_position}` con bloque enriquecido:
```
POSICIÓN ACTIVA: LONG @ 1.08450
- Volumen: 0.08 lotes
- PnL Actual: $12.35 (1.03R)
- Stop Loss Inicial: 1.08300 (distancia 150 pips internos)
- Stop Loss Actual: 1.08300
- Take Profit: 1.08750
- Duración: 45m
- Riesgo Inicial $: 11.84
```

## 4. Riesgo Dinámico
### 4.1. Flujo
1. IA devuelve `riesgo_porcentaje` dentro de la respuesta JSON (ej. `1.2`).
2. Se construyen `RiskParameters`:
   - `account_balance`
   - `risk_percentage`
   - `entry_price`
   - `stop_loss`
   - `symbol_spec` (tick_value, tick_size, contract_size, volume_step, min/max lot)
3. `PositionSizer.calculate_lot_size(risk_params)` devuelve:
   - `lot_size` ajustado a `volume_step`, límites min/max
   - `risk_amount` en USD
   - `pip_distance` y validaciones
4. El comentario de la orden se sanea (ejemplo: `B3_INTRA`).
5. Se registra operación en BD con campos ampliados.

### 4.2. Fórmula Simplificada
```
valor_por_pip = (contract_size * tick_value) / (1 / tick_size)
riesgo_USD = balance * (riesgo_porcentaje / 100)
lotes = riesgo_USD / (valor_por_pip * distancia_pips)
lotes_ajustados = round_to_step(lotes, volume_step)
```
(La implementación puede incluir factores de apalancamiento implícitos según especificación del símbolo en MT5.)

### 4.3. Validaciones
- Distancia SL mínima vs `trade_stops_level`.
- Lote no menor a `min_lot` ni mayor a `max_lot`.
- Redondeo a `volume_step`.
- Riesgo resultante recalculado tras ajuste de lote.

## 5. Persistencia en BD
Tabla `operations` incorpora:
- `risk_percentage` (REAL)
- `risk_amount` (REAL)
- `stop_loss_initial`, `take_profit_initial` (REAL) para cálculo posterior de evolución del R.
Al crear la operación se verifica unicidad por `magic_number`; si existe se retorna el registro previo (evita duplicados en reconexiones).

## 6. Prompt y Decisión IA
System prompt exige JSON con claves obligatorias, incluyendo `riesgo_porcentaje`. Ejemplo fragmento:
```
{
  "accion": "COMPRAR|VENDER|MANTENER|AJUSTAR_SL_TP|CERRAR|NO_OPERAR",
  "direccion": "long|short|neutral",
  "riesgo_porcentaje": 1.2,
  "razonamiento": "..."
}
```
Si la IA omite `riesgo_porcentaje` se aplica fallback (config `risk_per_trade`). Recomendación futura: registrar un warning y anotar en prompt para transparencia.

## 7. Logging Diagnóstico
En fallo de `order_send` se loguea:
- `last_error` MT5 (código y mensaje).
- Distancias `SL` / `TP` en puntos vs `trade_stops_level`.
- `free_margin` / `required_margin` si disponible.
- Parámetros de riesgo (porcentaje solicitado, lote calculado, distancia pips).
Esto acelera la identificación de:
- Comentario inválido.
- Distancia SL menor al mínimo.
- Margen insuficiente.
- Parámetros de símbolo incompletos.

## 8. Migración (Resumen)
1. Implementar Magic v2 y decodificación.
2. Añadir `risk_percentage`, `risk_amount`, `stop_loss_initial`, `take_profit_initial` a la tabla (migración idempotente).
3. Actualizar strategies (`_execute_open_position`, `_has_active_position`, `_get_current_position_info`).
4. Incluir campo `riesgo_porcentaje` en system prompt templates.
5. Añadir logging diagnóstico.
6. Crear tests de riesgo dinámico.

## 9. Tests
Ubicados en `tests/intraday/`:
- `test_intraday_dynamic_risk.py` (Gemini 3 Pro)
- `test_intraday_dynamic_risk_25.py` (Gemini 2.5 Pro)
Cada test:
1. Fuerza decisión con `riesgo_porcentaje`.
2. Calcula lote esperado con `PositionSizer`.
3. Ejecuta `_execute_open_position`.
4. Recupera posición y operación en BD.
5. Valida lote y riesgo persistido.

### Ejecución
```powershell
# Activar entorno
powershell -ExecutionPolicy Bypass -File .venv\Scripts\Activate.ps1

# Ejecutar tests individuales
python tests\intraday\test_intraday_dynamic_risk.py
python tests\intraday\test_intraday_dynamic_risk_25.py
```

## 10. Próximas Mejoras Sugeridas
- Fallback explícito y anotación en prompt cuando falta `riesgo_porcentaje`.
- Test de ajuste dinámico de SL (conversión de R a trailing R múltiplo).
- Dashboard de métricas: Distribución de R utilizado vs R objetivo.
- Alertas si `risk_amount` difiere >10% del teórico tras ajuste de step.

## 11. Referencias de Archivos
- `src/core/magic_number_generator.py`
- `src/core/sequence_manager.py`
- `src/core/position_sizer.py`
- `src/bots/strategies/intraday/gemini_3_pro/bot_1/strategy.py`
- `src/bots/strategies/intraday/gemini_2_5_pro/bot_1/strategy.py`
- `src/core/operations_repository.py`
- `config/prompt_templates/intraday_gemini_*_system.txt`

## 12. Changelog Relacionado
Ver también:
- `docs/MAGIC_NUMBER_FIX_SUMMARY.md`
- `docs/POSITION_DETECTION_BUG_FIX.md`

---
**Autor:** GitHub Copilot  
**Fecha:** 24 de noviembre de 2025  
**Versión:** 1.0.0
