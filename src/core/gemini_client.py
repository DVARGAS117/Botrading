"""
GeminiClient - T10
Cliente para comunicación con Gemini 2.5 Pro API

Este módulo gestiona la comunicación con la API de Google Gemini, incluyendo
envío de prompts (texto e imágenes), manejo de errores, reintentos automáticos
y seguimiento de uso y costos.

Características:
- Envío de prompts de texto
- Envío de imágenes (para análisis visual)
- Configuración de parámetros del modelo
- Reintentos automáticos con backoff exponencial
- Tracking de tokens y costos
- Manejo robusto de errores
- Timeout configurable
- Estadísticas de uso

Tickets relacionados: T10, T11 (tracking de tokens), T13 (parametrización)

Author: Botrading Team
Date: 2025-11-13
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
import time
import os
import json

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    GenerationConfig = None  # type: ignore
    genai = None  # type: ignore
    logging.warning("google-generativeai no está instalado. Instala con: pip install google-generativeai")

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig as VertexGenerationConfig
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    vertexai = None  # type: ignore
    GenerativeModel = None  # type: ignore
    VertexGenerationConfig = None  # type: ignore
    logging.warning("google-cloud-aiplatform no está instalado. Instala con: pip install google-cloud-aiplatform")


class GeminiClientError(Exception):
    """Excepción personalizada para errores del cliente Gemini"""
    pass


@dataclass
class GeminiConfig:
    """
    Configuración para el cliente Gemini
    
    Atributos:
        model: Nombre del modelo de Gemini (default: gemini-2.5-pro)
        temperature: Temperatura del modelo (0-2, default 0.7)
        max_tokens: Máximo de tokens en la respuesta (default 2048)
        top_p: Top-p sampling (default 0.9)
        top_k: Top-k sampling (default 40)
        timeout: Timeout en segundos (default 30)
        retry_attempts: Número de reintentos (default 3)
        backoff_factor: Factor de backoff exponencial (default 2)
        use_vertex_ai: Si usar Vertex AI en lugar de Google AI Studio (default False)
        project_id: ID del proyecto GCP para Vertex AI
        location: Región de Vertex AI (default us-central1)
        credentials_path: Ruta al archivo de credenciales JSON para Vertex AI
    """
    model: str = "gemini-3-pro-preview"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    top_k: int = 40
    timeout: int = 30
    retry_attempts: int = 3
    backoff_factor: float = 2.0
    use_vertex_ai: bool = False
    project_id: Optional[str] = None
    location: str = "us-central1"
    credentials_path: Optional[str] = None
    
    def __post_init__(self):
        """Valida los parámetros después de la inicialización"""
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature debe estar entre 0 y 2")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens debe ser positivo")
        
        if self.timeout <= 0:
            raise ValueError("timeout debe ser positivo")
        
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts no puede ser negativo")
        
        # Validaciones para Vertex AI
        if self.use_vertex_ai:
            if not self.project_id:
                raise ValueError("project_id es requerido cuando use_vertex_ai=True")
            if not self.location:
                raise ValueError("location es requerida cuando use_vertex_ai=True")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_json_file(cls, file_path: str) -> 'GeminiConfig':
        """
        Carga la configuración desde un archivo JSON
        
        Args:
            file_path: Ruta al archivo JSON con la configuración
            
        Returns:
            Instancia de GeminiConfig con los valores del archivo
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            json.JSONDecodeError: Si el JSON es inválido
            ValueError: Si los valores no son válidos
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Filtrar solo los campos válidos para GeminiConfig
        valid_fields = {
            'model', 'temperature', 'max_tokens', 'top_p', 'top_k',
            'timeout', 'retry_attempts', 'backoff_factor',
            'use_vertex_ai', 'project_id', 'location', 'credentials_path'
        }
        
        config_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**config_data)


