"""
Tests para BotInstance - T03: Instancias independientes por bot

Este módulo prueba que cada bot pueda ejecutarse como instancia independiente,
con su propia configuración, estado, y lifecycle management.

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T03 - Instancias independientes por bot
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import logging
from datetime import datetime

from src.core.bot_instance import (
    BotInstance,
    BotConfig,
    BotState,
    BotStatus,
    BotInstanceError,
    BotConfigurationError,
    BotStateError
)


# ==================== FIXTURES ====================

@pytest.fixture
def bot_config_dict():
    """Configuración básica de bot en formato dict"""
    return {
        "bot_id": 1,
        "bot_name": "TestBot1",
        "enabled": True,
        "schedule_config": {
            "trading_schedule": {
                "timezone": "America/Lima",
                "trading_hours": {
                    "start_time": "06:00",
                    "end_time": "13:00",
                    "ia_response_buffer_minutes": 3
                },
                "business_days": {
                    "enabled": [1, 2, 3, 4, 5]
                },
                "holidays": {
                    "enabled": True,
                    "dates": []
                }
            }
        },
        "mt5_config": {
            "account_id": "12345678",
            "password": "test_password",
            "server": "Pepperstone-Demo",
            "timeout": 60
        },
        "cycle_config": {
            "enabled": True,
            "start_delay_seconds": 3,
            "check_interval_seconds": 60,
            "max_wait_hours": 8
        }
    }


@pytest.fixture
def bot_config(bot_config_dict):
    """BotConfig instance"""
    return BotConfig.from_dict(bot_config_dict)


@pytest.fixture
def mock_time_validator():
    """Mock de TimeValidator"""
    with patch('src.core.bot_instance.TimeValidator') as mock:
        instance = Mock()
        instance.is_trading_time.return_value = Mock(is_valid=True, reason="Valid")
        mock.return_value = instance
        yield mock


@pytest.fixture
def mock_cycle_scheduler():
    """Mock de CycleScheduler"""
    with patch('src.core.bot_instance.CycleScheduler') as mock:
        instance = Mock()
        mock.return_value = instance
        yield mock


@pytest.fixture
def mock_mt5_module():
    """Mock del módulo MetaTrader5"""
    with patch('src.core.mt5_connector.mt5') as mock:
        # Simular que el módulo está disponible
        mock_module = Mock()
        mock.initialize.return_value = True
        mock.login.return_value = True
        mock.terminal_info.return_value = Mock(connected=True, trade_allowed=True)
        mock.shutdown.return_value = None
        yield mock

@pytest.fixture
def mock_mt5_connector(mock_mt5_module):
    """Mock de MT5Connector"""
    with patch('src.core.bot_instance.MT5Connector') as mock:
        instance = Mock()
        instance.is_connected.return_value = False
        instance.verify_connection.return_value = True
        instance.disconnect.return_value = None
        mock.return_value = instance
        yield mock


@pytest.fixture
def mock_logger():
    """Mock de Logger"""
    return Mock(spec=logging.Logger)


@pytest.fixture
def bot_instance(bot_config, mock_time_validator, mock_cycle_scheduler, mock_mt5_connector, mock_logger, mock_mt5_module):
    """Instancia de BotInstance con mocks"""
    return BotInstance(bot_config, logger=mock_logger)


# ==================== TESTS DE BOTCONFIG ====================

class TestBotConfig:
    """Tests para la clase BotConfig"""
    
    def test_bot_config_from_dict_success(self, bot_config_dict):
        """Test: Crear BotConfig desde diccionario válido"""
        config = BotConfig.from_dict(bot_config_dict)
        
        assert config.bot_id == 1
        assert config.bot_name == "TestBot1"
        assert config.enabled is True
        assert config.schedule_config is not None
        assert config.mt5_config is not None
        assert config.cycle_config is not None
    
    def test_bot_config_missing_bot_id(self, bot_config_dict):
        """Test: BotConfig falla sin bot_id"""
        del bot_config_dict["bot_id"]
        
        with pytest.raises(BotConfigurationError, match="bot_id es requerido"):
            BotConfig.from_dict(bot_config_dict)
    
    def test_bot_config_invalid_bot_id(self, bot_config_dict):
        """Test: BotConfig falla con bot_id inválido"""
        bot_config_dict["bot_id"] = 10  # Fuera del rango 1-5
        
        with pytest.raises(BotConfigurationError, match="bot_id debe estar entre 1 y 5"):
            BotConfig.from_dict(bot_config_dict)
    
    def test_bot_config_missing_bot_name(self, bot_config_dict):
        """Test: BotConfig falla sin bot_name"""
        del bot_config_dict["bot_name"]
        
        with pytest.raises(BotConfigurationError, match="bot_name es requerido"):
            BotConfig.from_dict(bot_config_dict)
    
    def test_bot_config_default_enabled_true(self, bot_config_dict):
        """Test: enabled es True por defecto"""
        del bot_config_dict["enabled"]
        config = BotConfig.from_dict(bot_config_dict)
        
        assert config.enabled is True
    
    def test_bot_config_different_bot_ids(self):
        """Test: Múltiples configs con diferentes bot_ids"""
        config1 = BotConfig(bot_id=1, bot_name="Bot1", enabled=True, 
                           schedule_config={}, mt5_config={}, cycle_config={})
        config2 = BotConfig(bot_id=2, bot_name="Bot2", enabled=True,
                           schedule_config={}, mt5_config={}, cycle_config={})
        
        assert config1.bot_id != config2.bot_id
        assert config1.bot_name != config2.bot_name


# ==================== TESTS DE BOTSTATE ====================

class TestBotState:
    """Tests para la clase BotState"""
    
    def test_bot_state_initialization(self):
        """Test: BotState se inicializa correctamente"""
        state = BotState(bot_id=1)
        
        assert state.bot_id == 1
        assert state.status == BotStatus.STOPPED
        assert state.started_at is None
        assert state.stopped_at is None
        assert state.cycles_completed == 0
        assert state.last_cycle_at is None
        assert state.error_count == 0
        assert state.last_error is None
    
    def test_bot_state_transition_to_running(self):
        """Test: Transición de estado a RUNNING"""
        state = BotState(bot_id=1)
        state.transition_to(BotStatus.RUNNING)
        
        assert state.status == BotStatus.RUNNING
        assert state.started_at is not None
        assert isinstance(state.started_at, datetime)
    
    def test_bot_state_transition_to_stopped(self):
        """Test: Transición de estado a STOPPED"""
        state = BotState(bot_id=1)
        state.transition_to(BotStatus.RUNNING)
        state.transition_to(BotStatus.STOPPED)
        
        assert state.status == BotStatus.STOPPED
        assert state.stopped_at is not None
    
    def test_bot_state_transition_to_error(self):
        """Test: Transición de estado a ERROR"""
        state = BotState(bot_id=1)
        state.transition_to(BotStatus.ERROR, error_message="Test error")
        
        assert state.status == BotStatus.ERROR
        assert state.last_error == "Test error"
        assert state.error_count == 1
    
    def test_bot_state_increment_cycle(self):
        """Test: Incrementar contador de ciclos"""
        state = BotState(bot_id=1)
        
        state.increment_cycle()
        assert state.cycles_completed == 1
        assert state.last_cycle_at is not None
        
        state.increment_cycle()
        assert state.cycles_completed == 2
    
    def test_bot_state_to_dict(self):
        """Test: Convertir estado a diccionario"""
        state = BotState(bot_id=1)
        state.transition_to(BotStatus.RUNNING)
        state.increment_cycle()
        
        state_dict = state.to_dict()
        
        assert state_dict["bot_id"] == 1
        assert state_dict["status"] == "RUNNING"
        assert state_dict["cycles_completed"] == 1
        assert "started_at" in state_dict


# ==================== TESTS DE BOTINSTANCE ====================

class TestBotInstance:
    """Tests para la clase BotInstance"""
    
    def test_bot_instance_initialization(self, bot_config, mock_logger, mock_mt5_module):
        """Test: BotInstance se inicializa correctamente"""
        with patch('src.core.bot_instance.TimeValidator'), \
             patch('src.core.bot_instance.CycleScheduler'), \
             patch('src.core.bot_instance.MT5Connector'):
            bot = BotInstance(bot_config, logger=mock_logger)
            
            assert bot.config == bot_config
            assert bot.bot_id == 1
            assert bot.bot_name == "TestBot1"
            assert bot.state.status == BotStatus.STOPPED
            assert bot.logger == mock_logger
    
    def test_bot_instance_creates_default_logger(self, bot_config, mock_mt5_module):
        """Test: BotInstance crea logger por defecto si no se proporciona"""
        with patch('src.core.bot_instance.TimeValidator'), \
             patch('src.core.bot_instance.CycleScheduler'), \
             patch('src.core.bot_instance.MT5Connector'):
            bot = BotInstance(bot_config)
            
            assert bot.logger is not None
            assert isinstance(bot.logger, logging.Logger)
            assert "BotInstance.TestBot1" in bot.logger.name
    
    def test_bot_instance_initializes_components(self, bot_config, mock_time_validator, 
                                                 mock_cycle_scheduler, mock_mt5_connector):
        """Test: BotInstance inicializa todos los componentes"""
        bot = BotInstance(bot_config)
        
        # Verificar que se crearon los componentes
        assert bot.time_validator is not None
        assert bot.cycle_scheduler is not None
        assert bot.mt5_connector is not None
    
    def test_bot_instance_disabled_by_config(self, bot_config_dict, mock_logger, mock_mt5_module):
        """Test: BotInstance respeta configuración enabled=False"""
        bot_config_dict["enabled"] = False
        config = BotConfig.from_dict(bot_config_dict)
        
        with patch('src.core.bot_instance.TimeValidator'), \
             patch('src.core.bot_instance.CycleScheduler'), \
             patch('src.core.bot_instance.MT5Connector'):
            bot = BotInstance(config, logger=mock_logger)
            
            assert bot.config.enabled is False
            
            # Intentar start no debe funcionar si está disabled
            result = bot.start()
            assert result is False
            assert bot.state.status == BotStatus.STOPPED
    
    def test_bot_instance_start_success(self, bot_instance, mock_mt5_connector):
        """Test: Start inicia el bot correctamente"""
        mock_mt5_connector.return_value.verify_connection.return_value = True
        
        result = bot_instance.start()
        
        assert result is True
        assert bot_instance.state.status == BotStatus.RUNNING
        assert bot_instance.state.started_at is not None
    
    def test_bot_instance_start_fails_if_already_running(self, bot_instance):
        """Test: Start falla si el bot ya está corriendo"""
        bot_instance.state.transition_to(BotStatus.RUNNING)
        
        result = bot_instance.start()
        
        assert result is False
    
    def test_bot_instance_start_fails_if_mt5_connection_fails(self, bot_instance, mock_mt5_connector):
        """Test: Start falla si no se puede conectar a MT5"""
        mock_mt5_connector.return_value.verify_connection.return_value = False
        
        result = bot_instance.start()
        
        assert result is False
        assert bot_instance.state.status == BotStatus.ERROR
    
    def test_bot_instance_stop_success(self, bot_instance):
        """Test: Stop detiene el bot correctamente"""
        bot_instance.state.transition_to(BotStatus.RUNNING)
        
        result = bot_instance.stop()
        
        assert result is True
        assert bot_instance.state.status == BotStatus.STOPPED
        assert bot_instance.state.stopped_at is not None
    
    def test_bot_instance_stop_fails_if_not_running(self, bot_instance):
        """Test: Stop falla si el bot no está corriendo"""
        result = bot_instance.stop()
        
        assert result is False
    
    def test_bot_instance_is_running(self, bot_instance):
        """Test: is_running retorna el estado correcto"""
        assert bot_instance.is_running() is False
        
        bot_instance.state.transition_to(BotStatus.RUNNING)
        assert bot_instance.is_running() is True
        
        bot_instance.state.transition_to(BotStatus.STOPPED)
        assert bot_instance.is_running() is False
    
    def test_bot_instance_get_status(self, bot_instance):
        """Test: get_status retorna información completa"""
        status = bot_instance.get_status()
        
        assert status["bot_id"] == 1
        assert status["bot_name"] == "TestBot1"
        assert status["status"] == "STOPPED"
        assert status["enabled"] is True
        assert "cycles_completed" in status
        assert "started_at" in status
    
    def test_bot_instance_execute_cycle_success(self, bot_instance):
        """Test: execute_cycle ejecuta un ciclo exitosamente"""
        bot_instance.state.transition_to(BotStatus.RUNNING)
        
        # Mock del callback de ciclo
        cycle_callback = Mock()
        
        bot_instance.execute_cycle(cycle_callback)
        
        # Verificar que se ejecutó el callback
        cycle_callback.assert_called_once()
        assert bot_instance.state.cycles_completed == 1
    
    def test_bot_instance_execute_cycle_fails_if_not_running(self, bot_instance):
        """Test: execute_cycle falla si el bot no está corriendo"""
        cycle_callback = Mock()
        
        with pytest.raises(BotStateError, match="Bot debe estar en estado RUNNING"):
            bot_instance.execute_cycle(cycle_callback)
        
        cycle_callback.assert_not_called()
    
    def test_bot_instance_execute_cycle_handles_exception(self, bot_instance):
        """Test: execute_cycle maneja excepciones del callback"""
        bot_instance.state.transition_to(BotStatus.RUNNING)
        
        cycle_callback = Mock(side_effect=Exception("Test error"))
        
        with pytest.raises(Exception, match="Test error"):
            bot_instance.execute_cycle(cycle_callback)
        
        # El estado debe cambiar a ERROR
        assert bot_instance.state.status == BotStatus.ERROR
        assert bot_instance.state.error_count == 1
    
    def test_multiple_bot_instances_are_independent(self, bot_config_dict, mock_logger, mock_mt5_module):
        """Test: Múltiples instancias de bot son independientes"""
        # Crear config para bot 1
        config1_dict = bot_config_dict.copy()
        config1_dict["bot_id"] = 1
        config1_dict["bot_name"] = "Bot1"
        config1 = BotConfig.from_dict(config1_dict)
        
        # Crear config para bot 2
        config2_dict = bot_config_dict.copy()
        config2_dict["bot_id"] = 2
        config2_dict["bot_name"] = "Bot2"
        config2 = BotConfig.from_dict(config2_dict)
        
        # Crear instancias
        with patch('src.core.bot_instance.TimeValidator'), \
             patch('src.core.bot_instance.CycleScheduler'), \
             patch('src.core.bot_instance.MT5Connector'):
            bot1 = BotInstance(config1, logger=mock_logger)
            bot2 = BotInstance(config2, logger=mock_logger)
            
            # Verificar independencia
            assert bot1.bot_id != bot2.bot_id
            assert bot1.bot_name != bot2.bot_name
            assert bot1.state is not bot2.state
            
            # Modificar estado de bot1 no debe afectar bot2
            bot1.state.transition_to(BotStatus.RUNNING)
            
            assert bot1.is_running() is True
            assert bot2.is_running() is False
    
    def test_bot_instance_restart(self, bot_instance):
        """Test: Reiniciar un bot (stop + start)"""
        # Start
        bot_instance.start()
        assert bot_instance.is_running() is True
        cycles_before = bot_instance.state.cycles_completed
        
        # Stop
        bot_instance.stop()
        assert bot_instance.is_running() is False
        
        # Start again
        bot_instance.start()
        assert bot_instance.is_running() is True
        
        # Los ciclos completados se mantienen
        assert bot_instance.state.cycles_completed == cycles_before


# ==================== TESTS DE INTEGRACIÓN ====================

class TestBotInstanceIntegration:
    """Tests de integración para BotInstance"""
    
    def test_bot_instance_full_lifecycle(self, bot_config, mock_mt5_module):
        """Test: Ciclo de vida completo de un bot"""
        with patch('src.core.bot_instance.TimeValidator'), \
             patch('src.core.bot_instance.CycleScheduler'), \
             patch('src.core.bot_instance.MT5Connector') as MockConnector:
            # Configurar mock del connector
            mock_connector_instance = Mock()
            mock_connector_instance.verify_connection.return_value = True
            mock_connector_instance.disconnect.return_value = None
            MockConnector.return_value = mock_connector_instance
            
            bot = BotInstance(bot_config)
            
            # 1. Estado inicial
            assert bot.is_running() is False
            assert bot.state.status == BotStatus.STOPPED
            
            # 2. Start
            bot.start()
            
            assert bot.is_running() is True
            assert bot.state.status == BotStatus.RUNNING
            
            # 3. Ejecutar ciclos
            cycle_callback = Mock()
            bot.execute_cycle(cycle_callback)
            bot.execute_cycle(cycle_callback)
            
            assert bot.state.cycles_completed == 2
            
            # 4. Stop
            bot.stop()
            
            assert bot.is_running() is False
            assert bot.state.status == BotStatus.STOPPED
            assert bot.state.stopped_at is not None
    
    def test_bot_instance_error_recovery(self, bot_config, mock_mt5_module):
        """Test: Recuperación de errores"""
        with patch('src.core.bot_instance.TimeValidator'), \
             patch('src.core.bot_instance.CycleScheduler'), \
             patch('src.core.bot_instance.MT5Connector') as MockConnector:
            # Configurar mock del connector
            mock_connector_instance = Mock()
            mock_connector_instance.verify_connection.return_value = True
            mock_connector_instance.disconnect.return_value = None
            MockConnector.return_value = mock_connector_instance
            
            bot = BotInstance(bot_config)
            
            # Start
            bot.start()
            
            # Simular error en ciclo
            cycle_callback = Mock(side_effect=Exception("Simulated error"))
            
            with pytest.raises(Exception):
                bot.execute_cycle(cycle_callback)
            
            assert bot.state.status == BotStatus.ERROR
            assert bot.state.error_count == 1
            
            # Stop y restart para recuperar
            bot.stop()
            
            bot.start()
            
            # Ahora debería funcionar
            cycle_callback_ok = Mock()
            bot.execute_cycle(cycle_callback_ok)
            
            assert bot.state.status == BotStatus.RUNNING
            assert bot.state.cycles_completed == 1
