import face_recognition
from flask import Flask, jsonify, request, redirect, render_template_string
import os
import numpy as np
import io
import base64
from PIL import Image

app = Flask(__name__)

# Allowed extensions for manual upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load known faces for demo
EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), 'examples')
known_face_encodings = []
known_face_names = []

def load_demo_faces():
    global known_face_encodings, known_face_names
    try:
        obama_path = os.path.join(EXAMPLES_DIR, 'obama.jpg')
        biden_path = os.path.join(EXAMPLES_DIR, 'biden.jpg')
        
        if os.path.exists(obama_path):
            obama_image = face_recognition.load_image_file(obama_path)
            obama_enc = face_recognition.face_encodings(obama_image)
            if obama_enc:
                known_face_encodings.append(obama_enc[0])
                known_face_names.append("Barack Obama")
            
        if os.path.exists(biden_path):
            biden_image = face_recognition.load_image_file(biden_path)
            biden_enc = face_recognition.face_encodings(biden_image)
            if biden_enc:
                known_face_encodings.append(biden_enc[0])
                known_face_names.append("Joe Biden")
    except Exception as e:
        print(f"Error loading demo faces: {e}")

load_demo_faces()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI FaceID | Premium Recognition</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-light: #818cf8;
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --glass: rgba(255, 255, 255, 0.03);
            --border: rgba(255, 255, 255, 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
        }

        body {
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 40%);
        }

        .container {
            max-width: 1200px;
            width: 95%;
            padding: 4rem 0;
            text-align: center;
        }

        header {
            margin-bottom: 4rem;
            animation: fadeInDown 0.8s ease-out;
        }

        h1 {
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(to right, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.05em;
        }

        p.explanation {
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid var(--primary);
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            color: var(--primary-light);
            font-weight: 600;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 2rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            align-items: center;
            animation: fadeInUp 0.8s ease-out;
        }

        .card:hover {
            transform: translateY(-8px);
            border-color: var(--primary);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }

        .icon-box {
            width: 50px;
            height: 50px;
            background: rgba(99, 102, 241, 0.1);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1rem;
            color: var(--primary);
            font-size: 1.2rem;
        }

        input[type="text"] {
            width: 100%;
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--border);
            color: white;
            padding: 0.8rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            outline: none;
        }

        input[type="text"]:focus {
            border-color: var(--primary);
        }

        .upload-zone {
            width: 100%;
            border: 2px dashed rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 1.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .upload-zone:hover {
            border-color: var(--primary);
            background: rgba(255,255,255,0.02);
        }

        .webcam-container {
            width: 100%;
            aspect-ratio: 4/3;
            background: #000;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 1rem;
        }

        video { width: 100%; height: 100%; object-fit: cover; }

        .btn {
            background: var(--primary);
            color: white; border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 1rem;
        }
        .btn:hover { background: var(--primary-light); }
        .btn-register { background: #10b981; }
        .btn-register:hover { background: #34d399; }

        #results { margin-top: 3rem; width: 100%; display: none; }
        .result-card {
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid var(--primary);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex; align-items: center;
            justify-content: space-between;
        }

        .loading-spinner {
            width: 20px; height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
            display: inline-block; vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AI FaceID</h1>
            <p class="subtitle">State-of-the-art face recognition. Register yourself first to enable matching!</p>
        </header>

        <p class="explanation">💡 Step 1: Register your name and face. <br> Step 2: Use matching to identify yourself.</p>

        <div class="grid">
            <!-- Registration Card -->
            <div class="card">
                <div class="icon-box">✍️</div>
                <h3>1. Register Face</h3>
                <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">Add a new person to the system</p>
                <input type="text" id="regName" placeholder="Enter Full Name">
                <div class="upload-zone" onclick="document.getElementById('regFileInput').click()">
                    <span id="regUploadText">Upload Portrait</span>
                    <input type="file" id="regFileInput" class="hidden" accept="image/*">
                </div>
                <button class="btn btn-register" id="regBtn">Enroll Member</button>
            </div>

            <!-- Upload Match Card -->
            <div class="card">
                <div class="icon-box">🔍</div>
                <h3>2. Identify Photo</h3>
                <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">Match uploaded image against database</p>
                <div class="upload-zone" onclick="document.getElementById('fileInput').click()">
                    <span id="uploadText">Search by Photo</span>
                    <input type="file" id="fileInput" class="hidden" accept="image/*">
                </div>
                <button class="btn" id="uploadBtn">Verify Identity</button>
            </div>

            <!-- Webcam Match Card -->
            <div class="card">
                <div class="icon-box">📷</div>
                <h3>3. Live ID</h3>
                <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">Instant recognition via Webcam</p>
                <div class="webcam-container">
                    <video id="video" autoplay muted></video>
                    <canvas id="canvas" class="hidden"></canvas>
                </div>
                <button class="btn" id="captureBtn">Live Scan</button>
            </div>
        </div>

        <div id="results">
            <div class="result-card">
                <div class="result-info" style="text-align: left;">
                    <h3 id="resName">Processing...</h3>
                    <p id="resDetails"></p>
                </div>
                <div id="resIcon" style="font-size: 2rem;">⏳</div>
            </div>
        </div>
    </div>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const captureBtn = document.getElementById('captureBtn');
        const uploadBtn = document.getElementById('uploadBtn');
        const regBtn = document.getElementById('regBtn');
        
        const fileInput = document.getElementById('fileInput');
        const regFileInput = document.getElementById('regFileInput');
        const regNameInput = document.getElementById('regName');
        const resultsDiv = document.getElementById('results');
        const resName = document.getElementById('resName');
        const resDetails = document.getElementById('resDetails');
        const resIcon = document.getElementById('resIcon');

        async function setupWebcam() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                video.srcObject = stream;
            } catch (err) {
                captureBtn.disabled = true;
                captureBtn.innerText = "No Webcam";
            }
        }
        setupWebcam();

        regBtn.onclick = async () => {
            const name = regNameInput.value.trim();
            const file = regFileInput.files[0];
            if (!name || !file) return alert("Enter name and select a photo");
            
            setLoading(regBtn, true);
            const formData = new FormData();
            formData.append('name', name);
            formData.append('file', file);
            
            const res = await fetch('/register', { method: 'POST', body: formData });
            const data = await res.json();
            alert(data.message || data.error);
            setLoading(regBtn, false);
            if(data.success) {
                regNameInput.value = '';
                document.getElementById('regUploadText').innerText = "Portrait Uploaded!";
            }
        };

        uploadBtn.onclick = async () => {
            if (!fileInput.files[0]) return alert("Select a file first");
            setLoading(uploadBtn, true);
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            await handleAction('/recognize', formData, uploadBtn);
        };

        captureBtn.onclick = async () => {
            setLoading(captureBtn, true);
            const context = canvas.getContext('2d');
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg'));
            const formData = new FormData();
            formData.append('file', blob, 'scan.jpg');
            await handleAction('/recognize', formData, captureBtn);
        };

        async function handleAction(url, formData, btn) {
            try {
                const response = await fetch(url, { method: 'POST', body: formData });
                const data = await response.json();
                showResult(data);
            } catch (err) { alert("Server Error"); }
            finally { setLoading(btn, false); }
        }

        function showResult(data) {
            resultsDiv.style.display = 'block';
            resultsDiv.scrollIntoView({ behavior: 'smooth' });
            if (data.match) {
                resName.innerText = `Verified: ${data.name}`;
                resDetails.innerText = "Multiple biometric points matched successfully.";
                resIcon.innerText = "✔️";
            } else if (data.face_found) {
                resName.innerText = "Unknown Identity";
                resDetails.innerText = "Face detected, but not registered in database.";
                resIcon.innerText = "🕵️";
            } else {
                resName.innerText = "No Face Found";
                resDetails.innerText = "Check lighting and center your face.";
                resIcon.innerText = "❌";
            }
        }

        function setLoading(btn, isLoading) {
            if (isLoading) {
                btn.disabled = true; btn._orig = btn.innerText;
                btn.innerHTML = `<span class="loading-spinner"></span>`;
            } else {
                btn.disabled = false; btn.innerText = btn._orig;
            }
        }

        fileInput.onchange = () => { document.getElementById('uploadText').innerText = fileInput.files[0]?.name || "Search by Photo"; };
        regFileInput.onchange = () => { document.getElementById('regUploadText').innerText = regFileInput.files[0]?.name || "Portrait Uploaded!"; };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    file = request.files.get('file')
    if not name or not file: return jsonify({"error": "Missing name or file"}), 400
    try:
        img = face_recognition.load_image_file(file)
        encodings = face_recognition.face_encodings(img)
        if not encodings: return jsonify({"error": "No face found in registration image"}), 400
        known_face_encodings.append(encodings[0])
        known_face_names.append(name)
        return jsonify({"success": True, "message": f"Successfully registered {name}!"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/recognize', methods=['POST'])
def recognize():
    file = request.files.get('file')
    if not file: return jsonify({"error": "No file uploaded"}), 400
    try:
        img = face_recognition.load_image_file(file)
        encs = face_recognition.face_encodings(img)
        if not encs: return jsonify({"face_found": False, "match": False})
        unknown_enc = encs[0]
        if not known_face_encodings: return jsonify({"face_found": True, "match": False})
        matches = face_recognition.compare_faces(known_face_encodings, unknown_enc, tolerance=0.6)
        name = "Unknown"; match_found = False
        if True in matches:
            distances = face_recognition.face_distance(known_face_encodings, unknown_enc)
            best_idx = np.argmin(distances)
            if matches[best_idx]:
                name = known_face_names[best_idx]
                match_found = True
        return jsonify({"face_found": True, "match": match_found, "name": name})
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
