# Evoke

**Turn music into visual inspiration.**

Evoke takes a piece of music and generates a Pinterest-style mood board of images that match its emotional and aesthetic qualities. It bridges the gap between what you hear and what you see — the same creative leap that musicians, designers, and artists make instinctively.

---

## Why This Exists

As a classical pianist, I've always experienced music visually. A Debussy prelude feels like watercolors bleeding into each other. A Bartók allegro feels like concrete and steel. This isn't unusual — the connection between sound and image is something most people feel, even if they can't articulate it.

I started thinking about visual discovery platforms like Pinterest and wondered: what if the starting point for visual inspiration wasn't a search query or a photo, but a song? What if you could say "find me images that feel like this music" and get back a curated board of visuals that capture the same mood, energy, and texture?

That's Evoke. It's a small experiment in cross-modal recommendation — using the emotional fingerprint of audio to retrieve visually resonant images.

---

## How It Works

### The Core Idea

Music and images both carry emotional information — energy, mood, warmth, complexity, tension. Evoke extracts these qualities from audio using a music understanding model, maps them into a shared representation space with image embeddings, and retrieves the most emotionally aligned images.

The user uploads or selects a track. The system listens, interprets, and responds with a visual mood board.

### User Flow

1. **Input** — Upload an audio file, paste a link, or choose from a curated library of classical, jazz, electronic, and ambient tracks.
2. **Analysis** — The system extracts the emotional and acoustic profile of the music: energy, valence, texture, harmonic complexity, rhythmic density.
3. **Retrieval** — Cross-modal search finds images whose visual qualities align with the audio's emotional fingerprint.
4. **Board** — A Pinterest-style grid of images is displayed, representing the "visual world" of the music.
5. **Refine** — Mood sliders (Energy, Warmth, Complexity, Abstraction) let the user adjust the board in real time, re-weighting the retrieval to explore different visual interpretations of the same piece.

---
s

## Architecture

### System Overview

Evoke has three layers: an audio understanding pipeline, an image retrieval pipeline, and a cross-modal bridge that connects them.

```
┌─────────────────────────────────────────────────────┐
│                    User Interface                    │
│         Audio input · Mood board · Refinement        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 Orchestration Layer                   │
│      Request handling · Caching · Session state      │
└─────┬───────────────────────────────────┬───────────┘
      │                                   │
      ▼                                   ▼
┌─────────────────┐             ┌─────────────────────┐
│  Audio Pipeline  │             │  Image Pipeline      │
│                  │             │                      │
│  Audio Encoder   │───────────▶│  Cross-Modal Bridge  │
│  Feature Extract │  Shared    │  Vector Search       │
│  Emotion Profile │  Space     │  Image Retrieval     │
└─────────────────┘             └─────────────────────┘
                                          │
                                          ▼
                                ┌─────────────────────┐
                                │   Image Index        │
                                │   Pre-embedded       │
                                │   visual corpus      │
                                └─────────────────────┘
```

### Audio Understanding Pipeline

**Model:** MuQ (Music Understanding Quantizer) — a self-supervised audio foundation model pretrained on large-scale music data. Selected for its strong performance on music understanding benchmarks and its ability to capture high-level musical semantics beyond raw acoustic features.

**Feature Extraction:** The audio encoder processes a track and produces a dense embedding that captures:

- **Energy** — Loudness contour, dynamic range, rhythmic intensity
- **Valence** — Major/minor tonality, harmonic tension and resolution patterns
- **Texture** — Timbral richness, instrumentation density, spectral complexity
- **Temporal arc** — How the emotional profile evolves across the piece

The system processes the full track but also segments it into windows to capture how the music's character shifts over time. The final audio embedding is a weighted combination of global and segment-level features.

### Image Retrieval Pipeline

**Model:** CLIP (Contrastive Language-Image Pretraining) — used to embed images into a semantically rich vector space where visual concepts like "warm," "chaotic," "serene," or "industrial" are spatially meaningful.

**Image Corpus:** A curated dataset of high-quality, aesthetically diverse images sourced from open datasets (Unsplash, WikiArt, Open Images). Each image is pre-embedded with CLIP and stored in a vector index. The corpus is tagged along emotional and aesthetic dimensions to support the cross-modal bridge.

**Vector Search:** Approximate nearest neighbor search over the image embedding index, returning the top-N most similar images to the query vector produced by the cross-modal bridge.

### Cross-Modal Bridge

This is the key architectural component — the layer that translates "what the music sounds like" into "what it looks like."

**Approach:** A learned projection layer that maps audio embeddings into CLIP's image embedding space. Trained on a dataset of music-image pairs where the pairing signal comes from:

- **Aesthetic tag co-occurrence** — Music and images independently labeled with mood/aesthetic tags (e.g., "melancholic," "energetic," "ethereal"), then paired by tag similarity.
- **Curated alignment data** — A smaller, hand-curated set of music-image pairs validated by musicians and visual artists, used for fine-tuning and evaluation.

The projection is intentionally simple — a shallow network rather than a deep one. The heavy lifting is done by the pretrained encoders on each side. The bridge just learns the correspondence between their respective spaces.

**Refinement mechanism:** When a user adjusts the mood sliders, the system applies learned direction vectors in CLIP space (e.g., the "warmth" direction, the "energy" direction) to shift the query embedding before re-running retrieval. This allows real-time exploration without re-processing the audio.

