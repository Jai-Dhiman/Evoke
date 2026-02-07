package vectorstore

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"math"
	"sort"
)

//go:embed data/images.json
var imagesData []byte

//go:embed data/directions.json
var directionsData []byte

//go:embed data/demo.json
var demoData []byte

type ImageEntry struct {
	URL       string    `json:"url"`
	Embedding []float32 `json:"embedding"`
}

type DirectionVectors struct {
	Energy  []float32 `json:"energy"`
	Valence []float32 `json:"valence"`
	Tempo   []float32 `json:"tempo"`
	Texture []float32 `json:"texture"`
}

type DemoData struct {
	Embedding   []float32     `json:"embedding"`
	MoodEnergy  float32       `json:"mood_energy"`
	MoodValence float32       `json:"mood_valence"`
	MoodTempo   float32       `json:"mood_tempo"`
	MoodTexture float32       `json:"mood_texture"`
	Images      []ImageResult `json:"images"`
}

type ImageResult struct {
	ID       int     `json:"id"`
	ImageURL string  `json:"image_url"`
	Score    float32 `json:"score"`
}

type VectorStore struct {
	images     []ImageEntry
	directions DirectionVectors
	demo       DemoData
}

func New() (*VectorStore, error) {
	vs := &VectorStore{}

	if err := json.Unmarshal(imagesData, &vs.images); err != nil {
		return nil, fmt.Errorf("failed to parse images.json: %w", err)
	}

	if err := json.Unmarshal(directionsData, &vs.directions); err != nil {
		return nil, fmt.Errorf("failed to parse directions.json: %w", err)
	}

	if err := json.Unmarshal(demoData, &vs.demo); err != nil {
		return nil, fmt.Errorf("failed to parse demo.json: %w", err)
	}

	return vs, nil
}

func (vs *VectorStore) Search(embedding []float32, topK int) []ImageResult {
	type scored struct {
		index int
		dist  float32
	}

	results := make([]scored, 0, len(vs.images))
	for i, img := range vs.images {
		dist := l2Distance(embedding, img.Embedding)
		results = append(results, scored{index: i, dist: dist})
	}

	sort.Slice(results, func(i, j int) bool {
		return results[i].dist < results[j].dist
	})

	if topK > len(results) {
		topK = len(results)
	}

	out := make([]ImageResult, topK)
	for i := 0; i < topK; i++ {
		idx := results[i].index
		out[i] = ImageResult{
			ID:       idx,
			ImageURL: vs.images[idx].URL,
			Score:    results[i].dist,
		}
	}

	return out
}

// RefineEmbedding applies mood slider adjustments to a base embedding.
// This is an exact port of bridge.py:87-113.
func (vs *VectorStore) RefineEmbedding(base []float32, energy, valence, tempo, texture float32) []float32 {
	dim := len(base)
	refined := make([]float32, dim)
	copy(refined, base)

	for i := 0; i < dim; i++ {
		var adjustment float32
		if i < len(vs.directions.Energy) {
			adjustment += vs.directions.Energy[i] * (energy - 0.5) * 0.2
		}
		if i < len(vs.directions.Valence) {
			adjustment += vs.directions.Valence[i] * (valence - 0.5) * 0.2
		}
		if i < len(vs.directions.Tempo) {
			adjustment += vs.directions.Tempo[i] * (tempo - 0.5) * 0.15
		}
		if i < len(vs.directions.Texture) {
			adjustment += vs.directions.Texture[i] * (texture - 0.5) * 0.15
		}
		refined[i] += adjustment
	}

	// L2 normalize
	var norm float64
	for _, v := range refined {
		norm += float64(v) * float64(v)
	}
	norm = math.Sqrt(norm)
	if norm > 0 {
		for i := range refined {
			refined[i] = float32(float64(refined[i]) / norm)
		}
	}

	return refined
}

func (vs *VectorStore) GetDemo() *DemoData {
	return &vs.demo
}

func (vs *VectorStore) ImageCount() int {
	return len(vs.images)
}

func l2Distance(a, b []float32) float32 {
	var sum float64
	n := len(a)
	if len(b) < n {
		n = len(b)
	}
	for i := 0; i < n; i++ {
		d := float64(a[i]) - float64(b[i])
		sum += d * d
	}
	return float32(math.Sqrt(sum))
}
