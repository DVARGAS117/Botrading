## Introducción
Este documento consolida las historias de usuario (tickets) derivadas del análisis del documento principal del proyecto de sistema de trading automatizado con IA.[9]
Cada ticket incluye la historia de usuario completa y al menos un criterio mínimo de aceptación en formato Gherkin, enfocado en validar el cumplimiento esencial de los requisitos funcionales y no funcionales.[9]
Los tickets están agrupados por épicas para mantener la estructura modular y facilitar el seguimiento en un backlog ágil.[9]

## Épica: Orquestación
La plataforma se compone de múltiples bots orquestadores independientes que ejecutan el flujo principal por ciclos, aplican filtros y coordinan los componentes de datos, IA, ejecución y persistencia.[9]
Cada bot corre en ventanas horarias específicas, itera por una lista configurable de activos y decide entre evaluación nueva o reevaluación según existencia de operaciones abiertas por activo y Magic Number.[9]

### Ticket 1: Ejecución de ciclo por bot a inicio de hora
**Historia de Usuario:** Como operador del sistema, quiero que cada bot ejecute su ciclo exactamente al inicio de cada hora, para respetar el modelo operativo de evaluación en ventana 06:00–13:00 Perú.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: El bot ejecuta su ciclo a inicio de hora  
  Dado que la hora local de Lima es HH:00 dentro de 06:00–13:00 en día hábil [attached_file:1]  
  Cuando el bot inicia su ciclo con un ligero retraso para asegurar velas cerradas [attached_file:1]  
  Entonces el ciclo comienza exactamente al inicio de la hora configurada [attached_file:1]  
```

### Ticket 2: Aplicación de filtros de horario y días hábiles
**Historia de Usuario:** Como bot orquestador, quiero aplicar filtros de horario y días hábiles antes de iniciar cualquier evaluación, para evitar operaciones fuera de condiciones permitidas.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Aplicar filtros de horario y días hábiles antes de evaluar  
  Dado que la ejecución verifica día laborable y franja 06:00–13:00 Lima [attached_file:1]  
  Cuando los filtros no se cumplen [attached_file:1]  
  Entonces el bot omite la evaluación y registra el motivo en logs [attached_file:1]  
```

### Ticket 3: Instancias independientes por bot
**Historia de Usuario:** Como operador del sistema, quiero que cada bot sea una instancia independiente ejecutable y monitoreable por separado, para facilitar pruebas A/B y mantenimiento.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Instancias independientes por bot  
  Dado que cada bot se despliega como proceso/servicio independiente [attached_file:1]  
  Cuando se requieren pruebas A/B o reinicios individuales [attached_file:1]  
  Entonces cada bot puede iniciarse, detenerse y monitorearse sin afectar a los otros [attached_file:1]  
```

### Ticket 4: Verificación de operación abierta por activo y Magic Number
**Historia de Usuario:** Como bot orquestador, quiero verificar si existe una operación abierta por activo y Magic Number antes de evaluar una nueva entrada, para forzar la ruta de reevaluación cuando corresponda.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Verificar operación abierta por activo y Magic Number  
  Dado que el bot conoce el símbolo actual y su Magic Number [attached_file:1]  
  Cuando consulta posiciones abiertas en MT5 filtrando por símbolo y Magic Number [attached_file:1]  
  Entonces decide ruta de reevaluación si existe al menos una posición abierta [attached_file:1]  
```

### Ticket 5: Parámetros globales centralizados
**Historia de Usuario:** Como administrador, quiero que los parámetros globales estén centralizados en archivos de configuración, para modificar activos, horarios y credenciales sin tocar código.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Parámetros globales centralizados  
  Dado que existen archivos de configuración JSON para horarios, activos y credenciales [attached_file:1]  
  Cuando se modifica un parámetro en config sin tocar código [attached_file:1]  
  Entonces el bot aplica el nuevo valor en el siguiente ciclo de ejecución [attached_file:1]  
