**Guía Rápida: Integración y Uso de Vertex Gemini en este Proyecto**

- **Objetivo:** explicar cómo este repo se conecta a Gemini vía Vertex AI, qué variables de entorno necesita, cómo probarlo y resolver problemas comunes.
- **Ámbito:** llamadas REST a `aiplatform.googleapis.com` (Vertex) y referencia al uso del SDK `google-generativeai` que también existe en el repo.

**Arquitectura**
- **Vertex REST (oficial en este repo):**
  - `src/services/vertex_gemini_client.py` arma la URL `https://aiplatform.googleapis.com/v1/publishers/google/models/{MODEL}:generateContent?key={GOOGLE_API_KEY}` y hace `POST` con `requests`.
  - `src/core/vertex_ai_client.py` ofrece una interfaz `send_prompt(...)` y retorna `GeminiResponse` para homogeneidad con el resto del core.
- **SDK AI Studio (opcional):** algunos ejemplos siguen usando `google.generativeai` vía `src/core/gemini_client.py`. No se elimina, pero el flujo por defecto es Vertex.

**Variables de Entorno Relevantes (.env)**
- **`GOOGLE_API_KEY`:** clave API con acceso a Vertex (formato puede variar; es válido el prefijo `AQ.`). Debe permitir llamadas a `aiplatform.googleapis.com`.
- **`GEMINI_MODEL`:** por defecto forzado a `gemini-2.5-pro`. Si estableces otro valor y quieres permitirlo, debes configurar también `ALLOW_CUSTOM_GEMINI_MODEL=1`.
- **`ALLOW_CUSTOM_GEMINI_MODEL` (opcional):** si vale `1`, permite usar un modelo distinto a `gemini-2.5-pro`.
- **`GEMINI_VERTEX_ENDPOINT` (opcional):** por defecto `https://aiplatform.googleapis.com/v1`.
- **`GEMINI_API_KEY` (opcional):** solo si deseas usar Google AI Studio como fallback.
- **`ALLOW_GEMINI_FALLBACK` (opcional):** si vale `1`, cuando falle la inicialización del cliente Vertex se intenta crear un cliente Gemini SDK (solo para continuidad; Vertex sigue siendo el camino oficial).

**Flujo de Llamada (Vertex)**
- **Bajo nivel:** `src/services/vertex_gemini_client.py` con `generate_vertex_response(...)`.
- **Alto nivel recomendado:** `src/core/vertex_ai_client.py` con `VertexAIClient.send_prompt(prompt)` que devuelve `GeminiResponse` (mismos campos que `GeminiClient`).
- **Payload:** incluye `contents`, `generationConfig` y opcionalmente `systemInstruction` y `safetySettings`.
- **Respuesta:** se parsea `candidates[*].content.parts[*].text`, `finishReason` y `usageMetadata` (tokens de entrada/salida y total).

**Prueba Rápida (recomendada)**
- Script mínimo: `test_vertex_simple.py` (usa `GOOGLE_API_KEY` o `config/credentials.json`).
- Ejecutar en PowerShell (con el venv activado):

```powershell
python .\test_vertex_simple.py
```

- Salida esperada: `HTTP 200`, `Respuesta: OK`, `finishReason: STOP`, métricas en `usageMetadata` y el modelo/endpoint usados.

**Ejemplo cURL (REST Vertex)**
Reemplaza `YOUR_API_KEY` y el modelo si corresponde.

```bash
curl -X POST "https://aiplatform.googleapis.com/v1/publishers/google/models/gemini-2.5-flash:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "contents": [{
          "role": "user",
          "parts": [{"text": "Responde EXACTAMENTE con: OK"}]
        }],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 48}
      }'
```

**Pasos para el Equipo (Checklist de Conexión)**
- **1. Habilitar API:** en Google Cloud Console, habilitar “Vertex AI API” para el proyecto de la clave.
- **2. Clave válida:** usar `GOOGLE_API_KEY` que tenga permisos sobre `aiplatform.googleapis.com` (las claves pueden no empezar por `AIza...`; `AQ.` también es válido).
- **3. Restricciones de clave (opcional):** si se restringe por API, incluir “Vertex AI API”. Si se restringe por IP/origen, considerar el host que llama.
- **4. Modelo forzado:** el sistema exige `gemini-2.5-pro`. Para usar otro (bajo tu responsabilidad), exporta además `ALLOW_CUSTOM_GEMINI_MODEL=1`.
- **5. Cliente alto nivel:** para bots y módulos del core, preferir `VertexAIClient` (homogéneo con `GeminiResponse`).
- **6. Probar con `test_vertex_simple.py`:** debe devolver `HTTP 200` y texto `OK`.

**Solución de Problemas**
- **HTTP 401 (Unauthorized) / 403 (Permission denied):**
  - Clave inválida o restringida; verificar que “Vertex AI API” esté habilitada y que la clave no bloquee `aiplatform.googleapis.com`.
  - Rotar o crear nueva clave y actualizar `.env`.
- **HTTP 400 (Invalid model / request):**
  - Modelo mal escrito o parámetros fuera de rango. Validar contra la doc oficial.
- **HTTP 404:**
  - Ruta incorrecta; validar `.../publishers/google/models/{MODEL}:generateContent`.
- **HTTP 429 (Rate limit):**
  - Ajustar frecuencia o solicitar aumento de cuota.

**Verificar a qué Proyecto Pertenece la Clave (opcional)**
- Requiere `gcloud` autenticado. Útil para confirmar que la cadena de clave apunta al proyecto correcto.

```powershell
gcloud auth login
gcloud services api-keys lookup "<GOOGLE_API_KEY>"
```

**Referencias Oficiales**
- Vertex Gemini (modelo/REST): https://cloud.google.com/vertex-ai/generative-ai/model-reference/gemini
- Gestión de claves API (Google Cloud): https://cloud.google.com/docs/authentication/api-keys
- Gemini API (AI Studio): https://ai.google.dev/gemini-api/docs

**Notas**
- Este repo combina dos integraciones: Vertex (REST) y SDK `google-generativeai`. La prueba `test_vertex_simple.py` valida específicamente Vertex.
- La presencia de `usageMetadata` con `promptTokenCount`/`candidatesTokenCount` y `finishReason` en la respuesta es característica del esquema Vertex.
 - La clase base de bots (`BaseBotOperations`) ya usa `VertexAIClient` por defecto. Solo Bot1 (estrategia numérica) está activo; los demás bots aún no han sido migrados.
 - Para activar fallback temporal al SDK Gemini si Vertex no inicializa, exporta `ALLOW_GEMINI_FALLBACK=1`.

**Estado de Migración a Vertex**
| Componente | Estado | Detalle |
|------------|--------|---------|
| Cliente bajo nivel REST | ✅ | `generate_vertex_response` estable |
| Cliente alto nivel Vertex | ✅ | `VertexAIClient` con enforcement de modelo |
| BaseBotOperations | ✅ | Usa Vertex por defecto, fallback opcional Gemini |
| Bot1 (Strategy) | ✅ | Utiliza flujo Vertex vía clase base |
| Bot2-Bot5 | ⏳ | Pendiente de implementación/migración |
| Métricas de costos Vertex | ⏳ | Por definir (actualmente sin cálculo) |
| Documentación fallback | ✅ | Variable `ALLOW_GEMINI_FALLBACK` añadida |

Hasta que los demás bots estén implementados, cualquier referencia a operación multi-bot asume solo Bot1 activo.
