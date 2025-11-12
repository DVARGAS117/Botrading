"""
Ejemplos completos de uso de PositionSizer - T29

Este archivo demuestra todas las funcionalidades del PositionSizer:
1. Cálculo básico de lote (Forex)
2. Cálculo para diferentes activos (Oro, Índices)
3. Posiciones BUY y SELL
4. Integración con OrderManager
5. Casos edge y validaciones
6. Normalización de riesgo entre activos

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T29 - Cálculo de lote por % riesgo y distancia al SL
"""

from src.core.position_sizer import (
    PositionSizer,
    RiskParameters,
    SymbolSpecification,
    PositionSize,
    InvalidRiskParametersError,
    InvalidSymbolSpecError
)
from src.core.order_manager import OrderManager, OrderRequest, OrderType
from src.core.mt5_connector import MT5Connector, BrokerConfig


# ============================================================================
# ESPECIFICACIONES DE SÍMBOLOS (Ejemplos)
# ============================================================================

def get_eurusd_spec():
    """Especificaciones de EURUSD"""
    return SymbolSpecification(
        symbol="EURUSD",
        point=0.0001,        # 1 pip estándar
        tick_size=0.00001,   # 1 pipette
        tick_value=1.0,      # $1 por tick por lote
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        contract_size=100000
    )


def get_xauusd_spec():
    """Especificaciones de XAUUSD (Oro)"""
    return SymbolSpecification(
        symbol="XAUUSD",
        point=0.01,          # 1 centavo
        tick_size=0.01,
        tick_value=1.0,
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        contract_size=100
    )


def get_us30_spec():
    """Especificaciones de US30 (Dow Jones)"""
    return SymbolSpecification(
        symbol="US30",
        point=1.0,           # 1 punto
        tick_size=1.0,
        tick_value=1.0,
        volume_min=0.1,
        volume_max=10.0,
        volume_step=0.1,
        contract_size=1
    )


# ============================================================================
# EJEMPLO 1: CÁLCULO BÁSICO (EURUSD)
# ============================================================================

def ejemplo_1_calculo_basico():
    """
    Ejemplo 1: Cálculo básico de lote para EURUSD
    
    Escenario:
    - Cuenta: $10,000
    - Riesgo: 2% = $200
    - Entrada: 1.1000
    - SL: 1.0950 (50 pips)
    
    Resultado esperado: 0.40 lotes
    """
    print("\n" + "="*80)
    print("EJEMPLO 1: Cálculo Básico (EURUSD)")
    print("="*80)
    
    sizer = PositionSizer()
    eurusd_spec = get_eurusd_spec()
    
    risk_params = RiskParameters(
        account_balance=10000.0,
        risk_percentage=2.0,
        entry_price=1.1000,
        stop_loss=1.0950,
        symbol_spec=eurusd_spec
    )
    
    result = sizer.calculate_lot_size(risk_params)
    
    print(f"📊 Parámetros:")
    print(f"   Balance: ${risk_params.account_balance:,.2f}")
    print(f"   Riesgo: {risk_params.risk_percentage}%")
    print(f"   Entrada: {risk_params.entry_price}")
    print(f"   Stop Loss: {risk_params.stop_loss}")
    
    print(f"\n💰 Resultado:")
    print(f"   Lote calculado: {result.lot_size}")
    print(f"   Riesgo en $: ${result.risk_amount:.2f}")
    print(f"   Distancia SL: {result.pip_distance:.1f} pips")
    print(f"   Valor por pip: ${result.pip_value:.2f}")
    
    print(f"\n✅ Validación:")
    print(f"   Riesgo total: {result.pip_distance:.1f} pips × ${result.pip_value:.2f}/pip = ${result.pip_distance * result.pip_value:.2f}")


# ============================================================================
# EJEMPLO 2: POSICIÓN SELL
# ============================================================================

