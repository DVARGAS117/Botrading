"""Debug de respuesta de Vertex AI."""

import os
import json
from src.services.vertex_gemini_client import generate_vertex_response

api_key = os.getenv("GOOGLE_API_KEY") or "AQ.Ab8RN6LqcYC63Ac0b0k-WflklnvDfB2l4IMG5IcK7UjQ9qOkZw"

print("🔍 Debug de Vertex AI response")
print("-" * 60)

result = generate_vertex_response(
    system_prompt=None,
    user_prompt="Responde con JSON: {'accion': 'NO_OPERAR', 'razonamiento': 'test'}",
    temperature=0.7,
    top_p=0.95,
    timeout=30,
    model="gemini-3-pro-preview",
    api_key=api_key,
    endpoint="https://aiplatform.googleapis.com/v1",
    max_output_tokens=500,
    safety_settings=None,
    response_mime_type="application/json",
    response_modalities=["TEXT"],
)

print("\n📊 Resultado parseado:")
print(json.dumps({k: v for k, v in result.items() if k != "raw"}, indent=2, ensure_ascii=False))

print("\n📄 Raw response (primeros 1000 chars):")
raw = result.get("raw", {})
print(json.dumps(raw, indent=2, ensure_ascii=False)[:1000])
