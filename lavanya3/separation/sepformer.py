from pathlib import Path
from typing import List

import torch
import torchaudio
from speechbrain.inference import SepformerSeparation


def _select_model_name(num_speakers: int) -> str:
	if num_speakers == 2:
		return "speechbrain/sepformer-wsj02mix"
	elif num_speakers == 3:
		return "speechbrain/sepformer-wsj03mix"
	raise ValueError("num_speakers must be 2 or 3")


def separate_speakers(wav_path: Path, output_dir: Path, num_speakers: int = 2) -> List[Path]:
	"""Run SepFormer separation and write `speaker_*.wav` files in output_dir.

	Returns the list of written paths.
	"""
	model_name = _select_model_name(num_speakers)
	separer = SepformerSeparation.from_hparams(source=model_name, savedir=str(output_dir / "sepformer_ckpt"))

	# Load wav: [channels, time]
	waveform, sample_rate = torchaudio.load(str(wav_path))
	if waveform.dim() == 2:
		# mix to mono -> [time]
		mono = torch.mean(waveform, dim=0)
	else:
		# already [time]
		mono = waveform

	# SepFormer expects [batch, time]
	batch_waveform = mono.unsqueeze(0)

	with torch.no_grad():
		est_sources = separer.separate_batch(batch_waveform)  # [batch, speakers, time] or [batch, time, speakers]

	# Remove batch dim -> either [speakers, time] or [time, speakers]
	est_sources = est_sources.squeeze(0)

	# Normalize to [speakers, time]
	if est_sources.dim() != 2:
		raise RuntimeError(f"Unexpected SepFormer output shape: {tuple(est_sources.shape)}")
	spk_first = est_sources
	if est_sources.shape[0] > 16 and est_sources.shape[1] <= 16:
		# Likely [time, speakers], transpose
		spk_first = est_sources.transpose(0, 1)

	# Cap to requested number of speakers
	num_tracks = min(num_speakers, spk_first.shape[0])

	written_paths: List[Path] = []
	for idx in range(num_tracks):
		track = spk_first[idx].unsqueeze(0)  # [1, time] for torchaudio.save
		out_path = output_dir / f"speaker_{idx + 1}.wav"
		torchaudio.save(str(out_path), track.cpu(), sample_rate)
		written_paths.append(out_path)

	return written_paths
