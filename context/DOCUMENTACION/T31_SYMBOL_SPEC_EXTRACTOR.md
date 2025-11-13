# T31 - Obtención de Especificaciones del Símbolo desde MT5

**Estado**: ✅ Implementado  
**Fecha**: 2025-11-13  
**Ticket**: #47  
**Prioridad**: P0  
**Fase**: 2

---

## 📋 Resumen

Este ticket implementa la funcionalidad para obtener especificaciones de símbolos directamente desde MetaTrader 5, evitando supuestos incorrectos y garantizando que el cálculo de lotes use datos reales del broker.

## 🎯 Objetivo

**Historia de Usuario:**  
Como desarrollador, quiero obtener especificaciones del activo desde MT5 antes del cálculo, para evitar supuestos incorrectos.

**Criterios de Aceptación:**
```gherkin
Escenario: Obtener especificaciones del símbolo desde MT5
  Dado que se va a calcular el lote
  Cuando se consultan dígitos, valor por tick y tamaño de contrato en MT5
  Entonces el cálculo usa datos reales del símbolo sin supuestos
```

## 🔧 Implementación

### Módulo Principal: `SymbolSpecificationExtractor`

**Ubicación**: `src/core/symbol_spec_extractor.py`

El módulo `SymbolSpecificationExtractor` es responsable de:

1. **Extraer información de MT5**: Usa `MT5Connector.get_symbol_info()` para obtener datos reales
2. **Convertir a SymbolSpecification**: Transforma la información de MT5 al formato usado por `PositionSizer` y `LotAdjuster`
3. **Cachear especificaciones**: Evita múltiples llamadas a MT5 para el mismo símbolo
4. **Validar datos**: Asegura que la información obtenida sea válida antes de usarla

### Componentes Implementados

#### 1. SymbolSpecificationExtractor

```python
from src.core.symbol_spec_extractor import SymbolSpecificationExtractor
from src.core.mt5_connector import MT5Connector, BrokerConfig

# Conectar a MT5
config = BrokerConfig(
    account_id="12345678",
    password="password",
    server="Pepperstone-Demo"
)
connector = MT5Connector(config)
connector.verify_connection()

# Crear extractor
extractor = SymbolSpecificationExtractor(connector)

# Obtener especificación para PositionSizer
spec = extractor.get_symbol_specification("EURUSD")
print(f"Min lot: {spec.volume_min}, Max: {spec.volume_max}")

# Obtener especificación para LotAdjuster
lot_spec = extractor.get_lot_adjuster_specification("EURUSD")
```

#### 2. Características Principales

**Caché de Especificaciones:**
```python
# Primera llamada: obtiene desde MT5
spec1 = extractor.get_symbol_specification("EURUSD")

# Segunda llamada: obtiene desde caché (instantáneo)
spec2 = extractor.get_symbol_specification("EURUSD")

# Limpiar caché específico
extractor.clear_cache("EURUSD")

# Limpiar todo el caché
extractor.clear_cache()
```

**Prefetch de Múltiples Símbolos:**
```python
symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
specs = extractor.prefetch_symbols(symbols)
print(f"Loaded {len(specs)} specifications")
```

**Refresh de Especificaciones:**
```python
# Forzar actualización desde MT5
spec = extractor.get_symbol_specification("EURUSD", use_cache=False)
```

#### 3. Excepciones

- `SymbolSpecificationError`: Error base
- `SymbolNotFoundError`: Símbolo no existe en MT5
- `InvalidSymbolDataError`: Datos inválidos recibidos de MT5

### Integración con Componentes Existentes

#### Con PositionSizer

```python
from src.core.position_sizer import PositionSizer, RiskParameters

# Obtener especificación desde MT5
spec = extractor.get_symbol_specification("EURUSD")

# Usar en PositionSizer
risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=1.0,
    entry_price=1.10000,
    stop_loss=1.09900,
    symbol_spec=spec  # ¡Datos reales de MT5!
)

sizer = PositionSizer()
result = sizer.calculate_lot_size(risk_params)
```

#### Con LotAdjuster

```python
from src.core.lot_adjuster import LotAdjuster

# Obtener especificación para LotAdjuster
lot_spec = extractor.get_lot_adjuster_specification("EURUSD")

# Usar en LotAdjuster
adjuster = LotAdjuster()
result = adjuster.adjust_lot(0.456, lot_spec)
```

