"""Script para probar la generación de prompts con el flag --dump-prompts.

Este script simula el flujo de prepare_data_for_ai() para verificar
que los prompts se generen correctamente con todas las variables reemplazadas.
"""

from pathlib import Path
from datetime import datetime
import json
import sys

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig

def test_prompt_generation():
    """Genera prompts y los guarda en archivos para revisión."""
    
    print("="*70)
    print("TEST DE GENERACIÓN DE PROMPTS")
    print("="*70)
    
    # Configurar bot
    config = BotConfig(
        bot_id=5,
        bot_name="INTRADAY Gemini 3 Pro Bot 1",
        bot_type="numerico",
        symbols=["EURUSD"],
        risk_per_trade=1.0,
        enable_dual_orders=False,
    )
    
    # Crear instancia de estrategia
    strategy = IntradayBot1Strategy(config)
    
    # Inicializar (requiere MT5 y conexiones)
    print("\n📡 Inicializando conexiones...")
    if not strategy.initialize():
        print("❌ Error: No se pudo inicializar MT5")
        print("   Este test requiere MT5 instalado y conectado")
        return
    
    print("✅ Conexiones inicializadas")
    
    # Preparar datos para la IA
    print("\n📊 Generando paquetes de datos...")
    symbol = "EURUSD"
    
    try:
        result = strategy.prepare_data_for_ai(
            symbol=symbol,
            indicators={},  # No usado por INTRADAY
            or_data=None,   # No usado por INTRADAY
            market_context=None,  # No usado por INTRADAY
            ohlcv_data=None,  # No usado por INTRADAY
        )
        
        print(f"✅ Datos preparados para {symbol}")
        print(f"   - Operation ID: {result['operation_id']}")
        print(f"   - Timestamp: {result['timestamp']}")
        print(f"   - Has position: {result['has_active_position']}")
        print(f"   - Tactical candles: {len(result['tactical_package'])}")
        print(f"   - Strategic candles: {len(result['strategic_package'])}")
        
        # Guardar prompts en archivos
        output_dir = Path(__file__).parent / "output_prompts"
        output_dir.mkdir(exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # System prompt
        system_file = output_dir / f"system_prompt_{timestamp_str}.txt"
        with open(system_file, 'w', encoding='utf-8') as f:
            f.write(result['system_prompt'])
        print(f"\n📄 System prompt guardado en: {system_file}")
        
        # User prompt
        user_file = output_dir / f"user_prompt_{timestamp_str}.txt"
        with open(user_file, 'w', encoding='utf-8') as f:
            f.write(result['user_prompt'])
        print(f"📄 User prompt guardado en: {user_file}")
        
        # Datos JSON (tactical + strategic)
        data_file = output_dir / f"market_data_{timestamp_str}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'operation_id': result['operation_id'],
                'symbol': result['symbol'],
                'timestamp': result['timestamp'],
                'has_active_position': result['has_active_position'],
                'tactical_package': result['tactical_package'][:5],  # Solo primeras 5 velas
                'strategic_package': result['strategic_package'][:5],  # Solo primeras 5 velas
                'tactical_total_candles': len(result['tactical_package']),
                'strategic_total_candles': len(result['strategic_package']),
            }, f, indent=2, ensure_ascii=False)
        print(f"📄 Market data (sample) guardado en: {data_file}")
        
        # Verificar longitud de prompts
        print("\n📏 Estadísticas de prompts:")
        print(f"   - System prompt: {len(result['system_prompt'])} caracteres")
        print(f"   - User prompt: {len(result['user_prompt'])} caracteres")
        print(f"   - Total combinado: {len(result['system_prompt']) + len(result['user_prompt'])} caracteres")
        
        # Verificar que las variables fueron reemplazadas
        print("\n🔍 Verificación de variables reemplazadas:")
        
        vars_to_check = [
            '{current_time}',
            '{symbol}',
            '{operation_id}',
            '{current_position}',
            '{tactical_package}',
            '{strategic_package}',
        ]
        
        all_good = True
        for var in vars_to_check:
            if var in result['user_prompt']:
                print(f"   ❌ Variable {var} NO fue reemplazada")
                all_good = False
            else:
                print(f"   ✅ Variable {var} reemplazada correctamente")
        
        if all_good:
            print("\n✅ TODAS las variables fueron reemplazadas correctamente")
        else:
            print("\n⚠️ ATENCIÓN: Algunas variables no fueron reemplazadas")
        
        print("\n" + "="*70)
        print("✅ TEST COMPLETADO")
        print("="*70)
        print(f"\n📂 Revisa los archivos generados en: {output_dir}")
        
    except Exception as e:
        print(f"\n❌ Error generando prompts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prompt_generation()
