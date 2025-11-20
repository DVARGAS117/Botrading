"""
Bot 5: Visual + Indicadores Numéricos Separados

Tipo: Visual con datos numéricos en JSON separado
Datos:
  - 3 imágenes de velas limpias (SIN indicadores dibujados)
  - JSON con indicadores calculados numéricamente
Estrategia: Dual Market + Limit
Prompts: hibrido_evaluacion, hibrido_reevaluacion

Objetivo:
Evaluar si proporcionar información visual (velas puras)
separada de los indicadores numéricos permite a la IA
procesar ambos tipos de datos de forma más efectiva.

Diferencia con Bot 3: Los indicadores NO están dibujados
en las imágenes, sino proporcionados como datos.

Diferencia con Bot 4: Usa visual + numérico tanto en
apertura como en reevaluación.
"""

__version__ = "0.1.0"
__bot_id__ = 5
__bot_type__ = "hibrido"
