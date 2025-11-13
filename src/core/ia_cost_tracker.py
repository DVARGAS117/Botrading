"""
Módulo de registro de costos y tokens para consultas IA.

Este módulo implementa la funcionalidad del Ticket T11: Registro de tokens y costo
por consulta, para medir la eficiencia económica de cada metodología.

Autor: Sistema Botrading
Fecha: 2025-11-13
Ticket: T11 - Registro de tokens y costo por consulta
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any


class IACostTracker:
    """
    Rastreador de costos y tokens para consultas de IA.

    Registra automáticamente tokens de entrada/salida y costos asociados
    a cada consulta de IA, permitiendo análisis de eficiencia económica.

    Attributes:
        log_dir (Path): Directorio donde se almacenan los logs
        log_file (Path): Archivo JSON donde se persisten los datos
    """

    def __init__(self, log_dir: str = "logs"):
        """
        Inicializa el rastreador de costos.

        Args:
            log_dir: Directorio para almacenar los logs de costos
        """
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "ia_costs.json"
        self._ensure_log_directory()

    def _ensure_log_directory(self):
        """Asegura que el directorio de logs existe."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def register_query(
        self,
        operation_id: str,
        tokens_input: int,
        tokens_output: int,
        cost: float,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Registra una consulta de IA con sus costos y tokens.

        Args:
            operation_id: Identificador de la operación (ej: 'eval_123', 'reeval_456')
            tokens_input: Número de tokens en la entrada
            tokens_output: Número de tokens en la salida
            cost: Costo de la consulta en USD
            timestamp: Timestamp de la consulta (por defecto: ahora)

        Raises:
            ValueError: Si los valores numéricos no son positivos
            TypeError: Si los tipos de parámetros son incorrectos
        """
        # Validación de tipos
        if not isinstance(operation_id, str):
            raise TypeError("operation_id debe ser string")
        if not isinstance(tokens_input, int):
            raise TypeError("tokens_input debe ser int")
        if not isinstance(tokens_output, int):
            raise TypeError("tokens_output debe ser int")
        if not isinstance(cost, (int, float)):
            raise TypeError("cost debe ser int o float")

        # Validación de valores
        if tokens_input < 0:
            raise ValueError("tokens_input debe ser >= 0")
        if tokens_output < 0:
            raise ValueError("tokens_output debe ser >= 0")
        if cost < 0:
            raise ValueError("cost debe ser >= 0")

        # Usar timestamp actual si no se proporciona
        if timestamp is None:
            timestamp = datetime.now()

        # Crear registro
        record = {
            "operation_id": operation_id,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "cost": float(cost),
            "timestamp": timestamp.isoformat()
        }

        # Cargar datos existentes
        existing_data = self._load_existing_data()

        # Agregar nuevo registro
        existing_data.append(record)

        # Guardar
        self._save_data(existing_data)

    def get_queries_for_operation(self, operation_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las consultas para una operación específica.

        Args:
            operation_id: Identificador de la operación

        Returns:
            Lista de consultas para la operación
        """
        all_queries = self.get_all_queries()
        return [q for q in all_queries if q["operation_id"] == operation_id]

    def get_all_queries(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las consultas registradas.

        Returns:
            Lista de todas las consultas, ordenadas por timestamp descendente
        """
        data = self._load_existing_data()

        # Ordenar por timestamp descendente (más reciente primero)
        try:
            data.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]), reverse=True)
        except (KeyError, ValueError):
            # Si hay problemas con timestamps, mantener orden original
            pass

        return data

    def get_total_cost(self) -> float:
        """
        Calcula el costo total de todas las consultas.

        Returns:
            Costo total en USD
        """
        queries = self.get_all_queries()
        return sum(q.get("cost", 0.0) for q in queries)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calcula estadísticas generales de uso.

        Returns:
            Diccionario con estadísticas:
            - total_queries: Número total de consultas
            - total_cost: Costo total
            - total_tokens_input: Total tokens de entrada
            - total_tokens_output: Total tokens de salida
            - unique_operations: Número de operaciones únicas
        """
        queries = self.get_all_queries()

        if not queries:
            return {
                "total_queries": 0,
                "total_cost": 0.0,
                "total_tokens_input": 0,
                "total_tokens_output": 0,
                "unique_operations": 0
            }

        total_cost = sum(q.get("cost", 0.0) for q in queries)
        total_input = sum(q.get("tokens_input", 0) for q in queries)
        total_output = sum(q.get("tokens_output", 0) for q in queries)
        unique_ops = len(set(q.get("operation_id", "") for q in queries))

        return {
            "total_queries": len(queries),
            "total_cost": round(total_cost, 6),
            "total_tokens_input": total_input,
            "total_tokens_output": total_output,
            "unique_operations": unique_ops
        }

    def _load_existing_data(self) -> List[Dict[str, Any]]:
        """
        Carga datos existentes desde el archivo JSON.

        Returns:
            Lista de registros existentes, o lista vacía si no existe archivo
        """
        if not self.log_file.exists():
            return []

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    # Si no es lista, asumir que es un error y retornar vacío
                    return []
        except (json.JSONDecodeError, IOError):
            # Archivo corrupto, retornar vacío
            return []

    def _save_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Guarda datos en el archivo JSON.

        Args:
            data: Lista de registros a guardar
        """
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)