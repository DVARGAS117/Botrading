#!/usr/bin/env python3
"""
Script de prueba completa para el bot de trading INTRADAY.

Ejecuta todas las operaciones posibles:
1. Abrir posición
2. Actualizar Stop Loss
3. Actualizar Take Profit
4. Cerrar posición

Este script modifica temporalmente la lógica del bot para testing.
"""

import sys
import os
import time
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.mt5_connector import MT5Connector, BrokerConfig
from src.core.order_manager import OrderManager, OrderType, OrderRequest
from src.core.symbol_spec_extractor import SymbolSpecificationExtractor
from src.core.magic_number_generator import MagicNumberGenerator


class TradingOperationsTester:
    """Clase para probar todas las operaciones de trading"""

    def __init__(self):
        self.mt5_connector = None
        self.order_manager = None
        self.symbol_spec_extractor = None
        self.magic_generator = None
        self.test_ticket = None

    def initialize_mt5(self):
        """Inicializar conexión MT5"""
        print("🔌 Inicializando conexión MT5...")
        
        # Configurar credenciales desde el archivo
        config = BrokerConfig(
            account_id="61409006",
            password="V3n3zu3l@",
            server="Pepperstone-Demo"
        )
        
        self.mt5_connector = MT5Connector(config)
        self.mt5_connector.verify_connection()

        self.order_manager = OrderManager(self.mt5_connector)
        self.symbol_spec_extractor = SymbolSpecificationExtractor(self.mt5_connector)
        self.magic_generator = MagicNumberGenerator()

        print("✅ MT5 inicializado correctamente")

    def test_open_position(self, symbol: str = "EURUSD"):
        """Prueba apertura de posición"""
        print(f"🧪 PASO 1: Abriendo posición BUY de prueba en {symbol}")

        try:
            # Obtener precio actual
            tick = self.mt5_connector._mt5.symbol_info_tick(symbol)
            if tick is None:
                raise Exception(f"No se pudo obtener tick para {symbol}")

            entry_price = tick.ask
            stop_loss = entry_price - 0.0010  # SL 10 pips por debajo
            take_profit = entry_price + 0.0020  # TP 20 pips por encima

            # Especificaciones del símbolo
            symbol_spec = self.symbol_spec_extractor.get_symbol_specification(symbol)

            # Magic number
            magic = self.magic_generator.generate(
                bot_id=1,
                ia_config_id=0,
                order_type="market"
            )

            # Crear orden BUY
            request = OrderRequest(
                symbol=symbol,
                order_type=OrderType.BUY,
                volume=max(symbol_spec.volume_min, symbol_spec.volume_step),
                price=float(entry_price),
                sl=float(stop_loss),
                tp=float(take_profit),
                magic=magic,
                comment="TEST-OPEN"
            )

            result = self.order_manager.send_market_order(request)
            self.test_ticket = result.order

            print("🧪 ✅ Posición BUY abierta exitosamente")
            print(f"   📊 Ticket: {result.order}")
            print(f"   📊 Precio: {result.price}")
            print(f"   📊 Volumen: {result.volume}")
            print(f"   📊 SL: {stop_loss}")
            print(f"   📊 TP: {take_profit}")

            return True

        except Exception as e:
            print(f"🧪 ❌ Error al abrir posición: {e}")
            return False

    def test_update_sl(self, symbol: str = "EURUSD"):
        """Prueba actualización de Stop Loss"""
        print(f"🧪 PASO 2: Actualizando Stop Loss en {symbol}")

        if not self.test_ticket:
            print("🧪 ❌ No hay ticket de posición para actualizar")
            return False

        try:
            # Obtener posición actual
            positions = self.mt5_connector._mt5.positions_get(symbol=symbol)
            if not positions:
                raise Exception(f"No se encontró posición abierta para {symbol}")

            position = positions[0]
            ticket = position.ticket

            # Nuevo SL: mover 5 pips más cerca del precio actual
            current_price = position.price_current
            new_sl = current_price - 0.0005  # 5 pips más cerca

            print(f"🧪 📊 Ajustando SL de posición #{ticket}")
            print(f"   📊 SL anterior: {position.sl}")
            print(f"   📊 SL nuevo: {new_sl}")
            print(f"   📊 Precio actual: {current_price}")

            # Modificar posición en MT5
            self.order_manager.modify_position(
                ticket=int(ticket),
                sl=float(new_sl),
                tp=position.tp  # Mantener TP actual
            )

            print(f"🧪 ✅ Stop Loss actualizado exitosamente para posición #{ticket}")

            return True

        except Exception as e:
            print(f"🧪 ❌ Error al actualizar SL: {e}")
            return False

    def test_update_tp(self, symbol: str = "EURUSD"):
        """Prueba actualización de Take Profit"""
        print(f"🧪 PASO 3: Actualizando Take Profit en {symbol}")

        if not self.test_ticket:
            print("🧪 ❌ No hay ticket de posición para actualizar")
            return False

        try:
            # Obtener posición actual
            positions = self.mt5_connector._mt5.positions_get(symbol=symbol)
            if not positions:
                raise Exception(f"No se encontró posición abierta para {symbol}")

            position = positions[0]
            ticket = position.ticket

            # Nuevo TP: mover 15 pips más lejos
            current_price = position.price_current
            new_tp = current_price + 0.0015  # 15 pips más lejos

            print(f"🧪 📊 Ajustando TP de posición #{ticket}")
            print(f"   📊 TP anterior: {position.tp}")
            print(f"   📊 TP nuevo: {new_tp}")
            print(f"   📊 Precio actual: {current_price}")

            # Modificar posición en MT5
            self.order_manager.modify_position(
                ticket=int(ticket),
                sl=position.sl,  # Mantener SL actual
                tp=float(new_tp)
            )

            print(f"🧪 ✅ Take Profit actualizado exitosamente para posición #{ticket}")

            return True

        except Exception as e:
            print(f"🧪 ❌ Error al actualizar TP: {e}")
            return False

    def test_close_position(self, symbol: str = "EURUSD"):
        """Prueba cierre de posición"""
        print(f"🧪 PASO 4: Cerrando posición de prueba en {symbol}")

        if not self.test_ticket:
            print("🧪 ❌ No hay ticket de posición para cerrar")
            return False

        try:
            # Obtener posición actual
            positions = self.mt5_connector._mt5.positions_get(symbol=symbol)
            if not positions:
                raise Exception(f"No se encontró posición abierta para {symbol}")

            position = positions[0]
            ticket = position.ticket

            print(f"🧪 📊 Cerrando posición #{ticket}")
            print(f"   📊 Profit: {position.profit}")
            print(f"   📊 Precio apertura: {position.price_open}")
            print(f"   📊 Precio actual: {position.price_current}")

            # Cerrar posición
            self.order_manager.close_position(ticket=int(ticket))

            print(f"🧪 ✅ Posición #{ticket} cerrada exitosamente")

            return True

        except Exception as e:
            print(f"🧪 ❌ Error al cerrar posición: {e}")
            return False

    def run_full_test(self, symbol: str = "EURUSD"):
        """Ejecuta la prueba completa de todas las operaciones"""
        print("=" * 60)
        print("🧪 TEST COMPLETO DE OPERACIONES DE TRADING")
        print("=" * 60)

        try:
            # Inicializar MT5
            self.initialize_mt5()

            # Ejecutar pruebas paso a paso
            steps = [
                ("Apertura de Posición", self.test_open_position, symbol),
                ("Actualización SL", self.test_update_sl, symbol),
                ("Actualización TP", self.test_update_tp, symbol),
                ("Cierre de Posición", self.test_close_position, symbol),
            ]

            results = []
            for step_name, step_func, *args in steps:
                print(f"\n🔄 Ejecutando: {step_name}")
                success = step_func(*args)
                results.append((step_name, success))

                if success:
                    print(f"✅ {step_name}: EXITOSA")
                else:
                    print(f"❌ {step_name}: FALLIDA")

                # Pequeña pausa entre operaciones
                if step_name != "Cierre de Posición":
                    print("⏳ Esperando 3 segundos...")
                    time.sleep(3)

            # Resumen final
            print("\n" + "=" * 60)
            print("📊 RESUMEN DEL TEST")
            print("=" * 60)

            successful = sum(1 for _, success in results if success)
            total = len(results)

            for step_name, success in results:
                status = "✅" if success else "❌"
                print(f"{status} {step_name}")

            print(f"\n🎯 Resultado: {successful}/{total} operaciones exitosas")

            if successful == total:
                print("🎉 ¡TEST COMPLETADO EXITOSAMENTE!")
                print("Todas las operaciones de trading funcionan correctamente.")
            else:
                print("⚠️  Algunas operaciones fallaron. Revisar logs para detalles.")

        except Exception as e:
            print(f"💥 Error crítico durante el test: {e}")
        finally:
            # Limpiar conexiones
            if self.mt5_connector:
                self.mt5_connector.disconnect()
                print("🔌 Conexión MT5 cerrada")


def main():
    """Función principal del script de test"""
    print("🤖 Iniciando Test Completo de Operaciones de Trading")
    print("Cuenta DEMO - Dinero ficticio")
    print()

    # Crear y ejecutar tester
    tester = TradingOperationsTester()
    tester.run_full_test("EURUSD")


if __name__ == "__main__":
    main()