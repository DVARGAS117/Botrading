# 📚 Índice de Documentación - Botrading

## 🚀 Inicio Rápido

¿Nuevo en el proyecto? Comienza aquí:

1. **[README Principal](../README.md)** - Visión general del proyecto
2. **[Inicio Rápido INTRADAY](INTRADAY_QUICK_START.md)** - Configuración en 5 minutos
3. **[Guía Completa del Bot INTRADAY](INTRADAY_BOT_GUIDE.md)** - Documentación completa del bot activo

---

## 🤖 Bot INTRADAY (Bot Activo)

### Documentación Principal
- **[📘 Guía Completa del Bot INTRADAY](INTRADAY_BOT_GUIDE.md)**
  - Arquitectura del bot
  - Configuración detallada
  - Flujo de operación
  - Sistema de indicadores
  - Gestión de posiciones
  - Persistencia de datos
  - Métricas y costos
  - Troubleshooting

- **[⚡ Inicio Rápido INTRADAY](INTRADAY_QUICK_START.md)**
  - Instalación en 5 minutos
  - Configuración básica
  - Verificación de componentes
  - Comandos útiles
  - Problemas comunes

- **[🔧 Referencia API INTRADAY](INTRADAY_API_REFERENCE.md)**
  - IntradayBot1Strategy
  - IntradayIndicatorCalculator
  - Repositorios (IA y Operaciones)
  - Estructuras de datos
  - Utilidades

### Documentación de Implementación
- **[🧠 Integración Completa INTRADAY](../context/INTRADAY_INTEGRACION_COMPLETA.md)**
  - Sistema de prompts
  - Paquetes de indicadores
  - Flujo de ejecución
  - Tracking de costos
  - Próximos pasos

- **[📝 Prompts INTRADAY Implementation](PROMPTS_INTRADAY_IMPLEMENTATION.md)**
  - Estructura de prompts
  - Variables disponibles
  - Ejemplos de uso
  - Best practices

- **[📊 Trading Sessions Implementation](TRADING_SESSIONS_IMPLEMENTATION.md)**
  - Configuración de sesiones
  - Horarios por región
  - Símbolos por sesión
  - Verificación de sesión activa

---

## 🔌 Integraciones

### Vertex AI (Gemini)
- **[🤖 Vertex AI Setup](VERTEX_AI_SETUP.md)**
  - Requisitos de Google Cloud
  - Configuración de credenciales
  - Autenticación y permisos
  - Configuración del cliente
  - Troubleshooting

- **[💲 Gemini Pricing](GEMINI_PRICING.md)**
  - Tarifas de Gemini 3 Pro Preview
  - Niveles de contexto (estándar vs largo)
  - Cálculo de costos
  - Optimización de uso
  - Ejemplos de costos

- **[🔄 Vertex AI vs Google AI](VERTEX_AI_VS_GOOGLE_AI.md)**
  - Comparación de APIs
  - Casos de uso
  - Ventajas y desventajas
  - Recomendaciones

### MetaTrader 5
- **[📈 Data Requirements](DATA_REQUIREMENTS.md)**
  - Requisitos de datos históricos
  - Timeframes soportados
  - Validación de datos
  - Manejo de datos faltantes

- **[📊 Asset Types Guide](ASSET_TYPES_GUIDE.md)**
  - Forex (pares de divisas)
  - Metales preciosos
  - Índices bursátiles
  - Criptomonedas
  - Configuración por tipo de activo
  - Validaciones específicas

- **[₿ Crypto Trading Guide](CRYPTO_TRADING_GUIDE.md)**
  - Características de criptomonedas
  - Configuración específica
  - Manejo de volatilidad extrema
  - Consideraciones de riesgo
  - Estado: Parcialmente implementado

- **[📅 Futures Trading Guide](FUTURES_TRADING_GUIDE.md)**
  - Características de contratos futuros
  - Tipos de futuros (índices, commodities, divisas)
  - Manejo de expiración y roll-over
  - Consideraciones de margen y leverage
  - Estado: NO implementado - planificación

---

## 🏗️ Arquitectura e Infraestructura

### Core del Sistema
- **[🔧 T45 - Arquitectura Core](../context/DOCUMENTACION/T45_reusabilidad_modulos_core.md)**
  - Clase base CoreModule
  - Patrones de reutilización
  - Mejores prácticas
  - Ejemplos de implementación

