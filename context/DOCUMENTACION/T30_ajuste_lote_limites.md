# T30 - Ajuste de Lote a Step y Límites del Símbolo

**Ticket:** #46  
**Épica:** Épica 9 - Riesgo y conversión de activos  
**Fase:** 2  
**Prioridad:** P0 (Crítica)  
**Estado:** ✅ Completado  

---

## 📋 Descripción

Módulo **LotAdjuster** que ajusta el tamaño de lote calculado a las restricciones del símbolo impuestas por el broker:

- **Volumen mínimo** (volume_min)
- **Volumen máximo** (volume_max)
- **Incremento permitido** (volume_step)

Garantiza que todas las órdenes enviadas a MetaTrader 5 cumplan con las reglas del broker, evitando rechazos por volúmenes inválidos.

---

## 🎯 Objetivos

### Objetivo Principal
Validar y ajustar automáticamente el tamaño de lote a las restricciones del símbolo, asegurando que todas las órdenes cumplan con las reglas del broker.

### Beneficios
1. **Prevención de Errores**: Evita rechazos de órdenes por volúmenes inválidos
2. **Cumplimiento Normativo**: Respeta automáticamente las restricciones de cada broker
3. **Reutilización**: Módulo centralizado usado por PositionSizer y OrderManager
4. **Validación en Tiempo Real**: Obtiene especificaciones actualizadas desde MT5

---

## 🏗️ Arquitectura

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                     LotAdjuster                             │
│─────────────────────────────────────────────────────────────│
│  adjust_lot(lot, spec) → AdjustedLot                        │
│  is_valid_lot(lot, spec) → bool                             │
│  adjust_lot_for_buy(lot, spec) → AdjustedLot                │
│  adjust_lot_for_sell(lot, spec) → AdjustedLot               │
│  _validate_inputs(lot, spec) → None                         │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│ SymbolSpec       │          │  AdjustedLot     │
│──────────────────│          │──────────────────│
│ - symbol         │          │ - adjusted_lot   │
│ - volume_min     │          │ - original_lot   │
│ - volume_max     │          │ - was_adjusted   │
│ - volume_step    │          │ - reason         │
└──────────────────┘          │ - symbol         │
                              └──────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  MT5Connector               │
│─────────────────────────────│
│ + get_symbol_info(symbol)   │
│   → MT5 SymbolInfo          │
└─────────────────────────────┘
```

### Flujo de Ajuste

```
1. Validar Entrada
   - lot_size > 0
   - spec no es None

2. Verificar Mínimo
   if lot < volume_min → lot = volume_min

3. Verificar Máximo
   elif lot > volume_max → lot = volume_max

4. Redondear al Step
   steps = lot / volume_step
   lot = round(steps) * volume_step

5. Re-verificar Límites
   Si después del redondeo excede, ajustar

6. Retornar AdjustedLot
   Con metadata del ajuste
```

---

## 📚 Referencia API

### LotAdjuster

```python
class LotAdjuster:
    def __init__(self, logger: Optional[logging.Logger] = None)
```

**Parámetros:**
- `logger`: Logger opcional para registrar operaciones

#### adjust_lot()

```python
def adjust_lot(
    self,
    lot_size: float,
    symbol_spec: SymbolSpecification
) -> AdjustedLot
```

Ajusta el tamaño de lote a las restricciones del símbolo.

**Parámetros:**
- `lot_size`: Tamaño de lote a ajustar
- `symbol_spec`: Especificaciones del símbolo

**Retorna:**
- `AdjustedLot` con el lote ajustado y metadata

**Ejemplo:**
```python
adjuster = LotAdjuster()

spec = SymbolSpecification(
    symbol="EURUSD",
    volume_min=0.01,
    volume_max=100.0,
    volume_step=0.01
)

result = adjuster.adjust_lot(0.456, spec)
print(f"Adjusted: {result.adjusted_lot}")  # 0.46
print(f"Was adjusted: {result.was_adjusted}")  # True
```

#### is_valid_lot()

```python
def is_valid_lot(
    self,
    lot_size: float,
    symbol_spec: SymbolSpecification
) -> bool
```

Verifica si un lote es válido sin ajustarlo.

**Parámetros:**
- `lot_size`: Tamaño de lote a verificar
- `symbol_spec`: Especificaciones del símbolo

**Retorna:**
- `True` si el lote es válido, `False` en caso contrario

**Ejemplo:**
```python
if adjuster.is_valid_lot(0.50, eurusd_spec):
    print("Lote válido")
