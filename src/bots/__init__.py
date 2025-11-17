"""
Paquete de bots de trading automatizado.

Este paquete contiene las 5 instancias de bots independientes:
- Bot 1: Numérico baseline (Market + Limit)
- Bot 2: Numérico con prompts alternativos (Market + Limit)
- Bot 3: Visual con indicadores en gráficos (Market + Limit)
- Bot 4: Híbrido - Visual para apertura, numérico para reevaluación (Market + Limit)
- Bot 5: Visual + Indicadores numéricos separados (Market + Limit)

Cada bot opera de forma independiente y puede ser ejecutado como proceso separado.
"""

__version__ = "0.1.0"

# Importar bots cuando estén implementados
# from .bot_1.main import Bot1
# from .bot_2.main import Bot2
# from .bot_3.main import Bot3
# from .bot_4.main import Bot4
# from .bot_5.main import Bot5
# from .orchestrator import BotOrchestrator

__all__ = [
    # "Bot1",
    # "Bot2",
    # "Bot3",
    # "Bot4",
    # "Bot5",
    # "BotOrchestrator",
]
