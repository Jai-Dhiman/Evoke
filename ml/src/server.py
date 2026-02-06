import sys
from concurrent import futures

import grpc
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, "/app")

from src.audio_encoder import AudioEncoder
from src.bridge import CrossModalBridge
from src.config import config

# Import generated protobuf code
try:
    from protos import ml_service_pb2, ml_service_pb2_grpc
except ImportError:
    # Fallback for local development
    import ml_service_pb2
    import ml_service_pb2_grpc


class MLServiceServicer(ml_service_pb2_grpc.MLServiceServicer):
    """gRPC service implementation for audio analysis."""

    def __init__(self):
        self.audio_encoder = AudioEncoder()
        self.bridge = CrossModalBridge()

        # Preload models
        print("Loading models...")
        self.audio_encoder.load_model()
        self.bridge.load_model()
        print("Models loaded successfully")

    def AnalyzeAudio(self, request, context):
        """Analyze audio and return embedding with mood features."""
        try:
            audio_data = request.audio_data
            audio_format = request.format or "wav"

            # Encode audio
            embedding, mood = self.audio_encoder.encode(audio_data, audio_format)

            # Project to CLIP space
            clip_embedding = self.bridge.project_to_clip_space(embedding)

            return ml_service_pb2.AnalyzeAudioResponse(
                embedding=clip_embedding.tolist(),
                mood_energy=mood["energy"],
                mood_valence=mood["valence"],
                mood_tempo=mood["tempo"],
                mood_texture=mood["texture"],
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ml_service_pb2.AnalyzeAudioResponse()

    def RefineEmbedding(self, request, context):
        """Refine embedding based on mood slider values."""
        try:
            base_embedding = np.array(request.base_embedding, dtype=np.float32)

            refined = self.bridge.refine_embedding(
                base_embedding,
                energy=request.energy,
                valence=request.valence,
                tempo=request.tempo,
                texture=request.texture,
            )

            return ml_service_pb2.RefineEmbeddingResponse(
                embedding=refined.tolist()
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ml_service_pb2.RefineEmbeddingResponse()

    def HealthCheck(self, request, context):
        """Health check endpoint."""
        return ml_service_pb2.HealthCheckResponse(
            healthy=True,
            message="ML service is running"
        )


def serve():
    """Start the gRPC server."""
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=config.GRPC_MAX_WORKERS),
        options=[
            ("grpc.max_receive_message_length", 100 * 1024 * 1024),  # 100MB
            ("grpc.max_send_message_length", 100 * 1024 * 1024),
        ]
    )

    servicer = MLServiceServicer()
    ml_service_pb2_grpc.add_MLServiceServicer_to_server(servicer, server)

    address = f"[::]:{config.GRPC_PORT}"
    server.add_insecure_port(address)

    print(f"Starting ML gRPC server on {address}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
