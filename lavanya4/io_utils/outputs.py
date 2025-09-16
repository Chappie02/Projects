import json
from pathlib import Path
from typing import Dict, Any


def write_transcripts(transcripts: Dict[str, Any], output_dir: Path) -> None:
	json_path = output_dir / "transcript.json"
	txt_path = output_dir / "transcript.txt"

	with open(json_path, "w", encoding="utf-8") as f:
		json.dump(transcripts, f, ensure_ascii=False, indent=2)

	lines = []
	for speaker_key in sorted(transcripts.keys()):
		spk_name = speaker_key.replace("_", " ").title()
		for seg in transcripts[speaker_key].get("segments", []):
			start = seg.get("start", 0.0)
			end = seg.get("end", 0.0)
			text = seg.get("text", "")
			lines.append(f"[{start:8.2f}-{end:8.2f}] {spk_name}: {text}")

	with open(txt_path, "w", encoding="utf-8") as f:
		f.write("\n".join(lines) + ("\n" if lines else ""))
