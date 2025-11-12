"""
Ejemplos de uso del CycleScheduler - T01 y T02

Este script demuestra cómo usar el CycleScheduler para ejecutar ciclos de trading
exactamente al inicio de cada hora dentro de la ventana de trading 06:00-13:00 Lima.

T01: Ejecución de ciclo por bot a inicio de hora
T02: Aplicación de filtros de horario y días hábiles con logging

Autor: Sistema Botrading
Fecha: 2025-11-11
Tickets: T01, T02
"""

from src.core.cycle_scheduler import CycleScheduler
from src.core.time_validator import TimeValidator
import logging
from datetime import datetime


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# EJEMPLO 1: USO BÁSICO - CICLO DE TRADING SIMPLE
# =============================================================================

def ejemplo_1_uso_basico():
    """Ejemplo básico de CycleScheduler con ciclo de trading simple"""
    print("\n" + "="*70)
    print("EJEMPLO 1: Uso Básico - Ciclo de Trading Simple")
    print("="*70)
    
    # Configurar TimeValidator
    time_validator = TimeValidator()
    
    # Configuración básica del scheduler
    config = {
        "cycle_scheduler": {
            "enabled": True,
            "start_delay_seconds": 3,  # Retraso para asegurar velas cerradas
            "check_interval_seconds": 60,  # Verificar cada minuto
            "max_wait_hours": 8
        }
    }
    
    # Crear scheduler
    scheduler = CycleScheduler(time_validator, config)
    
    # Definir el ciclo de trading
    def trading_cycle():
        """Ciclo que se ejecuta cada hora"""
        print(f"\n🚀 CICLO DE TRADING INICIADO - {datetime.now()}")
        print("  1️⃣  Extrayendo datos de MT5...")
        print("  2️⃣  Calculando indicadores...")
        print("  3️⃣  Consultando IA...")
        print("  4️⃣  Ejecutando operaciones...")
        print("✅ Ciclo completado exitosamente\n")
    
    # Ver estado actual
    status = scheduler.get_scheduler_status()
    print(f"\n📊 Estado del Scheduler:")
    print(f"  Habilitado: {status['enabled']}")
    print(f"  Tiempo válido de trading: {status['is_trading_time_valid']}")
    print(f"  Razón: {status['trading_time_reason']}")
    print(f"  Segundos hasta próxima hora: {status['seconds_until_next_hour']}")
    
    # NOTA: En producción, run_cycle() esperaría hasta la próxima hora
    # Para este ejemplo, solo mostramos cómo se configura
    print("\n⚠️  Para ejecutar: scheduler.run_cycle(trading_cycle)")
    print("    El scheduler esperará hasta el próximo HH:00 en horario de trading")


# =============================================================================
# EJEMPLO 2: CONFIGURACIÓN PERSONALIZADA
# =============================================================================

def ejemplo_2_configuracion_personalizada():
    """Ejemplo con configuración personalizada para diferentes escenarios"""
    print("\n" + "="*70)
    print("EJEMPLO 2: Configuración Personalizada")
    print("="*70)
    
    time_validator = TimeValidator()
    
    # Configuración para TESTING - delays más cortos
    test_config = {
        "cycle_scheduler": {
            "enabled": True,
            "start_delay_seconds": 1,  # 1 segundo para tests
            "check_interval_seconds": 5,  # Verificar cada 5 segundos
            "max_wait_hours": 1  # Timeout más corto
        }
    }
    
    # Configuración para PRODUCCIÓN - delays conservadores
    prod_config = {
        "cycle_scheduler": {
            "enabled": True,
            "start_delay_seconds": 5,  # 5 segundos de margen
            "check_interval_seconds": 30,  # Verificar cada 30 segundos
            "max_wait_hours": 10  # Timeout largo
        }
    }
    
    # Crear scheduler para testing
    test_scheduler = CycleScheduler(time_validator, test_config)
    print("\n🧪 Scheduler de TESTING:")
    print(f"  Delay inicial: {test_scheduler.start_delay_seconds}s")
    print(f"  Intervalo de verificación: {test_scheduler.check_interval_seconds}s")
    
    # Crear scheduler para producción
    prod_scheduler = CycleScheduler(time_validator, prod_config)
    print("\n🏭 Scheduler de PRODUCCIÓN:")
    print(f"  Delay inicial: {prod_scheduler.start_delay_seconds}s")
    print(f"  Intervalo de verificación: {prod_scheduler.check_interval_seconds}s")


# =============================================================================
# EJEMPLO 3: MONITOREO DE ESTADO
# =============================================================================

