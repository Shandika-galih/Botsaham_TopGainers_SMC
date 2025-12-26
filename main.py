from get_top_gainers import get_top_volume
from analysis import analyze_ticker
from telegram_bot import send_signal

def run_bot():
    tickers = get_top_volume(limit=50)
    if not tickers:
        print("⚠️ Tidak ada data top volume, analisis fallback ke BBRI.JK")
        tickers = ["BBRI.JK"]

    for t in tickers:
        print(f"🔍 Analisis {t}...")
        result = analyze_ticker(t)
        if result["signal"] != "WAIT":
            send_signal(result)

if __name__ == "__main__":
    run_bot()
