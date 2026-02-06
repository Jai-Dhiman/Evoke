package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/evoke/backend/internal/services"
)

type BoardHandler struct {
	cache  *services.CacheService
	milvus *services.MilvusService
	ml     *services.MLClient
}

func NewBoardHandler(cache *services.CacheService, milvus *services.MilvusService, ml *services.MLClient) *BoardHandler {
	return &BoardHandler{
		cache:  cache,
		milvus: milvus,
		ml:     ml,
	}
}

type GetBoardRequest struct {
	SessionID string  `form:"session_id" binding:"required"`
	Energy    float32 `form:"energy"`
	Valence   float32 `form:"valence"`
	Tempo     float32 `form:"tempo"`
	Texture   float32 `form:"texture"`
}

type BoardResponse struct {
	SessionID   string                 `json:"session_id"`
	MoodEnergy  float32                `json:"mood_energy"`
	MoodValence float32                `json:"mood_valence"`
	MoodTempo   float32                `json:"mood_tempo"`
	MoodTexture float32                `json:"mood_texture"`
	Images      []services.ImageResult `json:"images"`
}

type RefineRequest struct {
	SessionID string  `json:"session_id" binding:"required"`
	Energy    float32 `json:"energy"`
	Valence   float32 `json:"valence"`
	Tempo     float32 `json:"tempo"`
	Texture   float32 `json:"texture"`
}

func (h *BoardHandler) GetBoard(c *gin.Context) {
	var req GetBoardRequest
	if err := c.ShouldBindQuery(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "session_id is required"})
		return
	}

	session, err := h.cache.GetSession(c.Request.Context(), req.SessionID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "session not found"})
		return
	}

	if len(session.Embedding) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "no audio analyzed for this session"})
		return
	}

	// Search for images using current embedding
	images, err := h.milvus.Search(c.Request.Context(), session.Embedding, 20)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to search images"})
		return
	}

	c.JSON(http.StatusOK, BoardResponse{
		SessionID:   session.SessionID,
		MoodEnergy:  session.MoodEnergy,
		MoodValence: session.MoodValence,
		MoodTempo:   session.MoodTempo,
		MoodTexture: session.MoodTexture,
		Images:      images,
	})
}

func (h *BoardHandler) Refine(c *gin.Context) {
	var req RefineRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request body"})
		return
	}

	session, err := h.cache.GetSession(c.Request.Context(), req.SessionID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "session not found"})
		return
	}

	if len(session.Embedding) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "no audio analyzed for this session"})
		return
	}

	// Refine embedding based on slider values
	refinedEmbedding, err := h.ml.RefineEmbedding(
		c.Request.Context(),
		session.Embedding,
		req.Energy,
		req.Valence,
		req.Tempo,
		req.Texture,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to refine embedding"})
		return
	}

	// Update session with new slider values
	session.MoodEnergy = req.Energy
	session.MoodValence = req.Valence
	session.MoodTempo = req.Tempo
	session.MoodTexture = req.Texture

	if err := h.cache.SaveSession(c.Request.Context(), session); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to save session"})
		return
	}

	// Search for images with refined embedding
	images, err := h.milvus.Search(c.Request.Context(), refinedEmbedding, 20)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to search images"})
		return
	}

	c.JSON(http.StatusOK, BoardResponse{
		SessionID:   session.SessionID,
		MoodEnergy:  session.MoodEnergy,
		MoodValence: session.MoodValence,
		MoodTempo:   session.MoodTempo,
		MoodTexture: session.MoodTexture,
		Images:      images,
	})
}
