import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from signals_log import add_signal

def send_signal(result):
    """
    Kirim pesan sinyal ke Telegram.
    - Jika status OPEN → dikirim & ditambahkan ke log.
    - Jika status TP/SL → dikirim saja tanpa ditambahkan ke log.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"⚠️ Skipping send: Telegram token/chat ID belum diatur. ({result.get('ticker')})")
        return

    note = result.get("note", "")
    status = result.get("status", "OPEN")

    # Bangun pesan Telegram dengan HTML
    text = (
        f"<b>{result.get('ticker')}</b>\n"
        f"📊 Trend: {result.get('trend') or '-'}\n"
        f"📈 Sinyal: {result.get('signal')}\n"
        f"💰 Harga: {result.get('price')}\n"
        f"🎯 TP: {result.get('tp')}\n"
        f"🛑 SL: {result.get('sl')}"
    )

    if note:
        text += f"\n\n<b>{note}</b>"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Pesan terkirim ke Telegram: {result.get('ticker')} ({status})")

        # Hanya simpan ke log jika sinyal masih OPEN
        if status == "OPEN":
            try:
                add_signal(result)
            except Exception as e:
                print(f"⚠️ Gagal menambah ke log: {e}")

    except Exception as e:
        print(f"⚠️ Gagal kirim ke Telegram: {e}")
