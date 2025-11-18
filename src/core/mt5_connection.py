"""Stub MT5Connection (TBD real implementation)

Proporciona interfaz mínima necesaria para pruebas:
- connect() -> bool
- disconnect() -> None

Reemplazar con implementación real de conexión a MetaTrader 5 cuando esté lista.
"""

class MT5Connection:
    def __init__(self):
        self._connected = False

    def connect(self) -> bool:
        # Simula conexión exitosa
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
