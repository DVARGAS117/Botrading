````markdown
# Documentación: Módulo retry_handler

**Ticket:** T38 - Reintentos automáticos con backoff  
**Fase:** 1 - Núcleo  
**Prioridad:** P0  
**Fecha:** 2025-11-06  
**Desarrollador:** Sistema Botrading  

---

## 📋 Resumen

El módulo `retry_handler.py` implementa un sistema de reintentos automáticos con backoff exponencial para operaciones que pueden fallar temporalmente. Especialmente diseñado para llamadas a MT5 y APIs de IA (Gemini), mejora la resiliencia del sistema sin intervención manual.

---

## 🎯 Objetivos del Ticket T38

### Historia de Usuario
> Como operador, quiero reintentos automáticos con backoff ante fallos de MT5 o IA, para mejorar resiliencia sin intervención manual.

### Criterios de Aceptación ✅

**Escenario:** Reintentos automáticos con backoff
- ✅ **Dado que** una llamada a MT5 o IA falla temporalmente
- ✅ **Cuando** el bot aplica hasta tres reintentos con backoff
- ✅ **Entonces** la operación continúa si el reintento tiene éxito o se aborta con registro si no

---

## 🏗️ Arquitectura

### Componentes Principales

```
retry_handler.py
├── RetryConfig (Class)           # Configuración de reintentos
├── RetryHandler (Class)          # Handler principal
├── RetryConfigError (Exception)  # Error de configuración
├── RetryExhaustedError (Exception) # Reintentos agotados
├── with_retry() (Decorator)      # Decorador para funciones
├── MT5_RETRY_CONFIG             # Config predefinida MT5
├── IA_RETRY_CONFIG              # Config predefinida IA
├── NETWORK_RETRY_CONFIG         # Config predefinida red
├── retry_mt5_operation()        # Helper MT5
└── retry_ia_query()             # Helper IA
```

---

## 🔧 Funcionalidades Implementadas

### 1. Configuración de Reintentos

```python
from src.core.retry_handler import RetryConfig

# Configuración personalizada
config = RetryConfig(
    max_attempts=3,        # Número máximo de intentos
    initial_delay=1.0,     # Delay inicial en segundos
    max_delay=30.0,        # Delay máximo en segundos
    backoff_factor=2.0,    # Factor multiplicador
    exponential_base=2,    # Base exponencial
    jitter=True,           # Agregar jitter aleatorio
    retry_on=(ConnectionError, TimeoutError)  # Excepciones a reintentar
)
```

### 2. Handler de Reintentos

```python
from src.core.retry_handler import RetryHandler, RetryConfig

# Crear handler
config = RetryConfig(max_attempts=3)
handler = RetryHandler(config)

# Ejecutar función con reintentos
def connect_mt5():
    # Código que puede fallar
    return mt5.connect()

result = handler.execute(connect_mt5)
```

### 3. Decorador @with_retry

```python
from src.core.retry_handler import with_retry, RetryConfig

# Usar como decorador
@with_retry(RetryConfig(max_attempts=3, initial_delay=1.0))
def query_gemini(prompt):
    # Código que puede fallar
    return gemini_api.query(prompt)

# Uso normal
response = query_gemini("Analyze EURUSD")
```

### 4. Configuraciones Predefinidas

```python
from src.core.retry_handler import (
    MT5_RETRY_CONFIG,
    IA_RETRY_CONFIG,
    NETWORK_RETRY_CONFIG
)

# Para operaciones MT5
handler_mt5 = RetryHandler(MT5_RETRY_CONFIG)

# Para consultas IA
handler_ia = RetryHandler(IA_RETRY_CONFIG)

# Para operaciones de red genéricas
handler_network = RetryHandler(NETWORK_RETRY_CONFIG)
```

**MT5_RETRY_CONFIG:**
- max_attempts: 3
- initial_delay: 1.0s
- max_delay: 10.0s
- retry_on: ConnectionError, TimeoutError, OSError

