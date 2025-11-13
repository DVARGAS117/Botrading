"""
Ejemplo completo de uso de OrderManager - T09

Este ejemplo demuestra todas las funcionalidades del OrderManager:
1. Envío de órdenes Market (BUY/SELL)
2. Envío de órdenes Limit (BUY_LIMIT/SELL_LIMIT)
3. Modificación de SL/TP en posiciones abiertas
4. Cierre de posiciones (total y parcial)
5. Cierre masivo por filtros
6. Manejo de errores
7. Ciclo de vida completo de operaciones

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T09 - Envío de órdenes y gestión de SL/TP/cierre
"""

from src.core.mt5_connector import MT5Connector, BrokerConfig
from src.core.order_manager import (
    OrderManager,
    OrderRequest,
    OrderResult,
    OrderType,
    OrderManagerError,
    InvalidOrderParametersError,
    OrderExecutionError
)
from src.core.position_manager import PositionManager
from datetime import datetime, timedelta


def ejemplo_1_orden_market_basica():
    """
    Ejemplo 1: Enviar una orden Market simple (BUY)
    """
    print("\n" + "="*80)
    print("EJEMPLO 1: Orden Market Básica (BUY)")
    print("="*80)
    
    # Configurar broker (usar tus credenciales reales)
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    # Conectar a MT5
    with MT5Connector(config) as connector:
        # Crear OrderManager
        manager = OrderManager(connector)
        
        # Crear solicitud de orden
        request = OrderRequest(
            symbol="EURUSD",
            order_type=OrderType.BUY,
            volume=0.1,
            price=1.1000,  # Precio de referencia
            sl=1.0950,     # Stop Loss a 50 pips
            tp=1.1100,     # Take Profit a 100 pips
            magic=100001,
            comment="Ejemplo 1 - BUY Market"
        )
        
        try:
            # Enviar orden
            result = manager.send_market_order(request)
            
            print(f"✅ Orden ejecutada exitosamente")
            print(f"   Ticket: {result.order}")
            print(f"   Deal: {result.deal}")
            print(f"   Precio: {result.price}")
            print(f"   Volumen: {result.volume}")
            print(f"   Código retorno: {result.retcode}")
            
        except InvalidOrderParametersError as e:
            print(f"❌ Error en parámetros: {e}")
        except OrderExecutionError as e:
            print(f"❌ Error en ejecución: {e}")


def ejemplo_2_orden_market_sell():
    """
    Ejemplo 2: Enviar una orden Market SELL
    """
    print("\n" + "="*80)
    print("EJEMPLO 2: Orden Market SELL")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        
        request = OrderRequest(
            symbol="GBPUSD",
            order_type=OrderType.SELL,
            volume=0.1,
            price=1.2500,
            sl=1.2550,  # SL arriba para SELL
            tp=1.2400,  # TP abajo para SELL
            magic=100001,
            comment="Ejemplo 2 - SELL Market"
        )
        
        result = manager.send_market_order(request)
        print(f"✅ SELL ejecutado - Ticket: {result.order}")


def ejemplo_3_orden_limit():
    """
    Ejemplo 3: Enviar una orden Limit pendiente
    """
    print("\n" + "="*80)
    print("EJEMPLO 3: Orden Limit Pendiente (BUY_LIMIT)")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        
        # BUY_LIMIT: comprar cuando el precio baje a 1.0950
        request = OrderRequest(
            symbol="EURUSD",
            order_type=OrderType.BUY_LIMIT,
            volume=0.1,
            price=1.0950,  # Precio límite (más bajo que actual)
            sl=1.0900,
            tp=1.1050,
            magic=100002,
            comment="Ejemplo 3 - BUY LIMIT",
            expiration=datetime.now() + timedelta(days=7)  # Expira en 7 días
        )
        
        result = manager.send_limit_order(request)
        print(f"✅ Orden pendiente creada - Orden: {result.order}")
        print(f"   Precio límite: {request.price}")
        print(f"   Expira: {request.expiration}")


