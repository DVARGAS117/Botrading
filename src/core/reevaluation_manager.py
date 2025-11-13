"""
ReevaluationManager - T26
Coordinación del proceso completo de reevaluación de posiciones

Este módulo gestiona el proceso end-to-end de reevaluación de posiciones abiertas,
incluyendo la obtención de datos actualizados, consulta a IA, y ejecución de
decisiones (MANTENER/ACTUALIZAR/CERRAR).

Características:
- Reevaluación de posiciones individuales o múltiples
- Dos modos: conversación persistente vs. nueva conversación
- Extracción de datos actualizados del mercado
- Construcción de prompts de reevaluación
- Ejecución de decisiones en MT5
- Tracking de tokens y costos
- Manejo robusto de errores

Tickets relacionados: T26, T27 (decisiones), T28 (trazabilidad)

Author: Botrading Team
Date: 2025-11-13
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import uuid


class ReevaluationManagerError(Exception):
    """Excepción personalizada para errores del manager"""
    pass


class ReevaluationMode(Enum):
    """
    Modo de reevaluación
    
    Values:
        PERSISTENT_CONVERSATION: Mantiene contexto en misma conversación
        NEW_CONVERSATION: Crea nueva conversación cada vez
    """
    PERSISTENT_CONVERSATION = "persistent"
    NEW_CONVERSATION = "new"
    
    @classmethod
    def from_string(cls, value: str) -> 'ReevaluationMode':
        """
        Convierte string a ReevaluationMode
        
        Args:
            value: Modo como string
            
        Returns:
            ReevaluationMode enum correspondiente
            
        Raises:
            ValueError: Si el modo no es válido
        """
        value_lower = value.lower()
        for mode in cls:
            if mode.value == value_lower:
                return mode
        raise ValueError(
            f"Modo inválido: {value}. Válidos: {[m.value for m in cls]}"
        )


@dataclass
class ReevaluationContext:
    """
    Contexto de una reevaluación
    
    Atributos:
        position_id: ID de la posición en MT5
        symbol: Símbolo del activo (EURUSD, GBPUSD, etc.)
        magic_number: Magic number que identifica el bot
        direction: Dirección de la operación (BUY/SELL)
        entry_price: Precio de entrada original
        current_sl: Stop Loss actual
        current_tp: Take Profit actual
        current_price: Precio actual del mercado
        profit_pips: Profit/Loss actual en pips
        conversation_id: ID de conversación (para modo persistente)
        reevaluation_count: Número de reevaluaciones previas
    """
    position_id: str
    symbol: str
    magic_number: int
    direction: str  # BUY/SELL
    entry_price: float
    current_sl: float
    current_tp: float
    current_price: float
    profit_pips: float
    conversation_id: Optional[str] = None
    reevaluation_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convierte el contexto a diccionario"""
        return asdict(self)


@dataclass
class ReevaluationResult:
    """
    Resultado de una reevaluación
    
    Atributos:
        success: Si la reevaluación fue exitosa
        action_taken: Acción tomada (MANTENER/ACTUALIZAR/CERRAR)
        new_sl: Nuevo Stop Loss (si se actualizó)
        new_tp: Nuevo Take Profit (si se actualizó)
        reasoning: Razonamiento de la IA
        tokens_used: Tokens consumidos
        cost: Costo de la consulta
        error_message: Mensaje de error si falló
    """
    success: bool
    action_taken: str  # MANTENER/ACTUALIZAR/CERRAR/ERROR
    new_sl: Optional[float] = None
    new_tp: Optional[float] = None
    reasoning: str = ""
    tokens_used: int = 0
    cost: float = 0.0
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        """Convierte el resultado a diccionario"""
        return asdict(self)


