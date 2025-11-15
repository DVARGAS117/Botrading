# T24: Generación de Imágenes por Timeframe con Estilos Consistentes

**Ticket:** #40  
**Épica:** Indicadores e Imágenes  
**Fase:** 2  
**Prioridad:** P1  
**Estado:** ✅ Completado

---

## 📋 Resumen

Implementación de generación de imágenes de gráficos por timeframe (5M, 15M, 1H) con estilos consistentes para bots visuales e híbridos. Las imágenes son compatibles con Gemini API para análisis visual por IA.

## 🎯 Criterios de Aceptación

```gherkin
Escenario: Generar imágenes por timeframe con estilos consistentes
  Dado que el bot visual tiene configurado estilo con/sin indicadores
  Cuando genera imágenes de 5M, 15M y 1H
  Entonces produce archivos compatibles con Gemini con el estilo definido
```

**Resultado:** ✅ **CUMPLIDO**

---

## 🏗️ Arquitectura

### Módulos Implementados

1. **`src/core/chart_generator.py`** (413 líneas)
   - Generación de gráficos de velas japonesas
   - Soporte para indicadores técnicos (EMAs)
   - Múltiples estilos visuales
   - Gestión de archivos de salida

2. **`src/core/image_formatter.py`** (411 líneas)
   - Optimización de imágenes para Gemini
   - Validación de requisitos API (<20MB, PNG/JPEG)
   - Redimensionamiento con aspect ratio
   - Compresión inteligente

### Clases Principales

#### ChartGenerator
```python
ChartGenerator(config: ChartConfig)
├── generate_chart() → str
├── cleanup_old_charts() → int
└── _build_addplots() → List
```

#### ImageFormatter
```python
ImageFormatter(max_size_mb: int = 20)
├── validate_image() → Tuple[bool, str]
├── format_image() → FormattedImage
├── optimize_for_gemini() → FormattedImage
└── format_batch() → List[FormattedImage]
```

---

## 📊 Configuración

### ChartStyle
```json
{
  "width": 1200,
  "height": 800,
  "style_type": "charles",
  "show_volume": true,
  "show_grid": true,
  "title_fontsize": 12,
  "dpi": 100
}
```

### IndicatorStyle
```json
{
  "show_emas": true,
  "ema_periods": [20, 50],
  "ema_colors": ["blue", "red"],
  "show_rsi": false,
  "show_macd": false
}
```

---

## 🚀 Uso

### Ejemplo Básico

```python
from src.core.chart_generator import ChartGenerator, ChartConfig, ChartStyle, IndicatorStyle
from src.core.image_formatter import ImageFormatter

# Configurar
config = ChartConfig(
    chart_style=ChartStyle(style_type='charles'),
    indicator_style=IndicatorStyle(show_emas=True),
    output_dir="./charts"
)

generator = ChartGenerator(config)

# Generar gráfico
chart_path = generator.generate_chart(
    ohlcv_data=ohlcv_data,
    title="EURUSD 5M"
)

# Optimizar para Gemini
formatter = ImageFormatter()
formatted = formatter.optimize_for_gemini(
    input_path=chart_path,
    output_path="./gemini/eurusd_5m.png"
)
```

### Múltiples Timeframes

```python
for tf in [Timeframe.M5, Timeframe.M15, Timeframe.H1]:
    ohlcv_data = get_data(symbol, tf)
    chart_path = generator.generate_chart(
        ohlcv_data=ohlcv_data,
        title=f"{symbol} {tf.name}"
    )
```

---

## ✅ Testing

### Cobertura de Tests

- **test_chart_generator.py:** 22 tests ✅
- **test_image_formatter.py:** 21 tests ✅
- **Total:** 43 tests pasando

### Casos Cubiertos

| Categoría | Tests |
|-----------|-------|
| Configuración | 8 |
| Generación básica | 7 |
| Indicadores | 5 |
| Múltiples timeframes | 3 |
| Optimización Gemini | 8 |
| Manejo de errores | 6 |
| Integración E2E | 6 |

---

## 📦 Archivos Generados

```
src/core/
├── chart_generator.py      # 413 líneas
└── image_formatter.py      # 411 líneas

tests/unit/
├── test_chart_generator.py # 680 líneas
└── test_image_formatter.py # 480 líneas

config/
└── chart_styles.example.json # 135 líneas

examples/
└── chart_generator_example.py # 460 líneas

context/DOCUMENTACION/
└── T24_generacion_imagenes_timeframe.md (este archivo)
```

---

## 🔧 Dependencias Agregadas

```txt
matplotlib>=3.7.0
mplfinance>=0.12.0
ta>=0.11.0
```

---

## 💡 Características Clave

### 1. Estilos Consistentes
- **9 estilos mplfinance** disponibles
- Configuración por timeframe
- Personalización de colores

### 2. Compatibilidad Gemini
- ✅ Tamaño <20MB
- ✅ Formatos PNG/JPEG
- ✅ Dimensiones optimizadas
- ✅ Compresión inteligente

### 3. Indicadores Técnicos
- EMAs 20/50 superpuestas
- Panel de volumen opcional
- Extensible a RSI/MACD (futuro)

### 4. Gestión de Archivos
- Nombres consistentes por timeframe
- Limpieza automática de antiguos
- Organización por símbolo

---

## 🎨 Estilos Visuales Soportados

| Estilo | Descripción |
|--------|-------------|
| yahoo | Clásico estilo Yahoo Finance |
| charles | Estilo Charles Schwab (recomendado) |
| binance | Estilo Binance Exchange |
| mike | Estilo minimalista |
| nightclouds | Tema oscuro |

---

## 🚦 Flujo Completo: Bot Visual

```
1. Obtener datos OHLCV (MT5DataExtractor)
   ↓
2. Configurar ChartGenerator con estilo
   ↓
3. Generar gráficos por timeframe (5M, 15M, 1H)
   ↓
4. Optimizar para Gemini (ImageFormatter)
   ↓
5. Validar compatibilidad
   ↓
6. Enviar a IA para análisis
```

---

## 📈 Métricas

| Métrica | Valor |
|---------|-------|
| Tests implementados | 43 |
| Tests pasando | 43 ✅ |
| Líneas de código | 824 |
| Líneas de tests | 1160 |
| Cobertura estimada | >85% |
| Timeframes soportados | 3 (5M, 15M, 1H) |
| Estilos disponibles | 9 |
| Formatos imagen | 2 (PNG, JPEG) |

---

## 🔮 Mejoras Futuras

1. **Indicadores adicionales:**
   - RSI en panel separado
   - MACD con histograma
   - Bollinger Bands

2. **Optimizaciones:**
   - Cache de gráficos generados
   - Generación paralela
   - Compresión adaptativa

3. **Personalización:**
   - Temas custom
   - Overlays personalizados
   - Anotaciones automáticas

---

## ✅ Cumplimiento de Criterios

| Criterio | Estado |
|----------|--------|
| Genera imágenes 5M, 15M, 1H | ✅ |
| Estilos consistentes | ✅ |
| Con/sin indicadores | ✅ |
| Compatible con Gemini | ✅ |
| Tests >80% | ✅ |
| Documentación completa | ✅ |
| Ejemplos funcionales | ✅ |

---

**Autor:** Sistema Botrading  
**Fecha:** 2025-11-13  
**Versión:** 1.0
