import requests
from time import sleep


def get_top_gainers(limit=50, retries=3, backoff=1):
    """Fetch top gainers from TradingView with simple retries and safer parsing.

    Returns a list of tickers normalized to Yahoo/JK format (e.g. BBRI.JK).
    """
    url = "https://scanner.tradingview.com/indonesia/scan"

    payload = {
        "filter": [
            {"left": "change", "operation": "nempty"},
            {"left": "change", "operation": "greater", "right": 0}
        ],
        "options": {"lang": "id"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": ["name", "close", "change", "volume"],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, limit]
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    attempt = 0
    while attempt < retries:
        try:
            print("🚀 Mengambil Top Gainers dari TradingView...")
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

    gainers = []
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

        if ticker and ticker not in gainers:
            gainers.append(ticker)

    print(f"✅ Ditemukan {len(gainers)} Top Gainers:", gainers[:limit])
    return gainers[:limit]
