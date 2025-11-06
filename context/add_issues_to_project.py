#!/usr/bin/env python3
"""
Script para vincular automáticamente todos los issues al GitHub Project v2
Utiliza GraphQL API para añadir items al proyecto
"""

import subprocess
import json
import sys

PROJECT_ID = "PVT_kwHODXaYj84BHQWk"
OWNER = "DVARGAS117"
REPO = "Botrading"

def run_command(cmd: list) -> str:
    """Ejecutar comando gh y retornar output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None

def get_all_issues() -> list:
    """Obtener todos los issues del repositorio"""
    cmd = [
        "gh", "issue", "list",
        "-R", f"{OWNER}/{REPO}",
        "--json", "number,title,state",
        "--limit", "100"
    ]
    
    output = run_command(cmd)
    if output:
        return json.loads(output)
    return []

def add_issue_to_project(issue_number: int) -> bool:
    """Añadir un issue al proyecto usando GraphQL"""
    # Obtener el node ID del issue
    query = f"""
query {{
  repository(owner: "{OWNER}", name: "{REPO}") {{
    issue(number: {issue_number}) {{
      id
    }}
  }}
}}
"""
    
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    output = run_command(cmd)
    
    if not output:
        return False
    
    try:
        data = json.loads(output)
        issue_id = data['data']['repository']['issue']['id']
    except (KeyError, json.JSONDecodeError):
        return False
    
    # Añadir el issue al proyecto
    mutation = f"""
mutation {{
  addProjectV2ItemById(input: {{
    projectId: "{PROJECT_ID}"
    contentId: "{issue_id}"
  }}) {{
    item {{
      id
    }}
  }}
}}
"""
    
    cmd = ["gh", "api", "graphql", "-f", f"query={mutation}"]
    result = run_command(cmd)
    
    return result is not None

def main():
    print("🔗 Vinculando issues al GitHub Project v2...\n")
    
    # Obtener todos los issues
    print("📋 Obteniendo issues del repositorio...")
    issues = get_all_issues()
    
    if not issues:
        print("❌ No se encontraron issues")
        sys.exit(1)
    
    print(f"✅ Encontrados {len(issues)} issues\n")
    print("="*60)
    print("VINCULANDO AL PROYECTO")
    print("="*60 + "\n")
    
    successful = 0
    failed = 0
    
    for issue in issues:
        number = issue['number']
        title = issue['title'][:50]
        
        print(f"[#{number}] {title:50s} ... ", end="", flush=True)
        
        if add_issue_to_project(number):
            print("✅")
            successful += 1
        else:
            print("❌")
            failed += 1
    
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print(f"✅ Vinculados: {successful}")
    print(f"❌ Fallidos: {failed}")
    print(f"Total: {len(issues)}")
    
    print(f"\n📍 Ver proyecto en:")
    print(f"   https://github.com/users/{OWNER}/projects/2")
    
    if failed == 0:
        print("\n🎉 ¡Todos los issues vinculados exitosamente!")
    else:
        print(f"\n⚠️  {failed} issues no pudieron vincularse. Intenta manualmente desde la web.")

if __name__ == "__main__":
    main()
