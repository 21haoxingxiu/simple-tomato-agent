"""IP 白名单中间件.

合规要求:
    - 服务端口默认仅监听 127.0.0.1, 严禁 0.0.0.0 全网监听.
    - 跨主机调用必须配置 "IP + 端口" 白名单, 仅放行授信地址.

本模块提供应用层的 IP 白名单, 与网络层 (iptables/安全组) 形成纵深防御.
支持单 IP / CIDR 网段配置, 并兼容 Docker / 反向代理场景下的 X-Forwarded-For.
"""
from __future__ import annotations

import ipaddress
import logging
import os
from typing import Iterable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# 始终放行的本地回环网段: IPv4 127.0.0.0/8 + IPv6 ::1
_LOOPBACK_NETS: tuple[ipaddress._BaseNetwork, ...] = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
)


def _parse_networks(raw: str | None) -> list[ipaddress._BaseNetwork]:
    """解析逗号分隔的 IP / CIDR 列表为网段对象."""
    if not raw:
        return []
    nets: list[ipaddress._BaseNetwork] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            nets.append(ipaddress.ip_network(item, strict=False))
        except ValueError as exc:
            logger.warning("IP_ALLOWLIST 跳过非法条目 %r: %s", item, exc)
    return nets


def _client_ip(request: Request, trust_proxy: bool) -> str | None:
    """提取客户端真实 IP.

    - trust_proxy=True 时优先取 X-Forwarded-For 链路首跳 (网关/反代场景);
    - 否则使用 TCP 直连地址, 防止伪造头绕过白名单.
    """
    if trust_proxy:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        real = request.headers.get("x-real-ip")
        if real:
            return real.strip()
    if request.client is not None:
        return request.client.host
    return None


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """基于 IP / CIDR 的白名单中间件.

    Args:
        app: ASGI 应用.
        allowlist: 允许网段列表 (本地回环始终放行).
        trust_proxy: 是否信任 X-Forwarded-For (仅在前置可信反代时开启).
        exempt_paths: 健康检查等无需鉴权的路径.
    """

    def __init__(
        self,
        app: ASGIApp,
        allowlist: Iterable[ipaddress._BaseNetwork] = (),
        trust_proxy: bool = False,
        exempt_paths: Iterable[str] = ("/health",),
    ) -> None:
        super().__init__(app)
        self._nets: tuple[ipaddress._BaseNetwork, ...] = tuple(allowlist) + _LOOPBACK_NETS
        self._trust_proxy = trust_proxy
        self._exempt = tuple(exempt_paths)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self._exempt:
            return await call_next(request)

        client = _client_ip(request, self._trust_proxy)
        if client is None:
            return JSONResponse(
                status_code=403,
                content={"code": "FORBIDDEN", "message": "client ip unknown"},
            )

        try:
            ip_obj = ipaddress.ip_address(client)
        except ValueError:
            logger.warning("IPAllowlist: 非法客户端 IP %r", client)
            return JSONResponse(
                status_code=403,
                content={"code": "FORBIDDEN", "message": "invalid client ip"},
            )

        if not any(ip_obj in net for net in self._nets):
            logger.warning("IPAllowlist: 拒绝来自 %s 的访问 -> %s", client, request.url.path)
            return JSONResponse(
                status_code=403,
                content={"code": "FORBIDDEN", "message": "client ip not allowed"},
            )

        return await call_next(request)


def from_env(env_key: str = "IP_ALLOWLIST") -> tuple[list[ipaddress._BaseNetwork], bool]:
    """从环境变量读取白名单与 trust_proxy 配置."""
    nets = _parse_networks(os.getenv(env_key))
    trust_proxy = os.getenv("TRUST_PROXY", "false").lower() in ("1", "true", "yes")
    return nets, trust_proxy
