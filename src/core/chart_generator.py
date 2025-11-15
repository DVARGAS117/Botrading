"""
ChartGenerator - Módulo para generación de imágenes de gráficos por timeframe.

Este módulo implementa la generación de imágenes de velas japonesas (candlesticks)
con indicadores técnicos opcionales para bots visuales e híbridos. Genera gráficos
compatibles con la API de Gemini para análisis visual.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T24 - Generación de imágenes por timeframe con estilos consistentes
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime
import logging

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Backend sin interfaz gráfica
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplfinance as mpf

from src.core.mt5_data_extractor import OHLCVData, Timeframe
from src.core.logger import get_bot_logger


class ChartGeneratorError(Exception):
    """Excepción personalizada para errores de generación de gráficos."""
    pass


@dataclass
class ChartStyle:
    """
    Configuración de estilo visual para los gráficos.
    
    Attributes:
        width: Ancho de la imagen en píxeles
        height: Alto de la imagen en píxeles
        style_type: Estilo de gráfico mplfinance ('yahoo', 'charles', 'binance', 'mike')
        show_volume: Si mostrar panel de volumen
        show_grid: Si mostrar grilla
        title_fontsize: Tamaño de fuente del título
        dpi: Resolución de la imagen
    """
    width: int = 1200
    height: int = 800
    style_type: str = 'charles'
    show_volume: bool = True
    show_grid: bool = True
    title_fontsize: int = 12
    dpi: int = 100
    
    def __post_init__(self):
        """Validar parámetros después de inicialización"""
        valid_styles = ['yahoo', 'charles', 'binance', 'mike', 'nightclouds', 'sas', 'starsandstripes', 'brasil', 'ibd']
        if self.style_type not in valid_styles:
            raise ValueError(
                f"style_type inválido: {self.style_type}. "
                f"Válidos: {', '.join(valid_styles)}"
            )
        
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width y height deben ser positivos")
        
        if self.dpi <= 0:
            raise ValueError("dpi debe ser positivo")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estilo a diccionario"""
        return asdict(self)


@dataclass
class IndicatorStyle:
    """
    Configuración de indicadores técnicos a mostrar en el gráfico.
    
    Attributes:
        show_emas: Si mostrar medias móviles exponenciales
        ema_periods: Períodos de las EMAs a calcular
        ema_colors: Colores para cada EMA
        show_rsi: Si mostrar RSI en panel separado
        rsi_period: Período del RSI
        show_macd: Si mostrar MACD en panel separado
        macd_params: Parámetros MACD (fast, slow, signal)
    """
    show_emas: bool = False
    ema_periods: List[int] = field(default_factory=lambda: [20, 50])
    ema_colors: List[str] = field(default_factory=lambda: ['blue', 'red'])
    show_rsi: bool = False
    rsi_period: int = 14
    show_macd: bool = False
    macd_params: Tuple[int, int, int] = (12, 26, 9)
    
    def __post_init__(self):
        """Validar parámetros de indicadores"""
        if self.show_emas:
            if not self.ema_periods or len(self.ema_periods) == 0:
                raise ValueError("ema_periods no puede estar vacío si show_emas=True")
            
            if len(self.ema_colors) < len(self.ema_periods):
                # Completar con colores por defecto
                default_colors = ['blue', 'red', 'green', 'orange', 'purple']
                while len(self.ema_colors) < len(self.ema_periods):
                    idx = len(self.ema_colors)
                    self.ema_colors.append(default_colors[idx % len(default_colors)])
        
        if self.rsi_period <= 0:
            raise ValueError("rsi_period debe ser positivo")


@dataclass
class ChartConfig:
    """
    Configuración completa para generación de gráficos.
    
    Attributes:
        chart_style: Estilo visual del gráfico
        indicator_style: Configuración de indicadores
        output_dir: Directorio donde guardar las imágenes
    """
    chart_style: ChartStyle
    indicator_style: IndicatorStyle
    output_dir: str
    
    def __post_init__(self):
        """Validar configuración y crear directorio si no existe"""
        if not self.output_dir or self.output_dir.strip() == "":
            raise ChartGeneratorError("output_dir no puede estar vacío")
        
        # Crear directorio si no existe
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)