def ejemplo_4_modificar_sl_tp():
    """
    Ejemplo 4: Modificar SL/TP de una posición existente
    """
    print("\n" + "="*80)
    print("EJEMPLO 4: Modificar SL/TP de Posición Abierta")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        position_mgr = PositionManager(connector)
        
        # Obtener posiciones abiertas
        positions = position_mgr.get_positions_by_symbol("EURUSD")
        
        if positions:
            ticket = positions[0].ticket
            print(f"📌 Modificando posición {ticket}")
            
            # Modificar solo SL (mover a breakeven)
            result = manager.modify_position(
                ticket=ticket,
                sl=1.1000,  # Nuevo SL (breakeven)
                tp=0.0      # No modificar TP
            )
            print(f"✅ SL modificado exitosamente")
            
            # Modificar solo TP (extender objetivo)
            result = manager.modify_position(
                ticket=ticket,
                sl=0.0,     # No modificar SL
                tp=1.1150   # Nuevo TP
            )
            print(f"✅ TP modificado exitosamente")
            
            # Modificar ambos
            result = manager.modify_position(
                ticket=ticket,
                sl=1.1010,  # Nuevo SL
                tp=1.1200   # Nuevo TP
            )
            print(f"✅ SL y TP modificados exitosamente")
        else:
            print("⚠️  No hay posiciones abiertas de EURUSD")


def ejemplo_5_cerrar_posicion():
    """
    Ejemplo 5: Cerrar una posición abierta
    """
    print("\n" + "="*80)
    print("EJEMPLO 5: Cerrar Posición")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        position_mgr = PositionManager(connector)
        
        # Obtener posiciones
        positions = position_mgr.get_all_positions()
        
        if positions:
            pos = positions[0]
            print(f"📌 Cerrando posición {pos.ticket}")
            print(f"   Símbolo: {pos.symbol}")
            print(f"   Tipo: {pos.type}")
            print(f"   Volumen: {pos.volume}")
            
            # Cerrar posición completa
            result = manager.close_position(ticket=pos.ticket)
            
            print(f"✅ Posición cerrada")
            print(f"   Deal: {result.deal}")
            print(f"   Precio cierre: {result.price}")
        else:
            print("⚠️  No hay posiciones abiertas")


def ejemplo_6_cerrar_parcial():
    """
    Ejemplo 6: Cerrar parcialmente una posición
    """
    print("\n" + "="*80)
    print("EJEMPLO 6: Cierre Parcial de Posición")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        position_mgr = PositionManager(connector)
        
        # Buscar una posición con volumen >= 0.2
        positions = position_mgr.get_all_positions()
        
        for pos in positions:
            if pos.volume >= 0.2:
                print(f"📌 Cerrando 50% de posición {pos.ticket}")
                print(f"   Volumen total: {pos.volume}")
                
                # Cerrar solo la mitad
                volume_parcial = pos.volume / 2
                result = manager.close_position(
                    ticket=pos.ticket,
                    volume=volume_parcial
                )
                
                print(f"✅ Cerrados {volume_parcial} lotes")
                print(f"   Quedan {pos.volume - volume_parcial} lotes abiertos")
                break
        else:
            print("⚠️  No hay posiciones con volumen >= 0.2")


def ejemplo_7_cerrar_masivo_por_simbolo():
    """
    Ejemplo 7: Cerrar todas las posiciones de un símbolo
    """
    print("\n" + "="*80)
    print("EJEMPLO 7: Cierre Masivo por Símbolo")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        
        # Cerrar todas las posiciones de EURUSD
        results = manager.close_all_positions(symbol="EURUSD")
        
        exitosos = [r for r in results if r.success]
        fallidos = [r for r in results if not r.success]
        
        print(f"📊 Resultados:")
        print(f"   ✅ Cerradas exitosamente: {len(exitosos)}")
        print(f"   ❌ Fallidas: {len(fallidos)}")
        
        for i, result in enumerate(exitosos, 1):
            print(f"   {i}. Ticket {result.order} - Deal {result.deal}")


def ejemplo_8_cerrar_masivo_por_magic():
    """
    Ejemplo 8: Cerrar todas las posiciones de un bot (Magic Number)
    """
    print("\n" + "="*80)
    print("EJEMPLO 8: Cierre Masivo por Magic Number")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        
        # Cerrar todas las posiciones del Bot 1 (magic 100001)
        results = manager.close_all_positions(magic=100001)
        
        print(f"📊 Bot 1 (Magic 100001):")
        print(f"   Posiciones cerradas: {len([r for r in results if r.success])}")


