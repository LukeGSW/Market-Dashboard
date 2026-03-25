import os
import json
import math
import requests

API_TOKEN = os.environ.get("EODHD_API_TOKEN")
US_TICKERS = ["SPY", "QQQ", "DIA", "IWM", "DAX", "VT", "EEM", 
              "AAPL", "NVDA", "PG", "WMT", "AEM",
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

    try:
        # Iteriamo direttamente sui ticker per scaricare lo storico EOD.
        # L'esecuzione alle 01:00 UTC garantisce che l'Official Closing Price 
        # sia già stato consolidato e reso definitivo.
        for ticker in US_TICKERS:
            eod_url = f"https://eodhd.com/api/eod/{ticker}.US?api_token={API_TOKEN}&fmt=json&limit=21"
            eod_res = requests.get(eod_url).json()
            
            # Controllo per assicurarci che la risposta sia una lista valida
            if isinstance(eod_res, list) and len(eod_res) > 0:
                
                # 1. Serie per i calcoli quantitativi (include rettifiche per dividendi/split)
                closes_adj = [float(d['adjusted_close']) for d in eod_res]
                
                # 2. Serie per il prezzo ufficiale da visualizzare (puro)
                closes_raw = [float(d['close']) for d in eod_res]
                
                data_output[ticker] = {
                    "prevClose": closes_raw[-1],  # L'ultimo elemento è la chiusura ufficiale della giornata
                    "stdDev": calc_std_dev(closes_adj)
                }
            else:
                print(f"Attenzione: Dati non validi o vuoti per {ticker}")
                
    except Exception as e:
        print(f"Errore critico durante l'esecuzione: {e}")

    # Scrittura del JSON finale
    with open("data.json", "w") as f:
        json.dump(data_output, f, indent=4)

if __name__ == "__main__":
    main()
