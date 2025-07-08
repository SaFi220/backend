from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re
import yt_dlp

app =Flask(__name__)
CORS(app)

download_folder = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

@app.route('/instagram',methods=['POST'])

def download_media():
    data = request.get_json()
    
    if data is None:
        return jsonify({"error":"Request must be JSON"}),400
    
    url = data.get('url')
    media_format = data.get('format')

    if not url or not media_format:
        return jsonify({"error":"Missing 'url' or 'format' parameter"}),400
    
    try:
        ext, resolution = media_format.split("-")
        ext = ext.strip().lower()

        if ext == "mp4":
            height = int(resolution.replace("p", ""))
        elif ext == "mp3":
            bitrate_value = int(resolution.replace("kbps", ""))
        else:
            return jsonify({"error": f"Unsupported format '{ext}'. Use 'mp4' or 'mp3'."}), 400
    except Exception:
        return jsonify({"error": "Invalid format string. Use 'mp4-1080p' or 'mp3-320kbps'."}), 400
    
    if ext == "mp4":
        format_selector = (
            f"bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]/"
            f"best[ext=mp4][height<={height}]"
        )
        ydl_options = {
            "format": format_selector,
            "outtmpl": os.path.join(download_folder, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "force_keyframes_at_cuts": True,
            "allow_unplayable_formats": False,
            "restrict_filenames": True,
        }
    elif ext == "mp3":
        ydl_options = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(download_folder, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": str(bitrate_value),
                },
                {
                    "key": "FFmpegMetadata",
                },
            ],
        }

    try:
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_title = info.get('title', 'media')
            safe_title = re.sub(r'[<>:"/\\|?*]', '', raw_title)

            
            if ext == "mp4":
                final_filename = f"{safe_title}.mp4"
            elif ext == "mp3":
                final_filename = f"{safe_title}.mp3"

            final_filepath = os.path.join(download_folder, final_filename)

        return jsonify({"filename": final_filename}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/downloads/<path:filename>', methods=['GET'])
def serve_download(filename):
    return send_from_directory(download_folder, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, port=5003)
