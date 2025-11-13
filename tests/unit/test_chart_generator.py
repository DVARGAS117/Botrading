"""
Tests unitarios para ChartGenerator - T24

Estos tests validan la generación de imágenes de gráficos por timeframe
para bots visuales e híbridos, siguiendo la metodología TDD.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T24 - Generación de imágenes por timeframe con estilos consistentes
"""
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile

from src.core.chart_generator import (
    ChartGenerator,
    ChartStyle,
    ChartConfig,
    ChartGeneratorError,
    IndicatorStyle
)
from src.core.mt5_data_extractor import Timeframe, OHLCVData


class TestChartStyle:
    """Tests para la clase ChartStyle"""
    
    def test_chart_style_creation_default(self):
        """
        Dado que se crea un ChartStyle sin parámetros
        Cuando se accede a sus propiedades
        Entonces debe tener valores por defecto razonables
        """
        style = ChartStyle()
        assert style.width > 0
        assert style.height > 0
        assert style.style_type in ['yahoo', 'charles', 'binance', 'mike']
        assert isinstance(style.show_volume, bool)
        assert isinstance(style.show_grid, bool)
    
    def test_chart_style_custom_creation(self):
        """
        Dado que se crea un ChartStyle con parámetros personalizados
        Cuando se validan las propiedades
        Entonces debe mantener los valores personalizados
        """
        style = ChartStyle(
            width=1920,
            height=1080,
            style_type='charles',
            show_volume=False,
            show_grid=True,
            title_fontsize=14
        )
        assert style.width == 1920
        assert style.height == 1080
        assert style.style_type == 'charles'
        assert style.show_volume is False
        assert style.show_grid is True
        assert style.title_fontsize == 14
    
    def test_chart_style_to_dict(self):
        """
        Dado un ChartStyle
        Cuando se convierte a diccionario
        Entonces debe contener todas las propiedades
        """
        style = ChartStyle(width=800, height=600)
        result = style.to_dict()
        assert isinstance(result, dict)
        assert 'width' in result
        assert 'height' in result
        assert result['width'] == 800
        assert result['height'] == 600


class TestIndicatorStyle:
    """Tests para la clase IndicatorStyle"""
    
    def test_indicator_style_creation_emas(self):
        """
        Dado que se configura IndicatorStyle para EMAs
        Cuando se valida la configuración
        Entonces debe tener parámetros correctos para EMA 20/50
        """
        style = IndicatorStyle(
            show_emas=True,
            ema_periods=[20, 50],
            ema_colors=['blue', 'red']
        )
        assert style.show_emas is True
        assert 20 in style.ema_periods
        assert 50 in style.ema_periods
        assert len(style.ema_colors) == 2
    
    def test_indicator_style_creation_all_indicators(self):
        """
        Dado que se habilitan todos los indicadores
        Cuando se crea IndicatorStyle
        Entonces debe soportar EMAs, RSI y MACD
        """
        style = IndicatorStyle(
            show_emas=True,
            show_rsi=True,
            show_macd=True,
            ema_periods=[20, 50],
            rsi_period=14,
            macd_params=(12, 26, 9)
        )
        assert style.show_emas is True
        assert style.show_rsi is True
        assert style.show_macd is True
        assert style.rsi_period == 14
        assert style.macd_params == (12, 26, 9)
    
    def test_indicator_style_no_indicators(self):
        """
        Dado que se deshabilitan todos los indicadores
        Cuando se crea IndicatorStyle
        Entonces debe permitir gráficos sin indicadores
        """
        style = IndicatorStyle(
            show_emas=False,
            show_rsi=False,
            show_macd=False
        )
        assert style.show_emas is False
        assert style.show_rsi is False
        assert style.show_macd is False


class TestChartConfig:
    """Tests para la clase ChartConfig"""
    
    def test_chart_config_creation(self):
        """
        Dado que se crea un ChartConfig
        Cuando se validan sus propiedades
        Entonces debe combinar ChartStyle e IndicatorStyle
        """
        chart_style = ChartStyle()
        indicator_style = IndicatorStyle(show_emas=True)
        
        config = ChartConfig(
            chart_style=chart_style,
            indicator_style=indicator_style,
            output_dir="/tmp/charts"
        )
        assert config.chart_style == chart_style
        assert config.indicator_style == indicator_style
        assert config.output_dir == "/tmp/charts"
    
    def test_chart_config_validation_invalid_output_dir(self):
        """
        Dado que se proporciona un output_dir inválido
        Cuando se crea ChartConfig
        Entonces debe lanzar error de validación
        """
        with pytest.raises((ValueError, ChartGeneratorError)):
            ChartConfig(
                chart_style=ChartStyle(),
                indicator_style=IndicatorStyle(),
                output_dir=""  # Directorio vacío no válido
            )


