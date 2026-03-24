import os
import json
import math
import requests

API_TOKEN = os.environ.get("EODHD_API_TOKEN")

ASSETS = {
    "us": ["SPY", "QQQ", "DIA", "IWM", "EWG", "EWJ", 
           "AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "META", "GOOGL",
           "PG", "WMT", "JNJ", "KO", "JPM", "XOM", "AMAT", "AEM",
           "TLT", "GLD", "SLV", "USO", "UNG", "CPER", "FXE", "FXY"],
    "crypto": {
        "BTCUSDT": "btcusdt",
        "ETHUSDT": "ethusdt",
        "SOLUSDT": "solusdt"
    }
}

def calc_std_dev(prices):
    if len(prices) < 2: return None
    returns = [math.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return prices[-1] * math.sqrt(variance)

def main():
    data_output = {}

    # 1. FETCH AZIONI (EODHD)
    print("Fetch US Stocks...")
    if API_TOKEN:
        first_us = ASSETS["us"][0]
        rest_us = ",".join([f"{s}.US" for s in ASSETS["us"][1:]])
        rt_url = f"https://eodhd.com/api/real-time/{first_us}.US?api_token={API_TOKEN}&fmt=json&s={rest_us}"
        try:
            rt_res = requests.get(rt_url).json()
            items = rt_res if isinstance(rt_res, list) else [rt_res]
            for item in items:
                ticker = item['code'].split('.')[0]
                data_output[ticker] = {"prevClose": float(item['previousClose'])}
        except: print("Error fetching US RT data")

        for ticker in ASSETS["us"]:
            try:
                eod_url = f"https://eodhd.com/api/eod/{ticker}.US?api_token={API_TOKEN}&fmt=json&limit=21"
                eod_res = requests.get(eod_url).json()
                closes = [float(d['adjusted_close']) for d in eod_res]
                data_output[ticker]["stdDev"] = calc_std_dev(closes)
            except: print(f"Error SD for {ticker}")

    # 2. FETCH CRYPTO (Binance - Metodo Alternativo per evitare blocchi)
    print("Fetch Crypto from Binance...")
    for symbol, short in ASSETS["crypto"].items():
        try:
            # Usiamo le candele giornaliere per avere la chiusura esatta di ieri a mezzanotte
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=22"
            res = requests.get(url, timeout=10).json()
            # closes[-1] è la candela di oggi in corso, closes[-2] è la chiusura di ieri
            closes = [float(c[4]) for c in res]
            
            data_output[short] = {
                "prevClose": closes[-2], # Chiusura di ieri (Mezzanotte UTC)
                "stdDev": calc_std_dev(closes[:-1]) # SD calcolata sulle chiusure passate
            }
            print(f"Success {symbol}: Prev {closes[-2]}")
        except Exception as e:
            print(f"Error Crypto {symbol}: {e}")

    with open("data.json", "w") as f:
        json.dump(data_output, f, indent=4)

if __name__ == "__main__":
    main()
