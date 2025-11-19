"""
Ejemplo de Uso de Contexto de Conversación - T28

Este ejemplo demuestra cómo el sistema mantiene el contexto de conversación
durante múltiples reevaluaciones de una posición, permitiendo que la IA
tenga acceso al historial completo de decisiones.

Características demostradas:
1. Evaluación inicial que crea una conversación
2. Múltiples reevaluaciones usando el mismo conversation_id
3. La IA mantiene contexto entre reevaluaciones
4. Diferencia entre modo PERSISTENT vs NEW

Autor: Botrading Team
Fecha: 2025-11-13
Ticket: T28
"""

import asyncio
import os
import sys
from typing import Dict, Any
from pathlib import Path

# Agregar el directorio raíz al path para importaciones
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Importaciones del proyecto
from src.core.gemini_client import GeminiClient, GeminiConfig
from src.core.reevaluation_manager import (
    ReevaluationManager,
    ReevaluationMode,
    ReevaluationContext
)


async def ejemplo_basico_conversacion():
    """
    Ejemplo 1: Uso básico de conversaciones con GeminiClient
    
    Demuestra cómo enviar múltiples prompts dentro de la misma conversación
    para mantener el contexto.
    """
    print("=" * 80)
    print("EJEMPLO 1: Uso Básico de Conversaciones")
    print("=" * 80)
    
    # Configurar cliente Gemini
    # NOTA: En producción, usa una API key real en variable de entorno
    api_key = os.getenv("GEMINI_API_KEY", "demo_key")
    
    config = GeminiConfig(
        model="gemini-2.5-pro",
        temperature=0.7,
        max_tokens=1024
    )
    
    client = GeminiClient(api_key=api_key, config=config)
    
    # ID único de conversación (en producción vendría del sistema)
    conversation_id = "trade_eurusd_20251113_001"
    
    print(f"\n📝 Creando conversación: {conversation_id}")
    print("-" * 80)
    
    # Primer mensaje: Evaluación inicial
    print("\n🔹 Mensaje 1: Evaluación Inicial")
    prompt_1 = """
Analiza EURUSD con los siguientes datos:
- Precio actual: 1.2400
- RSI: 65.0
- EMA 20: 1.2350
- EMA 50: 1.2300

¿Debo operar?
"""
    
    # Enviar con conversation_id para iniciar la conversación
    response_1 = client.send_prompt(
        prompt=prompt_1,
        conversation_id=conversation_id
    )
    
    if response_1.success:
        print(f"✅ Respuesta IA: {response_1.content}")
        print(f"📊 Tokens: {response_1.total_tokens}, Costo: ${response_1.cost:.6f}")
    else:
        print(f"❌ Error: {response_1.error_message}")
    
    # Segundo mensaje: Primera reevaluación (10 minutos después)
    print("\n🔹 Mensaje 2: Primera Reevaluación (10 min después)")
    prompt_2 = """
Han pasado 10 minutos. Situación actualizada:
- Precio actual: 1.2420 (+20 pips)
- RSI: 68.0
- Momentum alcista continúa

¿Qué hago con la operación?
"""
    
    # Enviar con MISMO conversation_id - mantiene contexto
    response_2 = client.send_prompt(
        prompt=prompt_2,
        conversation_id=conversation_id
    )
    
    if response_2.success:
        print(f"✅ Respuesta IA: {response_2.content}")
        print(f"📊 Tokens: {response_2.total_tokens}, Costo: ${response_2.cost:.6f}")
    else:
        print(f"❌ Error: {response_2.error_message}")
    
    # Tercer mensaje: Segunda reevaluación (20 minutos después)
    print("\n🔹 Mensaje 3: Segunda Reevaluación (20 min después)")
    prompt_3 = """
Han pasado otros 10 minutos. Situación actualizada:
- Precio actual: 1.2405 (-15 pips desde última reevaluación)
- RSI: 58.0 (bajó)
- Señales de reversión

¿Qué hago ahora?
"""
    
    # Enviar con MISMO conversation_id - IA tiene TODO el historial
    response_3 = client.send_prompt(
        prompt=prompt_3,
        conversation_id=conversation_id
    )
    
    if response_3.success:
        print(f"✅ Respuesta IA: {response_3.content}")
        print(f"📊 Tokens: {response_3.total_tokens}, Costo: ${response_3.cost:.6f}")
    else:
        print(f"❌ Error: {response_3.error_message}")
    
    # Mostrar historial de conversación
    print("\n📜 Historial de Conversación")
    print("-" * 80)
    history = client.get_conversation_history(conversation_id)
    for i, msg in enumerate(history, 1):
        role_emoji = "👤" if msg['role'] == 'user' else "🤖"
        print(f"{role_emoji} Mensaje {i} ({msg['role']}):")
        print(f"   {msg['content'][:100]}...")
        print()
    
    # Estadísticas
    print("\n📊 Estadísticas de Conversaciones")
    print("-" * 80)
    conv_stats = client.get_conversation_stats()
    print(f"Conversaciones activas: {conv_stats['active_conversations']}")
    print(f"IDs de conversaciones: {conv_stats['conversation_ids']}")
    
    # Limpiar conversación al finalizar
    print(f"\n🧹 Limpiando conversación: {conversation_id}")
    client.clear_conversation(conversation_id)
    print("✅ Conversación eliminada")


