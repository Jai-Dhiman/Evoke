package handlers

import (
	"io"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"github.com/evoke/backend/internal/services"
)

type AudioHandler struct {
	cache  *services.CacheService
	milvus *services.MilvusService
	ml     *services.MLClient
}

func NewAudioHandler(cache *services.CacheService, milvus *services.MilvusService, ml *services.MLClient) *AudioHandler {
	return &AudioHandler{
		cache:  cache,
		milvus: milvus,
		ml:     ml,
	}
}

type CreateSessionResponse struct {
	SessionID string `json:"session_id"`
}

type AnalyzeRequest struct {
	SessionID string `form:"session_id" binding:"required"`
}

type AnalyzeResponse struct {
	SessionID   string                  `json:"session_id"`
	MoodEnergy  float32                 `json:"mood_energy"`
	MoodValence float32                 `json:"mood_valence"`
	MoodTempo   float32                 `json:"mood_tempo"`
	MoodTexture float32                 `json:"mood_texture"`
	Images      []services.ImageResult  `json:"images"`
}

func (h *AudioHandler) CreateSession(c *gin.Context) {
	if h.cache == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "cache service unavailable"})
		return
	}

	sessionID := uuid.New().String()

	session := &services.SessionData{
		SessionID:   sessionID,
		MoodEnergy:  0.5,
		MoodValence: 0.5,
		MoodTempo:   0.5,
		MoodTexture: 0.5,
		CreatedAt:   time.Now(),
	}

	if err := h.cache.SaveSession(c.Request.Context(), session); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create session"})
		return
	}

	c.JSON(http.StatusOK, CreateSessionResponse{SessionID: sessionID})
}

func (h *AudioHandler) Analyze(c *gin.Context) {
	if h.cache == nil || h.ml == nil || h.milvus == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "required services unavailable"})
		return
	}

	var req AnalyzeRequest
	if err := c.ShouldBind(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "session_id is required"})
		return
	}

	// Get the uploaded audio file
	file, _, err := c.Request.FormFile("audio")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "audio file is required"})
		return
	}
	defer file.Close()

	audioData, err := io.ReadAll(file)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to read audio file"})
		return
	}

	// Get existing session
	session, err := h.cache.GetSession(c.Request.Context(), req.SessionID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "session not found"})
		return
	}

	// Analyze audio with ML service
	result, err := h.ml.AnalyzeAudio(c.Request.Context(), audioData)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to analyze audio"})
		return
	}

	// Update session with analysis results
	session.Embedding = result.Embedding
	session.MoodEnergy = result.MoodEnergy
	session.MoodValence = result.MoodValence
	session.MoodTempo = result.MoodTempo
	session.MoodTexture = result.MoodTexture

	if err := h.cache.SaveSession(c.Request.Context(), session); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save session"})
		return
	}

	// Search for similar images
	images, err := h.milvus.Search(c.Request.Context(), result.Embedding, 20)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to search images"})
		return
	}

	c.JSON(http.StatusOK, AnalyzeResponse{
		SessionID:   session.SessionID,
		MoodEnergy:  session.MoodEnergy,
		MoodValence: session.MoodValence,
		MoodTempo:   session.MoodTempo,
		MoodTexture: session.MoodTexture,
		Images:      images,
	})
}