```

## Épica: Integración MT5
El sistema debe conectarse a MT5 para extraer velas cerradas, precios actuales, consultar posiciones, abrir órdenes Market/Limit, modificar SL/TP y cerrar posiciones, respetando especificaciones por activo.[9]
La integración debe ser robusta con reintentos y nunca inyectar datos ficticios en ausencia de respuesta de MT5.[9]

### Ticket 6: Verificación de conexión MT5 al inicio
**Historia de Usuario:** Como bot, quiero inicializar y verificar la conexión a MT5 al inicio del ciclo, para asegurar disponibilidad antes de extraer datos u operar.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Verificar conexión MT5 al inicio  
  Dado que el bot inicia el ciclo [attached_file:1]  
  Cuando valida la conexión a MT5 con reintentos configurados [attached_file:1]  
  Entonces continúa solo si la conexión está disponible, de lo contrario aborta el ciclo [attached_file:1]  
```

### Ticket 7: Extracción de velas cerradas OHLCV por timeframe
**Historia de Usuario:** Como bot, quiero extraer OHLCV de velas cerradas por timeframe requerido, para calcular indicadores de forma consistente y estable.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Extraer velas cerradas OHLCV por timeframe  
  Dado que el bot requiere datos 5M, 15M y 1H de velas cerradas [attached_file:1]  
  Cuando solicita OHLCV a MT5 para los timeframes requeridos [attached_file:1]  
  Entonces recibe datos consistentes de velas cerradas sin usar datos parciales [attached_file:1]  
```

### Ticket 8: Consulta de posiciones por símbolo y Magic Number
**Historia de Usuario:** Como bot, quiero consultar y filtrar posiciones abiertas por símbolo y Magic Number, para determinar si ejecutar reevaluación.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Consultar posiciones por símbolo y Magic Number  
  Dado que existen posiciones abiertas en MT5 [attached_file:1]  
  Cuando el bot filtra por símbolo y Magic Number [attached_file:1]  
  Entonces obtiene únicamente las posiciones relevantes para ese bot y tipo de orden [attached_file:1]  
```

### Ticket 9: Envío de órdenes y gestión de SL/TP/cierre
**Historia de Usuario:** Como bot, quiero enviar órdenes Market y Limit y luego modificar SL/TP o cerrar, para cumplir el ciclo de vida de la operación.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Enviar órdenes y gestionar SL/TP/cierre  
  Dado que la IA indica operar con parámetros válidos [attached_file:1]  
  Cuando el bot envía órdenes Market o Limit y luego modifica SL/TP o cierra según decisión [attached_file:1]  
  Entonces las operaciones quedan reflejadas en MT5 con los parámetros confirmados [attached_file:1]  
```

## Épica: IA (Gemini)
La decisión de operar y la reevaluación se delegan a un agente de IA Gemini con prompts estructurados y respuestas JSON, conservando el contexto conversacional entre reevaluaciones.[9]
Debe registrarse con precisión el consumo de tokens y el costo por consulta para evaluación costo/beneficio por bot y en el tiempo.[9]

### Ticket 10: Construcción de prompt y recepción de JSON de decisión
**Historia de Usuario:** Como orquestador, quiero construir prompts específicos por tipo de bot y enviar a Gemini 2.5 Pro, para recibir decisiones en formato JSON con campos de dirección, SL, TP y riesgo.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Construir prompt y recibir JSON de decisión  
  Dado que el bot prepara payload numérico/visual según su tipo [attached_file:1]  
  Cuando envía el prompt a Gemini 2.5 Pro con parámetros configurados [attached_file:1]  
  Entonces recibe una respuesta JSON válida con dirección, SL, TP y riesgo [attached_file:1]  
```

### Ticket 11: Registro de tokens y costo por consulta
**Historia de Usuario:** Como analista de costos, quiero registrar tokens input/output y costo por cada consulta, para medir la eficiencia económica de cada metodología.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Registrar tokens y costo por consulta  
  Dado que se realiza una consulta a IA [attached_file:1]  
  Cuando el proveedor devuelve uso de tokens input/output y costo [attached_file:1]  
  Entonces se persiste tokens y costo asociados a la operación o reevaluación [attached_file:1]  
```

### Ticket 12: Mantenimiento de contexto de conversación en reevaluación
**Historia de Usuario:** Como bot, quiero mantener el contexto conversacional mediante IDs de conversación, para que la reevaluación considere el historial de la operación.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Mantener contexto de conversación en reevaluación  
  Dado que existe un ID de conversación previo para la operación [attached_file:1]  
  Cuando el bot envía una reevaluación [attached_file:1]  
  Entonces la IA recibe y utiliza el contexto histórico de esa operación [attached_file:1]  
```