def ejemplo_9_dual_market_limit():
    """
    Ejemplo 9: Estrategia Dual - Abrir Market y Limit simultáneamente
    """
    print("\n" + "="*80)
    print("EJEMPLO 9: Estrategia Dual Market/Limit")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        
        # 1. Abrir orden Market inmediata
        market_request = OrderRequest(
            symbol="EURUSD",
            order_type=OrderType.BUY,
            volume=0.1,
            price=1.1000,
            sl=1.0950,
            tp=1.1100,
            magic=100001,
            comment="Dual - Market"
        )
        
        market_result = manager.send_market_order(market_request)
        print(f"✅ Market abierto - Ticket: {market_result.order}")
        
        # 2. Abrir orden Limit pendiente (mismo símbolo, mismo setup)
        limit_request = OrderRequest(
            symbol="EURUSD",
            order_type=OrderType.BUY_LIMIT,
            volume=0.1,
            price=1.0950,  # Entrada más favorable
            sl=1.0900,
            tp=1.1050,
            magic=100002,  # Diferente magic para identificar
            comment="Dual - Limit"
        )
        
        limit_result = manager.send_limit_order(limit_request)
        print(f"✅ Limit creado - Orden: {limit_result.order}")
        
        print(f"\n📊 Estrategia Dual configurada:")
        print(f"   Market (100001): Ticket {market_result.order}")
        print(f"   Limit (100002): Orden {limit_result.order}")


def ejemplo_10_ciclo_completo():
    """
    Ejemplo 10: Ciclo de vida completo de una operación
    Abrir → Modificar SL/TP → Cerrar
    """
    print("\n" + "="*80)
    print("EJEMPLO 10: Ciclo de Vida Completo")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        
        # PASO 1: Abrir posición
        print("\n📌 PASO 1: Abriendo posición...")
        request = OrderRequest(
            symbol="EURUSD",
            order_type=OrderType.BUY,
            volume=0.1,
            price=1.1000,
            sl=1.0950,
            tp=1.1100,
            magic=100001,
            comment="Ciclo completo"
        )
        
        result_open = manager.send_market_order(request)
        ticket = result_open.order
        print(f"✅ Posición abierta - Ticket: {ticket}")
        
        # Simular espera (en real sería entre ciclos)
        import time
        time.sleep(2)
        
        # PASO 2: Modificar SL a breakeven (simular que ganó 10 pips)
        print("\n📌 PASO 2: Moviendo SL a breakeven...")
        manager.modify_position(
            ticket=ticket,
            sl=1.1000,  # Breakeven
            tp=1.1100   # Mantener TP
        )
        print(f"✅ SL modificado a breakeven")
        
        time.sleep(2)
        
        # PASO 3: Extender TP (simular que la tendencia continúa)
        print("\n📌 PASO 3: Extendiendo Take Profit...")
        manager.modify_position(
            ticket=ticket,
            sl=1.1000,
            tp=1.1150  # TP extendido a 150 pips
        )
        print(f"✅ TP extendido a 1.1150")
        
        time.sleep(2)
        
        # PASO 4: Cerrar posición
        print("\n📌 PASO 4: Cerrando posición...")
        result_close = manager.close_position(ticket=ticket)
        print(f"✅ Posición cerrada - Deal: {result_close.deal}")
        
        print(f"\n🎯 Ciclo completado:")
        print(f"   Apertura: Ticket {result_open.order}")
        print(f"   Cierre: Deal {result_close.deal}")


