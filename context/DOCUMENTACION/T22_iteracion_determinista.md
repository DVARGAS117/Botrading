# T22: Iteración Determinista de Activos

## Estado
✅ **COMPLETADO** (2025-11-11)

## Resumen Ejecutivo
Implementación de iteración determinista de activos en el módulo **CoreModule**, garantizando que todos los bots del sistema procesen sus símbolos asignados en el mismo orden predecible en cada ciclo de trading. Esta funcionalidad es fundamental para asegurar cobertura completa, consistencia en la evaluación, y facilitar debugging y auditorías del sistema multi-activo.

## Problema Identificado
En un sistema de trading multi-activo donde múltiples bots operan diferentes símbolos, es crítico que:
- **Orden sea predecible**: Mismo orden de procesamiento en cada ciclo
- **Cobertura completa**: Todos los símbolos se evalúen en cada ciclo
- **Debugging facilitado**: Logs consistentes y predecibles
- **Auditoría posible**: Trazabilidad de qué símbolo se procesó cuándo
- **Sin aleatoriedad**: Comportamiento reproducible

Sin iteración determinista:
- Orden aleatorio dificulta debugging (logs diferentes cada vez)
- Imposible reproducir problemas específicos de un símbolo
- Auditorías complicadas (no se puede trazar secuencia)
- Testing no reproducible
- Riesgo de sesgo temporal (algunos símbolos siempre primero/último)

## Arquitectura

### Concepto de Determinismo

**Determinismo** significa que dadas las mismas entradas (lista de símbolos), el sistema siempre los procesa en el mismo orden.

```
Ciclo 1: ["EURUSD", "GBPUSD", "USDJPY"]  → Procesa en ese orden
Ciclo 2: ["EURUSD", "GBPUSD", "USDJPY"]  → Procesa en ese orden
Ciclo 3: ["EURUSD", "GBPUSD", "USDJPY"]  → Procesa en ese orden

❌ NO determinista (aleatorio):
Ciclo 1: ["USDJPY", "EURUSD", "GBPUSD"]
Ciclo 2: ["GBPUSD", "USDJPY", "EURUSD"]
Ciclo 3: ["EURUSD", "GBPUSD", "USDJPY"]
```

### Componentes que Garantizan Determinismo

#### 1. **GlobalConfigManager** (T05/T20)
Retorna listas ordenadas alfabéticamente:

```python
from src.core.global_config_manager import GlobalConfigManager

manager = GlobalConfigManager("config")

# get_all_instruments() SIEMPRE retorna ordenada alfabéticamente
instruments = manager.get_all_instruments()
# ["AUDUSD", "EURUSD", "GBPUSD", "USDJPY"]  ← Alfabético
# Llamar 100 veces → siempre mismo orden

# list_enabled_bots() SIEMPRE retorna ordenada alfabéticamente
bots = manager.list_enabled_bots()
# ["bot_1", "bot_2", "bot_3"]  ← Alfabético
```

#### 2. **CoreModule** Base Class
Proporciona infraestructura para módulos reutilizables:

```python
from src.core.core_module import CoreModule

class TradingModule(CoreModule):
    def __init__(self):
        super().__init__(
            name="TradingModule",
            version="1.0.0",
            description="Módulo de trading determinista"
        )
    
    def process_symbols(self, symbols: List[str]) -> None:
        """Procesa símbolos en orden determinista"""
        # Garantizar orden (aunque debería venir ordenado)
        sorted_symbols = sorted(symbols)
        
        for symbol in sorted_symbols:
            self.logger.info(f"Procesando {symbol}")
            # Lógica de trading...
```

#### 3. **Logging Estructurado** (T39)
Registra secuencia de procesamiento:

```python
from src.core.logger import BotLogger

logger = BotLogger("bot_1")

# En cada ciclo
for i, symbol in enumerate(instruments):
    logger.info(f"[{i+1}/{len(instruments)}] Procesando {symbol}")
    # 2025-11-11 10:00:01 - bot_1 - INFO - [1/3] Procesando EURUSD
    # 2025-11-11 10:00:05 - bot_1 - INFO - [2/3] Procesando GBPUSD
    # 2025-11-11 10:00:09 - bot_1 - INFO - [3/3] Procesando USDJPY
```

