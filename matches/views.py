from rest_framework import viewsets

from .models import Match
from .serializers import MatchDetailSerializer, MatchSerializer


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public match endpoints:
      GET /api/matches/                    -> every match, newest first
      GET /api/matches/?status=upcoming    -> fixtures, soonest first
      GET /api/matches/?status=finished    -> results, newest first
      GET /api/matches/5/                  -> one match with player stats
    """

    def get_serializer_class(self):
        # "retrieve" is the action name for fetching a single item
        if self.action == "retrieve":
            return MatchDetailSerializer
        return MatchSerializer

    def get_queryset(self):
        queryset = Match.objects.select_related("competition")

        if self.action == "retrieve":
            # Load the stat lines and their players in two extra queries in total,
            # instead of one query per stat line
            queryset = queryset.prefetch_related("stats__player")

        status = self.request.query_params.get("status")
        if status in Match.Status.values:
            queryset = queryset.filter(status=status)
        if status == Match.Status.UPCOMING:
            queryset = queryset.order_by("kickoff")

        return queryset