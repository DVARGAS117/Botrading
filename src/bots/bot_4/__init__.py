"""
Bot 4: Híbrido (Visual Apertura + Numérico Reevaluación)

Tipo: Híbrido - combina visual y numérico estratégicamente
Datos:
  - Apertura: 1 imagen de velas SIN indicadores
  - Reevaluación: Indicadores numéricos
Estrategia: Dual Market + Limit
Prompts: hibrido_evaluacion, numerico_reevaluacion

Objetivo:
Evaluar si un análisis visual "limpio" en la apertura
combinado con seguimiento numérico es más efectivo.

Hipótesis: La IA puede detectar patrones visuales puros mejor
sin el ruido de indicadores, pero para seguimiento
los datos numéricos son más eficientes.
"""

__version__ = "0.1.0"
__bot_id__ = 4
__bot_type__ = "hibrido"
