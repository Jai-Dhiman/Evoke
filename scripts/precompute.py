#!/usr/bin/env python3
"""
Pre-compute all deployment data for Evoke.

Generates:
- backend/internal/vectorstore/data/images.json   (image URLs + CLIP embeddings)
- backend/internal/vectorstore/data/directions.json (mood direction vectors)
- backend/internal/vectorstore/data/demo.json      (pre-computed demo results)

Usage:
    cd ml && uv run python ../scripts/precompute.py [--demo-audio path/to/audio.mp3]
"""

import argparse
import json
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image

# Add ml/ to path so we can import src.bridge and src.audio_encoder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml"))

from src.audio_encoder import AudioEncoder
from src.bridge import CrossModalBridge

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "backend" / "internal" / "vectorstore" / "data"

# Curated Unsplash images (50+ diverse images for mood board variety)
SAMPLE_IMAGES = [
    # Nature & landscapes
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=400",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
    "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?w=400",
    "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=400",
    "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=400",
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
    "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=400",
    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400",
    "https://images.unsplash.com/photo-1486728297118-82a07bc48a28?w=400",
    "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=400",
    "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=400",
    "https://images.unsplash.com/photo-1501854140801-50d01698950b?w=400",
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=400",
    "https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=400",
    "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=400",
    "https://images.unsplash.com/photo-1465056836041-7f43ac27dcb5?w=400",
    "https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=400",
    "https://images.unsplash.com/photo-1504198453319-5ce911bafcde?w=400",
    "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=400",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
    # Urban & architecture
    "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400",
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=400",
    "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400",
    "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=400",
    "https://images.unsplash.com/photo-1444723121867-7a241cacace9?w=400",
    # Abstract & art
    "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=400",
    "https://images.unsplash.com/photo-1550859492-d5da9d8e45f3?w=400",
    "https://images.unsplash.com/photo-1557672172-298e090bd0f1?w=400",
    "https://images.unsplash.com/photo-1549490349-8643362247b5?w=400",
    "https://images.unsplash.com/photo-1543857778-c4a1a3e0b2eb?w=400",
    # Moody & atmospheric
    "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=400",
    "https://images.unsplash.com/photo-1507400492013-162706c8c05e?w=400",
    "https://images.unsplash.com/photo-1489549132488-d00b7eee80f1?w=400",
    "https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=400",
    "https://images.unsplash.com/photo-1488866022916-f7f2a032cd23?w=400",
    # Warm & vibrant
    "https://images.unsplash.com/photo-1503803548695-c2a7b4a5b875?w=400",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400",
    "https://images.unsplash.com/photo-1476820865390-c52aeebb9891?w=400",
    "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?w=400",
    "https://images.unsplash.com/photo-1490682143684-14369e18dce8?w=400",
    # Cool & minimal
    "https://images.unsplash.com/photo-1531315630201-bb15abeb1653?w=400",
    "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=400",
    "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?w=400",
    "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=400",
    "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?w=400",
    # Textures & patterns
    "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400",
    "https://images.unsplash.com/photo-1553356084-58ef4a67b2a7?w=400",
    "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=400",
    "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=400",
    "https://images.unsplash.com/photo-1557682224-5b8590cd9ec5?w=400",
    # People & portraits (silhouettes/artistic)
    "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=400",
    "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=400",
    "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400",
    "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400",
    "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400",
    # Water & reflections
    "https://images.unsplash.com/photo-1468413253725-0d5181091126?w=400",
    "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=400",
    "https://images.unsplash.com/photo-1480936600919-bffa6b7ecf1e?w=400",
    "https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?w=400",
    "https://images.unsplash.com/photo-1439405326854-014607f694d7?w=400",
]


def download_image(url: str) -> Image.Image:
    """Download an image from a URL."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")


def compute_direction_vectors(dim: int = 512) -> dict:
    """Compute the 4 mood direction vectors (matching bridge.py:90-103)."""
    energy_direction = np.linspace(-1, 1, dim).astype(np.float32)
    valence_direction = np.sin(np.linspace(0, 4 * np.pi, dim)).astype(np.float32)
    tempo_direction = np.cos(np.linspace(0, 2 * np.pi, dim)).astype(np.float32)
    texture_direction = (np.random.RandomState(42).randn(dim) * 0.5).astype(np.float32)

    return {
        "energy": energy_direction.tolist(),
        "valence": valence_direction.tolist(),
        "tempo": tempo_direction.tolist(),
        "texture": texture_direction.tolist(),
    }


def l2_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute L2 (Euclidean) distance between two vectors."""
    diff = a - b
    return float(np.sqrt(np.dot(diff, diff)))


