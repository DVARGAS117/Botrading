"""
Ejemplo de uso de IntradayIndicatorCalculator.

Demuestra cómo generar los paquetes táctico y estratégico con indicadores
pre-calculados correctamente para la estrategia INTRADAY, incluyendo
actualizaciones incrementales.
"""
import json
from datetime import datetime, timedelta
from src.core.mt5_connector import create_connector_from_credentials
from src.core.mt5_data_extractor import MT5DataExtractor
from src.bots.strategies.intraday.gemini_3_pro.bot_1.intraday_indicators import (
    IntradayIndicatorCalculator
)


def main():
    """Ejemplo de generación de paquetes INTRADAY."""
    
    print("=" * 70)
    print("EJEMPLO: Calculador de Indicadores INTRADAY")
    print("=" * 70)
    
    # Conectar a MT5
    print("\n1. Conectando a MetaTrader 5...")
    connector = create_connector_from_credentials()
    
    if not connector.connect():
        print("❌ Error: No se pudo conectar a MT5")
        return
    
    print("✅ Conectado a MT5")
    
    # Crear extractor de datos
    print("\n2. Creando extractor de datos...")
    data_extractor = MT5DataExtractor(connector)
    
    # Crear calculador de indicadores
    print("\n3. Creando calculador de indicadores INTRADAY...")
    calculator = IntradayIndicatorCalculator(data_extractor)
    
    # Símbolo a analizar
    symbol = "EURUSD"
    
    print(f"\n4. Generando paquetes para {symbol}...")
    print("-" * 70)
    
    # --- PAQUETE TÁCTICO (M15) ---
    print("\n📊 PAQUETE TÁCTICO (M15):")
    print("   Generando 200 velas con indicadores pre-calculados...")
    
    tactical_package = calculator.calculate_tactical_package(
        symbol=symbol,
        candles_to_return=200
    )
    
    print(f"   ✅ {len(tactical_package)} velas generadas")
    print("\n   Última vela del paquete:")
    last_m15 = tactical_package[-1]
    print(f"   - Timestamp: {last_m15.timestamp}")
    print(f"   - Close: {last_m15.close:.5f}")
    print(f"   - EMA 20: {last_m15.ema_20:.5f}" if last_m15.ema_20 else "   - EMA 20: None")
    print(f"   - EMA 200: {last_m15.ema_200:.5f}" if last_m15.ema_200 else "   - EMA 200: None")
    print(f"   - VWAP: {last_m15.vwap:.5f}" if last_m15.vwap else "   - VWAP: None")
    print(f"   - RSI 14: {last_m15.rsi_14:.2f}" if last_m15.rsi_14 else "   - RSI 14: None")
    print(f"   - ATR 14: {last_m15.atr_14:.5f}" if last_m15.atr_14 else "   - ATR 14: None")
    print(f"   - BB Upper: {last_m15.bb_upper:.5f}" if last_m15.bb_upper else "   - BB Upper: None")
    print(f"   - BB Lower: {last_m15.bb_lower:.5f}" if last_m15.bb_lower else "   - BB Lower: None")
    print(f"   - BB Width: {last_m15.bb_width:.5f}" if last_m15.bb_width else "   - BB Width: None")
    
    print("\n   Primera vela del paquete (verificar pre-cálculo):")
    first_m15 = tactical_package[0]
    print(f"   - Timestamp: {first_m15.timestamp}")
    print(f"   - EMA 200: {first_m15.ema_200:.5f}" if first_m15.ema_200 else "   - EMA 200: ❌ None (ERROR)")
    
    if first_m15.ema_200 is not None:
        print("   ✅ EMA 200 pre-calculada correctamente en vela #1")
    else:
        print("   ❌ ERROR: EMA 200 no está pre-calculada")
    
    # --- PAQUETE ESTRATÉGICO (D1) ---
    print("\n📊 PAQUETE ESTRATÉGICO (D1):")
    print("   Generando 30 velas con indicadores pre-calculados...")
    
    strategic_package = calculator.calculate_strategic_package(
        symbol=symbol,
        candles_to_return=30
    )
    
    print(f"   ✅ {len(strategic_package)} velas generadas")
    print("\n   Última vela del paquete:")
    last_d1 = strategic_package[-1]
    print(f"   - Date: {last_d1.date}")
    print(f"   - Close: {last_d1.close:.5f}")
    print(f"   - EMA 200: {last_d1.ema_200:.5f}" if last_d1.ema_200 else "   - EMA 200: None")
    print(f"   - ATR 14: {last_d1.atr_14:.5f}" if last_d1.atr_14 else "   - ATR 14: None")
    print(f"   - Prev Close: {last_d1.prev_close:.5f}" if last_d1.prev_close else "   - Prev Close: None")
    print(f"   - Prev High: {last_d1.prev_high:.5f}" if last_d1.prev_high else "   - Prev High: None")
    print(f"   - Prev Low: {last_d1.prev_low:.5f}" if last_d1.prev_low else "   - Prev Low: None")
    
    # --- PAQUETES COMPLETOS JSON ---
    print("\n5. Generando ambos paquetes en formato JSON...")
    
    full_packages = calculator.get_full_intraday_packages(symbol)
    
    print(f"   ✅ Paquetes generados")
    print(f"   - Paquete Táctico (M15): {len(full_packages['tactical_m15'])} velas")
    print(f"   - Paquete Estratégico (D1): {len(full_packages['strategic_d1'])} velas")
    
    # Guardar ejemplo en JSON (solo primeras 5 velas de cada uno)
    sample_output = {
        "symbol": symbol,
        "tactical_m15_sample": full_packages['tactical_m15'][-5:],  # Últimas 5 velas
        "strategic_d1_sample": full_packages['strategic_d1'][-5:],  # Últimas 5 velas
    }
    
    print("\n6. Ejemplo de JSON (últimas 5 velas de cada paquete):")
    print("-" * 70)
    print(json.dumps(sample_output, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Ejemplo completado exitosamente")
    print("=" * 70)
    
    # Desconectar
    connector.disconnect()


# ========== ACTUALIZACIÓN TÁCTICA INCREMENTAL ==========
def example_tactical_update():
    """Ejemplo de actualización táctica incremental."""
    
    print("\n" + "=" * 70)
    print("EJEMPLO: Actualización Táctica Incremental")
    print("=" * 70)
    
    # Conectar a MT5
    print("\n1. Conectando a MetaTrader 5...")
    connector = create_connector_from_credentials()
    
    if not connector.connect():
        print("❌ Error: No se pudo conectar a MT5")
        return
    
    print("✅ Conectado a MT5")
    
    # Crear extractor y calculador
    data_extractor = MT5DataExtractor(connector)
    calculator = IntradayIndicatorCalculator(data_extractor)
    
    symbol = "EURUSD"
    
    # Simular que pasaron 30 minutos desde la última consulta
    print("\n2. Simulando actualización incremental...")
    last_query_time = datetime.now() - timedelta(minutes=30)
    current_time = datetime.now()
    
    print(f"\n   Última consulta: {last_query_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Consulta actual: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Intervalo: {(current_time - last_query_time).seconds / 60:.0f} minutos")
    
    # Obtener solo velas nuevas
    print(f"\n3. Obteniendo solo velas nuevas de {symbol}...")
    tactical_update = calculator.calculate_tactical_update(
        symbol=symbol,
        last_timestamp=last_query_time,
        current_timestamp=current_time
    )
    
    print(f"\n📈 Actualización Táctica:")
    print(f"   - Velas nuevas: {len(tactical_update)}")
    
    if len(tactical_update) > 0:
        print(f"\n   Velas incluidas en la actualización:")
        for i, candle in enumerate(tactical_update, 1):
            print(f"      {i}. {candle.timestamp}")
            print(f"         Close: {candle.close:.5f}")
            print(f"         EMA 200: {candle.ema_200:.5f if candle.ema_200 else 'N/A'}")
            print(f"         RSI 14: {candle.rsi_14:.2f if candle.rsi_14 else 'N/A'}")
    else:
        print("   ⚠️  No hay velas nuevas cerradas desde la última consulta")
    
    print("\n4. USO EN PRODUCCIÓN:")
    print("   # Consulta inicial")
    print("   packages = calculator.get_full_intraday_packages(symbol='EURUSD')")
    print("   # ... enviar a Gemini, registrar en IAQueryRepository ...")
    print("\n   # Actualización periódica (cada 15 min)")
    print("   last_query = ia_repo.get_queries_by_operation_id(op_id)[0]")
    print("   update = calculator.calculate_tactical_update(")
    print("       symbol='EURUSD',")
    print("       last_timestamp=last_query.created_at")
    print("   )")
    print("   # ... enviar solo velas nuevas a Gemini ...")
    
    print("\n" + "=" * 70)
    
    connector.disconnect()


if __name__ == "__main__":
    main()
    example_tactical_update()