class ReevaluationManager:
    """
    Gestiona el proceso completo de reevaluación
    
    Este manager coordina todos los pasos necesarios para reevaluar posiciones
    abiertas, desde la extracción de datos hasta la ejecución de decisiones.
    
    Uso básico:
        >>> manager = ReevaluationManager(
        >>>     mt5_connector=mt5_conn,
        >>>     data_extractor=extractor,
        >>>     prompt_builder=builder,
        >>>     gemini_client=client,
        >>>     response_parser=parser,
        >>>     position_manager=pos_mgr,
        >>>     mode=ReevaluationMode.PERSISTENT_CONVERSATION
        >>> )
        >>> 
        >>> # Reevaluar todas las posiciones de un bot
        >>> results = await manager.reevaluate_positions(
        >>>     bot_id="bot_1",
        >>>     magic_number=100101
        >>> )
    """
    
    def __init__(
        self,
        mt5_connector,
        data_extractor,
        prompt_builder,
        gemini_client,
        response_parser,
        position_manager,
        mode: ReevaluationMode = ReevaluationMode.PERSISTENT_CONVERSATION
    ):
        """
        Inicializa el manager
        
        Args:
            mt5_connector: Conector de MT5
            data_extractor: Extractor de datos del mercado
            prompt_builder: Constructor de prompts
            gemini_client: Cliente de Gemini API
            response_parser: Parser de respuestas de IA
            position_manager: Gestor de posiciones
            mode: Modo de reevaluación (persistent/new)
        """
        self.mt5_connector = mt5_connector
        self.data_extractor = data_extractor
        self.prompt_builder = prompt_builder
        self.gemini_client = gemini_client
        self.response_parser = response_parser
        self.position_manager = position_manager
        self.mode = mode
        
        # Diccionario de sesiones de conversación (solo para modo persistente)
        # position_id -> conversation_id
        self.conversation_sessions: Dict[str, str] = {}
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"ReevaluationManager inicializado en modo: {mode.value}"
        )
    
    async def reevaluate_positions(
        self,
        bot_id: str,
        magic_number: int
    ) -> List[ReevaluationResult]:
        """
        Reevalúa todas las posiciones abiertas de un bot
        
        Args:
            bot_id: ID del bot
            magic_number: Magic number del bot
            
        Returns:
            Lista de resultados de reevaluación
        """
        self.logger.info(
            f"Iniciando reevaluación para bot_id={bot_id}, "
            f"magic_number={magic_number}"
        )
        
        # Obtener posiciones abiertas
        positions = self.position_manager.get_open_positions(
            magic_number=magic_number
        )
        
        if not positions:
            self.logger.info("No hay posiciones abiertas para reevaluar")
            return []
        
        self.logger.info(f"Reevaluando {len(positions)} posiciones...")
        
        # Reevaluar cada posición
        results = []
        for pos_data in positions:
            try:
                # Crear contexto
                context = self._create_context_from_position(pos_data)
                
                # Reevaluar
                result = await self.reevaluate_single_position(context)
                results.append(result)
                
            except Exception as e:
                self.logger.error(
                    f"Error reevaluando posición {pos_data.get('position_id')}: {e}",
                    exc_info=True
                )
                results.append(ReevaluationResult(
                    success=False,
                    action_taken="ERROR",
                    error_message=str(e)
                ))
        
        # Estadísticas
        successful = sum(1 for r in results if r.success)
        self.logger.info(
            f"Reevaluación completada: {successful}/{len(results)} exitosas"
        )
        
        return results
    
    async def reevaluate_single_position(
        self,
        context: ReevaluationContext
    ) -> ReevaluationResult:
        """
        Reevalúa una posición específica
        
        Args:
            context: Contexto de la posición
            
        Returns:
            Resultado de la reevaluación
        """
        self.logger.debug(
            f"Reevaluando posición {context.position_id} "
            f"({context.symbol}, {context.direction})"
        )
        
        try:
            # 1. Extraer datos actualizados del mercado
            market_data = self.data_extractor.extract_current_data(
                symbol=context.symbol
            )
            
            # 2. Obtener o crear ID de conversación
            conversation_id = self._get_or_create_conversation(context.position_id)
            context.conversation_id = conversation_id
            
            # 3. Construir prompt de reevaluación
            prompt = self.prompt_builder.build_reevaluation_prompt(
                context=context,
                market_data=market_data
            )
            
            # 4. Enviar a IA
            self.logger.debug(f"Enviando prompt a IA (conversation_id={conversation_id})")
            ai_response = await self.gemini_client.send_prompt(
                prompt=prompt,
                conversation_id=conversation_id
            )
            
            if not ai_response.success:
                return ReevaluationResult(
                    success=False,
                    action_taken="ERROR",
                    error_message=f"Error de IA: {ai_response.error_message}"
                )
            
            # 5. Parsear respuesta
            parsed_decision = self.response_parser.parse_reevaluation(
                ai_response.content
            )
            
            if not parsed_decision.is_valid:
                return ReevaluationResult(
                    success=False,
                    action_taken="ERROR",
                    error_message=f"Respuesta inválida: {parsed_decision.error_message}",
                    tokens_used=ai_response.tokens_input + ai_response.tokens_output,
                    cost=ai_response.cost
                )
            
            # 6. Ejecutar acción según decisión
            action_success = self._execute_action(context, parsed_decision)
            
            if not action_success:
                return ReevaluationResult(
                    success=False,
                    action_taken=parsed_decision.decision_type.value,
                    error_message="Fallo al ejecutar acción en MT5",
                    reasoning=parsed_decision.reasoning,
                    tokens_used=ai_response.tokens_input + ai_response.tokens_output,
                    cost=ai_response.cost
                )
            
            # 7. Retornar resultado exitoso
            return ReevaluationResult(
                success=True,
                action_taken=parsed_decision.decision_type.value,
                new_sl=getattr(parsed_decision, 'new_stop_loss', None),
                new_tp=getattr(parsed_decision, 'new_take_profit', None),
                reasoning=parsed_decision.reasoning,
                tokens_used=ai_response.tokens_input + ai_response.tokens_output,
                cost=ai_response.cost
            )
            
        except Exception as e:
            self.logger.error(
                f"Error en reevaluación de {context.position_id}: {e}",
                exc_info=True
            )
            return ReevaluationResult(
                success=False,
                action_taken="ERROR",
                error_message=str(e)
            )
    
    def _create_context_from_position(self, pos_data: Dict) -> ReevaluationContext:
        """
        Crea contexto de reevaluación desde datos de posición
        
        Args:
            pos_data: Datos de la posición de MT5
            
        Returns:
            ReevaluationContext creado
        """
        return ReevaluationContext(
            position_id=pos_data['position_id'],
            symbol=pos_data['symbol'],
            magic_number=pos_data.get('magic_number', 0),
            direction=pos_data['direction'],
            entry_price=pos_data['entry_price'],
            current_sl=pos_data['current_sl'],
            current_tp=pos_data['current_tp'],
            current_price=pos_data['current_price'],
            profit_pips=pos_data['profit_pips'],
            reevaluation_count=pos_data.get('reevaluation_count', 0)
        )
    
    def _get_or_create_conversation(self, position_id: str) -> Optional[str]:
        """
        Obtiene o crea conversación según modo configurado
        
        Args:
            position_id: ID de la posición
            
        Returns:
            conversation_id si modo persistente, None si modo new
        """
        if self.mode == ReevaluationMode.NEW_CONVERSATION:
            # Modo NEW: siempre None (nueva conversación cada vez)
            return None
        
        # Modo PERSISTENT: reutilizar o crear
        if position_id not in self.conversation_sessions:
            # Crear nueva conversación
            conversation_id = f"conv_{position_id}_{uuid.uuid4().hex[:8]}"
            self.conversation_sessions[position_id] = conversation_id
            
            self.logger.debug(
                f"Nueva conversación creada: {conversation_id} "
                f"para posición {position_id}"
            )
        
        return self.conversation_sessions[position_id]
    
    def _execute_action(
        self,
        context: ReevaluationContext,
        decision
    ) -> bool:
        """
        Ejecuta la acción decidida por la IA
        
        Args:
            context: Contexto de la posición
            decision: Decisión parseada de la IA
            
        Returns:
            True si la ejecución fue exitosa
        """
        from src.core.ai_response_parser import AIDecisionType
        
        action = decision.decision_type
        
        if action == AIDecisionType.MANTENER:
            # No hacer nada, solo loggear
            self.logger.info(
                f"Posición {context.position_id}: MANTENER - {decision.reasoning}"
            )
            return True
        
        elif action == AIDecisionType.ACTUALIZAR:
            # Modificar SL/TP
            self.logger.info(
                f"Posición {context.position_id}: ACTUALIZAR - {decision.reasoning}"
            )
            
            new_sl = getattr(decision, 'new_stop_loss', None)
            new_tp = getattr(decision, 'new_take_profit', None)
            
            return self.position_manager.modify_position(
                position_id=context.position_id,
                new_sl=new_sl,
                new_tp=new_tp
            )
        
        elif action == AIDecisionType.CERRAR:
            # Cerrar posición
            self.logger.info(
                f"Posición {context.position_id}: CERRAR - {decision.reasoning}"
            )
            
            success = self.position_manager.close_position(context.position_id)
            
            # Si se cerró exitosamente, limpiar conversación
            if success and self.mode == ReevaluationMode.PERSISTENT_CONVERSATION:
                self.clear_conversation(context.position_id)
            
            return success
        
        else:
            self.logger.warning(
                f"Acción desconocida: {action}"
            )
            return False
    
    def clear_conversation(self, position_id: str):
        """
        Limpia la conversación de una posición
        
        Args:
            position_id: ID de la posición
            
        Útil cuando se cierra una posición para liberar memoria
        """
        if position_id in self.conversation_sessions:
            del self.conversation_sessions[position_id]
            self.logger.debug(f"Conversación limpiada para {position_id}")
    
    def clear_all_conversations(self):
        """Limpia todas las conversaciones"""
        count = len(self.conversation_sessions)
        self.conversation_sessions.clear()
        self.logger.info(f"{count} conversaciones limpiadas")
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del manager
        
        Returns:
            Diccionario con estadísticas actuales
        """
        return {
            'mode': self.mode.value,
            'active_conversations': len(self.conversation_sessions),
            'positions_tracked': list(self.conversation_sessions.keys())
        }