def brute_force_search(
    query: np.ndarray,
    images: list[dict],
    top_k: int = 20,
) -> list[dict]:
    """Brute-force L2 search over image embeddings."""
    scored = []
    for i, img in enumerate(images):
        emb = np.array(img["embedding"], dtype=np.float32)
        dist = l2_distance(query, emb)
        scored.append({"id": i, "image_url": img["url"], "score": dist})

    scored.sort(key=lambda x: x["score"])
    return scored[:top_k]


def main():
    parser = argparse.ArgumentParser(description="Pre-compute Evoke deployment data")
    parser.add_argument(
        "--demo-audio",
        type=str,
        help="Path to demo audio file (mp3/wav). If provided, generates demo data and copies to frontend/public/demo.mp3",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading CLIP model...")
    bridge = CrossModalBridge()
    bridge.load_model()
    print("CLIP model ready")

    # Step 1: Compute image embeddings
    print(f"\nProcessing {len(SAMPLE_IMAGES)} images...")
    image_entries = []
    for i, url in enumerate(SAMPLE_IMAGES):
        print(f"  [{i + 1}/{len(SAMPLE_IMAGES)}] {url[:60]}...")
        try:
            image = download_image(url)
            embedding = bridge.encode_image(image)
            image_entries.append({
                "url": url,
                "embedding": embedding.tolist(),
            })
        except requests.RequestException as e:
            print(f"    Failed to download: {e}")
        except Exception as e:
            print(f"    Failed to encode: {e}")

    print(f"\nSuccessfully processed {len(image_entries)} images")

    # Write images.json
    images_path = OUTPUT_DIR / "images.json"
    with open(images_path, "w") as f:
        json.dump(image_entries, f)
    print(f"Wrote {images_path}")

    # Step 2: Compute direction vectors
    directions = compute_direction_vectors()
    directions_path = OUTPUT_DIR / "directions.json"
    with open(directions_path, "w") as f:
        json.dump(directions, f)
    print(f"Wrote {directions_path}")

    # Step 3: Generate demo data (if audio provided)
    if args.demo_audio:
        print(f"\nProcessing demo audio: {args.demo_audio}")
        encoder = AudioEncoder()
        encoder.load_model()

        with open(args.demo_audio, "rb") as f:
            audio_data = f.read()

        embedding, mood = encoder.encode(audio_data, "auto")
        clip_embedding = bridge.project_to_clip_space(embedding)

        demo_images = brute_force_search(clip_embedding, image_entries, top_k=20)

        demo_data = {
            "embedding": clip_embedding.tolist(),
            "mood_energy": mood["energy"],
            "mood_valence": mood["valence"],
            "mood_tempo": mood["tempo"],
            "mood_texture": mood["texture"],
            "images": demo_images,
        }

        demo_path = OUTPUT_DIR / "demo.json"
        with open(demo_path, "w") as f:
            json.dump(demo_data, f)
        print(f"Wrote {demo_path}")

        # Copy audio to frontend/public/demo.mp3
        frontend_demo = Path(__file__).resolve().parent.parent / "frontend" / "public" / "demo.mp3"
        import shutil
        shutil.copy2(args.demo_audio, frontend_demo)
        print(f"Copied demo audio to {frontend_demo}")
    else:
        # Generate demo data without audio (use a synthetic embedding)
        print("\nNo demo audio provided, generating synthetic demo data...")
        # Use a random but deterministic embedding for the demo
        rng = np.random.RandomState(123)
        demo_embedding = rng.randn(512).astype(np.float32)
        norm = np.linalg.norm(demo_embedding)
        if norm > 0:
            demo_embedding = demo_embedding / norm

        demo_images = brute_force_search(demo_embedding, image_entries, top_k=20)

        demo_data = {
            "embedding": demo_embedding.tolist(),
            "mood_energy": 0.5,
            "mood_valence": 0.5,
            "mood_tempo": 0.5,
            "mood_texture": 0.5,
            "images": demo_images,
        }

        demo_path = OUTPUT_DIR / "demo.json"
        with open(demo_path, "w") as f:
            json.dump(demo_data, f)
        print(f"Wrote {demo_path}")

    print("\nPre-computation complete!")


if __name__ == "__main__":
    main()
