# Trading Sessions - Sistema de Horarios Dinámicos por Símbolo

## Fecha
2025-01-19

## Estado
✅ **IMPLEMENTADO Y TESTEADO**

## Descripción

Sistema que controla qué símbolos pueden ser consultados a la IA según el horario actual, optimizando costos de API y respetando horarios de mejor liquidez para cada par.

## Componentes Implementados

### 1. TradingSessionManager (`src/core/trading_session_manager.py`)

Clase principal que gestiona las sesiones de trading:

**Métodos principales:**
- `is_symbol_tradeable(symbol, current_time, has_open_position)`: Verifica si se puede consultar
- `get_active_session(symbol, time)`: Obtiene sesión activa
- `get_next_session(symbol, time)`: Obtiene próxima sesión disponible
- `get_active_symbols(current_time)`: Lista símbolos operables en el momento
- `get_current_session_info(symbol, time)`: Info completa de sesión

**Características:**
- Maneja sesiones que cruzan medianoche (ej: 22:00-02:00)
- Soporte para reevaluación fuera de horario si hay posición abierta
- Configuración JSON flexible
- Fallback graceful si no existe config

### 2. Configuración de Sesiones

**Archivos:**
- `config/trading_sessions.json`: Config de producción
- `config/trading_sessions.example.json`: Template con documentación

**Estructura JSON:**
```json
{
  "sessions": {
    "nombre_sesion": {
      "start": "HH:MM",
      "end": "HH:MM",
      "symbols": ["EURUSD", "GBPUSD"],
      "strategies": ["A_tendencia", "B_rango"],
      "risk_level": "alto"
    }
  },
  "global_rules": {
    "allow_reevaluation_outside_hours": true
  }
}
```

**Sesiones Configuradas:**

| Sesión | Horario | Símbolos | Risk Level | Observaciones |
|--------|---------|----------|------------|---------------|
| **londres** | 02:00-05:00 | EURUSD, GBPUSD, EURGBP | medio | Sesión europea temprana |
| **ny_londres_overlap** | 08:00-11:00 | EURUSD, GBPUSD, USDCAD, USDCHF | **alto** | ⭐ MÁXIMA PRIORIDAD - Mayor liquidez |
| **ny_tarde** | 11:00-13:00 | EURUSD, USDCAD | medio | Continuación NY |
| **dead_zone** | 13:00-18:00 | *(ninguno)* | ninguno | ⛔ NO OPERAR - Baja liquidez |
| **asia** | 19:00-23:59 | USDJPY, AUDUSD, NZDUSD | bajo | Sesión asiática |
| **asia_madrugada** | 00:00-02:00 | USDJPY, AUDUSD, NZDUSD | bajo | Continuación Asia |

### 3. Integración en BaseBotOperations

**Archivo:** `src/bots/base/base_bot_operations.py`

**Cambios:**

1. **Import agregado:**
```python
from src.core.trading_session_manager import TradingSessionManager
```

2. **Inicialización en `__init__`:**
```python
self.session_manager: Optional[TradingSessionManager] = None
```

3. **Setup en `initialize()`:**
```python
# 9. Trading Session Manager
try:
    self.session_manager = TradingSessionManager()
    self.logger.info("✅ TradingSessionManager inicializado")
except Exception as se:
    self.logger.warning(
        f"No se pudo cargar TradingSessionManager: {se}. "
        "Se permitirá trading en cualquier horario."
    )
```

4. **Nuevo método `_should_query_symbol()`:**
```python
def _should_query_symbol(self, symbol: str) -> Tuple[bool, str]:
    """
    Determina si se debe consultar a la IA para un símbolo.
    
    Verifica:
    - Horario de trading según sessions.json
    - Si tiene posición abierta (permite reevaluación)
    
    Returns:
        (debe_consultar, mensaje_info)
    """
```

5. **Modificación en `run_trading_cycle()`:**
```python
for symbol in self.config.symbols:
    # 3a. Verificar si el símbolo puede operarse en el horario actual
    should_query_ai, session_info = self._should_query_symbol(symbol)
    
    if not should_query_ai:
        self.logger.info(f"⏰ {symbol} fuera de horario. {session_info}")
        continue
    
    # Log información de sesión activa
    if "Sesión activa:" in session_info:
        self.logger.info(f"✅ {symbol} en horario permitido. {session_info}")
    
    # ... resto del flujo (extraer datos, consultar IA, etc.)
```

## Lógica de Validación

### Flujo de Decisión

```
┌─────────────────────────────────────┐
│  Bot consulta: ¿Operar EURUSD?     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  SessionManager verifica horario    │
└──────────────┬──────────────────────┘
               │
               ▼
         ¿Hora actual?
               │
    ┌──────────┼──────────┐
    │          │          │
09:00      14:00      20:00
    │          │          │
    ▼          ▼          ▼
NY+Londres  dead_zone   (No config)
    │          │          │
    ▼          ▼          ▼
 ✅ SÍ     ¿Posición?   ❌ NO
            │
    ┌───────┴───────┐
    │               │
   SÍ              NO
    │               │
    ▼               ▼
✅ REEVALUAR    ❌ SKIP
```

### Casos de Uso

**Caso 1: Símbolo en horario permitido**
- Input: EURUSD, 09:00, sin posición
- Output: ✅ `(True, "Sesión activa: ny_londres_overlap")`
- Acción: **Consultar IA normalmente**

