# NOTE: Strict-Transport-Security (HSTS) 不在此处设置。
# HSTS 应由反向代理 / 负载均衡器（Nginx、Cloudflare、ALB 等）统一注入，
# 避免在开发环境或非 TLS 场景下误启用导致浏览器强制 HTTPS。
SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"x-xss-protection", b"0"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
]


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                existing = {k for k, _ in headers}
                for key, value in SECURITY_HEADERS:
                    if key not in existing:
                        headers.append((key, value))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
