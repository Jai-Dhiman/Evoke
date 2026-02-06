# Evoke Enhancement Plan: Advanced Recommendation Techniques

## Context

Evoke is a cross-modal recommendation system that generates Pinterest-style mood boards from music. The current pipeline has a **fundamental alignment problem**: hand-crafted librosa audio features (zero-padded to 512 dims) are compared against CLIP image embeddings via an identity matrix "projection" (`bridge.py:43`). These vectors occupy entirely different semantic spaces -- any useful retrieval results are coincidental. The mood slider refinement compounds this by using synthetic direction vectors (`np.linspace`, `np.sin`, `np.cos`) that have no relationship to CLIP embedding geometry.

The enhancements below address this systematically, from fixing the foundation to adding genuinely novel interaction paradigms. Each technique includes the specific code locations it modifies, training data requirements, and implementation approach.

---

## Tier 1: Foundation (Fix the Core Pipeline)

### Enhancement 1: Semantic Mood Direction Vectors

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

**Why this matters:** This is the single highest-impact change relative to effort. It transforms the slider interaction from meaningless noise to genuine semantic navigation. A user sliding "energy" toward "intense" will actually see the mood board shift toward more vibrant, high-energy imagery.

---

### Enhancement 2: CLAP Audio Encoder with Learned Projection

**Problem:** `audio_encoder.py:114-190` extracts ~160 hand-crafted librosa statistics (mel spectrogram means/stds, MFCC stats, chroma stats, spectral features, rhythm, energy), zero-pads to 512 dims, and L2 normalizes. These statistics capture signal-level properties but not the semantic/emotional content that matters for visual association. The identity matrix projection in `bridge.py:43` (`np.eye(512)`) then passes these through unchanged to compare against CLIP image embeddings -- a meaningless comparison.

**Solution:** Replace the entire audio encoding pipeline with CLAP (Contrastive Language-Audio Pretraining), which produces embeddings aligned with text descriptions of sound. Then train a small linear projection to map CLAP audio space into CLIP image space using the MusicCaps dataset.

**Approach -- CLAP Encoder:**
1. Add `laion/larger_clap_music_and_speech` model (HuggingFace, designed specifically for music)
2. Replace `AudioEncoder._compute_embedding()` with a CLAP forward pass:
   - Load audio waveform (keep existing `_load_audio`)
   - Process through CLAP audio encoder -> 512-dim embedding
   - This embedding captures semantic audio content (mood, genre, instrumentation, energy)
3. Keep `_extract_mood()` as-is for the slider initial values -- librosa features are fine for basic mood estimation

**Approach -- Learned Projection (CLAP -> CLIP):**
1. Download Google's MusicCaps dataset (~5.5K music clips with human-written text captions)
2. For each clip: extract CLAP audio embedding + encode caption with CLIP text encoder
3. Since CLIP text and image spaces are aligned, CLIP text embeddings serve as proxy targets for image space
4. Train a 512x512 linear projection W minimizing:
   `loss = -mean(cosine_sim(W @ clap_audio, clip_text))` (for matched pairs)
   plus contrastive negatives (InfoNCE) using in-batch negatives
5. Architecture: single `nn.Linear(512, 512)` followed by L2 normalization
   - A linear projection is sufficient here because both CLAP and CLIP already produce well-structured embedding spaces. The projection learns the rotation/scaling between them.
   - Alternative: 2-layer MLP with LayerNorm + GELU if linear proves insufficient (but start simple)
6. Save trained weights to `ml/models/clap_to_clip_projection.pt`
7. Replace `self._projection = np.eye(512)` in `bridge.py:43` with loading the trained projection

**Training pipeline (new script):**
```
scripts/train_projection.py
  1. Download MusicCaps audio (YouTube clips via yt-dlp)
  2. Extract CLAP embeddings for all clips (batch, GPU)
  3. Encode captions with CLIP text encoder (batch, GPU)
  4. Train linear projection with AdamW, cosine annealing LR
  5. Validate on 10% held-out split (retrieval recall@10)
  6. Save best checkpoint
```

