"""
Prueba mínima de Vertex AI Gemini (REST)

Uso (PowerShell):
    python .\test_vertex_simple.py

Requiere variables de entorno:
    - GOOGLE_API_KEY
    - GEMINI_MODEL (opcional, por defecto: gemini-2.5-flash)
"""

import os
import json
import sys

from src.services.vertex_gemini_client import generate_vertex_response


def main() -> int:
    api_key = os.getenv("GOOGLE_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    endpoint = os.getenv("GEMINI_VERTEX_ENDPOINT", "https://aiplatform.googleapis.com/v1")

    if not api_key:
        # Fallback a credentials.json
        cred_path = os.path.join(os.path.dirname(__file__), 'config', 'credentials.json')
        if not os.path.exists(cred_path):
            # Intentar ruta alternativa config/ bajo repo
            cred_path = os.path.join(os.path.dirname(__file__), 'config', 'credentials.json')
        try:
            with open(cred_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                api_key = data.get('gemini', {}).get('api_key')
                if api_key:
                    print("ℹ️  GOOGLE_API_KEY no estaba en entorno; usando credentials.json")
        except Exception as e:
            pass

    if not api_key:
        print("❌ Falta GOOGLE_API_KEY (ni entorno ni credentials.json)")
        return 1

    print("🚀 Probando Vertex AI (REST)...")
    print(f"🔧 Modelo: {model}")
    print(f"🌐 Endpoint: {endpoint}")

    result = generate_vertex_response(
        system_prompt="Responde EXACTAMENTE con: OK",
        user_prompt="OK",
        temperature=0.0,
        top_p=1.0,
        timeout=30,
        model=model,
        api_key=api_key,
        endpoint=endpoint,
        max_output_tokens=48,
        safety_settings=None,
    )

    print("\n📥 Respuesta:")
    print(json.dumps({k: v for k, v in result.items() if k != "raw"}, ensure_ascii=False, indent=2))

    if result.get("status_code") == 200 and result.get("text") == "OK":
        print("\n✅ Vertex AI respondió OK. finish_reason=", result.get("finish_reason"))
        return 0
    else:
        print("\n⚠️  Respuesta inesperada o error.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