### Ticket 13: Parametrización de modelo y tiempo de espera
**Historia de Usuario:** Como operador, quiero parametrizar modelo, temperatura, max tokens y timeout en un JSON, para experimentar sin cambios de código.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Parametrizar modelo y tiempo de espera  
  Dado que el archivo de configuración define modelo, temperatura, max tokens y timeout [attached_file:1]  
  Cuando se actualiza la configuración [attached_file:1]  
  Entonces la siguiente llamada a IA usa los nuevos parámetros [attached_file:1]  
```

## Épica: Dual Market/Limit
Siempre que la IA decide operar, el bot abre dos operaciones simultáneas, una Market y otra Limit, para comparar rendimientos y tasas de activación.[9]
Se requiere gestión diferenciada de Magic Numbers, registro y reevaluación independiente de cada operación del par.[9]

### Ticket 14: Apertura simultánea de órdenes Market y Limit
**Historia de Usuario:** Como operador, quiero que se abran dos órdenes (Market y Limit) con los mismos parámetros de SL/TP y riesgo cuando la IA decide OPERAR, para medir desempeño comparado.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Abrir órdenes Market y Limit simultáneamente  
  Dado que la IA decide OPERAR con parámetros válidos [attached_file:1]  
  Cuando el bot ejecuta la apertura [attached_file:1]  
  Entonces se crean dos órdenes: una Market y una Limit con mismos SL/TP y riesgo [attached_file:1]  
```

### Ticket 15: Registro y comparación de desempeño Market vs Limit
**Historia de Usuario:** Como analista, quiero registrar y comparar P/L de Market vs Limit y su tasa de activación, para extraer conclusiones de efectividad por bot y activo.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Registrar y comparar desempeño Market vs Limit  
  Dado que existen resultados P/L para ambos tipos de orden [attached_file:1]  
  Cuando se consolidan métricas por operación y por día [attached_file:1]  
  Entonces queda disponible la comparación de P/L y activación entre Market y Limit [attached_file:1]  
```

### Ticket 16: Reevaluación independiente de Market y Limit
**Historia de Usuario:** Como bot, quiero reevaluar Market y Limit de forma independiente, para permitir decisiones divergentes en cada una según condiciones actuales.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Reevaluación independiente de Market y Limit  
  Dado que hay un par Market y Limit abiertos [attached_file:1]  
  Cuando el bot solicita reevaluación para cada uno [attached_file:1]  
  Entonces puede mantener, actualizar o cerrar cada orden de manera independiente [attached_file:1]  
```

## Épica: Magic Numbers
El sistema identifica operaciones con un Magic Number de seis dígitos que codifica Bot, IA y Tipo de orden, habilitando trazabilidad y consultas eficientes.[9]
La codificación debe permitir escalar a múltiples bots y IAs conservando unicidad y semántica.[9]

### Ticket 17: Generación de Magic Number único con estructura
**Historia de Usuario:** Como sistema, quiero generar Magic Numbers únicos con estructura [Bot][IA][Tipo], para identificar inequívocamente cada operación.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Generar Magic Number único con estructura [Bot][IA][Tipo]  
  Dado que el bot conoce sus IDs de bot, IA y tipo de orden [attached_file:1]  
  Cuando necesita identificar una operación [attached_file:1]  
  Entonces genera un Magic Number de seis dígitos único y decodificable [attached_file:1]  
```

### Ticket 18: Decodificación de Magic Number para auditoría
**Historia de Usuario:** Como operador, quiero decodificar Magic Numbers para auditar origen y tipo de operación, para análisis y soporte.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Decodificar Magic Number para auditoría  
  Dado que existe un Magic Number registrado [attached_file:1]  
  Cuando un operador lo consulta [attached_file:1]  
  Entonces puede obtener bot, IA y tipo de orden a partir del número [attached_file:1]  
```

