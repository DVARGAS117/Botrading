"""
Ejemplo de uso de SymbolSpecificationExtractor - T31

Demuestra cómo obtener especificaciones de símbolos directamente desde MT5
para usarlas en PositionSizer y LotAdjuster.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T31 - Obtención de especificaciones del símbolo desde MT5
"""

import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.mt5_connector import MT5Connector, BrokerConfig
from src.core.symbol_spec_extractor import SymbolSpecificationExtractor
from src.core.position_sizer import PositionSizer, RiskParameters
from src.core.lot_adjuster import LotAdjuster
from src.core.credential_manager import CredentialManager


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_usage():
    """
    Ejemplo 1: Uso básico del SymbolSpecificationExtractor
    
    Muestra cómo obtener especificaciones de un símbolo desde MT5
    sin necesidad de proporcionarlas manualmente.
    """
    print("\n" + "="*70)
    print("EJEMPLO 1: Uso Básico de SymbolSpecificationExtractor")
    print("="*70)
    
    try:
        # 1. Cargar credenciales
        cred_manager = CredentialManager()
        creds = cred_manager.load_from_file("config/credentials.json")
        
        # 2. Crear configuración de broker
        broker_config = BrokerConfig(
            account_id=creds['mt5']['account_id'],
            password=creds['mt5']['password'],
            server=creds['mt5']['server']
        )
        
        # 3. Conectar a MT5
        connector = MT5Connector(broker_config)
        
        if not connector.verify_connection():
            print("❌ No se pudo conectar a MT5")
            return
        
        print("✅ Conectado a MT5")
        
        # 4. Crear extractor
        extractor = SymbolSpecificationExtractor(connector)
        
        # 5. Obtener especificaciones de EURUSD
        print("\n📊 Obteniendo especificaciones de EURUSD desde MT5...")
        eurusd_spec = extractor.get_symbol_specification("EURUSD")
        
        print(f"\nEspecificaciones de {eurusd_spec.symbol}:")
        print(f"  Point: {eurusd_spec.point}")
        print(f"  Tick Size: {eurusd_spec.tick_size}")
        print(f"  Tick Value: ${eurusd_spec.tick_value}")
        print(f"  Contract Size: {eurusd_spec.contract_size:,.0f}")
        print(f"  Volume Min: {eurusd_spec.volume_min}")
        print(f"  Volume Max: {eurusd_spec.volume_max}")
        print(f"  Volume Step: {eurusd_spec.volume_step}")
        
        # 6. Obtener especificaciones de XAUUSD (Gold)
        print("\n📊 Obteniendo especificaciones de XAUUSD desde MT5...")
        xauusd_spec = extractor.get_symbol_specification("XAUUSD")
        
        print(f"\nEspecificaciones de {xauusd_spec.symbol}:")
        print(f"  Point: {xauusd_spec.point}")
        print(f"  Contract Size: {xauusd_spec.contract_size:,.0f}")
        print(f"  Volume Min: {xauusd_spec.volume_min}")
        print(f"  Volume Max: {xauusd_spec.volume_max}")
        
        # 7. Desconectar
        connector.disconnect()
        print("\n✅ Desconectado de MT5")
    
    except Exception as e:
        logger.error(f"Error en ejemplo 1: {e}")
        print(f"❌ Error: {e}")


def example_2_integration_with_position_sizer():
    """
    Ejemplo 2: Integración con PositionSizer
    
    Muestra cómo usar SymbolSpecificationExtractor para obtener
    especificaciones reales y calcular tamaños de posición.
    """
    print("\n" + "="*70)
    print("EJEMPLO 2: Integración con PositionSizer")
    print("="*70)
    
    try:
        # 1. Conectar a MT5
        cred_manager = CredentialManager()
        creds = cred_manager.load_from_file("config/credentials.json")
        
        broker_config = BrokerConfig(
            account_id=creds['mt5']['account_id'],
            password=creds['mt5']['password'],
            server=creds['mt5']['server']
        )
        
        connector = MT5Connector(broker_config)
        
        if not connector.verify_connection():
            print("❌ No se pudo conectar a MT5")
            return
        
        print("✅ Conectado a MT5")
        
        # 2. Crear extractor
        extractor = SymbolSpecificationExtractor(connector)
        
        # 3. Obtener especificaciones desde MT5 (NO MANUAL)
        print("\n📊 Obteniendo especificaciones reales desde MT5...")
        eurusd_spec = extractor.get_symbol_specification("EURUSD")
        
        print(f"✅ Especificaciones obtenidas de {eurusd_spec.symbol}")
        
        # 4. Obtener información de cuenta
        account = connector.get_account_info()
        print(f"\n💰 Balance de cuenta: ${account.balance:,.2f}")
        
        # 5. Calcular tamaño de posición con datos reales de MT5
        print("\n🧮 Calculando tamaño de posición...")
        
        risk_params = RiskParameters(
            account_balance=account.balance,
            risk_percentage=1.0,  # 1% de riesgo
            entry_price=1.10000,
            stop_loss=1.09900,    # 10 pips de SL
            symbol_spec=eurusd_spec  # ¡Datos reales de MT5!
        )
        
        sizer = PositionSizer()
        result = sizer.calculate_lot_size(risk_params)
        
        print(f"\n📈 Resultado del cálculo:")
        print(f"  Símbolo: {result.symbol}")
        print(f"  Lote calculado: {result.lot_size}")
        print(f"  Riesgo: ${result.risk_amount:.2f}")
        print(f"  Distancia SL: {result.pip_distance:.1f} pips")
        print(f"  Valor por pip: ${result.pip_value:.2f}")
        
        # 6. Desconectar
        connector.disconnect()
        print("\n✅ Desconectado de MT5")
    
    except Exception as e:
        logger.error(f"Error en ejemplo 2: {e}")
        print(f"❌ Error: {e}")