async def ejemplo_modo_persistente_vs_nuevo():
    """
    Ejemplo 2: Comparación entre modo PERSISTENT_CONVERSATION y NEW_CONVERSATION
    
    Demuestra la diferencia entre mantener contexto (PERSISTENT) y
    crear nuevas conversaciones cada vez (NEW).
    """
    print("\n" + "=" * 80)
    print("EJEMPLO 2: Modo PERSISTENT vs NEW")
    print("=" * 80)
    
    # Mocks simplificados para el ejemplo
    class MockDependencies:
        def __init__(self):
            self.mt5_connector = self._create_mock()
            self.data_extractor = self._create_mock()
            self.prompt_builder = self._create_mock()
            self.gemini_client = self._create_mock()
            self.response_parser = self._create_mock()
            self.position_manager = self._create_mock()
        
        def _create_mock(self):
            """Crea un mock simple"""
            class SimpleMock:
                def __getattr__(self, name):
                    def method(*args, **kwargs):
                        return None
                    return method
            return SimpleMock()
    
    # Crear managers en ambos modos
    deps = MockDependencies()
    
    print("\n🔹 Modo PERSISTENT_CONVERSATION")
    print("-" * 80)
    manager_persistent = ReevaluationManager(
        mt5_connector=deps.mt5_connector,
        data_extractor=deps.data_extractor,
        prompt_builder=deps.prompt_builder,
        gemini_client=deps.gemini_client,
        response_parser=deps.response_parser,
        position_manager=deps.position_manager,
        mode=ReevaluationMode.PERSISTENT_CONVERSATION
    )
    
    # Simular 3 reevaluaciones de la misma posición
    position_id = "pos_eurusd_001"
    
    for i in range(1, 4):
        conv_id = manager_persistent._get_or_create_conversation(position_id)
        print(f"   Reevaluación {i}: conversation_id = {conv_id}")
    
    print(f"\n   ✅ Resultado: Se creó 1 conversación, reutilizada 3 veces")
    print(f"   📊 Conversaciones activas: {len(manager_persistent.conversation_sessions)}")
    
    print("\n🔹 Modo NEW_CONVERSATION")
    print("-" * 80)
    manager_new = ReevaluationManager(
        mt5_connector=deps.mt5_connector,
        data_extractor=deps.data_extractor,
        prompt_builder=deps.prompt_builder,
        gemini_client=deps.gemini_client,
        response_parser=deps.response_parser,
        position_manager=deps.position_manager,
        mode=ReevaluationMode.NEW_CONVERSATION
    )
    
    # Simular 3 reevaluaciones de la misma posición
    for i in range(1, 4):
        conv_id = manager_new._get_or_create_conversation(position_id)
        print(f"   Reevaluación {i}: conversation_id = {conv_id}")
    
    print(f"\n   ✅ Resultado: Cada reevaluación es independiente (sin contexto)")
    print(f"   📊 Conversaciones activas: {len(manager_new.conversation_sessions)}")
    
    # Explicación
    print("\n📚 Explicación:")
    print("-" * 80)
    print("""
MODO PERSISTENT_CONVERSATION:
✅ Ventaja: La IA mantiene contexto completo entre reevaluaciones
✅ Uso: Ideal para tracking de posiciones individuales
✅ Beneficio: Decisiones más informadas basadas en historial
⚠️  Consideración: Mayor consumo de tokens en prompts largos

MODO NEW_CONVERSATION:
✅ Ventaja: Cada evaluación es independiente y "fresca"
✅ Uso: Para estrategias que prefieren decisiones aisladas
✅ Beneficio: Menor consumo de tokens
⚠️  Consideración: Sin memoria de decisiones previas
    """)


