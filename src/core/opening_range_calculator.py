"""
OpeningRangeCalculator - Cálculo de Opening Range de sesión.

Este módulo implementa el cálculo del Opening Range (OR), definido como
el rango de precio en los primeros 15-30 minutos de la sesión europea (08:00-08:30 GMT).

El OR es crítico para la metodología VWAP intradía ya que:
- Define niveles clave de soporte/resistencia
- Identifica breakouts alcistas o bajistas
- Ayuda a determinar el bias direccional del día

Autor: Sistema Botrading
Fecha: 2025-11-17
Ticket: VWAP Methodology - Opening Range Calculator
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum
import pandas as pd
from datetime import time


class BreakoutStatus(Enum):
    """Estado del precio respecto al Opening Range"""
    ABOVE = "above"  # Precio por encima de OR high (breakout alcista)
    BELOW = "below"  # Precio por debajo de OR low (breakout bajista)
    INSIDE = "inside"  # Precio dentro del rango OR


@dataclass
class OpeningRangeData:
    """
    Datos del Opening Range calculados.
    
    Attributes:
        or_high: Máximo del rango de apertura
        or_low: Mínimo del rango de apertura
        or_range: Tamaño del rango (or_high - or_low)
        or_midpoint: Punto medio del rango
        current_price: Precio actual (último close)
        breakout_status: Estado del precio respecto al OR
        distance_from_or_high: Distancia del precio actual al OR high
        distance_from_or_low: Distancia del precio actual al OR low
        session_start: Hora de inicio de sesión
        or_duration_minutes: Duración del OR en minutos
    """
    or_high: float
    or_low: float
    or_range: float
    or_midpoint: float
    current_price: float
    breakout_status: BreakoutStatus
    distance_from_or_high: float
    distance_from_or_low: float
    session_start: time
    or_duration_minutes: int


class OpeningRangeCalculator:
    """
    Calculador de Opening Range para sesión europea.
    
    El Opening Range se calcula sobre los primeros N minutos de la sesión,
    típicamente 15-30 minutos. Para EURUSD, la sesión europea comienza
    a las 08:00 GMT.
    """
    
    def __init__(self,
                 session_start_hour: int = 8,
                 session_start_minute: int = 0,
                 or_duration_minutes: int = 30):
        """
        Inicializa el calculador de Opening Range.
        
        Args:
            session_start_hour: Hora de inicio de sesión (default: 8 = 08:00 GMT)
            session_start_minute: Minuto de inicio (default: 0)
            or_duration_minutes: Duración del OR en minutos (default: 30)
        """
        self.session_start_hour = session_start_hour
        self.session_start_minute = session_start_minute
        self.or_duration_minutes = or_duration_minutes
        
        self.session_start = time(session_start_hour, session_start_minute)
    
    def calculate_opening_range(self, data: pd.DataFrame) -> OpeningRangeData:
        """
        Calcula el Opening Range para los datos proporcionados.
        
        Args:
            data: DataFrame con columnas 'time', 'high', 'low', 'close'
        
        Returns:
            OpeningRangeData con todos los valores calculados
        
        Raises:
            ValueError: Si no hay datos en la ventana de OR
        """
        # Asegurar que 'time' es datetime
        if not pd.api.types.is_datetime64_any_dtype(data['time']):
            data = data.copy()
            data['time'] = pd.to_datetime(data['time'])
        
        # Filtrar datos dentro de la ventana de OR
        or_window = self._get_or_window(data)
        
        if or_window.empty:
            raise ValueError(
                f"No se encontraron datos en la ventana de Opening Range "
                f"({self.session_start_hour:02d}:{self.session_start_minute:02d} - "
                f"{self.or_duration_minutes} minutos)"
            )
        
        # Calcular OR high y OR low
        or_high = or_window['high'].max()
        or_low = or_window['low'].min()
        
        # Calcular métricas derivadas
        or_range = or_high - or_low
        or_midpoint = (or_high + or_low) / 2
        
        # Precio actual (último close disponible)
        current_price = data['close'].iloc[-1]
        
        # Determinar estado de breakout
        breakout_status = self._determine_breakout_status(
            current_price, or_high, or_low
        )
        
        # Distancias
        distance_from_or_high = current_price - or_high
        distance_from_or_low = current_price - or_low
        
        return OpeningRangeData(
            or_high=or_high,
            or_low=or_low,
            or_range=or_range,
            or_midpoint=or_midpoint,
            current_price=current_price,
            breakout_status=breakout_status,
            distance_from_or_high=distance_from_or_high,
            distance_from_or_low=distance_from_or_low,
            session_start=self.session_start,
            or_duration_minutes=self.or_duration_minutes
        )
    
    def _get_or_window(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Filtra el DataFrame para obtener solo la ventana de OR.
        
        Args:
            data: DataFrame con columna 'time'
        
        Returns:
            DataFrame filtrado con datos de OR window
        """
        # Calcular tiempo de fin de OR
        start_minutes = self.session_start_hour * 60 + self.session_start_minute
        end_minutes = start_minutes + self.or_duration_minutes
        
        end_hour = end_minutes // 60
        end_minute = end_minutes % 60
        
        # Filtrar por tiempo (comparando solo hora y minuto, ignorando fecha)
        mask = (
            (data['time'].dt.hour > self.session_start_hour) |
            ((data['time'].dt.hour == self.session_start_hour) & 
             (data['time'].dt.minute >= self.session_start_minute))
        ) & (
            (data['time'].dt.hour < end_hour) |
            ((data['time'].dt.hour == end_hour) & 
             (data['time'].dt.minute < end_minute))
        )
        
        return data[mask]
    
    def _determine_breakout_status(self,
                                   current_price: float,
                                   or_high: float,
                                   or_low: float) -> BreakoutStatus:
        """
        Determina el estado del precio respecto al OR.
        
        Args:
            current_price: Precio actual
            or_high: OR high
            or_low: OR low
        
        Returns:
            BreakoutStatus indicando posición del precio
        """
        if current_price > or_high:
            return BreakoutStatus.ABOVE
        elif current_price < or_low:
            return BreakoutStatus.BELOW
        else:
            return BreakoutStatus.INSIDE
