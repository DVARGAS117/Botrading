"""
Ejemplo de uso del MT5Connector para verificar conexión a MetaTrader 5.

Este ejemplo demuestra cómo usar el MT5Connector con diferentes brokers
y cómo manejar errores de conexión apropiadamente.

Autor: Sistema Botrading
Fecha: 2025-11-06
Ticket: T06 - Verificación de conexión MT5 al inicio
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.core.mt5_connector import (
    MT5Connector,
    BrokerConfig,
    MT5ConnectionError,
    MT5InitializationError,
    create_connector_from_credentials
)
from src.core.logger import get_bot_logger, LogConfig, LogLevel
from src.core.credential_manager import CredentialManager


def example_basic_connection():
    """Ejemplo básico de conexión con Pepperstone"""
    print("\n=== Ejemplo 1: Conexión básica ===\n")
    
    # Configurar broker
    config = BrokerConfig(
        account_id="12345678",
        password="your_password",
        server="Pepperstone-Demo"
    )
    
    # Crear connector
    connector = MT5Connector(config)
    
    try:
        # Verificar conexión
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            # Obtener información del terminal
            terminal_info = connector.get_terminal_info()
            print(f"  - Terminal conectado: {terminal_info.connected}")
            print(f"  - Trading permitido: {terminal_info.trade_allowed}")
            
            # Obtener información de la cuenta
            account_info = connector.get_account_info()
            print(f"  - Cuenta: {account_info.login}")
            print(f"  - Balance: ${account_info.balance:.2f}")
            print(f"  - Equity: ${account_info.equity:.2f}")
            print(f"  - Servidor: {account_info.server}")
    
    except MT5InitializationError as e:
        print(f"✗ Error de inicialización: {e}")
    
    except MT5ConnectionError as e:
        print(f"✗ Error de conexión: {e}")
    
    finally:
        # Siempre desconectar
        connector.disconnect()
        print("  - Desconectado de MT5")


def example_with_context_manager():
    """Ejemplo usando context manager (recomendado)"""
    print("\n=== Ejemplo 2: Context Manager ===\n")
    
    config = BrokerConfig(
        account_id="12345678",
        password="your_password",
        server="Pepperstone-Demo"
    )
    
    try:
        # Context manager maneja conexión/desconexión automáticamente
        with MT5Connector(config) as connector:
            print("✓ Conexión establecida (context manager)")
            
            account_info = connector.get_account_info()
            print(f"  - Balance: ${account_info.balance:.2f}")
        
        print("  - Desconectado automáticamente")
    
    except MT5ConnectionError as e:
        print(f"✗ Error: {e}")


def example_with_logging():
    """Ejemplo con logging detallado"""
    print("\n=== Ejemplo 3: Con Logging ===\n")
    
    # Configurar logger
    log_config = LogConfig(level=LogLevel.INFO, log_to_console=True, log_to_file=False)
    logger = get_bot_logger("mt5_example", log_config)
    
    config = BrokerConfig(
        account_id="12345678",
        password="your_password",
        server="Pepperstone-Demo"
    )
    
    # Crear connector con logger
    connector = MT5Connector(config, logger=logger.logger)
    
    try:
        if connector.verify_connection():
            logger.info("Conexión exitosa")
            account = connector.get_account_info()
            logger.info(
                f"Cuenta verificada",
                extra={"balance": account.balance, "server": account.server}
            )
    
    except MT5ConnectionError as e:
        logger.error(f"Error de conexión: {e}")
    
    finally:
        connector.disconnect()


def example_with_credentials_manager():
    """Ejemplo cargando credenciales desde CredentialManager"""
    print("\n=== Ejemplo 4: Con CredentialManager ===\n")
    
    # Cargar credenciales desde archivo encriptado
    cred_manager = CredentialManager()
    
    # Nota: En producción cargarías desde archivo encriptado:
    # credentials = cred_manager.load_from_file('config/credentials.enc')
    
    # Para este ejemplo, las seteamos manualmente
    cred_manager.set_credential("mt5.account_id", "12345678")
    cred_manager.set_credential("mt5.password", "your_password")
    cred_manager.set_credential("mt5.server", "Pepperstone-Demo")
    
    # Validar que existan todas las credenciales requeridas
    try:
        cred_manager.validate_mt5_credentials()
        print("✓ Credenciales MT5 validadas")
    except Exception as e:
        print(f"✗ Credenciales incompletas: {e}")
        return
    
    # Crear configuración desde credenciales
    config = BrokerConfig(
        account_id=cred_manager.get_credential("mt5.account_id"),
        password=cred_manager.get_credential("mt5.password"),
        server=cred_manager.get_credential("mt5.server")
    )
    
    # O usar la función helper
    mt5_creds = {
        'account_id': cred_manager.get_credential("mt5.account_id"),
        'password': cred_manager.get_credential("mt5.password"),
        'server': cred_manager.get_credential("mt5.server")
    }
    
    try:
        connector = create_connector_from_credentials(mt5_creds)
        if connector.verify_connection():
            print("✓ Conectado usando credenciales encriptadas")
            connector.disconnect()
    
    except MT5ConnectionError as e:
        print(f"✗ Error: {e}")


def example_different_broker():
    """Ejemplo con un broker diferente (no Pepperstone)"""
    print("\n=== Ejemplo 5: Broker Diferente ===\n")
    
    # El MT5Connector es agnóstico al broker
    # Funciona con cualquier broker compatible con MT5
    
    configs = [
        BrokerConfig(
            account_id="12345678",
            password="password1",
            server="Pepperstone-Demo"
        ),
        BrokerConfig(
            account_id="87654321",
            password="password2",
            server="ICMarkets-Live"
        ),
        BrokerConfig(
            account_id="11223344",
            password="password3",
            server="XM-Demo"
        )
    ]
    
    for config in configs:
        print(f"\nIntentando conectar a: {config.server}")
        connector = MT5Connector(config)
        
        try:
            if connector.verify_connection():
                print(f"  ✓ Conectado a {config.server}")
                connector.disconnect()
        except MT5ConnectionError:
            print(f"  ✗ No se pudo conectar a {config.server}")


def example_connection_in_trading_cycle():
    """Ejemplo de uso en un ciclo de trading real"""
    print("\n=== Ejemplo 6: Ciclo de Trading ===\n")
    
    logger = get_bot_logger("bot_1", LogConfig(level=LogLevel.INFO, log_to_file=False))
    
    config = BrokerConfig(
        account_id="12345678",
        password="your_password",
        server="Pepperstone-Demo"
    )
    
    def trading_cycle():
        """Simula un ciclo de trading"""
        connector = MT5Connector(config, logger=logger.logger)
        
        try:
            # 1. Verificar conexión al inicio del ciclo
            logger.info("Iniciando ciclo de trading")
            
            if not connector.verify_connection():
                logger.error("No se pudo conectar a MT5, abortando ciclo")
                return False
            
            logger.info("Conexión MT5 verificada exitosamente")
            
            # 2. Verificar estado de la cuenta
            account = connector.get_account_info()
            logger.info(
                f"Estado de cuenta",
                extra={
                    "balance": account.balance,
                    "equity": account.equity,
                    "margin_free": account.margin_free
                }
            )
            
            # 3. Aquí irían las operaciones de trading
            #    - Extraer datos OHLCV
            #    - Calcular indicadores
            #    - Consultar IA
            #    - Ejecutar órdenes
            
            logger.info("Ciclo de trading completado exitosamente")
            return True
        
        except MT5ConnectionError as e:
            logger.error(f"Error de conexión en ciclo: {e}")
            return False
        
        except Exception as e:
            logger.exception(f"Error inesperado en ciclo: {e}")
            return False
        
        finally:
            # Siempre desconectar al final del ciclo
            connector.disconnect()
            logger.info("Conexión cerrada")
    
    # Ejecutar ciclo
    success = trading_cycle()
    print(f"\nCiclo completado: {'✓ Exitoso' if success else '✗ Fallido'}")


def main():
    """Ejecuta todos los ejemplos"""
    print("=" * 70)
    print("EJEMPLOS DE USO DEL MT5CONNECTOR")
    print("=" * 70)
    print("\nNOTA: Estos ejemplos requieren:")
    print("  1. MetaTrader 5 instalado")
    print("  2. Credenciales válidas configuradas")
    print("  3. MT5 ejecutándose en segundo plano")
    print("\n" + "=" * 70)
    
    # Descomentar los ejemplos que quieras ejecutar:
    
    # example_basic_connection()
    # example_with_context_manager()
    # example_with_logging()
    # example_with_credentials_manager()
    # example_different_broker()
    # example_connection_in_trading_cycle()
    
    print("\n" + "=" * 70)
    print("Para ejecutar los ejemplos, descomenta las líneas en main()")
    print("=" * 70)


if __name__ == "__main__":
    main()
