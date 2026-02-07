package handlers

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"github.com/evoke/backend/internal/services"
	"github.com/evoke/backend/internal/vectorstore"
)

type DemoHandler struct {
	vs    *vectorstore.VectorStore
	cache *services.CacheService
	ml    *services.MLClient
}

func NewDemoHandler(vs *vectorstore.VectorStore, cache *services.CacheService, ml *services.MLClient) *DemoHandler {
	return &DemoHandler{
		vs:    vs,
		cache: cache,
		ml:    ml,
	}
}

func (h *DemoHandler) Demo(c *gin.Context) {
	if h.cache == nil || h.vs == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "required services unavailable"})
		return
	}

	demo := h.vs.GetDemo()

	// Create a real session so subsequent /api/refine calls work
	sessionID := uuid.New().String()
	session := &services.SessionData{
		SessionID:   sessionID,
		Embedding:   demo.Embedding,
		MoodEnergy:  demo.MoodEnergy,
		MoodValence: demo.MoodValence,
		MoodTempo:   demo.MoodTempo,
		MoodTexture: demo.MoodTexture,
		CreatedAt:   time.Now(),
	}

	if err := h.cache.SaveSession(c.Request.Context(), session); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create demo session"})
		return
	}

	// Warm up ML service in background (non-blocking)
	if h.ml != nil {
		go func() {
			_ = h.ml.Ping(c.Request.Context())
		}()
	}

	c.JSON(http.StatusOK, AnalyzeResponse{
		SessionID:   sessionID,
		MoodEnergy:  demo.MoodEnergy,
		MoodValence: demo.MoodValence,
		MoodTempo:   demo.MoodTempo,
		MoodTexture: demo.MoodTexture,
		Images:      demo.Images,
	})
}