**IA_RETRY_CONFIG:**
- max_attempts: 3
- initial_delay: 2.0s
- max_delay: 30.0s
- retry_on: ConnectionError, TimeoutError

**NETWORK_RETRY_CONFIG:**
- max_attempts: 5
- initial_delay: 1.0s
- max_delay: 60.0s
- jitter: True

### 5. Funciones Helper

```python
from src.core.retry_handler import retry_mt5_operation, retry_ia_query

# Para MT5
result = retry_mt5_operation(mt5.connect, server="broker-demo")

# Para IA
response = retry_ia_query(gemini.query, prompt="Analyze market")
```

### 6. Backoff Exponencial

El delay entre reintentos crece exponencialmente:

```
Intento 1: Sin delay (intento inicial)
Intento 2: initial_delay = 1.0s
Intento 3: 1.0 × 2.0 = 2.0s
Intento 4: 2.0 × 2.0 = 4.0s
...
```

Con **jitter** (±25%):
- Previene "thundering herd problem"
- Distribuye carga en servicios externos
- Más robusto en escenarios de alta concurrencia

### 7. Manejo de Excepciones

```python
from src.core.retry_handler import (
    RetryHandler, 
    RetryConfig,
    RetryExhaustedError
)

config = RetryConfig(max_attempts=3)
handler = RetryHandler(config)

try:
    result = handler.execute(risky_operation)
except RetryExhaustedError as e:
    # Acceder a información detallada
    print(f"Intentos realizados: {e.attempts}")
    print(f"Última excepción: {e.last_exception}")
    
    # Obtener historial de intentos
    attempts = handler.get_last_attempts()
    for attempt in attempts:
        print(f"Intento {attempt['attempt_number']}: "
              f"{'Éxito' if attempt['success'] else 'Fallo'}")
```

### 8. Integración con Logger

```python
from src.core.logger import get_bot_logger, LogConfig
from src.core.retry_handler import RetryHandler, RetryConfig

# Crear logger
logger = get_bot_logger("bot_1", LogConfig())

# Crear handler
config = RetryConfig(max_attempts=3)
handler = RetryHandler(config)

# Ejecutar con logging automático
result = handler.execute(
    risky_operation,
    logger=logger  # Pasa el logger
)

# Logs automáticos:
# [WARNING] Intento 1 falló, reintentando en 1.00s
# [INFO] Operación exitosa después de 2 intentos
```

### 9. Context Manager

```python
from src.core.retry_handler import RetryHandler, RetryConfig

config = RetryConfig(max_attempts=3)

with RetryHandler(config) as handler:
    result = handler.execute(operation)
    # Cleanup automático al salir
```

---

## 📊 Tests y Cobertura

### Resultados de Tests

```
✅ 34/34 tests pasados (100%)
✅ 95% de cobertura de código
✅ 6.13s tiempo de ejecución
✅ Todos los criterios de aceptación verificados
```

### Tests Implementados

#### **Configuración (5 tests)**
1. test_default_config_values
2. test_custom_config_values
3. test_config_validation_max_attempts
4. test_config_validation_delays
5. test_config_validation_backoff_factor

#### **Reintentos Exitosos (4 tests)**
6. test_retry_succeeds_on_first_attempt
7. test_retry_succeeds_on_second_attempt
8. test_retry_succeeds_on_last_attempt
9. test_retry_with_args_and_kwargs

#### **Reintentos Agotados (3 tests)**
10. test_retry_exhausted_raises_exception
11. test_retry_exhausted_includes_original_exception
12. test_retry_exhausted_logs_all_attempts

#### **Backoff Exponencial (3 tests)**
13. test_backoff_delay_increases_exponentially
14. test_backoff_respects_max_delay
15. test_backoff_with_jitter_adds_randomness

