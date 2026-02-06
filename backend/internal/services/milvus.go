package services

import (
	"context"
	"fmt"

	"github.com/milvus-io/milvus-sdk-go/v2/client"
	"github.com/milvus-io/milvus-sdk-go/v2/entity"
)

const (
	CollectionName = "image_embeddings"
	EmbeddingDim   = 512
	MetricType     = entity.L2
	IndexType      = entity.IvfFlat
	NList          = 128
	TopK           = 20
)

type MilvusService struct {
	client client.Client
}

type ImageResult struct {
	ID       int64   `json:"id"`
	ImageURL string  `json:"image_url"`
	Score    float32 `json:"score"`
}

func NewMilvusService(addr string) (*MilvusService, error) {
	ctx := context.Background()

	c, err := client.NewClient(ctx, client.Config{
		Address: addr,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Milvus: %w", err)
	}

	return &MilvusService{client: c}, nil
}

func (m *MilvusService) EnsureCollection(ctx context.Context) error {
	exists, err := m.client.HasCollection(ctx, CollectionName)
	if err != nil {
		return fmt.Errorf("failed to check collection: %w", err)
	}

	if exists {
		return nil
	}

	schema := &entity.Schema{
		CollectionName: CollectionName,
		Description:    "Image embeddings for visual search",
		AutoID:         true,
		Fields: []*entity.Field{
			{
				Name:       "id",
				DataType:   entity.FieldTypeInt64,
				PrimaryKey: true,
				AutoID:     true,
			},
			{
				Name:     "image_url",
				DataType: entity.FieldTypeVarChar,
				TypeParams: map[string]string{
					"max_length": "512",
				},
			},
			{
				Name:     "embedding",
				DataType: entity.FieldTypeFloatVector,
				TypeParams: map[string]string{
					"dim": fmt.Sprintf("%d", EmbeddingDim),
				},
			},
		},
	}

	if err := m.client.CreateCollection(ctx, schema, 2); err != nil {
		return fmt.Errorf("failed to create collection: %w", err)
	}

	idx, err := entity.NewIndexIvfFlat(MetricType, NList)
	if err != nil {
		return fmt.Errorf("failed to create index params: %w", err)
	}

	if err := m.client.CreateIndex(ctx, CollectionName, "embedding", idx, false); err != nil {
		return fmt.Errorf("failed to create index: %w", err)
	}

	if err := m.client.LoadCollection(ctx, CollectionName, false); err != nil {
		return fmt.Errorf("failed to load collection: %w", err)
	}

	return nil
}

func (m *MilvusService) Search(ctx context.Context, embedding []float32, topK int) ([]ImageResult, error) {
	if topK <= 0 {
		topK = TopK
	}

	sp, err := entity.NewIndexIvfFlatSearchParam(16)
	if err != nil {
		return nil, fmt.Errorf("failed to create search params: %w", err)
	}

	vectors := []entity.Vector{entity.FloatVector(embedding)}

	results, err := m.client.Search(
		ctx,
		CollectionName,
		nil,
		"",
		[]string{"image_url"},
		vectors,
		"embedding",
		MetricType,
		topK,
		sp,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to search: %w", err)
	}

	var images []ImageResult
	for _, result := range results {
		for i := 0; i < result.ResultCount; i++ {
			var imageURL string
			urlField := result.Fields.GetColumn("image_url")
			if urlField != nil {
				if val, err := urlField.GetAsString(i); err == nil {
					imageURL = val
				}
			}

			images = append(images, ImageResult{
				ID:       result.IDs.(*entity.ColumnInt64).Data()[i],
				ImageURL: imageURL,
				Score:    result.Scores[i],
			})
		}
	}

	return images, nil
}

func (m *MilvusService) Insert(ctx context.Context, imageURLs []string, embeddings [][]float32) error {
	urlColumn := entity.NewColumnVarChar("image_url", imageURLs)

	embeddingData := make([][]float32, len(embeddings))
	copy(embeddingData, embeddings)
	embeddingColumn := entity.NewColumnFloatVector("embedding", EmbeddingDim, embeddingData)

	_, err := m.client.Insert(ctx, CollectionName, "", urlColumn, embeddingColumn)
	if err != nil {
		return fmt.Errorf("failed to insert: %w", err)
	}

	return nil
}

func (m *MilvusService) Ping(ctx context.Context) error {
	_, err := m.client.HasCollection(ctx, CollectionName)
	return err
}

func (m *MilvusService) Close() error {
	return m.client.Close()
}
