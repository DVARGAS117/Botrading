# 🚀 Guía de Inicio Rápido - Bot INTRADAY

## ⚡ Configuración en 5 Minutos

### 1. Requisitos Previos

```bash
✅ Python 3.13+
✅ MetaTrader 5 instalado
✅ Cuenta MT5 (demo o real)
✅ API Key de Google Cloud (Vertex AI)
✅ Git
```

### 2. Instalación

```bash
# Clonar repositorio
git clone https://github.com/DVARGAS117/Botrading.git
cd Botrading

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración Rápida

#### a) Copiar archivos de configuración

```bash
cp config/credentials.example.json config/credentials.json
cp config/settings.example.json config/settings.json
cp config/schedule.example.json config/schedule.json
cp config/ia_config.example.json config/ia_config.json
```

#### b) Editar credenciales

**Archivo**: `config/credentials.json`

```json
{
  "google_cloud": {
    "project_id": "TU-PROJECT-ID",
    "location": "us-central1",
    "api_key": "TU-API-KEY-AQUI"
  },
  "mt5": {
    "login": 12345678,
    "password": "tu-password-mt5",
    "server": "MetaQuotes-Demo"
  }
}
```

#### c) Configurar horarios (opcional)

**Archivo**: `config/schedule.json`

```json
{
  "sessions": {
    "american": {
      "name": "American Session",
      "start": "08:00",
      "end": "17:00",
      "timezone": "America/Lima",
      "symbols": ["EURUSD", "GBPUSD", "USDJPY"]
    }
  }
}
```

### 4. Ejecutar el Bot

```bash
# Activar entorno virtual
.venv\Scripts\activate  # Windows

# Ejecutar bot (siempre pregunta modo de evaluación)
python src/bots/strategies/intraday/gemini_3_pro/bot_1/main.py

# El bot preguntará automáticamente:
# ⏰ MODO DE EVALUACIÓN
# El bot puede:
# • INSTANT: Evaluar inmediatamente con datos disponibles
# • WAIT: Esperar el próximo ciclo de vela cerrada (1 min después)
# ¿Deseas evaluar al INSTANTE o ESPERAR el ciclo? (instant/wait):
```

**Nota**: El bot **siempre** pregunta el modo de evaluación al iniciar, garantizando que uses velas cerradas.

### 5. Verificar que Funciona

#### a) Revisar logs

```bash
# Ver logs en tiempo real
tail -f src/bots/strategies/intraday/gemini_3_pro/bot_1/logs/bot_101.log
```

**Logs esperados**:
```
2025-11-20 10:00:00 [INFO] Bot 1 (INTRADAY Baseline) inicializado
2025-11-20 10:00:01 [INFO] ✅ Símbolos activos para operar: EURUSD, GBPUSD
2025-11-20 10:00:02 [INFO] 📊 Procesando EURUSD...
2025-11-20 10:00:03 [INFO] Calculando paquetes INTRADAY para EURUSD
2025-11-20 10:00:05 [INFO] Datos INTRADAY preparados para EURUSD
2025-11-20 10:00:06 [INFO] Consultando Gemini 3 Pro para EURUSD
```

#### b) Verificar base de datos

```bash
# Instalar SQLite viewer (opcional)
pip install sqlite-web

# Ver consultas IA
sqlite-web data/consultas_ia.db

# Ver operaciones
sqlite-web data/operations.db
```

---

## 🎯 Comandos Útiles

### Ejecución

```bash
# Ejecutar bot (siempre pregunta modo de evaluación)
python src/bots/strategies/intraday/gemini_3_pro/bot_1/main.py

# Con nivel de log específico
python src/bots/strategies/intraday/gemini_3_pro/bot_1/main.py --log-level DEBUG

# Modo demo (para testing)
python src/bots/strategies/intraday/gemini_3_pro/bot_1/main.py --mode demo

# Modo live (requiere confirmación)
python src/bots/strategies/intraday/gemini_3_pro/bot_1/main.py --mode live
```

### Testing

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Tests del bot INTRADAY
pytest tests/bots/strategies/intraday/ -v

# Tests con cobertura
pytest tests/ -v --cov=src --cov-report=html
```

### Monitoreo

```bash
# Ver logs en tiempo real
tail -f src/bots/strategies/intraday/gemini_3_pro/bot_1/logs/bot_101.log

# Ver últimas 100 líneas
tail -100 src/bots/strategies/intraday/gemini_3_pro/bot_1/logs/bot_101.log

# Buscar errores
grep "ERROR" src/bots/strategies/intraday/gemini_3_pro/bot_1/logs/bot_101.log
```