#### **Excepciones Específicas (2 tests)**
16. test_retry_only_on_specified_exceptions
17. test_no_retry_on_non_specified_exceptions

#### **Decorador (3 tests)**
18. test_decorator_basic_usage
19. test_decorator_with_default_config
20. test_decorator_preserves_function_metadata

#### **Registro de Intentos (3 tests)**
21. test_records_all_attempts
22. test_attempt_includes_exception_info
23. test_successful_attempt_marked_correctly

#### **Integración (3 tests)**
24. test_integration_with_logger
25. test_mt5_connection_retry_scenario
26. test_ia_api_retry_scenario

#### **Casos Extremos (3 tests)**
27. test_zero_delay_between_retries
28. test_very_high_max_attempts
29. test_function_with_no_return_value

#### **Context Manager (2 tests)**
30. test_retry_handler_as_context_manager
31. test_context_manager_cleanup

#### **Criterios de Aceptación (3 tests)**
32. test_acceptance_temporary_failure_then_success
33. test_acceptance_all_retries_exhausted
34. test_acceptance_backoff_applied

---

## 📖 Ejemplos de Uso

### Caso de Uso 1: Conexión MT5

```python
from src.core.retry_handler import retry_mt5_operation
from src.core.logger import get_bot_logger
import MetaTrader5 as mt5

logger = get_bot_logger("bot_1")

# Conectar con reintentos automáticos
try:
    result = retry_mt5_operation(
        mt5.initialize,
        login=12345678,
        password="password",
        server="Broker-Demo"
    )
    
    if result:
        logger.info("Conexión MT5 exitosa")
    else:
        logger.error("Fallo al conectar MT5")
        
except RetryExhaustedError as e:
    logger.error(f"Agotados reintentos MT5: {e}")
```

### Caso de Uso 2: Consulta a Gemini

```python
from src.core.retry_handler import with_retry, IA_RETRY_CONFIG
from src.core.logger import get_bot_logger

logger = get_bot_logger("bot_1")

@with_retry(IA_RETRY_CONFIG)
def query_gemini(prompt, context):
    # Llamada a API que puede fallar
    response = gemini_api.generate_content(
        prompt=prompt,
        context=context
    )
    return response.text

# Uso
try:
    decision = query_gemini(
        prompt="Should I buy EURUSD?",
        context={"price": 1.1234, "trend": "upward"}
    )
    logger.info(f"Decisión IA: {decision}")
    
except RetryExhaustedError as e:
    logger.error(f"Gemini no disponible: {e}")
    # Fallback: decisión conservadora
    decision = "HOLD"
```

### Caso de Uso 3: Operaciones MT5 con Contexto

```python
from src.core.retry_handler import RetryHandler, MT5_RETRY_CONFIG
from src.core.logger import get_bot_logger
import MetaTrader5 as mt5

logger = get_bot_logger("bot_1")
handler = RetryHandler(MT5_RETRY_CONFIG)

def open_trade(symbol, order_type, volume, sl, tp):
    """Abre una operación en MT5"""
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "sl": sl,
        "tp": tp,
        "magic": 123456,
        "comment": "Bot trading"
    }
    
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise ConnectionError(f"MT5 error: {result.retcode}")
    
    return result

# Ejecutar con reintentos
try:
    result = handler.execute(
        open_trade,
        symbol="EURUSD",
        order_type=mt5.ORDER_TYPE_BUY,
        volume=0.1,
        sl=1.1200,
        tp=1.1300,
        logger=logger
    )
    
    logger.info(f"Trade abierto: {result.order}")
    
except RetryExhaustedError as e:
    logger.error(f"No se pudo abrir trade después de {e.attempts} intentos")
    # Registrar en base de datos para análisis
    db.log_failed_trade(symbol="EURUSD", error=str(e))
```

### Caso de Uso 4: Reintentos con Excepciones Específicas

