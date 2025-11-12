"""
Ejemplos de uso del módulo LotAdjuster - T30

Este script demuestra cómo usar LotAdjuster para ajustar tamaños de lote
a las restricciones del símbolo (min, max, step).

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T30 - Ajuste de lote a step y límites del símbolo
"""

from src.core.lot_adjuster import (
    LotAdjuster,
    SymbolSpecification,
    AdjustedLot
)
import logging


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# =============================================================================
# EJEMPLO 1: USO BÁSICO CON EURUSD
# =============================================================================

def ejemplo_1_basico():
    """Ejemplo básico de ajuste de lote con EURUSD"""
    print("\n" + "="*70)
    print("EJEMPLO 1: Uso Básico con EURUSD")
    print("="*70)
    
    # Crear LotAdjuster
    adjuster = LotAdjuster()
    
    # Especificaciones de EURUSD
    eurusd_spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    
    # Lote calculado por PositionSizer
    calculated_lot = 0.4567
    
    # Ajustar lote
    result = adjuster.adjust_lot(calculated_lot, eurusd_spec)
    
    print(f"\nLote original:  {result.original_lot}")
    print(f"Lote ajustado:  {result.adjusted_lot}")
    print(f"Fue ajustado:   {result.was_adjusted}")
    print(f"Razón:          {result.reason}")
    print(f"Símbolo:        {result.symbol}")
    
    # Convertir a dict
    print(f"\nComo dict:")
    print(result.to_dict())


# =============================================================================
# EJEMPLO 2: LOTE DEBAJO DEL MÍNIMO
# =============================================================================

def ejemplo_2_lote_minimo():
    """Ejemplo de lote que está debajo del mínimo permitido"""
    print("\n" + "="*70)
    print("EJEMPLO 2: Lote Debajo del Mínimo")
    print("="*70)
    
    adjuster = LotAdjuster()
    
    eurusd_spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    
    # Lote muy pequeño (cuenta muy pequeña o SL muy amplio)
    small_lot = 0.005
    
    result = adjuster.adjust_lot(small_lot, eurusd_spec)
    
    print(f"\nLote calculado: {small_lot}")
    print(f"Mínimo del símbolo: {eurusd_spec.volume_min}")
    print(f"Lote ajustado: {result.adjusted_lot}")
    print(f"Razón: {result.reason}")


# =============================================================================
# EJEMPLO 3: LOTE SOBRE EL MÁXIMO
# =============================================================================

def ejemplo_3_lote_maximo():
    """Ejemplo de lote que excede el máximo permitido"""
    print("\n" + "="*70)
    print("EJEMPLO 3: Lote Sobre el Máximo")
    print("="*70)
    
    adjuster = LotAdjuster()
    
    eurusd_spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    
    # Lote muy grande (cuenta muy grande o SL muy estrecho)
    large_lot = 150.0
    
    result = adjuster.adjust_lot(large_lot, eurusd_spec)
    
    print(f"\nLote calculado: {large_lot}")
    print(f"Máximo del símbolo: {eurusd_spec.volume_max}")
    print(f"Lote ajustado: {result.adjusted_lot}")
    print(f"Razón: {result.reason}")


# =============================================================================
# EJEMPLO 4: DIFERENTES SÍMBOLOS
# =============================================================================

def ejemplo_4_diferentes_simbolos():
    """Ejemplo con diferentes tipos de símbolos (Forex, Metales, Índices)"""
    print("\n" + "="*70)
    print("EJEMPLO 4: Diferentes Símbolos")
    print("="*70)
    
    adjuster = LotAdjuster()
    
    # EURUSD (Forex)
    eurusd_spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    
    # XAUUSD (Oro)
    xauusd_spec = SymbolSpecification(
        symbol="XAUUSD",
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01
    )
    
    # US30 (Índice Dow Jones)
    us30_spec = SymbolSpecification(
        symbol="US30",
        volume_min=0.1,
        volume_max=10.0,
        volume_step=0.1
    )
    
    test_lot = 0.456
    
    print(f"\nLote calculado: {test_lot}")
    print("\nAjustes por símbolo:")
    
    # EURUSD
    result = adjuster.adjust_lot(test_lot, eurusd_spec)
    print(f"  {eurusd_spec.symbol}: {result.adjusted_lot}")
    
    # XAUUSD
    result = adjuster.adjust_lot(test_lot, xauusd_spec)
    print(f"  {xauusd_spec.symbol}: {result.adjusted_lot}")
    
    # US30 (el mínimo es 0.1, así que se ajusta)
    result = adjuster.adjust_lot(test_lot, us30_spec)
    print(f"  {us30_spec.symbol}: {result.adjusted_lot}")


