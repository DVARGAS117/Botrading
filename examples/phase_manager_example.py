"""
Ejemplo de uso del PhaseManager.

Este script demuestra cómo usar el módulo PhaseManager para gestionar
las fases del proyecto Botrading y sus criterios de salida.

Autor: GitHub Copilot
Fecha: 15 de noviembre de 2025
Ticket: #66 (T50)
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from src.core.phase_manager import PhaseManager


def print_separator(char="=", length=70):
    """Imprime una línea separadora."""
    print(char * length)


def example_basic_usage():
    """Ejemplo 1: Uso básico del PhaseManager."""
    print("\n")
    print_separator()
    print("EJEMPLO 1: USO BÁSICO DEL PHASE MANAGER")
    print_separator()
    
    # Inicializar el gestor de fases
    manager = PhaseManager("config/phases.example.json")
    
    # Obtener la fase actual
    current_phase = manager.get_current_phase()
    print(f"\n📌 Fase actual: {current_phase.phase_number} - {current_phase.name}")
    print(f"   Descripción: {current_phase.description}")
    print(f"   Prioridad: {current_phase.priority}")
    
    # Mostrar criterios de la fase
    print(f"\n📋 Criterios de salida ({len(current_phase.criteria)} total):")
    for i, criteria in enumerate(current_phase.criteria, 1):
        status = "✅" if criteria.is_completed else "❌"
        optional = " [OPCIONAL]" if criteria.is_optional() else ""
        print(f"   {i}. {status} {criteria.id}: {criteria.description}{optional}")


def example_mark_criteria_completed():
    """Ejemplo 2: Marcar criterios como completados."""
    print("\n")
    print_separator()
    print("EJEMPLO 2: MARCAR CRITERIOS COMO COMPLETADOS")
    print_separator()
    
    manager = PhaseManager("config/phases.example.json")
    
    # Obtener fase 0
    phase0 = manager.get_phase(0)
    print(f"\n📌 Trabajando en Fase {phase0.phase_number}: {phase0.name}")
    
    # Marcar algunos criterios como completados
    print("\n⏳ Completando criterios...")
    
    # Completar el primer criterio
    success, message = manager.mark_criteria_completed(0, "P0_001")
    print(f"   {message}")
    
    # Completar el segundo criterio
    success, message = manager.mark_criteria_completed(0, "P0_002")
    print(f"   {message}")
    
    # Mostrar progreso
    progress = manager.get_phase_progress(0)
    print(f"\n📊 Progreso de Fase 0:")
    print(f"   Completados: {progress['completed']}/{progress['total']}")
    print(f"   Porcentaje: {progress['percentage']:.1f}%")


def example_phase_advancement():
    """Ejemplo 3: Avanzar a la siguiente fase."""
    print("\n")
    print_separator()
    print("EJEMPLO 3: AVANZAR A LA SIGUIENTE FASE")
    print_separator()
    
    manager = PhaseManager("config/phases.example.json")
    
    # Intentar avanzar sin completar criterios
    print("\n⚠️  Intentando avanzar sin completar criterios...")
    can_advance, message = manager.can_advance_to_next_phase()
    print(f"   ¿Puede avanzar? {can_advance}")
    if not can_advance:
        print(f"   Motivo: {message}")
    
    # Completar todos los criterios críticos de Fase 0
    print("\n✅ Completando todos los criterios críticos de Fase 0...")
    phase0 = manager.get_phase(0)
    for criteria in phase0.criteria:
        if not criteria.is_optional():
            criteria.mark_completed()
            print(f"   ✓ {criteria.id} completado")
    
    # Verificar que la fase está completa
    phase0.check_completion()
    print(f"\n✅ Fase 0 completada: {phase0.is_completed}")
    
    # Avanzar a la siguiente fase
    print("\n🚀 Avanzando a la siguiente fase...")
    success, message = manager.advance_to_next_phase()
    print(f"   {message}")
    
    if success:
        current = manager.get_current_phase()
        print(f"\n📌 Nueva fase actual: {current.phase_number} - {current.name}")


def example_overall_progress():
    """Ejemplo 4: Progreso general del proyecto."""
    print("\n")
    print_separator()
    print("EJEMPLO 4: PROGRESO GENERAL DEL PROYECTO")
    print_separator()
    
    manager = PhaseManager("config/phases.example.json")
    
    # Simular progreso en varias fases
    print("\n⏳ Simulando progreso del proyecto...")
    
    # Completar algunos criterios en diferentes fases
    manager.mark_criteria_completed(0, "P0_001")
    manager.mark_criteria_completed(0, "P0_002")
    manager.mark_criteria_completed(1, "P1_001")
    
    # Obtener progreso general
    progress = manager.get_overall_progress()
    
    print(f"\n📊 ESTADÍSTICAS GENERALES DEL PROYECTO")
    print(f"   Total de fases: {progress['total_phases']}")
    print(f"   Fases completadas: {progress['completed_phases']}")
    print(f"   Fase actual: {progress['current_phase']} - {progress['current_phase_name']}")
    print(f"   Total de criterios: {progress['total_criteria']}")
    print(f"   Criterios completados: {progress['completed_criteria']}")
    print(f"   Progreso general: {progress['overall_percentage']:.1f}%")


def example_phase_report():
    """Ejemplo 5: Generar reporte de una fase."""
    print("\n")
    print_separator()
    print("EJEMPLO 5: GENERAR REPORTE DE UNA FASE")
    print_separator()
    
    manager = PhaseManager("config/phases.example.json")
    
    # Completar algunos criterios para hacer el reporte más interesante
    manager.mark_criteria_completed(0, "P0_001")
    manager.mark_criteria_completed(0, "P0_003")
    
    # Generar reporte de Fase 0
    print("\n📄 Generando reporte de Fase 0...")
    report = manager.get_phase_report(0)
    print(report)


def example_save_and_load_state():
    """Ejemplo 6: Guardar y cargar estado del proyecto."""
    print("\n")
    print_separator()
    print("EJEMPLO 6: GUARDAR Y CARGAR ESTADO")
    print_separator()
    
    # Crear gestor y hacer algunos cambios
    manager = PhaseManager("config/phases.example.json")
    
    print("\n💾 Realizando cambios y guardando estado...")
    manager.mark_criteria_completed(0, "P0_001")
    manager.mark_criteria_completed(0, "P0_002")
    manager.mark_criteria_completed(0, "P0_003")
    
    # Guardar estado
    state_file = "data/phase_state_example.json"
    manager.save_state(state_file)
    print(f"   Estado guardado en: {state_file}")
    
    # Crear nuevo gestor y cargar estado
    print("\n📂 Cargando estado guardado...")
    manager2 = PhaseManager("config/phases.example.json")
    manager2.load_state(state_file)
    
    # Verificar que el estado se cargó correctamente
    phase0 = manager2.get_phase(0)
    completed_count = len([c for c in phase0.criteria if c.is_completed])
    print(f"   Criterios completados restaurados: {completed_count}")
    
    # Limpiar archivo de ejemplo
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"   Archivo de ejemplo eliminado: {state_file}")


def example_complete_workflow():
    """Ejemplo 7: Flujo completo de trabajo."""
    print("\n")
    print_separator()
    print("EJEMPLO 7: FLUJO COMPLETO DE TRABAJO")
    print_separator()
    
    manager = PhaseManager("config/phases.example.json")
    
    print("\n🎯 Simulando flujo completo de desarrollo del proyecto Botrading...")
    
    # Fase 0: Fundamentos
    print("\n" + "─" * 70)
    print("FASE 0: Fundamentos")
    print("─" * 70)
    
    phase0 = manager.get_phase(0)
    print(f"Trabajando en {len(phase0.criteria)} criterios...")
    
    # Simular completar criterios
    for criteria in phase0.criteria:
        if not criteria.is_optional():
            criteria.mark_completed()
            print(f"  ✅ {criteria.description}")
    
    # Verificar completitud
    phase0.check_completion()
    print(f"\n✨ Fase 0 completa! Progreso: {phase0.get_completion_percentage():.0f}%")
    
    # Avanzar a Fase 1
    success, message = manager.advance_to_next_phase()
    if success:
        print(f"\n🚀 {message}")
        
        # Mostrar nueva fase
        phase1 = manager.get_current_phase()
        print(f"\n📌 Ahora en: Fase {phase1.phase_number} - {phase1.name}")
        print(f"   {len(phase1.criteria)} criterios por completar")
        
        # Mostrar progreso general
        progress = manager.get_overall_progress()
        print(f"\n📊 Progreso del proyecto: {progress['overall_percentage']:.1f}%")


def main():
    """Función principal que ejecuta todos los ejemplos."""
    print("\n")
    print_separator("=")
    print("    EJEMPLOS DE USO DEL PHASE MANAGER - PROYECTO BOTRADING")
    print_separator("=")
    print("\nEste script demuestra el uso del PhaseManager para gestionar")
    print("las fases del proyecto y sus criterios de salida.")
    
    try:
        # Ejecutar ejemplos
        example_basic_usage()
        example_mark_criteria_completed()
        example_phase_advancement()
        example_overall_progress()
        example_phase_report()
        example_save_and_load_state()
        example_complete_workflow()
        
        print("\n")
        print_separator("=")
        print("✅ TODOS LOS EJEMPLOS EJECUTADOS EXITOSAMENTE")
        print_separator("=")
        print("\n💡 Tip: Puedes adaptar estos ejemplos para tu flujo de trabajo específico.")
        print("📖 Ver documentación completa en: context/DOCUMENTACION/T50_avance_por_fases.md\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Asegúrate de que el archivo config/phases.example.json existe.")
        print("   Ejecuta este script desde el directorio raíz del proyecto.\n")
        return 1
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
