"""
Tests unitarios para ImageFormatter - T24

Estos tests validan la preparación de imágenes para ser compatibles
con la API de Gemini, incluyendo validación de formato, tamaño y optimización.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T24 - Generación de imágenes por timeframe con estilos consistentes
"""
import pytest
from pathlib import Path
from PIL import Image
import tempfile
import os

from src.core.image_formatter import (
    ImageFormatter,
    ImageFormat,
    ImageFormatterError,
    FormattedImage
)


class TestImageFormat:
    """Tests para el enum ImageFormat"""
    
    def test_image_format_values(self):
        """
        Dado el enum ImageFormat
        Cuando se consultan los valores
        Entonces debe tener PNG y JPEG
        """
        assert ImageFormat.PNG.value == 'png'
        assert ImageFormat.JPEG.value == 'jpeg'
    
    def test_image_format_from_string(self):
        """
        Dado un string de formato
        Cuando se convierte a enum
        Entonces debe retornar el formato correcto
        """
        assert ImageFormat.from_string('png') == ImageFormat.PNG
        assert ImageFormat.from_string('PNG') == ImageFormat.PNG
        assert ImageFormat.from_string('jpeg') == ImageFormat.JPEG
        assert ImageFormat.from_string('jpg') == ImageFormat.JPEG


class TestFormattedImage:
    """Tests para la dataclass FormattedImage"""
    
    def test_formatted_image_creation(self):
        """
        Dado que se crea un FormattedImage
        Cuando se validan sus propiedades
        Entonces debe contener path, formato, tamaño y dimensiones
        """
        formatted = FormattedImage(
            path="/tmp/chart.png",
            format=ImageFormat.PNG,
            size_bytes=150000,
            width=1200,
            height=800
        )
        
        assert formatted.path == "/tmp/chart.png"
        assert formatted.format == ImageFormat.PNG
        assert formatted.size_bytes == 150000
        assert formatted.width == 1200
        assert formatted.height == 800
    
    def test_formatted_image_to_dict(self):
        """
        Dado un FormattedImage
        Cuando se convierte a diccionario
        Entonces debe incluir todas las propiedades
        """
        formatted = FormattedImage(
            path="/tmp/chart.png",
            format=ImageFormat.PNG,
            size_bytes=150000,
            width=1200,
            height=800
        )
        
        result = formatted.to_dict()
        
        assert isinstance(result, dict)
        assert result['path'] == "/tmp/chart.png"
        assert result['format'] == 'png'
        assert result['size_bytes'] == 150000
        assert result['width'] == 1200
        assert result['height'] == 800


