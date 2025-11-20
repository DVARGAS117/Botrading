"""Tests para el main del Bot 1 INTRADAY."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

from src.bots.base.base_bot_operations import BotMode
from src.bots.strategies.intraday.gemini_3_pro.bot_1.main import (
    parse_arguments,
    confirm_live_mode,
    display_bot_banner,
    display_gemini_config,
    display_execution_summary,
    main,
)


class TestParseArguments:
    """Tests para parse_arguments."""

    @patch("sys.argv", ["main.py"])
    def test_default_arguments(self):
        """Test: Argumentos por defecto."""
        args = parse_arguments()

        assert args.mode == "demo"
        assert args.single_cycle is False
        assert args.interval == 300
        assert args.symbols == ["EURUSD"]
        assert args.log_level == "INFO"
        assert args.yes is False
        assert args.save_prompts is False

    @patch("sys.argv", ["main.py", "--mode", "live"])
    def test_live_mode_argument(self):
        """Test: Argumento modo LIVE."""
        args = parse_arguments()

        assert args.mode == "live"

    @patch("sys.argv", ["main.py", "--single-cycle"])
    def test_single_cycle_argument(self):
        """Test: Argumento single-cycle."""
        args = parse_arguments()

        assert args.single_cycle is True

    @patch("sys.argv", ["main.py", "--interval", "600"])
    def test_interval_argument(self):
        """Test: Argumento interval."""
        args = parse_arguments()

        assert args.interval == 600

    @patch("sys.argv", ["main.py", "--symbols", "EURUSD", "GBPUSD"])
    def test_symbols_argument(self):
        """Test: Argumento múltiples símbolos."""
        args = parse_arguments()

        assert args.symbols == ["EURUSD", "GBPUSD"]

    @patch("sys.argv", ["main.py", "--log-level", "DEBUG"])
    def test_log_level_argument(self):
        """Test: Argumento log-level."""
        args = parse_arguments()

        assert args.log_level == "DEBUG"

    @patch("sys.argv", ["main.py", "--yes"])
    def test_yes_argument(self):
        """Test: Argumento yes (auto-confirmación)."""
        args = parse_arguments()

        assert args.yes is True

    @patch("sys.argv", ["main.py", "--save-prompts"])
    def test_save_prompts_argument(self):
        """Test: Argumento save-prompts."""
        args = parse_arguments()

        assert args.save_prompts is True


class TestConfirmLiveMode:
    """Tests para confirm_live_mode."""

    @patch("builtins.input", return_value="SI")
    @patch("sys.stdout", new_callable=StringIO)
    def test_confirm_live_mode_yes(self, mock_stdout, mock_input):
        """Test: Usuario confirma modo LIVE."""
        result = confirm_live_mode()

        assert result is True
        assert "MODO LIVE ACTIVADO" in mock_stdout.getvalue()

    @patch("builtins.input", return_value="NO")
    @patch("sys.stdout", new_callable=StringIO)
    def test_confirm_live_mode_no(self, mock_stdout, mock_input):
        """Test: Usuario rechaza modo LIVE."""
        result = confirm_live_mode()

        assert result is False

    @patch("builtins.input", return_value="si")
    def test_confirm_live_mode_lowercase(self, mock_input):
        """Test: Usuario confirma con minúsculas."""
        result = confirm_live_mode()

        assert result is True

    @patch("builtins.input", return_value="  SI  ")
    def test_confirm_live_mode_with_spaces(self, mock_input):
        """Test: Usuario confirma con espacios."""
        result = confirm_live_mode()

        assert result is True


class TestDisplayFunctions:
    """Tests para funciones de display."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_display_bot_banner(self, mock_stdout):
        """Test: Display de banner del bot."""
        display_bot_banner()

        output = mock_stdout.getvalue()
        assert "BOT 1 - ESTRATEGIA INTRADAY" in output
        assert "1.0.0" in output
        assert "INTRADAY" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_display_gemini_config(self, mock_stdout):
        """Test: Display de configuración Gemini."""
        display_gemini_config()

        output = mock_stdout.getvalue()
        assert "Gemini 3 Pro" in output
        assert "Thinking Level: HIGH" in output
        assert "Code Execution: Habilitado" in output
        assert "media_resolution: high" in output

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["main.py", "--mode", "demo"])
    def test_display_execution_summary(self, mock_argv, mock_stdout):
        """Test: Display de resumen de ejecución."""
        args = parse_arguments()
        display_execution_summary(args)

        output = mock_stdout.getvalue()
        assert "Configuración de Ejecución" in output
        assert "DEMO" in output
        assert "EURUSD" in output


