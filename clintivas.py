import websocket
import threading
import time
import json
import requests
from datetime import datetime
import html
import os
from flask import Flask, Response
import logging

# Setup basic logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- CONFIG --------------------

start_pinging = False
ws_instance = None

WS_URL = os.environ.get("WS_URL") or "wss://ivasms.com:2087/socket.io/?token=eyJpdiI6IkcyeVFWbFk1ZnhmWlZEZUUyOHZnSUE9PSIsInZhbHVlIjoiQWZRYWZmTnUxbHB4VVh2NGNUY0puckVURkZTTy9WMnBIbDMwL1llWFh3QVFRVDczZjVDWTNQUDN1c1IrY1ZqWW1zUS9PWlJic01EMnAyMmRxNVMyV3AvTFZwR1ZTeHNJY0ZaUS9uNU1Rc0xub2s1QTZsZFpZVTBvT2NHLzUvc0FnUGo3b2wxc2FrVXlER3lpeWJ3WmFBZDhEVnI1VEFQTkFyOTYyM2dsT2ZyVXBUaVFlNm1COW1xdzFYd3FYZzQ2L1lLMS9sYzVTd1ZXdXdYVXE4SVo1bVUyaGFneWVHeFRxaWFYTnpMSVQ4NDQ1aHFZeDRodG1DdFVMc0Nxc0FPd2VYUURyeEROeVhhVFlpUmZNeWNWbFI0WWc2ZlQ5SVo0Q3lHQmJsSC90U1U5R294bDZSWGx4b0tKa2JBWmJDSWlQaHpKcXljOElCKzlXNDNyM1d3a1FEU1hzNnd3Zm9reFlqQ1ByS3hQVVM0c3FWUHRyWVJ6R21qZWpZSk5lUzNKM0UyQ2Jzcmh1aEZVdmNNRU0rWVNON2JOL3BHWjh0ZGJXSHNaRW82aXBOL3JST1RyQ1V5eW9KT1lMYVVCbWdCY3J0VC84VnA3YUpmcVlRc0RWeVp5RUR6ZENFZ1YwN1RWN2I4SnVJS1Q4Q0FueHhJRlJyLzlJZlpCRk85dXNwejl5OWFrWnc1cVhIR2JzTjUxTUhQNkpsRXhzekN5TmJhR0V4VXd1dktORm5jPSIsIm1hYyI6IjQ1NDI1NDhmYThhODFiN2JkNmM2NDRjOWRjZmIxNDE5ODliNGQ3NjEyZDEzNmYzMTlhZThkZGI0MGI0YWQxNDEiLCJ0YWciOiIifQ%3D%3D&user=7d8f6191d6b3f074c60a8b326466582e&EIO=4&transport=websocket"
AUTH_MESSAGE = os.environ.get("AUTH_MESSAGE") or "7d8f6191d6b3f074c60a8b326466582e"
PING_INTERVAL = int(os.environ.get("PING_INTERVAL", 15))

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8262385394:AAF0saW-oHo-jxVESI5D1QbXu7ACpMfspFU"
GROUP_ID = os.environ.get("GROUP_ID") or "-1002717088045"
CHANNEL_URL = os.environ.get("CHANNEL_URL") or "https://t.me/mrchd112"
DEV_URL = os.environ.get("DEV_URL") or "https://t.me/vxxwo"
CHAT_URL = "https://t.me/DDXOTP"

# -------------------- TELEGRAM --------------------

def send_to_telegram(text):
    retries = 3
    delay = 1

    buttons = {
        "inline_keyboard": [
            [
                {"text": "👑 Channel", "url": CHANNEL_URL},
                {"text": "🖥️ Developer", "url": DEV_URL}
            ],
            [
                {"text": "🤖 Managed By", "url": CHAT_URL},
            ]
        ]
    }

    payload = {
        "chat_id": GROUP_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(buttons)
    }

    for attempt in range(retries):
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data=payload,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Message sent to Telegram")
                return True
            else:
                print(f"⚠️ Telegram Error [{response.status_code}]: {response.text}")
        except Exception as e:
            print(f"❌ Telegram Send Failed (Attempt {attempt+1}/{retries}):", e)
        
        if attempt < retries - 1:
            time.sleep(delay)
    return False

# -------------------- WEBSOCKET FUNCTIONS --------------------

def send_ping(ws):
    global start_pinging
    while getattr(ws, 'keep_running', False):
        if start_pinging:
            try:
                ws.send("3")
                print("📡 Ping sent (3)")
            except Exception as e:
                print("❌ Failed to send ping:", e)
                break
        time.sleep(PING_INTERVAL)

def on_open(ws):
    global start_pinging
    start_pinging = False
    print("✅ WebSocket connected - ON_OPEN CALLED")

    # Send startup notification
    send_to_telegram("🔗 <b>WebSocket Connected</b>\n<i>Service is now monitoring for OTPs...</i>")

    try:
        print("⏳ Waiting before sending namespace connection...")
        time.sleep(1)
        ws.send("40/livesms")
        print("➡️ Sent: 40/livesms")

        print("⏳ Waiting before sending auth...")
        time.sleep(1)
        ws.send(f'42/livesms,["auth","{AUTH_MESSAGE}"]')
        print("🔐 Sent auth token")

        # Start ping thread - make it non-daemon for render
        ping_thread = threading.Thread(target=send_ping, args=(ws,), daemon=False)
        ping_thread.start()
        print("🧵 Ping thread started")
        
    except Exception as e:
        print(f"❌ Error in on_open: {e}")
        send_to_telegram(f"❌ <b>on_open Error</b>\n<code>{str(e)}</code>")

