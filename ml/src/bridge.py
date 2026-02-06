import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor

from .config import config


class CrossModalBridge:
    """
    Bridge between audio embeddings and CLIP visual space.

    Maps audio features into the CLIP embedding space so that audio
    queries can retrieve visually similar images.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.embedding_dim = config.EMBEDDING_DIM

        self._clip_model = None
        self._clip_processor = None

        # Learned projection matrix (placeholder - would be trained)
        self._projection = None

    def load_model(self):
        """Load CLIP model for visual embedding reference."""
        if self._clip_model is not None:
            return

        print(f"Loading CLIP model: {config.CLIP_MODEL}")
        self._clip_model = CLIPModel.from_pretrained(
            config.CLIP_MODEL,
            cache_dir=config.MODEL_CACHE_DIR
        ).to(self.device)
        self._clip_processor = CLIPProcessor.from_pretrained(
            config.CLIP_MODEL,
            cache_dir=config.MODEL_CACHE_DIR
        )

        # Initialize projection matrix (identity + small noise for now)
        # In production, this would be a trained neural network
        self._projection = np.eye(self.embedding_dim, dtype=np.float32)

        print("CLIP model loaded successfully")

    def project_to_clip_space(self, audio_embedding: np.ndarray) -> np.ndarray:
        """
        Project audio embedding into CLIP visual embedding space.

        Args:
            audio_embedding: Audio embedding from AudioEncoder (512-dim)

        Returns:
            Embedding in CLIP visual space (512-dim)
        """
        self.load_model()

        # Apply learned projection
        projected = np.dot(audio_embedding, self._projection)

        # L2 normalize to match CLIP embedding norms
        norm = np.linalg.norm(projected)
        if norm > 0:
            projected = projected / norm

        return projected.astype(np.float32)

    def refine_embedding(
        self,
        base_embedding: np.ndarray,
        energy: float,
        valence: float,
        tempo: float,
        texture: float
    ) -> np.ndarray:
        """
        Refine embedding based on mood slider adjustments.

        This applies semantic adjustments to the embedding based on
        user-specified mood parameters.
        """
        self.load_model()

        # Create mood adjustment vector
        # These directions would ideally be learned from data
        adjustment = np.zeros(self.embedding_dim, dtype=np.float32)

        # Energy: affects overall intensity/brightness
        energy_direction = np.linspace(-1, 1, self.embedding_dim)
        adjustment += energy_direction * (energy - 0.5) * 0.2

        # Valence: affects warmth/coolness
        valence_direction = np.sin(np.linspace(0, 4 * np.pi, self.embedding_dim))
        adjustment += valence_direction * (valence - 0.5) * 0.2

        # Tempo: affects dynamism/motion
        tempo_direction = np.cos(np.linspace(0, 2 * np.pi, self.embedding_dim))
        adjustment += tempo_direction * (tempo - 0.5) * 0.15

        # Texture: affects complexity/detail
        texture_direction = np.random.RandomState(42).randn(self.embedding_dim) * 0.5
        adjustment += texture_direction * (texture - 0.5) * 0.15

        # Apply adjustment
        refined = base_embedding + adjustment

        # L2 normalize
        norm = np.linalg.norm(refined)
        if norm > 0:
            refined = refined / norm

        return refined.astype(np.float32)

    def encode_image(self, image) -> np.ndarray:
        """
        Encode an image into CLIP embedding space.

        Used for building the image index in Milvus.
        """
        self.load_model()

        inputs = self._clip_processor(images=image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            image_features = self._clip_model.get_image_features(**inputs)

        embedding = image_features.cpu().numpy().flatten()

        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.astype(np.float32)

    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text into CLIP embedding space.

        Can be used for text-based mood adjustments.
        """
        self.load_model()

        inputs = self._clip_processor(text=text, return_tensors="pt", padding=True).to(self.device)

        with torch.no_grad():
            text_features = self._clip_model.get_text_features(**inputs)

        embedding = text_features.cpu().numpy().flatten()

        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.astype(np.float32)
