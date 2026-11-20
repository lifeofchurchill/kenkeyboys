from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


from .models import NewsPost, Player, Trophy, TrialRequest
from .serializers import NewsPostSerializer, PlayerSerializer, TrialRequestSerializer, TrophySerializer

class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public squad endpoints:
      GET /api/players/                          -> the squad with season and career totals
      GET /api/players/3/                        -> one player
      GET /api/players/leaderboard/?stat=goals   -> top 10 by goals, assists, rating or motm
    """

    serializer_class = PlayerSerializer
    queryset = Player.objects.filter(is_active=True)

    # The stats a leaderboard can be sorted by, and the field each one uses
    LEADERBOARD_STATS = {
        "goals": "season_goals",
        "assists": "season_assists",
        "rating": "season_rating",
        "motm": "season_motm",
    }

    @action(detail=False)
    def leaderboard(self, request):
        stat = request.query_params.get("stat", "goals")
        field = self.LEADERBOARD_STATS.get(stat, "goals")

        top_players = (
            self.get_queryset()
            .filter(season_games__gt=0)       # leave out players who have not played
            .order_by(f"-{field}", "shirt_number")[:10]
        )
        serializer = self.get_serializer(top_players, many=True)
        return Response(serializer.data)

class TrophyViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/trophies/ and /api/trophies/?kind=team or individual"""

    serializer_class = TrophySerializer

    def get_queryset(self):
        # Fetch each trophy's player in the same query (the N+1 fix)
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

class TrialRequestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    POST /api/trials/  -> submit a trial request.
    Create-only: there is no way to list or read other people's requests here.
    """

    queryset = TrialRequest.objects.all()
    serializer_class = TrialRequestSerializer
    # Apply the "trials" rate limit defined in settings
    throttle_scope = "trials"