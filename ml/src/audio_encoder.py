import io
from typing import Tuple

import librosa
import numpy as np
import soundfile as sf
import torch
import torchaudio
from transformers import AutoModel, AutoProcessor

from .config import config


class AudioEncoder:
    """Encodes audio into embeddings using MuQ-style feature extraction."""

    def __init__(self):
        self.sample_rate = config.AUDIO_SAMPLE_RATE
        self.max_duration = config.AUDIO_MAX_DURATION
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._model = None
        self._processor = None

    def load_model(self):
        """Load the audio model (lazy loading)."""
        if self._model is not None:
            return

        # For MuQ, we'd use a music understanding model
        # Using a placeholder approach with spectral features for now
        # In production, this would load the actual MuQ model
        print(f"Audio encoder initialized on {self.device}")

    def encode(self, audio_data: bytes, audio_format: str = "wav") -> Tuple[np.ndarray, dict]:
        """
        Encode audio data into a fixed-size embedding.

        Returns:
            Tuple of (embedding, mood_features)
        """
        self.load_model()

        # Load audio from bytes
        waveform = self._load_audio(audio_data, audio_format)

        # Extract features
        features = self._extract_features(waveform)

        # Compute embedding (placeholder - would use actual MuQ model)
        embedding = self._compute_embedding(features)

        # Extract mood features
        mood = self._extract_mood(waveform, features)

        return embedding, mood

    def _load_audio(self, audio_data: bytes, audio_format: str) -> np.ndarray:
        """Load and preprocess audio from bytes."""
        audio_io = io.BytesIO(audio_data)

        # Load with librosa for robust format handling
        waveform, sr = librosa.load(
            audio_io,
            sr=self.sample_rate,
            mono=True,
            duration=self.max_duration
        )

        return waveform

    def _extract_features(self, waveform: np.ndarray) -> dict:
        """Extract spectral and temporal features."""
        # Mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=waveform,
            sr=self.sample_rate,
            n_mels=128,
            fmax=8000
        )
        mel_db = librosa.power_to_db(mel_spec, ref=np.max)

        # Chromagram
        chroma = librosa.feature.chroma_cqt(y=waveform, sr=self.sample_rate)

        # MFCCs
        mfccs = librosa.feature.mfcc(y=waveform, sr=self.sample_rate, n_mfcc=20)

        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=waveform, sr=self.sample_rate)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=waveform, sr=self.sample_rate)
        spectral_contrast = librosa.feature.spectral_contrast(y=waveform, sr=self.sample_rate)

        # Rhythm features
        tempo, beats = librosa.beat.beat_track(y=waveform, sr=self.sample_rate)
        onset_env = librosa.onset.onset_strength(y=waveform, sr=self.sample_rate)

        # RMS energy
        rms = librosa.feature.rms(y=waveform)

        return {
            "mel_spec": mel_db,
            "chroma": chroma,
            "mfccs": mfccs,
            "spectral_centroid": spectral_centroid,
            "spectral_rolloff": spectral_rolloff,
            "spectral_contrast": spectral_contrast,
            "tempo": tempo,
            "beats": beats,
            "onset_env": onset_env,
            "rms": rms,
        }

    def _compute_embedding(self, features: dict) -> np.ndarray:
        """
        Compute a fixed-size embedding from audio features.

        This is a placeholder implementation. In production, this would use
        the MuQ model to generate embeddings in a shared audio-visual space.
        """
        # Aggregate features into a fixed-size vector
        embedding_parts = []

        # Mel spectrogram statistics (128 * 4 = 512 values compressed to 64)
        mel_stats = np.concatenate([
            features["mel_spec"].mean(axis=1),
            features["mel_spec"].std(axis=1),
        ])[:64]
        embedding_parts.append(mel_stats)

        # MFCC statistics (20 * 2 = 40 values)
        mfcc_stats = np.concatenate([
            features["mfccs"].mean(axis=1),
            features["mfccs"].std(axis=1),
        ])
        embedding_parts.append(mfcc_stats)

        # Chroma statistics (12 * 2 = 24 values)
        chroma_stats = np.concatenate([
            features["chroma"].mean(axis=1),
            features["chroma"].std(axis=1),
        ])
        embedding_parts.append(chroma_stats)

        # Spectral features (compressed to 20 values)
        spectral_stats = np.array([
            features["spectral_centroid"].mean(),
            features["spectral_centroid"].std(),
            features["spectral_rolloff"].mean(),
            features["spectral_rolloff"].std(),
        ])
        spectral_contrast_mean = features["spectral_contrast"].mean(axis=1)
        spectral_stats = np.concatenate([spectral_stats, spectral_contrast_mean[:16]])
        embedding_parts.append(spectral_stats)

        # Rhythm features (8 values)
        tempo_normalized = float(np.asarray(features["tempo"]).flat[0]) / 200.0
        onset_stats = np.array([
            features["onset_env"].mean(),
            features["onset_env"].std(),
            features["onset_env"].max(),
        ])
        rhythm_stats = np.concatenate([[tempo_normalized], onset_stats, [0, 0, 0, 0]])[:8]
        embedding_parts.append(rhythm_stats)

        # Energy features (4 values)
        rms_stats = np.array([
            features["rms"].mean(),
            features["rms"].std(),
            features["rms"].max(),
            features["rms"].min(),
        ]).flatten()
        embedding_parts.append(rms_stats)

        # Concatenate and pad/truncate to target dimension
        raw_embedding = np.concatenate(embedding_parts)

        # Pad or truncate to 512 dimensions
        target_dim = config.EMBEDDING_DIM
        if len(raw_embedding) < target_dim:
            embedding = np.pad(raw_embedding, (0, target_dim - len(raw_embedding)))
        else:
            embedding = raw_embedding[:target_dim]

        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.astype(np.float32)

    def _extract_mood(self, waveform: np.ndarray, features: dict) -> dict:
        """
        Extract mood-related features from audio.

        Returns normalized values (0-1) for:
        - energy: overall loudness/intensity
        - valence: musical positivity (major vs minor, etc.)
        - tempo: perceived speed
        - texture: spectral complexity
        """
        # Energy: based on RMS
        rms_mean = features["rms"].mean()
        energy = float(np.clip(rms_mean * 10, 0, 1))

        # Valence: simplified approximation based on mode and spectral brightness
        # In production, this would use a trained classifier
        spectral_brightness = features["spectral_centroid"].mean() / 4000
        chroma_major = features["chroma"][[0, 2, 4, 5, 7, 9, 11]].mean()
        chroma_minor = features["chroma"][[0, 2, 3, 5, 7, 8, 10]].mean()
        mode_score = chroma_major / (chroma_major + chroma_minor + 1e-6)
        valence = float(np.clip((spectral_brightness + mode_score) / 2, 0, 1))

        # Tempo: normalized to 0-1 (assuming 60-180 BPM range)
        tempo_raw = float(features["tempo"])
        tempo = float(np.clip((tempo_raw - 60) / 120, 0, 1))

        # Texture: based on spectral contrast and complexity
        contrast_mean = features["spectral_contrast"].mean()
        texture = float(np.clip(contrast_mean / 50, 0, 1))

        return {
            "energy": energy,
            "valence": valence,
            "tempo": tempo,
            "texture": texture,
        }
