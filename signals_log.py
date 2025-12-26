import json
from pathlib import Path
from datetime import datetime
import yfinance as yf
from typing import Dict, Any, List

LOG_PATH = Path(__file__).parent / "signals_log.json"


def _read_log() -> List[Dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    try:
        with LOG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _write_log(data: List[Dict[str, Any]]):
    with LOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_signal(result: Dict[str, Any]):
    """Append a new signal to the persistent log with status OPEN.

    result is expected to contain keys: ticker, price, tp, sl, signal
    """
    ticker = result.get("ticker")
    data = _read_log()

    # If there is already an OPEN signal for the same ticker, avoid creating a duplicate.
    # Instead update the existing entry (refresh entry_price/tp/sl/timestamp) so we keep
    # a single authoritative OPEN entry per ticker.
    for item in data:
        if item.get("ticker") == ticker and item.get("status") == "OPEN":
            # update fields and return existing entry
            item["entry_price"] = result.get("price")
            item["tp"] = result.get("tp")
            item["sl"] = result.get("sl")
            item["signal"] = result.get("signal")
            item["timestamp"] = datetime.utcnow().isoformat()
            _write_log(data)
            return item

    # No existing OPEN entry — create a new one
    entry = {
        "id": f"{ticker}_{int(datetime.utcnow().timestamp())}",
        "timestamp": datetime.utcnow().isoformat(),
        "ticker": ticker,
        "entry_price": result.get("price"),
        "tp": result.get("tp"),
        "sl": result.get("sl"),
        "signal": result.get("signal"),
        "status": "OPEN",
        "updated_at": None,
    }
    data.append(entry)
    _write_log(data)
    return entry


def check_open_signals() -> List[Dict[str, Any]]:
    """Check all OPEN signals and update status to TP_HIT, SL_HIT, or keep OPEN.

    Returns a list of entries that changed state during this check.
    """
    data = _read_log()
    changed = []
    for item in data:
        if item.get("status") != "OPEN":
            continue

        ticker = item.get("ticker")
        try:
            # get latest close price (1m resolution may not be available; use 1d as fallback)
            df = yf.download(ticker, period="1d", interval="1m", progress=False, auto_adjust=False)
            if df.empty:
                df = yf.download(ticker, period="5d", interval="1h", progress=False, auto_adjust=False)
            if df.empty:
                continue
            current = float(df["Close"].iloc[-1])
        except Exception:
            continue

        tp = item.get("tp")
        sl = item.get("sl")
        sig = item.get("signal")
        new_status = None

        if sig == "BUY":
            if tp is not None and current >= tp:
                new_status = "TP_HIT"
            elif sl is not None and current <= sl:
                new_status = "SL_HIT"
        elif sig == "SELL":
            if tp is not None and current <= tp:
                new_status = "TP_HIT"
            elif sl is not None and current >= sl:
                new_status = "SL_HIT"

        if new_status:
            item["status"] = new_status
            item["updated_at"] = datetime.utcnow().isoformat()
            item["last_price_checked"] = current
            changed.append(item)

    if changed:
        _write_log(data)
    return changed


def list_signals() -> List[Dict[str, Any]]:
    return _read_log()


if __name__ == "__main__":
    # quick CLI: run check and print changes
    changed = check_open_signals()
    if not changed:
        print("No updates")
    else:
        for c in changed:
            print(f"Updated {c['id']}: {c['status']} (price={c.get('last_price_checked')})")
