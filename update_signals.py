import json
import os
from datetime import datetime
from signals_log import check_open_signals
from telegram_bot import send_signal

LOG_PATH = "signals_log.json"

def update_open_signals(notify_open: bool = False):
    print("=== 🚀 Memulai pengecekan sinyal OPEN ===")
    changed = check_open_signals()

    if not changed:
        print("⚠️ Tidak ada sinyal yang berubah status (mungkin belum kena TP/SL atau data kosong).")
        return

    # Baca file log lama
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            try:
                all_signals = json.load(f)
            except json.JSONDecodeError:
                all_signals = []
    else:
        all_signals = []

    new_log = []  # hanya untuk sinyal yang masih OPEN

    for item in all_signals:
        ticker = item.get("ticker")
        status = item.get("status", "OPEN")

        # cari apakah ticker ini berubah status
        updated = next((c for c in changed if c["ticker"] == ticker), None)
        if updated:
            status = updated.get("status")
            item["status"] = status
            item["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            result = {
                "ticker": ticker,
                "signal": item.get("signal"),
                "price": updated.get("last_price_checked") or item.get("price"),
                "tp": item.get("tp"),
                "sl": item.get("sl"),
                "status": status,
            }

            if status in ("TP_HIT", "TP"):
                result["note"] = "✅ TAKE PROFIT HIT"
                send_signal(result)
                print(f"✅ {ticker} mencapai TP")
                continue  # jangan simpan ke new_log

            elif status in ("SL_HIT", "SL"):
                result["note"] = "❌ STOP LOSS HIT"
                send_signal(result)
                print(f"❌ {ticker} terkena SL")
                continue  # jangan simpan ke new_log

            else:
                if notify_open:
                    result["note"] = "⚪ Masih OPEN"
                    send_signal(result)

        # simpan kembali hanya jika masih OPEN
        if status == "OPEN":
            new_log.append(item)

    # Simpan ulang log hanya dengan posisi yang masih open
    with open(LOG_PATH, "w") as f:
        json.dump(new_log, f, indent=2)

    print(f"✅ Log diperbarui — total sinyal masih OPEN: {len(new_log)}")


if __name__ == "__main__":
    update_open_signals(notify_open=False)
