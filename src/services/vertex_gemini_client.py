"""
Cliente REST para Vertex AI Gemini

Expone la función `generate_vertex_response` que realiza una llamada HTTP a
`aiplatform.googleapis.com` usando una API Key de Google Cloud con acceso a Vertex AI.

La respuesta se normaliza en un diccionario con los campos principales:
- text: texto concatenado de candidates[0].content.parts[*].text
- finish_reason: motivo de finalización del modelo
- usage: metadata de uso (tokens)
- status_code: código HTTP devuelto por la API

Nota: Este cliente es independiente del SDK `google-generativeai` y usa `requests`.
"""

from typing import Any, Dict, List, Optional
import requests
import json
import logging


def _build_url(endpoint: str, model: str, api_key: str) -> str:
    base = endpoint.rstrip("/")
    return f"{base}/publishers/google/models/{model}:generateContent?key={api_key}"


def _build_payload(
    system_prompt: Optional[str],
    user_prompt: str,
    temperature: float,
    top_p: float,
    max_output_tokens: int,
    safety_settings: Optional[List[Dict[str, Any]]] = None,
    response_mime_type: Optional[str] = None,
    response_modalities: Optional[List[str]] = None,
) -> Dict[str, Any]:
    contents = [
        {
            "role": "user",
            "parts": [{"text": user_prompt}],
        }
    ]

    gen_cfg: Dict[str, Any] = {
        "temperature": temperature,
        "topP": top_p,
        "maxOutputTokens": max_output_tokens,
    }

    # Forzar salida de texto cuando se solicite (útil para gemini-3)
    if response_mime_type:
        gen_cfg["responseMimeType"] = response_mime_type
    if response_modalities:
        gen_cfg["responseModalities"] = response_modalities

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": gen_cfg,
    }

    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    if safety_settings:
        payload["safetySettings"] = safety_settings

    return payload


def _parse_response(resp_json: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae texto y metadatos de la respuesta.

    Fallbacks añadidos para modelos gemini-3 que pueden devolver estructuras
    diferentes (p.ej. parts sin 'text', inlineData, functionCall, etc.).
    Si no se encuentra texto, se serializa el primer candidato para inspección.
    """
    text = ""
    finish_reason = None
    usage = resp_json.get("usageMetadata") or {}

    candidates = resp_json.get("candidates") or []
    if candidates:
        cand0 = candidates[0] or {}
        finish_reason = cand0.get("finishReason")
        content = cand0.get("content") or {}
        parts = content.get("parts") or []
        collected: List[str] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            # Prioridad: 'text'
            if "text" in part and part["text"]:
                collected.append(str(part["text"]))
                continue
            # inlineData (binario) -> ignorar pero marcar
            if "inlineData" in part:
                collected.append("[inlineData]")
                continue
            # functionCall -> representar
            if "functionCall" in part:
                fc = part["functionCall"]
                name = fc.get("name", "functionCall")
                collected.append(f"[functionCall:{name}]")
                continue
            # executableCode / codeBlock
            if "executableCode" in part:
                collected.append("[executableCode]")
                continue
            if "code" in part:
                collected.append(part.get("code", "[code]") )
                continue
            # Si nada coincide, añadir representación compacta
            collected.append(json.dumps(part, ensure_ascii=False)[:200])

        text = "".join(collected).strip()

        # Fallback: si sigue vacío, serializar candidato completo
        if not text:
            try:
                text = json.dumps(cand0, ensure_ascii=False)[:500]
            except Exception:
                text = ""

    # Logging de depuración si vacío
    if not text:
        logging.getLogger(__name__).debug(
            "Respuesta Gemini sin texto legible; estructura raw=%s",
            json.dumps(resp_json, ensure_ascii=False)[:800]
        )

    return {
        "text": text,
        "finish_reason": finish_reason,
        "usage": usage,
    }


def generate_vertex_response(
    system_prompt: Optional[str],
    user_prompt: str,
    temperature: float,
    top_p: float,
    timeout: int,
    model: str,
    api_key: str,
    endpoint: str = "https://aiplatform.googleapis.com/v1",
    max_output_tokens: int = 1024,
    safety_settings: Optional[List[Dict[str, Any]]] = None,
    response_mime_type: Optional[str] = None,
    response_modalities: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Realiza una llamada a Vertex AI Gemini (REST) y retorna datos normalizados.

    Args:
        system_prompt: Instrucción del sistema (opcional)
        user_prompt: Prompt del usuario
        temperature: Temperatura de generación
        top_p: Top-P sampling
        timeout: Timeout de la petición en segundos
        model: Nombre del modelo (p.ej. gemini-2.5-pro)
        api_key: API key con acceso a Vertex AI
        endpoint: Endpoint base de Vertex (default v1)
        max_output_tokens: Máximo de tokens en la respuesta
        safety_settings: Configuración de seguridad (opcional)

    Returns:
        Dict con: text, finish_reason, usage, status_code, raw (response JSON)
    """
    url = _build_url(endpoint=endpoint, model=model, api_key=api_key)
    payload = _build_payload(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_output_tokens,
        safety_settings=safety_settings,
        response_mime_type=response_mime_type,
        response_modalities=response_modalities,
    )

    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)

    try:
        data = resp.json()
    except Exception:
        data = {"error": resp.text}

    parsed = _parse_response(data if isinstance(data, dict) else {})
    parsed.update({
        "status_code": resp.status_code,
        "raw": data,
        "model": model,
        "endpoint": endpoint,
    })
    return parsed
