# T26 - Reevaluación Periódica cada 10 Minutos

**Ticket:** #42  
**Fase:** 2  
**Prioridad:** P1  
**Estado:** 🚧 En Desarrollo

---

## 📋 Resumen

Este ticket implementa el sistema de reevaluación periódica de operaciones abiertas, permitiendo al bot monitorear y ajustar activamente las posiciones cada 10 minutos con datos actualizados del mercado.

**Beneficio Principal:**
- ✅ Gestión activa del riesgo mediante reevaluaciones periódicas
- ✅ Reacción rápida a cambios de mercado con datos actualizados
- ✅ Optimización de resultados mediante trailing stops y ajustes dinámicos
- ✅ Experimentación con dos modos: conversación persistente vs. nueva conversación

---

## 🎯 Historia de Usuario

> Como bot, quiero reevaluar operaciones abiertas cada 10 minutos con velas cerradas e indicadores actuales, para reaccionar a cambios de mercado.

---

## ✅ Criterios de Aceptación

```gherkin
Escenario: Reevaluar cada 10 minutos con datos actualizados
  Dado que existe una posición abierta
  Cuando se cumple el intervalo de 10 minutos desde la última reevaluación
  Entonces el bot envía nueva evaluación con velas cerradas e indicadores actuales
```

---

## 🏗️ Arquitectura

### Componentes Principales

```
┌─────────────────────────┐
│  ReevaluationScheduler  │  Gestiona intervalos de 10 min
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  ReevaluationManager    │  Coordina proceso de reevaluación
└───────────┬─────────────┘
            │
            ├──► MT5DataExtractor      (Datos actualizados)
            ├──► PromptBuilder         (Construye prompt de reevaluación)
            ├──► GeminiClient          (Consulta a IA)
            ├──► AIResponseParser      (Parsea decisión)
            └──► PositionManager       (Ejecuta acción)
```

### Flujo de Reevaluación

```
1. TRIGGER (cada 10 min)
   ↓
2. OBTENER POSICIONES ABIERTAS
   ↓
3. POR CADA POSICIÓN:
   ├─► Extraer datos actualizados (MT5)
   ├─► Calcular indicadores actuales
   ├─► Construir prompt de reevaluación
   ├─► Enviar a IA (con o sin contexto previo)
   ├─► Parsear decisión (MANTENER/ACTUALIZAR/CERRAR)
   └─► Ejecutar acción en MT5
   ↓
4. REGISTRAR TRAZABILIDAD
   ↓
5. ESPERAR PRÓXIMO INTERVALO
```

---

## 📦 Módulos a Implementar

### 1. ReevaluationScheduler (`src/core/reevaluation_scheduler.py`)

**Responsabilidad:** Gestionar intervalos de 10 minutos para reevaluaciones

**Características:**
- Timer preciso cada 10 minutos
- Verificación de horario operacional (06:00-13:00 Lima)
- Coordinación con otros ciclos del bot
- Registro de última reevaluación por posición
- Soporte para modo demo y producción

**Interfaz:**

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Callable
import asyncio

@dataclass
class ReevaluationConfig:
    """Configuración del scheduler de reevaluación"""
    interval_minutes: int = 10
    enabled: bool = True
    timezone: str = "America/Lima"
    trading_window_start: str = "06:00"
    trading_window_end: str = "13:00"

class ReevaluationScheduler:
    """Gestiona el scheduling de reevaluaciones periódicas"""
    
    def __init__(self, config: ReevaluationConfig):
        self.config = config
        self.last_reevaluation: Dict[str, datetime] = {}
        self.is_running = False
    
    def should_reevaluate(self, position_id: str) -> bool:
        """Determina si una posición debe reevaluarse"""
        pass
    
    def mark_reevaluated(self, position_id: str):
        """Marca una posición como reevaluada"""
        pass
    
    async def start(self, callback: Callable):
        """Inicia el scheduler con callback periódico"""
        pass
    
    def stop(self):
        """Detiene el scheduler"""
        pass
```

---

### 2. ReevaluationManager (`src/core/reevaluation_manager.py`)

**Responsabilidad:** Coordinar el proceso completo de reevaluación

**Características:**
- Obtener posiciones abiertas filtradas por Magic Number
- Extraer datos actualizados del mercado
- Construir prompts de reevaluación
- Manejar dos modos: conversación persistente vs. nueva conversación
- Ejecutar decisiones de IA (MANTENER/ACTUALIZAR/CERRAR)
- Registrar trazabilidad completa
- Tracking de tokens y costos

**Interfaz:**

```python
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

