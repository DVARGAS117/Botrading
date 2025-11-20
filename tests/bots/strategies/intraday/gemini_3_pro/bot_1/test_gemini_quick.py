"""Test rápido de conexión a Gemini 3 Pro API.

Este test verifica que el API responde correctamente con un prompt mínimo.
"""

import os
import pytest
from src.core.vertex_ai_client import VertexAIClient, VertexAIConfig


def test_gemini_api_quick():
    """Test rápido de API de Gemini 3 Pro."""
    # Verificar API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY no configurada")
    
    # Configurar cliente
    config = VertexAIConfig(
        model="gemini-3-pro-preview",
        temperature=0.7,
        max_tokens=200,
        timeout=30,
    )
    
    client = VertexAIClient(config=config)
    
    # Prompt simple
    prompt = """Analiza EURUSD y responde EXACTAMENTE en este formato JSON:
{
  "accion": "NO_OPERAR",
  "razonamiento": "Test de API"
}"""
    
    # Llamar API
    response = client.send_prompt(prompt)
    
    # Verificar respuesta
    assert response.success is True
    assert response.content is not None
    assert len(response.content) > 0
    assert response.tokens_input > 0
    assert response.tokens_output > 0
    
    print(f"\n✅ API respondió correctamente:")
    print(f"   Tokens input: {response.tokens_input}")
    print(f"   Tokens output: {response.tokens_output}")
    print(f"   Costo: ${response.cost:.4f}")
    print(f"   Latencia: {response.latency:.2f}s")
    print(f"   Contenido: {response.content[:100]}...")