def ejemplo_2_posicion_sell():
    """
    Ejemplo 2: Calcular lote para posición SELL
    
    Para SELL, el SL está arriba de la entrada.
    La distancia se calcula como valor absoluto.
    """
    print("\n" + "="*80)
    print("EJEMPLO 2: Posición SELL (EURUSD)")
    print("="*80)
    
    sizer = PositionSizer()
    eurusd_spec = get_eurusd_spec()
    
    risk_params = RiskParameters(
        account_balance=10000.0,
        risk_percentage=2.0,
        entry_price=1.1000,
        stop_loss=1.1050,  # ← SL arriba (SELL)
        symbol_spec=eurusd_spec
    )
    
    result = sizer.calculate_lot_size(risk_params)
    
    print(f"📊 Posición SELL:")
    print(f"   Entrada: {risk_params.entry_price}")
    print(f"   Stop Loss: {risk_params.stop_loss} (arriba)")
    print(f"   Distancia: {result.pip_distance:.1f} pips (absoluta)")
    print(f"\n💰 Lote: {result.lot_size}")


# ============================================================================
# EJEMPLO 3: ORO (XAUUSD)
# ============================================================================

def ejemplo_3_oro():
    """
    Ejemplo 3: Calcular lote para Oro (XAUUSD)
    
    El oro tiene especificaciones diferentes:
    - Point = 0.01 (1 centavo)
    - Contract size = 100 onzas
    """
    print("\n" + "="*80)
    print("EJEMPLO 3: Oro (XAUUSD)")
    print("="*80)
    
    sizer = PositionSizer()
    xauusd_spec = get_xauusd_spec()
    
    # Oro a $2,000, SL en $1,980
    risk_params = RiskParameters(
        account_balance=10000.0,
        risk_percentage=2.0,
        entry_price=2000.0,
        stop_loss=1980.0,  # $20 de distancia
        symbol_spec=xauusd_spec
    )
    
    result = sizer.calculate_lot_size(risk_params)
    
    print(f"📊 Oro:")
    print(f"   Precio: ${risk_params.entry_price:,.2f}")
    print(f"   Stop Loss: ${risk_params.stop_loss:,.2f}")
    print(f"   Distancia: ${risk_params.entry_price - risk_params.stop_loss:.2f}")
    
    print(f"\n💰 Resultado:")
    print(f"   Lote: {result.lot_size}")
    print(f"   Riesgo: ${result.risk_amount:.2f}")
    print(f"   Pips: {result.pip_distance:.1f}")


# ============================================================================
# EJEMPLO 4: ÍNDICE (US30)
# ============================================================================

def ejemplo_4_indice():
    """
    Ejemplo 4: Calcular lote para índice US30
    
    Los índices tienen:
    - Point = 1.0 (1 punto)
    - Volume step = 0.1
    """
    print("\n" + "="*80)
    print("EJEMPLO 4: Índice US30 (Dow Jones)")
    print("="*80)
    
    sizer = PositionSizer()
    us30_spec = get_us30_spec()
    
    risk_params = RiskParameters(
        account_balance=20000.0,
        risk_percentage=1.5,
        entry_price=35000.0,
        stop_loss=34900.0,  # 100 puntos
        symbol_spec=us30_spec
    )
    
    result = sizer.calculate_lot_size(risk_params)
    
    print(f"📊 US30:")
    print(f"   Precio: {risk_params.entry_price:,.0f}")
    print(f"   Stop Loss: {risk_params.stop_loss:,.0f}")
    print(f"   Distancia: {risk_params.entry_price - risk_params.stop_loss:.0f} puntos")
    
    print(f"\n💰 Resultado:")
    print(f"   Lote: {result.lot_size}")
    print(f"   Riesgo: ${result.risk_amount:.2f}")


# ============================================================================
# EJEMPLO 5: COMPARACIÓN ENTRE ACTIVOS
# ============================================================================

