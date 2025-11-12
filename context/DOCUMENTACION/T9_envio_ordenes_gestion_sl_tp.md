# T09 - Envío de Órdenes y Gestión de SL/TP/Cierre

**Ticket:** #25  
**Fase:** 1  
**Prioridad:** P0 (Crítica)  
**Épica:** Integración MT5  
**Estado:** ✅ Completado  
**Fecha:** 2025-11-11

---

## 📋 Resumen

Implementación completa del módulo `OrderManager` que permite enviar órdenes Market y Limit a MetaTrader 5, modificar Stop Loss y Take Profit de posiciones abiertas, y cerrar posiciones de manera controlada.

Este módulo completa el ciclo de vida de las operaciones, complementando los tickets ya implementados:
- **T06**: Verificación de conexión MT5 
- **T07**: Extracción de velas OHLCV
- **T08**: Consulta de posiciones

---

## 🎯 Objetivos Cumplidos

### ✅ Funcionalidad Principal
1. **Envío de órdenes Market** (BUY/SELL) con ejecución inmediata
2. **Envío de órdenes Limit** (BUY_LIMIT/SELL_LIMIT) pendientes
3. **Modificación de SL/TP** en posiciones abiertas
4. **Cierre de posiciones** (total o parcial)
5. **Cierre masivo** por símbolo o Magic Number
6. **Validación exhaustiva** de parámetros
7. **Manejo robusto de errores** con excepciones específicas

### ✅ Calidad
- **32 tests unitarios** (100% passing)
- **86% de cobertura** de código
- **Logging detallado** de todas las operaciones
- **Documentación completa** con docstrings
- **Type hints** en todas las funciones

---

## 🏗️ Arquitectura

### Componentes Principales

```
OrderManager
├── Excepciones
│   ├── OrderManagerError (base)
│   ├── InvalidOrderParametersError
│   └── OrderExecutionError
│
├── Enums
│   └── OrderType (BUY, SELL, BUY_LIMIT, SELL_LIMIT)
│
├── Data Classes
│   ├── OrderRequest (solicitud de orden)
│   └── OrderResult (resultado de ejecución)
│
└── Métodos Principales
    ├── send_market_order()
    ├── send_limit_order()
    ├── modify_position()
    ├── close_position()
    └── close_all_positions()
```

### Diagrama de Flujo - Orden Market

```
┌─────────────────────┐
│ Crear OrderRequest  │
│  - symbol           │
│  - order_type       │
│  - volume           │
│  - price            │
│  - sl/tp            │
│  - magic            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Validar Parámetros  │
│  - volume > 0       │
│  - symbol no vacío  │
│  - price > 0        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Construir Request   │
│ MT5                 │
│  - TRADE_ACTION     │
│  - type             │
│  - filling          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Enviar a MT5        │
│ order_send()        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Validar Resultado   │
│  retcode == 10009?  │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
   Error       Éxito
     │           │
     ▼           ▼
┌─────────┐ ┌─────────┐
│  Raise  │ │ Return  │
│Exception│ │ Result  │
└─────────┘ └─────────┘
```

---

## 📦 Clases y Tipos

### OrderType (Enum)

```python
class OrderType(Enum):
    BUY = 0           # Compra inmediata (Market)
    SELL = 1          # Venta inmediata (Market)
    BUY_LIMIT = 2     # Compra pendiente a precio límite
    SELL_LIMIT = 3    # Venta pendiente a precio límite
    
    def is_market(self) -> bool:
        """True si es orden Market (BUY/SELL)"""
    
    def is_limit(self) -> bool:
        """True si es orden Limit (pendiente)"""
```

### OrderRequest (DataClass)

