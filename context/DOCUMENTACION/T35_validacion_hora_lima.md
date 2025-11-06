# T35: Validación de Hora Local de Lima y Días Hábiles

## Estado
✅ **COMPLETADO** (2025-11-06)

## Resumen Ejecutivo
Implementación de validador de tiempo para operaciones de trading en horario de Lima (UTC-5), con soporte para horarios configurables y **buffer de tiempo para respuesta de IA**. El sistema valida días hábiles, horarios, feriados y asegura que no se inicien operaciones demasiado cerca del cierre del mercado.

## Problema Identificado
Durante la discusión con el usuario, se identificó un **problema crítico**: 
> "muchas veces, la consulta de la IA demora 1 o 2 minutos, y si colocas que solo se opera hasta las 13 horas, la ultima respuesta ya no tiene validez"

**Solución**: Buffer configurable de tiempo antes del cierre del mercado. Si el cierre es a las 13:00 y el buffer es de 3 minutos, la última operación válida puede iniciar a las 12:57.

## Arquitectura

### Componentes Principales

#### 1. **TimeValidator** (`src/core/time_validator.py`)
Clase principal que valida condiciones de trading:

```python
from src.core.time_validator import TimeValidator

# Inicializar con configuración
validator = TimeValidator(config_file="config/schedule.json")

# Validación completa
result = validator.is_trading_time()
if result.is_valid:
    print("✅ Operación permitida")
else:
    print(f"❌ {result.reason}")

# Métodos disponibles
validator.is_business_day()           # Lun-Vie, excluye feriados
validator.is_within_trading_hours()   # 06:00-13:00 (ajustable)
validator.get_minutes_until_close()   # Tiempo restante
validator.get_next_trading_session()  # Próxima sesión
validator.get_trading_status_summary() # Resumen completo
```

#### 2. **ValidationResult** (Dataclass)
Resultado estructurado de validaciones:

```python
@dataclass
class ValidationResult:
    is_valid: bool              # True/False
    reason: Optional[str]       # Explicación del resultado
    timestamp: Optional[datetime] # Momento de validación
    
    def __bool__(self) -> bool:  # Permite: if result:
        return self.is_valid
```

#### 3. **TimeValidationError** (Exception)
Excepción personalizada para errores de configuración.

### Configuración JSON

**Archivo**: `config/schedule.json` (ejemplo en `config/schedule.example.json`)

```json
{
  "trading_schedule": {
    "timezone": "America/Lima",
    "trading_hours": {
      "start_time": "06:00",
      "end_time": "13:00",
      "ia_response_buffer_minutes": 3
    },
    "business_days": {
      "enabled": [1, 2, 3, 4, 5]
    },
    "holidays": {
      "enabled": true,
      "dates": ["2025-12-25", "2025-01-01", "2025-07-28"]
    }
  },
  "validation_rules": {
    "strict_mode": true,
    "log_rejections": true
  }
}
```

### Buffer de IA: Lógica de Implementación

**Escenario sin buffer:**
```
Hora actual: 12:58
Cierre: 13:00
Sistema: ✅ OK (está antes del cierre)
IA demora: 2 minutos
Respuesta llega: 13:00 → ❌ Mercado cerrado, operación inválida
```

**Escenario con buffer de 3 minutos:**
```
Hora actual: 12:58
Cierre efectivo: 13:00 - 3 min = 12:57
Sistema: ❌ RECHAZADO (dentro del buffer)
Razón: "Menos de 3 minutos antes del cierre"
```

**Código:**
```python
def is_within_trading_hours(self, check_time=None, consider_ia_buffer=False):
    if consider_ia_buffer:
        # Restar buffer al tiempo de cierre
        end_datetime = datetime.combine(date.today(), self.end_time)
        buffered_end = end_datetime - timedelta(minutes=self.ia_buffer_minutes)
        effective_end_time = buffered_end.time()
    
    return self.start_time <= current_time < effective_end_time
```

## Características Implementadas

### ✅ Validación de Timezone
- Zona horaria: **America/Lima (UTC-5)**
- Soporte para `zoneinfo.ZoneInfo`
- Conversión automática desde UTC

### ✅ Días Hábiles
- Por defecto: Lunes a Viernes (1-5)
- Configurable: Puede ajustarse a otros días
- Exclusión de fines de semana

### ✅ Feriados
- Lista configurable en JSON
- Formato: `YYYY-MM-DD`
- Validación automática
- Ejemplo: `["2025-12-25", "2025-01-01"]`

### ✅ Horarios de Trading
- **Configurable en runtime**
- Por defecto: 06:00 - 13:00
- Validación de rango (end_time > start_time)
- Soporte para actualización dinámica:
  ```python
  validator.update_trading_hours("08:00", "15:00")
  ```

