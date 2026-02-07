package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

type CacheService struct {
	client *redis.Client
	ttl    time.Duration
}

type SessionData struct {
	SessionID    string    `json:"session_id"`
	AudioPath    string    `json:"audio_path"`
	Embedding    []float32 `json:"embedding"`
	MoodEnergy   float32   `json:"mood_energy"`
	MoodValence  float32   `json:"mood_valence"`
	MoodTempo    float32   `json:"mood_tempo"`
	MoodTexture  float32   `json:"mood_texture"`
	CreatedAt    time.Time `json:"created_at"`
}

func NewCacheService(addr, password string, ttl time.Duration) (*CacheService, error) {
	client := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: password,
		DB:       0,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	return &CacheService{
		client: client,
		ttl:    ttl,
	}, nil
}

func NewCacheServiceFromURL(redisURL string, ttl time.Duration) (*CacheService, error) {
	opts, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse Redis URL: %w", err)
	}

	client := redis.NewClient(opts)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	return &CacheService{
		client: client,
		ttl:    ttl,
	}, nil
}

func (c *CacheService) SaveSession(ctx context.Context, session *SessionData) error {
	data, err := json.Marshal(session)
	if err != nil {
		return fmt.Errorf("failed to marshal session: %w", err)
	}

	key := fmt.Sprintf("session:%s", session.SessionID)
	return c.client.Set(ctx, key, data, c.ttl).Err()
}

func (c *CacheService) GetSession(ctx context.Context, sessionID string) (*SessionData, error) {
	key := fmt.Sprintf("session:%s", sessionID)
	data, err := c.client.Get(ctx, key).Bytes()
	if err != nil {
		if err == redis.Nil {
			return nil, fmt.Errorf("session not found: %s", sessionID)
		}
		return nil, fmt.Errorf("failed to get session: %w", err)
	}

	var session SessionData
	if err := json.Unmarshal(data, &session); err != nil {
		return nil, fmt.Errorf("failed to unmarshal session: %w", err)
	}

	return &session, nil
}

func (c *CacheService) UpdateMoodSliders(ctx context.Context, sessionID string, energy, valence, tempo, texture float32) error {
	session, err := c.GetSession(ctx, sessionID)
	if err != nil {
		return err
	}

	session.MoodEnergy = energy
	session.MoodValence = valence
	session.MoodTempo = tempo
	session.MoodTexture = texture

	return c.SaveSession(ctx, session)
}

func (c *CacheService) DeleteSession(ctx context.Context, sessionID string) error {
	key := fmt.Sprintf("session:%s", sessionID)
	return c.client.Del(ctx, key).Err()
}

func (c *CacheService) Ping(ctx context.Context) error {
	return c.client.Ping(ctx).Err()
}

func (c *CacheService) Close() error {
	return c.client.Close()
}
