from rest_framework.routers import DefaultRouter

from .views import PlayerViewSet

# The router builds the list and detail addresses for us
router = DefaultRouter()
router.register("players", PlayerViewSet, basename="player")

urlpatterns = router.urls