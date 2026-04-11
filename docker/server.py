import os
import uuid
import subprocess
import tempfile
import time
import ast
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)


def count_animations_ast(code: str) -> int:
    try:
        tree = ast.parse(code)

        # Resolve named list lengths from assignments e.g. values = [1, 2, 6, 3, 6]
        list_lengths = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(
                        node.value, ast.List
                    ):
                        list_lengths[target.id] = len(node.value.elts)

        inside_loop_nodes = set()  # track nodes already counted inside a loop

        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                iter_ = node.iter
                loop_count = 1

                if isinstance(iter_, ast.Call):
                    func_name = getattr(iter_.func, "id", None)
                    if func_name == "range" and iter_.args:
                        try:
                            if len(iter_.args) == 1:
                                loop_count = ast.literal_eval(iter_.args[0])
                            elif len(iter_.args) == 2:
                                loop_count = ast.literal_eval(
                                    iter_.args[1]
                                ) - ast.literal_eval(iter_.args[0])
                        except:
                            loop_count = 1
                    elif func_name == "enumerate" and iter_.args:
                        arg = iter_.args[0]
                        if isinstance(arg, ast.Name):
                            loop_count = list_lengths.get(arg.id, 1)
                        elif isinstance(arg, ast.List):
                            loop_count = len(arg.elts)
                elif isinstance(iter_, ast.Name):
                    loop_count = list_lengths.get(iter_.id, 1)

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if (
                            isinstance(func, ast.Attribute)
                            and func.attr in ("play", "wait")
                            and isinstance(func.value, ast.Name)
                            and func.value.id == "self"
                        ):
                            inside_loop_nodes.add(id(child))
                            count += loop_count

            elif isinstance(node, ast.Call) and id(node) not in inside_loop_nodes:
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr in ("play", "wait")
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "self"
                ):
                    count += 1

        print(
            f"[count_animations_ast] Found {count} play/wait calls (loop-aware)",
            flush=True,
        )
        return max(count, 1)
    except SyntaxError as e:
        print(f"[count_animations_ast] SyntaxError: {e}", flush=True)
        return 1


