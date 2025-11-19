# Configuración de Vertex AI para BOTRADING

## Descripción General

Este documento explica cómo configurar y usar **Google Cloud Vertex AI** con el proyecto BOTRADING. El sistema ahora soporta dos opciones para acceder a los modelos Gemini:

1. **Vertex AI** (Google Cloud Platform) - **OPCIÓN PRINCIPAL Y RECOMENDADA**
2. **Google AI Studio** (opción legacy) - Gratuito con límites

## ¿Cuándo usar cada opción?

### Vertex AI (RECOMENDADO - Opción principal)
- ✅ **PRINCIPAL**: Configuración por defecto del proyecto
- ✅ Sin límites de rate (según quota del proyecto)
- ✅ Ideal para producción y múltiples bots
- ✅ Integración completa con Google Cloud
- ✅ Gemini 2.0 Flash **GRATIS** durante preview
- ⚠️ Requiere proyecto GCP con facturación habilitada
- ⚠️ De pago después de preview (costos muy bajos)

### Google AI Studio (Legacy - Alternativa)
- ✅ **Gratis** hasta 1,500 requests/día
- ✅ Setup en 2 minutos
- ✅ Ideal para pruebas rápidas sin GCP
- ❌ Límites estrictos para producción
- ❌ No recomendado para uso continuo

## Configuración de Vertex AI

### Paso 1: Crear Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Anota el **Project ID** (lo necesitarás más adelante)

### Paso 2: Habilitar APIs Necesarias

En Google Cloud Console:

1. Ve a **APIs & Services** > **Library**
2. Busca y habilita:
   - **Vertex AI API**
   - **Cloud Resource Manager API**

### Paso 3: Configurar Facturación

⚠️ **IMPORTANTE**: Vertex AI requiere una cuenta de facturación activa

1. Ve a **Billing** en Google Cloud Console
2. Asocia una tarjeta de crédito/débito
3. Vertex AI tiene capa gratuita para Gemini 2.0 Flash (en preview)

### Paso 4: Crear Service Account

1. Ve a **IAM & Admin** > **Service Accounts**
2. Click en **Create Service Account**
3. Configura:
   - **Name**: `botrading-vertex-ai`
   - **Description**: `Service account for BOTRADING Vertex AI access`
4. Asigna roles:
   - `Vertex AI User`
   - `Service Account User`
5. Click **Create and Continue**
6. Click **Done**

### Paso 5: Descargar Credenciales JSON

1. En la lista de Service Accounts, encuentra la cuenta que creaste
2. Click en los tres puntos (**Actions**) > **Manage keys**
3. Click **Add Key** > **Create new key**
4. Selecciona **JSON**
5. Click **Create** - se descargará un archivo JSON
6. **Guarda este archivo de forma segura** (lo necesitarás para configurar BOTRADING)

⚠️ **SEGURIDAD**: Nunca compartas este archivo ni lo subas a Git

### Paso 6: Configurar Credenciales en BOTRADING

#### Opción A: Usando archivo de credenciales (Recomendado)

1. Copia el archivo JSON descargado a una ubicación segura:
   ```bash
   # Ejemplo en Windows
   mkdir C:\Users\TuUsuario\.gcp
   copy Downloads\botrading-*.json C:\Users\TuUsuario\.gcp\vertex-ai-credentials.json
   ```

2. Actualiza `config/credentials.json`:
   ```json
   {
       "mt5": {
           "account_id": "YOUR_ACCOUNT_ID",
           "password": "YOUR_PASSWORD",
           "server": "YOUR_BROKER_SERVER"
       },
       "vertex_ai": {
           "use_vertex_ai": true,
           "project_id": "tu-proyecto-gcp-12345",
           "location": "us-central1",
           "credentials_path": "C:\\Users\\TuUsuario\\.gcp\\vertex-ai-credentials.json"
       },
       "gemini": {
           "api_key": "YOUR_GEMINI_API_KEY"
       }
   }
   ```

#### Opción B: Usando variable de entorno

