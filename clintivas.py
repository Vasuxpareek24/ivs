import websocket
import threading
import time
import json
import requests
from datetime import datetime
import html
import os
from flask import Flask, Response

# -------------------- CONFIG --------------------

PING_INTERVAL = 15
start_pinging = False

WS_URL = os.environ.get("WS_URL") or "wss://ivasms.com:2087/socket.io/?token=eyJpdiI6IkxDaWhpcEVYQXhNWlZMWE5yU3Y1V3c9PSIsInZhbHVlIjoicCtSUnZDeVJiVytzalZia1VqNE9rRDRZUThsRVFncjIwdlBjUm9Mb2NuQ2lad1hjaUNJWC9iWU5DZXhXVWpkOE5tdHVDZ2FkdjZhSEhMd2tMUXFVUG5CUVM4eUY1TDdkVmNZa0Uzd0hEaG4vWm9jdktHWjh1MXNrZW4yOWgrUmlrdE1IVkt0cEp1Y1pRakhNNjhGNUgxVGlRUUw2K0RkQThGQ2VuYlhncVFyRk43cTVOcVdmNWJ6L0NHWnJBbGlSeDUvaE5NVzFjMzgvNnUySUUvM0xyWUF6VFp0NU5tQ1haS3NtR1RvbmNsV1FVcEhZSThPa1c5N2cwTFcvVHJnWUdQUFJ2SjQ2YVZ6WHNkb2hVcWk2bTMrVnBDUDhlTnlVM3J5RDhaOGErb0ZKRjAwSXVMRFBSWmlXNEZubVlPS28xSWNMSEpRdGhsM3VuYktTUzQzdmdNNnEvQUtvMEZzUW9xZkJQcHVBSlZHek52QUFTSlJpQnJKYnUxZ3ZOakNiVXZlUnd1WkZLVVdreWdQOVZ3TVRNR1orYmRSODd4WE5BOURxc202MzVnbElRNnFFUm1sb3dYb3k3S2MyUXM3WGFtc3lLZFJWbkxLRlZuU0dGbzJENnYrQmc3aVJ0YUJpZUduaVE2aC9Cd0NwcGVlWHdTTWlvWURSeStFOFNnVU8rTXdONGxZVldrWGtjR1FwKzRaVlh3PT0iLCJtYWMiOiJmN2ZjNjg0NjAwZDRjYjgyYmVmYTI1YmQ1NzUwZjYwNzQwZTJkOGRlZDEyODQ1N2U5NjBmMjMzZTY4NTJmYTk3IiwidGFnIjoiIn0%3D&user=8d75eedc6d2833853cf8fea9790e711a&EIO=4&transport=websocket"
AUTH_MESSAGE = os.environ.get("AUTH_MESSAGE") or "8d75eedc6d2833853cf8fea9790e711a"
PING_INTERVAL = int(os.environ.get("PING_INTERVAL", 25))

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8270301262:AAEldMmzcGK9sRbYk9WrFz6MqYE42EDnwlc"
GROUP_ID = os.environ.get("GROUP_ID") or "-4967707436"
CHANNEL_URL = os.environ.get("CHANNEL_URL") or "https://t.me/mrchd112"
DEV_URL = os.environ.get("DEV_URL") or "https://t.me/vxxwo"
CHAT_URL = "https://t.me/DDXOTP"

# Global WebSocket instance
ws_instance = None
connection_initialized = False

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

def initialize_connection(ws):
    """Manually initialize connection if on_open doesn't trigger"""
    global connection_initialized, start_pinging
    
    if connection_initialized:
        return
        
    try:
        print("🔧 Manually initializing WebSocket connection...")
        send_to_telegram("🔗 <b>WebSocket Connected</b>\n<i>Service is now monitoring for OTPs...</i>")
        
        time.sleep(1)
        ws.send("40/livesms")
        print("➡️ Sent: 40/livesms")

        time.sleep(1)
        ws.send(f'42/livesms,["auth","{AUTH_MESSAGE}"]')
        print("🔐 Sent auth token")

        # Start ping thread
        ping_thread = threading.Thread(target=send_ping, args=(ws,), daemon=False)
        ping_thread.start()
        
        connection_initialized = True
        print("✅ Connection initialized manually")
        
    except Exception as e:
        print(f"❌ Error in manual initialization: {e}")

def on_open(ws):
    global start_pinging, connection_initialized
    start_pinging = False
    connection_initialized = False
    print("✅ WebSocket on_open triggered")
    
    initialize_connection(ws)

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

                # Fix masking for short numbers
                if len(recipient) > 9:
                    masked = recipient[:5] + '●' * (len(recipient) - 9) + recipient[-4:]
                else:
                    masked = recipient
                    
                now = datetime.now().strftime("%H:%M:%S")

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
    global start_pinging, connection_initialized
    start_pinging = False
    connection_initialized = False
    print("🔌 WebSocket closed. Reconnecting in 2s...")
    time.sleep(2)
    start_ws_thread()

def connect():
    global ws_instance, connection_initialized
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

        # Start connection
        connection_thread = threading.Thread(target=lambda: ws_instance.run_forever(), daemon=False)
        connection_thread.start()
        
        # Wait and check if on_open was called
        time.sleep(3)
        if not connection_initialized and hasattr(ws_instance, 'sock') and ws_instance.sock:
            print("🔧 on_open not triggered, manually initializing...")
            initialize_connection(ws_instance)
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

def start_ws_thread():
    try:
        t = threading.Thread(target=connect, daemon=False)
        t.start()
        print("🚀 WebSocket thread started")
    except Exception as e:
        print(f"❌ Failed to start thread: {e}")

# -------------------- FLASK WEB SERVICE --------------------

app = Flask(__name__)

@app.route("/")
def root():
    global connection_initialized
    status = "✅ Connected" if connection_initialized else "❌ Disconnected"
    return Response(f"""
    <html>
    <head><title>IVASMS Service</title></head>
    <body>
        <h2>🚀 IVASMS WebSocket Service</h2>
        <p><strong>Status:</strong> {status}</p>
        <p><strong>Ping Interval:</strong> {PING_INTERVAL}s</p>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <p><a href="/health">Health Check</a> | <a href="/test">Test Telegram</a> | <a href="/force-init">Force Init</a></p>
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
    return Response("✅ Test message sent" if success else "❌ Failed to send", status=200 if success else 500)

@app.route("/force-init")
def force_init():
    global ws_instance
    if ws_instance and hasattr(ws_instance, 'sock') and ws_instance.sock:
        initialize_connection(ws_instance)
        return Response("✅ Force initialization triggered", status=200)
    else:
        return Response("❌ WebSocket not connected", status=500)

# -------------------- STARTUP --------------------

if __name__ == "__main__":
    print("🚀 Starting IVASMS Service...")
    
    # Test Telegram
    if send_to_telegram("🚀 <b>Service Started</b>\n<i>IVASMS WebSocket service is initializing...</i>"):
        print("✅ Telegram connection verified")
    
    # Start WebSocket
    start_ws_thread()
    
    # Start Flask
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Starting Flask server on port {port}")
    
    try:
        app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
    except Exception as e:
        print(f"❌ Flask server error: {e}")
