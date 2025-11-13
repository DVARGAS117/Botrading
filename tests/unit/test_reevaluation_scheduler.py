"""
Tests unitarios para ReevaluationScheduler (T26)

Este módulo contiene tests para el scheduler de reevaluaciones periódicas.
"""

import pytest
from datetime import datetime, timedelta, time
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from src.core.reevaluation_scheduler import (
    ReevaluationScheduler,
    ReevaluationConfig,
    ReevaluationSchedulerError
)


class TestReevaluationConfig:
    """Tests para configuración del scheduler"""
    
    def test_default_config(self):
        """Debe crear configuración con valores por defecto"""
        config = ReevaluationConfig()
        
        assert config.interval_minutes == 10
        assert config.enabled is True
        assert config.timezone == "America/Lima"
        assert config.trading_window_start == "06:00"
        assert config.trading_window_end == "13:00"
    
    def test_custom_config(self):
        """Debe permitir configuración personalizada"""
        config = ReevaluationConfig(
            interval_minutes=5,
            enabled=False,
            timezone="America/New_York"
        )
        
        assert config.interval_minutes == 5
        assert config.enabled is False
        assert config.timezone == "America/New_York"
    
    def test_validate_interval_positive(self):
        """Intervalo debe ser positivo"""
        with pytest.raises(ValueError, match="interval_minutes debe ser positivo"):
            ReevaluationConfig(interval_minutes=0)
        
        with pytest.raises(ValueError, match="interval_minutes debe ser positivo"):
            ReevaluationConfig(interval_minutes=-5)
    
    def test_validate_interval_reasonable(self):
        """Intervalo debe ser razonable (max 60 min)"""
        with pytest.raises(ValueError, match="interval_minutes no puede exceder 60"):
            ReevaluationConfig(interval_minutes=61)
        
        # Exactamente 60 debe ser válido
        config = ReevaluationConfig(interval_minutes=60)
        assert config.interval_minutes == 60
    
    def test_to_dict(self):
        """Debe convertir a diccionario correctamente"""
        config = ReevaluationConfig(interval_minutes=15)
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['interval_minutes'] == 15
        assert config_dict['enabled'] is True