def example_3_cache_and_prefetch():
    """
    Ejemplo 3: Uso de caché y prefetch
    
    Muestra cómo el extractor cachea especificaciones para evitar
    múltiples llamadas a MT5 y cómo pre-cargar símbolos.
    """
    print("\n" + "="*70)
    print("EJEMPLO 3: Caché y Prefetch de Especificaciones")
    print("="*70)
    
    try:
        # 1. Conectar a MT5
        cred_manager = CredentialManager()
        creds = cred_manager.load_from_file("config/credentials.json")
        
        broker_config = BrokerConfig(
            account_id=creds['mt5']['account_id'],
            password=creds['mt5']['password'],
            server=creds['mt5']['server']
        )
        
        connector = MT5Connector(broker_config)
        
        if not connector.verify_connection():
            print("❌ No se pudo conectar a MT5")
            return
        
        print("✅ Conectado a MT5")
        
        # 2. Crear extractor con caché habilitado
        extractor = SymbolSpecificationExtractor(connector, enable_cache=True)
        
        # 3. Pre-cargar especificaciones de múltiples símbolos
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
        
        print(f"\n📦 Pre-cargando especificaciones de {len(symbols)} símbolos...")
        specs = extractor.prefetch_symbols(symbols)
        
        print(f"✅ Cargados {len(specs)} símbolos en caché")
        print(f"   Símbolos: {', '.join(specs.keys())}")
        
        # 4. Verificar caché
        print("\n🔍 Verificando caché:")
        for symbol in symbols:
            is_cached = extractor.is_cached(symbol)
            status = "✅ En caché" if is_cached else "❌ No en caché"
            print(f"  {symbol}: {status}")
        
        # 5. Obtener especificación desde caché (sin llamar a MT5)
        print("\n⚡ Obteniendo EURUSD desde caché (instantáneo)...")
        eurusd_spec = extractor.get_symbol_specification("EURUSD")
        print(f"✅ {eurusd_spec.symbol} obtenido desde caché")
        
        # 6. Limpiar caché de un símbolo específico
        print("\n🧹 Limpiando caché de EURUSD...")
        extractor.clear_cache("EURUSD")
        
        is_cached = extractor.is_cached("EURUSD")
        print(f"   EURUSD en caché: {is_cached}")
        
        # 7. Limpiar todo el caché
        print("\n🧹 Limpiando todo el caché...")
        extractor.clear_cache()
        
        cached_symbols = extractor.get_cached_symbols()
        print(f"   Símbolos en caché: {len(cached_symbols)}")
        
        # 8. Desconectar
        connector.disconnect()
        print("\n✅ Desconectado de MT5")
    
    except Exception as e:
        logger.error(f"Error en ejemplo 3: {e}")
        print(f"❌ Error: {e}")


def example_4_integration_with_lot_adjuster():
    """
    Ejemplo 4: Integración con LotAdjuster
    
    Muestra cómo obtener especificaciones en formato LotAdjuster
    para validar y ajustar lotes.
    """
    print("\n" + "="*70)
    print("EJEMPLO 4: Integración con LotAdjuster")
    print("="*70)
    
    try:
        # 1. Conectar a MT5
        cred_manager = CredentialManager()
        creds = cred_manager.load_from_file("config/credentials.json")
        
        broker_config = BrokerConfig(
            account_id=creds['mt5']['account_id'],
            password=creds['mt5']['password'],
            server=creds['mt5']['server']
        )
        
        connector = MT5Connector(broker_config)
        
        if not connector.verify_connection():
            print("❌ No se pudo conectar a MT5")
            return
        
        print("✅ Conectado a MT5")
        
        # 2. Crear extractor
        extractor = SymbolSpecificationExtractor(connector)
        
        # 3. Obtener especificación para LotAdjuster
        print("\n📊 Obteniendo especificaciones para LotAdjuster...")
        lot_spec = extractor.get_lot_adjuster_specification("EURUSD")
        
        print(f"\nEspecificaciones de volumen para {lot_spec.symbol}:")
        print(f"  Min: {lot_spec.volume_min}")
        print(f"  Max: {lot_spec.volume_max}")
        print(f"  Step: {lot_spec.volume_step}")
        
        # 4. Usar LotAdjuster con especificaciones reales
        adjuster = LotAdjuster()
        
        # Probar diferentes lotes
        test_lots = [0.005, 0.456, 0.99, 150.0]
        
        print("\n🔧 Ajustando lotes con especificaciones reales de MT5:")
        for lot in test_lots:
            result = adjuster.adjust_lot(lot, lot_spec)
            
            status = "✅ Ajustado" if result.was_adjusted else "✓ OK"
            print(f"\n  {status} {lot} → {result.adjusted_lot}")
            print(f"    Razón: {result.reason}")
        
        # 5. Desconectar
        connector.disconnect()
        print("\n✅ Desconectado de MT5")
    
    except Exception as e:
        logger.error(f"Error en ejemplo 4: {e}")
        print(f"❌ Error: {e}")


def main():
    """Ejecutar todos los ejemplos"""
    print("\n" + "="*70)
    print("EJEMPLOS DE SymbolSpecificationExtractor - T31")
    print("Obtención de especificaciones de símbolos desde MT5")
    print("="*70)
    
    try:
        # Ejecutar ejemplos
        example_1_basic_usage()
        example_2_integration_with_position_sizer()
        example_3_cache_and_prefetch()
        example_4_integration_with_lot_adjuster()
        
        print("\n" + "="*70)
        print("✅ Todos los ejemplos completados exitosamente")
        print("="*70)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejemplos interrumpidos por el usuario")
    
    except Exception as e:
        logger.error(f"Error ejecutando ejemplos: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
