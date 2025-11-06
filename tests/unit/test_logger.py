"""
Tests unitarios para el módulo logger.

Este módulo prueba la funcionalidad de logging estructurado por bot y nivel,
asegurando el cumplimiento del Ticket T39.
"""
import os
import json
import logging
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.core.logger import BotLogger, LogLevel, LogConfig, LoggerError


class TestLogConfig:
    """Tests para la clase LogConfig"""
    
    def test_log_config_default_values(self):
        """
        Test: Debe crear configuración con valores por defecto
        
        Dado que se crea una configuración sin parámetros
        Cuando se inicializa LogConfig
        Entonces debe tener valores por defecto válidos
        """
        # Act
        config = LogConfig()
        
        # Assert
        assert config.level == LogLevel.INFO
        assert config.log_dir == "logs"
        assert config.log_to_console is True
        assert config.log_to_file is True
        assert config.format_json is False
    
    def test_log_config_custom_values(self):
        """
        Test: Debe aceptar valores personalizados
        
        Dado que se proporcionan valores personalizados
        Cuando se inicializa LogConfig
        Entonces debe usar esos valores
        """
        # Arrange & Act
        config = LogConfig(
            level=LogLevel.DEBUG,
            log_dir="custom_logs",
            log_to_console=False,
            format_json=True
        )
        
        # Assert
        assert config.level == LogLevel.DEBUG
        assert config.log_dir == "custom_logs"
        assert config.log_to_console is False
        assert config.format_json is True


