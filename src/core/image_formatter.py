"""
ImageFormatter - Módulo para formatear imágenes para compatibilidad con Gemini.

Este módulo implementa la preparación y optimización de imágenes de gráficos
para cumplir con los requisitos de la API de Gemini (tamaño, formato, compresión).

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T24 - Generación de imágenes por timeframe con estilos consistentes
"""
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import logging

from PIL import Image
from src.core.logger import get_bot_logger


class ImageFormatterError(Exception):
    """Excepción personalizada para errores de formateo de imágenes."""
    pass


class ImageFormat(Enum):
    """
    Formatos de imagen soportados.
    
    Values:
        PNG: Formato PNG (sin pérdida)
        JPEG: Formato JPEG (con compresión)
    """
    PNG = 'png'
    JPEG = 'jpeg'
    
    @classmethod
    def from_string(cls, value: str) -> 'ImageFormat':
        """
        Convierte string a ImageFormat (case-insensitive).
        
        Args:
            value: Formato como string ('png', 'jpeg', 'jpg')
            
        Returns:
            ImageFormat enum correspondiente
            
        Raises:
            ValueError: Si el formato no es válido
        """
        value_lower = value.lower()
        
        # Manejar alias
        if value_lower in ['jpg', 'jpeg']:
            return cls.JPEG
        
        for fmt in cls:
            if fmt.value == value_lower:
                return fmt
        
        raise ValueError(f"Formato inválido: {value}. Válidos: png, jpeg, jpg")


