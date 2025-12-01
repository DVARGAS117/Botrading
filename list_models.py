import json
import os
import sys
import google.generativeai as genai

def load_credentials():
    try:
        with open("config/credentials.json", "r") as f:
            creds = json.load(f)
            return creds.get("gemini", {}).get("api_key")
    except Exception as e:
        print(f"Error cargando credenciales: {e}")
        return None

def main():
    api_key = load_credentials()
    if not api_key:
        print("No API Key found")
        return

    genai.configure(api_key=api_key)
    
    print("Listando modelos disponibles...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listando modelos: {e}")

if __name__ == "__main__":
    main()
