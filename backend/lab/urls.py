from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AnalysisOrderViewSet, AnalysisTypeViewSet

router = SimpleRouter()
router.register(r"analysis-types", AnalysisTypeViewSet, basename="analysis-type")
router.register(r"analysis-orders", AnalysisOrderViewSet, basename="analysis-order")

urlpatterns = [
    path("", include(router.urls)),
]