1. Configura la variable de entorno `GOOGLE_APPLICATION_CREDENTIALS`:
   
   **Windows (PowerShell):**
   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\TuUsuario\.gcp\vertex-ai-credentials.json"
   
   # Para hacerlo permanente:
   [System.Environment]::SetEnvironmentVariable(
       'GOOGLE_APPLICATION_CREDENTIALS',
       'C:\Users\TuUsuario\.gcp\vertex-ai-credentials.json',
       'User'
   )
   ```

2. Actualiza `config/credentials.json`:
   ```json
   {
       "mt5": {...},
       "vertex_ai": {
           "use_vertex_ai": true,
           "project_id": "tu-proyecto-gcp-12345",
           "location": "us-central1",
           "credentials_path": null
       },
       "gemini": {...}
   }
   ```

### Paso 7: Actualizar Configuración de IA

Edita `config/ia_config.json`:

```json
{
    "provider": "gemini",
    "model": "gemini-2.5-pro",
    "temperature": 0.7,
    "max_tokens": 2048,
    "timeout": 30,
    "retry_attempts": 3,
    "backoff_factor": 2,
    "use_vertex_ai": true,
    "project_id": "tu-proyecto-gcp-12345",
    "location": "us-central1",
    "credentials_path": "C:\\Users\\TuUsuario\\.gcp\\vertex-ai-credentials.json"
}
```

## Uso en Código

### Inicialización con Vertex AI

```python
from src.core.gemini_client import GeminiClient, GeminiConfig

# Configuración para Vertex AI
config = GeminiConfig(
    use_vertex_ai=True,
    project_id="tu-proyecto-gcp-12345",
    location="us-central1",
    credentials_path="/path/to/credentials.json",
    model="gemini-2.0-flash-exp",
    temperature=0.7,
    max_tokens=2048
)

# Crear cliente
client = GeminiClient(config=config)

# Enviar prompt (funciona igual que con Google AI Studio)
response = client.send_prompt("Analiza el mercado EURUSD")

if response.success:
    print(f"Respuesta: {response.content}")
    print(f"Tokens: {response.total_tokens}")
    print(f"Costo: ${response.cost}")
```

### Inicialización con Google AI Studio (legacy)

```python
# Configuración para Google AI Studio (solo si no quieres usar Vertex AI)
config = GeminiConfig(
    use_vertex_ai=False,  # Cambiar a False para usar Google AI Studio
    model="gemini-2.0-flash-exp"
)

client = GeminiClient(api_key="AIzaSy...", config=config)
```

### Cambiar entre Vertex AI y Google AI Studio

El sistema usa **Vertex AI por defecto**. Para cambiar a Google AI Studio, configura `use_vertex_ai` a `false`:

```python
# Cargar desde archivo
from src.core.gemini_client import GeminiConfig

# Esta configuración determina qué API se usa (Vertex AI por defecto)
config = GeminiConfig.from_json_file("config/ia_config.json")
```

## Regiones Disponibles

Vertex AI está disponible en múltiples regiones. Las más comunes:

- `us-central1` (Iowa, USA) - **Recomendado**
- `us-east1` (South Carolina, USA)
- `us-west1` (Oregon, USA)
- `europe-west1` (Bélgica)
- `europe-west4` (Países Bajos)
- `asia-southeast1` (Singapur)

Consulta [la documentación oficial](https://cloud.google.com/vertex-ai/docs/general/locations) para la lista completa.

## Costos Estimados

### Gemini 2.0 Flash (Experimental)
- **Input**: $0.00025 por 1K tokens (~$0.25 por 1M tokens)
- **Output**: $0.001 por 1K tokens (~$1.00 por 1M tokens)
- **Gratis durante preview** (sujeto a cambios)

### Ejemplo de Uso BOTRADING (5 bots, 16 horas/día)

Estimación diaria:
- 5 bots × 12 consultas/hora × 16 horas = **960 requests/día**
- ~500 tokens input + 200 output por request = **672,000 tokens/día**

Costo estimado:
- Input: 672,000 tokens × $0.00025/1K = **$0.17/día**
- Output: 268,800 tokens × $0.001/1K = **$0.27/día**
- **Total: ~$0.44/día** (~$13/mes)

⚠️ **Nota**: Durante el preview de Gemini 2.0 Flash, esto puede ser **GRATIS**.

## Monitoreo de Uso

### Ver cuotas en Google Cloud

1. Ve a **IAM & Admin** > **Quotas**
2. Filtra por "Vertex AI"
3. Revisa:
   - `Requests per minute`
   - `Tokens per minute`
   - `Concurrent requests`

### Ver costos en Google Cloud

1. Ve a **Billing** > **Reports**
2. Filtra por "Vertex AI API"
3. Revisa el gasto diario/mensual

### Ver estadísticas en BOTRADING

```python
# Obtener estadísticas de uso
stats = client.get_usage_statistics()

