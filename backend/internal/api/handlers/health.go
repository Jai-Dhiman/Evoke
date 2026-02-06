package handlers

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/evoke/backend/internal/services"
)

type HealthHandler struct {
	cache  *services.CacheService
	milvus *services.MilvusService
	ml     *services.MLClient
}

func NewHealthHandler(cache *services.CacheService, milvus *services.MilvusService, ml *services.MLClient) *HealthHandler {
	return &HealthHandler{
		cache:  cache,
		milvus: milvus,
		ml:     ml,
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
	if err := h.cache.Ping(ctx); err != nil {
		status.Services["redis"] = "error: " + err.Error()
		status.Status = "degraded"
	} else {
		status.Services["redis"] = "ok"
	}

	// Check Milvus
	if err := h.milvus.Ping(ctx); err != nil {
		status.Services["milvus"] = "error: " + err.Error()
		status.Status = "degraded"
	} else {
		status.Services["milvus"] = "ok"
	}

	// Check ML Service
	if err := h.ml.Ping(ctx); err != nil {
		status.Services["ml"] = "error: " + err.Error()
		status.Status = "degraded"
	} else {
		status.Services["ml"] = "ok"
	}

	statusCode := http.StatusOK
	if status.Status != "ok" {
		statusCode = http.StatusServiceUnavailable
	}

	c.JSON(statusCode, status)
}
