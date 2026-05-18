package handlers

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

type ProxyHandler struct {
	agentServiceURL string
	client          *http.Client
	streamClient    *http.Client
}

func NewProxyHandler(agentURL string) *ProxyHandler {
	return &ProxyHandler{
		agentServiceURL: strings.TrimRight(agentURL, "/"),
		client:          &http.Client{Timeout: 60 * time.Second},
		streamClient:    &http.Client{}, // SSE 不超时
	}
}

// ProxyToAgent — 普通 JSON 请求转发(保留原 path,去掉 /api 前缀)
func (h *ProxyHandler) ProxyToAgent(c *gin.Context) {
	h.forwardSync(c, stripAPIPrefix(c.Request.URL.Path))
}

// ProxyToAgentRewrite — 转发到 agent 的固定路径(如 /api/me -> /auth/me)
func (h *ProxyHandler) ProxyToAgentRewrite(targetPath string) gin.HandlerFunc {
	return func(c *gin.Context) {
		h.forwardSync(c, targetPath)
	}
}

// ProxyStream — SSE 流式转发(用于 /api/chat/stream)
func (h *ProxyHandler) ProxyStream(c *gin.Context) {
	h.forwardStream(c, stripAPIPrefix(c.Request.URL.Path))
}

func (h *ProxyHandler) forwardSync(c *gin.Context, agentPath string) {
	targetURL := h.agentServiceURL + agentPath
	if c.Request.URL.RawQuery != "" {
		targetURL = fmt.Sprintf("%s?%s", targetURL, c.Request.URL.RawQuery)
	}

	req, err := http.NewRequestWithContext(c.Request.Context(), c.Request.Method, targetURL, c.Request.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"code": "PROXY_ERROR", "message": err.Error()})
		return
	}
	h.injectHeaders(c, req)

	resp, err := h.client.Do(req)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"code": "AGENT_UNAVAILABLE", "message": err.Error()})
		return
	}
	defer resp.Body.Close()

	for key, values := range resp.Header {
		if isHopOrCORSHeader(key) {
			continue
		}
		for _, v := range values {
			c.Writer.Header().Add(key, v)
		}
	}
	c.Status(resp.StatusCode)
	_, _ = io.Copy(c.Writer, resp.Body)
}

func (h *ProxyHandler) forwardStream(c *gin.Context, agentPath string) {
	targetURL := h.agentServiceURL + agentPath
	if c.Request.URL.RawQuery != "" {
		targetURL = fmt.Sprintf("%s?%s", targetURL, c.Request.URL.RawQuery)
	}

	ctx, cancel := context.WithCancel(c.Request.Context())
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, c.Request.Method, targetURL, c.Request.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"code": "PROXY_ERROR", "message": err.Error()})
		return
	}
	h.injectHeaders(c, req)
	req.Header.Set("Accept", "text/event-stream")

	resp, err := h.streamClient.Do(req)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"code": "AGENT_UNAVAILABLE", "message": err.Error()})
		return
	}
	defer resp.Body.Close()

	c.Writer.Header().Set("Content-Type", "text/event-stream")
	c.Writer.Header().Set("Cache-Control", "no-cache")
	c.Writer.Header().Set("Connection", "keep-alive")
	c.Writer.Header().Set("X-Accel-Buffering", "no")
	c.Status(resp.StatusCode)

	flusher, ok := c.Writer.(http.Flusher)
	if !ok {
		_, _ = io.Copy(c.Writer, resp.Body)
		return
	}

	buf := make([]byte, 4096)
	for {
		n, err := resp.Body.Read(buf)
		if n > 0 {
			if _, werr := c.Writer.Write(buf[:n]); werr != nil {
				return
			}
			flusher.Flush()
		}
		if err != nil {
			return
		}
	}
}

func (h *ProxyHandler) injectHeaders(c *gin.Context, req *http.Request) {
	for key, values := range c.Request.Header {
		if strings.EqualFold(key, "Host") || strings.EqualFold(key, "Connection") {
			continue
		}
		for _, v := range values {
			req.Header.Add(key, v)
		}
	}
	if uid := c.GetString("user_id"); uid != "" {
		req.Header.Set("X-User-ID", uid)
	}
	if ws := workspaceFromCtx(c); ws != "" {
		req.Header.Set("X-Workspace-ID", ws)
	}
}

func workspaceFromCtx(c *gin.Context) string {
	if v := c.GetHeader("X-Workspace-ID"); v != "" {
		return v
	}
	return c.GetString("workspace_id")
}

// isHopOrCORSHeader 判断是否是不应透传给浏览器的头:
//   - HTTP/1.1 hop-by-hop 头
//   - 上游(agent)的 CORS 头(由网关统一提供,避免出现重复)
func isHopOrCORSHeader(key string) bool {
	switch strings.ToLower(key) {
	case "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
		"te", "trailers", "transfer-encoding", "upgrade":
		return true
	}
	if strings.HasPrefix(strings.ToLower(key), "access-control-") {
		return true
	}
	return false
}

// 把网关侧的 /api/xxx 路径还原为 agent 真实路径 /xxx
func stripAPIPrefix(path string) string {
	if strings.HasPrefix(path, "/api/") {
		return path[4:]
	}
	if path == "/api" {
		return "/"
	}
	return path
}
