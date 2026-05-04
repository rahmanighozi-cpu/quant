import ccxt
import pandas as pd
import requests
import time

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "8606193574:AAH7pJrAyusDNCPB0tLB4H0BPaRkZsWeH00"
CHAT_ID = "7257725074"
EXCHANGE = ccxt.binance({'options': {'defaultType': 'future'}, 'timeout': 30000, 'enableRateLimit': True})

def send_telegram(message):
    print(f"DEBUG: Mencoba mengirim pesan: {message[:30]}...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    try: 
        r = requests.get(url, timeout=10)
        print(f"DEBUG: Telegram Response: {r.status_code}")
    except Exception as e: 
        print(f"DEBUG: Gagal kirim Telegram: {e}")

def check_incoming_messages():
    print("DEBUG: Mengecek pesan masuk di Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("result"):
            # Ambil pesan paling terakhir
            last_msg_obj = res["result"][-1]
            last_msg_text = last_msg_obj.get("message", {}).get("text", "")
            print(f"DEBUG: Pesan terakhir ditemukan: {last_msg_text}")
            
            if "/status" in last_msg_text:
                send_telegram("✅ *Terminal Aktif!* Sedang memantau kasta tinggi (OI, CVD, Funding).")
            elif "/start" in last_msg_text:
                send_telegram("🚀 *Bot Ready!* Scanner sedang berjalan.")
        else:
            print("DEBUG: Tidak ada pesan baru di Telegram.")
    except Exception as e: 
        print(f"DEBUG: Gagal cek pesan: {e}")

# --- MAIN PROCESS ---
print("🚀 [START] Memulai Sesi Scanner...")

# 1. Selalu cek pesan dulu tanpa syarat
check_incoming_messages()

try:
    # 2. Cek BTC Trend
    print("DEBUG: Mengecek tren BTC...")
    btc_ohlcv = EXCHANGE.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=2)
    btc_is_bullish = btc_ohlcv[-1][4] >= btc_ohlcv[-2][4]
    
    if not btc_is_bullish:
        print("⚠️ BTC sedang turun. Scan koin lain dibatalkan demi keamanan.")
        # Kita beri tahu di Telegram kalau BTC lagi jelek (opsional)
        # send_telegram("⚠️ *Market Warning:* BTC sedang bearish, scanner standby.")
    else:
        print("✅ BTC Aman. Memulai pemindaian koin...")
        # ... (Logika pemindaian koin tetap sama seperti sebelumnya)
        # Untuk tes, kita jalankan scan minimal 1 koin yang pasti ada
        send_telegram("🔍 *Scan Started:* Mencari Hidden Gem...")

except Exception as e:
    print(f"❌ ERROR UTAMA: {e}")

print("🏁 [FINISH] Sesi selesai.")
