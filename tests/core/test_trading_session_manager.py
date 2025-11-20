"""
Tests para TradingSessionManager - Gestión de horarios de trading por símbolo

Autor: Sistema Botrading
Fecha: 2025-11-19
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import time, datetime
from src.core.trading_session_manager import TradingSessionManager


@pytest.fixture
def sample_sessions_config():
    """Configuración de sesiones de ejemplo para tests."""
    return {
        "sessions": {
            "londres": {
                "start": "02:00",
                "end": "05:00",
                "symbols": ["EURUSD", "GBPUSD", "EURGBP"],
                "strategies": ["A_tendencia"],
                "risk_level": "medio"
            },
            "ny_londres_overlap": {
                "start": "08:00",
                "end": "11:00",
                "symbols": ["EURUSD", "GBPUSD", "USDCAD", "USDCHF"],
                "strategies": ["A_tendencia", "B_rango", "C_breakout"],
                "risk_level": "alto"
            },
            "dead_zone": {
                "start": "13:00",
                "end": "18:00",
                "symbols": [],
                "strategies": [],
                "risk_level": "ninguno"
            },
            "asia": {
                "start": "19:00",
                "end": "23:59",
                "symbols": ["USDJPY", "AUDUSD", "NZDUSD"],
                "strategies": ["B_rango"],
                "risk_level": "bajo"
            },
            "asia_madrugada": {
                "start": "00:00",
                "end": "02:00",
                "symbols": ["USDJPY", "AUDUSD", "NZDUSD"],
                "strategies": ["B_rango"],
                "risk_level": "bajo"
            }
        },
        "global_rules": {
            "allow_reevaluation_outside_hours": True
        }
    }


@pytest.fixture
def temp_config_file(sample_sessions_config):
    """Crea archivo temporal de configuración para tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_sessions_config, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    temp_path.unlink()


class TestTradingSessionManagerInit:
    """Tests de inicialización del TradingSessionManager."""
    
    def test_init_with_valid_config(self, temp_config_file):
        """Test: Inicialización con archivo de configuración válido."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        assert len(manager.sessions) == 5
        assert 'ny_londres_overlap' in manager.sessions
        assert manager.global_rules['allow_reevaluation_outside_hours'] is True
    
    def test_init_with_missing_file(self):
        """Test: Inicialización con archivo faltante usa config por defecto."""
        fake_path = Path("nonexistent/config.json")
        manager = TradingSessionManager(config_path=fake_path)
        
        # Debe crear config por defecto
        assert len(manager.sessions) == 1
        assert 'always' in manager.sessions
        assert manager.sessions['always']['symbols'] == []  # Todos permitidos
    
    def test_init_with_invalid_json(self):
        """Test: Inicialización con JSON inválido usa config por defecto."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json content")
            temp_path = Path(f.name)
        
        try:
            manager = TradingSessionManager(config_path=temp_path)
            
            # Debe usar config por defecto
            assert 'always' in manager.sessions
        finally:
            temp_path.unlink()