class TestReevaluationScheduler:
    """Tests para el scheduler de reevaluaciones"""
    
    @pytest.fixture
    def config(self):
        """Configuración de prueba"""
        return ReevaluationConfig(
            interval_minutes=10,
            enabled=True,
            timezone="America/Lima",
            trading_window_start="06:00",
            trading_window_end="13:00"
        )
    
    @pytest.fixture
    def scheduler(self, config):
        """Scheduler de prueba"""
        return ReevaluationScheduler(config)
    
    def test_init(self, scheduler, config):
        """Debe inicializar correctamente"""
        assert scheduler.config == config
        assert scheduler.last_reevaluation == {}
        assert scheduler.is_running is False
    
    def test_should_reevaluate_first_time(self, scheduler):
        """Primera vez siempre debe reevaluar"""
        position_id = "test_pos_1"
        
        # Mock para estar dentro de ventana de trading
        with patch.object(scheduler, 'is_within_trading_window', return_value=True):
            # Primera vez debe retornar True
            assert scheduler.should_reevaluate(position_id) is True
    
    def test_should_reevaluate_after_mark(self, scheduler):
        """No debe reevaluar inmediatamente después de marcar"""
        position_id = "test_pos_2"
        
        with patch.object(scheduler, 'is_within_trading_window', return_value=True):
            # Primera vez
            assert scheduler.should_reevaluate(position_id) is True
            
            # Marcar como reevaluada
            scheduler.mark_reevaluated(position_id)
            
            # Inmediatamente después, no debe reevaluar
            assert scheduler.should_reevaluate(position_id) is False
    
    def test_should_reevaluate_after_interval(self, scheduler):
        """Debe reevaluar después del intervalo configurado"""
        position_id = "test_pos_3"
        
        with patch.object(scheduler, 'is_within_trading_window', return_value=True):
            # Marcar como reevaluada
            scheduler.mark_reevaluated(position_id)
            
            # Inmediatamente después, no
            assert scheduler.should_reevaluate(position_id) is False
            
            # Simular paso del intervalo (10 minutos + 1 segundo)
            past_time = datetime.now() - timedelta(minutes=10, seconds=1)
            scheduler.last_reevaluation[position_id] = past_time
            
            # Ahora sí debe reevaluar
            assert scheduler.should_reevaluate(position_id) is True
    
    def test_should_reevaluate_just_before_interval(self, scheduler):
        """No debe reevaluar justo antes de cumplir el intervalo"""
        position_id = "test_pos_4"
        
        # Marcar como reevaluada
        scheduler.mark_reevaluated(position_id)
        
        # Simular paso de casi 10 minutos (9 min 59 seg)
        past_time = datetime.now() - timedelta(minutes=9, seconds=59)
        scheduler.last_reevaluation[position_id] = past_time
        
        # Aún no debe reevaluar
        assert scheduler.should_reevaluate(position_id) is False
    
    def test_multiple_positions_independent(self, scheduler):
        """Múltiples posiciones deben ser independientes"""
        pos1 = "pos_1"
        pos2 = "pos_2"
        pos3 = "pos_3"
        
        with patch.object(scheduler, 'is_within_trading_window', return_value=True):
            # Marcar solo pos1 como reevaluada
            scheduler.mark_reevaluated(pos1)
            
            # pos1 no debe reevaluar, pos2 y pos3 sí
            assert scheduler.should_reevaluate(pos1) is False
            assert scheduler.should_reevaluate(pos2) is True
            assert scheduler.should_reevaluate(pos3) is True
            
            # Marcar pos2
            scheduler.mark_reevaluated(pos2)
            
            # Ahora pos2 no, pero pos3 sí
            assert scheduler.should_reevaluate(pos2) is False
            assert scheduler.should_reevaluate(pos3) is True
    
    def test_mark_reevaluated(self, scheduler):
        """Debe registrar timestamp al marcar reevaluada"""
        position_id = "test_pos_5"
        
        before = datetime.now()
        scheduler.mark_reevaluated(position_id)
        after = datetime.now()
        
        # Debe existir en el diccionario
        assert position_id in scheduler.last_reevaluation
        
        # El timestamp debe estar entre before y after
        timestamp = scheduler.last_reevaluation[position_id]
        assert before <= timestamp <= after
    
    def test_get_last_reevaluation_existing(self, scheduler):
        """Debe retornar timestamp de última reevaluación"""
        position_id = "test_pos_6"
        
        scheduler.mark_reevaluated(position_id)
        
        last = scheduler.get_last_reevaluation(position_id)
        assert last is not None
        assert isinstance(last, datetime)
    
    def test_get_last_reevaluation_nonexisting(self, scheduler):
        """Debe retornar None si posición nunca fue reevaluada"""
        position_id = "never_reevaluated"
        
        last = scheduler.get_last_reevaluation(position_id)
        assert last is None
    
    def test_get_time_since_last_reevaluation(self, scheduler):
        """Debe calcular tiempo transcurrido correctamente"""
        position_id = "test_pos_7"
        
        # Posición nueva
        elapsed = scheduler.get_time_since_last_reevaluation(position_id)
        assert elapsed is None
        
        # Marcar y esperar un poco
        scheduler.mark_reevaluated(position_id)
        
        # Simular 5 minutos atrás
        past_time = datetime.now() - timedelta(minutes=5)
        scheduler.last_reevaluation[position_id] = past_time
        
        elapsed = scheduler.get_time_since_last_reevaluation(position_id)
        assert elapsed is not None
        assert 290 <= elapsed.total_seconds() <= 310  # ~5 minutos ± margen
    
    def test_is_within_trading_window_valid_time(self, scheduler):
        """Debe detectar correctamente hora dentro de ventana"""
        # Mock de datetime para controlar hora actual
        with patch('src.core.reevaluation_scheduler.datetime') as mock_dt:
            # Simular las 10:00 AM (dentro de 06:00-13:00)
            mock_dt.now.return_value = datetime(2025, 11, 13, 10, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            # Mock de día laborable (miércoles)
            with patch.object(scheduler, '_is_trading_day', return_value=True):
                assert scheduler.is_within_trading_window() is True
    
    def test_is_within_trading_window_before_start(self, scheduler):
        """Debe rechazar hora antes de ventana de trading"""
        with patch('src.core.reevaluation_scheduler.datetime') as mock_dt:
            # Simular las 05:00 AM (antes de 06:00)
            mock_dt.now.return_value = datetime(2025, 11, 13, 5, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch.object(scheduler, '_is_trading_day', return_value=True):
                assert scheduler.is_within_trading_window() is False
    
    def test_is_within_trading_window_after_end(self, scheduler):
        """Debe rechazar hora después de ventana de trading"""
        with patch('src.core.reevaluation_scheduler.datetime') as mock_dt:
            # Simular las 14:00 (después de 13:00)
            mock_dt.now.return_value = datetime(2025, 11, 13, 14, 0, 0)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            with patch.object(scheduler, '_is_trading_day', return_value=True):
                assert scheduler.is_within_trading_window() is False
    
    def test_is_within_trading_window_weekend(self, scheduler):
        """Debe rechazar fin de semana"""
        with patch('src.core.reevaluation_scheduler.datetime') as mock_dt:
            # Simular sábado 10:00 AM
            mock_dt.now.return_value = datetime(2025, 11, 15, 10, 0, 0)  # Sábado
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            assert scheduler.is_within_trading_window() is False
    
    def test_reset_position(self, scheduler):
        """Debe limpiar registro de posición"""
        position_id = "test_pos_8"
        
        with patch.object(scheduler, 'is_within_trading_window', return_value=True):
            # Marcar posición
            scheduler.mark_reevaluated(position_id)
            assert position_id in scheduler.last_reevaluation
            
            # Reset
            scheduler.reset_position(position_id)
            assert position_id not in scheduler.last_reevaluation
            
            # Ahora debe reevaluar de nuevo (como primera vez)
            assert scheduler.should_reevaluate(position_id) is True
    
    def test_reset_all(self, scheduler):
        """Debe limpiar todas las posiciones"""
        pos1 = "pos_1"
        pos2 = "pos_2"
        pos3 = "pos_3"
        
        with patch.object(scheduler, 'is_within_trading_window', return_value=True):
            # Marcar varias posiciones
            scheduler.mark_reevaluated(pos1)
            scheduler.mark_reevaluated(pos2)
            scheduler.mark_reevaluated(pos3)
            
            assert len(scheduler.last_reevaluation) == 3
            
            # Reset all
            scheduler.reset_all()
            
            assert len(scheduler.last_reevaluation) == 0
            assert scheduler.should_reevaluate(pos1) is True
            assert scheduler.should_reevaluate(pos2) is True
    
    def test_disabled_scheduler(self):
        """Scheduler deshabilitado nunca debe reevaluar"""
        config = ReevaluationConfig(enabled=False)
        scheduler = ReevaluationScheduler(config)
        
        position_id = "test_pos"
        
        # Siempre debe retornar False si está deshabilitado
        assert scheduler.should_reevaluate(position_id) is False
        
        # Incluso después de marcar
        scheduler.mark_reevaluated(position_id)
        assert scheduler.should_reevaluate(position_id) is False
    
    @pytest.mark.asyncio
    async def test_start_stop_scheduler(self, scheduler):
        """Debe iniciar y detener scheduler correctamente"""
        callback_called = False
        
        async def test_callback():
            nonlocal callback_called
            callback_called = True
        
        # Iniciar scheduler en background
        task = asyncio.create_task(scheduler.start(test_callback))
        
        # Esperar un poco
        await asyncio.sleep(0.1)
        
        # Debe estar running
        assert scheduler.is_running is True
        
        # Detener
        scheduler.stop()
        
        # Esperar a que termine
        await asyncio.sleep(0.1)
        
        # Debe estar stopped
        assert scheduler.is_running is False
        
        # Cancelar task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    def test_get_stats(self, scheduler):
        """Debe retornar estadísticas del scheduler"""
        pos1 = "pos_1"
        pos2 = "pos_2"
        
        # Inicialmente vacío
        stats = scheduler.get_stats()
        assert stats['total_positions'] == 0
        assert stats['enabled'] is True
        
        # Marcar posiciones
        scheduler.mark_reevaluated(pos1)
        scheduler.mark_reevaluated(pos2)
        
        stats = scheduler.get_stats()
        assert stats['total_positions'] == 2
        assert stats['interval_minutes'] == 10


class TestReevaluationSchedulerEdgeCases:
    """Tests de casos extremos"""
    
    def test_rapid_successive_calls(self):
        """Debe manejar llamadas rápidas sucesivas"""
        config = ReevaluationConfig(interval_minutes=10)
        scheduler = ReevaluationScheduler(config)
        
        position_id = "rapid_test"
        
        with patch.object(scheduler, 'is_within_trading_window', return_value=True):
            # Primera llamada
            assert scheduler.should_reevaluate(position_id) is True
            scheduler.mark_reevaluated(position_id)
            
            # 100 llamadas sucesivas deben retornar False
            for _ in range(100):
                assert scheduler.should_reevaluate(position_id) is False
    
    def test_concurrent_positions(self):
        """Debe manejar muchas posiciones concurrentes"""
        config = ReevaluationConfig(interval_minutes=10)
        scheduler = ReevaluationScheduler(config)
        
        # Crear 1000 posiciones
        positions = [f"pos_{i}" for i in range(1000)]
        
        # Marcar todas
        for pos in positions:
            scheduler.mark_reevaluated(pos)
        
        # Todas deben estar registradas
        assert len(scheduler.last_reevaluation) == 1000
        
        # Ninguna debe reevaluar inmediatamente
        for pos in positions:
            assert scheduler.should_reevaluate(pos) is False
    
    def test_very_short_interval(self):
        """Debe funcionar con intervalos muy cortos (1 min)"""
        config = ReevaluationConfig(interval_minutes=1)
        scheduler = ReevaluationScheduler(config)
        
        position_id = "short_interval"
        
        with patch.object(scheduler, 'is_within_trading_window', return_value=True):
            scheduler.mark_reevaluated(position_id)
            
            # Simular paso de 1 minuto
            past_time = datetime.now() - timedelta(minutes=1, seconds=1)
            scheduler.last_reevaluation[position_id] = past_time
            
            assert scheduler.should_reevaluate(position_id) is True
    
    def test_very_long_interval(self):
        """Debe funcionar con intervalos largos (60 min)"""
        config = ReevaluationConfig(interval_minutes=60)
        scheduler = ReevaluationScheduler(config)
        
        position_id = "long_interval"
        
        with patch.object(scheduler, 'is_within_trading_window', return_value=True):
            scheduler.mark_reevaluated(position_id)
            
            # 59 minutos: no debe reevaluar
            past_time = datetime.now() - timedelta(minutes=59)
            scheduler.last_reevaluation[position_id] = past_time
            assert scheduler.should_reevaluate(position_id) is False
            
            # 60 minutos: sí debe reevaluar
            past_time = datetime.now() - timedelta(minutes=60, seconds=1)
            scheduler.last_reevaluation[position_id] = past_time
            assert scheduler.should_reevaluate(position_id) is True
