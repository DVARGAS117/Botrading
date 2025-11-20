"""Entry point del Bot 1 (Numérico Baseline VWAP, Gemini 3 Pro)."""

from src.bots.strategies.vwap.gemini_3_pro.bot_1.main import main as bot_1_main
from src.bots.strategies.vwap.gemini_3_pro.bot_1.config import (
	BOT_1_SETTINGS,
)

__version__ = BOT_1_SETTINGS["version"]
__bot_id__ = 1
__bot_type__ = "numerico"

__all__ = ["bot_1_main", "__version__", "__bot_id__", "__bot_type__"]

