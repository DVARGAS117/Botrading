# Estrategia Kamikaze - Documentación

## Resumen
Estrategia de trading que combina análisis de tendencia H1 con Gemini 2.5 Pro y reconocimiento matemático de patrones de velas en M5 para ejecutar operaciones de alta precisión.

## Concepto Base

La estrategia "Kamikaze" opera bajo el principio de **confluencia entre tendencia y patrón**:

1. **Gemini 2.5 Pro** analiza 10 velas H1 para determinar la tendencia inmediata (BULLISH/BEARISH/NEUTRAL)
2. **Detector de Patrones** analiza 100 velas M5 (últimas 2 para patrones, 50+ para EMA de contexto)
3. **Ejecución** solo ocurre cuando hay confluencia: Tendencia + Patrón coinciden

### Datos Utilizados

- **Para Gemini (H1)**: 10 velas horarias (~10 horas de contexto)
  - Última vela: OPEN (en formación)
  - Anteriores: CLOSED
  - Incluye timestamp para análisis temporal

- **Para Patrones (M5)**: 100 velas de 5 minutos (~8.3 horas de historia)
  - Solo velas CLOSED (evita repintado)
  - Últimas 2 velas: Detección de patrones
  - 50+ velas: Cálculo de EMA 50 como contexto informativo

### Indicador de Contexto: EMA 50

La estrategia calcula una **EMA de 50 períodos en M5** como indicador de referencia:
- **NO bloquea trades** (no es filtro eliminatorio)
- Proporciona **contexto adicional** en los logs
- Permite análisis post-mortem de calidad de señales
- Identifica si el precio está en zona de compras (ABOVE EMA) o ventas (BELOW EMA)

**Filosofía**: Gemini ya actúa como filtro de tendencia macro. La EMA complementa sin interferir.

### Patrones Reconocidos

#### 1. HAMMER (Martillo) - Señal Alcista
- **Descripción**: Vela con mecha inferior larga (≥2x el cuerpo) y cuerpo pequeño en la parte superior
- **Significado**: Rechazo fuerte de zona baja, posible reversión alcista
- **Condición**: Requiere Bias BULLISH de Gemini

#### 2. SHOOTING STAR (Estrella Fugaz) - Señal Bajista
- **Descripción**: Vela con mecha superior larga (≥2x el cuerpo) y cuerpo pequeño en la parte inferior
- **Significado**: Rechazo fuerte de zona alta, posible reversión bajista
- **Condición**: Requiere Bias BEARISH de Gemini

#### 3. BULLISH ENGULFING (Envolvente Alcista) - Señal Alcista
- **Descripción**: Vela alcista que envuelve completamente a la vela bajista anterior
- **Significado**: Cambio de momentum, los compradores toman control
- **Condición**: Requiere Bias BULLISH de Gemini

#### 4. BEARISH ENGULFING (Envolvente Bajista) - Señal Bajista
- **Descripción**: Vela bajista que envuelve completamente a la vela alcista anterior
- **Significado**: Cambio de momentum, los vendedores toman control
- **Condición**: Requiere Bias BEARISH de Gemini

## Reglas de Trading

### Señal de COMPRA (LONG)
- Gemini indica tendencia BULLISH en H1
- **Y** se detecta patrón alcista en M5: HAMMER o BULLISH_ENGULFING
- **Y** no hay posición abierta en el par
- **Y** hay menos de 2 posiciones totales abiertas

### Señal de VENTA (SHORT)
- Gemini indica tendencia BEARISH en H1
- **Y** se detecta patrón bajista en M5: SHOOTING_STAR o BEARISH_ENGULFING
- **Y** no hay posición abierta en el par
- **Y** hay menos de 2 posiciones totales abiertas

### Gestión de Riesgo
- **Máximo de posiciones**: 2 simultáneas (1 por par)
- **Stop Loss**: 300 puntos (30 pips) - Ajustado para volatilidad intradía M5
- **Take Profit**: 600 puntos (60 pips) - Ratio 1:2 realista
- **Lote**: 0.01 (riesgo ~$3 por operación)
- **Activos**: XAUUSD (Oro), NAS100 (Nasdaq)

## Flujo de Ejecución

```
1. Cada 30 minutos:
   - Consultar Gemini con datos H1
   - Actualizar Bias del mercado
   - Guardar estado (persiste hasta próxima consulta)

2. Cada 5 minutos (M5, 1 minuto después del cierre de vela):
       - Verificar límite de posiciones
       - Analizar velas M5 cerradas
       - Detectar patrones matemáticos
       - Si hay confluencia Bias + Patrón:
         * Ejecutar orden
```

