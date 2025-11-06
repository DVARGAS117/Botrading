"""
Módulo base para todos los componentes core del sistema Botrading.

Este módulo define la clase base CoreModule que todos los módulos core
deben heredar para garantizar consistencia, reutilizabilidad y mantenibilidad.

Proporciona funcionalidad común como:
- Metadata del módulo (nombre, versión, descripción)
- Gestión del ciclo de vida (inicialización, shutdown, restart)
- Validación de dependencias entre módulos
- Información y estado del módulo
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class ModuleMetadata:
    """
    Metadata inmutable de un módulo core.
    
    Esta clase almacena información descriptiva del módulo que no debe
    cambiar durante su ciclo de vida.
    
    Attributes:
        name: Nombre único del módulo
        version: Versión del módulo en formato semántico (ej: "1.0.0")
        description: Descripción breve de la funcionalidad del módulo
        initialized_at: Timestamp de cuando fue inicializado el módulo
    """
    name: str
    version: str
    description: str
    initialized_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la metadata a un diccionario.
        
        Returns:
            Diccionario con toda la información de metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "initialized_at": self.initialized_at.isoformat()
        }


class CoreModule:
    """
    Clase base para todos los módulos core del sistema.
    
    Todos los módulos core (config_loader, logger, etc.) deben heredar
    de esta clase para garantizar una interfaz común y facilitar la
    reutilización.
    
    Proporciona funcionalidad base para:
    - Gestión de metadata del módulo
    - Ciclo de vida (inicialización, shutdown, restart)
    - Validación de dependencias
    - Información del estado del módulo
    
    Example:
        ```python
        class CustomModule(CoreModule):
            def __init__(self):
                super().__init__(
                    name="CustomModule",
                    version="1.0.0",
                    description="Mi módulo personalizado"
                )
                # Inicialización específica del módulo
        ```
    """
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str = "Core module",
        dependencies: Optional[List[str]] = None
    ):
        """
        Inicializa un módulo core.
        
        Args:
            name: Nombre único del módulo
            version: Versión del módulo (ej: "1.0.0")
            description: Descripción del módulo
            dependencies: Lista de nombres de módulos requeridos
            
        Raises:
            ValueError: Si name o version están vacíos
        """
        if not name or not name.strip():
            raise ValueError("Module name is required")
        if not version or not version.strip():
            raise ValueError("Module version is required")
        
        self._name = name.strip()
        self._version = version.strip()
        self._description = description or "Core module"
        self._dependencies = dependencies or []
        self._initialized = True
        self._metadata = ModuleMetadata(
            name=self._name,
            version=self._version,
            description=self._description
        )
    
    @property
    def name(self) -> str:
        """Nombre del módulo."""
        return self._name
    
    @property
    def version(self) -> str:
        """Versión del módulo."""
        return self._version
    
    @property
    def description(self) -> str:
        """Descripción del módulo."""
        return self._description
    
    @property
    def dependencies(self) -> List[str]:
        """Lista de dependencias del módulo."""
        return self._dependencies.copy()
    
    @property
    def metadata(self) -> ModuleMetadata:
        """Metadata inmutable del módulo."""
        return self._metadata
    
    def is_initialized(self) -> bool:
        """
        Verifica si el módulo está inicializado.
        
        Returns:
            True si el módulo está inicializado, False en caso contrario
        """
        return self._initialized
    
    def get_info(self) -> Dict[str, Any]:
        """
        Obtiene información completa del módulo.
        
        Returns:
            Diccionario con información del módulo incluyendo:
            - name: Nombre del módulo
            - version: Versión del módulo
            - description: Descripción del módulo
            - initialized_at: Timestamp de inicialización
            - dependencies: Lista de dependencias
        """
        info = self._metadata.to_dict()
        info["dependencies"] = self.dependencies
        return info
    
    def shutdown(self) -> None:
        """
        Apaga el módulo y libera recursos.
        
        Las subclases deben sobrescribir este método para implementar
        lógica específica de limpieza, pero deben llamar a super().shutdown()
        al final.
        """
        self._initialized = False
    
    def restart(self) -> None:
        """
        Reinicia el módulo.
        
        Las subclases pueden sobrescribir este método para implementar
        lógica específica de reinicio, pero deben llamar a super().restart()
        al final.
        """
        self._initialized = True
    
    def validate_dependencies(self, available_modules: Dict[str, Any]) -> bool:
        """
        Valida que todas las dependencias requeridas estén disponibles.
        
        Args:
            available_modules: Diccionario con módulos disponibles
                              (nombre -> instancia del módulo)
        
        Returns:
            True si todas las dependencias están disponibles
            
        Raises:
            ValueError: Si falta alguna dependencia requerida
        """
        missing = [dep for dep in self._dependencies if dep not in available_modules]
        
        if missing:
            raise ValueError(
                f"Missing required dependencies for {self._name}: {', '.join(missing)}"
            )
        
        return True
    
    def __str__(self) -> str:
        """
        Representación en string del módulo.
        
        Returns:
            String con el nombre y versión del módulo
        """
        return f"{self._name} v{self._version}"
    
    def __repr__(self) -> str:
        """
        Representación para debugging del módulo.
        
        Returns:
            String con información detallada del módulo
        """
        return (
            f"CoreModule(name='{self._name}', version='{self._version}', "
            f"initialized={self._initialized})"
        )
