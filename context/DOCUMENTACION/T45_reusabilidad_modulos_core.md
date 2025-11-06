# T45: Reutilización de Módulos Core

## 📋 Información General

- **Ticket**: T45
- **Título**: Reutilización de módulos core
- **Épica**: Configuración y modularidad
- **Fase**: 0 (Fundamentos)
- **Prioridad**: P0 (Crítica)
- **Estado**: ✅ Completado
- **Fecha**: 6 de noviembre de 2025

## 🎯 Objetivo

Establecer la arquitectura base y patrones de reutilización para todos los módulos core del sistema, garantizando consistencia, mantenibilidad y escalabilidad.

## 📖 Historia de Usuario

> Como desarrollador, quiero que los módulos core sean reutilizables por todos los bots, para acelerar implementación y reducir duplicación.

## ✅ Criterios de Aceptación

```gherkin
Escenario: Reutilización de módulos core
  Dado que los bots comparten módulos de core
  Cuando un nuevo bot requiere funcionalidad común
  Entonces puede integrarla sin duplicar código
```

## 🏗️ Arquitectura Implementada

### Clase Base: `CoreModule`

Todos los módulos core del sistema deben heredar de `CoreModule` para garantizar:

1. **Metadata consistente**: Nombre, versión, descripción
2. **Gestión de ciclo de vida**: Inicialización, shutdown, restart
3. **Validación de dependencias**: Entre módulos core
4. **Interfaz común**: Métodos estándar para todos los módulos

### Estructura de Archivos

```
src/core/
├── __init__.py
├── core_module.py       # Clase base (NUEVO)
├── config_loader.py     # Hereda de CoreModule (FUTURO)
└── logger.py            # Hereda de CoreModule (FUTURO)
```

## 📝 Implementación

### 1. ModuleMetadata (Dataclass)

Almacena información inmutable del módulo:

```python
@dataclass(frozen=True)
class ModuleMetadata:
    name: str
    version: str
    description: str
    initialized_at: datetime
```

**Características:**
- **Inmutable**: Usando `frozen=True`
- **Timestamp automático**: Registra cuándo fue inicializado
- **Serializable**: Método `to_dict()` para logging/persistencia

### 2. CoreModule (Clase Base)

Clase abstracta que todos los módulos core heredan:

```python
class CoreModule:
    def __init__(self, name, version, description, dependencies):
        # Validación obligatoria
        # Inicialización de metadata
        # Gestión de dependencias
```

**Propiedades (read-only):**
- `name`: Nombre único del módulo
- `version`: Versión semántica (ej: "1.0.0")
- `description`: Descripción breve
- `dependencies`: Lista de módulos requeridos
- `metadata`: Objeto ModuleMetadata inmutable

**Métodos principales:**

| Método | Descripción | Retorno |
|--------|-------------|---------|
| `is_initialized()` | Verifica si está inicializado | `bool` |
| `get_info()` | Info completa del módulo | `dict` |
| `shutdown()` | Apaga y libera recursos | `None` |
| `restart()` | Reinicia el módulo | `None` |
| `validate_dependencies()` | Valida módulos requeridos | `bool` |

### 3. Patrón de Herencia

Ejemplo de cómo un módulo core debe heredar:

```python
from src.core.core_module import CoreModule

class CustomModule(CoreModule):
    def __init__(self, config_param: str):
        super().__init__(
            name="CustomModule",
            version="1.0.0",
            description="Mi módulo personalizado",
            dependencies=["config_loader", "logger"]
        )
        # Inicialización específica
        self._config_param = config_param
    
    def shutdown(self):
        # Limpieza específica del módulo
        self._cleanup_resources()
        # Llamar al método base
        super().shutdown()
```

## 🧪 Tests Implementados

### Cobertura: 98%

**17 tests unitarios** que validan:

#### Inicialización y Validación
1. ✅ Inicialización correcta con metadata
2. ✅ Requiere nombre obligatorio
3. ✅ Requiere versión obligatoria
4. ✅ Descripción por defecto si no se provee

#### Información y Estado
5. ✅ `get_info()` retorna información completa
6. ✅ `is_initialized()` retorna estado correcto
7. ✅ `__str__()` representación legible

#### Ciclo de Vida
8. ✅ `shutdown()` marca como no inicializado
9. ✅ `restart()` reinicializa el módulo

#### Herencia y Reutilización
10. ✅ Puede ser heredado correctamente
11. ✅ Subclases mantienen funcionalidad base

#### Dependencias
12. ✅ Declaración de dependencias
13. ✅ Validación exitosa cuando están disponibles
14. ✅ Validación falla cuando faltan dependencias

#### Metadata
15. ✅ ModuleMetadata se inicializa correctamente
16. ✅ `to_dict()` retorna toda la información
17. ✅ Metadata es inmutable (frozen)

### Comando de Ejecución

```bash
pytest tests/unit/test_core_module.py -v --cov=src.core.core_module
```

**Resultado:**
```
17 passed in 0.36s
Coverage: 98%
Missing: línea 223 (código de ejemplo en docstring)
```

## 📚 Convenciones Establecidas

### 1. Naming Convention

