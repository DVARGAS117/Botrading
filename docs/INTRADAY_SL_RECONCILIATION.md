# INTRADAY SL/TP Reconciliation & Prompt Consistency

Fecha: 2025-11-24
Rama: feature/magic-number-v2-intraday

## Objetivo
Asegurar que el Stop Loss (SL) y Take Profit (TP) mostrados en los prompts intradía reflejen fielmente los niveles activos en el broker después de posibles ajustes automáticos (mínimos de distancia, normalizaciones), evitando inconsistencias y notas de "SL ajustado" falsas.

## Problema Detectado
- El prompt mostraba un "SL inicial" distinto al SL actual (ej.: inicial 156.77 vs actual 156.86) inmediatamente tras abrir la operación.
- Causa raíz: El broker ajustaba el SL al validar mínimos y la estrategia registraba en BD el nivel original antes del ajuste.
- Además, la lógica que detecta ajuste comparaba valores divergentes causando la aparición constante de la nota de ajuste.

## Solución Implementada
1. Uso directo de los niveles devueltos por la ejecución de la orden (price.sl / price.tp) como `stop_loss` y `stop_loss_initial` en BD.
2. Reconciliación post-apertura:
   - Sondeo hasta 5 intentos (1s intervalo) consultando posiciones vía `mt5_connection.get_positions`.
   - Si el broker ajusta SL/TP de forma significativa (>
     0.5 * pip), se actualizan `stop_loss`, `take_profit`, y sus valores iniciales en BD.
3. Recuperación del SL inicial robusta:
   - Itera posiciones del símbolo filtrando por Magic v2 y símbolo en BD.
   - Selecciona la operación más reciente (mayor `magic_number`).
   - Fallback: operaciones abiertas por símbolo si no se encuentra coincidencia directa.
4. Lógica de nota de ajuste del prompt:
   - Se considera ajuste solo si la diferencia `|SL_actual - SL_inicial| > 0.1 * pip`.
   - Test adaptado para tolerar diferencias legítimas de broker.

## Cambios Clave en Código
- `strategy.py` (Intraday Gemini 3 Pro & 2.5):
  - Eliminado recalculo artificial de SL/TP basado en desplazamiento fijo.
  - Añadida reconciliación de niveles tras registro en BD.
  - Logging detallado: verificación ajuste SL y reconciliación broker.
- `_get_initial_sl_from_db` reforzado: evita colisiones legacy y retorna el SL inicial correcto.
- Test `test_intraday_sl_consistency.py` actualizado para contemplar ajustes del broker:
  - Diferencias mayores a umbral permiten nota de ajuste.
  - Diferencias pequeñas la bloquean.

## Magic Number V2 Contextual
La corrección de SL/TP depende de la identificación única y estable de la operación. Magic Number V2 (family,strategy,order_type,agent,sequence) proporciona unicidad multi-símbolo y evita colisiones de secuencia.

## Riesgo Dinámico
Independiente del ajuste de SL: el sizing se calcula antes de enviar la orden; ajustes broker no alteran el `risk_percentage` ni `risk_amount` persistidos.

## Validación
- `test_intraday_dynamic_risk.py` & variantes: sizing correcto.
- `test_intraday_sl_consistency.py`: pasa tras adaptaciones, mostrando coherencia entre SL inicial (BD), método y prompt; nota de ajuste ausente cuando corresponde.

## Consideraciones Futuras
- Centralizar reconciliación en un servicio (evitar duplicación entre bots 2.5 y 3 Pro).
- Registrar motivo de ajuste (mínimo distancia, normalización) si MT5 expone metadata.
- Añadir métrica de frecuencia de ajustes para calibrar SL sugeridos antes del envío.

## Checklist Merge
- [x] Magic Number V2 estable.
- [x] Recuperación SL inicial por símbolo sin colisiones.
- [x] Reconciliación broker implementada y testeada.
- [x] Prompt consistente.
- [x] Tests de riesgo y consistencia SL verdes.

## Revisión Rápida de Archivos Modificados
```
config/prompt_templates/intraday_gemini_2_5_pro_bot_1_system.txt
config/prompt_templates/intraday_gemini_3_pro_bot_1_system.txt
src/bots/strategies/intraday/gemini_2_5_pro/bot_1/strategy.py
src/bots/strategies/intraday/gemini_3_pro/bot_1/strategy.py
src/core/operations_repository.py
tests/intraday/test_intraday_sl_consistency.py
```

## Próximo Paso
Realizar merge a rama `desarrollo` y preparar PR con este documento incluido.
