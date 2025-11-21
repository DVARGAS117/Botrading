"""Script de ejecución para Bot INTRADAY Gemini 2.5 Pro.

Este script configura el PYTHONPATH correctamente y ejecuta el bot.
"""

import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Importar y ejecutar el main del bot
from src.bots.strategies.intraday.gemini_2_5_pro.bot_1.main import main

if __name__ == "__main__":
    main()
