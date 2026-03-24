from flask import Flask, request, jsonify, send_file
from PIL import Image
import os
import time
from datetime import datetime
import pytz

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- STATE ----------------

events = []   # list of scheduled events

last_heartbeat = 0
HEARTBEAT_TIMEOUT = 3600


# ---------------- ESP STATUS ----------------

def is_esp_online():
    return (time.time() - last_heartbeat) < HEARTBEAT_TIMEOUT


# ---------------- WEB PAGE ----------------

@app.route("/")
def home():

    esp_status = is_esp_online()
    
    if not esp_status:
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Display Control</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f8f9fa;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 48px;
            max-width: 500px;
            text-align: center;
        }
        
        .offline-icon {
            font-size: 56px;
            margin-bottom: 20px;
        }
        
        h1 {
            color: #1a1a1a;
            font-size: 24px;
            margin-bottom: 12px;
            font-weight: 600;
        }
        
        p {
            color: #666;
            font-size: 15px;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="offline-icon">📡</div>
        <h1>Device Offline</h1>
        <p>The ESP device is currently offline. Please check if the device is powered on and connected to the network.</p>
    </div>
</body>
</html>
'''

    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Display Control</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f8f9fa;
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 640px;
            margin: 0 auto;
        }
        
        .header {
            margin-bottom: 32px;
        }
        
        .header h1 {
            color: #1a1a1a;
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .header p {
            color: #666;
            font-size: 15px;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #f0fdf4;
            color: #166534;
            padding: 8px 14px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            margin-top: 12px;
        }
        
        .status-dot {
            width: 6px;
            height: 6px;
            background: #22c55e;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 28px;
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 16px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group:last-child {
            margin-bottom: 0;
        }
        
        label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: #374151;
            margin-bottom: 8px;
        }
        
        .upload-zone {
            border: 2px dashed #d1d5db;
            border-radius: 8px;
            padding: 32px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            background: #fafafa;
        }
        
        .upload-zone:hover {
            border-color: #9ca3af;
            background: #f3f4f6;
        }
        
        .upload-zone.active {
            border-color: #3b82f6;
            background: #eff6ff;
        }
        
        .upload-icon {
            font-size: 32px;
            margin-bottom: 12px;
        }
        
        .upload-text {
            font-size: 15px;
            font-weight: 500;
            color: #1a1a1a;
            margin-bottom: 4px;
        }
        
        .upload-hint {
            font-size: 13px;
            color: #999;
        }
        
        input[type="file"] {
            display: none;
        }
        
        input[type="datetime-local"] {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.2s;
        }
        
        input[type="datetime-local"]:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .preview-section {
            margin-bottom: 20px;
        }
        
        .preview-label {
            font-size: 12px;
            font-weight: 600;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }
        
        #canvas {
            width: 100%;
            max-width: 340px;
            height: auto;
            display: block;
            margin: 0 auto;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            background: white;
            image-rendering: pixelated;
        }
        
        .button-group {
            display: flex;
            gap: 12px;
            margin-top: 28px;
        }
        
        button {
            flex: 1;
            padding: 12px 16px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
        }
        
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        
        .btn-primary:hover {
            background: #2563eb;
        }
        
        .btn-primary:active {
            background: #1d4ed8;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 0;
            }
            
            .card {
                border-radius: 0;
                padding: 20px;
            }
            
            .header h1 {
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>E-Display Control</h1>
            <p>Manage your e-ink display remotely</p>
            <div class="status-badge">
                <span class="status-dot"></span>
                Online
            </div>
        </div>
        
        <form method="POST" action="/upload" enctype="multipart/form-data">
            <div class="card">
                <div class="card-title">📤 Upload Image</div>
                
                <div class="form-group">
                    <label>Select Image</label>
                    <div class="upload-zone" id="upload-zone">
                        <div class="upload-icon">⬆️</div>
                        <div class="upload-text">Drop image here or <span style="color: #3b82f6; cursor: pointer;" onclick="document.getElementById(\'file-input\').click();">browse</span></div>
                        <div class="upload-hint">PNG, JPG — max 10 MB</div>
                    </div>
                    <input type="file" id="file-input" name="file" accept="image/*" onchange="processImage(event)">
                </div>
                
                <div class="preview-section" id="preview-section" style="display: none;">
                    <div class="preview-label">Preview</div>
                    <canvas id="canvas" width="296" height="128"></canvas>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">⏰ Schedule (optional)</div>
                
                <div class="form-group">
                    <label>When to display</label>
                    <input type="datetime-local" id="schedule-time" name="schedule_time" required>
                    <div style="font-size: 12px; color: #999; margin-top: 6px;">Leave empty to push immediately</div>
                </div>
            </div>
            
            <div class="card">
                <div class="button-group">
                    <button type="submit" class="btn-primary">✓ Send Now</button>
                </div>
            </div>
        </form>
    </div>
    
    <script>
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        document.getElementById("schedule-time").value = now.toISOString().slice(0, 16);
        
        function processImage(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = new Image();
                img.onload = function() {
                    const canvas = document.getElementById("canvas");
                    const ctx = canvas.getContext("2d");
                    
                    ctx.drawImage(img, 0, 0, 296, 128);
                    const imageData = ctx.getImageData(0, 0, 296, 128);
                    const data = imageData.data;
                    
                    for (let i = 0; i < data.length; i += 4) {
                        const avg = (data[i] + data[i+1] + data[i+2]) / 3;
                        const bw = avg > 128 ? 255 : 0;
                        data[i] = bw;
                        data[i+1] = bw;
                        data[i+2] = bw;
                    }
                    
                    ctx.putImageData(imageData, 0, 0);
                    document.getElementById("preview-section").style.display = "block";
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
        
        const uploadZone = document.getElementById("upload-zone");
        uploadZone.addEventListener("click", () => {
            document.getElementById("file-input").click();
        });
        
        uploadZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            uploadZone.classList.add("active");
        });
        
        uploadZone.addEventListener("dragleave", () => {
            uploadZone.classList.remove("active");
        });
        
        uploadZone.addEventListener("drop", (e) => {
            e.preventDefault();
            uploadZone.classList.remove("active");
            const files = e.dataTransfer.files;
            document.getElementById("file-input").files = files;
            const event = new Event("change", { bubbles: true });
            document.getElementById("file-input").dispatchEvent(event);
        });
    </script>
</body>
</html>
'''
    

# ---------------- HEARTBEAT ----------------

@app.route("/heartbeat", methods=["POST"])
def heartbeat():

    global last_heartbeat

    last_heartbeat = time.time()

    return jsonify({"status": "ESP online"})


# ---------------- IMAGE UPLOAD ----------------

@app.route("/upload", methods=["POST"])
def upload():

    global events

    file = request.files["file"]
    schedule_str = request.form["schedule_time"]

    ist = pytz.timezone("Asia/Kolkata")

    dt = datetime.strptime(schedule_str,"%Y-%m-%dT%H:%M")
    dt = ist.localize(dt)

    scheduled_time = int(dt.timestamp())

    print("\n------ NEW EVENT ------")
    print("Scheduled timestamp:",scheduled_time)
    print("Current timestamp:",int(time.time()))
    print("-----------------------\n")

    img = Image.open(file)
    img = img.resize((296,128))
    img = img.convert("1")

    # Save preview
    preview_path = os.path.join(UPLOAD_FOLDER,"preview.png")
    img.save(preview_path)

    # Convert to RAW buffer
    pixels = img.load()
    raw_data = bytearray()

    for y in range(128):

        for x_byte in range(296//8):

            byte=0

            for bit in range(8):

                x=x_byte*8+bit

                if pixels[x,y]==0:
                    byte|=(1<<(7-bit))

            raw_data.append(byte)

    filename=f"event_{scheduled_time}.bin"
    path=os.path.join(UPLOAD_FOLDER,filename)

    with open(path,"wb") as f:
        f.write(raw_data)

    events.append({
        "time":scheduled_time,
        "file":filename
    })

    events=sorted(events,key=lambda x:x["time"])

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Successful - E-Display</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f8f9fa;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 48px;
            max-width: 500px;
            text-align: center;
        }}
        
        .success-icon {{
            font-size: 56px;
            margin-bottom: 16px;
        }}
        
        h1 {{
            color: #1a1a1a;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .subtitle {{
            color: #666;
            font-size: 15px;
            margin-bottom: 24px;
            line-height: 1.6;
        }}
        
        .preview-box {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 20px;
            margin: 24px 0;
        }}
        
        .preview-label {{
            font-size: 12px;
            font-weight: 600;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }}
        
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            display: block;
            margin: 0 auto;
        }}
        
        .button-group {{
            display: flex;
            gap: 12px;
            margin-top: 24px;
        }}
        
        a {{
            flex: 1;
            padding: 12px 16px;
            background: #3b82f6;
            color: white;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            transition: background 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }}
        
        a:hover {{
            background: #2563eb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✅</div>
        <h1>Image Sent Successfully!</h1>
        <p class="subtitle">Your image has been processed and scheduled for display.</p>
        
        <div class="preview-box">
            <div class="preview-label">Processed Preview</div>
            <img src="/preview" alt="Processed image">
        </div>
        
        <div class="button-group">
            <a href="/">↻ Upload Another</a>
        </div>
    </div>
</body>
</html>
"""


# ---------------- PREVIEW ----------------

@app.route("/preview")
def preview():

    preview_path=os.path.join(UPLOAD_FOLDER,"preview.png")

    if os.path.exists(preview_path):
        return send_file(preview_path)

    return "No preview available",404


# ---------------- GET NEXT EVENT ----------------

@app.route("/next_event")
def next_event():

    now=int(time.time())
    TOLERANCE = 20   
    for e in events:

        if e["time"]>=now - TOLERANCE:
            return jsonify({
                "timestamp":e["time"],
                "image":e["file"]
            })

    return jsonify({
        "timestamp":0
    })


# ---------------- IMAGE DOWNLOAD ----------------

@app.route("/image/<filename>")
def image(filename):

    path=os.path.join(UPLOAD_FOLDER,filename)

    if os.path.exists(path):
        return send_file(path,mimetype="application/octet-stream")

    return "File not found",404


# ---------------- MARK DISPLAYED & CLEANUP ----------------

@app.route("/mark_displayed/<filename>", methods=["POST"])
def mark_displayed(filename):
    global events
    
    # Remove from events list
    events = [e for e in events if e["file"] != filename]
    
    # Delete the file
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
        print(f"Deleted: {filename}")
    
    return jsonify({"status": "File deleted"})


# ---------------- SERVER START ----------------

if __name__=="__main__":

    app.run(host="0.0.0.0",port=5000)