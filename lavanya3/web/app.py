import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, render_template, request, redirect, url_for, send_file, abort

from audio_utils.io import ensure_wav_mono_16k
from separation.sepformer import separate_speakers
from transcription.whisper_transcriber import transcribe_files
from io_utils.outputs import write_transcripts
from io_utils.zip_utils import zip_directory


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = BASE_DIR / "output"
UPLOAD_DIR = BASE_DIR / "uploads"

app = Flask(__name__, template_folder="templates", static_folder="static")


def _make_job_dir() -> Path:
	UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
	DEFAULT_OUTPUT.mkdir(parents=True, exist_ok=True)
	job_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
	job_dir = DEFAULT_OUTPUT / job_id
	job_dir.mkdir(parents=True, exist_ok=True)
	return job_dir


@app.route("/", methods=["GET", "POST"])
def index():
	if request.method == "POST":
		file = request.files.get("audio")
		num_speakers = int(request.form.get("num_speakers", 2))
		whisper_model = request.form.get("whisper_model", "base")
		if not file or file.filename == "":
			return render_template("index.html", error="Please choose an audio file.")

		job_dir = _make_job_dir()
		upload_path = job_dir / file.filename
		file.save(str(upload_path))

		try:
			prepared_wav = ensure_wav_mono_16k(upload_path, job_dir / "prepared.wav")
			separated_paths: List[Path] = separate_speakers(prepared_wav, job_dir, num_speakers=num_speakers)
			transcripts: Dict[str, Any] = transcribe_files(separated_paths, model_name=whisper_model)
			write_transcripts(transcripts, job_dir)
			zip_path = job_dir / "results.zip"
			zip_directory(job_dir, zip_path, include_parent=False)
		except Exception as e:
			return render_template("index.html", error=str(e))

		return redirect(url_for("result", job_id=job_dir.name))

	return render_template("index.html")


@app.route("/result/<job_id>")
def result(job_id: str):
	job_dir = DEFAULT_OUTPUT / job_id
	if not job_dir.exists():
		abort(404)

	files = sorted([p.name for p in job_dir.glob("speaker_*.wav")])
	json_exists = (job_dir / "transcript.json").exists()
	txt_exists = (job_dir / "transcript.txt").exists()
	zip_exists = (job_dir / "results.zip").exists()
	return render_template(
		"result.html",
		job_id=job_id,
		speaker_files=files,
		json_exists=json_exists,
		txt_exists=txt_exists,
		zip_exists=zip_exists,
	)


@app.route("/download/<job_id>/<path:filename>")
def download_file(job_id: str, filename: str):
	job_dir = DEFAULT_OUTPUT / job_id
	path = (job_dir / filename).resolve()
	if not path.exists() or job_dir not in path.parents:
		abort(404)
	return send_file(str(path), as_attachment=True)


@app.route("/download_zip/<job_id>")
def download_zip(job_id: str):
	job_dir = DEFAULT_OUTPUT / job_id
	zip_path = job_dir / "results.zip"
	if not zip_path.exists():
		abort(404)
	return send_file(str(zip_path), as_attachment=True)


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000, debug=True)