**Files modified:**
- `ml/src/audio_encoder.py` -- replace `_compute_embedding()`, add CLAP model loading to `load_model()`
- `ml/src/bridge.py` -- replace `self._projection = np.eye(...)` with loading trained projection weights in `load_model()`, update `project_to_clip_space()` to use PyTorch forward pass
- `ml/src/config.py` -- add `CLAP_MODEL` config field
- `ml/pyproject.toml` -- add `transformers[audio]` or `laion-clap` dependency

**New files:**
- `scripts/train_projection.py` -- training pipeline
- `ml/models/clap_to_clip_projection.pt` -- trained weights (generated, not committed)

**Training data:** MusicCaps (~5.5K pairs, free from Google). 5.5K pairs is sufficient for a 512x512 linear projection (262K parameters). With InfoNCE contrastive loss and batch size 256, this trains in ~10 minutes on a single GPU or ~1 hour on CPU.

---

### Enhancement 3: Text-Based Query Refinement

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

---

## Tier 2: Retrieval Quality

### Enhancement 4: MMR (Maximal Marginal Relevance) Re-ranking

**Problem:** `milvus.go:17` returns `TopK = 20` results by pure L2 distance. When the image corpus is large, this often produces visually redundant results -- 20 variations of the same sunset, for instance.

**Solution:** Fetch more candidates than needed, then iteratively select results that balance relevance with diversity.

**Approach:**
1. Change `TopK` from 20 to 60 in `milvus.go` (fetch 3x candidates)
2. Add `"embedding"` to the output fields in the search call (`milvus.go:118`) so candidate embeddings are returned
3. Implement MMR selection in Go:
   ```
   For each of 20 selections:
     score(d) = lambda * sim(d, query) - (1-lambda) * max_sim(d, already_selected)
     Select d with highest score
   ```
   where lambda = 0.7 balances relevance vs diversity
4. Return the 20 MMR-selected results instead of the raw top-20

**Files modified:**
- `backend/internal/services/milvus.go` -- modify `Search()` to fetch 60, add `RerankMMR()` function, update `ImageResult` to include embedding for pairwise comparison

**Note on metric:** Current metric is L2 (`milvus.go:14`). MMR typically uses cosine similarity. Since embeddings are L2-normalized, cosine_sim = 1 - L2^2/2, so conversion is straightforward. Or switch the Milvus index to cosine/IP metric.

---

### Enhancement 5: Expanded Image Index

**Problem:** The current corpus is 20 hardcoded Unsplash URLs (`seed_milvus.py:41-62`). This is insufficient to demonstrate recommendation quality -- with 20 images, vector search is essentially random selection.

**Solution:** Scale to 5K-10K curated images with batch CLIP embedding computation.

