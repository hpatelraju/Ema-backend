
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import ccxt
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

timeframes = ['1m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M']
ema_config = {
    'short': [7, 21],
    'medium': [21, 50],
    'long': [50, 100, 200]
}

@app.get("/api/ema")
def get_ema(symbol: str = Query(...), market: str = Query(...)):
    exchange = ccxt.binance({"enableRateLimit": True})
    result = {}

    base_symbol = symbol.replace('/', '')
    if market == 'spot':
        market_symbol = base_symbol
    elif market == 'futures':
        exchange = ccxt.binance({"options": {"defaultType": "future"}})
        market_symbol = base_symbol
    elif market == 'margin':
        market_symbol = base_symbol

    for tf in timeframes:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=200)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            ema_values = {}
            for period in (ema_config['short'] if tf in ['1m','5m','15m']
                           else ema_config['medium'] if tf in ['1h','2h','4h','6h','8h','12h']
                           else ema_config['long']):
                ema_values[f'EMA_{period}'] = df['close'].ewm(span=period).mean().iloc[-1]
            ema_values['Latest Price'] = df['close'].iloc[-1]
            result[tf] = ema_values
        except Exception as e:
            result[tf] = {"error": str(e)}

    return result
