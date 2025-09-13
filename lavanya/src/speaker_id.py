"""
Speaker identification and diarization module.
"""

import torch
import numpy as np
import pickle
import os
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from pathlib import Path
import time

from speechbrain.pretrained import EncoderClassifier
from sklearn.metrics.pairwise import cosine_similarity
from .config import config
from .separation import SeparatedAudio

logger = logging.getLogger(__name__)


@dataclass
class SpeakerProfile:
    """Represents a speaker's voice profile."""
    speaker_id: str
    name: str
    embedding: np.ndarray
    created_at: float
    sample_count: int
    confidence_threshold: float
    
    def similarity(self, other_embedding: np.ndarray) -> float:
        """Calculate similarity with another embedding."""
        return float(cosine_similarity(
            self.embedding.reshape(1, -1), 
            other_embedding.reshape(1, -1)
        )[0, 0])


@dataclass
class SpeakerMatch:
    """Represents a speaker match result."""
    speaker_id: str
    name: str
    confidence: float
    is_unknown: bool


class SpeakerEmbedder:
    """Speaker embedding extractor using ECAPA-TDNN model."""
    
    def __init__(self, 
                 model_name: str = None,
                 device: str = None,
                 embedding_dim: int = None):
        """Initialize speaker embedder.
        
        Args:
            model_name: Name of embedding model
            device: Device to run model on
            embedding_dim: Expected embedding dimension
        """
        self.model_name = model_name or config.get("models.speaker_recognition.model_name", 
                                                   "speechbrain/spkrec-ecapa-voxceleb")
        self.device = device or config.get_device("speaker_recognition")
        self.embedding_dim = embedding_dim or config.get("models.speaker_recognition.embedding_dim", 192)
        
        # Model
        self.model = None
        self.sample_rate = config.get("audio.sample_rate", 16000)
        
        logger.info(f"Initializing speaker embedder: {self.model_name} on {self.device}")
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        try:
            self.model = EncoderClassifier.from_hparams(
                source=self.model_name,
                savedir=f"pretrained_models/{self.model_name.split('/')[-1]}",
                run_opts={"device": self.device}
            )
            self.model.eval()
            
            logger.info(f"Successfully initialized embedding model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def extract_embedding(self, audio_data: np.ndarray, 
                         sample_rate: int = None) -> np.ndarray:
        """Extract speaker embedding from audio data.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate
            
        Returns:
            Speaker embedding vector
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_data).float()
            
            # Add batch and channel dimensions
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0).unsqueeze(0)
            elif audio_tensor.dim() == 2:
                audio_tensor = audio_tensor.unsqueeze(0)
            
            # Resample if necessary
            if sample_rate != self.sample_rate:
                resampler = torchaudio.transforms.Resample(sample_rate, self.sample_rate)
                audio_tensor = resampler(audio_tensor)
            
            # Move to device
            audio_tensor = audio_tensor.to(self.device)
            
            # Extract embedding
            with torch.no_grad():
                embedding = self.model.encode_batch(audio_tensor)
                embedding = embedding.squeeze().cpu().numpy()
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error extracting speaker embedding: {e}")
            # Return zero embedding on error
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def extract_batch_embeddings(self, audio_batch: List[np.ndarray], 
                                sample_rate: int = None) -> List[np.ndarray]:
        """Extract embeddings for batch of audio data.
        
        Args:
            audio_batch: List of audio data arrays
            sample_rate: Audio sample rate
            
        Returns:
            List of speaker embeddings
        """
        embeddings = []
        for audio_data in audio_batch:
            embedding = self.extract_embedding(audio_data, sample_rate)
            embeddings.append(embedding)
        return embeddings


class SpeakerDatabase:
    """Database for storing and managing speaker profiles."""
    
    def __init__(self, storage_dir: str = None):
        """Initialize speaker database.
        
        Args:
            storage_dir: Directory to store speaker profiles
        """
        self.storage_dir = Path(storage_dir or config.get("storage.speaker_embeddings_dir", 
                                                         "./data/speaker_embeddings"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage
        self.speakers: Dict[str, SpeakerProfile] = {}
        self.unknown_speakers: Dict[str, np.ndarray] = {}
        
        # Load existing profiles
        self._load_speakers()
    
    def _load_speakers(self):
        """Load speaker profiles from storage."""
        profiles_file = self.storage_dir / "speaker_profiles.pkl"
        
        if profiles_file.exists():
            try:
                with open(profiles_file, 'rb') as f:
                    self.speakers = pickle.load(f)
                logger.info(f"Loaded {len(self.speakers)} speaker profiles")
            except Exception as e:
                logger.error(f"Failed to load speaker profiles: {e}")
    
    def _save_speakers(self):
        """Save speaker profiles to storage."""
        profiles_file = self.storage_dir / "speaker_profiles.pkl"
        
        try:
            with open(profiles_file, 'wb') as f:
                pickle.dump(self.speakers, f)
        except Exception as e:
            logger.error(f"Failed to save speaker profiles: {e}")
    
    def add_speaker(self, speaker_id: str, name: str, 
                   embedding: np.ndarray,
                   confidence_threshold: float = None) -> bool:
        """Add or update speaker profile.
        
        Args:
            speaker_id: Unique speaker identifier
            name: Human-readable speaker name
            embedding: Speaker embedding vector
            confidence_threshold: Confidence threshold for this speaker
            
        Returns:
            True if successful, False otherwise
        """
        try:
            threshold = confidence_threshold or config.get("models.speaker_recognition.similarity_threshold", 0.7)
            
            profile = SpeakerProfile(
                speaker_id=speaker_id,
                name=name,
                embedding=embedding,
                created_at=time.time(),
                sample_count=1,
                confidence_threshold=threshold
            )
            
            self.speakers[speaker_id] = profile
            self._save_speakers()
            
            logger.info(f"Added speaker profile: {name} ({speaker_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add speaker profile: {e}")
            return False
    
    def update_speaker_embedding(self, speaker_id: str, 
                                new_embedding: np.ndarray,
                                update_method: str = "average") -> bool:
        """Update existing speaker embedding.
        
        Args:
            speaker_id: Speaker identifier
            new_embedding: New embedding vector
            update_method: Method to update ('average' or 'replace')
            
        Returns:
            True if successful, False otherwise
        """
        if speaker_id not in self.speakers:
            logger.warning(f"Speaker {speaker_id} not found for update")
            return False
        
        try:
            profile = self.speakers[speaker_id]
            
            if update_method == "average":
                # Weighted average with existing embedding
                weight = 1.0 / (profile.sample_count + 1)
                profile.embedding = (1 - weight) * profile.embedding + weight * new_embedding
            elif update_method == "replace":
                profile.embedding = new_embedding
            
            profile.sample_count += 1
            self._save_speakers()
            
            logger.info(f"Updated speaker profile: {profile.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update speaker embedding: {e}")
            return False
    
    def find_speaker(self, embedding: np.ndarray, 
                    threshold: float = None) -> SpeakerMatch:
        """Find matching speaker for embedding.
        
        Args:
            embedding: Query embedding
            threshold: Similarity threshold
            
        Returns:
            SpeakerMatch object
        """
        if not self.speakers:
            return SpeakerMatch(
                speaker_id="unknown",
                name="Unknown Speaker",
                confidence=0.0,
                is_unknown=True
            )
        
        threshold = threshold or config.get("models.speaker_recognition.similarity_threshold", 0.7)
        
        best_match = None
        best_similarity = -1.0
        
        for speaker_id, profile in self.speakers.items():
            similarity = profile.similarity(embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = profile
        
        if best_similarity >= threshold:
            return SpeakerMatch(
                speaker_id=best_match.speaker_id,
                name=best_match.name,
                confidence=best_similarity,
                is_unknown=False
            )
        else:
            # Generate unknown speaker ID
            unknown_id = f"unknown_{int(time.time())}"
            return SpeakerMatch(
                speaker_id=unknown_id,
                name="Unknown Speaker",
                confidence=best_similarity,
                is_unknown=True
            )
    
    def get_speaker(self, speaker_id: str) -> Optional[SpeakerProfile]:
        """Get speaker profile by ID."""
        return self.speakers.get(speaker_id)
    
    def list_speakers(self) -> List[SpeakerProfile]:
        """Get list of all speaker profiles."""
        return list(self.speakers.values())
    
    def delete_speaker(self, speaker_id: str) -> bool:
        """Delete speaker profile.
        
        Args:
            speaker_id: Speaker identifier to delete
            
        Returns:
            True if successful, False otherwise
        """
        if speaker_id in self.speakers:
            del self.speakers[speaker_id]
            self._save_speakers()
            logger.info(f"Deleted speaker profile: {speaker_id}")
            return True
        return False


class SpeakerIdentifier:
    """Real-time speaker identification system."""
    
    def __init__(self, 
                 embedder: SpeakerEmbedder = None,
                 database: SpeakerDatabase = None,
                 min_duration: float = None):
        """Initialize speaker identifier.
        
        Args:
            embedder: Speaker embedding extractor
            database: Speaker database
            min_duration: Minimum audio duration for identification
        """
        self.embedder = embedder or SpeakerEmbedder()
        self.database = database or SpeakerDatabase()
        self.min_duration = min_duration or config.get("processing.min_speaker_duration", 0.5)
        
        # Processing state
        self.speaker_timestamps: Dict[str, float] = {}
        self.active_speakers: Dict[str, float] = {}
        
        # Callbacks
        self.identification_callbacks = []
        
        logger.info("Speaker identifier initialized")
    
    def add_identification_callback(self, callback):
        """Add callback for speaker identification results."""
        self.identification_callbacks.append(callback)
    
    def identify_speakers(self, separated_audio: SeparatedAudio) -> List[SpeakerMatch]:
        """Identify speakers in separated audio streams.
        
        Args:
            separated_audio: Separated audio streams
            
        Returns:
            List of speaker matches for each stream
        """
        speaker_matches = []
        
        for i, stream in enumerate(separated_audio.streams):
            # Check if stream has sufficient duration
            stream_duration = len(stream) / separated_audio.sample_rate
            if stream_duration < self.min_duration:
                # Skip short streams
                speaker_matches.append(SpeakerMatch(
                    speaker_id="skip",
                    name="Short Audio",
                    confidence=0.0,
                    is_unknown=True
                ))
                continue
            
            # Extract embedding
            embedding = self.embedder.extract_embedding(stream, separated_audio.sample_rate)
            
            # Find matching speaker
            match = self.database.find_speaker(embedding)
            speaker_matches.append(match)
            
            # Update speaker activity tracking
            self._update_speaker_activity(match, separated_audio.timestamp)
        
        # Call identification callbacks
        for callback in self.identification_callbacks:
            try:
                callback(separated_audio, speaker_matches)
            except Exception as e:
                logger.error(f"Error in identification callback: {e}")
        
        return speaker_matches
    
    def _update_speaker_activity(self, match: SpeakerMatch, timestamp: float):
        """Update speaker activity tracking."""
        if not match.is_unknown:
            self.active_speakers[match.speaker_id] = timestamp
            self.speaker_timestamps[match.speaker_id] = timestamp
    
    def enroll_speaker(self, speaker_id: str, name: str, 
                      audio_data: np.ndarray,
                      sample_rate: int = None) -> bool:
        """Enroll new speaker.
        
        Args:
            speaker_id: Unique speaker identifier
            name: Human-readable name
            audio_data: Audio data for enrollment
            sample_rate: Audio sample rate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract embedding
            embedding = self.embedder.extract_embedding(audio_data, sample_rate)
            
            # Add to database
            success = self.database.add_speaker(speaker_id, name, embedding)
            
            if success:
                logger.info(f"Successfully enrolled speaker: {name} ({speaker_id})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to enroll speaker: {e}")
            return False
    
    def get_active_speakers(self, timeout: float = 5.0) -> List[str]:
        """Get list of currently active speakers.
        
        Args:
            timeout: Seconds of inactivity before considering speaker inactive
            
        Returns:
            List of active speaker IDs
        """
        current_time = time.time()
        active = []
        
        for speaker_id, last_seen in self.active_speakers.items():
            if current_time - last_seen <= timeout:
                active.append(speaker_id)
        
        return active
    
    def process_separated_stream(self, separated_audio: SeparatedAudio):
        """Process separated audio stream for speaker identification.
        
        Args:
            separated_audio: Separated audio streams
        """
        self.identify_speakers(separated_audio)


def create_speaker_identifier(**kwargs) -> SpeakerIdentifier:
    """Create speaker identifier with configuration.
    
    Args:
        **kwargs: Arguments for SpeakerIdentifier
        
    Returns:
        SpeakerIdentifier instance
    """
    return SpeakerIdentifier(**kwargs)