def ejemplo_3_monitoreo_estado():
    """Ejemplo de monitoreo del estado del scheduler"""
    print("\n" + "="*70)
    print("EJEMPLO 3: Monitoreo de Estado")
    print("="*70)
    
    time_validator = TimeValidator()
    config = {"cycle_scheduler": {"enabled": True}}
    scheduler = CycleScheduler(time_validator, config)
    
    # Obtener estado completo
    status = scheduler.get_scheduler_status()
    
    print("\n📊 ESTADO COMPLETO DEL SCHEDULER:")
    print("-" * 70)
    print(f"  ✓ Habilitado: {'SÍ' if status['enabled'] else 'NO'}")
    print(f"  ✓ Delay inicial: {status['start_delay_seconds']} segundos")
    print(f"  ✓ Intervalo de chequeo: {status['check_interval_seconds']} segundos")
    print(f"  ✓ Timeout máximo: {status['max_wait_hours']} horas")
    print()
    print(f"  📅 Hora actual: {status['current_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  ⏱️  Segundos hasta próxima hora: {status['seconds_until_next_hour']}")
    print()
    print(f"  🕐 Horario de trading válido: {'SÍ' if status['is_trading_time_valid'] else 'NO'}")
    if status['trading_time_reason']:
        print(f"  📝 Razón: {status['trading_time_reason']}")
    print("-" * 70)


# =============================================================================
# EJEMPLO 4: MÚLTIPLES BOTS CON DIFERENTES CONFIGURACIONES
# =============================================================================

def ejemplo_4_multiples_bots():
    """Ejemplo de múltiples bots con configuraciones diferentes"""
    print("\n" + "="*70)
    print("EJEMPLO 4: Múltiples Bots con Configuraciones Diferentes")
    print("="*70)
    
    time_validator = TimeValidator()
    
    # Bot 1: Trading agresivo (delay corto)
    bot1_config = {
        "cycle_scheduler": {
            "enabled": True,
            "start_delay_seconds": 2,
            "check_interval_seconds": 30,
            "max_wait_hours": 8
        }
    }
    
    # Bot 2: Trading conservador (delay largo)
    bot2_config = {
        "cycle_scheduler": {
            "enabled": True,
            "start_delay_seconds": 10,  # Espera más tiempo
            "check_interval_seconds": 60,
            "max_wait_hours": 8
        }
    }
    
    # Bot 3: Monitoring bot (solo monitoreo)
    bot3_config = {
        "cycle_scheduler": {
            "enabled": True,
            "start_delay_seconds": 1,
            "check_interval_seconds": 120,  # Verifica menos frecuente
            "max_wait_hours": 12
        }
    }
    
    # Crear schedulers para cada bot
    bot1_scheduler = CycleScheduler(time_validator, bot1_config)
    bot2_scheduler = CycleScheduler(time_validator, bot2_config)
    bot3_scheduler = CycleScheduler(time_validator, bot3_config)
    
    print("\n🤖 Bot 1 (Trading Agresivo):")
    print(f"  Delay: {bot1_scheduler.start_delay_seconds}s - Ejecuta rápido")
    
    print("\n🤖 Bot 2 (Trading Conservador):")
    print(f"  Delay: {bot2_scheduler.start_delay_seconds}s - Espera datos consolidados")
    
    print("\n🤖 Bot 3 (Monitoring):")
    print(f"  Delay: {bot3_scheduler.start_delay_seconds}s - Solo monitorea")


# =============================================================================
# EJEMPLO 5: MANEJO DE CONDICIONES ESPECIALES
# =============================================================================

def ejemplo_5_condiciones_especiales():
    """Ejemplo de cómo el scheduler maneja condiciones especiales"""
    print("\n" + "="*70)
    print("EJEMPLO 5: Manejo de Condiciones Especiales")
    print("="*70)
    
    time_validator = TimeValidator()
    config = {"cycle_scheduler": {"enabled": True}}
    scheduler = CycleScheduler(time_validator, config)
    
    print("\n🔍 Condiciones que el scheduler valida automáticamente:")
    print()
    print("  ✅ Horario de trading (06:00-13:00 Lima)")
    print("     → Fuera de horario: El ciclo NO se ejecuta")
    print()
    print("  ✅ Días hábiles (Lunes-Viernes)")
    print("     → Fin de semana: El ciclo NO se ejecuta")
    print()
    print("  ✅ Feriados peruanos")
    print("     → Día feriado: El ciclo NO se ejecuta")
    print()
    print("  ✅ Inicio exacto de hora (HH:00)")
    print("     → HH:15, HH:30, etc: El ciclo NO se ejecuta")
    print()
    print("  ✅ Buffer de IA (3 minutos antes del cierre)")
    print("     → 12:57-13:00: No permite nuevas operaciones")
    
    # Verificar si ahora se puede ejecutar
    can_start = scheduler.should_start_cycle()
    print(f"\n🎯 ¿Puede iniciar ciclo AHORA? {'SÍ ✅' if can_start else 'NO ❌'}")


