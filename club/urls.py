from rest_framework.routers import DefaultRouter

from .views import PlayerViewSet
from .views import NewsPostViewSet, PlayerViewSet, TrophyViewSet

# The router builds the list and detail addresses for us
router = DefaultRouter()
router.register("players", PlayerViewSet, basename="player")
router.register("trophies", TrophyViewSet, basename="trophy")
router.register("news", NewsPostViewSet, basename="news")

urlpatterns = router.urls