## Ventajas del Enfoque

1. **Filtro de Ruido**: No opera en cada movimiento pequeño
2. **Confluencia Doble**: Tendencia macro + patrón micro = Alta probabilidad
3. **Matemática Pura**: Detección de patrones sin subjetividad
4. **Control de Riesgo**: Límite de posiciones y gestión de capital
5. **Evita Contratendencia**: Si Gemini dice BEARISH pero aparece HAMMER, NO opera

## Datos Enviados a Gemini

Para maximizar precisión, Gemini recibe:
- Últimas 10 velas H1 con OHLC completo
- **Estado de cada vela**: OPEN (última, en formación) o CLOSED (históricas)
- **Timestamp del servidor**: Hora actual de consulta
- **Contexto**: Nombre del símbolo y solicitud de análisis SMC

## Configuración

### Parámetros Principales
```python
SYMBOLS = ["XAUUSD", "US100"]
TIMEFRAME_ANALYSIS = H1     # Gemini analiza en H1
TIMEFRAME_EXECUTION = M5    # Patrones se detectan en M5
GEMINI_INTERVAL = 1800      # 30 minutos entre consultas
LOT_SIZE = 0.01
SL_POINTS = 500
TP_POINTS = 1000
DEVIATION = 20
MAX_POSITIONS = 2           # Máximo total
MAX_PER_SYMBOL = 1          # Máximo por par
```

## Ejemplo de Operación Real

### Escenario 1: Compra en XAUUSD
```
10:00 - Gemini consulta H1 → Responde "BULLISH"
10:05 - Bot analiza M5 → Detecta velas normales → No opera
10:10 - Bot analiza M5 → Detecta HAMMER → ✅ COMPRA
       (Confluencia: BULLISH + HAMMER)
```

### Escenario 2: NO Opera (Sin Confluencia)
```
10:00 - Gemini consulta H1 → Responde "BULLISH"
10:05 - Bot analiza M5 → Detecta SHOOTING_STAR → ❌ NO OPERA
       (Patrón bajista con tendencia alcista = Sin confluencia)
```

### Escenario 3: Límite de Posiciones
```
10:00 - XAUUSD abierto, US100 abierto (2/2 posiciones)
10:05 - Nueva señal en XAUUSD → ❌ NO OPERA
       (Límite de posiciones alcanzado)
```

## Uso

### Ejecución en Modo Demo
```bash
python -m src.bots.strategies.Kamikaze.main --mode demo --verbose
```

### Ejecución en Modo Live
```bash
python -m src.bots.strategies.Kamikaze.main --mode live --verbose
```

### Ejecutar Pruebas
```bash
python -m unittest tests/bots/strategies/Kamikaze/test_kamikaze.py -v
```

## Pruebas Unitarias

La estrategia cuenta con 16 pruebas que validan:
- ✅ Detección correcta de cada patrón (HAMMER, SHOOTING_STAR, ENGULFING)
- ✅ Señales de compra/venta con confluencia
- ✅ Rechazo de señales sin confluencia
- ✅ Persistencia del Bias entre ciclos
- ✅ Límite de posiciones (total y por símbolo)
- ✅ Integración con Gemini (timestamp y estado de velas)

## Notas Técnicas

- **Velas cerradas**: El detector de patrones usa solo velas cerradas en M5 para evitar repinte
- **Velas abiertas a Gemini**: La última vela H1 se marca como OPEN para contexto completo
- **Backoff**: Si Gemini falla, el Bias se mantiene en NEUTRAL (no opera)
- **Logging**: Todos los patrones detectados y decisiones se registran con emojis para facilitar monitoreo

## Estructura de Archivos

```
src/bots/strategies/Kamikaze/
├── strategy.py      # Lógica principal de la estrategia
├── config.py        # Configuración y parámetros
├── main.py          # Punto de entrada
├── estrategia.md    # Script original de referencia
└── README.md        # Esta documentación

tests/bots/strategies/Kamikaze/
└── test_kamikaze.py # Pruebas unitarias completas
```

---

**Última actualización**: 2025-12-01  
**Versión**: 2.1 (scheduler M5 + verbose + Bias cada 30min)  
**Autor**: Botrading Team
