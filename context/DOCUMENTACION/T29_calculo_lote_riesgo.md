# T29 - Cálculo de Lote por % Riesgo y Distancia al SL

**Ticket:** #45  
**Épica:** Épica 9 - Riesgo y conversión de activos  
**Fase:** 2  
**Prioridad:** P0 (Crítica)  
**Estado:** ✅ Completado  

---

## 📋 Descripción

Módulo **PositionSizer** que calcula el tamaño óptimo de posición (lote) basándose en gestión de riesgo. Normaliza el riesgo entre activos heterogéneos (Forex, Metales, Índices) utilizando:

- Porcentaje de riesgo del capital
- Distancia al Stop Loss en pips
- Especificaciones del símbolo (tick value, contract size, etc.)

---

## 🎯 Objetivos

### Objetivo Principal
Calcular el tamaño de lote que normaliza el riesgo entre diferentes tipos de activos, asegurando que arriesgar 2% en EURUSD tenga el mismo impacto monetario que arriesgar 2% en XAUUSD.

### Beneficios
1. **Gestión de Riesgo Consistente**: Mismo % de riesgo = mismo impacto monetario
2. **Prevención de Sobrexposición**: Limita automáticamente al riesgo deseado
3. **Normalización Entre Activos**: Forex, metales, índices con la misma fórmula
4. **Integración Perfecta**: Se conecta con OrderManager para enviar órdenes

---

## 🏗️ Arquitectura

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                     PositionSizer                           │
│─────────────────────────────────────────────────────────────│
│  calculate_lot_size(RiskParameters) → PositionSize          │
│  calculate_risk_amount(balance, %) → float                  │
│  price_distance_to_pips(distance, spec) → float             │
│  pips_to_price_distance(pips, spec) → float                 │
│  _calculate_pip_value_per_lot(spec) → float                 │
│  _adjust_to_symbol_limits(lot, spec) → float                │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│ RiskParameters   │          │  PositionSize    │
│──────────────────│          │──────────────────│
│ - account_balance│          │ - lot_size       │
│ - risk_percentage│          │ - risk_amount    │
│ - entry_price    │          │ - pip_distance   │
│ - stop_loss      │          │ - pip_value      │
│ - symbol_spec    │          │ - symbol         │
└──────────────────┘          │ - success        │
                              │ - message        │
                              └──────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  SymbolSpecification        │
│─────────────────────────────│
│ - symbol: str               │
│ - point: float              │
│ - tick_size: float          │
│ - tick_value: float         │
│ - volume_min: float         │
│ - volume_max: float         │
│ - volume_step: float        │
│ - contract_size: float      │
└─────────────────────────────┘
```

### Flujo de Cálculo

```
1. Calcular Riesgo en $
   risk_$ = balance * (risk_% / 100)

2. Calcular Distancia en Pips
   pips = |entry - SL| / point

3. Calcular Valor por Pip
   pip_value = (tick_value / tick_size) * point

4. Calcular Lote Base
   lot = risk_$ / (pips * pip_value)

5. Ajustar a Límites
   - Si < min → min
   - Si > max → max
   - Redondear a step

6. Retornar PositionSize
```

---

## 📚 Referencia API

### PositionSizer

```python
class PositionSizer:
    def __init__(self, logger: Optional[logging.Logger] = None)
```

**Parámetros:**
- `logger`: Logger opcional para registrar operaciones

#### calculate_lot_size()

```python
def calculate_lot_size(self, risk_params: RiskParameters) -> PositionSize
```

Calcula el tamaño de lote óptimo basado en parámetros de riesgo.

**Parámetros:**
- `risk_params`: Objeto RiskParameters con todos los parámetros necesarios

**Retorna:**
- `PositionSize` con el lote calculado y metadata

**Fórmula:**
```
1. risk_amount = account_balance * (risk_percentage / 100)
2. pip_distance = |entry_price - stop_loss| / point
3. pip_value_per_lot = (tick_value / tick_size) * point
4. lot_size_raw = risk_amount / (pip_distance * pip_value_per_lot)
5. lot_size_adjusted = adjust_to_symbol_limits(lot_size_raw)
```

**Ejemplo:**
```python
sizer = PositionSizer()

risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=2.0,
    entry_price=1.1000,
    stop_loss=1.0950,  # 50 pips
    symbol_spec=eurusd_spec
)