```python
from src.core.retry_handler import RetryConfig, RetryHandler

# Solo reintentar para errores de red, no de validación
config = RetryConfig(
    max_attempts=5,
    initial_delay=1.0,
    retry_on=(ConnectionError, TimeoutError)  # NO ValueError
)

handler = RetryHandler(config)

def validate_and_execute(data):
    # Validar (no debe reintentar si falla)
    if not data.get("symbol"):
        raise ValueError("Symbol is required")
    
    # Ejecutar (debe reintentar si falla)
    result = external_api.call(data)
    return result

try:
    result = handler.execute(validate_and_execute, {"symbol": "EURUSD"})
except ValueError as e:
    # Error de validación, no se reintentó
    print(f"Validation error: {e}")
except RetryExhaustedError as e:
    # Error de red persistente después de reintentos
    print(f"Network error persists: {e}")
```

### Caso de Uso 5: Análisis de Intentos Fallidos

```python
from src.core.retry_handler import RetryHandler, RetryConfig, RetryExhaustedError

config = RetryConfig(max_attempts=3)
handler = RetryHandler(config)

try:
    result = handler.execute(unreliable_operation)
except RetryExhaustedError as e:
    # Analizar todos los intentos
    attempts = handler.get_last_attempts()
    
    print(f"Total intentos: {len(attempts)}")
    
    for attempt in attempts:
        print(f"\nIntento #{attempt['attempt_number']}")
        print(f"  Timestamp: {attempt['timestamp']}")
        print(f"  Éxito: {attempt['success']}")
        
        if not attempt['success']:
            print(f"  Excepción: {attempt['exception_type']}")
            print(f"  Mensaje: {attempt['exception_message']}")
    
    # Determinar si es problema sistemático
    error_types = [a['exception_type'] for a in attempts if not a['success']]
    if all(e == "ConnectionError" for e in error_types):
        print("Problema de conectividad persistente")
        # Alertar administrador
    else:
        print("Errores variados, posible problema transitorio")
```

---

## 🎓 Mejores Prácticas

### ✅ DO (Hacer)

1. **Usar configuraciones predefinidas para casos comunes:**
```python
# ✅ Correcto
from src.core.retry_handler import MT5_RETRY_CONFIG, RetryHandler
handler = RetryHandler(MT5_RETRY_CONFIG)
```

2. **Especificar excepciones a reintentar:**
```python
# ✅ Correcto - Solo reintentar errores de red
config = RetryConfig(
    max_attempts=3,
    retry_on=(ConnectionError, TimeoutError)
)
```

3. **Integrar con sistema de logging:**
```python
# ✅ Correcto
result = handler.execute(operation, logger=logger)
```

4. **Usar decorador para funciones que siempre deben reintentar:**
```python
# ✅ Correcto
@with_retry(MT5_RETRY_CONFIG)
def connect_mt5():
    return mt5.initialize()
```

5. **Manejar RetryExhaustedError apropiadamente:**
```python
# ✅ Correcto
try:
    result = handler.execute(operation)
except RetryExhaustedError as e:
    logger.error(f"Operation failed after {e.attempts} attempts")
    # Implementar fallback
```

### ❌ DON'T (No Hacer)

1. **No usar reintentos para errores de lógica:**
```python
# ❌ Malo - No reintentar errores de validación
config = RetryConfig(retry_on=(Exception,))  # Demasiado amplio

# ✅ Bueno
config = RetryConfig(retry_on=(ConnectionError, TimeoutError))
```

2. **No establecer max_attempts muy alto sin considerar tiempo:**
```python
# ❌ Malo - Puede bloquear por mucho tiempo
config = RetryConfig(
    max_attempts=100,  # Demasiado
    initial_delay=5.0
)

# ✅ Bueno
config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0
)
```

