import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from src.core.gemini_client import GeminiClient, GeminiConfig

def load_credentials():
    try:
        with open("config/credentials.json", "r") as f:
            creds = json.load(f)
            return creds.get("gemini", {}).get("api_key")
    except Exception as e:
        print(f"Error cargando credenciales: {e}")
        return None

def main():
    print("--- Iniciando prueba de conectividad Gemini 3 Pro ---")
    
    api_key = load_credentials()
    if not api_key:
        print("❌ No se encontró API Key en config/credentials.json")
        return

    # Configuración para Gemini 3 Pro
    config = GeminiConfig(
        model="gemini-3-pro-preview",
        temperature=0.7,
        max_tokens=1024,
        timeout=600, # Timeout extendido para prueba final
        use_vertex_ai=False
    )

    print(f"Configuración: Modelo={config.model}, Timeout={config.timeout}s")

    try:
        client = GeminiClient(api_key=api_key, config=config)
        print("✅ Cliente Gemini inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando cliente: {e}")
        return

    prompt = "Hola, ¿estás operativo? Responde con un 'Sí' y la hora actual."
    print(f"\nEnviando prompt simple: '{prompt}'")
    print("Esperando respuesta...")

    try:
        start_time = datetime.now()
        response = client.send_prompt(prompt)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if response.success:
            print(f"\n✅ Respuesta recibida en {duration:.2f} segundos:")
            print("-" * 40)
            print(response.content)
            print("-" * 40)
            print(f"Tokens usados: {response.total_tokens}")
            print(f"Costo estimado: ${response.cost:.6f}")
        else:
            print(f"\n❌ Error en la respuesta (Tiempo: {duration:.2f}s):")
            print(f"Mensaje: {response.error_message}")
            print(f"Tipo: {response.error_type}")

    except Exception as e:
        print(f"\n❌ Excepción durante el envío: {e}")

if __name__ == "__main__":
    main()