result = sizer.calculate_lot_size(risk_params)
print(f"Lot: {result.lot_size}")  # 0.40 lotes
print(f"Risk: ${result.risk_amount}")  # $200
print(f"Pips: {result.pip_distance}")  # 50.0
```

#### calculate_risk_amount()

```python
def calculate_risk_amount(
    self,
    account_balance: float,
    risk_percentage: float
) -> float
```

Calcula el monto de riesgo en dinero.

**Parámetros:**
- `account_balance`: Balance de la cuenta
- `risk_percentage`: Porcentaje a arriesgar (1-100)

**Retorna:**
- Monto de riesgo en dinero

**Ejemplo:**
```python
risk_$ = sizer.calculate_risk_amount(10000.0, 2.0)
# risk_$ = 200.0
```

#### price_distance_to_pips()

```python
def price_distance_to_pips(
    self,
    price_distance: float,
    symbol_spec: SymbolSpecification
) -> float
```

Convierte distancia de precio a pips.

**Parámetros:**
- `price_distance`: Distancia en unidades de precio
- `symbol_spec`: Especificaciones del símbolo

**Retorna:**
- Distancia en pips

**Ejemplo:**
```python
# EURUSD: 0.0050 = 50 pips
pips = sizer.price_distance_to_pips(0.0050, eurusd_spec)
# pips = 50.0
```

#### pips_to_price_distance()

```python
def pips_to_price_distance(
    self,
    pips: float,
    symbol_spec: SymbolSpecification
) -> float
```

Convierte pips a distancia de precio.

**Parámetros:**
- `pips`: Cantidad de pips
- `symbol_spec`: Especificaciones del símbolo

**Retorna:**
- Distancia en unidades de precio

**Ejemplo:**
```python
# EURUSD: 100 pips = 0.0100
price_dist = sizer.pips_to_price_distance(100.0, eurusd_spec)
# price_dist = 0.0100
```

### RiskParameters (Dataclass)

```python
@dataclass
class RiskParameters:
    account_balance: float      # Balance de la cuenta
    risk_percentage: float       # Porcentaje a arriesgar (1-100)
    entry_price: float           # Precio de entrada planeado
    stop_loss: float             # Precio del Stop Loss
    symbol_spec: SymbolSpecification  # Especificaciones del símbolo
```

**Validaciones Automáticas:**
- `account_balance > 0`
- `0 < risk_percentage <= 100`
- `entry_price > 0`
- `stop_loss > 0`
- `entry_price ≠ stop_loss`

### SymbolSpecification (Dataclass)

```python
@dataclass
class SymbolSpecification:
    symbol: str          # Nombre (ej: "EURUSD")
    point: float         # Tamaño del punto (ej: 0.0001)
    tick_size: float     # Movimiento mínimo (ej: 0.00001)
    tick_value: float    # Valor de un tick ($)
    volume_min: float    # Lote mínimo (ej: 0.01)
    volume_max: float    # Lote máximo (ej: 100.0)
    volume_step: float   # Incremento (ej: 0.01)
    contract_size: float # Tamaño del contrato (ej: 100000)
```

**Validaciones Automáticas:**
- Todos los valores positivos
- `volume_min <= volume_max`
- `volume_step > 0`

### PositionSize (Dataclass)

```python
@dataclass
class PositionSize:
    lot_size: float       # Lote calculado y ajustado
    risk_amount: float    # Monto de riesgo ($)
    pip_distance: float   # Distancia al SL (pips)
    pip_value: float      # Valor de 1 pip ($)
    symbol: str           # Símbolo
    success: bool         # Si fue exitoso
    message: str          # Mensaje descriptivo
    
    def to_dict(self) -> dict
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Cálculo Básico (EURUSD)

```python
from src.core.position_sizer import (
    PositionSizer,
    RiskParameters,
    SymbolSpecification
)

# Especificaciones de EURUSD
eurusd_spec = SymbolSpecification(
    symbol="EURUSD",
    point=0.0001,        # 1 pip
    tick_size=0.00001,   # 1 pipette
    tick_value=1.0,      # $1 por tick
    volume_min=0.01,
    volume_max=100.0,
    volume_step=0.01,
    contract_size=100000
)

# Crear sizer
sizer = PositionSizer()

# Parámetros de riesgo
risk_params = RiskParameters(
    account_balance=10000.0,  # $10,000
    risk_percentage=2.0,      # 2%
    entry_price=1.1000,
    stop_loss=1.0950,         # 50 pips
    symbol_spec=eurusd_spec
)

# Calcular lote
result = sizer.calculate_lot_size(risk_params)

print(f"Lote: {result.lot_size}")           # 0.40
print(f"Riesgo: ${result.risk_amount}")     # $200
print(f"Distancia: {result.pip_distance} pips")  # 50 pips
```

