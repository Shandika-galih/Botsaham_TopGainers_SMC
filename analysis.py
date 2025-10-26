import yfinance as yf
import pandas as pd


def analyze_ticker(ticker):
    """Analisa SMC sederhana dengan konfirmasi BOS, FVG, dan OB.

    Konsep:
    - BOS: price breaks the last important swing high/low
    - FVG: simple gap between consecutive candles (low_next > high_prev or high_next < low_prev)
    - Order Block: candle immediately before BOS (simple approach)
    """
    try:
        data = yf.download(
            ticker, period="14d", interval="1h", progress=False, auto_adjust=False
        )
    except Exception as e:
        print(f"⚠️ Gagal ambil data untuk {ticker}: {e}")
        return {"ticker": ticker, "trend": None, "signal": "WAIT", "price": None, "tp": None, "sl": None}

    if data.empty:
        return {"ticker": ticker, "trend": None, "signal": "WAIT", "price": None, "tp": None, "sl": None}

    # SMA and dropna to ensure we have enough history
    data["SMA20"] = data["Close"].rolling(20).mean()
    data.dropna(inplace=True)

    if len(data) < 20:
        return {"ticker": ticker, "trend": None, "signal": "WAIT", "price": None, "tp": None, "sl": None}

    # Normalize Close/High/Low/SMA to Series to avoid DataFrame indexing issues
    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    sma = data["SMA20"]

    if isinstance(close, pd.DataFrame):
        # pick the first column if multiple (yfinance sometimes returns multi-column)
        close = close.iloc[:, 0]
    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]
    if isinstance(low, pd.DataFrame):
        low = low.iloc[:, 0]
    if isinstance(sma, pd.DataFrame):
        sma = sma.iloc[:, 0]

    # Use iloc to extract the last scalar values
    last_close = float(close.iloc[-1])
    sma20 = float(sma.iloc[-1])

    # --- Trend Direction ---
    trend = "BULLISH" if last_close > sma20 else "BEARISH"

    # --- 1. Cek Break of Structure (BOS) ---
    recent_high = high.iloc[-11:-1].max()
    recent_low = low.iloc[-11:-1].min()
    bos_up = last_close > recent_high
    bos_down = last_close < recent_low

    # --- 2. Cek Fair Value Gap (FVG) ---
    fvg = False
    if len(data) >= 2:
        try:
            prev_high = float(high.iloc[-2])
            prev_low = float(low.iloc[-2])
            last_high = float(high.iloc[-1])
            last_low = float(low.iloc[-1])
        except Exception:
            return {"ticker": ticker, "trend": trend, "signal": "WAIT", "price": last_close, "tp": None, "sl": None}

        # Bullish FVG: current low above previous high
        if last_low > prev_high:
            fvg = True
        # Bearish FVG: current high below previous low
        elif last_high < prev_low:
            fvg = True

    # --- 3. Cek Order Block terakhir (OB) ---
    order_block_price = None
    # simple: take the candle before last as potential OB
    if len(data) >= 2:
        if bos_up:
            order_block_price = float(low.iloc[-2])
        elif bos_down:
            order_block_price = float(high.iloc[-2])

    # --- 4. Buat keputusan ---
    structure_confirmed = (
        (trend == "BULLISH" and bos_up and fvg and order_block_price is not None)
        or (trend == "BEARISH" and bos_down and fvg and order_block_price is not None)
    )

    if not structure_confirmed:
        return {
            "ticker": ticker,
            "trend": trend,
            "signal": "WAIT",
            "price": last_close,
            "tp": None,
            "sl": None,
            "bos_up": bos_up,
            "bos_down": bos_down,
            "fvg": fvg,
        }

    # --- 5. Hitung TP & SL (5% dari harga entry) ---
    signal = "BUY" if trend == "BULLISH" else "SELL"
    # Entry price = last_close
    if signal == "BUY":
        tp = round(last_close * 1.05, 2)
        sl = round(last_close * 0.95, 2)
    else:
        tp = round(last_close * 0.95, 2)
        sl = round(last_close * 1.05, 2)

    print(f"✅ SMC Setup terkonfirmasi untuk {ticker}: {signal}")

    return {
        "ticker": ticker,
        "trend": trend,
        "signal": signal,
        "price": last_close,
        "tp": tp,
        "sl": sl,
        "bos_up": bos_up,
        "bos_down": bos_down,
        "fvg": fvg,
    }
    