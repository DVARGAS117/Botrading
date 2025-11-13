"""
Ejemplo de Parametrización de Modelo y Timeout - T13

Este ejemplo demuestra cómo cargar y actualizar la configuración
del cliente Gemini desde archivos JSON, permitiendo experimentación
con diferentes parámetros sin modificar el código.

Author: Botrading Team
Date: 2025-11-13
"""

import json
import os
from src.core.gemini_client import GeminiClient, GeminiConfig


def create_example_configs():
    """Crea archivos de configuración de ejemplo para experimentación"""

    configs = {
        "conservative": {
            "model": "gemini-2.0-flash-exp",
            "temperature": 0.1,
            "max_tokens": 512,
            "timeout": 15,
            "retry_attempts": 2
        },
        "balanced": {
            "model": "gemini-2.5-pro",
            "temperature": 0.7,
            "max_tokens": 2048,
            "timeout": 30,
            "retry_attempts": 3
        },
        "creative": {
            "model": "gemini-2.5-pro",
            "temperature": 0.9,
            "max_tokens": 4096,
            "timeout": 60,
            "retry_attempts": 5
        }
    }

    # Crear directorio si no existe
    os.makedirs("config/experiments", exist_ok=True)

    for name, config in configs.items():
        filename = f"config/experiments/{name}_config.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuración '{name}' creada: {filename}")

    return list(configs.keys())


def demonstrate_config_loading():
    """Demuestra carga de configuración desde archivo"""

    print("\n🔧 DEMOSTRACIÓN: Carga de Configuración desde JSON")
    print("=" * 60)

    # Cargar configuración desde archivo
    try:
        config = GeminiConfig.from_json_file("config/ia_config.example.json")
        print("✅ Configuración cargada exitosamente:")
        print(f"   Modelo: {config.model}")
        print(f"   Temperatura: {config.temperature}")
        print(f"   Max tokens: {config.max_tokens}")
        print(f"   Timeout: {config.timeout}s")

    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return None

    return config


def demonstrate_runtime_updates():
    """Demuestra actualización de configuración en tiempo real"""

    print("\n🔄 DEMOSTRACIÓN: Actualización en Tiempo Real")
    print("=" * 60)

    # Crear cliente con configuración inicial
    initial_config = GeminiConfig(
        model="gemini-2.0-flash-exp",
        temperature=0.5,
        max_tokens=1024,
        timeout=20
    )

    # Nota: Usar API key real en producción
    client = GeminiClient(api_key="DEMO_API_KEY", config=initial_config)

    print("📊 Configuración inicial:")
    print(f"   Modelo: {client.config.model}")
    print(f"   Temperatura: {client.config.temperature}")
    print(f"   Max tokens: {client.config.max_tokens}")
    print(f"   Timeout: {client.config.timeout}s")

    # Crear archivos de experimento
    experiment_names = create_example_configs()

    # Probar cada configuración
    for exp_name in experiment_names:
        config_file = f"config/experiments/{exp_name}_config.json"

        try:
            print(f"\n🔄 Aplicando configuración '{exp_name}'...")
            client.update_config_from_file(config_file)

            print("✅ Configuración actualizada:")
            print(f"   Modelo: {client.config.model}")
            print(f"   Temperatura: {client.config.temperature}")
            print(f"   Max tokens: {client.config.max_tokens}")
            print(f"   Timeout: {client.config.timeout}s")

            # En producción, aquí iría la llamada real a la IA
            print(f"   → Próxima llamada a IA usará configuración '{exp_name}'")

        except Exception as e:
            print(f"❌ Error actualizando configuración '{exp_name}': {e}")


def demonstrate_error_handling():
    """Demuestra manejo de errores en carga de configuración"""

    print("\n🚨 DEMOSTRACIÓN: Manejo de Errores")
    print("=" * 60)

    error_cases = [
        ("Archivo inexistente", "config/nonexistent.json"),
        ("JSON inválido", "config/invalid.json"),
        ("Archivo válido", "config/ia_config.example.json")
    ]

    for case_name, file_path in error_cases:
        print(f"\n🔍 Probando: {case_name} ({file_path})")

        try:
            if "invalid" in file_path:
                # Crear archivo con JSON inválido
                os.makedirs("config", exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write("invalid json content {")

            config = GeminiConfig.from_json_file(file_path)
            print("✅ Carga exitosa")
            print(f"   Modelo: {config.model}")

        except FileNotFoundError:
            print("❌ Error: Archivo no encontrado")
        except json.JSONDecodeError:
            print("❌ Error: JSON inválido")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

        finally:
            # Limpiar archivo de prueba
            if "invalid" in file_path and os.path.exists(file_path):
                os.remove(file_path)


def main():
    """Función principal del ejemplo"""

    print("🚀 EJEMPLO T13: Parametrización de Modelo y Timeout")
    print("=" * 60)
    print("Este ejemplo muestra cómo parametrizar el cliente Gemini")
    print("usando archivos JSON para experimentación flexible.\n")

    # Demostración 1: Carga básica
    config = demonstrate_config_loading()
    if not config:
        print("❌ No se pudo cargar configuración básica. Abortando.")
        return

    # Demostración 2: Actualizaciones en tiempo real
    demonstrate_runtime_updates()

    # Demostración 3: Manejo de errores
    demonstrate_error_handling()

    print("\n" + "=" * 60)
    print("✅ EJEMPLO COMPLETADO")
    print("\n📝 RECOMENDACIONES:")
    print("• Usa archivos JSON separados para diferentes experimentos")
    print("• Valida la configuración antes de usar en producción")
    print("• Monitorea el rendimiento con diferentes parámetros")
    print("• Documenta los resultados de cada experimento")


if __name__ == "__main__":
    main()