3. **No ignorar la excepción original:**
```python
# ❌ Malo
try:
    result = handler.execute(operation)
except RetryExhaustedError:
    pass  # Ignorar completamente

# ✅ Bueno
try:
    result = handler.execute(operation)
except RetryExhaustedError as e:
    logger.error(f"Failed: {e.last_exception}")
    # Tomar acción apropiada
```

4. **No usar reintentos para operaciones no idempotentes sin cuidado:**
```python
# ❌ Malo - Puede crear múltiples órdenes
@with_retry()
def open_trade_non_idempotent():
    mt5.order_send(request)  # Sin verificar si ya se creó

# ✅ Bueno - Verificar estado antes de reintentar
@with_retry()
def open_trade_idempotent():
    if not trade_already_exists():
        mt5.order_send(request)
```

---

## 🔄 Integración con Otros Módulos

### Con logger.py (T39)

```python
from src.core.logger import get_bot_logger, LogConfig
from src.core.retry_handler import RetryHandler, MT5_RETRY_CONFIG

# Logger configurado
logger = get_bot_logger("bot_1", LogConfig())

# Handler con logging automático
handler = RetryHandler(MT5_RETRY_CONFIG)

# Logs automáticos en cada reintento
result = handler.execute(mt5_operation, logger=logger)
```

### Con config_loader.py (T44)

```python
from src.core.config_loader import ConfigLoader
from src.core.retry_handler import RetryConfig, RetryHandler

# Cargar configuración de reintentos desde JSON
config_loader = ConfigLoader()
config_loader.load_json_config("config/retry.json")

# Crear configuración de reintentos
retry_config = RetryConfig(
    max_attempts=config_loader.get_config_value("retry.max_attempts", 3),
    initial_delay=config_loader.get_config_value("retry.initial_delay", 1.0),
    max_delay=config_loader.get_config_value("retry.max_delay", 30.0)
)

handler = RetryHandler(retry_config)
```

### Con futuros módulos MT5

```python
from src.core.retry_handler import retry_mt5_operation
from src.integrations.mt5_connector import MT5Connector

class MT5Connector:
    def __init__(self):
        self.connected = False
    
    def connect(self):
        """Conecta con reintentos automáticos"""
        result = retry_mt5_operation(
            self._do_connect,
            login=self.account,
            password=self.password
        )
        self.connected = result
        return result
    
    def _do_connect(self, login, password):
        # Lógica de conexión real
        return mt5.initialize(login=login, password=password)
```

---

## 📈 Métricas

| Métrica | Valor |
|---------|-------|
| Líneas de código | 434 |
| Tests | 34 |
| Cobertura | 95% |
| Complejidad ciclomática | Baja |
| Mantenibilidad | Alta |
| Performance | Excelente |

---

## 🚀 Próximos Pasos

1. ✅ **T38 Completado** - Reintentos automáticos con backoff
2. ⏭️ **Integrar en MT5 Connector** - Aplicar reintentos en operaciones MT5
3. ⏭️ **Integrar en IA Agent** - Aplicar reintentos en consultas Gemini
4. ⏭️ **Métricas de reintentos** - Dashboard de intentos fallidos
5. ⏭️ **Alertas** - Notificar si hay muchos reintentos

---

## 🔧 Configuración Recomendada por Escenario

### Desarrollo / Testing
```python
RetryConfig(
    max_attempts=2,
    initial_delay=0.1,  # Rápido para tests
    max_delay=1.0,
    jitter=False  # Determinista para tests
)
```

### Producción - MT5
```python
RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    backoff_factor=2.0,
    retry_on=(ConnectionError, TimeoutError, OSError)
)
```

### Producción - IA (Gemini)
```python
RetryConfig(
    max_attempts=3,
    initial_delay=2.0,  # Más delay por cuota
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=True,  # Distribuir carga
    retry_on=(ConnectionError, TimeoutError)
)
```

### Alta Disponibilidad
```python
RetryConfig(
    max_attempts=5,
    initial_delay=0.5,
    max_delay=60.0,
    backoff_factor=2.0,
    jitter=True,
    retry_on=(ConnectionError, TimeoutError)
)
```

