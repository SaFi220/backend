import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app  = Flask(__name__)
CORS(app)

@app.route('/cleaner',methods=['POST'])
def get_response():
    response = request.get_json()
    if response is None:
        return jsonify({"error":"Request must be JSON"}),400
    status = response.get('status')
    if status == "completed":
        delete_all_files('C:\Users\MM2\Desktop\videoGrab\backend\downloads')
        return jsonify({"message":"All files deleted"}),200
    elif response == "failed":
        return jsonify({"error","Delete failed"}),400


def delete_all_files(directory_path):
    if not os.path.exists(directory_path):
        print(f"The directory {directory_path} does not exist.")
        return

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  
                print(f"Deleted file: {file_path}")
            elif os.path.isdir(file_path):
                print(f"Skipping directory: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)