### Frontend

A responsive web application that displays results as a masonry grid — the familiar Pinterest board layout. Key interface elements:

- **Audio player** with waveform visualization showing the current analysis window
- **Mood board** with smooth loading and hover-to-expand on individual images
- **Refinement panel** with labeled sliders that update the board in real time
- **Save and share** — Export the board as an image or shareable link

Built with a component-based frontend framework. Designed to feel like a native visual discovery experience, not a research demo.

### Infrastructure

- **Audio processing** runs on serverless GPU (model inference on demand, scales to zero when idle)
- **Image index** is pre-built and served from a vector database
- **API layer** handles orchestration, caching of audio embeddings, and session state for slider interactions
- **Static assets and frontend** served from edge CDN

---

## Tech Stack

Technologies chosen to align with Pinterest's engineering stack while enabling learning and growth.

### Frontend
| Technology | Purpose |
|------------|---------|
| **React** | UI framework (Pinterest's primary frontend framework) |
| **TypeScript** | Type-safe JavaScript development |
| **Gestalt** | Pinterest's open-source React component library |
| **Vite** | Build tooling and dev server |

### Backend
| Technology | Purpose |
|------------|---------|
| **Go** | API server and orchestration layer (used at Pinterest for high-performance services) |
| **Gin** | Go web framework for REST APIs |

### Data Layer
| Technology | Purpose |
|------------|---------|
| **MySQL** | Primary relational database (Pinterest's core data store) |
| **Redis** | Caching layer for embeddings and session state |
| **Apache Kafka** | Event streaming for async audio processing jobs |

### ML Infrastructure
| Technology | Purpose |
|------------|---------|
| **PyTorch** | Model inference for MuQ audio encoder |
| **CLIP** | Image embeddings via OpenAI's model |
| **Milvus** | Vector database for image similarity search |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **AWS S3** | Audio file and image storage |
| **AWS EC2 / Lambda** | Compute for API and GPU inference |
| **Nginx** | Reverse proxy and static asset serving |

---

## Data Strategy

### Image Corpus Curation

Quality matters more than quantity. The image corpus is curated for:

- **Aesthetic diversity** — Fine art, photography, architecture, nature, abstract, urban, textural
- **Emotional range** — From serene to chaotic, warm to cold, minimal to dense
- **Visual quality** — High resolution, strong composition, no watermarks or text overlays
- **Licensing** — All images sourced from open or Creative Commons licensed collections

Target corpus size: 50,000–100,000 images. Large enough for meaningful retrieval diversity, small enough to curate with care.

### Training Data for Cross-Modal Bridge

The bridge model is trained on paired music-image data constructed through:

1. **Tag-based pairing** — Both music tracks and images are labeled with mood/aesthetic descriptors from a shared vocabulary. Pairs are formed by tag similarity, with negative sampling from mismatched pairs.
2. **Human validation** — A subset of pairs is validated by people with backgrounds in both music and visual arts to calibrate the model toward subjectively meaningful correspondences.
3. **Iterative refinement** — Early model outputs are reviewed and corrected, feeding back into training data for subsequent iterations.

---

## Evaluation

### Quantitative

- **Retrieval relevance** — Given a held-out set of human-validated music-image pairs, measure Recall@K for the cross-modal retrieval pipeline.
- **Embedding alignment** — Cosine similarity distribution between matched vs. random audio-image pairs in the shared space.
- **Diversity** — Ensure retrieved boards are visually diverse (not 10 near-identical images). Measured by average pairwise distance among retrieved image embeddings.

### Qualitative

- **User studies** — Do people feel the board "matches" the music? Evaluated through A/B comparisons (real board vs. random board for the same track).
- **Expert review** — Feedback from musicians and designers on whether the visual interpretations are meaningfully connected to the audio input.
- **Consistency** — Does similar music produce similar boards? Do contrasting pieces produce visually distinct boards?

---

## Scope and Constraints

This is a focused prototype, not a production system. Deliberate constraints:

- **Single-track input only** — No playlist analysis or DJ set parsing
- **Pre-built image corpus** — No real-time image generation or web scraping
- **English-language UI** — No localization in v1
- **No user accounts** — Stateless sessions, no saved boards (save-as-image only)
- **~30 second analysis time** — Acceptable for an exploratory, creative tool

---

## Future Directions

Ideas worth exploring beyond the initial prototype:

- **Genre-aware retrieval** — Different visual vocabularies for classical, electronic, jazz, hip-hop
- **Temporal boards** — A board that evolves as the music plays, with images shifting to match the current section
- **Reverse mode** — Input a Pinterest board and get back a playlist that matches its visual energy
- **Collaborative boards** — Multiple people listen to the same track and see how their visual interpretations differ
- **Integration with Pinterest API** — Pull images directly from Pinterest's corpus and let users save boards to their accounts

---

## About

Built by [Jai Dhiman](https://jaidhiman.com) — a classical pianist turned software engineer exploring the space between music and visual perception.

Background: Bachelor of Music in Performance from Berklee College of Music, 100+ professional concerts, published ML research in audio foundation models ([arXiv:2601.19029](https://arxiv.org/abs/2601.19029)).

This project grew from a simple question: if Pinterest helps people discover visual inspiration through images and text, what would it look like if the starting point was a song?
