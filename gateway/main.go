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

	// CORS
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:3000"},
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Authorization"},
		AllowCredentials: true,
	}))

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok", "service": "gateway"})
	})

	// Auth routes (public)
	authHandler := handlers.NewAuthHandler(cfg.JWTSecret)
	auth := r.Group("/api/auth")
	{
		auth.POST("/login", authHandler.Login)
	}

	// Protected routes
	proxyHandler := handlers.NewProxyHandler(cfg.AgentServiceURL)
	api := r.Group("/api")
	api.Use(middleware.Auth(cfg.JWTSecret))
	{
		api.GET("/me", authHandler.Me)

		// Proxy to Python agent service
		api.Any("/agent/*path", proxyHandler.ProxyToAgent)
		api.Any("/chat/*path", proxyHandler.ProxyToAgent)
		api.Any("/knowledge/*path", proxyHandler.ProxyToAgent)
	}

	log.Printf("Gateway listening on :%s", cfg.Port)
	if err := r.Run(":" + cfg.Port); err != nil {
		log.Fatal(err)
	}
}