### Ticket 19: Filtrado de posiciones por Magic Number en MT5
**Historia de Usuario:** Como bot, quiero filtrar y consultar posiciones por Magic Number en MT5, para operar y reevaluar con precisión.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Filtrar posiciones por Magic Number en MT5  
  Dado que hay múltiples operaciones abiertas [attached_file:1]  
  Cuando se filtra por Magic Number [attached_file:1]  
  Entonces se listan solo las posiciones del bot y tipo correctos [attached_file:1]  
```

## Épica: Multi-activo
Cada bot itera sobre una lista configurable de activos, limitando a una operación por activo y evento, pero permitiendo operaciones simultáneas en diferentes símbolos.[9]
La configuración de activos debe residir en un archivo JSON y validarse en tiempo de ejecución.[9]

### Ticket 20: Administración de lista de activos en configuración
**Historia de Usuario:** Como administrador, quiero administrar la lista de activos en config/assets.json, para habilitar o deshabilitar símbolos sin despliegue.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Administrar lista de activos en configuración  
  Dado que existe config/assets.json con símbolos habilitados [attached_file:1]  
  Cuando se agrega o deshabilita un símbolo [attached_file:1]  
  Entonces el bot itera únicamente los activos habilitados en el siguiente ciclo [attached_file:1]  
```

### Ticket 21: Garantía de una sola operación por activo y evento
**Historia de Usuario:** Como bot, quiero garantizar una sola operación por activo por evento (market/limit), para evitar duplicidades y violaciones de la regla operacional.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Asegurar una sola operación por activo y evento  
  Dado que el bot evalúa un símbolo [attached_file:1]  
  Cuando detecta una operación abierta para ese símbolo y evento (market/limit) [attached_file:1]  
  Entonces bloquea nuevas entradas para ese símbolo y evento hasta cierre [attached_file:1]  
```

### Ticket 22: Iteración determinista de activos
**Historia de Usuario:** Como operador, quiero iterar activos de forma determinista en cada ciclo, para asegurar cobertura y consistencia en la evaluación.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Iteración determinista de activos  
  Dado que la lista de activos está ordenada en configuración [attached_file:1]  
  Cuando el bot inicia un ciclo [attached_file:1]  
  Entonces procesa los activos en el mismo orden determinista [attached_file:1]  
```

## Épica: Indicadores e imágenes
Los bots numéricos calculan EMA 20/50, RSI, MACD y volumen en 5M, 15M y 1H, y los bots visuales generan imágenes por timeframe con o sin indicadores, según el tipo de bot.[9]
El formato de datos a IA debe ser consistente, ya sea JSON numérico o imágenes compatibles con Gemini.[9]

### Ticket 23: Cálculo y formato de indicadores por timeframe
**Historia de Usuario:** Como bot numérico, quiero calcular y formatear indicadores por los tres timeframes, para enviar un payload consistente a IA.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Calcular indicadores por timeframe  
  Dado que existen velas cerradas 5M, 15M y 1H [attached_file:1]  
  Cuando el bot numérico calcula EMA 20/50, RSI, MACD y volumen [attached_file:1]  
  Entonces construye un JSON consistente para la IA por cada timeframe [attached_file:1]  
```

### Ticket 24: Generación de imágenes por timeframe con estilos consistentes
**Historia de Usuario:** Como bot visual, quiero generar imágenes por timeframe con estilos consistentes y, según el bot, con indicadores superpuestos o separados, para habilitar análisis visual por IA.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Generar imágenes por timeframe con estilos consistentes  
  Dado que el bot visual tiene configurado estilo con/sin indicadores [attached_file:1]  
  Cuando genera imágenes de 5M, 15M y 1H [attached_file:1]  
  Entonces produce archivos compatibles con Gemini con el estilo definido [attached_file:1]  
```

### Ticket 25: Alternancia entre entradas numéricas, visuales o híbridas
**Historia de Usuario:** Como orquestador, quiero alternar entre entradas numéricas, visuales o híbridas según el bot, para comparar metodologías de señal.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Alternar entradas numéricas, visuales o híbridas  
  Dado que el tipo de bot está definido en configuración [attached_file:1]  
  Cuando el orquestador prepara el payload [attached_file:1]  
  Entonces envía a IA datos numéricos, imágenes o ambos según el bot [attached_file:1]  
