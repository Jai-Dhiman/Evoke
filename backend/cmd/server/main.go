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
)

func main() {
	cfg := config.Load()

	// Initialize Redis cache
	cache, err := services.NewCacheService(cfg.RedisAddr(), cfg.RedisPassword, cfg.SessionTTL)
	if err != nil {
		log.Printf("Warning: Failed to connect to Redis: %v", err)
		log.Printf("Continuing without Redis (some features may not work)")
	}

	// Initialize Milvus
	milvus, err := services.NewMilvusService(cfg.MilvusAddr())
	if err != nil {
		log.Printf("Warning: Failed to connect to Milvus: %v", err)
		log.Printf("Continuing without Milvus (search will not work)")
	} else {
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		if err := milvus.EnsureCollection(ctx); err != nil {
			log.Printf("Warning: Failed to ensure Milvus collection: %v", err)
		}
		cancel()
	}

	// Initialize ML client
	ml, err := services.NewMLClient(cfg.MLServiceAddr())
	if err != nil {
		log.Printf("Warning: Failed to connect to ML service: %v", err)
		log.Printf("Continuing without ML service (analysis will not work)")
	}

	// Create router
	router := api.NewRouter(cache, milvus, ml)

	// Create server
	srv := &http.Server{
		Addr:         ":" + cfg.ServerPort,
		Handler:      router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
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
	if milvus != nil {
		milvus.Close()
	}
	if ml != nil {
		ml.Close()
	}

	log.Println("Server exited")
}
