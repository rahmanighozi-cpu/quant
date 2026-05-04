import ccxt
import pandas as pd
import requests
import time

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8606193574:AAH7pJrAyusDNCPB0tLB4H0BPaRkZsWeH00"
CHAT_ID = "7257725074"
EXCHANGE = ccxt.binance({'options': {'defaultType': 'future'}, 'timeout': 30000, 'enableRateLimit': True})

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try: requests.get(url, timeout=10)
    except: pass

def check_incoming_messages():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("result"):
            last_msg = res["result"][-1].get("message", {}).get("text", "")
            if last_msg == "/status":
                send_telegram("✅ *Terminal Aktif!* Sedang berburu Hidden Gems dengan data 90 hari.")
    except: pass

def get_alpha_signals(symbol):
    try:
        # 1. Fetch Data OHLCV
        ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe='1d', limit=90)
        if len(ohlcv) < 30: return None
        
        df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        
        # 2. ATR Compression (Squeeze)
        df['tr'] = df['h'] - df['l']
        atr_90 = df['tr'].rolling(window=14).mean().iloc[-1]
        is_squeeze = (df['h'].iloc[-1] - df['l'].iloc[-1]) < (0.7 * atr_90)

        # 3. RVOL vs 90 Hari
        avg_vol_90 = df['v'].rolling(window=30).mean().iloc[-1]
        rvol = df['v'].iloc[-1] / avg_vol_90 if avg_vol_90 > 0 else 0

        # 4. Derivatives (OI & Funding)
        oi_data = EXCHANGE.fetch_open_interest(symbol)
        funding = EXCHANGE.fetch_funding_rate(symbol)
        curr_funding = funding['fundingRate'] * 100
        
        # 5. Momentum & CVD Bias
        ema20 = df['c'].ewm(span=20).mean().iloc[-1]
        delta = (df['c'] - df['o']) / (df['h'] - df['l']) if (df['h'].iloc[-1] - df['l'].iloc[-1]) != 0 else 0
        cvd_score = delta.rolling(window=7).sum().iloc[-1]

        # --- SCORING ---
        score = 0
        if is_squeeze: score += 20
        if rvol > 1.5: score += 20
        if curr_funding < 0.03: score += 15
        if df['c'].iloc[-1] > ema20: score += 15
        if cvd_score > 0: score += 15
        if oi_data and oi_data.get('openInterestAmount', 0) > 0: score += 15

        return {'score': score, 'rvol': rvol, 'funding': curr_funding}
    except:
        return None

# --- MAIN WORKFLOW ---
print("🚀 Starting Professional Hidden Gem Scan...")
check_incoming_messages()

try:
    # Cek BTC Trend
    btc_ohlcv = EXCHANGE.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=2)
    if btc_ohlcv[-1][4] >= btc_ohlcv[-2][4]:
        tickers = EXCHANGE.fetch_tickers()
        for symbol, ticker in tickers.items():
            # Filter Target: USDT Futures & Mid-Cap Volume
            if '/USDT' in symbol and 10000000 < ticker.get('quoteVolume', 0) < 500000000:
                data = get_alpha_signals(symbol)
                if data and data['score'] >= 80:
                    msg = (f"💎 *HIDDEN GEM FOUND* 💎\n\n"
                           f"*Asset:* {symbol}\n"
                           f"*Score:* {data['score']}/100\n"
                           f"--------------------------\n"
                           f"📊 *RVOL:* {data['rvol']:.2f}x\n"
                           f"💰 *Funding:* {data['funding']:.4f}%\n"
                           f"🎯 *Structure:* Squeeze Confirmed ✅")
                    send_telegram(msg)
                    time.sleep(1) # Hindari rate limit
    else:
        print("BTC is Down. Skipping scan for safety.")
except Exception as e:
    print(f"Error: {e}")

print("✅ Scan Completed.")
