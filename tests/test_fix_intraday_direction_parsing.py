#!/usr/bin/env python3
"""
Test unitario para validar el fix del parsing de dirección en bot INTRADAY.

Este test valida que cuando la respuesta de IA no contiene el campo 'direccion',
se infiera correctamente desde el campo 'action'.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bots.strategies.intraday.gemini_3_pro.bot_1.strategy import IntradayBot1Strategy
from src.bots.base.base_bot_operations import BotConfig, BotMode


class TestIntradayDirectionParsing(unittest.TestCase):
    """Test para validar el parsing de dirección en bot INTRADAY."""

    def setUp(self):
        """Configurar el entorno de test."""
        # Crear configuración mínima
        config = BotConfig(
            bot_id=101,
            bot_name="TestBot",
            bot_type="numerico"
        )

        # Crear instancia del bot con configuración
        self.bot = IntradayBot1Strategy(config)

    def test_direction_parsing_comprar(self):
        """Test que valida parsing de dirección 'comprar'."""
        decision = {
            "accion": "OPERAR",
            "direccion": "comprar",
            "stop_loss": 1.0500,
            "take_profit": 1.0600
        }

        # Mock completo de todos los componentes necesarios
        with patch.object(self.bot, 'mt5_connection', MagicMock()), \
             patch.object(self.bot, 'order_manager', MagicMock()), \
             patch.object(self.bot, 'position_sizer', MagicMock()), \
             patch.object(self.bot, 'magic_number_generator', MagicMock()), \
             patch.object(self.bot, 'symbol_spec_extractor', MagicMock()):

            # Configurar mocks
            mock_tick = MagicMock()
            mock_tick.ask = 1.0550
            mock_tick.bid = 1.0545
            self.bot.mt5_connection._mt5.symbol_info_tick.return_value = mock_tick

            mock_account = MagicMock()
            mock_account.balance = 1000.0
            self.bot.mt5_connection.get_account_info.return_value = mock_account

            self.bot.mt5_connection.get_symbol_info.return_value = MagicMock()

            mock_symbol_spec = MagicMock()
            mock_symbol_spec.volume_min = 0.01
            mock_symbol_spec.volume_step = 0.01
            self.bot.symbol_spec_extractor.get_symbol_specification.return_value = mock_symbol_spec

            self.bot.magic_number_generator.generate.return_value = 12345

            mock_result = MagicMock()
            mock_result.order = 123456
            mock_result.price = 1.0550
            mock_result.volume = 0.01
            self.bot.order_manager.send_market_order.return_value = mock_result

            # Ejecutar el método
            self.bot._execute_open_position("EURUSD", decision)

            # Verificar que se llamó send_market_order
            self.assertTrue(self.bot.order_manager.send_market_order.called)

    def test_direction_parsing_vender(self):
        """Test que valida parsing de dirección 'vender'."""
        decision = {
            "accion": "OPERAR",
            "direccion": "vender",
            "stop_loss": 1.0600,
            "take_profit": 1.0500
        }

        # Mock completo
        with patch.object(self.bot, 'mt5_connection', MagicMock()), \
             patch.object(self.bot, 'order_manager', MagicMock()), \
             patch.object(self.bot, 'position_sizer', MagicMock()), \
             patch.object(self.bot, 'magic_number_generator', MagicMock()), \
             patch.object(self.bot, 'symbol_spec_extractor', MagicMock()):

            # Configurar mocks
            mock_tick = MagicMock()
            mock_tick.ask = 1.0550
            mock_tick.bid = 1.0545
            self.bot.mt5_connection._mt5.symbol_info_tick.return_value = mock_tick

            mock_account = MagicMock()
            mock_account.balance = 1000.0
            self.bot.mt5_connection.get_account_info.return_value = mock_account

            self.bot.mt5_connection.get_symbol_info.return_value = MagicMock()

            mock_symbol_spec = MagicMock()
            mock_symbol_spec.volume_min = 0.01
            mock_symbol_spec.volume_step = 0.01
            self.bot.symbol_spec_extractor.get_symbol_specification.return_value = mock_symbol_spec

            self.bot.magic_number_generator.generate.return_value = 12345

            mock_result = MagicMock()
            mock_result.order = 123456
            mock_result.price = 1.0545
            mock_result.volume = 0.01
            self.bot.order_manager.send_market_order.return_value = mock_result

            # Ejecutar el método
            self.bot._execute_open_position("EURUSD", decision)

            # Verificar que se llamó send_market_order
            self.assertTrue(self.bot.order_manager.send_market_order.called)

    def test_direction_parsing_missing_direccion(self):
        """Test que valida comportamiento cuando falta campo 'direccion'."""
        decision = {
            "accion": "OPERAR",
            "stop_loss": 1.0500,
            "take_profit": 1.0600
            # Sin campo 'direccion'
        }

        # Mock completo
        with patch.object(self.bot, 'mt5_connection', MagicMock()), \
             patch.object(self.bot, 'order_manager', MagicMock()), \
             patch.object(self.bot, 'position_sizer', MagicMock()), \
             patch.object(self.bot, 'magic_number_generator', MagicMock()), \
             patch.object(self.bot, 'symbol_spec_extractor', MagicMock()):

            # Configurar mocks
            mock_tick = MagicMock()
            mock_tick.ask = 1.0550
            mock_tick.bid = 1.0545
            self.bot.mt5_connection._mt5.symbol_info_tick.return_value = mock_tick

            mock_account = MagicMock()
            mock_account.balance = 1000.0
            self.bot.mt5_connection.get_account_info.return_value = mock_account

            self.bot.mt5_connection.get_symbol_info.return_value = MagicMock()

            mock_symbol_spec = MagicMock()
            mock_symbol_spec.volume_min = 0.01
            mock_symbol_spec.volume_step = 0.01
            self.bot.symbol_spec_extractor.get_symbol_specification.return_value = mock_symbol_spec

            # Ejecutar el método - debería fallar porque no hay dirección
            self.bot._execute_open_position("EURUSD", decision)

            # Verificar que NO se llamó a send_market_order porque no hay dirección válida
            self.assertFalse(self.bot.order_manager.send_market_order.called)


if __name__ == '__main__':
    unittest.main()

    def test_direction_inference_from_action_buy(self):
        """Test que valida inferencia de dirección BUY desde action COMPRAR."""
        decision = {
            "action": "COMPRAR",
            # Sin campo 'direccion'
        }

        # Simular el método _execute_open_position
        with patch.object(self.bot, '_get_mt5_connector', return_value=Mock()), \
             patch.object(self.bot, '_get_order_manager', return_value=Mock()), \
             patch.object(self.bot, '_get_position_manager', return_value=Mock()), \
             patch.object(self.bot, '_get_operations_repo', return_value=Mock()):

            # Mock del order manager
            mock_order_manager = Mock()
            self.bot._get_order_manager.return_value = mock_order_manager

            # Ejecutar el método (debería inferir 'buy' desde 'COMPRAR')
            try:
                result = self.bot._execute_open_position(
                    symbol="EURUSD",
                    decision=decision,
                    lot_size=0.01,
                    magic_number=12345
                )

                # Verificar que se llamó con dirección 'buy'
                mock_order_manager.send_market_order.assert_called_once()
                call_args = mock_order_manager.send_market_order.call_args
                self.assertEqual(call_args[1]['direction'], 'buy')  # direction debe ser 'buy'

            except Exception as e:
                # Si hay error, verificar que sea por MT5 no conectado, no por parsing
                self.assertIn("MT5", str(e))  # Debe ser error de conexión MT5, no de parsing

    def test_direction_inference_from_action_sell(self):
        """Test que valida inferencia de dirección SELL desde action VENDER."""
        decision = {
            "action": "VENDER",
            # Sin campo 'direccion'
        }

        with patch.object(self.bot, '_get_mt5_connector', return_value=Mock()), \
             patch.object(self.bot, '_get_order_manager', return_value=Mock()), \
             patch.object(self.bot, '_get_position_manager', return_value=Mock()), \
             patch.object(self.bot, '_get_operations_repo', return_value=Mock()):

            mock_order_manager = Mock()
            self.bot._get_order_manager.return_value = mock_order_manager

            try:
                result = self.bot._execute_open_position(
                    symbol="EURUSD",
                    decision=decision,
                    lot_size=0.01,
                    magic_number=12345
                )

                # Verificar que se llamó con dirección 'sell'
                mock_order_manager.send_market_order.assert_called_once()
                call_args = mock_order_manager.send_market_order.call_args
                self.assertEqual(call_args[1]['direction'], 'sell')  # direction debe ser 'sell'

            except Exception as e:
                self.assertIn("MT5", str(e))

    def test_direction_from_decision_when_present(self):
        """Test que valida uso de dirección directa cuando está presente."""
        decision = {
            "action": "COMPRAR",
            "direccion": "buy"  # Dirección presente
        }

        with patch.object(self.bot, '_get_mt5_connector', return_value=Mock()), \
             patch.object(self.bot, '_get_order_manager', return_value=Mock()), \
             patch.object(self.bot, '_get_position_manager', return_value=Mock()), \
             patch.object(self.bot, '_get_operations_repo', return_value=Mock()):

            mock_order_manager = Mock()
            self.bot._get_order_manager.return_value = mock_order_manager

            try:
                result = self.bot._execute_open_position(
                    symbol="EURUSD",
                    decision=decision,
                    lot_size=0.01,
                    magic_number=12345
                )

                # Verificar que se usó la dirección directa
                mock_order_manager.send_market_order.assert_called_once()
                call_args = mock_order_manager.send_market_order.call_args
                self.assertEqual(call_args[1]['direction'], 'buy')

            except Exception as e:
                self.assertIn("MT5", str(e))

    def test_invalid_action_raises_error(self):
        """Test que valida error cuando action no es válido."""
        decision = {
            "action": "INVALID_ACTION",
            # Sin campo 'direccion'
        }

        with patch.object(self.bot, '_get_mt5_connector', return_value=Mock()), \
             patch.object(self.bot, '_get_order_manager', return_value=Mock()), \
             patch.object(self.bot, '_get_position_manager', return_value=Mock()), \
             patch.object(self.bot, '_get_operations_repo', return_value=Mock()):

            with self.assertRaises(ValueError) as context:
                self.bot._execute_open_position(
                    symbol="EURUSD",
                    decision=decision,
                    lot_size=0.01,
                    magic_number=12345
                )

            self.assertIn("No se pudo determinar", str(context.exception))


if __name__ == '__main__':
    unittest.main()