class ReevaluationMode(Enum):
    """Modo de reevaluación"""
    PERSISTENT_CONVERSATION = "persistent"  # Mantiene contexto en misma conversación
    NEW_CONVERSATION = "new"                # Crea nueva conversación cada vez

@dataclass
class ReevaluationContext:
    """Contexto de una reevaluación"""
    position_id: str
    symbol: str
    magic_number: int
    direction: str  # BUY/SELL
    entry_price: float
    current_sl: float
    current_tp: float
    current_price: float
    profit_pips: float
    conversation_id: Optional[str] = None
    reevaluation_count: int = 0

@dataclass
class ReevaluationResult:
    """Resultado de una reevaluación"""
    success: bool
    action_taken: str  # MANTENER/ACTUALIZAR/CERRAR
    new_sl: Optional[float] = None
    new_tp: Optional[float] = None
    reasoning: str = ""
    tokens_used: int = 0
    cost: float = 0.0
    error_message: str = ""

class ReevaluationManager:
    """Gestiona el proceso completo de reevaluación"""
    
    def __init__(
        self,
        mt5_connector,
        data_extractor,
        prompt_builder,
        gemini_client,
        response_parser,
        position_manager,
        mode: ReevaluationMode = ReevaluationMode.PERSISTENT_CONVERSATION
    ):
        self.mt5_connector = mt5_connector
        self.data_extractor = data_extractor
        self.prompt_builder = prompt_builder
        self.gemini_client = gemini_client
        self.response_parser = response_parser
        self.position_manager = position_manager
        self.mode = mode
        self.conversation_sessions: Dict[str, str] = {}  # position_id -> conversation_id
    
    async def reevaluate_positions(
        self,
        bot_id: str,
        magic_number: int
    ) -> List[ReevaluationResult]:
        """Reevalúa todas las posiciones abiertas de un bot"""
        pass
    
    async def reevaluate_single_position(
        self,
        context: ReevaluationContext
    ) -> ReevaluationResult:
        """Reevalúa una posición específica"""
        pass
    
    def _get_or_create_conversation(self, position_id: str) -> Optional[str]:
        """Obtiene o crea conversación según modo configurado"""
        pass
    
    def _execute_action(
        self,
        context: ReevaluationContext,
        decision: ParsedDecision
    ) -> bool:
        """Ejecuta la acción decidida por la IA"""
        pass
```

---

## 🔄 Modos de Reevaluación: Conversación Persistente vs. Nueva

### Modo 1: Conversación Persistente (PERSISTENT_CONVERSATION)

**Características:**
- ✅ Mantiene el contexto conversacional de IA entre reevaluaciones
- ✅ La IA "recuerda" evaluaciones anteriores de la misma posición
- ✅ Potencialmente mejor continuidad en decisiones
- ❌ Posible acumulación de contexto y costos de tokens

**Uso:**
```python
manager = ReevaluationManager(
    ...,
    mode=ReevaluationMode.PERSISTENT_CONVERSATION
)
```

**Comportamiento:**
- Primera reevaluación → Crea nueva conversación, guarda ID
- Reevaluaciones subsecuentes → Usa mismo ID de conversación
- Al cerrar posición → Limpia conversación

---

### Modo 2: Nueva Conversación (NEW_CONVERSATION)

**Características:**
- ✅ Cada reevaluación es independiente
- ✅ Sin acumulación de contexto
- ✅ Menores costos de tokens
- ❌ Sin memoria de evaluaciones anteriores

**Uso:**
```python
manager = ReevaluationManager(
    ...,
    mode=ReevaluationMode.NEW_CONVERSATION
)
```

**Comportamiento:**
- Cada reevaluación → Nueva conversación desde cero
- Sin persistencia de conversación
- Más liviano en tokens

---

## 📊 Registro de Trazabilidad

### Tabla: reevaluations

```sql
CREATE TABLE reevaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Contexto de mercado
    symbol TEXT NOT NULL,
    current_price REAL NOT NULL,
    profit_pips REAL NOT NULL,
    
    -- Decisión de IA
    action TEXT NOT NULL,  -- MANTENER/ACTUALIZAR/CERRAR
    new_sl REAL,
    new_tp REAL,
    reasoning TEXT,
    
    -- Tracking de IA
    conversation_id TEXT,
    reevaluation_mode TEXT NOT NULL,  -- persistent/new
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost REAL,
    
    -- Métricas
    reevaluation_count INTEGER,
    time_since_last_reevaluation INTEGER,  -- segundos
    
    FOREIGN KEY (position_id) REFERENCES operations(id)
);

