"""Estrategia del Bot 1 (VWAP Gemini 3 Pro)."""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from src.bots.base.base_bot_operations import BaseBotOperations, BotConfig
from src.core.prompt_builder import PromptBuilder
from src.core.vwap_response_parser import VWAPResponseParser
from src.core.vwap_prompt_builder import MarketContext


class Bot1Strategy(BaseBotOperations):
    """Estrategia de Bot 1 - Numérico Baseline."""

    prompt_builder: Optional[PromptBuilder] = None
    response_parser: Optional[VWAPResponseParser] = None

    def __init__(self, config: BotConfig) -> None:
        super().__init__(config)

        self.logger.info(
            "Bot 1 (Numérico Baseline) inicializado",
            extra={
                "strategy": "VWAP Methodology",
                "data_type": "numeric_only",
            },
        )

    def prepare_data_for_ai(
        self,
        symbol: str,
        indicators: Dict,
        or_data: Optional[Any],
        market_context: MarketContext,
        ohlcv_data: Optional[Dict] = None,
    ) -> Tuple[str, str]:
        """Prepara datos numéricos para enviar a la IA."""

        if not self.prompt_builder:
            raise ValueError("prompt_builder no inicializado")

        system_prompt, user_prompt = self.prompt_builder.build_vwap_methodology_prompt(
            indicators=indicators,
            or_data=or_data,
            market_context=market_context,
            ohlcv_data=ohlcv_data,
        )

        self.logger.debug(
            f"Prompts preparados para {symbol}",
            extra={
                "symbol": symbol,
                "market_context": market_context.value,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
            },
        )

        return system_prompt, user_prompt

    def parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parsea la respuesta de la IA usando VWAPResponseParser."""

        if not self.response_parser:
            raise ValueError("response_parser no inicializado")

        parsed_response = self.response_parser.parse_response(response_text)

        is_valid = True
        validation_errors: list[str] = []
        if hasattr(self.response_parser, "validate_response"):
            try:
                is_valid, validation_errors = self.response_parser.validate_response(
                    parsed_response
                )
            except Exception:  # pragma: no cover - fallback tests
                is_valid = True
                validation_errors = []

        if not is_valid:
            self.logger.warning(
                "Respuesta IA tiene errores de validación",
                extra={"validation_errors": validation_errors},
            )
            return {
                "accion": "NO_OPERAR",
                "razonamiento": "Errores de validación: "
                + ", ".join(validation_errors),
            }

        if hasattr(self.response_parser, "convert_to_bot_format"):
            bot_decision = self.response_parser.convert_to_bot_format(parsed_response)
        else:
            bot_decision = {
                "accion": "NO_OPERAR",
                "razonamiento": "convert_to_bot_format ausente",
            }

        self.logger.info(
            "✅ Respuesta IA parseada correctamente",
            extra={
                "accion": bot_decision.get("accion"),
                "direccion": bot_decision.get("direccion"),
            },
        )
        return bot_decision

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento del bot."""

        return {
            "bot_id": self.config.bot_id,
            "bot_name": self.config.bot_name,
            "current_pnl_r": self.current_pnl_r,
            "trades_today": self.trades_today,
            "is_trading_hours": self.is_trading_hours(),
            "should_stop": self.should_stop_trading_today(),
            "market_context": self.get_market_context().value,
            "timestamp": datetime.now().isoformat(),
        }
