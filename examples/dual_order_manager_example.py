"""
Ejemplo de uso del DualOrderManager - T14

Este ejemplo demuestra cómo utilizar el DualOrderManager para abrir
simultáneamente órdenes Market y Limit con los mismos parámetros.

Funcionalidades demostradas:
- Apertura dual de órdenes BUY
- Apertura dual de órdenes SELL
- Manejo de diferentes activos
- Manejo de errores
- Validación de parámetros

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T14 - Apertura simultánea de órdenes Market y Limit
"""

import logging
import sys
from pathlib import Path
from decimal import Decimal

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Importar componentes core necesarios
from src.core.mt5_connector import MT5Connector, BrokerConfig
from src.core.order_manager import OrderManager
from src.core.position_sizer import PositionSizer, SymbolSpecification
from src.core.magic_number_generator import MagicNumberGenerator
from src.core.dual_order_manager import (
    DualOrderManager,
    DualOrderRequest,
    DualOrderManagerError,
    PartialExecutionError
)


# ==================== CONFIGURACIÓN DE LOGGING ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== FUNCIONES AUXILIARES ====================

def create_symbol_spec_manual(symbol: str) -> SymbolSpecification:
    """
    Crea especificaciones de símbolo manualmente (para demo).
    En producción, usar SymbolSpecExtractor.
    """
    # Specs comunes para Forex majors
    forex_specs = {
        "EURUSD": SymbolSpecification(
            symbol="EURUSD",
            point=0.00001,
            tick_size=0.00001,
            tick_value=1.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            contract_size=100000.0
        ),
        "GBPUSD": SymbolSpecification(
            symbol="GBPUSD",
            point=0.00001,
            tick_size=0.00001,
            tick_value=1.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            contract_size=100000.0
        ),
        "XAUUSD": SymbolSpecification(
            symbol="XAUUSD",
            point=0.01,
            tick_size=0.01,
            tick_value=1.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            contract_size=100.0
        )
    }
    
    return forex_specs.get(symbol, forex_specs["EURUSD"])


# ==================== EJEMPLO 1: APERTURA DUAL BUY ====================

