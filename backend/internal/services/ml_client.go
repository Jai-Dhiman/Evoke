package services

import (
	"context"
	"fmt"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type MLClient struct {
	conn *grpc.ClientConn
	addr string
}

type AnalysisResult struct {
	Embedding   []float32 `json:"embedding"`
	MoodEnergy  float32   `json:"mood_energy"`
	MoodValence float32   `json:"mood_valence"`
	MoodTempo   float32   `json:"mood_tempo"`
	MoodTexture float32   `json:"mood_texture"`
}

func NewMLClient(addr string) (*MLClient, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	conn, err := grpc.DialContext(ctx, addr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to ML service: %w", err)
	}

	return &MLClient{
		conn: conn,
		addr: addr,
	}, nil
}

func (c *MLClient) AnalyzeAudio(ctx context.Context, audioData []byte) (*AnalysisResult, error) {
	// TODO: Replace with actual gRPC call once proto is defined
	// For now, return stub data for integration testing

	// Simulated embedding (512 dimensions to match CLIP space)
	embedding := make([]float32, 512)
	for i := range embedding {
		embedding[i] = float32(i%100) / 100.0
	}

	return &AnalysisResult{
		Embedding:   embedding,
		MoodEnergy:  0.7,
		MoodValence: 0.6,
		MoodTempo:   0.5,
		MoodTexture: 0.4,
	}, nil
}

func (c *MLClient) RefineEmbedding(ctx context.Context, baseEmbedding []float32, energy, valence, tempo, texture float32) ([]float32, error) {
	// TODO: Replace with actual gRPC call
	// For now, apply simple linear adjustment to embedding

	refined := make([]float32, len(baseEmbedding))
	copy(refined, baseEmbedding)

	// Simple mood-based adjustment (placeholder)
	for i := range refined {
		adjustment := (energy + valence + tempo + texture) / 4.0 * 0.1
		refined[i] = refined[i] * (1.0 + adjustment)
	}

	return refined, nil
}

func (c *MLClient) Ping(ctx context.Context) error {
	if c.conn == nil {
		return fmt.Errorf("ML client not connected")
	}
	return nil
}

func (c *MLClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}
