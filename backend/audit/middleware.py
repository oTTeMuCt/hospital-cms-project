import logging
import re

from django.utils.deprecation import MiddlewareMixin

from .models import AuditLog

logger = logging.getLogger(__name__)

SKIP_PREFIXES = ("/health/", "/admin/jsi18n/", "/static/")

# Sensitive query parameters and path segments to redact
SENSITIVE_PARAMS = re.compile(
    r"(passport|pinfl|password|token|secret|key|auth|authorization|telegram_id)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_PATTERN = re.compile(r"(passport|pinfl|password|token|secret|key)=[^&]+", re.IGNORECASE)


def _sanitize_url(path: str, query_string: str = "") -> str:
    """Remove sensitive query parameters and path segments from the URL."""
    if query_string:
        sanitized_qs = SENSITIVE_VALUE_PATTERN.sub(r"\1=***REDACTED***", query_string)
        return f"{path}?{sanitized_qs}"
    return path


def _should_skip(path: str) -> bool:
    return any(path.startswith(p) for p in SKIP_PREFIXES)


class AuditMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if _should_skip(request.path):
            return response
        # Skip GET/HEAD/OPTIONS for non-sensitive paths (audit only mutating operations + auth)
        if request.method in ("GET", "HEAD", "OPTIONS") and not request.path.startswith("/api/auth"):
            return response

        # Sanitize the request path to remove sensitive data
        sanitized_action = _sanitize_url(request.path, request.META.get("QUERY_STRING", ""))

        try:
            AuditLog.objects.create(
                user=request.user if hasattr(request, "user") and request.user.is_authenticated else None,
                action=f"{request.method} {sanitized_action}",
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
