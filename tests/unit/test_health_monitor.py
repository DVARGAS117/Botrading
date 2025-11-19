"""
Tests unitarios para el módulo HealthMonitor.
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from src.core.health_monitor import HealthMonitor, BotHealthStatus, HealthAnomaly


class TestHealthMonitor:
    """Tests para HealthMonitor"""

    @pytest.fixture
    def temp_logs_dir(self):
        """Directorio temporal para logs de testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def health_monitor(self, temp_logs_dir):
        """Instancia de HealthMonitor para testing"""
        return HealthMonitor(logs_dir=temp_logs_dir)

    def test_init_with_valid_logs_dir(self, temp_logs_dir):
        """Test inicialización con directorio de logs válido"""
        monitor = HealthMonitor(logs_dir=temp_logs_dir)
        assert monitor.logs_dir == temp_logs_dir
        assert monitor.max_age_hours == 2

    def test_get_bot_status_no_logs(self, health_monitor):
        """Test obtener status de bot sin logs"""
        status = health_monitor.get_bot_status("bot_1")

        assert isinstance(status, BotHealthStatus)
        assert status.bot_name == "bot_1"
        assert status.is_active is False
        assert status.last_log_time is None
        assert status.recent_errors == []
        assert status.error_count == 0

    def test_is_recent_log(self, health_monitor):
        """Test verificar si log es reciente"""
        recent_time = datetime.now() - timedelta(minutes=30)
        old_time = datetime.now() - timedelta(hours=3)

        assert health_monitor._is_recent_log(recent_time) is True
        assert health_monitor._is_recent_log(old_time) is False

    def test_get_bot_status_with_recent_logs(self, temp_logs_dir, health_monitor):
        """Test obtener status con logs recientes"""
        # Crear archivo de log con entrada reciente
        recent_time = (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
        log_file = temp_logs_dir / "bot_1_20251113.log"
        log_content = f"[{recent_time}] [bot_1] [INFO] Bot iniciado\n"

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        assert log_file.exists()

        status = health_monitor.get_bot_status("bot_1")

        assert status.is_active is True
        assert status.last_log_time is not None
        assert status.error_count == 0

    def test_get_bot_status_with_old_logs(self, temp_logs_dir, health_monitor):
        """Test obtener status con logs antiguos"""
        # Crear archivo de log con entrada antigua
        old_time = (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
        log_file = temp_logs_dir / "bot_1_20251113.log"
        log_content = f"[{old_time}] [bot_1] [INFO] Bot iniciado\n"

        log_file.write_text(log_content)

        status = health_monitor.get_bot_status("bot_1")

        assert status.is_active is False
        assert status.last_log_time is not None

    def test_get_bot_status_with_errors(self, temp_logs_dir, health_monitor):
        """Test obtener status con errores en logs"""
        recent_time = (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
        log_file = temp_logs_dir / "bot_1_20251113.log"
        log_content = f"[{recent_time}] [bot_1] [ERROR] Error de conexión\n"

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        assert log_file.exists()

        status = health_monitor.get_bot_status("bot_1")

        assert status.is_active is True
        assert status.error_count == 1
        assert len(status.recent_errors) == 1
        assert "Error de conexión" in status.recent_errors[0]

    def test_get_all_bots_status(self, temp_logs_dir, health_monitor):
        """Test obtener status de todos los bots"""
        # Crear logs para múltiples bots
        recent_time = (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
        bots = ["bot_1", "bot_2", "bot_3"]
        for bot in bots:
            log_file = temp_logs_dir / f"{bot}_20251113.log"
            log_content = f"[{recent_time}] [{bot}] [INFO] Bot iniciado\n"

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(log_content)
            assert log_file.exists()

        statuses = health_monitor.get_all_bots_status()

        assert len(statuses) == 3
        for bot in bots:
            assert bot in statuses
            assert statuses[bot].is_active is True

    def test_check_anomalies_no_anomalies(self, health_monitor):
        """Test verificar anomalías cuando no hay"""
        anomalies = health_monitor.check_anomalies()
        assert anomalies == []

    def test_check_anomalies_inactive_bots(self, temp_logs_dir, health_monitor):
        """Test detectar bots inactivos como anomalía"""
        # Crear log antiguo
        old_time = (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
        log_file = temp_logs_dir / "bot_1_20251113.log"
        log_content = f"[{old_time}] [bot_1] [INFO] Bot iniciado\n"

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)

        anomalies = health_monitor.check_anomalies()

        assert len(anomalies) == 1
        assert anomalies[0].bot_name == "bot_1"
        assert "inactivo" in anomalies[0].message.lower()

    def test_check_anomalies_recent_errors(self, temp_logs_dir, health_monitor):
        """Test detectar errores recientes como anomalía"""
        recent_time = (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
        log_file = temp_logs_dir / "bot_1_20251113.log"
        log_content = f"[{recent_time}] [bot_1] [ERROR] Error crítico\n"

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)

        anomalies = health_monitor.check_anomalies()

        assert len(anomalies) == 1
        assert anomalies[0].bot_name == "bot_1"
        assert "error" in anomalies[0].message.lower()

    def test_parse_log_line_valid(self, health_monitor):
        """Test parsear línea de log válida"""
        line = "[2025-11-13 10:30:00] [bot_1] [INFO] Mensaje de prueba"
        parsed = health_monitor._parse_log_line(line)

        assert parsed is not None
        assert parsed["timestamp"] == datetime(2025, 11, 13, 10, 30, 0)
        assert parsed["bot_name"] == "bot_1"
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Mensaje de prueba"

    def test_parse_log_line_invalid(self, health_monitor):
        """Test parsear línea de log inválida"""
        line = "Línea inválida sin formato"
        parsed = health_monitor._parse_log_line(line)

        assert parsed is None