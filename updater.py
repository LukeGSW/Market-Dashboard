import os
import json
import math
import requests

API_TOKEN = os.environ.get("EODHD_API_TOKEN")
US_TICKERS = ["SPY", "QQQ", "DIA", "IWM", "EWG", "EWJ", 
              "AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "META", "GOOGL",
              "PG", "WMT", "JNJ", "KO", "JPM", "XOM", "AMAT", "AEM",
              "TLT", "GLD", "SLV", "USO", "UNG", "CPER", "FXE", "FXY"]

def calc_std_dev(prices):
    if len(prices) < 2: return None
    returns = [math.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return prices[-1] * math.sqrt(variance)

def main():
    data_output = {}
    if not API_TOKEN: return

    # Batch Real-Time per le chiusure US
    first_us = US_TICKERS[0]
    rest_us = ",".join([f"{s}.US" for s in US_TICKERS[1:]])
    rt_url = f"https://eodhd.com/api/real-time/{first_us}.US?api_token={API_TOKEN}&fmt=json&s={rest_us}"
    
    try:
        res = requests.get(rt_url).json()
        items = res if isinstance(res, list) else [res]
        for item in items:
            ticker = item['code'].split('.')[0]
            data_output[ticker] = {"prevClose": float(item['previousClose'])}
            
        # Storico per SD
        for ticker in US_TICKERS:
            eod_url = f"https://eodhd.com/api/eod/{ticker}.US?api_token={API_TOKEN}&fmt=json&limit=21"
            eod_res = requests.get(eod_url).json()
            closes = [float(d['adjusted_close']) for d in eod_res]
            data_output[ticker]["stdDev"] = calc_std_dev(closes)
    except: pass

    with open("data.json", "w") as f:
        json.dump(data_output, f, indent=4)

if __name__ == "__main__":
    main()
