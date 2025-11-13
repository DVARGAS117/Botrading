"""
ReevaluationIntegration - T26
Integración del sistema de reevaluación periódica con BotInstance

Este módulo conecta el ReevaluationScheduler y ReevaluationManager con
la instancia del bot, coordinando el proceso completo de reevaluación
periódica de posiciones abiertas.

Características:
- Inicialización automática de componentes
- Ejecución periódica cada N minutos
- Respeto de ventana de trading
- Filtrado de posiciones por bot/magic number
- Gestión de modos por bot (persistent/new conversation)
- Tracking de estadísticas y costos
- Manejo robusto de errores

Flujo de integración:
1. Bot inicia → Se crea ReevaluationIntegration
2. Cada N minutos → Scheduler determina si reevaluar
3. Obtener posiciones abiertas del bot
4. Filtrar posiciones que necesitan reevaluación
5. Manager ejecuta reevaluación (datos → IA → decisión)
6. Marcar posiciones reevaluadas en scheduler
7. Persistir resultados y estadísticas

Tickets relacionados: T26, T3 (bot instance), T4 (posiciones)

Author: Botrading Team
Date: 2025-11-13
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from src.core.reevaluation_scheduler import ReevaluationScheduler, ReevaluationConfig
from src.core.reevaluation_manager import (
    ReevaluationManager,
    ReevaluationMode,
    ReevaluationResult
)


class ReevaluationIntegrationError(Exception):
    """Excepción personalizada para errores de integración"""
    pass


@dataclass
class IntegrationConfig:
    """
    Configuración de la integración de reevaluación
    
    Atributos:
        enabled: Si la reevaluación está habilitada
        interval_minutes: Intervalo entre reevaluaciones
        mode: Modo de conversación (persistent/new)
        trading_window: Configuración de ventana de trading
        limits: Límites de reevaluaciones y costos
    """
    enabled: bool = True
    interval_minutes: int = 10
    mode: str = "persistent"
    trading_window: Optional[Dict[str, Any]] = None
    limits: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.trading_window is None:
            self.trading_window = {
                "timezone": "America/Lima",
                "start": "06:00",
                "end": "13:00",
                "days": ["MON", "TUE", "WED", "THU", "FRI"]
            }
        
        if self.limits is None:
            self.limits = {
                "max_reevaluations_per_position": 50,
                "max_cost_per_position_usd": 2.0
            }


class ReevaluationIntegration:
    """
    Integra el sistema de reevaluación periódica con BotInstance
    
    Esta clase orquesta el scheduler y manager para ejecutar
    reevaluaciones periódicas automáticas de posiciones abiertas
    del bot.
    
    Example:
        >>> # Crear integración para un bot
        >>> integration = ReevaluationIntegration(
        >>>     bot_id=1,
        >>>     bot_name="ScalpingBot",
        >>>     config=integration_config,
        >>>     mt5_connector=mt5_conn,
        >>>     data_extractor=extractor,
        >>>     prompt_builder=builder,
        >>>     gemini_client=client,
        >>>     response_parser=parser,
        >>>     position_manager=pos_mgr
        >>> )
        >>> 
        >>> # Iniciar reevaluación periódica
        >>> await integration.start()
        >>> 
        >>> # Detener
        >>> await integration.stop()
    """
    
    def __init__(
        self,
        bot_id: int,
        bot_name: str,
        magic_number: int,
        config: IntegrationConfig,
        mt5_connector,
        data_extractor,
        prompt_builder,
        gemini_client,
        response_parser,
        position_manager,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa la integración de reevaluación
        
        Args:
            bot_id: ID del bot (1-5)
            bot_name: Nombre del bot
            magic_number: Magic number del bot para filtrar posiciones
            config: Configuración de integración
            mt5_connector: Conector MT5
            data_extractor: Extractor de datos de mercado
            prompt_builder: Constructor de prompts
            gemini_client: Cliente Gemini
            response_parser: Parser de respuestas IA
            position_manager: Gestor de posiciones
            logger: Logger opcional
        """
        self.bot_id = bot_id
        self.bot_name = bot_name
        self.magic_number = magic_number
        self.config = config
        
        # Logger
        if logger is None:
            self.logger = logging.getLogger(
                f"ReevaluationIntegration.{bot_name}"
            )
            self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger
        
        # Componentes externos
        self.mt5_connector = mt5_connector
        self.position_manager = position_manager
        
        # Inicializar scheduler
        self._initialize_scheduler()
        
        # Inicializar manager
        self._initialize_manager(
            data_extractor,
            prompt_builder,
            gemini_client,
            response_parser
        )
        
        # Control de ejecución
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Estadísticas
        self._stats = {
            "total_cycles": 0,
            "total_positions_evaluated": 0,
            "successful_reevaluations": 0,
            "failed_reevaluations": 0,
            "total_cost_usd": 0.0,
            "total_tokens": 0,
            "started_at": None,
            "last_cycle_at": None
        }
        
        self.logger.info(
            f"ReevaluationIntegration inicializada para {bot_name} "
            f"(interval={config.interval_minutes}min, mode={config.mode})"
        )
    
    def _initialize_scheduler(self) -> None:
        """Inicializa el scheduler de reevaluación"""
        tw = self.config.trading_window or {}
        
        scheduler_config = ReevaluationConfig(
            interval_minutes=self.config.interval_minutes,
            enabled=self.config.enabled,
            timezone=tw.get("timezone", "America/Lima"),
            trading_window_start=tw.get("start", "06:00"),
            trading_window_end=tw.get("end", "13:00")
        )
        
        self.scheduler = ReevaluationScheduler(scheduler_config)
        self.logger.debug("Scheduler inicializado")
    
    def _initialize_manager(
        self,
        data_extractor,
        prompt_builder,
        gemini_client,
        response_parser
    ) -> None:
        """Inicializa el manager de reevaluación"""
        mode = ReevaluationMode.from_string(self.config.mode)
        
        self.manager = ReevaluationManager(
            mode=mode,
            mt5_connector=self.mt5_connector,
            data_extractor=data_extractor,
            prompt_builder=prompt_builder,
            gemini_client=gemini_client,
            response_parser=response_parser,
            position_manager=self.position_manager
        )
        self.logger.debug(f"Manager inicializado (mode={mode.value})")
    
    async def start(self) -> bool:
        """
        Inicia el proceso de reevaluación periódica
        
        Returns:
            True si se inició correctamente, False en caso contrario
        """
        if not self.config.enabled:
            self.logger.warning("Reevaluación deshabilitada en configuración")
            return False
        
        if self._running:
            self.logger.warning("Reevaluación ya está en ejecución")
            return False
        
        self.logger.info(
            f"Iniciando reevaluación periódica para {self.bot_name}..."
        )
        
        self._running = True
        self._stats["started_at"] = datetime.now()
        
        # Crear tarea asíncrona
        self._task = asyncio.create_task(self._reevaluation_loop())
        
        self.logger.info("Reevaluación periódica iniciada")
        return True
    
    async def stop(self) -> bool:
        """
        Detiene el proceso de reevaluación periódica
        
        Returns:
            True si se detuvo correctamente, False en caso contrario
        """
        if not self._running:
            self.logger.warning("Reevaluación no está en ejecución")
            return False
        
        self.logger.info(
            f"Deteniendo reevaluación periódica para {self.bot_name}..."
        )
        
        self._running = False
        
        # Cancelar tarea si existe
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Reevaluación periódica detenida")
        return True
    
    async def _reevaluation_loop(self) -> None:
        """
        Loop principal de reevaluación periódica
        
        Ejecuta el ciclo de reevaluación cada N minutos
        mientras el bot esté en ejecución
        """
        interval_seconds = self.config.interval_minutes * 60
        
        self.logger.info(
            f"Loop de reevaluación iniciado (cada {self.config.interval_minutes} min)"
        )
        
        while self._running:
            try:
                # Esperar intervalo
                await asyncio.sleep(interval_seconds)
                
                # Ejecutar ciclo de reevaluación
                await self._execute_reevaluation_cycle()
                
            except asyncio.CancelledError:
                self.logger.info("Loop de reevaluación cancelado")
                break
            
            except Exception as e:
                self.logger.error(
                    f"Error en loop de reevaluación: {e}",
                    exc_info=True
                )
                # Continuar ejecutando a pesar del error
                continue
    
    async def _execute_reevaluation_cycle(self) -> None:
        """
        Ejecuta un ciclo completo de reevaluación
        
        Pasos:
        1. Verificar ventana de trading
        2. Obtener posiciones abiertas
        3. Filtrar posiciones que necesitan reevaluación
        4. Ejecutar reevaluación
        5. Marcar posiciones reevaluadas
        6. Actualizar estadísticas
        """
        cycle_start = datetime.now()
        self._stats["total_cycles"] += 1
        
        self.logger.info(
            f"Iniciando ciclo de reevaluación #{self._stats['total_cycles']}"
        )
        
        try:
            # 1. Verificar ventana de trading
            if not self.scheduler.is_within_trading_window():
                self.logger.info(
                    "Fuera de ventana de trading, saltando reevaluación"
                )
                return
            
            # 2. Obtener posiciones abiertas del bot
            open_positions = await self._get_open_positions()
            
            if not open_positions:
                self.logger.debug("No hay posiciones abiertas para reevaluar")
                return
            
            self.logger.info(
                f"Encontradas {len(open_positions)} posiciones abiertas"
            )
            
            # 3. Filtrar posiciones que necesitan reevaluación
            positions_to_reevaluate = [
                pos for pos in open_positions
                if self.scheduler.should_reevaluate(pos["ticket"])
            ]
            
            if not positions_to_reevaluate:
                self.logger.debug(
                    "Ninguna posición necesita reevaluación en este momento"
                )
                return
            
            self.logger.info(
                f"{len(positions_to_reevaluate)} posiciones necesitan reevaluación"
            )
            
            # 4. Ejecutar reevaluación
            results = await self.manager.reevaluate_positions(
                bot_id=str(self.bot_id),
                magic_number=self.magic_number
            )
            
            # 5. Procesar resultados
            await self._process_results(results, positions_to_reevaluate)
            
            # 6. Actualizar estadísticas
            self._stats["last_cycle_at"] = cycle_start
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.logger.info(
                f"Ciclo de reevaluación completado en {cycle_duration:.2f}s"
            )
        
        except Exception as e:
            self.logger.error(
                f"Error en ciclo de reevaluación: {e}",
                exc_info=True
            )
            raise
    
    async def _get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Obtiene posiciones abiertas del bot
        
        Returns:
            Lista de posiciones abiertas filtradas por magic number
        """
        try:
            # Usar position_manager para obtener posiciones
            all_positions = self.position_manager.get_positions()
            
            # Filtrar por magic number del bot
            bot_positions = [
                pos for pos in all_positions
                if pos.get("magic") == self.magic_number
            ]
            
            return bot_positions
        
        except Exception as e:
            self.logger.error(f"Error obteniendo posiciones: {e}")
            return []
    
    async def _process_results(
        self,
        results: List[ReevaluationResult],
        positions: List[Dict[str, Any]]
    ) -> None:
        """
        Procesa los resultados de reevaluación
        
        Args:
            results: Resultados de las reevaluaciones
            positions: Posiciones reevaluadas
        """
        for i, result in enumerate(results):
            position = positions[i]
            position_id = position["ticket"]
            
            # Actualizar estadísticas
            self._stats["total_positions_evaluated"] += 1
            self._stats["total_tokens"] += result.tokens_used
            self._stats["total_cost_usd"] += result.cost
            
            if result.success:
                # Marcar como reevaluada en scheduler
                self.scheduler.mark_reevaluated(position_id)
                
                self._stats["successful_reevaluations"] += 1
                
                self.logger.info(
                    f"Posición {position_id} reevaluada: "
                    f"{result.action_taken} "
                    f"(tokens={result.tokens_used}, cost=${result.cost:.4f})"
                )
            else:
                self._stats["failed_reevaluations"] += 1
                
                self.logger.warning(
                    f"Fallo en reevaluación de posición {position_id}: "
                    f"{result.error_message}"
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de reevaluación
        
        Returns:
            Diccionario con estadísticas completas
        """
        # Combinar stats de integración con scheduler y manager
        integration_stats = self._stats.copy()
        
        # Agregar stats del scheduler
        scheduler_stats = self.scheduler.get_stats()
        integration_stats["scheduler"] = scheduler_stats
        
        # Agregar stats del manager
        manager_stats = self.manager.get_stats()
        integration_stats["manager"] = manager_stats
        
        # Calcular métricas adicionales
        if integration_stats["total_positions_evaluated"] > 0:
            integration_stats["success_rate"] = (
                integration_stats["successful_reevaluations"] /
                integration_stats["total_positions_evaluated"]
            ) * 100
            
            integration_stats["avg_cost_per_reevaluation"] = (
                integration_stats["total_cost_usd"] /
                integration_stats["total_positions_evaluated"]
            )
        else:
            integration_stats["success_rate"] = 0.0
            integration_stats["avg_cost_per_reevaluation"] = 0.0
        
        return integration_stats
    
    def is_running(self) -> bool:
        """
        Verifica si la reevaluación está en ejecución
        
        Returns:
            True si está ejecutándose, False en caso contrario
        """
        return self._running
    
    def __repr__(self) -> str:
        """Representación del objeto"""
        return (
            f"<ReevaluationIntegration(bot={self.bot_name}, "
            f"interval={self.config.interval_minutes}min, "
            f"mode={self.config.mode}, running={self._running})>"
        )
