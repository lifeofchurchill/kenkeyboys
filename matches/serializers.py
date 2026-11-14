from rest_framework import serializers

from .models import Competition, Match


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ["id", "name", "season"]


class MatchSerializer(serializers.ModelSerializer):
    """Turns a Match into JSON, with its competition included."""

    # Nest the full competition instead of just its id,
    # so the website does not need a second request to learn the name
    competition = CompetitionSerializer(read_only=True)
    # The W/D/L property from the model; read-only because it is calculated
    result = serializers.CharField(read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "competition",
            "opponent",
            "kickoff",
            "status",
            "our_score",
            "opponent_score",
            "result",
        ]