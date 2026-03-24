import os
import json
import math
import requests

# Token prelevato in modo sicuro dai Secrets di GitHub
API_TOKEN = os.environ.get("EODHD_API_TOKEN")

ASSETS = {
    "us": ["SPY", "QQQ", "DIA", "IWM", "EWG", "EWJ", 
           "AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "META", "GOOGL",
           "PG", "WMT", "JNJ", "KO", "JPM", "XOM", "AMAT", "AEM",
           "TLT", "GLD", "SLV", "USO", "UNG", "CPER", "FXE", "FXY"],
    "crypto": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
}

def calc_std_dev(prices):
    if len(prices) < 2: return None
    returns = [math.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return prices[-1] * math.sqrt(variance)

def main():
    data_output = {}

    # 1. FETCH EODHD (Azioni ed ETF)
    if API_TOKEN:
        print("Scaricamento dati US (EODHD)...")
        # Prendi le chiusure (Previous Close) in batch
        first_us = ASSETS["us"][0]
        rest_us = ",".join([f"{s}.US" for s in ASSETS["us"][1:]])
        rt_url = f"https://eodhd.com/api/real-time/{first_us}.US?api_token={API_TOKEN}&fmt=json&s={rest_us}"
        
        try:
            rt_data = requests.get(rt_url).json()
            rt_data = rt_data if isinstance(rt_data, list) else [rt_data]
            for item in rt_data:
                if item.get("code"):
                    ticker = item["code"].split(".")[0]
                    data_output[ticker] = {
                        "prevClose": float(item.get("previousClose", 0))
                    }
        except Exception as e:
            print(f"Errore Real-Time EODHD: {e}")

        # Calcola Volatilità EODHD
        for ticker in ASSETS["us"]:
            try:
                eod_url = f"https://eodhd.com/api/eod/{ticker}.US?api_token={API_TOKEN}&fmt=json&limit=21"
                eod_data = requests.get(eod_url).json()
                if len(eod_data) > 1:
                    # Usa l'adjusted close
                    closes = [float(d.get("adjusted_close", d.get("close", 0))) for d in eod_data if float(d.get("adjusted_close", d.get("close", 0))) > 0]
                    std_dev = calc_std_dev(closes)
                    if ticker not in data_output: data_output[ticker] = {}
                    data_output[ticker]["stdDev"] = std_dev
            except Exception as e:
                print(f"Errore Storico {ticker}: {e}")

    # 2. FETCH BINANCE (Crypto)
    print("Scaricamento dati Crypto (Binance)...")
    for crypto in ASSETS["crypto"]:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={crypto}&interval=1d&limit=21"
            kline_data = requests.get(url).json()
            closes = [float(candle[4]) for candle in kline_data]
            prev_close = closes[-2] if len(closes) > 1 else closes[-1]
            std_dev = calc_std_dev(closes)
            
            ticker_lower = crypto.lower()
            data_output[ticker_lower] = {
                "prevClose": prev_close,
                "stdDev": std_dev
            }
        except Exception as e:
            print(f"Errore Crypto {crypto}: {e}")

    # 3. SALVATAGGIO JSON
    with open("data.json", "w") as f:
        json.dump(data_output, f, indent=4)
    print("data.json generato con successo!")

if __name__ == "__main__":
    main()
