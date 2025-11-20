# 📊 Guía de Tipos de Activos Soportados

## 📋 Índice
1. [Introducción](#introducción)
2. [Forex (Pares de Divisas)](#forex-pares-de-divisas)
3. [Metales Preciosos](#metales-preciosos)
4. [Índices Bursátiles](#índices-bursátiles)
5. [Criptomonedas](#criptomonedas)
6. [Configuración por Tipo de Activo](#configuración-por-tipo-de-activo)
7. [Validaciones Específicas](#validaciones-específicas)
8. [Ejemplos de Configuración](#ejemplos-de-configuración)

---

## 🎯 Introducción

El sistema de trading automatizado soporta múltiples tipos de activos financieros, cada uno con sus propias características de cálculo de riesgo y especificaciones técnicas. El sistema obtiene automáticamente las especificaciones desde MT5, pero requiere configuración adecuada para cada tipo de activo.

### Tipos de Activos Soportados

| Tipo | Ejemplos | Estado | Documentación |
|------|----------|--------|---------------|
| Forex | EURUSD, GBPUSD | ✅ Completo | ✅ Documentado |
| Metales | XAUUSD, XAGUSD | ✅ Completo | ✅ Documentado |
| Índices | US30, DE30 | ✅ Completo | ✅ Documentado |
| Criptos | BTCUSD, ETHUSD | ⚠️ Parcial | ✅ [Guía específica](./CRYPTO_TRADING_GUIDE.md) |
| Futuros | ES, GC, CL | ❌ No implementado | ✅ [Guía de planificación](./FUTURES_TRADING_GUIDE.md) |

---

## 💱 Forex (Pares de Divisas)

### Características Principales
- **Contract Size**: 100,000 unidades por lote estándar
- **Point**: 0.00001 (para mayoría de pares)
- **Tick Value**: Variable según par
- **Volatilidad**: Media-Baja

### Ejemplos de Especificaciones

#### EURUSD
```python
SymbolSpecification(
    symbol="EURUSD",
    point=0.00001,        # 1 pip = 0.00001
    tick_size=0.00001,
    tick_value=1.0,       # $1 por pip por lote
    volume_min=0.01,
    volume_max=100.0,
    volume_step=0.01,
    contract_size=100000  # 100,000 unidades
)
```

#### USDJPY
```python
SymbolSpecification(
    symbol="USDJPY",
    point=0.001,          # 1 pip = 0.001
    tick_size=0.001,
    tick_value=1000.0,    # ¥1,000 por pip por lote
    volume_min=0.01,
    volume_max=100.0,
    volume_step=0.01,
    contract_size=100000
)
```

### Cálculo de Riesgo
```python
# EURUSD: 1 pip = $10 por lote estándar
# Riesgo: 2% de $10,000 = $200
# SL: 50 pips de distancia
# Lote calculado: $200 / (50 pips × $10) = 0.4 lotes
```

---

## 🏆 Metales Preciosos

### Características Principales
- **Contract Size**: Variable (100 oz para XAU, 5000 oz para XAG)
- **Point**: 0.01 (para mayoría)
- **Tick Value**: Variable según precio del metal
- **Volatilidad**: Media-Alta

### Ejemplo: XAUUSD (Oro)

```python
SymbolSpecification(
    symbol="XAUUSD",
    point=0.01,           # 1 pip = 0.01 USD
    tick_size=0.01,
    tick_value=1.0,       # $1 por pip por lote
    volume_min=0.01,
    volume_max=10.0,
    volume_step=0.01,
    contract_size=100     # 100 onzas
)
```

### Cálculo de Riesgo
```python
# XAUUSD a $2,000/oz
# Riesgo: 2% de $10,000 = $200
# SL: $20 de distancia (2000 pips)
# Lote calculado: $200 / (2000 pips × $1) = 0.1 lotes
```

### Validaciones Específicas
- Precio debe ser positivo y razonable (> 1000 para XAU)
- Contract size debe coincidir con estándar del broker
- Tick value puede variar según precio spot del metal

---

## 📈 Índices Bursátiles

### Características Principales
- **Contract Size**: 1 (índice puro)
- **Point**: 1.0 (cada punto del índice)
- **Tick Value**: $1 por punto por lote
- **Volatilidad**: Variable según mercado

### Ejemplo: US30 (Dow Jones)

```python
SymbolSpecification(
    symbol="US30",
    point=1.0,            # 1 punto = 1.0
    tick_size=1.0,
    tick_value=1.0,       # $1 por punto por lote
    volume_min=0.1,
    volume_max=10.0,
    volume_step=0.1,
    contract_size=1       # Índice puro
)
```

### Cálculo de Riesgo
```python
# US30 a 35,000 puntos
# Riesgo: 1.5% de $20,000 = $300
# SL: 100 puntos de distancia
# Lote calculado: $300 / (100 puntos × $1) = 3.0 lotes
```

### Otros Índices Comunes
- **DE30**: DAX Alemán
- **UK100**: FTSE 100
- **JP225**: Nikkei 225

---

## ₿ Criptomonedas

### Estado Actual: ⚠️ Parcialmente Implementado

El sistema tiene referencias básicas a criptomonedas pero requiere configuración completa.

### Características Esperadas
- **Contract Size**: Variable (1 BTC, 1 ETH, etc.)
- **Point**: Variable (depende de decimales)
- **Tick Value**: Variable según precio
- **Volatilidad**: Muy Alta

### Configuración Pendiente
```python
# Ejemplo conceptual para BTCUSD
SymbolSpecification(
    symbol="BTCUSD",
    point=0.1,            # Ajustar según broker
    tick_size=0.1,
    tick_value=0.1,       # Variable según precio
    volume_min=0.001,
    volume_max=1.0,
    volume_step=0.001,
    contract_size=1       # 1 BTC
)
```

### Consideraciones Especiales
- Alta volatilidad requiere SL más amplios
- Spreads variables afectan cálculos
- Horarios de trading 24/7
- Decimales variables según cripto

---

## ⚙️ Configuración por Tipo de Activo

### Archivo: `config/trading_sessions.json`

```json
{
    "sessions": {
        "forex_session": {
            "start": "02:00",
            "end": "05:00",
            "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
            "strategies": ["A_tendencia"],
            "risk_level": "medio"
        },
        "metals_session": {
            "start": "08:00",
            "end": "11:00",
            "symbols": ["XAUUSD", "XAGUSD"],
            "strategies": ["B_rango"],
            "risk_level": "alto"
        },
        "indices_session": {
            "start": "14:30",
            "end": "21:00",
            "symbols": ["US30", "DE30"],
            "strategies": ["C_breakout"],
            "risk_level": "medio"
        }
    }
}
```

### Archivo: `config/settings.json`

```json
{
    "asset_types": {
        "forex": {
            "max_risk_per_trade": 2.0,
            "min_sl_pips": 10,
            "max_sl_pips": 200
        },
        "metals": {
            "max_risk_per_trade": 1.5,
            "min_sl_pips": 500,
            "max_sl_pips": 5000
        },
        "indices": {
            "max_risk_per_trade": 1.0,
            "min_sl_pips": 50,
            "max_sl_pips": 1000
        }
    }
}
```

---

## ✅ Validaciones Específicas

### Por Tipo de Activo

#### Forex
- Point debe ser 0.00001 o 0.001
- Contract size debe ser 100,000
- Volume step debe ser 0.01

#### Metales
- Point debe ser 0.01
- Contract size debe ser 100 (XAU) o 5000 (XAG)
- Precios deben ser > 1000 (XAU) o > 15 (XAG)

#### Índices
- Point debe ser 1.0
- Contract size debe ser 1
- Volume step debe ser 0.1

### Validaciones Generales
- Volume min < volume max
- Tick value > 0
- Contract size > 0
- Point > 0

---

## 📝 Ejemplos de Configuración

### Configuración Completa para EURUSD

```python
from src.core.position_sizer import SymbolSpecification, RiskParameters, PositionSizer

# Especificaciones obtenidas automáticamente de MT5
eurusd_spec = SymbolSpecification(
    symbol="EURUSD",
    point=0.00001,
    tick_size=0.00001,
    tick_value=1.0,
    volume_min=0.01,
    volume_max=100.0,
    volume_step=0.01,
    contract_size=100000
)

# Parámetros de riesgo
risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=2.0,
    entry_price=1.1000,
    stop_loss=1.0950,
    symbol_spec=eurusd_spec
)

# Cálculo de lote
sizer = PositionSizer()
result = sizer.calculate_lot_size(risk_params)

print(f"Lote calculado: {result.lot_size}")
print(f"Riesgo en dinero: ${result.risk_amount}")
print(f"Distancia SL: {result.pip_distance} pips")
```

### Configuración para XAUUSD

```python
xauusd_spec = SymbolSpecification(
    symbol="XAUUSD",
    point=0.01,
    tick_size=0.01,
    tick_value=1.0,
    volume_min=0.01,
    volume_max=10.0,
    volume_step=0.01,
    contract_size=100
)

risk_params = RiskParameters(
    account_balance=10000.0,
    risk_percentage=2.0,
    entry_price=2000.0,
    stop_loss=1980.0,
    symbol_spec=xauusd_spec
)

sizer = PositionSizer()
result = sizer.calculate_lot_size(risk_params)
# Resultado: 0.1 lotes
```

---

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Especificaciones Incorrectas
**Síntoma**: Cálculos de lote erróneos
**Solución**: Verificar que MT5 esté conectado y las especificaciones sean correctas

#### 2. Contract Size Incorrecto
**Síntoma**: Valores de pip erróneos
**Solución**: Confirmar contract_size con el broker

#### 3. Tick Value Variable
**Síntoma**: Cálculos inconsistentes en metales/índices
**Solución**: El sistema maneja automáticamente, pero validar con broker

### Logs Relevantes
```
INFO - Symbol info for XAUUSD: point=0.01, tick_value=1.0, contract_size=100
WARNING - tick_size was None for BTCUSD, using point value: 0.1
ERROR - Invalid contract_size: 0 for symbol EURUSD
```

---

## 📚 Referencias

- [MT5 Symbol Specifications](https://www.metatrader5.com/en/terminal/help/trading_advanced/symbol_settings)
- [Position Sizer Documentation](./POSITION_SIZER.md)
- [Symbol Specification Extractor](./SYMBOL_SPEC_EXTRACTOR.md)
- [Trading Sessions Configuration](./TRADING_SESSIONS.md)

---

**Última actualización**: Noviembre 2025  
**Versión**: 1.0  
**Estado**: Documentación completa para activos implementados</content>
<parameter name="filePath">c:\Users\Hector\Desktop\Proyectos\BOTRADING\docs\ASSET_TYPES_GUIDE.md