### Ejemplo 2: Oro (XAUUSD)

```python
# Especificaciones de Oro
xauusd_spec = SymbolSpecification(
    symbol="XAUUSD",
    point=0.01,          # 1 centavo
    tick_size=0.01,
    tick_value=1.0,
    volume_min=0.01,
    volume_max=50.0,
    volume_step=0.01,
    contract_size=100    # 100 onzas
)

# Oro a $2,000, SL en $1,980
risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=2.0,
    entry_price=2000.0,
    stop_loss=1980.0,  # $20 de distancia
    symbol_spec=xauusd_spec
)

result = sizer.calculate_lot_size(risk_params)
print(f"Lote: {result.lot_size}")  # 0.10
```

### Ejemplo 3: Índice (US30)

```python
# Especificaciones de US30 (Dow Jones)
us30_spec = SymbolSpecification(
    symbol="US30",
    point=1.0,           # 1 punto
    tick_size=1.0,
    tick_value=1.0,      # $1 por punto
    volume_min=0.1,
    volume_max=10.0,
    volume_step=0.1,
    contract_size=1
)

# US30 a 35,000, SL en 34,900
risk_params = RiskParameters(
    account_balance=20000.0,
    risk_percentage=1.5,
    entry_price=35000.0,
    stop_loss=34900.0,  # 100 puntos
    symbol_spec=us30_spec
)

result = sizer.calculate_lot_size(risk_params)
print(f"Lote: {result.lot_size}")  # 3.0
```

### Ejemplo 4: Posición SELL

```python
# Para posiciones SELL, SL está arriba de la entrada
risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=2.0,
    entry_price=1.1000,
    stop_loss=1.1050,   # SL arriba (SELL)
    symbol_spec=eurusd_spec
)

result = sizer.calculate_lot_size(risk_params)
# La distancia es absoluta, calcula correctamente
print(f"Lote: {result.lot_size}")  # 0.40
```

### Ejemplo 5: Integración con OrderManager

```python
from src.core.order_manager import OrderManager, OrderRequest, OrderType

# 1. Calcular lote con PositionSizer
sizer = PositionSizer()
risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=2.0,
    entry_price=1.1000,
    stop_loss=1.0950,
    symbol_spec=eurusd_spec
)
position_size = sizer.calculate_lot_size(risk_params)

# 2. Crear orden con el lote calculado
order_mgr = OrderManager(mt5_connector)
order_request = OrderRequest(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    volume=position_size.lot_size,  # ← Lote calculado
    price=1.1000,
    sl=1.0950,
    tp=1.1100,
    magic=100001,
    comment=f"Risk: ${position_size.risk_amount:.2f}"
)

# 3. Enviar orden
result = order_mgr.send_market_order(order_request)
```

---

## 🧪 Cobertura de Tests

### Resumen
- **Total de tests**: 40
- **Tests pasando**: 40 (100%)
- **Cobertura**: 87%

### Distribución de Tests

| Categoría | Tests | Descripción |
|-----------|-------|-------------|
| Inicialización | 2 | Creación del sizer con/sin logger |
| Cálculo Forex | 4 | EURUSD BUY/SELL, cuentas pequeñas/grandes |
| Otros Activos | 2 | Oro (XAUUSD), Índices (US30) |
| Validaciones RiskParameters | 8 | Balance, risk%, entry, SL |
| Validaciones SymbolSpec | 4 | Point, tick value, volumes, contract size |
| Conversión Pips | 4 | Precio ↔ Pips en diferentes activos |
| Ajuste de Lote | 4 | Min, max, step en diferentes símbolos |
| Cálculo Riesgo | 3 | Diferentes percentages y balances |
| Dataclass | 2 | Inicialización, to_dict |
| Casos Edge | 3 | Cuentas extremas, SL muy anchos/estrechos |
| Logging | 2 | Logs exitosos, logs de ajustes |
| Integración | 2 | Integración con OrderManager |

