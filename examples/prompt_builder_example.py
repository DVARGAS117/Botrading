"""
Ejemplo de uso del sistema de PromptBuilder y GeminiClient - T10

Este ejemplo demuestra el flujo completo de:
1. Construcción de prompts por tipo de bot
2. Envío a Gemini 2.5 Pro
3. Parseo de respuestas
4. Manejo de errores

Author: Botrading Team
Date: 2025-11-13
"""

import os
from src.core.prompt_builder import (
    PromptBuilder,
    PromptData,
    BotType,
    PromptType
)
from src.core.gemini_client import (
    GeminiClient,
    GeminiConfig,
    GeminiResponse
)
from src.core.vertex_ai_client import (
    VertexAIClient, VertexAIConfig
)
from src.core.ai_response_parser import (
    AIResponseParser,
    AIDecisionType
)


def example_numeric_evaluation():
    """
    Ejemplo 1: Evaluación inicial con bot numérico
    """
    print("=" * 60)
    print("EJEMPLO 1: Evaluación Numérica")
    print("=" * 60)
    
    # 1. Preparar datos de mercado
    data = PromptData(
        symbol="EURUSD",
        timeframe="5M",
        indicators={
            "rsi": 65.0,
            "ema_20": 1.2345,
            "ema_50": 1.2340,
            "macd": 0.0012,
            "volume": 15000
        },
        current_price=1.2350
    )
    
    # 2. Construir prompt
    builder = PromptBuilder()
    prompt = builder.build_prompt(
        bot_type=BotType.NUMERICO,
        prompt_type=PromptType.EVALUACION,
        data=data,
        include_json_instructions=True
    )
    
    print("\n📝 Prompt generado:")
    print("-" * 60)
    print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
    
    # 3. Configurar y enviar a IA (Vertex por defecto)
    vertex_key = os.getenv("GOOGLE_API_KEY")
    if vertex_key:
        vcfg = VertexAIConfig(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        vclient = VertexAIClient(api_key=vertex_key, config=vcfg)
        response = vclient.send_prompt(prompt)
    else:
        # Fallback a Gemini API Studio si no hay GOOGLE_API_KEY
        api_key = os.getenv("GEMINI_API_KEY", "demo_key")
        if api_key == "demo_key":
            print("\n⚠️  No hay GOOGLE_API_KEY ni GEMINI_API_KEY. Usando modo demo.")
            return
        gcfg = GeminiConfig(model="gemini-2.0-flash-exp", temperature=0.7, max_tokens=1024, timeout=30, retry_attempts=3)
        gclient = GeminiClient(api_key=api_key, config=gcfg)
        response = gclient.send_prompt(prompt)
        
        print("\n✅ Respuesta de Gemini:")
        print("-" * 60)
        if response.success:
            print(f"Content: {response.content}")
            print(f"Tokens: {response.total_tokens}")
            print(f"Costo: ${response.cost:.4f}")
            
            # 4. Parsear respuesta
            parser = AIResponseParser()
            parsed = parser.parse_evaluation(response.content)
            
            if parsed.is_valid:
                print("\n📊 Decisión parseada:")
                print(f"  Acción: {parsed.decision_type.value}")
                if parsed.decision_type == AIDecisionType.OPERAR:
                    print(f"  Dirección: {parsed.direction.value}")
                    print(f"  Stop Loss: {parsed.stop_loss}")
                    print(f"  Take Profit: {parsed.take_profit}")
                    print(f"  Riesgo: {parsed.risk_percentage}%")
            else:
                print(f"\n❌ Error de parseo: {parsed.error_message}")
        else:
            print(f"❌ Error: {response.error_message}")
    else:
        # No-op si no había llaves
        pass


def example_visual_evaluation():
    """
    Ejemplo 2: Evaluación inicial con bot visual (imágenes)
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Evaluación Visual")
    print("=" * 60)
    
    # 1. Preparar datos con imágenes
    data = PromptData(
        symbol="GBPUSD",
        timeframe="15M",
        image_paths=[
            "/path/to/chart_5m.png",
            "/path/to/chart_15m.png",
            "/path/to/chart_1h.png"
        ],
        current_price=1.3505
    )
    
    # 2. Construir prompt
    builder = PromptBuilder()
    prompt = builder.build_prompt(
        bot_type=BotType.VISUAL,
        prompt_type=PromptType.EVALUACION,
        data=data
    )
    
    print("\n📝 Prompt generado:")
    print("-" * 60)
    print(prompt[:200] + "...")
    print(f"\n📸 Imágenes incluidas: {len(data.image_paths)}")
    
    # En producción, enviar prompt con imágenes
    # response = client.send_prompt(prompt, image_paths=data.image_paths)


def example_reevaluation():
    """
    Ejemplo 3: Reevaluación de posición abierta
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Reevaluación de Posición")
    print("=" * 60)
    
    # 1. Preparar datos de posición abierta
    data = PromptData(
        symbol="USDJPY",
        timeframe="1H",
        indicators={
            "rsi": 60.0,
            "macd": 0.0010
        },
        current_price=150.80,
        position_data={
            "entry_price": 150.50,
            "stop_loss": 149.50,
            "take_profit": 151.50,
            "current_pnl": 30.0,
            "direction": "BUY",
            "opened_at": "2025-11-13 10:00:00"
        }
    )
    
    # 2. Construir prompt de reevaluación
    builder = PromptBuilder()
    prompt = builder.build_prompt(
        bot_type=BotType.NUMERICO,
        prompt_type=PromptType.REEVALUACION,
        data=data
    )
    
    print("\n📝 Prompt de reevaluación:")
    print("-" * 60)
    print(prompt[:300] + "...")
    
    # Respuesta simulada para demostración
    simulated_response = """{
        "accion": "ACTUALIZAR",
        "nuevo_stop_loss": 150.20,
        "nuevo_take_profit": 151.80,
        "razonamiento": "Mover SL a breakeven, la operación va bien"
    }"""
    
    print("\n📥 Respuesta simulada de IA:")
    print(simulated_response)
    
    # 3. Parsear respuesta
    parser = AIResponseParser()
    parsed = parser.parse_reevaluation(simulated_response)
    
    if parsed.is_valid:
        print("\n📊 Decisión parseada:")
        print(f"  Acción: {parsed.decision_type.value}")
        if parsed.decision_type == AIDecisionType.ACTUALIZAR:
            if parsed.new_stop_loss:
                print(f"  Nuevo SL: {parsed.new_stop_loss}")
            if parsed.new_take_profit:
                print(f"  Nuevo TP: {parsed.new_take_profit}")
            print(f"  Razón: {parsed.reasoning}")


def example_multi_timeframe():
    """
    Ejemplo 4: Prompt con múltiples timeframes
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Múltiples Timeframes")
    print("=" * 60)
    
    # Preparar datos para cada timeframe
    data_5m = PromptData(
        symbol="EURUSD",
        timeframe="5M",
        indicators={"rsi": 65.0, "ema_20": 1.2345},
        current_price=1.2350
    )
    
    data_15m = PromptData(
        symbol="EURUSD",
        timeframe="15M",
        indicators={"rsi": 60.0, "ema_20": 1.2340},
        current_price=1.2350
    )
    
    data_1h = PromptData(
        symbol="EURUSD",
        timeframe="1H",
        indicators={"rsi": 58.0, "ema_20": 1.2335},
        current_price=1.2350
    )
    
    # Construir prompt multi-timeframe
    builder = PromptBuilder()
    prompt = builder.build_multi_timeframe_prompt(
        bot_type=BotType.NUMERICO,
        prompt_type=PromptType.EVALUACION,
        timeframe_data=[data_5m, data_15m, data_1h]
    )
    
    print("\n📝 Prompt multi-timeframe:")
    print("-" * 60)
    print(prompt[:400] + "...")


def example_error_handling():
    """
    Ejemplo 5: Manejo de errores
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Manejo de Errores")
    print("=" * 60)
    
    # Respuesta inválida simulada
    invalid_responses = [
        ("JSON inválido", "Esta no es una respuesta JSON"),
        ("Campos faltantes", '{"accion": "OPERAR"}'),
        ("Valor inválido", '{"accion": "COMPRAR"}')
    ]
    
    parser = AIResponseParser()
    
    for error_type, response in invalid_responses:
        print(f"\n🔍 Probando: {error_type}")
        print(f"   Respuesta: {response}")
        
        # Parseo seguro (no lanza excepciones)
        parsed = parser.safe_parse_evaluation(response)
        
        if not parsed.is_valid:
            print(f"   ❌ Error detectado: {parsed.error_type}")
            print(f"   📝 Mensaje: {parsed.error_message}")
        else:
            print(f"   ✅ Válido")


def example_usage_statistics():
    """
    Ejemplo 6: Tracking de estadísticas
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 6: Estadísticas de Uso")
    print("=" * 60)
    
    # Mostrar estadísticas del cliente si se usa Gemini (en Vertex las exponemos por request)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        config = GeminiConfig(model="gemini-2.0-flash-exp")
        client = GeminiClient(api_key=api_key, config=config)
        stats = client.get_usage_statistics()
        
        print("\n📊 Estadísticas de uso:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Exitosos: {stats['successful_requests']}")
        print(f"  Fallidos: {stats['failed_requests']}")
        print(f"  Tokens input: {stats['total_tokens_input']}")
        print(f"  Tokens output: {stats['total_tokens_output']}")
        print(f"  Costo total: ${stats['total_cost']:.4f}")
        if stats['successful_requests'] > 0:
            print(f"  Latencia promedio: {stats['average_latency']:.2f}s")
            print(f"  Costo promedio: ${stats['average_cost_per_request']:.4f}")
    else:
        print("\nℹ️  Estadísticas detalladas dependen del cliente en uso.")


def example_custom_template():
    """
    Ejemplo 7: Template personalizado
    """
    print("\n" + "=" * 60)
    print("EJEMPLO 7: Template Personalizado")
    print("=" * 60)
    
    builder = PromptBuilder()
    
    # Agregar template personalizado
    custom_template = """
Eres un analista experto de {symbol}.

Analiza cuidadosamente los datos:
- Precio actual: {current_price}
- Indicadores: {indicators_formatted}

Da tu recomendación profesional en formato JSON.
"""
    
    builder.add_template(
        name="custom_professional",
        bot_type=BotType.NUMERICO,
        prompt_type=PromptType.EVALUACION,
        template_text=custom_template,
        description="Template profesional personalizado"
    )
    
    data = PromptData(
        symbol="BTCUSD",
        timeframe="1H",
        indicators={"rsi": 72.0},
        current_price=45000.0
    )
    
    prompt = builder.build_prompt(
        bot_type=BotType.NUMERICO,
        prompt_type=PromptType.EVALUACION,
        data=data,
        include_json_instructions=False  # Sin instrucciones default
    )
    
    print("\n📝 Prompt con template personalizado:")
    print("-" * 60)
    print(prompt)


def main():
    """Ejecuta todos los ejemplos"""
    print("\n" + "🤖 " * 20)
    print("EJEMPLOS DE USO: PromptBuilder + GeminiClient + AIResponseParser")
    print("🤖 " * 20)
    
    # Ejecutar ejemplos
    example_numeric_evaluation()
    example_visual_evaluation()
    example_reevaluation()
    example_multi_timeframe()
    example_error_handling()
    example_usage_statistics()
    example_custom_template()
    
    print("\n" + "=" * 60)
    print("✅ Todos los ejemplos completados")
    print("=" * 60)
    print("\n💡 Para usar en producción:")
    print("   1. Preferido: configura GOOGLE_API_KEY para Vertex AI")
    print("      Alternativa: GEMINI_API_KEY (Google AI Studio)")
    print("   2. Personaliza templates en config/prompt_templates.example.json")
    print("   3. Revisa la documentación en context/DOCUMENTACION/T10_ia_prompt_builder.md")
    print()


if __name__ == "__main__":
    main()
