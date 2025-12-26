"""
Scheduler bot saham:
Menjalankan dua fungsi bersamaan di setiap jadwal:
1. run_bot() → ambil & kirim sinyal baru
2. update_open_signals() → cek sinyal open (TP/SL)

Jadwal WIB:
- 07:58
- 12:00
- 17:00
- 20:00
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import time as time_module
import logging

from main import run_bot
from update_signals import update_open_signals

# Zona waktu Indonesia Barat
JAKARTA = ZoneInfo("Asia/Jakarta")

# Jadwal eksekusi harian
SCHEDULE_TIMES = [
    time(7, 58),
    time(12, 0),
    time(17, 0),
    time(20, 0),
]


def _next_run(now: datetime) -> datetime:
    """Tentukan waktu berikutnya bot dijalankan setelah waktu `now`."""
    today = now.date()
    candidates = []
    for t in SCHEDULE_TIMES:
        dt = datetime.combine(today, t).replace(tzinfo=JAKARTA)
        if dt <= now:
            dt += timedelta(days=1)
        candidates.append(dt)
    return min(candidates)


def main_loop():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s WIB - %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.info("🕐 Scheduler aktif. Jadwal bot: %s",
                 ", ".join(t.strftime("%H:%M") for t in SCHEDULE_TIMES))

    while True:
        now = datetime.now(JAKARTA)
        next_dt = _next_run(now)
        wait_seconds = (next_dt - now).total_seconds()

        logging.info(
            "⏳ Jadwal berikutnya: %s (dalam %.0f detik)",
            next_dt.strftime("%Y-%m-%d %H:%M:%S"),
            wait_seconds,
        )

        try:
            if wait_seconds > 0:
                time_module.sleep(wait_seconds)
        except KeyboardInterrupt:
            logging.info("⛔ Scheduler dihentikan oleh user.")
            return

        logging.info("🚀 Menjalankan bot pada %s", datetime.now(JAKARTA).strftime("%Y-%m-%d %H:%M:%S"))

        try:
            # Langsung jalankan dua proses: run_bot lalu update_open_signals
            logging.info("📈 Menjalankan pengambilan sinyal baru...")
            run_bot()

            logging.info("🔄 Menjalankan update sinyal open (cek TP/SL)...")
            update_open_signals()

            logging.info("✅ Kedua tugas selesai dijalankan.")

        except Exception as e:
            logging.exception("❌ Error saat menjalankan bot: %s", e)

        # Tunggu 1 detik agar tidak double-trigger
        time_module.sleep(1)


if __name__ == "__main__":
    main_loop()