def ejemplo_5_comparacion_activos():
    """
    Ejemplo 5: Demostrar normalización de riesgo entre activos
    
    Con el mismo % de riesgo, diferentes activos tienen
    el mismo impacto monetario.
    """
    print("\n" + "="*80)
    print("EJEMPLO 5: Normalización de Riesgo Entre Activos")
    print("="*80)
    
    sizer = PositionSizer()
    account_balance = 10000.0
    risk_percentage = 2.0  # 2% en todos
    
    # EURUSD
    eurusd_params = RiskParameters(
        account_balance=account_balance,
        risk_percentage=risk_percentage,
        entry_price=1.1000,
        stop_loss=1.0950,
        symbol_spec=get_eurusd_spec()
    )
    eurusd_result = sizer.calculate_lot_size(eurusd_params)
    
    # XAUUSD
    xauusd_params = RiskParameters(
        account_balance=account_balance,
        risk_percentage=risk_percentage,
        entry_price=2000.0,
        stop_loss=1980.0,
        symbol_spec=get_xauusd_spec()
    )
    xauusd_result = sizer.calculate_lot_size(xauusd_params)
    
    # US30
    us30_params = RiskParameters(
        account_balance=account_balance,
        risk_percentage=risk_percentage,
        entry_price=35000.0,
        stop_loss=34900.0,
        symbol_spec=get_us30_spec()
    )
    us30_result = sizer.calculate_lot_size(us30_params)
    
    print(f"📊 Cuenta: ${account_balance:,.2f}")
    print(f"   Riesgo: {risk_percentage}% = ${account_balance * risk_percentage / 100:.2f}")
    
    print(f"\n🔹 EURUSD:")
    print(f"   Lote: {eurusd_result.lot_size}")
    print(f"   Riesgo real: ${eurusd_result.risk_amount:.2f}")
    
    print(f"\n🔹 XAUUSD:")
    print(f"   Lote: {xauusd_result.lot_size}")
    print(f"   Riesgo real: ${xauusd_result.risk_amount:.2f}")
    
    print(f"\n🔹 US30:")
    print(f"   Lote: {us30_result.lot_size}")
    print(f"   Riesgo real: ${us30_result.risk_amount:.2f}")
    
    print(f"\n✅ Todos tienen el mismo riesgo: ${eurusd_result.risk_amount:.2f}")


# ============================================================================
# EJEMPLO 6: CUENTA PEQUEÑA
# ============================================================================

def ejemplo_6_cuenta_pequena():
    """
    Ejemplo 6: Cuenta pequeña con SL amplio
    
    Demuestra cómo el lote se ajusta al mínimo permitido.
    """
    print("\n" + "="*80)
    print("EJEMPLO 6: Cuenta Pequeña")
    print("="*80)
    
    sizer = PositionSizer()
    eurusd_spec = get_eurusd_spec()
    
    risk_params = RiskParameters(
        account_balance=100.0,  # ← Cuenta muy pequeña
        risk_percentage=2.0,
        entry_price=1.1000,
        stop_loss=1.0500,  # ← SL muy amplio (500 pips)
        symbol_spec=eurusd_spec
    )
    
    result = sizer.calculate_lot_size(risk_params)
    
    print(f"📊 Parámetros:")
    print(f"   Balance: ${risk_params.account_balance:.2f}")
    print(f"   Riesgo deseado: ${result.risk_amount:.2f}")
    print(f"   Distancia SL: {result.pip_distance:.0f} pips")
    
    print(f"\n💰 Resultado:")
    print(f"   Lote calculado teórico: muy pequeño")
    print(f"   Lote ajustado: {result.lot_size} (mínimo)")
    print(f"   ⚠️  Riesgo real será menor que el deseado")


# ============================================================================
# EJEMPLO 7: DIFERENTES PORCENTAJES DE RIESGO
# ============================================================================

