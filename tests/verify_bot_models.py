"""Test de verificación: Cada bot usa su modelo correcto.

Este test asegura que:
- Bot Gemini 3 Pro (bot_id=101) usa modelo 'gemini-3-pro-preview'
- Bot Gemini 2.5 Pro (bot_id=106) usa modelo 'gemini-2.5-pro'
"""

import pytest
from src.bots.strategies.intraday.gemini_3_pro.bot_1.config import (
    get_bot_1_config as get_gemini_3_config
)
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.config import (
    get_bot_1_config as get_gemini_25_config
)
from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import (
    IntradayBot1Strategy as Gemini3ProStrategy
)
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.strategy import (
    IntradayBot1Strategy as Gemini25ProStrategy
)


def test_gemini_3_pro_uses_correct_model():
    """Verificar que Bot Gemini 3 Pro usa modelo correcto."""
    config = get_gemini_3_config()
    
    # Verificar configuración
    assert config.bot_id == 101, f"Bot ID incorrecto: {config.bot_id} (esperado: 101)"
    assert config.ai_model == "gemini-3-pro-preview", \
        f"Modelo incorrecto: {config.ai_model} (esperado: gemini-3-pro-preview)"
    assert config.bot_name == "INTRADAY Baseline", \
        f"Nombre incorrecto: {config.bot_name}"
    
    print("✅ Bot Gemini 3 Pro:")
    print(f"   - bot_id: {config.bot_id}")
    print(f"   - ai_model: {config.ai_model}")
    print(f"   - bot_name: {config.bot_name}")


def test_gemini_25_pro_uses_correct_model():
    """Verificar que Bot Gemini 2.5 Pro usa modelo correcto."""
    config = get_gemini_25_config()
    
    # Verificar configuración
    assert config.bot_id == 106, f"Bot ID incorrecto: {config.bot_id} (esperado: 106)"
    assert config.ai_model == "gemini-2.5-pro", \
        f"Modelo incorrecto: {config.ai_model} (esperado: gemini-2.5-pro)"
    assert config.bot_name == "INTRADAY Gemini 2.5 Pro", \
        f"Nombre incorrecto: {config.bot_name}"
    
    print("✅ Bot Gemini 2.5 Pro:")
    print(f"   - bot_id: {config.bot_id}")
    print(f"   - ai_model: {config.ai_model}")
    print(f"   - bot_name: {config.bot_name}")


def test_both_bots_have_different_ids():
    """Verificar que ambos bots tienen IDs únicos."""
    config_3pro = get_gemini_3_config()
    config_25pro = get_gemini_25_config()
    
    assert config_3pro.bot_id != config_25pro.bot_id, \
        f"Los bots tienen el mismo ID: {config_3pro.bot_id}"
    
    print("✅ IDs únicos verificados:")
    print(f"   - Gemini 3 Pro: {config_3pro.bot_id}")
    print(f"   - Gemini 2.5 Pro: {config_25pro.bot_id}")


def test_both_bots_have_different_models():
    """Verificar que ambos bots usan modelos diferentes."""
    config_3pro = get_gemini_3_config()
    config_25pro = get_gemini_25_config()
    
    assert config_3pro.ai_model != config_25pro.ai_model, \
        f"Los bots usan el mismo modelo: {config_3pro.ai_model}"
    
    print("✅ Modelos diferentes verificados:")
    print(f"   - Gemini 3 Pro: {config_3pro.ai_model}")
    print(f"   - Gemini 2.5 Pro: {config_25pro.ai_model}")


def test_bot_strategies_initialize_with_correct_models():
    """Verificar que las estrategias se inicializan con los modelos correctos."""
    config_3pro = get_gemini_3_config()
    config_25pro = get_gemini_25_config()
    
    # Crear instancias
    bot_3pro = Gemini3ProStrategy(config_3pro)
    bot_25pro = Gemini25ProStrategy(config_25pro)
    
    # Verificar que cada bot tiene su configuración correcta
    assert bot_3pro.config.ai_model == "gemini-3-pro-preview", \
        f"Bot 3 Pro tiene modelo incorrecto: {bot_3pro.config.ai_model}"
    assert bot_25pro.config.ai_model == "gemini-2.5-pro", \
        f"Bot 2.5 Pro tiene modelo incorrecto: {bot_25pro.config.ai_model}"
    
    print("✅ Estrategias inicializadas correctamente:")
    print(f"   - Bot 3 Pro usa: {bot_3pro.config.ai_model}")
    print(f"   - Bot 2.5 Pro usa: {bot_25pro.config.ai_model}")


if __name__ == "__main__":
    """Ejecutar tests manualmente para ver output detallado."""
    print("\n" + "="*60)
    print("VERIFICACIÓN: Modelos de IA por Bot")
    print("="*60 + "\n")
    
    try:
        test_gemini_3_pro_uses_correct_model()
        print()
        test_gemini_25_pro_uses_correct_model()
        print()
        test_both_bots_have_different_ids()
        print()
        test_both_bots_have_different_models()
        print()
        test_bot_strategies_initialize_with_correct_models()
        print()
        print("="*60)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ ERROR: {e}")
        print("="*60)
        raise
