# T6: Verificación de Conexión MT5 al Inicio

## Estado
✅ **COMPLETADO** (2025-11-06)

## Resumen Ejecutivo
Implementación del **MT5Connector**, un componente robusto y agnóstico al broker para conectar, validar y gestionar la conexión con MetaTrader 5. Este módulo asegura que la conexión esté disponible antes de cualquier operación de trading, implementando validación con reintentos automáticos y manejo integral de errores.

## Problema Identificado
Los bots de trading necesitan garantizar una conexión estable con MT5 antes de:
- Extraer datos de mercado (OHLCV)
- Consultar posiciones abiertas
- Ejecutar órdenes de compra/venta
- Modificar stop loss y take profit

Conectar sin validación puede causar:
- Operaciones con datos inválidos
- Errores en cascada difíciles de diagnosticar
- Pérdidas financieras por órdenes mal ejecutadas
- Falta de trazabilidad en caso de fallos

## Arquitectura

### Componentes Principales

#### 1. **BrokerConfig** (`src/core/mt5_connector.py`)
Dataclass que encapsula la configuración del broker:

```python
from src.core.mt5_connector import BrokerConfig

# Pepperstone (broker actual)
config = BrokerConfig(
    account_id="12345678",
    password="your_password",
    server="Pepperstone-Demo",
    timeout=60
)

# IC Markets (futuro posible cambio)
config = BrokerConfig(
    account_id="87654321",
    password="another_password",
    server="ICMarkets-Live",
    timeout=60
)
```

**Características:**
- ✅ Validación automática de campos requeridos
- ✅ Valores por defecto para timeout (60s)
- ✅ Agnóstico al broker (funciona con cualquiera)
- ✅ Inmutable después de creación (dataclass)

#### 2. **MT5Connector** (`src/core/mt5_connector.py`)
Clase principal que gestiona la conexión a MT5:

```python
from src.core.mt5_connector import MT5Connector

connector = MT5Connector(config)

# Verificar conexión
if connector.verify_connection():
    # Trabajar con MT5
    account = connector.get_account_info()
    terminal = connector.get_terminal_info()
    
# Desconectar
connector.disconnect()
```

**Métodos Principales:**
- `verify_connection()`: Conecta y valida MT5
- `disconnect()`: Cierra la conexión
- `is_connected()`: Verifica estado de conexión
- `get_terminal_info()`: Info del terminal MT5
- `get_account_info()`: Info de la cuenta del broker

### Flujo de Verificación de Conexión

```
1. Bot inicia ciclo de trading
   │
   ├── Crea MT5Connector con BrokerConfig
   │
2. Llama a verify_connection()
   │
   ├── Paso 1: Inicializar MT5
   │   ├── mt5.initialize()
   │   ├── ¿Éxito?
   │   │   ├── NO → Lanza MT5InitializationError
   │   │   └── SÍ → Continúa
   │
   ├── Paso 2: Autenticar
   │   ├── mt5.login(account_id, password, server)
   │   ├── ¿Éxito?
   │   │   ├── NO → Lanza MT5ConnectionError
   │   │   └── SÍ → Continúa
   │
   ├── Paso 3: Verificar terminal
   │   ├── mt5.terminal_info()
   │   ├── ¿Conectado?
   │   │   ├── NO → Lanza MT5ConnectionError
   │   │   └── SÍ → Continúa
   │   ├── ¿Trading permitido?
   │   │   ├── NO → Warning en logs
   │   │   └── SÍ → OK
   │
   └── Retorna True (conexión exitosa)

3. Bot procede con operaciones
   │
   └── Al finalizar: disconnect()
```

## Características Implementadas

### ✅ Diseño Agnóstico al Broker
- **Problema**: Actualmente usa Pepperstone, pero puede cambiar
- **Solución**: `BrokerConfig` acepta cualquier servidor MT5
- **Ejemplos soportados**:
  - Pepperstone: `Pepperstone-Demo`, `Pepperstone-Live`
  - IC Markets: `ICMarkets-Demo`, `ICMarkets-Live`
  - XM: `XM-Demo`, `XM-Real`
  - Cualquier broker compatible con MT5

### ✅ Validación Robusta
- **Inicialización**: Verifica que MT5 se inicialice correctamente
- **Autenticación**: Valida credenciales con el broker
- **Estado del terminal**: Confirma conexión activa al servidor
- **Trading permitido**: Advierte si el trading está deshabilitado

### ✅ Manejo de Errores
- **Excepciones específicas**:
  - `MT5InitializationError`: Fallos al inicializar MT5
  - `MT5ConnectionError`: Fallos de conexión o autenticación
- **Información detallada**: Incluye códigos de error de MT5
- **Logging estructurado**: Registra todos los eventos