```python
@dataclass
class OrderRequest:
    symbol: str                          # "EURUSD", "GBPUSD", etc.
    order_type: OrderType                # BUY, SELL, BUY_LIMIT, SELL_LIMIT
    volume: float                        # Lotes (0.01, 0.1, 1.0, etc.)
    price: float                         # Precio de referencia/límite
    sl: float = 0.0                      # Stop Loss (0 = sin SL)
    tp: float = 0.0                      # Take Profit (0 = sin TP)
    magic: int = 0                       # Magic Number del bot
    comment: str = ""                    # Comentario de la orden
    deviation: int = 10                  # Desviación máxima (solo market)
    expiration: Optional[datetime] = None # Expiración (solo limit)
    
    def validate(self) -> None:
        """Valida todos los parámetros"""
```

### OrderResult (DataClass)

```python
@dataclass
class OrderResult:
    success: bool        # ¿Operación exitosa?
    retcode: int         # Código de retorno MT5
    order: int = 0       # Número de orden
    deal: int = 0        # Número de deal (si aplica)
    volume: float = 0.0  # Volumen ejecutado
    price: float = 0.0   # Precio de ejecución
    comment: str = ""    # Comentario del resultado
    request: Optional[Dict[str, Any]] = None  # Request original
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
```

---

## 🔧 Métodos Principales

### 1. send_market_order()

Envía una orden Market (BUY o SELL) con ejecución inmediata.

**Parámetros:**
- `request: OrderRequest` - Solicitud de orden con parámetros

**Retorna:**
- `OrderResult` - Resultado de la ejecución

**Excepciones:**
- `InvalidOrderParametersError` - Parámetros inválidos
- `OrderExecutionError` - Error en ejecución

**Ejemplo:**
```python
request = OrderRequest(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    volume=0.1,
    price=1.1000,
    sl=1.0950,
    tp=1.1100,
    magic=100001,
    comment="Bot 1 - Entry"
)

result = manager.send_market_order(request)
print(f"Orden ejecutada: {result.order}")
print(f"Deal: {result.deal}")
print(f"Precio: {result.price}")
```

---

### 2. send_limit_order()

Envía una orden Limit pendiente (BUY_LIMIT o SELL_LIMIT).

**Parámetros:**
- `request: OrderRequest` - Solicitud con precio límite

**Retorna:**
- `OrderResult` - Resultado del envío

**Excepciones:**
- `InvalidOrderParametersError` - Parámetros inválidos
- `OrderExecutionError` - Error en envío

**Ejemplo:**
```python
request = OrderRequest(
    symbol="EURUSD",
    order_type=OrderType.BUY_LIMIT,
    volume=0.1,
    price=1.0950,  # Precio límite
    sl=1.0900,
    tp=1.1050,
    magic=100002,
    expiration=datetime(2025, 12, 31, 23, 59, 59)
)

result = manager.send_limit_order(request)
print(f"Orden pendiente creada: {result.order}")
```

---

### 3. modify_position()

Modifica el Stop Loss y/o Take Profit de una posición abierta.

**Parámetros:**
- `ticket: int` - Número de ticket de la posición
- `sl: float = 0.0` - Nuevo SL (0 para no modificar)
- `tp: float = 0.0` - Nuevo TP (0 para no modificar)

**Retorna:**
- `OrderResult` - Resultado de la modificación

**Excepciones:**
- `ValueError` - Ticket inválido
- `InvalidOrderParametersError` - No se especifica SL ni TP
- `OrderExecutionError` - Error en modificación

**Ejemplo:**
```python
# Modificar solo SL
manager.modify_position(ticket=123456, sl=1.0960, tp=0.0)

# Modificar solo TP
manager.modify_position(ticket=123456, sl=0.0, tp=1.1120)

# Modificar ambos
manager.modify_position(ticket=123456, sl=1.0960, tp=1.1120)
```

---

### 4. close_position()

Cierra una posición abierta (total o parcialmente).

**Parámetros:**
- `ticket: int` - Ticket de la posición
- `volume: Optional[float] = None` - Volumen a cerrar (None = total)
- `deviation: int = 10` - Desviación máxima

**Retorna:**
- `OrderResult` - Resultado del cierre

**Excepciones:**
- `ValueError` - Ticket inválido
- `OrderExecutionError` - Posición no existe o error en cierre

