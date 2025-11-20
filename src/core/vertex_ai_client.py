"""
VertexAIClient - Cliente para comunicación con Vertex AI (Gemini vía REST)

Este cliente ofrece una interfaz similar a `GeminiClient.send_prompt`, pero
utilizando el endpoint REST de Vertex AI documentado en `context/VERTEX_GEMINI_API_GUIDE.md`.

Depende de `src.services.vertex_gemini_client.generate_vertex_response`.
"""

from dataclasses import dataclass
from typing import List, Optional
import os
import time
import json
from pathlib import Path

import src.services.vertex_gemini_client as vertex_module
from src.core.gemini_client import GeminiResponse
import logging


@dataclass
class VertexAIConfig:
    model: str = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
    temperature: float = 0.0
    # Triplicado desde config original (8192 -> 24576)
    max_tokens: int = 24576
    top_p: float = 1.0
    # Ampliar timeout para razonamiento profundo (30 -> 120 segundos)
    timeout: int = 120
    endpoint: str = os.getenv("GEMINI_VERTEX_ENDPOINT", "https://aiplatform.googleapis.com/v1")
    project_id: Optional[str] = os.getenv("VERTEX_PROJECT_ID")
    location: str = os.getenv("VERTEX_LOCATION", "us-central1")

    def __post_init__(self):
        """Enforce del modelo por defecto gemini-3-pro-preview salvo override manual.

        Override permitido si:
        - Se pasa explícitamente un modelo distinto al instanciar VertexAIConfig (param model) Y
        - La variable de entorno ALLOW_CUSTOM_GEMINI_MODEL == "1"

        De lo contrario, se fuerza gemini-3-pro-preview.
        
        Modelos permitidos por defecto:
        - gemini-3-pro-preview
        - gemini-2.5-pro
        """
        allowed_models = ["gemini-3-pro-preview", "gemini-2.5-pro"]
        allow_custom = os.getenv("ALLOW_CUSTOM_GEMINI_MODEL") == "1"
        
        if self.model not in allowed_models and not allow_custom:
            raise ValueError(
                f"Modelo '{self.model}' no permitido. Usa uno de {allowed_models} o establece ALLOW_CUSTOM_GEMINI_MODEL=1 para override manual."
            )
        # Si ya se proporcionó project_id y el endpoint no incluye la ruta de proyecto, complétalo
        if self.project_id and "/projects/" not in self.endpoint:
            self.endpoint = f"https://aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}"


class VertexAIClient:
    """
    Cliente para enviar prompts a Vertex AI y obtener una GeminiResponse homogénea.
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[VertexAIConfig] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Falta API key. Usa parámetro api_key o variable GOOGLE_API_KEY.")
        self.config = config or VertexAIConfig()

        # Si no hay project_id configurado, intentar cargarlo de config/ia_config.json
        if not self.config.project_id:
            try:
                cfg_path = Path("config/ia_config.json")
                if cfg_path.exists():
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        ia_cfg = json.load(f)
                    proj = (ia_cfg.get("project_id") or "").strip()
                    loc = (ia_cfg.get("location") or self.config.location).strip()
                    # Ignorar placeholder por defecto
                    if proj and proj.upper() != "YOUR_GCP_PROJECT_ID":
                        self.config.project_id = proj
                        self.config.location = loc or self.config.location
            except Exception:
                # No bloquear por problemas de lectura; seguirá usando endpoint base
                pass

        # Si tenemos project_id y el endpoint no incluye la ruta de proyecto, constrúyelo
        if self.config.project_id and "/projects/" not in self.config.endpoint:
            self.config.endpoint = f"https://aiplatform.googleapis.com/v1/projects/{self.config.project_id}/locations/{self.config.location}"

    def send_prompt(self, prompt: str, image_paths: Optional[List[str]] = None) -> GeminiResponse:
        if not prompt or not prompt.strip():
            return GeminiResponse(success=False, error_message="Prompt no puede estar vacío", error_type="validation_error")

        start = time.time()
        result = vertex_module.generate_vertex_response(
            system_prompt=None,
            user_prompt=prompt,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            timeout=self.config.timeout,
            model=self.config.model,
            api_key=self.api_key,
            endpoint=self.config.endpoint,
            max_output_tokens=self.config.max_tokens,
            safety_settings=None,
            # Para gemini-3 se recomienda forzar salida en JSON de texto
            response_mime_type="application/json",
            response_modalities=["TEXT"],
        )
        latency = time.time() - start

        if int(result.get("status_code", 0)) == 200:
            usage = result.get("usage", {}) or {}
            tokens_in = int(usage.get("promptTokenCount") or 0)
            tokens_out = int(usage.get("candidatesTokenCount") or 0)
            finish = result.get('finish_reason')

            # Estimación de costos para gemini-3-pro-preview (misma lógica que GeminiClient)
            cost = None
            if self.config.model.startswith("gemini-3-pro-preview"):
                # Tarifas por 1K tokens (estándar vs largo contexto)
                STD_IN = 2.00 / 1000
                STD_OUT = 12.00 / 1000
                LONG_IN = 4.00 / 1000
                LONG_OUT = 18.00 / 1000
                LONG_THRESHOLD = 128_000
                if tokens_in > LONG_THRESHOLD:
                    in_rate = LONG_IN
                    out_rate = LONG_OUT
                    pricing_tier = "long_context"
                else:
                    in_rate = STD_IN
                    out_rate = STD_OUT
                    pricing_tier = "standard"
                cost = round((tokens_in/1000)*in_rate + (tokens_out/1000)*out_rate, 8)
                logging.getLogger(__name__).info(
                    f"Uso IA: tier={pricing_tier} prompt_tokens={tokens_in} output_tokens={tokens_out} cost=${cost} finish_reason={finish}"
                )
            else:
                logging.getLogger(__name__).info(
                    f"Uso IA: prompt_tokens={tokens_in} output_tokens={tokens_out} finish_reason={finish}"
                )

            return GeminiResponse(
                success=True,
                content=result.get("text", ""),
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                cost=cost,
                latency=latency,
            )

        # Error
        return GeminiResponse(
            success=False,
            error_message=f"HTTP {result.get('status_code')}: {result.get('raw')}",
            error_type="api_error",
            latency=latency,
        )
