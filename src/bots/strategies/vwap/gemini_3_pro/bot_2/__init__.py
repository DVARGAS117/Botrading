"""
Bot 2: Numérico con Prompts Alternativos

Tipo: Análisis numérico puro (mismo que Bot 1)
Datos: EMA 20, EMA 50, RSI, MACD, Volumen (3 timeframes: 5M, 15M, 1H)
Estrategia: Dual Market + Limit
Prompts: numerico_evaluacion (versión customizada), numerico_reevaluacion

Objetivo:
Comparar el impacto de diferentes enfoques en los prompts
usando exactamente los mismos datos que Bot 1.

Diferencia clave: Los prompts tienen instrucciones/metodología diferente
(por ejemplo: enfoque en SMC, ICT, o estrategia específica).
"""

__version__ = "0.1.0"
__bot_id__ = 2
__bot_type__ = "numerico"
