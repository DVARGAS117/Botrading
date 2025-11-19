"""
Prueba básica de Vertex AI para BOTRADING

Este script demuestra cómo usar Vertex AI con el GeminiClient.
Requiere credenciales válidas de Google Cloud Platform.

Uso:
    python examples/vertex_ai_test.py

Nota: Asegúrate de tener configuradas las credenciales de Vertex AI
en config/credentials.json antes de ejecutar.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.gemini_client import GeminiClient, GeminiConfig

def test_vertex_ai_basic():
    """Prueba básica de conexión con Vertex AI"""
    print("🔄 Probando conexión con Vertex AI...")

    try:
        # Configuración para Vertex AI
        config = GeminiConfig(
            use_vertex_ai=True,
            project_id="tu-proyecto-gcp-12345",  # Reemplaza con tu project ID
            location="us-central1",
            credentials_path="C:\\Users\\TuUsuario\\.gcp\\vertex-ai-credentials.json",  # Reemplaza con tu ruta
            model="gemini-2.5-pro",
            temperature=0.7,
            max_tokens=1024
        )

        # Crear cliente
        client = GeminiClient(config=config)

        # Enviar prompt de prueba
        prompt = "Hola, ¿puedes confirmar que estás usando Vertex AI? Responde con una frase corta."
        response = client.send_prompt(prompt)

        if response.success:
            print("✅ Conexión exitosa con Vertex AI!")
            print(f"📝 Respuesta: {response.content}")
            print(f"📊 Tokens usados: {response.total_tokens}")
            print(f"💰 Costo estimado: ${response.cost:.6f}")

            # Mostrar estadísticas
            stats = client.get_usage_statistics()
            print("📈 Estadísticas de uso:"            print(f"   - Total requests: {stats['total_requests']}")
            print(f"   - Requests exitosos: {stats['successful_requests']}")
            print(f"   - Latencia promedio: {stats['average_latency']:.2f}s")

        else:
            print("❌ Error en la conexión con Vertex AI")
            print(f"Error: {response.error_message}")
            return False

    except Exception as e:
        print(f"❌ Error al inicializar Vertex AI: {str(e)}")
        print("💡 Asegúrate de:")
        print("   1. Tener credenciales válidas de Google Cloud")
        print("   2. El project_id correcto")
        print("   3. La ruta al archivo de credenciales correcta")
        print("   4. Vertex AI API habilitada en tu proyecto GCP")
        return False

    return True

def test_google_ai_studio_fallback():
    """Prueba de fallback a Google AI Studio"""
    print("\n🔄 Probando fallback a Google AI Studio...")

    try:
        # Configuración para Google AI Studio
        config = GeminiConfig(
            use_vertex_ai=False,  # Usar Google AI Studio
            model="gemini-2.5-pro",
            temperature=0.7,
            max_tokens=1024
        )

        # Crear cliente con API key
        api_key = os.getenv("GEMINI_API_KEY") or "tu-api-key-aqui"  # Reemplaza con tu API key
        client = GeminiClient(api_key=api_key, config=config)

        # Enviar prompt de prueba
        prompt = "Hola, ¿puedes confirmar que estás usando Google AI Studio? Responde con una frase corta."
        response = client.send_prompt(prompt)

        if response.success:
            print("✅ Conexión exitosa con Google AI Studio!")
            print(f"📝 Respuesta: {response.content}")
            print(f"📊 Tokens usados: {response.total_tokens}")
            print(f"💰 Costo estimado: ${response.cost:.6f}")
        else:
            print("❌ Error en la conexión con Google AI Studio")
            print(f"Error: {response.error_message}")
            print("💡 Obtén tu API key en: https://aistudio.google.com/app/apikey")
            return False

    except Exception as e:
        print(f"❌ Error al inicializar Google AI Studio: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    print("🚀 Prueba de APIs de Gemini para BOTRADING")
    print("=" * 50)

    # Probar Vertex AI primero (recomendado)
    vertex_success = test_vertex_ai_basic()

    # Si Vertex AI falla, probar Google AI Studio
    if not vertex_success:
        print("\n⚠️  Vertex AI no disponible, probando Google AI Studio...")
        studio_success = test_google_ai_studio_fallback()

        if studio_success:
            print("\n✅ Google AI Studio funciona correctamente")
            print("💡 Para usar Vertex AI, configura tus credenciales de GCP")
        else:
            print("\n❌ Ninguna API disponible")
            print("💡 Revisa la configuración en config/credentials.json")
            sys.exit(1)
    else:
        print("\n✅ Vertex AI configurado correctamente!")
        print("💡 Puedes cambiar entre Vertex AI y Google AI Studio")
        print("   modificando 'use_vertex_ai' en config/ia_config.json")