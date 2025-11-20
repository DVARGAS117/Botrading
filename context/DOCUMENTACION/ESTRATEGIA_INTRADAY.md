# ESTRATEGIA INTRADAY - Gemini 3 Pro

## Descripción General

La estrategia **INTRADAY** es un sistema de trading diseñado para operar dentro del día, aprovechando movimientos de precio en marcos temporales cortos. A diferencia de la estrategia VWAP, INTRADAY es una estrategia independiente con sus propias reglas, indicadores y gestión de riesgo.

**Versión**: 1.0.0  
**Fecha**: 19 de Noviembre de 2025  
**Estado**: Estructura Base Implementada - Pendiente Definición de Indicadores

---

## Características Principales

### 1. Análisis Multi-Timeframe
- **M1**: Señales precisas de entrada
- **M5**: Contexto táctico
- **M15**: Contexto intermedio
- **H1**: Tendencia general del día

### 2. Gestión de Riesgo Específica
- **Riesgo por operación**: 1% del capital
- **Riesgo máximo diario**: 3R (Risk units)
- **Una orden por señal** (sin dual orders)
- **Reevaluación**: Cada 10 minutos

### 3. Horario de Operación
- **Horario**: 08:00 - 16:00 (hora Lima, UTC-5)
- **Timeframe objetivo**: Sesión europea y americana

---

## Configuración Técnica

### Modelo de IA: Gemini 3 Pro

La estrategia utiliza **Gemini 3 Pro Preview** con los siguientes parámetros optimizados:

```json
{
  "thinking_level": "HIGH",
  "code_execution": true,
  "media_resolution": "high",
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192
}
```

**Justificación de Parámetros**:
- `thinking_level: HIGH`: Razonamiento profundo para análisis técnico complejo
- `code_execution: true`: Cálculos matemáticos precisos de indicadores
- `media_resolution: high`: Análisis de alta calidad (futuro: gráficos)

### Costos Estimados (Vertex AI)

| Nivel de Contexto | Input (por 1M tokens) | Output (por 1M tokens) |
|-------------------|----------------------|------------------------|
| Estándar (≤ 128k) | $2.00 USD | $12.00 USD |
| Contexto Largo (> 128k) | $4.00 USD | $18.00 USD |

---

## Estructura del Proyecto

```
src/bots/strategies/intraday/
├── __init__.py
└── gemini_3_pro/
    ├── __init__.py
    └── bot_1/
        ├── __init__.py
        ├── config.py           # Configuración del bot
        ├── strategy.py         # Lógica de la estrategia
        ├── main.py            # Punto de entrada
        └── prompts/
            └── README.md       # Documentación de prompts
```

---

## Configuración del Bot (config.py)

### BotConfig

```python
BotConfig(
    bot_id=101,                           # ID único para INTRADAY
    bot_name="INTRADAY Baseline",
    bot_type="intraday",
    mode=BotMode.DEMO,                    # DEMO o LIVE
    symbols=["EURUSD"],
    timeframes=[M1, M5, M15, H1],
    trading_hours=("08:00", "16:00"),     # Personalizado
    timezone_local="America/Lima",
    risk_per_trade=1.0,                   # 1% por operación
    max_daily_risk=3.0,                   # 3R máximo diario
    reevaluation_interval_minutes=10,     # Cada 10 min
    ai_model="gemini-3-pro-preview",
    enable_dual_orders=False,             # Solo una orden
    log_level="INFO"
)
```

### BOT_1_SETTINGS

```python
{
    "nombre_corto": "B1_INTRADAY",
    "estrategia": "INTRADAY",
    "version": "1.0.0",
    
    "gemini_config": {
        "thinking_level": "HIGH",
        "code_execution": True,
        "media_resolution": "high",
        ...
    },
    
    "execution_config": {
        "use_market_orders": True,
        "use_dual_orders": False,           # Diferencia clave con VWAP
        "max_slippage_pips": 5.0,
        "partial_close_enabled": True
    }
}
```

---

## Métodos Principales (strategy.py)

### IntradayBot1Strategy

Hereda de `BaseBotOperations` y proporciona:

#### 1. `prepare_data_for_ai()`
Construye prompts para Gemini 3 Pro con:
- Indicadores técnicos (TODO: definir cuáles)
- Contexto de mercado
- Datos OHLCV históricos

**Estado**: Implementación placeholder

#### 2. `parse_ai_response()`
Parsea respuesta de Gemini 3 Pro a formato ejecutable:
```python
{
    "accion": "COMPRAR" | "VENDER" | "NO_OPERAR",
    "razonamiento": str,
    "direccion": "LONG" | "SHORT" | None,
    "stop_loss": float,
    "take_profit": float,
    "confianza": float
}
```

**Estado**: Implementación placeholder

#### 3. `get_performance_metrics()`
Retorna métricas en tiempo real:
- PnL del día (en R)
- Número de trades
- Contexto de mercado
- Estado del bot

**Estado**: ✅ Implementado

#### 4. `analyze_intraday_levels()` *(Placeholder)*
Identificación de niveles clave:
- Soportes
- Resistencias
- Puntos pivote

**Estado**: Pendiente de implementación

#### 5. `calculate_intraday_volatility()` *(Placeholder)*
Cálculo de volatilidad para ajuste dinámico de stops.

**Estado**: Pendiente de implementación

---

## Ejecución del Bot

### Línea de Comandos

