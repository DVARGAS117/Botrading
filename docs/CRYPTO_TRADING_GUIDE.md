# ₿ Guía de Trading con Criptomonedas

## 📋 Índice
1. [Estado de Implementación](#estado-de-implementación)
2. [Características de Criptomonedas](#características-de-criptomonedas)
3. [Configuración Requerida](#configuración-requerida)
4. [Especificaciones Técnicas](#especificaciones-técnicas)
5. [Consideraciones de Riesgo](#consideraciones-de-riesgo)
6. [Ejemplos de Configuración](#ejemplos-de-configuración)

---

## ⚠️ Estado de Implementación

**Estado Actual**: Parcialmente Implementado

### ✅ Lo que SÍ funciona:
- Sistema de cálculo de lotes genérico (PositionSizer)
- Extracción automática de especificaciones desde MT5
- Soporte básico en tests y ejemplos

### ❌ Lo que FALTA implementar:
- Configuración específica de sesiones de trading
- Validaciones específicas para criptos
- Manejo de volatilidad extrema
- Ajustes de spread variables

---

## ₿ Características de Criptomonedas

### Aspectos Técnicos
- **Volatilidad**: Muy alta (10-20% diario típico)
- **Horarios**: Trading 24/7 (no hay sesiones específicas)
- **Spreads**: Variables y generalmente más amplios
- **Decimales**: Variables según criptomoneda
- **Liquidez**: Variable según par y exchange

### Diferencias con Forex/Metales
| Aspecto | Forex/Metales | Criptomonedas |
|---------|----------------|---------------|
| Volatilidad | Media-Baja | Muy Alta |
| Horarios | Sesiones específicas | 24/7 |
| Spreads | Estables | Variables |
| Contract Size | Fijo | Variable |
| Point | Estándar | Variable |

---

## ⚙️ Configuración Requerida

### 1. Especificaciones de Símbolos

El sistema obtiene automáticamente las especificaciones desde MT5, pero aquí están los valores típicos:

#### BTCUSD (Bitcoin vs USD)
```python
SymbolSpecification(
    symbol="BTCUSD",
    point=0.1,            # 1 pip = 0.1 USD
    tick_size=0.1,
    tick_value=0.1,       # $0.1 por pip por lote
    volume_min=0.001,     # 0.001 BTC mínimo
    volume_max=1.0,       # 1 BTC máximo
    volume_step=0.001,
    contract_size=1       # 1 BTC por contrato
)
```

#### ETHUSD (Ethereum vs USD)
```python
SymbolSpecification(
    symbol="ETHUSD",
    point=0.01,           # 1 pip = 0.01 USD
    tick_size=0.01,
    tick_value=0.01,      # $0.01 por pip por lote
    volume_min=0.01,      # 0.01 ETH mínimo
    volume_max=10.0,      # 10 ETH máximo
    volume_step=0.01,
    contract_size=1       # 1 ETH por contrato
)
```

### 2. Configuración de Sesiones

Como las criptos operan 24/7, se pueden incluir en sesiones existentes:

```json
{
    "sessions": {
        "crypto_session": {
            "start": "00:00",
            "end": "23:59",
            "symbols": ["BTCUSD", "ETHUSD"],
            "strategies": ["B_rango"],
            "risk_level": "bajo"
        }
    }
}
```

### 3. Configuración de Riesgo

Debido a la alta volatilidad, se recomienda riesgo más conservador:

```json
{
    "asset_types": {
        "crypto": {
            "max_risk_per_trade": 0.5,    // 0.5% (muy conservador)
            "min_sl_pips": 1000,          // SL amplio por volatilidad
            "max_sl_pips": 10000
        }
    }
}
```

---

## 🔧 Especificaciones Técnicas

### Cálculo de Lotes

#### Ejemplo BTCUSD
```python
# BTC a $50,000
# Riesgo: 0.5% de $10,000 = $50
# SL: 5% de distancia ($2,500 = 25,000 pips)
# Valor por pip: $0.1
# Lote calculado: $50 / (25,000 pips × $0.1) = 0.0002 BTC

risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=0.5,
    entry_price=50000.0,
    stop_loss=47500.0,    # 5% de SL
    symbol_spec=btc_spec
)

sizer = PositionSizer()
result = sizer.calculate_lot_size(risk_params)
# Resultado: ~0.0002 lotes
```

### Manejo de Decimales

Las criptos requieren manejo especial de decimales:

```python
# BTC: hasta 8 decimales
# ETH: hasta 6 decimales
# Ajustar volume_step según precisión requerida

btc_spec = SymbolSpecification(
    symbol="BTCUSD",
    volume_step=0.00000001,  # 8 decimales para BTC
    # ... otros parámetros
)
```

---

## ⚠️ Consideraciones de Riesgo

### Volatilidad Extrema
- **Movimientos diarios**: 5-15% son comunes
- **Eventos de mercado**: Pueden causar gaps de 20-50%
- **Recomendación**: SL amplio (mínimo 2-3% del precio)

### Liquidez Variable
- **Horas pico**: Mayor liquidez (sesiones forex superpuestas)
- **Horas bajas**: Spreads más amplios, slippage mayor
- **Recomendación**: Evitar trading en horas de baja liquidez

### Correlación con Mercado Tradicional
- **Sesiones forex**: Mayor volatilidad cuando NY/Londres operan
- **Fin de semana**: Menor liquidez, mayor volatilidad
- **Recomendación**: Alinear con sesiones tradicionales

### Consideraciones Técnicas
- **Spreads variables**: Afectan cálculos de SL/TP
- **Slippage**: Común en órdenes market
- **Gaps**: Posibles en precios entre sesiones

---

## 📝 Ejemplos de Configuración

### Configuración Completa para BTCUSD

```python
from src.core.position_sizer import SymbolSpecification, RiskParameters, PositionSizer

# Especificaciones para BTCUSD (valores aproximados)
btc_spec = SymbolSpecification(
    symbol="BTCUSD",
    point=0.1,
    tick_size=0.1,
    tick_value=0.1,
    volume_min=0.001,
    volume_max=1.0,
    volume_step=0.001,
    contract_size=1
)

# Parámetros de riesgo conservadores para criptos
risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=0.5,      # Muy conservador
    entry_price=50000.0,
    stop_loss=47500.0,        # 5% de SL (muy amplio)
    symbol_spec=btc_spec
)

# Cálculo de lote
sizer = PositionSizer()
result = sizer.calculate_lot_size(risk_params)

print(f"Lote calculado: {result.lot_size}")
print(f"Riesgo en dinero: ${result.risk_amount}")
print(f"Distancia SL: {result.pip_distance} pips")
```

### Configuración para Sesión de Criptos

```json
{
    "sessions": {
        "crypto_24_7": {
            "start": "00:00",
            "end": "23:59",
            "symbols": ["BTCUSD", "ETHUSD", "ADAUSD"],
            "strategies": ["B_rango"],
            "risk_level": "bajo",
            "description": "Criptomonedas - trading 24/7 con riesgo conservador"
        }
    }
}
```

### Validación de Precios

```python
def validate_crypto_price(symbol: str, price: float) -> bool:
    """Validar que el precio es razonable para criptos"""
    price_ranges = {
        "BTCUSD": (10000, 200000),   # $10K - $200K
        "ETHUSD": (100, 10000),      # $100 - $10K
        "ADAUSD": (0.1, 10),         # $0.1 - $10
    }

    if symbol not in price_ranges:
        return False

    min_price, max_price = price_ranges[symbol]
    return min_price <= price <= max_price
```

---

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Volatilidad Extrema
**Síntoma**: SL se activa inmediatamente
**Solución**: Aumentar distancia del SL (mínimo 2-3%)

#### 2. Spreads Variables
**Síntoma**: Cálculos de pip value inconsistentes
**Solución**: Verificar tick_value en tiempo real desde MT5

#### 3. Liquidez Baja
**Síntoma**: Slippage alto, órdenes no ejecutadas
**Solución**: Operar solo en horas de alta liquidez

#### 4. Gaps de Precio
**Síntoma**: Precios discontinuos entre sesiones
**Solución**: Usar órdenes limit, evitar órdenes market en gaps

### Logs Relevantes
```
WARNING - High volatility detected for BTCUSD: price moved 3% in 5 minutes
INFO - Crypto session active: BTCUSD, ETHUSD
ERROR - Slippage exceeded limit for crypto order
```

---

## 📚 Referencias

- [Asset Types Guide](./ASSET_TYPES_GUIDE.md) - Guía general de tipos de activos
- [Position Sizer Documentation](./POSITION_SIZER.md) - Cálculo de lotes
- [Trading Sessions Configuration](./TRADING_SESSIONS.md) - Configuración de sesiones
- [Risk Management Guide](./RISK_MANAGEMENT.md) - Gestión de riesgo

---

## 🚧 Próximos Pasos

### Implementación Pendiente
1. **Configuración de sesiones específicas** para criptos
2. **Validaciones de volatilidad** en tiempo real
3. **Ajustes automáticos de SL** según volatilidad
4. **Manejo de spreads variables** en cálculos
5. **Alertas de liquidez** baja

### Mejoras Futuras
1. **Integración con datos de volatilidad** externa
2. **Ajustes dinámicos de riesgo** según mercado
3. **Soporte para más criptomonedas** (SOL, DOT, etc.)
4. **Análisis de correlación** con forex/índices

---

**Última actualización**: Noviembre 2025  
**Versión**: 0.5 (Parcial)  
**Estado**: Documentación preliminar - implementación pendiente</content>
<parameter name="filePath">c:\Users\Hector\Desktop\Proyectos\BOTRADING\docs\CRYPTO_TRADING_GUIDE.md