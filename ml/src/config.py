import os


class Config:
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))
    GRPC_MAX_WORKERS: int = int(os.getenv("GRPC_MAX_WORKERS", "10"))

    CLIP_MODEL: str = os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")
    EMBEDDING_DIM: int = 512

    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_MAX_DURATION: int = 30

    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "/app/models")


config = Config()