---

## 🔍 Verificación de Componentes

### 1. Conexión MT5

```python
from src.core.mt5_connector import MT5Connector

mt5 = MT5Connector()
if mt5.initialize():
    print("✅ Conexión MT5 exitosa")
    info = mt5.symbol_info("EURUSD")
    print(f"Símbolo EURUSD disponible: {info is not None}")
else:
    print("❌ Error en conexión MT5")
```

### 2. Vertex AI (Gemini)

```python
from src.core.vertex_ai_client import VertexAIClient, VertexAIConfig

config = VertexAIConfig(
    model="gemini-3-pro-preview",
    temperature=0.7,
    max_tokens=8192
)

client = VertexAIClient(config=config)
response = client.send_prompt("Hola, ¿funcionas correctamente?")

if response.success:
    print("✅ Vertex AI funcionando")
    print(f"Respuesta: {response.content[:100]}...")
else:
    print(f"❌ Error: {response.error_message}")
```

### 3. Cálculo de Indicadores

```python
from src.core.mt5_data_extractor import MT5DataExtractor
from src.bots.strategies.intraday.gemini_3_pro.bot_1.intraday_indicators import IntradayIndicatorCalculator

extractor = MT5DataExtractor()
calculator = IntradayIndicatorCalculator(extractor)

packages = calculator.get_full_intraday_packages("EURUSD")

print(f"✅ Paquete M15: {len(packages['tactical_m15'])} velas")
print(f"✅ Paquete D1: {len(packages['strategic_d1'])} velas")
```

---

## ⚠️ Problemas Comunes

### Error: "MT5 not initialized"

**Solución**: Asegúrate de que MetaTrader 5 esté abierto y ejecutándose.

```bash
# Verificar proceso MT5 (Windows)
tasklist | findstr "terminal64.exe"
```

### Error: "Invalid Google Cloud API Key"

**Solución**: Verifica tu API key en `config/credentials.json`

```bash
# Probar API key manualmente
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://us-central1-aiplatform.googleapis.com/v1/projects/YOUR_PROJECT/locations/us-central1
```

### Error: "Datos insuficientes para EURUSD M15"

**Solución**: El broker debe tener suficiente histórico. Prueba con otro símbolo o espera a que se acumule más histórico.

```python
# Verificar histórico disponible
from src.core.mt5_data_extractor import MT5DataExtractor, Timeframe

extractor = MT5DataExtractor()
ohlcv = extractor.get_ohlcv("EURUSD", Timeframe.M15, count=500)
print(f"Velas disponibles: {ohlcv.count}")
```

---

## 📊 Dashboard de Métricas (Próximamente)

```python
# Consultar métricas del bot
from src.core.daily_metrics_repository import DailyMetricsRepository

repo = DailyMetricsRepository()
metrics = repo.get_metrics_by_bot_and_date(bot_id=101, date="2025-11-20")

print(f"Trades ejecutados: {metrics.trades_executed}")
print(f"PnL total: {metrics.total_pnl_r:.2f}R (${metrics.total_pnl_usd:.2f})")
print(f"Costo IA: ${metrics.ia_cost_total:.4f}")
print(f"Win rate: {metrics.win_rate:.1f}%")
```

---

## 🎓 Próximos Pasos

1. ✅ **Personalizar Prompts**
   - Editar `config/prompt_templates/intraday_gemini_3_pro_bot_1_system.txt`
   - Editar `config/prompt_templates/intraday_gemini_3_pro_bot_1_user.txt`

2. ✅ **Ajustar Configuración**
   - Modificar `risk_per_trade` y `max_daily_risk` en `BotConfig`
   - Configurar horarios en `config/schedule.json`

3. ✅ **Monitorear Rendimiento**
   - Revisar logs diariamente
   - Analizar métricas en base de datos
   - Ajustar parámetros según resultados

4. ✅ **Leer Documentación Completa**
   - [Guía Completa del Bot](INTRADAY_BOT_GUIDE.md)
   - [Vertex AI Setup](VERTEX_AI_SETUP.md)
   - [Gemini Pricing](GEMINI_PRICING.md)

---

## 📞 Ayuda

- **Documentación**: Ver `docs/`
- **GitHub Issues**: https://github.com/DVARGAS117/Botrading/issues
- **Logs del Bot**: `src/bots/strategies/intraday/gemini_3_pro/bot_1/logs/`

---

**¡Listo para operar! 🚀**
