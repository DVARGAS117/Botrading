"""
SequenceManager: calcula la siguiente secuencia (00-99) por símbolo para magic v2.

Clave: (family_id, strategy_id, agent_variant_id, symbol)

Fuente de verdad: operaciones abiertas en BD (operations_repo). Si no hay datos,
retorna 0. Si hay varias, retorna (max_seq + 1) % 100 para evitar colisiones.
"""

from typing import Tuple

from src.core.enhanced_magic_number_generator import EnhancedMagicNumberGenerator, EnhancedMagicNumberError
from src.core.operations_repository import OperationsRepository, OperationStatus


class SequenceManager:
    def __init__(self) -> None:
        # Cache ahora global por (family_id, strategy_id, agent_variant_id)
        # Eliminamos el símbolo para evitar que la misma secuencia 00 genere
        # magic numbers idénticos en distintos símbolos (colisión en BD UNIQUE).
        self._cache: dict[Tuple[int, int, int], int] = {}
        self._decoder = EnhancedMagicNumberGenerator()

    def next_sequence(
        self,
        repo: OperationsRepository,
        family_id: int,
        strategy_id: int,
        agent_variant_id: int,
        symbol: str,  # mantenido para interfaz pero ya no afecta la secuencia
    ) -> int:
        key = (family_id, strategy_id, agent_variant_id)

        # Si está en caché, incrementar y wrap
        if key in self._cache:
            self._cache[key] = (self._cache[key] + 1) % 100
            return self._cache[key]

        # Consultar BD por TODAS las operaciones (abiertas y cerradas) para esta combinación
        # evitando colisiones cross-símbolo al iniciar todas en secuencia 00.
        all_ops = repo.list_operations()  # sin filtros
        max_seq = -1
        for op in all_ops:
            try:
                comp = self._decoder.decode(int(op.magic_number))
            except Exception:
                continue
            if (
                comp.family_id == family_id
                and comp.strategy_id == strategy_id
                and comp.agent_id == agent_variant_id
            ):
                if comp.sequence > max_seq:
                    max_seq = comp.sequence

        next_seq = (max_seq + 1) % 100
        self._cache[key] = next_seq
        return next_seq