def on_message(ws, message):
    global start_pinging
    print(f"📨 Received: {message}")
    
    if message == "3":
        print("✅ Pong received")
    elif message.startswith("40/livesms"):
        print("✅ Namespace joined — starting ping")
        start_pinging = True
        send_to_telegram("🎯 <b>Authentication Successful</b>\n<i>Ready to receive OTPs...</i>")
    elif message.startswith("42/livesms,"):
        try:
            payload = message[len("42/livesms,"):]
            data = json.loads(payload)

            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], dict):
                sms = data[1]
                raw_msg = sms.get("message", "")
                originator = sms.get("originator", "Unknown")
                recipient = sms.get("recipient", "Unknown")
                country = sms.get("country_iso", "??").upper()

                import re
                otp_match = re.search(r'\b\d{3}[- ]?\d{3}\b|\b\d{6}\b', raw_msg)
                otp = otp_match.group(0) if otp_match else "N/A"

                # Fix masking to handle short numbers
                if len(recipient) > 9:
                    masked = recipient[:5] + '●' * (len(recipient) - 9) + recipient[-4:]
                else:
                    masked = recipient
                    
                now = datetime.now().strftime("%H:%M:%S")
                service = "WhatsApp" if "whatsapp" in raw_msg.lower() else "Unknown"

                # Your exact original message format
                telegram_msg = (
                    "<blockquote>📟 <b><u>New OTP Alert</u></b></blockquote>\n"
                    "─────────────────\n"
                    f"<blockquote>🌍 <b>Country:</b> <code>{country}</code></blockquote>\n"
                    f"<blockquote>🔐 <b>OTP:</b> <code>{otp}</code></blockquote>\n"
                    f"<blockquote>🕐 <b>Time:</b> <code>{now}</code></blockquote>\n"
                    f"<blockquote>📢 <b>Service:</b> <code>{originator}</code></blockquote>\n"
                    f"<blockquote>📱 <b>Number:</b> <code>{masked}</code></blockquote>\n"
                    "─────────────────\n"
                    "<blockquote>💬 <b>Message:</b></blockquote>\n"
                    f"<blockquote><pre>{html.escape(raw_msg)}</pre></blockquote>\n"
                    "─────────────────\n\n"
                    "<blockquote><i>⚡ Delivered instantly via @DDxOTP</i></blockquote>"
                )

                print(f"📨 Sending OTP to Telegram: {otp}")
                send_to_telegram(telegram_msg)

            else:
                print("⚠️ Unexpected data format:", data)

        except Exception as e:
            print("❌ Error parsing message:", e)
            print("Raw message:", message)

def on_error(ws, error):
    print("❌ WebSocket error:", error)

def on_close(ws, code, msg):
    global start_pinging
    start_pinging = False
    print("🔌 WebSocket closed. Reconnecting in 2s...")
    send_to_telegram("🔌 <b>Connection Lost</b>\n<i>Attempting to reconnect...</i>")
    time.sleep(2)
    start_ws_thread()  # Reconnect automatically

def connect():
    global ws_instance
    print("🔄 Connecting to IVASMS WebSocket...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://ivasms.com",
        "Referer": "https://ivasms.com/",
        "Host": "ivasms.com"
    }

    try:
        ws_instance = websocket.WebSocketApp(
            WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            header=[f"{k}: {v}" for k, v in headers.items()]
        )

        ws_instance.run_forever(ping_interval=60, ping_timeout=10)
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        time.sleep(5)
        start_ws_thread()

def start_ws_thread():
    try:
        # Use non-daemon thread for render hosting
        t = threading.Thread(target=connect, daemon=False)
        t.start()
        print("🚀 WebSocket thread started")
    except Exception as e:
        print(f"❌ Failed to start WebSocket thread: {e}")

# -------------------- FLASK WEB SERVICE --------------------

app = Flask(__name__)

@app.route("/")
def root():
    status = "Connected" if ws_instance and hasattr(ws_instance, 'keep_running') and ws_instance.keep_running else "Disconnected"
    return Response(f"""
    <html>
    <head><title>IVASMS Service</title></head>
    <body>
        <h2>🚀 IVASMS WebSocket Service</h2>
        <p><strong>Status:</strong> Running ✅</p>
        <p><strong>WebSocket:</strong> {status}</p>
        <p><strong>Ping Interval:</strong> {PING_INTERVAL}s</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <p><a href="/health">Health Check</a> | <a href="/test">Test Telegram</a></p>
    </body>
    </html>
    """, status=200, mimetype='text/html')

@app.route("/health")
def health():
    return Response("OK", status=200)

@app.route("/test")
def test_telegram():
    test_msg = (
        "<blockquote>🧪 <b><u>Test Message</u></b></blockquote>\n"
        "─────────────────\n"
        f"<blockquote>🕐 <b>Time:</b> <code>{datetime.now().strftime('%H:%M:%S')}</code></blockquote>\n"
        "<blockquote>📡 <b>Status:</b> <code>Service Working</code></blockquote>\n"
        "─────────────────\n\n"
        "<blockquote><i>⚡ Test message via @DDxOTP</i></blockquote>"
    )
    
    success = send_to_telegram(test_msg)
    if success:
        return Response("✅ Test message sent to Telegram", status=200)
    else:
        return Response("❌ Failed to send test message", status=500)

# -------------------- STARTUP --------------------

if __name__ == "__main__":
    print("🚀 Starting IVASMS Service...")
    
    # Test Telegram first
    if send_to_telegram("🚀 <b>Service Started</b>\n<i>IVASMS WebSocket service is initializing...</i>"):
        print("✅ Telegram connection verified")
    
    # Start WebSocket
    start_ws_thread()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Starting Flask server on port {port}")
    
    try:
        app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
    except Exception as e:
        print(f"❌ Flask server error: {e}")
