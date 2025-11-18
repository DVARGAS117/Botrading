# Configuración de Gemini AI API Key

## Problema Identificado

La API key actual en `config/credentials.json` **NO es una API key de Gemini AI**. 

El error indica:
```
401 API keys are not supported by this API. Expected OAuth2 access token or other authentication credentials
```

Esto significa que la key proporcionada es probablemente:
- Una API key de Google Cloud Platform (GCP)
- Una credencial de Azure DevOps
- Otro tipo de credencial que NO es válida para Gemini AI

## Solución: Obtener API Key de Gemini AI

### Opción 1: Google AI Studio (Recomendado - Gratuito)

**Google AI Studio** proporciona acceso gratuito a Gemini con límites generosos.

#### Pasos:

1. **Acceder a Google AI Studio**
   - URL: https://aistudio.google.com/app/apikey
   - O: https://makersuite.google.com/app/apikey

2. **Iniciar sesión**
   - Usa tu cuenta de Google

3. **Crear API Key**
   - Click en "Get API Key" o "Create API Key"
   - Click en "Create API key in new project" (o selecciona un proyecto existente)
   - Copia la API key generada (formato: `AIza...`)

4. **Actualizar credentials.json**
   ```json
   {
       "mt5": {
           "account_id": "61409006",
           "password": "V3n3zu3l@",
           "server": "Pepperstone-Demo"
       },
       "gemini": {
           "api_key": "AIzaSy..."  <-- Tu nueva API key aquí
       }
   }
   ```

#### Límites Gratuitos (Google AI Studio):
- ✅ **60 requests por minuto**
- ✅ **1,500 requests por día**
- ✅ **100,000 tokens por día** (suficiente para miles de análisis)
- ✅ Sin costo

### Opción 2: Google Cloud Platform

Si necesitas más capacidad o quieres usar facturación por uso:

1. **Crear proyecto en Google Cloud**
   - URL: https://console.cloud.google.com/

2. **Habilitar Gemini API**
   - Buscar "Generative Language API" en el catálogo de APIs
   - Habilitar la API

3. **Crear credenciales**
   - Ir a "APIs & Services" > "Credentials"
   - Crear API Key
   - Restringir la API key solo a "Generative Language API"

4. **Configurar facturación**
   - Necesitas una tarjeta de crédito
   - Pricing: https://ai.google.dev/pricing

#### Costos (Google Cloud):
- **Gemini 2.0 Flash (Experimental)**: Gratis durante preview
- **Gemini 1.5 Flash**: ~$0.075 por 1M tokens input, ~$0.30 por 1M tokens output
- **Gemini 1.5 Pro**: ~$1.25 por 1M tokens input, ~$5.00 por 1M tokens output

## Diferencias Clave

### ❌ Google Cloud API Key (Lo que NO funciona)
```
Formato típico: AIza + números/letras random PERO configurada solo para GCP
Propósito: Acceso a servicios de Google Cloud (Storage, BigQuery, etc.)
Error: "API keys are not supported by this API"
```

### ✅ Gemini AI API Key (Lo que SÍ funciona)
```
Formato típico: AIza + números/letras random configurada para Gemini AI
Propósito: Acceso a modelos Gemini (generación de texto, visión)
Funciona con: google.generativeai Python library
```

### ❌ Azure DevOps Key
```
Formato típico: AQ.Ab8RN... (como la que tienes ahora)
Propósito: Acceso a Azure DevOps (Pipelines, Repos, Work Items)
NO funciona: Para Gemini AI
```

## Verificación Rápida

Para verificar que tu API key funciona:

```python
import google.generativeai as genai

# Configurar con tu API key
genai.configure(api_key="TU_API_KEY_AQUI")

# Probar conexión
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content("Di 'Hola mundo'")
print(response.text)
```

Si funciona, verás: "Hola mundo" (o similar)

## Recomendación para BOTRADING

Para tu caso de uso (trading bot con 5 bots consultando cada 5 minutos):

**Usa Google AI Studio (Opción 1 - Gratuita)**

Estimación de uso diario:
- 5 bots × 12 consultas/hora × 16 horas trading = **960 requests/día**
- Cada prompt ~500 tokens, respuesta ~200 tokens = **~670,000 tokens/día**

✅ Dentro de los límites gratuitos de Google AI Studio

## Siguiente Paso

1. Ve a: https://aistudio.google.com/app/apikey
2. Crea tu API key
3. Actualiza `config/credentials.json`
4. Ejecuta: `python -m src.bots.bot_1.main --single-cycle --force-trading`

## Testing con --force-trading

Ahora puedes probar fuera de horario:

```bash
# Testing fuera de horario
python -m src.bots.bot_1.main --single-cycle --force-trading

# Testing continuo fuera de horario (cada 5 min)
python -m src.bots.bot_1.main --force-trading --interval 300

# Testing con debug detallado
python -m src.bots.bot_1.main --single-cycle --force-trading --log-level DEBUG
```

El flag `--force-trading` ignorará las restricciones de horario y te permitirá:
- ✅ Probar el bot fuera del horario 06:00-13:00 (Lima)
- ✅ Debuggear errores sin esperar al horario de trading
- ✅ Validar la integración con Gemini AI inmediatamente