## ✅ Tests

**Ubicación**: `tests/unit/core/test_symbol_spec_extractor.py`

**Cobertura de Tests:**
- ✅ Inicialización correcta
- ✅ Extracción de especificaciones (EURUSD, XAUUSD)
- ✅ Manejo de símbolos no encontrados
- ✅ Validación de nombres vacíos/None
- ✅ Conversión a formato LotAdjuster
- ✅ Sistema de caché
- ✅ Limpieza de caché
- ✅ Caché de múltiples símbolos
- ✅ Validación de datos inválidos
- ✅ Refresh de especificaciones
- ✅ Integración con PositionSizer
- ✅ Manejo de errores de MT5

**Ejecución de Tests:**
```bash
pytest tests/unit/core/test_symbol_spec_extractor.py -v
```

**Resultado**: ✅ 17/17 tests passing

## 📚 Ejemplos

**Ubicación**: `examples/symbol_spec_extractor_example.py`

El archivo de ejemplos incluye 4 escenarios completos:

1. **Uso Básico**: Obtener especificaciones de símbolos desde MT5
2. **Integración con PositionSizer**: Calcular lotes con datos reales
3. **Caché y Prefetch**: Optimización de llamadas a MT5
4. **Integración con LotAdjuster**: Validar lotes con límites reales

**Ejecutar Ejemplos:**
```bash
python examples/symbol_spec_extractor_example.py
```

## 📊 Especificaciones Obtenidas

Las especificaciones extraídas desde MT5 incluyen:

| Campo | Descripción | Ejemplo (EURUSD) |
|-------|-------------|------------------|
| `symbol` | Nombre del símbolo | "EURUSD" |
| `point` | Tamaño del punto | 0.00001 |
| `tick_size` | Tamaño del tick | 0.00001 |
| `tick_value` | Valor del tick | $1.00 |
| `volume_min` | Volumen mínimo | 0.01 |
| `volume_max` | Volumen máximo | 100.0 |
| `volume_step` | Incremento de volumen | 0.01 |
| `contract_size` | Tamaño del contrato | 100,000 |

## 🔍 Validaciones

El extractor valida automáticamente:

- ✅ Point > 0
- ✅ Tick size > 0
- ✅ Tick value > 0
- ✅ Volume min > 0
- ✅ Volume max > 0
- ✅ Volume min ≤ Volume max
- ✅ Volume step > 0
- ✅ Contract size > 0

## 🚀 Beneficios

1. **Evita Supuestos Incorrectos**: Los datos vienen directamente de MT5
2. **Normalización del Riesgo**: Garantiza cálculos precisos entre diferentes activos
3. **Prevención de Errores**: Las órdenes cumplen con restricciones reales del broker
4. **Optimización**: Sistema de caché reduce llamadas a MT5
5. **Flexibilidad**: Funciona con cualquier broker compatible con MT5
6. **Escalabilidad**: Prefetch permite cargar múltiples símbolos eficientemente

## 🔄 Flujo de Trabajo

```
┌─────────────────┐
│  Bot necesita   │
│  calcular lote  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ SymbolSpecExtractor     │
│ .get_symbol_spec()      │
└────────┬────────────────┘
         │
         ▼
    ¿En caché?
    ┌───┴───┐
    │  SÍ   │           NO
    │       │            │
    ▼       │            ▼
Retornar    │    ┌──────────────┐
desde       │    │ MT5Connector │
caché       │    │.get_symbol   │
            │    │   _info()    │
            │    └──────┬───────┘
            │           │
            │           ▼
            │    ┌──────────────┐
            │    │  Validar     │
            │    │   datos      │
            │    └──────┬───────┘
            │           │
            │           ▼
            │    ┌──────────────┐
            │    │ Convertir a  │
            │    │SymbolSpec    │
            │    └──────┬───────┘
            │           │
            │           ▼
            │    ┌──────────────┐
            │    │  Guardar en  │
            │    │    caché     │
            │    └──────┬───────┘
            │           │
            └───────────┴────────┐
                        │
                        ▼
                ┌──────────────┐
                │  Retornar    │
                │SymbolSpec    │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ PositionSizer│
                │   calcula    │
                │     lote     │
                └──────────────┘
```

## 📖 Documentación de API

### SymbolSpecificationExtractor

#### `__init__(connector, logger=None, enable_cache=True)`
Inicializa el extractor.

