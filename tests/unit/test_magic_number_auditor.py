"""
Tests unitarios para utilidades de auditoría de Magic Numbers - T18

Este módulo de tests cubre las funcionalidades de auditoría:
- Decodificación de Magic Numbers para análisis
- Generación de reportes de auditoría
- Análisis de distribución de operaciones
- Exportación a formatos para reportes

Metodología TDD: Red -> Green -> Refactor

Autor: Sistema Botrading
Fecha: 2025-11-11
Ticket: T18 - Decodificación de Magic Number para auditoría
"""

import pytest
from unittest.mock import Mock
from typing import List, Dict

from src.core.magic_number_generator import (
    MagicNumberGenerator,
    MagicNumberComponents,
    MagicNumberError
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
def sample_magic_numbers(generator):
    """Lista de magic numbers de ejemplo para auditoría"""
    return [
        generator.generate(1, 0, "market", 0),   # 100000
        generator.generate(1, 0, "market", 1),   # 100001
        generator.generate(1, 1, "limit", 0),    # 111000
        generator.generate(2, 3, "market", 0),   # 230000
        generator.generate(2, 3, "limit", 5),    # 231005
        generator.generate(3, 5, "market", 10),  # 350010
    ]


# ============================================================================
# TEST: DECODIFICACIÓN BATCH
# ============================================================================

class TestBatchDecoding:
    """Tests de decodificación en lote para auditoría"""
    
    def test_decode_batch_empty_list(self, generator):
        """Test: Decodificar lista vacía debe retornar lista vacía"""
        result = generator.decode_batch([])
        assert result == []
    
    def test_decode_batch_single_magic(self, generator):
        """Test: Decodificar un solo magic number"""
        magic_numbers = [100000]
        result = generator.decode_batch(magic_numbers)
        
        assert len(result) == 1
        assert result[0].bot_id == 1
        assert result[0].ia_config_id == 0
        assert result[0].order_type == "market"
    
    def test_decode_batch_multiple_magics(self, generator, sample_magic_numbers):
        """Test: Decodificar múltiples magic numbers"""
        result = generator.decode_batch(sample_magic_numbers)
        
        assert len(result) == 6
        assert all(isinstance(comp, MagicNumberComponents) for comp in result)
    
    def test_decode_batch_with_invalid_magic(self, generator):
        """Test: Decodificar batch con un magic inválido debe lanzar error"""
        magic_numbers = [100000, 12345, 200000]  # 12345 es inválido (5 dígitos)
        
        with pytest.raises(MagicNumberError):
            generator.decode_batch(magic_numbers)
    
    def test_decode_batch_preserves_order(self, generator):
        """Test: El orden de decodificación debe preservarse"""
        magic_numbers = [231000, 100000, 350000]
        result = generator.decode_batch(magic_numbers)
        
        assert result[0].bot_id == 2
        assert result[1].bot_id == 1
        assert result[2].bot_id == 3


# ============================================================================
# TEST: GENERACIÓN DE REPORTES
# ============================================================================

class TestAuditReporting:
    """Tests de generación de reportes de auditoría"""
    
    def test_generate_audit_report_basic(self, generator, sample_magic_numbers):
        """Test: Generar reporte de auditoría básico"""
        report = generator.generate_audit_report(sample_magic_numbers)
        
        assert "total_operations" in report
        assert "operations_by_bot" in report
        assert "operations_by_ia_config" in report
        assert "operations_by_type" in report
        
        assert report["total_operations"] == 6
    
    def test_generate_audit_report_by_bot(self, generator, sample_magic_numbers):
        """Test: Reporte debe agrupar correctamente por bot"""
        report = generator.generate_audit_report(sample_magic_numbers)
        
        by_bot = report["operations_by_bot"]
        assert by_bot[1] == 3  # Bot 1 tiene 3 operaciones
        assert by_bot[2] == 2  # Bot 2 tiene 2 operaciones
        assert by_bot[3] == 1  # Bot 3 tiene 1 operación
    
    def test_generate_audit_report_by_type(self, generator, sample_magic_numbers):
        """Test: Reporte debe agrupar correctamente por tipo"""
        report = generator.generate_audit_report(sample_magic_numbers)
        
        by_type = report["operations_by_type"]
        assert by_type["market"] == 4  # 4 market orders
        assert by_type["limit"] == 2   # 2 limit orders
    
    def test_generate_audit_report_by_ia_config(self, generator, sample_magic_numbers):
        """Test: Reporte debe agrupar correctamente por IA config"""
        report = generator.generate_audit_report(sample_magic_numbers)
        
        by_ia = report["operations_by_ia_config"]
        assert by_ia[0] == 2  # IA Config 0 tiene 2 operaciones
        assert by_ia[1] == 1  # IA Config 1 tiene 1 operación
        assert by_ia[3] == 2  # IA Config 3 tiene 2 operaciones
        assert by_ia[5] == 1  # IA Config 5 tiene 1 operación
    
    def test_generate_audit_report_empty_list(self, generator):
        """Test: Reporte de lista vacía"""
        report = generator.generate_audit_report([])
        
        assert report["total_operations"] == 0
        assert report["operations_by_bot"] == {}
        assert report["operations_by_type"] == {}


# ============================================================================
# TEST: ANÁLISIS DE DISTRIBUCIÓN
# ============================================================================

class TestDistributionAnalysis:
    """Tests de análisis de distribución de operaciones"""
    
    def test_get_distribution_by_bot(self, generator, sample_magic_numbers):
        """Test: Obtener distribución de operaciones por bot"""
        distribution = generator.get_distribution_by_bot(sample_magic_numbers)
        
        assert isinstance(distribution, dict)
        assert 1 in distribution
        assert 2 in distribution
        assert 3 in distribution
        
        assert distribution[1]["count"] == 3
        assert distribution[1]["percentage"] > 0
    
    def test_distribution_percentages_sum_to_100(self, generator, sample_magic_numbers):
        """Test: Los porcentajes deben sumar aproximadamente 100%"""
        distribution = generator.get_distribution_by_bot(sample_magic_numbers)
        
        total_percentage = sum(d["percentage"] for d in distribution.values())
        assert abs(total_percentage - 100.0) < 0.01  # Margen de error mínimo
    
    def test_get_distribution_by_type(self, generator, sample_magic_numbers):
        """Test: Obtener distribución por tipo de orden"""
        distribution = generator.get_distribution_by_type(sample_magic_numbers)
        
        assert "market" in distribution
        assert "limit" in distribution
        
        assert distribution["market"]["count"] == 4
        assert distribution["limit"]["count"] == 2
    
    def test_get_distribution_by_ia_config(self, generator, sample_magic_numbers):
        """Test: Obtener distribución por configuración IA"""
        distribution = generator.get_distribution_by_ia_config(sample_magic_numbers)
        
        assert 0 in distribution
        assert 3 in distribution
        assert distribution[0]["count"] == 2


# ============================================================================
# TEST: FILTRADO Y CONSULTAS
# ============================================================================

class TestFilteringAndQueries:
    """Tests de filtrado y consultas de magic numbers"""
    
    def test_filter_by_bot(self, generator, sample_magic_numbers):
        """Test: Filtrar magic numbers por bot específico"""
        filtered = generator.filter_by_bot(sample_magic_numbers, bot_id=1)
        
        assert len(filtered) == 3
        
        for magic in filtered:
            components = generator.decode(magic)
            assert components.bot_id == 1
    
    def test_filter_by_bot_no_results(self, generator, sample_magic_numbers):
        """Test: Filtrar por bot que no existe"""
        filtered = generator.filter_by_bot(sample_magic_numbers, bot_id=5)
        
        assert len(filtered) == 0
    
    def test_filter_by_type(self, generator, sample_magic_numbers):
        """Test: Filtrar por tipo de orden"""
        market_orders = generator.filter_by_type(sample_magic_numbers, order_type="market")
        limit_orders = generator.filter_by_type(sample_magic_numbers, order_type="limit")
        
        assert len(market_orders) == 4
        assert len(limit_orders) == 2
    
    def test_filter_by_ia_config(self, generator, sample_magic_numbers):
        """Test: Filtrar por configuración IA"""
        filtered = generator.filter_by_ia_config(sample_magic_numbers, ia_config_id=3)
        
        assert len(filtered) == 2
        
        for magic in filtered:
            components = generator.decode(magic)
            assert components.ia_config_id == 3
    
    def test_filter_by_multiple_criteria(self, generator, sample_magic_numbers):
        """Test: Filtrar por múltiples criterios"""
        # Filtrar bot=2 AND type=limit
        bot2_magics = generator.filter_by_bot(sample_magic_numbers, bot_id=2)
        bot2_limit = generator.filter_by_type(bot2_magics, order_type="limit")
        
        assert len(bot2_limit) == 1
        components = generator.decode(bot2_limit[0])
        assert components.bot_id == 2
        assert components.order_type == "limit"


# ============================================================================
# TEST: EXPORTACIÓN A FORMATOS
# ============================================================================

class TestExportFormats:
    """Tests de exportación a diferentes formatos"""
    
    def test_export_to_dict_list(self, generator, sample_magic_numbers):
        """Test: Exportar a lista de diccionarios"""
        result = generator.export_to_dict_list(sample_magic_numbers)
        
        assert isinstance(result, list)
        assert len(result) == 6
        
        for item in result:
            assert isinstance(item, dict)
            assert "bot_id" in item
            assert "ia_config_id" in item
            assert "order_type" in item
            assert "sequence" in item
            assert "magic_number" in item
    
    def test_export_to_csv_format(self, generator, sample_magic_numbers):
        """Test: Exportar a formato CSV (lista de listas)"""
        result = generator.export_to_csv_format(sample_magic_numbers, include_header=True)
        
        assert isinstance(result, list)
        assert len(result) == 7  # 6 datos + 1 header
        
        # Verificar header
        header = result[0]
        assert "magic_number" in header
        assert "bot_id" in header
        
        # Verificar datos
        for row in result[1:]:
            assert len(row) == 5  # 5 columnas
    
    def test_export_to_csv_no_header(self, generator, sample_magic_numbers):
        """Test: Exportar CSV sin header"""
        result = generator.export_to_csv_format(sample_magic_numbers, include_header=False)
        
        assert len(result) == 6  # Solo datos, sin header
    
    def test_export_summary_stats(self, generator, sample_magic_numbers):
        """Test: Exportar estadísticas resumen"""
        stats = generator.get_summary_statistics(sample_magic_numbers)
        
        assert "total_operations" in stats
        assert "unique_bots" in stats
        assert "unique_ia_configs" in stats
        assert "market_count" in stats
        assert "limit_count" in stats
        
        assert stats["total_operations"] == 6
        assert stats["unique_bots"] == 3  # Bots 1, 2, 3
        assert stats["market_count"] == 4
        assert stats["limit_count"] == 2


# ============================================================================
# TEST: VALIDACIÓN DE AUDITORÍA
# ============================================================================

class TestAuditValidation:
    """Tests de validación para auditoría"""
    
    def test_validate_magic_number_range(self, generator):
        """Test: Validar que un magic number está en el rango válido"""
        assert generator.is_valid_magic_number(100000) == True
        assert generator.is_valid_magic_number(591999) == True
        assert generator.is_valid_magic_number(99999) == False
        assert generator.is_valid_magic_number(600000) == False
    
    def test_validate_batch_all_valid(self, generator, sample_magic_numbers):
        """Test: Validar batch donde todos son válidos"""
        invalid = generator.get_invalid_magic_numbers(sample_magic_numbers)
        
        assert len(invalid) == 0
    
    def test_validate_batch_with_invalids(self, generator):
        """Test: Validar batch con algunos inválidos"""
        magic_numbers = [100000, 12345, 200000, 999999]
        
        invalid = generator.get_invalid_magic_numbers(magic_numbers)
        
        assert len(invalid) == 2  # 12345 y 999999
        assert 12345 in invalid
        assert 999999 in invalid
    
    def test_get_audit_summary_with_invalids(self, generator):
        """Test: Resumen de auditoría debe identificar magic numbers inválidos"""
        magic_numbers = [100000, 12345, 200000]
        
        summary = generator.get_audit_summary(magic_numbers, strict=False)
        
        assert summary["total_magic_numbers"] == 3
        assert summary["valid_count"] == 2
        assert summary["invalid_count"] == 1
        assert len(summary["invalid_magic_numbers"]) == 1


# ============================================================================
# TEST: BÚSQUEDA Y LOOKUP
# ============================================================================

class TestSearchAndLookup:
    """Tests de búsqueda y lookup de magic numbers"""
    
    def test_find_magic_numbers_for_bot(self, generator, sample_magic_numbers):
        """Test: Encontrar todos los magic numbers de un bot"""
        bot1_magics = generator.find_by_bot(sample_magic_numbers, 1)
        
        assert len(bot1_magics) == 3
        assert 100000 in bot1_magics
        assert 100001 in bot1_magics
        assert 111000 in bot1_magics
    
    def test_find_magic_numbers_for_ia_config(self, generator, sample_magic_numbers):
        """Test: Encontrar magic numbers por configuración IA"""
        ia3_magics = generator.find_by_ia_config(sample_magic_numbers, 3)
        
        assert len(ia3_magics) == 2
    
    def test_find_with_complex_query(self, generator, sample_magic_numbers):
        """Test: Búsqueda con criterios complejos"""
        # Encontrar: Bot 1 OR Bot 2, tipo Market
        results = generator.find_by_criteria(
            sample_magic_numbers,
            bot_ids=[1, 2],
            order_type="market"
        )
        
        assert len(results) == 3  # Bot1: 2 market, Bot2: 1 market
