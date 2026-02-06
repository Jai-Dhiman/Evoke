package api

import (
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"

	"github.com/evoke/backend/internal/api/handlers"
	"github.com/evoke/backend/internal/services"
)

func NewRouter(cache *services.CacheService, milvus *services.MilvusService, ml *services.MLClient) *gin.Engine {
	router := gin.Default()

	// CORS configuration
	config := cors.DefaultConfig()
	config.AllowOrigins = []string{"http://localhost:3000", "http://localhost:5173"}
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Accept", "Authorization"}
	router.Use(cors.New(config))

	// Initialize handlers
	healthHandler := handlers.NewHealthHandler(cache, milvus, ml)
	audioHandler := handlers.NewAudioHandler(cache, milvus, ml)
	boardHandler := handlers.NewBoardHandler(cache, milvus, ml)

	// Health check
	router.GET("/health", healthHandler.Health)

	// API routes
	api := router.Group("/api")
	{
		// Session management
		api.POST("/sessions", audioHandler.CreateSession)

		// Audio analysis
		api.POST("/analyze", audioHandler.Analyze)

		// Board operations
		api.GET("/board", boardHandler.GetBoard)
		api.POST("/refine", boardHandler.Refine)
	}

	return router
}
