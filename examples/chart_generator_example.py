"""
Ejemplo de uso de ChartGenerator e ImageFormatter - T24

Este ejemplo demuestra el flujo completo para generar imágenes de gráficos
por timeframe y formatearlas para análisis visual con Gemini.

Casos de uso:
1. Generación de gráficos básicos por timeframe
2. Gráficos con indicadores (EMAs)
3. Gráficos sin indicadores (solo precio)
4. Formateo y optimización para Gemini
5. Procesamiento batch de múltiples timeframes

Author: Botrading Team
Date: 2025-11-13
Ticket: T24 - Generación de imágenes por timeframe con estilos consistentes
"""
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from src.core.mt5_data_extractor import OHLCVData, Timeframe
from src.core.chart_generator import (
    ChartGenerator,
    ChartConfig,
    ChartStyle,
    IndicatorStyle
)
from src.core.image_formatter import ImageFormatter, ImageFormat


def generate_sample_ohlcv_data(symbol: str, timeframe: Timeframe, num_candles: int = 150) -> OHLCVData:
    """
    Genera datos OHLCV de ejemplo para demostración.
    
    En producción, estos datos vendrían de MT5DataExtractor.
    """
    dates = pd.date_range(
        start=datetime.now() - timedelta(hours=num_candles),
        periods=num_candles,
        freq=f'{timeframe.value}min'
    )
    
    # Generar datos sintéticos con tendencia
    base_price = 1.2000
    data = pd.DataFrame({
        'time': dates,
        'open': [base_price + i*0.0001 + (i % 10) * 0.0001 for i in range(num_candles)],
        'high': [base_price + i*0.0001 + (i % 10) * 0.0001 + 0.0005 for i in range(num_candles)],
        'low': [base_price + i*0.0001 + (i % 10) * 0.0001 - 0.0005 for i in range(num_candles)],
        'close': [base_price + i*0.0001 + (i % 10) * 0.0001 + 0.0002 for i in range(num_candles)],
        'volume': [1000 + i*10 + (i % 5) * 100 for i in range(num_candles)]
    })
    
    return OHLCVData(
        symbol=symbol,
        timeframe=timeframe,
        data=data,
        count=num_candles
    )


def example_1_basic_chart_generation():
    """
    Ejemplo 1: Generación básica de gráfico por timeframe
    
    Demuestra:
    - Crear configuración de estilo
    - Generar gráfico simple
    - Guardar en archivo PNG
    """
    print("\n" + "="*70)
    print("EJEMPLO 1: Generación Básica de Gráfico")
    print("="*70)
    
    # 1. Configurar el generador
    config = ChartConfig(
        chart_style=ChartStyle(
            width=1200,
            height=800,
            style_type='charles',
            show_volume=True
        ),
        indicator_style=IndicatorStyle(
            show_emas=False  # Sin indicadores por ahora
        ),
        output_dir="./examples_output/charts"
    )
    
    generator = ChartGenerator(config)
    
    # 2. Generar datos de ejemplo
    ohlcv_data = generate_sample_ohlcv_data("EURUSD", Timeframe.M5, 100)
    
    # 3. Generar gráfico
    chart_path = generator.generate_chart(
        ohlcv_data=ohlcv_data,
        title="EURUSD 5M - Gráfico Básico"
    )
    
    print(f"✅ Gráfico generado: {chart_path}")
    print(f"📊 Tamaño: {Path(chart_path).stat().st_size / 1024:.2f} KB")
    
    return chart_path


def example_2_chart_with_indicators():
    """
    Ejemplo 2: Gráfico con indicadores técnicos
    
    Demuestra:
    - Habilitar EMAs 20/50
    - Personalizar colores
    - Mostrar panel de volumen
    """
    print("\n" + "="*70)
    print("EJEMPLO 2: Gráfico con Indicadores (EMAs)")
    print("="*70)
    
    # 1. Configurar con indicadores
    config = ChartConfig(
        chart_style=ChartStyle(
            width=1200,
            height=800,
            style_type='binance',
            show_volume=True,
            show_grid=True
        ),
        indicator_style=IndicatorStyle(
            show_emas=True,
            ema_periods=[20, 50],
            ema_colors=['#4169E1', '#DC143C']  # Azul y Rojo
        ),
        output_dir="./examples_output/charts"
    )
    
    generator = ChartGenerator(config)
    
    # 2. Generar datos
    ohlcv_data = generate_sample_ohlcv_data("GBPUSD", Timeframe.M15, 150)
    
    # 3. Generar gráfico
    chart_path = generator.generate_chart(
        ohlcv_data=ohlcv_data,
        title="GBPUSD 15M - Con EMAs 20/50",
        filename="gbpusd_15m_with_emas.png"
    )
    
    print(f"✅ Gráfico con indicadores generado: {chart_path}")
    print(f"📊 Incluye: EMA 20 (azul) y EMA 50 (rojo)")
    
    return chart_path


