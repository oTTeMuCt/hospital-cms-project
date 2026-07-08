import logging

from django.utils.deprecation import MiddlewareMixin

from .models import AuditLog

logger = logging.getLogger(__name__)

SKIP_PREFIXES = ("/health/", "/admin/jsi18n/", "/static/")


def _should_skip(path: str) -> bool:
    return any(path.startswith(p) for p in SKIP_PREFIXES)


class AuditMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if _should_skip(request.path):
            return response
        # Skip GET/HEAD/OPTIONS for non-sensitive paths (audit only mutating operations + auth)
        if request.method in ("GET", "HEAD", "OPTIONS") and not request.path.startswith("/api/auth"):
            return response

        try:
            AuditLog.objects.create(
                user=request.user if hasattr(request, "user") and request.user.is_authenticated else None,
                action=f"{request.method} {request.path}",
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
                succeeded=200 <= response.status_code < 400,
                metadata={
                    "status_code": response.status_code,
                },
            )
        except Exception as exc:
            logger.exception("Failed to write audit log: %s", exc)
        return response
