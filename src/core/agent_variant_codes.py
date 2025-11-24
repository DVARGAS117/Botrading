"""
Mapeos de códigos para Familia IA, Estrategia y Variante de Agente (modelo+modalidad).

Objetivo: Resolver (family_id, strategy_id, agent_variant_id) a partir de
ai_model, nombre de estrategia y modo de datos (raw/images/hybrid).

Compatibilidad: Si no se provee `data_mode`, por defecto "raw".
"""

from typing import Tuple


# Familias IA
FAMILY_GEMINI = 1
FAMILY_GPT = 2
FAMILY_GROK = 3

# Estrategias
STRATEGY_INTRADAY = 1
STRATEGY_VWAP = 2
STRATEGY_SWING = 3


def _family_from_model(ai_model: str) -> int:
    m = (ai_model or "").lower()
    if m.startswith("gemini"):
        return FAMILY_GEMINI
    if m.startswith("gpt") or "openai" in m:
        return FAMILY_GPT
    if "grok" in m:
        return FAMILY_GROK
    # Default a GEMINI si no se reconoce
    return FAMILY_GEMINI


def _strategy_from_name(strategy_name: str) -> int:
    s = (strategy_name or "").lower().strip()
    if s == "intraday":
        return STRATEGY_INTRADAY
    if s == "vwap":
        return STRATEGY_VWAP
    if s == "swing":
        return STRATEGY_SWING
    # Default bucket
    return 9


def _agent_variant_for_gemini(ai_model: str, data_mode: str) -> int:
    """Asignaciones para estrategia Intraday (referencia base; reutilizable en otras).

    1 = Gemini 2.5 Pro (raw)
    2 = Gemini 2.5 Pro (images)
    3 = Gemini 2.5 Pro (hybrid)
    4 = Gemini 3 Pro (raw)
    5 = Gemini 3 Pro (images)
    6 = Gemini 3 Pro (hybrid)
    """
    model = (ai_model or "").lower()
    mode = (data_mode or "raw").lower()
    if "2.5" in model:
        if mode == "images":
            return 2
        if mode in ("hybrid", "combined"):
            return 3
        return 1
    # gemini 3
    if mode == "images":
        return 5
    if mode in ("hybrid", "combined"):
        return 6
    return 4


def _agent_variant_generic(data_mode: str) -> int:
    # Fallback genérico para otras familias: 1 raw, 2 images, 3 hybrid
    mode = (data_mode or "raw").lower()
    if mode == "images":
        return 2
    if mode in ("hybrid", "combined"):
        return 3
    return 1


def resolve_codes(ai_model: str, strategy_name: str, data_mode: str | None) -> Tuple[int, int, int]:
    """Retorna (family_id, strategy_id, agent_variant_id)."""
    family = _family_from_model(ai_model)
    strategy = _strategy_from_name(strategy_name)
    if family == FAMILY_GEMINI:
        agent_variant = _agent_variant_for_gemini(ai_model, data_mode or "raw")
    else:
        agent_variant = _agent_variant_generic(data_mode or "raw")
    return family, strategy, agent_variant