class TestChartGenerator:
    """Tests principales para ChartGenerator"""
    
    @pytest.fixture
    def sample_ohlcv_data(self):
        """
        Fixture que provee datos OHLCV de ejemplo para testing
        """
        # Crear 100 velas de datos sintéticos
        dates = pd.date_range(
            start=datetime.now() - timedelta(hours=100),
            periods=100,
            freq='1H'
        )
        
        data = pd.DataFrame({
            'time': dates,
            'open': [1.2000 + i*0.0001 for i in range(100)],
            'high': [1.2010 + i*0.0001 for i in range(100)],
            'low': [1.1990 + i*0.0001 for i in range(100)],
            'close': [1.2005 + i*0.0001 for i in range(100)],
            'volume': [1000 + i*10 for i in range(100)]
        })
        
        return OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            data=data,
            count=100
        )
    
    @pytest.fixture
    def generator(self, tmp_path):
        """
        Fixture que provee un ChartGenerator configurado con directorio temporal
        """
        config = ChartConfig(
            chart_style=ChartStyle(),
            indicator_style=IndicatorStyle(show_emas=True),
            output_dir=str(tmp_path)
        )
        return ChartGenerator(config)
    
    def test_generator_initialization(self, tmp_path):
        """
        Dado que se inicializa ChartGenerator
        Cuando se provee una configuración válida
        Entonces debe crear instancia correctamente
        """
        config = ChartConfig(
            chart_style=ChartStyle(),
            indicator_style=IndicatorStyle(),
            output_dir=str(tmp_path)
        )
        generator = ChartGenerator(config)
        assert generator is not None
        assert generator.config == config
    
    def test_generator_initialization_invalid_config(self):
        """
        Dado que se inicializa ChartGenerator
        Cuando se provee configuración None
        Entonces debe lanzar error
        """
        with pytest.raises((ValueError, TypeError, ChartGeneratorError)):
            ChartGenerator(None)
    
    def test_generate_chart_basic(self, generator, sample_ohlcv_data, tmp_path):
        """
        Dado un conjunto de datos OHLCV válidos
        Cuando se genera un gráfico básico
        Entonces debe crear archivo de imagen PNG
        
        Criterio de aceptación T24:
        - Genera imágenes de timeframes (5M, 15M, 1H)
        - Produce archivos compatibles con Gemini
        """
        result_path = generator.generate_chart(
            ohlcv_data=sample_ohlcv_data,
            title="EURUSD Test Chart"
        )
        
        assert result_path is not None
        assert Path(result_path).exists()
        assert Path(result_path).suffix == '.png'
        assert Path(result_path).stat().st_size > 0  # Archivo no vacío
    
    def test_generate_chart_with_emas(self, sample_ohlcv_data, tmp_path):
        """
        Dado un ChartGenerator configurado con EMAs
        Cuando se genera el gráfico
        Entonces debe incluir líneas EMA 20/50
        
        Criterio de aceptación T24:
        - Bot visual tiene configurado estilo con indicadores
        """
        config = ChartConfig(
            chart_style=ChartStyle(),
            indicator_style=IndicatorStyle(
                show_emas=True,
                ema_periods=[20, 50]
            ),
            output_dir=str(tmp_path)
        )
        generator = ChartGenerator(config)
        
        result_path = generator.generate_chart(
            ohlcv_data=sample_ohlcv_data,
            title="EURUSD with EMAs"
        )
        
        assert result_path is not None
        assert Path(result_path).exists()
    
    def test_generate_chart_without_indicators(self, sample_ohlcv_data, tmp_path):
        """
        Dado un ChartGenerator sin indicadores
        Cuando se genera el gráfico
        Entonces debe crear gráfico solo con velas
        
        Criterio de aceptación T24:
        - Estilo con/sin indicadores según configuración
        """
        config = ChartConfig(
            chart_style=ChartStyle(),
            indicator_style=IndicatorStyle(
                show_emas=False,
                show_rsi=False,
                show_macd=False
            ),
            output_dir=str(tmp_path)
        )
        generator = ChartGenerator(config)
        
        result_path = generator.generate_chart(
            ohlcv_data=sample_ohlcv_data,
            title="EURUSD Clean Chart"
        )
        
        assert result_path is not None
        assert Path(result_path).exists()
    
    def test_generate_multiple_timeframes(self, generator, tmp_path):
        """
        Dado que se requieren múltiples timeframes
        Cuando se generan gráficos para 5M, 15M y 1H
        Entonces debe crear tres archivos distintos
        
        Criterio de aceptación T24:
        - Genera imágenes de 5M, 15M y 1H
        - Produce archivos compatibles con Gemini con el estilo definido
        """
        timeframes = [Timeframe.M5, Timeframe.M15, Timeframe.H1]
        generated_files = []
        
        for tf in timeframes:
            # Crear datos para cada timeframe
            dates = pd.date_range(
                start=datetime.now() - timedelta(hours=100),
                periods=100,
                freq=f'{tf.value}min'
            )
            
            data = pd.DataFrame({
                'time': dates,
                'open': [1.2000 + i*0.0001 for i in range(100)],
                'high': [1.2010 + i*0.0001 for i in range(100)],
                'low': [1.1990 + i*0.0001 for i in range(100)],
                'close': [1.2005 + i*0.0001 for i in range(100)],
                'volume': [1000 + i*10 for i in range(100)]
            })
            
            ohlcv_data = OHLCVData(
                symbol="EURUSD",
                timeframe=tf,
                data=data,
                count=100
            )
            
            result_path = generator.generate_chart(
                ohlcv_data=ohlcv_data,
                title=f"EURUSD {tf.name}"
            )
            
            generated_files.append(result_path)
        
        # Validar que se generaron 3 archivos distintos
        assert len(generated_files) == 3
        assert len(set(generated_files)) == 3  # Todos únicos
        
        for file_path in generated_files:
            assert Path(file_path).exists()
            assert Path(file_path).suffix == '.png'
    
    def test_generate_chart_empty_data(self, generator):
        """
        Dado que se proveen datos OHLCV vacíos
        Cuando se intenta generar gráfico
        Entonces debe lanzar ChartGeneratorError
        """
        empty_data = OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=pd.DataFrame(),  # DataFrame vacío
            count=0
        )
        
        with pytest.raises(ChartGeneratorError):
            generator.generate_chart(
                ohlcv_data=empty_data,
                title="Empty Chart"
            )
    
    def test_generate_chart_invalid_data_format(self, generator):
        """
        Dado que se proveen datos con formato inválido
        Cuando se intenta generar gráfico
        Entonces debe lanzar ChartGeneratorError
        """
        # DataFrame sin columnas requeridas
        invalid_data = pd.DataFrame({
            'time': [datetime.now()],
            'price': [1.2000]  # Falta OHLCV
        })
        
        ohlcv_data = OHLCVData(
            symbol="EURUSD",
            timeframe=Timeframe.M5,
            data=invalid_data,
            count=1
        )
        
        with pytest.raises(ChartGeneratorError):
            generator.generate_chart(
                ohlcv_data=ohlcv_data,
                title="Invalid Chart"
            )
    
    def test_generate_chart_custom_filename(self, generator, sample_ohlcv_data):
        """
        Dado que se especifica un nombre de archivo personalizado
        Cuando se genera el gráfico
        Entonces debe usar el nombre especificado
        """
        custom_filename = "custom_chart_eurusd_h1.png"
        
        result_path = generator.generate_chart(
            ohlcv_data=sample_ohlcv_data,
            title="Custom Chart",
            filename=custom_filename
        )
        
        assert Path(result_path).name == custom_filename
    
    def test_generate_chart_different_styles(self, sample_ohlcv_data, tmp_path):
        """
        Dado que se usan diferentes estilos de gráfico
        Cuando se generan múltiples gráficos
        Entonces cada uno debe mantener su estilo consistente
        
        Criterio de aceptación T24:
        - Genera imágenes con estilos consistentes
        """
        styles = ['yahoo', 'charles', 'binance']
        
        for style_name in styles:
            config = ChartConfig(
                chart_style=ChartStyle(style_type=style_name),
                indicator_style=IndicatorStyle(),
                output_dir=str(tmp_path)
            )
            generator = ChartGenerator(config)
            
            result_path = generator.generate_chart(
                ohlcv_data=sample_ohlcv_data,
                title=f"EURUSD {style_name} style"
            )
            
            assert Path(result_path).exists()
    
    def test_chart_dimensions_gemini_compatible(self, generator, sample_ohlcv_data):
        """
        Dado que Gemini tiene requisitos de tamaño de imagen
        Cuando se genera un gráfico
        Entonces debe cumplir con dimensiones compatibles (máx 20MB, formatos PNG/JPEG)
        
        Criterio de aceptación T24:
        - Produce archivos compatibles con Gemini
        """
        result_path = generator.generate_chart(
            ohlcv_data=sample_ohlcv_data,
            title="Gemini Compatible Chart"
        )
        
        file_size = Path(result_path).stat().st_size
        
        # Gemini acepta hasta 20MB por imagen
        assert file_size < 20 * 1024 * 1024  # 20MB en bytes
        assert Path(result_path).suffix in ['.png', '.jpg', '.jpeg']
    
    def test_cleanup_old_charts(self, generator, sample_ohlcv_data, tmp_path):
        """
        Dado que se generan múltiples gráficos
        Cuando se invoca cleanup con retention
        Entonces debe eliminar gráficos antiguos
        """
        # Generar varios gráficos
        for i in range(5):
            generator.generate_chart(
                ohlcv_data=sample_ohlcv_data,
                title=f"Chart {i}",
                filename=f"chart_{i}.png"
            )
        
        # Verificar que se crearon
        files_before = list(Path(tmp_path).glob("*.png"))
        assert len(files_before) == 5
        
        # Limpiar manteniendo solo 2
        generator.cleanup_old_charts(keep_last=2)
        
        files_after = list(Path(tmp_path).glob("*.png"))
        assert len(files_after) <= 2
    
    def test_generate_chart_with_volume_panel(self, sample_ohlcv_data, tmp_path):
        """
        Dado que se habilita el panel de volumen
        Cuando se genera el gráfico
        Entonces debe incluir barras de volumen
        """
        config = ChartConfig(
            chart_style=ChartStyle(show_volume=True),
            indicator_style=IndicatorStyle(),
            output_dir=str(tmp_path)
        )
        generator = ChartGenerator(config)
        
        result_path = generator.generate_chart(
            ohlcv_data=sample_ohlcv_data,
            title="Chart with Volume"
        )
        
        assert Path(result_path).exists()


