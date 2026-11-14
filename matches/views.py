from rest_framework import viewsets

from .models import Match
from .serializers import MatchSerializer


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public match endpoints:
      GET /api/matches/                    -> every match, newest first
      GET /api/matches/?status=upcoming    -> fixtures, soonest first
      GET /api/matches/?status=finished    -> results, newest first
      GET /api/matches/5/                  -> one match
    """

    serializer_class = MatchSerializer

    def get_queryset(self):
        # select_related fetches each match's competition in the same database query.
        # Without it, Django would run one extra query per match to get the name
        queryset = Match.objects.select_related("competition")

        # Read the optional ?status=... part of the address
        status = self.request.query_params.get("status")

        # Only accept values the model actually defines; ignore anything else
        if status in Match.Status.values:
            queryset = queryset.filter(status=status)

        # Fixtures read best soonest-first; everything else keeps newest-first
        if status == Match.Status.UPCOMING:
            queryset = queryset.order_by("kickoff")

        return queryset