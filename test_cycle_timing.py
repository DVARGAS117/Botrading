"""Script de prueba para verificar cálculo de próximo ciclo M15."""
from datetime import datetime, timedelta

def get_next_cycle_time() -> datetime:
    """Calcula el próximo tiempo de ciclo: 1 minuto después de vela M15 cerrada.
    
    Velas M15 se cierran en: :00, :15, :30, :45
    Ciclos ejecutan en: :01, :16, :31, :46
    """
    now = datetime.now()
    current_minute = now.minute
    
    # Calcular minuto de cierre de vela más cercano
    if current_minute < 15:
        next_close = 15
    elif current_minute < 30:
        next_close = 30
    elif current_minute < 45:
        next_close = 45
    else:
        next_close = 0  # Siguiente hora
    
    # Ciclo es 1 minuto después del cierre
    next_cycle_minute = (next_close + 1) % 60
    
    # Si next_close=0 (cambio de hora), agregar 1 hora
    if next_close == 0 and current_minute >= 45:
        next_time = now.replace(minute=next_cycle_minute, second=0, microsecond=0)
        next_time += timedelta(hours=1)
    else:
        next_time = now.replace(minute=next_cycle_minute, second=0, microsecond=0)
    
    # Si ya pasó este minuto, avanzar al siguiente ciclo
    if next_time <= now:
        next_time += timedelta(minutes=15)
    
    return next_time

# Pruebas con diferentes horas
test_cases = [
    ("19:02:30", datetime(2025, 11, 20, 19, 2, 30)),   # -> próximo: 19:16:00
    ("19:16:30", datetime(2025, 11, 20, 19, 16, 30)),  # -> próximo: 19:31:00
    ("19:31:30", datetime(2025, 11, 20, 19, 31, 30)),  # -> próximo: 19:46:00
    ("19:46:30", datetime(2025, 11, 20, 19, 46, 30)),  # -> próximo: 20:01:00
    ("00:46:30", datetime(2025, 11, 20, 0, 46, 30)),   # -> próximo: 01:01:00
]

print("🧪 Test de cálculo de próximo ciclo M15:\n")
print("Velas M15 cierran en: :00, :15, :30, :45")
print("Ciclos ejecutan en: :01, :16, :31, :46\n")
print("=" * 60)

def calculate_next(test_time: datetime) -> datetime:
    """Versión standalone del cálculo."""
    current_minute = test_time.minute
    
    if current_minute < 15:
        next_close = 15
    elif current_minute < 30:
        next_close = 30
    elif current_minute < 45:
        next_close = 45
    else:
        next_close = 0
    
    next_cycle_minute = (next_close + 1) % 60
    
    if next_close == 0 and current_minute >= 45:
        next_time = test_time.replace(minute=next_cycle_minute, second=0, microsecond=0)
        next_time += timedelta(hours=1)
    else:
        next_time = test_time.replace(minute=next_cycle_minute, second=0, microsecond=0)
    
    if next_time <= test_time:
        next_time += timedelta(minutes=15)
    
    return next_time

for label, test_time in test_cases:
    next_cycle = calculate_next(test_time)
    wait_seconds = (next_cycle - test_time).total_seconds()
    
    print(f"Hora actual: {label} "
          f"-> Próximo ciclo: {next_cycle.strftime('%H:%M:%S')} "
          f"(en {wait_seconds:.0f}s)")

print("=" * 60)

# Verificar hora real
now = datetime.now()
next_real = get_next_cycle_time()
wait_real = (next_real - now).total_seconds()
print(f"\n✅ HORA REAL:")
print(f"Ahora: {now.strftime('%H:%M:%S')}")
print(f"Próximo ciclo: {next_real.strftime('%H:%M:%S')} (en {wait_real:.0f}s)")