### Flujo de Iteración Determinista

```
1. Sistema inicia ciclo de trading (T01)
   │
2. GlobalConfigManager carga configuración
   │   manager = GlobalConfigManager("config")
   │
3. Obtener bots habilitados (orden alfabético garantizado)
   │   enabled_bots = manager.list_enabled_bots()
   │   → ["bot_1", "bot_2", "bot_3"]  ✓ Siempre mismo orden
   │
4. Iterar cada bot (orden determinista)
   │   for bot_name in enabled_bots:
   │
5. Para cada bot, obtener sus símbolos
   │       bot_config = manager.get_bot_config(bot_name)
   │       instruments = bot_config["instruments"]
   │       → ["EURUSD", "GBPUSD"]  ✓ Orden del config
   │
6. Procesar cada símbolo (orden determinista)
   │       for symbol in instruments:
   │           logger.info(f"Procesando {symbol}")
   │           process_symbol(symbol)
   │
7. Próximo ciclo → mismo orden exacto
```

## Características Implementadas

### ✅ Ordenamiento Alfabético Garantizado
- **get_all_instruments()**: Retorna `sorted(list(set(...)))`
- **list_enabled_bots()**: Retorna lista ordenada
- **Consistencia**: Python's `sorted()` garantiza orden estable

### ✅ Metadata de Módulo
- **CoreModule base class**: Todos los módulos heredan
- **Timestamp de inicialización**: Registro de cuándo se creó
- **Versión y descripción**: Trazabilidad de componentes

### ✅ Logging de Secuencia
- **Índice en logs**: `[1/3]`, `[2/3]`, `[3/3]`
- **Timestamp preciso**: Permite calcular tiempo por símbolo
- **Bot identificado**: Logs separados por bot

### ✅ Validación de Orden
- **Tests específicos**: Verifican que orden se preserve
- **Múltiples ejecuciones**: Tests ejecutan múltiples veces para verificar
- **No aleatoriedad**: Sin uso de `random`, `shuffle`, etc.

### ✅ Reproducibilidad
- **Mismos inputs → mismos outputs**: Garantizado por diseño
- **Testing determinista**: Tests no son flaky
- **Debugging facilitado**: Reproducir problemas posible

## Casos de Uso

### 1. Ciclo de Trading Determinista (Caso Principal)
```python
from src.core.global_config_manager import GlobalConfigManager
from src.core.logger import BotLogger

def execute_trading_cycle():
    """Ejecuta un ciclo de trading con iteración determinista"""
    manager = GlobalConfigManager("config")
    
    # Obtener bots habilitados (orden determinista)
    enabled_bots = manager.list_enabled_bots()
    
    for bot_name in enabled_bots:
        logger = BotLogger(bot_name)
        logger.info(f"=== Iniciando ciclo de {bot_name} ===")
        
        # Obtener configuración del bot
        bot_config = manager.get_bot_config(bot_name)
        instruments = bot_config["instruments"]
        
        # Procesar cada símbolo en orden determinista
        for i, symbol in enumerate(instruments, start=1):
            logger.info(f"[{i}/{len(instruments)}] Procesando {symbol}")
            
            # Aquí va la lógica de trading:
            # - Extraer velas
            # - Calcular indicadores
            # - Consultar IA
            # - Ejecutar órdenes si corresponde
            
            process_symbol(symbol, bot_config)
        
        logger.info(f"=== Ciclo de {bot_name} completado ===")
```