def example_3_multiple_timeframes():
    """
    Ejemplo 3: Generar gráficos para múltiples timeframes
    
    Demuestra:
    - Procesamiento de 5M, 15M y 1H
    - Mismo símbolo, diferentes timeframes
    - Nombres de archivo consistentes
    
    Criterio de aceptación T24:
    "Cuando genera imágenes de 5M, 15M y 1H
     Entonces produce archivos compatibles con Gemini con el estilo definido"
    """
    print("\n" + "="*70)
    print("EJEMPLO 3: Múltiples Timeframes (5M, 15M, 1H)")
    print("="*70)
    
    # Configurar generador
    config = ChartConfig(
        chart_style=ChartStyle(
            width=1200,
            height=800,
            style_type='charles',
            show_volume=True
        ),
        indicator_style=IndicatorStyle(
            show_emas=True,
            ema_periods=[20, 50]
        ),
        output_dir="./examples_output/charts/multi_timeframe"
    )
    
    generator = ChartGenerator(config)
    
    # Timeframes a procesar
    timeframes = [Timeframe.M5, Timeframe.M15, Timeframe.H1]
    symbol = "USDJPY"
    generated_charts = []
    
    for tf in timeframes:
        # Generar datos para cada timeframe
        ohlcv_data = generate_sample_ohlcv_data(symbol, tf, 150)
        
        # Generar gráfico
        chart_path = generator.generate_chart(
            ohlcv_data=ohlcv_data,
            title=f"{symbol} {tf.name}",
            filename=f"{symbol.lower()}_{tf.name.lower()}.png"
        )
        
        generated_charts.append(chart_path)
        print(f"  ✓ {tf.name}: {chart_path}")
    
    print(f"\n✅ Generados {len(generated_charts)} gráficos para análisis multi-timeframe")
    
    return generated_charts


def example_4_optimize_for_gemini():
    """
    Ejemplo 4: Optimizar gráficos para Gemini
    
    Demuestra:
    - Validar compatibilidad con Gemini
    - Optimizar tamaño y formato
    - Cumplir requisitos de API (<20MB, PNG/JPEG)
    
    Criterio de aceptación T24:
    "Produce archivos compatibles con Gemini con el estilo definido"
    """
    print("\n" + "="*70)
    print("EJEMPLO 4: Optimización para Gemini API")
    print("="*70)
    
    # 1. Generar gráfico original
    print("\n📊 Paso 1: Generar gráfico original...")
    config = ChartConfig(
        chart_style=ChartStyle(width=1920, height=1080, dpi=150),
        indicator_style=IndicatorStyle(show_emas=True),
        output_dir="./examples_output/charts/original"
    )
    
    generator = ChartGenerator(config)
    ohlcv_data = generate_sample_ohlcv_data("EURUSD", Timeframe.H1, 200)
    
    original_chart = generator.generate_chart(
        ohlcv_data=ohlcv_data,
        title="EURUSD 1H - Alta Resolución",
        filename="eurusd_h1_original.png"
    )
    
    original_size = Path(original_chart).stat().st_size
    print(f"  ✓ Original: {original_size / (1024*1024):.2f} MB")
    
    # 2. Optimizar para Gemini
    print("\n🔄 Paso 2: Optimizar para Gemini...")
    formatter = ImageFormatter(max_size_mb=20)
    
    optimized_chart = formatter.optimize_for_gemini(
        input_path=original_chart,
        output_path="./examples_output/charts/gemini/eurusd_h1_gemini.png"
    )
    
    print(f"  ✓ Optimizado: {optimized_chart.size_bytes / (1024*1024):.2f} MB")
    print(f"  ✓ Formato: {optimized_chart.format.value}")
    print(f"  ✓ Dimensiones: {optimized_chart.width}x{optimized_chart.height}")
    
    # 3. Validar compatibilidad
    print("\n✔️ Paso 3: Validar compatibilidad...")
    is_valid, message = formatter.validate_image(optimized_chart.path)
    
    if is_valid:
        print(f"  ✅ Imagen compatible con Gemini")
        print(f"  📝 {message}")
    else:
        print(f"  ❌ Problemas de compatibilidad: {message}")
    
    return optimized_chart


