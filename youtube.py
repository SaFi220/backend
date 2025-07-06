from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re
import yt_dlp

app = Flask(__name__)
CORS(app)

download_folder = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

@app.route('/youtube', methods=['POST'])
def download_media():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Request must be JSON"}), 400

    url = data.get('url')
    media_format = data.get('format')
    if not url or not media_format:
        return jsonify({"error": "Missing 'url' or 'format' parameter"}), 400

    try:
        ext, resolution = media_format.split("-")
        height = int(resolution.replace("p", ""))
    except Exception:
        return jsonify({"error": "Invalid format string. Use format like 'mp4-1080p'"}), 400

    format_selector = (
        f"bestvideo[ext={ext}][height<={height}]+bestaudio[ext=m4a]/"
        f"best[ext={ext}][height<={height}]"
    )

    ydl_options = {
        "format": format_selector,
        "outtmpl": os.path.join(download_folder, "%(title)s.%(ext)s"),
        "merge_output_format": ext,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            raw_title = info.get('title', 'video')
            safe_title = re.sub(r'[<>:"/\\|?*]', '', raw_title)
            final_filename = f"{safe_title}.{ext}"

            # Rename file to safe filename if needed
            final_filepath = os.path.join(download_folder, final_filename)
            if filename != final_filepath:
                os.rename(filename, final_filepath)

        # Return only filename to frontend
        return jsonify({"filename": final_filename}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve the downloaded files with proper attachment headers
@app.route('/downloads/<path:filename>', methods=['GET'])
def serve_download(filename):
    return send_from_directory(download_folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
