package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/evoke/backend/internal/services"
	"github.com/evoke/backend/internal/vectorstore"
)

type BoardHandler struct {
	cache *services.CacheService
	vs    *vectorstore.VectorStore
}

func NewBoardHandler(cache *services.CacheService, vs *vectorstore.VectorStore) *BoardHandler {
	return &BoardHandler{
		cache: cache,
		vs:    vs,
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
	SessionID   string                    `json:"session_id"`
	MoodEnergy  float32                   `json:"mood_energy"`
	MoodValence float32                   `json:"mood_valence"`
	MoodTempo   float32                   `json:"mood_tempo"`
	MoodTexture float32                   `json:"mood_texture"`
	Images      []vectorstore.ImageResult `json:"images"`
}

type RefineRequest struct {
	SessionID string  `json:"session_id" binding:"required"`
	Energy    float32 `json:"energy"`
	Valence   float32 `json:"valence"`
	Tempo     float32 `json:"tempo"`
	Texture   float32 `json:"texture"`
}

func (h *BoardHandler) GetBoard(c *gin.Context) {
	if h.cache == nil || h.vs == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "required services unavailable"})
		return
	}

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
	images := h.vs.Search(session.Embedding, 20)

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
	if h.cache == nil || h.vs == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "required services unavailable"})
		return
	}

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

	// Refine embedding locally using vectorstore direction vectors
	refinedEmbedding := h.vs.RefineEmbedding(
		session.Embedding,
		req.Energy,
		req.Valence,
		req.Tempo,
		req.Texture,
	)

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
	images := h.vs.Search(refinedEmbedding, 20)

	c.JSON(http.StatusOK, BoardResponse{
		SessionID:   session.SessionID,
		MoodEnergy:  session.MoodEnergy,
		MoodValence: session.MoodValence,
		MoodTempo:   session.MoodTempo,
		MoodTexture: session.MoodTexture,
		Images:      images,
	})
}
