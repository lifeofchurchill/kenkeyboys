from rest_framework import serializers
from .models import Competition, Match, PlayerMatchStat



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

class PlayerMatchStatSerializer(serializers.ModelSerializer):
    # Pull a few player details across so the page can show a name and number
    player_name = serializers.CharField(source="player.display_name", read_only=True)
    shirt_number = serializers.IntegerField(source="player.shirt_number", read_only=True)
    position = serializers.CharField(source="player.position", read_only=True)

    class Meta:
        model = PlayerMatchStat
        fields = ["player", "player_name", "shirt_number", "position", "goals", "assists", "rating", "is_motm"]


class MatchDetailSerializer(MatchSerializer):
    """Everything in MatchSerializer, plus the full list of player stats."""

    stats = PlayerMatchStatSerializer(many=True, read_only=True)

    class Meta(MatchSerializer.Meta):
        fields = MatchSerializer.Meta.fields + ["stats"]