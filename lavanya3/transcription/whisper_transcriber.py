from pathlib import Path
from typing import Dict, Any, List

import whisper


def transcribe_files(audio_paths: List[Path], model_name: str = "base") -> Dict[str, Any]:
	"""Transcribe each audio in audio_paths using Whisper.

	Returns a dict keyed by speaker file stem (e.g., speaker_1) with fields:
	- file: path string
	- segments: list of {start, end, text}
	- text: concatenated transcript
	"""
	model = whisper.load_model(model_name)
	result: Dict[str, Any] = {}
	for ap in audio_paths:
		out = model.transcribe(str(ap), fp16=False, temperature=0.0)
		segments = [
			{"start": float(seg.get("start", 0.0)), "end": float(seg.get("end", 0.0)), "text": seg.get("text", "").strip()}
			for seg in out.get("segments", [])
		]
		full_text = " ".join([s["text"] for s in segments]).strip()
		result[ap.stem] = {
			"file": str(ap),
			"segments": segments,
			"text": full_text,
		}
	return result
