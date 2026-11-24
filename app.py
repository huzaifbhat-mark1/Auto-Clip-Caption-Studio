import os
import uuid
from flask import Flask, request, send_from_directory, render_template_string
from clipper import process_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Auto-Clip & Caption Studio (Free Ad-Supported)</title>
  <style>
    * { box-sizing: border-box; font-family: Arial, sans-serif; }
    body { margin: 0; background: #0d0f14; color: #f3f4f6; }
    .container { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
    .ad-slot {
      background: #161a24;
      border: 1px dashed #3b4254;
      color: #9ca3af;
      text-align: center;
      padding: 14px;
      border-radius: 8px;
      font-size: 13px;
      margin-bottom: 20px;
    }
    .card {
      background: #151922;
      border: 1px solid #262c3a;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 20px;
    }
    h1 { margin: 0 0 8px; font-size: 26px; }
    p.sub { margin: 0 0 20px; color: #9ca3af; }
    label { display: block; margin-bottom: 6px; font-weight: bold; font-size: 14px; }
    input[type="file"], input[type="number"] {
      width: 100%;
      padding: 10px;
      margin-bottom: 16px;
      background: #0d0f14;
      color: #fff;
      border: 1px solid #303748;
      border-radius: 8px;
    }
    .hint { display: block; margin-top: -10px; margin-bottom: 16px; color: #9ca3af; font-size: 12px; }
    button {
      background: #22c55e;
      color: #07130b;
      border: none;
      padding: 12px 20px;
      font-size: 15px;
      font-weight: bold;
      border-radius: 8px;
      cursor: pointer;
    }
    button:hover { background: #16a34a; }
    .result-box {
      background: #102418;
      border: 1px solid #22c55e;
      padding: 16px;
      border-radius: 10px;
      margin-top: 16px;
    }
    a.download-btn {
      display: inline-block;
      margin-top: 10px;
      background: #facc15;
      color: #111;
      text-decoration: none;
      padding: 10px 16px;
      border-radius: 8px;
      font-weight: bold;
    }
    .error-box {
      background: #2b1215;
      border: 1px solid #ef4444;
      color: #fecaca;
      padding: 14px;
      border-radius: 8px;
      margin-top: 14px;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="ad-slot" id="ad-top-banner">
      TOP BANNER AD SLOT (728x90 / Responsive) — Free for Clippers, Monetized via Ads
    </div>

    <div class="card">
      <h1>Auto-Clip & Caption Studio</h1>
      <p class="sub">100% Free Watermark-Free 9:16 Vertical Clipper + Active Word Captions</p>

      <form method="POST" enctype="multipart/form-data">
        <label for="video">Select Source Video (.mp4, .mov, .mkv)</label>
        <input type="file" id="video" name="video" accept="video/*" required />

        <label for="start_time">Start Time (seconds)</label>
        <input type="number" id="start_time" name="start_time" value="0" min="0" max="36000" step="1" />
        <span class="hint">Enter 0 to start from the beginning (or enter any second like 15, 45, 120 to cut that exact section).</span>

        <label for="duration">Clip Duration (seconds)</label>
        <input type="number" id="duration" name="duration" value="30" min="10" max="120" step="1" required />

        <button type="submit">Generate Viral Clip</button>
      </form>

      {% if error %}
        <div class="error-box">{{ error }}</div>
      {% endif %}

      {% if output_file %}
        <div class="ad-slot" id="ad-download-slot" style="margin-top: 18px;">
          SPONSOR / AD SLOT — Clip Ready Below
        </div>

        <div class="result-box">
          <strong>Your clip is ready!</strong><br />
          <a class="download-btn" href="/download/{{ output_file }}" download>Download {{ output_file }}</a>
        </div>
      {% endif %}
    </div>

    <div class="ad-slot" id="ad-bottom-banner">
      BOTTOM BANNER AD SLOT — Support Free Tools via Ad Views
    </div>
  </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    output_file = None
    error = None

    if request.method == "POST":
        uploaded = request.files.get("video")
        duration_raw = request.form.get("duration", "30")
        start_raw = request.form.get("start_time", "0")

        if not uploaded or not uploaded.filename:
            error = "Please choose a video file first."
        else:
            try:
                duration = float(duration_raw)
            except ValueError:
                duration = 30.0

            try:
                start_time = float(start_raw) if start_raw.strip() != "" else 0.0
            except ValueError:
                start_time = 0.0

            ext = os.path.splitext(uploaded.filename)[1] or ".mp4"
            job_id = uuid.uuid4().hex[:8]
            input_path = os.path.join(UPLOAD_DIR, f"{job_id}_input{ext}")
            out_name = f"{job_id}_viral_clip.mp4"
            output_path = os.path.join(OUTPUT_DIR, out_name)

            uploaded.save(input_path)

            try:
                process_video(input_path, output_path, clip_duration=duration, start_time=start_time)
                if os.path.exists(output_path):
                    output_file = out_name
                else:
                    error = "No speech was detected or output file was not created."
            except Exception as exc:
                error = f"Processing failed: {exc}"

    return render_template_string(HTML_TEMPLATE, output_file=output_file, error=error)


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)