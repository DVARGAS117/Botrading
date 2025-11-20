Aquí tienes un resumen completo en formato Markdown, listo para que lo copies y guardes en tu archivo `.md`.

***

# Guía Técnica: Uso de API Gemini 3 Pro en Vertex AI

**Versión del Modelo:** `gemini-3-pro-preview-11-2025`
**Fecha de Documento:** Noviembre 2025
**Uso:** Trading Algorítmico y Análisis de Datos en Tiempo Real

## 1. Precios y Facturación

El costo se basa en el tamaño del contexto (número de tokens) que envías y recibes.

### Tabla de Costos (Por 1 Millón de Tokens)

| Nivel de Contexto | Input (Lo que envías) | Output (Lo que responde) |
| :--- | :--- | :--- |
| **Estándar (≤ 128k)** | $2.00 USD | $12.00 USD |
| **Contexto Largo (> 128k)** | $4.00 USD | $18.00 USD |
| **Context Caching (Storage)** | ~$4.50 USD / hora | N/A |

> **Nota:** Estos precios son para la versión *Preview*. Históricamente, los precios suelen bajar (20-50%) al pasar a versión estable. No existe "Free Tier" para uso en Vertex AI (producción).

## 2. Configuración Técnica Recomendada

Para maximizar la capacidad de razonamiento lógico y matemático (crítico para trading), se recomienda la siguiente configuración de parámetros en el cuerpo de la solicitud API.

### Parámetros Clave

```json
{
  "model": "gemini-3-pro-preview-11-2025",
  "generation_config": {
    "thinking_level": "HIGH", 
    "media_resolution": "high" 
  },
  "tools": [
    { "code_execution": {} } 
  ]
}
```

### Explicación de Parámetros
*   **`thinking_level: "HIGH"`**: Fuerza al modelo a realizar un "pensamiento profundo" antes de responder, ideal para deducir tendencias o correlaciones complejas. Reemplaza al antiguo `thinking_budget`.
*   **`code_execution: {}`**: Permite al modelo escribir y ejecutar código Python en un entorno seguro (sandbox) para realizar cálculos matemáticos precisos en lugar de "alucinarlos".
    *   *Advertencia:* El código generado y su output consumen tokens adicionales.


** TODOS ESTOS PARAMETROS SE DEBEN MANTENER ACTIVOS PARA NUESTROS AGENTES GEMINI 3 PRO. **