# =============================================================================
# EJEMPLO 6: INTEGRACIÓN CON LÓGICA DE NEGOCIO
# =============================================================================

def ejemplo_6_integracion_negocio():
    """Ejemplo de integración con lógica de negocio real"""
    print("\n" + "="*70)
    print("EJEMPLO 6: Integración con Lógica de Negocio")
    print("="*70)
    
    time_validator = TimeValidator()
    config = {"cycle_scheduler": {"enabled": True}}
    scheduler = CycleScheduler(time_validator, config)
    
    # Simular clase de Bot de Trading
    class TradingBot:
        def __init__(self, name: str, scheduler: CycleScheduler):
            self.name = name
            self.scheduler = scheduler
            self.cycle_count = 0
        
        def extract_data(self):
            """Simula extracción de datos de MT5"""
            print(f"    [{self.name}] 📊 Extrayendo datos de MT5...")
        
        def calculate_indicators(self):
            """Simula cálculo de indicadores"""
            print(f"    [{self.name}] 📈 Calculando EMA, RSI, MACD...")
        
        def consult_ai(self):
            """Simula consulta a IA"""
            print(f"    [{self.name}] 🤖 Consultando a Gemini AI...")
        
        def execute_trades(self):
            """Simula ejecución de trades"""
            print(f"    [{self.name}] 💰 Ejecutando operaciones...")
        
        def trading_cycle(self):
            """Ciclo completo de trading"""
            self.cycle_count += 1
            print(f"\n  🔄 CICLO #{self.cycle_count} - {datetime.now()}")
            self.extract_data()
            self.calculate_indicators()
            self.consult_ai()
            self.execute_trades()
            print(f"  ✅ Ciclo #{self.cycle_count} completado\n")
        
        def start(self):
            """Inicia el bot - esperaría hasta la próxima hora"""
            print(f"\n🚀 Bot '{self.name}' iniciado")
            status = self.scheduler.get_scheduler_status()
            print(f"  ⏱️  Esperará {status['seconds_until_next_hour']}s hasta próxima hora")
            
            # En producción:
            # self.scheduler.run_cycle(self.trading_cycle)
    
    # Crear bot de ejemplo
    bot = TradingBot("EURUSD_Bot_1", scheduler)
    
    print("\n📝 Estructura del Bot de Trading:")
    print("  1. __init__: Inicializa con scheduler")
    print("  2. trading_cycle: Método que se ejecutará cada hora")
    print("  3. start: Inicia el bot y espera")
    
    # Simular inicio
    bot.start()


# =============================================================================
# EJEMPLO 7: SCHEDULER DESHABILITADO
# =============================================================================

def ejemplo_7_scheduler_deshabilitado():
    """Ejemplo con scheduler deshabilitado (útil para testing)"""
    print("\n" + "="*70)
    print("EJEMPLO 7: Scheduler Deshabilitado")
    print("="*70)
    
    time_validator = TimeValidator()
    
    # Scheduler deshabilitado
    config = {
        "cycle_scheduler": {
            "enabled": False  # DESHABILITADO
        }
    }
    
    scheduler = CycleScheduler(time_validator, config)
    
    print("\n⚠️  Scheduler DESHABILITADO")
    print("  Útil para:")
    print("    • Testing manual")
    print("    • Debugging")
    print("    • Mantenimiento del sistema")
    
    # Intentar verificar si puede iniciar
    can_start = scheduler.should_start_cycle()
    print(f"\n  ¿Puede iniciar? {can_start} (siempre False cuando está disabled)")
    
    # Estado
    status = scheduler.get_scheduler_status()
    print(f"  Estado habilitado: {status['enabled']}")


# =============================================================================
# EJEMPLO 8: CÁLCULO DE TIEMPO HASTA PRÓXIMA HORA
# =============================================================================

def ejemplo_8_calculo_tiempo():
    """Ejemplo de cálculo de tiempo hasta próxima hora"""
    print("\n" + "="*70)
    print("EJEMPLO 8: Cálculo de Tiempo hasta Próxima Hora")
    print("="*70)
    
    time_validator = TimeValidator()
    config = {"cycle_scheduler": {"enabled": True}}
    scheduler = CycleScheduler(time_validator, config)
    
    status = scheduler.get_scheduler_status()
    seconds = status['seconds_until_next_hour']
    
    # Convertir a formato legible
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    print(f"\n⏰ Tiempo hasta próxima hora:")
    print(f"  Total: {seconds} segundos")
    print(f"  Formato: {hours}h {minutes}m {secs}s")
    
    # Hora actual y próxima
    now = status['current_time']
    print(f"\n📅 Hora actual: {now.strftime('%H:%M:%S')}")
    
    # Calcular próxima hora
    next_hour = (now.hour + 1) % 24
    print(f"📅 Próximo ciclo: {next_hour:02d}:00:00")


