import logging

from django.utils.deprecation import MiddlewareMixin

from .models import AuditLog

logger = logging.getLogger(__name__)


class AuditMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        try:
            AuditLog.objects.create(
                user=request.user if hasattr(request, "user") and request.user.is_authenticated else None,
                action=f"{request.method} {request.path}",
                succeeded=200 <= response.status_code < 400,
                metadata={
                    "status_code": response.status_code,
                    "content_type": response.get("Content-Type", ""),
                },
            )
        except Exception as exc:
            logger.exception("Failed to write audit log: %s", exc)
        return response