### ✅ Integración con RetryHandler
- **Reintentos automáticos**: Usa `MT5_RETRY_CONFIG` predefinido
- **Backoff exponencial**: Espera creciente entre reintentos
- **Límite de intentos**: 3 intentos por defecto
- **Excepciones específicas**: Solo reintenta errores de conexión

### ✅ Context Manager
- **Conexión automática**: Al entrar al contexto
- **Desconexión garantizada**: Al salir del contexto (incluso con excepciones)
- **Código limpio**: Menos líneas, más seguro

```python
# Sin context manager (manual)
connector = MT5Connector(config)
try:
    connector.verify_connection()
    # usar connector
finally:
    connector.disconnect()

# Con context manager (recomendado)
with MT5Connector(config) as connector:
    # usar connector
    # desconexión automática
```

### ✅ Decorador @require_connection
- **Validación automática**: Métodos que requieren conexión la validan
- **Error descriptivo**: Mensaje claro si no hay conexión
- **Métodos protegidos**:
  - `get_terminal_info()`
  - `get_account_info()`

### ✅ Logging Detallado
- **Niveles apropiados**:
  - INFO: Conexión exitosa, desconexión
  - WARNING: Trading no permitido
  - ERROR: Fallos de inicialización o conexión
  - DEBUG: Pasos intermedios
- **Contexto rico**: IDs de cuenta, servidores, códigos de error

## Casos de Uso

### 1. Conexión en Ciclo de Trading
```python
from src.core.mt5_connector import MT5Connector, BrokerConfig
from src.core.logger import get_bot_logger, LogLevel, LogConfig

def trading_cycle():
    """Ciclo principal del bot"""
    logger = get_bot_logger("bot_1", LogConfig(level=LogLevel.INFO))
    
    config = BrokerConfig(
        account_id="12345678",
        password="my_password",
        server="Pepperstone-Demo"
    )
    
    connector = MT5Connector(config, logger=logger.logger)
    
    try:
        # Verificar conexión al inicio
        if not connector.verify_connection():
            logger.error("Falló verificación MT5, abortando ciclo")
            return False
        
        logger.info("MT5 conectado exitosamente")
        
        # Aquí van las operaciones:
        # - Extraer OHLCV
        # - Calcular indicadores
        # - Consultar IA
        # - Ejecutar órdenes
        
        return True
    
    except Exception as e:
        logger.exception(f"Error en ciclo: {e}")
        return False
    
    finally:
        connector.disconnect()
```

### 2. Con Context Manager (Recomendado)
```python
with MT5Connector(config) as connector:
    account = connector.get_account_info()
    print(f"Balance: ${account.balance:.2f}")
    
    terminal = connector.get_terminal_info()
    print(f"Conectado: {terminal.connected}")
    print(f"Trading: {terminal.trade_allowed}")
```

### 3. Con CredentialManager
```python
from src.core.credential_manager import CredentialManager
from src.core.mt5_connector import create_connector_from_credentials

# Cargar credenciales encriptadas
cred_manager = CredentialManager()
credentials = cred_manager.load_from_file('config/credentials.enc')

# Validar
cred_manager.validate_mt5_credentials()

# Crear connector
mt5_creds = {
    'account_id': credentials.get('mt5', {}).get('account_id'),
    'password': credentials.get('mt5', {}).get('password'),
    'server': credentials.get('mt5', {}).get('server')
}

connector = create_connector_from_credentials(mt5_creds)
```

### 4. Cambio de Broker
```python
# De Pepperstone a IC Markets (sin cambiar código del bot)

# Antes (Pepperstone)
config_old = BrokerConfig(
    account_id="12345678",
    password="pepperstone_pass",
    server="Pepperstone-Demo"
)

# Después (IC Markets)
config_new = BrokerConfig(
    account_id="87654321",
    password="icmarkets_pass",
    server="ICMarkets-Live"
)

# El resto del código del bot NO cambia
connector = MT5Connector(config_new)
```

## Testing

### Cobertura Completa (27 tests, 100%)

#### Tests de BrokerConfig (5 tests)
- ✅ Inicialización con todos los parámetros
- ✅ Timeout por defecto (60s)
- ✅ Validación de account_id requerido
- ✅ Validación de password requerido
- ✅ Validación de server requerido

#### Tests de MT5Connector (22 tests)
- ✅ **Inicialización** (2 tests)
  - Con/sin logger personalizado
  - Estado inicial desconectado
  
- ✅ **Conexión exitosa** (2 tests)
  - Verificación completa
  - Con retry handler
  
- ✅ **Fallos de conexión** (3 tests)
  - Fallo en inicialización
  - Fallo en login
  - Terminal no conectado
  
