import os
import json
import math
import requests

API_TOKEN = os.environ.get("EODHD_API_TOKEN")

# Inserito VIXY e AMAT nella lista standard
US_TICKERS = ["VIXY", "SPY", "QQQ", "DIA", "IWM", "DAX", "VT", "EEM", 
              "AAPL", "NVDA", "PG", "WMT", "AEM", "AMAT",
              "XLK", "XLV", "XLF", "XLY", "XLI", "XLP", "XLE", "XLU",
              "GLD", "SLV", "USO", "UNG", "CPER", 
              "TLT", "HYG", "FXE", "FXY"]

def calc_std_dev(prices):
    if len(prices) < 2: return None
    returns = [math.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return prices[-1] * math.sqrt(variance)

def main():
    data_output = {}
    if not API_TOKEN:
        print("Errore: API_TOKEN mancante.")
        return

    for ticker in US_TICKERS:
        try:
            eod_url = f"https://eodhd.com/api/eod/{ticker}.US?api_token={API_TOKEN}&fmt=json&limit=21"
            response = requests.get(eod_url)
            
            if response.status_code != 200:
                print(f"Errore API per {ticker}: HTTP {response.status_code}")
                continue
                
            eod_res = response.json()
            
            if isinstance(eod_res, list) and len(eod_res) > 0:
                closes_adj = [float(d['adjusted_close']) for d in eod_res]
                closes_raw = [float(d['close']) for d in eod_res]
                
                data_output[ticker] = {
                    "prevClose": closes_raw[-1],
                    "stdDev": calc_std_dev(closes_adj)
                }
            else:
                print(f"Attenzione: Dati non validi o vuoti per {ticker}")
                
        except Exception as e:
            print(f"Errore critico elaborando {ticker}: {e}")

    with open("data.json", "w") as f:
        json.dump(data_output, f, indent=4)

if __name__ == "__main__":
    main()