```

## Épica: Reevaluación
Cuando hay operaciones abiertas, se ejecuta un ciclo de reevaluación cada 10 minutos con datos e indicadores actualizados, manteniendo el contexto de la conversación de IA.[9]
La decisión puede ser mantener, actualizar SL/TP o cerrar, y todo debe registrarse con tokens y costos acumulados.[9]

### Ticket 26: Reevaluación cada 10 minutos con datos actualizados
**Historia de Usuario:** Como bot, quiero reevaluar operaciones abiertas cada 10 minutos con velas cerradas e indicadores actuales, para reaccionar a cambios de mercado.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Reevaluar cada 10 minutos con datos actualizados  
  Dado que existe una posición abierta [attached_file:1]  
  Cuando se cumple el intervalo de 10 minutos desde la última reevaluación [attached_file:1]  
  Entonces el bot envía nueva evaluación con velas cerradas e indicadores actuales [attached_file:1]  
```

### Ticket 27: Aplicación de decisión de actualizar SL/TP o cerrar
**Historia de Usuario:** Como bot, quiero aplicar la decisión de IA de actualizar SL/TP o cerrar posiciones, para gestionar activamente el riesgo y el resultado.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Aplicar decisión de actualizar SL/TP o cerrar  
  Dado que la IA devuelve una decisión de gestión [attached_file:1]  
  Cuando la decisión es actualizar SL/TP o cerrar [attached_file:1]  
  Entonces el bot ejecuta la acción en MT5 y registra el resultado [attached_file:1]  
```

### Ticket 28: Registro de trazabilidad de cada reevaluación
**Historia de Usuario:** Como auditor, quiero registrar cada reevaluación con decisión, tokens y costos asociados, para mantener trazabilidad completa.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Registrar trazabilidad de cada reevaluación  
  Dado que se realizó una reevaluación [attached_file:1]  
  Cuando se persisten decisión, tokens y costos [attached_file:1]  
  Entonces la operación queda con historial completo de reevaluaciones [attached_file:1]  
```

## Épica: Riesgo y conversión de activos
El tamaño de lote debe calcularse por porcentaje de riesgo considerando la distancia al SL y las especificaciones del activo provenientes de MT5.[9]
La conversión debe contemplar dígitos, valor por tick, tamaño de contrato y límites de volumen por símbolo.[9]

### Ticket 29: Cálculo de lote por % riesgo y distancia al SL
**Historia de Usuario:** Como gestor de riesgo, quiero calcular el lote en función del % de riesgo, distancia al SL y valor por tick, para normalizar el riesgo entre activos heterogéneos.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Calcular lote por % riesgo y distancia al SL  
  Dado que se conoce el % de riesgo, precio de entrada, SL y valor por tick [attached_file:1]  
  Cuando se calcula el tamaño de la posición [attached_file:1]  
  Entonces el lote resultante normaliza el riesgo entre activos heterogéneos [attached_file:1]  
```

### Ticket 30: Ajuste de lote a step y límites del símbolo
**Historia de Usuario:** Como bot, quiero ajustar el lote al step permitido y a los mínimos y máximos de MT5, para cumplir restricciones del símbolo.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Ajustar lote a step y límites del símbolo  
  Dado que MT5 expone step, mínimos y máximos de volumen [attached_file:1]  
  Cuando el cálculo de lote excede límites o no respeta el step [attached_file:1]  
  Entonces el lote se ajusta al valor permitido más cercano [attached_file:1]  
```

### Ticket 31: Obtención de especificaciones del símbolo desde MT5
**Historia de Usuario:** Como desarrollador, quiero obtener especificaciones del activo desde MT5 antes del cálculo, para evitar supuestos incorrectos.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Obtener especificaciones del símbolo desde MT5  
  Dado que se va a calcular el lote [attached_file:1]  
  Cuando se consultan dígitos, valor por tick y tamaño de contrato en MT5 [attached_file:1]  
  Entonces el cálculo usa datos reales del símbolo sin supuestos [attached_file:1]  