**Ejemplo:**
```python
# Cerrar posición completa
result = manager.close_position(ticket=123456)

# Cerrar parcialmente (0.5 lotes de 1.0 total)
result = manager.close_position(ticket=123456, volume=0.5)

print(f"Posición cerrada - Deal: {result.deal}")
```

---

### 5. close_all_positions()

Cierra múltiples posiciones según filtros.

**Parámetros:**
- `symbol: Optional[str] = None` - Filtrar por símbolo
- `magic: Optional[int] = None` - Filtrar por Magic Number

**Retorna:**
- `List[OrderResult]` - Lista de resultados

**Ejemplo:**
```python
# Cerrar todas las posiciones de EURUSD
results = manager.close_all_positions(symbol="EURUSD")

# Cerrar todas las posiciones del bot 1 (magic 100001)
results = manager.close_all_positions(magic=100001)

# Cerrar todas las posiciones de EURUSD del bot 1
results = manager.close_all_positions(symbol="EURUSD", magic=100001)

print(f"Cerradas {len([r for r in results if r.success])} posiciones")
```

---

## 🔍 Validaciones Implementadas

### Validación de OrderRequest

```python
def validate(self) -> None:
    """
    Validaciones automáticas:
    ✓ Símbolo no vacío
    ✓ Volumen > 0
    ✓ Precio > 0
    ✓ SL >= 0
    ✓ TP >= 0
    ✓ Magic >= 0
    """
```

### Validación de Resultados

```python
# Todos los métodos validan:
✓ Resultado no es None
✓ retcode == TRADE_RETCODE_DONE (10009)
✓ Lanza OrderExecutionError si falla
```

---

## 📊 Códigos de Retorno MT5

Los códigos más comunes que maneja el módulo:

| Código | Constante | Significado |
|--------|-----------|-------------|
| 10009 | TRADE_RETCODE_DONE | ✅ Orden ejecutada exitosamente |
| 10004 | TRADE_RETCODE_REQUOTE | ❌ Requote (precio cambió) |
| 10006 | TRADE_RETCODE_REJECT | ❌ Orden rechazada |
| 10013 | TRADE_RETCODE_INVALID_PRICE | ❌ Precio inválido |
| 10015 | TRADE_RETCODE_INVALID_STOPS | ❌ SL/TP inválidos |
| 10018 | TRADE_RETCODE_MARKET_CLOSED | ❌ Mercado cerrado |
| 10019 | TRADE_RETCODE_NO_MONEY | ❌ Fondos insuficientes |

---

## 🧪 Testing

### Cobertura de Tests

**32 tests unitarios** que cubren:

1. **Inicialización** (3 tests)
   - Conexión válida
   - Sin conexión
   - Logger por defecto

2. **Órdenes Market** (8 tests)
   - BUY exitoso
   - SELL exitoso
   - Parámetros inválidos
   - Ejecución fallida
   - MT5 retorna None
   - Con desviación
   - Logging

3. **Órdenes Limit** (3 tests)
   - BUY_LIMIT exitoso
   - SELL_LIMIT exitoso
   - Con expiración

4. **Modificación SL/TP** (6 tests)
   - Modificar ambos
   - Solo SL
   - Solo TP
   - Ticket inválido
   - Sin cambios
   - Falla modificación

5. **Cierre de Posiciones** (6 tests)
   - Cierre exitoso
   - Posición no encontrada
   - Ticket inválido
   - Falla cierre
   - Volumen parcial
   - Logging

6. **Cierre Masivo** (2 tests)
   - Por símbolo
   - Por Magic Number

7. **Ciclos Completos** (2 tests)
   - Market: Abrir → Modificar → Cerrar
   - Limit: Abrir → Activación

8. **Validaciones** (2 tests)
   - OrderRequest
   - OrderType enum

### Ejecución de Tests

```bash
# Tests del módulo
pytest tests/unit/test_order_manager.py -v

# Con coverage
pytest tests/unit/test_order_manager.py --cov=src/core/order_manager --cov-report=html
```

**Resultado:**
- ✅ **32/32 tests passing (100%)**
- ✅ **86% de cobertura**