def example_1_dual_buy_order():
    """
    Ejemplo 1: Apertura dual de órdenes BUY en EURUSD
    
    Escenario:
    - Bot 1, IA Config 0
    - Símbolo: EURUSD
    - Dirección: BUY
    - Balance: $10,000
    - Riesgo: 1%
    - Entry: 1.1000
    - SL: 1.0950 (50 pips debajo)
    - TP: 1.1100 (100 pips arriba)
    - Limit: 1.0990 (10 pips debajo del entry para mejor precio)
    """
    logger.info("=" * 60)
    logger.info("EJEMPLO 1: Apertura Dual BUY en EURUSD")
    logger.info("=" * 60)
    
    # NOTA: Este ejemplo asume conexión activa a MT5
    # En un entorno real, descomentar las siguientes líneas:
    
    # # 1. Configurar y conectar a MT5
    # broker_config = BrokerConfig(
    #     account_id=123456,
    #     password="your_password",
    #     server="YourBroker-Server",
    #     path="C:/Program Files/MetaTrader 5/terminal64.exe"
    # )
    # connector = MT5Connector(broker_config)
    # connector.verify_connection()
    
    # # 2. Inicializar componentes
    # order_manager = OrderManager(connector)
    # position_sizer = PositionSizer()
    # magic_generator = MagicNumberGenerator()
    
    # # 3. Crear DualOrderManager
    # dual_manager = DualOrderManager(
    #     order_manager=order_manager,
    #     position_sizer=position_sizer,
    #     magic_number_generator=magic_generator
    # )
    
    # Para el ejemplo, solo mostramos la estructura del request
    symbol_spec = create_symbol_spec_manual("EURUSD")
    
    # 4. Crear solicitud de orden dual
    request = DualOrderRequest(
        symbol="EURUSD",
        direction="buy",
        account_balance=10000.0,
        risk_percentage=1.0,
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        limit_price=1.0990,
        bot_id=1,
        ia_config_id=0,
        symbol_spec=symbol_spec,
        comment="Ejemplo dual BUY EURUSD",
        deviation=10
    )
    
    logger.info(f"Request creado:")
    logger.info(f"  Símbolo: {request.symbol}")
    logger.info(f"  Dirección: {request.direction.upper()}")
    logger.info(f"  Balance: ${request.account_balance:,.2f}")
    logger.info(f"  Riesgo: {request.risk_percentage}%")
    logger.info(f"  Entry: {request.entry_price}")
    logger.info(f"  SL: {request.stop_loss} ({abs(request.entry_price - request.stop_loss) / request.symbol_spec.point:.0f} pips)")
    logger.info(f"  TP: {request.take_profit} ({abs(request.take_profit - request.entry_price) / request.symbol_spec.point:.0f} pips)")
    logger.info(f"  Limit: {request.limit_price}")
    logger.info(f"  Bot ID: {request.bot_id}")
    logger.info(f"  IA Config: {request.ia_config_id}")
    
    # 5. Validar request
    try:
        request.validate()
        logger.info("✅ Request validado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error de validación: {e}")
        return
    
    # 6. Ejecutar (descomentado en producción)
    # try:
    #     result = dual_manager.open_dual_orders(request)
    #     
    #     logger.info("✅ Órdenes duales ejecutadas exitosamente:")
    #     logger.info(f"  Market Ticket: {result.market_order.order}")
    #     logger.info(f"  Market Magic: {result.market_magic}")
    #     logger.info(f"  Market Price: {result.market_order.price}")
    #     logger.info(f"  Limit Ticket: {result.limit_order.order}")
    #     logger.info(f"  Limit Magic: {result.limit_magic}")
    #     logger.info(f"  Limit Price: {result.limit_order.price}")
    #     logger.info(f"  Lot Size: {result.lot_size}")
    #     
    # except DualOrderManagerError as e:
    #     logger.error(f"❌ Error en apertura dual: {e}")
    # except PartialExecutionError as e:
    #     logger.warning(f"⚠️  Ejecución parcial: {e}")
    #     logger.info(f"  Market ejecutado: Ticket {e.market_order.order} (Magic: {e.market_magic})")
    
    logger.info("Ejemplo 1 completado (modo demo)\n")


# ==================== EJEMPLO 2: APERTURA DUAL SELL ====================

def example_2_dual_sell_order():
    """
    Ejemplo 2: Apertura dual de órdenes SELL en GBPUSD
    
    Escenario:
    - Bot 2, IA Config 1
    - Símbolo: GBPUSD
    - Dirección: SELL
    - Balance: $20,000
    - Riesgo: 2%
    - Entry: 1.2500
    - SL: 1.2550 (50 pips arriba)
    - TP: 1.2400 (100 pips abajo)
    - Limit: 1.2510 (10 pips arriba del entry para mejor precio)
    """
    logger.info("=" * 60)
    logger.info("EJEMPLO 2: Apertura Dual SELL en GBPUSD")
    logger.info("=" * 60)
    
    symbol_spec = create_symbol_spec_manual("GBPUSD")
    
    request = DualOrderRequest(
        symbol="GBPUSD",
        direction="sell",
        account_balance=20000.0,
        risk_percentage=2.0,
        entry_price=1.2500,
        stop_loss=1.2550,  # SL arriba en SELL
        take_profit=1.2400,  # TP abajo en SELL
        limit_price=1.2510,  # Limit arriba del entry en SELL
        bot_id=2,
        ia_config_id=1,
        symbol_spec=symbol_spec,
        comment="Ejemplo dual SELL GBPUSD"
    )
    
    logger.info(f"Request creado:")
    logger.info(f"  Símbolo: {request.symbol}")
    logger.info(f"  Dirección: {request.direction.upper()}")
    logger.info(f"  Balance: ${request.account_balance:,.2f}")
    logger.info(f"  Riesgo: {request.risk_percentage}%")
    logger.info(f"  Entry: {request.entry_price}")
    logger.info(f"  SL: {request.stop_loss} ({abs(request.stop_loss - request.entry_price) / request.symbol_spec.point:.0f} pips)")
    logger.info(f"  TP: {request.take_profit} ({abs(request.entry_price - request.take_profit) / request.symbol_spec.point:.0f} pips)")
    logger.info(f"  Limit: {request.limit_price}")
    logger.info(f"  Bot ID: {request.bot_id}")
    logger.info(f"  IA Config: {request.ia_config_id}")
    
    try:
        request.validate()
        logger.info("✅ Request validado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error de validación: {e}")
        return
    
    logger.info("Ejemplo 2 completado (modo demo)\n")