**Approach:**
1. Source images from Unsplash dataset (free for developers) or LAION-Aesthetics subset (filtered for high aesthetic quality)
2. Expand `seed_milvus.py` into a batch pipeline:
   - Read URLs/paths from a file or directory
   - Process in GPU-accelerated batches (CLIP's `CLIPProcessor` supports batch inputs, ~10x speedup)
   - Insert into Milvus in batches of 1000
   - Add progress tracking with `tqdm`
3. Compute and store metadata alongside embeddings (see Enhancement 6)

**Files modified:**
- `scripts/seed_milvus.py` -- rewrite as batch pipeline

**Image sourcing options:**
- Unsplash API: free, high quality, searchable by mood/scene keywords
- LAION-Aesthetics: large-scale, pre-filtered for visual quality, includes aesthetic scores
- WikiArt: art-focused, good for painterly/abstract aesthetic that suits music-to-visual
- Mix of all three for visual diversity

---

### Enhancement 6: Hybrid Search with Metadata Filtering

**Problem:** Vector similarity alone cannot capture all desirable matching criteria. An audio track that is "calm and dark" should not just find semantically similar images -- it should specifically find images that are dark in luminance and subdued in color.

**Solution:** Enrich the Milvus schema with structured metadata fields and use Milvus's boolean expression filtering to combine vector search with hard constraints.

**Approach:**
1. Add schema fields to the Milvus collection:
   - `mood_tags` (VarChar): JSON array from CLIP zero-shot classification against mood prompts
   - `scene_type` (VarChar): nature/urban/abstract/portrait/indoor/outdoor via CLIP zero-shot
   - `brightness` (Float): mean luminance (0-1)
   - `color_temperature` (Float): warm-cool scale derived from dominant colors
   - `complexity` (Float): edge density or spectral entropy of the image
2. Compute metadata at seed time using CLIP zero-shot classification + basic image processing
3. At query time, map audio mood features to metadata constraints:
   - High energy -> brightness >= 0.4
   - Low valence -> color_temperature <= 0.4 (cool tones)
   - High texture -> complexity >= 0.5
4. Pass constraints as Milvus filter expressions in `Search()` (currently empty string at `milvus.go:117`)

**Files modified:**
- `backend/internal/services/milvus.go` -- expand schema in `EnsureCollection()`, accept filter params in `Search()`
- `backend/internal/api/handlers/board.go` -- construct filters from mood values
- `scripts/seed_milvus.py` -- compute and insert metadata fields

---

## Tier 3: User Feedback Loop

### Enhancement 7: Implicit Feedback Collection

**Problem:** User interactions are discarded. `ImageCard.tsx` fires `onClick` which opens the URL in a new tab (`App.tsx:65-67`). No signal about what the user likes or dislikes is captured.

**Solution:** Track user interactions and use them to adapt the query embedding within a session.

**Approach -- Frontend:**
1. Track events on `ImageCard`:
   - **Click** (existing, add tracking)
   - **Long hover** (>1.5s, indicates interest)
   - **Save/favorite** (new heart icon overlay on cards)
   - **Dismiss** (new X icon overlay, "show less like this")
2. Batch events and send to backend periodically or on board refresh

**Approach -- Backend:**
1. New endpoint: `POST /api/feedback`
2. Store feedback events in Redis alongside session data:
   - Extend `SessionData` in `cache.go:17` with `LikedImageIDs []int64` and `DismissedImageIDs []int64`
3. On next search/refine request, if feedback exists:
   - Fetch embeddings of liked images from Milvus
   - Compute liked centroid
   - Adjust query: `adjusted = 0.75 * query + 0.25 * liked_centroid`
   - For dismissed images: subtract a fraction of their centroid
   - The weights shift as more feedback accumulates (alpha decreases from 0.85 toward 0.5)

**Files modified:**
- `frontend/src/components/ImageCard.tsx` -- add hover tracking, save/dismiss buttons
- `frontend/src/api/client.ts` -- add `sendFeedback()` API call
- `frontend/src/App.tsx` -- wire feedback handlers
- `backend/internal/api/handlers/board.go` -- add feedback handler, modify `GetBoard`/`Refine` to apply feedback adjustment
- `backend/internal/api/router.go` -- register feedback route
- `backend/internal/services/cache.go` -- extend `SessionData` struct

---

### Enhancement 8: Session-Based State Evolution

**Problem:** Each slider adjustment independently refines the base embedding. There's no cumulative learning from the sequence of user actions within a session.

**Solution:** Maintain an evolving "session embedding" that accumulates all user signals.

**Approach:**
1. Store a `CurrentEmbedding` in `SessionData` (separate from the original `Embedding`)
2. Each action modifies `CurrentEmbedding`:
   - Slider change: apply semantic direction vectors (Enhancement 1) to `CurrentEmbedding`
   - Image like: `CurrentEmbedding = 0.9 * CurrentEmbedding + 0.1 * liked_image_embedding`
   - Image dismiss: `CurrentEmbedding = CurrentEmbedding - 0.05 * dismissed_embedding`, then renormalize
   - Text refine: blend text embedding into `CurrentEmbedding`
3. Always search using `CurrentEmbedding`, not the original
4. "Start Over" resets `CurrentEmbedding` back to the original `Embedding`

**Files modified:**
- `backend/internal/services/cache.go` -- add `CurrentEmbedding` field to `SessionData`
- `backend/internal/api/handlers/board.go` -- use `CurrentEmbedding` for searches, update it on each action

---

## Tier 4: Advanced Techniques

### Enhancement 9: Temporal Audio Modeling

**Problem:** The entire audio clip is collapsed into a single embedding by averaging features over time (`audio_encoder.py:125-128`, statistics across temporal axis). A song's intro, verse, chorus, and bridge evoke different visual imagery -- this is lost.

**Solution:** Compute per-segment embeddings and allow users to explore the temporal arc of the music.

**Approach:**
1. Segment audio into 5-second windows with 2.5-second overlap
2. Extract CLAP embeddings per segment (after Enhancement 2)
3. Attention-based pooling for the global embedding:
   ```python
   class TemporalAttentionPool(nn.Module):
       def __init__(self, dim=512):
           self.attn = nn.Sequential(nn.Linear(dim, 128), nn.Tanh(), nn.Linear(128, 1))
       def forward(self, segments):  # (n_segments, 512)
           weights = F.softmax(self.attn(segments), dim=0)
           return (weights * segments).sum(dim=0)
   ```
4. Return segment embeddings + timestamps in the gRPC response
5. Frontend: timeline markers on the `WaveformPlayer` -- clicking a segment updates the mood board with that segment's embedding

**Files modified:**
- `ml/protos/ml_service.proto` -- extend `AnalyzeAudioResponse` with `repeated SegmentEmbedding segments`
- `ml/src/audio_encoder.py` -- add segmentation and per-segment encoding
- `ml/src/server.py` -- return segment data
- `backend/proto/` -- regenerate
- `backend/internal/api/handlers/board.go` -- support segment-based search
- `frontend/src/components/WaveformPlayer.tsx` -- add segment markers, click-to-seek
- `frontend/src/App.tsx` -- wire segment selection

---

### Enhancement 10: Multi-Objective Retrieval

**Problem:** Pure similarity retrieval optimizes for a single objective. A good mood board should be relevant, diverse, novel (not previously seen), and cover different aspects of the audio's character.

**Solution:** Submodular greedy selection optimizing for multiple objectives simultaneously.

**Approach:**
1. Fetch 100 candidates from Milvus
2. Iteratively select 20 results maximizing:
   ```
   score(d) = w_rel * cosine(d, query)
            + w_div * min_distance_to_selected(d)
            + w_nov * novelty(d)  // 0 if seen before in session, 1 otherwise
            + w_cov * coverage(d)  // similarity to underrepresented audio segments
   ```
   Default weights: w_rel=0.5, w_div=0.25, w_nov=0.15, w_cov=0.1
3. Submodular guarantee: greedy selection gives (1-1/e) ~ 63% approximation of optimal

**Files modified:**
- `backend/internal/services/milvus.go` -- extends Enhancement 4's MMR with additional objectives

---

### Enhancement 11: Generative Augmentation

**Problem:** Retrieval is limited to existing images in the index. For niche or highly specific audio moods, the corpus may not contain good matches.

**Solution:** Generate images conditioned on the audio's semantic content using Stable Diffusion, mixed into the retrieved results.

**Approach:**
1. Convert audio embedding to a text prompt:
   - Use CLAP to find the k-nearest text descriptions
   - Or use a small trained caption generator (CLAP embedding -> text decoder)
2. Feed text prompt to an image generation API:
   - Self-hosted: `diffusers` library with SDXL (requires GPU)
   - External: Replicate, Together AI, or Stability AI API (no GPU required, adds latency + cost)
3. Generate 2-4 images per audio upload
4. Display generated images in a separate "Imagined" section of the mood board, or interleave with retrieved results
5. Optionally: add generated images back into the Milvus index for future retrieval

**Files modified:**
- `ml/src/server.py` -- add `GenerateImages` RPC
- `ml/protos/ml_service.proto` -- new message types
- `backend/internal/api/handlers/board.go` -- orchestrate generation + retrieval
- `frontend/src/App.tsx` / `MoodBoard.tsx` -- display generated images with distinct styling

---

### Enhancement 12: HNSW Index

**Problem:** IVF_FLAT (`milvus.go:15`) with `nlist=128` is fine for small datasets but has lower recall than HNSW at scale.

**Solution:** Switch to HNSW when the collection exceeds ~10K images.

**Approach:**
- Change `IndexType = entity.IvfFlat` to `entity.HNSW` in `milvus.go:15`
- Parameters: M=16, efConstruction=200 (build), ef=64 (search)
- HNSW uses ~1.5x memory but provides better recall at the same query latency
- No training phase required (unlike IVF which needs a training step)

**Files modified:**
- `backend/internal/services/milvus.go` -- index type and search params

---

## Model Comparison

| Model | Space Alignment | Music Quality | Availability | Verdict |
|-------|----------------|---------------|--------------|---------|
| **CLAP** (`laion/larger_clap_music`) | Text-aligned (needs bridge to CLIP) | Excellent (trained on music) | HuggingFace, open | **Primary choice** |
| **AudioCLIP** | Direct audio-visual alignment | Moderate (trained on environmental sounds) | GitHub, open | Backup option |
| **MuQ** (referenced in README) | Custom emotional space | Unknown | Not publicly available | Future option |
| **Librosa + MLP** | Requires full training | Bounded by hand-crafted features | N/A | Last resort |

---

## Dependency Graph

```
Enhancement 1 (Mood Directions)    -- standalone, no dependencies
Enhancement 2 (CLAP + Projection)  -- standalone, no dependencies
Enhancement 3 (Text Refinement)    -- standalone, benefits from 1+2
Enhancement 4 (MMR)                -- standalone
Enhancement 5 (Expand Index)       -- standalone, prerequisite for 6
Enhancement 6 (Hybrid Search)      -- depends on 5
Enhancement 7 (Feedback)           -- benefits from 4
Enhancement 8 (Session Evolution)  -- depends on 7
Enhancement 9 (Temporal)           -- depends on 2
Enhancement 10 (Multi-Objective)   -- extends 4, benefits from 7+9
Enhancement 11 (Generative)        -- benefits from 2
Enhancement 12 (HNSW)              -- depends on 5
```

Recommended implementation order: 1 -> 2 -> 5 -> 4 -> 3 -> 6 -> 7 -> 8 -> 9 -> 10 -> 12 -> 11

---

## Critical Files Reference

| File | Current State | Enhancements |
|------|--------------|--------------|
| `ml/src/bridge.py` | Identity projection, synthetic mood directions | 1, 2, 3, 7, 8 |
| `ml/src/audio_encoder.py` | Librosa features, zero-padded to 512 | 2, 9 |
| `ml/src/server.py` | AnalyzeAudio + RefineEmbedding RPCs | 3, 9, 11 |
| `ml/protos/ml_service.proto` | 3 RPCs, basic request/response types | 3, 9, 11 |
| `ml/src/config.py` | CLIP model path, audio params | 2 |
| `backend/internal/services/milvus.go` | IVF_FLAT, L2, TopK=20, basic schema | 4, 5, 6, 10, 12 |
| `backend/internal/services/cache.go` | SessionData with embedding + mood values | 7, 8 |
| `backend/internal/api/handlers/board.go` | GetBoard + Refine handlers | 3, 7, 8 |
| `scripts/seed_milvus.py` | 20 Unsplash URLs, sequential processing | 5, 6 |
| `frontend/src/App.tsx` | Upload, sliders, board display | 3, 7, 9 |
| `frontend/src/components/ImageCard.tsx` | Click-to-open, no feedback tracking | 7 |

---

## Verification Strategy

**Per-enhancement verification:**
1. **Mood Directions:** Upload the same audio file, sweep each slider min-to-max. Verify board changes are visually coherent (energy slider should shift brightness/intensity, not random variation).
2. **CLAP + Projection:** Compare retrieval results between old librosa pipeline and new CLAP pipeline using 5 diverse audio samples. New results should be semantically related to the audio's mood.
3. **Text Refinement:** Upload audio, then type "ocean" -- verify ocean-related images appear. Type "neon city" -- verify shift to urban/neon imagery.
4. **MMR:** Upload audio, inspect 20 results. Before: potential duplicates. After: visually distinct results covering different aspects of the mood.
5. **Expanded Index:** Run `make seed` with batch script, verify Milvus entity count matches expected. Spot-check 10 random embeddings for correct dimensionality and normalization.
6. **Hybrid Search:** Upload calm, dark audio. Verify returned images are predominantly dark/cool-toned (metadata filtering active).
7. **Feedback:** Click/hover on several images, refresh. Verify new results lean toward the style of liked images and away from dismissed images.
8. **Session Evolution:** Perform a sequence of actions (adjust sliders, like images, type text). Verify each action builds on the previous, and "Start Over" fully resets.
9. **Temporal:** Upload a 30-second clip with distinct sections. Click different timeline markers. Verify mood board changes between sections.
10. **Multi-Objective:** Verify result set has no near-duplicate images and includes at least 3 visually distinct "clusters".

**Integration test:** Full flow -- upload audio -> inspect initial board -> adjust sliders -> type refinement text -> like/dismiss images -> verify board improves -> start over -> verify clean reset.