---

## 💡 Casos de Uso

### Caso 1: Bot Simple - Market Order

```python
from src.core.mt5_connector import MT5Connector, BrokerConfig
from src.core.order_manager import OrderManager, OrderRequest, OrderType

# Conectar a MT5
config = BrokerConfig(
    account_id="12345678",
    password="password",
    server="Pepperstone-Demo"
)

connector = MT5Connector(config)
connector.verify_connection()

# Crear manager
manager = OrderManager(connector)

# Enviar orden BUY
request = OrderRequest(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    volume=0.1,
    price=1.1000,
    sl=1.0950,
    tp=1.1100,
    magic=100001,
    comment="Bot Simple - Entry"
)

result = manager.send_market_order(request)
print(f"✅ Orden abierta: {result.order}")
```

### Caso 2: Dual Market/Limit

```python
# Abrir orden Market
market_request = OrderRequest(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    volume=0.1,
    price=1.1000,
    sl=1.0950,
    tp=1.1100,
    magic=100001,
    comment="Market order"
)

market_result = manager.send_market_order(market_request)

# Abrir orden Limit simultánea
limit_request = OrderRequest(
    symbol="EURUSD",
    order_type=OrderType.BUY_LIMIT,
    volume=0.1,
    price=1.0950,
    sl=1.0900,
    tp=1.1050,
    magic=100002,
    comment="Limit order"
)

limit_result = manager.send_limit_order(limit_request)

print(f"Market: {market_result.order}, Limit: {limit_result.order}")
```

### Caso 3: Reevaluación con Modificación de SL/TP

```python
# Posición ya existe con ticket=123456
# Actualizar SL a breakeven después de 10 pips de ganancia

current_price = 1.1010  # Precio actual
entry_price = 1.1000    # Precio de entrada

if current_price >= entry_price + 0.0010:  # +10 pips
    # Mover SL a breakeven
    manager.modify_position(
        ticket=123456,
        sl=entry_price,  # Breakeven
        tp=1.1100        # Mantener TP
    )
    print("✅ SL movido a breakeven")
```

### Caso 4: Cierre por Decisión de IA

```python
# La IA decide cerrar todas las posiciones de EURUSD
# porque detectó cambio de tendencia

results = manager.close_all_positions(
    symbol="EURUSD",
    magic=100001  # Solo del bot 1
)

exitosos = [r for r in results if r.success]
fallidos = [r for r in results if not r.success]

print(f"✅ Cerradas: {len(exitosos)}")
print(f"❌ Fallidas: {len(fallidos)}")
```

### Caso 5: Manejo de Errores

```python
from src.core.order_manager import (
    OrderExecutionError, 
    InvalidOrderParametersError
)

try:
    request = OrderRequest(
        symbol="EURUSD",
        order_type=OrderType.BUY,
        volume=0.1,
        price=1.1000,
        sl=1.0950,
        tp=1.1100,
        magic=100001
    )
    
    result = manager.send_market_order(request)
    print(f"✅ Orden: {result.order}")
    
except InvalidOrderParametersError as e:
    print(f"❌ Parámetros inválidos: {e}")
    
except OrderExecutionError as e:
    print(f"❌ Error en ejecución: {e}")
    # Reintentar o alertar
```

---

## 🔗 Integración con Otros Módulos

### Con MT5Connector (T06)

```python
# OrderManager requiere MT5Connector conectado
connector = MT5Connector(config)
connector.verify_connection()  # Requerido antes de OrderManager

manager = OrderManager(connector)
```

### Con PositionManager (T08)

```python
from src.core.position_manager import PositionManager

# Obtener posiciones del bot
position_mgr = PositionManager(connector)
positions = position_mgr.get_positions_by_magic(magic=100001)

# Cerrar todas las posiciones encontradas
for pos in positions:
    manager.close_position(ticket=pos.ticket)
```

### Con Logger (T39)

```python
from src.core.logger import setup_logger

# OrderManager acepta logger personalizado
logger = setup_logger(
    name="OrderManager",
    log_file="logs/orders.log",
    level="INFO"
)

manager = OrderManager(connector, logger=logger)
```