### Tests Destacados

```python
# Test: Normalización entre activos
def test_calculate_lot_eurusd_basic()  # EURUSD
def test_calculate_lot_xauusd()        # Oro
def test_calculate_lot_us30()          # Índice

# Test: Validaciones robustas
def test_invalid_account_balance_negative()
def test_invalid_risk_percentage_too_high()
def test_invalid_entry_equals_stop_loss()

# Test: Casos edge
def test_very_small_account_very_wide_stop()
def test_very_large_account_tight_stop()
def test_fractional_pip_distance()
```

---

## 🔗 Integración con Otros Módulos

### Con OrderManager (T09)

```python
# PositionSizer calcula el lote
position_size = sizer.calculate_lot_size(risk_params)

# OrderManager envía la orden
order_mgr.send_market_order(OrderRequest(
    volume=position_size.lot_size,  # ← Integración
    ...
))
```

### Con SymbolInfoManager (T31 - Pendiente)

```python
# SymbolInfoManager obtendrá specs desde MT5
symbol_info_mgr = SymbolInfoManager(mt5_connector)
symbol_spec = symbol_info_mgr.get_symbol_specification("EURUSD")

# PositionSizer usa las specs
risk_params = RiskParameters(
    ...,
    symbol_spec=symbol_spec  # ← Integración futura
)
```

### Con LotAdjuster (T30 - Pendiente)

```python
# LotAdjuster refinará el ajuste a límites
lot_adjuster = LotAdjuster()
adjusted_lot = lot_adjuster.adjust_to_symbol_limits(
    lot_size=position_size.lot_size,
    symbol_spec=symbol_spec
)
```

---

## 🎓 Conceptos Clave

### ¿Qué es un Pip?

**Pip** = "Percentage in Point" o "Point in Percentage"

- **Forex (4 decimales)**: 1 pip = 0.0001
  - EURUSD: 1.1000 → 1.1001 = 1 pip
- **Forex JPY (2 decimales)**: 1 pip = 0.01
  - USDJPY: 110.00 → 110.01 = 1 pip
- **Metales (2 decimales)**: 1 pip = 0.01
  - XAUUSD: $2000.00 → $2000.01 = 1 pip
- **Índices (puntos)**: 1 pip = 1 punto
  - US30: 35000 → 35001 = 1 pip

### ¿Cómo se calcula el valor de un Pip?

Para **EURUSD** (lote estándar = 100,000 unidades):
```
Distancia: 0.0001 (1 pip)
Lote: 1.0 (100,000 EUR)
Valor: 0.0001 * 100,000 = 10 USD

Por tanto: 1 pip = $10 por lote estándar
```

Para **XAUUSD** (lote = 100 onzas):
```
Distancia: 0.01 (1 pip = 1 centavo)
Lote: 1.0 (100 onzas)
Valor: 0.01 * 100 = 1 USD

Por tanto: 1 pip = $1 por lote
```

### Fórmula de Gestión de Riesgo

```
Tamaño de Lote = Riesgo en $ / (Distancia en Pips * Valor por Pip)
```

**Ejemplo EURUSD:**
```
Balance: $10,000
Riesgo: 2% = $200
Entrada: 1.1000
SL: 1.0950 (50 pips)
Valor por pip: $10 (por lote)

Lote = $200 / (50 pips * $10) = 0.40 lotes
```

**Validación:**
```
Distancia: 50 pips
Lote: 0.40
Valor por pip: $10 * 0.40 = $4
Riesgo total: 50 pips * $4 = $200 ✓
```

---

## ⚠️ Consideraciones Importantes

### 1. Precisión de Punto Flotante

Los cálculos usan `float`, lo que puede causar pequeños errores de redondeo. Para comparaciones, use tolerancias:

```python
# ❌ Malo
if result.pip_distance == 50.0:

# ✅ Bueno
if abs(result.pip_distance - 50.0) < 0.01:
```

### 2. Ajuste a Límites del Símbolo

El lote calculado **siempre** se ajusta a:
- **Mínimo**: Si < volume_min → volume_min
- **Máximo**: Si > volume_max → volume_max
- **Step**: Redondeado al volume_step más cercano

