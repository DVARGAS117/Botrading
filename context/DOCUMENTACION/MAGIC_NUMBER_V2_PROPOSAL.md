# Propuesta: Magic Number v2 para Estrategias y Agentes (Intraday)

## Objetivo
- Identificar de forma inequívoca Estrategia + Agente (modelo) + Tipo de orden por operación.
- Garantizar: una sola operación abierta por símbolo (par) por agente dentro de la estrategia.
- Mantener compatibilidad con lo existente introduciendo una variante “v2” sin romper T17.

## Mapeo propuesto (6 dígitos)
- D1: Familia IA (1=Gemini, 2=GPT, 3=Grok)
- D2: Estrategia (1=Intraday, 2=VWAP, 3=Swing)
- D3: Tipo (0=Market, 1=Limit)
- D4: Agente dentro de estrategia (Intraday: 1=Gemini 2.5 Pro, 2=Gemini 3 Pro, 3=GPT-4, 4=Grok)
- D5–D6: Sequence por símbolo (00–99) para permitir múltiples órdenes a lo largo del tiempo evitando colisiones.

Notas:
- Secuencia por símbolo: el siguiente número se decide consultando BD/MT5 (máximo usado +1, con wrap si >99).
- Este esquema es la “v2”. La “v1” (T17) permanece intacta para otros bots.

## Reglas de negocio
- Un agente (p.ej. Intraday + Gemini 3 Pro) solo puede tener 1 operación abierta simultánea por símbolo.
- Si ya hay operación abierta en un símbolo, el prompt pasa a modo “gestión” (MANTENER/AJUSTAR_SL_TP/CERRAR).
- Si no hay operación abierta, se usa modo “evaluación” (COMPRAR/VENDER/NO_OPERAR) y se genera un nuevo magic v2.

## Plan por fases
1) Generador v2
   - Crear `src/core/enhanced_magic_number_generator.py` con encode/decode y validaciones.
   - Añadir tests: `tests/unit/test_enhanced_magic_number_generator.py`.

2) Gestión de secuencia
   - Implementar `SequenceManager` (memoria + fallback a BD) por clave (familia, estrategia, agente, símbolo).
   - Función: `next_sequence(symbol_ctx) -> int`.

3) Verificación operación abierta
   - Sin migrar schema: helper que lista operaciones `OPEN` por símbolo y decodifica magic para filtrar por estrategia/agente.
   - Nuevo método en repositorio (helper o en estrategia) para `get_open_by_symbol_and_agent(symbol, strategy_code, agent_code)`.

4) Integración en Intraday (Gemini 3 Pro)
   - Antes de abrir: usar verificación anterior; si existe, ir a reevaluación.
   - Si no existe: generar magic v2 (con secuencia) y abrir.
   - Persistir operación (mantener stop_loss_initial/take_profit_initial).

5) Integración en Intraday (Gemini 2.5 Pro)
   - Replicar ajustes del punto 4.

6) Prompts y flujo
   - Asegurar que con posición abierta se arma prompt “gestión” con datos de BD.
   - Mantener persistencia IAQuery (EVALUATION vs REEVALUATION).

7) Tests funcionales
   - “No abre segunda operación en mismo símbolo si ya hay una abierta”.
   - “Sí abre en otro símbolo distinto”.
   - “Secuencia incrementa correctamente y no colisiona”.

8) Feature flag y despliegue
   - Habilitar v2 solo para Intraday inicialmente (flag en config/env).
   - Documentación y guía de rollback.

## Asignación de códigos iniciales
- Familia IA: 1=Gemini, 2=GPT, 3=Grok
- Estrategia: 1=Intraday, 2=VWAP, 3=Swing
- Agente Intraday: 1=Gemini 2.5 Pro, 2=Gemini 3 Pro, 3=GPT-4, 4=Grok

## Criterios de aceptación
- Una sola posición abierta por símbolo para cada (estrategia, agente).
- Magic v2 decodificable en logs y herramientas.
- Compatibilidad: otros bots continúan con v1.

## Tracking de tareas
- [ ] 1. Crear EnhancedMagicNumberGenerator (v2)
- [ ] 2. Añadir tests unitarios v2
- [ ] 3. Implementar SequenceManager (por símbolo)
- [ ] 4. Verificación open-position por (estrategia, agente, símbolo)
- [ ] 5. Integrar en Intraday Gemini 3 Pro
- [ ] 6. Integrar en Intraday Gemini 2.5 Pro
- [ ] 7. Tests funcionales anti-doble-apertura por símbolo
- [ ] 8. Feature flag + docs

## Notas de implementación
- Sin cambiar schema por ahora: se decodifica magic para segmentar por estrategia/agente.
- Si más adelante necesitamos filtros SQL nativos, evaluamos migración para `strategy_code` y `agent_code` en `operations`.

## Bitácora
- 2025-11-23: Documento inicial creado en rama `feature/magic-number-v2-intraday`.
