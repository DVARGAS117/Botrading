
import pytest
import json
from pathlib import Path
from src.core.trading_session_manager import TradingSessionManager

class TestProductionConfig:
    """Tests para verificar la configuración de producción en config/trading_sessions.json"""

    @pytest.fixture
    def production_config_path(self):
        """Ruta al archivo de configuración de producción."""
        return Path(__file__).parent.parent.parent / "config" / "trading_sessions.json"

    def test_only_ny_londres_overlap_is_active(self, production_config_path):
        """Test: Verificar que solo la sesión ny_londres_overlap está activa."""
        
        # Cargar la configuración real
        with open(production_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        sessions = config.get('sessions', {})
        
        # Verificar que ny_londres_overlap existe
        assert 'ny_londres_overlap' in sessions, "La sesión ny_londres_overlap debe existir"
        
        # Verificar que NO existen otras sesiones de trading
        forbidden_sessions = ['londres', 'ny_tarde', 'asia', 'asia_madrugada']
        for session in forbidden_sessions:
            assert session not in sessions, f"La sesión {session} no debe estar activa en producción"
            
    def test_reevaluation_is_allowed(self, production_config_path):
        """Test: Verificar que la reevaluación fuera de horario está permitida."""
        with open(production_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        global_rules = config.get('global_rules', {})
        assert global_rules.get('allow_reevaluation_outside_hours') is True, "La reevaluación fuera de horario debe estar permitida"

    def test_manager_behavior_with_production_config(self):
        """Test: Verificar el comportamiento del manager con la config de producción."""
        # Inicializar manager con la config por defecto (que es la de producción)
        manager = TradingSessionManager()
        
        # Verificar que solo carga la sesión permitida (y dead_zone si se mantiene, o nada más)
        # Nota: dead_zone puede mantenerse o no, el requerimiento es "deshabilitar todos los horarios, solo vamos a operar en ny_londres_overlap"
        # Si dead_zone existe pero no tiene símbolos, no afecta, pero mejor verificar que las otras no están.
        
        active_sessions = manager.sessions.keys()
        assert 'ny_londres_overlap' in active_sessions
        assert 'londres' not in active_sessions
        assert 'asia' not in active_sessions
