"""
Ejemplos de uso del PositionManager.

Este archivo demuestra diferentes formas de consultar y filtrar
posiciones abiertas en MetaTrader 5 usando el PositionManager.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T08 - Consulta de posiciones por símbolo y Magic Number
"""
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.mt5_connector import MT5Connector, BrokerConfig
from src.core.position_manager import PositionManager, PositionType
from src.core.credential_manager import CredentialManager


def ejemplo_1_consultar_todas_las_posiciones():
    """
    Ejemplo 1: Consultar todas las posiciones abiertas
    
    Demuestra cómo obtener la lista completa de posiciones en la cuenta.
    """
    print("\n" + "="*80)
    print("EJEMPLO 1: Consultar Todas las Posiciones Abiertas")
    print("="*80)
    
    # Configurar broker
    broker_config = BrokerConfig(
        account_id="51852965",
        password="YourPassword",  # Reemplazar con credencial real
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    # Conectar a MT5
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            # Crear position manager
            manager = PositionManager(connector)
            
            # Obtener todas las posiciones
            positions = manager.get_all_positions()
            
            print(f"\n✓ Total de posiciones abiertas: {len(positions)}")
            
            if positions:
                print("\nDetalles de posiciones:")
                for i, pos in enumerate(positions, 1):
                    print(f"\n  Posición {i}:")
                    print(f"    Ticket: {pos.ticket}")
                    print(f"    Símbolo: {pos.symbol}")
                    print(f"    Tipo: {pos.type}")
                    print(f"    Volumen: {pos.volume}")
                    print(f"    Precio apertura: {pos.price_open:.5f}")
                    print(f"    Precio actual: {pos.price_current:.5f}")
                    print(f"    Profit: ${pos.profit:.2f}")
                    print(f"    Magic: {pos.magic}")
            else:
                print("  No hay posiciones abiertas")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()
        print("\nConexión cerrada")


def ejemplo_2_filtrar_por_simbolo():
    """
    Ejemplo 2: Filtrar posiciones por símbolo
    
    Demuestra cómo obtener solo las posiciones de un par específico.
    """
    print("\n" + "="*80)
    print("EJEMPLO 2: Filtrar Posiciones por Símbolo")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id="51852965",
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            manager = PositionManager(connector)
            
            # Filtrar por símbolo EURUSD
            symbol = "EURUSD"
            positions = manager.get_positions_by_symbol(symbol)
            
            print(f"\n✓ Posiciones de {symbol}: {len(positions)}")
            
            if positions:
                total_profit = sum(p.profit for p in positions)
                total_volume = sum(p.volume for p in positions)
                
                print(f"  Volumen total: {total_volume} lotes")
                print(f"  Profit total: ${total_profit:.2f}")
                
                print(f"\n  Lista de posiciones:")
                for pos in positions:
                    print(f"    • Ticket {pos.ticket}: {pos.type} {pos.volume} lotes - "
                          f"Profit: ${pos.profit:.2f}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_3_filtrar_por_magic_number():
    """
    Ejemplo 3: Filtrar posiciones por Magic Number
    
    Demuestra cómo obtener solo las posiciones de un bot específico.
    """
    print("\n" + "="*80)
    print("EJEMPLO 3: Filtrar Posiciones por Magic Number")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id="51852965",
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            manager = PositionManager(connector)
            
            # Filtrar por Magic Number (ej: 100001 = Bot RSI)
            magic = 100001
            positions = manager.get_positions_by_magic(magic)
            
            print(f"\n✓ Posiciones con Magic {magic}: {len(positions)}")
            
            if positions:
                # Agrupar por símbolo
                by_symbol = {}
                for pos in positions:
                    if pos.symbol not in by_symbol:
                        by_symbol[pos.symbol] = []
                    by_symbol[pos.symbol].append(pos)
                
                print(f"\n  Símbolos negociados:")
                for symbol, symbol_positions in by_symbol.items():
                    count = len(symbol_positions)
                    profit = sum(p.profit for p in symbol_positions)
                    print(f"    • {symbol}: {count} posición(es) - Profit: ${profit:.2f}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_4_filtrar_por_simbolo_y_magic():
    """
    Ejemplo 4: Filtrar por símbolo Y Magic Number (PRINCIPAL DEL TICKET T08)
    
    Este es el método clave del ticket T08: permite identificar
    posiciones relevantes para un bot específico en un par específico.
    """
    print("\n" + "="*80)
    print("EJEMPLO 4: Filtrar por Símbolo Y Magic Number ⭐ [T08]")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id="51852965",
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            manager = PositionManager(connector)
            
            # Criterio de aceptación del T08:
            # "Bot filtra por símbolo y Magic Number para obtener
            # únicamente las posiciones relevantes para ese bot"
            
            symbol = "EURUSD"
            magic = 100001  # Magic del bot RSI
            
            positions = manager.get_positions_by_symbol_and_magic(symbol, magic)
            
            print(f"\n✓ Posiciones de {symbol} con Magic {magic}: {len(positions)}")
            
            if positions:
                print("\n  Posiciones relevantes para este bot:")
                for pos in positions:
                    direction = "📈" if pos.type == PositionType.BUY else "📉"
                    status = "🟢" if pos.profit > 0 else "🔴" if pos.profit < 0 else "⚪"
                    
                    print(f"\n    {direction} Ticket {pos.ticket}")
                    print(f"       Tipo: {pos.type}")
                    print(f"       Volumen: {pos.volume} lotes")
                    print(f"       Apertura: {pos.price_open:.5f}")
                    print(f"       Actual: {pos.price_current:.5f}")
                    print(f"       {status} Profit: ${pos.profit:.2f}")
                    print(f"       Tiempo: {pos.time_open}")
                
                # Decisión de reevaluación (ejemplo)
                total_profit = sum(p.profit for p in positions)
                print(f"\n  💰 Profit total del bot en {symbol}: ${total_profit:.2f}")
                
                if total_profit < -50:
                    print("  ⚠️  ACCIÓN: Considerar reevaluación de estrategia")
                elif total_profit > 100:
                    print("  ✅ ACCIÓN: Estrategia funcionando bien")
            else:
                print(f"\n  ℹ️  No hay posiciones activas de este bot en {symbol}")
                print("  ✅ ACCIÓN: Bot puede abrir nuevas posiciones")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_5_consultar_por_ticket():
    """
    Ejemplo 5: Consultar posición específica por ticket
    
    Demuestra cómo obtener los detalles de una posición conocida.
    """
    print("\n" + "="*80)
    print("EJEMPLO 5: Consultar Posición por Ticket")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id="51852965",
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            manager = PositionManager(connector)
            
            # Supongamos que queremos consultar el ticket 123456
            ticket = 123456  # Reemplazar con ticket real
            
            position = manager.get_position_by_ticket(ticket)
            
            if position:
                print(f"\n✓ Posición encontrada:")
                print(f"  Ticket: {position.ticket}")
                print(f"  Símbolo: {position.symbol}")
                print(f"  Tipo: {position.type}")
                print(f"  Volumen: {position.volume}")
                print(f"  Precio apertura: {position.price_open:.5f}")
                print(f"  Precio actual: {position.price_current:.5f}")
                print(f"  SL: {position.sl:.5f}" if position.sl != 0 else "  SL: No configurado")
                print(f"  TP: {position.tp:.5f}" if position.tp != 0 else "  TP: No configurado")
                print(f"  Profit: ${position.profit:.2f}")
                print(f"  Swap: ${position.swap:.2f}")
                print(f"  Magic: {position.magic}")
                print(f"  Comentario: {position.comment}")
            else:
                print(f"\n✗ No se encontró posición con ticket {ticket}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_6_estadisticas_generales():
    """
    Ejemplo 6: Obtener estadísticas generales de posiciones
    
    Demuestra cómo usar los métodos auxiliares para análisis rápido.
    """
    print("\n" + "="*80)
    print("EJEMPLO 6: Estadísticas Generales de Posiciones")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id="51852965",
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            manager = PositionManager(connector)
            
            # Estadísticas generales
            total_positions = manager.get_total_positions()
            total_profit = manager.get_total_profit()
            
            print(f"\n📊 ESTADÍSTICAS GENERALES")
            print(f"  Total de posiciones: {total_positions}")
            print(f"  Profit/Loss total: ${total_profit:.2f}")
            
            # Por tipo
            buy_positions = manager.get_positions_by_type(PositionType.BUY)
            sell_positions = manager.get_positions_by_type(PositionType.SELL)
            
            print(f"\n📈 POSICIONES COMPRA (BUY)")
            print(f"  Cantidad: {len(buy_positions)}")
            if buy_positions:
                buy_profit = sum(p.profit for p in buy_positions)
                buy_volume = sum(p.volume for p in buy_positions)
                print(f"  Volumen total: {buy_volume} lotes")
                print(f"  Profit total: ${buy_profit:.2f}")
            
            print(f"\n📉 POSICIONES VENTA (SELL)")
            print(f"  Cantidad: {len(sell_positions)}")
            if sell_positions:
                sell_profit = sum(p.profit for p in sell_positions)
                sell_volume = sum(p.volume for p in sell_positions)
                print(f"  Volumen total: {sell_volume} lotes")
                print(f"  Profit total: ${sell_profit:.2f}")
            
            # Verificar si hay posiciones
            if manager.has_positions():
                print(f"\n✅ Cuenta con posiciones activas")
            else:
                print(f"\n⚠️  Cuenta sin posiciones activas")
            
            # Verificar por símbolo específico
            if manager.has_positions(symbol="EURUSD"):
                print(f"✓ Hay posiciones en EURUSD")
            
            # Verificar por magic específico
            if manager.has_positions(magic=100001):
                print(f"✓ Hay posiciones del bot con magic 100001")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def ejemplo_7_conversion_a_diccionario():
    """
    Ejemplo 7: Convertir posiciones a diccionario para serialización
    
    Demuestra cómo exportar datos de posiciones a formato JSON.
    """
    print("\n" + "="*80)
    print("EJEMPLO 7: Conversión a Diccionario/JSON")
    print("="*80)
    
    broker_config = BrokerConfig(
        account_id="51852965",
        password="YourPassword",
        server="Pepperstone-Demo",
        timeout=60000
    )
    
    connector = MT5Connector(broker_config)
    
    try:
        if connector.verify_connection():
            print("✓ Conexión exitosa a MT5")
            
            manager = PositionManager(connector)
            
            # Obtener posiciones
            positions = manager.get_all_positions()
            
            if positions:
                # Convertir a lista de diccionarios
                positions_dict = [p.to_dict() for p in positions[:3]]  # Primeras 3
                
                print(f"\n✓ Posiciones convertidas a diccionario:")
                
                import json
                json_str = json.dumps(positions_dict, indent=2, default=str)
                print(f"\n{json_str}")
                
                # También se puede guardar en archivo
                # with open('positions.json', 'w') as f:
                #     json.dump(positions_dict, f, indent=2, default=str)
                # print("\n✓ Datos guardados en positions.json")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        connector.disconnect()


def menu_principal():
    """Menú principal de ejemplos"""
    ejemplos = {
        '1': ejemplo_1_consultar_todas_las_posiciones,
        '2': ejemplo_2_filtrar_por_simbolo,
        '3': ejemplo_3_filtrar_por_magic_number,
        '4': ejemplo_4_filtrar_por_simbolo_y_magic,
        '5': ejemplo_5_consultar_por_ticket,
        '6': ejemplo_6_estadisticas_generales,
        '7': ejemplo_7_conversion_a_diccionario,
    }
    
    print("\n" + "="*80)
    print(" "*20 + "POSITION MANAGER - EJEMPLOS")
    print("="*80)
    print("\nSeleccione un ejemplo para ejecutar:")
    print("\n  1. Consultar todas las posiciones abiertas")
    print("  2. Filtrar posiciones por símbolo")
    print("  3. Filtrar posiciones por Magic Number")
    print("  4. Filtrar por símbolo Y Magic Number ⭐ [T08]")
    print("  5. Consultar posición por ticket")
    print("  6. Estadísticas generales de posiciones")
    print("  7. Conversión a diccionario/JSON")
    print("\n  0. Salir")
    print("  A. Ejecutar todos los ejemplos")
    print("\n" + "="*80)
    
    while True:
        opcion = input("\nOpción: ").strip().upper()
        
        if opcion == '0':
            print("\n¡Hasta luego!")
            break
        elif opcion == 'A':
            for i in range(1, 8):
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