# ==================== EJEMPLO 3: ORO (XAUUSD) ====================

def example_3_gold_dual_order():
    """
    Ejemplo 3: Apertura dual en oro (XAUUSD)
    
    El oro tiene diferentes especificaciones (point, contract size)
    que Forex, demostrando la adaptabilidad del sistema.
    """
    logger.info("=" * 60)
    logger.info("EJEMPLO 3: Apertura Dual BUY en XAUUSD (Oro)")
    logger.info("=" * 60)
    
    symbol_spec = create_symbol_spec_manual("XAUUSD")
    
    request = DualOrderRequest(
        symbol="XAUUSD",
        direction="buy",
        account_balance=10000.0,
        risk_percentage=1.5,
        entry_price=2000.00,
        stop_loss=1990.00,  # $10 debajo
        take_profit=2020.00,  # $20 arriba
        limit_price=1998.00,  # $2 debajo del entry
        bot_id=3,
        ia_config_id=2,
        symbol_spec=symbol_spec,
        comment="Ejemplo dual ORO"
    )
    
    logger.info(f"Request creado:")
    logger.info(f"  Símbolo: {request.symbol}")
    logger.info(f"  Dirección: {request.direction.upper()}")
    logger.info(f"  Balance: ${request.account_balance:,.2f}")
    logger.info(f"  Riesgo: {request.risk_percentage}%")
    logger.info(f"  Entry: ${request.entry_price}")
    logger.info(f"  SL: ${request.stop_loss} (${abs(request.entry_price - request.stop_loss):.2f})")
    logger.info(f"  TP: ${request.take_profit} (${abs(request.take_profit - request.entry_price):.2f})")
    logger.info(f"  Limit: ${request.limit_price}")
    
    try:
        request.validate()
        logger.info("✅ Request validado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error de validación: {e}")
        return
    
    logger.info("Ejemplo 3 completado (modo demo)\n")


# ==================== EJEMPLO 4: MANEJO DE ERRORES ====================

def example_4_error_handling():
    """
    Ejemplo 4: Demostración de validación y manejo de errores
    
    Muestra los diferentes tipos de errores que puede detectar
    el sistema.
    """
    logger.info("=" * 60)
    logger.info("EJEMPLO 4: Manejo de Errores y Validación")
    logger.info("=" * 60)
    
    symbol_spec = create_symbol_spec_manual("EURUSD")
    
    # Error 1: Dirección inválida
    logger.info("\n--- Error 1: Dirección inválida ---")
    try:
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="LONG",  # ❌ Debe ser 'buy' o 'sell'
            account_balance=10000.0,
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=symbol_spec
        )
        request.validate()
    except Exception as e:
        logger.error(f"✅ Error detectado correctamente: {e}")
    
    # Error 2: SL en dirección incorrecta (BUY)
    logger.info("\n--- Error 2: SL incorrecto en BUY ---")
    try:
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="buy",
            account_balance=10000.0,
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.1050,  # ❌ SL arriba del entry en BUY
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=symbol_spec
        )
        request.validate()
    except Exception as e:
        logger.error(f"✅ Error detectado correctamente: {e}")
    
    # Error 3: Riesgo fuera de rango
    logger.info("\n--- Error 3: Riesgo fuera de rango ---")
    try:
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="buy",
            account_balance=10000.0,
            risk_percentage=150.0,  # ❌ Más del 100%
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=1,
            ia_config_id=0,
            symbol_spec=symbol_spec
        )
        request.validate()
    except Exception as e:
        logger.error(f"✅ Error detectado correctamente: {e}")
    
    # Error 4: Bot ID inválido
    logger.info("\n--- Error 4: Bot ID inválido ---")
    try:
        request = DualOrderRequest(
            symbol="EURUSD",
            direction="buy",
            account_balance=10000.0,
            risk_percentage=1.0,
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1100,
            limit_price=1.0990,
            bot_id=10,  # ❌ Debe estar entre 1-5
            ia_config_id=0,
            symbol_spec=symbol_spec
        )
        request.validate()
    except Exception as e:
        logger.error(f"✅ Error detectado correctamente: {e}")
    
    logger.info("\nEjemplo 4 completado\n")