# =============================================================================
# EJEMPLO 5: VALIDACIÓN PREVIA
# =============================================================================

def ejemplo_5_validacion_previa():
    """Ejemplo de validación de lote antes de operar"""
    print("\n" + "="*70)
    print("EJEMPLO 5: Validación Previa")
    print("="*70)
    
    adjuster = LotAdjuster()
    
    eurusd_spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    
    lots_to_check = [0.50, 0.005, 150.0, 0.456]
    
    print("\nValidando lotes:")
    for lot in lots_to_check:
        is_valid = adjuster.is_valid_lot(lot, eurusd_spec)
        status = "✓ VÁLIDO" if is_valid else "✗ INVÁLIDO"
        print(f"  Lote {lot:6.3f}: {status}")
        
        if not is_valid:
            result = adjuster.adjust_lot(lot, eurusd_spec)
            print(f"    → Ajustado a: {result.adjusted_lot}")


# =============================================================================
# EJEMPLO 6: STEP IRREGULAR
# =============================================================================

def ejemplo_6_step_irregular():
    """Ejemplo con step irregular (no es 0.01)"""
    print("\n" + "="*70)
    print("EJEMPLO 6: Step Irregular")
    print("="*70)
    
    adjuster = LotAdjuster()
    
    # Símbolo con step de 0.05
    exotic_spec = SymbolSpecification(
        symbol="EXOTIC",
        volume_min=0.05,
        volume_max=5.0,
        volume_step=0.05
    )
    
    test_lots = [0.23, 0.47, 0.98]
    
    print(f"\nStep del símbolo: {exotic_spec.volume_step}")
    print("\nAjustes:")
    
    for lot in test_lots:
        result = adjuster.adjust_lot(lot, exotic_spec)
        print(f"  {lot:.2f} → {result.adjusted_lot:.2f}")


# =============================================================================
# EJEMPLO 7: BATCH ADJUSTMENT
# =============================================================================

def ejemplo_7_batch_adjustment():
    """Ejemplo de ajuste de múltiples lotes a la vez"""
    print("\n" + "="*70)
    print("EJEMPLO 7: Ajuste en Lote (Batch)")
    print("="*70)
    
    adjuster = LotAdjuster()
    
    eurusd_spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    
    # Múltiples lotes calculados
    calculated_lots = [0.005, 0.456, 0.789, 1.234, 150.0]
    
    print("\nAjustando múltiples lotes:")
    print(f"{'Original':<10} {'Ajustado':<10} {'¿Cambió?':<10} {'Razón'}")
    print("-" * 70)
    
    for lot in calculated_lots:
        result = adjuster.adjust_lot(lot, eurusd_spec)
        changed = "Sí" if result.was_adjusted else "No"
        print(f"{lot:<10.3f} {result.adjusted_lot:<10.2f} {changed:<10} {result.reason[:30]}")


# =============================================================================
# EJEMPLO 8: INTEGRACIÓN CON POSITION SIZER
# =============================================================================

def ejemplo_8_integracion_position_sizer():
    """Ejemplo de integración con PositionSizer"""
    print("\n" + "="*70)
    print("EJEMPLO 8: Integración con PositionSizer")
    print("="*70)
    
    from src.core.position_sizer import (
        PositionSizer,
        RiskParameters,
        SymbolSpecification as PosAdjusterSymbolSpec
    )
    
    # PositionSizer ahora usa LotAdjuster internamente
    sizer = PositionSizer()
    
    # Especificaciones de EURUSD para PositionSizer
    eurusd_spec = PosAdjusterSymbolSpec(
        symbol="EURUSD",
        point=0.00001,
        tick_size=0.00001,
        tick_value=1.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        contract_size=100000
    )
    
    # Parámetros de riesgo
    risk_params = RiskParameters(
        account_balance=10000.0,
        risk_percentage=2.0,
        entry_price=1.1000,
        stop_loss=1.0950,  # 50 pips
        symbol_spec=eurusd_spec
    )
    
    # PositionSizer calcula y ajusta automáticamente
    position_size = sizer.calculate_lot_size(risk_params)
    
    print(f"\nCuenta: ${risk_params.account_balance:,.2f}")
    print(f"Riesgo: {risk_params.risk_percentage}%")
    print(f"SL Distance: 50 pips")
    print(f"\nLote calculado y ajustado: {position_size.lot_size}")
    print(f"Riesgo en $: ${position_size.risk_amount:.2f}")


