# 📅 Guía de Trading con Futuros

## 📋 Índice
1. [Estado de Implementación](#estado-de-implementación)
2. [Características de Futuros](#características-de-futuros)
3. [Tipos de Futuros](#tipos-de-futuros)
4. [Especificaciones Técnicas](#especificaciones-técnicas)
5. [Consideraciones de Riesgo](#consideraciones-de-riesgo)
6. [Implementación Requerida](#implementación-requerida)

---

## ❌ Estado de Implementación

**Estado Actual**: NO Implementado

### ✅ Lo que YA funciona en el sistema:
- Sistema genérico de cálculo de lotes (PositionSizer)
- Extracción automática de especificaciones desde MT5
- Soporte para contract_size variable
- Manejo de diferentes tick_size y tick_value

### ❌ Lo que FALTA implementar:
- Configuración específica para contratos futuros
- Manejo de expiración de contratos
- Ajustes por leverage
- Cálculos de margen de mantenimiento
- Roll-over automático de contratos

---

## 📅 Características de Futuros

### Aspectos Generales
- **Apalancamiento**: Alto (típicamente 5:1 a 100:1)
- **Expiración**: Contratos con fecha de vencimiento
- **Liquidez**: Muy alta en contratos principales
- **Horarios**: Sesiones extendidas
- **Costos**: Comisiones más bajas que spot

### Diferencias con Spot Trading
| Aspecto | Spot Trading | Futuros |
|---------|--------------|---------|
| Posesión | Sí | No (contrato) |
| Expiración | No | Sí |
| Apalancamiento | Bajo | Alto |
| Margen | No requerido | Sí requerido |
| Comisiones | Variables | Fijas |

---

## 📊 Tipos de Futuros

### 1. Futuros de Índices
- **Ejemplos**: ES (E-mini S&P 500), NQ (Nasdaq 100)
- **Contract Size**: Variable (ej: $50 × índice para ES)
- **Tick Size**: 0.25 puntos
- **Volatilidad**: Alta

### 2. Futuros de Commodities
- **Ejemplos**: GC (Gold), CL (Crude Oil)
- **Contract Size**: Fijo por commodity
- **Tick Size**: Variable por commodity
- **Volatilidad**: Muy alta

### 3. Futuros de Divisas
- **Ejemplos**: 6E (Euro FX), 6J (Japanese Yen)
- **Contract Size**: 125,000 unidades
- **Tick Size**: Variable
- **Volatilidad**: Media-Alta

---

## 🔧 Especificaciones Técnicas

### Ejemplos de Configuración

#### ES (E-mini S&P 500)
```python
SymbolSpecification(
    symbol="ES",
    point=0.25,           # Tick size = 0.25 puntos
    tick_size=0.25,
    tick_value=12.5,      # $12.50 por tick ($50 × 0.25)
    volume_min=1,         # 1 contrato mínimo
    volume_max=100,       # 100 contratos máximo
    volume_step=1,
    contract_size=50      # $50 × valor del índice
)
```

#### GC (Gold Futures)
```python
SymbolSpecification(
    symbol="GC",
    point=0.1,            # 0.1 USD por tick
    tick_size=0.1,
    tick_value=10.0,      # $10 por tick (100 oz × $0.10)
    volume_min=1,
    volume_max=50,
    volume_step=1,
    contract_size=100     # 100 onzas de oro
)
```

#### 6E (Euro FX Futures)
```python
SymbolSpecification(
    symbol="6E",
    point=0.00005,        # 0.5 pips
    tick_size=0.00005,
    tick_value=6.25,      # $6.25 por tick
    volume_min=1,
    volume_max=200,
    volume_step=1,
    contract_size=125000  # 125,000 EUR
)
```

### Cálculo de Lotes con Apalancamiento

```python
def calculate_futures_lot_size(
    account_balance: float,
    risk_percentage: float,
    entry_price: float,
    stop_loss: float,
    symbol_spec: SymbolSpecification,
    leverage: float = 1.0
) -> float:
    """
    Cálculo de lote para futuros considerando leverage

    Args:
        leverage: Factor de apalancamiento (ej: 5.0 = 5:1)
    """
    # Riesgo efectivo considerando leverage
    effective_balance = account_balance * leverage

    # Cálculo estándar con balance efectivo
    risk_amount = effective_balance * (risk_percentage / 100)
    price_distance = abs(entry_price - stop_loss)
    pip_distance = price_distance / symbol_spec.point

    # Para futuros, tick_value ya incluye el contract_size
    pip_value = symbol_spec.tick_value

    lot_size = risk_amount / (pip_distance * pip_value)

    return lot_size
```

---

## ⚠️ Consideraciones de Riesgo

### Apalancamiento Alto
- **Ventaja**: Amplifica ganancias potenciales
- **Riesgo**: Amplifica pérdidas potenciales
- **Recomendación**: Usar leverage máximo 5:1 inicialmente

### Margen de Mantenimiento
- **Initial Margin**: Margen requerido para abrir posición
- **Maintenance Margin**: Nivel mínimo para mantener posición
- **Margin Call**: Liquidación forzada si equity < maintenance margin

### Expiración de Contratos
- **Roll-over**: Cambio a próximo contrato antes de expiración
- **Timing**: Típicamente 1-2 semanas antes de expiración
- **Costos**: Spread entre contratos puede afectar P&L

### Liquidez y Slippage
- **Horarios**: Mejor liquidez durante sesiones regulares
- **Volumen**: Contratos principales tienen mejor liquidez
- **Slippage**: Común en órdenes grandes

---

## 🚧 Implementación Requerida

### 1. Clase FuturesSymbolManager

```python
class FuturesSymbolManager:
    """Gestor específico para símbolos de futuros"""

    def __init__(self, mt5_connector):
        self.connector = mt5_connector
        self.contract_expirations = {}

    def get_futures_spec(self, symbol: str) -> SymbolSpecification:
        """Obtener especificaciones con ajustes para futuros"""
        base_spec = self.connector.get_symbol_info(symbol)

        # Ajustes específicos para futuros
        if self._is_index_future(symbol):
            return self._adjust_index_future_spec(base_spec)
        elif self._is_commodity_future(symbol):
            return self._adjust_commodity_future_spec(base_spec)
        elif self._is_currency_future(symbol):
            return self._adjust_currency_future_spec(base_spec)

    def check_expiration(self, symbol: str) -> dict:
        """Verificar expiración del contrato"""
        # Lógica para obtener fecha de expiración
        # Alertas cuando se acerca la expiración
        pass

    def calculate_rollover_cost(self, symbol: str) -> float:
        """Calcular costo de roll-over entre contratos"""
        # Diferencia entre precio actual y próximo contrato
        pass
```

### 2. FuturesPositionSizer

```python
class FuturesPositionSizer(PositionSizer):
    """PositionSizer especializado para futuros"""

    def __init__(self, *args, leverage: float = 1.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.leverage = leverage

    def calculate_lot_size(self, risk_params: RiskParameters) -> PositionSize:
        """Cálculo considerando leverage y margen"""
        # Ajustar balance efectivo por leverage
        effective_balance = risk_params.account_balance * self.leverage

        # Verificar margen requerido
        margin_required = self._calculate_margin_required(
            risk_params.symbol_spec, effective_balance
        )

        if effective_balance < margin_required:
            raise InsufficientMarginError(
                f"Insufficient margin. Required: ${margin_required}, "
                f"Available: ${effective_balance}"
            )

        # Proceder con cálculo estándar
        adjusted_params = RiskParameters(
            account_balance=effective_balance,
            risk_percentage=risk_params.risk_percentage,
            entry_price=risk_params.entry_price,
            stop_loss=risk_params.stop_loss,
            symbol_spec=risk_params.symbol_spec
        )

        return super().calculate_lot_size(adjusted_params)
```

### 3. FuturesSessionManager

```python
class FuturesSessionManager:
    """Gestor de sesiones específico para futuros"""

    FUTURES_SESSIONS = {
        "us_futures": {
            "start": "09:30",    # NYSE opening
            "end": "16:00",      # NYSE closing
            "symbols": ["ES", "NQ", "CL", "GC"],
            "timezone": "America/New_York"
        },
        "crypto_futures": {
            "start": "00:00",
            "end": "23:59",
            "symbols": ["BTC", "ETH"],
            "timezone": "UTC"
        }
    }
```

### 4. Configuración de Base de Datos

```sql
-- Tabla para expiraciones de contratos
CREATE TABLE futures_expirations (
    symbol TEXT PRIMARY KEY,
    expiration_date DATE,
    next_contract TEXT,
    rollover_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para márgenes
CREATE TABLE futures_margins (
    symbol TEXT PRIMARY KEY,
    initial_margin REAL,
    maintenance_margin REAL,
    leverage REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📋 Checklist de Implementación

### Fase 1: Base
- [ ] Crear FuturesSymbolManager
- [ ] Implementar FuturesPositionSizer
- [ ] Agregar configuraciones de margen
- [ ] Tests unitarios básicos

### Fase 2: Funcionalidad Core
- [ ] Sistema de expiración de contratos
- [ ] Cálculo de roll-over costs
- [ ] Validaciones de margen
- [ ] Alertas de expiración

### Fase 3: Integración
- [ ] Integrar con bot INTRADAY
- [ ] Configurar sesiones de futuros
- [ ] Logging específico para futuros
- [ ] Tests de integración

### Fase 4: Avanzado
- [ ] Roll-over automático
- [ ] Gestión de múltiples contratos
- [ ] Análisis de correlación
- [ ] Optimización de costos

---

## 📚 Referencias

- [Asset Types Guide](./ASSET_TYPES_GUIDE.md) - Guía general de tipos de activos
- [Position Sizer Documentation](./POSITION_SIZER.md) - Cálculo de lotes base
- [CME Group - Futures Specifications](https://www.cmegroup.com/trading/) - Especificaciones oficiales
- [Interactive Brokers - Futures](https://www.ibkr.com/support/doc) - Guía de futuros

---

## 🎯 Beneficios de Implementar Futuros

### Ventajas
1. **Apalancamiento**: Mayor eficiencia de capital
2. **Liquidez**: Mercados muy líquidos
3. **Diversificación**: Acceso a diferentes mercados
4. **Costos**: Comisiones competitivas

### Casos de Uso
1. **Hedging**: Cobertura de posiciones spot
2. **Speculation**: Trading direccional con leverage
3. **Arbitrage**: Entre spot y futuros
4. **Portfolio Management**: Gestión de riesgo institucional

---

**Última actualización**: Noviembre 2025  
**Versión**: 0.1 (Planificación)  
**Estado**: NO implementado - documentación de requerimientos</content>
<parameter name="filePath">c:\Users\Hector\Desktop\Proyectos\BOTRADING\docs\FUTURES_TRADING_GUIDE.md