class TestChartGeneratorIntegration:
    """Tests de integración para generación completa de gráficos"""
    
    def test_full_workflow_visual_bot(self, tmp_path):
        """
        Escenario completo: Bot visual genera gráficos para análisis IA
        
        Dado que el bot visual tiene configurado estilo con indicadores
        Cuando genera imágenes de 5M, 15M y 1H
        Entonces produce archivos compatibles con Gemini con el estilo definido
        """
        # 1. Configurar generador para bot visual
        config = ChartConfig(
            chart_style=ChartStyle(
                width=1200,
                height=800,
                style_type='charles',
                show_volume=True
            ),
            indicator_style=IndicatorStyle(
                show_emas=True,
                ema_periods=[20, 50],
                show_rsi=False,  # Bot visual puede elegir indicadores
                show_macd=False
            ),
            output_dir=str(tmp_path)
        )
        generator = ChartGenerator(config)
        
        # 2. Generar gráficos para múltiples timeframes
        timeframes = [Timeframe.M5, Timeframe.M15, Timeframe.H1]
        generated_charts = []
        
        for tf in timeframes:
            dates = pd.date_range(
                start=datetime.now() - timedelta(hours=200),
                periods=150,
                freq=f'{tf.value}min'
            )
            
            data = pd.DataFrame({
                'time': dates,
                'open': [1.2000 + i*0.0001 for i in range(150)],
                'high': [1.2015 + i*0.0001 for i in range(150)],
                'low': [1.1985 + i*0.0001 for i in range(150)],
                'close': [1.2005 + i*0.0001 for i in range(150)],
                'volume': [1000 + i*10 for i in range(150)]
            })
            
            ohlcv_data = OHLCVData(
                symbol="EURUSD",
                timeframe=tf,
                data=data,
                count=150
            )
            
            chart_path = generator.generate_chart(
                ohlcv_data=ohlcv_data,
                title=f"EURUSD {tf.name}",
                filename=f"eurusd_{tf.name.lower()}.png"
            )
            
            generated_charts.append(chart_path)
        
        # 3. Validar resultados
        assert len(generated_charts) == 3
        
        for chart_path in generated_charts:
            assert Path(chart_path).exists()
            assert Path(chart_path).suffix == '.png'
            
            # Validar compatibilidad con Gemini
            file_size = Path(chart_path).stat().st_size
            assert file_size > 0
            assert file_size < 20 * 1024 * 1024  # <20MB
        
        # 4. Verificar que los archivos son únicos
        assert len(set(generated_charts)) == 3