class ChartGenerator:
    """
    Generador de gráficos de velas japonesas con indicadores técnicos.
    
    Genera imágenes PNG de gráficos de trading para análisis visual por IA,
    con soporte para múltiples timeframes y estilos configurables.
    
    Ejemplo:
        ```python
        # Configurar generador
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
        ```
    """
    
    def __init__(self, config: ChartConfig):
        """
        Inicializa el generador de gráficos.
        
        Args:
            config: Configuración del generador
            
        Raises:
            ChartGeneratorError: Si la configuración es inválida
        """
        if config is None:
            raise ChartGeneratorError("config no puede ser None")
        
        self.config = config
        self.logger = get_bot_logger(__name__)
        
        self.logger.info(
            f"ChartGenerator inicializado",
            extra={
                'output_dir': config.output_dir,
                'style': config.chart_style.style_type,
                'show_emas': config.indicator_style.show_emas
            }
        )
    
    def generate_chart(
        self,
        ohlcv_data: OHLCVData,
        title: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Genera un gráfico de velas japonesas con los datos proporcionados.
        
        Args:
            ohlcv_data: Datos OHLCV para el gráfico
            title: Título del gráfico
            filename: Nombre del archivo (opcional, se genera automático si None)
            
        Returns:
            str: Ruta completa del archivo PNG generado
            
        Raises:
            ChartGeneratorError: Si hay error en la generación
        """
        try:
            # Validar datos
            self._validate_ohlcv_data(ohlcv_data)
            
            # Preparar DataFrame para mplfinance
            df = self._prepare_dataframe(ohlcv_data)
            
            # Generar nombre de archivo si no se proporciona
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{ohlcv_data.symbol}_{ohlcv_data.timeframe.name}_{timestamp}.png"
            
            # Ruta completa del archivo
            output_path = Path(self.config.output_dir) / filename
            
            # Configurar plots adicionales (EMAs, etc)
            addplot_list = self._build_addplots(df)
            
            # Configurar estilo mplfinance
            style = mpf.make_mpf_style(base_mpf_style=self.config.chart_style.style_type)
            
            # Calcular figsize
            figsize = (
                self.config.chart_style.width / self.config.chart_style.dpi,
                self.config.chart_style.height / self.config.chart_style.dpi
            )
            
            # Generar gráfico
            plot_kwargs = {
                'type': 'candle',
                'style': style,
                'title': title,
                'ylabel': 'Price',
                'volume': self.config.chart_style.show_volume,
                'figsize': figsize,
                'savefig': dict(
                    fname=str(output_path),
                    dpi=self.config.chart_style.dpi,
                    bbox_inches='tight'
                ),
                'returnfig': False,
                'show_nontrading': False,
                'scale_padding': {'left': 0.1, 'right': 0.3, 'top': 0.5, 'bottom': 0.5}
            }
            
            # Solo agregar addplot si hay indicadores
            if addplot_list:
                plot_kwargs['addplot'] = addplot_list
            
            mpf.plot(df, **plot_kwargs)
            
            # Cerrar todas las figuras para liberar memoria
            plt.close('all')
            
            self.logger.info(
                f"Gráfico generado exitosamente",
                extra={
                    'symbol': ohlcv_data.symbol,
                    'timeframe': ohlcv_data.timeframe.name,
                    'output_path': str(output_path),
                    'file_size': output_path.stat().st_size
                }
            )
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(
                f"Error generando gráfico: {str(e)}",
                extra={
                    'symbol': ohlcv_data.symbol if ohlcv_data else 'N/A',
                    'error': str(e)
                }
            )
            raise ChartGeneratorError(f"Error generando gráfico: {str(e)}") from e
    
    def _validate_ohlcv_data(self, ohlcv_data: OHLCVData) -> None:
        """
        Valida que los datos OHLCV sean correctos para generar gráfico.
        
        Args:
            ohlcv_data: Datos a validar
            
        Raises:
            ChartGeneratorError: Si los datos son inválidos
        """
        if ohlcv_data is None:
            raise ChartGeneratorError("ohlcv_data no puede ser None")
        
        if ohlcv_data.data is None or ohlcv_data.data.empty:
            raise ChartGeneratorError("ohlcv_data.data no puede estar vacío")
        
        # Verificar columnas requeridas
        required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in ohlcv_data.data.columns]
        
        if missing_columns:
            raise ChartGeneratorError(
                f"Faltan columnas requeridas en datos OHLCV: {', '.join(missing_columns)}"
            )
        
        # Verificar que haya al menos algunas velas
        if len(ohlcv_data.data) < 2:
            raise ChartGeneratorError(
                f"Se requieren al menos 2 velas para generar gráfico, recibidas: {len(ohlcv_data.data)}"
            )
    
    def _prepare_dataframe(self, ohlcv_data: OHLCVData) -> pd.DataFrame:
        """
        Prepara DataFrame en el formato requerido por mplfinance.
        
        Args:
            ohlcv_data: Datos OHLCV originales
            
        Returns:
            DataFrame con índice datetime y columnas OHLCV
        """
        df = ohlcv_data.data.copy()
        
        # Asegurar que 'time' sea datetime
        if not pd.api.types.is_datetime64_any_dtype(df['time']):
            df['time'] = pd.to_datetime(df['time'])
        
        # Establecer 'time' como índice
        df.set_index('time', inplace=True)
        
        # Renombrar columnas al formato esperado por mplfinance (capitalizado)
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        return df
    
    def _build_addplots(self, df: pd.DataFrame) -> Optional[List]:
        """
        Construye lista de plots adicionales (indicadores) para mplfinance.
        
        Args:
            df: DataFrame con datos OHLCV
            
        Returns:
            Lista de objetos make_addplot o None si no hay indicadores
        """
        addplot_list = []
        
        # Agregar EMAs si están habilitadas
        if self.config.indicator_style.show_emas:
            for i, period in enumerate(self.config.indicator_style.ema_periods):
                ema = df['Close'].ewm(span=period, adjust=False).mean()
                color = self.config.indicator_style.ema_colors[i]
                
                addplot_list.append(
                    mpf.make_addplot(ema, color=color, width=1.5, label=f'EMA{period}')
                )
        
        # RSI y MACD requieren paneles separados
        # Por simplicidad en v1, solo soportamos EMAs superpuestas
        # TODO: Agregar soporte para RSI y MACD en paneles separados
        
        return addplot_list if addplot_list else None
    
    def cleanup_old_charts(self, keep_last: int = 10) -> int:
        """
        Limpia gráficos antiguos del directorio de salida.
        
        Args:
            keep_last: Número de gráficos más recientes a mantener
            
        Returns:
            int: Número de archivos eliminados
        """
        try:
            output_dir = Path(self.config.output_dir)
            
            # Obtener todos los archivos PNG ordenados por fecha de modificación
            chart_files = sorted(
                output_dir.glob("*.png"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # Eliminar archivos antiguos
            files_to_delete = chart_files[keep_last:]
            deleted_count = 0
            
            for file_path in files_to_delete:
                file_path.unlink()
                deleted_count += 1
            
            if deleted_count > 0:
                self.logger.info(
                    f"Limpieza de gráficos completada",
                    extra={
                        'deleted_count': deleted_count,
                        'kept_count': keep_last
                    }
                )
            
            return deleted_count
            
        except Exception as e:
            self.logger.warning(
                f"Error en limpieza de gráficos: {str(e)}",
                extra={'error': str(e)}
            )
            return 0
