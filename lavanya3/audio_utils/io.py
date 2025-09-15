from pathlib import Path
from typing import Optional

import librosa
import numpy as np
import soundfile as sf


def ensure_wav_mono_16k(input_audio: Path, out_wav: Path, target_sr: int = 16000) -> Path:
	"""Load audio (mp3/wav/...) and write mono 16k WAV.

	Returns the output WAV path.
	"""
	y, sr = librosa.load(str(input_audio), sr=target_sr, mono=True)
	y = np.asarray(y, dtype=np.float32)
	sf.write(str(out_wav), y, target_sr, subtype="PCM_16")
	return out_wav
