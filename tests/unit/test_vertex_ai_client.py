import json
from typing import Any, Dict


def test_vertex_ai_client_success(monkeypatch):
    # Mock REST generate function to avoid network
    def fake_generate_vertex_response(**kwargs):  # type: ignore
        return {
            "status_code": 200,
            "text": "OK",
            "finish_reason": "STOP",
            "usage": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 5,
                "totalTokenCount": 15,
            },
            "raw": {},
        }

    monkeypatch.setenv("GOOGLE_API_KEY", "AQ.fake")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")

    import importlib
    rest_module = importlib.import_module("src.services.vertex_gemini_client")
    monkeypatch.setattr(rest_module, "generate_vertex_response", fake_generate_vertex_response)

    # Import client after monkeypatch
    client_module = importlib.import_module("src.core.vertex_ai_client")
    client = client_module.VertexAIClient()

    resp = client.send_prompt("Responde EXACTAMENTE con: OK")
    assert resp.success is True
    assert resp.content == "OK"
    assert resp.tokens_input == 10
    assert resp.tokens_output == 5


def test_vertex_ai_client_missing_key(monkeypatch):
    # Ensure no key present
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    import importlib
    with __import__("pytest").raises(ValueError):
        import src.core.vertex_ai_client as vac
        vac.VertexAIClient()