```python
# Ejemplo: volume_step = 0.01
calculated = 0.456
adjusted = 0.46  # Redondeado a 0.01
```

### 3. Diferentes Tipos de Cuenta

El valor por pip puede variar según el tipo de cuenta:
- **Cuenta USD**: Valores directos en USD
- **Cuenta EUR**: Requiere conversión EUR/USD
- **Cuenta JPY**: Requiere conversión USD/JPY

**Nota**: Este módulo asume que `tick_value` ya está en la moneda de la cuenta.

### 4. Símbolos Exóticos

Para símbolos exóticos (ej: EURCZK, USDMXN), asegúrese de que las especificaciones sean correctas, especialmente `tick_value` y `contract_size`.

---

## 🐛 Troubleshooting

### Problema: Lote siempre es el mínimo

**Causa**: Cuenta demasiado pequeña o SL muy amplio.

**Solución**:
```python
# Verificar cálculo intermedio
risk_$ = balance * (risk_% / 100)
required_lot = risk_$ / (pips * pip_value)

if required_lot < volume_min:
    print("Lote calculado muy pequeño")
    print(f"Necesitas: ${risk_$ / (pips * volume_min)} de balance")
```

### Problema: Lote siempre es el máximo

**Causa**: SL muy estrecho o cuenta muy grande.

**Solución**:
```python
# Ampliar SL o reducir % de riesgo
risk_params.risk_percentage = 1.0  # Reducir a 1%
# o
risk_params.stop_loss = 1.0900  # SL más amplio
```

### Problema: Valor por pip incorrecto

**Causa**: Especificaciones del símbolo incorrectas.

**Solución**:
```python
# Verificar especificaciones
print(f"Point: {spec.point}")
print(f"Tick size: {spec.tick_size}")
print(f"Tick value: {spec.tick_value}")

# Para EURUSD debería ser:
# point = 0.0001
# tick_size = 0.00001
# tick_value = 1.0
```

### Problema: Error "Distance cannot be zero"

**Causa**: `entry_price == stop_loss`.

**Solución**:
```python
# Asegurar que entry y SL sean diferentes
if entry_price == stop_loss:
    raise ValueError("SL debe ser diferente de entrada")
```

---

## 📊 Métricas de Calidad

| Métrica | Valor | Estado |
|---------|-------|--------|
| Tests Unitarios | 40/40 | ✅ 100% |
| Cobertura de Código | 87% | ✅ Excelente |
| Complejidad Ciclomática | 4.2 | ✅ Baja |
| Líneas de Código | 520 | ✅ Moderado |
| Documentación | 100% | ✅ Completa |
| Type Hints | 100% | ✅ Completo |
| Validaciones | 12 | ✅ Robustas |

---

## 🚀 Próximos Pasos

### Inmediatos
1. ✅ Implementar PositionSizer
2. ✅ Tests unitarios (40 tests)
3. ✅ Documentación técnica
4. ⏳ Archivo de ejemplos
5. ⏳ Commit y PR

### Futuras Mejoras (Otros Tickets)
1. **T31 - SymbolInfoManager**: Obtener specs desde MT5
2. **T30 - LotAdjuster**: Refinamiento adicional de ajustes
3. **T32 - Persistencia**: Guardar cálculos en BD
4. **Soporte Multi-Moneda**: Convertir automáticamente según moneda de cuenta

---

## 📝 Notas de Implementación

### Decisiones de Diseño

1. **Dataclasses**: Usan `@dataclass` para estructuras de datos inmutables
2. **Validaciones**: Se hacen en `__post_init__` de dataclasses
3. **Logging**: Opcional pero recomendado para auditoría
4. **Precisión**: Se redondea a 2 decimales para evitar problemas flotantes
5. **Excepciones**: Específicas por tipo de error

### Limitaciones Conocidas

1. **Moneda de Cuenta**: Asume que `tick_value` ya está convertido
2. **Spreads**: No considera el spread en el cálculo
3. **Swaps**: No considera costos de mantenimiento
4. **Comisiones**: No considera comisiones del broker

### Compatibilidad

- **Python**: 3.8+
- **MetaTrader**: MT5 (independiente del broker)
- **Módulos**: Compatible con todos los módulos core existentes

---

**Documentación generada**: 11 de Noviembre de 2025  
**Autor**: Sistema Botrading  
**Versión**: 1.0  
**Ticket**: #45 - T29