### ✅ Buffer de IA
- Configurable: `ia_response_buffer_minutes`
- Por defecto: 3 minutos
- Ajustable en runtime:
  ```python
  validator.update_ia_buffer(5)  # 5 minutos
  ```

### ✅ Métodos Utilitarios
- `get_minutes_until_close()`: Tiempo restante
- `get_next_trading_session()`: Próxima sesión (salta fines de semana y feriados)
- `get_trading_status_summary()`: Resumen completo del estado
- `get_current_lima_time()`: Hora actual en Lima

### ✅ Recarga Dinámica de Configuración
```python
validator.reload_config("config/schedule_prod.json")
```

## Casos de Uso

### 1. Validación Básica
```python
from src.core.time_validator import TimeValidator

validator = TimeValidator()
result = validator.is_trading_time()

if result:
    # Proceder con operación
    ejecutar_trading()
else:
    logger.warning(f"Trading no permitido: {result.reason}")
```

### 2. Consultar Estado Completo
```python
status = validator.get_trading_status_summary()
print(status)
# Output:
# {
#     "current_lima_time": "2025-11-06 10:30:00",
#     "is_trading_time": true,
#     "is_business_day": true,
#     "minutes_until_close": 150,
#     "next_trading_session": "2025-11-07 06:00:00",
#     "ia_buffer_minutes": 3,
#     "effective_close_time": "12:57"
# }
```

### 3. Validación con Buffer Deshabilitado
```python
# Sin considerar buffer (útil para análisis histórico)
result = validator.is_trading_time(consider_ia_buffer=False)
```

### 4. Calcular Próxima Sesión
```python
next_session = validator.get_next_trading_session()
print(f"Próximo trading: {next_session.strftime('%Y-%m-%d %H:%M')}")
# Si es viernes 14:00 → "2025-11-10 06:00" (Lunes)
```

## Testing

### Cobertura
- **33 tests unitarios** (100% de éxito)
- **135 tests totales** del proyecto pasando
- Cobertura completa de casos edge

### Casos Testeados

#### Inicialización (6 tests)
- ✅ Configuración desde diccionario
- ✅ Configuración desde archivo JSON
- ✅ Valores por defecto
- ✅ Validación de timezone inválido
- ✅ Validación de formato de hora
- ✅ Validación end_time > start_time

#### Días Hábiles (4 tests)
- ✅ Lunes a Viernes como hábiles
- ✅ Sábado y Domingo como no hábiles
- ✅ Días hábiles personalizados
- ✅ Detección de feriados

#### Horarios de Trading (4 tests)
- ✅ Horas válidas (06:00-12:59)
- ✅ Horas inválidas (antes/después)
- ✅ Buffer de IA antes del cierre
- ✅ Buffer no afecta hora de inicio

#### Validación Completa (5 tests)
- ✅ Caso válido (día hábil + horario correcto)
- ✅ Rechazo por fin de semana
- ✅ Rechazo por fuera de horario
- ✅ Rechazo por feriado
- ✅ Rechazo por estar dentro del buffer

#### Utilidades (4 tests)
- ✅ Cálculo de minutos hasta cierre
- ✅ Minutos negativos = 0 (ya cerró)
- ✅ Próxima sesión (salta fines de semana)
- ✅ Resumen de estado completo

#### Configuración Dinámica (3 tests)
- ✅ Actualizar horarios en runtime
- ✅ Actualizar buffer de IA
- ✅ Recargar configuración desde archivo

#### Otros (7 tests)
- ✅ Obtener hora actual en Lima
- ✅ Verificar UTC-5
- ✅ ValidationResult válido/inválido
- ✅ Representación string
- ✅ Integración con logger

### Ejecución de Tests

```powershell
# Tests específicos de time_validator
pytest tests/unit/test_time_validator.py -v

# Suite completa
pytest tests/ -v

# Con cobertura (requiere pytest-cov)
pytest tests/unit/test_time_validator.py --cov=src/core/time_validator --cov-report=term-missing
```

## Integración con Otros Módulos

### ✅ Integración con ConfigLoader (T44)
```python
from src.core.config_loader import ConfigLoader
from src.core.time_validator import TimeValidator

# Cargar config general
config_loader = ConfigLoader(config_file="config/app.config.json")

# TimeValidator usa su propia config
validator = TimeValidator(config_file="config/schedule.json")

# O cargar desde config general
schedule_config = config_loader.get_config_value("trading_schedule")
validator = TimeValidator(config={"trading_schedule": schedule_config})
```

