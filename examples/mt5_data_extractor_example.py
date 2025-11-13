"""
Ejemplos de uso del MT5DataExtractor.

Este archivo demuestra diferentes formas de usar el MT5DataExtractor
para extraer datos OHLCV desde MetaTrader 5.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T07 - Extracción de velas cerradas OHLCV por timeframe
"""
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from src.core.mt5_connector import MT5Connector, BrokerConfig
from src.core.mt5_data_extractor import (
    MT5DataExtractor,
    Timeframe,
    OHLCVData,
    MT5DataError
)
from src.core.credential_manager import CredentialManager
from src.core.logger import get_bot_logger, LogConfig
from src.core.candle_waiter import CandleWaiter
from src.core.time_validator import TimeValidator


def ejemplo_1_extraccion_basica():
    """
    Ejemplo 1: Extracción básica de velas OHLCV
    
    Demuestra cómo extraer un número específico de velas cerradas
    para un símbolo y timeframe.
    """
    print("\n" + "="*80)
    print("EJEMPLO 1: Extracción Básica de Velas OHLCV")
    print("="*80)
    
    # Configurar broker
    broker_config = BrokerConfig(
        account_id=51852965,
        password="YourPassword",  # Reemplazar con credencial real
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    # Conectar a MT5
    connector = MT5Connector(broker_config)
    
    try:
        # Verificar conexión
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            # Crear extractor
            extractor = MT5DataExtractor(connector)
            
            # Extraer últimas 100 velas de EURUSD en M5
            print("\nExtrayendo últimas 100 velas de EURUSD en M5...")
            data = extractor.get_ohlcv(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                count=100
            )
            
            print(f"\n✓ Extraídas {data.count} velas de {data.symbol}")
            print(f"  Timeframe: {data.timeframe.name}")
            print(f"\n  Primeras 5 velas:")
            print(data.data.head())
            print(f"\n  Últimas 5 velas:")
            print(data.data.tail())
            
    except MT5DataError as e:
        print(f"✗ Error de datos MT5: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()
        print("\nConexión cerrada")


def ejemplo_2_velas_cerradas_sin_actual():
    """
    Ejemplo 2: Extracción excluyendo vela actual
    
    Demuestra cómo extraer solo velas cerradas, excluyendo
    la vela actual que puede estar parcialmente formada.
    """
    print("\n" + "="*80)
    print("EJEMPLO 2: Extracción Excluyendo Vela Actual (Solo Cerradas)")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id=51852965,
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            extractor = MT5DataExtractor(connector)
            
            # Extraer velas SIN la actual
            print("\nExtrayendo 50 velas cerradas de GBPUSD en M15...")
            data = extractor.get_ohlcv(
                symbol="GBPUSD",
                timeframe=Timeframe.M15,
                count=50,
                exclude_current=True  # ← Solo velas cerradas
            )
            
            print(f"\n✓ Extraídas {data.count} velas CERRADAS")
            print(f"  Última vela (ya cerrada):")
            print(f"  Time: {data.data.iloc[-1]['time']}")
            print(f"  OHLC: O={data.data.iloc[-1]['open']:.5f}, "
                  f"H={data.data.iloc[-1]['high']:.5f}, "
                  f"L={data.data.iloc[-1]['low']:.5f}, "
                  f"C={data.data.iloc[-1]['close']:.5f}")
            
    except MT5DataError as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_3_multiples_timeframes():
    """
    Ejemplo 3: Extracción de múltiples timeframes
    
    Demuestra cómo extraer datos de varios timeframes simultáneamente,
    útil para análisis multi-temporal.
    """
    print("\n" + "="*80)
    print("EJEMPLO 3: Extracción Multi-Timeframe")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id=51852965,
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            extractor = MT5DataExtractor(connector)
            
            # Extraer datos de 3 timeframes: M5, M15, H1
            print("\nExtrayendo EURUSD en 3 timeframes: M5, M15, H1...")
            multi_data = extractor.get_ohlcv_multi_timeframe(
                symbol="EURUSD",
                timeframes=[Timeframe.M5, Timeframe.M15, Timeframe.H1],
                count=50,
                exclude_current=True
            )
            
            print(f"\n✓ Extracción exitosa de {len(multi_data)} timeframes")
            
            for tf, data in multi_data.items():
                print(f"\n  {tf.name}:")
                print(f"    Velas: {data.count}")
                print(f"    Última vela: {data.data.iloc[-1]['time']}")
                print(f"    Close: {data.data.iloc[-1]['close']:.5f}")
            
    except MT5DataError as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_4_rango_de_fechas():
    """
    Ejemplo 4: Extracción por rango de fechas
    
    Demuestra cómo extraer datos históricos de un período específico.
    """
    print("\n" + "="*80)
    print("EJEMPLO 4: Extracción por Rango de Fechas")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id=51852965,
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            extractor = MT5DataExtractor(connector)
            
            # Definir rango de fechas (última semana)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            print(f"\nExtrayendo EURUSD M5 desde {start_date} hasta {end_date}...")
            data = extractor.get_ohlcv_range(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                start_date=start_date,
                end_date=end_date
            )
            
            print(f"\n✓ Extraídas {data.count} velas del período solicitado")
            print(f"  Primera vela: {data.data.iloc[0]['time']}")
            print(f"  Última vela: {data.data.iloc[-1]['time']}")
            
    except MT5DataError as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_5_validacion_de_simbolos():
    """
    Ejemplo 5: Validación de símbolos antes de extraer
    
    Demuestra cómo validar que un símbolo existe en MT5
    antes de intentar extraer sus datos.
    """
    print("\n" + "="*80)
    print("EJEMPLO 5: Validación de Símbolos")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id=51852965,
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            extractor = MT5DataExtractor(connector)
            
            # Lista de símbolos a validar
            symbols = ["EURUSD", "GBPUSD", "INVALID_SYMBOL", "USDJPY"]
            
            print("\nValidando símbolos...")
            for symbol in symbols:
                is_valid = extractor.validate_symbol(symbol)
                status = "✓ Válido" if is_valid else "✗ No disponible"
                print(f"  {symbol}: {status}")
            
            # Extraer solo símbolos válidos
            print("\nExtrayendo datos de símbolos válidos...")
            valid_symbols = [s for s in symbols if extractor.validate_symbol(s)]
            
            for symbol in valid_symbols:
                data = extractor.get_ohlcv(
                    symbol=symbol,
                    timeframe=Timeframe.M5,
                    count=10
                )
                print(f"  {symbol}: {data.count} velas extraídas")
            
    except MT5DataError as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_6_con_cache():
    """
    Ejemplo 6: Uso de caché para optimizar peticiones
    
    Demuestra cómo habilitar el caché para evitar peticiones
    repetidas a MT5 con los mismos parámetros.
    """
    print("\n" + "="*80)
    print("EJEMPLO 6: Uso de Caché")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id=51852965,
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            # Crear extractor con caché habilitado
            extractor = MT5DataExtractor(connector, enable_cache=True)
            
            print("\nPrimera extracción (desde MT5)...")
            import time
            start = time.time()
            data1 = extractor.get_ohlcv(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                count=100
            )
            time1 = time.time() - start
            print(f"  Tiempo: {time1:.3f}s - {data1.count} velas")
            
            print("\nSegunda extracción (desde caché)...")
            start = time.time()
            data2 = extractor.get_ohlcv(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                count=100
            )
            time2 = time.time() - start
            print(f"  Tiempo: {time2:.3f}s - {data2.count} velas")
            print(f"  ✓ Aceleración: {time1/time2:.1f}x más rápido")
            
            # Limpiar caché si es necesario
            extractor.clear_cache()
            print("\n✓ Caché limpiado")
            
    except MT5DataError as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_7_con_credential_manager():
    """
    Ejemplo 7: Integración con CredentialManager
    
    Demuestra cómo usar el CredentialManager para gestionar
    credenciales de forma segura.
    """
    print("\n" + "="*80)
    print("EJEMPLO 7: Integración con CredentialManager")
    print("="*80)
    
    try:
        # Cargar credenciales desde archivo
        cred_manager = CredentialManager("config/credentials.json")
        
        # Obtener credenciales de MT5
        creds = cred_manager.get_credentials("mt5")
        
        # Crear configuración del broker
        broker_config = BrokerConfig(
            account_id=creds.get("account_id"),
            password=creds.get("password"),
            server=creds.get("server"),
            timeout=60000
        )
        
        connector = MT5Connector(broker_config)
        
        if connector.verify_connection():
            print("✓ Conexión exitosa usando CredentialManager")
            
            extractor = MT5DataExtractor(connector)
            
            # Extraer datos
            data = extractor.get_ohlcv(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                count=50
            )
            
            print(f"\n✓ Extraídas {data.count} velas de {data.symbol}")
            
        connector.disconnect()
        
    except FileNotFoundError:
        print("✗ Archivo de credenciales no encontrado")
        print("  Asegúrese de crear config/credentials.json")
    except Exception as e:
        print(f"✗ Error: {e}")


def ejemplo_8_conversion_a_dict():
    """
    Ejemplo 8: Conversión de datos a diccionario
    
    Demuestra cómo convertir OHLCVData a diccionario
    para serialización JSON o integración con APIs.
    """
    print("\n" + "="*80)
    print("EJEMPLO 8: Conversión a Diccionario/JSON")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id=51852965,
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            extractor = MT5DataExtractor(connector)
            
            # Extraer datos
            data = extractor.get_ohlcv(
                symbol="EURUSD",
                timeframe=Timeframe.M5,
                count=5
            )
            
            # Convertir a diccionario
            data_dict = data.to_dict()
            
            print("\n✓ Datos convertidos a diccionario:")
            print(f"  Symbol: {data_dict['symbol']}")
            print(f"  Timeframe: {data_dict['timeframe']}")
            print(f"  Count: {data_dict['count']}")
            print(f"\n  Primeras 2 velas:")
            for i, candle in enumerate(data_dict['data'][:2]):
                print(f"    Vela {i+1}: O={candle['open']:.5f}, "
                      f"C={candle['close']:.5f}, "
                      f"V={candle['volume']}")
            
            # También se puede serializar a JSON
            import json
            json_str = json.dumps(data_dict, indent=2, default=str)
            print(f"\n  JSON (primeros 300 chars):")
            print(f"  {json_str[:300]}...")
            
    except MT5DataError as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_9_espera_cierre_vela():
    """
    Ejemplo 9: Espera por cierre de vela antes de extraer datos (T37)
    
    Demuestra cómo usar CandleWaiter para esperar el cierre de vela
    antes de extraer datos, garantizando indicadores consistentes.
    """
    print("\n" + "="*80)
    print("EJEMPLO 9: Espera por Cierre de Vela (T37)")
    print("="*80)
    
    try:
        # Configurar TimeValidator para validación de horarios
        time_validator = TimeValidator("config/schedule.example.json")
        
        # Configurar CandleWaiter para velas M5
        candle_config = {
            "candle_wait": {
                "delay_seconds": 3,  # Espera 3 segundos después del cierre
                "timeout_seconds": 300,
                "strict_mode": True
            }
        }
        
        candle_waiter = CandleWaiter("M5", candle_config, time_validator)
        
        print("✓ CandleWaiter configurado para M5")
        
        # Mostrar estado actual
        summary = candle_waiter.get_wait_summary()
        print(f"\nEstado actual:")
        print(f"  Timeframe: {summary['timeframe']}")
        print(f"  Próximo cierre: {summary['next_close_time']}")
        print(f"  Segundos hasta cierre: {summary['seconds_until_close']}")
        print(f"  Horario de trading: {summary['is_trading_time']}")
        
        # Esperar cierre de vela
        print(f"\nEsperando cierre de vela M5...")
        import time
        start_time = time.time()
        
        success = candle_waiter.wait_for_candle_close()
        
        elapsed = time.time() - start_time
        
        if success:
            print(f"✅ Vela cerrada exitosamente después de {elapsed:.1f} segundos")
            
            # Ahora extraer datos con confianza de que son completos
            print("\nExtrayendo datos de velas cerradas...")
            
            # Configurar broker (usando credenciales de ejemplo)
            broker_config = BrokerConfig(
                account_id="51852965",  # Convertir a string
                password="YourPassword",
                server="Pepperstone-Demo",
                timeout=60000
            )
            
            connector = MT5Connector(broker_config)
            
            if connector.verify_connection():
                print("✓ Conexión MT5 exitosa")
                
                # Crear extractor con integración de CandleWaiter
                extractor = MT5DataExtractor(
                    connector,
                    candle_waiter=candle_waiter  # Integración opcional
                )
                
                # Extraer datos con wait_for_close=True (usando la integración)
                data = extractor.get_ohlcv(
                    symbol="EURUSD",
                    timeframe=Timeframe.M5,
                    count=10,
                    wait_for_close=True  # ← Esta es la funcionalidad clave de T37
                )
                
                print(f"\n✅ Extraídas {data.count} velas CERRADAS de {data.symbol}")
                print(f"   Última vela: {data.data.iloc[-1]['time']}")
                print(f"   Close: {data.data.iloc[-1]['close']:.5f}")
                print(f"\n   ✅ Indicadores calculados con datos consistentes!")
                
            else:
                print("✗ No se pudo conectar a MT5")
                
            connector.disconnect()
            
        else:
            print(f"❌ Espera fallida después de {elapsed:.1f} segundos")
            print("   Posibles causas:")
            print("   - Fuera de horario de trading")
            print("   - Timeout excedido")
            print("   - Error en TimeValidator")
    
    except FileNotFoundError:
        print("✗ Archivos de configuración no encontrados")
        print("   Asegúrese de tener config/schedule.example.json")
    except Exception as e:
        print(f"✗ Error: {e}")


def menu_principal():
    """Menú principal de ejemplos"""
    ejemplos = {
        '1': ejemplo_1_extraccion_basica,
        '2': ejemplo_2_velas_cerradas_sin_actual,
        '3': ejemplo_3_multiples_timeframes,
        '4': ejemplo_4_rango_de_fechas,
        '5': ejemplo_5_validacion_de_simbolos,
        '6': ejemplo_6_con_cache,
        '7': ejemplo_7_con_credential_manager,
        '8': ejemplo_8_conversion_a_dict,
        '9': ejemplo_9_espera_cierre_vela,
    }
    
    print("\n" + "="*80)
    print(" "*20 + "MT5 DATA EXTRACTOR - EJEMPLOS")
    print("="*80)
    print("\nSeleccione un ejemplo para ejecutar:")
    print("\n  1. Extracción básica de velas OHLCV")
    print("  2. Extracción excluyendo vela actual (solo cerradas)")
    print("  3. Extracción de múltiples timeframes")
    print("  4. Extracción por rango de fechas")
    print("  5. Validación de símbolos")
    print("  6. Uso de caché para optimización")
    print("  7. Integración con CredentialManager")
    print("  8. Conversión de datos a diccionario/JSON")
    print("  9. Espera por cierre de vela (T37)")
    print("\n  0. Salir")
    print("  A. Ejecutar todos los ejemplos")
    print("\n" + "="*80)
    
    while True:
        opcion = input("\nOpción: ").strip().upper()
        
        if opcion == '0':
            print("\n¡Hasta luego!")
            break
        elif opcion == 'A':
            for i in range(1, 10):
                ejemplos[str(i)]()
            print("\n" + "="*80)
            print("  TODOS LOS EJEMPLOS COMPLETADOS")
            print("="*80)
        elif opcion in ejemplos:
            ejemplos[opcion]()
        else:
            print("✗ Opción inválida")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n✗ Interrumpido por el usuario")
    except Exception as e:
        print(f"\n✗ Error fatal: {e}")
        import traceback
        traceback.print_exc()
