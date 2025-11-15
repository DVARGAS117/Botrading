"""
Ejemplo de uso de IAQueryRepository - T33

Este ejemplo demuestra cómo utilizar el repositorio de consultas IA
para registrar prompts, respuestas, tokens y costos.

Autor: Sistema Botrading
Fecha: 2025-11-15
Ticket: T33 - Registro de consultas a IA con prompts, respuesta, tokens y costo
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.ia_query_repository import (
    IAQueryRepository,
    QueryType
)


def main():
    """Ejemplo completo de uso del IAQueryRepository"""
    
    print("="*80)
    print("EJEMPLO: Registro de Consultas IA - T33")
    print("="*80)
    
    # 1. Inicializar repositorio
    print("\n1️⃣  Inicializando repositorio...")
    repo = IAQueryRepository(db_path=Path("data/ia_queries.db"))
    print("✅ Repositorio inicializado")
    
    # 2. Registrar consulta de evaluación (sin operación)
    print("\n2️⃣  Registrando consulta de EVALUACIÓN...")
    eval_query = repo.create_query(
        bot_id=1,
        ia_id=1,
        symbol="EURUSD",
        query_type=QueryType.EVALUATION,
        prompt="""
Analiza EURUSD con los siguientes datos:
- EMA(20): 1.0850
- RSI(14): 65
- MACD: Señal alcista
- Precio actual: 1.0855
        """.strip(),
        response='{"decision": "OPERAR", "direction": "BUY", "sl": 1.0800, "tp": 1.0950, "confidence": 0.75}',
        tokens_input=150,
        tokens_output=80,
        cost_usd=0.0023,
        action_decided="OPERAR"
    )
    print(f"✅ Consulta de evaluación creada con ID: {eval_query.id}")
    print(f"   - Tokens totales: {eval_query.tokens_total}")
    print(f"   - Costo: ${eval_query.cost_usd:.4f}")
    
    # 3. Simular que se abrió una operación y vincularla
    print("\n3️⃣  Vinculando consulta a operación...")
    operation_id = 456  # ID de operación creada
    if eval_query.id is not None:
        eval_query = repo.update_operation_id(eval_query.id, operation_id)
        print(f"✅ Consulta vinculada a operación {operation_id}")
    
    # 4. Registrar reevaluaciones periódicas
    print("\n4️⃣  Registrando reevaluaciones cada 10 minutos...")
    
    # Primera reevaluación
    reeval1 = repo.create_query(
        bot_id=1,
        ia_id=1,
        symbol="EURUSD",
        query_type=QueryType.REEVALUATION,
        prompt="Reevaluar posición EURUSD - Ciclo 1. Precio: 1.0870, SL: 1.0800, TP: 1.0950",
        response='{"decision": "MANTENER", "reason": "Operación saludable"}',
        tokens_input=100,
        tokens_output=40,
        cost_usd=0.0014,
        action_decided="MANTENER",
        operation_id=operation_id
    )
    print(f"   ✅ Reevaluación 1: {reeval1.action_decided}")
    
    # Segunda reevaluación
    reeval2 = repo.create_query(
        bot_id=1,
        ia_id=1,
        symbol="EURUSD",
        query_type=QueryType.REEVALUATION,
        prompt="Reevaluar posición EURUSD - Ciclo 2. Precio: 1.0890, SL: 1.0800, TP: 1.0950",
        response='{"decision": "ACTUALIZAR_SL", "new_sl": 1.0820, "reason": "Precio alcanzó 50% del TP"}',
        tokens_input=110,
        tokens_output=50,
        cost_usd=0.0016,
        action_decided="ACTUALIZAR_SL",
        operation_id=operation_id
    )
    print(f"   ✅ Reevaluación 2: {reeval2.action_decided}")
    
    # Tercera reevaluación
    reeval3 = repo.create_query(
        bot_id=1,
        ia_id=1,
        symbol="EURUSD",
        query_type=QueryType.REEVALUATION,
        prompt="Reevaluar posición EURUSD - Ciclo 3. Precio: 1.0945, SL: 1.0820, TP: 1.0950",
        response='{"decision": "CERRAR", "reason": "Precio cerca del TP, cerrar con beneficio"}',
        tokens_input=105,
        tokens_output=45,
        cost_usd=0.0015,
        action_decided="CERRAR",
        operation_id=operation_id
    )
    print(f"   ✅ Reevaluación 3: {reeval3.action_decided}")
    
    # 5. Consultar historial de la operación
    print(f"\n5️⃣  Consultando historial de operación {operation_id}...")
    operation_queries = repo.get_queries_by_operation_id(operation_id)
    print(f"✅ Se encontraron {len(operation_queries)} consultas:")
    for idx, query in enumerate(operation_queries, 1):
        print(f"   {idx}. {query.query_type.value.upper()}: {query.action_decided}")
    
    # 6. Consultas adicionales para otros bots/símbolos
    print("\n6️⃣  Registrando consultas para otros bots...")
    
    # Bot 2
    repo.create_query(
        bot_id=2,
        ia_id=1,
        symbol="GBPUSD",
        query_type=QueryType.EVALUATION,
        prompt="Analiza GBPUSD...",
        response='{"decision": "NO_OPERAR", "reason": "Condiciones desfavorables"}',
        tokens_input=120,
        tokens_output=60,
        cost_usd=0.0018,
        action_decided="NO_OPERAR"
    )
    
    # Bot 3
    repo.create_query(
        bot_id=3,
        ia_id=1,
        symbol="XAUUSD",
        query_type=QueryType.EVALUATION,
        prompt="Analiza XAUUSD...",
        response='{"decision": "OPERAR", "direction": "SELL"}',
        tokens_input=140,
        tokens_output=70,
        cost_usd=0.0021,
        action_decided="OPERAR"
    )
    print("✅ Consultas adicionales registradas")
    
    # 7. Estadísticas generales
    print("\n7️⃣  Calculando estadísticas generales...")
    stats = repo.get_statistics()
    print(f"✅ Estadísticas del sistema:")
    print(f"   - Total de consultas: {stats['total_queries']}")
    print(f"   - Costo total: ${stats['total_cost']:.4f}")
    print(f"   - Tokens input: {stats['total_tokens_input']:,}")
    print(f"   - Tokens output: {stats['total_tokens_output']:,}")
    print(f"   - Tokens totales: {stats['total_tokens_total']:,}")
    
    # 8. Estadísticas por bot
    print("\n8️⃣  Estadísticas por bot...")
    for bot_id in [1, 2, 3]:
        bot_stats = repo.get_statistics_by_bot(bot_id)
        if bot_stats['total_queries'] > 0:
            print(f"   Bot {bot_id}:")
            print(f"      - Consultas: {bot_stats['total_queries']}")
            print(f"      - Costo: ${bot_stats['total_cost']:.4f}")
    
    # 9. Costo por tipo de consulta
    print("\n9️⃣  Costo por tipo de consulta...")
    eval_cost = repo.get_cost_by_type(QueryType.EVALUATION)
    reeval_cost = repo.get_cost_by_type(QueryType.REEVALUATION)
    print(f"   - Evaluaciones: ${eval_cost:.4f}")
    print(f"   - Reevaluaciones: ${reeval_cost:.4f}")
    
    # 10. Consultar por símbolo
    print("\n🔟 Consultas por símbolo...")
    eurusd_queries = repo.get_queries_by_symbol("EURUSD")
    print(f"   - EURUSD: {len(eurusd_queries)} consultas")
    
    gbpusd_queries = repo.get_queries_by_symbol("GBPUSD")
    print(f"   - GBPUSD: {len(gbpusd_queries)} consultas")
    
    xauusd_queries = repo.get_queries_by_symbol("XAUUSD")
    print(f"   - XAUUSD: {len(xauusd_queries)} consultas")
    
    print("\n" + "="*80)
    print("✅ EJEMPLO COMPLETADO CON ÉXITO")
    print("="*80)
    print(f"\n📁 Base de datos creada en: {repo.db_path}")
    print("💡 Puedes inspeccionar la BD con: sqlite3 data/ia_queries.db")


if __name__ == "__main__":
    main()
