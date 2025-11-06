#!/usr/bin/env python3
"""
Script mejorado para crear tickets en GitHub Projects v2
Crea etiquetas primero, luego issues sin asignar labels
"""

import json
import subprocess
import sys
from typing import Dict, List, Any

# Configuración
PROJECT_ID = "PVT_kwHODXaYj84BHQWk"
PROJECT_NUMBER = 2
OWNER = "DVARGAS117"
REPO = "Botrading"

def run_command(cmd: List[str]) -> str:
    """Ejecutar comando y retornar output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None

def create_labels() -> bool:
    """Crear labels necesarias"""
    labels = [
        ("epic", "16a34b"),          # Verde oscuro
        ("phase-0", "fdbf56"),       # Amarillo
        ("phase-1", "0366d6"),       # Azul
        ("phase-2", "6f42c1"),       # Morado
        ("phase-3", "f1a208"),       # Naranja
        ("phase-4", "d73a49"),       # Rojo
        ("P0", "d73a49"),            # Rojo
        ("P1", "f1a208"),            # Naranja
    ]
    
    print("📏 Creando etiquetas...")
    for label, color in labels:
        cmd = [
            "gh", "label", "create", label,
            "-R", f"{OWNER}/{REPO}",
            "-c", color,
            "--force"
        ]
        result = run_command(cmd)
        if result:
            print(f"  ✅ Etiqueta '{label}' creada")
        else:
            print(f"  ⚠️  Etiqueta '{label}' ya existe o error")
    
    return True

def create_epic_issue(epic: Dict[str, Any]) -> str:
    """Crear un issue para la épica"""
    title = f"📌 {epic['title']}"
    body = f"""# Épica: {epic['title']}

**Descripción:**
{epic['description']}

**Fase:** {epic['phase']}
**Prioridad:** {epic['priority']}

---
_Generado automáticamente_
"""
    
    cmd = [
        "gh", "issue", "create",
        "-R", f"{OWNER}/{REPO}",
        "-t", title,
        "-b", body
    ]
    
    issue_url = run_command(cmd)
    if issue_url:
        issue_number = issue_url.split("/")[-1]
        return issue_number
    return None

def create_ticket(ticket: Dict[str, Any], epic_number: str) -> str:
    """Crear un issue para el ticket"""
    title = f"[T{ticket['number']:02d}] {ticket['title']}"
    body = f"""## Historia de Usuario
{ticket['description']}

## Criterios de Aceptación
```gherkin
{ticket['acceptance_criteria']}
```

**Relación:** Épica #{epic_number}
**Fase:** {ticket['phase']}
**Prioridad:** {ticket['priority']}

---
_Generado automáticamente desde tareas.md_
"""
    
    cmd = [
        "gh", "issue", "create",
        "-R", f"{OWNER}/{REPO}",
        "-t", title,
        "-b", body
    ]
    
    issue_url = run_command(cmd)
    if issue_url:
        issue_number = issue_url.split("/")[-1]
        return issue_number
    return None

def add_labels_to_issue(issue_number: str, labels: List[str]) -> bool:
    """Agregar etiquetas a un issue"""
    for label in labels:
        cmd = [
            "gh", "issue", "edit", issue_number,
            "-R", f"{OWNER}/{REPO}",
            "-a", label
        ]
        run_command(cmd)
    return True

def main():
    print("🤖 Iniciando creación de tickets en GitHub Projects...\n")
    
    # Cargar JSON
    try:
        with open("tickets.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ No se encontró tickets.json")
        sys.exit(1)
    
    print(f"📊 Encontrados:")
    print(f"   - {len(data['epics'])} épicas")
    print(f"   - {len(data['tickets'])} tickets\n")
    
    # Crear etiquetas
    create_labels()
    
    print("\n" + "="*60)
    print("CREANDO ÉPICAS")
    print("="*60 + "\n")
    
    epic_issues = {}
    
    for epic in data['epics']:
        print(f"📌 {epic['title']}", end=" ... ")
        epic_number = create_epic_issue(epic)
        if epic_number:
            epic_issues[epic['id']] = epic_number
            # Agregar labels a épica
            add_labels_to_issue(epic_number, ["epic", f"phase-{epic['phase']}", epic['priority']])
            print(f"#{epic_number}")
        else:
            print("❌")
    
    print("\n" + "="*60)
    print("CREANDO TICKETS")
    print("="*60 + "\n")
    
    tickets_created = 0
    for i, ticket in enumerate(data['tickets'], 1):
        epic_id = ticket['epic']
        epic_number = epic_issues.get(epic_id, "?")
        
        print(f"[{i:2d}/52] T{ticket['number']:02d}: {ticket['title'][:40]:40s} ... ", end="", flush=True)
        issue_number = create_ticket(ticket, epic_number)
        if issue_number:
            # Agregar labels
            add_labels_to_issue(issue_number, [f"phase-{ticket['phase']}", ticket['priority']])
            tickets_created += 1
            print(f"#{issue_number}")
        else:
            print("❌")
    
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print(f"✅ Épicas creadas: {len(epic_issues)}")
    print(f"✅ Tickets creados: {tickets_created}/{len(data['tickets'])}")
    print(f"\n📍 Ver proyecto en:")
    print(f"   https://github.com/users/{OWNER}/projects/{PROJECT_NUMBER}")
    print(f"\n📍 O ver issues en:")
    print(f"   https://github.com/{OWNER}/{REPO}/issues")
    print("\n✅ Ahora debes añadir estos issues al proyecto GitHub Projects manualmente")
    print("   desde la interfaz web, o usar la API de GraphQL si tienes permisos.")

if __name__ == "__main__":
    main()
