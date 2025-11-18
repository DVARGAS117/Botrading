# Vertex AI vs Google AI Studio - Análisis para BOTRADING

## Situación Actual

El proyecto usa `google-generativeai` (Google AI Studio) pero el usuario tiene credenciales de **Google Cloud Platform / Vertex AI**.

## Diferencias Clave

### Google AI Studio (Implementación ACTUAL)

**Librería:**
```python
import google.generativeai as genai
genai.configure(api_key="AIzaSy...")
```

**Autenticación:**
- ✅ API Key simple (formato: `AIzaSy...`)
- ❌ NO funciona con credenciales de Google Cloud
- ❌ NO funciona con Service Accounts

**Costos:**
- ✅ **GRATIS** hasta 60 req/min, 1,500 req/día
- ✅ Ideal para desarrollo y testing
- ❌ Límites estrictos para producción

**Setup:**
1. Ve a https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copia y pega en `credentials.json`

---

### Vertex AI (Lo que el usuario TIENE)

**Librería:**
```python
from vertexai.generative_models import GenerativeModel
import vertexai

vertexai.init(project="tu-proyecto-gcp", location="us-central1")
model = GenerativeModel("gemini-2.0-flash-exp")
```

**Autenticación:**
- ✅ Service Account JSON
- ✅ Application Default Credentials (ADC)
- ✅ OAuth 2.0
- ❌ NO funciona con API keys simples

**Costos:**
- ✅ Sin límites de rate (depende de quota de proyecto)
- ✅ Mejor para producción
- ⚠️ **DE PAGO** (aunque Gemini 2.0 Flash está gratis en preview)
- Requiere proyecto GCP con facturación habilitada

**Setup:**
1. Tienes proyecto en Google Cloud Console
2. Habilitar Vertex AI API
3. Crear Service Account
4. Descargar JSON de credenciales
5. Configurar `GOOGLE_APPLICATION_CREDENTIALS`

---

## Comparación para BOTRADING

### Escenario 1: Desarrollo y Testing (0-6 meses)

**Recomendación: Google AI Studio**

| Aspecto | Google AI Studio | Vertex AI |
|---------|------------------|-----------|
| **Setup** | 2 minutos | 30+ minutos |
| **Costo** | $0 | $0* (preview) pero necesitas billing |
| **Límites** | 1,500 req/día | Sin límites prácticos |
| **Complejidad** | Muy simple | Medio-alta |
| **Ideal para** | ✅ Testing Bot 1-5 | ❌ Overkill |

\* Gemini Flash gratis en preview, pero requieres tarjeta de crédito

### Escenario 2: Producción (6+ meses, múltiples bots)

**Recomendación: Vertex AI**

| Aspecto | Google AI Studio | Vertex AI |
|---------|------------------|-----------|
| **Setup** | Ya configurado | Migración necesaria |
| **Costo** | $0 (con límites) | ~$5-20/mes estimado |
| **Límites** | 60 req/min | 300+ req/min |
| **Monitoring** | Básico | ✅ Cloud Monitoring completo |
| **Ideal para** | ❌ Límites bajos | ✅ Producción real |

---

## Estimación de Uso BOTRADING

### Setup Actual (5 bots)
- 5 bots × 12 consultas/hora × 16 horas = **960 req/día**
- Promedio 500 tokens input + 200 output = **672,000 tokens/día**

### ✅ Google AI Studio: SUFICIENTE
- Límite: 1,500 req/día → Sobran 540 requests
- Límite: 100,000 tokens/día → ⚠️ **EXCEDIDO por 6.7x**

### ✅ Vertex AI: MÁS QUE SUFICIENTE
- Límite: Sin límites prácticos de requests
- Límite: Quota por proyecto (configurable, típicamente 10M+ tokens/día)

---

## Decisión Recomendada

### Para AHORA (próximos 3 meses):

**Usa Google AI Studio** porque:
1. ✅ Setup en 2 minutos vs 30+ minutos
2. ✅ Totalmente gratis
3. ✅ Suficiente para testing de Bot 1
4. ✅ Puedes migrar a Vertex AI después

### Para PRODUCCIÓN (cuando todos los bots funcionen):

**Migrar a Vertex AI** porque:
1. ✅ Ya tienes las credenciales
2. ✅ Sin límites de tokens
3. ✅ Mejor monitoring y control
4. ✅ Integración con Google Cloud

---

## Implementación Dual (Solución Híbrida)

Puedo modificar `GeminiClient` para soportar **AMBOS**:

```python
class GeminiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        vertex_ai: bool = False,  # 🆕 Flag para usar Vertex AI
        project_id: Optional[str] = None,  # 🆕 Para Vertex AI
        location: str = "us-central1"  # 🆕 Para Vertex AI
    ):
        if vertex_ai:
            # Usar Vertex AI con tus credenciales actuales
            self._init_vertex_ai(project_id, location)
        else:
            # Usar Google AI Studio (actual)
            self._init_google_ai(api_key)
```

**Configuración en `credentials.json`:**
```json
{
    "gemini": {
        "use_vertex_ai": false,
        "api_key": "AIzaSy...",  // Para Google AI Studio
        "project_id": "tu-proyecto-gcp",  // Para Vertex AI
        "location": "us-central1"  // Para Vertex AI
    }
}
```

---

## Próximos Pasos

### Opción A: Rápido (5 minutos) - USA ESTO AHORA
1. Ve a https://aistudio.google.com/app/apikey
2. Crea API key (formato: `AIzaSy...`)
3. Actualiza `config/credentials.json`:
   ```json
   "gemini": {
       "api_key": "AIzaSy_TU_NUEVA_KEY"
   }
   ```
4. Ejecuta: `python -m src.bots.bot_1.main --single-cycle --force-trading`

### Opción B: Completo (30+ minutos) - Para después
1. Modifico `gemini_client.py` para soportar Vertex AI
2. Agregas tus credenciales de Google Cloud
3. Actualizas `requirements.txt` para incluir `google-cloud-aiplatform`
4. Configuras `GOOGLE_APPLICATION_CREDENTIALS`

---

## Mi Recomendación

**Para HOY:**
- ✅ Usa Google AI Studio (Opción A)
- ✅ Testea Bot 1 con `--force-trading`
- ✅ Valida toda la lógica funcione

**Para DESPUÉS (cuando los 5 bots funcionen):**
- 🔄 Migro el código a Vertex AI (Opción B)
- 🔄 Usas tus credenciales de Google Cloud
- 🔄 Quitas límites de producción

¿Qué opción prefieres?
