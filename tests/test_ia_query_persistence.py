import os
from pathlib import Path

from src.bots.base.base_bot_operations import BaseBotOperations, BotConfig, BotMode
from src.core.ia_query_repository import IAQueryRepository
from src.core.gemini_client import GeminiResponse
from src.core.mt5_data_extractor import Timeframe


class DummyAIClient:
    def send_prompt(self, prompt: str):
        # Simular respuesta JSON mínima usada por parse_ai_response
        return GeminiResponse(
            success=True,
            content='{"accion":"OPERAR","direccion":"buy"}',
            tokens_input=150,
            tokens_output=50,
            cost=0.002
        )


class DummyBot(BaseBotOperations):
    def prepare_data_for_ai(self, symbol, indicators, or_data, market_context, ohlcv_data=None):
        return "SYSTEM", "USER"

    def parse_ai_response(self, response_text: str):
        # Parse mínimo sin validar estructura compleja
        if 'OPERAR' in response_text:
            return {"accion": "OPERAR", "direccion": "comprar"}
        return {"accion": "NO_OPERAR"}


class StubOHLCV:
    def __init__(self):
        self.data = []


class StubDataExtractor:
    def get_ohlcv(self, symbol: str, timeframe: Timeframe, count: int):
        return StubOHLCV()


class StubIndicatorCalculator:
    def calculate_indicators_for_timeframe(self, ohlcv_data):
        return {}


class StubOpeningRangeCalculator:
    def calculate_opening_range(self, data):
        return None


def test_ai_query_persistence(tmp_path):
    db_path = Path("data/test_ia_queries.db")
    if db_path.exists():
        os.remove(db_path)

    config = BotConfig(
        bot_id=1,
        bot_name="TestBot",
        bot_type="numerico",
        mode=BotMode.DEMO,
        symbols=["EURUSD"],
        timeframes=[Timeframe.M1],
        trading_hours=("00:00", "23:59"),
        ai_model="gemini-3-pro-preview",
        save_prompts=False
    )

    bot = DummyBot(config)
    # Inicialización mínima sin MT5 real
    bot.is_initialized = True
    bot.data_extractor = StubDataExtractor()
    bot.indicator_calculator = StubIndicatorCalculator()
    bot.or_calculator = StubOpeningRangeCalculator()
    bot.ai_client = DummyAIClient()
    bot.ia_query_repo = IAQueryRepository(db_path)

    bot.run_trading_cycle()

    queries = bot.ia_query_repo.get_queries_by_bot(bot_id=1)
    assert len(queries) == 1, "Debe haberse persistido una consulta IA"
    q = queries[0]
    assert q.tokens_input == 150
    assert q.tokens_output == 50
    assert q.cost_usd == 0.002
    assert q.action_decided == "OPERAR"

    # Limpieza
    bot.ia_query_repo.close()
    if db_path.exists():
        os.remove(db_path)