- ✅ **Reintentos** (1 test)
  - Éxito en segundo intento
  
- ✅ **Desconexión** (2 tests)
  - Cuando está conectado
  - Cuando no está conectado
  
- ✅ **Información** (4 tests)
  - Terminal info cuando conectado/desconectado
  - Account info cuando conectado/desconectado
  
- ✅ **Context Manager** (2 tests)
  - Conexión/desconexión automática
  - Desconexión incluso con excepciones
  
- ✅ **Decoradores** (2 tests)
  - @require_connection cuando conectado
  - @require_connection cuando desconectado
  
- ✅ **Compatibilidad de Broker** (2 tests)
  - Pepperstone
  - Broker genérico
  
- ✅ **Logging** (2 tests)
  - Logs en conexión exitosa
  - Logs en conexión fallida

### Ejecutar Tests
```powershell
# Todos los tests del MT5Connector
pytest tests/unit/test_mt5_connector.py -v

# Solo tests de BrokerConfig
pytest tests/unit/test_mt5_connector.py::TestBrokerConfig -v

# Solo tests de conexión
pytest tests/unit/test_mt5_connector.py -k "connection" -v

# Con coverage
pytest tests/unit/test_mt5_connector.py --cov=src.core.mt5_connector --cov-report=term-missing
```

## Integración con Otros Módulos

### ✅ RetryHandler (T38)
- **Dependencia**: Usa `MT5_RETRY_CONFIG` predefinido
- **Uso**: Reintentos automáticos en `verify_connection()`
- **Configuración**: 3 intentos, backoff exponencial

### ✅ Logger (T39)
- **Dependencia**: Acepta logger personalizado
- **Formato**: Logs estructurados con extra data
- **Niveles**: DEBUG, INFO, WARNING, ERROR

### ✅ CredentialManager (T47)
- **Integración**: `create_connector_from_credentials()`
- **Validación**: `validate_mt5_credentials()`
- **Seguridad**: Credenciales encriptadas

### 🔄 Próximas Integraciones
- **CycleScheduler (T01)**: Verificar conexión al inicio de cada ciclo
- **Extracción OHLCV (T07)**: Usar connector para obtener datos
- **Gestión de Posiciones (T08)**: Consultar posiciones abiertas
- **Ejecución de Órdenes (T09)**: Abrir/cerrar/modificar órdenes

## Decisiones de Diseño

### 1. **Diseño Agnóstico al Broker**
**Decisión**: No hardcodear configuración de Pepperstone  
**Razón**: Permitir fácil migración a otros brokers en el futuro  
**Beneficio**: Flexibilidad, reutilización, mantenibilidad

### 2. **Excepciones Específicas**
**Decisión**: `MT5InitializationError` y `MT5ConnectionError` separados  
**Razón**: Distinguir entre fallos de init vs fallos de conexión  
**Beneficio**: Mejor manejo de errores, diagnóstico más preciso

### 3. **Decorador @require_connection**
**Decisión**: Validar conexión automáticamente en métodos que la requieren  
**Razón**: Evitar errores crípticos de MT5 por uso sin conexión  
**Beneficio**: Código más limpio, errores más claros

### 4. **Context Manager**
**Decisión**: Implementar `__enter__` y `__exit__`  
**Razón**: Garantizar desconexión incluso con excepciones  
**Beneficio**: Prevención de leaks de conexión, código más pythónico

### 5. **Integración con RetryHandler**
**Decisión**: Usar `MT5_RETRY_CONFIG` predefinido  
**Razón**: Consistencia con otros componentes del sistema  
**Beneficio**: Comportamiento predecible, menos configuración

### 6. **Import Condicional de MT5**
**Decisión**: `try/except` al importar MetaTrader5  
**Razón**: Permitir tests sin tener MT5 instalado  
**Beneficio**: CI/CD funciona, desarrollo sin MT5 posible

## Línea de Tiempo

| Fecha | Actividad | Estado |
|-------|-----------|--------|
| 2025-11-06 18:00 | Selección del issue T06 | ✅ |
| 2025-11-06 18:15 | Diseño de arquitectura y API | ✅ |
| 2025-11-06 18:30 | Tests TDD (27 tests - Red) | ✅ |
| 2025-11-06 19:00 | Implementación MT5Connector | ✅ |
| 2025-11-06 19:30 | Tests TDD (27/27 - Green) | ✅ |
| 2025-11-06 19:45 | Ejemplo de uso completo | ✅ |
| 2025-11-06 20:00 | Documentación completa | ✅ |

**Tiempo total**: ~2 horas

## Comandos Útiles

