import requests
from time import sleep


def get_top_volume(limit=50, retries=3, backoff=1):
    """Fetch top volume stocks from TradingView with simple retries and safer parsing.

    Returns a list of tickers normalized to Yahoo/JK format (e.g. BBRI.JK).
    """
    url = "https://scanner.tradingview.com/indonesia/scan"

    payload = {
        "filter": [
            {"left": "volume", "operation": "nempty"}
        ],
        "options": {"lang": "id"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": ["name", "close", "change", "volume"],
        "sort": {"sortBy": "volume", "sortOrder": "desc"},
        "range": [0, limit]
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    attempt = 0
    while attempt < retries:
        try:
            print("🚀 Mengambil Top Volume Stocks dari TradingView...")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            break
        except Exception as e:
            attempt += 1
            print(f"⚠️ Gagal ambil data dari TradingView (attempt {attempt}/{retries}): {e}")
            if attempt >= retries:
                return []
            sleep(backoff * attempt)

    volume_stocks = []
    for d in data.get("data", []):
        s = d.get("s") or d.get("symbol")
        if not s:
            continue

        # Normalize symbol into Yahoo-style .JK if it's an IDX symbol
        ticker = None
        if isinstance(s, str) and s.startswith("IDX:"):
            ticker = s.split("IDX:", 1)[1] + ".JK"
        elif isinstance(s, str) and s.endswith(".JK"):
            ticker = s
        else:
            # When the symbol is a plain ticker without exchange, assume .JK
            if isinstance(s, str) and ":" not in s:
                ticker = s + ".JK"

        if ticker and ticker not in volume_stocks:
            volume_stocks.append(ticker)

    print(f"✅ Ditemukan {len(volume_stocks)} Top Volume:", volume_stocks[:limit])
    return volume_stocks[:limit]
