"""
Módulo de clases base para todos los bots.

Este módulo define las clases base que todos los bots deben heredar
para mantener consistencia y reutilizar código común.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.core.bot_instance import BotInstance, BotConfig


class BotType(Enum):
    """Tipos de bots disponibles"""
    NUMERICO = "numerico"
    VISUAL = "visual"
    HIBRIDO = "hibrido"


@dataclass
class TradingDecision:
    """
    Decisión de trading tomada por la IA.
    
    Attributes:
        action: OPERAR, NO_OPERAR, MANTENER, ACTUALIZAR, CERRAR
        direction: BUY o SELL (si aplica)
        entry_price: Precio de entrada sugerido
        stop_loss: Precio de stop loss
        take_profit: Precio de take profit
        risk_percentage: Porcentaje de riesgo (1-5%)
        reasoning: Explicación de la decisión
    """
    action: str
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_percentage: Optional[float] = None
    reasoning: Optional[str] = None


class BaseBot(ABC):
    """
    Clase base abstracta para todos los bots de trading.
    
    Define la interfaz común que todos los bots deben implementar.
    
    Attributes:
        bot_id: ID único del bot (1-5)
        bot_name: Nombre descriptivo del bot
        bot_type: Tipo de bot (numerico, visual, hibrido)
        instance: Instancia de BotInstance para gestión de estado
    """
    
    def __init__(
        self,
        bot_id: int,
        bot_name: str,
        bot_type: BotType,
        config: Dict[str, Any]
    ):
        """
        Inicializa el bot base.
        
        Args:
            bot_id: ID único del bot (1-5)
            bot_name: Nombre descriptivo
            bot_type: Tipo de bot (enum)
            config: Configuración del bot
        """
        self.bot_id = bot_id
        self.bot_name = bot_name
        self.bot_type = bot_type
        self.config = config
        
        # Crear configuración de BotInstance
        bot_config = BotConfig(
            bot_id=bot_id,
            bot_name=bot_name,
            enabled=config.get("enabled", True),
            schedule_config=config.get("schedule", {}),
            mt5_config=config.get("mt5", {}),
            cycle_config=config.get("cycle", {})
        )
        
        # Crear instancia del bot
        self.instance = BotInstance(bot_config)
    
    @abstractmethod
    def prepare_data_for_evaluation(
        self,
        symbol: str,
        timeframes: List[str]
    ) -> Dict[str, Any]:
        """
        Prepara los datos necesarios para evaluación inicial.
        
        Args:
            symbol: Símbolo a analizar (ej: "EURUSD")
            timeframes: Lista de timeframes (ej: ["5M", "15M", "1H"])
        
        Returns:
            Diccionario con datos preparados según tipo de bot
        """
        pass
    
    @abstractmethod
    def prepare_data_for_reevaluation(
        self,
        symbol: str,
        position_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepara los datos necesarios para reevaluación de posición abierta.
        
        Args:
            symbol: Símbolo de la posición
            position_data: Datos de la posición abierta
        
        Returns:
            Diccionario con datos preparados para reevaluación
        """
        pass
    
    @abstractmethod
    def build_prompt(
        self,
        prompt_type: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Construye el prompt para enviar a la IA.
        
        Args:
            prompt_type: Tipo de prompt ("evaluacion" o "reevaluacion")
            data: Datos preparados
        
        Returns:
            Prompt formateado como string
        """
        pass
    
    def start(self):
        """Inicia el bot"""
        self.instance.start()
    
    def stop(self):
        """Detiene el bot"""
        self.instance.stop()
    
    def get_status(self) -> str:
        """
        Obtiene el estado actual del bot.
        
        Returns:
            Estado del bot como string
        """
        return self.instance.get_status().value
    
    def execute_trading_cycle(self):
        """
        Ejecuta un ciclo completo de trading.
        
        Este método coordina:
        1. Validación de horario
        2. Iteración por activos
        3. Consulta a IA
        4. Apertura de operaciones
        5. Reevaluación de posiciones
        """
        # Implementación base que puede ser sobrescrita
        pass


class BaseStrategy(ABC):
    """
    Clase base para estrategias de trading.
    
    Define la interfaz para las diferentes estrategias que pueden
    implementar los bots.
    """
    
    @abstractmethod
    def should_open_position(
        self,
        decision: TradingDecision,
        market_data: Dict[str, Any]
    ) -> bool:
        """
        Determina si se debe abrir una posición basado en la decisión de IA.
        
        Args:
            decision: Decisión tomada por la IA
            market_data: Datos actuales del mercado
        
        Returns:
            True si se debe abrir posición, False en caso contrario
        """
        pass
    
    @abstractmethod
    def calculate_position_size(
        self,
        risk_percentage: float,
        account_balance: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """
        Calcula el tamaño de la posición basado en riesgo.
        
        Args:
            risk_percentage: Porcentaje de riesgo (1-5%)
            account_balance: Balance de la cuenta
            entry_price: Precio de entrada
            stop_loss: Precio de stop loss
        
        Returns:
            Tamaño del lote
        """
        pass