---

## 🛡️ Consideraciones de Seguridad

1. **No exponer credenciales en logs de error:**
```python
# ✅ Correcto
logger.error("Failed to connect", extra={"server": server_name})

# ❌ Malo
logger.error(f"Failed: {username}:{password}")
```

2. **Límite de reintentos para prevenir DoS:**
- max_attempts razonable (≤5)
- max_delay para evitar bloqueos largos

3. **Jitter para evitar thundering herd:**
- Siempre habilitado en producción
- Distribuye carga en servicios compartidos

---

## 📊 Análisis de Performance

### Tiempo Total de Reintentos

Para `max_attempts=3`, `initial_delay=1.0`, `backoff_factor=2.0`:

```
Intento 1: 0s (falla)
  ↓ delay 1.0s
Intento 2: 0s (falla)
  ↓ delay 2.0s
Intento 3: 0s (éxito)

Tiempo total: ~3.0s
```

### Recomendaciones

- **Operaciones críticas:** max_attempts=5, initial_delay=0.5s
- **Operaciones normales:** max_attempts=3, initial_delay=1.0s
- **Operaciones costosas:** max_attempts=2, initial_delay=2.0s

---

## 🤝 Compatibilidad

- ✅ Python 3.13+
- ✅ Windows, Linux, macOS
- ✅ Thread-safe
- ✅ Async-compatible (con adaptación)
- ✅ Sin dependencias externas

---

## 📝 Ejemplo de Archivo de Configuración

**config/retry.json:**
```json
{
  "retry": {
    "mt5": {
      "max_attempts": 3,
      "initial_delay": 1.0,
      "max_delay": 10.0,
      "backoff_factor": 2.0,
      "jitter": true
    },
    "ia": {
      "max_attempts": 3,
      "initial_delay": 2.0,
      "max_delay": 30.0,
      "backoff_factor": 2.0,
      "jitter": true
    },
    "network": {
      "max_attempts": 5,
      "initial_delay": 1.0,
      "max_delay": 60.0,
      "backoff_factor": 2.0,
      "jitter": true
    }
  }
}
```

---

## 🎯 Casos de Uso Reales

### 1. Reconexión MT5 en Inicio de Ciclo
```python
@with_retry(MT5_RETRY_CONFIG)
def ensure_mt5_connection():
    if not mt5.terminal_info():
        raise ConnectionError("MT5 not connected")
    return True

# En el orquestador
try:
    ensure_mt5_connection()
    # Continuar con ciclo
except RetryExhaustedError:
    logger.critical("Cannot connect to MT5, skipping cycle")
    return
```

### 2. Consulta Gemini con Fallback
```python
@with_retry(IA_RETRY_CONFIG)
def get_ia_decision(market_data):
    response = gemini.query(prompt=generate_prompt(market_data))
    return parse_response(response)

try:
    decision = get_ia_decision(market_data)
except RetryExhaustedError:
    # Fallback a estrategia simple
    decision = simple_strategy(market_data)
    logger.warning("Using fallback strategy due to IA unavailability")
```

### 3. Gestión de Órdenes con Verificación
```python
@with_retry(MT5_RETRY_CONFIG)
def modify_order_with_verification(ticket, new_sl, new_tp):
    # Modificar orden
    result = mt5.order_modify(ticket, sl=new_sl, tp=new_tp)
    
    if not result:
        raise ConnectionError("Failed to modify order")
    
    # Verificar que se aplicó
    position = mt5.positions_get(ticket=ticket)
    if not position or position[0].sl != new_sl:
        raise ConnectionError("Order modification not applied")
    
    return True
```

---

**Documento generado:** 2025-11-06  
**Versión:** 1.0  
**Estado:** ✅ Completado y testeado  
**Cobertura:** 95%  
**Tests:** 34/34 pasados

````