def render_chunk(
    code: str, scene_name: str, work_dir: str, chunk_idx: int, start: int, end: int
) -> str:

    chunk_dir = os.path.join(work_dir, f"chunk_{chunk_idx}")
    os.makedirs(chunk_dir, exist_ok=True)

    script_path = os.path.join(chunk_dir, "scene.py")
    with open(script_path, "w") as f:
        f.write(code)

    print(f"[chunk_{chunk_idx}] Rendering animations [{start}, {end}) ...", flush=True)

    t0 = time.perf_counter()
    result = subprocess.run(
        [
            "manim",
            "-ql",
            "--media_dir",
            chunk_dir,
            script_path,
            scene_name,
            "-n",
            f"{start},{end}",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    print(
        f"[chunk_{chunk_idx}] render took {round((time.perf_counter()-t0)*1000)}ms",
        flush=True,
    )

    print(f"[chunk_{chunk_idx}] returncode={result.returncode}", flush=True)
    if result.returncode != 0:
        print(f"[chunk_{chunk_idx}] stderr={result.stderr[-500:]}", flush=True)
        raise RuntimeError(f"Chunk {chunk_idx} failed:\n{result.stderr[-500:]}")

    for root, _, files in os.walk(chunk_dir):
        for f in files:
            if f.endswith(".mp4"):
                print(f"[chunk_{chunk_idx}] Found output: {f}", flush=True)
                return os.path.join(root, f)

    raise RuntimeError(f"Chunk {chunk_idx}: no video output found")


def concat_videos(video_paths: List[str], output_path: str) -> None:
    list_file = output_path + ".txt"
    with open(list_file, "w") as f:
        for p in video_paths:
            f.write(f"file '{p}'\n")

    print(
        f"[concat] Concatenating {len(video_paths)} chunks -> {output_path}", flush=True
    )

    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_file,
            "-c",
            "copy",
            output_path,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    os.unlink(list_file)

    if result.returncode != 0:
        print(f"[concat] ffmpeg stderr={result.stderr}", flush=True)
        raise RuntimeError(f"ffmpeg concat failed:\n{result.stderr}")

    print(f"[concat] Done.", flush=True)


@app.route("/render", methods=["POST"])
def render():
    data = request.get_json()
    code = data.get("code", "")
    scene_name = data.get("scene", None)

    if not code:
        return jsonify({"error": "No code provided"}), 400

    job_id = str(uuid.uuid4())
    work_dir = os.path.join(tempfile.gettempdir(), f"manim_{job_id}")
    os.makedirs(work_dir, exist_ok=True)

    script_path = os.path.join(work_dir, "scene.py")
    with open(script_path, "w") as f:
        f.write(code)

    cmd = ["manim", "-ql", "--media_dir", work_dir, script_path]
    if scene_name:
        cmd.append(scene_name)

    print(f"[render] Starting job {job_id}", flush=True)
    t0 = time.perf_counter()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        render_duration_ms = round((time.perf_counter() - t0) * 1000)
        if result.returncode != 0:
            print(f"[render] Failed: {result.stderr[-300:]}", flush=True)
            return jsonify({"error": result.stderr}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Render timed out"}), 504

    print(f"[render] Done in {render_duration_ms}ms", flush=True)

    for root, _, files in os.walk(work_dir):
        for f in files:
            if f.endswith(".mp4"):
                response = send_file(
                    os.path.join(root, f),
                    mimetype="video/mp4",
                    as_attachment=False,
                )
                response.headers["X-Render-Duration-Ms"] = str(render_duration_ms)
                return response

    return jsonify({"error": "No video output found"}), 500


@app.route("/render_fast", methods=["POST"])
def render_fast():
    data = request.get_json()
    code = data.get("code", "")
    scene_name = data.get("scene", None)
    chunks = int(data.get("chunks", 4))

    if not code:
        return jsonify({"error": "No code provided"}), 400

    job_id = str(uuid.uuid4())
    work_dir = os.path.join(tempfile.gettempdir(), f"manim_fast_{job_id}")
    os.makedirs(work_dir, exist_ok=True)

    print(f"[render_fast] Starting job {job_id} with {chunks} chunks", flush=True)
    t0 = time.perf_counter()

    total_anims = count_animations_ast(code)
    chunks = min(chunks, total_anims)

    ranges = [
        (i, (i * total_anims) // chunks, ((i + 1) * total_anims) // chunks)
        for i in range(chunks)
    ]
    ranges = [(i, s, e) for i, s, e in ranges if s < e]

    print(f"[render_fast] total_anims={total_anims}, ranges={ranges}", flush=True)

    chunk_paths: List[str | None] = [None] * len(ranges)
    with ThreadPoolExecutor(max_workers=len(ranges)) as executor:
        futures = {
            executor.submit(render_chunk, code, scene_name, work_dir, i, s, e): i
            for i, s, e in ranges
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                chunk_paths[idx] = future.result()
            except RuntimeError as e:
                print(f"[render_fast] Chunk {idx} skipped: {e}", flush=True)

    chunk_paths = [p for p in chunk_paths if p is not None]
    print(f"[render_fast] Chunk paths: {chunk_paths}", flush=True)

    if not chunk_paths:
        return jsonify({"error": "No chunks rendered successfully"}), 500

    output_path = os.path.join(work_dir, "final.mp4")
    try:
        concat_videos(chunk_paths, output_path)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    render_duration_ms = round((time.perf_counter() - t0) * 1000)
    print(f"[render_fast] Total time: {render_duration_ms}ms", flush=True)

    response = send_file(output_path, mimetype="video/mp4", as_attachment=False)
    response.headers["X-Render-Duration-Ms"] = str(render_duration_ms)
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