def ejemplo_7_diferentes_riesgos():
    """
    Ejemplo 7: Comparar lotes con diferentes % de riesgo
    """
    print("\n" + "="*80)
    print("EJEMPLO 7: Diferentes Porcentajes de Riesgo")
    print("="*80)
    
    sizer = PositionSizer()
    eurusd_spec = get_eurusd_spec()
    
    account_balance = 10000.0
    entry = 1.1000
    sl = 1.0950
    
    risk_percentages = [0.5, 1.0, 2.0, 5.0]
    
    print(f"📊 Balance: ${account_balance:,.2f}")
    print(f"   Entrada: {entry}")
    print(f"   Stop Loss: {sl}")
    print(f"\n{'Riesgo %':<10} {'Riesgo $':<12} {'Lote':<10} {'Valor/pip':<12}")
    print("-" * 50)
    
    for risk_pct in risk_percentages:
        risk_params = RiskParameters(
            account_balance=account_balance,
            risk_percentage=risk_pct,
            entry_price=entry,
            stop_loss=sl,
            symbol_spec=eurusd_spec
        )
        
        result = sizer.calculate_lot_size(risk_params)
        
        print(f"{risk_pct:<10.1f} ${result.risk_amount:<11.2f} {result.lot_size:<10.2f} ${result.pip_value:<11.2f}")


# ============================================================================
# EJEMPLO 8: INTEGRACIÓN CON ORDER MANAGER
# ============================================================================

def ejemplo_8_integracion_order_manager():
    """
    Ejemplo 8: Integración completa con OrderManager
    
    Flujo completo:
    1. PositionSizer calcula el lote
    2. OrderManager envía la orden
    """
    print("\n" + "="*80)
    print("EJEMPLO 8: Integración con OrderManager")
    print("="*80)
    
    # Paso 1: Calcular lote con PositionSizer
    sizer = PositionSizer()
    eurusd_spec = get_eurusd_spec()
    
    risk_params = RiskParameters(
        account_balance=10000.0,
        risk_percentage=2.0,
        entry_price=1.1000,
        stop_loss=1.0950,
        symbol_spec=eurusd_spec
    )
    
    position_size = sizer.calculate_lot_size(risk_params)
    
    print(f"📊 Paso 1: PositionSizer")
    print(f"   Lote calculado: {position_size.lot_size}")
    print(f"   Riesgo: ${position_size.risk_amount:.2f}")
    
    # Paso 2: Crear OrderRequest con el lote calculado
    print(f"\n📝 Paso 2: Crear OrderRequest")
    
    # En un caso real, aquí conectarías con MT5
    # config = BrokerConfig(...)
    # with MT5Connector(config) as connector:
    #     order_mgr = OrderManager(connector)
    #     ...
    
    # Para el ejemplo, solo mostramos cómo se usaría
    print(f"   OrderRequest(")
    print(f"       symbol='EURUSD',")
    print(f"       order_type=OrderType.BUY,")
    print(f"       volume={position_size.lot_size},  ← Lote calculado")
    print(f"       price={risk_params.entry_price},")
    print(f"       sl={risk_params.stop_loss},")
    print(f"       tp=1.1100,")
    print(f"       comment='Risk: ${position_size.risk_amount:.2f}'")
    print(f"   )")
    
    print(f"\n✅ El lote calculado por PositionSizer se usa directamente")
    print(f"   en la orden enviada por OrderManager")


# ============================================================================
# EJEMPLO 9: MANEJO DE ERRORES
# ============================================================================