```bash
# Modo DEMO - Un solo ciclo
python -m src.bots.strategies.intraday.gemini_3_pro.bot_1.main --single-cycle

# Modo DEMO - Continuo (cada 5 minutos)
python -m src.bots.strategies.intraday.gemini_3_pro.bot_1.main --interval 300

# Modo LIVE (requiere confirmación)
python -m src.bots.strategies.intraday.gemini_3_pro.bot_1.main --mode live

# Modo LIVE (auto-confirmado)
python -m src.bots.strategies.intraday.gemini_3_pro.bot_1.main --mode live --yes

# Múltiples símbolos
python -m src.bots.strategies.intraday.gemini_3_pro.bot_1.main --symbols EURUSD GBPUSD

# Solo generar prompts (sin consultar IA)
python -m src.bots.strategies.intraday.gemini_3_pro.bot_1.main --save-prompts
```

### Argumentos Disponibles

| Argumento | Descripción | Default |
|-----------|-------------|---------|
| `--mode` | Modo de operación (demo/live) | `demo` |
| `--single-cycle` | Ejecutar solo un ciclo | `False` |
| `--interval` | Intervalo entre ciclos (segundos) | `300` |
| `--symbols` | Símbolos a operar | `["EURUSD"]` |
| `--log-level` | Nivel de logging | `INFO` |
| `--yes` | Auto-confirmar modo LIVE | `False` |
| `--save-prompts` | Solo guardar prompts | `False` |

---

## Testing

### Estructura de Tests

```
tests/bots/strategies/intraday/gemini_3_pro/bot_1/
├── __init__.py
├── test_config.py      # Tests de configuración
├── test_strategy.py    # Tests de lógica de estrategia
└── test_main.py        # Tests de punto de entrada
```

### Ejecutar Tests

```bash
# Todos los tests de INTRADAY Bot 1
pytest tests/bots/strategies/intraday/gemini_3_pro/bot_1/ -v

# Solo tests de configuración
pytest tests/bots/strategies/intraday/gemini_3_pro/bot_1/test_config.py -v

# Con cobertura
pytest tests/bots/strategies/intraday/gemini_3_pro/bot_1/ --cov=src.bots.strategies.intraday
```

**Estado**: ✅ Tests implementados y pasando

---

## Diferencias con Estrategia VWAP

| Característica | VWAP | INTRADAY |
|----------------|------|----------|
| **Dual Orders** | ✅ Sí (Market + Limit) | ❌ No (solo Market) |
| **Horario** | 09:00 - 13:00 | 08:00 - 16:00 |
| **Riesgo/Trade** | 0.5% | 1.0% |
| **Riesgo Diario** | 2R | 3R |
| **Reevaluación** | 10 min | 10 min |
| **Indicadores** | VWAP, Bandas, OR | TODO: Definir |
| **Metodología** | Trend-following VWAP | TODO: Definir |

---

## Pendientes de Implementación

### 🔴 Crítico (Próximos Pasos)

1. **Definir Indicadores Técnicos**
   - EMA (¿períodos?)
   - RSI (¿períodos?)
   - MACD
   - Bandas de Bollinger
   - Otros...

2. **Implementar Prompt Builder Específico**
   - System prompt para estrategia INTRADAY
   - User prompt con formato de indicadores
   - Instrucciones de análisis

3. **Implementar Response Parser**
   - Parseo de respuesta de Gemini
   - Validación de campos
   - Conversión a formato ejecutable

4. **Definir Reglas de Entrada/Salida**
   - Condiciones para LONG
   - Condiciones para SHORT
   - Condiciones para NO_OPERAR
   - Gestión de stops y targets

### 🟡 Media Prioridad

5. **Análisis de Niveles Intraday**
   - Implementar `analyze_intraday_levels()`
   - Soportes y resistencias dinámicos
   - Puntos pivote

6. **Cálculo de Volatilidad**
   - Implementar `calculate_intraday_volatility()`
   - ATR u otra métrica
   - Ajuste dinámico de stops

7. **Logging Avanzado**
   - Guardar gráficos (opcional)
   - Historial de decisiones IA
   - Métricas de rendimiento

### 🟢 Baja Prioridad

8. **Optimización de Parámetros**
   - Backtesting de horarios
   - Ajuste de riesgo
   - Optimización de indicadores

9. **Trailing Stops**
   - Implementar trailing stop dinámico
   - Basado en ATR o volatilidad

10. **Multi-Symbol**
    - Optimizar para múltiples pares
    - Gestión de correlaciones

---

## Documentos Relacionados

- [Parámetros Gemini 3 Pro](./PARAMETROS_GEMINI_3_PRO.md)
- [Sistema de Consultas y Almacenamiento](./INTRADAY_SISTEMA_CONSULTAS.md)
- [Mapa de Ubicación de Bots](./MAPA_UBICACION_BOTS.md)
- [Agents Rules](../agents.md)

---

## Notas Importantes

⚠️ **ADVERTENCIA**: Esta es la estructura BASE de la estrategia INTRADAY. Los métodos críticos (`prepare_data_for_ai`, `parse_ai_response`) están implementados como placeholders y **NO** son funcionales para trading real.

✅ **Próximos Pasos**: Definir indicadores, prompts y reglas de la estrategia antes de ejecutar en modo LIVE.

📊 **Testing**: Todos los tests unitarios pasan correctamente. La estructura está lista para implementar la lógica específica.

---

**Última Actualización**: 19 de Noviembre de 2025  
**Autor**: Agente IA siguiendo TDD y reglas del proyecto  
**Branch**: `feature/estrategia-intraday-gemini-3-pro`