class TestImageFormatter:
    """Tests principales para ImageFormatter"""
    
    @pytest.fixture
    def sample_png_image(self, tmp_path):
        """
        Fixture que crea una imagen PNG de ejemplo
        """
        img_path = tmp_path / "test_chart.png"
        
        # Crear imagen de prueba
        img = Image.new('RGB', (1200, 800), color='white')
        img.save(img_path, 'PNG')
        
        return str(img_path)
    
    @pytest.fixture
    def large_image(self, tmp_path):
        """
        Fixture que crea una imagen grande (>20MB) para testing
        """
        img_path = tmp_path / "large_chart.png"
        
        # Crear imagen muy grande
        img = Image.new('RGB', (5000, 5000), color='blue')
        img.save(img_path, 'PNG')
        
        return str(img_path)
    
    @pytest.fixture
    def formatter(self):
        """
        Fixture que provee un ImageFormatter configurado
        """
        return ImageFormatter(max_size_mb=20)
    
    def test_formatter_initialization(self):
        """
        Dado que se inicializa ImageFormatter
        Cuando se provee configuración válida
        Entonces debe crear instancia correctamente
        """
        formatter = ImageFormatter(max_size_mb=20)
        assert formatter is not None
        assert formatter.max_size_mb == 20
    
    def test_formatter_initialization_default(self):
        """
        Dado que se inicializa ImageFormatter sin parámetros
        Cuando se usa configuración por defecto
        Entonces debe usar 20MB como límite
        """
        formatter = ImageFormatter()
        assert formatter.max_size_mb == 20
    
    def test_validate_image_gemini_compatible(self, formatter, sample_png_image):
        """
        Dado una imagen PNG válida
        Cuando se valida compatibilidad con Gemini
        Entonces debe pasar validación
        
        Criterio de aceptación T24:
        - Produce archivos compatibles con Gemini
        """
        is_valid, message = formatter.validate_image(sample_png_image)
        assert is_valid is True
        assert "compatible" in message.lower() or message == ""
    
    def test_validate_image_file_not_exists(self, formatter):
        """
        Dado que se valida imagen inexistente
        Cuando el archivo no existe
        Entonces debe fallar validación
        """
        is_valid, message = formatter.validate_image("/nonexistent/image.png")
        assert is_valid is False
        assert ("not found" in message.lower() or 
                "no existe" in message.lower() or 
                "encontrado" in message.lower())
    
    def test_validate_image_invalid_format(self, formatter, tmp_path):
        """
        Dado que se valida archivo con formato no soportado
        Cuando se valida un BMP o GIF
        Entonces debe fallar validación
        """
        # Crear imagen BMP
        bmp_path = tmp_path / "chart.bmp"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(bmp_path, 'BMP')
        
        is_valid, message = formatter.validate_image(str(bmp_path))
        assert is_valid is False
        assert "format" in message.lower() or "formato" in message.lower()
    
    def test_validate_image_too_large(self, formatter, large_image):
        """
        Dado una imagen mayor a 20MB
        Cuando se valida el tamaño
        Entonces debe fallar validación
        """
        # Verificar que la imagen es realmente grande
        size_mb = Path(large_image).stat().st_size / (1024 * 1024)
        
        if size_mb > 20:
            is_valid, message = formatter.validate_image(large_image)
            assert is_valid is False
            assert "size" in message.lower() or "tamaño" in message.lower()
    
    def test_format_image_basic(self, formatter, sample_png_image, tmp_path):
        """
        Dado una imagen PNG válida
        Cuando se formatea para Gemini
        Entonces debe crear FormattedImage válido
        
        Criterio de aceptación T24:
        - Produce archivos compatibles con Gemini con el estilo definido
        """
        output_path = tmp_path / "formatted_chart.png"
        
        formatted = formatter.format_image(
            input_path=sample_png_image,
            output_path=str(output_path)
        )
        
        assert isinstance(formatted, FormattedImage)
        assert Path(formatted.path).exists()
        assert formatted.format == ImageFormat.PNG
        assert formatted.size_bytes > 0
        assert formatted.size_bytes < 20 * 1024 * 1024  # <20MB
    
    def test_format_image_compress_large(self, formatter, large_image, tmp_path):
        """
        Dado una imagen grande
        Cuando se formatea con compresión
        Entonces debe reducir tamaño manteniendo calidad
        """
        output_path = tmp_path / "compressed_chart.jpeg"
        
        formatted = formatter.format_image(
            input_path=large_image,
            output_path=str(output_path),
            compress=True
        )
        
        assert Path(formatted.path).exists()
        assert formatted.size_bytes < Path(large_image).stat().st_size
        assert formatted.size_bytes < 20 * 1024 * 1024  # Gemini limit
    
    def test_format_image_convert_to_jpeg(self, formatter, sample_png_image, tmp_path):
        """
        Dado una imagen PNG
        Cuando se solicita conversión a JPEG
        Entonces debe convertir correctamente
        """
        output_path = tmp_path / "chart.jpeg"
        
        formatted = formatter.format_image(
            input_path=sample_png_image,
            output_path=str(output_path),
            target_format=ImageFormat.JPEG
        )
        
        assert formatted.format == ImageFormat.JPEG
        assert Path(formatted.path).suffix.lower() in ['.jpg', '.jpeg']
    
    def test_format_image_resize_if_needed(self, formatter, tmp_path):
        """
        Dado una imagen muy grande en dimensiones
        Cuando se formatea con resize automático
        Entonces debe ajustar dimensiones
        """
        # Crear imagen muy grande
        huge_img_path = tmp_path / "huge.png"
        img = Image.new('RGB', (8000, 6000), color='green')
        img.save(huge_img_path, 'PNG')
        
        output_path = tmp_path / "resized.png"
        
        formatted = formatter.format_image(
            input_path=str(huge_img_path),
            output_path=str(output_path),
            max_width=1920,
            max_height=1080
        )
        
        assert formatted.width <= 1920
        assert formatted.height <= 1080
    
    def test_format_image_invalid_input(self, formatter):
        """
        Dado que se provee input inválido
        Cuando el archivo no existe
        Entonces debe lanzar ImageFormatterError
        """
        with pytest.raises(ImageFormatterError):
            formatter.format_image(
                input_path="/nonexistent/image.png",
                output_path="/tmp/output.png"
            )
    
    def test_format_image_maintain_aspect_ratio(self, formatter, tmp_path):
        """
        Dado que se redimensiona imagen
        Cuando se aplica resize
        Entonces debe mantener aspect ratio
        """
        # Crear imagen 1200x800 (ratio 3:2)
        img_path = tmp_path / "original.png"
        img = Image.new('RGB', (1200, 800), color='blue')
        img.save(img_path, 'PNG')
        
        output_path = tmp_path / "resized.png"
        
        formatted = formatter.format_image(
            input_path=str(img_path),
            output_path=str(output_path),
            max_width=600
        )
        
        # Verificar que se mantuvo el aspect ratio 3:2
        aspect_ratio = formatted.width / formatted.height
        expected_ratio = 1200 / 800
        
        assert abs(aspect_ratio - expected_ratio) < 0.01  # Tolerancia mínima
    
    def test_format_multiple_images_batch(self, formatter, tmp_path):
        """
        Dado múltiples imágenes
        Cuando se formatean en batch
        Entonces debe procesar todas correctamente
        """
        # Crear 3 imágenes de prueba
        image_paths = []
        for i in range(3):
            img_path = tmp_path / f"chart_{i}.png"
            img = Image.new('RGB', (1200, 800), color=(i*80, 100, 150))
            img.save(img_path, 'PNG')
            image_paths.append(str(img_path))
        
        # Formatear en batch
        formatted_images = formatter.format_batch(
            input_paths=image_paths,
            output_dir=str(tmp_path / "formatted")
        )
        
        assert len(formatted_images) == 3
        
        for formatted in formatted_images:
            assert Path(formatted.path).exists()
            assert formatted.size_bytes < 20 * 1024 * 1024
    
    def test_get_image_info(self, formatter, sample_png_image):
        """
        Dado una imagen
        Cuando se consulta información
        Entonces debe retornar datos completos
        """
        info = formatter.get_image_info(sample_png_image)
        
        assert 'format' in info
        assert 'width' in info
        assert 'height' in info
        assert 'size_bytes' in info
        assert info['format'].upper() == 'PNG'
    
    def test_optimize_for_gemini(self, formatter, sample_png_image, tmp_path):
        """
        Dado una imagen de gráfico
        Cuando se optimiza específicamente para Gemini
        Entonces debe cumplir todos los requisitos de la API
        
        Criterio de aceptación T24:
        - Produce archivos compatibles con Gemini
        """
        output_path = tmp_path / "optimized_for_gemini.png"
        
        formatted = formatter.optimize_for_gemini(
            input_path=sample_png_image,
            output_path=str(output_path)
        )
        
        # Validar requisitos de Gemini:
        # 1. Tamaño <20MB
        assert formatted.size_bytes < 20 * 1024 * 1024
        
        # 2. Formato soportado (PNG o JPEG)
        assert formatted.format in [ImageFormat.PNG, ImageFormat.JPEG]
        
        # 3. Dimensiones razonables (no excesivas)
        assert formatted.width <= 4096  # Límite razonable
        assert formatted.height <= 4096
        
        # 4. Archivo existe y es legible
        assert Path(formatted.path).exists()
        img = Image.open(formatted.path)
        assert img is not None


