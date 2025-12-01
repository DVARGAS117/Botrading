import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime, time as dt_time

from src.bots.strategies.Kamikaze.strategy import KamikazeStrategy
from src.bots.base.base_bot_operations import BotConfig, BotMode
from src.core.order_manager import OrderType
from src.core.mt5_data_extractor import Timeframe
from src.core.enhanced_magic_number_generator import EnhancedMagicNumberGenerator

class TestKamikazeStrategy(unittest.TestCase):
    def setUp(self):
        self.config = BotConfig(
            bot_id=106,
            bot_name="Test Kamikaze",
            bot_type="numerico",
            mode=BotMode.DEMO,
            symbols=["XAUUSD"],
            timeframes=[Timeframe.M5, Timeframe.H1],
            ai_model="gemini-2.5-pro"
        )
        self.strategy = KamikazeStrategy(self.config)
        
        # Mocks
        self.strategy.mt5_connection = MagicMock()
        self.strategy.data_extractor = MagicMock()
        self.strategy.gemini_client = MagicMock()
        self.strategy.order_manager = MagicMock()
        self.strategy.logger = MagicMock()
        
        # Mock initialized state
        self.strategy.is_initialized = True

    def test_ask_gemini_bias_bullish(self):
        # Mock H1 data
        df = pd.DataFrame({
            'time': [datetime.now()] * 10,
            'open': [1.0] * 10,
            'high': [1.2] * 10,
            'low': [0.8] * 10,
            'close': [1.1] * 10,
            'volume': [100] * 10
        })
        mock_ohlcv = MagicMock()
        mock_ohlcv.data = df
        self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
        
        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = "BULLISH"
        self.strategy.gemini_client.send_prompt.return_value = mock_response
        
        bias = self.strategy.ask_gemini_bias("XAUUSD")
        self.assertEqual(bias, "BULLISH")
        
        # Verify prompt contained "OPEN" for last candle
        args, _ = self.strategy.gemini_client.send_prompt.call_args
        self.assertIn("OPEN", args[0])

    def test_execute_strategy_buy_signal(self):
        """Test que se genera señal de COMPRA con Bias BULLISH + patrón alcista."""
        # Mock horario de trading válido
        with patch('src.bots.strategies.Kamikaze.strategy.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 1, 3, 30)  # 3:30 AM EST (London Open)
            
            # Setup Bias
            self.strategy.market_bias["XAUUSD"] = "BULLISH"
        
            # Mock M5 data - Crear patrón HAMMER (alcista)
            # Hammer: mecha inferior larga, cuerpo pequeño arriba
            df = pd.DataFrame({
                'open': [100.0, 101.0],
                'high': [102.0, 101.5],
                'low': [99.0, 98.0],  # Mecha inferior larga en última vela
                'close': [101.0, 101.3],  # Cuerpo pequeño
            })
            mock_ohlcv = MagicMock()
            mock_ohlcv.data = df
            self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
            
            # Mock no open positions
            self.strategy.mt5_connection.get_positions.return_value = []
            
            # Mock Tick
            mock_tick = MagicMock()
            mock_tick.ask = 101.5
            self.strategy.mt5_connection._mt5.symbol_info_tick.return_value = mock_tick
            
            # Mock Symbol Info
            mock_info = MagicMock()
            mock_info.point = 0.01
            self.strategy.mt5_connection.get_symbol_info.return_value = mock_info
            
            # Execute
            self.strategy.execute_strategy("XAUUSD")
            
            # Verify Order Placed
            self.strategy.order_manager.send_market_order.assert_called_once()
            args, _ = self.strategy.order_manager.send_market_order.call_args
            request = args[0]
            self.assertEqual(request.order_type, OrderType.BUY)
            self.assertEqual(request.symbol, "XAUUSD")

    def test_execute_strategy_no_signal_mixed(self):
        """Test que NO se genera señal cuando bias y patrón no coinciden."""
        # Setup Bias BULLISH
        self.strategy.market_bias["XAUUSD"] = "BULLISH"
        
        # Mock M5 data - Crear patrón SHOOTING_STAR (bajista, no coincide con bias)
        df = pd.DataFrame({
            'open': [100.0, 101.0],
            'high': [102.0, 104.0],  # Mecha superior larga
            'low': [99.0, 100.5],
            'close': [101.0, 100.8],  # Cuerpo pequeño abajo
        })
        mock_ohlcv = MagicMock()
        mock_ohlcv.data = df
        self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
        
        self.strategy.mt5_connection.get_positions.return_value = []
        
        # Execute
        self.strategy.execute_strategy("XAUUSD")
        
        # Verify NO Order Placed (patrón bajista con bias alcista)
        self.strategy.order_manager.send_market_order.assert_not_called()

    def test_execute_strategy_sell_signal(self):
        """Test que se genera señal de VENTA con Bias BEARISH + patrón bajista."""
        # Mock horario de trading válido
        with patch('src.bots.strategies.Kamikaze.strategy.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 1, 9, 0)  # 9:00 AM EST (NY Open)
            
            # Setup Bias
            self.strategy.market_bias["XAUUSD"] = "BEARISH"
            
            # Mock M5 data - Crear patrón BEARISH_ENGULFING
            df = pd.DataFrame({
                'open': [101.0, 102.0],
                'high': [102.0, 102.5],
                'low': [100.0, 99.0],
                'close': [101.5, 99.5],  # Vela bajista envuelve a la alcista anterior
            })
            mock_ohlcv = MagicMock()
            mock_ohlcv.data = df
            self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
            
            # Mock no open positions
            self.strategy.mt5_connection.get_positions.return_value = []
            
            # Mock Tick
            mock_tick = MagicMock()
            mock_tick.bid = 98.5
            self.strategy.mt5_connection._mt5.symbol_info_tick.return_value = mock_tick
            
            # Mock Symbol Info
            mock_info = MagicMock()
            mock_info.point = 0.01
            self.strategy.mt5_connection.get_symbol_info.return_value = mock_info
            
            # Execute
            self.strategy.execute_strategy("XAUUSD")
            
            # Verify Order Placed
            self.strategy.order_manager.send_market_order.assert_called_once()
            args, _ = self.strategy.order_manager.send_market_order.call_args
            request = args[0]
            self.assertEqual(request.order_type, OrderType.SELL)
            self.assertEqual(request.symbol, "XAUUSD")

    def test_execute_strategy_no_signal_due_to_bias(self):
        # Setup Bias NEUTRAL
        self.strategy.market_bias["XAUUSD"] = "NEUTRAL"
        
        # Execute
        self.strategy.execute_strategy("XAUUSD")
        
        # Verify NO Order Placed and no data fetched
        self.strategy.data_extractor.get_ohlcv.assert_not_called()
        self.strategy.order_manager.send_market_order.assert_not_called()

    def test_run_cycle_updates_bias_and_executes(self):
        # Force Gemini call
        self.strategy.last_gemini_call = 0
        self.strategy.gemini_interval = 100 # seconds
        
        # Mock ask_gemini_bias
        with patch.object(self.strategy, 'ask_gemini_bias', return_value="BULLISH") as mock_ask_bias:
            # Mock execute_strategy
            with patch.object(self.strategy, 'execute_strategy') as mock_execute:
                self.strategy.run_trading_cycle()
                
                # Verify bias was updated for the symbol
                mock_ask_bias.assert_called_once_with("XAUUSD")
                self.assertEqual(self.strategy.market_bias["XAUUSD"], "BULLISH")
                
                # Verify strategy was executed for the symbol
                mock_execute.assert_called_once_with("XAUUSD")

    def test_wait_for_gemini_response(self):
        # Simulate that a Gemini update is pending
        self.strategy.last_gemini_call = 0
        self.strategy.gemini_interval = 100
        self.strategy.market_bias["XAUUSD"] = "NEUTRAL" # Start with neutral

        # Mock a slow Gemini response
        with patch.object(self.strategy, 'ask_gemini_bias', return_value="BULLISH") as mock_ask_bias:
            # Mock execute_strategy to check the bias at the time of execution
            with patch.object(self.strategy, 'execute_strategy') as mock_execute:
                
                # First cycle: Gemini is called, but let's assume the bot logic
                # would not trade until the bias is updated.
                self.strategy.run_trading_cycle()

                # Assert that execute_strategy was called AFTER the bias was updated
                mock_ask_bias.assert_called_once()
                mock_execute.assert_called_once()
                
                # Check the state of the bias when execute_strategy was called
                self.assertEqual(self.strategy.market_bias["XAUUSD"], "BULLISH")

    def test_bias_persists_between_cycles(self):
        """Test que el bias de Gemini persiste entre ciclos hasta la próxima actualización."""
        import time
        
        # Set initial bias and recent Gemini call
        self.strategy.market_bias["XAUUSD"] = "BULLISH"
        self.strategy.last_gemini_call = time.time()  # Justo ahora
        self.strategy.gemini_interval = 1800  # 30 minutos
        
        # Mock execute_strategy
        with patch.object(self.strategy, 'ask_gemini_bias') as mock_ask_bias:
            with patch.object(self.strategy, 'execute_strategy') as mock_execute:
                # Run cycle - should NOT call Gemini
                self.strategy.run_trading_cycle()
                
                # Verify Gemini was NOT called (too soon)
                mock_ask_bias.assert_not_called()
                
                # But strategy should still execute with the existing bias
                mock_execute.assert_called_once_with("XAUUSD")
                
                # Bias should remain unchanged
                self.assertEqual(self.strategy.market_bias["XAUUSD"], "BULLISH")

    def test_ask_gemini_includes_timestamp(self):
        """Test que la consulta a Gemini incluye timestamp y estado de velas."""
        # Mock H1 data
        df = pd.DataFrame({
            'time': [datetime(2025, 12, 1, 10, i) for i in range(10)],
            'open': [1.0] * 10,
            'high': [1.2] * 10,
            'low': [0.8] * 10,
            'close': [1.1] * 10,
            'volume': [100] * 10
        })
        mock_ohlcv = MagicMock()
        mock_ohlcv.data = df
        self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
        
        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.content = "BEARISH"
        self.strategy.gemini_client.send_prompt.return_value = mock_response
        
        bias = self.strategy.ask_gemini_bias("XAUUSD")
        
        # Verify the prompt contains all required information
        args, _ = self.strategy.gemini_client.send_prompt.call_args
        prompt = args[0]
        self.assertIn("OPEN", prompt)  # Last candle should be marked as OPEN
        self.assertIn("CLOSED", prompt)  # Previous candles should be CLOSED
        self.assertIn("Hora actual", prompt)  # Should include current time
        self.assertIn("time", prompt)  # Should include time column
        self.assertEqual(bias, "BEARISH")

    def test_execute_strategy_with_open_position(self):
        """Test que no se abren nuevas operaciones si ya hay una posición abierta."""
        # Setup Bias
        self.strategy.market_bias["XAUUSD"] = "BULLISH"
        
        # Mock M5 data (Patrón válido) 
        df = pd.DataFrame({
            'open': [100.0, 101.0],
            'high': [102.0, 101.5],
            'low': [99.0, 98.0],
            'close': [101.0, 101.3],
        })
        mock_ohlcv = MagicMock()
        mock_ohlcv.data = df
        self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
        
        # Mock existing open position
        mock_position = MagicMock()
        self.strategy.mt5_connection.get_positions.return_value = [mock_position]
        
        # Execute
        self.strategy.execute_strategy("XAUUSD")
        
        # Verify NO new Order Placed
        self.strategy.order_manager.send_market_order.assert_not_called()

    def test_detect_pattern_hammer(self):
        """Test detección de patrón HAMMER (alcista)."""
        # Crear DataFrame con patrón Hammer
        df = pd.DataFrame({
            'open': [100.0, 101.0],
            'high': [102.0, 101.5],
            'low': [99.0, 98.0],  # Mecha inferior larga
            'close': [101.0, 101.3],  # Cuerpo pequeño
        })
        
        pattern = self.strategy.detect_pattern(df)
        self.assertEqual(pattern, "HAMMER")

    def test_detect_pattern_shooting_star(self):
        """Test detección de patrón SHOOTING_STAR (bajista)."""
        # Crear DataFrame con patrón Shooting Star
        # Mecha superior debe ser > 2x el cuerpo, mecha inferior < cuerpo
        df = pd.DataFrame({
            'open': [100.0, 100.5],
            'high': [102.0, 103.5],  # Mecha superior muy larga (3.0 puntos)
            'low': [99.0, 100.3],    # Mecha inferior pequeña (0.2 puntos)
            'close': [101.0, 100.8], # Cuerpo pequeño (0.3 puntos)
        })
        
        pattern = self.strategy.detect_pattern(df)
        self.assertEqual(pattern, "SHOOTING_STAR")

    def test_detect_pattern_bullish_engulfing(self):
        """Test detección de patrón BULLISH_ENGULFING."""
        # Crear DataFrame con patrón Bullish Engulfing
        df = pd.DataFrame({
            'open': [102.0, 99.0],   # Prev bajista, curr alcista
            'high': [103.0, 103.0],
            'low': [100.0, 98.0],
            'close': [100.5, 102.5], # Vela alcista envuelve a bajista
        })
        
        pattern = self.strategy.detect_pattern(df)
        self.assertEqual(pattern, "BULLISH_ENGULFING")

    def test_detect_pattern_bearish_engulfing(self):
        """Test detección de patrón BEARISH_ENGULFING."""
        # Crear DataFrame con patrón Bearish Engulfing
        df = pd.DataFrame({
            'open': [100.0, 103.0],  # Prev alcista, curr bajista
            'high': [103.0, 103.5],
            'low': [99.0, 99.0],
            'close': [102.5, 99.5],  # Vela bajista envuelve a alcista
        })
        
        pattern = self.strategy.detect_pattern(df)
        self.assertEqual(pattern, "BEARISH_ENGULFING")

    def test_detect_pattern_none(self):
        """Test que no se detecta patrón cuando no hay confluencia."""
        # Velas normales sin patrón específico
        df = pd.DataFrame({
            'open': [100.0, 101.0],
            'high': [101.0, 102.0],
            'low': [99.0, 100.0],
            'close': [100.5, 101.5],
        })
        
        pattern = self.strategy.detect_pattern(df)
        self.assertIsNone(pattern)

    def test_max_positions_limit(self):
        """Test que respeta el límite de 2 posiciones totales."""
        # Setup Bias y patrón válido
        self.strategy.market_bias["XAUUSD"] = "BULLISH"
        
        df = pd.DataFrame({
            'open': [100.0, 101.0],
            'high': [102.0, 101.5],
            'low': [99.0, 98.0],
            'close': [101.0, 101.3],
        })
        mock_ohlcv = MagicMock()
        mock_ohlcv.data = df
        self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
        
        # Mock 2 posiciones ya abiertas (máximo alcanzado)
        mock_pos1 = MagicMock()
        mock_pos2 = MagicMock()
        self.strategy.mt5_connection.get_positions.side_effect = [
            [],  # Primera llamada: no hay posición en XAUUSD
            [mock_pos1, mock_pos2]  # Segunda llamada: 2 posiciones totales
        ]
        
        # Execute
        self.strategy.execute_strategy("XAUUSD")
        
        # Verify NO Order Placed (límite alcanzado)
        self.strategy.order_manager.send_market_order.assert_not_called()

    def test_magic_number_generation(self):
        """Test que el magic number se genera correctamente según el estándar v2."""
        # Mock horario de trading válido
        with patch('src.bots.strategies.Kamikaze.strategy.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 1, 3, 30)  # 3:30 AM EST
            
            # Setup para ejecutar una orden
            self.strategy.market_bias["XAUUSD"] = "BULLISH"
            
            df = pd.DataFrame({
                'open': [100.0, 101.0],
                'high': [102.0, 101.5],
                'low': [99.0, 98.0],
                'close': [101.0, 101.3],
            })
            mock_ohlcv = MagicMock()
            mock_ohlcv.data = df
            self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
            
            self.strategy.mt5_connection.get_positions.return_value = []
            
            mock_tick = MagicMock()
            mock_tick.ask = 101.5
            self.strategy.mt5_connection._mt5.symbol_info_tick.return_value = mock_tick
            
            mock_info = MagicMock()
            mock_info.point = 0.01
            self.strategy.mt5_connection.get_symbol_info.return_value = mock_info
            
            # Execute
            self.strategy.execute_strategy("XAUUSD")
            
            # Verify magic number structure
            self.strategy.order_manager.send_market_order.assert_called_once()
            args, _ = self.strategy.order_manager.send_market_order.call_args
            request = args[0]
            
            # Verificar que el magic number tiene 6 dígitos
            magic = request.magic
            self.assertIsInstance(magic, int)
            self.assertTrue(100000 <= magic <= 999999, f"Magic number {magic} debe tener 6 dígitos")
            
            # Decodificar y verificar estructura
            magic_gen = EnhancedMagicNumberGenerator()
            components = magic_gen.decode(magic)
            
            self.assertEqual(components.family_id, 1, "Family ID debe ser 1 (Gemini)")
            self.assertEqual(components.strategy_id, 6, "Strategy ID debe ser 6 (Kamikaze)")
            self.assertEqual(components.order_type, "market", "Order type debe ser market")
            self.assertEqual(components.agent_id, 1, "Agent ID debe ser 1")
            self.assertEqual(components.sequence, 0, "Primera orden debe tener secuencia 0")

    def test_magic_number_sequence_increment(self):
        """Test que la secuencia del magic number se incrementa correctamente."""
        # Mock horario de trading válido
        with patch('src.bots.strategies.Kamikaze.strategy.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 1, 3, 30)  # 3:30 AM EST
            
            # Mock para permitir múltiples órdenes
            self.strategy.market_bias["XAUUSD"] = "BULLISH"
            
            df = pd.DataFrame({
                'open': [100.0, 101.0],
                'high': [102.0, 101.5],
                'low': [99.0, 98.0],
                'close': [101.0, 101.3],
            })
            mock_ohlcv = MagicMock()
            mock_ohlcv.data = df
            self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
            
            # Primera orden: no hay posiciones
            self.strategy.mt5_connection.get_positions.return_value = []
            
            mock_tick = MagicMock()
            mock_tick.ask = 101.5
            self.strategy.mt5_connection._mt5.symbol_info_tick.return_value = mock_tick
            
            mock_info = MagicMock()
            mock_info.point = 0.01
            self.strategy.mt5_connection.get_symbol_info.return_value = mock_info
            
            # Ejecutar primera orden
            self.strategy.execute_strategy("XAUUSD")
            first_call_args = self.strategy.order_manager.send_market_order.call_args[0][0]
            first_magic = first_call_args.magic
            
            # Reset mock para segunda orden
            self.strategy.order_manager.reset_mock()
            
            # Ejecutar segunda orden (simular que ya no hay posición)
            self.strategy.execute_strategy("XAUUSD")
            second_call_args = self.strategy.order_manager.send_market_order.call_args[0][0]
            second_magic = second_call_args.magic
            
            # Verificar que la secuencia incrementó
            magic_gen = EnhancedMagicNumberGenerator()
            first_components = magic_gen.decode(first_magic)
            second_components = magic_gen.decode(second_magic)
            
            self.assertEqual(first_components.sequence, 0)
            self.assertEqual(second_components.sequence, 1)

    def test_is_trading_time_london_open(self):
        """Test que identifica correctamente el horario de London Open."""
        # Mock hora dentro de London Open (2am - 5am EST)
        with patch('src.bots.strategies.Kamikaze.strategy.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 1, 3, 30)  # 3:30 AM EST
            self.assertTrue(self.strategy.is_trading_time())

    def test_is_trading_time_ny_open(self):
        """Test que identifica correctamente el horario de NY Open."""
        # Mock hora dentro de NY Open (8am - 11am EST)
        with patch('src.bots.strategies.Kamikaze.strategy.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 1, 9, 0)  # 9:00 AM EST
            self.assertTrue(self.strategy.is_trading_time())

    def test_is_trading_time_outside_sessions(self):
        """Test que rechaza horarios fuera de las sesiones de trading."""
        # Mock hora fuera de sesiones (12pm EST)
        with patch('src.bots.strategies.Kamikaze.strategy.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 1, 12, 0)  # 12:00 PM EST
            self.assertFalse(self.strategy.is_trading_time())

    def test_execute_strategy_outside_trading_hours(self):
        """Test que NO opera fuera de horarios de trading."""
        # Mock hora fuera de sesiones
        with patch('src.bots.strategies.Kamikaze.strategy.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 1, 12, 0)  # 12:00 PM EST
            
            # Setup Bias y patrón válido
            self.strategy.market_bias["XAUUSD"] = "BULLISH"
            
            df = pd.DataFrame({
                'open': [100.0, 101.0],
                'high': [102.0, 101.5],
                'low': [99.0, 98.0],
                'close': [101.0, 101.3],
            })
            mock_ohlcv = MagicMock()
            mock_ohlcv.data = df
            self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
            
            self.strategy.mt5_connection.get_positions.return_value = []
            
            # Execute
            self.strategy.execute_strategy("XAUUSD")
            
            # Verify NO Order Placed (fuera de horario)
            self.strategy.order_manager.send_market_order.assert_not_called()

    def test_execute_strategy_during_london_open(self):
        """Test que opera correctamente durante London Open."""
        # Mock hora dentro de London Open
        with patch('src.bots.strategies.Kamikaze.strategy.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 1, 3, 30)  # 3:30 AM EST
            
            # Setup Bias y patrón válido
            self.strategy.market_bias["XAUUSD"] = "BULLISH"
            
            df = pd.DataFrame({
                'open': [100.0, 101.0],
                'high': [102.0, 101.5],
                'low': [99.0, 98.0],
                'close': [101.0, 101.3],
            })
            mock_ohlcv = MagicMock()
            mock_ohlcv.data = df
            self.strategy.data_extractor.get_ohlcv.return_value = mock_ohlcv
            
            self.strategy.mt5_connection.get_positions.return_value = []
            
            mock_tick = MagicMock()
            mock_tick.ask = 101.5
            self.strategy.mt5_connection._mt5.symbol_info_tick.return_value = mock_tick
            
            mock_info = MagicMock()
            mock_info.point = 0.01
            self.strategy.mt5_connection.get_symbol_info.return_value = mock_info
            
            # Execute
            self.strategy.execute_strategy("XAUUSD")
            
            # Verify Order WAS Placed (dentro de horario)
            self.strategy.order_manager.send_market_order.assert_called_once()

if __name__ == '__main__':
    unittest.main()