@dataclass
class FormattedImage:
    """
    Información de imagen formateada.
    
    Attributes:
        path: Ruta del archivo formateado
        format: Formato de la imagen
        size_bytes: Tamaño del archivo en bytes
        width: Ancho de la imagen en píxeles
        height: Alto de la imagen en píxeles
    """
    path: str
    format: ImageFormat
    size_bytes: int
    width: int
    height: int
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte FormattedImage a diccionario.
        
        Returns:
            Diccionario con todas las propiedades
        """
        return {
            'path': self.path,
            'format': self.format.value,
            'size_bytes': self.size_bytes,
            'width': self.width,
            'height': self.height
        }


class ImageFormatter:
    """
    Formateador de imágenes para compatibilidad con Gemini.
    
    Prepara imágenes de gráficos para cumplir con los requisitos de la API:
    - Tamaño máximo: 20MB
    - Formatos: PNG o JPEG
    - Dimensiones razonables
    - Optimización de calidad/tamaño
    
    Ejemplo:
        ```python
        formatter = ImageFormatter(max_size_mb=20)
        
        formatted = formatter.optimize_for_gemini(
            input_path="chart.png",
            output_path="chart_gemini.png"
        )
        
        print(f"Tamaño: {formatted.size_bytes} bytes")
        ```
    """
    
    # Límites de Gemini
    DEFAULT_MAX_SIZE_MB = 20
    DEFAULT_MAX_WIDTH = 4096
    DEFAULT_MAX_HEIGHT = 4096
    
    # Formatos soportados por Gemini
    SUPPORTED_FORMATS = [ImageFormat.PNG, ImageFormat.JPEG]
    
    def __init__(self, max_size_mb: int = DEFAULT_MAX_SIZE_MB):
        """
        Inicializa el formateador de imágenes.
        
        Args:
            max_size_mb: Tamaño máximo en MB (por defecto 20MB para Gemini)
        """
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.logger = get_bot_logger(__name__)
        
        self.logger.info(
            f"ImageFormatter inicializado",
            extra={'max_size_mb': max_size_mb}
        )
    
    def validate_image(self, image_path: str) -> Tuple[bool, str]:
        """
        Valida si una imagen cumple requisitos de Gemini.
        
        Args:
            image_path: Ruta de la imagen a validar
            
        Returns:
            Tuple (is_valid, message) donde is_valid indica si es válida
            y message contiene detalles
        """
        try:
            # Verificar que existe
            path = Path(image_path)
            if not path.exists():
                return False, f"Archivo no encontrado: {image_path}"
            
            # Abrir imagen
            img = Image.open(image_path)
            
            # Validar formato
            img_format = ImageFormat.from_string(img.format)
            if img_format not in self.SUPPORTED_FORMATS:
                return False, f"Formato no soportado: {img.format}. Usar PNG o JPEG"
            
            # Validar tamaño de archivo
            file_size = path.stat().st_size
            if file_size > self.max_size_bytes:
                size_mb = file_size / (1024 * 1024)
                return False, f"Imagen muy grande: {size_mb:.2f}MB > {self.max_size_mb}MB"
            
            # Validar dimensiones
            width, height = img.size
            if width > self.DEFAULT_MAX_WIDTH or height > self.DEFAULT_MAX_HEIGHT:
                return False, f"Dimensiones muy grandes: {width}x{height}"
            
            return True, "Imagen compatible con Gemini"
            
        except Exception as e:
            return False, f"Error validando imagen: {str(e)}"
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        Obtiene información de una imagen.
        
        Args:
            image_path: Ruta de la imagen
            
        Returns:
            Diccionario con información (format, width, height, size_bytes)
            
        Raises:
            ImageFormatterError: Si hay error leyendo la imagen
        """
        try:
            path = Path(image_path)
            
            if not path.exists():
                raise ImageFormatterError(f"Archivo no encontrado: {image_path}")
            
            img = Image.open(image_path)
            width, height = img.size
            file_size = path.stat().st_size
            
            return {
                'format': img.format,
                'width': width,
                'height': height,
                'size_bytes': file_size,
                'mode': img.mode
            }
            
        except Exception as e:
            raise ImageFormatterError(f"Error obteniendo info de imagen: {str(e)}") from e
    
    def format_image(
        self,
        input_path: str,
        output_path: str,
        target_format: Optional[ImageFormat] = None,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        compress: bool = False,
        quality: int = 95
    ) -> FormattedImage:
        """
        Formatea una imagen con parámetros especificados.
        
        Args:
            input_path: Ruta de la imagen de entrada
            output_path: Ruta donde guardar imagen formateada
            target_format: Formato objetivo (None mantiene original)
            max_width: Ancho máximo (redimensiona si excede)
            max_height: Alto máximo (redimensiona si excede)
            compress: Si aplicar compresión adicional
            quality: Calidad de compresión (1-100)
            
        Returns:
            FormattedImage con información del resultado
            
        Raises:
            ImageFormatterError: Si hay error en el formateo
        """
        try:
            # Validar entrada
            input_file = Path(input_path)
            if not input_file.exists():
                raise ImageFormatterError(f"Archivo de entrada no encontrado: {input_path}")
            
            # Crear directorio de salida si no existe
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Abrir imagen
            img = Image.open(input_path)
            
            # Convertir a RGB si es necesario (para JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar si es necesario
            if max_width or max_height:
                img = self._resize_image(img, max_width, max_height)
            
            # Determinar formato de salida
            if target_format:
                save_format = target_format.value.upper()
                if save_format == 'JPEG':
                    save_format = 'JPEG'
            else:
                # Mantener formato original o usar PNG por defecto
                save_format = img.format if img.format else 'PNG'
            
            # Guardar imagen
            save_kwargs = {}
            if save_format == 'PNG':
                save_kwargs['optimize'] = compress
            elif save_format == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = compress
            
            img.save(output_path, save_format, **save_kwargs)
            
            # Obtener información de salida
            final_width, final_height = img.size
            final_size = Path(output_path).stat().st_size
            final_format = ImageFormat.from_string(save_format.lower())
            
            formatted = FormattedImage(
                path=str(output_path),
                format=final_format,
                size_bytes=final_size,
                width=final_width,
                height=final_height
            )
            
            self.logger.info(
                f"Imagen formateada exitosamente",
                extra={
                    'input_path': input_path,
                    'output_path': output_path,
                    'format': final_format.value,
                    'size_mb': final_size / (1024 * 1024)
                }
            )
            
            return formatted
            
        except Exception as e:
            self.logger.error(
                f"Error formateando imagen: {str(e)}",
                extra={'input_path': input_path, 'error': str(e)}
            )
            raise ImageFormatterError(f"Error formateando imagen: {str(e)}") from e
    
    def _resize_image(
        self,
        img: Image.Image,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None
    ) -> Image.Image:
        """
        Redimensiona imagen manteniendo aspect ratio.
        
        Args:
            img: Imagen a redimensionar
            max_width: Ancho máximo
            max_height: Alto máximo
            
        Returns:
            Imagen redimensionada
        """
        width, height = img.size
        
        # Calcular nuevo tamaño manteniendo aspect ratio
        if max_width and width > max_width:
            ratio = max_width / width
            new_width = max_width
            new_height = int(height * ratio)
        else:
            new_width = width
            new_height = height
        
        if max_height and new_height > max_height:
            ratio = max_height / new_height
            new_height = max_height
            new_width = int(new_width * ratio)
        
        if new_width != width or new_height != height:
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.logger.debug(
                f"Imagen redimensionada",
                extra={
                    'original_size': f'{width}x{height}',
                    'new_size': f'{new_width}x{new_height}'
                }
            )
        
        return img
    
    def optimize_for_gemini(
        self,
        input_path: str,
        output_path: str
    ) -> FormattedImage:
        """
        Optimiza imagen específicamente para Gemini API.
        
        Aplica configuración óptima para cumplir requisitos de Gemini:
        - Tamaño <20MB
        - Formato PNG o JPEG
        - Dimensiones razonables
        
        Args:
            input_path: Ruta de imagen de entrada
            output_path: Ruta de salida
            
        Returns:
            FormattedImage optimizada para Gemini
        """
        # Obtener info de entrada
        info = self.get_image_info(input_path)
        
        # Determinar si necesita compresión
        needs_compression = info['size_bytes'] > (self.max_size_bytes * 0.8)
        
        # Determinar si necesita resize
        needs_resize = (
            info['width'] > self.DEFAULT_MAX_WIDTH or
            info['height'] > self.DEFAULT_MAX_HEIGHT
        )
        
        # Formatear con configuración óptima
        formatted = self.format_image(
            input_path=input_path,
            output_path=output_path,
            target_format=ImageFormat.PNG,  # PNG por defecto (sin pérdida)
            max_width=self.DEFAULT_MAX_WIDTH if needs_resize else None,
            max_height=self.DEFAULT_MAX_HEIGHT if needs_resize else None,
            compress=needs_compression,
            quality=90
        )
        
        # Si aún es muy grande, convertir a JPEG
        if formatted.size_bytes > self.max_size_bytes:
            self.logger.warning(
                f"Imagen PNG muy grande, convirtiendo a JPEG",
                extra={'size_mb': formatted.size_bytes / (1024 * 1024)}
            )
            
            formatted = self.format_image(
                input_path=input_path,
                output_path=output_path.replace('.png', '.jpeg'),
                target_format=ImageFormat.JPEG,
                max_width=self.DEFAULT_MAX_WIDTH if needs_resize else None,
                max_height=self.DEFAULT_MAX_HEIGHT if needs_resize else None,
                compress=True,
                quality=85
            )
        
        return formatted
    
    def format_batch(
        self,
        input_paths: List[str],
        output_dir: str,
        **format_kwargs
    ) -> List[FormattedImage]:
        """
        Formatea múltiples imágenes en batch.
        
        Args:
            input_paths: Lista de rutas de entrada
            output_dir: Directorio de salida
            **format_kwargs: Parámetros adicionales para format_image
            
        Returns:
            Lista de FormattedImage
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        formatted_images = []
        
        for input_path in input_paths:
            input_file = Path(input_path)
            output_file = output_path / input_file.name
            
            try:
                formatted = self.format_image(
                    input_path=input_path,
                    output_path=str(output_file),
                    **format_kwargs
                )
                formatted_images.append(formatted)
                
            except Exception as e:
                self.logger.error(
                    f"Error formateando {input_path}: {str(e)}",
                    extra={'error': str(e)}
                )
        
        self.logger.info(
            f"Batch completado",
            extra={
                'total': len(input_paths),
                'successful': len(formatted_images)
            }
        )
        
        return formatted_images