print(f"Total requests: {stats['total_requests']}")
print(f"Tokens input: {stats['total_tokens_input']}")
print(f"Tokens output: {stats['total_tokens_output']}")
print(f"Costo total: ${stats['total_cost']:.4f}")
print(f"Latencia promedio: {stats['average_latency']:.2f}s")
```

## Solución de Problemas

### Error: "Permission denied"

**Causa**: Service Account no tiene permisos suficientes

**Solución**:
1. Ve a **IAM & Admin** > **IAM**
2. Encuentra tu Service Account
3. Asegúrate de tener rol `Vertex AI User`

### Error: "Project not found"

**Causa**: Project ID incorrecto

**Solución**:
1. Verifica el Project ID en Google Cloud Console
2. Actualiza `project_id` en la configuración

### Error: "Billing not enabled"

**Causa**: Proyecto no tiene facturación habilitada

**Solución**:
1. Ve a **Billing** en Google Cloud Console
2. Asocia una cuenta de facturación al proyecto

### Error: "Vertex AI API not enabled"

**Causa**: API no habilitada en el proyecto

**Solución**:
1. Ve a **APIs & Services** > **Library**
2. Busca "Vertex AI API"
3. Click en **Enable**

### Error: "Could not load credentials"

**Causa**: Ruta al archivo de credenciales incorrecta

**Solución**:
1. Verifica que el archivo existe en la ruta especificada
2. Usa rutas absolutas (ej: `C:\Users\...`)
3. En Windows, usa `\\` o `/` en las rutas

## Migración a Vertex AI

Si tienes el proyecto funcionando con Google AI Studio y quieres migrar a Vertex AI (recomendado):

1. **Completa la configuración de Vertex AI** siguiendo los pasos anteriores
2. **Agrega la configuración de Vertex AI** en `credentials.json` 
3. **El flag `use_vertex_ai` ya está en `true`** por defecto en `ia_config.json`
4. **Prueba con un bot** antes de activar todos

### Reversión a Google AI Studio

Si necesitas volver temporalmente a Google AI Studio, cambia:
```json
{
    "use_vertex_ai": false
}
```

Y proporciona un `api_key` válido en `credentials.json`.

## Mejores Prácticas

### Seguridad
- ✅ Nunca subas `credentials.json` a Git
- ✅ Agrega `*.json` al `.gitignore` (excepto `*.example.json`)
- ✅ Usa permisos mínimos necesarios en Service Account
- ✅ Rota credenciales periódicamente

### Costos
- ✅ Monitorea uso diario en Google Cloud Console
- ✅ Configura alertas de facturación
- ✅ Usa `reset_statistics()` para reiniciar contadores

### Rendimiento
- ✅ Usa `us-central1` para menor latencia desde América
- ✅ Configura `retry_attempts` apropiadamente
- ✅ Ajusta `timeout` según tu conexión

## Referencias

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Pricing](https://cloud.google.com/vertex-ai/pricing)
- [Service Accounts Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
- [Vertex AI Quotas](https://cloud.google.com/vertex-ai/docs/quotas)

## Soporte

Si encuentras problemas:

1. Revisa los logs del sistema
2. Verifica las quotas en Google Cloud Console
3. Consulta la documentación oficial de Vertex AI
4. Crea un issue en el repositorio del proyecto

---

**Última actualización**: Noviembre 2025  
**Versión**: 1.0.0
