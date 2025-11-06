# SISTEMA DE TRADING AUTOMATIZADO CON IA
## Documento Principal del Proyecto

**VersiÃ³n:** 1.0  
**Fecha:** 24 de Octubre, 2025  
**Estado:** EspecificaciÃ³n Inicial

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Definiciones y Glosario](#2-definiciones-y-glosario)
3. [Objetivos del Proyecto](#3-objetivos-del-proyecto)
4. [Arquitectura General](#4-arquitectura-general)
5. [Componentes Principales](#5-componentes-principales)
6. [Flujo de Trabajo Principal](#6-flujo-de-trabajo-principal)
7. [Sistema de Magic Numbers](#7-sistema-de-magic-numbers)
8. [GestiÃ³n Multi-Activo](#8-gestiÃ³n-multi-activo)
9. [Sistema Dual Market/Limit](#9-sistema-dual-marketlimit)
10. [Indicadores y Timeframes](#10-indicadores-y-timeframes)
11. [Filtros y Horarios](#11-filtros-y-horarios)
12. [IntegraciÃ³n con IA (Gemini 2.5 Pro)](#12-integraciÃ³n-con-ia-gemini-25-pro)
13. [Almacenamiento de Datos](#13-almacenamiento-de-datos)
14. [Manejo de Errores](#14-manejo-de-errores)
15. [Estructura Modular del CÃ³digo](#15-estructura-modular-del-cÃ³digo)
16. [ConversiÃ³n y CÃ¡lculo de Activos](#16-conversiÃ³n-y-cÃ¡lculo-de-activos)
17. [Requisitos TÃ©cnicos](#17-requisitos-tÃ©cnicos)
18. [Roadmap de ImplementaciÃ³n](#18-roadmap-de-implementaciÃ³n)

---

## 1. RESUMEN EJECUTIVO

### 1.1 VisiÃ³n General

El proyecto consiste en el desarrollo de un **sistema de trading automatizado multi-bot** para el mercado FOREX que utiliza inteligencia artificial como motor de decisiÃ³n. El sistema estÃ¡ diseÃ±ado para operar en MetaTrader 5 (MT5) conectado al proveedor Pepperstone, empleando **Google Gemini 2.5 Pro** como agente de IA principal.

### 1.2 PropÃ³sito

Crear un ecosistema de bots independientes que permitan:
- Probar mÃºltiples metodologÃ­as de trading simultÃ¡neamente
- Comparar rendimiento entre diferentes enfoques (numÃ©ricos vs. visuales)
- Evaluar eficiencia de costos de IA mediante tracking preciso de tokens
- Analizar diferencias de rendimiento entre Ã³rdenes Market y Limit
- Optimizar estrategias basadas en datos reales y mÃ©tricas precisas

### 1.3 Alcance Inicial

**Fase 1:** ImplementaciÃ³n de 5 bots orquestadores con las siguientes caracterÃ­sticas:
- **Bot 1:** Indicadores numÃ©ricos + entradas duales (Market + Limit)
- **Bot 2:** Indicadores numÃ©ricos con prompts diferentes + entradas duales
- **Bot 3:** AnÃ¡lisis visual con imÃ¡genes de 3 timeframes + entradas duales
- **Bot 4:** HÃ­brido (imagen para apertura, numÃ©rico para reevaluaciÃ³n) + entradas duales
- **Bot 5:** Imagen de velas + indicadores separados + entradas duales

Cada bot opera de forma **independiente y aislada**, permitiendo ejecuciÃ³n, monitoreo y modificaciÃ³n individual.

### 1.4 CaracterÃ­sticas Clave

1. **OperaciÃ³n Multi-Activo:** GestiÃ³n simultÃ¡nea de mÃºltiples pares (FOREX, metales, criptos)
2. **Sistema Dual:** Apertura automÃ¡tica de operaciones Market y Limit en paralelo
3. **Magic Numbers Ãšnicos:** Sistema de codificaciÃ³n para identificaciÃ³n precisa de operaciones
4. **Tracking Completo:** Almacenamiento de tokens, costos, decisiones y resultados
5. **ValidaciÃ³n de Datos:** Solo datos reales de MT5, sin estimaciones ni datos ficticios
6. **Arquitectura Modular:** CÃ³digo organizado en mÃºltiples archivos pequeÃ±os para facilitar mantenimiento

---

## 2. DEFINICIONES Y GLOSARIO

### 2.1 Conceptos Fundamentales

| TÃ©rmino | DefiniciÃ³n |
|---------|------------|
| **IA (Agente)** | Instancia de modelo de inteligencia artificial que recibe datos y genera decisiones. Ejemplo: Agente Gemini 2.5 Pro. |
| **Bot (Orquestador)** | Entidad principal que gestiona el flujo completo: extracciÃ³n de datos MT5, cÃ¡lculo de indicadores, consulta a IA, ejecuciÃ³n de Ã³rdenes y almacenamiento. |
| **MetodologÃ­a** | Estrategia operativa definida a travÃ©s de prompts especÃ­ficos. Puede ser genÃ©rica o basada en frameworks especÃ­ficos (SMC, ICT, etc.). |
| **Magic Number** | Identificador Ãºnico numÃ©rico de 6 dÃ­gitos que identifica cada operaciÃ³n: `[Bot][IA][Tipo]`. Ejemplo: `110201` = Bot 1, IA 02, Market (01). |
| **Market** | Orden ejecutada al precio actual de mercado de forma instantÃ¡nea. |
| **Limit** | Orden pendiente que se ejecuta cuando el precio alcanza un nivel especÃ­fico. |
| **ReevaluaciÃ³n** | Proceso de consulta a la IA sobre una operaciÃ³n abierta para decidir mantener, actualizar SL/TP o cerrar. |
| **Filtro** | CondiciÃ³n lÃ³gica pre-IA que determina si se debe consultar al agente (horario, volatilidad, etc.). |

### 2.2 AcrÃ³nimos TÃ©cnicos

- **MT5:** MetaTrader 5
- **TF:** Timeframe (marco temporal)
- **SL:** Stop Loss
- **TP:** Take Profit
- **EMA:** Exponential Moving Average
- **RSI:** Relative Strength Index
- **MACD:** Moving Average Convergence Divergence
- **BD:** Base de Datos
- **API:** Application Programming Interface
- **P/L:** Profit/Loss (Ganancia/PÃ©rdida)

---

## 3. OBJETIVOS DEL PROYECTO

### 3.1 Objetivos Primarios

1. **AutomatizaciÃ³n Completa:** Eliminar intervenciÃ³n manual en la ejecuciÃ³n de operaciones basadas en anÃ¡lisis de IA.

2. **ComparaciÃ³n de MetodologÃ­as:** Evaluar rendimiento de diferentes enfoques:
   - AnÃ¡lisis numÃ©rico vs. visual
   - Indicadores tÃ©cnicos vs. anÃ¡lisis de velas
   - Entradas Market vs. Limit

3. **OptimizaciÃ³n de Costos:** Medir con precisiÃ³n el consumo de tokens y costos de API para identificar la relaciÃ³n costo/beneficio de cada bot.

4. **Trazabilidad Total:** Registrar todas las decisiones, operaciones y resultados para anÃ¡lisis posterior y mejora continua.

### 3.2 Objetivos Secundarios

1. **Escalabilidad:** Arquitectura que permita agregar nuevos bots, IAs o metodologÃ­as sin reescribir cÃ³digo base.

2. **Modularidad:** CÃ³digo organizado en componentes pequeÃ±os y reutilizables para facilitar mantenimiento.

3. **PrecisiÃ³n de Datos:** Garantizar que toda informaciÃ³n enviada a la IA sea real y exacta, sin estimaciones.

4. **GestiÃ³n de Riesgos:** Implementar cÃ¡lculo correcto de lotes basado en % de riesgo sugerido por IA, adaptado a cada tipo de activo.

---

## 4. ARQUITECTURA GENERAL

### 4.1 Diagrama de Alto Nivel

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    SISTEMA FOREX TRADING BOT                 â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚                     â”‚                     â”‚
   â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”           â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”           â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”
   â”‚  BOT 1  â”‚           â”‚  BOT 2  â”‚    ...    â”‚  BOT 5  â”‚
   â”‚(NumÃ©ricoâ”‚           â”‚(NumÃ©ricoâ”‚           â”‚(Imagen+ â”‚
   â”‚ Market/ â”‚           â”‚ Market/ â”‚           â”‚Indic.   â”‚
   â”‚ Limit)  â”‚           â”‚ Limit)  â”‚           â”‚Market/  â”‚
   â”‚         â”‚           â”‚         â”‚           â”‚Limit)   â”‚
   â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜           â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜           â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜
        â”‚                     â”‚                     â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚                                           â”‚
   â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”                              â”Œâ”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”
   â”‚   MT5    â”‚â—„â”€â”€â”€â”€â”€â”€ Datos Reales â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚  GEMINI   â”‚
   â”‚Pepperstoneâ”‚       (Velas, Precios,       â”‚  2.5 PRO  â”‚
   â”‚          â”‚        Indicadores)           â”‚   API     â”‚
   â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜                              â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
        â”‚                                           â”‚
        â”‚         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”              â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚  SQLite DB      â”‚â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                  â”‚  - Operaciones  â”‚
                  â”‚  - Tokens       â”‚
                  â”‚  - Costos       â”‚
                  â”‚  - Resultados   â”‚
                  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 4.2 Capas del Sistema

#### Capa 1: OrquestaciÃ³n (Bots)
- GestiÃ³n del flujo de trabajo
- Control de tiempo y filtros
- CoordinaciÃ³n entre componentes

#### Capa 2: Datos (MT5 + Indicadores)
- ConexiÃ³n con MT5
- ExtracciÃ³n de velas y precios
- CÃ¡lculo de indicadores tÃ©cnicos
- GeneraciÃ³n de imÃ¡genes (si aplica)

#### Capa 3: Inteligencia (IA Gemini)
- AnÃ¡lisis de datos recibidos
- GeneraciÃ³n de decisiones de trading
- Respuestas estructuradas en JSON

#### Capa 4: EjecuciÃ³n (MT5 API)
- EnvÃ­o de Ã³rdenes Market
- EnvÃ­o de Ã³rdenes Limit
- ModificaciÃ³n de SL/TP
- Cierre de operaciones

#### Capa 5: Persistencia (SQLite)
- Almacenamiento de operaciones
- Registro de consultas a IA
- Tracking de tokens y costos
- HistÃ³rico de decisiones

### 4.3 Principios de DiseÃ±o

1. **Independencia de Bots:** Cada bot es una instancia separada ejecutable de forma individual.

2. **SeparaciÃ³n de Responsabilidades:** Cada mÃ³dulo tiene una funciÃ³n especÃ­fica y bien definida.

3. **ConfiguraciÃ³n Centralizada:** ParÃ¡metros globales (lista de activos, horarios, credenciales) en archivos de configuraciÃ³n.

4. **ValidaciÃ³n Estricta:** Solo datos verificados y reales son procesados y enviados.

5. **Idempotencia:** Las operaciones pueden reintentar sin efectos secundarios duplicados.

---

## 5. COMPONENTES PRINCIPALES

### 5.1 Bot Orquestador

**Responsabilidades:**
- Ejecutar loop principal cada hora
- Aplicar filtros (horario, dÃ­as hÃ¡biles)
- Iterar sobre lista de activos
- Verificar operaciones abiertas por activo
- Coordinar flujo de evaluaciÃ³n o reevaluaciÃ³n
- Gestionar errores y reintentos

**Archivos Asociados:**
- `bot_main.py` - Loop principal
- `bot_config.py` - ConfiguraciÃ³n especÃ­fica del bot
- `bot_filters.py` - LÃ³gica de filtros

### 5.2 Gestor MT5

**Responsabilidades:**
- Inicializar conexiÃ³n con MT5
- Extraer datos de velas (OHLCV)
- Obtener precios actuales (bid/ask)
- Consultar operaciones abiertas
- Enviar Ã³rdenes (Market/Limit)
- Modificar SL/TP
- Cerrar posiciones
- Manejar diferentes tipos de activos (conversiÃ³n correcta)

**Archivos Asociados:**
- `mt5_connector.py` - ConexiÃ³n y operaciones bÃ¡sicas
- `mt5_data_extractor.py` - ExtracciÃ³n de velas y precios
- `mt5_order_manager.py` - EnvÃ­o y modificaciÃ³n de Ã³rdenes
- `mt5_asset_converter.py` - ConversiÃ³n entre activos (oro, crypto, forex)

### 5.3 Calculador de Indicadores

**Responsabilidades:**
- Calcular EMAs (20, 50) para cada TF
- Calcular RSI para cada TF
- Calcular MACD para cada TF
- Calcular volumen para cada TF
- Formatear indicadores para envÃ­o a IA

**Archivos Asociados:**
- `indicators_calculator.py` - CÃ¡lculo de todos los indicadores
- `indicators_formatter.py` - Formato de salida para IA

### 5.4 Generador de ImÃ¡genes

**Responsabilidades:**
- Generar grÃ¡ficos de velas con/sin indicadores
- Crear imÃ¡genes para 3 timeframes (5M, 15M, 1H)
- Aplicar estilos consistentes
- Exportar en formato compatible con Gemini

**Archivos Asociados:**
- `image_generator.py` - CreaciÃ³n de grÃ¡ficos
- `chart_plotter.py` - Dibujo de velas e indicadores

### 5.5 Cliente IA (Gemini)

**Responsabilidades:**
- Construir prompts segÃºn tipo de bot
- Enviar consultas a Gemini 2.5 Pro API
- Parsear respuestas JSON
- Manejar errores de API
- Registrar tokens y costos exactos
- Mantener contexto de conversaciÃ³n para reevaluaciones

**Archivos Asociados:**
- `gemini_client.py` - Cliente API de Gemini
- `prompt_builder.py` - ConstrucciÃ³n de prompts
- `response_parser.py` - Parsing de respuestas JSON

### 5.6 Gestor de Magic Numbers

**Responsabilidades:**
- Generar Magic Numbers Ãºnicos
- Decodificar Magic Numbers existentes
- Validar formato correcto

**Archivos Asociados:**
- `magic_number_manager.py` - GeneraciÃ³n y decodificaciÃ³n

### 5.7 Calculador de Riesgo

**Responsabilidades:**
- Calcular tamaÃ±o de lote basado en % riesgo
- Ajustar cÃ¡lculo segÃºn tipo de activo
- Validar tamaÃ±os mÃ­nimos/mÃ¡ximos
- Calcular distancia en pips/puntos entre entrada y SL

**Archivos Asociados:**
- `risk_calculator.py` - CÃ¡lculo de lotes
- `asset_specs.py` - Especificaciones por activo

### 5.8 Base de Datos (SQLite)

**Responsabilidades:**
- Almacenar operaciones abiertas y cerradas
- Registrar consultas a IA
- Guardar tokens y costos
- Almacenar diferencias precio sugerido vs real
- Mantener histÃ³rico completo

**Archivos Asociados:**
- `database.py` - Clase para interactuar con BD
- `models.py` - DefiniciÃ³n de tablas y esquemas

### 5.9 Logger y Monitor

**Responsabilidades:**
- Registrar eventos del sistema
- Capturar errores y excepciones
- Generar logs estructurados
- Facilitar debugging

**Archivos Asociados:**
- `logger.py` - Sistema de logging
- `monitor.py` - Monitoreo de estado

---

## 6. FLUJO DE TRABAJO PRINCIPAL

### 6.1 Ciclo de EjecuciÃ³n

```
INICIO (Cada hora en punto dentro de horario 06:00-13:00 PerÃº)
â”‚
â”œâ”€â–º [1] VERIFICAR FILTROS GLOBALES
â”‚   â”œâ”€â–º Horario dentro de 06:00-13:00 hora PerÃº?
â”‚   â”œâ”€â–º Es dÃ­a hÃ¡bil (Lunes-Viernes)?
â”‚   â””â”€â–º Si NO pasa filtros â†’ ESPERAR prÃ³xima hora
â”‚
â”œâ”€â–º [2] ITERAR SOBRE LISTA DE ACTIVOS
â”‚   â”‚   (Ejemplo: EURUSD, GBPUSD, XAUUSD, BTCUSD, etc.)
â”‚   â”‚
â”‚   â””â”€â–º Para cada ACTIVO:
â”‚       â”‚
â”‚       â”œâ”€â–º [3] CONSULTAR OPERACIONES ABIERTAS
â”‚       â”‚   â”œâ”€â–º Â¿Existe operaciÃ³n con Magic Number de este Bot+IA en este activo?
â”‚       â”‚   â”œâ”€â–º SI existe â†’ REEVALUACIÃ“N (ir a paso 7)
â”‚       â”‚   â””â”€â–º NO existe â†’ EVALUACIÃ“N NUEVA (continuar a paso 4)
â”‚       â”‚
â”‚       â”œâ”€â–º [4] EXTRACCIÃ“N DE DATOS MT5
â”‚       â”‚   â”œâ”€â–º Extraer Ãºltimas velas cerradas:
â”‚       â”‚   â”‚   â”œâ”€â–º TF 5M: Ãºltimas 100 velas
â”‚       â”‚   â”‚   â”œâ”€â–º TF 15M: Ãºltimas 80 velas
â”‚       â”‚   â”‚   â””â”€â–º TF 1H: Ãºltimas 50 velas
â”‚       â”‚   â”œâ”€â–º Obtener precio actual (bid/ask)
â”‚       â”‚   â””â”€â–º Solo velas CERRADAS (nunca vela en curso)
â”‚       â”‚
â”‚       â”œâ”€â–º [5] CALCULAR INDICADORES
â”‚       â”‚   â”œâ”€â–º Para cada TF (5M, 15M, 1H):
â”‚       â”‚   â”‚   â”œâ”€â–º EMA 20
â”‚       â”‚   â”‚   â”œâ”€â–º EMA 50
â”‚       â”‚   â”‚   â”œâ”€â–º RSI
â”‚       â”‚   â”‚   â”œâ”€â–º MACD
â”‚       â”‚   â”‚   â””â”€â–º Volumen
â”‚       â”‚   â””â”€â–º Generar imÃ¡genes si el bot lo requiere
â”‚       â”‚
â”‚       â”œâ”€â–º [6] CONSULTAR IA (EVALUACIÃ“N NUEVA)
â”‚       â”‚   â”œâ”€â–º Construir prompt segÃºn tipo de bot
â”‚       â”‚   â”œâ”€â–º Enviar a Gemini 2.5 Pro
â”‚       â”‚   â”œâ”€â–º Recibir respuesta JSON
â”‚       â”‚   â”œâ”€â–º Parsear decisiÃ³n (OPERAR/NO_OPERAR)
â”‚       â”‚   â””â”€â–º Registrar tokens y costos exactos
â”‚       â”‚
â”‚       â”œâ”€â–º [7] EVALUAR DECISIÃ“N
â”‚       â”‚   â”œâ”€â–º Si NO_OPERAR â†’ Registrar en BD y pasar a siguiente activo
â”‚       â”‚   â””â”€â–º Si OPERAR â†’ Continuar a paso 8
â”‚       â”‚
â”‚       â”œâ”€â–º [8] SISTEMA DUAL: ABRIR 2 OPERACIONES
â”‚       â”‚   â”‚
â”‚       â”‚   â”œâ”€â–º OPERACIÃ“N MARKET:
â”‚       â”‚   â”‚   â”œâ”€â–º Calcular lote basado en % riesgo (IA)
â”‚       â”‚   â”‚   â”œâ”€â–º Precio entrada = Precio actual (bid/ask)
â”‚       â”‚   â”‚   â”œâ”€â–º SL y TP segÃºn respuesta IA
â”‚       â”‚   â”‚   â”œâ”€â–º Magic Number = [Bot][IA][01] (Market)
â”‚       â”‚   â”‚   â””â”€â–º Ejecutar orden Market en MT5
â”‚       â”‚   â”‚
â”‚       â”‚   â””â”€â–º OPERACIÃ“N LIMIT:
â”‚       â”‚       â”œâ”€â–º Calcular lote basado en % riesgo (IA)
â”‚       â”‚       â”œâ”€â–º Precio entrada = Precio sugerido por IA
â”‚       â”‚       â”œâ”€â–º SL y TP segÃºn respuesta IA
â”‚       â”‚       â”œâ”€â–º Magic Number = [Bot][IA][02] (Limit)
â”‚       â”‚       â””â”€â–º Ejecutar orden Limit en MT5
â”‚       â”‚
â”‚       â”œâ”€â–º [9] REGISTRAR EN BD
â”‚       â”‚   â”œâ”€â–º Guardar ambas operaciones
â”‚       â”‚   â”œâ”€â–º ID de conversaciÃ³n IA
â”‚       â”‚   â”œâ”€â–º Precio sugerido vs precio real (Market)
â”‚       â”‚   â”œâ”€â–º Tokens consumidos
â”‚       â”‚   â”œâ”€â–º Costo de consulta
â”‚       â”‚   â””â”€â–º Timestamp y datos completos
â”‚       â”‚
â”‚       â””â”€â–º [10] CONTINUAR CON SIGUIENTE ACTIVO
â”‚
â””â”€â–º [11] ESPERAR PRÃ“XIMA HORA (Loop continuo)
```

### 6.2 Flujo de ReevaluaciÃ³n (OperaciÃ³n Abierta)

```
REEVALUACIÃ“N (Cada 10 minutos si hay operaciÃ³n abierta)
â”‚
â”œâ”€â–º [1] DETECTAR OPERACIÃ“N ABIERTA
â”‚   â”œâ”€â–º Buscar por Magic Number de este Bot+IA+Activo
â”‚   â””â”€â–º Recuperar ID de conversaciÃ³n original de BD
â”‚
â”œâ”€â–º [2] EXTRAER DATOS ACTUALIZADOS
â”‚   â”œâ”€â–º Ãšltima vela cerrada de cada TF
â”‚   â”œâ”€â–º Indicadores actualizados
â”‚   â”œâ”€â–º P/L actual de la operaciÃ³n
â”‚   â”œâ”€â–º Precio actual
â”‚   â””â”€â–º Generar imÃ¡genes si aplica (segÃºn tipo bot)
â”‚
â”œâ”€â–º [3] CONSULTAR IA (CONTINUACIÃ“N DE CONVERSACIÃ“N)
â”‚   â”œâ”€â–º Usar mismo ID de conversaciÃ³n
â”‚   â”œâ”€â–º Enviar datos actualizados
â”‚   â”œâ”€â–º NO aplicar filtros (siempre consultar)
â”‚   â”œâ”€â–º Recibir decisiÃ³n: MANTENER/ACTUALIZAR/CERRAR
â”‚   â””â”€â–º Registrar tokens y costos
â”‚
â”œâ”€â–º [4] EJECUTAR DECISIÃ“N
â”‚   â”œâ”€â–º MANTENER â†’ No hacer nada, esperar prÃ³xima reevaluaciÃ³n
â”‚   â”œâ”€â–º ACTUALIZAR â†’ Modificar SL y/o TP en MT5
â”‚   â””â”€â–º CERRAR â†’ Cerrar posiciÃ³n en MT5
â”‚
â”œâ”€â–º [5] REGISTRAR EN BD
â”‚   â”œâ”€â–º Actualizar registro de operaciÃ³n
â”‚   â”œâ”€â–º Guardar nueva consulta IA
â”‚   â”œâ”€â–º Acumular tokens y costos
â”‚   â””â”€â–º Si cerrÃ³: registrar resultado final (P/L)
â”‚
â””â”€â–º [6] ESPERAR PRÃ“XIMA REEVALUACIÃ“N (10 minutos)
```

### 6.3 Consideraciones Importantes

#### 6.3.1 Velas Cerradas Ãšnicamente
- **CRÃTICO:** Solo enviar velas completamente cerradas a la IA
- La vela actual (en curso) puede tener indicadores variables
- CÃ¡lculo de indicadores SIEMPRE sobre velas cerradas

#### 6.3.2 Datos Reales
- **NUNCA** enviar datos estimados, ficticios o "imaginados"
- Si MT5 no responde, NO inventar valores
- Si falta informaciÃ³n, reintentar o esperar siguiente ciclo

#### 6.3.3 SincronizaciÃ³n de Hora
- Ejecutar al inicio de cada hora (HH:00:00)
- Esperar cierre de vela antes de extraer datos
- Considerar pequeÃ±o delay (ej: 5 segundos post-cierre) para asegurar datos finales

---

## 7. SISTEMA DE MAGIC NUMBERS

### 7.1 Estructura del Magic Number

El Magic Number es un identificador Ãºnico de **6 dÃ­gitos** que codifica informaciÃ³n sobre la operaciÃ³n:

```
[Bot ID][IA ID][Tipo Orden]

DÃ­gitos: [1][2][3][4][5][6]
         â””â”€â”€â”˜ â””â”€â”€â”˜ â””â”€â”€â”€â”˜
          Bot   IA   Tipo
```

**Ejemplo:**
- Magic Number: `110201`
  - Bot: `11` (Bot 1)
  - IA: `02` (Gemini configuraciÃ³n 2)
  - Tipo: `01` (Market)

### 7.2 CodificaciÃ³n

#### Bot ID (2 dÃ­gitos)
| Bot | ID |
|-----|-----|
| Bot 1 | 11 |
| Bot 2 | 12 |
| Bot 3 | 13 |
| Bot 4 | 14 |
| Bot 5 | 15 |
| Bot 6+ | 16, 17... |

#### IA ID (2 dÃ­gitos)
| IA | ID |
|----|-----|
| Gemini 2.5 Pro (Config 1) | 01 |
| Gemini 2.5 Pro (Config 2) | 02 |
| Gemini 2.5 Flash | 03 |
| GPT-4 | 04 |
| Claude | 05 |
| Otros | 06+ |

#### Tipo Orden (2 dÃ­gitos)
| Tipo | ID |
|------|-----|
| Market | 01 |
| Limit | 02 |

### 7.3 Ejemplos de Magic Numbers

| Magic Number | Bot | IA | Tipo | DescripciÃ³n |
|--------------|-----|-----|------|-------------|
| 110101 | 1 | Gemini Config 1 | Market | Bot 1, orden market |
| 110102 | 1 | Gemini Config 1 | Limit | Bot 1, orden limit |
| 120201 | 2 | Gemini Config 2 | Market | Bot 2, orden market |
| 130102 | 3 | Gemini Config 1 | Limit | Bot 3, orden limit |

### 7.4 Uso del Magic Number

#### En Apertura de OperaciÃ³n
```python
magic_number = generate_magic_number(
    bot_id=1,
    ia_id=1,
    order_type='market'  # o 'limit'
)
# Resultado: 110101
```

#### En Consulta de Operaciones
```python
# Buscar si existe operaciÃ³n para Bot 1, IA 1, en activo EURUSD
open_positions = mt5.positions_get(
    symbol="EURUSD",
    magic=110101  # Market
)
# O tambiÃ©n verificar:
open_positions_limit = mt5.positions_get(
    symbol="EURUSD",
    magic=110102  # Limit
)
```

#### En ReevaluaciÃ³n
- Decodificar Magic Number para identificar bot y configuraciÃ³n
- Recuperar ID de conversaciÃ³n IA de la BD usando Magic Number
- Continuar conversaciÃ³n con contexto correcto

### 7.5 Ventajas del Sistema

1. **IdentificaciÃ³n Ãšnica:** Cada operaciÃ³n tiene un identificador inequÃ­voco
2. **Trazabilidad:** Permite rastrear origen de cada operaciÃ³n
3. **SeparaciÃ³n:** Diferencia Market vs Limit del mismo evento de apertura
4. **Escalabilidad:** Soporta hasta 99 bots, 99 IAs
5. **Consulta Eficiente:** MT5 permite filtrar por Magic Number

---

## 8. GESTIÃ“N MULTI-ACTIVO

### 8.1 Lista de Activos

Se mantendrÃ¡ una **lista configurable** de activos sobre los cuales cada bot iterarÃ¡:

**Archivo:** `config/assets.json`

```json
{
  "active_assets": [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "XAUUSD",
    "BTCUSD",
    "ETHUSD"
  ]
}
```

### 8.2 LÃ³gica de IteraciÃ³n

En cada ciclo horario:

```python
for asset in active_assets:
    # Verificar si ya existe operaciÃ³n abierta para este bot+ia+asset
    has_market = check_open_position(asset, magic_market)
    has_limit = check_open_position(asset, magic_limit)
    
    if has_market or has_limit:
        # ReevaluaciÃ³n
        reevaluate_position(asset)
    else:
        # EvaluaciÃ³n nueva
        evaluate_new_entry(asset)
```

### 8.3 RestricciÃ³n por Activo

**Regla:** Un bot puede tener **solo UNA operaciÃ³n abierta por activo**, pero puede tener operaciones abiertas en **mÃºltiples activos simultÃ¡neamente**.

**Ejemplo vÃ¡lido:**
- Bot 1 tiene operaciÃ³n Market en EURUSD (Magic: 110101)
- Bot 1 tiene operaciÃ³n Limit en EURUSD (Magic: 110102) âœ“ (mismo evento)
- Bot 1 tiene operaciÃ³n Market en GBPUSD (Magic: 110101) âœ“
- Bot 1 tiene operaciÃ³n Market en XAUUSD (Magic: 110101) âœ“

**Ejemplo NO vÃ¡lido:**
- Bot 1 tiene operaciÃ³n Market en EURUSD (Magic: 110101)
- Bot 1 intenta abrir OTRA operaciÃ³n Market en EURUSD âœ—

**ValidaciÃ³n:**
Antes de evaluar entrada, verificar:
```python
existing_market = check_position(asset, bot_magic_market)
existing_limit = check_position(asset, bot_magic_limit)

# Si alguna de las dos (market o limit) del evento anterior existe:
if existing_market or existing_limit:
    # Ir a reevaluaciÃ³n
    reevaluate()
else:
    # Evaluar nueva entrada
    evaluate_new()
```

---

## 9. SISTEMA DUAL MARKET/LIMIT

### 9.1 Concepto

**SIEMPRE** que la IA decide operar, el bot abrirÃ¡ **DOS operaciones simultÃ¡neamente**:

1. **OperaciÃ³n MARKET:** Entrada al precio actual de mercado
2. **OperaciÃ³n LIMIT:** Entrada al precio sugerido por la IA

### 9.2 PropÃ³sito

Comparar rendimiento entre:
- Entradas inmediatas (Market)
- Entradas en niveles especÃ­ficos (Limit)

Esto permite evaluar:
- PrecisiÃ³n de predicciones de la IA
- Diferencia en P/L entre ambos tipos
- Tasa de activaciÃ³n de lÃ­mites
- Efectividad de cada estrategia

### 9.3 Flujo de Apertura Dual

```python
# La IA responde:
{
    "accion": "OPERAR",
    "direccion": "BUY",
    "precio_entrada": 1.1050,  # Precio sugerido por IA
    "stop_loss": 1.1000,
    "take_profit": 1.1150,
    "riesgo_porcentaje": 2.0
}

# El bot ejecuta:

# 1. ORDEN MARKET
precio_actual = get_current_price("EURUSD")  # Ej: 1.1045
abrir_orden(
    tipo="MARKET",
    direccion="BUY",
    precio=precio_actual,  # 1.1045 (real en ese momento)
    sl=1.1000,
    tp=1.1150,
    lote=calcular_lote(riesgo=2.0, distancia_sl=45_pips),
    magic=110101  # Market
)

# 2. ORDEN LIMIT
abrir_orden(
    tipo="LIMIT",
    direccion="BUY",
    precio=1.1050,  # Precio sugerido por IA
    sl=1.1000,
    tp=1.1150,
    lote=calcular_lote(riesgo=2.0, distancia_sl=50_pips),
    magic=110102  # Limit
)
```

### 9.4 Escenarios

#### Escenario A: Precio actual < Precio sugerido (BUY)
- **Market:** Compra inmediata a precio actual (ej: 1.1045)
- **Limit:** Orden pendiente en precio superior (ej: 1.1050)
- **Resultado:** Market se ejecuta de inmediato, Limit puede no activarse

#### Escenario B: Precio actual > Precio sugerido (BUY)
- **Market:** Compra inmediata a precio actual (ej: 1.1055)
- **Limit:** Orden pendiente en precio inferior (ej: 1.1050)
- **Resultado:** Ambas pueden ejecutarse, o solo Market si precio no retrocede

#### Escenario C: Precio actual cerca del sugerido
- **Market:** Ejecuta al precio disponible
- **Limit:** Se activa rÃ¡pidamente si el precio toca el nivel

### 9.5 Diferencias Clave

| Aspecto | MARKET | LIMIT |
|---------|--------|-------|
| Precio Entrada | Precio actual (bid/ask) | Precio sugerido por IA |
| EjecuciÃ³n | Inmediata | Cuando precio alcanza nivel |
| Magic Number | [Bot][IA]01 | [Bot][IA]02 |
| Registro BD | Precio sugerido â‰  precio real | Precio sugerido = precio entrada |
| Slippage | Posible | MÃ­nimo (ejecuciÃ³n a precio exacto) |

### 9.6 ReevaluaciÃ³n de Operaciones Duales

- **Cada operaciÃ³n se reevalÃºa independientemente**
- Se usa el mismo ID de conversaciÃ³n para ambas (o IDs separados segÃºn diseÃ±o)
- La IA puede decidir diferente para cada una:
  - Mantener Market, cerrar Limit
  - Actualizar SL en ambas
  - Cerrar ambas si condiciones cambiaron

---

## 10. INDICADORES Y TIMEFRAMES

### 10.1 Timeframes Utilizados

Todos los bots trabajarÃ¡n con **3 timeframes**:

| Timeframe | CÃ³digo MT5 | Velas a Enviar |
|-----------|------------|----------------|
| 5 Minutos | M5 | 100 Ãºltimas velas cerradas |
| 15 Minutos | M15 | 80 Ãºltimas velas cerradas |
| 1 Hora | H1 | 50 Ãºltimas velas cerradas |

### 10.2 Indicadores TÃ©cnicos

Para **cada timeframe**, se calcularÃ¡n los siguientes indicadores:

| Indicador | ParÃ¡metros | DescripciÃ³n |
|-----------|------------|-------------|
| **EMA 20** | Periodo: 20 | Media mÃ³vil exponencial rÃ¡pida |
| **EMA 50** | Periodo: 50 | Media mÃ³vil exponencial lenta |
| **RSI** | Periodo: 14 | Relative Strength Index (sobreventa/sobrecompra) |
| **MACD** | 12, 26, 9 | Moving Average Convergence Divergence |
| **Volumen** | - | Volumen de cada vela |

### 10.3 Formato de EnvÃ­o a IA (NumÃ©rico)

Para bots que usan indicadores numÃ©ricos (Bot 1, 2):

```json
{
  "activo": "EURUSD",
  "precio_actual": 1.1045,
  
  "timeframe_5M": {
    "ultima_vela": {
      "open": 1.1043,
      "high": 1.1048,
      "low": 1.1041,
      "close": 1.1045,
      "volume": 150
    },
    "indicadores": {
      "ema_20": 1.1042,
      "ema_50": 1.1038,
      "rsi": 58.3,
      "macd": {
        "macd_line": 0.0003,
        "signal_line": 0.0002,
        "histogram": 0.0001
      }
    },
    "ultimas_100_velas": [...]
  },
  
  "timeframe_15M": {
    "ultima_vela": {...},
    "indicadores": {...},
    "ultimas_80_velas": [...]
  },
  
  "timeframe_1H": {
    "ultima_vela": {...},
    "indicadores": {...},
    "ultimas_50_velas": [...]
  }
}
```

### 10.4 Formato de ImÃ¡genes (Visual)

Para bots que usan imÃ¡genes (Bot 3, 4, 5):

#### Bot 3: ImÃ¡genes con indicadores dibujados
- **3 imÃ¡genes PNG/JPG**
- Velas + EMA 20 + EMA 50 + RSI + MACD superpuestos
- Una imagen por timeframe (5M, 15M, 1H)

#### Bot 4: Imagen sin indicadores (apertura), numÃ©ricos (reevaluaciÃ³n)
- **1 imagen (apertura):** Solo velas, sin indicadores
- **ReevaluaciÃ³n:** Indicadores numÃ©ricos + Ãºltimas velas

#### Bot 5: Imagen de velas + indicadores separados
- **3 imÃ¡genes:** Solo velas (sin indicadores)
- **JSON separado:** Indicadores calculados para cada TF

### 10.5 CÃ¡lculo de Indicadores

**LibrerÃ­a recomendada:** `ta` (Technical Analysis Library) o `pandas_ta`

```python
import pandas as pd
import ta

def calcular_indicadores(velas_df, timeframe):
    """
    velas_df: DataFrame con columnas ['open','high','low','close','volume']
    """
    # EMA 20
    ema_20 = ta.trend.ema_indicator(velas_df['close'], window=20)
    
    # EMA 50
    ema_50 = ta.trend.ema_indicator(velas_df['close'], window=50)
    
    # RSI
    rsi = ta.momentum.rsi(velas_df['close'], window=14)
    
    # MACD
    macd = ta.trend.MACD(velas_df['close'])
    
    return {
        'ema_20': ema_20.iloc[-1],
        'ema_50': ema_50.iloc[-1],
        'rsi': rsi.iloc[-1],
        'macd': {
            'macd_line': macd.macd().iloc[-1],
            'signal_line': macd.macd_signal().iloc[-1],
            'histogram': macd.macd_diff().iloc[-1]
        },
        'volumen': velas_df['volume'].iloc[-1]
    }
```

---

## 11. FILTROS Y HORARIOS

### 11.1 Filtro de Horario

**Horario de OperaciÃ³n:** 06:00 - 13:00 (Hora de PerÃº, GMT-5)

```python
import pytz
from datetime import datetime

def validar_horario():
    tz_peru = pytz.timezone('America/Lima')
    hora_actual = datetime.now(tz_peru)
    
    # Verificar hora
    if hora_actual.hour < 6 or hora_actual.hour >= 13:
        return False
    
    # Verificar dÃ­a hÃ¡bil (Lunes=0, Domingo=6)
    if hora_actual.weekday() >= 5:  # SÃ¡bado o Domingo
        return False
    
    return True
```

### 11.2 Frecuencia de EjecuciÃ³n

- **EvaluaciÃ³n nueva:** Cada hora en punto (HH:00:00)
- **ReevaluaciÃ³n:** Cada 10 minutos si hay operaciÃ³n abierta

**ImplementaciÃ³n sugerida:**
```python
import schedule
import time

def job_evaluacion():
    if validar_horario():
        ejecutar_evaluacion()

def job_reevaluacion():
    if validar_horario():
        ejecutar_reevaluacion()

# Ejecutar evaluaciÃ³n cada hora
schedule.every().hour.at(":00").do(job_evaluacion)

# Ejecutar reevaluaciÃ³n cada 10 minutos
schedule.every(10).minutes.do(job_reevaluacion)

while True:
    schedule.run_pending()
    time.sleep(1)
```

### 11.3 Filtros Adicionales (Futuro)

Actualmente solo se implementa filtro de horario y dÃ­as. En el futuro se pueden agregar:

- **Volatilidad:** Solo operar si ATR > umbral
- **Spread:** No operar si spread > X pips
- **Eventos econÃ³micos:** Evitar operar 30 min antes/despuÃ©s de noticias importantes
- **Drawdown:** Pausar si pÃ©rdida acumulada > X%

**Archivo de configuraciÃ³n sugerido:** `config/filters.json`

```json
{
  "horario": {
    "inicio": "06:00",
    "fin": "13:00",
    "timezone": "America/Lima",
    "dias_habiles": true
  },
  "volatilidad": {
    "enabled": false,
    "atr_minimo": 0.0010
  },
  "spread": {
    "enabled": false,
    "spread_maximo_pips": 3
  }
}
```

---

## 12. INTEGRACIÃ“N CON IA (GEMINI 2.5 PRO)

### 12.1 ConfiguraciÃ³n de API

**Proveedor:** Google Gemini  
**Modelo:** gemini-2.5-pro (o gemini-2.0-flash-exp segÃºn disponibilidad)  
**AutenticaciÃ³n:** API Key

**Archivo:** `config/gemini_config.json`

```json
{
  "api_key": "GEMINI_API_KEY_AQUI",
  "model": "gemini-2.5-pro",
  "temperature": 0.7,
  "max_tokens": 2000,
  "timeout": 30
}
```

### 12.2 ConstrucciÃ³n de Prompts

#### Prompt Base (GenÃ©rico)

```
Eres un asistente experto en trading de FOREX. Tu tarea es analizar los datos proporcionados y decidir si abrir una operaciÃ³n, mantener, actualizar o cerrar.

DATOS RECIBIDOS:
- Activo: {activo}
- Precio actual: {precio_actual}
- Timeframes: 5M, 15M, 1H
- Indicadores: EMA 20, EMA 50, RSI, MACD, Volumen
- Ãšltimas velas: [...]

INSTRUCCIONES:
1. Analiza los indicadores y velas de los 3 timeframes
2. Identifica tendencias, soportes/resistencias, seÃ±ales de entrada/salida
3. Decide si OPERAR, NO_OPERAR, MANTENER, ACTUALIZAR o CERRAR
4. Si decides OPERAR, especifica:
   - DirecciÃ³n: BUY o SELL
   - Tipo de orden: MARKET o LIMIT
   - Precio de entrada (si es LIMIT)
   - Stop Loss
   - Take Profit
   - Porcentaje de riesgo (1-5%)

FORMATO DE RESPUESTA (JSON):
{
  "accion": "OPERAR|NO_OPERAR|MANTENER|ACTUALIZAR|CERRAR",
  "direccion": "BUY|SELL",
  "tipo_orden": "MARKET|LIMIT",
  "precio_entrada": 1.2345,
  "stop_loss": 1.2300,
  "take_profit": 1.2450,
  "riesgo_porcentaje": 2.0,
  "razonamiento": "ExplicaciÃ³n breve de la decisiÃ³n"
}
```

#### Prompt para ReevaluaciÃ³n

```
OPERACIÃ“N ABIERTA:
- Activo: {activo}
- DirecciÃ³n: {direccion}
- Precio entrada: {precio_entrada}
- Stop Loss actual: {sl_actual}
- Take Profit actual: {tp_actual}
- P/L actual: {profit_loss}
- Precio actual: {precio_actual}

DATOS ACTUALIZADOS:
[... indicadores y velas actuales ...]

DECISIÃ“N:
Analiza si debes:
- MANTENER: No hacer cambios
- ACTUALIZAR: Modificar SL y/o TP (especifica nuevos valores)
- CERRAR: Cerrar la operaciÃ³n ahora

FORMATO DE RESPUESTA (JSON):
{
  "accion": "MANTENER|ACTUALIZAR|CERRAR",
  "nuevo_stop_loss": 1.2350,  // Solo si ACTUALIZAR
  "nuevo_take_profit": 1.2500, // Solo si ACTUALIZAR
  "razonamiento": "ExplicaciÃ³n"
}
```

### 12.3 EnvÃ­o y RecepciÃ³n

```python
import google.generativeai as genai
import json

def consultar_gemini(prompt, imagenes=None):
    """
    EnvÃ­a prompt (y opcionalmente imÃ¡genes) a Gemini
    """
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-pro')
    
    try:
        if imagenes:
            # Enviar con imÃ¡genes
            response = model.generate_content([prompt] + imagenes)
        else:
            # Solo texto
            response = model.generate_content(prompt)
        
        # Extraer respuesta
        texto_respuesta = response.text
        
        # Parsear JSON
        respuesta_json = json.loads(texto_respuesta)
        
        # Obtener tokens y costo
        tokens_usados = response.usage_metadata.total_token_count
        costo = calcular_costo(tokens_usados)
        
        return {
            'respuesta': respuesta_json,
            'tokens': tokens_usados,
            'costo': costo
        }
        
    except Exception as e:
        raise Exception(f"Error al consultar Gemini: {e}")
```

### 12.4 Manejo de Conversaciones

Para **reevaluaciones**, mantener contexto de conversaciÃ³n:

```python
# Al abrir operaciÃ³n, guardar chat session
chat = model.start_chat(history=[])
response = chat.send_message(prompt_inicial)

# Guardar en BD:
conversation_id = guardar_conversacion(chat)

# En reevaluaciÃ³n, recuperar y continuar:
chat = recuperar_conversacion(conversation_id)
response = chat.send_message(prompt_reevaluacion)
```

### 12.5 CÃ¡lculo de Costos

**Precios Gemini 2.5 Pro (aproximados, verificar documentaciÃ³n oficial):**
- Input: $0.00125 / 1K tokens
- Output: $0.005 / 1K tokens

```python
def calcular_costo(tokens_input, tokens_output):
    costo_input = (tokens_input / 1000) * 0.00125
    costo_output = (tokens_output / 1000) * 0.005
    return costo_input + costo_output
```

---

## 13. ALMACENAMIENTO DE DATOS

### 13.1 Base de Datos: SQLite

**Archivo:** `database/trading_bot.db`

### 13.2 Estructura de Tablas

#### Tabla: `operaciones`

Almacena todas las operaciones abiertas y cerradas.

```sql
CREATE TABLE operaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    magic_number INTEGER NOT NULL,
    bot_id INTEGER NOT NULL,
    ia_id INTEGER NOT NULL,
    tipo_orden TEXT NOT NULL,  -- 'market' o 'limit'
    activo TEXT NOT NULL,
    direccion TEXT NOT NULL,   -- 'BUY' o 'SELL'
    
    -- Precios y parÃ¡metros
    precio_sugerido REAL NOT NULL,
    precio_entrada_real REAL,
    stop_loss REAL NOT NULL,
    take_profit REAL NOT NULL,
    lote REAL NOT NULL,
    riesgo_porcentaje REAL NOT NULL,
    
    -- Estado
    estado TEXT NOT NULL,  -- 'abierta', 'cerrada', 'pendiente'
    
    -- Resultados
    profit_loss REAL,
    fecha_apertura DATETIME NOT NULL,
    fecha_cierre DATETIME,
    
    -- Referencia a IA
    conversation_id TEXT,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_magic_activo ON operaciones(magic_number, activo);
CREATE INDEX idx_estado ON operaciones(estado);
```

#### Tabla: `consultas_ia`

Registro de todas las consultas enviadas a la IA.

```sql
CREATE TABLE consultas_ia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operacion_id INTEGER,  -- Puede ser NULL si no operÃ³
    bot_id INTEGER NOT NULL,
    ia_id INTEGER NOT NULL,
    activo TEXT NOT NULL,
    
    -- Tipo de consulta
    tipo_consulta TEXT NOT NULL,  -- 'evaluacion' o 'reevaluacion'
    
    -- Prompt y respuesta
    prompt TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    
    -- Tokens y costos
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    tokens_total INTEGER NOT NULL,
    costo_usd REAL NOT NULL,
    
    -- DecisiÃ³n tomada
    accion_decidida TEXT NOT NULL,  -- 'OPERAR', 'NO_OPERAR', 'MANTENER', etc.
    
    -- Timestamp
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (operacion_id) REFERENCES operaciones(id)
);

CREATE INDEX idx_operacion ON consultas_ia(operacion_id);
CREATE INDEX idx_bot_ia ON consultas_ia(bot_id, ia_id);
```

#### Tabla: `metricas_diarias`

Resumen de mÃ©tricas por dÃ­a para anÃ¡lisis rÃ¡pido.

```sql
CREATE TABLE metricas_diarias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    
    -- Operaciones
    total_operaciones INTEGER DEFAULT 0,
    operaciones_ganadoras INTEGER DEFAULT 0,
    operaciones_perdedoras INTEGER DEFAULT 0,
    
    -- Resultados
    profit_loss_total REAL DEFAULT 0,
    profit_loss_market REAL DEFAULT 0,
    profit_loss_limit REAL DEFAULT 0,
    
    -- Costos IA
    total_consultas INTEGER DEFAULT 0,
    tokens_totales INTEGER DEFAULT 0,
    costo_ia_total REAL DEFAULT 0,
    
    -- Ratios
    winrate REAL,
    profit_factor REAL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(bot_id, fecha)
);
```

#### Tabla: `configuracion`

ConfiguraciÃ³n y parÃ¡metros del sistema.

```sql
CREATE TABLE configuracion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT UNIQUE NOT NULL,
    valor TEXT NOT NULL,
    descripcion TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insertar configuraciÃ³n inicial
INSERT INTO configuracion (clave, valor, descripcion) VALUES
('activos', '["EURUSD","GBPUSD","XAUUSD"]', 'Lista de activos a operar'),
('horario_inicio', '06:00', 'Hora de inicio (PerÃº)'),
('horario_fin', '13:00', 'Hora de fin (PerÃº)'),
('reevaluacion_intervalo', '10', 'Minutos entre reevaluaciones');
```

### 13.3 Operaciones CRUD

```python
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='database/trading_bot.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def insertar_operacion(self, datos):
        query = """
        INSERT INTO operaciones (
            magic_number, bot_id, ia_id, tipo_orden, activo, direccion,
            precio_sugerido, precio_entrada_real, stop_loss, take_profit,
            lote, riesgo_porcentaje, estado, conversation_id, fecha_apertura
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, datos)
        self.conn.commit()
        return self.cursor.lastrowid
    
    def buscar_operacion_abierta(self, activo, magic_number):
        query = """
        SELECT * FROM operaciones
        WHERE activo = ? AND magic_number = ? AND estado = 'abierta'
        """
        self.cursor.execute(query, (activo, magic_number))
        return self.cursor.fetchone()
    
    def insertar_consulta_ia(self, datos):
        query = """
        INSERT INTO consultas_ia (
            operacion_id, bot_id, ia_id, activo, tipo_consulta,
            prompt, respuesta, tokens_input, tokens_output,
            tokens_total, costo_usd, accion_decidida
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, datos)
        self.conn.commit()
    
    def cerrar_operacion(self, operacion_id, profit_loss):
        query = """
        UPDATE operaciones
        SET estado = 'cerrada', profit_loss = ?, fecha_cierre = ?, updated_at = ?
        WHERE id = ?
        """
        self.cursor.execute(query, (profit_loss, datetime.now(), datetime.now(), operacion_id))
        self.conn.commit()
```

---

## 14. MANEJO DE ERRORES

### 14.1 Principios Fundamentales

1. **NUNCA enviar datos ficticios a la IA**
2. **Reintentar hasta 3 veces** ante fallos de API/MT5
3. **Esperar siguiente iteraciÃ³n** si reintentos fallan
4. **Registrar todos los errores** en logs

### 14.2 Estrategia de Reintentos

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"Fallo despuÃ©s de {max_attempts} intentos: {e}")
                        raise
                    logger.warning(f"Intento {attempts} fallÃ³: {e}. Reintentando en {delay}s...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry(max_attempts=3, delay=2)
def obtener_datos_mt5(activo):
    # Si falla, reintenta hasta 3 veces
    datos = mt5.copy_rates_from_pos(activo, mt5.TIMEFRAME_M5, 0, 100)
    if datos is None:
        raise Exception("MT5 no respondiÃ³")
    return datos
```

### 14.3 Tipos de Errores

#### Error de ConexiÃ³n MT5
```python
try:
    datos = obtener_datos_mt5("EURUSD")
except Exception as e:
    logger.error(f"No se pudieron obtener datos MT5: {e}")
    # NO enviar datos ficticios
    # Esperar siguiente iteraciÃ³n
    return
```

#### Error de API Gemini
```python
try:
    respuesta = consultar_gemini(prompt)
except Exception as e:
    logger.error(f"Fallo en API Gemini: {e}")
    # Reintentar o esperar
    return
```

#### Error de Parsing
```python
try:
    decision = json.loads(respuesta_ia)
except json.JSONDecodeError as e:
    logger.error(f"Respuesta IA no es JSON vÃ¡lido: {e}")
    # Registrar en BD como error
    return
```

### 14.4 Registro de Errores

```python
import logging

# Configurar logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Uso:
logger.info("Iniciando evaluaciÃ³n para EURUSD")
logger.warning("Spread alto detectado: 5 pips")
logger.error("Fallo al conectar con MT5")
```

---

## 15. ESTRUCTURA MODULAR DEL CÃ“DIGO

### 15.1 OrganizaciÃ³n de Directorios

```
trading_bot/
â”‚
â”œâ”€â”€ config/
â”‚   â”œâ”€â”€ gemini_config.json
â”‚   â”œâ”€â”€ mt5_config.json
â”‚   â”œâ”€â”€ assets.json
â”‚   â””â”€â”€ filters.json
â”‚
â”œâ”€â”€ database/
â”‚   â”œâ”€â”€ trading_bot.db
â”‚   â”œâ”€â”€ database.py
â”‚   â””â”€â”€ models.py
â”‚
â”œâ”€â”€ logs/
â”‚   â”œâ”€â”€ bot_1.log
â”‚   â”œâ”€â”€ bot_2.log
â”‚   â””â”€â”€ ...
â”‚
â”œâ”€â”€ bots/
â”‚   â”œâ”€â”€ bot_1/
â”‚   â”‚   â”œâ”€â”€ bot_main.py
â”‚   â”‚   â”œâ”€â”€ bot_config.py
â”‚   â”‚   â””â”€â”€ bot_filters.py
â”‚   â”œâ”€â”€ bot_2/
â”‚   â”‚   â”œâ”€â”€ bot_main.py
â”‚   â”‚   â”œâ”€â”€ bot_config.py
â”‚   â”‚   â””â”€â”€ bot_filters.py
â”‚   â””â”€â”€ ...
â”‚
â”œâ”€â”€ core/
â”‚   â”œâ”€â”€ mt5_connector.py
â”‚   â”œâ”€â”€ mt5_data_extractor.py
â”‚   â”œâ”€â”€ mt5_order_manager.py
â”‚   â”œâ”€â”€ mt5_asset_converter.py
â”‚   â”œâ”€â”€ indicators_calculator.py
â”‚   â”œâ”€â”€ indicators_formatter.py
â”‚   â”œâ”€â”€ image_generator.py
â”‚   â”œâ”€â”€ chart_plotter.py
â”‚   â”œâ”€â”€ gemini_client.py
â”‚   â”œâ”€â”€ prompt_builder.py
â”‚   â”œâ”€â”€ response_parser.py
â”‚   â”œâ”€â”€ magic_number_manager.py
â”‚   â”œâ”€â”€ risk_calculator.py
â”‚   â”œâ”€â”€ asset_specs.py
â”‚   â””â”€â”€ logger.py
â”‚
â”œâ”€â”€ utils/
â”‚   â”œâ”€â”€ helpers.py
â”‚   â”œâ”€â”€ validators.py
â”‚   â””â”€â”€ converters.py
â”‚
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ test_mt5.py
â”‚   â”œâ”€â”€ test_indicators.py
â”‚   â””â”€â”€ test_gemini.py
â”‚
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ documento-principal-proyecto.md
â”‚   â”œâ”€â”€ bot-1-documentacion.md
â”‚   â”œâ”€â”€ bot-2-documentacion.md
â”‚   â””â”€â”€ ...
â”‚
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ README.md
â””â”€â”€ main.py
```

### 15.2 Principios de DiseÃ±o

1. **Un archivo, una responsabilidad:** Cada archivo debe tener ~100-200 lÃ­neas mÃ¡ximo
2. **SeparaciÃ³n por bot:** Cada bot en su propio directorio
3. **Core reutilizable:** MÃ³dulos en `core/` son compartidos por todos los bots
4. **ConfiguraciÃ³n externa:** JSON para parÃ¡metros, no hardcoded
5. **Tests independientes:** Cada componente testeable individualmente

### 15.3 Ejemplo de Archivo

**`core/mt5_connector.py` (~100 lÃ­neas)**

```python
import MetaTrader5 as mt5
from utils.logger import logger

class MT5Connector:
    def __init__(self, login, password, server):
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
    
    def connect(self):
        """Inicializa conexiÃ³n con MT5"""
        if not mt5.initialize():
            logger.error("MT5 initialize() fallÃ³")
            return False
        
        if not mt5.login(self.login, self.password, self.server):
            logger.error("MT5 login() fallÃ³")
            return False
        
        self.connected = True
        logger.info("Conectado a MT5 exitosamente")
        return True
    
    def disconnect(self):
        """Cierra conexiÃ³n"""
        mt5.shutdown()
        self.connected = False
    
    def is_connected(self):
        """Verifica estado de conexiÃ³n"""
        return self.connected and mt5.terminal_info() is not None
```

---

## 16. CONVERSIÃ“N Y CÃLCULO DE ACTIVOS

### 16.1 ProblemÃ¡tica

Diferentes activos tienen **especificaciones distintas**:

| Activo | Tipo | TamaÃ±o Contrato | Valor Pip | DÃ­gitos |
|--------|------|-----------------|-----------|---------|
| EURUSD | Forex | 100,000 | $10 por lote | 5 |
| XAUUSD | Metal | 100 oz | Variable | 2 |
| BTCUSD | Crypto | 1 BTC | Variable | 2 |
| USDJPY | Forex | 100,000 | Â¥1,000 por lote | 3 |

### 16.2 Obtener Especificaciones de MT5

```python
def obtener_specs_activo(simbolo):
    """Obtiene especificaciones del activo desde MT5"""
    info = mt5.symbol_info(simbolo)
    
    if info is None:
        raise Exception(f"No se pudo obtener info de {simbolo}")
    
    return {
        'digits': info.digits,
        'point': info.point,
        'trade_contract_size': info.trade_contract_size,
        'volume_min': info.volume_min,
        'volume_max': info.volume_max,
        'volume_step': info.volume_step,
        'trade_tick_size': info.trade_tick_size,
        'trade_tick_value': info.trade_tick_value
    }
```

### 16.3 CÃ¡lculo de Lote Basado en Riesgo

```python
def calcular_lote_por_riesgo(
    activo,
    balance,
    riesgo_porcentaje,
    precio_entrada,
    stop_loss
):
    """
    Calcula tamaÃ±o de lote basado en % de riesgo
    
    Args:
        activo: SÃ­mbolo (ej: "EURUSD")
        balance: Balance de cuenta
        riesgo_porcentaje: % a arriesgar (ej: 2.0 = 2%)
        precio_entrada: Precio de entrada
        stop_loss: Precio de stop loss
    
    Returns:
        float: TamaÃ±o de lote
    """
    specs = obtener_specs_activo(activo)
    
    # Dinero a arriesgar
    dinero_riesgo = balance * (riesgo_porcentaje / 100)
    
    # Distancia en pips/puntos
    distancia = abs(precio_entrada - stop_loss)
    distancia_pips = distancia / specs['point']
    
    # Valor por pip
    valor_pip = specs['trade_tick_value']
    
    # CÃ¡lculo de lote
    lote = dinero_riesgo / (distancia_pips * valor_pip)
    
    # Ajustar a step permitido
    lote = round(lote / specs['volume_step']) * specs['volume_step']
    
    # Limitar a min/max
    lote = max(specs['volume_min'], min(lote, specs['volume_max']))
    
    return lote
```

### 16.4 Ejemplo de Uso

```python
# Cuenta con $10,000
# Quiere arriesgar 2%
# EURUSD: entrada 1.1050, SL 1.1000 (50 pips)

lote = calcular_lote_por_riesgo(
    activo="EURUSD",
    balance=10000,
    riesgo_porcentaje=2.0,
    precio_entrada=1.1050,
    stop_loss=1.1000
)

# Resultado: 0.04 lotes (ajustado a steps de MT5)
```

---

## 17. REQUISITOS TÃ‰CNICOS

### 17.1 Software

| Componente | VersiÃ³n | PropÃ³sito |
|------------|---------|-----------|
| Python | 3.10+ | Lenguaje principal |
| MetaTrader 5 | Ãšltima | Plataforma de trading |
| SQLite | 3.35+ | Base de datos |
| Pepperstone MT5 | - | Broker |

### 17.2 LibrerÃ­as Python

**`requirements.txt`**

```
MetaTrader5>=5.0.45
google-generativeai>=0.3.0
pandas>=2.0.0
numpy>=1.24.0
ta>=0.11.0
Pillow>=10.0.0
matplotlib>=3.7.0
mplfinance>=0.12.0
pytz>=2023.3
schedule>=1.2.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### 17.3 Hardware

**MÃ­nimo:**
- CPU: 2 cores
- RAM: 4GB
- Disco: 10GB SSD
- Internet: 5 Mbps estable

**Recomendado:**
- CPU: 4+ cores
- RAM: 8GB
- Disco: 20GB SSD
- Internet: 10+ Mbps estable con baja latencia

### 17.4 Sistema Operativo

- Windows 10/11 (recomendado para MT5)
- Linux (con Wine para MT5)
- macOS (con Wine para MT5)

### 17.5 Cuentas y APIs

1. **Pepperstone MT5:**
   - Cuenta demo o real
   - Credenciales: login, password, server

2. **Google Cloud / Gemini:**
   - API Key de Gemini
   - FacturaciÃ³n activada
   - Cuota suficiente

---

## 18. ROADMAP DE IMPLEMENTACIÃ“N

### Fase 1: Fundamentos (Semana 1-2)
- [ ] Configurar entorno Python
- [ ] Instalar MT5 y conectar con Pepperstone
- [ ] Crear estructura de directorios
- [ ] Implementar conexiÃ³n MT5 bÃ¡sica
- [ ] Implementar extracciÃ³n de velas
- [ ] Crear base de datos SQLite (tablas)
- [ ] Implementar logger

### Fase 2: Indicadores e IA (Semana 3-4)
- [ ] Implementar cÃ¡lculo de indicadores (EMA, RSI, MACD)
- [ ] Implementar generaciÃ³n de imÃ¡genes
- [ ] Configurar cliente Gemini
- [ ] Implementar construcciÃ³n de prompts
- [ ] Implementar parsing de respuestas
- [ ] Tests unitarios de componentes

### Fase 3: Bot 1 (Semana 5)
- [ ] Implementar lÃ³gica de filtros
- [ ] Implementar sistema de Magic Numbers
- [ ] Implementar cÃ¡lculo de riesgo y lotes
- [ ] Implementar apertura dual (Market/Limit)
- [ ] Implementar loop principal
- [ ] Implementar reevaluaciÃ³n
- [ ] Tests de integraciÃ³n Bot 1

### Fase 4: Bots 2-5 (Semana 6-8)
- [ ] Adaptar Bot 2 (indicadores numÃ©ricos, prompts diferentes)
- [ ] Implementar Bot 3 (imÃ¡genes con indicadores)
- [ ] Implementar Bot 4 (hÃ­brido)
- [ ] Implementar Bot 5 (imagen + indicadores separados)
- [ ] Tests de cada bot

### Fase 5: Refinamiento (Semana 9-10)
- [ ] Optimizar consultas a BD
- [ ] Implementar manejo robusto de errores
- [ ] Mejorar logging y monitoreo
- [ ] Implementar mÃ©tricas y dashboards
- [ ] Documentar cÃ³digo completo
- [ ] Crear guÃ­as de uso

### Fase 6: Testing en Demo (Semana 11-12)
- [ ] Ejecutar bots en cuenta demo
- [ ] Monitorear comportamiento
- [ ] Ajustar prompts y parÃ¡metros
- [ ] Analizar costos de IA
- [ ] Comparar rendimiento Market vs Limit
- [ ] Identificar y corregir bugs

### Fase 7: ProducciÃ³n (Semana 13+)
- [ ] Validar estabilidad en demo
- [ ] Migrar a cuenta real (capital pequeÃ±o)
- [ ] Monitoreo continuo
- [ ] IteraciÃ³n y mejora de prompts
- [ ] ExpansiÃ³n de activos
- [ ] ImplementaciÃ³n de filtros avanzados

---

## APÃ‰NDICES

### A. Glosario Extendido

| TÃ©rmino | DefiniciÃ³n Completa |
|---------|---------------------|
| **Slippage** | Diferencia entre precio esperado y precio de ejecuciÃ³n real |
| **Spread** | Diferencia entre precio bid y ask |
| **Pip** | Point in Percentage, unidad mÃ­nima de movimiento (0.0001 en EURUSD) |
| **Lote** | TamaÃ±o estandarizado de contrato (1 lote = 100,000 unidades) |
| **Equity** | Balance + P/L de operaciones abiertas |
| **Drawdown** | PÃ©rdida desde el pico mÃ¡s alto hasta el valle mÃ¡s bajo |

### B. Referencias

1. **MetaTrader 5 Python API:** https://www.mql5.com/en/docs/python_metatrader5
2. **Gemini API Documentation:** https://ai.google.dev/docs
3. **Technical Analysis Library (ta):** https://github.com/bukosabino/ta
4. **mplfinance:** https://github.com/matplotlib/mplfinance

### C. Contacto y Soporte

**DocumentaciÃ³n:** `docs/` en repositorio  
**Logs:** `logs/` para debugging  
**Issues:** Registrar en sistema de control de versiones

---

## CONCLUSIÃ“N

Este documento establece las bases del **Sistema de Trading Automatizado con IA**, un proyecto modular, escalable y orientado a la comparaciÃ³n de metodologÃ­as de trading mediante inteligencia artificial.

Los **5 bots iniciales** permitirÃ¡n evaluar diferentes enfoques (numÃ©ricos, visuales, hÃ­bridos) y tipos de entrada (Market vs Limit), generando datos valiosos para optimizaciÃ³n continua.

La arquitectura propuesta, basada en **archivos modulares pequeÃ±os**, facilita el mantenimiento y la expansiÃ³n futura del sistema.

**PrÃ³ximos pasos:**
1. Revisar y aprobar este documento
2. Proceder con documentaciÃ³n individual de cada bot
3. Iniciar implementaciÃ³n segÃºn roadmap

---

**Documento generado:** 24 de Octubre, 2025  
**VersiÃ³n:** 1.0 - EspecificaciÃ³n Inicial  
**PrÃ³xima revisiÃ³n:** Post-implementaciÃ³n Fase 1