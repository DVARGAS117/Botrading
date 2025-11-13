# T23 - Cálculo y formato de indicadores por timeframe

## Historia de Usuario

Como bot numérico, quiero calcular y formatear indicadores por los tres timeframes, para enviar un payload consistente a IA.

## Criterios de Aceptación

- **Escenario: Calcular indicadores por timeframe**
  - Dado que existen velas cerradas 5M, 15M y 1H
  - Cuando el bot numérico calcula EMA 20/50, RSI, MACD y volumen
  - Entonces construye un JSON consistente para la IA por cada timeframe

## Implementación

### Arquitectura

Se implementa la clase `IndicatorCalculator` en `src/core/indicator_calculator.py` que proporciona:

- Cálculo de indicadores técnicos individuales (EMA, RSI, MACD, volumen promedio)
- Cálculo de indicadores para un timeframe específico
- Cálculo de indicadores para múltiples timeframes simultáneamente
- Formateo consistente de resultados en JSON para IA

### Indicadores Calculados

#### EMA (Exponential Moving Average)
- **EMA 20**: Media móvil exponencial de 20 períodos
- **EMA 50**: Media móvil exponencial de 50 períodos
- **Implementación**: Usando `pandas.Series.ewm(span=period, adjust=False).mean()`

#### RSI (Relative Strength Index)
- **Período**: 14 períodos por defecto
- **Fórmula**: RSI = 100 - (100 / (1 + RS)) donde RS = Average Gain / Average Loss
- **Rango**: 0-100

#### MACD (Moving Average Convergence Divergence)
- **Componentes**:
  - **MACD Line**: EMA(12) - EMA(26)
  - **Signal Line**: EMA(9) del MACD Line
  - **Histogram**: MACD Line - Signal Line
- **Períodos**: 12, 26, 9 (fast, slow, signal)

#### Volumen Promedio
- **Período**: 20 períodos
- **Implementación**: Media móvil simple del volumen

### Estructura de Datos

#### IndicatorData
```python
@dataclass
class IndicatorData:
    symbol: str
    timeframe: Timeframe
    ema20: Optional[float]
    ema50: Optional[float]
    rsi: Optional[float]
    macd: Optional[float]
    signal: Optional[float]
    histogram: Optional[float]
    volume_avg: Optional[float]
```

#### TimeframeIndicators
```python
@dataclass
class TimeframeIndicators:
    symbol: str
    indicators: Dict[Timeframe, IndicatorData]
```

### Formato JSON para IA

```json
{
  "symbol": "EURUSD",
  "timestamp": "2025-11-13T10:30:00.000000",
  "timeframes": {
    "M5": {
      "indicators": {
        "ema20": 1.1050,
        "ema50": 1.1020,
        "rsi": 65.5,
        "macd": 0.0012,
        "signal": 0.0008,
        "histogram": 0.0004,
        "volume_avg": 5000.0
      }
    },
    "M15": {
      "indicators": {
        "ema20": 1.1045,
        "ema50": 1.1015,
        "rsi": 62.0,
        "macd": 0.0010,
        "signal": 0.0007,
        "histogram": 0.0003,
        "volume_avg": 4800.0
      }
    },
    "H1": {
      "indicators": {
        "ema20": 1.1040,
        "ema50": 1.1010,
        "rsi": 58.5,
        "macd": 0.0008,
        "signal": 0.0006,
        "histogram": 0.0002,
        "volume_avg": 4500.0
      }
    }
  }
}
```

### Requisitos de Datos

- **Mínimo de velas**: 50 velas por timeframe para garantizar cálculos confiables
- **Columnas requeridas**: time, open, high, low, close, volume
- **Timeframes soportados**: M5, M15, H1

### Métodos Principales

#### `calculate_indicators_for_timeframe(ohlcv_data: OHLCVData) -> IndicatorData`
Calcula todos los indicadores para un timeframe específico.

#### `calculate_indicators_multi_timeframe(symbol: str, timeframes_data: Dict[Timeframe, OHLCVData]) -> TimeframeIndicators`
Calcula indicadores para múltiples timeframes simultáneamente.

#### `format_indicators_json(indicators: TimeframeIndicators) -> Dict`
Formatea los indicadores en estructura JSON consistente para IA.

### Validaciones

- Verificación de datos suficientes (mínimo 50 velas)
- Validación de columnas requeridas en DataFrame
- Manejo de errores por timeframe individual
- Continuación del procesamiento aunque fallen algunos timeframes

### Testing

Se implementan pruebas unitarias completas en `tests/unit/test_indicator_calculator.py`:

- Pruebas de cálculo individual de cada indicador
- Pruebas de integración por timeframe
- Pruebas de cálculo multi-timeframe
- Pruebas de formateo JSON
- Pruebas de manejo de errores

### Dependencias

- **pandas**: Para manipulación de datos y cálculos técnicos
- **numpy**: Para operaciones numéricas
- **datetime**: Para timestamps en JSON

### Integración

El módulo se integra con:

- `MT5DataExtractor`: Para obtener datos OHLCV
- Sistema de IA: Para enviar indicadores formateados
- Sistema de logging: Para trazabilidad de cálculos

### Consideraciones de Rendimiento

- Los cálculos se realizan en memoria usando pandas/numpy
- No hay operaciones I/O durante el cálculo
- Los indicadores se calculan de forma vectorizada para eficiencia

### Mantenibilidad

- Código documentado con docstrings PyDoc
- Funciones modulares y reutilizables
- Manejo robusto de errores
- Tests automatizados para regression testing

## Autor

Sistema Botrading

## Fecha

2025-11-13

## Ticket

T23 - Cálculo y formato de indicadores por timeframe