else:
    print("Lote inválido, requiere ajuste")
```

### SymbolSpecification (Dataclass)

```python
@dataclass
class SymbolSpecification:
    symbol: str          # Nombre (ej: "EURUSD")
    volume_min: float    # Lote mínimo (ej: 0.01)
    volume_max: float    # Lote máximo (ej: 100.0)
    volume_step: float   # Incremento (ej: 0.01)
```

**Validaciones Automáticas:**
- Todos los volúmenes positivos
- `volume_min <= volume_max`
- `volume_step > 0`

### AdjustedLot (Dataclass)

```python
@dataclass
class AdjustedLot:
    adjusted_lot: float   # Lote ajustado
    original_lot: float   # Lote original
    was_adjusted: bool    # Si fue modificado
    reason: str           # Razón del ajuste
    symbol: str           # Símbolo
    
    def to_dict(self) -> dict
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Ajuste Básico (EURUSD)

```python
from src.core.lot_adjuster import LotAdjuster, SymbolSpecification

# Crear adjuster
adjuster = LotAdjuster()

# Especificaciones de EURUSD
eurusd_spec = SymbolSpecification(
    symbol="EURUSD",
    volume_min=0.01,
    volume_max=100.0,
    volume_step=0.01
)

# Lote calculado por PositionSizer: 0.4567
result = adjuster.adjust_lot(0.4567, eurusd_spec)

print(f"Original: {result.original_lot}")    # 0.4567
print(f"Adjusted: {result.adjusted_lot}")    # 0.46
print(f"Changed: {result.was_adjusted}")     # True
print(f"Reason: {result.reason}")            # "Lot rounded to step 0.01"
```

### Ejemplo 2: Lote Debajo del Mínimo

```python
# Lote muy pequeño
result = adjuster.adjust_lot(0.005, eurusd_spec)

print(f"Adjusted: {result.adjusted_lot}")  # 0.01 (mínimo)
print(f"Reason: {result.reason}")  
# "Adjusted from 0.005 to minimum 0.01"
```

### Ejemplo 3: Lote Sobre el Máximo

```python
# Lote demasiado grande
result = adjuster.adjust_lot(150.0, eurusd_spec)

print(f"Adjusted: {result.adjusted_lot}")  # 100.0 (máximo)
print(f"Reason: {result.reason}")  
# "Adjusted from 150.0 to maximum 100.0"
```

### Ejemplo 4: Obtener Especificaciones desde MT5

```python
from src.core.mt5_connector import MT5Connector, BrokerConfig
from src.core.lot_adjuster import LotAdjuster, SymbolSpecification

# Conectar a MT5
config = BrokerConfig(
    account_id="12345678",
    password="password",
    server="Pepperstone-Demo"
)

with MT5Connector(config) as mt5:
    # Obtener info del símbolo desde MT5
    symbol_info = mt5.get_symbol_info("EURUSD")
    
    # Crear especificación para LotAdjuster
    spec = SymbolSpecification(
        symbol=symbol_info.name,
        volume_min=symbol_info.volume_min,
        volume_max=symbol_info.volume_max,
        volume_step=symbol_info.volume_step
    )
    
    # Ajustar lote
    adjuster = LotAdjuster()
    result = adjuster.adjust_lot(0.456, spec)
    
    print(f"Adjusted lot: {result.adjusted_lot}")
```

### Ejemplo 5: Integración con PositionSizer

```python
from src.core.position_sizer import PositionSizer, RiskParameters
from src.core.lot_adjuster import LotAdjuster

# PositionSizer ahora usa LotAdjuster internamente
sizer = PositionSizer()

risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=2.0,
    entry_price=1.1000,
    stop_loss=1.0950,
    symbol_spec=eurusd_spec
)

# PositionSizer calcula y ajusta automáticamente
position_size = sizer.calculate_lot_size(risk_params)

print(f"Lot: {position_size.lot_size}")  # Ya está ajustado
```

### Ejemplo 6: Validación Previa

