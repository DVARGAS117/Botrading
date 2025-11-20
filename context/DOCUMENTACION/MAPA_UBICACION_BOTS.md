# MAPA DE UBICACIÓN DE BOTS

## Estrategia VWAP - Gemini 3 Pro

```text
src/
  bots/
    base/                              # Operaciones comunes de bots
    common/                            # Utilidades/abstracciones compartidas
    strategies/
      vwap/
        __init__.py
        gemini_3_pro/
          __init__.py
          bot_1/                       # Bot 1 - Numérico baseline VWAP
            __init__.py
            config.py
            strategy.py
            main.py
            prompts/
          bot_2/                       # Bot 2 - Numérico alt prompts (pendiente ajustes)
          bot_3/                       # Bot 3 - Visual (pendiente ajustes)
          bot_4/                       # Bot 4 - Híbrido (pendiente ajustes)
          bot_5/                       # Bot 5 - Visual+numérico (pendiente ajustes)
```

## Notas

- Los bots `bot_1` a `bot_5` representan variantes de la **misma estrategia VWAP**, con diferentes formatos de entrada (numérico, visual, híbrido) bajo `strategies/vwap/gemini_3_pro`.
- La nueva organización por estrategia/agente permite añadir fácilmente:
  - Otros agentes IA (p. ej. `gpt_4_x`, `grok_1_0`) bajo `strategies/vwap/`.
  - Nuevas estrategias (p. ej. `mean_reversion`, `breakout`) como subcarpetas dentro de `strategies/`.
- La prioridad actual es que `bot_1` funcione totalmente desde la nueva ubicación; los bots 2–5 ya están ubicados en `strategies/vwap/gemini_3_pro` pero aún requieren ajustes de imports e implementación.
