import pytest

from src.core.enhanced_magic_number_generator import (
    EnhancedMagicNumberGenerator,
    EnhancedMagicNumberError,
)


def test_generate_and_decode_market_seq0():
    gen = EnhancedMagicNumberGenerator()
    magic = gen.generate(family_id=1, strategy_id=1, order_type="market", agent_id=2, sequence=0)
    assert isinstance(magic, int)
    assert 100000 <= magic <= 999999

    comp = gen.decode(magic)
    assert comp.family_id == 1
    assert comp.strategy_id == 1
    assert comp.order_type == "market"
    assert comp.agent_id == 2
    assert comp.sequence == 0


def test_generate_limit_seq99_and_format():
    gen = EnhancedMagicNumberGenerator()
    magic = gen.generate(family_id=1, strategy_id=1, order_type="limit", agent_id=3, sequence=99)
    # Últimos dos dígitos deben ser 99
    assert magic % 100 == 99
    # D3 (tipo) debe ser 1
    assert (magic // 1000) % 10 == 1
    # Formato con ceros a la izquierda
    assert len(gen.format(magic)) == 6

    comp = gen.decode(magic)
    assert comp.order_type == "limit"
    assert comp.sequence == 99


@pytest.mark.parametrize("bad_family", [0, 10, -1, "a"]) 
def test_invalid_family_raises(bad_family):
    gen = EnhancedMagicNumberGenerator()
    with pytest.raises(EnhancedMagicNumberError):
        gen.generate(family_id=bad_family, strategy_id=1, order_type="market", agent_id=2, sequence=0)


@pytest.mark.parametrize("bad_order", [2, -1, "x", None])
def test_invalid_order_type_raises(bad_order):
    gen = EnhancedMagicNumberGenerator()
    with pytest.raises(EnhancedMagicNumberError):
        gen.generate(family_id=1, strategy_id=1, order_type=bad_order, agent_id=2, sequence=0)


@pytest.mark.parametrize("bad_seq", [-1, 100, 1000])
def test_invalid_sequence_raises(bad_seq):
    gen = EnhancedMagicNumberGenerator()
    with pytest.raises(EnhancedMagicNumberError):
        gen.generate(family_id=1, strategy_id=1, order_type="market", agent_id=2, sequence=bad_seq)
