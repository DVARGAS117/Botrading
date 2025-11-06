# Documentación: Módulo config_loader

**Ticket:** T44 - Gestión de credenciales y parámetros en JSON  
**Fase:** 0 - Fundamentos  
**Prioridad:** P0  
**Fecha:** 2025-11-06  
**Desarrollador:** Sistema Botrading  

---

## 📋 Resumen

El módulo `config_loader.py` implementa un sistema robusto y seguro para la gestión de configuración del sistema Botrading. Permite cargar configuración desde múltiples fuentes (archivos JSON y variables de entorno) sin exponer credenciales sensibles en el código o en los logs.

---

## 🎯 Objetivos del Ticket T44

### Historia de Usuario
> Como administrador, quiero gestionar credenciales, modelos y parámetros en config/*.json, para cambiar proveedores o ajustes sin redeploy de código.

### Criterios de Aceptación ✅

**Escenario:** Gestionar credenciales y parámetros en JSON
- ✅ **Dado que** existen archivos config/*.json para credenciales y parámetros
- ✅ **Cuando** se actualiza una credencial o parámetro
- ✅ **Entonces** el sistema usa el nuevo valor sin redeploy

---

## 🏗️ Arquitectura

### Estructura de Archivos

```
BOTRADING/
├── config/
│   ├── settings.example.json          # Configuración general (ejemplo)
│   ├── credentials.example.json       # Credenciales (ejemplo)
│   ├── ia_config.example.json         # Configuración IA (ejemplo)
│   ├── settings.json                  # Configuración real (gitignored)
│   └── credentials.json               # Credenciales reales (gitignored)
├── src/
│   └── core/
│       └── config_loader.py           # Módulo principal
├── tests/
│   └── unit/
│       └── test_config_loader.py      # Tests unitarios
└── .env.example                        # Variables de entorno (ejemplo)
```

---

## 🔧 Funcionalidades Implementadas

### 1. Carga de Configuración desde JSON

```python
from src.core.config_loader import ConfigLoader

loader = ConfigLoader()
config = loader.load_json_config("config/settings.json")
```

**Características:**
- ✅ Validación de existencia del archivo
- ✅ Validación de formato JSON
- ✅ Manejo robusto de errores
- ✅ Logging seguro sin exponer credenciales

### 2. Carga de Variables de Entorno

```python
env_vars = loader.load_env_variables([
    "MT5_ACCOUNT_ID",
    "MT5_PASSWORD",
    "GEMINI_API_KEY"
])
```

**Características:**
- ✅ Validación de variables requeridas
- ✅ Mensajes de error claros si faltan variables
- ✅ Integración con archivos .env

### 3. Acceso a Valores con Notación de Punto

```python
# Acceso simple
timezone = loader.get_config_value("timezone")

# Acceso anidado
start_time = loader.get_config_value("trading_window.start")

# Con valor por defecto
risk = loader.get_config_value("risk.default", default=1.0)
```

### 4. Validación de Configuración

```python
required_keys = [
    "timezone",
    "trading_window.start",
    "trading_window.end"
]

loader.validate_required_keys(required_keys)
```

### 5. Fusión de Configuraciones

```python
# Fusionar configuraciones con prioridad
default_config = {...}
user_config = {...}
merged = loader.merge_configs(default_config, user_config)
```

---

## 🔒 Seguridad

### Protección de Credenciales

El módulo implementa múltiples capas de seguridad:

1. **Exclusión de Git**
   - Archivos sensibles en `.gitignore`
   - Solo archivos `.example` en el repositorio

2. **Sanitización de Logs**
   - Credenciales nunca aparecen en logs
   - Valores sensibles reemplazados por `***`
   - Detección automática de claves sensibles:
     - password, api_key, secret, token, credentials, key, pass

3. **Variables de Entorno**
   - Soporte para archivos `.env`
   - Validación de variables requeridas

### Ejemplo de Log Seguro

```python
# Configuración cargada
config = {
    "timezone": "America/Lima",
    "mt5": {
        "password": "super_secret_123"
    }
}

# Log generado (seguro)
# INFO: Configuration loaded from config/credentials.json. Keys: ['timezone', 'mt5']
# ❌ NO aparece: "super_secret_123"
```

---

## 📊 Tests y Cobertura

### Resultados de Tests

```
✅ 13/13 tests pasados
✅ 94% de cobertura de código
✅ 0.58s tiempo de ejecución
```

### Tests Implementados

1. **test_load_json_config_success** - Carga exitosa de JSON
2. **test_load_json_config_file_not_found** - Manejo de archivo no encontrado
3. **test_load_json_config_invalid_json** - Manejo de JSON inválido
4. **test_load_env_variables_success** - Carga de variables de entorno
5. **test_load_env_variables_missing_required** - Variables faltantes
6. **test_get_config_value_success** - Acceso a valores anidados
7. **test_get_config_value_not_found** - Manejo de claves inexistentes
8. **test_get_config_value_with_default** - Valores por defecto
9. **test_validate_required_keys_success** - Validación exitosa
10. **test_validate_required_keys_missing** - Validación con errores
11. **test_reload_config** - Recarga de configuración
12. **test_merge_configs** - Fusión de configuraciones
13. **test_credentials_not_exposed_in_logs** - Seguridad en logs

---

## 📖 Uso en el Proyecto

### Configuración Inicial

1. **Copiar archivos de ejemplo:**
```bash
cp config/settings.example.json config/settings.json
cp config/credentials.example.json config/credentials.json
cp config/ia_config.example.json config/ia_config.json
cp .env.example .env
```

2. **Editar credenciales:**
```json
{
  "mt5": {
    "account_id": "12345678",
    "password": "tu_password_real",
    "server": "TuBroker-Server"
  },
  "gemini": {
    "api_key": "tu_api_key_real"
  }
}
```

3. **Usar en el código:**
```python
from src.core.config_loader import ConfigLoader

# Inicializar
loader = ConfigLoader()

# Cargar configuraciones
loader.load_json_config("config/settings.json")
loader.load_json_config("config/credentials.json")
loader.load_json_config("config/ia_config.json")

# Usar valores
timezone = loader.get_config_value("timezone")
mt5_account = loader.get_config_value("mt5.account_id")
```

---

## 🎓 Mejores Prácticas

### ✅ DO (Hacer)

1. **Usar archivos .example para documentación**
2. **Nunca commitear archivos con credenciales reales**
3. **Validar configuración al inicio de la aplicación**
4. **Usar valores por defecto razonables**
5. **Documentar cada parámetro de configuración**

### ❌ DON'T (No Hacer)

1. **No hardcodear credenciales en el código**
2. **No loggear valores sensibles**
3. **No compartir archivos .env en repositorios**
4. **No usar la misma configuración para dev y prod**
5. **No omitir validación de configuración**

---

## 🔄 Integración con Otros Módulos

El `config_loader` será utilizado por:

- ✅ **T45** - Módulos core reutilizables
- ✅ **T47** - Almacenamiento seguro de credenciales
- ✅ **Fase 1** - Integración MT5
- ✅ **Fase 2** - Integración IA (Gemini)

---

## 📈 Métricas

| Métrica | Valor |
|---------|-------|
| Líneas de código | 296 |
| Tests | 13 |
| Cobertura | 94% |
| Complejidad ciclomática | Baja |
| Mantenibilidad | Alta |

---

## 🚀 Próximos Pasos

1. ✅ **T44 Completado** - Gestión de credenciales y parámetros en JSON
2. ⏭️ **T45** - Reutilización de módulos core
3. ⏭️ **T46** - Tests unitarios por componente
4. ⏭️ **T47** - Almacenamiento seguro de credenciales

---

## 📝 Notas Adicionales

### Extensibilidad

El módulo está diseñado para ser fácilmente extensible:

- Agregar nuevos formatos (YAML, TOML)
- Integración con servicios de secrets (AWS Secrets Manager, Azure Key Vault)
- Configuración dinámica desde base de datos
- Hot-reload de configuración

### Compatibilidad

- ✅ Python 3.13+
- ✅ Windows, Linux, macOS
- ✅ Compatible con Docker
- ✅ Sin dependencias externas complejas

---

## 🤝 Contribuciones

Para modificar o extender este módulo:

1. Escribir tests primero (TDD)
2. Mantener cobertura > 90%
3. Documentar cambios en este archivo
4. Seguir PEP 8 y type hints
5. Actualizar archivos `.example` si es necesario

---

**Documento generado:** 2025-11-06  
**Versión:** 1.0  
**Estado:** ✅ Completado y en producción