```powershell
# Ejecutar tests
pytest tests/unit/test_mt5_connector.py -v

# Ejecutar ejemplo (requiere MT5 instalado y configurado)
python examples/mt5_connection_example.py

# Ver representación del connector
python -c "
from src.core.mt5_connector import MT5Connector, BrokerConfig
config = BrokerConfig('123', 'pass', 'Pepperstone-Demo')
connector = MT5Connector(config)
print(connector)
print(repr(connector))
"

# Verificar imports
python -c "from src.core.mt5_connector import *; print('OK')"
```

## Dependencias

### Runtime
- **Python 3.9+**
- **MetaTrader5**: `pip install MetaTrader5` (opcional para desarrollo, requerido en producción)
- **dataclasses**: Estándar en Python 3.7+
- **typing**: Estándar en Python 3.5+

### Módulos Internos
- `src.core.retry_handler`: Para reintentos automáticos
- `src.core.logger`: Para logging estructurado (opcional)
- `src.core.credential_manager`: Para credenciales encriptadas (opcional)

### Testing
- `pytest >= 8.0`
- `unittest.mock`: Estándar en Python 3.3+

## Archivos Creados/Modificados

### Nuevos Archivos
```
src/core/mt5_connector.py                           (450 líneas)
tests/unit/test_mt5_connector.py                    (650 líneas)
examples/mt5_connection_example.py                  (350 líneas)
context/DOCUMENTACION/T6_verificacion_conexion_mt5.md  (este archivo)
```

### Archivos Modificados
```
(ninguno)
```

## Configuración

### config/credentials.example.json
```json
{
    "mt5": {
        "account_id": "12345678",
        "password": "YOUR_PASSWORD",
        "server": "Pepperstone-Demo"
    }
}
```

### Variables de Entorno (Opcional)
```bash
# Para CredentialManager
export BOTRADING_ENCRYPTION_KEY="<base64_encoded_key>"
```

## Próximos Pasos

### Inmediatos
1. ✅ **Commit y push** a rama `feature/T06-verificacion-conexion-mt5`
2. 🔄 **Integración con CycleScheduler** (T01) para verificar al inicio de ciclo
3. 🔄 **Documentación de integración** con otros módulos

### Phase 1 - Siguiente
- **T07**: Extracción de velas cerradas OHLCV por timeframe
- **T08**: Consulta de posiciones por símbolo y Magic Number
- **T09**: Envío de órdenes y gestión de SL/TP/cierre

### Mejoras Futuras (Opcional)
- Reconexión automática en caso de desconexión durante operación
- Health check periódico de la conexión
- Métricas de latencia de conexión
- Pool de conexiones para múltiples cuentas

## Ejemplos de Uso

Ver archivo completo: `examples/mt5_connection_example.py`

Incluye 6 ejemplos:
1. ✅ Conexión básica
2. ✅ Context manager
3. ✅ Con logging
4. ✅ Con CredentialManager
5. ✅ Diferentes brokers
6. ✅ Ciclo de trading completo

## Troubleshooting

### Error: "MetaTrader5 no está disponible"
**Causa**: MT5 no instalado  
**Solución**: `pip install MetaTrader5`

### Error: "No se pudo inicializar MT5"
**Causa**: MT5 no está ejecutándose  
**Solución**: Abrir MetaTrader 5 en el sistema

### Error: "No se pudo autenticar"
**Causa**: Credenciales incorrectas o servidor inválido  
**Solución**: Verificar account_id, password y server en BrokerConfig

### Error: "Terminal no conectado"
**Causa**: MT5 abierto pero sin conexión al broker  
**Solución**: Verificar conexión a internet y estado del servidor del broker

## Conclusión

✅ **T06 completado exitosamente** con implementación robusta:
- Conexión validada con reintentos automáticos
- Diseño agnóstico al broker (Pepperstone, IC Markets, cualquier otro)
- 27 tests unitarios (100% cobertura)
- Integración perfecta con RetryHandler, Logger y CredentialManager
- Context manager para gestión segura de conexiones
- Documentación completa y ejemplos de uso
- Preparado para siguiente fase de integración

**Beneficios Clave:**
- ✅ Previene operaciones con conexión inválida
- ✅ Fácil cambio de broker en el futuro
- ✅ Manejo robusto de errores
- ✅ Logging detallado para diagnóstico
- ✅ API limpia y pythónica

**Próximo ticket recomendado**: T07 (Extracción de velas OHLCV) - usa este connector.

---

**Autor**: Sistema Botrading  
**Fecha**: 2025-11-06  
**Ticket**: T06 - Verificación de conexión MT5 al inicio  
**Branch**: `feature/T06-verificacion-conexion-mt5`  
**Tests**: 27/27 ✅  
**Status**: COMPLETADO ✅