# ==================== EJEMPLO 5: COMPARACIÓN DE RESULTADOS ====================

def example_5_result_comparison():
    """
    Ejemplo 5: Estructura de resultado y comparación
    
    Muestra cómo extraer y comparar información de los resultados
    de órdenes Market vs Limit.
    """
    logger.info("=" * 60)
    logger.info("EJEMPLO 5: Estructura de Resultados")
    logger.info("=" * 60)
    
    # Simulación de resultado (en producción vendría de dual_manager.open_dual_orders)
    logger.info("\nEstructura de DualOrderResult:")
    logger.info("""
    {
        'success': True,
        'symbol': 'EURUSD',
        'direction': 'buy',
        'lot_size': 0.20,
        'market_magic': 100000,
        'limit_magic': 100001,
        'market_order': {
            'success': True,
            'retcode': 10009,
            'order': 12345,
            'deal': 67890,
            'volume': 0.20,
            'price': 1.1000,
            'comment': 'Market order executed'
        },
        'limit_order': {
            'success': True,
            'retcode': 10009,
            'order': 12346,
            'deal': 0,  # Limit no tiene deal hasta activación
            'volume': 0.20,
            'price': 1.0990,
            'comment': 'Limit order placed'
        },
        'message': 'Dual BUY orders opened successfully - Market: 12345, Limit: 12346'
    }
    """)
    
    logger.info("\nCampos clave para análisis:")
    logger.info("  - market_magic / limit_magic: Para seguimiento independiente")
    logger.info("  - market_order.order / limit_order.order: Tickets para consultas")
    logger.info("  - market_order.price vs limit_order.price: Comparación de ejecución")
    logger.info("  - lot_size: Mismo lote para ambas órdenes (normalizado por riesgo)")
    
    logger.info("\nEjemplo 5 completado\n")


# ==================== MAIN ====================

def main():
    """
    Función principal que ejecuta todos los ejemplos.
    """
    logger.info("\n" + "=" * 60)
    logger.info(" EJEMPLOS DE USO: DualOrderManager (T14)")
    logger.info("=" * 60 + "\n")
    
    # Ejecutar ejemplos
    example_1_dual_buy_order()
    example_2_dual_sell_order()
    example_3_gold_dual_order()
    example_4_error_handling()
    example_5_result_comparison()
    
    logger.info("=" * 60)
    logger.info(" TODOS LOS EJEMPLOS COMPLETADOS")
    logger.info("=" * 60)
    
    logger.info("\n📌 NOTAS IMPORTANTES:")
    logger.info("  1. Estos ejemplos están en modo DEMO (sin conexión real a MT5)")
    logger.info("  2. Para usar en producción, descomentar las secciones de conexión MT5")
    logger.info("  3. Asegúrate de configurar correctamente BrokerConfig con tus credenciales")
    logger.info("  4. El sistema valida automáticamente todos los parámetros antes de ejecutar")
    logger.info("  5. Ambas órdenes usan el mismo lote calculado por % de riesgo")
    logger.info("  6. Cada orden tiene un Magic Number único para trazabilidad")
    logger.info("  7. Si Market falla, no se envía Limit (seguridad)")
    logger.info("  8. Si Limit falla tras Market exitoso, se lanza PartialExecutionError\n")


if __name__ == "__main__":
    main()