# =============================================================================
# EJEMPLO 9: CASOS EDGE
# =============================================================================

def ejemplo_9_casos_edge():
    """Ejemplo de casos edge y límites"""
    print("\n" + "="*70)
    print("EJEMPLO 9: Casos Edge")
    print("="*70)
    
    adjuster = LotAdjuster()
    
    eurusd_spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    
    print("\nCasos edge:")
    
    # Exactamente en el mínimo
    result = adjuster.adjust_lot(0.01, eurusd_spec)
    print(f"  Exactamente mínimo (0.01): ajustado={result.was_adjusted}")
    
    # Exactamente en el máximo
    result = adjuster.adjust_lot(100.0, eurusd_spec)
    print(f"  Exactamente máximo (100.0): ajustado={result.was_adjusted}")
    
    # Lote extremadamente pequeño
    result = adjuster.adjust_lot(0.0001, eurusd_spec)
    print(f"  Extremadamente pequeño (0.0001): → {result.adjusted_lot}")
    
    # Lote extremadamente grande
    result = adjuster.adjust_lot(999999.99, eurusd_spec)
    print(f"  Extremadamente grande (999999.99): → {result.adjusted_lot}")
    
    # Precisión flotante
    result = adjuster.adjust_lot(1/3, eurusd_spec)  # 0.333333...
    print(f"  1/3 (0.333...): → {result.adjusted_lot}")


# =============================================================================
# EJEMPLO 10: MANEJO DE ERRORES
# =============================================================================

def ejemplo_10_manejo_errores():
    """Ejemplo de manejo de errores y validaciones"""
    print("\n" + "="*70)
    print("EJEMPLO 10: Manejo de Errores")
    print("="*70)
    
    from src.core.lot_adjuster import (
        InvalidLotSizeError,
        InvalidSymbolSpecError
    )
    
    adjuster = LotAdjuster()
    
    eurusd_spec = SymbolSpecification(
        symbol="EURUSD",
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01
    )
    
    print("\nProbando validaciones:")
    
    # Error: Lote negativo
    try:
        adjuster.adjust_lot(-0.50, eurusd_spec)
    except InvalidLotSizeError as e:
        print(f"  ✓ Lote negativo detectado: {e}")
    
    # Error: Lote cero
    try:
        adjuster.adjust_lot(0.0, eurusd_spec)
    except InvalidLotSizeError as e:
        print(f"  ✓ Lote cero detectado: {e}")
    
    # Error: SymbolSpec inválida (volume_min > volume_max)
    try:
        bad_spec = SymbolSpecification(
            symbol="BAD",
            volume_min=100.0,
            volume_max=10.0,
            volume_step=0.01
        )
    except InvalidSymbolSpecError as e:
        print(f"  ✓ SymbolSpec inválida detectada: {e}")


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """Ejecutar todos los ejemplos"""
    print("\n" + "="*70)
    print(" EJEMPLOS DE USO: LotAdjuster")
    print("="*70)
    
    ejemplo_1_basico()
    ejemplo_2_lote_minimo()
    ejemplo_3_lote_maximo()
    ejemplo_4_diferentes_simbolos()
    ejemplo_5_validacion_previa()
    ejemplo_6_step_irregular()
    ejemplo_7_batch_adjustment()
    ejemplo_8_integracion_position_sizer()
    ejemplo_9_casos_edge()
    ejemplo_10_manejo_errores()
    
    print("\n" + "="*70)
    print(" FIN DE LOS EJEMPLOS")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