CREATE INDEX idx_reevaluations_position ON reevaluations(position_id);
CREATE INDEX idx_reevaluations_timestamp ON reevaluations(timestamp);
```

---

## 🎯 Casos de Uso

### Caso 1: Trailing Stop

```python
# Contexto: Operación BUY en profit +80 pips
context = ReevaluationContext(
    position_id="12345",
    symbol="EURUSD",
    direction="BUY",
    entry_price=1.2400,
    current_sl=1.2350,  # -50 pips
    current_tp=1.2550,  # +150 pips
    current_price=1.2480,  # +80 pips profit
    profit_pips=80.0
)

# IA decide: ACTUALIZAR con trailing stop
decision = {
    "accion": "ACTUALIZAR",
    "nuevo_stop_loss": 1.2420,  # Mover a breakeven + 20 pips
    "razonamiento": "Proteger profit. Trailing stop a +20 pips."
}

# Sistema ejecuta modificación de SL en MT5
```

---

### Caso 2: Extensión de TP

```python
# Contexto: Momentum fuerte, operación va muy bien
context = ReevaluationContext(
    position_id="12346",
    symbol="GBPUSD",
    direction="SELL",
    entry_price=1.3200,
    current_sl=1.3250,
    current_tp=1.3100,
    current_price=1.3130,  # +70 pips profit
    profit_pips=70.0
)

# IA decide: ACTUALIZAR TP extendido
decision = {
    "accion": "ACTUALIZAR",
    "nuevo_take_profit": 1.3050,  # Extender de 100 a 150 pips
    "razonamiento": "Momentum bajista fuerte. Extender objetivo."
}
```

---

### Caso 3: Cerrar por Reversión

```python
# Contexto: Señales de reversión detectadas
context = ReevaluationContext(
    position_id="12347",
    symbol="USDJPY",
    direction="BUY",
    entry_price=150.50,
    current_sl=150.00,
    current_tp=151.50,
    current_price=151.20,  # +70 pips profit
    profit_pips=70.0
)

# IA decide: CERRAR
decision = {
    "accion": "CERRAR",
    "razonamiento": "Divergencia bajista RSI. MACD cruce bajista. Mejor cerrar con profit actual."
}

# Sistema cierra posición en MT5
```

---

## 🧪 Tests Unitarios

### test_reevaluation_scheduler.py

```python
import pytest
from datetime import datetime, timedelta
from src.core.reevaluation_scheduler import ReevaluationScheduler, ReevaluationConfig

class TestReevaluationScheduler:
    
    def test_should_reevaluate_after_interval(self):
        """Debe reevaluar después de 10 minutos"""
        config = ReevaluationConfig(interval_minutes=10)
        scheduler = ReevaluationScheduler(config)
        
        position_id = "test_123"
        
        # Primera vez siempre debe reevaluar
        assert scheduler.should_reevaluate(position_id) is True
        
        # Marcar como reevaluada
        scheduler.mark_reevaluated(position_id)
        
        # Inmediatamente después, no debe reevaluar
        assert scheduler.should_reevaluate(position_id) is False
        
        # Simular paso de 10 minutos
        scheduler.last_reevaluation[position_id] -= timedelta(minutes=10, seconds=1)
        
        # Ahora sí debe reevaluar
        assert scheduler.should_reevaluate(position_id) is True
    
    def test_respects_trading_window(self):
        """Debe respetar ventana de trading (06:00-13:00)"""
        config = ReevaluationConfig(
            trading_window_start="06:00",
            trading_window_end="13:00"
        )
        scheduler = ReevaluationScheduler(config)
        
        # TODO: Test con diferentes horas
        pass
    
    def test_multiple_positions_independent(self):
        """Múltiples posiciones deben reevaluarse independientemente"""
        config = ReevaluationConfig(interval_minutes=10)
        scheduler = ReevaluationScheduler(config)
        
        pos1 = "pos_1"
        pos2 = "pos_2"
        
        # Reevaluar pos1
        scheduler.mark_reevaluated(pos1)
        
        # pos2 nunca fue reevaluada
        assert scheduler.should_reevaluate(pos2) is True
        assert scheduler.should_reevaluate(pos1) is False
```

### test_reevaluation_manager.py

```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.core.reevaluation_manager import (
    ReevaluationManager,
    ReevaluationMode,
    ReevaluationContext,
    ReevaluationResult
)

