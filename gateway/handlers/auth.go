package handlers

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"

	"github.com/ai-demo/gateway/middleware"
)

type AuthHandler struct {
	jwtSecret string
}

func NewAuthHandler(secret string) *AuthHandler {
	return &AuthHandler{jwtSecret: secret}
}

type LoginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required,min=6"`
}

// Login creates a JWT for demo purposes (no real DB check)
func (h *AuthHandler) Login(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"code": "VALIDATION_ERROR", "message": err.Error()})
		return
	}

	// Demo: accept any email/password combination
	claims := &middleware.Claims{
		UserID:      "user-demo-001",
		WorkspaceID: "ws-1",
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Subject:   req.Email,
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, err := token.SignedString([]byte(h.jwtSecret))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"code": "TOKEN_SIGN_ERROR"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"token":   signed,
		"user_id": claims.UserID,
		"email":   req.Email,
	})
}

func (h *AuthHandler) Me(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"user_id":      c.GetString("user_id"),
		"workspace_id": c.GetString("workspace_id"),
	})
}
