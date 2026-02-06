# Evoke

Cross-modal recommendation system that generates Pinterest-style mood boards from music. Upload a track, get back images that match its emotional profile.

Built with **Go** / **React + TypeScript** / **PyTorch** / **Milvus**

## How It Works

1. User uploads audio (or picks from a sample library)
2. **MuQ** (audio foundation model) extracts an emotional embedding -- energy, valence, texture, temporal arc
3. A learned projection maps that embedding into **CLIP** image space
4. **Milvus** vector search retrieves the closest images from a pre-embedded corpus
5. Results display as a masonry grid with mood sliders (Energy, Warmth, Complexity, Abstraction) for real-time refinement

The sliders work by applying learned direction vectors in CLIP space to shift the query embedding without re-processing the audio.

## Architecture

```
React + TypeScript (Vite)
        |
    Go API (Gin) -- Redis cache
        |
   ┌────┴────┐
   |         |
MuQ audio   CLIP image
encoder     embeddings
   |         |
   └──┬──────┘
      |
  Projection Layer  -->  Milvus (ANN search)
  (audio -> CLIP space)      |
                        Image corpus
                     (Unsplash, WikiArt, Open Images)
```

**Audio pipeline** -- MuQ processes full tracks + windowed segments, produces a weighted global embedding capturing energy, valence, texture, and temporal arc.

**Cross-modal bridge** -- Shallow projection network trained on tag-paired music-image data (mood/aesthetic co-occurrence) plus a human-validated fine-tuning set. Intentionally simple -- the pretrained encoders do the heavy lifting.

**Image pipeline** -- ~50-100K curated images pre-embedded with CLIP, stored in Milvus. ANN search returns top-N results against the projected audio query.

## Project Structure

```
backend/          Go API server (Gin)
  cmd/server/       entrypoint
  internal/
    api/            routes + handlers (audio, board, health)
    services/       Milvus, Redis, ML client
    config/         env config

frontend/         React + TypeScript
  src/
    components/     AudioUploader, MoodBoard, MoodSliders,
                    WaveformPlayer, ImageCard
    hooks/          useAudioAnalysis, useMoodBoard
    api/            API client

ml/               Python ML service
  src/              MuQ encoder, CLIP bridge, gRPC server
  protos/           service definitions

data/             seed scripts, corpus metadata
scripts/          tooling (Milvus seeding, etc.)
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React, TypeScript, Gestalt (Pinterest's component library), Vite |
| Backend | Go, Gin, Redis |
| ML | PyTorch, MuQ, CLIP, gRPC |
| Data | MySQL, Milvus (vector DB), Kafka (async jobs) |
| Infra | Docker, AWS (S3, EC2/Lambda), Nginx |

## Getting Started

```bash
# clone and configure
cp .env.example .env

# run everything
make up        # docker-compose up

# or run individually
make backend   # Go API on :8080
make frontend  # React dev server on :5173
make ml        # ML service on :50051
```

## Motivation

I'm a former professional musician (Berklee B.A., 100+ concerts, 2 international tours) who transitioned into software engineering. Music has always been visual to me, a Debussy prelude feels like watercolors, a Bartok allegro feels like concrete. This project asks: what if visual discovery started from a song instead of a search query?

Published related research on audio foundation models: [arXiv:2601.19029](https://arxiv.org/abs/2601.19029)

---

Built by [Jai Dhiman](https://www.jaidhiman.com)