**Caso 2: Símbolo fuera de horario, sin posición**
- Input: EURUSD, 14:00, sin posición
- Output: ❌ `(False, "No hay sesiones configuradas para EURUSD")`
- Acción: **Skip, no consultar IA** (ahorro de $$$)

**Caso 3: Símbolo fuera de horario, CON posición abierta**
- Input: EURUSD, 14:00, con posición
- Output: ✅ `(True, "Fuera de horario pero tiene posición abierta (reevaluación permitida)")`
- Acción: **Consultar IA para reevaluación** (cerrar posición si es necesario)

**Caso 4: Dead Zone**
- Input: CUALQUIER_SIMBOLO, 15:00
- Output: ❌ `(False, "No hay sesiones configuradas para X")`
- Acción: **Skip** (excepto reevaluación de posiciones abiertas)

## Tests

### Tests Unitarios
**Archivo:** `tests/core/test_trading_session_manager.py`

Cobertura:
- ✅ Inicialización con config válida/inválida
- ✅ Verificación de símbolos en diferentes horarios
- ✅ Sesiones que cruzan medianoche
- ✅ Reevaluación fuera de horario
- ✅ Dead zone (ningún símbolo permitido)
- ✅ Próxima sesión disponible
- ✅ Símbolos activos por horario
- ✅ Parseo de tiempos
- ✅ Información completa de sesión

### Tests Manuales
**Archivo:** `test_sessions_manual.py`

Ejecuta 8 escenarios reales con output detallado.

**Resultado:**
```
✅ EURUSD 09:00: Permitido (ny_londres_overlap)
❌ EURUSD 14:00 SIN posición: Bloqueado
✅ EURUSD 14:00 CON posición: Reevaluación permitida
✅ USDJPY 20:00: Permitido (asia)
✅ Símbolos activos 09:00: EURUSD, GBPUSD, USDCAD, USDCHF
❌ Símbolos activos 15:00: NINGUNO (dead_zone)
```

## Beneficios

### 1. Optimización de Costos
- **Antes:** Consulta IA en cualquier horario → más llamadas a API
- **Ahora:** Consulta solo en horarios óptimos → **ahorro de $$$ en Gemini API**

### 2. Mejor Calidad de Señales
- Trading solo en horarios de alta liquidez
- Evita rangos con spreads amplios (dead_zone)
- Respeta características de cada par (USDJPY en Asia, EURUSD en NY+Londres)

### 3. Control de Riesgo
- Nivel de riesgo por sesión: alto/medio/bajo
- Permite ajustar lot size según sesión
- Estrategias específicas por sesión

### 4. Flexibilidad
- Configuración JSON fácil de modificar
- Agregar/quitar sesiones sin cambiar código
- Fallback graceful si no hay config

### 5. Logging Claro
```
09:00 ✅ EURUSD en horario permitido. Sesión activa: ny_londres_overlap
14:00 ⏰ EURUSD fuera de horario. No hay sesiones configuradas para EURUSD
14:00 ✅ EURUSD en horario permitido. Fuera de horario pero tiene posición abierta (reevaluación permitida)
```

## Uso

### Para el Usuario (Configuración)

1. **Editar horarios:** Modificar `config/trading_sessions.json`
2. **Agregar símbolos a sesión:**
   ```json
   "ny_londres_overlap": {
       "symbols": ["EURUSD", "GBPUSD", "NUEVO_SIMBOLO"]
   }
   ```
3. **Crear nueva sesión:**
   ```json
   "nueva_sesion": {
       "start": "12:00",
       "end": "15:00",
       "symbols": ["XAUUSD"],
       "strategies": ["A_tendencia"],
       "risk_level": "alto"
   }
   ```

### Para el Desarrollador (Integración)

El sistema ya está integrado en `BaseBotOperations`, por lo que **todos los bots** (numérico, visual, híbrido, VWAP, INTRADAY) heredan automáticamente esta funcionalidad.

**No se requiere cambio de código en bots individuales.**

## Próximos Pasos (Opcionales)

### Mejoras Futuras Posibles

1. **Timezone dinámico:**
   - Actualmente: horarios en hora local (America/Lima)
   - Mejora: Permitir timezone configurable en JSON

2. **Ajuste dinámico de lot size:**
   - Leer `risk_level` de sesión
   - Aumentar lots en sesiones "alto", reducir en "bajo"

3. **Estrategias por sesión:**
   - Campo `strategies` ya existe en config
   - Filtrar estrategias según sesión activa

4. **Holidays:**
   - Agregar lista de días festivos donde no operar
   - Verificar en `is_symbol_tradeable()`

5. **Backtesting con horarios:**
   - Al hacer backtest, respetar sesiones históricas
   - Evaluar impacto de horarios en performance

## Estado de Implementación

| Componente | Estado | Tests |
|------------|--------|-------|
| TradingSessionManager | ✅ Completo | ✅ 8 escenarios |
| Config JSON | ✅ Creado | ✅ Validado |
| Integración BaseBotOperations | ✅ Completo | ✅ Funcional |
| Logging | ✅ Completo | ✅ Output claro |
| Manejo de errores | ✅ Completo | ✅ Fallback graceful |
| Documentación | ✅ Completo | ✅ Este archivo |

## Conclusión

Sistema de sesiones de trading implementado y operativo. Controla inteligentemente cuándo consultar a la IA según horarios óptimos por símbolo, con soporte para reevaluación de posiciones abiertas fuera de horario.

**Próximo paso del usuario:** Escribir los prompts (Step 1 del documento INTRADAY).

---

**Autor:** Sistema Botrading  
**Fecha:** 2025-01-19  
**Versión:** 1.0