**Output en logs (siempre mismo orden):**
```
2025-11-11 10:00:00 - bot_1 - INFO - === Iniciando ciclo de bot_1 ===
2025-11-11 10:00:01 - bot_1 - INFO - [1/2] Procesando EURUSD
2025-11-11 10:00:05 - bot_1 - INFO - [2/2] Procesando GBPUSD
2025-11-11 10:00:09 - bot_1 - INFO - === Ciclo de bot_1 completado ===
2025-11-11 10:00:10 - bot_2 - INFO - === Iniciando ciclo de bot_2 ===
2025-11-11 10:00:11 - bot_2 - INFO - [1/3] Procesando AUDUSD
2025-11-11 10:00:15 - bot_2 - INFO - [2/3] Procesando NZDUSD
2025-11-11 10:00:19 - bot_2 - INFO - [3/3] Procesando USDJPY
2025-11-11 10:00:23 - bot_2 - INFO - === Ciclo de bot_2 completado ===
```

### 2. Debugging con Orden Predecible
```python
# Escenario: Bug en procesamiento de GBPUSD del bot_1

# 1. Revisar logs (orden siempre igual)
# 2025-11-11 10:00:01 - bot_1 - INFO - [1/2] Procesando EURUSD
# 2025-11-11 10:00:05 - bot_1 - INFO - [2/2] Procesando GBPUSD  ← Error aquí
# 2025-11-11 10:00:05 - bot_1 - ERROR - Error en GBPUSD: ...

# 2. Reproducir exactamente
def test_gbpusd_bug():
    """Test que reproduce el bug en GBPUSD"""
    # Simular hasta GBPUSD (segundo símbolo)
    instruments = ["EURUSD", "GBPUSD"]  # Orden determinista
    
    for symbol in instruments:
        if symbol == "GBPUSD":
            # Aquí reproduzco el bug
            result = process_symbol("GBPUSD", test_config)
            assert result is not None  # Falla igual que en producción
```

### 3. Auditoría de Cobertura
```python
def audit_symbol_coverage():
    """Verifica que todos los símbolos se procesaron en el ciclo"""
    manager = GlobalConfigManager("config")
    
    # Símbolos esperados (orden determinista)
    expected_symbols = set(manager.get_all_instruments())
    
    # Símbolos procesados (extraer de logs)
    processed_symbols = extract_processed_symbols_from_logs()
    
    # Verificar cobertura completa
    missing = expected_symbols - processed_symbols
    extra = processed_symbols - expected_symbols
    
    if missing:
        print(f"⚠ Símbolos no procesados: {missing}")
    
    if extra:
        print(f"⚠ Símbolos procesados no configurados: {extra}")
    
    if not missing and not extra:
        print("✓ Cobertura completa - Todos los símbolos procesados")
```

### 4. Análisis de Tiempo de Procesamiento
```python
import time
from collections import defaultdict

def analyze_processing_time():
    """Analiza tiempo de procesamiento por símbolo"""
    manager = GlobalConfigManager("config")
    
    timings = defaultdict(list)
    
    # Ejecutar múltiples ciclos
    for cycle in range(10):
        instruments = manager.get_all_instruments()  # Orden determinista
        
        for symbol in instruments:
            start = time.time()
            process_symbol(symbol, config)
            elapsed = time.time() - start
            
            timings[symbol].append(elapsed)
    
    # Analizar resultados
    print("=== TIEMPOS DE PROCESAMIENTO ===")
    for symbol in sorted(timings.keys()):  # Orden alfabético en reporte
        times = timings[symbol]
        avg = sum(times) / len(times)
        print(f"{symbol}: {avg:.2f}s promedio")
```

### 5. Testing con Múltiples Ejecuciones
```python
def test_deterministic_iteration_multiple_runs():
    """Verifica que múltiples ejecuciones producen mismo orden"""
    manager = GlobalConfigManager("config")
    
    # Ejecutar 100 veces
    results = []
    for _ in range(100):
        instruments = manager.get_all_instruments()
        results.append(instruments.copy())
    
    # Verificar que todas son iguales
    first = results[0]
    for i, result in enumerate(results[1:], start=2):
        assert result == first, f"Iteración {i} difiere de la primera"
    
    print("✓ 100 ejecuciones con orden idéntico")
```

## Testing

### Cobertura de Determinismo

