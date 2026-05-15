package handlers

import (
	"fmt"
	"io"
	"net/http"

	"github.com/gin-gonic/gin"
)

type ProxyHandler struct {
	agentServiceURL string
}

func NewProxyHandler(agentURL string) *ProxyHandler {
	return &ProxyHandler{agentServiceURL: agentURL}
}

// ProxyToAgent forwards requests to the Python agent service
func (h *ProxyHandler) ProxyToAgent(c *gin.Context) {
	targetURL := fmt.Sprintf("%s%s", h.agentServiceURL, c.Request.URL.Path)

	req, err := http.NewRequestWithContext(c.Request.Context(), c.Request.Method, targetURL, c.Request.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"code": "PROXY_ERROR", "message": err.Error()})
		return
	}

	// Forward headers
	for key, values := range c.Request.Header {
		for _, v := range values {
			req.Header.Add(key, v)
		}
	}

	// Inject user context from JWT
	req.Header.Set("X-User-ID", c.GetString("user_id"))
	req.Header.Set("X-Workspace-ID", c.GetString("workspace_id"))

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"code": "AGENT_UNAVAILABLE", "message": err.Error()})
		return
	}
	defer resp.Body.Close()

	// Forward response
	for key, values := range resp.Header {
		for _, v := range values {
			c.Header(key, v)
		}
	}
	c.Status(resp.StatusCode)
	io.Copy(c.Writer, resp.Body)
}
