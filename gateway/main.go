package main

import (
	"log"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"

	"github.com/ai-demo/gateway/config"
	"github.com/ai-demo/gateway/handlers"
	"github.com/ai-demo/gateway/middleware"
)

func main() {
	cfg := config.Load()

	r := gin.Default()

	// ---- 安全中间件 (最外层, 优先于业务) -----------------------------------
	// IP 白名单: 默认仅本地回环, IP_ALLOWLIST 环境变量声明跨主机授信网段.
	r.Use(middleware.IPAllowlist(
		middleware.ParseAllowlist(cfg.IPAllowlistRaw),
		cfg.TrustProxy,
		"/health",
	))

	// CORS: 显式来源白名单, 严禁通配符 "*".
	r.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.AllowedOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization", "X-Workspace-ID", "X-User-ID", "Accept"},
		ExposeHeaders:    []string{"Content-Type", "Content-Disposition"},
		AllowCredentials: true,
		MaxAge:           86400,
	}))
	// ----------------------------------------------------------------------

	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok", "service": "gateway"})
	})

	proxyHandler := handlers.NewProxyHandler(cfg.AgentServiceURL)

	r.Any("/api/auth/*path", proxyHandler.ProxyToAgent)

	api := r.Group("/api")
	api.Use(middleware.Auth(cfg.JWTSecret))
	{
		api.GET("/me", proxyHandler.ProxyToAgentRewrite("/auth/me"))

		api.POST("/chat/stream", proxyHandler.ProxyStream)
		api.POST("/chat/completions", proxyHandler.ProxyToAgent)
		api.GET("/chat/conversations", proxyHandler.ProxyToAgent)
		api.GET("/chat/conversations/:id/messages", proxyHandler.ProxyToAgent)
		api.DELETE("/chat/conversations/:id", proxyHandler.ProxyToAgent)

		api.Any("/knowledge/*path", proxyHandler.ProxyToAgent)
		api.Any("/eval/*path", proxyHandler.ProxyToAgent)
		api.Any("/voice/*path", proxyHandler.ProxyToAgent)
		api.Any("/agent/*path", proxyHandler.ProxyToAgent)
	}

	log.Printf("Gateway listening on %s -> agent=%s (origins=%v, ip_allowlist=%q, trust_proxy=%v)",
		cfg.BindAddr, cfg.AgentServiceURL, cfg.AllowedOrigins, cfg.IPAllowlistRaw, cfg.TrustProxy)
	if err := r.Run(cfg.BindAddr); err != nil {
		log.Fatal(err)
	}
}
