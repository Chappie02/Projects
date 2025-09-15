import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from rich import print
from rich.console import Console

from audio_utils.io import ensure_wav_mono_16k
from separation.sepformer import separate_speakers
from transcription.whisper_transcriber import transcribe_files
from io_utils.outputs import write_transcripts


console = Console()


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Speaker Isolation & Identification CLI")
	parser.add_argument("input", type=str, help="Path to input MP3 file")
	parser.add_argument("--output", type=str, default="output", help="Output directory")
	parser.add_argument("--num-speakers", type=int, default=2, choices=[2, 3], help="Number of speakers to separate")
	parser.add_argument("--whisper-model", type=str, default="base", help="Whisper model name (tiny, base, small, medium, large)")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	input_path = Path(args.input).expanduser().resolve()
	output_dir = Path(args.output).expanduser().resolve()
	output_dir.mkdir(parents=True, exist_ok=True)

	if not input_path.exists():
		raise FileNotFoundError(f"Input file not found: {input_path}")

	console.log(f"Input: {input_path}")
	console.log(f"Output dir: {output_dir}")

	with tempfile.TemporaryDirectory() as tmpdir:
		tmpdir_path = Path(tmpdir)
		# 1) Convert/prepare audio to WAV mono 16k for downstream
		wav_path = ensure_wav_mono_16k(input_path, tmpdir_path / "prepared.wav")
		console.log(f"Prepared WAV at {wav_path}")

		# 2) Separate speakers using SpeechBrain SepFormer
		separated_paths: List[Path] = separate_speakers(
			wav_path,
			output_dir,
			num_speakers=args.num_speakers,
		)
		for p in separated_paths:
			console.log(f"Wrote separated track: {p}")

		# 3) Transcribe each separated speaker track with Whisper
		transcripts: Dict[str, Any] = transcribe_files(
			separated_paths,
			model_name=args.whisper_model,
		)

		# 4) Collate and write transcript outputs (JSON + TXT)
		write_transcripts(transcripts, output_dir)

	console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
	main()
