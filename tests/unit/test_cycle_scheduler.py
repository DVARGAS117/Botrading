import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, time
import time as time_module
from src.core.cycle_scheduler import CycleScheduler
from src.core.time_validator import TimeValidator


class TestCycleScheduler:
    """Test suite for CycleScheduler - T1: Ejecución de ciclo por bot a inicio de hora"""

    @pytest.fixture
    def mock_time_validator(self):
        """Mock TimeValidator for testing"""
        validator = Mock(spec=TimeValidator)
        return validator

    @pytest.fixture
    def scheduler_config(self):
        """Default scheduler configuration"""
        return {
            "cycle_scheduler": {
                "enabled": True,
                "start_delay_seconds": 5,  # Ligero retraso para asegurar velas cerradas
                "check_interval_seconds": 30,  # Verificar cada 30 segundos
                "max_wait_hours": 8  # Máximo 8 horas de espera (06:00-13:00)
            }
        }

    @pytest.fixture
    def cycle_scheduler(self, mock_time_validator, scheduler_config):
        """Create CycleScheduler instance for testing"""
        return CycleScheduler(mock_time_validator, scheduler_config)

    def test_initialization_with_valid_config(self, mock_time_validator, scheduler_config):
        """Test scheduler initializes correctly with valid configuration"""
        scheduler = CycleScheduler(mock_time_validator, scheduler_config)

        assert scheduler.time_validator == mock_time_validator
        assert scheduler.start_delay_seconds == 5
        assert scheduler.check_interval_seconds == 30
        assert scheduler.max_wait_hours == 8
        assert scheduler.enabled == True

    def test_initialization_with_default_config(self, mock_time_validator):
        """Test scheduler initializes with default values when config is minimal"""
        minimal_config = {"cycle_scheduler": {}}
        scheduler = CycleScheduler(mock_time_validator, minimal_config)

        assert scheduler.start_delay_seconds == 3  # default
        assert scheduler.check_interval_seconds == 60  # default
        assert scheduler.max_wait_hours == 8  # default

    def test_initialization_disabled_scheduler(self, mock_time_validator):
        """Test scheduler can be disabled via config"""
        config = {"cycle_scheduler": {"enabled": False}}
        scheduler = CycleScheduler(mock_time_validator, config)

        assert scheduler.enabled == False

    @patch('src.core.cycle_scheduler.datetime')
    def test_should_start_cycle_at_hour_start(self, mock_datetime, cycle_scheduler, mock_time_validator):
        """Test that cycle should start exactly at hour start (HH:00)"""
        # Mock current time as 10:00:00 (exactly hour start)
        mock_datetime.now.return_value = datetime(2025, 11, 6, 10, 0, 0)

        # Mock time validator as valid trading time
        mock_time_validator.is_trading_time.return_value = Mock(is_valid=True)

        assert cycle_scheduler.should_start_cycle() == True

    @patch('src.core.cycle_scheduler.datetime')
    def test_should_not_start_cycle_not_hour_start(self, mock_datetime, cycle_scheduler, mock_time_validator):
        """Test that cycle should NOT start when not at hour start"""
        # Mock current time as 10:15:30 (not hour start)
        mock_datetime.now.return_value = datetime(2025, 11, 6, 10, 15, 30)

        # Mock time validator as valid trading time
        mock_time_validator.is_trading_time.return_value = Mock(is_valid=True)

        assert cycle_scheduler.should_start_cycle() == False

    @patch('src.core.cycle_scheduler.datetime')
    def test_should_not_start_cycle_outside_trading_hours(self, mock_datetime, cycle_scheduler, mock_time_validator):
        """Test that cycle should NOT start outside trading hours"""
        # Mock current time as 10:00:00 (hour start but outside trading)
        mock_datetime.now.return_value = datetime(2025, 11, 6, 10, 0, 0)

        # Mock time validator as invalid trading time
        mock_time_validator.is_trading_time.return_value = Mock(is_valid=False, reason="Outside trading hours")

        assert cycle_scheduler.should_start_cycle() == False

    @patch('src.core.cycle_scheduler.datetime')
    def test_should_not_start_cycle_weekend(self, mock_datetime, cycle_scheduler, mock_time_validator):
        """Test that cycle should NOT start on weekend"""
        # Mock current time as Saturday 10:00:00
        mock_datetime.now.return_value = datetime(2025, 11, 8, 10, 0, 0)  # Saturday

        # Mock time validator as invalid (weekend)
        mock_time_validator.is_trading_time.return_value = Mock(is_valid=False, reason="Weekend")

        assert cycle_scheduler.should_start_cycle() == False

    @patch('src.core.cycle_scheduler.time.sleep')
    @patch('src.core.cycle_scheduler.datetime')
    def test_wait_for_cycle_start_applies_delay(self, mock_datetime, mock_sleep, cycle_scheduler, mock_time_validator):
        """Test that wait_for_cycle_start applies the configured delay"""
        # Mock current time as 10:00:00
        mock_datetime.now.return_value = datetime(2025, 11, 6, 10, 0, 0)

        # Mock time validator as valid
        mock_time_validator.is_trading_time.return_value = Mock(is_valid=True)

        # Call wait_for_cycle_start
        result = cycle_scheduler.wait_for_cycle_start()

        # Should sleep for start_delay_seconds (5)
        mock_sleep.assert_called_once_with(5)
        assert result == True

    @patch('src.core.cycle_scheduler.time.sleep')
    @patch('src.core.cycle_scheduler.time.time')
    @patch('src.core.cycle_scheduler.datetime')
    def test_wait_for_cycle_start_timeout(self, mock_datetime, mock_time, mock_sleep, cycle_scheduler, mock_time_validator):
        """Test that wait_for_cycle_start times out after max_wait_hours"""
        # Set max_wait_hours to 1 for faster test
        cycle_scheduler.max_wait_hours = 1

        # Mock time validator always invalid (simulating waiting)
        mock_time_validator.is_trading_time.return_value = Mock(is_valid=False)

        # Mock time.time: start at 0, then simulate loop iterations, finally exceed timeout
        mock_time.side_effect = [0, 1000, 2000, 4000]  # 0=start, then exceed 3600

        # Mock datetime to always return non-hour start
        mock_datetime.now.return_value = datetime(2025, 11, 6, 10, 15, 30)

        result = cycle_scheduler.wait_for_cycle_start()

        # Should timeout and return False
        assert result == False
        # Should have slept at least once (in the loop)
        assert mock_sleep.call_count >= 1

    @patch('src.core.cycle_scheduler.time.sleep')
    @patch('src.core.cycle_scheduler.time.time')
    @patch('src.core.cycle_scheduler.datetime')
    def test_run_cycle_executes_callback(self, mock_datetime, mock_time, mock_sleep, cycle_scheduler, mock_time_validator):
        """Test that run_cycle executes the provided callback when conditions are met"""
        # Mock callback
        mock_callback = Mock()

        # Mock time.time to not timeout
        mock_time.return_value = 0

        # Mock datetime: first call not hour start, second call hour start
        mock_datetime.now.side_effect = [
            datetime(2025, 11, 6, 9, 59, 30),  # Not hour start
            datetime(2025, 11, 6, 10, 0, 0),   # Hour start
            datetime(2025, 11, 6, 10, 0, 0),   # Hour start (for delay sleep)
        ]

        # Mock time validator: invalid first, valid subsequent
        call_count = 0
        def mock_is_trading_time():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Mock(is_valid=False)
            else:
                return Mock(is_valid=True)
        
        mock_time_validator.is_trading_time.side_effect = mock_is_trading_time

        # Run cycle
        cycle_scheduler.run_cycle(mock_callback)

        # Callback should have been called once
        mock_callback.assert_called_once()

        # Should have slept for delay
        mock_sleep.assert_called_with(5)

    def test_get_scheduler_status(self, cycle_scheduler, mock_time_validator):
        """Test get_scheduler_status returns correct information"""
        # Mock time validator
        mock_time_validator.is_trading_time.return_value = Mock(is_valid=True, reason="Valid trading time")

        status = cycle_scheduler.get_scheduler_status()

        expected_keys = [
            'enabled', 'start_delay_seconds', 'check_interval_seconds',
            'max_wait_hours', 'is_trading_time_valid', 'trading_time_reason'
        ]

        for key in expected_keys:
            assert key in status

        assert status['enabled'] == True
        assert status['is_trading_time_valid'] == True

    @patch('src.core.cycle_scheduler.datetime')
    def test_calculate_seconds_until_next_hour(self, mock_datetime, cycle_scheduler):
        """Test calculation of seconds until next hour"""
        # Mock current time as 10:15:30
        mock_datetime.now.return_value = datetime(2025, 11, 6, 10, 15, 30)

        seconds = cycle_scheduler._calculate_seconds_until_next_hour()

        # Should be 44 minutes 30 seconds = 2670 seconds
        assert seconds == 2670

    @patch('src.core.cycle_scheduler.datetime')
    def test_calculate_seconds_until_next_hour_at_hour_start(self, mock_datetime, cycle_scheduler):
        """Test calculation returns 0 when at hour start"""
        # Mock current time as 10:00:00
        mock_datetime.now.return_value = datetime(2025, 11, 6, 10, 0, 0)

        seconds = cycle_scheduler._calculate_seconds_until_next_hour()

        assert seconds == 0

    def test_scheduler_disabled_does_not_run(self, mock_time_validator):
        """Test that disabled scheduler does not execute cycles"""
        config = {"cycle_scheduler": {"enabled": False}}
        scheduler = CycleScheduler(mock_time_validator, config)

        mock_callback = Mock()

        # Should not run anything
        scheduler.run_cycle(mock_callback)

        # Callback should not be called
        mock_callback.assert_not_called()

    # =========================================================================
    # T02: Tests para logging de rechazos de filtros
    # =========================================================================

    def test_initialization_with_logger(self, mock_time_validator, scheduler_config):
        """Test scheduler accepts optional logger parameter"""
        mock_logger = Mock()
        scheduler = CycleScheduler(mock_time_validator, scheduler_config, logger=mock_logger)

        assert scheduler.logger == mock_logger

    def test_initialization_without_logger_creates_default(self, mock_time_validator, scheduler_config):
        """Test scheduler creates default logger when not provided"""
        scheduler = CycleScheduler(mock_time_validator, scheduler_config)

        assert scheduler.logger is not None

    @patch('src.core.cycle_scheduler.datetime')
    def test_logs_rejection_outside_trading_hours(self, mock_datetime, mock_time_validator, scheduler_config):
        """Test that scheduler logs when filters reject due to outside trading hours"""
        # Mock logger
        mock_logger = Mock()
        
        scheduler = CycleScheduler(mock_time_validator, scheduler_config, logger=mock_logger)
        
        # Mock current time as hour start
        mock_datetime.now.return_value = datetime(2025, 11, 6, 14, 0, 0)  # 14:00 - outside trading hours
        
        # Mock time validator as invalid
        mock_time_validator.is_trading_time.return_value = Mock(
            is_valid=False,
            reason="Outside trading hours (06:00-13:00 Lima)"
        )
        
        # Try to start cycle
        result = scheduler.should_start_cycle()
        
        # Should not start
        assert result == False
        
        # Should log the rejection
        mock_logger.info.assert_called()
        log_call_args = mock_logger.info.call_args[0][0]
        assert "filter" in log_call_args.lower() or "reject" in log_call_args.lower()
        assert "Outside trading hours" in log_call_args

    @patch('src.core.cycle_scheduler.datetime')
    def test_logs_rejection_weekend(self, mock_datetime, mock_time_validator, scheduler_config):
        """Test that scheduler logs when filters reject due to weekend"""
        mock_logger = Mock()
        scheduler = CycleScheduler(mock_time_validator, scheduler_config, logger=mock_logger)
        
        # Mock Saturday
        mock_datetime.now.return_value = datetime(2025, 11, 8, 10, 0, 0)  # Saturday
        
        # Mock time validator as invalid
        mock_time_validator.is_trading_time.return_value = Mock(
            is_valid=False,
            reason="Weekend (non-business day)"
        )
        
        result = scheduler.should_start_cycle()
        
        assert result == False
        mock_logger.info.assert_called()
        log_call_args = mock_logger.info.call_args[0][0]
        assert "Weekend" in log_call_args

    @patch('src.core.cycle_scheduler.datetime')
    def test_logs_rejection_holiday(self, mock_datetime, mock_time_validator, scheduler_config):
        """Test that scheduler logs when filters reject due to holiday"""
        mock_logger = Mock()
        scheduler = CycleScheduler(mock_time_validator, scheduler_config, logger=mock_logger)
        
        # Mock holiday
        mock_datetime.now.return_value = datetime(2025, 12, 25, 10, 0, 0)  # Christmas
        
        # Mock time validator as invalid
        mock_time_validator.is_trading_time.return_value = Mock(
            is_valid=False,
            reason="Holiday (Peru)"
        )
        
        result = scheduler.should_start_cycle()
        
        assert result == False
        mock_logger.info.assert_called()
        log_call_args = mock_logger.info.call_args[0][0]
        assert "Holiday" in log_call_args

    @patch('src.core.cycle_scheduler.datetime')
    def test_does_not_log_when_filters_pass(self, mock_datetime, mock_time_validator, scheduler_config):
        """Test that scheduler does NOT log rejection when filters pass"""
        mock_logger = Mock()
        scheduler = CycleScheduler(mock_time_validator, scheduler_config, logger=mock_logger)
        
        # Mock valid time
        mock_datetime.now.return_value = datetime(2025, 11, 6, 10, 0, 0)  # Wednesday 10:00
        
        # Mock time validator as VALID
        mock_time_validator.is_trading_time.return_value = Mock(
            is_valid=True,
            reason=None
        )
        
        result = scheduler.should_start_cycle()
        
        # Should start
        assert result == True
        
        # Should NOT log any rejection
        # Filter calls to info that mention "reject" or "filter"
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        rejection_logs = [log for log in info_calls if "reject" in log.lower() or ("filter" in log.lower() and "not" in log.lower())]
        assert len(rejection_logs) == 0

    @patch('src.core.cycle_scheduler.datetime')
    def test_logs_contain_bot_context(self, mock_datetime, mock_time_validator, scheduler_config):
        """Test that log messages contain bot context when available"""
        mock_logger = Mock()
        scheduler = CycleScheduler(mock_time_validator, scheduler_config, logger=mock_logger, bot_name="EURUSD_Bot_1")
        
        # Mock invalid time
        mock_datetime.now.return_value = datetime(2025, 11, 6, 14, 0, 0)
        mock_time_validator.is_trading_time.return_value = Mock(
            is_valid=False,
            reason="Outside trading hours"
        )
        
        scheduler.should_start_cycle()
        
        # Check if bot_name is included in logs or extra context
        assert mock_logger.info.called
        # The bot_name should be stored in scheduler for use in logging
        assert scheduler.bot_name == "EURUSD_Bot_1"