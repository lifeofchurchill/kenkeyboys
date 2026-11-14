from django.utils import timezone
from rest_framework import viewsets
from .models import NewsPost, Player, Trophy
from .serializers import NewsPostSerializer, PlayerSerializer, TrophySerializer

class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public squad endpoints:
      GET /api/players/      -> the whole squad
      GET /api/players/3/    -> one player
    """

    # Only current squad members; players who left are hidden
    queryset = Player.objects.filter(is_active=True)
    serializer_class = PlayerSerializer

class TrophyViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/trophies/ and /api/trophies/?kind=team or individual"""

    serializer_class = TrophySerializer

    def get_queryset(self):
        # Fetch each trophy's player in the same query (the N+1 fix from last step)
        queryset = Trophy.objects.select_related("player")
        kind = self.request.query_params.get("kind")
        if kind in Trophy.Kind.values:
            queryset = queryset.filter(kind=kind)
        return queryset


class NewsPostViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/news/ and /api/news/?category=match_report"""

    serializer_class = NewsPostSerializer

    def get_queryset(self):
        # Hide posts scheduled for the future: only show ones whose time has come
        queryset = NewsPost.objects.filter(published_at__lte=timezone.now())
        category = self.request.query_params.get("category")
        if category in NewsPost.Category.values:
            queryset = queryset.filter(category=category)
        return queryset