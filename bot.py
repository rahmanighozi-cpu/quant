import ccxt
import pandas as pd
import requests

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8606193574:AAH7pJrAyusDNCPB0tLB4H0BPaRkZsWeH00"
CHAT_ID = "7257725074"
EXCHANGE = ccxt.binance()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try:
        requests.get(url)
    except:
        pass

def get_alpha_score(symbol):
    try:
        # 1. Filter Keamanan: Cek Tren BTC
        btc = EXCHANGE.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=2)
        if btc[-1][4] < btc[-2][4]: 
            return 0 

        # 2. Ambil Data Koin (Daily 90 hari)
        ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe='1d', limit=90)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        
        # 3. ATR Compression (Squeeze)
        df['tr'] = df['high'] - df['low']
        atr = df['tr'].rolling(window=14).mean().iloc[-1]
        current_range = df['high'].iloc[-1] - df['low'].iloc[-1]
        volat_score = 40 if current_range < (0.6 * atr) else 0 

        # 4. Relative Volume (RVOL)
        avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
        rvol = df['volume'].iloc[-1] / avg_vol
        rvol_score = 30 if rvol > 1.8 else 0 

        # 5. Price Momentum
        momentum_score = 30 if df['close'].iloc[-1] > df['close'].iloc[-2] else 0

        return volat_score + rvol_score + momentum_score
    except:
        return 0

watch_list = ['APE/USDT', 'ORDI/USDT', 'ONDO/USDT', 'LTC/USDT', 'BERA/USDT', 'TIA/USDT', 'ARB/USDT', 'FET/USDT']

for coin in watch_list:
    score = get_alpha_score(coin)
    if score >= 80:
        msg = f"🔥 *HIGH QUALITY ALPHA* 🔥\n\n*Coin:* {coin}\n*Score:* {score}/100\n*Status:* Ready for Ignition 🚀"
        send_telegram(msg)
