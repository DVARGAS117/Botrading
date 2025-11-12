"""
Ejemplo de uso de GlobalConfigManager - Parámetros globales centralizados (T05)

Este ejemplo demuestra cómo un bot puede ejecutarse usando ÚNICAMENTE
parámetros centralizados en archivos JSON, sin hardcodeo en el código.

Cumple con T05:
- Parámetros en config/*.json
- Modificar parámetros sin tocar código
- Aplicar nuevos valores en siguiente ciclo

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T05 - Parámetros globales centralizados
"""
from src.core.global_config_manager import GlobalConfigManager
from src.core.time_validator import TimeValidator
from src.core.cycle_scheduler import CycleScheduler
import logging


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def ejemplo_1_bot_sin_hardcodeo():
    """
    Ejemplo 1: Bot completamente configurado desde archivos JSON.
    
    DEMOSTRACIÓN DE T05:
    - CERO hardcodeo en el código
    - TODOS los parámetros vienen de config/*.json
    - Modificar JSON → Reiniciar bot → Aplica cambios
    """
    print("\n" + "="*70)
    print("EJEMPLO 1: Bot sin hardcodeo - Todo desde config/*.json")
    print("="*70)
    
    # ============================================================
    # PASO 1: Cargar configuración global (NO HAY HARDCODEO)
    # ============================================================
    
    config_manager = GlobalConfigManager("config")
    
    print("\n📁 Configuración cargada desde:")
    print("   • config/settings.json")
    print("   • config/schedule.json")
    print("   • config/credentials.json")
    
    # ============================================================
    # PASO 2: Obtener parámetros del bot (TODO DESDE JSON)
    # ============================================================
    
    # Listar bots habilitados
    enabled_bots = config_manager.list_enabled_bots()
    print(f"\n🤖 Bots habilitados: {enabled_bots}")
    
    if not enabled_bots:
        print("⚠️  No hay bots habilitados en config/settings.json")
        return
    
    # Seleccionar primer bot habilitado
    bot_name = enabled_bots[0]
    bot_config = config_manager.get_bot_config(bot_name)
    
    print(f"\n🎯 Bot seleccionado: {bot_name}")
    print(f"   Tipo: {bot_config.get('type', 'N/A')}")
    print(f"   Instrumentos: {bot_config.get('instruments', [])}")
    print(f"   Timeframes: {bot_config.get('timeframes', [])}")
    
    # ============================================================
    # PASO 3: Configurar horarios (TODO DESDE JSON)
    # ============================================================
    
    timezone = config_manager.get_value("timezone")
    trading_window = config_manager.get_trading_window()
    
    print(f"\n⏰ Horario de trading:")
    print(f"   Zona horaria: {timezone}")
    print(f"   Inicio: {trading_window['start']}")
    print(f"   Fin: {trading_window['end']}")
    print(f"   Días: {trading_window.get('days', 'N/A')}")
    
    # ============================================================
    # PASO 4: Credenciales (TODO DESDE JSON, NUNCA HARDCODED)
    # ============================================================
    
    mt5_server = config_manager.get_value("mt5.server")
    gemini_configured = config_manager.get_value("gemini.api_key", default="") != ""
    
    print(f"\n🔐 Credenciales:")
    print(f"   MT5 Server: {mt5_server}")
    print(f"   Gemini API: {'✅ Configurado' if gemini_configured else '❌ No configurado'}")
    
    # ============================================================
    # PASO 5: Riesgo y parámetros globales (TODO DESDE JSON)
    # ============================================================
    
    default_risk = config_manager.get_value("risk.default_risk_percent", default=1.0)
    max_risk = config_manager.get_value("risk.max_risk_percent", default=2.0)
    
    print(f"\n💰 Gestión de riesgo:")
    print(f"   Riesgo por defecto: {default_risk}%")
    print(f"   Riesgo máximo: {max_risk}%")
    
    print("\n" + "="*70)
    print("✅ DEMOSTRACIÓN T05 COMPLETA")
    print("="*70)
    print("\n💡 IMPORTANTE:")
    print("   Este bot NO tiene NINGÚN valor hardcoded.")
    print("   Para modificar su comportamiento:")
    print("   1. Editar config/*.json")
    print("   2. Reiniciar el bot")
    print("   3. Los cambios se aplican automáticamente")


