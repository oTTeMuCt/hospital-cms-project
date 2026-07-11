from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import FileViewSet

router = SimpleRouter()
router.register(r"files", FileViewSet, basename="file")

urlpatterns = [
    path("", include(router.urls)),
]