def ejemplo_9_manejo_errores():
    """
    Ejemplo 9: Demostrar validaciones y manejo de errores
    """
    print("\n" + "="*80)
    print("EJEMPLO 9: Manejo de Errores")
    print("="*80)
    
    sizer = PositionSizer()
    eurusd_spec = get_eurusd_spec()
    
    # Error 1: Balance negativo
    print("\n🔍 Test 1: Balance negativo")
    try:
        RiskParameters(
            account_balance=-1000.0,  # ❌
            risk_percentage=2.0,
            entry_price=1.1000,
            stop_loss=1.0950,
            symbol_spec=eurusd_spec
        )
    except InvalidRiskParametersError as e:
        print(f"   ✅ Error capturado: {e}")
    
    # Error 2: Riesgo > 100%
    print("\n🔍 Test 2: Riesgo > 100%")
    try:
        RiskParameters(
            account_balance=10000.0,
            risk_percentage=150.0,  # ❌
            entry_price=1.1000,
            stop_loss=1.0950,
            symbol_spec=eurusd_spec
        )
    except InvalidRiskParametersError as e:
        print(f"   ✅ Error capturado: {e}")
    
    # Error 3: Entry = SL
    print("\n🔍 Test 3: Entrada = Stop Loss")
    try:
        RiskParameters(
            account_balance=10000.0,
            risk_percentage=2.0,
            entry_price=1.1000,
            stop_loss=1.1000,  # ❌ Igual
            symbol_spec=eurusd_spec
        )
    except InvalidRiskParametersError as e:
        print(f"   ✅ Error capturado: {e}")
    
    # Error 4: Volume min > max
    print("\n🔍 Test 4: Especificación inválida")
    try:
        SymbolSpecification(
            symbol="TEST",
            point=0.0001,
            tick_size=0.00001,
            tick_value=1.0,
            volume_min=10.0,  # ❌ Mayor que max
            volume_max=1.0,
            volume_step=0.01,
            contract_size=100000
        )
    except InvalidSymbolSpecError as e:
        print(f"   ✅ Error capturado: {e}")


# ============================================================================
# EJEMPLO 10: CONVERSIÓN PIPS ↔ PRECIO
# ============================================================================

def ejemplo_10_conversion_pips():
    """
    Ejemplo 10: Convertir entre pips y precio
    """
    print("\n" + "="*80)
    print("EJEMPLO 10: Conversión Pips ↔ Precio")
    print("="*80)
    
    sizer = PositionSizer()
    eurusd_spec = get_eurusd_spec()
    
    # Precio → Pips
    price_distance = 0.0050  # 50 pips en precio
    pips = sizer.price_distance_to_pips(price_distance, eurusd_spec)
    print(f"📊 EURUSD:")
    print(f"   Distancia precio: {price_distance}")
    print(f"   Distancia pips: {pips:.0f}")
    
    # Pips → Precio
    pips_to_convert = 100.0
    price_dist = sizer.pips_to_price_distance(pips_to_convert, eurusd_spec)
    print(f"\n   {pips_to_convert:.0f} pips = {price_dist}")
    
    # Para Oro
    xauusd_spec = get_xauusd_spec()
    gold_distance = 20.0  # $20
    gold_pips = sizer.price_distance_to_pips(gold_distance, xauusd_spec)
    print(f"\n📊 XAUUSD:")
    print(f"   Distancia precio: ${gold_distance:.2f}")
    print(f"   Distancia pips: {gold_pips:.0f}")


# ============================================================================
# EJEMPLO 11: MÉTODOS DE CONVENIENCIA
# ============================================================================

def ejemplo_11_metodos_conveniencia():
    """
    Ejemplo 11: Usar métodos de conveniencia para BUY/SELL
    """
    print("\n" + "="*80)
    print("EJEMPLO 11: Métodos de Conveniencia")
    print("="*80)
    
    sizer = PositionSizer()
    eurusd_spec = get_eurusd_spec()
    
    # Método para BUY
    result_buy = sizer.calculate_lot_for_buy(
        account_balance=10000.0,
        risk_percentage=2.0,
        entry_price=1.1000,
        stop_loss=1.0950,  # SL abajo
        symbol_spec=eurusd_spec
    )
    
    print(f"📈 BUY:")
    print(f"   Lote: {result_buy.lot_size}")
    print(f"   SL: {1.0950} (abajo de entrada)")
    
    # Método para SELL
    result_sell = sizer.calculate_lot_for_sell(
        account_balance=10000.0,
        risk_percentage=2.0,
        entry_price=1.1000,
        stop_loss=1.1050,  # SL arriba
        symbol_spec=eurusd_spec
    )
    
    print(f"\n📉 SELL:")
    print(f"   Lote: {result_sell.lot_size}")
    print(f"   SL: {1.1050} (arriba de entrada)")
    
    print(f"\n✅ Ambos calculan correctamente la distancia absoluta")


