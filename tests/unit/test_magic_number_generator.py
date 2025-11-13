"""
Tests unitarios para MagicNumberGenerator - T17

Este módulo de tests cubre todas las funcionalidades del MagicNumberGenerator:
- Generación de Magic Numbers con estructura [Bot][IA][Tipo]
- Validación de parámetros (bot_id, ia_config_id, order_type)
- Unicidad de Magic Numbers
- Formato de 6 dígitos
- Decodificación de Magic Numbers (preparación para T18)

Metodología TDD: Red -> Green -> Refactor

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T17 - Generación de Magic Number único con estructura
"""

import pytest
from unittest.mock import Mock
from typing import Set

from src.core.magic_number_generator import (
    MagicNumberGenerator,
    MagicNumberError,
    InvalidBotIdError,
    InvalidIAConfigIdError,
    InvalidOrderTypeError,
    MagicNumberComponents
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_logger():
    """Mock del logger"""
    return Mock()


@pytest.fixture
def generator(mock_logger):
    """Generator con logger mockeado"""
    return MagicNumberGenerator(logger=mock_logger)


@pytest.fixture
def generator_no_logger():
    """Generator sin logger"""
    return MagicNumberGenerator()


# ============================================================================
# TEST: INICIALIZACIÓN
# ============================================================================

class TestMagicNumberGeneratorInitialization:
    """Tests de inicialización del MagicNumberGenerator"""
    
    def test_init_with_logger(self, mock_logger):
        """Test: Inicialización con logger personalizado"""
        generator = MagicNumberGenerator(logger=mock_logger)
        assert generator is not None
        assert generator.logger == mock_logger
    
    def test_init_without_logger(self):
        """Test: Inicialización sin logger crea uno por defecto"""
        generator = MagicNumberGenerator()
        assert generator is not None
        assert generator.logger is not None
    
    def test_generator_starts_with_empty_history(self, generator):
        """Test: El generator inicia sin historial de magic numbers"""
        # Los Magic Numbers no se almacenan en historial por defecto
        # Son calculados de forma determinista
        assert generator is not None


# ============================================================================
# TEST: GENERACIÓN DE MAGIC NUMBER
# ============================================================================

class TestGenerateMagicNumber:
    """Tests de generación de Magic Numbers"""
    
    def test_generate_valid_magic_number_bot1_ia0_market(self, generator):
        """Test: Generar Magic Number válido para Bot 1, IA 0, Market"""
        magic = generator.generate(bot_id=1, ia_config_id=0, order_type="market")
        assert magic == 100000  # Bot=1, IA=0, Type=0, Sequence=000
    
    def test_generate_valid_magic_number_bot2_ia3_limit(self, generator):
        """Test: Generar Magic Number válido para Bot 2, IA 3, Limit"""
        magic = generator.generate(bot_id=2, ia_config_id=3, order_type="limit")
        assert magic == 231000  # Bot=2, IA=3, Type=1, Sequence=000
    
    def test_generate_valid_magic_number_bot5_ia9_market(self, generator):
        """Test: Generar Magic Number válido para Bot 5, IA 9, Market"""
        magic = generator.generate(bot_id=5, ia_config_id=9, order_type="market")
        assert magic == 590000  # Bot=5, IA=9, Type=0, Sequence=000
    
    def test_magic_number_is_six_digits(self, generator):
        """Test: Magic Number debe tener exactamente 6 dígitos"""
        magic = generator.generate(bot_id=1, ia_config_id=0, order_type="market")
        assert 100000 <= magic <= 999999
        assert len(str(magic)) == 6
    
    def test_magic_number_different_for_different_order_types(self, generator):
        """Test: Magic Numbers diferentes para Market vs Limit"""
        magic_market = generator.generate(bot_id=1, ia_config_id=0, order_type="market")
        magic_limit = generator.generate(bot_id=1, ia_config_id=0, order_type="limit")
        assert magic_market != magic_limit
    
    def test_magic_number_different_for_different_bots(self, generator):
        """Test: Magic Numbers diferentes para diferentes bots"""
        magic_bot1 = generator.generate(bot_id=1, ia_config_id=0, order_type="market")
        magic_bot2 = generator.generate(bot_id=2, ia_config_id=0, order_type="market")
        assert magic_bot1 != magic_bot2
    
    def test_magic_number_different_for_different_ia_configs(self, generator):
        """Test: Magic Numbers diferentes para diferentes configs IA"""
        magic_ia0 = generator.generate(bot_id=1, ia_config_id=0, order_type="market")
        magic_ia1 = generator.generate(bot_id=1, ia_config_id=1, order_type="market")
        assert magic_ia0 != magic_ia1


# ============================================================================
# TEST: VALIDACIÓN DE PARÁMETROS
# ============================================================================

class TestParameterValidation:
    """Tests de validación de parámetros"""
    
    def test_invalid_bot_id_zero(self, generator):
        """Test: bot_id=0 debe lanzar InvalidBotIdError"""
        with pytest.raises(InvalidBotIdError) as exc_info:
            generator.generate(bot_id=0, ia_config_id=0, order_type="market")
        assert "bot_id debe estar entre 1 y 5" in str(exc_info.value)
    
    def test_invalid_bot_id_negative(self, generator):
        """Test: bot_id negativo debe lanzar InvalidBotIdError"""
        with pytest.raises(InvalidBotIdError) as exc_info:
            generator.generate(bot_id=-1, ia_config_id=0, order_type="market")
        assert "bot_id debe estar entre 1 y 5" in str(exc_info.value)
    
    def test_invalid_bot_id_too_high(self, generator):
        """Test: bot_id > 5 debe lanzar InvalidBotIdError"""
        with pytest.raises(InvalidBotIdError) as exc_info:
            generator.generate(bot_id=6, ia_config_id=0, order_type="market")
        assert "bot_id debe estar entre 1 y 5" in str(exc_info.value)
    
    def test_invalid_ia_config_id_negative(self, generator):
        """Test: ia_config_id negativo debe lanzar InvalidIAConfigIdError"""
        with pytest.raises(InvalidIAConfigIdError) as exc_info:
            generator.generate(bot_id=1, ia_config_id=-1, order_type="market")
        assert "ia_config_id debe estar entre 0 y 9" in str(exc_info.value)
    
    def test_invalid_ia_config_id_too_high(self, generator):
        """Test: ia_config_id > 9 debe lanzar InvalidIAConfigIdError"""
        with pytest.raises(InvalidIAConfigIdError) as exc_info:
            generator.generate(bot_id=1, ia_config_id=10, order_type="market")
        assert "ia_config_id debe estar entre 0 y 9" in str(exc_info.value)
    
    def test_invalid_order_type_empty(self, generator):
        """Test: order_type vacío debe lanzar InvalidOrderTypeError"""
        with pytest.raises(InvalidOrderTypeError) as exc_info:
            generator.generate(bot_id=1, ia_config_id=0, order_type="")
        assert "order_type debe ser 'market' o 'limit'" in str(exc_info.value)
    
    def test_invalid_order_type_unknown(self, generator):
        """Test: order_type desconocido debe lanzar InvalidOrderTypeError"""
        with pytest.raises(InvalidOrderTypeError) as exc_info:
            generator.generate(bot_id=1, ia_config_id=0, order_type="stop")
        assert "order_type debe ser 'market' o 'limit'" in str(exc_info.value)
    
    def test_order_type_case_insensitive(self, generator):
        """Test: order_type debe aceptar mayúsculas/minúsculas"""
        magic_lower = generator.generate(bot_id=1, ia_config_id=0, order_type="market")
        magic_upper = generator.generate(bot_id=1, ia_config_id=0, order_type="MARKET")
        magic_mixed = generator.generate(bot_id=1, ia_config_id=0, order_type="Market")
        assert magic_lower == magic_upper == magic_mixed


# ============================================================================
# TEST: SECUENCIAS (Para múltiples operaciones del mismo bot/IA/tipo)
# ============================================================================

class TestSequenceGeneration:
    """Tests de generación de secuencias para múltiples operaciones"""
    
    def test_generate_with_sequence_number(self, generator):
        """Test: Generar con número de secuencia específico"""
        magic = generator.generate(bot_id=1, ia_config_id=0, order_type="market", sequence=5)
        assert magic == 100005  # Bot=1, IA=0, Type=0, Sequence=005
    
    def test_sequence_increments_correctly(self, generator):
        """Test: Secuencias incrementan correctamente"""
        magic1 = generator.generate(bot_id=1, ia_config_id=0, order_type="market", sequence=0)
        magic2 = generator.generate(bot_id=1, ia_config_id=0, order_type="market", sequence=1)
        magic3 = generator.generate(bot_id=1, ia_config_id=0, order_type="market", sequence=2)
        
        assert magic1 == 100000
        assert magic2 == 100001
        assert magic3 == 100002
    
    def test_sequence_max_value(self, generator):
        """Test: Secuencia máxima de 999"""
        magic = generator.generate(bot_id=1, ia_config_id=0, order_type="market", sequence=999)
        assert magic == 100999
    
    def test_sequence_overflow_raises_error(self, generator):
        """Test: Secuencia > 999 debe lanzar error"""
        with pytest.raises(MagicNumberError) as exc_info:
            generator.generate(bot_id=1, ia_config_id=0, order_type="market", sequence=1000)
        assert "sequence debe estar entre 0 y 999" in str(exc_info.value)
    
    def test_sequence_negative_raises_error(self, generator):
        """Test: Secuencia negativa debe lanzar error"""
        with pytest.raises(MagicNumberError) as exc_info:
            generator.generate(bot_id=1, ia_config_id=0, order_type="market", sequence=-1)
        assert "sequence debe estar entre 0 y 999" in str(exc_info.value)


# ============================================================================
# TEST: DECODIFICACIÓN (Preparación para T18)
# ============================================================================

class TestDecodeMagicNumber:
    """Tests de decodificación de Magic Numbers"""
    
    def test_decode_valid_magic_number(self, generator):
        """Test: Decodificar Magic Number válido"""
        magic = 121456  # Bot=1, IA=2, Type=1 (limit), Seq=456
        components = generator.decode(magic)
        
        assert isinstance(components, MagicNumberComponents)
        assert components.bot_id == 1
        assert components.ia_config_id == 2
        assert components.order_type == "limit"
        assert components.sequence == 456
    
    def test_decode_market_order(self, generator):
        """Test: Decodificar orden Market"""
        magic = 100005  # Bot=1, IA=0, Type=0 (market), Seq=005
        components = generator.decode(magic)
        
        assert components.bot_id == 1
        assert components.ia_config_id == 0
        assert components.order_type == "market"
        assert components.sequence == 5
    
    def test_decode_limit_order(self, generator):
        """Test: Decodificar orden Limit"""
        magic = 231000  # Bot=2, IA=3, Type=1 (limit), Seq=000
        components = generator.decode(magic)
        
        assert components.bot_id == 2
        assert components.ia_config_id == 3
        assert components.order_type == "limit"
        assert components.sequence == 0
    
    def test_decode_invalid_magic_number_too_short(self, generator):
        """Test: Magic Number muy corto debe lanzar error"""
        with pytest.raises(MagicNumberError) as exc_info:
            generator.decode(12345)  # Solo 5 dígitos
        assert "Magic Number debe tener exactamente 6 dígitos" in str(exc_info.value)
    
    def test_decode_invalid_magic_number_too_long(self, generator):
        """Test: Magic Number muy largo debe lanzar error"""
        with pytest.raises(MagicNumberError) as exc_info:
            generator.decode(1234567)  # 7 dígitos
        assert "Magic Number debe tener exactamente 6 dígitos" in str(exc_info.value)
    
    def test_decode_invalid_bot_id_in_magic(self, generator):
        """Test: bot_id inválido en magic number debe lanzar error"""
        with pytest.raises(InvalidBotIdError) as exc_info:
            generator.decode(600000)  # Bot=6 (inválido)
        assert "bot_id debe estar entre 1 y 5" in str(exc_info.value)
    
    def test_encode_decode_roundtrip(self, generator):
        """Test: Encode -> Decode debe retornar los mismos componentes"""
        # Generar
        original_magic = generator.generate(
            bot_id=3, 
            ia_config_id=7, 
            order_type="limit", 
            sequence=123
        )
        
        # Decodificar
        components = generator.decode(original_magic)
        
        # Verificar
        assert components.bot_id == 3
        assert components.ia_config_id == 7
        assert components.order_type == "limit"
        assert components.sequence == 123
        
        # Re-generar con componentes decodificados
        reconstructed_magic = generator.generate(
            bot_id=components.bot_id,
            ia_config_id=components.ia_config_id,
            order_type=components.order_type,
            sequence=components.sequence
        )
        
        assert reconstructed_magic == original_magic


# ============================================================================
# TEST: UNICIDAD Y COLISIONES
# ============================================================================

class TestUniqueness:
    """Tests de unicidad de Magic Numbers"""
    
    def test_all_possible_combinations_are_unique(self, generator):
        """Test: Todas las combinaciones posibles generan Magic Numbers únicos"""
        magic_numbers: Set[int] = set()
        
        # Generar todas las combinaciones
        for bot_id in range(1, 6):  # 1-5
            for ia_config_id in range(0, 10):  # 0-9
                for order_type in ["market", "limit"]:
                    magic = generator.generate(bot_id, ia_config_id, order_type, sequence=0)
                    
                    # Verificar unicidad
                    assert magic not in magic_numbers, (
                        f"Colisión detectada: bot={bot_id}, ia={ia_config_id}, "
                        f"type={order_type} generó {magic} (ya existente)"
                    )
                    
                    magic_numbers.add(magic)
        
        # Verificar que se generaron 5 * 10 * 2 = 100 magic numbers únicos
        assert len(magic_numbers) == 100
    
    def test_sequences_are_unique_within_combination(self, generator):
        """Test: Diferentes secuencias generan Magic Numbers únicos"""
        magic_numbers: Set[int] = set()
        
        # Generar 100 secuencias para la misma combinación
        for sequence in range(100):
            magic = generator.generate(
                bot_id=1, 
                ia_config_id=0, 
                order_type="market", 
                sequence=sequence
            )
            
            assert magic not in magic_numbers
            magic_numbers.add(magic)
        
        assert len(magic_numbers) == 100


# ============================================================================
# TEST: FORMATO Y REPRESENTACIÓN
# ============================================================================

class TestFormatting:
    """Tests de formato y representación"""
    
    def test_format_as_string(self, generator):
        """Test: Formatear como string con ceros leading"""
        magic = 100005
        formatted = generator.format_magic_number(magic)
        assert formatted == "100005"
    
    def test_components_to_dict(self, generator):
        """Test: Convertir componentes a diccionario"""
        magic = 231456
        components = generator.decode(magic)
        components_dict = components.to_dict()
        
        assert components_dict == {
            "bot_id": 2,
            "ia_config_id": 3,
            "order_type": "limit",
            "sequence": 456,
            "magic_number": 231456
        }
    
    def test_components_string_representation(self, generator):
        """Test: Representación en string de componentes"""
        magic = 100000
        components = generator.decode(magic)
        components_str = str(components)
        
        assert "Bot: 1" in components_str
        assert "IA Config: 0" in components_str
        assert "Order Type: market" in components_str
        assert "Sequence: 0" in components_str
        assert "MagicNumber: 100000" in components_str


# ============================================================================
# TEST: CASOS EDGE
# ============================================================================

class TestEdgeCases:
    """Tests de casos edge"""
    
    def test_minimum_valid_magic_number(self, generator):
        """Test: Magic Number mínimo válido"""
        magic = generator.generate(bot_id=1, ia_config_id=0, order_type="market", sequence=0)
        assert magic == 100000
    
    def test_maximum_valid_magic_number(self, generator):
        """Test: Magic Number máximo válido"""
        magic = generator.generate(bot_id=5, ia_config_id=9, order_type="limit", sequence=999)
        assert magic == 591999
    
    def test_all_bots_can_generate(self, generator):
        """Test: Todos los bots (1-5) pueden generar Magic Numbers"""
        for bot_id in range(1, 6):
            magic = generator.generate(bot_id=bot_id, ia_config_id=0, order_type="market")
            assert isinstance(magic, int)
            assert 100000 <= magic <= 999999
    
    def test_all_ia_configs_can_generate(self, generator):
        """Test: Todas las configs IA (0-9) pueden generar Magic Numbers"""
        for ia_config_id in range(0, 10):
            magic = generator.generate(bot_id=1, ia_config_id=ia_config_id, order_type="market")
            assert isinstance(magic, int)
            assert 100000 <= magic <= 999999