class TestMain:
    """Tests para la función main."""

    @patch("sys.argv", ["main.py", "--single-cycle"])
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.IntradayBot1Strategy")
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.get_bot_logger")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_single_cycle_demo(
        self, mock_stdout, mock_logger, mock_strategy_class
    ):
        """Test: Main con un solo ciclo en modo DEMO."""
        # Mock del bot
        mock_bot = Mock()
        mock_bot.initialize.return_value = True
        mock_bot.get_performance_metrics.return_value = {
            "current_pnl_r": 1.5,
            "trades_today": 2,
            "market_context": "london_open",
            "timestamp": "2025-11-19T10:00:00",
        }
        mock_strategy_class.return_value = mock_bot

        main()

        # Verificar que se inicializó el bot
        mock_strategy_class.assert_called_once()
        mock_bot.initialize.assert_called_once()
        mock_bot.run_trading_cycle.assert_called_once()
        mock_bot.get_performance_metrics.assert_called_once()

    @patch("sys.argv", ["main.py", "--mode", "live", "--yes"])
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.IntradayBot1Strategy")
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.get_bot_logger")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_live_mode_with_yes_flag(
        self, mock_stdout, mock_logger, mock_strategy_class
    ):
        """Test: Main en modo LIVE con flag --yes."""
        mock_bot = Mock()
        mock_bot.initialize.return_value = True
        mock_strategy_class.return_value = mock_bot

        # No debe pedir confirmación
        main()

        mock_strategy_class.assert_called_once()

    @patch("sys.argv", ["main.py", "--mode", "live"])
    @patch("builtins.input", return_value="NO")
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.get_bot_logger")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_live_mode_cancelled(self, mock_stdout, mock_logger, mock_input):
        """Test: Main en modo LIVE cancelado por usuario."""
        main()

        output = mock_stdout.getvalue()
        assert "cancelada" in output

    @patch("sys.argv", ["main.py"])
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.IntradayBot1Strategy")
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.get_bot_logger")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_initialization_failed(
        self, mock_stdout, mock_logger, mock_strategy_class
    ):
        """Test: Main cuando falla la inicialización."""
        mock_bot = Mock()
        mock_bot.initialize.return_value = False
        mock_strategy_class.return_value = mock_bot

        main()

        output = mock_stdout.getvalue()
        assert "Error en inicialización" in output

    @patch("sys.argv", ["main.py"])
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.IntradayBot1Strategy")
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.get_bot_logger")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_keyboard_interrupt(
        self, mock_stdout, mock_logger, mock_strategy_class
    ):
        """Test: Main interrumpido por usuario (Ctrl+C)."""
        mock_bot = Mock()
        mock_bot.initialize.return_value = True
        mock_bot.run_trading_cycle.side_effect = KeyboardInterrupt()
        mock_strategy_class.return_value = mock_bot

        main()

        output = mock_stdout.getvalue()
        assert "detenido" in output.lower()

    @patch("sys.argv", ["main.py"])
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.IntradayBot1Strategy")
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.get_bot_logger")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_critical_error(self, mock_stdout, mock_logger, mock_strategy_class):
        """Test: Main con error crítico."""
        mock_strategy_class.side_effect = Exception("Error crítico de prueba")

        main()

        output = mock_stdout.getvalue()
        assert "Error crítico" in output

    @patch("sys.argv", ["main.py", "--interval", "600"])
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.IntradayBot1Strategy")
    @patch("src.bots.strategies.intraday.gemini_3_pro.bot_1.main.get_bot_logger")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_continuous_mode(self, mock_stdout, mock_logger, mock_strategy_class):
        """Test: Main en modo continuo."""
        mock_bot = Mock()
        mock_bot.initialize.return_value = True
        mock_bot.run_continuous.side_effect = KeyboardInterrupt()
        mock_strategy_class.return_value = mock_bot

        main()

        mock_bot.run_continuous.assert_called_once_with(interval_seconds=600)
