"""
PromptBuilder - T10
Construcción de prompts específicos por tipo de bot para consultas a IA

Este módulo permite construir prompts estructurados y configurables para
diferentes tipos de bots (numéricos, visuales, híbridos) y tipos de consulta
(evaluación inicial, reevaluación).

Características:
- Plantillas configurables por tipo de bot y prompt
- Soporte para datos numéricos (indicadores)
- Soporte para datos visuales (imágenes de gráficos)
- Soporte para datos híbridos (numéricos + visuales)
- Múltiples timeframes (5M, 15M, 1H)
- Variables personalizadas
- Validación de datos
- Instrucciones de formato JSON

Tickets relacionados: T10, T23 (Indicadores), T24 (Imágenes)

Author: Botrading Team
Date: 2025-11-13
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json

from src.core.vwap_prompt_builder import VWAPPromptBuilder


class PromptBuilderError(Exception):
    """Excepción personalizada para errores de construcción de prompts"""
    pass


class BotType(Enum):
    """
    Tipos de bots soportados
    
    Values:
        NUMERICO: Bot que usa solo datos numéricos (indicadores)
        VISUAL: Bot que usa solo imágenes de gráficos
        HIBRIDO: Bot que combina datos numéricos e imágenes
    """
    NUMERICO = "numerico"
    VISUAL = "visual"
    HIBRIDO = "hibrido"
    
    @classmethod
    def from_string(cls, value: str) -> 'BotType':
        """
        Convierte string a BotType (case-insensitive)
        
        Args:
            value: Tipo de bot como string
            
        Returns:
            BotType enum correspondiente
            
        Raises:
            ValueError: Si el tipo no es válido
        """
        value_lower = value.lower()
        for bot_type in cls:
            if bot_type.value == value_lower:
                return bot_type
        raise ValueError(f"Tipo de bot inválido: {value}. Válidos: {[b.value for b in cls]}")


class PromptType(Enum):
    """
    Tipos de prompts soportados
    
    Values:
        EVALUACION: Evaluación inicial (¿debo operar?)
        REEVALUACION: Reevaluación de posición abierta (¿mantener/actualizar/cerrar?)
    """
    EVALUACION = "evaluacion"
    REEVALUACION = "reevaluacion"
    
    @classmethod
    def from_string(cls, value: str) -> 'PromptType':
        """
        Convierte string a PromptType (case-insensitive)
        
        Args:
            value: Tipo de prompt como string
            
        Returns:
            PromptType enum correspondiente
            
        Raises:
            ValueError: Si el tipo no es válido
        """
        value_lower = value.lower()
        for prompt_type in cls:
            if prompt_type.value == value_lower:
                return prompt_type
        raise ValueError(f"Tipo de prompt inválido: {value}")


@dataclass
class PromptData:
    """
    Datos para construir un prompt
    
    Atributos:
        symbol: Símbolo del activo (ej: "EURUSD")
        timeframe: Timeframe (ej: "5M", "15M", "1H")
        current_price: Precio actual del activo
        indicators: Diccionario de indicadores técnicos (para bots numéricos/híbridos)
        image_paths: Lista de rutas a imágenes de gráficos (para bots visuales/híbridos)
        position_data: Datos de posición abierta (para reevaluación)
        timestamp: Timestamp de los datos
        custom_fields: Campos adicionales personalizados
    """
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    current_price: Optional[float] = None
    indicators: Optional[Dict[str, float]] = None
    image_paths: Optional[List[str]] = None
    position_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validación y defaults después de inicialización"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario"""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                result[key] = value
        return result


