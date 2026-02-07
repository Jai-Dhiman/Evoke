# Evoke Enhancement Plan

## Context

Evoke is a cross-modal recommendation system that generates Pinterest-style mood boards from music. The current pipeline has a **fundamental alignment problem**: hand-crafted librosa audio features (zero-padded to 512 dims) are compared against CLIP image embeddings via an identity matrix "projection" (`bridge.py:43`). These vectors occupy entirely different semantic spaces -- any useful retrieval results are coincidental. The mood slider refinement compounds this by using synthetic direction vectors (`np.linspace`, `np.sin`, `np.cos`) that have no relationship to CLIP embedding geometry.

This plan is scoped to the changes that materially improve the demo and codebase quality. Enhancements are prioritized by their impact on a live demo and code review, not theoretical completeness.

---

## Implementation Scope

### Step 1: Semantic Mood Direction Vectors (~2 hours)

**Problem:** `bridge.py:90-103` uses `np.linspace`, `np.sin`, `np.cos`, and seeded random vectors as mood directions. These are arbitrary mathematical functions with zero semantic meaning in CLIP space. Moving the energy slider produces random vector perturbations, not movement toward "intense" or "calm" imagery.

**Solution:** Derive direction vectors empirically from CLIP's own text encoder. CLIP's text and image spaces are aligned -- text embeddings for mood concepts point in semantically meaningful directions within the image retrieval space.

**Approach:**
1. Define text prompts for each slider's extremes:
   - Energy: ["intense", "powerful", "vibrant", "explosive", "dynamic"] vs ["calm", "peaceful", "serene", "tranquil", "gentle"]
   - Valence: ["bright", "joyful", "warm", "colorful", "cheerful"] vs ["dark", "melancholic", "moody", "somber", "cold"]
   - Tempo: ["rapid", "energetic", "racing", "urgent", "frenetic"] vs ["slow", "languid", "still", "frozen", "meditative"]
   - Texture: ["intricate", "complex", "detailed", "layered", "ornate"] vs ["minimal", "clean", "simple", "sparse", "bare"]
2. At model load time, encode all prompts via the existing `bridge.encode_text()` method
3. Compute direction = mean(high_embeddings) - mean(low_embeddings), L2 normalized
4. Cache these 4 direction vectors as instance attributes
5. Replace the synthetic directions in `refine_embedding()` with the cached vectors

**Files modified:**
- `ml/src/bridge.py` -- `load_model()` (add direction computation after CLIP loads), `refine_embedding()` (replace lines 90-103)

**Training data:** None. Uses CLIP's pre-trained text understanding.

**Why this matters:** Highest-impact change relative to effort. Transforms slider interaction from meaningless noise to genuine semantic navigation. A user sliding "energy" toward "intense" will actually see the mood board shift toward more vibrant, high-energy imagery. This is the difference between a broken demo and a convincing one.

**Verification:** Upload the same audio file, sweep each slider min-to-max. Board changes should be visually coherent (energy slider shifts brightness/intensity, valence shifts warmth/coolness, etc.).

---

### Step 2: Expanded Image Index (~4 hours)

**Problem:** The current corpus is 20 hardcoded Unsplash URLs (`seed_milvus.py:41-62`). With 20 images, vector search is essentially random selection -- there is no retrieval quality to evaluate or demonstrate.

**Solution:** Scale to 2-3K curated images with batch CLIP embedding computation.