#### Tests de CoreModule (10+ tests)
- ✅ Inicialización con metadata
- ✅ Metadata inmutable (frozen dataclass)
- ✅ Ciclo de vida (shutdown, restart)
- ✅ Validación de dependencias
- ✅ Información del módulo

#### Tests de Orden Determinista (5+ tests)
- ✅ get_all_instruments() retorna siempre mismo orden
- ✅ list_enabled_bots() retorna siempre mismo orden
- ✅ Múltiples llamadas producen mismo resultado
- ✅ Orden alfabético verificado
- ✅ Sin duplicados en instrumentos

### Ejemplo de Test Crítico
```python
def test_deterministic_iteration_guaranteed():
    """
    Test crítico para T22: Verificar que la iteración es determinista
    
    GIVEN múltiples bots con múltiples instrumentos
    WHEN se obtienen los instrumentos múltiples veces
    THEN el orden es siempre idéntico
    """
    manager = GlobalConfigManager("config")
    
    # Ejecutar 50 veces
    iterations = []
    for _ in range(50):
        instruments = manager.get_all_instruments()
        iterations.append(tuple(instruments))  # tuple para comparación
    
    # Todas las iteraciones deben ser idénticas
    assert len(set(iterations)) == 1, "Orden no es determinista"
    
    # Verificar que está ordenado alfabéticamente
    first_iteration = list(iterations[0])
    assert first_iteration == sorted(first_iteration)
```

## Integración con Otros Módulos

### ✅ GlobalConfigManager (T05/T20)
- **Fuente de datos**: Proporciona listas ordenadas de bots e instrumentos
- **Garantía de orden**: Implementa ordenamiento alfabético

### ✅ BotLogger (T39)
- **Trazabilidad**: Logs muestran secuencia de procesamiento
- **Debugging**: Logs consistentes facilitan debugging

### ✅ CycleScheduler (T01)
- **Orquestación**: Usa orden determinista para ejecutar ciclos
- **Cobertura**: Garantiza que todos los símbolos se procesen

### 🔄 Próximas Integraciones
- **BotInstance (T03)**: Cada instancia procesa sus símbolos en orden
- **FilterManager (T02)**: Aplica filtros en orden determinista
- **OperationVerifier (T04)**: Verifica operaciones en orden predecible

## Decisiones de Diseño

### 1. **Orden Alfabético como Estándar**
**Decisión**: Usar orden alfabético en lugar de orden de archivo  
**Razón**:
- Predecible: Fácil de saber qué viene después
- Universal: No depende de formato de archivo
- Natural: Coincide con expectativas humanas

### 2. **sorted() en Retorno, No en Almacenamiento**
**Decisión**: Ordenar al retornar, no al almacenar  
**Razón**:
- Flexibilidad: Archivo puede tener cualquier orden
- Simplicidad: Menos lógica en carga de config
- Eficiencia: sorted() es O(n log n) aceptable

### 3. **CoreModule como Base**
**Decisión**: Clase base CoreModule para todos los módulos  
**Razón**:
- Reutilización: Metadata y logging común
- Consistencia: Todos los módulos con misma interfaz
- Mantenibilidad: Cambios en un lugar

### 4. **Logging con Índice [i/total]**
**Decisión**: Incluir `[1/3]`, `[2/3]` en logs  
**Razón**:
- Progreso: Fácil ver cuánto falta
- Debugging: Identificar dónde ocurrió error
- Auditoría: Verificar cobertura completa

### 5. **Sin Paralelización en Iteración**
**Decisión**: Procesamiento secuencial, no paralelo  
**Razón**:
- Determinismo: Paralelo es no determinista
- Simplicidad: Más fácil de debuggear
- MT5 Limitation: MT5 no es thread-safe

### 6. **Validación en Tests, No en Runtime**
**Decisión**: Tests verifican orden, no validación en cada ciclo  
**Razón**:
- Performance: No overhead en producción
- Confianza: Tests garantizan comportamiento
- Claridad: Si tests pasan, orden está garantizado

## Beneficios

### 🎯 Debugging Facilitado
- Logs consistentes en cada ciclo
- Problemas reproducibles
- Identificación rápida de símbolos problemáticos