- **[📦 T44 - Config Loader](../context/DOCUMENTACION/T44_config_loader.md)**
  - Gestión centralizada de configuración
  - Estructura de archivos JSON
  - Validación de configuración
  - Uso en componentes

- **[📝 T39 - Logger](../context/DOCUMENTACION/T39_logger.md)**
  - Sistema de logging por bot
  - Niveles de log
  - Formato y rotación
  - Logging estructurado

### Seguridad
- **[🔐 T47 - Credential Manager](../context/DOCUMENTACION/T47_almacenamiento_seguro_credenciales.md)**
  - Encriptación AES-128 (Fernet)
  - Almacenamiento seguro
  - Gestión de claves
  - Buenas prácticas de seguridad

---

## ✅ Testing

### Infraestructura de Tests
- **[🧪 T46 - Testing Infrastructure](../context/DOCUMENTACION/T46_tests_unitarios_por_componente.md)**
  - Estructura de tests
  - Fixtures y mocks
  - Tests unitarios
  - Tests de integración
  - Cobertura de código

### Ejecución de Tests
```bash
# Todos los tests
pytest tests/ -v

# Tests con cobertura
pytest tests/ -v --cov=src --cov-report=html

# Tests del bot INTRADAY
pytest tests/bots/strategies/intraday/ -v
```

---

## ⏰ Módulos Auxiliares

### Validadores
- **[🕐 T35 - Time Validator](../context/DOCUMENTACION/T35_validacion_hora_lima.md)**
  - Validación de horarios de trading
  - Zona horaria Lima
  - Días hábiles
  - Verificación de sesiones

- **[⏳ T37 - Candle Waiter](../context/DOCUMENTACION/T37_espera_cierre_vela.md)**
  - Espera inteligente de cierre de vela
  - Cálculo de tiempo restante
  - Manejo de timeframes
  - Sincronización con MT5

- **[📊 T48 - Quota Validator](../context/DOCUMENTACION/T48_validacion_cuota_ia.md)**
  - Validación de cuota de IA
  - Límites de uso
  - Verificación de disponibilidad
  - Manejo de errores

- **[🎛️ T36 - Filter Manager](../context/DOCUMENTACION/T36_filtros_configurables.md)**
  - Filtros de volatilidad
  - Filtros de spread
  - Configuración dinámica
  - Activación/desactivación

- **[🎯 T52 - Demo Mode Validator](../context/DOCUMENTACION/T52_operacion_demo_antes_real.md)**
  - Validación de operación demo
  - Verificación pre-producción
  - Prevención de errores
  - Checklist de validación

### Gestión de IA
- **[🔄 T49 - IA Config Manager](../context/DOCUMENTACION/T49_config_alternante_ia.md)**
  - Alternancia de configuraciones IA
  - Perfiles de IA por bot
  - Cambio dinámico de modelo
  - Parámetros configurables

- **[📋 Formato Respuestas IA](../context/FORMATO_RESPUESTAS_IA.md)**
  - Estructura JSON esperada
  - Campos obligatorios
  - Validación de respuestas
  - Ejemplos de respuestas válidas

---

## 📋 Gestión de Proyecto

### Planificación
- **[📊 Resumen Ejecutivo](../context/RESUMEN_EJECUTIVO.md)**
  - Visión general del proyecto
  - Objetivos principales
  - Estado actual
  - Roadmap

- **[📝 Lista de Tickets](../context/TICKETS_LIST.md)**
  - 52 tickets organizados en 16 épicas
  - Estado de implementación
  - Prioridades
  - Dependencias

- **[🤖 Reglas del Agente](../context/agents.md)**
  - Metodología TDD
  - Estándares de código
  - Flujo de trabajo
  - Buenas prácticas

### Análisis
- **[🔍 Análisis de Fase 1](../context/ANALISIS_FASE_1.md)**
  - Análisis detallado de tickets
  - Dependencias entre componentes
  - Estimaciones de esfuerzo
  - Plan de implementación

- **[📊 Análisis de Tickets](../context/ANALISIS_TICKETS.md)**
  - Desglose por épica
  - Complejidad técnica
  - Riesgos identificados
  - Recomendaciones

---

## 📚 Recursos Adicionales

### Contexto del Proyecto
- **[📂 INDEX](../context/INDEX.md)** - Índice completo de documentación de contexto
- **[✅ VERIFICACIÓN](../context/VERIFICATION_CHECKLIST.md)** - Checklist de verificación
- **[📊 Resumen de Etiquetado](../context/RESUMEN_ETIQUETADO.md)** - Sistema de etiquetas

