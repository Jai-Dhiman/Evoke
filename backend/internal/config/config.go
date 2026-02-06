package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	AppEnv         string
	ServerPort     string
	RedisHost      string
	RedisPort      string
	RedisPassword  string
	MilvusHost     string
	MilvusPort     string
	MLServiceHost  string
	MLServicePort  string
	SessionTTL     time.Duration
}

func Load() *Config {
	ttlHours, _ := strconv.Atoi(getEnv("SESSION_TTL_HOURS", "1"))

	return &Config{
		AppEnv:         getEnv("APP_ENV", "development"),
		ServerPort:     getEnv("BACKEND_PORT", "8080"),
		RedisHost:      getEnv("REDIS_HOST", "localhost"),
		RedisPort:      getEnv("REDIS_PORT", "6379"),
		RedisPassword:  getEnv("REDIS_PASSWORD", ""),
		MilvusHost:     getEnv("MILVUS_HOST", "localhost"),
		MilvusPort:     getEnv("MILVUS_PORT", "19530"),
		MLServiceHost:  getEnv("ML_SERVICE_HOST", "localhost"),
		MLServicePort:  getEnv("ML_SERVICE_PORT", "50051"),
		SessionTTL:     time.Duration(ttlHours) * time.Hour,
	}
}

func (c *Config) RedisAddr() string {
	return c.RedisHost + ":" + c.RedisPort
}

func (c *Config) MilvusAddr() string {
	return c.MilvusHost + ":" + c.MilvusPort
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
