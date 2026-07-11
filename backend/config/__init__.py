try:
    from .celery import app as celery_app

    __all__ = ["celery_app"]
except ImportError:
    # Celery is optional — allows running without Redis
    celery_app = None
    __all__ = ["celery_app"]
