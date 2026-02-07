package api

import (
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"

	"github.com/evoke/backend/internal/api/handlers"
	"github.com/evoke/backend/internal/services"
	"github.com/evoke/backend/internal/vectorstore"
)

func NewRouter(cache *services.CacheService, vs *vectorstore.VectorStore, ml *services.MLClient, allowedOrigins []string) *gin.Engine {
	router := gin.Default()

	// CORS configuration
	config := cors.DefaultConfig()
	config.AllowOrigins = allowedOrigins
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Accept", "Authorization"}
	router.Use(cors.New(config))

	// Initialize handlers
	healthHandler := handlers.NewHealthHandler(cache, vs, ml)
	audioHandler := handlers.NewAudioHandler(cache, vs, ml)
	boardHandler := handlers.NewBoardHandler(cache, vs)
	demoHandler := handlers.NewDemoHandler(vs, cache, ml)

	// Health check
	router.GET("/health", healthHandler.Health)

	// API routes
	api := router.Group("/api")
	{
		// Session management
		api.POST("/sessions", audioHandler.CreateSession)

		// Audio analysis
		api.POST("/analyze", audioHandler.Analyze)

		// Demo
		api.POST("/demo", demoHandler.Demo)

		// Board operations
		api.GET("/board", boardHandler.GetBoard)
		api.POST("/refine", boardHandler.Refine)
	}

	return router
}
