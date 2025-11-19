import json
from typing import Any, Dict


def test_generate_vertex_response_builds_request_and_parses_response(monkeypatch):
    # Import deferred after mock setup to avoid real imports
    import importlib

    # Arrange: mock requests.post
    fake_response_payload: Dict[str, Any] = {
        "candidates": [
            {
                "content": {"parts": [{"text": "OK"}]},
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 5,
            "candidatesTokenCount": 2,
            "totalTokenCount": 7,
        },
    }

    class FakeResp:
        status_code = 200

        def json(self):
            return fake_response_payload

        @property
        def text(self):
            return json.dumps(fake_response_payload)

    calls: Dict[str, Any] = {}

    def fake_post(url, json=None, headers=None, timeout=None):  # type: ignore
        calls["url"] = url
        calls["json"] = json
        calls["headers"] = headers
        calls["timeout"] = timeout
        return FakeResp()

    monkeypatch.setattr("requests.post", fake_post)

    # Act: call function
    module = importlib.import_module("src.services.vertex_gemini_client")
    result = module.generate_vertex_response(
        system_prompt="Responde EXACTAMENTE con: OK",
        user_prompt="OK",
        temperature=0.7,
        top_p=0.9,
        timeout=30,
        model="gemini-2.5-pro",
        api_key="AQ.fake_key",
        endpoint="https://aiplatform.googleapis.com/v1",
        max_output_tokens=48,
        safety_settings=None,
    )

    # Assert: HTTP call shape
    expected_url = (
        "https://aiplatform.googleapis.com/v1/publishers/google/models/"
        "gemini-2.5-flash:generateContent?key=AQ.fake_key"
    )
    assert calls["url"] == expected_url
    assert calls["timeout"] == 30
    assert calls["headers"]["Content-Type"] == "application/json"
    payload = calls["json"]
    assert "contents" in payload and "generationConfig" in payload

    # Assert: parsed response
    assert result["status_code"] == 200
    assert result["text"] == "OK"
    assert result["finish_reason"] == "STOP"
    assert result["usage"]["promptTokenCount"] == 5
    assert result["usage"]["candidatesTokenCount"] == 2
    assert result["usage"]["totalTokenCount"] == 7