---

## 📈 Métricas de Calidad

| Métrica | Valor | Estado |
|---------|-------|--------|
| Tests Unitarios | 32 | ✅ 100% passing |
| Cobertura de Código | 86% | ✅ Excelente |
| Líneas de Código | 182 | ✅ Modular |
| Líneas de Tests | 750+ | ✅ Exhaustivo |
| Complejidad Ciclomática | Baja | ✅ Mantenible |
| Type Hints | 100% | ✅ Completo |
| Docstrings | 100% | ✅ Completo |

---

## 🚀 Próximos Pasos

Este módulo habilita los siguientes tickets:

1. **T17-T19**: Magic Numbers - Usar magic en órdenes ✅
2. **T14-T16**: Dual Market/Limit - Abrir pares simultáneos ✅
3. **T26-T28**: Reevaluación - Modificar SL/TP según IA ✅
4. **T10-T13**: IA Gemini - Recibir decisiones y ejecutarlas ⏳
5. **T29-T31**: Gestión de Riesgo - Calcular lotes y enviar ⏳

---

## 📝 Notas Técnicas

### Constantes MT5 Utilizadas

```python
# Actions
TRADE_ACTION_DEAL = 1      # Market order
TRADE_ACTION_PENDING = 5   # Pending order
TRADE_ACTION_SLTP = 2      # Modify SL/TP

# Order Types
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3

# Filling
ORDER_FILLING_IOC = 1  # Immediate or Cancel
ORDER_FILLING_FOK = 2  # Fill or Kill

# Time
ORDER_TIME_GTC = 0        # Good Till Cancel
ORDER_TIME_SPECIFIED = 1  # Until specified time
```

### Consideraciones de Broker

- **Desviación**: Algunos brokers requieren desviación (10 puntos default)
- **Filling Type**: IOC es el más compatible
- **Stops**: Validar distancia mínima de SL/TP según símbolo
- **Volumen**: Respetar step_volume del símbolo

---

## 🐛 Troubleshooting

### Error: "No hay conexión activa"
**Causa**: OrderManager se inicializa sin conexión  
**Solución**: Llamar `connector.verify_connection()` antes

### Error: "Invalid stops"
**Causa**: SL/TP muy cerca del precio actual  
**Solución**: Obtener stops_level del símbolo y respetar distancia mínima

### Error: "Market is closed"
**Causa**: Intentar operar fuera de horario  
**Solución**: Usar TimeValidator (T35) para validar horario

### Error: "No money"
**Causa**: Fondos insuficientes  
**Solución**: Reducir volumen o implementar cálculo de lote por % riesgo (T29)

---

## ✅ Criterios de Aceptación

Según el ticket #25:

> **Dado que** la IA indica operar con parámetros válidos  
> **Cuando** el bot envía órdenes Market o Limit y luego modifica SL/TP o cierra según decisión  
> **Entonces** las operaciones quedan reflejadas en MT5 con los parámetros confirmados

**Estado**: ✅ **CUMPLIDO**

- ✅ Envío de órdenes Market (BUY/SELL)
- ✅ Envío de órdenes Limit (BUY_LIMIT/SELL_LIMIT)
- ✅ Modificación de SL/TP
- ✅ Cierre de posiciones
- ✅ Validación de parámetros
- ✅ Confirmación de operaciones en MT5
- ✅ 32 tests unitarios (100% passing)
- ✅ 86% de cobertura

---

## 📚 Referencias

- **Issue GitHub**: #25
- **Código**: `src/core/order_manager.py`
- **Tests**: `tests/unit/test_order_manager.py`
- **Ejemplo**: `examples/order_manager_example.py`
- **Épica**: Integración MT5
- **Tickets Relacionados**: T06, T07, T08, T17-T19, T14-T16, T26-T28

---

**Documento generado**: 2025-11-11  
**Autor**: Sistema Botrading  
**Versión**: 1.0  
**Estado**: ✅ Completado
