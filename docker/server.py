import os
import uuid
import subprocess
import tempfile
import drive
from flask import Flask, request, send_file, jsonify


app = Flask(__name__)

@app.route("/render", methods=["POST"])
#get code, render, and return video
def render():
    data = request.get_json()
    code = data.get("code", "") 
    scene_name = data.get("scene", None)

    if not code:
        return jsonify({"error": "No code provided"}), 400

    # job_id = str(uuid.uuid4())
    # work_dir = f"/tmp/manim_{job_id}"
    # os.makedirs(work_dir, exist_ok=True)
    
    job_id = str(uuid.uuid4())
    base_tmp_dir = tempfile.gettempdir() 
    work_dir = os.path.join(base_tmp_dir, f"manim_{job_id}")
    os.makedirs(work_dir, exist_ok=True)

    script_path = os.path.join(work_dir, "scene.py")
    with open(script_path, "w") as f:
        f.write(code)

    cmd = ["manim", "-ql", "--media_dir", work_dir, script_path]
    if scene_name:
        cmd.append(scene_name)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Render timed out"}), 504

    # Find the output mp4
    for root, dirs, files in os.walk(work_dir):
        for f in files:
            if f.endswith(".mp4"):
                
                # drive.upload_file(os.path.join(root, f), f)
                
                return send_file(
                    os.path.join(root, f),
                    mimetype="video/mp4",
                    as_attachment=False
                )

    return jsonify({"error": "No video output found"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)