- **Módulos**: `snake_case` (ej: `config_loader.py`)
- **Clases**: `PascalCase` (ej: `CoreModule`, `BotLogger`)
- **Funciones/Métodos**: `snake_case` (ej: `get_info()`)
- **Constantes**: `UPPER_SNAKE_CASE` (ej: `MAX_RETRIES`)

### 2. Versionado Semántico

Formato: `MAJOR.MINOR.PATCH`

- **MAJOR**: Cambios incompatibles con versiones anteriores
- **MINOR**: Nueva funcionalidad compatible
- **PATCH**: Correcciones de bugs

### 3. Estructura de Documentación

Cada módulo core debe incluir:

```python
"""
Breve descripción del módulo.

Descripción detallada con:
- Propósito del módulo
- Funcionalidad principal
- Dependencias

Example:
    Ejemplo de uso básico
"""
```

### 4. Gestión de Dependencias

Declarar explícitamente en `__init__`:

```python
super().__init__(
    name="MyModule",
    version="1.0.0",
    dependencies=["config_loader", "logger"]
)
```

Validar antes de usar:

```python
available = {"config_loader": config, "logger": log}
self.validate_dependencies(available)
```

### 5. Ciclo de Vida

**Inicialización:**
- Constructor debe llamar a `super().__init__()`
- Inicializar atributos privados con `_`
- No realizar operaciones pesadas en `__init__`

**Shutdown:**
- Liberar recursos (archivos, conexiones)
- Llamar a `super().shutdown()` al final
- Marcar estado interno como no inicializado

**Restart:**
- Limpiar estado anterior
- Reinicializar recursos
- Llamar a `super().restart()` al final

## 🔄 Beneficios de la Arquitectura

### 1. Consistencia
✅ Todos los módulos tienen la misma interfaz base
✅ Metadata estandarizada
✅ Patrón predecible de uso

### 2. Reutilización
✅ Código compartido en clase base
✅ No duplicación de lógica común
✅ Fácil integración en nuevos bots

### 3. Mantenibilidad
✅ Cambios en un solo lugar
✅ Tests centralizados
✅ Documentación estandarizada

### 4. Escalabilidad
✅ Fácil agregar nuevos módulos
✅ Gestión clara de dependencias
✅ Ciclo de vida bien definido

### 5. Testabilidad
✅ Interfaz común para mocks
✅ Validación de dependencias
✅ Estado verificable

## 🔮 Próximos Pasos

### Fase 1: Migración de Módulos Existentes

1. **config_loader**: Heredar de `CoreModule`
2. **logger**: Heredar de `CoreModule`
3. Actualizar tests para validar herencia

### Fase 2: Nuevos Módulos Core

Siguiendo el patrón establecido, implementar:

- **mt5_connector**: Integración con MetaTrader 5
- **ai_client**: Cliente para Gemini AI
- **magic_number**: Generación y decodificación
- **risk_manager**: Cálculo de lotes y riesgo

### Fase 3: Orquestación

Implementar `ModuleRegistry` para:
- Registro centralizado de módulos
- Resolución automática de dependencias
- Inicialización en orden correcto
- Health checks de módulos

## 📊 Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| Tests | 17 | >10 | ✅ |
| Cobertura | 98% | >90% | ✅ |
| Tests Pasando | 17/17 (100%) | 100% | ✅ |
| Tiempo Ejecución | 0.36s | <1s | ✅ |
| Líneas de Código | 228 | N/A | ✅ |
| Complejidad Ciclomática | Baja | Baja | ✅ |

## 🎓 Lecciones Aprendidas

### 1. Inmutabilidad
El uso de `@dataclass(frozen=True)` para `ModuleMetadata` previene modificaciones accidentales y hace el código más seguro.

### 2. Properties vs Atributos
Usar properties con `@property` en lugar de atributos públicos permite:
- Validación en el futuro
- Control de acceso
- Compatibilidad con cambios internos

### 3. Validación Temprana
Validar `name` y `version` en el constructor previene errores sutiles más adelante.

### 4. Documentación Clara
Docstrings detallados facilitan el uso correcto de la clase base por otros desarrolladores.

### 5. TDD para Arquitectura
Escribir tests primero ayudó a definir la API pública de manera natural y usable.

## 🔗 Referencias

- **Repositorio**: [DVARGAS117/Botrading](https://github.com/DVARGAS117/Botrading)
- **Issue GitHub**: #56 (T45)
- **Branch**: `feature/T45-reusabilidad-modulos-core`
- **Módulo principal**: `src/core/core_module.py`
- **Tests**: `tests/unit/test_core_module.py`

## 📝 Conclusión

El T45 establece la **base arquitectónica** para todo el sistema Botrading. La clase `CoreModule` proporciona:

✅ **Interfaz consistente** para todos los módulos core
✅ **Gestión estandarizada** del ciclo de vida
✅ **Validación robusta** de dependencias
✅ **Alta testabilidad** y mantenibilidad
✅ **Escalabilidad** para futuros módulos

Esta implementación garantiza que cualquier nuevo módulo core pueda integrarse fácilmente, siguiendo patrones probados y con calidad asegurada mediante tests automatizados.

---

**Implementado por**: GitHub Copilot + TDD
**Fecha de finalización**: 6 de noviembre de 2025
**Resultado**: ✅ 17/17 tests pasando, 98% coverage