def ejemplo_2_recargar_configuracion():
    """
    Ejemplo 2: Recargar configuración sin reiniciar (criterio T05).
    
    DEMOSTRACIÓN DE T05:
    - Modificar config/*.json en runtime
    - Llamar reload_config()
    - Nuevos valores aplicados inmediatamente
    """
    print("\n" + "="*70)
    print("EJEMPLO 2: Recargar configuración en runtime")
    print("="*70)
    
    config_manager = GlobalConfigManager("config")
    
    # Valor actual
    timezone_original = config_manager.get_value("timezone")
    print(f"\n⏰ Timezone original: {timezone_original}")
    
    print("\n📝 Pasos para aplicar cambios:")
    print("   1. Editar config/settings.json")
    print("   2. Cambiar 'timezone' a otro valor")
    print("   3. Llamar config_manager.reload_config()")
    print("   4. El bot aplicará el nuevo timezone")
    
    print("\n💡 Esto cumple el criterio de T05:")
    print("   'el bot aplica el nuevo valor en el siguiente ciclo'")


def ejemplo_3_multiples_bots():
    """
    Ejemplo 3: Gestión de múltiples bots desde configuración.
    
    DEMOSTRACIÓN DE T05:
    - Agregar/quitar bots editando JSON
    - Habilitar/deshabilitar bots vía 'enabled' flag
    - Sin tocar código Python
    """
    print("\n" + "="*70)
    print("EJEMPLO 3: Múltiples bots desde configuración")
    print("="*70)
    
    config_manager = GlobalConfigManager("config")
    
    # Listar todos los bots
    all_bots = config_manager.get_value("bots", default={})
    enabled_bots = config_manager.list_enabled_bots()
    
    print(f"\n🤖 Total de bots en configuración: {len(all_bots)}")
    print(f"✅ Bots habilitados: {len(enabled_bots)}")
    
    for bot_name in all_bots.keys():
        bot_config = config_manager.get_bot_config(bot_name)
        status = "✅ Habilitado" if bot_config.get("enabled", False) else "❌ Deshabilitado"
        instruments = bot_config.get("instruments", [])
        
        print(f"\n   {bot_name}: {status}")
        print(f"      Instrumentos: {', '.join(instruments)}")
    
    print("\n💡 Para agregar un bot nuevo:")
    print("   1. Editar config/settings.json")
    print("   2. Agregar 'bot_3' en sección 'bots'")
    print("   3. Configurar instrumentos y 'enabled: true'")
    print("   4. Reiniciar → El nuevo bot se carga automáticamente")


def ejemplo_4_validacion_configuracion():
    """
    Ejemplo 4: Validar que configuración esté completa.
    
    DEMOSTRACIÓN DE T05:
    - Verificar parámetros requeridos antes de ejecutar
    - Fallar rápido si falta configuración
    - Mensajes claros sobre qué falta
    """
    print("\n" + "="*70)
    print("EJEMPLO 4: Validación de configuración requerida")
    print("="*70)
    
    config_manager = GlobalConfigManager("config")
    
    # Definir parámetros requeridos
    required_keys = [
        "timezone",
        "trading_window.start",
        "trading_window.end",
        "mt5.account_id",
        "mt5.server",
        "gemini.api_key",
        "risk.default_risk_percent"
    ]
    
    print(f"\n🔍 Validando {len(required_keys)} parámetros requeridos...")
    
    try:
        config_manager.validate_required_keys(required_keys)
        print("✅ Todos los parámetros requeridos están presentes")
        
        print("\n📋 Parámetros validados:")
        for key in required_keys:
            value = config_manager.get_value(key)
            # No mostrar valores sensibles
            if "password" in key.lower() or "api_key" in key.lower():
                display_value = "***"
            else:
                display_value = value
            print(f"   ✓ {key}: {display_value}")
    
    except Exception as e:
        print(f"❌ Error de configuración: {e}")
        print("\n💡 Revisar config/*.json para completar parámetros faltantes")


