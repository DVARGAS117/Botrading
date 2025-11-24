"""
Enhanced Magic Number Generator (v2)

Estructura de 6 dígitos:
  D1: Familia IA (1-9)
  D2: Estrategia (1-9)
  D3: Tipo (0=market, 1=limit)
  D4: Agente dentro de la estrategia (1-9)
  D5-D6: Secuencia por símbolo (00-99)

Ejemplo: 112301 -> Familia=1, Estrategia=1, Tipo=2 (inválido), Agente=3, Secuencia=01

Nota: Solo se aceptan Tipo 0 o 1. Para compatibilidad con strings se aceptan
      'market' -> 0, 'limit' -> 1 (case-insensitive).
"""

from dataclasses import dataclass
from typing import Literal


class EnhancedMagicNumberError(Exception):
    pass


OrderTypeCode = Literal[0, 1]


@dataclass
class EnhancedMagicComponents:
    family_id: int
    strategy_id: int
    order_type: str  # 'market' | 'limit'
    agent_id: int
    sequence: int  # 0-99
    magic_number: int


class EnhancedMagicNumberGenerator:
    MARKET = 0
    LIMIT = 1

    def _validate_family(self, family_id: int) -> None:
        if not isinstance(family_id, int) or not (1 <= family_id <= 9):
            raise EnhancedMagicNumberError(
                f"family_id debe estar entre 1 y 9. Recibido: {family_id}"
            )

    def _validate_strategy(self, strategy_id: int) -> None:
        if not isinstance(strategy_id, int) or not (1 <= strategy_id <= 9):
            raise EnhancedMagicNumberError(
                f"strategy_id debe estar entre 1 y 9. Recibido: {strategy_id}"
            )

    def _validate_agent(self, agent_id: int) -> None:
        if not isinstance(agent_id, int) or not (1 <= agent_id <= 9):
            raise EnhancedMagicNumberError(
                f"agent_id debe estar entre 1 y 9. Recibido: {agent_id}"
            )

    def _validate_sequence(self, sequence: int) -> None:
        if not isinstance(sequence, int) or not (0 <= sequence <= 99):
            raise EnhancedMagicNumberError(
                f"sequence debe estar entre 0 y 99. Recibido: {sequence}"
            )

    def _encode_order_type(self, order_type: int | str) -> OrderTypeCode:
        if isinstance(order_type, int):
            if order_type in (0, 1):
                return order_type  # type: ignore
            raise EnhancedMagicNumberError(
                f"order_type entero debe ser 0 (market) o 1 (limit). Recibido: {order_type}"
            )
        if not isinstance(order_type, str):
            raise EnhancedMagicNumberError(
                f"order_type debe ser int o str. Recibido: {type(order_type).__name__}"
            )
        ot = order_type.lower().strip()
        if ot == "market":
            return self.MARKET
        if ot == "limit":
            return self.LIMIT
        raise EnhancedMagicNumberError(
            f"order_type debe ser 'market' o 'limit'. Recibido: '{order_type}'"
        )

    def _decode_order_type(self, code: int) -> str:
        if code == self.MARKET:
            return "market"
        if code == self.LIMIT:
            return "limit"
        raise EnhancedMagicNumberError(
            f"Código de tipo inválido al decodificar: {code}"
        )

    def generate(
        self,
        family_id: int,
        strategy_id: int,
        order_type: int | str,
        agent_id: int,
        sequence: int = 0,
    ) -> int:
        """
        Genera un magic number v2 de 6 dígitos.
        """
        self._validate_family(family_id)
        self._validate_strategy(strategy_id)
        self._validate_agent(agent_id)
        self._validate_sequence(sequence)
        type_code = self._encode_order_type(order_type)

        # D1 D2 D3 D4 D5 D6
        # f  s  t  a  seq(2)
        magic = (
            family_id * 100000
            + strategy_id * 10000
            + type_code * 1000
            + agent_id * 100
            + sequence  # 00-99 ocupa D5-D6
        )
        if magic < 100000 or magic > 999999:
            raise EnhancedMagicNumberError(
                f"Resultado fuera de 6 dígitos: {magic}"
            )
        return magic

    def decode(self, magic_number: int) -> EnhancedMagicComponents:
        if not isinstance(magic_number, int) or not (100000 <= magic_number <= 999999):
            raise EnhancedMagicNumberError(
                f"magic_number debe tener 6 dígitos. Recibido: {magic_number}"
            )
        family = magic_number // 100000
        strategy = (magic_number // 10000) % 10
        type_code = (magic_number // 1000) % 10
        agent = (magic_number // 100) % 10
        sequence = magic_number % 100

        # Validar componentes
        self._validate_family(family)
        self._validate_strategy(strategy)
        if type_code not in (0, 1):
            raise EnhancedMagicNumberError(
                f"order_type code inválido en magic: {type_code}"
            )
        self._validate_agent(agent)
        self._validate_sequence(sequence)

        return EnhancedMagicComponents(
            family_id=family,
            strategy_id=strategy,
            order_type=self._decode_order_type(type_code),
            agent_id=agent,
            sequence=sequence,
            magic_number=magic_number,
        )

    def format(self, magic_number: int) -> str:
        if not isinstance(magic_number, int):
            raise EnhancedMagicNumberError("magic_number debe ser int")
        return f"{magic_number:06d}"
