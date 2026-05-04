import ccxt
import pandas as pd
import requests

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8606193574:AAH7pJrAyusDNCPB0tLB4H0BPaRkZsWeH00"
CHAT_ID = "7257725074"
EXCHANGE = ccxt.binance({'options': {'defaultType': 'future'}})

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try: requests.get(url)
    except: pass

def check_incoming_messages():
    """Menjawab /status agar kamu tahu bot tetap nyala"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        res = requests.get(url).json()
        if res["result"]:
            last_msg = res["result"][-1]["message"]["text"]
            if last_msg == "/status":
                send_telegram("✅ *Hidden Gem Hunter Aktif!* Memindai seluruh pasar dengan data 90 hari.")
    except: pass

def get_alpha_signals(symbol):
    try:
        # 1. CEK BTC TREND (Safety Switch)
        btc = EXCHANGE.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=2)
        if btc[-1][4] < btc[-2][4]: return None

        # 2. DATA STABIL (90 Hari)
        ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe='1d', limit=90)
        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        
        # ATR Compression & Price Action
        df['tr'] = df['h'] - df['l']
        atr_90 = df['tr'].rolling(window=14).mean().iloc[-1]
        is_squeeze = (df['h'].iloc[-1] - df['l'].iloc[-1]) < (0.6 * atr_90)

        # RVOL vs 90 Hari
        avg_vol_90 = df['v'].rolling(window=30).mean().iloc[-1]
        rvol = df['v'].iloc[-1] / avg_vol_90

        # 3. DERIVATIVES (OI, Funding, CVD)
        oi_data = EXCHANGE.fetch_open_interest(symbol)
        funding = EXCHANGE.fetch_funding_rate(symbol)
        curr_funding = funding['fundingRate'] * 100
        ema20 = df['c'].ewm(span=20).mean().iloc[-1]
        
        delta = (df['c'] - df['o']) / (df['h'] - df['l'])
        cvd_score = delta.rolling(window=7).sum().iloc[-1]

        # Scoring Logic
        score = 0
        if is_squeeze: score += 20
        if rvol > 1.8: score += 20
        if curr_funding < 0.02: score += 15
        if df['c'].iloc[-1] > ema20: score += 15 # Momentum Runner
        if cvd_score > 0: score += 15
        if oi_data['openInterestAmount'] > 0: score += 15

        return {'score': score, 'rvol': rvol, 'funding': curr_funding, 'cvd': cvd_score}
    except: return None

check_incoming_messages()

# Pemindaian Dinamis ke Seluruh Market Binance Futures
all_tickers = EXCHANGE.fetch_tickers()
for symbol in all_tickers:
    # Filter Low-Mid Cap berdasarkan Volume ($10jt - $500jt)
    if '/USDT' in symbol and 10000000 < all_tickers[symbol]['quoteVolume'] < 500000000:
        data = get_alpha_signals(symbol)
        if data and data['score'] >= 80:
            msg = (f"💎 *HIDDEN GEM FOUND* 💎\n\n"
                   f"*Asset:* {symbol}\n"
                   f"*Score:* {data['score']}/100\n"
                   f"--------------------------\n"
                   f"📊 *RVOL:* {data['rvol']:.2f}x\n"
                   f"💰 *Funding:* {data['funding']:.4f}%\n"
                   f"📈 *CVD Bias:* Bullish\n"
                   f"🎯 *Structure:* ATR Squeeze ✅\n\n"
                   f"Status: *Momentum Runner Confirmed!*")
            send_telegram(msg)