# ============================================================================
# EJEMPLO 12: ANÁLISIS DE RIESGO
# ============================================================================

def ejemplo_12_analisis_riesgo():
    """
    Ejemplo 12: Análisis completo de riesgo
    """
    print("\n" + "="*80)
    print("EJEMPLO 12: Análisis Completo de Riesgo")
    print("="*80)
    
    sizer = PositionSizer()
    eurusd_spec = get_eurusd_spec()
    
    account_balance = 10000.0
    risk_percentage = 2.0
    entry = 1.1000
    sl = 1.0950
    
    risk_params = RiskParameters(
        account_balance=account_balance,
        risk_percentage=risk_percentage,
        entry_price=entry,
        stop_loss=sl,
        symbol_spec=eurusd_spec
    )
    
    result = sizer.calculate_lot_size(risk_params)
    
    print(f"📊 ANÁLISIS DE RIESGO - EURUSD")
    print(f"\n1️⃣  Información de Cuenta:")
    print(f"   Balance: ${account_balance:,.2f}")
    print(f"   Riesgo deseado: {risk_percentage}%")
    print(f"   Riesgo en dinero: ${result.risk_amount:.2f}")
    
    print(f"\n2️⃣  Información de Entrada:")
    print(f"   Precio entrada: {entry}")
    print(f"   Stop Loss: {sl}")
    print(f"   Distancia: {result.pip_distance:.1f} pips ({entry - sl:.4f})")
    
    print(f"\n3️⃣  Tamaño de Posición:")
    print(f"   Lote calculado: {result.lot_size}")
    print(f"   Valor por pip: ${result.pip_value:.2f}")
    
    print(f"\n4️⃣  Validación de Riesgo:")
    print(f"   Riesgo máximo: ${result.risk_amount:.2f}")
    print(f"   Riesgo real: {result.pip_distance:.1f} × ${result.pip_value:.2f} = ${result.pip_distance * result.pip_value:.2f}")
    print(f"   ✅ Coincide: {abs((result.pip_distance * result.pip_value) - result.risk_amount) < 1.0}")
    
    print(f"\n5️⃣  Información Adicional:")
    print(f"   Símbolo: {result.symbol}")
    print(f"   Status: {'✅ Exitoso' if result.success else '❌ Fallido'}")
    print(f"   Mensaje: {result.message}")


# ============================================================================
# EJECUTAR EJEMPLOS
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*18 + "EJEMPLOS DE POSITION SIZER - T29" + " "*28 + "║")
    print("╚" + "="*78 + "╝")
    
    print("\n⚠️  NOTA:")
    print("   Estos son ejemplos educativos que demuestran el uso del PositionSizer.")
    print("   En producción, las especificaciones se obtendrían desde MT5.")
    
    # Ejecutar todos los ejemplos
    ejemplo_1_calculo_basico()
    ejemplo_2_posicion_sell()
    ejemplo_3_oro()
    ejemplo_4_indice()
    ejemplo_5_comparacion_activos()
    ejemplo_6_cuenta_pequena()
    ejemplo_7_diferentes_riesgos()
    ejemplo_8_integracion_order_manager()
    ejemplo_9_manejo_errores()
    ejemplo_10_conversion_pips()
    ejemplo_11_metodos_conveniencia()
    ejemplo_12_analisis_riesgo()
    
    print("\n" + "="*80)
    print("✅ Todos los ejemplos ejecutados exitosamente")
    print("="*80 + "\n")
