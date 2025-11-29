"""
Audio capture, speech-to-text, and text-to-speech utilities.
"""

from __future__ import annotations

import json
import logging
import queue
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import numpy as np
except ImportError:  # pragma: no cover - dependency check
    np = None

from .config import AudioConfig

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - hardware/audio dependency
    sd = None

try:  # pragma: no cover - heavy models
    import whisper
except ImportError:
    whisper = None

try:  # pragma: no cover - heavy models
    from vosk import KaldiRecognizer, Model as VoskModel
except ImportError:
    KaldiRecognizer = None
    VoskModel = None


@dataclass
class AudioCaptureResult:
    """Container for captured audio metadata."""

    wav_path: Path
    duration_sec: float


class AudioManager:
    """Coordinates microphone capture, STT, and TTS playback."""

    def __init__(self, config: AudioConfig, logger: Optional[logging.Logger] = None):
        if np is None:
            raise RuntimeError("numpy is required for audio processing but is not installed.")

        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._recording_flag = threading.Event()
        self._frames: "queue.Queue[np.ndarray]" = queue.Queue()
        self._capture_thread: Optional[threading.Thread] = None
        self._vosk_model: Optional[VoskModel] = None
        self._whisper_model = None

        if VoskModel and config.vosk_model_path:
            self._logger.info("Loading Vosk model from %s", config.vosk_model_path)
            self._vosk_model = VoskModel(str(config.vosk_model_path))

        if whisper:
            self._logger.info("Loading Whisper model: %s", config.whisper_model)
            self._whisper_model = whisper.load_model(config.whisper_model)

    def start_recording(self) -> None:
        """Begin asynchronous microphone capture."""
        if sd is None:
            raise RuntimeError("sounddevice library not available on this system.")

        if self._recording_flag.is_set():
            self._logger.debug("Recording already in progress; ignoring start command.")
            return

        self._logger.debug("Starting microphone capture.")
        self._recording_flag.set()
        self._frames = queue.Queue()
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def _capture_loop(self) -> None:
        if sd is None:
            return

        def callback(indata, *_):
            self._frames.put(indata.copy())

        with sd.InputStream(
            samplerate=self._config.sample_rate,
            channels=self._config.channels,
            dtype="float32",
            callback=callback,
            device=self._config.mic_device,
        ):
            while self._recording_flag.is_set():
                sd.sleep(50)

    def stop_and_transcribe(self) -> str:
        """Stop recording, persist WAV, and run STT."""
        if not self._recording_flag.is_set():
            self._logger.debug("stop_and_transcribe called but recording flag is clear.")
            return ""

        self._logger.debug("Stopping microphone capture.")
        self._recording_flag.clear()
        if self._capture_thread:
            self._capture_thread.join(timeout=2)

        frames = []
        while not self._frames.empty():
            frames.append(self._frames.get())

        if not frames:
            self._logger.warning("No frames captured; returning empty transcription.")
            return ""

        audio = np.concatenate(frames, axis=0)
        wav_path = self._write_wav(audio)
        transcript = self._transcribe_audio(wav_path)
        return transcript.strip()

    def _write_wav(self, audio: np.ndarray) -> Path:
        wav_path = Path(tempfile.mkstemp(prefix="chat_audio_", suffix=".wav")[1])
        self._logger.debug("Persisting captured audio to %s", wav_path)
        audio_int16 = np.int16(audio * 32767)
        try:
            from scipy.io import wavfile  # type: ignore
        except ImportError as exc:  # pragma: no cover - dependency check
            raise RuntimeError("scipy is required to persist WAV files.") from exc

        wavfile.write(str(wav_path), self._config.sample_rate, audio_int16)
        return wav_path

    def _transcribe_audio(self, wav_path: Path) -> str:
        if self._vosk_model and KaldiRecognizer:
            return self._transcribe_vosk(wav_path)
        if self._whisper_model:
            return self._transcribe_whisper(wav_path)
        raise RuntimeError("No STT backend available (Vosk/Whisper not installed).")

    def _transcribe_vosk(self, wav_path: Path) -> str:
        import wave

        wf = wave.open(str(wav_path), "rb")
        recognizer = KaldiRecognizer(self._vosk_model, wf.getframerate())
        result = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                res = json.loads(recognizer.Result())
                result.append(res.get("text", ""))
        final = json.loads(recognizer.FinalResult())
        result.append(final.get("text", ""))
        transcript = " ".join(filter(None, result))
        self._logger.info("Vosk transcription: %s", transcript)
        return transcript

    def _transcribe_whisper(self, wav_path: Path) -> str:
        assert self._whisper_model is not None
        result = self._whisper_model.transcribe(str(wav_path))
        text = result.get("text", "")
        self._logger.info("Whisper transcription: %s", text)
        return text

    def speak_text(self, text: str) -> None:
        """Pipe generated speech to USB speaker using Piper/Coqui."""
        if not text:
            return

        if self._config.tts_voice_path:
            self._speak_with_piper(text)
        else:
            self._logger.warning("No TTS voice configured; skipping speech output.")

    def _speak_with_piper(self, text: str) -> None:
        voice_path = self._config.tts_voice_path
        if voice_path is None:
            return

        command = [
            self._config.tts_binary,
            "--model",
            str(voice_path),
            "--output-raw",
            "--sentence-silence",
            "0.1",
        ]
        self._logger.debug("Invoking Piper: %s", " ".join(command))
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdin is not None
        process.stdin.write(text.encode("utf-8"))
        process.stdin.close()
        if sd is None:
            self._logger.warning("sounddevice not available; cannot stream Piper output.")
            return

        raw_audio = process.stdout.read()
        process.wait()
        audio_array = np.frombuffer(raw_audio, dtype=np.int16)
        self._logger.debug("Playing TTS audio (%d samples).", audio_array.size)
        sd.play(audio_array, samplerate=22050, device=self._config.speaker_device)
        sd.wait()

    def cleanup(self) -> None:
        self._recording_flag.clear()
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=1)