class TestReevaluationManager:
    
    @pytest.fixture
    def manager(self):
        """Manager con dependencias mockeadas"""
        return ReevaluationManager(
            mt5_connector=Mock(),
            data_extractor=Mock(),
            prompt_builder=Mock(),
            gemini_client=AsyncMock(),
            response_parser=Mock(),
            position_manager=Mock(),
            mode=ReevaluationMode.PERSISTENT_CONVERSATION
        )
    
    @pytest.mark.asyncio
    async def test_reevaluate_maintain_decision(self, manager):
        """Debe manejar decisión de MANTENER correctamente"""
        context = ReevaluationContext(
            position_id="test_1",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2450,
            profit_pips=50.0
        )
        
        # Mock de respuesta IA: MANTENER
        manager.response_parser.parse_reevaluation.return_value = Mock(
            is_valid=True,
            decision_type=Mock(value="MANTENER"),
            reasoning="Todo va bien"
        )
        
        result = await manager.reevaluate_single_position(context)
        
        assert result.success is True
        assert result.action_taken == "MANTENER"
        assert result.new_sl is None
        assert result.new_tp is None
    
    @pytest.mark.asyncio
    async def test_reevaluate_update_sl_decision(self, manager):
        """Debe ejecutar actualización de SL en MT5"""
        context = ReevaluationContext(
            position_id="test_2",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2480,
            profit_pips=80.0
        )
        
        # Mock de respuesta IA: ACTUALIZAR SL
        manager.response_parser.parse_reevaluation.return_value = Mock(
            is_valid=True,
            decision_type=Mock(value="ACTUALIZAR"),
            new_stop_loss=1.2420,
            new_take_profit=None,
            reasoning="Trailing stop a breakeven"
        )
        
        manager.position_manager.modify_position.return_value = True
        
        result = await manager.reevaluate_single_position(context)
        
        assert result.success is True
        assert result.action_taken == "ACTUALIZAR"
        assert result.new_sl == 1.2420
        assert result.new_tp is None
        
        # Verificar que se llamó a modify_position
        manager.position_manager.modify_position.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reevaluate_close_decision(self, manager):
        """Debe cerrar posición cuando IA decide CERRAR"""
        context = ReevaluationContext(
            position_id="test_3",
            symbol="EURUSD",
            magic_number=100101,
            direction="BUY",
            entry_price=1.2400,
            current_sl=1.2350,
            current_tp=1.2550,
            current_price=1.2480,
            profit_pips=80.0
        )
        
        # Mock de respuesta IA: CERRAR
        manager.response_parser.parse_reevaluation.return_value = Mock(
            is_valid=True,
            decision_type=Mock(value="CERRAR"),
            reasoning="Señales de reversión"
        )
        
        manager.position_manager.close_position.return_value = True
        
        result = await manager.reevaluate_single_position(context)
        
        assert result.success is True
        assert result.action_taken == "CERRAR"
        
        # Verificar que se llamó a close_position
        manager.position_manager.close_position.assert_called_once()
    
    def test_persistent_conversation_mode(self, manager):
        """Modo persistente debe reutilizar conversation_id"""
        position_id = "test_pos_1"
        
        # Primera llamada crea nueva conversación
        conv_id_1 = manager._get_or_create_conversation(position_id)
        assert conv_id_1 is not None
        
        # Segunda llamada reutiliza la misma
        conv_id_2 = manager._get_or_create_conversation(position_id)
        assert conv_id_1 == conv_id_2
    
    def test_new_conversation_mode(self):
        """Modo nuevo siempre crea nueva conversación"""
        manager = ReevaluationManager(
            mt5_connector=Mock(),
            data_extractor=Mock(),
            prompt_builder=Mock(),
            gemini_client=AsyncMock(),
            response_parser=Mock(),
            position_manager=Mock(),
            mode=ReevaluationMode.NEW_CONVERSATION
        )
        
        position_id = "test_pos_2"
        
        # Cada llamada debería retornar None (sin persistencia)
        conv_id_1 = manager._get_or_create_conversation(position_id)
        conv_id_2 = manager._get_or_create_conversation(position_id)
        
        assert conv_id_1 is None
        assert conv_id_2 is None
