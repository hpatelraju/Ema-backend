from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import pandas as pd
from datetime import datetime

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# CoinGecko API base
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# EMA config by timeframe
EMA_CONFIG = {
    "1m": [5, 10],
    "5m": [5, 15],
    "15m": [10, 25],
    "30m": [10, 30],
    "1h": [10, 50],
    "2h": [20, 60],
    "4h": [25, 75],
    "6h": [30, 90],
    "8h": [35, 105],
    "12h": [40, 120],
    "1d": [10, 20, 50, 100],
    "3d": [20, 50, 100],
    "1w": [10, 20, 50],
    "1M": [10, 20, 50]
}

@app.get("/api/ema")
def get_ema(
    coin_id: str = Query("dogecoin", description="Coin ID (as per CoinGecko)"),
    vs_currency: str = Query("usd", description="Quote currency")
):
    result = {}
    try:
        market_data_url = (
            f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
            f"?vs_currency={vs_currency}&days=90&interval=hourly"
        )
        r = requests.get(market_data_url)
        if r.status_code != 200:
            return {"error": f"Failed to fetch data: {r.text}"}
        prices = r.json().get("prices", [])
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        for timeframe, periods in EMA_CONFIG.items():
            sub_result = {}
            for p in periods:
                sub_result[f"EMA_{p}"] = round(df["price"].ewm(span=p, adjust=False).mean().iloc[-1], 6)
            result[timeframe] = sub_result

        return result
    except Exception as e:
        return {"error": str(e)}