class TestIsSymbolTradeable:
    """Tests del método is_symbol_tradeable."""
    
    def test_symbol_in_active_session(self, temp_config_file):
        """Test: Símbolo en sesión activa retorna True."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        # 09:00 está dentro de ny_londres_overlap (08:00-11:00)
        test_time = datetime(2025, 1, 15, 9, 30)
        is_tradeable, reason = manager.is_symbol_tradeable("EURUSD", test_time)
        
        assert is_tradeable is True
        assert "ny_londres_overlap" in reason
    
    def test_symbol_outside_hours_no_position(self, temp_config_file):
        """Test: Símbolo fuera de horario sin posición retorna False."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        # 14:00 está en dead_zone (13:00-18:00) donde EURUSD no está permitido
        test_time = datetime(2025, 1, 15, 14, 0)
        is_tradeable, reason = manager.is_symbol_tradeable(
            "EURUSD", 
            test_time,
            has_open_position=False
        )
        
        assert is_tradeable is False
        assert "Fuera de horario" in reason
    
    def test_symbol_outside_hours_with_position(self, temp_config_file):
        """Test: Símbolo fuera de horario CON posición permite reevaluación."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        # 14:00 está en dead_zone, pero tiene posición abierta
        test_time = datetime(2025, 1, 15, 14, 0)
        is_tradeable, reason = manager.is_symbol_tradeable(
            "EURUSD",
            test_time,
            has_open_position=True
        )
        
        assert is_tradeable is True
        assert "posición abierta" in reason
        assert "reevaluación permitida" in reason
    
    def test_symbol_not_in_any_session(self, temp_config_file):
        """Test: Símbolo no configurado en ninguna sesión retorna False."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        # XAUUSD no está en ninguna sesión
        test_time = datetime(2025, 1, 15, 10, 0)
        is_tradeable, reason = manager.is_symbol_tradeable("XAUUSD", test_time)
        
        assert is_tradeable is False
        assert "No hay sesiones configuradas" in reason
    
    def test_midnight_crossover_session(self, temp_config_file):
        """Test: Sesión que cruza medianoche (19:00-02:00) funciona correctamente."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        # 23:30 está en sesión asia (19:00-23:59)
        test_time = datetime(2025, 1, 15, 23, 30)
        is_tradeable, reason = manager.is_symbol_tradeable("USDJPY", test_time)
        
        assert is_tradeable is True
        assert "asia" in reason
        
        # 01:00 está en sesión asia_madrugada (00:00-02:00)
        test_time = datetime(2025, 1, 15, 1, 0)
        is_tradeable, reason = manager.is_symbol_tradeable("USDJPY", test_time)
        
        assert is_tradeable is True
        assert "asia_madrugada" in reason


class TestGetActiveSession:
    """Tests del método _get_active_session."""
    
    def test_get_active_session_found(self, temp_config_file):
        """Test: Encuentra sesión activa correctamente."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        test_time = time(9, 0)  # 09:00 en ny_londres_overlap
        session = manager._get_active_session("EURUSD", test_time)
        
        assert session is not None
        assert session['name'] == 'ny_londres_overlap'
        assert 'EURUSD' in session['symbols']
    
    def test_get_active_session_not_found(self, temp_config_file):
        """Test: Retorna None cuando no hay sesión activa."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        test_time = time(14, 0)  # 14:00 en dead_zone, EURUSD no permitido
        session = manager._get_active_session("EURUSD", test_time)
        
        assert session is None


class TestGetNextSession:
    """Tests del método _get_next_session."""
    
    def test_get_next_session_found(self, temp_config_file):
        """Test: Encuentra próxima sesión correctamente."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        test_time = time(6, 0)  # 06:00, próxima sesión es ny_londres_overlap a las 08:00
        next_session = manager._get_next_session("EURUSD", test_time)
        
        assert next_session is not None
        assert next_session['name'] == 'ny_londres_overlap'
        assert next_session['start'] == '08:00'
    
    def test_get_next_session_none(self, temp_config_file):
        """Test: Retorna None si no hay más sesiones en el día."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        test_time = time(12, 0)  # 12:00, no hay sesiones después para EURUSD
        next_session = manager._get_next_session("EURUSD", test_time)
        
        assert next_session is None


class TestGetActiveSymbols:
    """Tests del método get_active_symbols."""
    
    def test_get_active_symbols_during_overlap(self, temp_config_file):
        """Test: Retorna símbolos activos durante overlap."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        test_time = datetime(2025, 1, 15, 9, 0)  # 09:00 en ny_londres_overlap
        active = manager.get_active_symbols(test_time)
        
        assert 'EURUSD' in active
        assert 'GBPUSD' in active
        assert 'USDCAD' in active
        assert 'USDCHF' in active
    
    def test_get_active_symbols_during_dead_zone(self, temp_config_file):
        """Test: Retorna lista vacía durante dead_zone."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        test_time = datetime(2025, 1, 15, 15, 0)  # 15:00 en dead_zone
        active = manager.get_active_symbols(test_time)
        
        assert active == []
    
    def test_get_active_symbols_asia(self, temp_config_file):
        """Test: Retorna símbolos asiáticos durante sesión Asia."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        test_time = datetime(2025, 1, 15, 20, 0)  # 20:00 en asia
        active = manager.get_active_symbols(test_time)
        
        assert 'USDJPY' in active
        assert 'AUDUSD' in active
        assert 'NZDUSD' in active


class TestTimeRangeLogic:
    """Tests de lógica de rangos de tiempo."""
    
    def test_is_time_in_range_normal(self, temp_config_file):
        """Test: Rango normal (sin cruce de medianoche)."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        # 09:00 está entre 08:00 y 11:00
        assert manager._is_time_in_range(
            time(9, 0),
            time(8, 0),
            time(11, 0)
        ) is True
        
        # 12:00 NO está entre 08:00 y 11:00
        assert manager._is_time_in_range(
            time(12, 0),
            time(8, 0),
            time(11, 0)
        ) is False
    
    def test_is_time_in_range_midnight_crossover(self, temp_config_file):
        """Test: Rango que cruza medianoche."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        # 23:00 está en rango 22:00-02:00
        assert manager._is_time_in_range(
            time(23, 0),
            time(22, 0),
            time(2, 0)
        ) is True
        
        # 01:00 está en rango 22:00-02:00
        assert manager._is_time_in_range(
            time(1, 0),
            time(22, 0),
            time(2, 0)
        ) is True
        
        # 10:00 NO está en rango 22:00-02:00
        assert manager._is_time_in_range(
            time(10, 0),
            time(22, 0),
            time(2, 0)
        ) is False


class TestParseTime:
    """Tests de conversión de strings a time."""
    
    def test_parse_time_valid(self, temp_config_file):
        """Test: Parseo correcto de formato HH:MM."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        result = manager._parse_time("09:30")
        assert result == time(9, 30)
        
        result = manager._parse_time("00:00")
        assert result == time(0, 0)
        
        result = manager._parse_time("23:59")
        assert result == time(23, 59)
    
    def test_parse_time_invalid(self, temp_config_file):
        """Test: Parseo de formato inválido retorna 00:00."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        result = manager._parse_time("invalid")
        assert result == time(0, 0)
        
        result = manager._parse_time("25:00")  # Hora inválida
        assert result == time(0, 0)


class TestGetCurrentSessionInfo:
    """Tests del método get_current_session_info."""
    
    def test_get_session_info_active(self, temp_config_file):
        """Test: Información completa cuando hay sesión activa."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        test_time = datetime(2025, 1, 15, 9, 0)
        info = manager.get_current_session_info("EURUSD", test_time)
        
        assert info['is_tradeable'] is True
        assert info['session_name'] == 'ny_londres_overlap'
        assert info['session_data'] is not None
        assert 'Sesión activa' in info['reason']
    
    def test_get_session_info_inactive(self, temp_config_file):
        """Test: Información cuando no hay sesión activa."""
        manager = TradingSessionManager(config_path=temp_config_file)
        
        test_time = datetime(2025, 1, 15, 14, 0)  # dead_zone
        info = manager.get_current_session_info("EURUSD", test_time)
        
        assert info['is_tradeable'] is False
        assert info['session_name'] is None
        assert info['session_data'] is None
        assert 'Fuera de horario' in info['reason']