class PromptTemplate:
    """
    Plantilla de prompt configurable
    
    Una plantilla define cómo construir un prompt para un tipo específico
    de bot y tipo de consulta.
    """
    
    def __init__(
        self,
        name: str,
        bot_type: BotType,
        prompt_type: PromptType,
        template_text: str,
        description: Optional[str] = None
    ):
        """
        Inicializa la plantilla
        
        Args:
            name: Nombre identificador de la plantilla
            bot_type: Tipo de bot para el que aplica
            prompt_type: Tipo de prompt (evaluación/reevaluación)
            template_text: Texto de la plantilla con variables {variable}
            description: Descripción opcional de la plantilla
        """
        self.name = name
        self.bot_type = bot_type
        self.prompt_type = prompt_type
        self.template_text = template_text
        self.description = description
    
    def render(
        self,
        data: PromptData,
        custom_vars: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Renderiza la plantilla con los datos proporcionados
        
        Args:
            data: Datos para renderizar
            custom_vars: Variables personalizadas adicionales
            
        Returns:
            Texto del prompt renderizado
            
        Raises:
            PromptBuilderError: Si falta una variable requerida
        """
        # Preparar variables para renderizado
        variables = data.to_dict()
        
        # Agregar variables personalizadas
        if custom_vars:
            variables.update(custom_vars)
        
        # Renderizar template
        try:
            rendered = self.template_text.format(**variables)
            return rendered
        except KeyError as e:
            raise PromptBuilderError(
                f"Variable faltante en template '{self.name}': {str(e)}"
            )
        except Exception as e:
            raise PromptBuilderError(
                f"Error al renderizar template '{self.name}': {str(e)}"
            )


class PromptBuilder:
    """
    Constructor de prompts específicos por tipo de bot
    
    Gestiona plantillas y construye prompts estructurados para consultas
    a la IA, adaptándose al tipo de bot y tipo de consulta.
    
    Ejemplo:
        ```python
        builder = PromptBuilder()
        
        # Datos numéricos
        data = PromptData(
            symbol="EURUSD",
            timeframe="5M",
            indicators={"rsi": 65.0, "ema_20": 1.2345},
            current_price=1.2350
        )
        
        # Construir prompt
        prompt = builder.build_prompt(
            bot_type=BotType.NUMERICO,
            prompt_type=PromptType.EVALUACION,
            data=data
        )
        ```
    """
    
    # Plantillas por defecto
    DEFAULT_TEMPLATES = {
        "numerico_evaluacion": """Analiza los siguientes datos de mercado y decide si operar.

SÍMBOLO: {symbol}
TIMEFRAME: {timeframe}
PRECIO ACTUAL: {current_price}

INDICADORES TÉCNICOS:
{indicators_formatted}

RESPONDE ÚNICAMENTE CON UN JSON EN EL FORMATO ESPECIFICADO.""",
        
        "visual_evaluacion": """Analiza las siguientes gráficas de {symbol} en timeframe {timeframe}.

Las imágenes muestran el comportamiento del precio y pueden incluir indicadores técnicos.

PRECIO ACTUAL: {current_price}

Analiza las tendencias, patrones y señales visuales.

RESPONDE ÚNICAMENTE CON UN JSON EN EL FORMATO ESPECIFICADO.""",
        
        "hibrido_evaluacion": """Analiza los siguientes datos de mercado combinando información numérica y visual.

SÍMBOLO: {symbol}
TIMEFRAME: {timeframe}
PRECIO ACTUAL: {current_price}

INDICADORES TÉCNICOS:
{indicators_formatted}

Además, analiza las gráficas adjuntas que complementan los datos numéricos.

RESPONDE ÚNICAMENTE CON UN JSON EN EL FORMATO ESPECIFICADO.""",
        
        "numerico_reevaluacion": """Reevalúa la siguiente posición abierta en {symbol}.

DATOS ACTUALES:
- Timeframe: {timeframe}
- Precio Actual: {current_price}

INDICADORES ACTUALES:
{indicators_formatted}

DATOS DE LA POSICIÓN:
{position_data_formatted}

Decide si MANTENER, ACTUALIZAR (SL/TP) o CERRAR la posición.

RESPONDE ÚNICAMENTE CON UN JSON EN EL FORMATO ESPECIFICADO.""",
        
        "visual_reevaluacion": """Reevalúa la siguiente posición abierta en {symbol} analizando las gráficas actuales.

DATOS DE LA POSICIÓN:
{position_data_formatted}

PRECIO ACTUAL: {current_price}

Analiza las gráficas adjuntas para determinar si la posición debe mantenerse, actualizarse o cerrarse.

RESPONDE ÚNICAMENTE CON UN JSON EN EL FORMATO ESPECIFICADO.""",
        
        "hibrido_reevaluacion": """Reevalúa la siguiente posición abierta en {symbol} usando datos numéricos y visuales.

DATOS ACTUALES:
- Precio Actual: {current_price}

INDICADORES ACTUALES:
{indicators_formatted}

DATOS DE LA POSICIÓN:
{position_data_formatted}

Además, analiza las gráficas adjuntas.

RESPONDE ÚNICAMENTE CON UN JSON EN EL FORMATO ESPECIFICADO."""
    }
    
    JSON_FORMAT_INSTRUCTIONS = """
=== FORMATO DE RESPUESTA OBLIGATORIO ===

Debes responder ÚNICAMENTE con un objeto JSON válido.
NO incluyas texto adicional antes o después del JSON.
NO uses markdown ni bloques de código.
Solo el JSON puro.

Para EVALUACIÓN INICIAL, usa uno de estos formatos:

1. Si NO hay señal clara:
{
  "accion": "NO_OPERAR",
  "razonamiento": "explicación"
}

2. Si hay señal para operar:
{
  "accion": "OPERAR",
  "direccion": "BUY" o "SELL",
  "tipo_orden": "MARKET" o "LIMIT",
  "precio_entrada": número (solo si tipo_orden es LIMIT),
  "stop_loss": número,
  "take_profit": número,
  "riesgo_porcentaje": número entre 1.0 y 5.0,
  "razonamiento": "explicación"
}

REGLAS CRÍTICAS:
- Todos los precios deben ser NÚMEROS, NO strings
- Para BUY: stop_loss < precio_entrada < take_profit
- Para SELL: stop_loss > precio_entrada > take_profit
- riesgo_porcentaje entre 1.0 y 5.0
- Palabras en MAYÚSCULAS: OPERAR, NO_OPERAR, BUY, SELL, MARKET, LIMIT

Para REEVALUACIÓN, usa uno de estos formatos:

1. Si todo va bien:
{
  "accion": "MANTENER",
  "razonamiento": "explicación"
}

2. Si quieres modificar SL/TP:
{
  "accion": "ACTUALIZAR",
  "nuevo_stop_loss": número (opcional),
  "nuevo_take_profit": número (opcional),
  "razonamiento": "explicación"
}

3. Si detectas señales de salida:
{
  "accion": "CERRAR",
  "razonamiento": "explicación"
}
"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el constructor de prompts
        
        Args:
            config: Configuración con plantillas personalizadas
        """
        self.logger = logging.getLogger(__name__)
        self.templates: List[PromptTemplate] = []
        
        # Cargar configuración
        if config is None:
            config = {}
        
        self._load_config(config)
        
        # Si no hay templates configurados, cargar defaults
        if not self.templates:
            self._load_default_templates()
    
    def _load_config(self, config: Dict[str, Any]) -> None:
        """Carga plantillas desde configuración"""
        templates_config = config.get("prompt_templates", {})
        
        for name, template_data in templates_config.items():
            try:
                bot_type = BotType.from_string(template_data["bot_type"])
                prompt_type = PromptType.from_string(template_data["prompt_type"])
                template_text = template_data["template"]
                description = template_data.get("description")
                
                template = PromptTemplate(
                    name=name,
                    bot_type=bot_type,
                    prompt_type=prompt_type,
                    template_text=template_text,
                    description=description
                )
                
                self.templates.append(template)
                
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Error cargando template '{name}': {str(e)}")
    
    def _load_default_templates(self) -> None:
        """Carga plantillas por defecto"""
        templates_config = {
            "numerico_evaluacion": {
                "bot_type": "numerico",
                "prompt_type": "evaluacion",
                "template": self.DEFAULT_TEMPLATES["numerico_evaluacion"]
            },
            "visual_evaluacion": {
                "bot_type": "visual",
                "prompt_type": "evaluacion",
                "template": self.DEFAULT_TEMPLATES["visual_evaluacion"]
            },
            "hibrido_evaluacion": {
                "bot_type": "hibrido",
                "prompt_type": "evaluacion",
                "template": self.DEFAULT_TEMPLATES["hibrido_evaluacion"]
            },
            "numerico_reevaluacion": {
                "bot_type": "numerico",
                "prompt_type": "reevaluacion",
                "template": self.DEFAULT_TEMPLATES["numerico_reevaluacion"]
            },
            "visual_reevaluacion": {
                "bot_type": "visual",
                "prompt_type": "reevaluacion",
                "template": self.DEFAULT_TEMPLATES["visual_reevaluacion"]
            },
            "hibrido_reevaluacion": {
                "bot_type": "hibrido",
                "prompt_type": "reevaluacion",
                "template": self.DEFAULT_TEMPLATES["hibrido_reevaluacion"]
            }
        }
        
        self._load_config({"prompt_templates": templates_config})
    
    def get_template(
        self,
        bot_type: BotType,
        prompt_type: PromptType
    ) -> PromptTemplate:
        """
        Obtiene la plantilla para un tipo de bot y prompt
        
        Args:
            bot_type: Tipo de bot
            prompt_type: Tipo de prompt
            
        Returns:
            PromptTemplate correspondiente
            
        Raises:
            PromptBuilderError: Si no se encuentra la plantilla
        """
        for template in self.templates:
            if template.bot_type == bot_type and template.prompt_type == prompt_type:
                return template
        
        raise PromptBuilderError(
            f"No se encontró template para bot_type={bot_type.value}, "
            f"prompt_type={prompt_type.value}"
        )
    
    def add_template(
        self,
        name: str,
        bot_type: BotType,
        prompt_type: PromptType,
        template_text: str,
        description: Optional[str] = None
    ) -> None:
        """
        Agrega o reemplaza una plantilla
        
        Args:
            name: Nombre de la plantilla
            bot_type: Tipo de bot
            prompt_type: Tipo de prompt
            template_text: Texto de la plantilla
            description: Descripción opcional
        """
        # Remover plantilla existente con mismo bot_type y prompt_type
        self.templates = [
            t for t in self.templates
            if not (t.bot_type == bot_type and t.prompt_type == prompt_type)
        ]
        
        # Agregar nueva plantilla
        template = PromptTemplate(
            name=name,
            bot_type=bot_type,
            prompt_type=prompt_type,
            template_text=template_text,
            description=description
        )
        
        self.templates.append(template)
    
    def validate_data(self, bot_type: BotType, data: PromptData) -> bool:
        """
        Valida que los datos sean apropiados para el tipo de bot
        
        Args:
            bot_type: Tipo de bot
            data: Datos a validar
            
        Returns:
            True si los datos son válidos, False en caso contrario
        """
        if bot_type == BotType.NUMERICO:
            # Debe tener indicadores
            return data.indicators is not None and len(data.indicators) > 0
        
        elif bot_type == BotType.VISUAL:
            # Debe tener imágenes
            return data.image_paths is not None and len(data.image_paths) > 0
        
        elif bot_type == BotType.HIBRIDO:
            # Debe tener ambos
            has_indicators = data.indicators is not None and len(data.indicators) > 0
            has_images = data.image_paths is not None and len(data.image_paths) > 0
            return has_indicators and has_images
        
        return False
    
    def _format_indicators(self, indicators: Dict[str, float]) -> str:
        """Formatea indicadores para incluir en el prompt"""
        lines = []
        for key, value in indicators.items():
            formatted_key = key.replace("_", " ").upper()
            lines.append(f"- {formatted_key}: {value}")
        return "\n".join(lines)
    
    def _format_position_data(self, position_data: Dict[str, Any]) -> str:
        """Formatea datos de posición para incluir en el prompt"""
        lines = []
        for key, value in position_data.items():
            formatted_key = key.replace("_", " ").title()
            lines.append(f"- {formatted_key}: {value}")
        return "\n".join(lines)
    
    def build_prompt(
        self,
        bot_type: BotType,
        prompt_type: PromptType,
        data: PromptData,
        include_json_instructions: bool = True,
        custom_vars: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construye un prompt completo
        
        Args:
            bot_type: Tipo de bot
            prompt_type: Tipo de prompt
            data: Datos para el prompt
            include_json_instructions: Si incluir instrucciones de formato JSON
            custom_vars: Variables personalizadas adicionales
            
        Returns:
            Prompt completo renderizado
            
        Raises:
            PromptBuilderError: Si faltan datos requeridos o la plantilla no existe
        """
        # Validar campos requeridos
        if not data.symbol:
            raise PromptBuilderError("Campo requerido 'symbol' faltante en PromptData")
        
        # Validar datos según tipo de bot
        if not self.validate_data(bot_type, data):
            raise PromptBuilderError(
                f"Datos inválidos para bot tipo {bot_type.value}. "
                f"Verifica que tengas los campos requeridos."
            )
        
        # Obtener plantilla
        template = self.get_template(bot_type, prompt_type)
        
        # Preparar variables adicionales
        extra_vars = custom_vars.copy() if custom_vars else {}
        
        # Formatear indicadores si existen
        if data.indicators:
            extra_vars["indicators_formatted"] = self._format_indicators(data.indicators)
        
        # Formatear datos de posición si existen
        if data.position_data:
            extra_vars["position_data_formatted"] = self._format_position_data(data.position_data)
        
        # Renderizar template
        prompt = template.render(data, extra_vars)
        
        # Agregar instrucciones de formato JSON si se solicita
        if include_json_instructions:
            prompt += "\n\n" + self.JSON_FORMAT_INSTRUCTIONS
        
        return prompt
    
    def build_multi_timeframe_prompt(
        self,
        bot_type: BotType,
        prompt_type: PromptType,
        timeframe_data: List[PromptData],
        include_json_instructions: bool = True,
        custom_vars: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construye un prompt con datos de múltiples timeframes
        
        Args:
            bot_type: Tipo de bot
            prompt_type: Tipo de prompt
            timeframe_data: Lista de datos por timeframe (5M, 15M, 1H)
            include_json_instructions: Si incluir instrucciones JSON
            custom_vars: Variables personalizadas
            
        Returns:
            Prompt completo con todos los timeframes
        """
        if not timeframe_data:
            raise PromptBuilderError("timeframe_data no puede estar vacío")
        
        # Usar el primer símbolo
        symbol = timeframe_data[0].symbol
        
        # Construir secciones por timeframe
        sections = []
        for data in timeframe_data:
            section = f"\n=== TIMEFRAME {data.timeframe} ===\n"
            section += f"Precio: {data.current_price}\n"
            
            if data.indicators:
                section += "Indicadores:\n"
                section += self._format_indicators(data.indicators)
            
            sections.append(section)
        
        # Construir prompt final
        prompt = f"Analiza {symbol} en múltiples timeframes:\n"
        prompt += "\n".join(sections)
        
        if include_json_instructions:
            prompt += "\n\n" + self.JSON_FORMAT_INSTRUCTIONS
        
        return prompt
    
    def build_vwap_methodology_prompt(
        self,
        indicators: Dict,
        or_data: Optional[Any],
        market_context: Any
    ) -> tuple[str, str]:
        """
        Construye prompts usando VWAP Methodology específica.
        
        Este método delega la construcción al VWAPPromptBuilder especializado,
        que implementa la metodología VWAP trend-following completa.
        
        Args:
            indicators: Diccionario de indicadores por timeframe (desde IndicatorCalculator)
            or_data: Datos del Opening Range (desde OpeningRangeCalculator)
            market_context: Contexto de mercado (Enum MarketContext)
            
        Returns:
            tuple: (system_prompt, user_prompt)
            
        Raises:
            PromptBuilderError: Si faltan datos requeridos
        
        Example:
            ```python
            from src.core.vwap_prompt_builder import MarketContext
            from src.core.mt5_data_extractor import Timeframe
            
            builder = PromptBuilder()
            
            # indicators es un Dict[Timeframe, IndicatorData]
            system_prompt, user_prompt = builder.build_vwap_methodology_prompt(
                indicators=indicators,  # Resultado de IndicatorCalculator
                or_data=or_data,        # Resultado de OpeningRangeCalculator
                market_context=MarketContext.EUROPEAN_SESSION
            )
            ```
        """
        # Crear instancia de VWAPPromptBuilder
        vwap_builder = VWAPPromptBuilder()
        
        # Construir system prompt (fijo)
        system_prompt = vwap_builder.build_system_prompt()
        
        # Construir user prompt (variable)
        user_prompt = vwap_builder.build_user_prompt(
            indicators=indicators,
            or_data=or_data,
            market_context=market_context
        )
        
        return system_prompt, user_prompt
