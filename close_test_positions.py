"""Cerrar todas las posiciones de test en MT5"""
import MetaTrader5 as mt5
import time

def close_test_positions():
    """Cierra todas las posiciones con magic 100000 (test)"""
    if not mt5.initialize():
        print("❌ Error al inicializar MT5")
        return False
    
    print("\n🔍 Buscando posiciones de test...")
    
    # Buscar posiciones con magic 100000 (test)
    positions = mt5.positions_get()
    test_positions = [p for p in positions if p.magic == 100000]
    
    if not test_positions:
        print("✅ No hay posiciones de test abiertas")
        mt5.shutdown()
        return True
    
    print(f"\n📋 Encontradas {len(test_positions)} posiciones de test:")
    for pos in test_positions:
        print(f"  Ticket: {pos.ticket}, Symbol: {pos.symbol}, Type: {'BUY' if pos.type == 0 else 'SELL'}, Volume: {pos.volume}, Profit: ${pos.profit:.2f}")
    
    print("\n🔒 Cerrando posiciones...")
    
    for pos in test_positions:
        # Determinar tipo de orden opuesto
        order_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        
        # Crear request de cierre
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": pos.ticket,
            "magic": pos.magic,
            "comment": "Test cleanup",
            "type_filling": mt5.ORDER_FILLING_IOC,
            "type_time": mt5.ORDER_TIME_GTC,
        }
        
        # Enviar orden
        result = mt5.order_send(close_request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"  ✅ Cerrado ticket #{pos.ticket}")
        else:
            print(f"  ❌ Error cerrando #{pos.ticket}: {result.comment}")
        
        time.sleep(0.5)  # Pequeña pausa entre cierres
    
    print("\n✅ Proceso completado")
    mt5.shutdown()
    return True

if __name__ == "__main__":
    close_test_positions()
