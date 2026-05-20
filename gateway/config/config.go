package config

import (
	"os"
	"strings"
)

// Config 网关运行时配置.
//
// 安全相关默认值遵循 "最小暴露面" 原则:
//   - BindAddr 默认 127.0.0.1:8080, 禁止 0.0.0.0;
//   - AllowedOrigins 默认仅本机前端, 禁止 "*";
//   - IPAllowlist 默认空, 配合中间件仅放行本地回环;
//   - 跨主机访问需在 IP_ALLOWLIST / CORS_ALLOWED_ORIGINS 中显式声明.
type Config struct {
	BindAddr        string
	JWTSecret       string
	AgentServiceURL string
	AllowedOrigins  []string
	IPAllowlistRaw  string
	TrustProxy      bool
}

func Load() *Config {
	bind := getEnv("BIND_ADDR", "")
	if bind == "" {
		host := getEnv("HOST", "127.0.0.1")
		port := getEnv("PORT", "8080")
		bind = host + ":" + port
	}

	return &Config{
		BindAddr:        bind,
		JWTSecret:       getEnv("JWT_SECRET", "dev-secret-change-in-prod"),
		AgentServiceURL: getEnv("AGENT_SERVICE_URL", "http://127.0.0.1:8000"),
		AllowedOrigins:  splitCSV(getEnv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")),
		IPAllowlistRaw:  os.Getenv("IP_ALLOWLIST"),
		TrustProxy: strings.EqualFold(os.Getenv("TRUST_PROXY"), "true") ||
			os.Getenv("TRUST_PROXY") == "1",
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func splitCSV(raw string) []string {
	if raw == "" {
		return nil
	}
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		if p = strings.TrimSpace(p); p != "" {
			out = append(out, p)
		}
	}
	return out
}
