# Tests Intraday: Riesgo Dinámico y Magic v2

## Objetivo
Validar que el sizing dinámico basado en `riesgo_porcentaje` funciona correctamente y que las operaciones persisten con los campos de riesgo en BD usando Magic Number v2.

## Archivos
- `test_intraday_dynamic_risk.py`: Gemini 3 Pro.
- `test_intraday_dynamic_risk_25.py`: Gemini 2.5 Pro.

## Flujo de Cada Test
1. Obtiene balance y especificación del símbolo.
2. Calcula lote esperado con `PositionSizer` (usando distancia SL fija y riesgo %).
3. Ejecuta apertura forzada vía `_execute_open_position` con decisión simulada.
4. Recupera posición abierta y operación en BD (por `magic`).
5. Compara lote real vs esperado y riesgo persistido $ / %.
6. Reporta diferencias y valida tolerancias.

## Ejecución
```powershell
# Activar entorno virtual
powershell -ExecutionPolicy Bypass -File .venv\Scripts\Activate.ps1

# Test Gemini 3 Pro
python tests\intraday\test_intraday_dynamic_risk.py

# Test Gemini 2.5 Pro
python tests\intraday\test_intraday_dynamic_risk_25.py
```

## Requisitos
- Cuenta MT5 DEMO conectada y símbolo `EURUSD` habilitado.
- Configuración de bots con IDs actualizados (3 y 4) y lógica Magic v2 activa.

## Interpretación de Resultados
- Diferencia de lote < 0.05 confirma ajuste correcto a step y límites.
- `risk_percentage` y `risk_amount` persistidos deben alinearse con cálculo teórico (tolerancia <= $0.5).
- Si no se abre posición se revisa:
  - `trade_stops_level` vs distancia SL.
  - `last_error` MT5.
  - Comentario (sanitizado: `B3_INTRA` / `B4_INTRA`).

## Próximas Extensiones
- Test de ajuste dinámico de SL (Trailing en múltiplos de R).
- Test cierre y cálculo de PnL en R acumulado.
- Test fallback cuando la IA omite `riesgo_porcentaje`.

---
Autor: GitHub Copilot
Fecha: 24-11-2025
