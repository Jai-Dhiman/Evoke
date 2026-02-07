package handlers

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/evoke/backend/internal/services"
	"github.com/evoke/backend/internal/vectorstore"
)

type HealthHandler struct {
	cache *services.CacheService
	vs    *vectorstore.VectorStore
	ml    *services.MLClient
}

func NewHealthHandler(cache *services.CacheService, vs *vectorstore.VectorStore, ml *services.MLClient) *HealthHandler {
	return &HealthHandler{
		cache: cache,
		vs:    vs,
		ml:    ml,
	}
}

type HealthStatus struct {
	Status   string            `json:"status"`
	Services map[string]string `json:"services"`
}

func (h *HealthHandler) Health(c *gin.Context) {
	ctx, cancel := context.WithTimeout(c.Request.Context(), 5*time.Second)
	defer cancel()

	status := HealthStatus{
		Status:   "ok",
		Services: make(map[string]string),
	}

	// Check Redis
	if h.cache == nil {
		status.Services["redis"] = "error: not connected"
		status.Status = "degraded"
	} else if err := h.cache.Ping(ctx); err != nil {
		status.Services["redis"] = "error: " + err.Error()
		status.Status = "degraded"
	} else {
		status.Services["redis"] = "ok"
	}

	// Check VectorStore (always passes since data is embedded)
	if h.vs == nil {
		status.Services["vectorstore"] = "error: not loaded"
		status.Status = "degraded"
	} else {
		status.Services["vectorstore"] = fmt.Sprintf("ok (%d images)", h.vs.ImageCount())
	}

	// Check ML Service
	if h.ml == nil {
		status.Services["ml"] = "not configured"
	} else if err := h.ml.Ping(ctx); err != nil {
		status.Services["ml"] = "cold (will start on demand)"
	} else {
		status.Services["ml"] = "ok"
	}

	statusCode := http.StatusOK
	if status.Status != "ok" {
		statusCode = http.StatusServiceUnavailable
	}

	c.JSON(statusCode, status)
}
