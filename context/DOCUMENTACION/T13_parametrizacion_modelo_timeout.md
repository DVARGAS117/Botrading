# T13 - Parametrización de Modelo y Tiempo de Espera

**Ticket:** #29  
**Fase:** 2  
**Prioridad:** P1  
**Estado:** ✅ Implementado

---

## 📋 Resumen

Este ticket implementa la parametrización dinámica de los parámetros del modelo de IA (modelo, temperatura, max tokens y timeout) a través de un archivo JSON de configuración. Permite a los operadores experimentar con diferentes configuraciones sin modificar el código fuente.

**Características implementadas:**
- Carga de configuración desde archivo JSON
- Actualización en tiempo real de parámetros
- Validación de parámetros
- Compatibilidad con configuración existente

---

## 🏗️ Arquitectura

### Componentes Modificados

#### 1. GeminiConfig (`src/core/gemini_client.py`)

**Nuevos métodos:**
- `from_json_file()`: Carga configuración desde archivo JSON
- Filtrado automático de campos válidos
- Validación de tipos y rangos

#### 2. GeminiClient (`src/core/gemini_client.py`)

**Nuevo método:**
- `update_config_from_file()`: Actualiza configuración del cliente desde archivo

### Flujo de Parametrización

```
Archivo JSON ──► GeminiConfig.from_json_file() ──► GeminiClient.update_config_from_file()
      │
      ▼
Validación ──► Aplicación ──► Próxima llamada a IA usa nuevos parámetros
```

---

## 📦 Implementación

### Archivo de Configuración: `config/ia_config.example.json`

```json
{
    "provider": "gemini",
    "model": "gemini-2.5-pro",
    "temperature": 0.7,
    "max_tokens": 2048,
    "timeout": 30,
    "retry_attempts": 3,
    "backoff_factor": 2
}
```

**Campos soportados:**
- `model`: Nombre del modelo Gemini
- `temperature`: Temperatura (0-2)
- `max_tokens`: Máximo tokens en respuesta
- `timeout`: Timeout en segundos
- `retry_attempts`: Número de reintentos
- `backoff_factor`: Factor de backoff exponencial

### Uso Programático

#### Carga desde Archivo

```python
from src.core.gemini_client import GeminiConfig, GeminiClient

# Cargar configuración desde archivo
config = GeminiConfig.from_json_file('config/ia_config.json')

# Crear cliente con configuración cargada
client = GeminiClient(api_key="YOUR_API_KEY", config=config)
```

#### Actualización en Tiempo Real

```python
# Actualizar configuración durante ejecución
client.update_config_from_file('config/ia_config_updated.json')

# La siguiente llamada usará los nuevos parámetros
response = client.send_prompt("Nuevo prompt con configuración actualizada")
```

---

## 🔧 Configuración

### Archivo JSON

Crear `config/ia_config.json` basado en el ejemplo:

```bash
cp config/ia_config.example.json config/ia_config.json
```

### Modificación de Parámetros

Editar el archivo JSON para experimentar:

```json
{
    "model": "gemini-2.0-flash-exp",
    "temperature": 0.3,
    "max_tokens": 1024,
    "timeout": 45
}
```

### Aplicación de Cambios

```python
# En código de producción
client.update_config_from_file('config/ia_config.json')
```

---

## 📊 Validación y Manejo de Errores

### Validaciones Implementadas

- **Archivo existe**: `FileNotFoundError` si no se encuentra
- **JSON válido**: `json.JSONDecodeError` si formato incorrecto
- **Campos válidos**: Solo se procesan campos conocidos
- **Rangos**: Validación de temperature, max_tokens, timeout

### Manejo de Errores

```python
try:
    client.update_config_from_file('config/ia_config.json')
    print("Configuración actualizada exitosamente")
except FileNotFoundError:
    print("Archivo de configuración no encontrado")
except json.JSONDecodeError:
    print("Archivo JSON inválido")
except ValueError as e:
    print(f"Parámetros inválidos: {e}")
```

---

## 🧪 Tests

### Tests Unitarios
- `tests/unit/test_gemini_client.py`: Tests para carga y actualización desde JSON

**Ejecutar tests:**

```bash
pytest tests/unit/test_gemini_client.py::TestGeminiConfig::test_config_from_json_file -v
pytest tests/unit/test_gemini_client.py::TestGeminiClientEdgeCases::test_config_update_from_json_file -v
```

### Cobertura de Tests

- ✅ Carga exitosa desde archivo válido
- ✅ Error con archivo inexistente
- ✅ Error con JSON inválido
- ✅ Actualización en tiempo real
- ✅ Validación de parámetros

---

## 🎯 Escenario de Uso

### Experimentos con Diferentes Modelos

**Archivo 1: `config/experiment_high_creativity.json`**
```json
{
    "model": "gemini-2.5-pro",
    "temperature": 0.9,
    "max_tokens": 4096,
    "timeout": 60
}
```

**Archivo 2: `config/experiment_conservative.json`**
```json
{
    "model": "gemini-2.0-flash-exp",
    "temperature": 0.1,
    "max_tokens": 512,
    "timeout": 15
}
```

**Código de experimentación:**

```python
# Experimento 1: Alta creatividad
client.update_config_from_file('config/experiment_high_creativity.json')
response1 = client.send_prompt("Genera ideas creativas para trading")

# Experimento 2: Conservador
client.update_config_from_file('config/experiment_conservative.json')
response2 = client.send_prompt("Análisis conservador del mercado")

# Comparar resultados
print(f"Creativo: {len(response1.content)} caracteres")
print(f"Conservador: {len(response2.content)} caracteres")
```

---

## 📈 Beneficios

### Para Operadores
- **Experimentación rápida**: Cambiar parámetros sin recompilar
- **A/B Testing**: Comparar diferentes configuraciones fácilmente
- **Optimización**: Ajustar parámetros basados en rendimiento

### Para Desarrolladores
- **Separación de concerns**: Configuración separada del código
- **Mantenibilidad**: Cambios de configuración sin modificar código
- **Flexibilidad**: Soporte para múltiples entornos

---

## 🔗 Tickets Relacionados

- **T10**: Construcción de prompts e integración con IA ✅
- **T11**: Registro de tokens y costo ✅
- **T14**: Configuración de prompts desde JSON (pendiente)

---

## ✅ Criterios de Aceptación

**Escenario: Parametrizar modelo y tiempo de espera**

- ✅ **Dado** que el archivo de configuración define modelo, temperatura, max tokens y timeout
- ✅ **Cuando** se actualiza la configuración desde el archivo JSON
- ✅ **Entonces** la siguiente llamada a IA usa los nuevos parámetros

---

## 📝 Notas de Implementación

### Compatibilidad
- Archivos JSON existentes siguen funcionando
- Campos opcionales: usa valores por defecto si no especificados
- Campos desconocidos: ignorados silenciosamente

### Rendimiento
- Carga de archivo solo cuando se solicita
- Validación en carga, no en cada request
- Reinicialización del modelo solo cuando cambia configuración

### Seguridad
- Validación estricta de rangos y tipos
- Logging de cambios de configuración
- No expone información sensible en logs

---

**Autor:** Botrading Team  
**Fecha:** 13 de Noviembre de 2025  
**Versión:** 1.0