### 🔍 Auditoría Simplificada
- Trazabilidad completa de procesamiento
- Verificación de cobertura posible
- Análisis temporal facilitado

### 📊 Testing Robusto
- Tests no flaky (no aleatorios)
- Reproducibilidad garantizada
- Verificación de cobertura en tests

### 🧪 Análisis de Rendimiento
- Comparaciones válidas entre ciclos
- Tiempos de procesamiento comparables
- Identificación de cuellos de botella

### 🔧 Mantenibilidad
- Comportamiento predecible
- Menos bugs por aleatoriedad
- Más fácil razonar sobre el código

## Línea de Tiempo

| Fecha | Hora | Actividad | Estado |
|-------|------|-----------|--------|
| 2025-11-11 | 08:00 | Diseño de CoreModule base class | ✅ |
| 2025-11-11 | 08:30 | Implementación de ordenamiento en GlobalConfigManager | ✅ |
| 2025-11-11 | 09:00 | Tests de determinismo | ✅ |
| 2025-11-11 | 09:30 | Validación con múltiples ejecuciones | ✅ |
| 2025-11-11 | 10:00 | Documentación | ✅ |

**Tiempo total**: ~2 horas (distribuido en T05 y CoreModule)

## Comandos Útiles

```powershell
# Ejecutar tests de CoreModule
python -m pytest tests/unit/test_core_module.py -v

# Ejecutar tests de GlobalConfigManager (incluye orden)
python -m pytest tests/unit/test_global_config_manager.py -v

# Verificar orden determinista interactivamente
python -c "
from src.core.global_config_manager import GlobalConfigManager
manager = GlobalConfigManager('config')
for i in range(5):
    print(f'Iteración {i+1}:', manager.get_all_instruments())
"

# Analizar logs de orden
grep 'Procesando' logs/bot_1.log | head -10
```

## Dependencias

### Runtime
- **Python 3.9+**
- **Módulos estándar**: `dataclasses`, `datetime`, `typing`

### Módulos Internos
- `src.core.global_config_manager` (T05/T20)
- `src.core.core_module` (Base class)
- `src.core.logger` (T39)

### Testing
- `pytest >= 8.0`

## Archivos Relacionados

```
src/core/core_module.py                     (Base class)
src/core/global_config_manager.py           (Orden garantizado)
tests/unit/test_core_module.py              (Tests de base class)
tests/unit/test_global_config_manager.py    (Tests de orden)
context/DOCUMENTACION/T22_iteracion_determinista.md  (Este archivo)
```

## Métricas

| Métrica | Valor |
|---------|-------|
| **Módulos con iteración determinista** | 2 (CoreModule, GlobalConfigManager) |
| **Tests de determinismo** | 5+ |
| **Tests de CoreModule** | 10+ |
| **Ejecuciones en tests de repetición** | 50-100 |
| **Garantía de orden** | 100% (alfabético) |

## Conclusión

✅ **T22 completado exitosamente** mediante:
- Ordenamiento alfabético garantizado en GlobalConfigManager
- CoreModule base class con metadata y lifecycle
- Tests que verifican determinismo con múltiples ejecuciones
- Logging estructurado con índices de progreso
- Sin aleatoriedad en ninguna parte del sistema

**Beneficios Clave:**
- ✅ Debugging facilitado con logs predecibles
- ✅ Auditoría simplificada con orden consistente
- ✅ Testing robusto sin flakiness
- ✅ Análisis de rendimiento válido
- ✅ Mantenibilidad mejorada

**Impacto en Otros Tickets:**
- T01: Ciclo de ejecución usa orden determinista
- T03: Cada instancia de bot procesa símbolos en orden
- T04: Verificación de operaciones en orden predecible
- T21: Garantía de operación única depende de orden

---

**Autor**: Sistema Botrading  
**Fecha**: 2025-11-11  
**Ticket**: T22 - Iteración determinista de activos  
**Issue**: #38  
**Implementado en**: CoreModule + GlobalConfigManager  
**Tests**: 15+ tests de determinismo ✅
