FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY protos/ ./protos/
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system -e .

# Generate protobuf code
RUN python -m grpc_tools.protoc \
    -I./protos \
    --python_out=./protos \
    --grpc_python_out=./protos \
    ./protos/ml_service.proto

# Create models directory
RUN mkdir -p /app/models

# Pre-download CLIP model at build time (eliminates cold start download)
RUN python -c "from transformers import CLIPModel, CLIPProcessor; \
    CLIPModel.from_pretrained('openai/clip-vit-base-patch32', cache_dir='/app/models'); \
    CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32', cache_dir='/app/models')"

# Cloud Run sets PORT; default to 50051
ENV PORT=50051

# Expose gRPC port
EXPOSE 50051

# Run the server
CMD ["python", "-m", "src.server"]
