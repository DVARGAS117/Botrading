"""
Ejemplo de flujo completo con ajuste de SL/TP

Muestra cómo la IA puede decidir ajustar trailing stop.
"""

# Ejemplo 1: Posición con +2R de ganancia - Debería ajustar SL a +1R

position_info_input = """
POSICIÓN ACTIVA: LONG @ 1.05000
- Volumen: 0.1 lotes
- PnL Actual: $40.00 USD (40.0 pips = 2.00R)
- Stop Loss: 1.04800 | Take Profit: 1.05500
- Precio Actual: 1.05400
- Duración: 2h 15m
- Riesgo Inicial (1R): 20.0 pips

⚠️ PRIORIDAD: Gestiona esta posición. Evalúa si debe CERRARSE, AJUSTAR_SL_TP o MANTENERSE.
"""

expected_response_1 = {
    "accion": "AJUSTAR_SL_TP",
    "razonamiento": "Ganancia de +2R alcanzada. Aplicar trailing stop moviendo SL a +1R para proteger ganancias.",
    "direccion": None,
    "stop_loss": 1.05200,  # Nuevo SL a +1R (precio entrada + 20 pips)
    "take_profit": 1.05500,  # TP sin cambios
    "confianza": 85,
    "estrategia_usada": "A",
    "diagnostico_mercado": "TENDENCIA_ALCISTA"
}

print("="*70)
print("EJEMPLO 1: Trailing Stop con +2R de ganancia")
print("="*70)
print("\nINPUT (Posición Actual):")
print(position_info_input)
print("\nEXPECTED OUTPUT (Decisión IA):")
import json
print(json.dumps(expected_response_1, indent=2))
print()

# Ejemplo 2: Posición con +1R - Debería mover SL a break-even

position_info_input_2 = """
POSICIÓN ACTIVA: SHORT @ 1.06000
- Volumen: 0.1 lotes
- PnL Actual: $25.00 USD (25.0 pips = 1.25R)
- Stop Loss: 1.06200 | Take Profit: 1.05500
- Precio Actual: 1.05750
- Duración: 1h 45m
- Riesgo Inicial (1R): 20.0 pips

⚠️ PRIORIDAD: Gestiona esta posición. Evalúa si debe CERRARSE, AJUSTAR_SL_TP o MANTENERSE.
"""

expected_response_2 = {
    "accion": "AJUSTAR_SL_TP",
    "razonamiento": "Ganancia >= +1R. Mover SL a break-even para eliminar riesgo.",
    "direccion": None,
    "stop_loss": 1.06000,  # Nuevo SL a break-even (precio entrada)
    "take_profit": 1.05500,  # TP sin cambios
    "confianza": 90,
    "estrategia_usada": "A",
    "diagnostico_mercado": "TENDENCIA_BAJISTA"
}

print("="*70)
print("EJEMPLO 2: Break-even con +1R de ganancia")
print("="*70)
print("\nINPUT (Posición Actual):")
print(position_info_input_2)
print("\nEXPECTED OUTPUT (Decisión IA):")
print(json.dumps(expected_response_2, indent=2))
print()

# Ejemplo 3: Precio cerca de TP pero hay resistencia - Ajustar TP

position_info_input_3 = """
POSICIÓN ACTIVA: LONG @ 1.05000
- Volumen: 0.1 lotes
- PnL Actual: $35.00 USD (35.0 pips = 1.75R)
- Stop Loss: 1.04800 | Take Profit: 1.05500
- Precio Actual: 1.05350
- Duración: 3h 10m
- Riesgo Inicial (1R): 20.0 pips

⚠️ PRIORIDAD: Gestiona esta posición. Evalúa si debe CERRARSE, AJUSTAR_SL_TP o MANTENERSE.

NOTA ADICIONAL: Análisis técnico muestra resistencia fuerte en 1.05450 (máximo previo de sesión).
"""

expected_response_3 = {
    "accion": "AJUSTAR_SL_TP",
    "razonamiento": "Resistencia fuerte en 1.05450 detectada. Ajustar TP antes para asegurar ganancias de +1.5R.",
    "direccion": None,
    "stop_loss": 1.05200,  # Mover SL a +1R también
    "take_profit": 1.05400,  # Nuevo TP antes de resistencia
    "confianza": 80,
    "estrategia_usada": "A",
    "diagnostico_mercado": "TENDENCIA_ALCISTA"
}

print("="*70)
print("EJEMPLO 3: Ajuste de TP por resistencia cercana")
print("="*70)
print("\nINPUT (Posición Actual):")
print(position_info_input_3)
print("\nEXPECTED OUTPUT (Decisión IA):")
print(json.dumps(expected_response_3, indent=2))
print()

# Ejemplo 4: Posición sin necesidad de ajuste

position_info_input_4 = """
POSICIÓN ACTIVA: LONG @ 1.05000
- Volumen: 0.1 lotes
- PnL Actual: $10.00 USD (10.0 pips = 0.50R)
- Stop Loss: 1.04800 | Take Profit: 1.05500
- Precio Actual: 1.05100
- Duración: 0h 25m
- Riesgo Inicial (1R): 20.0 pips

⚠️ PRIORIDAD: Gestiona esta posición. Evalúa si debe CERRARSE, AJUSTAR_SL_TP o MANTENERSE.
"""

expected_response_4 = {
    "accion": "MANTENER",
    "razonamiento": "Posición aún no alcanza +1R. Tendencia sigue válida. Mantener sin cambios.",
    "direccion": None,
    "stop_loss": None,  # Sin cambios
    "take_profit": None,  # Sin cambios
    "confianza": 75,
    "estrategia_usada": "A",
    "diagnostico_mercado": "TENDENCIA_ALCISTA"
}

print("="*70)
print("EJEMPLO 4: Mantener sin ajustes (menos de +1R)")
print("="*70)
print("\nINPUT (Posición Actual):")
print(position_info_input_4)
print("\nEXPECTED OUTPUT (Decisión IA):")
print(json.dumps(expected_response_4, indent=2))
print()

print("="*70)
print("RESUMEN DE ACCIONES")
print("="*70)
print("""
AJUSTAR_SL_TP: Cuando se necesita modificar SL/TP
  - Trailing stop: +1R -> break-even, +2R -> +1R
  - Ajuste de TP: Resistencia/soporte cercano
  
MANTENER: Cuando la posición está bien pero no necesita ajustes
  - Ganancia < +1R
  - Sin señales de reversión
  
CERRAR: Cuando debe salir completamente
  - TP alcanzado
  - SL alcanzado
  - Señal fuerte de reversión
""")
