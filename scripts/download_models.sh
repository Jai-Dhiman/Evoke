#!/bin/bash
set -e

echo "Downloading ML models for Evoke..."

# Create models directory
mkdir -p ml/models

# Download CLIP model (will be cached by transformers)
echo "CLIP model will be downloaded on first run by the ML service."
echo "To pre-download, run:"
echo "  python -c \"from transformers import CLIPModel, CLIPProcessor; CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')\""

echo ""
echo "Model download script complete."
echo "Models will be automatically downloaded when the ML service starts."