**Approach:**
1. Source images from Unsplash dataset (free for developers) or LAION-Aesthetics subset (filtered for high aesthetic quality)
2. Expand `seed_milvus.py` into a batch pipeline:
   - Read URLs/paths from a file or directory
   - Process in GPU-accelerated batches (CLIP's `CLIPProcessor` supports batch inputs, ~10x speedup)
   - Insert into Milvus in batches of 1000
   - Add progress tracking with `tqdm`

**Files modified:**
- `scripts/seed_milvus.py` -- rewrite as batch pipeline

**Image sourcing options:**
- Unsplash API: free, high quality, searchable by mood/scene keywords
- LAION-Aesthetics: large-scale, pre-filtered for visual quality, includes aesthetic scores
- WikiArt: art-focused, good for painterly/abstract aesthetic that suits music-to-visual
- Mix of all three for visual diversity

**Why this matters:** Non-negotiable for a credible demo. With 20 images, "recommendation" is indistinguishable from random selection. With 2-3K images, the semantic direction vectors from Step 1 can actually produce meaningful retrieval differences when sliders change.

**Verification:** Run the batch seed script, verify Milvus entity count matches expected. Spot-check 10 random embeddings for correct dimensionality (512) and L2 normalization.

---

### Step 3: Test Suite (~4 hours)

**Problem:** Zero test files exist anywhere in the codebase. This is the single biggest code-quality red flag for anyone reviewing the repo.

**Solution:** Add focused tests covering critical paths in each service. Not aiming for full coverage -- aiming to demonstrate engineering discipline and test the contracts that matter.

**Backend (Go):**
- Handler tests: verify API contracts for `/api/sessions`, `/api/analyze`, `/api/board`, `/api/refine` (mock services, test HTTP status codes, response shapes, error cases)
- Service tests: CacheService serialization round-trip, MilvusService search parameter construction
- Use Go's `httptest` package and table-driven tests

**ML Service (Python):**
- Bridge tests: verify `encode_text()` returns 512-dim L2-normalized vectors, verify `refine_embedding()` output shape and normalization, verify semantic direction vectors are computed correctly (Step 1)
- Audio encoder tests: verify `_extract_mood()` returns values in [0, 1], verify embedding dimension and normalization
- Use `pytest`

**Frontend (TypeScript):**
- API client tests: verify request construction and response parsing
- Hook tests: basic state management for `useAudioAnalysis` and `useMoodBoard`
- Use `vitest` (already available via Vite)

**Files created:**
- `backend/internal/api/handlers/audio_handler_test.go`
- `backend/internal/api/handlers/board_handler_test.go`
- `backend/internal/services/cache_test.go`
- `ml/tests/test_bridge.py`
- `ml/tests/test_audio_encoder.py`
- `frontend/src/api/client.test.ts`

**Why this matters:** If anyone looks at the code (and engineers on an interview panel might), the presence of tests signals "this person writes production code." The absence of tests signals "this is a weekend hack." It's the difference between a project and a portfolio piece.

**Verification:** `make test` passes across all three services.

---

### Step 4: Text-Based Query Refinement (~4 hours)

**Problem:** Users can only steer the mood board through 4 fixed sliders. There's no way to express specific visual concepts like "ocean", "neon", "watercolor", or "brutalist architecture".

**Solution:** Add a text input that modifies the query embedding using CLIP arithmetic. CLIP embeddings support meaningful addition/subtraction (analogous to word2vec), so encoding "ocean" with CLIP's text encoder and adding it to the audio embedding shifts retrieval toward ocean-related imagery while preserving the audio's mood.

**Approach:**
1. New gRPC method in the proto: `TextRefine(TextRefineRequest) returns (RefineEmbeddingResponse)`
2. ML service implementation: encode user text via existing `bridge.encode_text()`, blend with base embedding:
   `refined = normalize(alpha * base_embedding + (1-alpha) * text_embedding)`
   where alpha ~0.6-0.7 (audio-dominant, text as modifier)
3. New Go handler endpoint: `POST /api/board/text-refine`
4. Frontend: text input in the sidebar below mood sliders, debounced submission

**Files modified:**
- `ml/protos/ml_service.proto` -- add `TextRefineRequest` message and `TextRefine` RPC
- `ml/src/server.py` -- implement `TextRefine` handler
- `ml/src/bridge.py` -- add `text_refine_embedding()` method (trivial, ~10 lines using existing `encode_text`)
- `backend/proto/` -- regenerate Go gRPC code
- `backend/internal/services/ml_client.go` -- add `TextRefineEmbedding()` client method
- `backend/internal/api/handlers/board.go` -- add `TextRefine()` handler
- `backend/internal/api/router.go` -- register new route
- `frontend/src/App.tsx` -- add text input state and handler
- `frontend/src/api/client.ts` -- add `textRefine()` API call
- `frontend/src/types/index.ts` -- add request/response types

**Why this matters:** This is the killer demo feature. Type "ocean" and the board shifts to ocean imagery. Type "neon city" and it shifts to urban neon. It's interactive, immediately legible, and directly maps to Pinterest's own text search + visual search paradigm. The interviewer can play with it.

**Verification:** Upload audio, then type "ocean" -- verify ocean-related images appear. Type "neon city" -- verify shift to urban/neon imagery. Verify the audio mood is preserved (results aren't purely text-driven).

---

## Out of Scope (Interview Talking Points)

The following enhancements are deliberately excluded from implementation. Each is well-understood and can be discussed in detail during interviews to demonstrate depth of thinking without over-engineering the demo.

### CLAP Audio Encoder with Learned Projection
The current audio encoder uses librosa features with an identity matrix projection -- the audio-to-CLIP mapping is fundamentally broken. The fix is replacing the encoder with CLAP (`laion/larger_clap_music_and_speech`) and training a 512x512 linear projection on MusicCaps (~5.5K paired audio-text samples). This is the "right" technical solution but requires days of work (downloading MusicCaps via yt-dlp, extracting CLAP embeddings, training with InfoNCE loss, validation). The current librosa encoder is honest about being a placeholder, and the demo works well enough with semantic direction vectors (Step 1) doing the heavy lifting for slider interaction.

### MMR Re-ranking
Fetch 3x candidates from Milvus, iteratively select results balancing relevance (cosine similarity to query) with diversity (minimum distance to already-selected items). Lambda=0.7. ~50 lines of Go. Low visible impact in a demo but good for discussing retrieval quality trade-offs.

### Implicit Feedback Collection
Track user interactions (clicks, long hovers, saves, dismissals) and use them to adapt the query embedding within a session. Adjust query by blending liked-image centroids. Directly relevant to Pinterest's core product loop. Best discussed as architecture: "Here's how I'd close the feedback loop" rather than implemented as a half-working feature.

### Session-Based State Evolution
Maintain an evolving "session embedding" that accumulates all user signals (slider changes, likes, text refinement) rather than independently refining from the base embedding each time. Depends on feedback collection.

### Temporal Audio Modeling
Segment audio into 5-second windows, compute per-segment embeddings, add timeline markers to the waveform player so clicking a segment updates the mood board. Requires CLAP (out of scope) and attention-based pooling. Impressive but complex.

### Multi-Objective Retrieval
Submodular greedy selection optimizing for relevance, diversity, novelty, and coverage simultaneously. Extends MMR with additional objectives. Academic flavor -- good for demonstrating familiarity with recommendation literature.

### Hybrid Search with Metadata Filtering
Enrich Milvus schema with structured metadata (mood tags, scene type, brightness, color temperature, complexity) computed at seed time via CLIP zero-shot classification. Apply boolean filter expressions at query time.

### Generative Augmentation
Generate images conditioned on audio semantic content using Stable Diffusion when the corpus lacks good matches. Interleave generated images with retrieved results.

---

## Implementation Order

```
Step 1 (Semantic Directions) -- no dependencies
    |
Step 2 (Expand Index)        -- no dependencies, can parallelize with Step 1
    |
Step 3 (Tests)               -- benefits from Steps 1-2 being in place
    |
Step 4 (Text Refinement)     -- benefits from Steps 1-2 for demo quality
```

Steps 1 and 2 are independent and can be worked on in parallel.
Step 3 should cover the new code from Steps 1-2.
Step 4 is a full-stack feature that ties the demo together.

---

## Critical Files Reference

| File | Current State | Steps |
|------|--------------|-------|
| `ml/src/bridge.py` | Identity projection, synthetic mood directions | 1, 4 |
| `ml/src/audio_encoder.py` | Librosa features, zero-padded to 512 | 3 (tests) |
| `ml/src/server.py` | AnalyzeAudio + RefineEmbedding RPCs | 4 |
| `ml/protos/ml_service.proto` | 3 RPCs, basic request/response types | 4 |
| `backend/internal/services/milvus.go` | IVF_FLAT, L2, TopK=20, basic schema | 2 |
| `backend/internal/api/handlers/board.go` | GetBoard + Refine handlers | 4 |
| `scripts/seed_milvus.py` | 20 Unsplash URLs, sequential processing | 2 |
| `frontend/src/App.tsx` | Upload, sliders, board display | 4 |
| `frontend/src/api/client.ts` | Typed fetch wrapper | 4 |

---

## End-to-End Verification

After all steps are complete, the full demo flow should work:

1. Upload audio -> waveform player appears -> mood board loads with 20 images from a 2-3K corpus
2. Adjust sliders -> board shifts in semantically meaningful directions (energy = intensity, valence = warmth, etc.)
3. Type "ocean" in text input -> board shifts toward ocean imagery while preserving audio mood
4. Type "neon city" -> board shifts to urban/neon aesthetic
5. `make test` passes across all three services