### 🔄 Integración con Logger (T39)
```python
from src.core.logger import BotLogger
from src.core.time_validator import TimeValidator

logger = BotLogger(bot_name="trading_validator")
validator = TimeValidator()

result = validator.is_trading_time()
if not result:
    logger.warning("Trading rechazado", extra={
        "reason": result.reason,
        "timestamp": result.timestamp
    })
```

## Decisiones de Diseño

### 1. **Configuración Externa vs Hardcoded**
**Decisión**: Configuración 100% externa en JSON  
**Razón**: Requerimiento del usuario de poder "cambiar sin complejidad"

### 2. **Buffer de IA**
**Decisión**: Parámetro configurable separado  
**Razón**: La IA puede tardar 1-2 minutos, necesitamos margen antes del cierre

### 3. **ValidationResult Dataclass**
**Decisión**: Estructura tipada con razón del resultado  
**Razón**: Mejor debugging y logging (saber POR QUÉ se rechazó)

### 4. **Timezone con zoneinfo**
**Decisión**: `zoneinfo.ZoneInfo` (Python 3.9+) en lugar de pytz  
**Razón**: Estándar en Python moderno, menos dependencias

### 5. **Métodos `consider_ia_buffer`**
**Decisión**: Flag opcional, True por defecto  
**Razón**: Siempre considerar buffer en producción, pero permitir deshabilitarlo para testing/análisis

## Limitaciones y Futuras Mejoras

### Limitaciones Actuales
1. **No maneja cambios de horario de verano** (Lima no tiene DST, pero podría ser necesario para otros mercados)
2. **Feriados son estáticos** (no hay integración con APIs de feriados oficiales)
3. **No soporta múltiples sesiones diarias** (ej: pre-market, regular, after-hours)

### Futuras Mejoras (Opcional)
1. **Integración con API de feriados**: Actualización automática de feriados peruanos
2. **Soporte multi-sesión**: Trading pre-market y after-hours
3. **Alertas proactivas**: Notificar X minutos antes del cierre
4. **Estadísticas**: Tracking de rechazos por tipo (feriado, horario, buffer, etc.)

## Línea de Tiempo

| Fecha | Actividad | Estado |
|-------|-----------|--------|
| 2025-11-06 10:00 | Usuario solicita T35 | ✅ |
| 2025-11-06 10:15 | Identificación de requisito de buffer IA | ✅ |
| 2025-11-06 10:30 | Creación de config/schedule.example.json | ✅ |
| 2025-11-06 10:45 | Escritura de 33 tests (TDD Red) | ✅ |
| 2025-11-06 11:15 | Implementación de TimeValidator | ✅ |
| 2025-11-06 11:30 | 33/33 tests pasando (Green) | ✅ |
| 2025-11-06 11:45 | Suite completa: 135 tests, 0 regresiones | ✅ |
| 2025-11-06 12:00 | Documentación | ✅ |

**Tiempo total**: ~2 horas

## Comandos Útiles

```powershell
# Ejecutar tests
pytest tests/unit/test_time_validator.py -v

# Ver estado del validador en runtime
python -c "from src.core.time_validator import TimeValidator; import json; v=TimeValidator(); print(json.dumps(v.get_trading_status_summary(), indent=2))"

# Copiar configuración de ejemplo
Copy-Item config/schedule.example.json config/schedule.json

# Verificar sin regresiones
pytest tests/ -v
```

## Dependencias

### Runtime
- **Python 3.9+**: `zoneinfo.ZoneInfo`
- **Módulos estándar**: `datetime`, `json`, `pathlib`, `dataclasses`

### Testing
- `pytest >= 8.0`
- `unittest.mock` (estándar)

### Integración (Opcional)
- `src.core.config_loader` (T44)
- `src.core.logger` (T39)

## Archivos Creados/Modificados

### Nuevos Archivos
```
config/schedule.example.json          (35 líneas)
src/core/time_validator.py            (692 líneas)
tests/unit/test_time_validator.py     (538 líneas)
context/DOCUMENTACION/T35_validacion_hora_lima.md  (este archivo)
```

### Archivos Modificados
```
README.md                             (stats de tests)
```

## Conclusión

✅ **T35 completado exitosamente** con todas las funcionalidades requeridas:
- Validación de hora Lima (UTC-5)
- Días hábiles configurables
- Horarios configurables
- **Buffer de IA** (requisito crítico identificado)
- Feriados configurables
- 33 tests unitarios (100%)
- 0 regresiones en suite completa (135 tests)
- Integración con módulos existentes

**Próximo ticket recomendado**: T37 (Espera por cierre de vela) - depende de T35 para validar timing de operaciones.

---

**Autor**: Sistema Botrading  
**Fecha**: 2025-11-06  
**Ticket**: T35 - Validación de hora local de Lima y días hábiles  
**Branch**: `feature/T35-validacion-hora-lima`
