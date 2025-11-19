# GEMINI 3 PRO PREVIEW - PRICING & COSTO ESTIMADO

Fecha: 19-11-2025

## Resumen
Se integró cálculo de costos para el modelo `gemini-3-pro-preview` tanto en:
- `GeminiClient` (SDK) -> método `_calculate_cost` con detección de contexto largo.
- `VertexAIClient` (REST) -> estimación equivalente en `send_prompt`.

## Tabla Oficial Proporcionada (por 1M tokens)
| Nivel de Contexto | Input | Output |
| ------------------ | ----- | ------ |
| Estándar (≤ 128k)  | $2.00 | $12.00 |
| Largo (> 128k)     | $4.00 | $18.00 |

## Conversión Interna (por 1K tokens)
| Tier         | Input | Output |
|--------------|-------|--------|
| Estándar     | 0.002 | 0.012  |
| Largo        | 0.004 | 0.018  |

Umbral para contexto largo: **128,000 tokens de entrada**.

## Lógica Implementada
```text
if model startswith gemini-3-pro-preview:
    if tokens_input > 128_000:
        usar tarifas LONG
    else:
        usar tarifas STANDARD
```

## Variables de Entorno (Overrides Estándar)
- `G3_STD_INPUT_PER_1K`  (ej: 0.0021)
- `G3_STD_OUTPUT_PER_1K` (ej: 0.0125)

Si se definen, sustituyen únicamente el tier estándar; el tier largo permanece fijo (se puede extender si es requerido).

## Ejemplo de Cálculo
Prompt tokens = 25,000
Output tokens = 3,000
Tier = estándar (25,000 < 128,000)
Costo = (25,000/1,000)*0.002 + (3,000/1,000)*0.012 = 0.05 + 0.036 = **$0.086**

## Futuras Extensiones
- Registrar costo acumulado por bot/día en tabla SQLite.
- Alertar si coste diario supera umbral de presupuesto.
- Modo simulación: estimar coste potencial de prompts guardados (`--save-prompts`).
- Añadir override para tarifas contexto largo (`G3_LONG_INPUT_PER_1K`, `G3_LONG_OUTPUT_PER_1K`).
- Diferenciar coste por conversación vs prompts aislados.

## Consideraciones
- No se excede actualmente el umbral de contexto largo con los `max_tokens` configurados (5120 / 10240), pero la lógica está lista para futuros ajustes.
- Redondeo a 8 decimales para evitar acumulación de flotantes.
- Tests existentes no dependen de valores concretos de coste (usan overrides internos), por lo que la actualización no rompe suites.

## Referencias
- Código: `src/core/gemini_client.py`, `src/core/vertex_ai_client.py`
- README: Sección "Migración a gemini-3-pro-preview".

---
Autor: Sistema Botrading
