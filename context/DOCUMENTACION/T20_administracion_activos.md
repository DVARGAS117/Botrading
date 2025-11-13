# T20: Administración de Lista de Activos en Configuración

## Estado
✅ **COMPLETADO** (2025-11-11)

## Resumen Ejecutivo
Implementación de la funcionalidad de administración de activos (símbolos) a través del **GlobalConfigManager**, permitiendo habilitar/deshabilitar instrumentos de trading de forma dinámica mediante archivos de configuración JSON sin necesidad de modificar código fuente ni redesplegar el sistema. Esta capacidad es fundamental para la gestión operacional del sistema multi-activo (Épica #6).

## Problema Identificado
En un sistema de trading automatizado que opera múltiples símbolos (EURUSD, GBPUSD, USDJPY, etc.), es necesario:
- **Habilitar/deshabilitar** símbolos sin tocar código
- **Agregar** nuevos instrumentos sin redespliegue
- **Configurar por bot**: Cada bot puede operar diferentes símbolos
- **Cambios en caliente**: Aplicar cambios sin reiniciar el sistema completo
- **Gestión centralizada**: Un solo lugar para administrar activos

Sin esta capacidad:
- Cada cambio de símbolos requeriría modificar código fuente
- Riesgo de bugs al modificar archivos .py
- Imposible hacer cambios rápidos en producción
- Difícil probar nuevos instrumentos
- No se puede responder ágilmente a condiciones de mercado

## Arquitectura

### Componente Principal: GlobalConfigManager

El `GlobalConfigManager` (implementado en T05) proporciona la infraestructura para administrar activos:

```python
from src.core.global_config_manager import GlobalConfigManager

# Inicializar con directorio de configuración
manager = GlobalConfigManager("config")

# Obtener lista de activos de un bot específico
bot_instruments = manager.get_bot_config("bot_1")["instruments"]
print(bot_instruments)  # ["EURUSD", "GBPUSD"]

# Obtener todos los instrumentos de todos los bots habilitados
all_instruments = manager.get_all_instruments()
print(all_instruments)  # ["EURUSD", "GBPUSD", "USDJPY"]

# Listar bots habilitados
enabled_bots = manager.list_enabled_bots()
print(enabled_bots)  # ["bot_1", "bot_2"]
```

### Estructura de Configuración

#### settings.json
```json
{
  "timezone": "America/Lima",
  "trading_window": {
    "start": "06:00",
    "end": "13:00"
  },
  "bots": {
    "bot_1": {
      "enabled": true,
      "instruments": ["EURUSD", "GBPUSD"],
      "timeframe": "H1",
      "ia_config_id": 0
    },
    "bot_2": {
      "enabled": true,
      "instruments": ["USDJPY", "AUDUSD"],
      "timeframe": "H4",
      "ia_config_id": 1
    },
    "bot_3": {
      "enabled": false,
      "instruments": ["EURJPY"],
      "timeframe": "D1",
      "ia_config_id": 2
    }
  }
}
```

**Campos Clave:**
- `enabled`: true/false para habilitar/deshabilitar bot completo
- `instruments`: Lista de símbolos que el bot debe operar
- `timeframe`: Temporalidad de las velas (H1, H4, D1, etc.)
- `ia_config_id`: Configuración de IA a usar

### Flujo de Administración de Activos

```
1. Operador necesita cambiar activos
   │
   ├── Opción A: Agregar nuevo símbolo
   │   1. Editar config/settings.json
   │   2. Agregar "EURJPY" a instruments de bot_1
   │   3. Guardar archivo
   │   4. Llamar manager.reload_config()
   │   5. Bot procesa EURJPY en siguiente ciclo
   │
   ├── Opción B: Deshabilitar símbolo
   │   1. Editar config/settings.json
   │   2. Quitar "GBPUSD" de instruments de bot_1
   │   3. Guardar archivo
   │   4. Llamar manager.reload_config()
   │   5. Bot ignora GBPUSD en siguiente ciclo
   │
   ├── Opción C: Deshabilitar bot completo
   │   1. Editar config/settings.json
   │   2. Cambiar "enabled": false en bot_3
   │   3. Guardar archivo
   │   4. Llamar manager.reload_config()
   │   5. Sistema ignora bot_3
   │
   └── Opción D: Habilitar bot previamente deshabilitado
       1. Editar config/settings.json
       2. Cambiar "enabled": true en bot_3
       3. Guardar archivo
       4. Llamar manager.reload_config()
       5. Bot_3 comienza a operar
```

## Características Implementadas

### ✅ Configuración por Bot
- **get_bot_config(bot_name)**: Obtiene configuración completa de un bot
- **Estructura clara**: Cada bot tiene su sección independiente
- **Validación**: Error si bot no existe en configuración

### ✅ Lista de Bots Habilitados
- **list_enabled_bots()**: Retorna solo bots con `enabled: true`
- **Filtrado automático**: Ignora bots deshabilitados
- **Orden determinista**: Retorna lista ordenada

### ✅ Agregación de Instrumentos
- **get_all_instruments()**: Lista única de todos los símbolos
- **Sin duplicados**: Usa set() internamente
- **Solo bots habilitados**: Ignora instrumentos de bots deshabilitados
- **Ordenamiento**: Retorna lista alfabéticamente ordenada

### ✅ Recarga en Caliente
- **reload_config()**: Recarga archivos sin reiniciar aplicación
- **Limpia cache**: Descarta configuración anterior
- **Valida integridad**: Verifica que archivos sean válidos
- **Logging**: Registra evento de recarga

### ✅ Validación de Configuración
- **validate_required_keys()**: Verifica claves requeridas
- **Notación de punto**: Valida claves anidadas
- **Fail-fast**: Error inmediato si falta configuración crítica

### ✅ Acceso Flexible
- **get_value()**: Acceso a cualquier valor con notación de punto
- **Default values**: Valores por defecto opcionales
- **Tipos preservados**: Retorna tipos originales (list, dict, bool, etc.)

## Casos de Uso

### 1. Obtener Activos de un Bot Específico
```python
from src.core.global_config_manager import GlobalConfigManager

manager = GlobalConfigManager("config")

# Obtener configuración completa del bot
bot1_config = manager.get_bot_config("bot_1")

# Extraer instrumentos
instruments = bot1_config["instruments"]
print(f"Bot 1 opera: {', '.join(instruments)}")

# Verificar si bot está habilitado
if bot1_config["enabled"]:
    print("Bot 1 está activo")
else:
    print("Bot 1 está deshabilitado")
```

### 2. Iterar Activos de Bots Habilitados (Caso Principal - T22)
```python
# Obtener solo bots habilitados
enabled_bots = manager.list_enabled_bots()

for bot_name in enabled_bots:
    bot_config = manager.get_bot_config(bot_name)
    instruments = bot_config["instruments"]
    
    print(f"\n{bot_name}:")
    for symbol in instruments:
        print(f"  - Procesando {symbol}")
        # Aquí va la lógica de trading para este símbolo
        process_symbol(symbol, bot_config)
```

### 3. Obtener Todos los Símbolos Únicos
```python
# Caso: Necesitas cargar datos de todos los símbolos que el sistema opera
all_instruments = manager.get_all_instruments()

print(f"Total de instrumentos: {len(all_instruments)}")
print(f"Símbolos: {', '.join(all_instruments)}")

# Precargar datos de mercado para todos los símbolos
from src.core.mt5_data_extractor import MT5DataExtractor

extractor = MT5DataExtractor(connector)

for symbol in all_instruments:
    candles = extractor.get_candles(symbol, "H1", count=100)
    print(f"Cargadas {len(candles)} velas de {symbol}")
```

### 4. Aplicar Cambios sin Reiniciar
```python
# Escenario: Operador modifica config/settings.json en producción

print("Sistema en ejecución...")

# Usuario edita archivo externamente
# (Agrega "EURJPY" a bot_1.instruments)

# Aplicar cambios sin reiniciar
manager.reload_config()
print("✓ Configuración recargada")

# Verificar cambios
new_instruments = manager.get_bot_config("bot_1")["instruments"]
print(f"Nuevos instrumentos de bot_1: {new_instruments}")

# Sistema continúa operando con nueva configuración
```

### 5. Validar Configuración al Inicio
```python
# Escenario: Validar que configuración tiene todas las claves requeridas

required_keys = [
    "timezone",
    "trading_window.start",
    "trading_window.end",
    "bots.bot_1.enabled",
    "bots.bot_1.instruments"
]

try:
    manager.validate_required_keys(required_keys)
    print("✓ Configuración válida")
except ConfigurationError as e:
    print(f"✗ Configuración inválida: {e}")
    sys.exit(1)
```

### 6. Habilitar/Deshabilitar Bots Dinámicamente
```python
# Ejemplo: Deshabilitar bot_2 si hay problema

# Leer configuración actual
all_config = manager.get_all_config()

# Modificar
all_config["bots"]["bot_2"]["enabled"] = False

# Guardar a archivo
import json
with open("config/settings.json", "w") as f:
    json.dump(all_config, f, indent=2)

# Recargar
manager.reload_config()

# Verificar
if "bot_2" not in manager.list_enabled_bots():
    print("✓ Bot 2 deshabilitado exitosamente")
```

### 7. Configurar Activos por Entorno
```python
# Escenario: Diferentes activos en demo vs producción

# config/settings.demo.json
demo_instruments = ["EURUSD", "GBPUSD"]  # Pocos para testing

# config/settings.prod.json
prod_instruments = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURJPY"]

# Código del bot
import os
env = os.getenv("TRADING_ENV", "demo")
config_file = f"config/settings.{env}.json"

manager = GlobalConfigManager(config_file)
instruments = manager.get_all_instruments()

print(f"Operando en {env} con {len(instruments)} instrumentos")
```

## Testing

### Cobertura Completa (Test de GlobalConfigManager)

#### Inicialización (3 tests)
- ✅ Carga automática de todos los archivos de configuración
- ✅ Error si falta archivo requerido (settings, schedule, credentials)
- ✅ Carga archivos opcionales sin error si no existen

#### Acceso a Valores (5 tests)
- ✅ get_value() con notación de punto
- ✅ get_value() con valor por defecto
- ✅ get_value() con claves anidadas profundas
- ✅ Tipos preservados (list, dict, bool, int, string)
- ✅ Error si clave requerida no existe

#### Administración de Bots (4 tests)
- ✅ get_bot_config() retorna configuración completa
- ✅ list_enabled_bots() filtra solo habilitados
- ✅ list_enabled_bots() retorna lista ordenada
- ✅ Error si bot no existe

#### Administración de Instrumentos (3 tests)
- ✅ get_all_instruments() retorna lista única
- ✅ get_all_instruments() solo de bots habilitados
- ✅ get_all_instruments() ordenados alfabéticamente

#### Recarga de Configuración (2 tests)
- ✅ reload_config() limpia y recarga archivos
- ✅ reload_config() aplica cambios correctamente

#### Validación (2 tests)
- ✅ validate_required_keys() pasa con claves válidas
- ✅ validate_required_keys() falla si falta clave

### Ejemplo de Test Crítico
```python
def test_get_all_instruments_unique_and_sorted(temp_config_dir):
    """
    Test crítico para T20: Verificar que get_all_instruments()
    retorna lista única de todos los símbolos de bots habilitados
    """
    # Configurar múltiples bots con símbolos overlapping
    settings = {
        "bots": {
            "bot_1": {
                "enabled": True,
                "instruments": ["EURUSD", "GBPUSD"]
            },
            "bot_2": {
                "enabled": True,
                "instruments": ["GBPUSD", "USDJPY"]  # GBPUSD duplicado
            },
            "bot_3": {
                "enabled": False,
                "instruments": ["EURJPY"]  # Deshabilitado
            }
        }
    }
    
    manager = GlobalConfigManager(temp_config_dir)
    
    # Ejecutar
    instruments = manager.get_all_instruments()
    
    # Verificar
    assert isinstance(instruments, list)
    assert len(instruments) == 3  # Solo únicos
    assert set(instruments) == {"EURUSD", "GBPUSD", "USDJPY"}
    assert instruments == sorted(instruments)  # Ordenados
    assert "EURJPY" not in instruments  # Bot deshabilitado excluido
```

## Integración con Otros Módulos

### ✅ ConfigLoader (T44)
- **Base fundamental**: GlobalConfigManager usa ConfigLoader internamente
- **Carga de archivos**: Delega en ConfigLoader para JSON parsing
- **Validación**: Usa métodos de validación de ConfigLoader

### ✅ CycleScheduler (T01)
- **Uso**: CycleScheduler usa get_all_instruments() para iterar símbolos
- **Bots habilitados**: Solo procesa bots retornados por list_enabled_bots()

### 🔄 Próximas Integraciones
- **BotInstance (T03)**: Cada instancia carga su configuración
- **Iteración Determinista (T22)**: Usa get_all_instruments() para procesar
- **FilterManager (T02)**: Accede a trading_window desde configuración

## Decisiones de Diseño

### 1. **Configuración Centralizada en settings.json**
**Decisión**: Mantener lista de activos en settings.json, no en archivo separado  
**Razón**:
- Simplicidad: Todo en un lugar
- Consistencia: Configuración de bot completa en una sección
- Mantenibilidad: Menos archivos que gestionar

### 2. **enabled Flag por Bot**
**Decisión**: Habilitar/deshabilitar a nivel de bot, no de instrumento  
**Razón**:
- Granularidad apropiada: Control a nivel de estrategia
- Simplicidad: Un flag vs múltiples flags
- Uso común: Normalmente se habilita/deshabilita bot completo

### 3. **get_all_instruments() Sin Duplicados**
**Decisión**: Retornar lista única aunque múltiples bots operen mismo símbolo  
**Razón**:
- Caso de uso: Cargar datos de mercado (una vez por símbolo)
- Eficiencia: Evitar cargas duplicadas
- Claridad: Set semántico (colección única)

### 4. **reload_config() Manual**
**Decisión**: No recarga automática, requiere llamada explícita  
**Razón**:
- Control: Operador decide cuándo aplicar cambios
- Seguridad: Evita cambios inesperados durante operación
- Testing: Más fácil de testear comportamiento

### 5. **Ordenamiento Alfabético**
**Decisión**: Retornar listas ordenadas alfabéticamente  
**Razón**:
- Determinismo: Orden predecible (importante para T22)
- Debugging: Más fácil verificar visualmente
- Consistencia: Mismo orden en todos los ciclos

### 6. **Notación de Punto para Acceso**
**Decisión**: Usar "bots.bot_1.instruments" en lugar de ["bots"]["bot_1"]["instruments"]  
**Razón**:
- Legibilidad: Más fácil de leer
- Compacto: Menos caracteres
- Validación: Delegada a ConfigLoader

## Beneficios

### 🎯 Gestión Operacional Ágil
- Cambios de activos sin código ni despliegue
- Respuesta rápida a condiciones de mercado
- Testing de nuevos símbolos simplificado

### 🔒 Separación de Configuración y Código
- Cambios en JSON, no en .py
- Menos riesgo de introducir bugs
- Configuración versionable (Git)

### 📊 Multi-Bot Facilitado
- Cada bot con sus propios símbolos
- Independencia operacional
- Escalabilidad horizontal

### 🧪 Testing y Staging
- Diferentes configuraciones por entorno
- Testing con pocos símbolos (demo)
- Producción con portafolio completo

### 🔧 Recarga en Caliente
- Aplicar cambios sin reiniciar sistema
- Mínima interrupción de servicio
- Cambios auditables (logs)

## Línea de Tiempo

| Fecha | Hora | Actividad | Estado |
|-------|------|-----------|--------|
| 2025-11-11 | 09:00 | Diseño de estructura de configuración | ✅ |
| 2025-11-11 | 09:30 | Implementación en GlobalConfigManager | ✅ |
| 2025-11-11 | 10:00 | Tests de administración de activos | ✅ |
| 2025-11-11 | 10:30 | Validación con múltiples bots | ✅ |
| 2025-11-11 | 11:00 | Documentación inline | ✅ |

**Tiempo total**: ~2 horas (como parte de T05)

## Comandos Útiles

```powershell
# Ejecutar tests de GlobalConfigManager
python -m pytest tests/unit/test_global_config_manager.py -v

# Ejecutar solo tests de instrumentos
python -m pytest tests/unit/test_global_config_manager.py -k "instruments" -v

# Uso interactivo
python -c "
from src.core.global_config_manager import GlobalConfigManager
manager = GlobalConfigManager('config')
print('Bots habilitados:', manager.list_enabled_bots())
print('Instrumentos:', manager.get_all_instruments())
"

# Validar configuración
python -c "
from src.core.global_config_manager import GlobalConfigManager
try:
    manager = GlobalConfigManager('config')
    manager.validate_required_keys(['bots.bot_1.instruments'])
    print('✓ Configuración válida')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## Dependencias

### Runtime
- **Python 3.9+**
- **Módulos estándar**: `pathlib`, `typing`

### Módulos Internos
- `src.core.config_loader` (T44)

### Testing
- `pytest >= 8.0`
- `tempfile` (estándar)

## Archivos Relacionados

```
src/core/global_config_manager.py           (Implementación)
tests/unit/test_global_config_manager.py    (Tests)
config/settings.example.json                (Ejemplo de configuración)
context/DOCUMENTACION/T20_administracion_activos.md  (Este archivo)
```

## Ejemplo de Configuración Completa

### config/settings.json
```json
{
  "timezone": "America/Lima",
  "trading_window": {
    "start": "06:00",
    "end": "13:00",
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
  },
  "bots": {
    "bot_1": {
      "enabled": true,
      "name": "Conservative EURUSD",
      "instruments": ["EURUSD", "GBPUSD"],
      "timeframe": "H1",
      "ia_config_id": 0,
      "risk_percentage": 1.5
    },
    "bot_2": {
      "enabled": true,
      "name": "Aggressive Multi-Pair",
      "instruments": ["USDJPY", "AUDUSD", "NZDUSD"],
      "timeframe": "H4",
      "ia_config_id": 1,
      "risk_percentage": 3.0
    },
    "bot_3": {
      "enabled": false,
      "name": "Experimental JPY Pairs",
      "instruments": ["EURJPY", "GBPJPY"],
      "timeframe": "D1",
      "ia_config_id": 2,
      "risk_percentage": 2.0,
      "comment": "Deshabilitado - En testing"
    }
  }
}
```

## Métricas

| Métrica | Valor |
|---------|-------|
| **Métodos relacionados con activos** | 3 |
| **Tests de administración de activos** | 7 |
| **Archivos de configuración** | 3 (settings, schedule, credentials) |
| **Bots máximo probados** | 5 |
| **Símbolos máximo probados** | 10+ |

## Conclusión

✅ **T20 completado exitosamente** como parte de GlobalConfigManager (T05):
- Administración flexible de activos por bot
- Habilitación/deshabilitación dinámica de bots
- Lista única de todos los instrumentos del sistema
- Recarga en caliente sin reiniciar aplicación
- Validación de configuración robusta
- Tests completos con múltiples escenarios

**Beneficios Clave:**
- ✅ Cambios de activos sin código
- ✅ Gestión operacional ágil
- ✅ Multi-bot independiente
- ✅ Testing facilitado
- ✅ Recarga en caliente

**Próximos Pasos Habilitados:**
- T22: Iteración determinista de activos
- T03: Instancias independientes por bot
- T01: Ciclo de ejecución con múltiples símbolos

---

**Autor**: Sistema Botrading  
**Fecha**: 2025-11-11  
**Ticket**: T20 - Administración de lista de activos en configuración  
**Issue**: #36  
**Parte de**: T05 (GlobalConfigManager)  
**Tests**: Cubierto en test_global_config_manager.py ✅
