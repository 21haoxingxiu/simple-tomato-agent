package config

import "os"

type Config struct {
	Port           string
	JWTSecret      string
	AgentServiceURL string
}

func Load() *Config {
	return &Config{
		Port:           getEnv("PORT", "8080"),
		JWTSecret:      getEnv("JWT_SECRET", "dev-secret-change-in-prod"),
		AgentServiceURL: getEnv("AGENT_SERVICE_URL", "http://localhost:8000"),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