```

## Épica: Persistencia y trazabilidad
Se debe usar SQLite para registrar operaciones, consultas a IA, tokens, costos y métricas diarias, además de índices para consultas eficientes.[9]
El sistema debe almacenar precio sugerido vs real en Market, conversación de IA y tiempos de apertura y cierre.[9]

### Ticket 32: Persistencia de operaciones con parámetros y estados
**Historia de Usuario:** Como auditor, quiero almacenar en la tabla operaciones todos los parámetros de la orden, estados y resultados, para análisis posterior y cumplimiento.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Persistir operaciones con parámetros y estados  
  Dado que se abre o modifica una operación [attached_file:1]  
  Cuando se registra en SQLite con índices definidos [attached_file:1]  
  Entonces quedan almacenados parámetros, estados, tiempos y resultados [attached_file:1]  
```

### Ticket 33: Registro de consultas a IA con prompts, respuesta, tokens y costo
**Historia de Usuario:** Como analista, quiero registrar consultas a IA con prompt, respuesta, tokens y costo, para evaluar eficiencia y calidad de decisión.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Registrar consultas a IA con prompts, respuesta, tokens y costo  
  Dado que se envía una consulta a IA [attached_file:1]  
  Cuando se recibe la respuesta [attached_file:1]  
  Entonces se guarda prompt, respuesta, tokens, costo y referencias a la operación [attached_file:1]  
```

### Ticket 34: Consolidación de métricas diarias por bot
**Historia de Usuario:** Como operador, quiero consolidar métricas diarias por bot (winrate, profit factor, costos IA), para revisar desempeño agregado.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Consolidar métricas diarias por bot  
  Dado que existen operaciones y consultas registradas en el día [attached_file:1]  
  Cuando se ejecuta el consolidado diario [attached_file:1]  
  Entonces se calculan winrate, profit factor, P/L por tipo de orden y costo IA [attached_file:1]  
```

## Épica: Filtros y horarios
El único filtro obligatorio inicial es el horario y días hábiles, con posibilidad futura de agregar volatilidad, spread, eventos y límites por drawdown mediante configuración.[9]
La validación debe considerar huso horario de Lima y ejecución exacta en HH:00 con ligero retraso para asegurar velas cerradas.[9]

### Ticket 35: Validación de hora local de Lima y días hábiles
**Historia de Usuario:** Como operador, quiero validar hora local de Lima y días hábiles antes de operar, para alinear el sistema al horario de trabajo definido.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Validar hora local de Lima y días hábiles  
  Dado que el sistema conoce el timezone America/Lima [attached_file:1]  
  Cuando la fecha u hora no cumplen las reglas [attached_file:1]  
  Entonces el bot no evalúa ni opera y registra la causa [attached_file:1]  
```

### Ticket 36: Activación de filtros futuros vía configuración
**Historia de Usuario:** Como administrador, quiero activar futuros filtros de volatilidad y spread vía config/filters.json, para evolucionar la gobernanza de señales.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Activar filtros futuros vía configuración  
  Dado que existe config/filters.json [attached_file:1]  
  Cuando se habilita un filtro de volatilidad o spread [attached_file:1]  
  Entonces el bot aplica el filtro sin cambiar el código fuente [attached_file:1]  
```

### Ticket 37: Espera por cierre de vela antes de extraer datos
**Historia de Usuario:** Como bot, quiero esperar el cierre de vela y un pequeño delay antes de extraer datos, para evitar inconsistencias en indicadores.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Esperar cierre de vela antes de extraer datos  
  Dado que está por cerrar la vela del timeframe objetivo [attached_file:1]  
  Cuando se aplica un pequeño delay configurado tras el cierre [attached_file:1]  
  Entonces los indicadores se calculan únicamente con velas cerradas [attached_file:1]  
```

## Épica: Errores y logging
El sistema debe reintentar hasta tres veces fallos de MT5 y API de IA, registrar errores y nunca simular datos, dejando la evaluación para el siguiente ciclo si falla.[9]
El logging estructurado por bot y nivel debe facilitar diagnósticos en tiempo de ejecución y post mortem.[9]

### Ticket 38: Reintentos automáticos con backoff
**Historia de Usuario:** Como operador, quiero reintentos automáticos con backoff ante fallos de MT5 o IA, para mejorar resiliencia sin intervención manual.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Reintentos automáticos con backoff  
  Dado que una llamada a MT5 o IA falla temporalmente [attached_file:1]  
  Cuando el bot aplica hasta tres reintentos con backoff [attached_file:1]  
  Entonces la operación continúa si el reintento tiene éxito o se aborta con registro si no [attached_file:1]  
```