@dataclass
class GeminiResponse:
    """
    Respuesta de la API de Gemini
    
    Atributos:
        success: Si la llamada fue exitosa
        content: Contenido de la respuesta (JSON string)
        tokens_input: Tokens usados en el prompt
        tokens_output: Tokens usados en la respuesta
        cost: Costo estimado de la llamada
        latency: Tiempo de respuesta en segundos
        error_message: Mensaje de error si falló
        error_type: Tipo de error si falló
        timestamp: Timestamp de la respuesta
    """
    success: bool
    content: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost: Optional[float] = None
    latency: Optional[float] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Agrega timestamp si no existe"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    @property
    def total_tokens(self) -> int:
        """Calcula el total de tokens usados"""
        input_tokens = self.tokens_input or 0
        output_tokens = self.tokens_output or 0
        return input_tokens + output_tokens
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la respuesta a diccionario"""
        result = asdict(self)
        result['total_tokens'] = self.total_tokens
        return result


class GeminiClient:
    """
    Cliente para comunicación con Gemini 2.5 Pro API
    
    Gestiona el envío de prompts (texto e imágenes) y maneja respuestas,
    errores, reintentos y seguimiento de uso.
    
    Ejemplo:
        ```python
        # Inicializar cliente
        config = GeminiConfig(
            model="gemini-2.5-pro",
            temperature=0.7,
            max_tokens=1024
        )
        client = GeminiClient(api_key="YOUR_API_KEY", config=config)
        
        # Enviar prompt de texto
        response = client.send_prompt("Analiza EURUSD con RSI 65.0")
        
        if response.success:
            print(response.content)
            print(f"Tokens: {response.total_tokens}, Costo: ${response.cost}")
        else:
            print(f"Error: {response.error_message}")
        ```
    """
    
    # Costos por 1000 tokens (valores aproximados para Gemini 2.5 Pro)
    # Estos valores deben actualizarse según las tarifas oficiales
    DEFAULT_COST_PER_1K_INPUT = 0.00025   # $0.00025 por 1K tokens de input
    DEFAULT_COST_PER_1K_OUTPUT = 0.001     # $0.001 por 1K tokens de output
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[GeminiConfig] = None
    ):
        """
        Inicializa el cliente de Gemini
        
        Args:
            api_key: API key de Google AI. Si es None, intenta obtener de variable de entorno
            config: Configuración del cliente
            
        Raises:
            GeminiClientError: Si no hay API key o la librería no está disponible
        """
        # Configuración
        self.config = config if config is not None else GeminiConfig()
        
        if self.config.use_vertex_ai:
            # Usar Vertex AI (intento de importación dinámica si no estaba disponible al cargar el módulo)
            if not VERTEX_AVAILABLE:
                try:
                    import importlib  # type: ignore
                    vertexai_mod = importlib.import_module("vertexai")
                    from vertexai.generative_models import GenerativeModel as _GenModel, GenerationConfig as _VertexGenConfig  # type: ignore
                    globals()["vertexai"] = vertexai_mod
                    globals()["GenerativeModel"] = _GenModel
                    globals()["VertexGenerationConfig"] = _VertexGenConfig
                    globals()["VERTEX_AVAILABLE"] = True
                except Exception:
                    # Si las pruebas han hecho patch de GenerativeModel, permitir continuar
                    if globals().get("GenerativeModel") is not None:
                        globals()["VERTEX_AVAILABLE"] = True
                    else:
                        raise GeminiClientError(
                            "google-cloud-aiplatform no está instalado o falló la importación dinámica. "
                            "Instala con: pip install google-cloud-aiplatform"
                        )
            
            if not self.config.project_id:
                raise GeminiClientError("project_id es requerido para Vertex AI")
            
            # Configurar credenciales si se proporciona
            if self.config.credentials_path:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.config.credentials_path
            
            # Inicializar Vertex AI
            vertexai.init(project=self.config.project_id, location=self.config.location)
            
            # Inicializar modelo Vertex AI
            self.model = GenerativeModel(self.config.model)
            self.api_key = None  # No se usa en Vertex AI
            
        else:
            # Usar Google AI Studio
            if not GEMINI_AVAILABLE:
                raise GeminiClientError(
                    "google-generativeai no está instalado. "
                    "Instala con: pip install google-generativeai"
                )
            
            # Obtener API key
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise GeminiClientError(
                    "API key es requerida. Proporciona api_key o establece GEMINI_API_KEY"
                )
            
            # Configurar API
            genai.configure(api_key=self.api_key)
            
            # Inicializar modelo
            self.model = genai.GenerativeModel(self.config.model)
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Costos
        self._cost_per_1k_input_tokens = self.DEFAULT_COST_PER_1K_INPUT
        self._cost_per_1k_output_tokens = self.DEFAULT_COST_PER_1K_OUTPUT
        
        # Estadísticas de uso
        self._usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_input": 0,
            "total_tokens_output": 0,
            "total_cost": 0.0,
            "total_latency": 0.0
        }
        
        # Diccionario de sesiones de conversación activas
        # conversation_id -> ChatSession
        self._conversation_sessions: Dict[str, Any] = {}
        
        self.logger.info(f"Cliente Gemini inicializado: {'Vertex AI' if self.config.use_vertex_ai else 'Google AI Studio'} - {self.config.model}")
    
    def _initialize_model(self) -> None:
        """Inicializa el modelo de Gemini con la configuración"""
        try:
            self.model = genai.GenerativeModel(self.config.model)
            self.logger.info(f"Modelo Gemini inicializado: {self.config.model}")
        except Exception as e:
            raise GeminiClientError(f"Error inicializando modelo Gemini: {str(e)}")
    
    def _get_generation_config(self) -> Any:
        """Crea la configuración de generación para la API"""
        if self.config.use_vertex_ai:
            if not VERTEX_AVAILABLE or VertexGenerationConfig is None:
                # Permitir tests con mocks sin dependencia real
                return {
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                    "top_p": self.config.top_p,
                    "top_k": self.config.top_k,
                }
            return VertexGenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k
            )
        else:
            if not GEMINI_AVAILABLE or GenerationConfig is None:
                raise GeminiClientError("google-generativeai no está disponible")
            return GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k
            )
    
    def _calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """
        Calcula el costo de una llamada
        
        Args:
            tokens_input: Tokens de entrada
            tokens_output: Tokens de salida
            
        Returns:
            Costo en dólares
        """
        cost_input = (tokens_input / 1000) * self._cost_per_1k_input_tokens
        cost_output = (tokens_output / 1000) * self._cost_per_1k_output_tokens
        return cost_input + cost_output
    
    def _validate_image_paths(self, image_paths: Optional[List[str]]) -> bool:
        """
        Valida las rutas de imágenes
        
        Args:
            image_paths: Lista de rutas a imágenes
            
        Returns:
            True si son válidas, False en caso contrario
        """
        if image_paths is None:
            return True  # None es válido (sin imágenes)
        
        if not isinstance(image_paths, list):
            return False
        
        if len(image_paths) == 0:
            return False
        
        # Podríamos agregar validación adicional aquí (archivos existen, formato, etc.)
        return True
    
    def _format_prompt_for_api(self, prompt: str) -> str:
        """
        Formatea el prompt para la API
        
        Args:
            prompt: Prompt original
            
        Returns:
            Prompt formateado
        """
        # Por ahora, simplemente retorna el prompt sin cambios
        # Aquí se podrían agregar transformaciones si son necesarias
        return prompt
    
    def _load_images(self, image_paths: List[str]) -> List[Any]:
        """
        Carga imágenes desde las rutas proporcionadas
        
        Args:
            image_paths: Lista de rutas a imágenes
            
        Returns:
            Lista de objetos de imagen para la API
            
        Raises:
            GeminiClientError: Si hay error cargando imágenes
        """
        images = []
        
        try:
            from PIL import Image
            
            for path in image_paths:
                if not os.path.exists(path):
                    raise GeminiClientError(f"Imagen no encontrada: {path}")
                
                img = Image.open(path)
                images.append(img)
            
            return images
            
        except ImportError:
            raise GeminiClientError(
                "PIL no está instalado. Instala con: pip install Pillow"
            )
        except Exception as e:
            raise GeminiClientError(f"Error cargando imágenes: {str(e)}")
    
    def send_prompt(
        self,
        prompt: str,
        image_paths: Optional[List[str]] = None,
        conversation_id: Optional[str] = None
    ) -> GeminiResponse:
        """
        Envía un prompt a la API de Gemini con reintentos automáticos
        
        Args:
            prompt: Texto del prompt
            image_paths: Lista opcional de rutas a imágenes
            conversation_id: ID opcional de conversación para mantener contexto
            
        Returns:
            GeminiResponse con el resultado
            
        Raises:
            GeminiClientError: Si el prompt está vacío
            
        Note:
            Si se proporciona conversation_id, el prompt se enviará dentro de esa
            conversación manteniendo el historial. Si no existe la conversación,
            se creará automáticamente. Si conversation_id es None, se enviará
            como prompt individual sin contexto.
        """
        # Validar prompt
        if not prompt or not prompt.strip():
            raise GeminiClientError("Prompt no puede estar vacío")
        
        # Validar imágenes si se proporcionan
        if not self._validate_image_paths(image_paths):
            return GeminiResponse(
                success=False,
                error_message="Rutas de imágenes inválidas",
                error_type="validation_error"
            )
        
        # Formatear prompt
        formatted_prompt = self._format_prompt_for_api(prompt)
        
        # Preparar contenido
        content = [formatted_prompt]
        
        # Cargar imágenes si se proporcionan
        if image_paths:
            try:
                images = self._load_images(image_paths)
                content.extend(images)
            except GeminiClientError as e:
                return GeminiResponse(
                    success=False,
                    error_message=str(e),
                    error_type="image_loading_error"
                )
        
        # Intentar enviar con reintentos
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.time()
                
                # Generar contenido
                generation_config = self._get_generation_config()
                
                # Decidir si usar conversación o envío directo
                if conversation_id is not None:
                    # Usar conversación para mantener contexto
                    chat_session = self.get_conversation(conversation_id)
                    response = chat_session.send_message(
                        content,
                        generation_config=generation_config
                    )
                else:
                    # Envío directo sin contexto
                    response = self.model.generate_content(
                        content,
                        generation_config=generation_config,
                        request_options={'timeout': self.config.timeout}
                    )
                
                latency = time.time() - start_time
                
                # Extraer métricas
                tokens_input = response.usage_metadata.prompt_token_count
                tokens_output = response.usage_metadata.candidates_token_count
                cost = self._calculate_cost(tokens_input, tokens_output)
                
                # Actualizar estadísticas
                self._update_statistics(
                    success=True,
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    cost=cost,
                    latency=latency
                )
                
                # Retornar respuesta exitosa
                return GeminiResponse(
                    success=True,
                    content=response.text,
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    cost=cost,
                    latency=latency
                )
                
            except TimeoutError as e:
                error_msg = f"Timeout en intento {attempt + 1}/{self.config.retry_attempts}"
                self.logger.warning(error_msg)
                
                if attempt == self.config.retry_attempts - 1:
                    # Último intento
                    self._update_statistics(success=False)
                    return GeminiResponse(
                        success=False,
                        error_message=f"Request timeout después de {self.config.retry_attempts} intentos",
                        error_type="timeout"
                    )
                
                # Esperar antes de reintentar (backoff exponencial)
                wait_time = self.config.backoff_factor ** attempt
                time.sleep(wait_time)
                
            except Exception as e:
                error_msg = f"Error en intento {attempt + 1}/{self.config.retry_attempts}: {str(e)}"
                self.logger.warning(error_msg)
                
                if attempt == self.config.retry_attempts - 1:
                    # Último intento
                    self._update_statistics(success=False)
                    return GeminiResponse(
                        success=False,
                        error_message=f"Error después de {self.config.retry_attempts} intentos: {str(e)}",
                        error_type="api_error"
                    )
                
                # Esperar antes de reintentar (backoff exponencial)
                wait_time = self.config.backoff_factor ** attempt
                time.sleep(wait_time)
        
        # No debería llegar aquí, pero por si acaso
        self._update_statistics(success=False)
        return GeminiResponse(
            success=False,
            error_message="Error desconocido en send_prompt",
            error_type="unknown_error"
        )
    
    def _update_statistics(
        self,
        success: bool,
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost: float = 0.0,
        latency: float = 0.0
    ) -> None:
        """Actualiza las estadísticas de uso"""
        self._usage_stats["total_requests"] += 1
        
        if success:
            self._usage_stats["successful_requests"] += 1
            self._usage_stats["total_tokens_input"] += tokens_input
            self._usage_stats["total_tokens_output"] += tokens_output
            self._usage_stats["total_cost"] += cost
            self._usage_stats["total_latency"] += latency
        else:
            self._usage_stats["failed_requests"] += 1
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso del cliente
        
        Returns:
            Diccionario con estadísticas
        """
        stats = self._usage_stats.copy()
        
        # Agregar métricas calculadas
        if stats["successful_requests"] > 0:
            stats["average_latency"] = stats["total_latency"] / stats["successful_requests"]
            stats["average_cost_per_request"] = stats["total_cost"] / stats["successful_requests"]
        else:
            stats["average_latency"] = 0.0
            stats["average_cost_per_request"] = 0.0
        
        return stats
    
    def reset_statistics(self) -> None:
        """Reinicia las estadísticas de uso"""
        self._usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_input": 0,
            "total_tokens_output": 0,
            "total_cost": 0.0,
            "total_latency": 0.0
        }
        self.logger.info("Estadísticas de uso reiniciadas")
    
    def update_config(self, new_config: GeminiConfig) -> None:
        """
        Actualiza la configuración del cliente
        
        Args:
            new_config: Nueva configuración
        """
        self.config = new_config
        self._initialize_model()  # Reinicializar modelo con nueva config
        self.logger.info("Configuración actualizada")
    
    def update_config_from_file(self, config_file_path: str) -> None:
        """
        Actualiza la configuración del cliente desde un archivo JSON
        
        Args:
            config_file_path: Ruta al archivo JSON con la nueva configuración
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            json.JSONDecodeError: Si el JSON es inválido
            ValueError: Si los valores no son válidos
        """
        new_config = GeminiConfig.from_json_file(config_file_path)
        self.update_config(new_config)
        self.logger.info(f"Configuración actualizada desde archivo: {config_file_path}")
    
    def set_cost_rates(
        self,
        cost_per_1k_input: float,
        cost_per_1k_output: float
    ) -> None:
        """
        Establece las tarifas de costo personalizadas
        
        Args:
            cost_per_1k_input: Costo por 1000 tokens de input
            cost_per_1k_output: Costo por 1000 tokens de output
        """
        self._cost_per_1k_input_tokens = cost_per_1k_input
        self._cost_per_1k_output_tokens = cost_per_1k_output
        self.logger.info(
            f"Tarifas actualizadas: input=${cost_per_1k_input}/1K, "
            f"output=${cost_per_1k_output}/1K"
        )
    
    # ========================================================================
    # Métodos de Gestión de Conversaciones (T28)
    # ========================================================================
    
    def create_conversation(self, conversation_id: str) -> Any:
        """
        Crea una nueva sesión de conversación
        
        Args:
            conversation_id: Identificador único de la conversación
            
        Returns:
            ChatSession creada
            
        Raises:
            GeminiClientError: Si hay error al crear la sesión
            ValueError: Si conversation_id está vacío o ya existe
        """
        if not conversation_id or not conversation_id.strip():
            raise ValueError("conversation_id no puede estar vacío")
        
        if conversation_id in self._conversation_sessions:
            raise ValueError(
                f"La conversación '{conversation_id}' ya existe. "
                "Usa get_conversation() para obtenerla o clear_conversation() para eliminarla."
            )
        
        try:
            # Crear nueva sesión de chat
            chat_session = self.model.start_chat(history=[])
            self._conversation_sessions[conversation_id] = chat_session
            
            self.logger.info(f"Sesión de conversación creada: {conversation_id}")
            return chat_session
            
        except Exception as e:
            raise GeminiClientError(
                f"Error creando sesión de chat para '{conversation_id}': {str(e)}"
            )
    
    def get_conversation(self, conversation_id: str) -> Any:
        """
        Obtiene una conversación existente o crea una nueva si no existe
        
        Args:
            conversation_id: Identificador de la conversación
            
        Returns:
            ChatSession correspondiente
            
        Raises:
            GeminiClientError: Si hay error al obtener/crear la sesión
        """
        if not conversation_id or not conversation_id.strip():
            raise ValueError("conversation_id no puede estar vacío")
        
        # Si existe, retornarla
        if conversation_id in self._conversation_sessions:
            return self._conversation_sessions[conversation_id]
        
        # Si no existe, crearla
        self.logger.debug(
            f"Conversación '{conversation_id}' no existe. Creando nueva..."
        )
        return self.create_conversation(conversation_id)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Elimina una conversación específica
        
        Args:
            conversation_id: Identificador de la conversación
            
        Returns:
            True si se eliminó, False si no existía
        """
        if conversation_id in self._conversation_sessions:
            del self._conversation_sessions[conversation_id]
            self.logger.info(f"Conversación '{conversation_id}' eliminada")
            return True
        else:
            self.logger.warning(
                f"Intento de eliminar conversación inexistente: '{conversation_id}'"
            )
            return False
    
    def clear_all_conversations(self) -> int:
        """
        Elimina todas las conversaciones activas
        
        Returns:
            Número de conversaciones eliminadas
        """
        count = len(self._conversation_sessions)
        self._conversation_sessions.clear()
        self.logger.info(f"Todas las conversaciones eliminadas ({count} en total)")
        return count
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de una conversación
        
        Args:
            conversation_id: Identificador de la conversación
            
        Returns:
            Lista de mensajes en formato dict con 'role' y 'content'
            Retorna lista vacía si la conversación no existe
        """
        if conversation_id not in self._conversation_sessions:
            self.logger.warning(
                f"Intento de obtener historial de conversación inexistente: '{conversation_id}'"
            )
            return []
        
        chat_session = self._conversation_sessions[conversation_id]
        
        try:
            # Convertir historial a formato simple
            history = []
            for msg in chat_session.history:
                history.append({
                    'role': msg.role,
                    'content': msg.parts[0].text if msg.parts else ""
                })
            
            return history
            
        except Exception as e:
            self.logger.error(
                f"Error obteniendo historial de '{conversation_id}': {e}",
                exc_info=True
            )
            return []
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de conversaciones activas
        
        Returns:
            Diccionario con estadísticas:
            - active_conversations: Número de conversaciones activas
            - conversation_ids: Lista de IDs de conversaciones
        """
        return {
            'active_conversations': len(self._conversation_sessions),
            'conversation_ids': list(self._conversation_sessions.keys())
        }
    
    def has_conversation(self, conversation_id: str) -> bool:
        """
        Verifica si existe una conversación
        
        Args:
            conversation_id: Identificador de la conversación
            
        Returns:
            True si existe, False en caso contrario
        """
        return conversation_id in self._conversation_sessions

