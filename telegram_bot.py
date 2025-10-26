import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from signals_log import add_signal


def send_signal(result):
    """Send a formatted Telegram message and log it.

    If TELEGRAM credentials are not configured the function will skip sending.
    After a successful send the signal is appended to the persistent log.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"⚠️ Skipping send: TELEGRAM_TOKEN/CHAT_ID not configured. Signal: {result.get('ticker')}")
        return

    # Build message using HTML formatting
    text = (
        f"<b>{result.get('ticker')}</b>\n"
        f"Trend: {result.get('trend')}\n"
        f"Sinyal: {result.get('signal')}\n"
        f"Harga: {result.get('price')}\n"
        f"🎯 TP: {result.get('tp')}\n"
        f"🛑 SL: {result.get('sl')}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Sinyal terkirim: {result.get('ticker')}")
        # Log the sent signal for later monitoring
        try:
            add_signal(result)
        except Exception as e:
            print(f"⚠️ Gagal menambahkan sinyal ke log: {e}")
    except Exception as e:
        # Keep the program running even if Telegram fails
        print(f"⚠️ Gagal kirim sinyal: {e}")