async def ejemplo_ciclo_completo_reevaluacion():
    """
    Ejemplo 3: Ciclo completo de evaluación y reevaluaciones
    
    Simula el flujo real del sistema desde la evaluación inicial
    hasta el cierre de la operación.
    """
    print("\n" + "=" * 80)
    print("EJEMPLO 3: Ciclo Completo de Evaluación → Reevaluaciones → Cierre")
    print("=" * 80)
    
    print("""
ESCENARIO:
- Símbolo: EURUSD
- Estrategia: Bot numérico con indicadores
- Modo: PERSISTENT_CONVERSATION (mantiene contexto)

FLUJO:
1. Evaluación inicial → Decisión: OPERAR (BUY)
2. Reevaluación T+10min → Decisión: MANTENER
3. Reevaluación T+20min → Decisión: ACTUALIZAR SL (breakeven)
4. Reevaluación T+30min → Decisión: CERRAR (target alcanzado)
    """)
    
    # Simular contextos de cada paso
    steps = [
        {
            "tiempo": "T+0min",
            "accion": "EVALUACION_INICIAL",
            "precio": 1.2400,
            "rsi": 65.0,
            "decision_esperada": "OPERAR (BUY)",
            "razonamiento": "Ruptura alcista confirmada, RSI con momentum"
        },
        {
            "tiempo": "T+10min",
            "accion": "REEVALUACION_1",
            "precio": 1.2420,
            "rsi": 68.0,
            "decision_esperada": "MANTENER",
            "razonamiento": "Operación en profit +20 pips, tendencia continúa"
        },
        {
            "tiempo": "T+20min",
            "accion": "REEVALUACION_2",
            "precio": 1.2450,
            "rsi": 70.0,
            "decision_esperada": "ACTUALIZAR SL",
            "razonamiento": "Profit +50 pips, mover SL a breakeven (1.2400)"
        },
        {
            "tiempo": "T+30min",
            "accion": "REEVALUACION_3",
            "precio": 1.2500,
            "rsi": 72.0,
            "decision_esperada": "CERRAR",
            "razonamiento": "Target alcanzado (+100 pips), tomar ganancias"
        }
    ]
    
    conversation_id = "trade_eurusd_cycle_demo"
    
    print("\n📊 EJECUCIÓN DEL CICLO:")
    print("=" * 80)
    
    for i, step in enumerate(steps, 1):
        print(f"\n🔹 Paso {i}: {step['accion']} ({step['tiempo']})")
        print("-" * 80)
        print(f"   Precio: {step['precio']}")
        print(f"   RSI: {step['rsi']}")
        print(f"   Conversación ID: {conversation_id}")
        print(f"   📍 Decisión Esperada: {step['decision_esperada']}")
        print(f"   💭 Razonamiento: {step['razonamiento']}")
        
        if i == 1:
            print(f"   ✨ Se CREA la conversación {conversation_id}")
        else:
            print(f"   ♻️  Se REUTILIZA la conversación (IA tiene historial completo)")
    
    print("\n" + "=" * 80)
    print("✅ CICLO COMPLETADO")
    print("=" * 80)
    print(f"""
RESULTADO:
- Operación abierta en: 1.2400
- Operación cerrada en: 1.2500
- Profit: +100 pips
- Reevaluaciones: 3
- Conversaciones creadas: 1 (reutilizada 4 veces)
- Beneficio del contexto: La IA "recuerda" que:
  * Abrió la operación en 1.2400
  * Decidió mantener en +20 pips
  * Movió SL a breakeven en +50 pips
  * Cerró al alcanzar objetivo de +100 pips
    """)


async def main():
    """
    Función principal que ejecuta todos los ejemplos
    """
    print("\n" + "=" * 80)
    print("EJEMPLOS DE USO: Contexto de Conversación en Reevaluaciones (T28)")
    print("=" * 80)
    
    try:
        # Ejemplo 1: Uso básico
        # NOTA: Comentado porque requiere API key real
        # await ejemplo_basico_conversacion()
        
        print("\n⚠️  NOTA: Ejemplo 1 comentado (requiere API key de Gemini)")
        print("Para ejecutarlo, configura GEMINI_API_KEY en variables de entorno")
        
        # Ejemplo 2: Modos PERSISTENT vs NEW
        await ejemplo_modo_persistente_vs_nuevo()
        
        # Ejemplo 3: Ciclo completo
        await ejemplo_ciclo_completo_reevaluacion()
        
        print("\n" + "=" * 80)
        print("✅ TODOS LOS EJEMPLOS COMPLETADOS")
        print("=" * 80)
        
        print("""
RESUMEN:
--------
El sistema de contexto de conversación permite que la IA mantenga memoria
de todas las interacciones previas con una operación específica.

BENEFICIOS CLAVE:
1. Decisiones más informadas basadas en historial completo
2. Coherencia entre evaluaciones sucesivas
3. La IA puede referenciar decisiones anteriores
4. Mejor tracking de la evolución de cada trade
5. Facilita estrategias de trailing stop y gestión dinámica

USO RECOMENDADO:
- PERSISTENT_CONVERSATION: Para bots de trading con gestión activa
- NEW_CONVERSATION: Para señales independientes sin contexto

IMPLEMENTACIÓN:
- GeminiClient: Maneja sesiones de chat con ChatSession de Gemini
- ReevaluationManager: Coordina el uso de conversation_id
- Automático: El sistema gestiona creación/reutilización/limpieza

PRÓXIMOS PASOS:
1. Revisar documentación en context/DOCUMENTACION/T28_contexto_conversacion.md
2. Ejecutar tests: pytest tests/unit/test_gemini_client.py::TestGeminiClientConversations
3. Probar en demo antes de producción
        """)
        
    except Exception as e:
        print(f"\n❌ Error ejecutando ejemplos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
