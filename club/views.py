from rest_framework import viewsets

from .models import Player
from .serializers import PlayerSerializer


class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public squad endpoints:
      GET /api/players/      -> the whole squad
      GET /api/players/3/    -> one player
    """

    # Only current squad members; players who left are hidden
    queryset = Player.objects.filter(is_active=True)
    serializer_class = PlayerSerializer