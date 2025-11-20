"""
Gestor de sesiones de trading por símbolo y horario.

Maneja la lógica de horarios permitidos para cada par de divisas
según las sesiones de mercado (Londres, NY, Asia, etc.).

Autor: Sistema Botrading
Fecha: 2025-11-19
"""

import json
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging


class TradingSessionManager:
    """Gestiona horarios de trading por símbolo según sesiones de mercado."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Inicializa el gestor de sesiones.
        
        Args:
            config_path: Ruta al archivo trading_sessions.json
                        Si es None, usa config/trading_sessions.json
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "trading_sessions.json"
        
        self.config_path = config_path
        self.sessions: Dict = {}
        self.global_rules: Dict = {}
        self.logger = logging.getLogger(__name__)
        
        self._load_config()
    
    def _load_config(self) -> None:
        """Carga la configuración de sesiones desde archivo JSON."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.sessions = data.get('sessions', {})
            self.global_rules = data.get('global_rules', {})
            
            self.logger.info(
                f"Configuración de sesiones cargada: {len(self.sessions)} sesiones",
                extra={'config_path': str(self.config_path)}
            )
        except FileNotFoundError:
            self.logger.warning(
                f"Archivo de sesiones no encontrado: {self.config_path}. "
                "Usando configuración por defecto (siempre permitido)"
            )
            self._set_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(
                f"Error parseando trading_sessions.json: {e}. "
                "Usando configuración por defecto"
            )
            self._set_default_config()
    
    def _set_default_config(self) -> None:
        """Configura valores por defecto (permite todo)."""
        self.sessions = {}
        self.global_rules = {
            "allow_reevaluation_outside_hours": True
        }
    
    def is_symbol_tradeable(
        self,
        symbol: str,
        current_time: Optional[datetime] = None,
        has_open_position: bool = False
    ) -> Tuple[bool, str]:
        """Verifica si un símbolo puede ser operado en el horario actual.
        
        Args:
            symbol: Símbolo a verificar (ej: "EURUSD")
            current_time: Hora actual (si es None, usa datetime.now())
            has_open_position: Si tiene posición abierta (permite reevaluación)
        
        Returns:
            Tupla (es_tradeable, razon)
            - es_tradeable: True si puede consultar a la IA
            - razon: Descripción de por qué sí/no
        """
        if current_time is None:
            current_time = datetime.now()
        
        current_time_obj = current_time.time()
        
        # Buscar sesión activa para este símbolo
        active_session = self._get_active_session(symbol, current_time_obj)
        
        if active_session:
            # Está en horario permitido
            session_name = active_session['name']
            return True, f"Sesión activa: {session_name}"
        
        # No está en horario permitido
        # Verificar si puede reevaluar posición abierta
        allow_reevaluation = self.global_rules.get('allow_reevaluation_outside_hours', True)
        
        if has_open_position and allow_reevaluation:
            return True, "Fuera de horario pero tiene posición abierta (reevaluación permitida)"
        
        # No puede operar
        next_session = self._get_next_session(symbol, current_time_obj)
        if next_session:
            return False, f"Fuera de horario. Próxima sesión: {next_session['name']} a las {next_session['start']}"
        else:
            return False, f"No hay sesiones configuradas para {symbol}"
    
    def _get_active_session(self, symbol: str, current_time: time) -> Optional[Dict]:
        """Obtiene la sesión activa para un símbolo en el horario dado.
        
        Returns:
            Dict con datos de la sesión si está activa, None si no
        """
        for session_name, session_data in self.sessions.items():
            # Verificar horario primero
            start_str = session_data.get('start', '00:00')
            end_str = session_data.get('end', '23:59')
            
            start_time = self._parse_time(start_str)
            end_time = self._parse_time(end_str)
            
            if not self._is_time_in_range(current_time, start_time, end_time):
                continue
            
            # Verificar si el símbolo está en la whitelist de esta sesión
            session_symbols = session_data.get('symbols', [])
            
            # Si la lista está vacía, significa "ninguno permitido" (como dead_zone)
            # Si la lista no existe o tiene al menos un símbolo, verificar membership
            if len(session_symbols) == 0:
                # Lista vacía = ningún símbolo permitido en esta sesión
                continue
            
            # Verificar si el símbolo está en la lista permitida
            if symbol not in session_symbols:
                continue
            
            # Símbolo permitido en esta sesión
            return {
                'name': session_name,
                'start': start_str,
                'end': end_str,
                'symbols': session_symbols,
                'strategies': session_data.get('strategies', []),
                'risk_level': session_data.get('risk_level', 'medio')
            }
        
        return None
    
    def _get_next_session(self, symbol: str, current_time: time) -> Optional[Dict]:
        """Obtiene la próxima sesión disponible para un símbolo.
        
        Returns:
            Dict con datos de la próxima sesión, None si no hay
        """
        next_sessions = []
        
        for session_name, session_data in self.sessions.items():
            session_symbols = session_data.get('symbols', [])
            
            # Si la lista está vacía, ningún símbolo permitido
            if len(session_symbols) == 0:
                continue
            
            # Si el símbolo no está en la lista, saltar
            if symbol not in session_symbols:
                continue
            
            start_str = session_data.get('start', '00:00')
            start_time = self._parse_time(start_str)
            
            # Si la sesión empieza después de la hora actual
            if start_time > current_time:
                next_sessions.append({
                    'name': session_name,
                    'start': start_str,
                    'start_time': start_time
                })
        
        if next_sessions:
            # Ordenar por hora de inicio y retornar la más próxima
            next_sessions.sort(key=lambda x: x['start_time'])
            return next_sessions[0]
        
        return None
    
    def _is_time_in_range(
        self,
        current: time,
        start: time,
        end: time
    ) -> bool:
        """Verifica si una hora está dentro de un rango.
        
        Maneja correctamente rangos que cruzan medianoche (ej: 22:00 - 02:00)
        """
        if start <= end:
            # Rango normal (ej: 08:00 - 17:00)
            return start <= current <= end
        else:
            # Rango que cruza medianoche (ej: 22:00 - 02:00)
            return current >= start or current <= end
    
    def _parse_time(self, time_str: str) -> time:
        """Convierte string 'HH:MM' a objeto time."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour=hour, minute=minute)
        except (ValueError, AttributeError):
            self.logger.warning(f"Error parseando hora: {time_str}. Usando 00:00")
            return time(hour=0, minute=0)
    
    def get_current_session_info(
        self,
        symbol: str,
        current_time: Optional[datetime] = None
    ) -> Dict:
        """Obtiene información completa de la sesión actual para un símbolo.
        
        Returns:
            Dict con:
            - is_tradeable: bool
            - session_name: str o None
            - session_data: Dict o None
            - reason: str
        """
        if current_time is None:
            current_time = datetime.now()
        
        current_time_obj = current_time.time()
        active_session = self._get_active_session(symbol, current_time_obj)
        
        if active_session:
            return {
                'is_tradeable': True,
                'session_name': active_session['name'],
                'session_data': active_session,
                'reason': f"Sesión activa: {active_session['name']}"
            }
        else:
            next_session = self._get_next_session(symbol, current_time_obj)
            next_info = f" Próxima: {next_session['name']} a las {next_session['start']}" if next_session else ""
            
            return {
                'is_tradeable': False,
                'session_name': None,
                'session_data': None,
                'reason': f"Fuera de horario.{next_info}"
            }
    
    def get_active_symbols(self, current_time: Optional[datetime] = None) -> List[str]:
        """Retorna lista de símbolos que pueden operarse en el horario actual.
        
        Args:
            current_time: Hora a verificar (si es None, usa ahora)
        
        Returns:
            Lista de símbolos permitidos
        """
        if current_time is None:
            current_time = datetime.now()
        
        current_time_obj = current_time.time()
        active_symbols = set()
        
        for session_name, session_data in self.sessions.items():
            start_str = session_data.get('start', '00:00')
            end_str = session_data.get('end', '23:59')
            
            start_time = self._parse_time(start_str)
            end_time = self._parse_time(end_str)
            
            if self._is_time_in_range(current_time_obj, start_time, end_time):
                symbols = session_data.get('symbols', [])
                active_symbols.update(symbols)
        
        return sorted(list(active_symbols))
