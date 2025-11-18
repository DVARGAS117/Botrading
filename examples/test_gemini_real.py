"""
Prueba directa de la API de Gemini con credenciales existentes

Este script prueba la funcionalidad real de Gemini API usando las credenciales
configuradas en config/credentials.json
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.gemini_client import GeminiClient, GeminiConfig

def load_credentials():
    """Carga las credenciales desde el archivo de configuración"""
    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'credentials.json')

    try:
        with open(credentials_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo de credenciales: {credentials_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear el archivo de credenciales: {e}")
        return None

def test_gemini_api_real():
    """Prueba real de la API de Gemini"""
    print("🔄 Probando conexión real con Gemini API...")
    print("=" * 50)

    # Cargar credenciales
    credentials = load_credentials()
    if not credentials:
        return False

    gemini_creds = credentials.get('gemini', {})
    api_key = gemini_creds.get('api_key')

    if not api_key:
        print("❌ No se encontró API key de Gemini en las credenciales")
        print("💡 Verifica config/credentials.json")
        return False

    print(f"🔑 API Key encontrada: {api_key[:10]}...{api_key[-4:]}")

    try:
        # Configuración básica para Google AI Studio
        config = GeminiConfig(
            use_vertex_ai=False,  # Usar Google AI Studio
            model="gemini-1.5-flash",  # Modelo disponible y económico
            temperature=0.7,
            max_tokens=512
        )

        print(f"⚙️  Configuración:")
        print(f"   - Modelo: {config.model}")
        print(f"   - Temperatura: {config.temperature}")
        print(f"   - Max tokens: {config.max_tokens}")
        print(f"   - Vertex AI: {config.use_vertex_ai}")

        # Crear cliente
        print("\n🔧 Inicializando cliente...")
        client = GeminiClient(api_key=api_key, config=config)

        # Prompt de prueba simple
        prompt = "Responde únicamente con: 'Conexión exitosa con Gemini API'"

        print(f"📤 Enviando prompt: '{prompt}'")

        # Enviar prompt
        response = client.send_prompt(prompt)

        print("\n📥 Respuesta recibida:")
        print("-" * 30)

        if response.success:
            print("✅ ¡CONEXIÓN EXITOSA!")
            print(f"📝 Contenido: {response.content}")
            print(f"📊 Tokens usados: {response.total_tokens}")
            print(f"💰 Costo estimado: ${response.cost:.6f}")

            # Mostrar estadísticas del cliente
            stats = client.get_usage_statistics()
            print(f"\n📈 Estadísticas del cliente:")
            print(f"   - Total de requests: {stats['total_requests']}")
            print(f"   - Requests exitosos: {stats['successful_requests']}")
            print(f"   - Latencia promedio: {stats['average_latency']:.2f}s")
            return True

        else:
            print("❌ ERROR en la respuesta")
            print(f"📝 Mensaje de error: {response.error_message}")
            if hasattr(response, 'raw_response'):
                print(f"📝 Respuesta cruda: {response.raw_response}")
            return False

    except Exception as e:
        print(f"❌ ERROR al inicializar o usar Gemini API: {str(e)}")
        print(f"🔍 Tipo de error: {type(e).__name__}")
        import traceback
        print("📋 Traceback completo:")
        traceback.print_exc()
        return False

def test_vertex_ai_config():
    """Verifica la configuración de Vertex AI (sin llamada real)"""
    print("\n🔄 Verificando configuración de Vertex AI...")
    print("=" * 50)

    credentials = load_credentials()
    if not credentials:
        return False

    # Verificar si hay configuración de Vertex AI
    gemini_creds = credentials.get('gemini', {})

    vertex_config = gemini_creds.get('vertex_ai', {})
    if not vertex_config:
        print("⚠️  No se encontró configuración de Vertex AI en credentials.json")
        print("💡 Para usar Vertex AI, agrega una sección 'vertex_ai' con:")
        print("   - project_id: Tu ID de proyecto de GCP")
        print("   - location: Región (ej: 'us-central1')")
        print("   - credentials_path: Ruta al archivo JSON de credenciales")
        return False

    print("✅ Configuración de Vertex AI encontrada:")
    print(f"   - Project ID: {vertex_config.get('project_id', 'NO CONFIGURADO')}")
    print(f"   - Location: {vertex_config.get('location', 'NO CONFIGURADO')}")
    print(f"   - Credentials path: {vertex_config.get('credentials_path', 'NO CONFIGURADO')}")

    # Verificar que el archivo de credenciales existe
    creds_path = vertex_config.get('credentials_path')
    if creds_path and os.path.exists(creds_path):
        print("✅ Archivo de credenciales encontrado")
        return True
    else:
        print("❌ Archivo de credenciales NO encontrado")
        print(f"   Ruta esperada: {creds_path}")
        return False

if __name__ == "__main__":
    print("🚀 PRUEBA REAL DE GEMINI API PARA BOTRADING")
    print("=" * 60)

    # Probar Gemini API real
    gemini_success = test_gemini_api_real()

    # Verificar configuración de Vertex AI
    vertex_config_ok = test_vertex_ai_config()

    print("\n" + "=" * 60)
    print("📊 RESULTADOS FINALES:")

    if gemini_success:
        print("✅ Gemini API (Google AI Studio): FUNCIONANDO")
    else:
        print("❌ Gemini API (Google AI Studio): ERROR")

    if vertex_config_ok:
        print("✅ Vertex AI: CONFIGURADO (pero no probado)")
    else:
        print("❌ Vertex AI: NO CONFIGURADO")

    if gemini_success:
        print("\n🎉 ¡El sistema está listo para usar Gemini API!")
        print("💡 Puedes configurar Vertex AI más tarde si lo necesitas.")
    else:
        print("\n⚠️  Revisa la configuración de credenciales y vuelve a intentar.")
        sys.exit(1)