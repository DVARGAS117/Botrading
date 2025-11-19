"""
Tests para GeminiClient - T10
Cliente para comunicación con Gemini 2.5 Pro API

Funcionalidades a testear:
- Envío de prompts de texto
- Envío de prompts con imágenes
- Recepción y parseo de respuestas JSON
- Manejo de errores y reintentos
- Configuración de parámetros
- Tracking de tokens y costos
- Timeout y manejo de excepciones

Author: Botrading Team
Date: 2025-11-13
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.gemini_client import (
    GeminiClient,
    GeminiClientError,
    GeminiResponse,
    GeminiConfig
)
import json
import tempfile
import os


class TestGeminiConfig:
    """Tests para la configuración del cliente Gemini"""
    
    def test_config_creation_default(self):
        """Verificar creación con valores por defecto"""
        config = GeminiConfig()
        
        assert config.model == "gemini-3-pro-preview"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.timeout == 30
        assert config.retry_attempts == 3
    
    def test_config_creation_custom(self):
        """Verificar creación con valores personalizados"""
        config = GeminiConfig(
            model="gemini-2.5-pro",
            temperature=0.5,
            max_tokens=1024,
            timeout=60,
            retry_attempts=5
        )
        
        assert config.model == "gemini-2.5-pro"
        assert config.temperature == 0.5
        assert config.max_tokens == 1024
        assert config.timeout == 60
        assert config.retry_attempts == 5
    
    def test_config_validation_temperature(self):
        """Verificar validación de temperatura"""
        with pytest.raises(ValueError, match="temperature debe estar entre 0 y 2"):
            GeminiConfig(temperature=-0.1)
        
        with pytest.raises(ValueError, match="temperature debe estar entre 0 y 2"):
            GeminiConfig(temperature=2.5)
    
    def test_config_validation_vertex_ai_missing_project_id(self):
        """Verificar validación de Vertex AI sin project_id"""
        with pytest.raises(ValueError, match="project_id es requerido cuando use_vertex_ai=True"):
            GeminiConfig(use_vertex_ai=True, project_id=None)
    
    def test_config_validation_vertex_ai_missing_location(self):
        """Verificar validación de Vertex AI sin location"""
        with pytest.raises(ValueError, match="location es requerida cuando use_vertex_ai=True"):
            GeminiConfig(use_vertex_ai=True, project_id="test-project", location=None)
    
    def test_config_to_dict(self):
        """Verificar conversión a diccionario"""
        config = GeminiConfig(model="gemini-2.5-pro", temperature=0.8)
        result = config.to_dict()
        
        assert result["model"] == "gemini-2.5-pro"
        assert result["temperature"] == 0.8
        assert "max_tokens" in result
    
    def test_config_from_json_file(self, tmp_path):
        """Verificar carga de configuración desde archivo JSON"""
        # Crear archivo JSON temporal
        config_data = {
            "model": "gemini-2.5-pro",
            "temperature": 0.5,
            "max_tokens": 1024,
            "timeout": 60,
            "retry_attempts": 5
        }
        
        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Cargar configuración
        config = GeminiConfig.from_json_file(str(config_file))
        
        # Verificar valores
        assert config.model == "gemini-2.5-pro"
        assert config.temperature == 0.5
        assert config.max_tokens == 1024
        assert config.timeout == 60
        assert config.retry_attempts == 5
    
    def test_config_from_json_file_missing_file(self):
        """Verificar error cuando el archivo no existe"""
        with pytest.raises(FileNotFoundError):
            GeminiConfig.from_json_file("nonexistent_file.json")
    
    def test_config_from_json_file_invalid_json(self, tmp_path):
        """Verificar error con JSON inválido"""
        config_file = tmp_path / "invalid.json"
        with open(config_file, 'w') as f:
            f.write("invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            GeminiConfig.from_json_file(str(config_file))


class TestGeminiResponse:
    """Tests para la respuesta de Gemini"""
    
    def test_response_creation_success(self):
        """Verificar creación de respuesta exitosa"""
        response = GeminiResponse(
            success=True,
            content='{"accion": "OPERAR"}',
            tokens_input=100,
            tokens_output=50,
            cost=0.01
        )
        
        assert response.success is True
        assert response.content == '{"accion": "OPERAR"}'
        assert response.tokens_input == 100
        assert response.tokens_output == 50
        assert response.cost == 0.01
        assert response.error_message is None
    
    def test_response_creation_error(self):
        """Verificar creación de respuesta con error"""
        response = GeminiResponse(
            success=False,
            error_message="API timeout",
            error_type="timeout"
        )
        
        assert response.success is False
        assert response.error_message == "API timeout"
        assert response.error_type == "timeout"
        assert response.content is None
    
    def test_response_total_tokens(self):
        """Verificar cálculo de tokens totales"""
        response = GeminiResponse(
            success=True,
            content="test",
            tokens_input=100,
            tokens_output=50
        )
        
        assert response.total_tokens == 150
    
    def test_response_to_dict(self):
        """Verificar conversión a diccionario"""
        response = GeminiResponse(
            success=True,
            content="test",
            tokens_input=100,
            tokens_output=50,
            cost=0.01
        )
        
        result = response.to_dict()
        assert result["success"] is True
        assert result["content"] == "test"
        assert result["total_tokens"] == 150


class TestGeminiClient:
    """Tests para el cliente principal de Gemini"""
    
    @pytest.fixture
    def mock_api_key(self):
        """Fixture que retorna una API key de prueba"""
        return "test_api_key_1234567890"
    
    @pytest.fixture
    def client(self, mock_api_key):
        """Fixture que retorna un cliente configurado"""
        config = GeminiConfig(
            model="gemini-2.5-pro",
            temperature=0.7,
            max_tokens=1024,
            retry_attempts=3
        )
        
        # Mockear el modelo durante la inicialización
        with patch('src.core.gemini_client.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = Mock()
            
            client = GeminiClient(api_key=mock_api_key, config=config)
            client.model = mock_model  # Asegurar que tenemos el mock
            
            yield client
    
    def test_client_initialization(self, client):
        """Verificar inicialización correcta del cliente"""
        assert client is not None
        assert client.config.model == "gemini-2.5-pro"
        assert client.config.temperature == 0.7
    
    def test_client_initialization_without_api_key(self):
        """Verificar error si no se proporciona API key"""
        with pytest.raises(GeminiClientError, match="API key es requerida"):
            GeminiClient(api_key=None)
    
    def test_send_text_prompt_success(self, client):
        """Verificar envío exitoso de prompt de texto"""
        # Mock de la respuesta de la API
        mock_response = Mock()
        mock_response.text = '{"accion": "OPERAR", "direccion": "BUY"}'
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        client.model.generate_content.return_value = mock_response
        
        # Ejecutar
        prompt = "Analiza EURUSD con RSI 65.0"
        response = client.send_prompt(prompt)
        
        # Verificar
        assert response.success is True
        assert "OPERAR" in response.content
        assert response.tokens_input == 100
        assert response.tokens_output == 50
    
    @patch('os.path.exists', return_value=True)
    @patch('PIL.Image.open')
    def test_send_text_prompt_with_images(self, mock_image_open, mock_exists, client):
        """Verificar envío de prompt con imágenes"""
        # Mock imagen
        mock_img = Mock()
        mock_image_open.return_value = mock_img
        
        mock_response = Mock()
        mock_response.text = '{"accion": "NO_OPERAR"}'
        mock_response.usage_metadata.prompt_token_count = 200
        mock_response.usage_metadata.candidates_token_count = 30
        
        client.model.generate_content.return_value = mock_response
        
        # Ejecutar con imágenes
        prompt = "Analiza estas gráficas"
        image_paths = ["/path/chart_5m.png", "/path/chart_15m.png"]
        
        response = client.send_prompt(prompt, image_paths=image_paths)
        
        # Verificar
        assert response.success is True
        assert response.tokens_input == 200
    
    def test_send_prompt_api_error(self, client):
        """Verificar manejo de error de API"""
        client.model.generate_content.side_effect = Exception("API Error")
        
        # Ejecutar
        response = client.send_prompt("Test prompt")
        
        # Verificar que retorna error en lugar de lanzar excepción
        assert response.success is False
        assert response.error_message is not None
        assert "API Error" in response.error_message
    
    def test_send_prompt_timeout(self, client):
        """Verificar manejo de timeout"""
        import time
        
        # Simular timeout
        client.model.generate_content.side_effect = TimeoutError("Request timeout")
        
        response = client.send_prompt("Test prompt")
        
        assert response.success is False
        assert response.error_type == "timeout"
    
    def test_send_prompt_with_retry(self, client):
        """Verificar reintentos automáticos"""
        mock_response_success = Mock()
        mock_response_success.text = '{"accion": "OPERAR"}'
        mock_response_success.usage_metadata.prompt_token_count = 100
        mock_response_success.usage_metadata.candidates_token_count = 50
        
        # Primera llamada falla, segunda tiene éxito
        client.model.generate_content.side_effect = [
            Exception("Temporary error"),
            mock_response_success
        ]
        
        # Ejecutar
        response = client.send_prompt("Test prompt")
        
        # Debe tener éxito después de reintentar
        assert response.success is True
        assert response.content == '{"accion": "OPERAR"}'
        assert client.model.generate_content.call_count == 2
    
    def test_send_prompt_max_retries_exceeded(self, client):
        """Verificar fallo después de agotar reintentos"""
        client.model.generate_content.side_effect = Exception("Persistent error")
        
        # Ejecutar
        response = client.send_prompt("Test prompt")
        
        # Debe fallar después de todos los reintentos
        assert response.success is False
        assert client.model.generate_content.call_count == client.config.retry_attempts
    
    def test_calculate_cost(self, client):
        """Verificar cálculo de costo"""
        # Mock de tarifas
        cost_per_1k_input = 0.00025
        cost_per_1k_output = 0.001
        
        client._cost_per_1k_input_tokens = cost_per_1k_input
        client._cost_per_1k_output_tokens = cost_per_1k_output
        
        # Calcular costo
        tokens_input = 1000
        tokens_output = 500
        
        cost = client._calculate_cost(tokens_input, tokens_output)
        
        expected_cost = (tokens_input / 1000 * cost_per_1k_input) + (tokens_output / 1000 * cost_per_1k_output)
        assert cost == pytest.approx(expected_cost, rel=1e-6)
    
    def test_track_usage_statistics(self, client):
        """Verificar seguimiento de estadísticas de uso"""
        mock_response = Mock()
        mock_response.text = '{"accion": "OPERAR"}'
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        client.model.generate_content.return_value = mock_response
        
        # Hacer varias llamadas
        client.send_prompt("Prompt 1")
        client.send_prompt("Prompt 2")
        client.send_prompt("Prompt 3")
        
        # Obtener estadísticas
        stats = client.get_usage_statistics()
        
        assert stats["total_requests"] == 3
        assert stats["total_tokens_input"] == 300
        assert stats["total_tokens_output"] == 150
        assert stats["total_cost"] > 0
    
    def test_reset_statistics(self, client):
        """Verificar reinicio de estadísticas"""
        # Agregar algunos datos
        client._usage_stats = {
            "total_requests": 5,
            "total_tokens_input": 500,
            "total_tokens_output": 250,
            "total_cost": 1.50
        }
        
        # Reiniciar
        client.reset_statistics()
        
        # Verificar
        stats = client.get_usage_statistics()
        assert stats["total_requests"] == 0
        assert stats["total_tokens_input"] == 0
        assert stats["total_cost"] == 0.0
    
    def test_send_prompt_invalid_json_response(self, client):
        """Verificar manejo de respuesta JSON inválida"""
        mock_response = Mock()
        mock_response.text = "Esta no es una respuesta JSON válida"
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        client.model.generate_content.return_value = mock_response
        
        # Ejecutar
        response = client.send_prompt("Test prompt")
        
        # Debe tener éxito pero con advertencia en logs
        # (el parseo JSON lo hace AIResponseParser, no GeminiClient)
        assert response.success is True
        assert response.content == "Esta no es una respuesta JSON válida"
    
    def test_validate_image_paths(self, client):
        """Verificar validación de rutas de imágenes"""
        # Rutas válidas
        valid_paths = ["/path/chart1.png", "/path/chart2.jpg"]
        assert client._validate_image_paths(valid_paths) is True
        
        # Rutas inválidas (vacías)
        assert client._validate_image_paths([]) is False
        
        # Rutas inválidas (None)
        assert client._validate_image_paths(None) is True  # None es válido (sin imágenes)
    
    def test_format_prompt_for_api(self, client):
        """Verificar formateo de prompt para la API"""
        prompt = "Analiza EURUSD"
        formatted = client._format_prompt_for_api(prompt)
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
    
    def test_concurrent_requests(self, client):
        """Verificar manejo de múltiples requests concurrentes"""
        mock_response = Mock()
        mock_response.text = '{"accion": "OPERAR"}'
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        client.model.generate_content.return_value = mock_response
        
        # Simular requests concurrentes
        responses = []
        for i in range(5):
            resp = client.send_prompt(f"Prompt {i}")
            responses.append(resp)
        
        # Todas deben tener éxito
        assert all(r.success for r in responses)
        assert len(responses) == 5


class TestGeminiClientEdgeCases:
    """Tests para casos borde y situaciones especiales"""
    
    def test_empty_prompt(self):
        """Verificar manejo de prompt vacío"""
        client = GeminiClient(api_key="test_key")
        
        with pytest.raises(GeminiClientError, match="Prompt no puede estar vacío"):
            client.send_prompt("")
    
    def test_extremely_long_prompt(self):
        """Verificar manejo de prompt muy largo"""
        with patch('src.core.gemini_client.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = Mock()
            
            client = GeminiClient(api_key="test_key")
            client.model = mock_model  # Asegurar que tenemos el mock
        
        # Prompt de 100k caracteres
        long_prompt = "A" * 100000
        
        # Debe manejar o truncar el prompt
        # (Implementación específica depende de límites de la API)
        mock_response = Mock()
        mock_response.text = '{"accion": "NO_OPERAR"}'
        mock_response.usage_metadata.prompt_token_count = 50000
        mock_response.usage_metadata.candidates_token_count = 50
        
        client.model.generate_content.return_value = mock_response
        
        response = client.send_prompt(long_prompt)
        # Debe manejar sin error
        assert response is not None
    
    def test_special_characters_in_prompt(self):
        """Verificar manejo de caracteres especiales"""
        with patch('src.core.gemini_client.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = Mock()
            
            client = GeminiClient(api_key="test_key")
            client.model = mock_model  # Asegurar que tenemos el mock
        
        prompt_with_special = "Analiza €USD con émojis 📈📉 y símbolos ©®™"
        
        mock_response = Mock()
        mock_response.text = '{"accion": "OPERAR"}'
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        client.model.generate_content.return_value = mock_response
        
        response = client.send_prompt(prompt_with_special)
        assert response.success is True
    
    def test_config_update_after_initialization(self):
        """Verificar actualización de configuración después de inicialización"""
        client = GeminiClient(api_key="test_key")
        
        # Configuración inicial
        assert client.config.temperature == 0.7
        
        # Actualizar configuración
        new_config = GeminiConfig(temperature=0.5, max_tokens=512)
        client.update_config(new_config)
        
        # Verificar cambio
        assert client.config.temperature == 0.5
        assert client.config.max_tokens == 512
    
    def test_config_update_from_json_file(self, tmp_path):
        """Verificar actualización de configuración desde archivo JSON"""
        client = GeminiClient(api_key="test_key")
        
        # Configuración inicial
        assert client.config.temperature == 0.7
        
        # Crear archivo JSON con nueva configuración
        config_data = {
            "model": "gemini-2.5-pro",
            "temperature": 0.3,
            "max_tokens": 512,
            "timeout": 45
        }
        
        config_file = tmp_path / "update_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Actualizar desde archivo
        client.update_config_from_file(str(config_file))
        
        # Verificar cambios
        assert client.config.model == "gemini-2.5-pro"
        assert client.config.temperature == 0.3
        assert client.config.max_tokens == 512
        assert client.config.timeout == 45


class TestGeminiClientVertexAI:
    """Tests para el cliente Gemini con Vertex AI"""
    
    @pytest.fixture
    def vertex_config(self):
        """Fixture que retorna configuración para Vertex AI"""
        return GeminiConfig(
            use_vertex_ai=True,
            project_id="test-project-123",
            location="us-central1",
            credentials_path="/path/to/credentials.json",
            model="gemini-2.5-pro",
            temperature=0.7,
            max_tokens=1024
        )
    
    @pytest.fixture
    def vertex_client(self, vertex_config):
        """Fixture que retorna un cliente Vertex AI configurado"""
        with patch('src.core.gemini_client.vertexai') as mock_vertexai, \
             patch('src.core.gemini_client.GenerativeModel') as mock_generative_model:
            
            mock_model = Mock()
            mock_generative_model.return_value = mock_model
            
            client = GeminiClient(config=vertex_config)
            client.model = mock_model
            
            yield client
    
    def test_vertex_client_initialization(self, vertex_client, vertex_config):
        """Verificar inicialización correcta del cliente Vertex AI"""
        assert vertex_client is not None
        assert vertex_client.config.use_vertex_ai is True
        assert vertex_client.config.project_id == "test-project-123"
        assert vertex_client.config.location == "us-central1"
        assert vertex_client.api_key is None  # No se usa en Vertex AI
    
    def test_vertex_client_initialization_missing_project_id(self):
        """Verificar error si falta project_id en Vertex AI"""
        with pytest.raises(ValueError, match="project_id es requerido cuando use_vertex_ai=True"):
            GeminiConfig(use_vertex_ai=True, location="us-central1")
    
    def test_vertex_send_text_prompt_success(self, vertex_client):
        """Verificar envío exitoso de prompt de texto con Vertex AI"""
        # Mock de la respuesta de Vertex AI
        mock_response = Mock()
        mock_response.text = '{"accion": "OPERAR", "direccion": "BUY"}'
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        vertex_client.model.generate_content.return_value = mock_response
        
        # Ejecutar
        prompt = "Analiza EURUSD con RSI 65.0"
        response = vertex_client.send_prompt(prompt)
        
        # Verificar
        assert response.success is True
        assert "OPERAR" in response.content
        assert response.tokens_input == 100
        assert response.tokens_output == 50
    
    def test_vertex_send_prompt_with_conversation(self, vertex_client):
        """Verificar envío de prompt con conversación en Vertex AI"""
        with patch.object(vertex_client, 'model') as mock_model:
            # Crear mock de chat session
            mock_chat_session = Mock()
            mock_response = Mock()
            mock_response.text = '{"accion": "MANTENER", "razonamiento": "Todo bien"}'
            mock_response.usage_metadata.prompt_token_count = 150
            mock_response.usage_metadata.candidates_token_count = 75
            
            mock_chat_session.send_message.return_value = mock_response
            mock_model.start_chat.return_value = mock_chat_session
            
            # Enviar mensaje en conversación
            conversation_id = "vertex_conv_test"
            response = vertex_client.send_prompt(
                "Evaluación con Vertex AI",
                conversation_id=conversation_id
            )
            
            assert response.success is True
            assert "MANTENER" in response.content
            assert conversation_id in vertex_client._conversation_sessions
    """Tests para manejo de conversaciones con contexto - T28"""
    
    def test_create_conversation_session(self):
        """Verificar creación de nueva sesión de conversación"""
        client = GeminiClient(api_key="test_key")
        
        conversation_id = "test_conv_123"
        session = client.create_conversation(conversation_id)
        
        assert session is not None
        assert conversation_id in client._conversation_sessions
        assert client._conversation_sessions[conversation_id] is session
    
    def test_get_existing_conversation(self):
        """Verificar obtención de conversación existente"""
        client = GeminiClient(api_key="test_key")
        
        conversation_id = "test_conv_456"
        session1 = client.create_conversation(conversation_id)
        session2 = client.get_conversation(conversation_id)
        
        assert session1 is session2  # Debe ser la misma instancia
    
    def test_get_non_existing_conversation_creates_new(self):
        """Verificar que obtener conversación inexistente crea una nueva"""
        client = GeminiClient(api_key="test_key")
        
        conversation_id = "test_conv_789"
        session = client.get_conversation(conversation_id)
        
        assert session is not None
        assert conversation_id in client._conversation_sessions
    
    def test_send_prompt_with_conversation_id(self):
        """Verificar envío de prompt dentro de conversación"""
        client = GeminiClient(api_key="test_key")
        
        with patch.object(client, 'model') as mock_model:
            # Crear mock de chat session
            mock_chat_session = Mock()
            mock_response = Mock()
            mock_response.text = '{"accion": "MANTENER", "razonamiento": "Todo bien"}'
            mock_response.usage_metadata.prompt_token_count = 150
            mock_response.usage_metadata.candidates_token_count = 75
            
            mock_chat_session.send_message.return_value = mock_response
            mock_model.start_chat.return_value = mock_chat_session
            
            # Enviar primer mensaje en conversación
            conversation_id = "conv_test_001"
            response1 = client.send_prompt(
                "Primera evaluación",
                conversation_id=conversation_id
            )
            
            assert response1.success is True
            assert "MANTENER" in response1.content
            assert conversation_id in client._conversation_sessions
            
            # Enviar segundo mensaje en misma conversación
            response2 = client.send_prompt(
                "Segunda reevaluación",
                conversation_id=conversation_id
            )
            
            assert response2.success is True
            # Verificar que se usó la misma sesión de chat
            assert mock_chat_session.send_message.call_count == 2
    
    def test_send_prompt_without_conversation_id_no_persistence(self):
        """Verificar que sin conversation_id no se mantiene contexto"""
        client = GeminiClient(api_key="test_key")
        
        with patch.object(client, 'model') as mock_model:
            mock_response = Mock()
            mock_response.text = '{"accion": "NO_OPERAR"}'
            mock_response.usage_metadata.prompt_token_count = 100
            mock_response.usage_metadata.candidates_token_count = 50
            
            mock_model.generate_content.return_value = mock_response
            
            # Enviar sin conversation_id
            response = client.send_prompt("Test prompt")
            
            assert response.success is True
            assert len(client._conversation_sessions) == 0  # No debe crear sesión
    
    def test_clear_conversation(self):
        """Verificar limpieza de conversación específica"""
        client = GeminiClient(api_key="test_key")
        
        # Crear múltiples conversaciones
        conv_id_1 = "conv_001"
        conv_id_2 = "conv_002"
        
        client.create_conversation(conv_id_1)
        client.create_conversation(conv_id_2)
        
        assert len(client._conversation_sessions) == 2
        
        # Limpiar una conversación
        client.clear_conversation(conv_id_1)
        
        assert len(client._conversation_sessions) == 1
        assert conv_id_1 not in client._conversation_sessions
        assert conv_id_2 in client._conversation_sessions
    
    def test_clear_all_conversations(self):
        """Verificar limpieza de todas las conversaciones"""
        client = GeminiClient(api_key="test_key")
        
        # Crear múltiples conversaciones
        client.create_conversation("conv_001")
        client.create_conversation("conv_002")
        client.create_conversation("conv_003")
        
        assert len(client._conversation_sessions) == 3
        
        # Limpiar todas
        client.clear_all_conversations()
        
        assert len(client._conversation_sessions) == 0
    
    def test_get_conversation_history(self):
        """Verificar obtención del historial de una conversación"""
        client = GeminiClient(api_key="test_key")
        
        with patch.object(client, 'model') as mock_model:
            mock_chat_session = Mock()
            mock_chat_session.history = [
                Mock(role="user", parts=[Mock(text="Primera pregunta")]),
                Mock(role="model", parts=[Mock(text='{"accion": "OPERAR"}')]),
                Mock(role="user", parts=[Mock(text="Reevaluación")]),
                Mock(role="model", parts=[Mock(text='{"accion": "MANTENER"}')])
            ]
            
            mock_model.start_chat.return_value = mock_chat_session
            
            conversation_id = "conv_history_test"
            client.create_conversation(conversation_id)
            
            # Obtener historial
            history = client.get_conversation_history(conversation_id)
            
            assert history is not None
            assert len(history) == 4
            assert history[0]['role'] == 'user'
            assert history[1]['role'] == 'model'
    
    def test_get_conversation_history_non_existing(self):
        """Verificar que obtener historial de conversación inexistente retorna vacío"""
        client = GeminiClient(api_key="test_key")
        
        history = client.get_conversation_history("non_existing_conv")
        
        assert history == []
    
    def test_get_active_conversations_stats(self):
        """Verificar obtención de estadísticas de conversaciones activas"""
        client = GeminiClient(api_key="test_key")
        
        # Crear varias conversaciones
        client.create_conversation("conv_001")
        client.create_conversation("conv_002")
        client.create_conversation("conv_003")
        
        stats = client.get_conversation_stats()
        
        assert stats['active_conversations'] == 3
        assert 'conv_001' in stats['conversation_ids']
        assert 'conv_002' in stats['conversation_ids']
        assert 'conv_003' in stats['conversation_ids']
    
    def test_conversation_error_handling(self):
        """Verificar manejo de errores en conversaciones"""
        client = GeminiClient(api_key="test_key")
        
        with patch.object(client, 'model') as mock_model:
            mock_model.start_chat.side_effect = Exception("Chat session error")
            
            # Intentar crear conversación con error
            with pytest.raises(GeminiClientError, match="Error creando sesión de chat"):
                client.create_conversation("error_conv")
    
    def test_send_prompt_with_images_and_conversation(self):
        """Verificar envío de imágenes dentro de conversación"""
        client = GeminiClient(api_key="test_key")
        
        with patch.object(client, 'model') as mock_model, \
             patch('PIL.Image.open') as mock_image_open:
            
            # Mock imagen
            mock_image = Mock()
            mock_image_open.return_value = mock_image
            
            # Mock chat session
            mock_chat_session = Mock()
            mock_response = Mock()
            mock_response.text = '{"accion": "OPERAR", "direccion": "BUY"}'
            mock_response.usage_metadata.prompt_token_count = 200
            mock_response.usage_metadata.candidates_token_count = 100
            
            mock_chat_session.send_message.return_value = mock_response
            mock_model.start_chat.return_value = mock_chat_session
            
            # Crear archivo temporal de imagen
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_img:
                image_path = tmp_img.name
            
            try:
                conversation_id = "conv_with_images"
                response = client.send_prompt(
                    "Analiza esta gráfica",
                    image_paths=[image_path],
                    conversation_id=conversation_id
                )
                
                assert response.success is True
                assert conversation_id in client._conversation_sessions
            finally:
                if os.path.exists(image_path):
                    os.unlink(image_path)
    
    def test_conversation_isolation(self):
        """Verificar que las conversaciones están aisladas entre sí"""
        client = GeminiClient(api_key="test_key")
        
        with patch.object(client, 'model') as mock_model:
            # Crear dos sesiones de chat separadas
            mock_chat_1 = Mock()
            mock_chat_2 = Mock()
            
            mock_model.start_chat.side_effect = [mock_chat_1, mock_chat_2]
            
            conv_id_1 = "isolated_conv_1"
            conv_id_2 = "isolated_conv_2"
            
            session_1 = client.create_conversation(conv_id_1)
            session_2 = client.create_conversation(conv_id_2)
            
            # Verificar que son instancias diferentes
            assert session_1 is not session_2
            assert client._conversation_sessions[conv_id_1] is session_1
            assert client._conversation_sessions[conv_id_2] is session_2
