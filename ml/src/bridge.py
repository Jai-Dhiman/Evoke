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

    MOOD_PROMPTS = {
        "energy": {
            "high": ["intense", "powerful", "vibrant", "explosive", "dynamic"],
            "low": ["calm", "peaceful", "serene", "tranquil", "gentle"],
        },
        "valence": {
            "high": ["bright", "joyful", "warm", "colorful", "cheerful"],
            "low": ["dark", "melancholic", "moody", "somber", "cold"],
        },
        "tempo": {
            "high": ["rapid", "energetic", "racing", "urgent", "frenetic"],
            "low": ["slow", "languid", "still", "frozen", "meditative"],
        },
        "texture": {
            "high": ["intricate", "complex", "detailed", "layered", "ornate"],
            "low": ["minimal", "clean", "simple", "sparse", "bare"],
        },
    }

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.embedding_dim = config.EMBEDDING_DIM

        self._clip_model = None
        self._clip_processor = None
        self._direction_vectors = None

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

        if self._direction_vectors is None:
            self._direction_vectors = self.compute_direction_vectors()

        # Create mood adjustment vector using semantic CLIP directions
        adjustment = np.zeros(self.embedding_dim, dtype=np.float32)
        adjustment += self._direction_vectors["energy"] * (energy - 0.5) * 0.2
        adjustment += self._direction_vectors["valence"] * (valence - 0.5) * 0.2
        adjustment += self._direction_vectors["tempo"] * (tempo - 0.5) * 0.15
        adjustment += self._direction_vectors["texture"] * (texture - 0.5) * 0.15

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
            output = self._clip_model.get_image_features(**inputs)
            image_features = output.pooler_output if hasattr(output, 'pooler_output') else output

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
            output = self._clip_model.get_text_features(**inputs)
            text_features = output.pooler_output if hasattr(output, 'pooler_output') else output

        embedding = text_features.cpu().numpy().flatten()

        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.astype(np.float32)

    def compute_direction_vectors(self) -> dict[str, np.ndarray]:
        """
        Compute semantic direction vectors from CLIP text embeddings.

        For each mood dimension, encodes high/low text prompts and computes
        the direction as mean(high) - mean(low), L2-normalized.
        """
        self.load_model()

        directions = {}
        for mood, prompts in self.MOOD_PROMPTS.items():
            high_embeddings = np.stack([self.encode_text(w) for w in prompts["high"]])
            low_embeddings = np.stack([self.encode_text(w) for w in prompts["low"]])

            direction = high_embeddings.mean(axis=0) - low_embeddings.mean(axis=0)
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction = direction / norm

            directions[mood] = direction.astype(np.float32)

        return directions