# =============================================================================
# EJEMPLO 9: LOGGING DE RECHAZOS (T02)
# =============================================================================

def ejemplo_9_logging_rechazos():
    """
    Ejemplo de logging automático cuando filtros rechazan ciclos (T02).
    
    NUEVO EN T02:
    - CycleScheduler ahora acepta parámetros 'logger' y 'bot_name'
    - Registra automáticamente cuando los filtros de horario/días no se cumplen
    - Permite debugging, auditoría y monitoreo en producción
    """
    print("\n" + "="*70)
    print("EJEMPLO 9: Logging de Rechazos (T02)")
    print("="*70)
    
    time_validator = TimeValidator()
    config = {"cycle_scheduler": {"enabled": True}}
    
    # Crear logger específico para el bot
    bot_logger = logging.getLogger("EURUSD_Bot_1")
    bot_logger.setLevel(logging.INFO)
    
    # Agregar handler para capturar logs en consola
    if not bot_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        bot_logger.addHandler(handler)
    
    # Crear scheduler con logger personalizado (NUEVO EN T02)
    scheduler = CycleScheduler(
        time_validator,
        config,
        logger=bot_logger,          # ← PARÁMETRO NUEVO EN T02
        bot_name="EURUSD_Bot_1"     # ← PARÁMETRO NUEVO EN T02
    )
    
    print("\n🔍 El scheduler ahora registrará rechazos de filtros:")
    print()
    print("  Escenarios que generan logs:")
    print("    • Fuera de horario (antes de 06:00 o después de 13:00 Lima)")
    print("    • Fin de semana (Sábado/Domingo)")
    print("    • Feriados peruanos")
    print("    • Buffer de IA (últimos 3 minutos de la hora)")
    print()
    print("  Ejemplo de mensaje de log:")
    print("    [2025-11-11 14:00:00] INFO - EURUSD_Bot_1")
    print("    [EURUSD_Bot_1] Cycle rejected by time filter:")
    print("    Outside trading hours (06:00-13:00 Lima)")
    print()
    print("  Beneficios:")
    print("    ✅ Auditabilidad completa de decisiones del scheduler")
    print("    ✅ Debugging facilitado (saber POR QUÉ no ejecutó)")
    print("    ✅ Monitoreo en producción (detectar problemas)")
    print("    ✅ Trazabilidad para compliance y reportes")
    
    # Obtener estado
    status = scheduler.get_scheduler_status()
    print(f"\n📊 Estado actual del scheduler:")
    print(f"  Scheduler habilitado: {status['scheduler_enabled']}")
    print(f"  Horario válido: {status['is_trading_time_valid']}")
    if status['trading_time_reason']:
        print(f"  Razón de rechazo: {status['trading_time_reason']}")
    print(f"  Bot name: {scheduler.bot_name}")
    print(f"  Logger: {scheduler.logger.name}")
    
    # Simular verificación (si no es horario válido, SE REGISTRARÁ EN LOGS)
    if not status['is_trading_time_valid']:
        print("\n⚠️  Como estamos fuera de horario, should_start_cycle()")
        print("    registrará el rechazo en los logs automáticamente.")


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Ejecutar todos los ejemplos"""
    print("\n" + "="*70)
    print(" EJEMPLOS DE USO: CycleScheduler (T01 y T02)")
    print("="*70)
    
    ejemplo_1_uso_basico()
    ejemplo_2_configuracion_personalizada()
    ejemplo_3_monitoreo_estado()
    ejemplo_4_multiples_bots()
    ejemplo_5_condiciones_especiales()
    ejemplo_6_integracion_negocio()
    ejemplo_7_scheduler_deshabilitado()
    ejemplo_8_calculo_tiempo()
    ejemplo_9_logging_rechazos()  # ← NUEVO T02
    
    print("\n" + "="*70)
    print(" FIN DE LOS EJEMPLOS")
    print("="*70 + "\n")
    
    print("💡 NOTA IMPORTANTE:")
    print("   En producción, scheduler.run_cycle(callback) bloqueará")
    print("   hasta que sea el momento correcto de ejecutar el ciclo.")
    print("   Los ejemplos anteriores solo muestran configuración.\n")
    print("📝 NUEVO EN T02:")
    print("   El scheduler ahora registra en logs cuando los filtros")
    print("   de horario y días hábiles no se cumplen, facilitando")
    print("   debugging y auditoría del sistema.\n")


if __name__ == "__main__":
    main()
