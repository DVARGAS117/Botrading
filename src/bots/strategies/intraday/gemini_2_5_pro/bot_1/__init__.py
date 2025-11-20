"""Bot 1 - INTRADAY Strategy con Gemini 2.5 Pro.

Este paquete contiene la implementación del bot de estrategia INTRADAY
utilizando el modelo Gemini 2.5 Pro.
"""

from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.config import (
    get_bot_1_config,
    BOT_1_SETTINGS,
)
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.strategy import (
    IntradayBot1Strategy,
)

__all__ = [
    "get_bot_1_config",
    "BOT_1_SETTINGS",
    "IntradayBot1Strategy",
]
