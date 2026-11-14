from rest_framework.routers import DefaultRouter

from .views import MatchViewSet

router = DefaultRouter()
# basename is required here because the view has no fixed queryset to name it from
router.register("matches", MatchViewSet, basename="match")

urlpatterns = router.urls