**Parámetros:**
- `connector`: MT5Connector ya conectado
- `logger`: Logger opcional
- `enable_cache`: Habilitar caché (default: True)

#### `get_symbol_specification(symbol, use_cache=True) -> PositionSizerSpec`
Obtiene especificación completa de un símbolo.

**Parámetros:**
- `symbol`: Nombre del símbolo (ej: "EURUSD")
- `use_cache`: Usar caché si está disponible

**Returns:** `SymbolSpecification` para PositionSizer

**Raises:**
- `ValueError`: Si symbol está vacío
- `SymbolNotFoundError`: Si el símbolo no existe
- `SymbolSpecificationError`: Si hay error obteniendo datos

#### `get_lot_adjuster_specification(symbol, use_cache=True) -> LotAdjusterSpec`
Obtiene especificación para LotAdjuster.

**Returns:** `SymbolSpecification` para LotAdjuster (más ligero)

#### `clear_cache(symbol=None)`
Limpia caché de especificaciones.

**Parámetros:**
- `symbol`: Símbolo específico o None para limpiar todo

#### `is_cached(symbol) -> bool`
Verifica si un símbolo está en caché.

#### `get_cached_symbols() -> list`
Obtiene lista de símbolos en caché.

#### `prefetch_symbols(symbols) -> Dict[str, SymbolSpecification]`
Pre-carga especificaciones de múltiples símbolos.

**Parámetros:**
- `symbols`: Lista de nombres de símbolos

**Returns:** Diccionario {symbol: SymbolSpecification}

## 🔗 Archivos Modificados/Creados

### Nuevos Archivos
- ✅ `src/core/symbol_spec_extractor.py`
- ✅ `tests/unit/core/test_symbol_spec_extractor.py`
- ✅ `examples/symbol_spec_extractor_example.py`
- ✅ `context/DOCUMENTACION/T31_SYMBOL_SPEC_EXTRACTOR.md` (este archivo)

### Archivos Existentes (Sin cambios requeridos)
- `src/core/mt5_connector.py` - Ya tiene `get_symbol_info()`
- `src/core/position_sizer.py` - Compatible con la implementación
- `src/core/lot_adjuster.py` - Compatible con la implementación

## 🎓 Casos de Uso

### Caso 1: Bot Automático
```python
# Al inicio del ciclo, obtener especificaciones
specs = extractor.prefetch_symbols(["EURUSD", "GBPUSD", "XAUUSD"])

# Durante el ciclo, usar desde caché
for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]:
    spec = extractor.get_symbol_specification(symbol)
    # Calcular lote...
```

### Caso 2: Validación en Tiempo Real
```python
# Obtener especificación actualizada sin caché
spec = extractor.get_symbol_specification(
    "EURUSD",
    use_cache=False
)

# Validar lote antes de enviar orden
if adjuster.is_valid_lot(calculated_lot, spec):
    # Enviar orden...
```

### Caso 3: Análisis Multi-Broker
```python
# Comparar especificaciones entre brokers
pepperstone_spec = extractor1.get_symbol_specification("EURUSD")
icmarkets_spec = extractor2.get_symbol_specification("EURUSD")

print(f"Pepperstone Min: {pepperstone_spec.volume_min}")
print(f"ICMarkets Min: {icmarkets_spec.volume_min}")
```

## ✅ Verificación de Implementación

- [x] Módulo `SymbolSpecificationExtractor` creado
- [x] Tests unitarios implementados (17 tests)
- [x] Todos los tests pasan
- [x] Ejemplos de uso creados
- [x] Documentación completa
- [x] Validación de datos implementada
- [x] Sistema de caché funcional
- [x] Integración con PositionSizer verificada
- [x] Integración con LotAdjuster verificada
- [x] Manejo de errores robusto

## 🚧 Próximos Pasos

1. Crear PR para revisión
2. Fusionar a rama `desarrollo`
3. Actualizar otros módulos para usar el extractor
4. Documentar en README principal

## 📝 Notas Técnicas

- El caché usa diccionarios en memoria (no persistente)
- Las especificaciones no cambian frecuentemente, el caché es seguro
- Para trading en vivo, considerar refresh periódico de especificaciones
- El extractor es thread-safe para lectura, no para escritura concurrente

---

**Autor**: GitHub Copilot  
**Fecha de Implementación**: 2025-11-13  
**Versión**: 1.0  
**Estado**: ✅ Completado
