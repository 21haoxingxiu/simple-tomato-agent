package middleware

// IP 白名单中间件 — 与应用层 JWT/网络层防火墙形成纵深防御:
//   - 默认放行本地回环 (127.0.0.0/8, ::1)
//   - 通过 IP_ALLOWLIST 环境变量声明跨主机授信网段 (逗号分隔, 支持 CIDR)
//   - TRUST_PROXY=true 时才信任 X-Forwarded-For, 否则只看 TCP 直连地址
//
// 强烈建议: 仅允许来自 127.0.0.1 + 显式配置的内网网段, 严禁公网 0.0.0.0/0.

import (
	"log"
	"net"
	"net/http"
	"os"
	"strings"

	"github.com/gin-gonic/gin"
)

var loopbackNets = mustParseCIDRs([]string{"127.0.0.0/8", "::1/128"})

// IPAllowlist 返回基于 CIDR 白名单的 Gin 中间件.
//
// allowlist: 允许网段 (本地回环始终放行)
// trustProxy: 是否优先采用 X-Forwarded-For (仅在前置可信反代时开启)
// exemptPaths: 健康检查等无需鉴权的路径
func IPAllowlist(allowlist []*net.IPNet, trustProxy bool, exemptPaths ...string) gin.HandlerFunc {
	nets := append([]*net.IPNet{}, allowlist...)
	nets = append(nets, loopbackNets...)
	exempt := make(map[string]struct{}, len(exemptPaths))
	for _, p := range exemptPaths {
		exempt[p] = struct{}{}
	}

	return func(c *gin.Context) {
		if _, ok := exempt[c.Request.URL.Path]; ok {
			c.Next()
			return
		}

		ip := clientIP(c, trustProxy)
		if ip == nil {
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
				"code":    "FORBIDDEN",
				"message": "client ip unknown",
			})
			return
		}

		for _, n := range nets {
			if n.Contains(ip) {
				c.Next()
				return
			}
		}

		log.Printf("IPAllowlist: 拒绝来自 %s 的访问 -> %s", ip.String(), c.Request.URL.Path)
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
			"code":    "FORBIDDEN",
			"message": "client ip not allowed",
		})
	}
}

// ParseAllowlist 把 "10.0.0.0/8,192.168.1.10" 解析为 *net.IPNet 列表.
// 单 IP 自动补全为 /32 或 /128.
func ParseAllowlist(raw string) []*net.IPNet {
	if raw == "" {
		return nil
	}
	out := make([]*net.IPNet, 0, 4)
	for _, item := range strings.Split(raw, ",") {
		item = strings.TrimSpace(item)
		if item == "" {
			continue
		}
		if !strings.Contains(item, "/") {
			if ip := net.ParseIP(item); ip != nil {
				if ip.To4() != nil {
					item += "/32"
				} else {
					item += "/128"
				}
			}
		}
		_, cidr, err := net.ParseCIDR(item)
		if err != nil {
			log.Printf("IPAllowlist: 跳过非法条目 %q: %v", item, err)
			continue
		}
		out = append(out, cidr)
	}
	return out
}

// AllowlistFromEnv 读取 IP_ALLOWLIST / TRUST_PROXY 环境变量.
func AllowlistFromEnv() ([]*net.IPNet, bool) {
	nets := ParseAllowlist(os.Getenv("IP_ALLOWLIST"))
	trust := strings.EqualFold(os.Getenv("TRUST_PROXY"), "true") ||
		os.Getenv("TRUST_PROXY") == "1"
	return nets, trust
}

func clientIP(c *gin.Context, trustProxy bool) net.IP {
	if trustProxy {
		if xff := c.GetHeader("X-Forwarded-For"); xff != "" {
			first := strings.TrimSpace(strings.Split(xff, ",")[0])
			if ip := net.ParseIP(first); ip != nil {
				return ip
			}
		}
		if real := c.GetHeader("X-Real-IP"); real != "" {
			if ip := net.ParseIP(strings.TrimSpace(real)); ip != nil {
				return ip
			}
		}
	}
	host, _, err := net.SplitHostPort(c.Request.RemoteAddr)
	if err != nil {
		host = c.Request.RemoteAddr
	}
	return net.ParseIP(host)
}

func mustParseCIDRs(items []string) []*net.IPNet {
	out := make([]*net.IPNet, 0, len(items))
	for _, item := range items {
		_, cidr, err := net.ParseCIDR(item)
		if err != nil {
			panic(err)
		}
		out = append(out, cidr)
	}
	return out
}
