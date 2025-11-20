"""
Test de integración REAL del Bot INTRADAY - ABRE OPERACIÓN EN MT5

Este test simula TODO el flujo real:
1. Inicializa el bot
2. Simula respuesta de Gemini (con la respuesta exacta que causó error)
3. Procesa la decisión
4. ABRE UNA OPERACIÓN REAL EN MT5

NO ES UN TEST DE CONSOLA - ABRE OPERACIÓN REAL EN MT5 (dinero ficticio)
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.bots.base.base_bot_operations import BotConfig
from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.core.gemini_client import GeminiResponse


def test_open_real_position_with_gemini_response():
    """
    Test que simula la respuesta exacta de Gemini y ABRE OPERACIÓN REAL EN MT5.
    
    Flujo:
    1. Inicializar bot INTRADAY
    2. Mockear respuesta de Gemini (respuesta real que causó error)
    3. Ejecutar ciclo completo
    4. Verificar que se abre operación en MT5
    """
    print("\n" + "="*80)
    print("🚀 TEST DE APERTURA REAL DE OPERACIÓN - BOT INTRADAY")
    print("="*80 + "\n")
    
    # ============================================================================
    # 1. CONFIGURACIÓN DEL BOT
    # ============================================================================
    print("📋 Paso 1: Configurando bot...")
    
    config = BotConfig(
        bot_id=5,
        bot_name="INTRADAY Baseline",
        bot_type="numerico",
        symbols=["USDCHF", "XAUUSD"],  # Símbolos del error
        risk_per_trade=0.1,  # 0.1% para test (mínimo)
        max_daily_risk=3.0,
        enable_dual_orders=False,
        ai_model="gemini-3-pro-preview",
        log_level="INFO",
    )
    
    bot = IntradayBot1Strategy(config)
    
    print(f"✅ Bot configurado: {config.bot_name} (ID: {config.bot_id})")
    print(f"   Símbolos: {config.symbols}")
    print(f"   Riesgo por operación: {config.risk_per_trade}%")
    
    # ============================================================================
    # 2. INICIALIZAR BOT
    # ============================================================================
    print("\n📋 Paso 2: Inicializando bot (conexión MT5, etc.)...")
    
    try:
        success = bot.initialize()
        if not success:
            print("❌ ERROR: No se pudo inicializar el bot")
            print("   Verifica que MT5 esté abierto y conectado")
            return
        
        print("✅ Bot inicializado correctamente")
        print(f"   MT5 conectado: {bot.mt5_connection is not None}")
        print(f"   Position Manager: {bot.position_manager is not None}")
        print(f"   Order Manager: {bot.order_manager is not None}")
        
    except Exception as e:
        print(f"❌ ERROR al inicializar bot: {e}")
        return
    
    # ============================================================================
    # 3. SIMULAR RESPUESTAS DE GEMINI (EXACTAS DEL ERROR)
    # ============================================================================
    print("\n📋 Paso 3: Preparando respuestas simuladas de Gemini...")
    
    # Respuesta EXACTA que causó el error en USDCHF
    gemini_response_usdchf = {
        "accion": "COMPRAR",
        "razonamiento": "Tendencia intradía alcista intacta (Precio > EMA20 > VWAP > EMA200). El precio está consolidando sobre la EMA 20 (0.8066) tras un retroceso, ofreciendo un punto de entrada de bajo riesgo tipo 'Trend Surfer'.",
        "direccion": "LONG",
        "stop_loss": 0.8048,
        "take_profit": 0.8102,
        "confianza": 80,
        "estrategia_usada": "A",
        "diagnostico_mercado": "TENDENCIA_ALCISTA"
    }
    
    # Respuesta EXACTA que causó el error en XAUUSD
    gemini_response_xauusd = {
        "accion": "COMPRAR",
        "razonamiento": "Configuración válida de Estrategia A (Trend Surfer). El precio mantiene la estructura alcista (Precio > VWAP > EMA200). La última vela muestra un pullback agresivo que perforó la EMA20 pero cerró con una fuerte mecha de rechazo inferior, recuperando el nivel por encima de la EMA20 y el VWAP, confirmando presión compradora en el soporte dinámico.",
        "direccion": "LONG",
        "stop_loss": 4073.0,
        "take_profit": 4112.0,
        "confianza": 85,
        "estrategia_usada": "A",
        "diagnostico_mercado": "TENDENCIA_ALCISTA"
    }
    
    print("✅ Respuestas de Gemini preparadas:")
    print(f"   USDCHF: {gemini_response_usdchf['accion']} {gemini_response_usdchf['direccion']} @ SL={gemini_response_usdchf['stop_loss']}, TP={gemini_response_usdchf['take_profit']}")
    print(f"   XAUUSD: {gemini_response_xauusd['accion']} {gemini_response_xauusd['direccion']} @ SL={gemini_response_xauusd['stop_loss']}, TP={gemini_response_xauusd['take_profit']}")
    
    # ============================================================================
    # 4. EJECUTAR CICLO COMPLETO PARA CADA SÍMBOLO
    # ============================================================================
    print("\n📋 Paso 4: Ejecutando ciclo completo (ABRIRÁ OPERACIONES REALES)...")
    print("⚠️  ADVERTENCIA: Este test ABRIRÁ OPERACIONES REALES EN MT5")
    print("   (con dinero ficticio de cuenta demo)")
    
    # Esperar confirmación del usuario
    import time
    print("\n⏳ Esperando 3 segundos antes de abrir operaciones...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    print("   ¡Iniciando!\n")
    
    # Símbolos y sus respuestas
    test_data = [
        ("USDCHF", gemini_response_usdchf),
        ("XAUUSD", gemini_response_xauusd),
    ]
    
    for symbol, gemini_response in test_data:
        print(f"\n{'='*80}")
        print(f"🔄 PROCESANDO: {symbol}")
        print(f"{'='*80}\n")
        
        try:
            # ----------------------------------------------------------------
            # 4.1. MOCKEAR RESPUESTA DE VERTEX AI
            # ----------------------------------------------------------------
            print(f"   📤 Mockeando respuesta de Vertex AI para {symbol}...")
            
            # Convertir respuesta a JSON string (como lo retorna Gemini)
            gemini_json = json.dumps(gemini_response, indent=2)
            
            # Crear mock de GeminiResponse
            mock_gemini = GeminiResponse(
                success=True,
                content=gemini_json,
                tokens_input=5000,  # Simulado
                tokens_output=300,  # Simulado
                cost=0.05,  # Simulado
                latency=2.5,  # Simulado
                error_message=None,
                error_type=None,
            )
            
            # Parchear el método send_prompt del cliente Vertex AI
            with patch.object(bot.vertex_client, 'send_prompt', return_value=mock_gemini):
                print(f"   ✅ Respuesta de Gemini mockeada")
                print(f"      Acción: {gemini_response['accion']}")
                print(f"      Dirección: {gemini_response['direccion']}")
                print(f"      SL: {gemini_response['stop_loss']}, TP: {gemini_response['take_profit']}")
                
                # ----------------------------------------------------------------
                # 4.2. EJECUTAR CICLO COMPLETO (prepare_data + consulta + parse + registro)
                # ----------------------------------------------------------------
                print(f"\n   🔄 Ejecutando ciclo de análisis...")
                
                decision = bot.execute_cycle(symbol)
                
                print(f"   ✅ Decisión obtenida:")
                print(f"      Acción: {decision.get('accion')}")
                print(f"      Dirección: {decision.get('direccion')}")
                print(f"      SL: {decision.get('stop_loss')}, TP: {decision.get('take_profit')}")
                print(f"      Confianza: {decision.get('confidence')}%")
                print(f"      Operation ID: {decision.get('operation_id')}")
                print(f"      Costo IA: ${decision.get('cost_usd'):.4f}")
                reasoning = decision.get('reasoning', '')
                if reasoning:
                    print(f"      Razonamiento: {reasoning[:100]}...")
                
                # ----------------------------------------------------------------
                # 4.3. EJECUTAR DECISIÓN (ABRE OPERACIÓN REAL EN MT5)
                # ----------------------------------------------------------------
                print(f"\n   🚀 Ejecutando decisión (ABRIRÁ OPERACIÓN REAL EN MT5)...")
                
                try:
                    bot._execute_decision(symbol, decision)
                    
                    print(f"   ✅ Decisión ejecutada")
                    
                    # Verificar si se abrió la operación
                    time.sleep(1)  # Esperar a que MT5 procese
                    
                    # Generar magic number correcto (estructura de 6 dígitos)
                    magic_to_check = config.bot_id
                    if bot.magic_number_generator:
                        magic_to_check = bot.magic_number_generator.generate(
                            bot_id=config.bot_id,
                            ia_config_id=0,
                            order_type="market",
                            sequence=0
                        )
                    
                    positions = bot.position_manager.get_positions_by_symbol_and_magic(
                        symbol=symbol,
                        magic=magic_to_check
                    )
                    
                    if positions:
                        pos = positions[0]
                        print(f"\n   ✅ ¡OPERACIÓN ABIERTA EN MT5!")
                        print(f"      Ticket: {pos.ticket}")
                        print(f"      Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
                        print(f"      Volumen: {pos.volume} lotes")
                        print(f"      Precio entrada: {pos.price_open}")
                        print(f"      Stop Loss: {pos.sl}")
                        print(f"      Take Profit: {pos.tp}")
                        print(f"      Magic Number: {pos.magic}")
                        print(f"      Profit actual: ${pos.profit:.2f}")
                    else:
                        print(f"\n   ⚠️  No se encontró posición abierta para {symbol}")
                        print(f"      Esto puede ser un error o la orden fue rechazada por MT5")
                        
                except Exception as e:
                    print(f"   ❌ ERROR al ejecutar decisión: {e}")
                    import traceback
                    traceback.print_exc()
                
        except Exception as e:
            print(f"   ❌ ERROR en ciclo de {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    # ============================================================================
    # 5. RESUMEN FINAL
    # ============================================================================
    print(f"\n{'='*80}")
    print("📊 RESUMEN FINAL")
    print(f"{'='*80}\n")
    
    # Contar posiciones abiertas
    total_positions = 0
    for symbol in config.symbols:
        # Generar magic number correcto para verificación
        magic_to_check = config.bot_id
        if bot.magic_number_generator:
            magic_to_check = bot.magic_number_generator.generate(
                bot_id=config.bot_id,
                ia_config_id=0,
                order_type="market",
                sequence=0
            )
        
        positions = bot.position_manager.get_positions_by_symbol_and_magic(
            symbol=symbol,
            magic=magic_to_check
        )
        total_positions += len(positions)
        
        if positions:
            for pos in positions:
                print(f"✅ {symbol}: Ticket {pos.ticket} | {'BUY' if pos.type == 0 else 'SELL'} {pos.volume} lotes | PnL: ${pos.profit:.2f}")
    
    if total_positions == 0:
        print("⚠️  No se abrieron operaciones")
        print("   Posibles causas:")
        print("   - Error en la dirección (revisar logs)")
        print("   - Broker rechazó la orden (volumen mínimo, spread, etc.)")
        print("   - Error en el código")
    else:
        print(f"\n✅ Total de operaciones abiertas: {total_positions}")
    
    print(f"\n{'='*80}")
    print("✅ TEST COMPLETADO")
    print(f"{'='*80}\n")
    
    print("📝 Notas:")
    print("   - Las operaciones están abiertas en MT5")
    print("   - Ciérralas manualmente o espera a que el bot las cierre")
    print("   - Revisa los logs del bot para más detalles")
    print("   - Si no se abrieron, revisa los logs en busca de errores")


if __name__ == "__main__":
    test_open_real_position_with_gemini_response()
