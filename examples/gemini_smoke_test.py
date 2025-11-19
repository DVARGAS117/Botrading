"""
Gemini Smoke Test - Enviar un "hola" a gemini-3-pro-preview vía Vertex REST

Requisitos:
- API key en `config/credentials.json` bajo `gemini.api_key`
- Dependencias instaladas (requests)

Ejecución:
    python -m examples.gemini_smoke_test
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
import argparse

# Permitir modelos custom en VertexAIConfig
os.environ["ALLOW_CUSTOM_GEMINI_MODEL"] = "1"

# Ajustar sys.path para importar el paquete src
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.vertex_ai_client import VertexAIClient, VertexAIConfig  # noqa: E402
from src.services.vertex_gemini_client import generate_vertex_response  # noqa: E402


def load_api_key() -> str:
    cred_path = ROOT / "config" / "credentials.json"
    if not cred_path.exists():
        print(f"No se encontró {cred_path}")
        sys.exit(1)
    try:
        data = json.loads(cred_path.read_text(encoding="utf-8"))
        key = (data.get("gemini") or {}).get("api_key")
        if not key:
            print("No se encontró 'gemini.api_key' en credentials.json")
            sys.exit(1)
        return key
    except Exception as e:
        print(f"Error leyendo credentials.json: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini smoke test (Vertex REST)")
    parser.add_argument("prompt", nargs="?", default="hola", help="Texto a enviar al modelo")
    args = parser.parse_args()

    api_key = load_api_key()
    # Configurar modelo solicitado (no forzamos texto desde el core)
    config = VertexAIConfig(model="gemini-3-pro-preview", temperature=0.2, max_tokens=256)
    prompt = args.prompt

    # 1) Llamada REST directa con force text SOLO PARA PRUEBA
    print(f"Enviando (REST directo) al modelo {config.model}: '{prompt}'\n")
    raw = generate_vertex_response(
        system_prompt=None,
        user_prompt=prompt,
        temperature=0.2,
        top_p=1.0,
        timeout=30,
        model=config.model,
        api_key=api_key,
        endpoint=config.endpoint,
        max_output_tokens=256,
        safety_settings=None,
        response_mime_type="text/plain",
        response_modalities=["TEXT"],
    )
    if int(raw.get("status_code", 0)) == 200:
        print("✅ REST Éxito\n")
        print("--- Respuesta (REST) ---")
        print(raw.get("text") or "<sin contenido>")
    else:
        print("❌ REST Fallo\n")
        print(raw.get("raw"))

    # 2) Opcional: llamada vía VertexAIClient (sin forzar text globalmente)
    client = VertexAIClient(api_key=api_key, config=config)
    print("\nProbando vía VertexAIClient (sin forzar MIME):\n")
    resp = client.send_prompt(prompt)
    if resp.success:
        print("✅ Client Éxito\n")
        print("--- Respuesta (Client) ---")
        print(resp.content or "<sin contenido>")
        print("\n--- Métricas ---")
        print(f"Tokens in: {resp.tokens_input} | Tokens out: {resp.tokens_output}")
        print(f"Latency: {resp.latency:.2f}s")
    else:
        print("❌ Client Fallo\n")
        print(f"Tipo: {resp.error_type}")
        print(f"Mensaje: {resp.error_message}")


if __name__ == "__main__":
    main()
