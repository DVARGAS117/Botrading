# 📝 Prompts de Bot 2 - Numérico Alternativo

Esta carpeta contiene los prompts enviados a Gemini 2.5 Pro cuando se ejecuta el bot con el flag `--save-prompts`.

## 📁 Estructura

```
prompts/
├── YYYYMMDD/                    # Carpeta por fecha
│   ├── prompt_HHMMSS_SYMBOL.txt
│   ├── prompt_HHMMSS_SYMBOL.txt
│   └── ...
└── README.md
```

## 🎯 Uso

```bash
# Activar guardado de prompts
python -m src.bots.bot_2.main --save-prompts
```

## 📄 Formato del archivo

Cada archivo contiene:
- **Metadata**: Timestamp, bot, símbolo, modo, intento
- **System Prompt**: Instrucciones del sistema
- **User Prompt**: Prompt del usuario con datos de mercado
- **Combined Prompt**: Prompt final enviado a Gemini

## 🔍 Ejemplo de uso

Útil para:
- ✅ Validar que el prompt contiene la información correcta
- ✅ Debug de decisiones de la IA
- ✅ Auditoría de consultas realizadas
- ✅ Comparar prompts alternativos vs Bot 1
- ✅ Análisis retrospectivo de operaciones

## ⚠️ Nota

Los archivos `.txt` están excluidos del control de versiones (git) para evitar llenar el repositorio.