def example_5_full_workflow_visual_bot():
    """
    Ejemplo 5: Flujo completo para bot visual
    
    Demuestra:
    - Workflow completo desde datos hasta Gemini
    - Procesamiento de múltiples timeframes
    - Optimización batch
    - Preparación para envío a IA
    
    Criterio de aceptación T24 (Integración):
    "Dado que el bot visual tiene configurado estilo con indicadores
     Cuando genera imágenes de 5M, 15M y 1H
     Entonces produce archivos compatibles con Gemini con el estilo definido"
    """
    print("\n" + "="*70)
    print("EJEMPLO 5: Workflow Completo - Bot Visual")
    print("="*70)
    
    symbol = "GBPUSD"
    timeframes = [Timeframe.M5, Timeframe.M15, Timeframe.H1]
    
    # PASO 1: Configurar generador para bot visual
    print("\n📋 Paso 1: Configurar generador para bot visual...")
    config = ChartConfig(
        chart_style=ChartStyle(
            width=1200,
            height=800,
            style_type='charles',
            show_volume=True,
            show_grid=True
        ),
        indicator_style=IndicatorStyle(
            show_emas=True,
            ema_periods=[20, 50],
            ema_colors=['blue', 'red']
        ),
        output_dir="./examples_output/charts/bot_visual"
    )
    
    generator = ChartGenerator(config)
    print("  ✓ Generador configurado")
    
    # PASO 2: Generar gráficos para cada timeframe
    print("\n📊 Paso 2: Generar gráficos por timeframe...")
    raw_charts = []
    
    for tf in timeframes:
        ohlcv_data = generate_sample_ohlcv_data(symbol, tf, 150)
        
        chart_path = generator.generate_chart(
            ohlcv_data=ohlcv_data,
            title=f"{symbol} {tf.name}",
            filename=f"{symbol.lower()}_{tf.name.lower()}_raw.png"
        )
        
        raw_charts.append(chart_path)
        print(f"  ✓ {tf.name}: Generado")
    
    # PASO 3: Optimizar batch para Gemini
    print("\n🔄 Paso 3: Optimizar batch para Gemini...")
    formatter = ImageFormatter()
    
    optimized_charts = []
    for i, chart_path in enumerate(raw_charts):
        tf_name = timeframes[i].name
        
        optimized = formatter.optimize_for_gemini(
            input_path=chart_path,
            output_path=f"./examples_output/charts/bot_visual/gemini/{symbol.lower()}_{tf_name.lower()}_gemini.png"
        )
        
        optimized_charts.append(optimized)
        print(f"  ✓ {tf_name}: {optimized.size_bytes / 1024:.0f} KB")
    
    # PASO 4: Validar compatibilidad de todos
    print("\n✔️ Paso 4: Validar compatibilidad...")
    all_valid = True
    
    for optimized in optimized_charts:
        is_valid, _ = formatter.validate_image(optimized.path)
        if not is_valid:
            all_valid = False
    
    if all_valid:
        print("  ✅ Todos los gráficos compatibles con Gemini")
        print(f"  📦 {len(optimized_charts)} imágenes listas para análisis IA")
    else:
        print("  ⚠️ Algunos gráficos requieren ajuste")
    
    # PASO 5: Preparar payload para Gemini (simulado)
    print("\n🤖 Paso 5: Preparar para envío a Gemini...")
    image_paths = [opt.path for opt in optimized_charts]
    
    payload = {
        'symbol': symbol,
        'timeframes': [tf.name for tf in timeframes],
        'image_paths': image_paths,
        'total_size_mb': sum(opt.size_bytes for opt in optimized_charts) / (1024*1024),
        'ready_for_ai': all_valid
    }
    
    print(f"  ✓ Símbolo: {payload['symbol']}")
    print(f"  ✓ Timeframes: {', '.join(payload['timeframes'])}")
    print(f"  ✓ Tamaño total: {payload['total_size_mb']:.2f} MB")
    print(f"  ✓ Listo para IA: {'Sí' if payload['ready_for_ai'] else 'No'}")
    
    print("\n✅ Workflow completo finalizado exitosamente")
    
    return payload


def main():
    """
    Ejecuta todos los ejemplos de uso de ChartGenerator e ImageFormatter
    """
    print("\n" + "="*70)
    print("EJEMPLOS DE USO: ChartGenerator e ImageFormatter (T24)")
    print("="*70)
    print("\nDemostración de generación de imágenes por timeframe")
    print("para bots visuales e híbridos con compatibilidad Gemini")
    
    # Ejecutar ejemplos
    try:
        # Ejemplo 1: Básico
        example_1_basic_chart_generation()
        
        # Ejemplo 2: Con indicadores
        example_2_chart_with_indicators()
        
        # Ejemplo 3: Múltiples timeframes
        example_3_multiple_timeframes()
        
        # Ejemplo 4: Optimización Gemini
        example_4_optimize_for_gemini()
        
        # Ejemplo 5: Workflow completo
        example_5_full_workflow_visual_bot()
        
        print("\n" + "="*70)
        print("✅ TODOS LOS EJEMPLOS EJECUTADOS EXITOSAMENTE")
        print("="*70)
        print("\n📁 Los gráficos se guardaron en: ./examples_output/charts/")
        print("📖 Revisar cada ejemplo para casos de uso específicos")
        
    except Exception as e:
        print(f"\n❌ Error ejecutando ejemplos: {str(e)}")
        raise


if __name__ == "__main__":
    main()