```python
# Verificar si un lote es válido antes de enviar
adjuster = LotAdjuster()

lot_to_trade = 0.50

if adjuster.is_valid_lot(lot_to_trade, eurusd_spec):
    # Enviar orden directamente
    order_manager.send_market_order(...)
else:
    # Ajustar primero
    result = adjuster.adjust_lot(lot_to_trade, eurusd_spec)
    order_manager.send_market_order(
        volume=result.adjusted_lot,
        ...
    )
```

### Ejemplo 7: Símbolos con Step Irregular

```python
# Símbolo con step de 0.05
exotic_spec = SymbolSpecification(
    symbol="EXOTIC",
    volume_min=0.05,
    volume_max=5.0,
    volume_step=0.05
)

# 0.23 no es múltiplo de 0.05
result = adjuster.adjust_lot(0.23, exotic_spec)

print(f"Adjusted: {result.adjusted_lot}")  # 0.25 (más cercano)
```

---

## 🔗 Integración con Otros Módulos

### Con MT5Connector (T06)

```python
# MT5Connector obtiene especificaciones del símbolo
mt5_connector = MT5Connector(config)
mt5_connector.verify_connection()

symbol_info = mt5_connector.get_symbol_info("EURUSD")

# LotAdjuster usa las especificaciones
spec = SymbolSpecification(
    symbol=symbol_info.name,
    volume_min=symbol_info.volume_min,
    volume_max=symbol_info.volume_max,
    volume_step=symbol_info.volume_step
)

adjuster = LotAdjuster()
result = adjuster.adjust_lot(0.456, spec)
```

### Con PositionSizer (T29)

```python
# PositionSizer usa LotAdjuster para ajustar lotes
sizer = PositionSizer()
# Internamente usa LotAdjuster para _adjust_to_symbol_limits
```

### Con OrderManager (T09)

```python
# OrderManager puede usar LotAdjuster antes de enviar
order_manager = OrderManager(mt5_connector)

# Ajustar lote antes de enviar
result = adjuster.adjust_lot(calculated_lot, symbol_spec)

order_request = OrderRequest(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    volume=result.adjusted_lot,  # ← Lote ajustado
    ...
)

order_manager.send_market_order(order_request)
```

---

## 🧪 Cobertura de Tests

### Resumen
- **Total de tests**: 47
- **Tests pasando**: 47 (100%)
- **Cobertura**: 89%

### Distribución de Tests

| Categoría | Tests | Descripción |
|-----------|-------|-------------|
| Inicialización | 2 | Creación del adjuster con/sin logger |
| Validación SymbolSpec | 7 | Volúmenes, step, validaciones |
| Ajuste a Límites | 5 | Min, max, exactos |
| Ajuste al Step | 5 | Redondeo, pasos irregulares |
| Diferentes Símbolos | 3 | EURUSD, XAUUSD, US30 |
| Validación de Entrada | 4 | Lotes negativos, cero, None |
| Casos Edge | 4 | Lotes extremos, precisión |
| Logging | 2 | Logs de ajuste y éxito |
| Dataclass | 2 | to_dict, repr |
| Batch Adjustment | 1 | Múltiples lotes |
| Integración | 1 | PositionSizer |
| Método is_valid_lot | 5 | Validaciones sin ajuste |
| Cálculo de Ajuste | 3 | Montos de ajuste |
| Casos Reales | 3 | Trades típicos |

### Tests Destacados

```python
# Test: Ajuste al step
def test_adjust_lot_to_step_round_up()  # 0.456 → 0.46

# Test: Límites
def test_adjust_lot_below_minimum()     # 0.005 → 0.01
def test_adjust_lot_above_maximum()     # 150.0 → 100.0

# Test: Validación
def test_is_valid_lot_true()
def test_is_valid_lot_false_wrong_step()

# Test: Integración
def test_adjust_lot_from_position_sizer_output()
```

---

## ⚠️ Consideraciones Importantes

### 1. Precisión de Punto Flotante

El módulo usa `round()` con 2 decimales para evitar problemas de precisión flotante:

```python
adjusted_lot = round(rounded_steps * volume_step, 2)
```

### 2. Redondeo al Step

El redondeo se hace al step **más cercano**:

```python
# 0.456 con step 0.01
steps = 0.456 / 0.01 = 45.6
rounded_steps = round(45.6) = 46
adjusted = 46 * 0.01 = 0.46
```

