import os
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import yt_dlp

# -------------------------
# App Initialization
# -------------------------
app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# -------------------------
# Cleaner API
# -------------------------
@app.route('/cleaner', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000', supports_credentials=True)
def cleaner():
    data = request.get_json()
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight OK"}), 200
    if not data:
        return jsonify({"error": "Request must be JSON"}), 400
    status = data.get('status')
    if status == "completed":
        delete_all_files(DOWNLOADS_DIR)
        return jsonify({"message": "All files deleted"}), 200
    return jsonify({"error": "Invalid status"}), 400

def delete_all_files(directory):
    for f in os.listdir(directory):
        path = os.path.join(directory, f)
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            elif os.path.isdir(path):
                pass
        except Exception as e:
            print(f"Failed to delete {path}. Reason: {e}")

# -------------------------
# Generic Downloader Function
# -------------------------
def handle_download(data, platform):
    if not data:
        return jsonify({"error":"Request must be JSON"}), 400
    url = data.get('url')
    media_format = data.get('format')
    cookies = data.get('cookies')  # optional, only for platforms that need it

    if not url or not media_format:
        return jsonify({"error":"Missing 'url' or 'format' parameter"}),400

    # parse format
    try:
        ext, res = media_format.split("-")
        ext = ext.strip().lower()
        if ext == "mp4":
            height = int(res.replace("p", ""))
        elif ext == "mp3":
            bitrate_value = int(res.replace("kbps", ""))
        else:
            return jsonify({"error": f"Unsupported format '{ext}'"}),400
    except:
        return jsonify({"error": "Invalid format string"}),400

    # base options
    ydl_options = {
        "outtmpl": os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "restrict_filenames": True,
    }

    if ext == "mp4":
        ydl_options.update({
            "format": f"bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]/best[ext=mp4][height<={height}]",
            "merge_output_format": "mp4",
        })
    elif ext == "mp3":
        ydl_options.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {"key": "FFmpegExtractAudio","preferredcodec": "mp3","preferredquality": str(bitrate_value)},
                {"key": "FFmpegMetadata"}
            ],
        })

    # platform-specific tweaks
    if platform.lower() in ["instagram", "tiktok", "twitch"]:
        if cookies:
            ydl_options["cookiefile"] = cookies
        else:
            print(f"Warning: {platform} may require authentication via cookies")

    try:
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(url, download=True)
            safe_title = re.sub(r'[<>:"/\\|?*]', '', info.get('title','media'))
            filename = f"{safe_title}.{ext}"
        return jsonify({"filename": filename}),200
    except Exception as e:
        return jsonify({"error": str(e)}),500

# -------------------------
# Download Endpoints
# -------------------------
@app.route('/instagram', methods=['POST'])
def instagram():
    return handle_download(request.get_json(), platform="instagram")

@app.route('/tiktok', methods=['POST'])
def tiktok():
    return handle_download(request.get_json(), platform="tiktok")

@app.route('/twitch', methods=['POST'])
def twitch():
    return handle_download(request.get_json(), platform="twitch")

@app.route('/youtube', methods=['POST'])
def youtube():
    return handle_download(request.get_json(), platform="youtube")

# -------------------------
# Serve Downloads
# -------------------------
@app.route('/downloads/<path:filename>', methods=['GET'])
def serve_download(filename):
    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=True)

# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
