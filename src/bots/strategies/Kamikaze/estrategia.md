import MetaTrader5 as mt5
import pandas as pd
import time
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURACIÓN DE USUARIO ---
API_KEY_GEMINI = "TU_API_KEY_DE_GEMINI_AQUI"
MT5_LOGIN = 12345678  # Tu ID de cuenta
MT5_PASSWORD = "TU_PASSWORD"
MT5_SERVER = "TU_SERVER_BROKER"

# Configuración de Activos y Riesgo
SYMBOLS = ["XAUUSD", "US100"]  # Asegúrate que tu broker usa estos nombres (o NAS100, GOLD)
LOT_SIZE = 0.01  # Mínimo posible para empezar
TIMEFRAME_ANALYSIS = mt5.TIMEFRAME_H1  # Gemini analiza H1
TIMEFRAME_EXECUTION = mt5.TIMEFRAME_M5 # Python ejecuta en M5
DEVIATION = 20 # Desviación permitida en puntos

# Configuración Gemini
genai.configure(api_key=API_KEY_GEMINI)
model = genai.GenerativeModel('gemini-1.5-flash') # Usamos Flash por velocidad

# Estado Global del Bias (Actualizado por Gemini)
market_bias = {symbol: "NEUTRAL" for symbol in SYMBOLS}

def connect_mt5():
    if not mt5.initialize(login=MT5_LOGIN, server=MT5_SERVER, password=MT5_PASSWORD):
        print("Error al iniciar MT5:", mt5.last_error())
        quit()
    else:
        print("Conectado a MT5 exitosamente")

def get_market_data(symbol, timeframe, n_candles=20):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_candles)
    if rates is None:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def ask_gemini_bias(symbol):
    """
    Envía datos numéricos a Gemini para obtener la estructura del mercado.
    """
    df = get_market_data(symbol, TIMEFRAME_ANALYSIS, 10) # Últimas 10 velas de H1
    if df is None: return "NEUTRAL"
    
    # Preparamos el prompt con datos crudos
    data_str = df[['time', 'open', 'high', 'low', 'close']].to_string()
    
    prompt = f"""
    Eres un trader experto en Smart Money Concepts. Analiza estos datos de precios (H1) para {symbol}:
    {data_str}
    
    Determina la TENDENCIA INMEDIATA basándote en máximos y mínimos recientes.
    Responde SOLO con una palabra: "BULLISH" (si debo buscar compras), "BEARISH" (si debo buscar ventas), o "RANGING" (si no hay claridad).
    No des explicaciones.
    """
    
    try:
        response = model.generate_content(prompt)
        bias = response.text.strip().upper()
        # Limpieza básica por si Gemini habla de más
        if "BULLISH" in bias: return "BULLISH"
        if "BEARISH" in bias: return "BEARISH"
        return "NEUTRAL"
    except Exception as e:
        print(f"Error Gemini: {e}")
        return "NEUTRAL"

def execute_strategy(symbol):
    """
    Estrategia simple de ruptura de volatilidad en M5 alineada con Gemini.
    """
    df_m5 = get_market_data(symbol, TIMEFRAME_EXECUTION, 20)
    if df_m5 is None: return

    current_price = mt5.symbol_info_tick(symbol).ask
    last_close = df_m5.iloc[-1]['close']
    prev_close = df_m5.iloc[-2]['close']
    
    bias = market_bias[symbol]
    
    print(f"[{symbol}] Precio: {current_price} | Bias Gemini: {bias}")

    # --- LÓGICA DE GATILLO (SIMPLIFICADA PARA VELOCIDAD) ---
    
    # COMPRA: Gemini dice BULLISH + Vela M5 anterior cerró alcista con fuerza
    if bias == "BULLISH" and last_close > prev_close:
        if not check_open_positions(symbol): # Solo una operación a la vez por par
            place_order(symbol, mt5.ORDER_TYPE_BUY)

    # VENTA: Gemini dice BEARISH + Vela M5 anterior cerró bajista con fuerza
    elif bias == "BEARISH" and last_close < prev_close:
        if not check_open_positions(symbol):
            place_order(symbol, mt5.ORDER_TYPE_SELL)

def check_open_positions(symbol):
    positions = mt5.positions_get(symbol=symbol)
    return len(positions) > 0

def place_order(symbol, order_type):
    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    
    # SL y TP agresivos (Scalping)
    # Ajustar según el activo: XAUUSD necesita más puntos que EURUSD
    point = mt5.symbol_info(symbol).point
    sl_points = 500 # 50 pips (Ajustar según volatilidad)
    tp_points = 1000 # 100 pips (Ratio 1:2)
    
    sl = price - sl_points * point if order_type == mt5.ORDER_TYPE_BUY else price + sl_points * point
    tp = price + tp_points * point if order_type == mt5.ORDER_TYPE_BUY else price - tp_points * point

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": DEVIATION,
        "magic": 234000,
        "comment": "Gemini AI Trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Error orden {symbol}: {result.comment}")
    else:
        print(f"ORDEN EJECUTADA EN {symbol}: {result.order}")

# --- BUCLE PRINCIPAL ---
connect_mt5()

last_gemini_call = 0
GEMINI_INTERVAL = 1800 # 30 minutos

print("--- INICIANDO PROTOCOLO KAMIKAZE ---")

while True:
    # 1. Consultar a Gemini cada 30 min para actualizar el Bias
    if time.time() - last_gemini_call > GEMINI_INTERVAL:
        for symbol in SYMBOLS:
            print(f"Consultando a Gemini para {symbol}...")
            market_bias[symbol] = ask_gemini_bias(symbol)
            print(f"Nuevo Bias para {symbol}: {market_bias[symbol]}")
        last_gemini_call = time.time()
    
    # 2. Ejecutar lógica técnica cada ciclo (aprox cada 10 seg)
    for symbol in SYMBOLS:
        execute_strategy(symbol)
    
    time.sleep(10) # Espera 10 segundos antes del siguiente ciclo



    