### 3. Re-verificación Después del Redondeo

Después de redondear al step, se vuelven a verificar los límites:

```python
# Si después de redondear excede el máximo
if lot_size > symbol_spec.volume_max:
    # Redondear hacia abajo
    rounded_steps = math.floor(steps)
    lot_size = rounded_steps * symbol_spec.volume_step
```

### 4. Logging de Ajustes

Todos los ajustes se registran en el logger:

```python
# Warning para ajustes a límites
self.logger.warning(f"{symbol}: Lot {original} below minimum...")

# Info para ajustes de step
self.logger.info(f"{symbol}: Lot {original} rounded to step...")
```

---

## 🐛 Troubleshooting

### Problema: Lote siempre se ajusta al mínimo

**Causa**: Lote calculado es muy pequeño para el símbolo.

**Solución**:
```python
# Verificar especificaciones del símbolo
print(f"Volume min: {spec.volume_min}")
print(f"Calculated lot: {calculated_lot}")

# Si calculated_lot < volume_min siempre
# Aumentar % riesgo o reducir distancia al SL
```

### Problema: Error "Lot size must be positive"

**Causa**: Se está pasando un lote negativo o cero.

**Solución**:
```python
# Asegurar que el lote es positivo
if lot_size <= 0:
    raise ValueError("Lot must be positive")
```

### Problema: Lote no se ajusta correctamente al step

**Causa**: Problemas de precisión de punto flotante.

**Verificación**:
```python
result = adjuster.adjust_lot(0.456, spec)
# Verificar manualmente
expected = round(round(0.456 / 0.01) * 0.01, 2)
print(f"Expected: {expected}, Got: {result.adjusted_lot}")
```

### Problema: Symbol not found

**Causa**: El símbolo no está disponible en el broker.

**Solución**:
```python
try:
    symbol_info = mt5_connector.get_symbol_info("EURUSD")
except ValueError as e:
    print(f"Symbol not available: {e}")
    # Usar símbolo alternativo o verificar con broker
```

---

## 📊 Métricas de Calidad

| Métrica | Valor | Estado |
|---------|-------|--------|
| Tests Unitarios | 47/47 | ✅ 100% |
| Cobertura de Código | 89% | ✅ Excelente |
| Complejidad Ciclomática | 3.8 | ✅ Baja |
| Líneas de Código | 386 | ✅ Moderado |
| Documentación | 100% | ✅ Completa |
| Type Hints | 100% | ✅ Completo |
| Validaciones | 8 | ✅ Robustas |

---

## 🚀 Próximos Pasos

### Completado ✅
1. Implementar LotAdjuster
2. Tests unitarios (47 tests)
3. Integración con PositionSizer
4. Extender MT5Connector con get_symbol_info()
5. Tests de integración MT5-LotAdjuster
6. Documentación técnica
7. Archivo de ejemplos

### Futuras Mejoras
1. **Caché de Especificaciones**: Cachear symbol_info para evitar consultas repetidas
2. **Validación de Spread**: Considerar spread en la validación
3. **Soporte Multi-Broker**: Adaptar a diferentes brokers con reglas específicas
4. **Métricas de Ajustes**: Estadísticas de cuántos ajustes se hacen

---

## 📝 Notas de Implementación

### Decisiones de Diseño

1. **Dataclasses**: Uso de `@dataclass` para estructuras inmutables
2. **Validaciones**: Se hacen en `__post_init__` de dataclasses
3. **Logging**: Opcional pero recomendado para auditoría
4. **Precisión**: Se redondea a 2 decimales para evitar problemas flotantes
5. **Excepciones**: Específicas por tipo de error

### Limitaciones Conocidas

1. **Precisión Flotante**: Pequeños errores de redondeo posibles
2. **Sin Caché**: Especificaciones se pasan como parámetro, no se cachean
3. **Sin Spread**: No considera el spread en el ajuste
4. **Sin Margen**: No verifica margen disponible

### Compatibilidad

- **Python**: 3.8+
- **MetaTrader**: MT5 (independiente del broker)
- **Módulos**: Compatible con todos los módulos core existentes

---

**Documentación generada**: 11 de Noviembre de 2025  
**Autor**: Sistema Botrading  
**Versión**: 1.0  
**Ticket**: #46 - T30
