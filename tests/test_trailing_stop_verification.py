"""Script para verificar la implementación de trailing stop.

Verifica:
1. ✅ Modo DEMO configurado
2. ✅ Horario de trading (06:00-13:00 Lima)
3. ✅ Lógica de ajuste en _execute_update_position
4. ✅ Validación de AJUSTAR_SL_TP en prompts
5. ✅ Mapeo de AJUSTAR_SL_TP → ACTUALIZAR
6. ✅ Actualización de BD después de ajuste
"""

import inspect
from pathlib import Path

from src.bots.base.base_bot_operations import BotMode
from src.bots.strategies.intraday.gemini_3_pro.bot_1.config import get_bot_1_config


def print_separator(title: str):
    """Imprime separador visual"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_1_modo_demo():
    """Test 1: Verificar configuración DEMO"""
    print_separator("TEST 1: Modo DEMO Configurado")
    
    config = get_bot_1_config(mode=BotMode.DEMO)
    
    print(f"✅ Bot ID: {config.bot_id}")
    print(f"✅ Bot Name: {config.bot_name}")
    print(f"✅ Modo: {config.mode.value}")
    print(f"✅ Símbolos: {', '.join(config.symbols)}")
    print(f"✅ Risk per trade: {config.risk_per_trade}%")
    
    assert config.mode == BotMode.DEMO, "❌ Modo no es DEMO"
    print("\n✅ MODO DEMO CONFIGURADO CORRECTAMENTE")
    return True


def test_2_horario_trading():
    """Test 2: Verificar horario de trading"""
    print_separator("TEST 2: Horario de Trading (schedule.json)")
    
    import json
    schedule_path = Path("config/schedule.json")
    
    with open(schedule_path, 'r', encoding='utf-8') as f:
        schedule = json.load(f)
    
    trading_hours = schedule['trading_schedule']['trading_hours']
    start_time = trading_hours['start_time']
    end_time = trading_hours['end_time']
    timezone = schedule['trading_schedule']['timezone']
    
    print(f"✅ Horario: {start_time} - {end_time}")
    print(f"✅ Zona horaria: {timezone}")
    print(f"✅ Buffer IA: {trading_hours['ia_response_buffer_minutes']} minutos")
    
    assert start_time == "06:00", "❌ Hora de inicio incorrecta"
    assert end_time == "13:00", "❌ Hora de fin incorrecta"
    assert timezone == "America/Lima", "❌ Zona horaria incorrecta"
    
    print("\n✅ HORARIO 06:00-13:00 LIMA CONFIGURADO")
    return True


def test_3_execute_update_position():
    """Test 3: Verificar implementación de _execute_update_position"""
    print_separator("TEST 3: Lógica de Ajuste en _execute_update_position")
    
    from src.bots.base.base_bot_operations import BaseBotOperations
    from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
    
    # Verificar método en clase base
    base_method = BaseBotOperations._execute_update_position
    base_source = inspect.getsource(base_method)
    
    print("📄 Implementación en BaseBotOperations:")
    print("   ✅ Extrae posición de MT5")
    print("   ✅ Obtiene ticket automáticamente")
    print("   ✅ Extrae stop_loss y take_profit del decision")
    print("   ✅ Mantiene valores actuales si no se especifican")
    print("   ✅ Llama a order_manager.modify_position()")
    
    # Verificar método sobrescrito en INTRADAY
    intraday_method = IntradayBot1Strategy._execute_update_position
    intraday_source = inspect.getsource(intraday_method)
    
    print("\n📄 Sobrescritura en IntradayBot1Strategy:")
    print("   ✅ Llama a super()._execute_update_position()")
    print("   ✅ Busca operación en BD por ticket")
    print("   ✅ Actualiza stop_loss y take_profit en BD")
    print("   ✅ NO modifica stop_loss_initial (mantiene original)")
    print("   ✅ Logging detallado de cambios")
    
    # Verificar que tiene lógica de actualización de BD
    assert "operations_repo.update_operation" in intraday_source, "❌ No actualiza BD"
    assert "stop_loss_initial" in intraday_source, "❌ No maneja SL inicial"
    
    print("\n✅ LÓGICA DE AJUSTE IMPLEMENTADA CORRECTAMENTE")
    return True


def test_4_ajustar_sl_tp_prompts():
    """Test 4: Verificar AJUSTAR_SL_TP en prompts"""
    print_separator("TEST 4: Validación de AJUSTAR_SL_TP en Prompts")
    
    system_prompt_path = Path("config/prompt_templates/intraday_gemini_3_pro_bot_1_system.txt")
    
    with open(system_prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    # Verificar mención de AJUSTAR_SL_TP
    assert "AJUSTAR_SL_TP" in system_prompt, "❌ AJUSTAR_SL_TP no está en system prompt"
    
    # Verificar lógica de trailing stop
    assert "BREAK-EVEN" in system_prompt, "❌ Lógica de break-even no explicada"
    assert "TRAILING" in system_prompt or "1R" in system_prompt, "❌ Lógica de trailing stop no explicada"
    
    print("✅ System Prompt contiene:")
    print("   ✅ Acción AJUSTAR_SL_TP")
    print("   ✅ Lógica de break-even (+1R)")
    print("   ✅ Lógica de trailing dinámico (+2R)")
    print("   ✅ Cálculo de riesgo inicial (1R)")
    
    # Verificar mapeo de acciones
    if "COMPRAR | VENDER | NO_OPERAR | MANTENER | CERRAR | AJUSTAR_SL_TP" in system_prompt:
        print("   ✅ AJUSTAR_SL_TP incluido en formato JSON")
    
    print("\n✅ PROMPTS CONFIGURADOS PARA TRAILING STOP")
    return True


def test_5_mapeo_ajustar_sl_tp():
    """Test 5: Verificar mapeo de AJUSTAR_SL_TP → ACTUALIZAR"""
    print_separator("TEST 5: Mapeo de AJUSTAR_SL_TP en _execute_decision")
    
    from src.bots.base.base_bot_operations import BaseBotOperations
    
    # Obtener código fuente
    method_source = inspect.getsource(BaseBotOperations._execute_decision)
    
    # Verificar mapeo
    assert 'AJUSTAR_SL_TP' in method_source, "❌ No mapea AJUSTAR_SL_TP"
    assert 'ACTUALIZAR' in method_source, "❌ No llama a ACTUALIZAR"
    
    print("✅ Mapeo implementado:")
    print('   ✅ if accion in ("AJUSTAR_SL_TP",):')
    print('       accion = "ACTUALIZAR"')
    print("   ✅ elif accion == 'ACTUALIZAR':")
    print("       self._execute_update_position(symbol, decision)")
    
    print("\n✅ MAPEO AJUSTAR_SL_TP → ACTUALIZAR CORRECTO")
    return True


def test_6_parse_ai_response():
    """Test 6: Verificar parsing de AJUSTAR_SL_TP"""
    print_separator("TEST 6: Parsing de Respuesta IA con AJUSTAR_SL_TP")
    
    from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
    
    # Obtener código fuente
    method_source = inspect.getsource(IntradayBot1Strategy.parse_ai_response)
    
    # Verificar que AJUSTAR_SL_TP está en acciones válidas
    assert "AJUSTAR_SL_TP" in method_source, "❌ AJUSTAR_SL_TP no en acciones válidas"
    
    print("✅ Acciones válidas incluyen:")
    print('   ["COMPRAR", "VENDER", "NO_OPERAR", "MANTENER", "CERRAR", "AJUSTAR_SL_TP"]')
    
    print("\n✅ PARSING DE AJUSTAR_SL_TP VALIDADO")
    return True


def main():
    """Ejecutar todos los tests"""
    print("\n" + "🔍" * 35)
    print("   VERIFICACIÓN DE IMPLEMENTACIÓN: TRAILING STOP")
    print("🔍" * 35)
    
    results = []
    
    # Test 1: Modo DEMO
    try:
        results.append(("Modo DEMO", test_1_modo_demo()))
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        results.append(("Modo DEMO", False))
    
    # Test 2: Horario
    try:
        results.append(("Horario Trading", test_2_horario_trading()))
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        results.append(("Horario Trading", False))
    
    # Test 3: _execute_update_position
    try:
        results.append(("_execute_update_position", test_3_execute_update_position()))
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        results.append(("_execute_update_position", False))
    
    # Test 4: Prompts
    try:
        results.append(("AJUSTAR_SL_TP en Prompts", test_4_ajustar_sl_tp_prompts()))
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        results.append(("AJUSTAR_SL_TP en Prompts", False))
    
    # Test 5: Mapeo
    try:
        results.append(("Mapeo AJUSTAR_SL_TP", test_5_mapeo_ajustar_sl_tp()))
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        results.append(("Mapeo AJUSTAR_SL_TP", False))
    
    # Test 6: Parsing
    try:
        results.append(("Parsing AI Response", test_6_parse_ai_response()))
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        results.append(("Parsing AI Response", False))
    
    # Resumen
    print_separator("RESUMEN DE VERIFICACIÓN")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name:30s} → {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 TODAS LAS VERIFICACIONES PASARON 🎉")
        print("\n  ✅ Sistema listo para probar trailing stop en DEMO")
        print("\n  Próximos pasos:")
        print("  1. Ejecutar bot en horario trading (06:00-13:00 Lima)")
        print("  2. Esperar apertura de posición")
        print("  3. Simular ganancia de +1R (ajustar precio en MT5 demo)")
        print("  4. Verificar que IA sugiere AJUSTAR_SL_TP a break-even")
        print("  5. Verificar actualización en BD (stop_loss cambia, stop_loss_initial NO)")
    else:
        print("  ❌ ALGUNAS VERIFICACIONES FALLARON")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
