"""Simple scheduler to run the bot at 07:00 and 12:00 WIB (Asia/Jakarta).

This implementation uses the standard library only (zoneinfo) and a sleep
loop. It imports `run_bot` from `main.py` so ensure `main.py` does not
execute the bot on import (it doesn't: guarded by __name__ == '__main__').

Run with:
    python scheduler.py

The script runs forever and calls `run_bot()` at the two scheduled times.
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import time as time_module
import logging

from main import run_bot


JAKARTA = ZoneInfo("Asia/Jakarta")
SCHEDULE_TIMES = [time(7, 0), time(12, 0)]  # 07:00 and 12:00 WIB


def _next_run(now: datetime) -> datetime:
    """Return the next datetime (tz-aware) to run the job after `now`."""
    today = now.date()
    candidates = []
    for t in SCHEDULE_TIMES:
        dt = datetime.combine(today, t).replace(tzinfo=JAKARTA)
        if dt <= now:
            # If the time already passed today, schedule for tomorrow
            dt = dt + timedelta(days=1)
        candidates.append(dt)

    # Return the earliest candidate
    return min(candidates)


def main_loop():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    logging.info("Scheduler started. Will run at: %s", ", ".join(t.strftime("%H:%M") for t in SCHEDULE_TIMES))

    while True:
        now = datetime.now(JAKARTA)
        next_dt = _next_run(now)
        wait_seconds = (next_dt - now).total_seconds()
        logging.info("Next run scheduled at %s (in %.0f seconds)", next_dt.isoformat(), wait_seconds)

        # Sleep until next run (wake early if interrupted)
        try:
            if wait_seconds > 0:
                time_module.sleep(wait_seconds)
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user")
            return

        # Execute the bot
        try:
            logging.info("Running bot at %s", datetime.now(JAKARTA).isoformat())
            run_bot()
            logging.info("Run finished")
        except Exception as e:
            logging.exception("Error while running bot: %s", e)

        # Small sleep to avoid immediate re-run in case of clock rounding
        time_module.sleep(1)


if __name__ == "__main__":
    main_loop()
