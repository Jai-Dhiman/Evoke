package services

import (
	"context"
	"crypto/tls"
	"fmt"
	"time"

	"github.com/evoke/backend/proto"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
)

type MLClient struct {
	conn   *grpc.ClientConn
	client proto.MLServiceClient
	addr   string
}

type AnalysisResult struct {
	Embedding   []float32 `json:"embedding"`
	MoodEnergy  float32   `json:"mood_energy"`
	MoodValence float32   `json:"mood_valence"`
	MoodTempo   float32   `json:"mood_tempo"`
	MoodTexture float32   `json:"mood_texture"`
}

func NewMLClient(addr string, useTLS bool) (*MLClient, error) {
	var creds grpc.DialOption
	if useTLS {
		creds = grpc.WithTransportCredentials(credentials.NewTLS(&tls.Config{}))
	} else {
		creds = grpc.WithTransportCredentials(insecure.NewCredentials())
	}

	conn, err := grpc.NewClient(addr, creds)
	if err != nil {
		return nil, fmt.Errorf("failed to create ML client: %w", err)
	}

	client := proto.NewMLServiceClient(conn)

	return &MLClient{
		conn:   conn,
		client: client,
		addr:   addr,
	}, nil
}

func (c *MLClient) AnalyzeAudio(ctx context.Context, audioData []byte) (*AnalysisResult, error) {
	ctx, cancel := context.WithTimeout(ctx, 120*time.Second)
	defer cancel()

	req := &proto.AnalyzeAudioRequest{
		AudioData: audioData,
		Format:    "auto",
	}

	resp, err := c.client.AnalyzeAudio(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to analyze audio: %w", err)
	}

	return &AnalysisResult{
		Embedding:   resp.Embedding,
		MoodEnergy:  resp.MoodEnergy,
		MoodValence: resp.MoodValence,
		MoodTempo:   resp.MoodTempo,
		MoodTexture: resp.MoodTexture,
	}, nil
}

func (c *MLClient) RefineEmbedding(ctx context.Context, baseEmbedding []float32, energy, valence, tempo, texture float32) ([]float32, error) {
	req := &proto.RefineEmbeddingRequest{
		BaseEmbedding: baseEmbedding,
		Energy:        energy,
		Valence:       valence,
		Tempo:         tempo,
		Texture:       texture,
	}

	resp, err := c.client.RefineEmbedding(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to refine embedding: %w", err)
	}

	return resp.Embedding, nil
}

func (c *MLClient) Ping(ctx context.Context) error {
	if c.conn == nil {
		return fmt.Errorf("ML client not connected")
	}

	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	resp, err := c.client.HealthCheck(ctx, &proto.HealthCheckRequest{})
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	if !resp.Healthy {
		return fmt.Errorf("ML service unhealthy: %s", resp.Message)
	}

	return nil
}

func (c *MLClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}