### Ticket 39: Logging por bot y nivel
**Historia de Usuario:** Como desarrollador, quiero logs por bot con niveles info, warning y error, para depurar y trazar problemas rápidamente.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Logging por bot y nivel  
  Dado que el sistema emite logs estructurados [attached_file:1]  
  Cuando ocurre un evento info, warning o error [attached_file:1]  
  Entonces el log incluye bot, nivel, timestamp y mensaje para diagnóstico [attached_file:1]  
```

### Ticket 40: Registro de errores de parsing de IA
**Historia de Usuario:** Como auditor, quiero registrar errores de parsing de respuestas IA y su impacto, para mejorar robustez del parser.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Registrar errores de parsing de IA  
  Dado que se recibe una respuesta IA no parseable [attached_file:1]  
  Cuando el parser detecta el error [attached_file:1]  
  Entonces se registra el incidente y se omite la acción hasta el siguiente ciclo [attached_file:1]  
```

## Épica: Métricas y monitoreo
Las métricas diarias por bot deben resumir operaciones, resultados y costos de IA para análisis comparativo de metodologías y tipos de entrada.[9]
Se plantea mejorar dashboards y monitoreo en fases posteriores del roadmap.[9]

### Ticket 41: Disponibilización de métricas diarias por bot
**Historia de Usuario:** Como analista, quiero disponer de winrate, profit factor, P/L por tipo de orden y costo IA total por día y bot, para evaluar efectividad y eficiencia.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Disponibilizar métricas diarias por bot  
  Dado que se generaron métricas del día [attached_file:1]  
  Cuando un analista consulta el resumen [attached_file:1]  
  Entonces visualiza winrate, profit factor, P/L por tipo y costo IA total [attached_file:1]  
```

### Ticket 42: Comparación de desempeño entre metodologías
**Historia de Usuario:** Como PM, quiero comparar desempeño entre bots numéricos, visuales e híbridos, para decidir continuidad o ajustes de prompts y señales.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Comparar desempeño entre metodologías  
  Dado que existen métricas para bots numéricos, visuales e híbridos [attached_file:1]  
  Cuando se consulta el comparativo [attached_file:1]  
  Entonces se muestran indicadores clave por bot para decisiones de continuidad [attached_file:1]  
```

### Ticket 43: Monitoreo de estado y logs de cada bot
**Historia de Usuario:** Como operador, quiero monitorear logs y estado de cada bot, para detectar caídas o anomalías operativas.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Monitorear estado y logs de cada bot  
  Dado que cada bot emite health y logs [attached_file:1]  
  Cuando el operador revisa el estado [attached_file:1]  
  Entonces puede detectar caídas o anomalías operativas oportunamente [attached_file:1]  
```

## Épica: Configuración y modularidad
El código debe ser modular con responsabilidades pequeñas por archivo, reutilización de core y configuración externa en JSON para evitar hardcoding.[9]
La separación por bot en directorios propios permite experimentación y pruebas específicas por metodología.[9]

### Ticket 44: Gestión de credenciales y parámetros en JSON
**Historia de Usuario:** Como administrador, quiero gestionar credenciales, modelos y parámetros en config/*.json, para cambiar proveedores o ajustes sin redeploy de código.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Gestionar credenciales y parámetros en JSON  
  Dado que existen archivos config/*.json para credenciales y parámetros [attached_file:1]  
  Cuando se actualiza una credencial o parámetro [attached_file:1]  
  Entonces el sistema usa el nuevo valor sin redeploy [attached_file:1]  
```

### Ticket 45: Reutilización de módulos core
**Historia de Usuario:** Como desarrollador, quiero que los módulos core sean reutilizables por todos los bots, para acelerar implementación y reducir duplicación.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Reutilización de módulos core  
  Dado que los bots comparten módulos de core [attached_file:1]  
  Cuando un nuevo bot requiere funcionalidad común [attached_file:1]  
  Entonces puede integrarla sin duplicar código [attached_file:1]  
