package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/evoke/backend/internal/api"
	"github.com/evoke/backend/internal/config"
	"github.com/evoke/backend/internal/services"
	"github.com/evoke/backend/internal/vectorstore"
)

func main() {
	cfg := config.Load()

	// Initialize VectorStore (embedded data, must succeed)
	vs, err := vectorstore.New()
	if err != nil {
		log.Fatalf("Failed to load vector store: %v", err)
	}
	log.Printf("VectorStore loaded: %d images", vs.ImageCount())

	// Initialize Redis cache
	var cache *services.CacheService
	if cfg.RedisURL != "" {
		cache, err = services.NewCacheServiceFromURL(cfg.RedisURL, cfg.SessionTTL)
	} else {
		cache, err = services.NewCacheService(cfg.RedisAddr(), cfg.RedisPassword, cfg.SessionTTL)
	}
	if err != nil {
		log.Printf("Warning: Failed to connect to Redis: %v", err)
		log.Printf("Continuing without Redis (some features may not work)")
	}

	// Initialize ML client (non-blocking, lazy connection)
	ml, err := services.NewMLClient(cfg.MLServiceAddr(), cfg.MLServiceTLS)
	if err != nil {
		log.Printf("Warning: Failed to create ML client: %v", err)
		log.Printf("Continuing without ML service (analysis will not work)")
	}

	// Create router
	router := api.NewRouter(cache, vs, ml, cfg.AllowedOrigins)

	// Create server
	srv := &http.Server{
		Addr:         ":" + cfg.ServerPort,
		Handler:      router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 120 * time.Second,
	}

	// Start server in goroutine
	go func() {
		log.Printf("Starting server on port %s", cfg.ServerPort)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")

	// Graceful shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Printf("Server forced to shutdown: %v", err)
	}

	// Cleanup connections
	if cache != nil {
		cache.Close()
	}
	if ml != nil {
		ml.Close()
	}

	log.Println("Server exited")
}