def ejemplo_11_manejo_errores():
    """
    Ejemplo 11: Manejo completo de errores
    """
    print("\n" + "="*80)
    print("EJEMPLO 11: Manejo de Errores")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        manager = OrderManager(connector)
        
        # Error 1: Volumen inválido
        print("\n🔍 Test 1: Volumen inválido (negativo)")
        try:
            request = OrderRequest(
                symbol="EURUSD",
                order_type=OrderType.BUY,
                volume=-0.1,  # ❌ Inválido
                price=1.1000
            )
            manager.send_market_order(request)
        except InvalidOrderParametersError as e:
            print(f"✅ Error capturado correctamente: {e}")
        
        # Error 2: Símbolo vacío
        print("\n🔍 Test 2: Símbolo vacío")
        try:
            request = OrderRequest(
                symbol="",  # ❌ Inválido
                order_type=OrderType.BUY,
                volume=0.1,
                price=1.1000
            )
            manager.send_market_order(request)
        except InvalidOrderParametersError as e:
            print(f"✅ Error capturado correctamente: {e}")
        
        # Error 3: Ticket inválido para modificar
        print("\n🔍 Test 3: Ticket inválido")
        try:
            manager.modify_position(
                ticket=-1,  # ❌ Inválido
                sl=1.0950,
                tp=1.1100
            )
        except ValueError as e:
            print(f"✅ Error capturado correctamente: {e}")
        
        # Error 4: Modificar sin especificar SL ni TP
        print("\n🔍 Test 4: Modificar sin cambios")
        try:
            manager.modify_position(
                ticket=123456,
                sl=0.0,  # No modificar
                tp=0.0   # No modificar
            )
        except InvalidOrderParametersError as e:
            print(f"✅ Error capturado correctamente: {e}")


def ejemplo_12_integracion_position_manager():
    """
    Ejemplo 12: Integración con PositionManager
    """
    print("\n" + "="*80)
    print("EJEMPLO 12: Integración con PositionManager")
    print("="*80)
    
    config = BrokerConfig(
        account_id="12345678",
        password="tu_password",
        server="Pepperstone-Demo"
    )
    
    with MT5Connector(config) as connector:
        order_mgr = OrderManager(connector)
        position_mgr = PositionManager(connector)
        
        # 1. Obtener posiciones del Bot 1
        print("\n📊 Consultando posiciones del Bot 1...")
        positions = position_mgr.get_positions_by_magic(100001)
        
        print(f"   Posiciones encontradas: {len(positions)}")
        
        # 2. Para cada posición, modificar SL a breakeven si tiene ganancia
        for pos in positions:
            print(f"\n📌 Posición {pos.ticket}:")
            print(f"   Símbolo: {pos.symbol}")
            print(f"   Tipo: {pos.type}")
            print(f"   Precio entrada: {pos.price_open}")
            print(f"   Precio actual: {pos.price_current}")
            print(f"   Profit: ${pos.profit:.2f}")
            
            # Si tiene ganancia, mover SL a breakeven
            if pos.profit > 0:
                print(f"   ✅ Tiene ganancia, moviendo SL a breakeven...")
                order_mgr.modify_position(
                    ticket=pos.ticket,
                    sl=pos.price_open,  # Breakeven
                    tp=pos.tp           # Mantener TP
                )
                print(f"   ✅ SL movido a {pos.price_open}")


# ============================================================================
# EJECUTAR EJEMPLOS
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "EJEMPLOS DE ORDER MANAGER - T09" + " "*27 + "║")
    print("╚" + "="*78 + "╝")
    
    print("\n⚠️  IMPORTANTE:")
    print("   - Cambia las credenciales por las tuyas reales")
    print("   - Ejecuta en cuenta DEMO primero")
    print("   - Algunos ejemplos requieren posiciones abiertas")
    print("   - Descomenta los ejemplos que quieras ejecutar")
    
    # Descomenta los ejemplos que quieras ejecutar:
    
    # ejemplo_1_orden_market_basica()
    # ejemplo_2_orden_market_sell()
    # ejemplo_3_orden_limit()
    # ejemplo_4_modificar_sl_tp()
    # ejemplo_5_cerrar_posicion()
    # ejemplo_6_cerrar_parcial()
    # ejemplo_7_cerrar_masivo_por_simbolo()
    # ejemplo_8_cerrar_masivo_por_magic()
    # ejemplo_9_dual_market_limit()
    # ejemplo_10_ciclo_completo()
    # ejemplo_11_manejo_errores()
    # ejemplo_12_integracion_position_manager()
    
    print("\n✅ Para ejecutar un ejemplo, descomenta la línea correspondiente")
    print("\n" + "="*80 + "\n")