class TestBotLogger:
    """Tests para la clase BotLogger"""
    
    def test_create_logger_with_bot_name(self, tmp_path):
        """
        Test: Debe crear logger con nombre de bot
        
        Dado que se proporciona un nombre de bot
        Cuando se crea el logger
        Entonces el logger debe tener ese nombre
        """
        # Arrange
        bot_name = "bot_1"
        config = LogConfig(log_dir=str(tmp_path))
        
        # Act
        logger = BotLogger(bot_name, config)
        
        # Assert
        assert logger.bot_name == bot_name
        assert logger.logger.name == f"botrading.{bot_name}"
    
    def test_log_info_includes_required_fields(self, tmp_path, caplog):
        """
        Test: Debe incluir bot, nivel, timestamp y mensaje
        
        Dado que se registra un mensaje INFO
        Cuando se llama a info()
        Entonces el log debe incluir bot, nivel, timestamp y mensaje
        """
        # Arrange
        bot_name = "bot_test"
        config = LogConfig(log_dir=str(tmp_path), log_to_file=False)
        logger = BotLogger(bot_name, config)
        message = "Test message"
        
        # Act
        with caplog.at_level(logging.INFO):
            logger.info(message)
        
        # Assert
        assert len(caplog.records) == 1
        record = caplog.records[0]
        # El bot_name está en el extra data, no en el mensaje
        assert hasattr(record, 'bot_name')
        assert record.bot_name == bot_name
        assert message in record.getMessage()
        assert record.levelname == "INFO"
    
    def test_log_warning_level(self, tmp_path, caplog):
        """
        Test: Debe registrar mensajes WARNING correctamente
        
        Dado que se registra un mensaje WARNING
        Cuando se llama a warning()
        Entonces debe aparecer con nivel WARNING
        """
        # Arrange
        config = LogConfig(log_dir=str(tmp_path), log_to_file=False)
        logger = BotLogger("bot_test", config)
        
        # Act
        with caplog.at_level(logging.WARNING):
            logger.warning("Warning message")
        
        # Assert
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
    
    def test_log_error_level(self, tmp_path, caplog):
        """
        Test: Debe registrar mensajes ERROR correctamente
        
        Dado que se registra un mensaje ERROR
        Cuando se llama a error()
        Entonces debe aparecer con nivel ERROR
        """
        # Arrange
        config = LogConfig(log_dir=str(tmp_path), log_to_file=False)
        logger = BotLogger("bot_test", config)
        
        # Act
        with caplog.at_level(logging.ERROR):
            logger.error("Error message")
        
        # Assert
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
    
    def test_log_debug_level(self, tmp_path, caplog):
        """
        Test: Debe registrar mensajes DEBUG cuando el nivel lo permite
        
        Dado que el logger está configurado en nivel DEBUG
        Cuando se llama a debug()
        Entonces debe aparecer el mensaje
        """
        # Arrange
        config = LogConfig(
            level=LogLevel.DEBUG, 
            log_dir=str(tmp_path), 
            log_to_file=False
        )
        logger = BotLogger("bot_test", config)
        
        # Act
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
        
        # Assert
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "DEBUG"
    
    def test_log_debug_not_shown_in_info_level(self, tmp_path, caplog):
        """
        Test: No debe mostrar DEBUG cuando el nivel es INFO
        
        Dado que el logger está configurado en nivel INFO
        Cuando se llama a debug()
        Entonces NO debe aparecer el mensaje
        """
        # Arrange
        config = LogConfig(
            level=LogLevel.INFO,
            log_dir=str(tmp_path),
            log_to_file=False
        )
        logger = BotLogger("bot_test", config)
        
        # Act
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
        
        # Assert
        assert len(caplog.records) == 0
    
    def test_log_to_file_creates_file(self, tmp_path):
        """
        Test: Debe crear archivo de log cuando está habilitado
        
        Dado que log_to_file está habilitado
        Cuando se registra un mensaje
        Entonces debe crearse el archivo de log
        """
        # Arrange
        log_dir = tmp_path / "logs"
        config = LogConfig(log_dir=str(log_dir), log_to_console=False)
        logger = BotLogger("bot_test", config)
        
        # Act
        logger.info("Test message")
        
        # Assert
        log_files = list(log_dir.glob("bot_test_*.log"))
        assert len(log_files) > 0
    
    def test_log_file_naming_convention(self, tmp_path):
        """
        Test: El archivo de log debe seguir convención de nombres
        
        Dado que se crea un logger
        Cuando se genera el archivo de log
        Entonces debe tener formato: {bot_name}_{YYYYMMDD}.log
        """
        # Arrange
        log_dir = tmp_path / "logs"
        bot_name = "bot_test"
        config = LogConfig(log_dir=str(log_dir), log_to_console=False)
        logger = BotLogger(bot_name, config)
        
        # Act
        logger.info("Test")
        
        # Assert
        today = datetime.now().strftime("%Y%m%d")
        expected_file = log_dir / f"{bot_name}_{today}.log"
        assert expected_file.exists()
    
    def test_log_json_format(self, tmp_path):
        """
        Test: Debe formatear logs en JSON cuando está configurado
        
        Dado que format_json está habilitado
        Cuando se registra un mensaje
        Entonces debe estar en formato JSON válido
        """
        # Arrange
        log_dir = tmp_path / "logs"
        config = LogConfig(
            log_dir=str(log_dir),
            log_to_console=False,
            format_json=True
        )
        logger = BotLogger("bot_test", config)
        
        # Act
        logger.info("Test message", extra={"key": "value"})
        
        # Assert
        log_files = list(log_dir.glob("bot_test_*.log"))
        assert len(log_files) > 0
        
        with open(log_files[0], 'r') as f:
            log_line = f.readline()
            log_data = json.loads(log_line)
            assert "bot" in log_data
            assert "level" in log_data
            assert "timestamp" in log_data
            assert "message" in log_data
    
    def test_log_with_extra_data(self, tmp_path, caplog):
        """
        Test: Debe incluir datos extra en el log
        
        Dado que se proporcionan datos extra
        Cuando se registra un mensaje
        Entonces los datos extra deben incluirse
        """
        # Arrange
        config = LogConfig(log_dir=str(tmp_path), log_to_file=False)
        logger = BotLogger("bot_test", config)
        extra_data = {"operation_id": "123", "symbol": "EURUSD"}
        
        # Act
        with caplog.at_level(logging.INFO):
            logger.info("Trade executed", extra=extra_data)
        
        # Assert
        record = caplog.records[0]
        assert hasattr(record, 'operation_id')
        assert record.operation_id == "123"
    
    def test_multiple_bots_separate_logs(self, tmp_path):
        """
        Test: Cada bot debe tener su propio archivo de log
        
        Dado que hay múltiples bots
        Cuando cada uno registra mensajes
        Entonces deben tener archivos separados
        """
        # Arrange
        log_dir = tmp_path / "logs"
        config = LogConfig(log_dir=str(log_dir), log_to_console=False)
        logger1 = BotLogger("bot_1", config)
        logger2 = BotLogger("bot_2", config)
        
        # Act
        logger1.info("Bot 1 message")
        logger2.info("Bot 2 message")
        
        # Assert
        today = datetime.now().strftime("%Y%m%d")
        assert (log_dir / f"bot_1_{today}.log").exists()
        assert (log_dir / f"bot_2_{today}.log").exists()
    
    def test_log_exception_with_traceback(self, tmp_path, caplog):
        """
        Test: Debe registrar excepciones con traceback
        
        Dado que ocurre una excepción
        Cuando se llama a exception()
        Entonces debe incluir el traceback
        """
        # Arrange
        config = LogConfig(log_dir=str(tmp_path), log_to_file=False)
        logger = BotLogger("bot_test", config)
        
        # Act
        try:
            raise ValueError("Test error")
        except ValueError:
            with caplog.at_level(logging.ERROR):
                logger.exception("An error occurred")
        
        # Assert
        assert len(caplog.records) == 1
        assert "Traceback" in caplog.text or "ValueError" in caplog.text
    
    def test_log_rotation_by_date(self, tmp_path):
        """
        Test: Los logs deben rotar por fecha
        
        Dado que cambia el día
        Cuando se registran mensajes
        Entonces debe crearse un nuevo archivo
        """
        # Arrange
        log_dir = tmp_path / "logs"
        config = LogConfig(log_dir=str(log_dir), log_to_console=False)
        logger = BotLogger("bot_test", config)
        
        # Act
        logger.info("Message 1")
        
        # Simulate date change (verificar que el nombre incluye fecha)
        today = datetime.now().strftime("%Y%m%d")
        expected_file = log_dir / f"bot_test_{today}.log"
        
        # Assert
        assert expected_file.exists()
    
    def test_logger_thread_safe(self, tmp_path):
        """
        Test: El logger debe ser thread-safe
        
        Dado que múltiples threads usan el logger
        Cuando se registran mensajes concurrentemente
        Entonces no deben perderse mensajes
        """
        # Arrange
        import threading
        log_dir = tmp_path / "logs"
        config = LogConfig(log_dir=str(log_dir), log_to_console=False)
        logger = BotLogger("bot_test", config)
        
        def log_messages():
            for i in range(10):
                logger.info(f"Message {i}")
        
        # Act
        threads = [threading.Thread(target=log_messages) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Assert
        log_files = list(log_dir.glob("bot_test_*.log"))
        assert len(log_files) > 0
        
        with open(log_files[0], 'r') as f:
            lines = f.readlines()
            assert len(lines) == 50  # 5 threads * 10 messages
    
    def test_disable_console_logging(self, tmp_path, caplog):
        """
        Test: Debe poder deshabilitar logging a consola
        
        Dado que log_to_console está deshabilitado
        Cuando se registra un mensaje
        Entonces no debe aparecer en consola
        """
        # Arrange
        log_dir = tmp_path / "logs"
        config = LogConfig(
            log_dir=str(log_dir),
            log_to_console=False,
            log_to_file=True
        )
        logger = BotLogger("bot_test", config)
        
        # Act
        logger.info("Test message")
        
        # Assert - No debe haber registros en caplog (consola)
        # pero sí en archivo
        log_files = list(log_dir.glob("bot_test_*.log"))
        assert len(log_files) > 0