### Legacy (Referencia)
- **[📈 VWAP Implementation](../context/RESUMEN_VWAP_IMPLEMENTATION.md)** - Implementación VWAP (legacy)
- **[📝 Tareas VWAP](../context/TAREAS_VWAP_METHODOLOGY.md)** - Metodología VWAP (legacy)

---

## 🗂️ Estructura de Carpetas

```
docs/                                 # Documentación técnica
├── INTRADAY_BOT_GUIDE.md            # Guía completa del bot
├── INTRADAY_QUICK_START.md          # Inicio rápido
├── INTRADAY_API_REFERENCE.md        # Referencia API
├── VERTEX_AI_SETUP.md               # Setup Vertex AI
├── GEMINI_PRICING.md                # Precios Gemini
├── TRADING_SESSIONS_IMPLEMENTATION.md  # Sesiones de trading
├── PROMPTS_INTRADAY_IMPLEMENTATION.md  # Sistema de prompts
├── VERTEX_AI_VS_GOOGLE_AI.md        # Comparación APIs
├── DATA_REQUIREMENTS.md             # Requisitos de datos
├── GEMINI_API_SETUP.md              # Setup Gemini API
└── DOCUMENTATION_INDEX.md           # Este archivo

context/                              # Documentación de contexto
├── DOCUMENTACION/                   # Docs técnicas detalladas
│   ├── T45_reusabilidad_modulos_core.md
│   ├── T46_tests_unitarios_por_componente.md
│   ├── T47_almacenamiento_seguro_credenciales.md
│   ├── T44_config_loader.md
│   ├── T39_logger.md
│   ├── T35_validacion_hora_lima.md
│   ├── T37_espera_cierre_vela.md
│   ├── T48_validacion_cuota_ia.md
│   ├── T49_config_alternante_ia.md
│   ├── T36_filtros_configurables.md
│   └── T52_operacion_demo_antes_real.md
├── INTRADAY_INTEGRACION_COMPLETA.md # Integración INTRADAY
├── RESUMEN_EJECUTIVO.md             # Resumen del proyecto
├── TICKETS_LIST.md                  # Lista de tickets
├── agents.md                        # Reglas del agente
├── FORMATO_RESPUESTAS_IA.md         # Formato respuestas IA
└── ...                              # Otros documentos de contexto
```

---

## 🔍 Cómo Navegar

### Para Desarrolladores Nuevos
1. Lee el [README Principal](../README.md)
2. Sigue el [Inicio Rápido INTRADAY](INTRADAY_QUICK_START.md)
3. Consulta la [Guía Completa del Bot](INTRADAY_BOT_GUIDE.md)
4. Revisa la [Referencia API](INTRADAY_API_REFERENCE.md)

### Para Configuración
1. [Vertex AI Setup](VERTEX_AI_SETUP.md) - Configurar Gemini
2. [Trading Sessions](TRADING_SESSIONS_IMPLEMENTATION.md) - Configurar horarios
3. [Prompts Implementation](PROMPTS_INTRADAY_IMPLEMENTATION.md) - Personalizar prompts

### Para Desarrollo
1. [Arquitectura Core](../context/DOCUMENTACION/T45_reusabilidad_modulos_core.md) - Entender la base
2. [Testing Infrastructure](../context/DOCUMENTACION/T46_tests_unitarios_por_componente.md) - Escribir tests
3. [Referencia API](INTRADAY_API_REFERENCE.md) - Consultar métodos

### Para Troubleshooting
1. [Guía del Bot - Troubleshooting](INTRADAY_BOT_GUIDE.md#troubleshooting) - Problemas comunes
2. [Inicio Rápido - Problemas](INTRADAY_QUICK_START.md#problemas-comunes) - Errores frecuentes
3. [Vertex AI Setup - Troubleshooting](VERTEX_AI_SETUP.md#troubleshooting) - Problemas de IA

---

## 📞 Soporte

- **GitHub Issues**: https://github.com/DVARGAS117/Botrading/issues
- **Proyecto**: https://github.com/users/DVARGAS117/projects/2
- **Logs**: `src/bots/strategies/intraday/gemini_3_pro/bot_1/logs/`

---

**Última actualización:** 20 de noviembre de 2025  
**Mantenido por:** Sistema Botrading  
**Versión:** 1.0.0