```

### Ticket 46: Tests unitarios por componente
**Historia de Usuario:** Como QA, quiero tests unitarios por componente y estructura de tests dedicada, para validar calidad de forma aislada.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Tests unitarios por componente  
  Dado que existe una estructura de tests dedicada [attached_file:1]  
  Cuando se ejecutan los tests [attached_file:1]  
  Entonces se validan comportamientos aislados de cada módulo [attached_file:1]  
```

## Épica: Seguridad y cuentas/APIs
El sistema requiere cuentas MT5 y claves de API activas con facturación y cuota suficiente, administradas de forma segura.[9]
La selección de modelo y cuotas impacta costos y disponibilidad, por lo que deben ser configurables.[9]

### Ticket 47: Almacenamiento seguro de credenciales
**Historia de Usuario:** Como administrador, quiero almacenar de forma segura las credenciales de MT5 y API Key de Gemini, para operar sin exponer secretos en código.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Almacenamiento seguro de credenciales  
  Dado que el sistema necesita claves de MT5 y Gemini [attached_file:1]  
  Cuando se configuran secretos en archivos seguros o variables de entorno [attached_file:1]  
  Entonces las credenciales no quedan expuestas en el código [attached_file:1]  
```

### Ticket 48: Validación de cuota y disponibilidad de modelo IA
**Historia de Usuario:** Como operador, quiero validar cuota y disponibilidad del modelo antes de iniciar ciclos, para evitar fallos por límites de uso.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Validar cuota y disponibilidad de modelo IA  
  Dado que se va a iniciar un ciclo que usa IA [attached_file:1]  
  Cuando se consulta cuota y estado del modelo [attached_file:1]  
  Entonces el bot procede solo si hay capacidad, de lo contrario espera o aborta [attached_file:1]  
```

### Ticket 49: Alternancia de configuraciones de IA por bot
**Historia de Usuario:** Como PM, quiero poder alternar entre configuraciones de IA por bot, para medir impacto en costo y calidad.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Alternar configuraciones de IA por bot  
  Dado que cada bot puede usar configuración de IA distinta [attached_file:1]  
  Cuando el PM cambia el perfil de IA para un bot [attached_file:1]  
  Entonces el bot aplica el cambio en su siguiente ciclo [attached_file:1]  
```

## Épica: Roadmap y calidad
La implementación se estructura en fases con entregables claros: fundamentos, indicadores/IA, Bot 1, Bots 2–5, refinamiento, demo y producción.[9]
La documentación por bot y guías de uso deben acompañar despliegues para facilitar operación y revisión.[9]

### Ticket 50: Avance por fases con criterios de salida
**Historia de Usuario:** Como PM, quiero avanzar por fases con criterios de salida definidos por entregable, para gestionar riesgo y asegurar integraciones incrementales.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Avanzar por fases con criterios de salida  
  Dado que el roadmap define fases y entregables [attached_file:1]  
  Cuando un entregable cumple sus criterios [attached_file:1]  
  Entonces la fase se da por completada y se inicia la siguiente [attached_file:1]  
```

### Ticket 51: Pruebas de integración E2E por bot
**Historia de Usuario:** Como QA, quiero pruebas de integración del Bot 1 y luego de cada bot adicional, para validar extremo a extremo antes de pasar a demo.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Pruebas de integración E2E por bot  
  Dado que Bot 1 está implementado [attached_file:1]  
  Cuando se ejecutan pruebas de integración extremo a extremo [attached_file:1]  
  Entonces se valida la cadena datos→IA→ejecución→persistencia antes de avanzar [attached_file:1]  
```

### Ticket 52: Operación en demo antes de real
**Historia de Usuario:** Como operador, quiero ejecutar en demo, monitorear, ajustar prompts y parámetros y solo luego migrar a real, para minimizar riesgo financiero.[9]

**Criterios Mínimos de Aceptación:**  
```gherkin  
Escenario: Operar en demo antes de real  
  Dado que existe entorno de demo y de real [attached_file:1]  
  Cuando el operador valida desempeño y ajusta prompts/parámetros en demo [attached_file:1]  
  Entonces recién se migra a real para minimizar riesgo financiero [attached_file:1]  
```