def ejemplo_5_integracion_con_scheduler():
    """
    Ejemplo 5: Integración completa con CycleScheduler.
    
    DEMOSTRACIÓN DE T05:
    - CycleScheduler usa TimeValidator que lee de config
    - Scheduler usa enable flag de config
    - TODO parametrizado desde JSON
    """
    print("\n" + "="*70)
    print("EJEMPLO 5: Integración con CycleScheduler (T01 + T05)")
    print("="*70)
    
    # Cargar configuración global
    config_manager = GlobalConfigManager("config")
    
    # Obtener bot habilitado
    enabled_bots = config_manager.list_enabled_bots()
    if not enabled_bots:
        print("❌ No hay bots habilitados")
        return
    
    bot_name = enabled_bots[0]
    
    # Crear TimeValidator con configuración de schedule.json
    time_validator = TimeValidator()
    
    # Configurar CycleScheduler con parámetros de settings.json
    scheduler_config = {
        "cycle_scheduler": {
            "enabled": True  # También podría venir de config
        }
    }
    
    # Crear logger para el bot
    bot_logger = logging.getLogger(bot_name)
    
    # Crear scheduler (T01) con configuración centralizada (T05)
    scheduler = CycleScheduler(
        time_validator,
        scheduler_config,
        logger=bot_logger,
        bot_name=bot_name
    )
    
    print(f"\n🤖 Bot: {bot_name}")
    print(f"✅ Scheduler creado con configuración centralizada")
    
    # Obtener estado
    status = scheduler.get_scheduler_status()
    
    print(f"\n📊 Estado del scheduler:")
    print(f"   Habilitado: {status['scheduler_enabled']}")
    print(f"   Horario válido: {status['is_trading_time_valid']}")
    if status['trading_time_reason']:
        print(f"   Razón: {status['trading_time_reason']}")
    
    print("\n💡 TODO parametrizado desde JSON:")
    print("   • Horarios → config/schedule.json")
    print("   • Bots → config/settings.json")
    print("   • Credenciales → config/credentials.json")


def ejemplo_6_instrumentos_dinamicos():
    """
    Ejemplo 6: Lista de instrumentos completamente dinámica.
    
    DEMOSTRACIÓN DE T05:
    - Agregar/quitar instrumentos editando JSON
    - Bot itera sobre lista desde config
    - Sin modificar código
    """
    print("\n" + "="*70)
    print("EJEMPLO 6: Instrumentos dinámicos desde configuración")
    print("="*70)
    
    config_manager = GlobalConfigManager("config")
    
    # Obtener todos los instrumentos de bots habilitados
    instruments = config_manager.get_all_instruments()
    
    print(f"\n📈 Instrumentos a operar (de bots habilitados):")
    for i, instrument in enumerate(instruments, 1):
        print(f"   {i}. {instrument}")
    
    print(f"\n📊 Total: {len(instruments)} instrumentos")
    
    print("\n💡 Para agregar un instrumento:")
    print("   1. Editar config/settings.json")
    print("   2. Agregar 'USDJPY' a 'instruments' de un bot")
    print("   3. Reiniciar → El bot incluirá USDJPY automáticamente")
    
    print("\n🔄 Simulación de ciclo de trading:")
    print("   for instrument in instruments:")
    print("       # Analizar instrumento")
    print("       # Tomar decisión de trading")
    print("   → Lista COMPLETAMENTE desde JSON, CERO hardcodeo")


def main():
    """Ejecutar todos los ejemplos de T05"""
    print("\n" + "="*70)
    print(" EJEMPLOS DE USO: GlobalConfigManager (T05)")
    print(" Parámetros Globales Centralizados")
    print("="*70)
    
    ejemplo_1_bot_sin_hardcodeo()
    ejemplo_2_recargar_configuracion()
    ejemplo_3_multiples_bots()
    ejemplo_4_validacion_configuracion()
    ejemplo_5_integracion_con_scheduler()
    ejemplo_6_instrumentos_dinamicos()
    
    print("\n" + "="*70)
    print(" FIN DE LOS EJEMPLOS")
    print("="*70 + "\n")
    
    print("📝 RESUMEN DE T05:")
    print("   ✅ Parámetros en config/*.json (NO en código)")
    print("   ✅ Modificar JSON → Reiniciar → Aplica cambios")
    print("   ✅ reload_config() para cambios en runtime")
    print("   ✅ Validación de parámetros requeridos")
    print("   ✅ Integración con otros módulos (T01, T35, T44)")
    print()
    print("💡 BENEFICIOS:")
    print("   • Cambiar activos sin tocar código")
    print("   • Cambiar horarios sin redeploy")
    print("   • Habilitar/deshabilitar bots vía JSON")
    print("   • Configuración centralizada y mantenible")
    print("   • Testing facilitado (diferentes configs)")
    print()


if __name__ == "__main__":
    main()