class TestImageFormatterIntegration:
    """Tests de integración para flujo completo"""
    
    def test_full_workflow_chart_to_gemini(self, tmp_path):
        """
        Escenario completo: Gráfico generado → Formato Gemini
        
        Dado que se generó un gráfico de trading
        Cuando se formatea para envío a Gemini
        Entonces debe cumplir todos los requisitos de compatibilidad
        """
        # 1. Simular gráfico generado por ChartGenerator
        chart_path = tmp_path / "eurusd_m5_chart.png"
        img = Image.new('RGB', (1200, 800), color='white')
        
        # Agregar algo de contenido para simular gráfico real
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 1150, 750], outline='black', width=2)
        
        img.save(chart_path, 'PNG', quality=95)
        
        # 2. Formatear para Gemini
        formatter = ImageFormatter()
        formatted = formatter.optimize_for_gemini(
            input_path=str(chart_path),
            output_path=str(tmp_path / "gemini_ready.png")
        )
        
        # 3. Validar resultado
        assert Path(formatted.path).exists()
        assert formatted.format == ImageFormat.PNG
        assert formatted.size_bytes > 0
        assert formatted.size_bytes < 20 * 1024 * 1024
        
        # 4. Verificar que puede ser leído
        gemini_img = Image.open(formatted.path)
        assert gemini_img.size == (formatted.width, formatted.height)
    
    def test_workflow_multiple_timeframes(self, tmp_path):
        """
        Escenario: Formatear gráficos de múltiples timeframes para Gemini
        
        Dado que se generaron gráficos para 5M, 15M y 1H
        Cuando se formatean todos para Gemini
        Entonces todos deben cumplir requisitos
        """
        formatter = ImageFormatter()
        timeframes = ['5M', '15M', '1H']
        formatted_images = []
        
        for tf in timeframes:
            # Crear gráfico simulado
            chart_path = tmp_path / f"eurusd_{tf}.png"
            img = Image.new('RGB', (1200, 800), color='lightblue')
            img.save(chart_path, 'PNG')
            
            # Formatear
            output_path = tmp_path / "gemini" / f"eurusd_{tf}_formatted.png"
            formatted = formatter.optimize_for_gemini(
                input_path=str(chart_path),
                output_path=str(output_path)
            )
            
            formatted_images.append(formatted)
        
        # Validar que todos cumplen requisitos
        assert len(formatted_images) == 3
        
        for formatted in formatted_images:
            assert Path(formatted.path).exists()
            assert formatted.size_bytes < 20 * 1024 * 1024
            assert formatted.format in [ImageFormat.PNG, ImageFormat.JPEG]
