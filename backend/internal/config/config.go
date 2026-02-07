package config

import (
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	AppEnv         string
	ServerPort     string
	RedisHost      string
	RedisPort      string
	RedisPassword  string
	RedisURL       string
	MLServiceHost  string
	MLServicePort  string
	MLServiceTLS   bool
	AllowedOrigins []string
	SessionTTL     time.Duration
}

func Load() *Config {
	ttlHours, _ := strconv.Atoi(getEnv("SESSION_TTL_HOURS", "1"))

	// Cloud Run sets PORT; fall back to BACKEND_PORT, then 8080
	port := getEnv("PORT", "")
	if port == "" {
		port = getEnv("BACKEND_PORT", "8080")
	}

	// Parse allowed origins from comma-separated env var
	originsStr := getEnv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
	origins := strings.Split(originsStr, ",")
	for i := range origins {
		origins[i] = strings.TrimSpace(origins[i])
	}

	return &Config{
		AppEnv:         getEnv("APP_ENV", "development"),
		ServerPort:     port,
		RedisHost:      getEnv("REDIS_HOST", "localhost"),
		RedisPort:      getEnv("REDIS_PORT", "6379"),
		RedisPassword:  getEnv("REDIS_PASSWORD", ""),
		RedisURL:       getEnv("REDIS_URL", ""),
		MLServiceHost:  getEnv("ML_SERVICE_HOST", "localhost"),
		MLServicePort:  getEnv("ML_SERVICE_PORT", "50051"),
		MLServiceTLS:   getEnv("ML_SERVICE_TLS", "false") == "true",
		AllowedOrigins: origins,
		SessionTTL:     time.Duration(ttlHours) * time.Hour,
	}
}

func (c *Config) RedisAddr() string {
	return c.RedisHost + ":" + c.RedisPort
}

func (c *Config) MLServiceAddr() string {
	return c.MLServiceHost + ":" + c.MLServicePort
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
