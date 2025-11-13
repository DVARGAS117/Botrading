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
    
    def test_config_creation_defaults(self):
        """Verificar creación con valores por defecto"""
        config = GeminiConfig()
        
        assert config.model == "gemini-2.0-flash-exp"
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
    
    def test_config_validation_max_tokens(self):
        """Verificar validación de max_tokens"""
        with pytest.raises(ValueError, match="max_tokens debe ser positivo"):
            GeminiConfig(max_tokens=0)
        
        with pytest.raises(ValueError, match="max_tokens debe ser positivo"):
            GeminiConfig(max_tokens=-100)
    
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
            model="gemini-2.0-flash-exp",
            temperature=0.7,
            max_tokens=1024,
            retry_attempts=3
        )
        return GeminiClient(api_key=mock_api_key, config=config)
    
    def test_client_initialization(self, client):
        """Verificar inicialización correcta del cliente"""
        assert client is not None
        assert client.config.model == "gemini-2.0-flash-exp"
        assert client.config.temperature == 0.7
    
    def test_client_initialization_without_api_key(self):
        """Verificar error si no se proporciona API key"""
        with pytest.raises(GeminiClientError, match="API key es requerida"):
            GeminiClient(api_key=None)
    
    @patch('google.generativeai.GenerativeModel')
    def test_send_text_prompt_success(self, mock_model, client):
        """Verificar envío exitoso de prompt de texto"""
        # Mock de la respuesta de la API
        mock_response = Mock()
        mock_response.text = '{"accion": "OPERAR", "direccion": "BUY"}'
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        # Ejecutar
        prompt = "Analiza EURUSD con RSI 65.0"
        response = client.send_prompt(prompt)
        
        # Verificar
        assert response.success is True
        assert "OPERAR" in response.content
        assert response.tokens_input == 100
        assert response.tokens_output == 50
    
    @patch('google.generativeai.GenerativeModel')
    def test_send_text_prompt_with_images(self, mock_model, client):
        """Verificar envío de prompt con imágenes"""
        mock_response = Mock()
        mock_response.text = '{"accion": "NO_OPERAR"}'
        mock_response.usage_metadata.prompt_token_count = 200
        mock_response.usage_metadata.candidates_token_count = 30
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        # Ejecutar con imágenes
        prompt = "Analiza estas gráficas"
        image_paths = ["/path/chart_5m.png", "/path/chart_15m.png"]
        
        response = client.send_prompt(prompt, image_paths=image_paths)
        
        # Verificar
        assert response.success is True
        assert response.tokens_input == 200
    
    @patch('google.generativeai.GenerativeModel')
    def test_send_prompt_api_error(self, mock_model, client):
        """Verificar manejo de error de API"""
        mock_model_instance = Mock()
        mock_model_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_model_instance
        
        # Ejecutar
        response = client.send_prompt("Test prompt")
        
        # Verificar que retorna error en lugar de lanzar excepción
        assert response.success is False
        assert response.error_message is not None
        assert "API Error" in response.error_message
    
    @patch('google.generativeai.GenerativeModel')
    def test_send_prompt_timeout(self, mock_model, client):
        """Verificar manejo de timeout"""
        import time
        
        mock_model_instance = Mock()
        # Simular timeout
        mock_model_instance.generate_content.side_effect = TimeoutError("Request timeout")
        mock_model.return_value = mock_model_instance
        
        response = client.send_prompt("Test prompt")
        
        assert response.success is False
        assert response.error_type == "timeout"
    
    @patch('google.generativeai.GenerativeModel')
    def test_send_prompt_with_retry(self, mock_model, client):
        """Verificar reintentos automáticos"""
        mock_model_instance = Mock()
        
        # Primera llamada falla, segunda tiene éxito
        mock_response_success = Mock()
        mock_response_success.text = '{"accion": "OPERAR"}'
        mock_response_success.usage_metadata.prompt_token_count = 100
        mock_response_success.usage_metadata.candidates_token_count = 50
        
        mock_model_instance.generate_content.side_effect = [
            Exception("Temporary error"),
            mock_response_success
        ]
        mock_model.return_value = mock_model_instance
        
        # Ejecutar
        response = client.send_prompt("Test prompt")
        
        # Debe tener éxito después de reintentar
        assert response.success is True
        assert response.content == '{"accion": "OPERAR"}'
        assert mock_model_instance.generate_content.call_count == 2
    
    @patch('google.generativeai.GenerativeModel')
    def test_send_prompt_max_retries_exceeded(self, mock_model, client):
        """Verificar fallo después de agotar reintentos"""
        mock_model_instance = Mock()
        mock_model_instance.generate_content.side_effect = Exception("Persistent error")
        mock_model.return_value = mock_model_instance
        
        # Ejecutar
        response = client.send_prompt("Test prompt")
        
        # Debe fallar después de todos los reintentos
        assert response.success is False
        assert mock_model_instance.generate_content.call_count == client.config.retry_attempts
    
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
    
    @patch('google.generativeai.GenerativeModel')
    def test_track_usage_statistics(self, mock_model, client):
        """Verificar seguimiento de estadísticas de uso"""
        mock_response = Mock()
        mock_response.text = '{"accion": "OPERAR"}'
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
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
    
    @patch('google.generativeai.GenerativeModel')
    def test_send_prompt_invalid_json_response(self, mock_model, client):
        """Verificar manejo de respuesta JSON inválida"""
        mock_response = Mock()
        mock_response.text = "Esta no es una respuesta JSON válida"
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
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
    
    @patch('google.generativeai.GenerativeModel')
    def test_concurrent_requests(self, mock_model, client):
        """Verificar manejo de múltiples requests concurrentes"""
        mock_response = Mock()
        mock_response.text = '{"accion": "OPERAR"}'
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 50
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
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
        client = GeminiClient(api_key="test_key")
        
        # Prompt de 100k caracteres
        long_prompt = "A" * 100000
        
        # Debe manejar o truncar el prompt
        # (Implementación específica depende de límites de la API)
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = '{"accion": "NO_OPERAR"}'
            mock_response.usage_metadata.prompt_token_count = 50000
            mock_response.usage_metadata.candidates_token_count = 50
            
            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_model_instance
            
            response = client.send_prompt(long_prompt)
            # Debe manejar sin error
            assert response is not None
    
    def test_special_characters_in_prompt(self):
        """Verificar manejo de caracteres especiales"""
        client = GeminiClient(api_key="test_key")
        
        prompt_with_special = "Analiza €USD con émojis 📈📉 y símbolos ©®™"
        
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = '{"accion": "OPERAR"}'
            mock_response.usage_metadata.prompt_token_count = 100
            mock_response.usage_metadata.candidates_token_count = 50
            
            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_model_instance
            
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