```

---

## 📈 Métricas de Reevaluación

### Métricas a Trackear

1. **Frecuencia:**
   - Número de reevaluaciones por posición
   - Tiempo promedio entre reevaluaciones
   - Reevaluaciones por día/bot

2. **Decisiones:**
   - % de MANTENER vs ACTUALIZAR vs CERRAR
   - Ratio de trailing stops ejecutados
   - Ratio de cierres anticipados

3. **Costos:**
   - Tokens consumidos por reevaluación
   - Costo promedio por reevaluación
   - Costo total por posición (apertura + N reevaluaciones)

4. **Efectividad:**
   - P/L promedio de posiciones con reevaluación vs sin reevaluación
   - Mejora en winrate por reevaluaciones
   - ROI considerando costos de reevaluación

---

## 🔧 Configuración

### config/reevaluation.json

```json
{
  "enabled": true,
  "interval_minutes": 10,
  "mode": "persistent",
  
  "trading_window": {
    "timezone": "America/Lima",
    "start": "06:00",
    "end": "13:00",
    "days": ["MON", "TUE", "WED", "THU", "FRI"]
  },
  
  "bots": {
    "bot_1": {
      "enabled": true,
      "mode": "persistent"
    },
    "bot_2": {
      "enabled": true,
      "mode": "new"
    },
    "bot_3": {
      "enabled": true,
      "mode": "persistent"
    }
  },
  
  "limits": {
    "max_reevaluations_per_position": 50,
    "max_cost_per_position_usd": 2.0
  }
}
```

---

## 🚀 Integración con Bot Principal

```python
from src.core.reevaluation_scheduler import ReevaluationScheduler, ReevaluationConfig
from src.core.reevaluation_manager import ReevaluationManager, ReevaluationMode

class BotOrchestrator:
    
    def __init__(self):
        # ... inicializar otros componentes
        
        # Configurar reevaluación
        reeval_config = ReevaluationConfig(
            interval_minutes=10,
            enabled=True
        )
        
        self.reeval_scheduler = ReevaluationScheduler(reeval_config)
        
        self.reeval_manager = ReevaluationManager(
            mt5_connector=self.mt5_connector,
            data_extractor=self.data_extractor,
            prompt_builder=self.prompt_builder,
            gemini_client=self.gemini_client,
            response_parser=self.response_parser,
            position_manager=self.position_manager,
            mode=ReevaluationMode.PERSISTENT_CONVERSATION
        )
    
    async def start(self):
        """Inicia bot principal y scheduler de reevaluación"""
        
        # Callback para reevaluaciones
        async def reevaluate_callback():
            results = await self.reeval_manager.reevaluate_positions(
                bot_id=self.bot_id,
                magic_number=self.magic_number
            )
            
            for result in results:
                self.logger.info(
                    f"Reevaluación: {result.action_taken} - {result.reasoning}"
                )
        
        # Iniciar scheduler
        await self.reeval_scheduler.start(reevaluate_callback)
        
        # Ciclo principal del bot
        while self.is_running:
            await self.execute_main_cycle()
            await asyncio.sleep(3600)  # Cada hora
```

---

## 📊 Comparación de Modos

### Experimento Sugerido

**Hipótesis:** El modo persistente mejorará la continuidad de decisiones pero aumentará costos.

**Metodología:**
1. Bot 1 → Modo PERSISTENT_CONVERSATION
2. Bot 2 → Modo NEW_CONVERSATION
3. Mismo activo, mismas condiciones, mismo periodo
4. Comparar:
   - Winrate
   - Profit Factor
   - Costo total de IA
   - ROI neto (profit - costos)

**Duración:** 30 días en demo

---

## 📝 Checklist de Implementación

- [ ] Implementar `ReevaluationScheduler`
- [ ] Implementar `ReevaluationManager`
- [ ] Crear tabla `reevaluations` en SQLite
- [ ] Implementar persistencia de conversaciones (modo persistent)
- [ ] Implementar modo new conversation
- [ ] Tests unitarios (100% cobertura)
- [ ] Tests de integración
- [ ] Documentar en `examples/reevaluation_example.py`
- [ ] Actualizar configuración en `config/reevaluation.example.json`
- [ ] Validar con datos reales en demo
- [ ] Medir métricas de efectividad y costos

---

## 🔗 Tickets Relacionados

- **T4:** Verificación de operación abierta (pre-requisito)
- **T10:** PromptBuilder y GeminiClient (usa para reevaluación)
- **T12:** Mantenimiento de contexto conversacional
- **T27:** Aplicación de decisiones de actualizar/cerrar
- **T28:** Registro de trazabilidad

---

## 📚 Referencias

- Documentación PromptBuilder: `T10_ia_prompt_builder.md`
- Formato de respuestas IA: `FORMATO_RESPUESTAS_IA.md`
- Parser de respuestas: `src/core/ai_response_parser.py`

---

**Fecha de Creación:** 2025-11-13  
**Autor:** GitHub Copilot  
**Estado:** En Desarrollo
